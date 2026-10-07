"""Stage 5: tail in water – comparison with air, tethered thrust.

Usage:  source scripts/env.sh && python scripts/run_stage5.py   (~25 min, 3 simulations at once)
        python scripts/run_stage5.py --plot-only                (only the plot from CSV)

The same run as stage 4 (coarse mesh, 1 s prefill, 2 Hz rhythm with a 1 s ramp, 4.5 s),
but environment="water": apparent weight of the silicone, weightless water in the chambers,
water drag on the skin (fishsofa/water.py). Three simulations, run in parallel
(fishsofa/parallel.py):
  - air, dt = 1 ms        (reference; at 2 ms the 5% difference is numerical damping, stage 4),
  - water, dt = 1 ms      (explicit drag: at 2 ms max(c·dt/m) ≈ 0.7 > 0.5 on the fin),
  - water, dt = 0.5 ms    (check: whether the water result is independent of dt).

Results in results/: s5_water_vs_air.png, s5_water_vs_air.csv, s5_summary.txt.
"""
import csv
import os
import sys
from dataclasses import replace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fishsofa import PROJECT_DIR, headless, parallel  # noqa: E402
from fishsofa.config import TailConfig  # noqa: E402

LEVEL = "coarse"
T_END = 4.5
RESULTS = os.path.join(PROJECT_DIR, "results")
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"   # dataviz palette, fixed order
COLS = ("t", "V_ref", "V_p", "p_L", "p_R", "theta", "F_x", "F_y", "drag_power", "stability")
RUNS = {  # key: (environment, dt)
    "air_1ms": ("air", 0.001),
    "water_1ms": ("water", 0.001),
    "water_0.5ms": ("water", 0.0005),
}


def main():
    os.makedirs(RESULTS, exist_ok=True)
    base = TailConfig()
    jobs = {k: dict(cfg=replace(base, environment=env, dt=dt), level=LEVEL, t_end=T_END)
            for k, (env, dt) in RUNS.items()}
    runs = parallel.run_all(headless.run_flapping, jobs, label="Stage 5: ")
    with open(os.path.join(RESULTS, "s5_water_vs_air.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run"] + list(COLS))
        for key in RUNS:
            L = runs[key].log
            for i in range(len(L["t"])):
                w.writerow([key] + [f"{L[c][i]:.9g}" if c in L else "" for c in COLS])
    txt = summary({k: (runs[k].log, runs[k].ms_per_step, runs[k].dt) for k in RUNS}, base)
    print("\n" + txt)
    with open(os.path.join(RESULTS, "s5_summary.txt"), "w") as f:
        f.write(txt + "\n")
    plot({k: runs[k].log for k in RUNS}, base)


def steady_metrics(L: dict, cfg: TailConfig) -> dict:
    """Amplitude and phase (headless.cycle_metrics) + thrust = mean F_x over the last 2 cycles."""
    c = headless.cycle_metrics(L, cfg)
    T = 1.0 / cfg.tail_freq
    t0 = cfg.prefill_time + cfg.ramp_time
    n_cyc = int((L["t"][-1] - t0) // T)
    m = (L["t"] >= t0 + (n_cyc - 2) * T) & (L["t"] < t0 + n_cyc * T)
    out = {"amp_deg": np.degrees(c["amplitude_per_cycle"][-1]), "phase_deg": c.get("phase_lag_deg", np.nan),
           "steady_change": c.get("steady_change", np.nan),
           "amps_deg": [np.degrees(a) for a in c["amplitude_per_cycle"]],
           "dp_max_kPa": np.abs(L["p_L"][m] - L["p_R"][m]).max() / 1e3}
    if "F_x" in L:
        out["thrust_mN"] = 1e3 * L["F_x"][m].mean()
        out["Fy_amp_mN"] = 1e3 * 0.5 * (L["F_y"][m].max() - L["F_y"][m].min())
        out["drag_power_mW"] = 1e3 * L["drag_power"][m].mean()
        out["stability_max"] = float(np.nanmax(L["stability"]))
    return out


def summary(runs: dict, cfg: TailConfig) -> str:
    lines = ["Stage 5 – water vs air (coarse, V4, antagonistic system, same V_ref rhythm)",
             f"f = {cfg.tail_freq} Hz, A_V = {cfg.tail_volume_amp * 1e6:g} ml, V_prefill = {cfg.V_prefill * 1e6:g} ml, "
             f"C_n = {cfg.drag_C_n}, C_t = {cfg.drag_C_t} (PLACEHOLDER)", ""]
    met = {}
    for key, (L, ms, dt) in runs.items():
        m = met[key] = steady_metrics(L, cfg)
        lines += [f"{key}: {ms:.0f} ms/step = {ms / (dt * 1e3):.0f}× slower than real time",
                  "  θ amplitude in successive cycles [°]: " + ", ".join(f"{a:.2f}" for a in m["amps_deg"]),
                  f"  steady cycle: ±{m['amp_deg']:.2f}°, change in the last cycle {100 * m['steady_change']:.2f}%, "
                  f"phase lag relative to −V_ref {m['phase_deg']:.1f}°, |Δp| max {m['dp_max_kPa']:.1f} kPa"]
        if "thrust_mN" in m:
            lines += [f"  thrust (mean F_x, last 2 cycles): {m['thrust_mN']:+.2f} mN; lateral force ±{m['Fy_amp_mN']:.0f} mN; "
                      f"mean drag power {m['drag_power_mW']:.0f} mW",
                      f"  explicit drag stability: max(c·dt/m) = {m['stability_max']:.3f} (required < 0.5)"]
        lines.append("")
    a, w, w2 = met["air_1ms"], met["water_1ms"], met["water_0.5ms"]
    lines += [f"water/air: amplitude {w['amp_deg'] / a['amp_deg']:.2f}×, phase {w['phase_deg'] - a['phase_deg']:+.1f}°",
              f"water, dt 1 ms vs 0.5 ms: amplitude {100 * (w['amp_deg'] / w2['amp_deg'] - 1):+.2f}%, "
              f"thrust {100 * (w['thrust_mN'] / w2['thrust_mN'] - 1):+.1f}%"]
    return "\n".join(lines)


def _style(ax):
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def plot(logs: dict, cfg: TailConfig):
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK})
    A, W, W2 = logs["air_1ms"], logs["water_1ms"], logs["water_0.5ms"]
    fig, axes = plt.subplots(4, 1, figsize=(10, 10.5), sharex=True, constrained_layout=True)
    for ax in axes:
        _style(ax)
        ax.axvspan(0, cfg.prefill_time, color=GRID, alpha=0.5, linewidth=0)
    a, b, c, d = axes

    a.plot(A["t"], np.degrees(A["theta"]), color=ORANGE, linewidth=2, label="air")
    a.plot(W["t"], np.degrees(W["theta"]), color=BLUE, linewidth=2, label="water")
    a.plot(W2["t"], np.degrees(W2["theta"]), color=INK2, linewidth=1, linestyle="--", label="water, dt/2")
    a.set_ylabel("tip angle θ [°]")
    a.set_title("Tip angle for the same volume rhythm V_ref", loc="left", fontsize=10)
    a.legend(frameon=False, labelcolor=INK, loc="upper left", ncol=3)

    b.plot(A["t"], (A["p_L"] - A["p_R"]) / 1e3, color=ORANGE, linewidth=2, label="air")
    b.plot(W["t"], (W["p_L"] - W["p_R"]) / 1e3, color=BLUE, linewidth=2, label="water")
    b.set_ylabel("Δp = p_L − p_R [kPa]")
    b.set_title("Pressure difference: almost unchanged in water (Δp is set mainly by tail stiffness, not drag)", loc="left", fontsize=10)
    b.legend(frameon=False, labelcolor=INK, loc="upper left", ncol=2)

    T = 1.0 / cfg.tail_freq
    t0 = cfg.prefill_time + cfg.ramp_time
    c.plot(W["t"], 1e3 * W["F_y"], color=GREEN, linewidth=1.2, label="F_y (lateral)")
    c.plot(W["t"], 1e3 * W["F_x"], color=BLUE, linewidth=2, label="F_x (thrust > 0)")
    m = W["t"] >= t0
    # Moving average of F_x over one cycle – the thrust itself is small vs the lateral force.
    n = int(round(T / (W["t"][1] - W["t"][0])))
    fx_avg = np.convolve(W["F_x"], np.ones(n) / n, mode="same")
    c.plot(W["t"][m][n // 2:-n // 2], 1e3 * fx_avg[m][n // 2:-n // 2], color=INK, linewidth=1.5,
           linestyle="--", label="F_x cycle average")
    c.set_ylabel("water force on the tail [mN]")
    c.set_title("Water drag forces (local model, no added mass – thrust is only qualitative)", loc="left", fontsize=10)
    c.legend(frameon=False, labelcolor=INK, loc="upper left", ncol=3)

    d.plot(W["t"], W["stability"], color=BLUE, linewidth=1.5, label="dt = 1 ms")
    d.plot(W2["t"], W2["stability"], color=INK2, linewidth=1, linestyle="--", label="dt = 0.5 ms")
    d.axhline(0.5, color=ORANGE, linewidth=1.5)
    d.text(W["t"][-1], 0.5, "limit 0.5 ", color=ORANGE, va="bottom", ha="right", fontsize=9)
    d.set_ylabel("max(c·dt/m)")
    d.set_xlabel("time [s]")
    d.set_title("Stability of the explicitly computed drag (worst node, usually on the fin)", loc="left", fontsize=10)
    d.legend(frameon=False, labelcolor=INK, loc="center left", ncol=2)

    fig.suptitle(f"Stage 5 – water vs air: f = {cfg.tail_freq:g} Hz, A_V = {cfg.tail_volume_amp * 1e6:g} ml, "
                 f"C_n = {cfg.drag_C_n:g}, C_t = {cfg.drag_C_t:g} (PLACEHOLDER)\nmesh {LEVEL}, V4, "
                 f"E = {cfg.young_modulus:.0e} Pa (PLACEHOLDER)", x=0.01, ha="left", color=INK, fontsize=11)
    fig.savefig(os.path.join(RESULTS, "s5_water_vs_air.png"), dpi=150, facecolor="white")
    plt.close(fig)


def load_csv() -> dict:
    logs = {}
    with open(os.path.join(RESULTS, "s5_water_vs_air.csv")) as f:
        for row in csv.DictReader(f):
            d = logs.setdefault(row["run"], {k: [] for k in COLS})
            for k in COLS:
                d[k].append(float(row[k]) if row[k] != "" else np.nan)
    return {r: {k: np.array(v) for k, v in d.items()} for r, d in logs.items()}


if __name__ == "__main__":
    if "--plot-only" in sys.argv:
        plot(load_csv(), TailConfig())
    else:
        main()
