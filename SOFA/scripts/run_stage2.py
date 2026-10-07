"""Stage 2: chamber L quasi-statically – p–V curve and tip angle, mesh convergence study.

Usage:  source scripts/env.sh && python scripts/run_stage2.py   (~25 min, mostly fine)
        python scripts/run_stage2.py --plot-only                (only the plots from CSV)

Design V4 (spine + hoop fibers, the default in config.py). Chamber L: prescribed volume
growth 0…dV_max; chamber R vented (pressure 0, like the second port left open on the
test bench); no weight (the curve depends only on the design).
This is a curve that can be measured on the real tail: a syringe/metering pump
dosing the volume, a pressure sensor, a protractor or a photo from above.

Results in results/: s2_pv_curve.png, s2_tip_angle.png, s2_curves.csv, s2_convergence.txt.
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
COLORS = {"coarse": "#2a78d6", "medium": "#eb6834", "fine": "#1baf7a"}   # dataviz palette, fixed order
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

    # Convergence: difference of coarse and medium vs fine at dV_max and at half the range.
    ref = curves["fine"]
    lines = ["Stage 2 – mesh convergence (V4, chamber L, R vented, no weight)",
             "difference vs fine; negative = less than fine", ""]
    for k_pt in (len(ref.dV) // 2 - 1, len(ref.dV) - 1):
        lines.append(f"ΔV = {ref.dV[k_pt] * 1e6:.1f} ml: fine p = {ref.p[k_pt] / 1e3:.3f} kPa, "
                     f"θ = {np.degrees(ref.tip_angle[k_pt]):.3f}°")
        for lv in ("coarse", "medium"):
            c = curves[lv]
            dp = (c.p[k_pt] / ref.p[k_pt] - 1) * 100
            dth = (c.tip_angle[k_pt] / ref.tip_angle[k_pt] - 1) * 100
            lines.append(f"  {lv:6s} ({ntets[lv]} tets): p {dp:+.1f}%, θ {dth:+.1f}%")
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
            ("s2_pv_curve.png", "pressure p [kPa]", lambda c: np.array(c.p) / 1e3,
             "Pressure–volume curve of chamber L"),
            ("s2_tip_angle.png", "tip angle θ_tip [°]", lambda c: np.degrees(c.tip_angle),
             "Tip angle vs volume (negative = bending towards −Y, to the right)")]:
        fig, ax = plt.subplots(figsize=(7.5, 4.6), constrained_layout=True)
        _style(ax)
        for lv, c in curves.items():
            ax.plot(np.r_[0, np.array(c.dV) * 1e6], np.r_[0, fn(c)], color=COLORS[lv], linewidth=2,
                    marker="o", markersize=5, label=f"{lv} ({ntets[lv] // 1000}k tets)")
        ax.set_xlabel("chamber L volume growth, ΔV [ml]")
        ax.set_ylabel(ylab)
        fig.suptitle(title, x=0.01, ha="left", color=INK, fontsize=12)
        ax.set_title(f"V4: spine E×{cfg.spine_E_factor:.0f} + hoop fibers; E = {cfg.young_modulus:.0e} Pa "
                     "(PLACEHOLDER); chamber R vented; no weight", loc="left", color=INK2, fontsize=8)
        ax.legend(frameon=False, labelcolor=INK)
        fig.savefig(os.path.join(RESULTS, fname), dpi=150, facecolor="white")
        plt.close(fig)


def plot_from_csv():
    """Redraw the plots from results/s2_curves.csv without recomputing."""
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
