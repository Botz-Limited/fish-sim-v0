"""Wideo machania ogona: powietrze i woda obok siebie, w czasie rzeczywistym.

Uruchomienie:  source scripts/env.sh && python scripts/render_video.py      (~3 min)
Wymaga nagrań z scripts/record.py (recordings/air.npz, recordings/water.npz) oraz
pakietu pyvista (pip install pyvista==0.49.0) i ffmpeg w systemie.

Wynik: results/flapping.mp4 (1920×1080, 60 kl./s):
  - cały przebieg 4.5 s w czasie rzeczywistym (prefill, rampa, rytm 2 Hz),
  - potem ostatni cykl 4× zwolniony.
Widok z góry (oś Z do patrzącego): ogon wychodzi w lewo z kadłuba (szary prostokąt),
komora L (+Y) jest u góry. Skóra półprzezroczysta, komory kolorowane ciśnieniem
(wspólna skala dla obu przebiegów). Pod spodem kąt końcówki θ(t) z kursorem.
"""
import os
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from matplotlib import cm
from matplotlib.colors import Normalize

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fishsofa import PROJECT_DIR  # noqa: E402

REC_DIR = os.path.join(PROJECT_DIR, "recordings")
OUT = os.path.join(PROJECT_DIR, "results", "flapping.mp4")
W, H, FPS = 1920, 1080, 60
SLOWMO = 0.25
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE = "#2a78d6", "#eb6834"
SKIN = "#f2b24d"
CMAP = matplotlib.colormaps["coolwarm"]
RUNS = (("air", "powietrze", ORANGE), ("water", "woda", BLUE))


def faces(tris):
    return np.hstack([np.full((len(tris), 1), 3), tris]).ravel()


class Scene3D:
    """Plotter PyVista dla jednego nagrania; frame(x, pL, pR) zwraca obraz RGB."""

    def __init__(self, rec, size, bounds, norm):
        self.norm = norm
        x0 = rec["x"][0].astype(float)
        self.p = pv.Plotter(off_screen=True, window_size=size)
        self.p.set_background("white")
        self.skin = pv.PolyData(x0, faces(rec["tri_outer"]))
        self.cL = pv.PolyData(x0, faces(rec["tri_chamber_L"]))
        self.cR = pv.PolyData(x0, faces(rec["tri_chamber_R"]))
        # Komory bez cieniowania (lighting=False): kolor ma odpowiadać skali ciśnienia 1:1.
        self.aL = self.p.add_mesh(self.cL, color="white", lighting=False)
        self.aR = self.p.add_mesh(self.cR, color="white", lighting=False)
        self.p.add_mesh(self.skin, color=SKIN, opacity=0.25, smooth_shading=True)
        # Kadłub (nieruchomy) – ogon jest do niego przymocowany w x = 0.
        self.p.add_mesh(pv.Box((0.0, 0.03, -0.035, 0.035, -0.045, 0.045)), color="#9b9a96")
        self.p.view_xy()
        self.p.camera.focal_point = bounds["center"]
        self.p.camera.position = (*bounds["center"][:2], 1.0)
        self.p.camera.parallel_projection = True
        self.p.camera.parallel_scale = bounds["half_height"]

    def frame(self, x, p_L, p_R):
        for mesh in (self.skin, self.cL, self.cR):
            mesh.points = x
        self.aL.prop.color = CMAP(self.norm(p_L))[:3]
        self.aR.prop.color = CMAP(self.norm(p_R))[:3]
        # Bez jawnego render() screenshot zwraca ostatni narysowany obraz (pierwszą klatkę).
        self.p.render()
        return self.p.screenshot(return_img=True)


def interp_frame(rec, t):
    """Pozycje węzłów w chwili t (liniowo między klatkami nagrania)."""
    tt = rec["t"]
    k = int(np.clip(np.searchsorted(tt, t) - 1, 0, len(tt) - 2))
    a = (t - tt[k]) / (tt[k + 1] - tt[k])
    return ((1 - a) * rec["x"][k] + a * rec["x"][k + 1]).astype(float)


def main():
    recs = {}
    for env, _, _ in RUNS:
        path = os.path.join(REC_DIR, f"{env}.npz")
        if not os.path.exists(path):
            sys.exit(f"brak {path} – najpierw: python scripts/record.py")
        recs[env] = dict(np.load(path))
    t_end = min(r["t"][-1] for r in recs.values())
    T = 1.0 / float(recs["water"]["tail_freq"])
    # Czas nagrania dla każdej klatki wideo: całość w czasie rzeczywistym + ostatni cykl zwolniony.
    t_video = np.concatenate([np.arange(0, t_end, 1 / FPS), np.arange(t_end - T, t_end, SLOWMO / FPS)])
    slow_from = int(np.ceil(t_end * FPS))

    # Wspólna skala ciśnień z fazy rytmu (po prefillu): ciśnienie wspólne ~53 kPa, a ruch
    # steruje różnica ±6 kPa – skala od 0 by ją ukryła. W prefillu kolor jest poza skalą (niebieski).
    p_all = np.concatenate([np.r_[r["log_p_L"][m], r["log_p_R"][m]] for r in recs.values()
                            for m in [r["log_t"] > float(r["prefill_time"]) + 0.2]])
    norm = Normalize(p_all.min(), p_all.max(), clip=True)
    xy = np.concatenate([r["x"][:, :, :2].reshape(-1, 2) for r in recs.values()])
    lo, hi = xy.min(axis=0), xy.max(axis=0)
    lo[0], hi[0] = lo[0] - 0.01, 0.03 + 0.01   # z kadłubem
    half_w, half_h = 0.5 * (hi - lo) * 1.05
    panel = (900, 560)
    half_h = max(half_h, half_w * panel[1] / panel[0])
    bounds = {"center": (*(0.5 * (lo + hi)), 0.0), "half_height": half_h}
    scenes = {env: Scene3D(recs[env], panel, bounds, norm) for env, _, _ in RUNS}

    plt.rcParams.update({"font.size": 13, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2})
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor="white")
    gs = fig.add_gridspec(2, 3, height_ratios=[2.3, 1], width_ratios=[1, 1, 0.04],
                          left=0.06, right=0.95, top=0.88, bottom=0.09, hspace=0.25, wspace=0.05)
    img_axes = {env: fig.add_subplot(gs[0, i]) for i, (env, _, _) in enumerate(RUNS)}
    ims = {}
    for env, label, color in RUNS:
        ax = img_axes[env]
        ims[env] = ax.imshow(np.ones((panel[1], panel[0], 3), np.uint8) * 255)
        ax.set_axis_off()
        ax.set_title(label, color=color, fontsize=18, fontweight="bold", loc="left")
    cax = fig.add_subplot(gs[0, 2])
    cb = fig.colorbar(cm.ScalarMappable(norm=Normalize(norm.vmin / 1e3, norm.vmax / 1e3), cmap=CMAP), cax=cax)
    cb.set_label("ciśnienie w komorze [kPa] (zakres z fazy rytmu)", color=INK2)
    cb.outline.set_visible(False)
    axt = fig.add_subplot(gs[1, :2])
    for env, label, color in RUNS:
        r = recs[env]
        axt.plot(r["log_t"], np.degrees(r["log_theta"]), color=color, linewidth=2, label=label)
    axt.axvspan(0, float(recs["water"]["prefill_time"]), color=GRID, alpha=0.6, linewidth=0)
    axt.text(0.5 * float(recs["water"]["prefill_time"]), 0.05, "prefill komór", transform=axt.get_xaxis_transform(),
             ha="center", color=INK2, fontsize=11)
    axt.set_xlim(0, t_end)
    axt.set_ylabel("kąt końcówki θ [°]")
    axt.set_xlabel("czas symulacji [s]")
    axt.grid(True, color=GRID)
    for s in ("top", "right"):
        axt.spines[s].set_visible(False)
    axt.legend(frameon=False, loc="upper left", ncol=2)
    cursor = axt.axvline(0, color=INK, linewidth=1.5)
    fig.text(0.03, 0.95, "Miękki ogon robota-ryby (SOFA, FEM): komora L ↔ R, rytm 2 Hz, A_V = 17 ml",
             fontsize=20, color=INK, fontweight="bold")
    status = fig.text(0.03, 0.915, "", fontsize=14, color=INK2)
    ms = {env: float(recs[env]["dt"]) for env, _, _ in RUNS}
    note = (f"Widok z góry, kadłub po prawej. Liczone offline (krok {ms['air'] * 1e3:g} / {ms['water'] * 1e3:g} ms, "
            "~400–800× wolniej niż czas rzeczywisty), odtwarzane w czasie rzeczywistym. Parametry PLACEHOLDER.")
    fig.text(0.03, 0.015, note, fontsize=11, color=INK2)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                           "-crf", "20", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    for i, t in enumerate(t_video):
        for env, _, _ in RUNS:
            r = recs[env]
            p_L, p_R = (np.interp(t, r["log_t"], r[k]) for k in ("log_p_L", "log_p_R"))
            ims[env].set_data(scenes[env].frame(interp_frame(r, t), p_L, p_R))
        cursor.set_xdata([t, t])
        speed = "czas rzeczywisty" if i < slow_from else f"ostatni cykl, zwolnione {1 / SLOWMO:g}×"
        status.set_text(f"t = {t:5.2f} s   ·   {speed}")
        fig.canvas.draw()
        ff.stdin.write(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].tobytes())
        if (i + 1) % 60 == 0:
            print(f"  {i + 1}/{len(t_video)} klatek", flush=True)
    ff.stdin.close()
    ff.wait()
    print(f"{OUT}: {len(t_video) / FPS:.1f} s, {os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
