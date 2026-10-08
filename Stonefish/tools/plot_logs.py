#!/usr/bin/env python3
"""CSV logs (results/logs/) -> PNG plots + plotted data (CSV) in results/.

    .venv/bin/python tools/plot_logs.py

Each plot has a CSV file next to it with exactly the data drawn on it
(the full logs are large and do not go into git). At the end it prints a numerical summary
(these numbers are in the README).

NED frame: z = depth (+ down), y = to the right. On the XY plots the world X axis ("north")
is vertical and Y ("east") horizontal – as on a map.
"""

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fishcfg import ROOT, load_config  # noqa: E402
from fishlog import read_log  # noqa: E402

LOGS = ROOT / "results" / "logs"
OUT = ROOT / "results"

# Categorical palette (fixed order, not cycled) and auxiliary colours.
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, INK2, GRID, NEUTRAL = "#1f1f1e", "#5f5e58", "#e6e5df", "#8a8980"

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 130, "font.size": 9.5,
    "axes.edgecolor": NEUTRAL, "axes.labelcolor": INK, "axes.titlecolor": INK,
    "axes.titlesize": 10.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": INK2, "ytick.color": INK2, "lines.linewidth": 1.6,
    "legend.frameon": False, "legend.fontsize": 8.5,
})


def log(name):
    return read_log(LOGS / f"{name}.csv")


def save(fig, name, rows, header):
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight")
    plt.close(fig)
    with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow([f"{v:.6g}" if isinstance(v, float) else v for v in r])
    print(f"  results/{name}.png (+ .csv)")


def cycle_mean(t, y, period):
    """Moving average over one tail-beat period – removes the 2f oscillation from the speed."""
    dt = t[1] - t[0]
    n = max(1, int(round(period / dt)))
    k = np.ones(n) / n
    out = np.convolve(y, k, mode="same")
    h = n // 2
    out[:h] = np.nan            # at the edges the window extends past the data – not drawn
    out[len(out) - h:] = np.nan
    return out


def mean_speed(d, last=5.0):
    m = d.t > d.t[-1] - last
    return float(np.hypot(d.x[m][-1] - d.x[m][0], d.y[m][-1] - d.y[m][0]) / (d.t[m][-1] - d.t[m][0]))


def mean_fwd(d, last=10.0):
    """Signed mean speed ALONG the head axis (negative = fish swims backwards)."""
    m = d.t > d.t[-1] - last
    return float(np.mean(d.v_fwd[m]))


def harmonic_amp(t, y, f):
    """Amplitude of the component at frequency f (first harmonic)."""
    return float(abs(2 * np.mean((y - y.mean()) * np.exp(-2j * np.pi * f * t))))


SUMMARY = {}


# ------------------------------------------------------------------ scenario 1
def plot_s1():
    d = log("s1_hover")
    z0 = d.z[0]
    m5 = d.t <= 5.0
    dz5 = float(abs(d.z[m5][-1] - z0))
    SUMMARY["s1_dz_5s_mm"] = dz5 * 1e3
    SUMMARY["s1_dz_10s_mm"] = float(abs(d.z[-1] - z0) * 1e3)
    SUMMARY["s1_drift_xy_10s_mm"] = float(np.hypot(d.x[-1] - d.x[0], d.y[-1] - d.y[0]) * 1e3)

    fig, ax = plt.subplots(2, 1, figsize=(7.5, 5.2), sharex=True)
    ax[0].plot(d.t, (d.depth_meas - z0) * 1e3, color=C[0], lw=0.7, alpha=0.45, label="pressure sensor (noisy)")
    ax[0].plot(d.t, (d.z - z0) * 1e3, color=C[0], lw=2, label="true depth")
    ax[0].set_ylabel("Δz [mm] (+ down)")
    ax[0].set_title("Hover without propulsion: the fish stays in place (VBS at half range)")
    ax[0].legend(loc="upper right")
    ax[1].plot(d.t, (d.x - d.x[0]) * 1e3, color=C[1], label="x (forward)")
    ax[1].plot(d.t, (d.y - d.y[0]) * 1e3, color=C[2], label="y (right)")
    ax[1].set_ylabel("horizontal drift [mm]")
    ax[1].set_xlabel("time [s]")
    ax[1].legend(loc="upper right")
    save(fig, "s1_hover_drift", zip(d.t, d.z, d.depth_meas, d.x, d.y), ["t_s", "z_true_m", "depth_meas_m", "x_m", "y_m"])

    d = log("s1_righting")
    m = d.t <= 10.0
    roll = np.degrees(d.roll)
    i5 = np.argmin(abs(d.t - 5.0))
    SUMMARY["s1_roll_start_deg"] = float(roll[0])
    SUMMARY["s1_roll_5s_deg"] = float(abs(roll[i5]))
    env = [float(np.abs(roll[(d.t >= t) & (d.t < t + 1)]).max()) for t in range(int(d.t[-1]))]
    SUMMARY["s1_roll_envelope_deg_per_s"] = env
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ax.plot(d.t[m], np.degrees(d.imu_roll[m]), color=C[0], lw=0.8, alpha=0.5, label="IMU (noisy)")
    ax.plot(d.t[m], roll[m], color=C[0], lw=2, label="true roll")
    ax.plot(d.t[m], np.degrees(d.pitch[m]), color=C[1], label="true pitch")
    ax.axhline(0, color=NEUTRAL, lw=1)
    ax.set_xlabel("time [s]")
    ax.set_ylabel("angle [°]")
    ax.set_title("Start with 30° roll: righting moment acts immediately, but roll damping is weak")
    ax.legend(loc="upper right")
    save(fig, "s1_righting", zip(d.t[m], roll[m], np.degrees(d.imu_roll[m]), np.degrees(d.pitch[m])),
         ["t_s", "roll_true_deg", "roll_imu_deg", "pitch_true_deg"])


# ------------------------------------------------------------------ scenario 2
S2 = [("s2_swim", "default: fin lift + Blasius friction"),
      ("s2_swim_nolift", "no lift (Blasius friction)"),
      ("s2_swim_libfriction", "lift + library friction"),
      ("s2_swim_libfriction_nolift", "Stonefish only (no lift, library friction)"),
      ("s2_swim_locked", "tail locked")]


def plot_s2():
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.5, 1]})
    rows = []
    speeds = {}
    for i, (name, label) in enumerate(S2):
        d = log(name)
        v = cycle_mean(d.t, d.v_fwd, 0.5) * 100
        speeds[name] = mean_speed(d)
        ax[0].plot(d.t, v, color=C[i], label=f"{label}: {speeds[name] * 100:.1f} cm/s")
        rows += [(name, t, vv) for t, vv in zip(d.t[::10], v[::10]) if np.isfinite(vv)]
    SUMMARY["s2_speed_cm_s"] = {k: v * 100 for k, v in speeds.items()}
    ax[0].axhline(0, color=NEUTRAL, lw=1)
    ax[0].set_xlabel("time [s]")
    ax[0].set_ylabel("forward speed [cm/s]\n(tail-beat period average)")
    ax[0].set_title("CPG 2 Hz: where the thrust comes from")
    ax[0].legend(loc="upper left", fontsize=8)

    # force balance in steady motion (default variant)
    d = log("s2_swim")
    m = d.t > d.t[-1] - 5
    comp = [("fin lift", d.fin_thrust[m].mean()), ("head pressure drag", d.Fdrag_head[m].mean()),
            ("segment pressure drag", d.Fdrag_tail[m].mean()), ("fin pressure drag", d.Fdrag_fin[m].mean()),
            ("skin friction (all)", d.Fskin_all[m].mean())]
    SUMMARY["s2_force_balance_N"] = {k: float(v) for k, v in comp}
    names = [c[0] for c in comp][::-1]
    vals = [c[1] for c in comp][::-1]
    ax[1].barh(names, vals, color=[C[0] if v > 0 else NEUTRAL for v in vals], height=0.6)
    for y, v in enumerate(vals):
        ax[1].text(max(v, 0) + 0.015, y, f"{v:+.3f} N", va="center", ha="left", color=INK2, fontsize=8.5)
    ax[1].axvline(0, color=INK2, lw=1)
    ax[1].set_xlim(-0.4, 0.75)
    ax[1].set_xlabel("mean force along the fish axis [N] (+ = forward)")
    ax[1].set_title("Force balance, steady motion (default)")
    ax[1].grid(axis="y", visible=False)
    save(fig, "s2_speed_vs_locked", rows, ["variant", "t_s", "v_fwd_cycle_mean_cm_s"])


# ------------------------------------------------------------------ scenario 3
def plot_s3():
    from run_scenarios import TURN_BIASES_ML
    fig, ax = plt.subplots(figsize=(7, 6.4))
    # diverging: negative bias = blue, positive = orange, 0 = grey; lightness ~ |bias|
    blues = ["#86b6ef", "#3987e5", "#1c5cab"]
    oranges = ["#f4a37f", "#eb6834", "#b8461b"]
    rows, radii = [], {}
    for b in TURN_BIASES_ML:
        d = log(f"s3_turn_{b:+d}ml")
        col = NEUTRAL if b == 0 else (blues[abs(b) - 1] if b < 0 else oranges[abs(b) - 1])
        d["x"], d["y"] = d.x - d.x[0], d.y - d.y[0]          # relative to the start point
        ax.plot(d.y, d.x, color=col, lw=1.8)
        ax.annotate(f"{b:+d} ml", (d.y[-1], d.x[-1]), xytext=(4, 0), textcoords="offset points",
                    color=INK2, fontsize=8, va="center")
        m = d.t > 10
        if b != 0:
            x, y = d.x[m], d.y[m]
            A = np.c_[2 * x, 2 * y, np.ones_like(x)]
            c = np.linalg.lstsq(A, x * x + y * y, rcond=None)[0]
            radii[b] = float(np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2))
        rows += [(b, t, x, y) for t, x, y in zip(d.t[::20], d.x[::20], d.y[::20])]
    SUMMARY["s3_radius_m"] = radii
    ax.set_aspect("equal")
    ax.set_xlabel("y – right (east), from start [m]")
    ax.set_ylabel("x – forward (north), from start [m]")
    ax.set_title("Turning: V_bias bends the tail, the fish swims along an arc (30 s, CPG 2 Hz)")
    ax.text(0.02, 0.02, "V_bias > 0: tail bent left -> left turn\nradii (fitted circle): "
            + ", ".join(f"{b:+d} ml: {r:.1f} m" for b, r in sorted(radii.items())),
            transform=ax.transAxes, fontsize=8, color=INK2)
    save(fig, "s3_trajectory", rows, ["V_bias_ml", "t_s", "x_m", "y_m"])


# ------------------------------------------------------------------ scenario 4
def plot_s4():
    d = log("s4_depth")
    cfg = load_config(ROOT / "config" / "s4_depth.json")
    vmin, vmax = cfg["vbs"]["v_min"] * 1e6, cfg["vbs"]["v_max"] * 1e6
    sched = cfg["depth"]["schedule"] + [[d.t[-1] + 1, None]]
    seg = []
    for (t0, ref), (t1, _) in zip(sched[1:], sched[2:]):
        m = (d.t >= t0) & (d.t < t1)
        z, t = d.z[m], d.t[m]
        up = ref > z[0]
        over = (z.max() - ref) if up else (ref - z.min())
        out = np.abs(z - ref) > 0.05
        ts = float(t[np.where(out)[0][-1]] - t0) if out.any() else 0.0
        tail = t > t1 - 10
        seg.append(dict(step=f"{z[0]:.0f}->{ref:.0f} m", overshoot_cm=float(max(over, 0) * 100), t_settle_5cm_s=ts,
                        err_end_cm=float(abs(z[tail] - ref).mean() * 100),
                        err_meas_true_rms_cm=float(np.sqrt(np.mean((d.depth_filt[m] - z) ** 2)) * 100)))
    SUMMARY["s4"] = seg
    SUMMARY["s4_vbs_range_ml"] = [float(d.vbs_V.min() * 1e6), float(d.vbs_V.max() * 1e6)]

    fig, ax = plt.subplots(3, 1, figsize=(8.5, 8), sharex=True, gridspec_kw={"height_ratios": [1.5, 0.9, 1]})
    ax[0].plot(d.t, d.depth_meas, color=C[0], lw=0.6, alpha=0.35, label="pressure sensor (σ ≈ 5 mm)")
    ax[0].plot(d.t, d.depth_filt, color=C[1], lw=1.4, label="after 1 Hz filter (controller input)")
    ax[0].plot(d.t, d.z, color=C[0], lw=2, label="true depth")
    ax[0].step(d.t, d.depth_ref, where="post", color=INK, lw=1.2, ls="--", label="setpoint")
    ax[0].invert_yaxis()
    ax[0].set_ylabel("depth [m]")
    ax[0].set_title("Depth control: PID on the pressure sensor reading -> VBS")
    ax[0].legend(loc="upper right", fontsize=8)
    ax[1].plot(d.t, (d.depth_meas - d.z) * 100, color=C[0], lw=0.6, alpha=0.5, label="sensor − truth")
    ax[1].plot(d.t, (d.depth_filt - d.z) * 100, color=C[1], lw=1.4, label="filtered − truth (less noise, but lag)")
    ax[1].axhline(0, color=NEUTRAL, lw=1)
    ax[1].set_ylabel("depth measurement\nerror [cm]")
    ax[1].legend(loc="upper right", fontsize=8, ncol=2)
    ax[2].plot(d.t, d.vbs_Vref * 1e6, color=C[1], lw=1.2, label="V_ref (PID output)")
    ax[2].plot(d.t, d.vbs_V * 1e6, color=C[0], lw=2, label="water in VBS")
    for v in (vmin, vmax):
        ax[2].axhline(v, color=NEUTRAL, lw=1, ls=":")
    ax[2].text(d.t[-1], vmax, " full", va="center", color=INK2, fontsize=8)
    ax[2].text(d.t[-1], vmin, " empty", va="center", color=INK2, fontsize=8)
    ax[2].set_ylabel("volume [ml]\n(more = heavier)")
    ax[2].set_xlabel("time [s]")
    ax[2].legend(loc="upper right", fontsize=8, ncol=2)
    save(fig, "s4_depth_true_vs_measured", zip(d.t[::5], d.depth_ref[::5], d.z[::5], d.depth_meas[::5], d.depth_filt[::5],
                                                d.vbs_V[::5] * 1e6, d.vbs_Vref[::5] * 1e6),
         ["t_s", "depth_ref_m", "depth_true_m", "depth_meas_m", "depth_filt_m", "vbs_V_ml", "vbs_Vref_ml"])


# ------------------------------------------------------------------ scenario 5
def plot_s5():
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1, 1.4]})
    rows = []
    for i, (name, label) in enumerate([("s5_current", "no heading controller"),
                                       ("s5_current_heading", "heading controller (IMU -> V_bias)")]):
        d = log(name)
        ax[0].plot(d.y, d.x, color=C[i], lw=2, label=label)
        yaw = cycle_mean(d.t, np.degrees(np.unwrap(d.yaw)), 0.5)
        ax[1].plot(d.t, yaw, color=C[i], lw=2, label=label)
        m = d.t > 20
        SUMMARY[f"{name}_mean_yaw_deg"] = float(np.nanmean(yaw[m]))
        SUMMARY[f"{name}_y_drift_30s_m"] = float(d.y[-1])
        rows += [(name, t, x, y, w) for t, x, y, w in zip(d.t[::10], d.x[::10], d.y[::10], yaw[::10]) if np.isfinite(w)]
    ax[0].annotate("", xy=(0.95, 0.12), xytext=(0.75, 0.12), xycoords="axes fraction",
                   arrowprops=dict(arrowstyle="->", color=INK2, lw=1.5))
    ax[0].text(0.85, 0.15, "current 5 cm/s", transform=ax[0].transAxes, ha="center", color=INK2, fontsize=8)
    ax[0].set_aspect("equal", adjustable="datalim")
    ax[0].set_xlabel("y – right [m]")
    ax[0].set_ylabel("x – forward [m]")
    ax[0].set_title("Cross current: XY trajectory (30 s)")
    ax[0].legend(loc="upper left", fontsize=8)
    ax[1].axhline(0, color=NEUTRAL, lw=1)
    ax[1].set_xlabel("time [s]")
    ax[1].set_ylabel("heading (yaw) [°], period average")
    ax[1].set_title("Heading: without the controller the fish turns into the current")
    ax[1].legend(loc="lower left", fontsize=8)
    save(fig, "s5_current_drift", rows, ["variant", "t_s", "x_m", "y_m", "yaw_cycle_mean_deg"])


# ------------------------------------------------------------------ scenario 6
def plot_s6():
    from run_scenarios import SWEEP_FREQS
    cfg = load_config()
    h, r = cfg["hydraulics"], cfg["rhythm"]
    f_sat = h["Q_max"] / (2 * math.pi * r["volume_amp"])
    rows = []
    for f in SWEEP_FREQS:
        d = log(f"s6_sweep_{f:.2f}Hz")
        m = d.t > d.t[-1] - 10
        t = d.t[m]
        fin = d.theta1 + d.theta2 + d.theta3 + d.theta4 + d.theta5     # fin angle relative to the head
        early = (d.t >= 5) & (d.t < 15)
        yaw = np.degrees(np.unwrap(d.yaw))
        rows.append((f, mean_fwd(d) * 100, float(np.mean(d.v_fwd[early]) * 100), float(abs(yaw[m].mean())), math.degrees(harmonic_amp(t, fin[m], f)),
                     math.degrees(harmonic_amp(t, d.L[m], f)), float(np.mean(np.abs(d.u[m]) > 0.999) * 100)))
    rows = np.array(rows)
    SUMMARY["s6"] = {f"{r_[0]:.2f}Hz": dict(speed_cm_s=float(r_[1]), speed_5_15s_cm_s=float(r_[2]),
                                            heading_change_deg=float(r_[3]), fin_amp_deg=float(r_[4]),
                                            sat_pct=float(r_[6])) for r_ in rows}
    SUMMARY["s6_f_sat_Hz"] = f_sat
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.8))
    ax[0].plot(rows[:, 0], rows[:, 2], "o--", color=C[1], ms=5, lw=1.2, label="start (5–15 s)")
    ax[0].plot(rows[:, 0], rows[:, 1], "o-", color=C[0], ms=5, label="steady (50–60 s)")
    for r_ in rows:
        if r_[3] > 30:
            ax[0].annotate("turned back" if r_[3] > 150 else "turning back", (r_[0], r_[1]), xytext=(0, 8), textcoords="offset points",
                           ha="center", fontsize=7.5, color=INK2)
    ax[0].axhline(0, color=INK2, lw=1)
    ax[0].set_ylabel("speed along the head axis [cm/s]\n(< 0 = fish swims backwards)")
    ax[0].set_title("Speed")
    ax[0].legend(fontsize=8, loc="lower center")
    ax[1].plot(rows[:, 0], rows[:, 4], "o-", color=C[2], ms=5, label="fin relative to head (Σθ)")
    ax[1].plot(rows[:, 0], rows[:, 5], "o-", color=C[3], ms=5, label="\"tendon\" L = Σ w·θ")
    ax[1].set_ylabel("amplitude [°]")
    ax[1].set_title("Tail amplitude")
    ax[1].legend(fontsize=8)
    ax[2].plot(rows[:, 0], rows[:, 6], "o-", color=C[4], ms=5)
    ax[2].set_ylabel("time with |u| = 1 [%]")
    ax[2].set_title("Tail pump saturation")
    for a in ax:
        a.axvline(f_sat, color=NEUTRAL, lw=1.2, ls="--")
        a.set_xlabel("CPG frequency [Hz]")
    ax[0].text(f_sat, ax[0].get_ylim()[1], f" Q_max/(2π·A_V) = {f_sat:.2f} Hz", va="top", color=INK2, fontsize=8)
    fig.suptitle("Frequency sweep 0.5–3 Hz, 60 s per point (same commanded amplitude A_V = 8 ml)", x=0.01, ha="left",
                 fontweight="bold", color=INK)
    save(fig, "s6_freq_sweep", rows.tolist(), ["freq_Hz", "speed_50_60s_cm_s", "speed_5_15s_cm_s", "heading_change_deg", "fin_amp_deg", "L_amp_deg",
          "pump_saturated_pct"])


def summary_internal():
    d = log("t_internal")
    SUMMARY["t_internal"] = dict(com_drift_mm=float(np.hypot(np.ptp(d.com_x), np.ptp(d.com_y)) * 1e3),
                                 P_max=float(np.hypot(d.Px, d.Py).max()), Lz_max=float(abs(d.Lz).max()),
                                 head_yaw_amp_deg=float(np.degrees(np.ptp(d.yaw)) / 2))


def main():
    print("Plots:")
    for fn in (plot_s1, plot_s2, plot_s3, plot_s4, plot_s5, plot_s6, summary_internal):
        fn()
    (OUT / "summary.json").write_text(json.dumps(SUMMARY, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Summary: results/summary.json")
    print(json.dumps(SUMMARY, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
