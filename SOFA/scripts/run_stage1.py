"""Stage 1: meshes at 3 levels, quality report, tail sag under its own weight.

Usage:  source scripts/env.sh && python scripts/run_stage1.py   (~10–20 min, mostly the fine mesh)
        python scripts/run_stage1.py --plot-only                (only the plot from CSV)

Results in results/:
  s1_mesh_report.txt – mesh quality, step time, static sag at each level,
  s1_sag.csv         – static sag vs element count (a first look at convergence),
  s1_dynamic.csv     – tip motion over time after "releasing" the tail (coarse mesh),
  s1_sag.png         – both plots.

Physics: tail in air (environment="air"), chambers full of water, no actuation.
The tail is a cantilever clamped at x = 0, so it sags in −Z. A coarser mesh is
stiffer (too few elements across the wall thickness -> locking), so the sag should
grow with refinement and approach a limit.
"""
import csv
import os
import sys
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fishsofa import PROJECT_DIR, headless, mesh_gen  # noqa: E402
from fishsofa.config import TailConfig  # noqa: E402

LEVELS = ["coarse", "medium", "fine"]
RESULTS = os.path.join(PROJECT_DIR, "results")

# Colors and ink (reference palette of the dataviz skill, light mode).
INK, INK2, GRID, SERIES1 = "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6"


def main():
    os.makedirs(RESULTS, exist_ok=True)
    cfg = TailConfig()
    rows, lines = [], []
    for lv in LEVELS:
        print(f"[{lv}] mesh...", flush=True)
        mesh_gen.ensure(cfg, lv)
        mesh = mesh_gen.load(cfg, lv)
        rep = mesh_gen.quality_report(mesh, cfg)

        print(f"[{lv}] statics...", flush=True)
        t0 = time.perf_counter()
        st = headless.static_sag(cfg, lv)
        t_static = time.perf_counter() - t0

        print(f"[{lv}] dynamics step time...", flush=True)
        dy = headless.run(cfg, lv, n_steps=10)

        tip = st.tip[-1]
        rows.append({"level": lv, "n_tets": rep["n_tets"], "n_nodes": rep["n_nodes"],
                     "elements_across_wall": rep["elements_across_wall"],
                     "tip_dz_mm": tip[2] * 1e3, "tip_dx_mm": tip[0] * 1e3,
                     "static_s": t_static, "dynamic_ms_per_step": dy.ms_per_step,
                     "realtime_factor": dy.ms_per_step / (cfg.dt * 1e3)})
        lines += [mesh_gen.format_report(rep),
                  f"  static tip sag (fin centroid): Δz = {tip[2] * 1e3:.2f} mm, "
                  f"Δx = {tip[0] * 1e3:.2f} mm (StaticSolver, {t_static:.1f} s)",
                  f"  dynamics: {dy.ms_per_step:.0f} ms/step at dt = {cfg.dt * 1e3:.0f} ms "
                  f"-> {rows[-1]['realtime_factor']:.0f}× slower than real time", ""]
        print(lines[-4], lines[-3], lines[-2], sep="\n", flush=True)

    # Dynamics on coarse: tail "released" at t = 0 (weight applied as a step).
    print("[coarse] dynamics 0.4 s...", flush=True)
    dyn = headless.run(cfg, "coarse", n_steps=200)
    tz = np.array([p[2] for p in dyn.tip]) * 1e3
    lines.append(f"[coarse] dynamics 200 steps: NaN = {dyn.has_nan}, max node displacement = "
                 f"{max(dyn.max_disp) * 1e3:.1f} mm (tail length {cfg.tail_length * 1e3:.0f} mm)")

    with open(os.path.join(RESULTS, "s1_sag.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(RESULTS, "s1_dynamic.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "tip_dz_mm", "max_disp_mm"])
        for t, z, m in zip(dyn.t, tz, dyn.max_disp):
            w.writerow([f"{t:.4f}", f"{z:.4f}", f"{m * 1e3:.4f}"])
    header = ("Stage 1 – tail meshes and sag under its own weight (air, chambers full of water)\n"
              f"E = {cfg.young_modulus:.0e} Pa, ν = {cfg.poisson_ratio}, ρ = {cfg.rho_silicone} kg/m³ "
              "(all PLACEHOLDER)\n"
              "'elem. across wall' = thickness / mean tetra edge near the cavity (approximation)\n\n")
    with open(os.path.join(RESULTS, "s1_mesh_report.txt"), "w") as f:
        f.write(header + "\n".join(lines) + "\n")

    plot(rows, dyn.t, tz, cfg)
    print("\n".join(lines[-1:]))
    print(f"-> {RESULTS}")


def plot(rows, t, tz, cfg):
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK})
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    for ax in (a, b):
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    n = [r["n_tets"] for r in rows]
    dz = [r["tip_dz_mm"] for r in rows]
    a.plot(n, dz, color=SERIES1, linewidth=2, marker="o", markersize=8,
           markeredgecolor="white", markeredgewidth=2)
    for r in rows:
        a.annotate(f"{r['level']}\n{r['tip_dz_mm']:.1f} mm", (r["n_tets"], r["tip_dz_mm"]),
                   textcoords="offset points", xytext=(0, 10), ha="center", color=INK2, fontsize=9)
    a.set_xscale("log")
    a.set_xlabel("number of tetrahedra")
    a.set_ylabel("tip deflection Δz [mm]")
    a.set_title("Static sag under weight vs mesh density", loc="left")
    lo = min(dz)
    a.set_ylim(lo * 1.25, 0)

    b.plot(t, tz, color=SERIES1, linewidth=2)
    static_coarse = rows[0]["tip_dz_mm"]
    b.axhline(static_coarse, color=INK2, linewidth=1, linestyle="--")
    b.annotate(f"static equilibrium ({static_coarse:.1f} mm)", (t[-1], static_coarse),
               textcoords="offset points", xytext=(-4, 6), ha="right", color=INK2, fontsize=9)
    b.set_xlabel("time [s]")
    b.set_ylabel("tip deflection Δz [mm]")
    b.set_title("Coarse: motion after releasing the tail (t = 0)", loc="left")
    fig.suptitle(f"Stage 1 – tail in air, E = {cfg.young_modulus:.0e} Pa (placeholder)",
                 x=0.01, ha="left", color=INK, fontsize=11)
    fig.savefig(os.path.join(RESULTS, "s1_sag.png"), dpi=150, facecolor="white")


def plot_from_csv():
    with open(os.path.join(RESULTS, "s1_sag.csv")) as f:
        rows = [{"level": r["level"], "n_tets": int(r["n_tets"]), "tip_dz_mm": float(r["tip_dz_mm"])}
                for r in csv.DictReader(f)]
    with open(os.path.join(RESULTS, "s1_dynamic.csv")) as f:
        dyn = list(csv.DictReader(f))
    t = [float(r["t_s"]) for r in dyn]
    tz = np.array([float(r["tip_dz_mm"]) for r in dyn])
    plot(rows, t, tz, TailConfig())


if __name__ == "__main__":
    if "--plot-only" in sys.argv:
        plot_from_csv()
    else:
        main()
