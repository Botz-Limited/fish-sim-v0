"""Etap 2: komora L quasi-statycznie – krzywa p–V i kąt końcówki, studium zbieżności siatki.

Uruchomienie:  source scripts/env.sh && python scripts/run_stage2.py   (~25 min, głównie fine)

Konstrukcja V4 (kręgosłup + włókna obwodowe, domyślna w config.py). Komora L: zadany
przyrost objętości 0…dV_max; komora R odpowietrzona (ciśnienie 0, jak drugi króciec
otwarty na stanowisku pomiarowym); bez ciężaru (krzywa zależy tylko od konstrukcji).
To jest krzywa, którą da się zmierzyć na prawdziwym ogonie: strzykawka/pompa
dozująca objętość, czujnik ciśnienia, kątomierz albo zdjęcie z góry.

Wyniki w results/: s2_pv_curve.png, s2_tip_angle.png, s2_curves.csv, s2_convergence.txt.
"""
import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fishsofa import PROJECT_DIR, headless, mesh_gen  # noqa: E402
from fishsofa.config import TailConfig  # noqa: E402

LEVELS = ["coarse", "medium", "fine"]
RESULTS = os.path.join(PROJECT_DIR, "results")
COLORS = {"coarse": "#2a78d6", "medium": "#eb6834", "fine": "#1baf7a"}   # paleta dataviz, stała kolejność
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def main():
    os.makedirs(RESULTS, exist_ok=True)
    cfg = TailConfig(include_weight=False)
    targets = np.arange(5e-6, cfg.dV_max + 1e-12, 5e-6)
    curves, ntets = {}, {}
    for lv in LEVELS:
        print(f"[{lv}] ...", flush=True)
        mesh_gen.ensure(cfg, lv)
        ntets[lv] = len(mesh_gen.load(cfg, lv).tets)
        c = headless.quasi_static_sweep(cfg, lv, targets, ramp_steps=3)
        curves[lv] = c
        print(f"  V0 = {c.v0 * 1e6:.1f} ml; ΔV = {c.dV[-1] * 1e6:.1f} ml -> p = {c.p[-1] / 1e3:.2f} kPa, "
              f"θ = {np.degrees(c.tip_angle[-1]):.2f}°; max KE/W = {max(c.ke_ratio):.1e}; {c.wall_s:.0f} s", flush=True)

    with open(os.path.join(RESULTS, "s2_curves.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["level", "n_tets", "dV_ml", "p_kPa", "theta_deg", "ke_ratio"])
        for lv, c in curves.items():
            for a, b, t, k in zip(c.dV, c.p, c.tip_angle, c.ke_ratio):
                w.writerow([lv, ntets[lv], f"{a * 1e6:.4f}", f"{b / 1e3:.5f}", f"{np.degrees(t):.5f}", f"{k:.2e}"])

    # Zbieżność: różnica coarse i medium względem fine w punkcie dV_max i w połowie zakresu.
    ref = curves["fine"]
    lines = ["Etap 2 – zbieżność siatki (V4, komora L, R odpowietrzona, bez ciężaru)",
             "różnica względem fine; ujemna = mniej niż fine", ""]
    for k_pt in (len(ref.dV) // 2 - 1, len(ref.dV) - 1):
        lines.append(f"ΔV = {ref.dV[k_pt] * 1e6:.1f} ml: fine p = {ref.p[k_pt] / 1e3:.3f} kPa, "
                     f"θ = {np.degrees(ref.tip_angle[k_pt]):.3f}°")
        for lv in ("coarse", "medium"):
            c = curves[lv]
            dp = (c.p[k_pt] / ref.p[k_pt] - 1) * 100
            dth = (c.tip_angle[k_pt] / ref.tip_angle[k_pt] - 1) * 100
            lines.append(f"  {lv:6s} ({ntets[lv]} tetr): p {dp:+.1f}%, θ {dth:+.1f}%")
    txt = "\n".join(lines)
    print("\n" + txt)
    with open(os.path.join(RESULTS, "s2_convergence.txt"), "w") as f:
        f.write(txt + "\n")
    plot(curves, ntets, cfg)


def _style(ax):
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def plot(curves, ntets, cfg):
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK})
    for fname, ylab, fn, title in [
            ("s2_pv_curve.png", "ciśnienie p [kPa]", lambda c: np.array(c.p) / 1e3,
             "Krzywa ciśnienie–objętość komory L"),
            ("s2_tip_angle.png", "kąt końcówki θ_tip [°]", lambda c: np.degrees(c.tip_angle),
             "Kąt końcówki vs objętość (ujemny = zgięcie w −Y, w prawo)")]:
        fig, ax = plt.subplots(figsize=(7.5, 4.6), constrained_layout=True)
        _style(ax)
        for lv, c in curves.items():
            ax.plot(np.r_[0, np.array(c.dV) * 1e6], np.r_[0, fn(c)], color=COLORS[lv], linewidth=2,
                    marker="o", markersize=5, label=f"{lv} ({ntets[lv] // 1000}k tetr)")
        ax.set_xlabel("przyrost objętości komory L, ΔV [ml]")
        ax.set_ylabel(ylab)
        fig.suptitle(title, x=0.01, ha="left", color=INK, fontsize=12)
        ax.set_title(f"V4: kręgosłup E×{cfg.spine_E_factor:.0f} + włókna obwodowe; E = {cfg.young_modulus:.0e} Pa "
                     "(PLACEHOLDER); komora R odpowietrzona; bez ciężaru", loc="left", color=INK2, fontsize=8)
        ax.legend(frameon=False, labelcolor=INK)
        fig.savefig(os.path.join(RESULTS, fname), dpi=150, facecolor="white")
        plt.close(fig)


def plot_from_csv():
    """Przerysowanie wykresów z results/s2_curves.csv bez ponownego liczenia."""
    from types import SimpleNamespace
    curves, ntets = {}, {}
    with open(os.path.join(RESULTS, "s2_curves.csv")) as f:
        for row in csv.DictReader(f):
            c = curves.setdefault(row["level"], SimpleNamespace(dV=[], p=[], tip_angle=[]))
            ntets[row["level"]] = int(row["n_tets"])
            c.dV.append(float(row["dV_ml"]) * 1e-6)
            c.p.append(float(row["p_kPa"]) * 1e3)
            c.tip_angle.append(np.radians(float(row["theta_deg"])))
    plot(curves, ntets, TailConfig())


if __name__ == "__main__":
    if "--plot-only" in sys.argv:
        plot_from_csv()
    else:
        main()
