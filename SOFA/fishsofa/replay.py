"""Odtwarzanie nagrania (scripts/record.py) w GUI SOFA, w czasie rzeczywistym.

Scena bez fizyki: tylko modele wizualne skóry i komór. Kontroler w każdej klatce GUI
liczy, która klatka nagrania odpowiada upływowi czasu na zegarze ściennym, i podmienia
pozycje wierzchołków. Dzięki temu tempo nie zależy od tego, jak szybko GUI rysuje:
1 s nagrania trwa 1 s (albo 1/speed s, np. speed = 0.25 to zwolnione tempo).
Nagranie odtwarza się w pętli.

Komory są kolorowane ciśnieniem z nagrania (niebieski = najniższe w fazie rytmu,
czerwony = najwyższe), skóra jest półprzezroczysta, żeby było je widać.
"""
import time

import numpy as np
import Sofa.Core

SKIN = [0.95, 0.70, 0.30, 0.35]


def _colormap(s: float) -> list:
    """0 -> niebieski, 1 -> czerwony (przez jasną szarość), RGBA."""
    s = float(np.clip(s, 0.0, 1.0))
    lo, mid, hi = np.array([0.16, 0.47, 0.84]), np.array([0.85, 0.85, 0.85]), np.array([0.92, 0.25, 0.15])
    c = lo + (mid - lo) * s * 2 if s < 0.5 else mid + (hi - mid) * (s - 0.5) * 2
    return [*c.tolist(), 1.0]


def build(root, path: str, speed: float = 1.0):
    rec = np.load(path)
    x0 = rec["x"][0].astype(float)
    root.addObject("RequiredPlugin", pluginName=["Sofa.Component.AnimationLoop", "Sofa.GL.Component.Rendering3D",
                                                 "Sofa.Component.Visual"])
    root.addObject("DefaultAnimationLoop")
    root.addObject("VisualStyle", displayFlags="showVisualModels")
    root.dt = 1.0 / 60
    root.gravity = [0.0, 0.0, 0.0]
    models = {}
    for name, key, color in (("skin", "tri_outer", SKIN), ("chamberL", "tri_chamber_L", _colormap(0.5)),
                             ("chamberR", "tri_chamber_R", _colormap(0.5))):
        tris = rec[key]
        used = np.unique(tris)          # tylko wierzchołki tej powierzchni (mniej danych na klatkę)
        remap = np.full(len(x0), -1)
        remap[used] = np.arange(len(used))
        node = root.addChild(name)
        models[name] = (node.addObject("OglModel", name="ogl", position=x0[used].tolist(),
                                       triangles=remap[tris].tolist(), color=color), used)
    root.addObject(ReplayController(name="replay", rec=rec, models=models, speed=speed))
    return root


class ReplayController(Sofa.Core.Controller):
    def __init__(self, *args, rec, models, speed, **kwargs):
        super().__init__(*args, **kwargs)
        self.t, self.x, self.models, self.speed = rec["t"], rec["x"], models, speed
        p_L, p_R, t_log = rec["log_p_L"], rec["log_p_R"], rec["log_t"]
        # Ciśnienie w chwilach klatek (log ma krok dt, klatki co 1/60 s).
        self.p = {"chamberL": np.interp(self.t, t_log, p_L), "chamberR": np.interp(self.t, t_log, p_R)}
        # Skala z fazy rytmu (po prefillu): ruch steruje różnica ±6 kPa na tle ciśnienia
        # wspólnego ~53 kPa; skala od 0 by ją ukryła. W prefillu kolor jest poza skalą.
        m = self.t > float(rec["prefill_time"]) + 0.2
        lo = min(self.p["chamberL"][m].min(), self.p["chamberR"][m].min())
        hi = max(self.p["chamberL"][m].max(), self.p["chamberR"][m].max())
        self.p_range = (lo, max(hi, lo + 1.0))
        self.start = None
        self.last = -1
        print(f"Odtwarzanie: {rec['env']}, {len(self.t)} klatek, {self.t[-1]:.2f} s nagrania, tempo ×{speed:g}")

    def onAnimateBeginEvent(self, event):
        now = time.perf_counter()
        if self.start is None:
            self.start = now
        t_rec = ((now - self.start) * self.speed) % self.t[-1]
        k = int(np.searchsorted(self.t, t_rec))
        k = min(k, len(self.t) - 1)
        if k == self.last:
            return
        self.last = k
        x = self.x[k]
        lo, hi = self.p_range
        for name, (ogl, used) in self.models.items():
            ogl.position.value = x[used]
            if name in self.p:
                ogl.material.value = _material(_colormap((self.p[name][k] - lo) / (hi - lo)))


def _material(rgba) -> str:
    """Materiał OglModel (format SOFA) o kolorze rozproszonym rgba."""
    c = " ".join(f"{v:.3f}" for v in rgba)
    return f"Default Diffuse 1 {c} Ambient 1 {c} Specular 0 1 1 1 1 Emissive 0 0 0 0 0 Shininess 0 45"
