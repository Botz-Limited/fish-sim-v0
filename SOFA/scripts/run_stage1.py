"""Etap 1: siatki 3 poziomów, raport jakości, ugięcie ogona pod własnym ciężarem.

Uruchomienie:  source scripts/env.sh && python scripts/run_stage1.py   (~10–20 min, głównie siatka fine)

Wyniki w results/:
  s1_mesh_report.txt – jakość siatek, czas kroku, ugięcie statyczne na każdym poziomie,
  s1_sag.csv         – ugięcie statyczne vs liczba elementów (pierwszy obraz zbieżności),
  s1_dynamic.csv     – ruch końcówki w czasie po „puszczeniu” ogona (siatka coarse),
  s1_sag.png         – oba wykresy.

Fizyka: ogon w powietrzu (environment="air"), komory pełne wody, brak aktuacji.
Ogon to wspornik utwierdzony w x = 0, więc ugina się w −Z. Grubsza siatka jest
sztywniejsza (za mało elementów na grubość ścianek -> locking), więc ugięcie powinno
rosnąć przy zagęszczaniu i zbliżać się do granicy.
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

# Kolory i tusz (paleta referencyjna skilla dataviz, tryb jasny).
INK, INK2, GRID, SERIES1 = "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6"


def main():
    os.makedirs(RESULTS, exist_ok=True)
    cfg = TailConfig()
    rows, lines = [], []
    for lv in LEVELS:
        print(f"[{lv}] siatka...", flush=True)
        mesh_gen.ensure(cfg, lv)
        mesh = mesh_gen.load(cfg, lv)
        rep = mesh_gen.quality_report(mesh, cfg)

        print(f"[{lv}] statyka...", flush=True)
        t0 = time.perf_counter()
        st = headless.static_sag(cfg, lv)
        t_static = time.perf_counter() - t0

        print(f"[{lv}] czas kroku dynamiki...", flush=True)
        dy = headless.run(cfg, lv, n_steps=10)

        tip = st.tip[-1]
        rows.append({"level": lv, "n_tets": rep["n_tets"], "n_nodes": rep["n_nodes"],
                     "elements_across_wall": rep["elements_across_wall"],
                     "tip_dz_mm": tip[2] * 1e3, "tip_dx_mm": tip[0] * 1e3,
                     "static_s": t_static, "dynamic_ms_per_step": dy.ms_per_step,
                     "realtime_factor": dy.ms_per_step / (cfg.dt * 1e3)})
        lines += [mesh_gen.format_report(rep),
                  f"  ugięcie statyczne końcówki (centroid płetwy): Δz = {tip[2] * 1e3:.2f} mm, "
                  f"Δx = {tip[0] * 1e3:.2f} mm (StaticSolver, {t_static:.1f} s)",
                  f"  dynamika: {dy.ms_per_step:.0f} ms/krok przy dt = {cfg.dt * 1e3:.0f} ms "
                  f"-> {rows[-1]['realtime_factor']:.0f}× wolniej niż czas rzeczywisty", ""]
        print(lines[-4], lines[-3], lines[-2], sep="\n", flush=True)

    # Dynamika na coarse: ogon „puszczony” w t = 0 (ciężar włączony skokowo).
    print("[coarse] dynamika 0.4 s...", flush=True)
    dyn = headless.run(cfg, "coarse", n_steps=200)
    tz = np.array([p[2] for p in dyn.tip]) * 1e3
    lines.append(f"[coarse] dynamika 200 kroków: NaN = {dyn.has_nan}, max przemieszczenie węzła = "
                 f"{max(dyn.max_disp) * 1e3:.1f} mm (długość ogona {cfg.tail_length * 1e3:.0f} mm)")

    with open(os.path.join(RESULTS, "s1_sag.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(RESULTS, "s1_dynamic.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "tip_dz_mm", "max_disp_mm"])
        for t, z, m in zip(dyn.t, tz, dyn.max_disp):
            w.writerow([f"{t:.4f}", f"{z:.4f}", f"{m * 1e3:.4f}"])
    header = ("Etap 1 – siatki ogona i ugięcie pod własnym ciężarem (powietrze, komory pełne wody)\n"
              f"E = {cfg.young_modulus:.0e} Pa, ν = {cfg.poisson_ratio}, ρ = {cfg.rho_silicone} kg/m³ "
              "(wszystko PLACEHOLDER)\n"
              "'elem. na ściankę' = grubość / średnia krawędź tetr przy wnęce (przybliżenie)\n\n")
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
    a.set_xlabel("liczba czworościanów")
    a.set_ylabel("ugięcie końcówki Δz [mm]")
    a.set_title("Statyczne ugięcie pod ciężarem vs gęstość siatki", loc="left")
    lo = min(dz)
    a.set_ylim(lo * 1.25, 0)

    b.plot(t, tz, color=SERIES1, linewidth=2)
    static_coarse = rows[0]["tip_dz_mm"]
    b.axhline(static_coarse, color=INK2, linewidth=1, linestyle="--")
    b.annotate(f"równowaga statyczna ({static_coarse:.1f} mm)", (t[-1], static_coarse),
               textcoords="offset points", xytext=(-4, 6), ha="right", color=INK2, fontsize=9)
    b.set_xlabel("czas [s]")
    b.set_ylabel("ugięcie końcówki Δz [mm]")
    b.set_title("Coarse: ruch po puszczeniu ogona (t = 0)", loc="left")
    fig.suptitle(f"Etap 1 – ogon w powietrzu, E = {cfg.young_modulus:.0e} Pa (placeholder)",
                 x=0.01, ha="left", color=INK, fontsize=11)
    fig.savefig(os.path.join(RESULTS, "s1_sag.png"), dpi=150, facecolor="white")


if __name__ == "__main__":
    main()
