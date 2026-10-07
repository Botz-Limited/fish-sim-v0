"""Runs the stage scenarios and saves PNG plots + CSV files to results/.

    python scripts/run_scenarios.py            # all stages
    python scripts/run_scenarios.py --stage 1  # stage 1 only

Independent runs are computed in parallel (processes, fishrod.perf.N_WORKERS).
"""

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import fishrod  # noqa: E402,F401  (performance settings before numpy/numba)
import numpy as np  # noqa: E402
from fishrod import scenarios as S  # noqa: E402
from fishrod.config import default_config  # noqa: E402
from fishrod.perf import N_WORKERS  # noqa: E402
from plotting import SERIES, THEORY, plt  # noqa: E402

RESULTS = ROOT / "results"


# ---------------------------------------------------------------- stage 1
STAGE1_N = (25, 50, 100)


def _arc(n):
    return n, S.cantilever_arc(S.coarse(default_config(), n), verbose=False)


def _vib(n):
    return n, S.cantilever_free_vibration(S.coarse(default_config(), n), verbose=False)


def stage1(pool):
    arcs = dict(pool.map(_arc, STAGE1_N))
    vibs = dict(pool.map(_vib, STAGE1_N))
    n_ref = STAGE1_N[-1]
    a, v = arcs[n_ref], vibs[n_ref]

    # --- arc vs theory + convergence
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.5, 1]})
    ax1.plot(a["x_th"], a["y_th"], "--", color=THEORY, label="theory: arc R = EI/M")
    for i, n in enumerate(STAGE1_N):
        r = arcs[n]
        ax1.plot(r["x"], r["y"], color=SERIES[i], lw=1.5, label=f"PyElastica, n = {n}")
    ax1.set_aspect("equal")
    ax1.set_xlabel("x [m]")
    ax1.set_ylabel("y [m]")
    ax1.set_title(f"Cantilever, tip moment M = {a['M']*1e3:.0f} mN·m")
    ax1.legend(loc="upper left")
    ns = np.array(STAGE1_N)
    tip = np.array([arcs[n]["tip_err"] for n in ns]) * 100
    frq = np.array([vibs[n]["freq_err"] for n in ns]) * 100
    ax2.loglog(ns, tip, "o-", color=SERIES[0], label="tip error (arc)")
    ax2.loglog(ns, frq, "s-", color=SERIES[1], label="ω₁ error")
    ax2.loglog(ns, 0.6 * tip[0] * ns[0] / ns, ":", color=THEORY, lw=1.2, label="slope 1/n")
    ax2.set_xlabel("number of elements n")
    ax2.set_ylabel("relative error [%]")
    ax2.set_title("Convergence with mesh density")
    ax2.legend()
    fig.savefig(RESULTS / "e1_cantilever_vs_theory.png")
    plt.close(fig)
    np.savetxt(RESULTS / "e1_cantilever_vs_theory.csv",
               np.column_stack([a["s"], a["x"], a["y"], a["x_th"], a["y_th"]]),
               delimiter=",", header="s,x,y,x_theory,y_theory", comments="")

    # --- free vibration vs theory + energy
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5.5), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})
    t = v["t"]
    amp = np.max(np.abs(v["y_tip"]))
    ax1.plot(t, v["y_tip"] * 1e3, color=SERIES[0], label=f"PyElastica, n = {n_ref}")
    ax1.plot(t, amp * np.sin(v["omega_th"] * t) * 1e3, "--", color=THEORY, lw=1.2,
             label="theory: sin(ω₁t)")
    ax1.set_ylabel("tip y [mm]")
    ax1.set_ylim(-1.3 * amp * 1e3, 1.8 * amp * 1e3)
    ax1.set_title(f"Cantilever free vibration: ω₁ = {v['omega_sim']:.3f} rad/s "
                  f"(theory {v['omega_th']:.3f}, error {v['freq_err']*100:.2f}%)")
    ax1.legend(loc="upper center", ncol=2)
    ax2.plot(t, (v["energy"] / v["E0"] - 1) * 100, color=SERIES[0])
    ax2.set_ylabel("ΔE / E₀ [%]")
    ax2.set_xlabel("time [s]")
    ax2.set_title(f"Energy without damping (max. deviation {v['energy_drift']*100:.4f}%)")
    fig.savefig(RESULTS / "e1_natural_freq.png")
    plt.close(fig)
    np.savetxt(RESULTS / "e1_natural_freq.csv",
               np.column_stack([t, v["y_tip"], v["energy"]]),
               delimiter=",", header="t,y_tip,energy", comments="")

    print("Stage 1:")
    print(f"  {'n':>4} {'dt [s]':>9} {'tip error':>14} {'shape error':>14} "
          f"{'ω₁ sim':>8} {'ω₁ err':>8} {'E drift':>8}")
    for n in STAGE1_N:
        r, q = arcs[n], vibs[n]
        print(f"  {n:4d} {r['dt']:9.2e} {r['tip_err']*100:13.3f}% {r['shape_err']*100:13.3f}% "
              f"{q['omega_sim']:8.4f} {q['freq_err']*100:7.2f}% {q['energy_drift']*100:7.4f}%")
    print(f"  ω₁ theory = {v['omega_th']:.4f} rad/s  (f₁ = {v['omega_th']/2/np.pi:.3f} Hz)")


# ---------------------------------------------------------------- stage 2
def _bend_p(dp):
    return S.static_bend_pressure(default_config(), dp)


def _bend_v(V):
    return S.static_bend_volume(default_config(), V)


def _vacuum(mode):
    return S.free_vacuum(default_config(), mode)


VACUUM_LABELS = {"rest_curvature": "κ_rest (internal), L_z ≡ 0",
                 "torque_pair": "torque pair ±M, L_z ≡ 0 (overlaps κ_rest)",
                 "single_torque": "single torque (WRONG)"}


def stage2(pool):
    cfg = default_config()
    s2 = cfg.stage2
    f_p = pool.map(_bend_p, s2.pressures)
    f_v = pool.map(_bend_v, s2.volumes)
    f_m = pool.map(_vacuum, VACUUM_LABELS)
    P, V, F = list(f_p), list(f_v), {r["actuation"]: r for r in f_m}

    # --- bending vs pressure
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2), gridspec_kw={"width_ratios": [1.4, 1, 1]})
    ax = axs[0]
    blues = plt.get_cmap("Blues")
    z0, z1 = cfg.fish.chamber_zone
    for i, r in enumerate(P):
        col = blues(0.35 + 0.6 * i / (len(P) - 1))
        ax.plot(r["x"], r["y"] * 1e3, color=col, lw=1.6, label=f"{r['dp']/1e3:.0f} kPa")
        ax.plot(r["x_th"], r["y_th"] * 1e3, "--", color=THEORY, lw=0.8)
    ax.axvspan(z0, z1, color="#f2f1ed", zorder=0)
    ax.text(0.5 * (z0 + z1), -78, "chamber\nzone", ha="center", va="bottom", color=THEORY, fontsize=9)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [mm]")
    ax.set_title("Shape (head clamped); theory – dashed")
    ax.legend(title="Δp", ncol=2, fontsize=8, loc="lower left")

    ax = axs[1]
    dp = np.array([r["dp"] for r in P]) / 1e3
    ax.plot(dp, [np.degrees(r["theta_th"]) for r in P], "--", color=THEORY, label="theory θ = A_r·Δp·Λ")
    ax.plot(dp, [np.degrees(r["theta"]) for r in P], "o", color=SERIES[0], ms=7, label="PyElastica")
    ax.set_xlabel("Δp = p_L − p_R [kPa]")
    ax.set_ylabel("chamber zone bend angle θ [°]")
    ax.set_title("Prescribed pressure")
    ax.legend()

    ax = axs[2]
    vp = np.array([r["V_p"] for r in V]) * 1e6
    ax.plot(vp, [r["dp_th"] / 1e3 for r in V], "--", color=THEORY,
            label="theory Δp = V_p/(C_h + A_r²Λ)")
    ax.plot(vp, [r["dp"] / 1e3 for r in V], "o", color=SERIES[1], ms=7, label="Δp (PyElastica + pump)")
    ax.set_xlabel("pumped volume V_p [ml]")
    ax.set_ylabel("Δp [kPa]")
    k = np.degrees(V[-1]["theta"]) / (V[-1]["V_p"] * 1e6)
    ax.set_title(f"Pump + rod coupling (θ ≈ {k:.1f}°/ml)")
    ax.legend(loc="upper left", fontsize=8)
    fig.savefig(RESULTS / "e2_bend_vs_pressure.png")
    plt.close(fig)
    np.savetxt(RESULTS / "e2_bend_vs_pressure.csv",
               np.array([[r["dp"], r["theta"], r["theta_th"], r["tip_y"], r["tip_y_th"]] for r in P]),
               delimiter=",", header="dp,theta,theta_theory,tip_y,tip_y_theory", comments="")
    np.savetxt(RESULTS / "e2_bend_vs_volume.csv",
               np.array([[r["V_p"], r["dp"], r["dp_th"], r["theta"], r["theta_th"]] for r in V]),
               delimiter=",", header="V_p,dp,dp_theory,theta,theta_theory", comments="")

    # --- internal actuation in vacuum
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2), gridspec_kw={"width_ratios": [1, 1, 1.3]})
    for i, (mode, lab) in enumerate(VACUUM_LABELS.items()):
        r = F[mode]
        axs[0].plot(r["t"], r["L"][:, 2] * 1e3, color=SERIES[i], lw=1.5, label=lab)
        axs[1].plot(r["t"], np.degrees(r["heading"]), color=SERIES[i], lw=1.5, label=lab)
    axs[0].set_xlabel("time [s]")
    axs[0].set_ylabel("angular momentum L_z [g·m²/s]")
    axs[0].set_title("Angular momentum of the whole fish")
    fig.legend(*axs[0].get_legend_handles_labels(), loc="lower center", ncol=3,
               bbox_to_anchor=(0.36, -0.07))
    axs[1].set_xlabel("time [s]")
    axs[1].set_ylabel("head heading [°]")
    axs[1].set_title("Head heading: recoil (±) vs drift (WRONG)")
    r = F["rest_curvature"]
    for k, snap in enumerate(r["snapshots"]):
        axs[2].plot(snap[0] * 1e3, snap[1] * 1e3, color=SERIES[0], lw=1.2,
                    alpha=0.35 + 0.65 * k / max(1, len(r["snapshots"]) - 1))
    xcm = np.max(np.linalg.norm(r["x_cm"], axis=1))
    axs[2].set_aspect("equal")
    axs[2].set_ylim(-70, 70)
    axs[2].set_xlabel("x [mm]")
    axs[2].set_ylabel("y [mm]")
    axs[2].set_title("Shapes over one period (κ_rest)")
    axs[2].text(0.02, 0.04, f"max |Δx center of mass| = {xcm:.0e} m", transform=axs[2].transAxes,
                fontsize=8, color=THEORY)
    fig.savefig(RESULTS / "e2_internal_actuation.png")
    plt.close(fig)
    np.savetxt(RESULTS / "e2_internal_actuation.csv",
               np.column_stack([F["rest_curvature"]["t"]] + [np.column_stack(
                   [F[m]["x_cm"][:, 0], F[m]["L"][:, 2], F[m]["heading"]]) for m in VACUUM_LABELS]),
               delimiter=",", comments="",
               header="t," + ",".join(f"{m}_dxcm,{m}_Lz,{m}_heading" for m in VACUUM_LABELS))

    print("Stage 2:")
    print(f"  {'Δp [kPa]':>9} {'θ sim [°]':>10} {'θ theory':>9} {'tip y [mm]':>13} {'theory':>8}")
    for r in P:
        print(f"  {r['dp']/1e3:9.0f} {np.degrees(r['theta']):10.3f} {np.degrees(r['theta_th']):9.3f} "
              f"{r['tip_y']*1e3:13.2f} {r['tip_y_th']*1e3:8.2f}")
    print(f"  {'V_p [ml]':>9} {'Δp sim [kPa]':>13} {'theory':>8} {'θ [°]':>7}")
    for r in V:
        print(f"  {r['V_p']*1e6:9.1f} {r['dp']/1e3:13.3f} {r['dp_th']/1e3:8.3f} {np.degrees(r['theta']):7.2f}")
    for m in VACUUM_LABELS:
        r = F[m]
        print(f"  vacuum, {m:15s} max|Δx_cm| = {np.max(np.linalg.norm(r['x_cm'], axis=1)):.1e} m, "
              f"max|L_z| = {np.max(np.abs(r['L'][:, 2])):.1e}, rotation = {np.degrees(r['heading'][-1]):+.2f}°, "
              f"θ amplitude = {np.degrees(np.max(np.abs(r['theta']))):.1f}°")


# ---------------------------------------------------------------- stage 3
MODEL_LABELS = {"none": "no water", "drag": "drag", "drag+reactive": "drag + reactive"}


def _tethered(model):
    return S.tethered(default_config(), model)


def stage3(pool):
    cfg = default_config()
    models = cfg.stage3.models
    R = {r["model"]: r for r in pool.map(_tethered, models)}
    f = cfg.hydraulics.tail_freq

    fig = plt.figure(figsize=(14, 7.5))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.15], hspace=0.3, wspace=0.28)
    lim = max(np.max(np.abs(sn[1])) for r in R.values() for sn in r["snapshots"]) * 1e3 * 1.15
    for i, m in enumerate(models):
        ax = fig.add_subplot(gs[0, i])
        sn = R[m]["snapshots"]
        for k, p in enumerate(sn):
            ax.plot(p[0] * 1e3, p[1] * 1e3, color=SERIES[i], lw=1.2,
                    alpha=0.3 + 0.7 * k / max(1, len(sn) - 1))
        ax.axvspan(0, cfg.fish.head_length * 1e3, color="#f2f1ed", zorder=0)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_title(f"{MODEL_LABELS[m]}: tip amplitude {R[m]['amp_tip']*1e3:.0f} mm")
        ax.set_xlabel("x [mm]")
        if i == 0:
            ax.set_ylabel("y [mm]")
            ax.text(5, -lim * 0.9, "head\nclamped", fontsize=8, color=THEORY)

    ax = fig.add_subplot(gs[1, :2])
    t_show = cfg.stage3.t_end - 2.0 / f
    for i, m in enumerate(models):
        r = R[m]
        k = r["t"] >= t_show
        ax.plot(r["t"][k], -r["tip_y"][k] * 1e3, color=SERIES[i], lw=1.6,
                label=f"{MODEL_LABELS[m]} (phase {r['phase_tip']:+.0f}° vs pump)")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("tip deflection to the right [mm]")
    ax.set_title(f"Tail tip motion in steady state ({f:.0f} Hz)")
    ax.legend(loc="upper right", fontsize=8, ncol=3, bbox_to_anchor=(1.0, 1.0))
    ax.set_ylim(top=ax.get_ylim()[1] * 1.35)

    ax = fig.add_subplot(gs[1, 2])
    x = np.arange(len(models))
    td = np.array([R[m]["thrust_drag"] for m in models]) * 1e3
    tr = np.array([R[m]["thrust_react"] for m in models]) * 1e3
    ax.bar(x, td, width=0.6, color=SERIES[1], label="from drag")
    ax.bar(x, tr, width=0.6, bottom=td, color=SERIES[2], label="from reactive force",
           edgecolor="white", linewidth=2)
    for xi, tot in zip(x, td + tr):
        ax.text(xi, max(tot, 0) + 3, f"{abs(tot) if abs(tot) < 0.5 else tot:.0f} mN",
                ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x, [MODEL_LABELS[m] for m in models], fontsize=9)
    ax.set_ylabel("mean tethered thrust [mN]")
    ax.set_title("Thrust (force on the mount)")
    ax.set_ylim(0, max(td + tr) * 1.2 + 5)
    ax.grid(axis="x", visible=False)
    ax.legend(fontsize=8, loc="upper left")
    fig.savefig(RESULTS / "e3_tethered_models.png")
    plt.close(fig)

    rows = [[R[m]["amp_tip"], R[m]["phase_tip"], R[m]["theta_amp"], R[m]["dp_amp"],
             R[m]["thrust"], R[m]["thrust_drag"], R[m]["thrust_react"], R[m]["lateral_amp"]]
            for m in models]
    with open(RESULTS / "e3_tethered_models.csv", "w") as fh:
        fh.write("model,tip_amp_m,phase_deg,theta_amp_rad,dp_amp_Pa,thrust_N,thrust_drag_N,"
                 "thrust_reactive_N,lateral_force_amp_N\n")
        for m, row in zip(models, rows):
            fh.write(m + "," + ",".join(f"{v:.6g}" for v in row) + "\n")

    print("Stage 3 (tethered tail, %.0f Hz):" % f)
    print(f"  {'model':>15} {'tip ampl.':>11} {'phase':>7} {'θ ampl.':>8} {'Δp ampl.':>9} "
          f"{'thrust':>9} {'(drag':>7} {'+ react.)':>9} {'F lateral':>9}")
    for m in models:
        r = R[m]
        print(f"  {m:>15} {r['amp_tip']*1e3:9.1f}mm {r['phase_tip']:6.0f}° "
              f"{np.degrees(r['theta_amp']):7.1f}° {r['dp_amp']/1e3:7.1f}kPa "
              f"{r['thrust']*1e3:7.1f}mN {r['thrust_drag']*1e3:7.1f} {r['thrust_react']*1e3:9.1f} "
              f"{r['lateral_amp']*1e3:7.0f}mN")
        if m == "drag":
            print(f"  {'':>15} max. drag power: {r['P_drag'].max():.1e} W (must be ≤ 0)")


# ---------------------------------------------------------------- stage 4
SWIM_RUNS = [("none", "laplace"), ("drag", "laplace"), ("drag+reactive", "laplace"),
             ("stokes_sbt", "laplace"), ("drag+reactive", "analytical")]
SWIM_LABELS = {"none": "no water", "drag": "drag", "drag+reactive": "drag + reactive",
               "stokes_sbt": "Stokes SBT (built-in, overlaps “no water”)"}
SWIM_COLORS = {"none": SERIES[0], "drag": SERIES[1], "drag+reactive": SERIES[2],
               "stokes_sbt": SERIES[3]}


def _swim(run):
    return S.free_swim(default_config(), *run)


def stage4(pool):
    cfg = default_config()
    R = {run: r for run, r in zip(SWIM_RUNS, pool.map(_swim, SWIM_RUNS))}
    main = R[("drag+reactive", "laplace")]
    np.savez_compressed(RESULTS / "e4_free_swim_frames.npz", frames=main["frames"],
                        t=main["frame_t"], length=main["length"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [1.15, 1]})
    for (m, d), r in R.items():
        ls = "-" if d == "laplace" else "--"
        lab = SWIM_LABELS[m] + ("" if d == "laplace" else " + AnalyticalLinearDamper (WRONG)")
        ax1.plot(r["t"], r["U_avg"] * 100, ls, color=SWIM_COLORS[m], lw=1.8,
                 label=f"{lab}: {abs(r['U_final']) * 100 if abs(r['U_final']) < 5e-4 else r['U_final'] * 100:.1f} cm/s")
    ax1.axhline(0, color=THEORY, lw=0.8)
    ax1.set_xlabel("time [s]")
    ax1.set_ylabel("forward speed U [cm/s] (period average)")
    ax1.set_title(f"Free swimming, {cfg.hydraulics.tail_freq:.0f} Hz "
                  f"(Re ≈ {main['reynolds']:.0e} for drag + reactive)")
    ax1.legend(fontsize=8, loc="upper left")
    ax1.set_ylim(top=max(r["U_avg"].max() for r in R.values()) * 100 * 1.45)

    fr, ft = main["frames"], main["frame_t"]
    T = 1.0 / cfg.hydraulics.tail_freq
    last = np.where(ft >= ft[-1] - T)[0]
    col = SWIM_COLORS["drag+reactive"]
    for j, k in enumerate(last[::2]):
        p = fr[k][:2] - fr[k][:2].mean(axis=1, keepdims=True)
        # rotate into the fish frame: X axis along the mean body direction (nose to the left)
        e = fr[k][:2, -1] - fr[k][:2, 0]
        c, s_ = e / np.linalg.norm(e)
        rot = np.array([[c, s_], [-s_, c]])
        q = rot @ p
        ax2.plot(q[0] * 1e3, q[1] * 1e3, color=col, lw=1.2,
                 alpha=0.3 + 0.7 * j / max(1, len(last[::2]) - 1))
        ax2.plot(q[0, 0] * 1e3, q[1, 0] * 1e3, "o", color=col, ms=3)
    ax2.set_aspect("equal")
    ax2.set_ylim(-90, 90)
    ax2.set_xlabel("along the fish [mm] (nose on the left)")
    ax2.set_ylabel("across [mm]")
    ax2.set_title("Shape over one period, center-of-mass frame (drag + reactive)")
    ax2.text(0.02, 0.04, f"distance in {ft[-1]:.0f} s: {main['distance']:.1f} m, turn {main['heading_change']:+.0f}°",
             transform=ax2.transAxes, fontsize=8, color=THEORY)
    fig.savefig(RESULTS / "e4_free_swim_speed.png")
    plt.close(fig)

    with open(RESULTS / "e4_free_swim_speed.csv", "w") as fh:
        fh.write("t," + ",".join(f"U_{m}_{d}" for m, d in SWIM_RUNS) + "\n")
        t = main["t"]
        cols = [np.interp(t, R[k]["t"], R[k]["U_avg"]) for k in SWIM_RUNS]
        for i in range(len(t)):
            fh.write(f"{t[i]:.4f}," + ",".join(f"{c[i]:.6g}" for c in cols) + "\n")

    print("Stage 4 (free swimming, %.0f Hz):" % cfg.hydraulics.tail_freq)
    print(f"  {'model':>15} {'damping':>11} {'U final':>9} {'[BL/s]':>7} {'dist.':>7} "
          f"{'turn':>7} {'max |z|':>8} {'Re':>8}")
    for (m, d), r in R.items():
        print(f"  {m:>15} {d:>11} {r['U_final']*100:7.2f}cm/s {r['U_final']/r['length']:7.3f} "
              f"{r['distance']:6.2f}m {r['heading_change']:6.1f}° {r['z_max'].max():8.1e} "
              f"{r['reynolds']:8.1e}")


# ---------------------------------------------------------------- stage 5
def _sweep(args):
    return S.sweep_point(default_config(), *args)


def _fn(E_factor):
    return S.tail_natural_frequency(default_config(), E_factor)


def stage5(pool):
    cfg = default_config()
    s5 = cfg.stage5
    grid = [(f, e) for e in s5.E_factors for f in s5.freqs]
    fn_jobs = pool.map(_fn, s5.E_factors)
    pts = list(pool.map(_sweep, grid))
    FN = {r["E_factor"]: r["f_n"] for r in fn_jobs}
    blues = plt.get_cmap("Blues")
    cols = {e: blues(0.45 + 0.5 * i / (len(s5.E_factors) - 1)) for i, e in enumerate(s5.E_factors)}
    E0 = cfg.rod.youngs_modulus

    fig, axs = plt.subplots(1, 3, figsize=(15, 4.5))
    panels = [("U", 100, "steady speed U [cm/s]", "Swimming speed"),
              ("tip_amp", 1000, "tail tip amplitude [mm]", "Tail amplitude (fish frame)"),
              ("strouhal", 1, "St = f·2A/U [-]", "Strouhal number")]
    for ax, (key, sc, ylab, title) in zip(axs, panels):
        for e in s5.E_factors:
            rows = [p for p in pts if p["E_factor"] == e]
            ax.plot([p["freq"] for p in rows], [p[key] * sc for p in rows], "o-", color=cols[e],
                    ms=6, label=f"E = {e:g}·E₀ = {e * E0 / 1e3:.0f} kPa (f_n = {FN[e]:.2f} Hz)")
            if key != "strouhal":
                ax.axvline(FN[e], color=cols[e], ls=":", lw=1.2)
        ax.set_xlabel("tail-beat frequency f [Hz]")
        ax.set_ylabel(ylab)
        ax.set_title(title)
    axs[2].axhspan(0.2, 0.4, color="#f2f1ed", zorder=0)
    axs[2].text(0.55, 0.3, "real fish\nSt ≈ 0.2–0.4", fontsize=8, color=THEORY, va="center")
    axs[0].text(0.02, 0.97, "dotted: tail natural frequency\nin vacuum (pump idle)",
                transform=axs[0].transAxes, fontsize=8, color=THEORY, va="top")
    fig.legend(*axs[0].get_legend_handles_labels(), loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, -0.08))
    fig.savefig(RESULTS / "e5_sweep_freq_E.png")
    plt.close(fig)
    with open(RESULTS / "e5_sweep_freq_E.csv", "w") as fh:
        fh.write("E_factor,freq_Hz,U_m_s,U_BL_s,tip_amp_m,strouhal,theta_amp_rad,dp_amp_Pa,f_n_Hz\n")
        for p in pts:
            fh.write(f"{p['E_factor']},{p['freq']},{p['U']:.6g},{p['U']/p['length']:.6g},"
                     f"{p['tip_amp']:.6g},{p['strouhal']:.6g},{p['theta_amp']:.6g},"
                     f"{p['dp_amp']:.6g},{FN[p['E_factor']]:.6g}\n")

    print("Stage 5 (f × E sweep, drag+reactive model):")
    for e in s5.E_factors:
        print(f"  E = {e:g}·E₀: tail f_n (vacuum) = {FN[e]:.3f} Hz")
    print(f"  {'E×':>4} {'f [Hz]':>7} {'U [cm/s]':>9} {'[BL/s]':>7} {'tip A':>9} {'St':>6} "
          f"{'θ ampl.':>8} {'Δp ampl.':>9}")
    for p in pts:
        print(f"  {p['E_factor']:4g} {p['freq']:7.1f} {p['U']*100:9.2f} {p['U']/p['length']:7.3f} "
              f"{p['tip_amp']*1e3:7.1f}mm {p['strouhal']:6.2f} {np.degrees(p['theta_amp']):7.1f}° "
              f"{p['dp_amp']/1e3:7.1f}kPa")


# ---------------------------------------------------------------- stage 6
def stage6(pool):
    cfg = default_config()
    r = pool.submit(S.depth_control, cfg, True).result()
    t = r["t"]
    fig, axs = plt.subplots(3, 1, figsize=(11, 8.2), sharex=True,
                            gridspec_kw={"height_ratios": [1.4, 1, 0.8]})
    ax = axs[0]
    ax.step(t, -r["z_ref"], where="post", color=THEORY, ls="--", lw=1.2, label="setpoint")
    ax.plot(t, -r["z"], color=SERIES[0], label="fish (center of mass)")
    ax.invert_yaxis()
    ax.set_ylabel("depth [m]")
    ax.set_title(f"Depth control with the bladder (fish swims at {cfg.hydraulics.tail_freq:.0f} Hz, "
                 f"mean {np.mean(r['U'][t > 5]) * 100:.0f} cm/s)")
    ax.legend(loc="lower right")
    ax = axs[1]
    ax.plot(t, r["V_ref"] * 1e6, color=SERIES[1], lw=1.2, label="V_ref from PID")
    ax.plot(t, r["V_b"] * 1e6, color=SERIES[0], label="bladder V")
    ax.axhline(r["V_neutral"] * 1e6, color=THEORY, ls=":", lw=1.2)
    ax.text(t[-1], r["V_neutral"] * 1e6 + 0.8, f"neutral {r['V_neutral']*1e6:.1f} ml",
            ha="right", va="bottom", fontsize=8, color=THEORY)
    ax.set_ylabel("volume [ml]")
    ax.set_ylim(cfg.buoyancy.V_min * 1e6 - 2, cfg.buoyancy.V_max * 1e6 + 4)
    ax.legend(loc="upper left", ncol=2)
    ax = axs[2]
    ax.plot(t, r["pitch"], color=SERIES[2], lw=1.0, label="pitch (+ nose up)")
    ax.plot(t, r["roll"], color=SERIES[4], lw=0.8, label="roll")
    ax.set_ylabel("angle [°]")
    ax.set_xlabel("time [s]")
    ax.legend(loc="upper left", ncol=2, fontsize=8)
    ax.set_ylim(top=max(np.max(np.abs(r["roll"])), np.max(np.abs(r["pitch"]))) * 1.6)
    fig.savefig(RESULTS / "e6_depth_control.png")
    plt.close(fig)
    np.savetxt(RESULTS / "e6_depth_control.csv",
               np.column_stack([t, r["z"], r["z_ref"], r["V_b"], r["V_ref"], r["pitch"], r["roll"], r["U"]]),
               delimiter=",", header="t,z,z_ref,V_bladder,V_ref,pitch_deg,roll_deg,U", comments="")
    np.savez_compressed(RESULTS / "e6_trajectory.npz", t=t, x_cm=r["x_cm"])

    print("Stage 6 (3D, buoyancy + bladder + PID):")
    print(f"  mass {r['mass']:.3f} kg, body volume {r['V_body']*1e6:.0f} ml, "
          f"neutral bladder {r['V_neutral']*1e6:.1f} ml at s = {r['s_bladder']:.3f} m")
    sched = list(cfg.stage6.schedule) + [(t[-1], None)]
    for (t0, z0), (t1, _) in zip(sched[:-1], sched[1:]):
        m = (t >= t0) & (t < t1)
        z = r["z"][m]
        err = np.abs(z - z0)
        tol = 0.05 * max(abs(z0 - r["z"][m][0]), 0.1)
        settle = t[m][np.where(err > tol)[0][-1]] - t0 if np.any(err > tol) else 0.0
        over = np.max(z - z0) if z0 > r["z"][m][0] else np.max(z0 - z)
        print(f"  z_ref = {z0:+.2f} m from {t0:4.1f} s: settling time (±5%) {settle:5.1f} s, "
              f"overshoot {max(over, 0)*100:4.1f} cm, final error {(z[-1]-z0)*100:+.1f} cm")
    print(f"  max |pitch| = {np.max(np.abs(r['pitch'])):.1f}°, "
          f"max |roll| = {np.max(np.abs(r['roll'])):.1f}°, "
          f"bladder saturated {100*np.mean((r['V_ref'] <= cfg.buoyancy.V_min + 1e-12) | (r['V_ref'] >= cfg.buoyancy.V_max - 1e-12)):.0f}% of the time")


STAGES = {1: stage1, 2: stage2, 3: stage3, 4: stage4, 5: stage5, 6: stage6}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, nargs="*", default=sorted(STAGES))
    args = ap.parse_args()
    RESULTS.mkdir(exist_ok=True)
    with ProcessPoolExecutor(N_WORKERS) as pool:
        for s in args.stage:
            STAGES[s](pool)
