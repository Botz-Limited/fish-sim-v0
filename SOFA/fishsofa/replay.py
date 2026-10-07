"""Real-time playback of a recording (scripts/record.py) in the SOFA GUI.

A scene without physics: only visual models of the skin and chambers. Each GUI frame the
controller computes which recording frame matches the elapsed wall-clock time and swaps
in the vertex positions. So the playback speed does not depend on how fast the GUI draws:
1 s of recording lasts 1 s (or 1/speed s, e.g. speed = 0.25 is slow motion).
The recording plays in a loop.

Chambers are colored by the recorded pressure (blue = lowest in the rhythm phase,
red = highest); the skin is semi-transparent so they are visible.
"""
import time

import numpy as np
import Sofa.Core

SKIN = [0.95, 0.70, 0.30, 0.35]


def _colormap(s: float) -> list:
    """0 -> blue, 1 -> red (via light gray), RGBA."""
    s = float(np.clip(s, 0.0, 1.0))
    lo, mid, hi = np.array([0.16, 0.47, 0.84]), np.array([0.85, 0.85, 0.85]), np.array([0.92, 0.25, 0.15])
    c = lo + (mid - lo) * s * 2 if s < 0.5 else mid + (hi - mid) * (s - 0.5) * 2
    return [*c.tolist(), 1.0]


def build(root, path: str, speed: float = 1.0):
    rec = np.load(path)
    x0 = rec["x"][0].astype(float)
    root.addObject("RequiredPlugin", pluginName=["Sofa.Component.AnimationLoop", "Sofa.GL.Component.Rendering3D",
                                                 "Sofa.Component.Visual", "Sofa.Component.StateContainer",
                                                 "Sofa.Component.Mapping.Linear"])
    root.addObject("DefaultAnimationLoop")
    root.addObject("VisualStyle", displayFlags="showVisualModels")
    root.dt = 1.0 / 60
    root.gravity = [0.0, 0.0, 0.0]
    models = {}
    for name, key, color in (("skin", "tri_outer", SKIN), ("chamberL", "tri_chamber_L", _colormap(0.5)),
                             ("chamberR", "tri_chamber_R", _colormap(0.5))):
        tris = rec[key]
        used = np.unique(tris)          # only this surface's vertices (less data per frame)
        remap = np.full(len(x0), -1)
        remap[used] = np.arange(len(used))
        # Positions live in a MechanicalObject, and OglModel gets them via IdentityMapping.
        # Writing directly to OglModel.position does not refresh the on-screen geometry
        # (color does, shape does not); SOFA updates mappings every step.
        node = root.addChild(name)
        dofs = node.addObject("MechanicalObject", name="dofs", template="Vec3d", position=x0[used].tolist())
        ogl = node.addObject("OglModel", name="ogl", position=x0[used].tolist(),
                             triangles=remap[tris].tolist(), color=color)
        node.addObject("IdentityMapping", input="@dofs", output="@ogl")
        models[name] = (dofs, ogl, used)
    root.addObject(ReplayController(name="replay", rec=rec, models=models, speed=speed))
    return root


class ReplayController(Sofa.Core.Controller):
    def __init__(self, *args, rec, models, speed, **kwargs):
        super().__init__(*args, **kwargs)
        self.t, self.x, self.models, self.speed = rec["t"], rec["x"], models, speed
        p_L, p_R, t_log = rec["log_p_L"], rec["log_p_R"], rec["log_t"]
        # Pressure at frame instants (the log has step dt, frames every 1/60 s).
        self.p = {"chamberL": np.interp(self.t, t_log, p_L), "chamberR": np.interp(self.t, t_log, p_R)}
        # Scale from the rhythm phase (after prefill): motion is driven by a ±6 kPa difference
        # on top of a ~53 kPa common pressure; a scale from 0 would hide it. During prefill the
        # color is out of scale.
        m = self.t > float(rec["prefill_time"]) + 0.2
        lo = min(self.p["chamberL"][m].min(), self.p["chamberR"][m].min())
        hi = max(self.p["chamberL"][m].max(), self.p["chamberR"][m].max())
        self.p_range = (lo, max(hi, lo + 1.0))
        self.start = None
        self.last = -1
        print(f"Replay: {rec['env']}, {len(self.t)} frames, {self.t[-1]:.2f} s of recording, speed ×{speed:g}")

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
        for name, (dofs, ogl, used) in self.models.items():
            dofs.position.value = x[used]
            if name in self.p:
                ogl.material.value = _material(_colormap((self.p[name][k] - lo) / (hi - lo)))


def _material(rgba) -> str:
    """OglModel material (SOFA format) with diffuse color rgba."""
    c = " ".join(f"{v:.3f}" for v in rgba)
    return f"Default Diffuse 1 {c} Ambient 1 {c} Specular 0 1 1 1 1 Emissive 0 0 0 0 0 Shininess 0 45"
