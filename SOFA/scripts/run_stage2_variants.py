"""Stage 2a: sweep of tail design variants – which one bends?

Usage:  source scripts/env.sh && python scripts/run_stage2_variants.py   (~10–15 min)
        python scripts/run_stage2_variants.py --plot-only                (only the plot from CSV)

Problem (stage 2 plan): with the current geometry, 30 ml in chamber L bends the tail by
< 0.1°, because the thin outer wall bulges like a balloon. We compare variants, each
quasi-statically (chamber L, R vented, no weight, coarse mesh):
  V0 current, V1 spine (septum E×20), V2 wall 8 mm,
  V3 hoop fibers on the skin, V4 spine + fibers.
Selection criterion: 15° at p ≤ 50 kPa (relief valve p_max in MuJoCo) and ΔV ≤ 50% of the
chamber volume (curves computed up to 80% to show the trend);
among those that pass – the lowest pressure.

Results: results/s2_variants.csv, results/s2_variants.png, table on screen.
"""
import csv
import os
import sys
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fishsofa import PROJECT_DIR, headless  # noqa: E402
from fishsofa.config import TailConfig  # noqa: E402

LEVEL = "coarse"
P_MAX = 50e3          # [Pa] as p_max in MuJoCo/fishsim/config.py (PLACEHOLDER)
TARGET_DEG = 15.0
DV_TARGETS = np.arange(2.5e-6, 75e-6, 2.5e-6)
MAX_FRACTION_SWEEP = 0.8   # compute beyond the criterion to show the trend
MAX_FRACTION_OK = 0.5      # selection criterion: ΔV ≤ 50% of the chamber volume
RESULTS = os.path.join(PROJECT_DIR, "results")

# Each variant sets ALL design switches EXPLICITLY: the default config is already V4,
# so a bare "{}" would not be the current variant (this happened in one run).
_BASE = {"spine_E_factor": 1.0, "hoop_fibers": False, "wall_thickness": 0.004}
VARIANTS = {
    "V0 current": {**_BASE},
    "V1 spine E×20": {**_BASE, "spine_E_factor": 20.0},
    "V2 wall 8 mm": {**_BASE, "wall_thickness": 0.008},
    "V3 hoop fibers": {**_BASE, "hoop_fibers": True},
    "V4 spine + fibers": {**_BASE, "spine_E_factor": 20.0, "hoop_fibers": True},
}

# Categorical palette (dataviz skill, light mode), fixed order.
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def at_angle(curve, deg):
    """ΔV and p needed for |θ| = deg (linear interpolation); None if not reached."""
    th = np.degrees(np.abs(curve.tip_angle))
    for k in range(1, len(th)):
        if th[k] >= deg > th[k - 1]:
            f = (deg - th[k - 1]) / (th[k] - th[k - 1])
            return (curve.dV[k - 1] + f * (curve.dV[k] - curve.dV[k - 1]),
                    curve.p[k - 1] + f * (curve.p[k] - curve.p[k - 1]))
    return None


def main():
    os.makedirs(RESULTS, exist_ok=True)
    curves, rows = {}, []
    for name, over in VARIANTS.items():
        cfg = TailConfig(include_weight=False, **over)
        print(f"[{name}] ...", flush=True)
        c = headless.quasi_static_sweep(cfg, LEVEL, DV_TARGETS, p_stop=P_MAX, max_fraction=MAX_FRACTION_SWEEP)
        curves[name] = c
        hit = at_angle(c, TARGET_DEG)
        k = int(np.argmax(np.abs(c.tip_angle)))
        rows.append({
            "variant": name, "V0_ml": c.v0 * 1e6,
            "max_angle_deg": float(np.degrees(np.abs(c.tip_angle[k]))), "at_dV_ml": c.dV[k] * 1e6,
            "p_at_max_kPa": c.p[k] / 1e3, "dV_last_ml": c.dV[-1] * 1e6, "p_last_kPa": c.p[-1] / 1e3,
            "dV_15deg_ml": hit[0] * 1e6 if hit else float("nan"),
            "p_15deg_kPa": hit[1] / 1e3 if hit else float("nan"),
            "bulge_last_mm": c.bulge[-1] * 1e3, "time_s": c.wall_s,
        })
        r = rows[-1]
        print(f"  V0 = {r['V0_ml']:.1f} ml, max |θ| = {r['max_angle_deg']:.2f}° at ΔV = {r['at_dV_ml']:.1f} ml "
              f"(p = {r['p_at_max_kPa']:.1f} kPa); 15°: "
              + (f"ΔV = {r['dV_15deg_ml']:.1f} ml, p = {r['p_15deg_kPa']:.1f} kPa" if hit else "not reached")
              + f"; bulging {r['bulge_last_mm']:.1f} mm; {r['time_s']:.0f} s", flush=True)

    with open(os.path.join(RESULTS, "s2_variants.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
        f.write("\n# curves: variant, dV_ml, p_kPa, theta_deg, bulge_mm\n")
        for name, c in curves.items():
            for a, b, t, g in zip(c.dV, c.p, c.tip_angle, c.bulge):
                f.write(f"# {name},{a * 1e6:.3f},{b / 1e3:.4f},{np.degrees(t):.4f},{g * 1e3:.3f}\n")

    ok = [r for r in rows if r["p_15deg_kPa"] == r["p_15deg_kPa"]
          and r["dV_15deg_ml"] <= MAX_FRACTION_OK * r["V0_ml"] and r["p_15deg_kPa"] <= P_MAX / 1e3]
    best = min(ok, key=lambda r: r["p_15deg_kPa"]) if ok else None
    print("\nCHOICE:", f"{best['variant']} (15° at {best['p_15deg_kPa']:.1f} kPa, ΔV {best['dV_15deg_ml']:.1f} ml)"
          if best else "no variant reaches 15° within p ≤ 50 kPa and ΔV ≤ 50% V0")
    plot(curves)


def plot(curves):
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK})
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), constrained_layout=True)
    panels = [("|θ_tip| [°]", lambda c: np.degrees(np.abs(c.tip_angle)), "Tip angle"),
              ("pressure [kPa]", lambda c: np.array(c.p) / 1e3, "Chamber L pressure"),
              ("bulging relative to the axis [mm]", lambda c: np.array(c.bulge) * 1e3, "Lateral bulging (skin relative to the axis)")]
    for ax, (ylab, fn, title) in zip(axes, panels):
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for col, (name, c) in zip(COLORS, curves.items()):
            ax.plot(np.array(c.dV) * 1e6, fn(c), color=col, linewidth=2, marker="o", markersize=4, label=name)
        ax.set_xlabel("chamber L volume growth, ΔV [ml]")
        ax.set_ylabel(ylab)
        ax.set_title(title, loc="left")
    axes[0].axhline(TARGET_DEG, color=INK2, linewidth=1, linestyle="--")
    axes[0].annotate("target 15°", (0, TARGET_DEG), textcoords="offset points", xytext=(4, 4), color=INK2, fontsize=9)
    axes[1].axhline(P_MAX / 1e3, color=INK2, linewidth=1, linestyle="--")
    axes[1].annotate("p_max 50 kPa", (0, P_MAX / 1e3), textcoords="offset points", xytext=(4, -12),
                     color=INK2, fontsize=9)
    axes[0].legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.suptitle("Stage 2a – design variants (coarse, quasi-static, chamber R vented, no weight)",
                 x=0.01, ha="left", color=INK, fontsize=11)
    fig.savefig(os.path.join(RESULTS, "s2_variants.png"), dpi=150, facecolor="white")


def plot_from_csv():
    # The curves are the "# name,dV_ml,p_kPa,theta_deg,bulge_mm" lines below the summary table.
    curves = {}
    with open(os.path.join(RESULTS, "s2_variants.csv")) as f:
        for line in f:
            if not line.startswith("# ") or line.startswith("# curves:"):
                continue
            name, dv, p, theta, bulge = line[2:].rstrip("\n").rsplit(",", 4)
            c = curves.setdefault(name, SimpleNamespace(dV=[], p=[], tip_angle=[], bulge=[]))
            c.dV.append(float(dv) * 1e-6)
            c.p.append(float(p) * 1e3)
            c.tip_angle.append(np.radians(float(theta)))
            c.bulge.append(float(bulge) * 1e-3)
    for c in curves.values():
        c.tip_angle = np.array(c.tip_angle)
    plot(curves)


if __name__ == "__main__":
    if "--plot-only" in sys.argv:
        plot_from_csv()
    else:
        main()
