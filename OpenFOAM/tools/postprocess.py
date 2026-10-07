#!/usr/bin/env python3
"""Postprocessing of the FSI demo stages -> PNG plots + CSV in results/.

Usage:
    python tools/postprocess.py e0 00-reference-flap
    python tools/postprocess.py e1 01-solid-only
"""
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import params as P  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def save_csv(name, header, rows):
    np.savetxt(RESULTS / name, np.asarray(rows), delimiter=",", header=header,
               comments="", fmt="%.6g")


def read_ccx_dat(path, nset="NTIP"):
    """Returns an array [time, ux, uy] for the first node of the set from a .dat file."""
    rows, t, want = [], None, False
    for line in Path(path).read_text().splitlines():
        m = re.search(rf"displacements .* for set {nset} and time\s+(\S+)", line)
        if m:
            t, want = float(m.group(1)), True
            continue
        if want and line.strip():
            parts = line.split()
            rows.append((t, float(parts[1]), float(parts[2])))
            want = False
    return np.array(rows)


def tip_angle_deg(ux, uy):
    """Tip angle: angle of the segment root(0,0) -> tip middle relative to the x axis."""
    return np.degrees(np.arctan2(uy, P.L + ux))


# ---------------------------------------------------------------------------
def e0(case):
    """Stage 0: flap tip displacement vs the tutorial reference."""
    case = Path(case)
    ref = np.loadtxt(case / "reference/tip_reference.csv", delimiter=",", skiprows=1)
    wp = case / "solid-calculix/precice-Solid-watchpoint-Flap-Tip.log"
    d = np.loadtxt(wp, skiprows=1)
    t, dx = d[:, 0], d[:, 3]
    # compare at the same time instants
    dx_i = np.interp(ref[:, 0], t, dx)
    err = np.max(np.abs(dx_i - ref[:, 1])) / np.max(np.abs(ref[:, 1]))
    save_csv("e0_flap_tip.csv", "time,dx_run,dx_reference",
             np.column_stack([ref[:, 0], dx_i, ref[:, 1]]))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(ref[:, 0], ref[:, 1], "k-", lw=2, label="tutorial reference")
    ax.plot(t, dx, "r--", label="this run")
    ax.set(xlabel="time [s]", ylabel="tip displacement x [m]",
           title=f"Stage 0: perpendicular-flap (max. relative error {err:.2%})")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "e0_flap_tip.png", dpi=150)
    print(f"e0: max. relative tip error = {err:.3%}")
    return err


def e1(case):
    """Stage 1: tip deflection and angle vs pressure, L/R symmetry test."""
    case = Path(case)
    p_max = 20e3  # must match *DLOAD in tail_L.inp / tail_R.inp
    data = {}
    for side in "LR":
        d = read_ccx_dat(case / f"tail_{side}.dat")
        data[side] = d
    pL, pR = data["L"][:, 0] * p_max, data["R"][:, 0] * p_max
    angL = tip_angle_deg(data["L"][:, 1], data["L"][:, 2])
    angR = tip_angle_deg(data["R"][:, 1], data["R"][:, 2])

    # symmetry: |uy_L(p)| vs |uy_R(p)| on a common pressure grid
    p_common = pL[(pL <= pR.max())]
    uyR = np.interp(p_common, pR, data["R"][:, 2])
    uyL = np.interp(p_common, pL, data["L"][:, 2])
    mask = np.abs(uyL) > 1e-6
    asym = np.max(np.abs(np.abs(uyL[mask]) - np.abs(uyR[mask])) / np.abs(uyL[mask]))
    monotonic = bool(np.all(np.diff(np.abs(data["L"][:, 2])) > 0)
                     and np.all(np.diff(np.abs(data["R"][:, 2])) > 0))

    rows = []
    for side, p, d, ang in (("L", pL, data["L"], angL), ("R", pR, data["R"], angR)):
        for pi, (_, ux, uy), a in zip(p, d, ang):
            rows.append((0 if side == "L" else 1, pi, ux, uy, a))
    save_csv("e1_tip_vs_pressure.csv", "chamber(0=L;1=R),p_Pa,ux_m,uy_m,angle_deg", rows)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.plot(pL / 1e3, data["L"][:, 2] * 1e3, "o-", ms=3, label="chamber L")
    ax1.plot(pR / 1e3, data["R"][:, 2] * 1e3, "s-", ms=3, label="chamber R")
    ax1.axhline(-0.15 * P.L * 1e3, color="gray", ls=":", lw=1)
    ax1.axhline(0.15 * P.L * 1e3, color="gray", ls=":", lw=1, label="±15% L")
    ax1.set(xlabel="chamber pressure [kPa]", ylabel="tip deflection y [mm]",
            title="Tip deflection (dry)")
    ax2.plot(pL / 1e3, angL, "o-", ms=3, label="chamber L")
    ax2.plot(pR / 1e3, angR, "s-", ms=3, label="chamber R")
    ax2.set(xlabel="chamber pressure [kPa]", ylabel="tip angle [°]",
            title=f"Tip angle (L/R asymmetry {asym:.2%})")
    for ax in (ax1, ax2):
        ax.grid(alpha=0.3)
        ax.legend()
    fig.suptitle("Stage 1: tail alone in CalculiX (NLGEOM), parameters = PLACEHOLDER")
    fig.tight_layout()
    fig.savefig(RESULTS / "e1_tip_vs_pressure.png", dpi=150)
    print(f"e1: L/R asymmetry = {asym:.3%}, monotonic = {monotonic}, "
          f"deflection at {pL[-1] / 1e3:.1f} kPa = {data['L'][-1, 2] * 1e3:.1f} mm, "
          f"angle = {angL[-1]:.1f}°")
    return asym, monotonic


def read_forces(case, name="forcesBody"):
    """[time, Fx, Fy, Fx_pressure, Fx_viscous] from postProcessing/<name>/*/force.dat
    (consecutive time directories after a restart are concatenated)."""
    parts = []
    for d in sorted((Path(case) / "postProcessing" / name).iterdir(), key=lambda p: float(p.name)):
        a = np.loadtxt(d / "force.dat", comments="#")
        parts.append(a[:, [0, 1, 2, 4, 7]])
    a = np.vstack(parts)
    # With implicit coupling OpenFOAM writes a row at EVERY coupling iteration
    # (same time, unconverged values). We keep the last row for each time
    # instant = the converged value.
    _, idx = np.unique(a[::-1, 0], return_index=True)
    return a[::-1][idx]


def n_cells(case):
    m = re.search(r"cells:\s+(\d+)", (Path(case) / "log.checkMesh").read_text())
    return int(m.group(1))


def read_surface_raw(path):
    """Raw file from the 'surfaces' function: columns x y z value."""
    return np.loadtxt(path, comments="#")


def e2(stage):
    """Stage 2: rigid-body drag – mesh convergence, boundary effect, Cp."""
    stage = Path(stage)
    u_in, t_avg = 0.2, 5.0          # consistent with system/caseParams (U_IN, AVG_START)
    variants = [("mesh-coarse", "coarse"), ("mesh-medium", "medium"),
                ("mesh-fine", "fine"), ("domain-1.5x", "medium, domain 1.5x")]
    rows, series = [], {}
    for name, label in variants:
        case = stage / name
        if not (case / "postProcessing").exists():
            print(f"e2: no results for {name}, skipping")
            continue
        f = read_forces(case)
        sel = f[:, 0] >= t_avg
        fx, fy = f[sel, 1].mean(), f[sel, 2]
        cd = fx / (0.5 * P.RHO_FLUID * u_in**2 * (P.L + P.HEAD_A))
        rows.append((n_cells(case), fx, f[sel, 3].mean(), f[sel, 4].mean(),
                     fy.std(), cd, 1 if "domain" in name else 0))
        series[label] = f
    rows = np.array(rows)
    save_csv("e2_mesh_convergence.csv",
             "cells,Fx_mean_N_per_m,Fx_pressure,Fx_viscous,Fy_std,Cd_chord,domain_variant", rows)

    mesh_rows = rows[rows[:, 6] == 0]
    mesh_rows = mesh_rows[np.argsort(mesh_rows[:, 0])]
    change_fine = abs(mesh_rows[-1, 1] - mesh_rows[-2, 1]) / abs(mesh_rows[-1, 1])
    dom = rows[rows[:, 6] == 1]
    medium = mesh_rows[1]
    change_dom = abs(dom[0, 1] - medium[1]) / abs(medium[1]) if len(dom) else float("nan")

    fig, axs = plt.subplots(1, 3, figsize=(16, 4.5))
    for label, f in series.items():
        axs[0].plot(f[:, 0], f[:, 1], lw=0.8, label=label)
    axs[0].axvline(t_avg, color="gray", ls=":")
    axs[0].set(xlabel="time [s]", ylabel="Fx [N/m]", title="Drag over time (start-up, then averaging)")
    axs[0].set_ylim(0, 3 * max(r[1] for r in rows))
    axs[0].legend(fontsize=8)

    axs[1].plot(mesh_rows[:, 0], mesh_rows[:, 1], "o-", label="total drag")
    axs[1].plot(mesh_rows[:, 0], mesh_rows[:, 2], "s--", label="pressure part")
    axs[1].plot(mesh_rows[:, 0], mesh_rows[:, 3], "^--", label="viscous part (friction)")
    if len(dom):
        axs[1].plot(dom[:, 0], dom[:, 1], "r*", ms=12, label="domain 1.5x")
    axs[1].set(xlabel="number of cells", ylabel="mean Fx [N/m]",
               title=f"Convergence: fine/medium change {change_fine:.1%}, domain {change_dom:.1%}")
    axs[1].legend(fontsize=8)

    # Cp = p / (0.5 U^2) (kinematic p) on the surface, finest mesh
    fine = stage / "mesh-fine" / "postProcessing" / "bodySurface"
    if fine.exists():
        last = sorted(fine.iterdir(), key=lambda p: float(p.name))[-1]
        raw = read_surface_raw(next(last.glob("pMean_*.raw")))
        x, y, cp = raw[:, 0], raw[:, 1], raw[:, 3] / (0.5 * u_in**2)
        for side, m, mk in (("left (y>0)", y > 0, "."), ("right (y<0)", y < 0, "x")):
            o = np.argsort(x[m])
            axs[2].plot(x[m][o], cp[m][o], mk, ms=3, label=side)
        axs[2].axvline(0, color="gray", ls=":", lw=1)
        axs[2].text(0.002, axs[2].get_ylim()[1] * 0.9 if axs[2].get_ylim()[1] > 0 else 0.5,
                    "tail root", fontsize=8)
        axs[2].invert_yaxis()
        axs[2].set(xlabel="x [m] (head < 0 < tail)", ylabel="Cp (inverted axis)",
                   title="Mean pressure coefficient, fine mesh")
        axs[2].legend(fontsize=8)
    for ax in axs:
        ax.grid(alpha=0.3)
    fig.suptitle(f"Stage 2: rigid body in inflow U = {u_in} m/s (laminar, 2D)")
    fig.tight_layout()
    fig.savefig(RESULTS / "e2_mesh_convergence.png", dpi=150)
    print(f"e2: Fx [N/m] per mesh = {np.round(mesh_rows[:, 1], 4)}, "
          f"fine/medium change = {change_fine:.2%}, domain 1.5x = {change_dom:.2%}")
    return change_fine, change_dom


def read_watchpoint(case):
    """[time, dx, dy, Fx, Fy] of the tip from the preCICE watch point (Solid participant)."""
    f = Path(case) / "solid-calculix" / "precice-Solid-watchpoint-Tip.log"
    if not f.exists() or f.stat().st_size == 0:
        return np.empty((0, 5))
    d = np.atleast_2d(np.genfromtxt(f, skip_header=1, invalid_raise=False))
    return d[:, [0, 3, 4, 5, 6]]


def read_iterations(case):
    """[window, iterations] from precice-Solid-iterations.log (implicit coupling only)."""
    f = Path(case) / "solid-calculix" / "precice-Solid-iterations.log"
    if not f.exists():
        return np.empty((0, 2))
    d = np.atleast_2d(np.loadtxt(f, skiprows=1))
    return d[:, [0, 2]]


def e3(stage):
    """Stage 3: explicit vs implicit coupling (added-mass effect)."""
    stage = Path(stage)
    ex, im = read_watchpoint(stage / "explicit"), read_watchpoint(stage / "implicit")
    it = read_iterations(stage / "implicit")
    dt = 0.0025  # time-window-size
    rows = []
    for name, d in (("explicit", ex), ("implicit", im)):
        for r in d:
            rows.append((0 if name == "explicit" else 1, *r))
    save_csv("e3_explicit_vs_implicit.csv", "coupling(0=explicit;1=implicit),time,dx,dy,Fx,Fy", rows)
    save_csv("e3_iterations.csv", "window,iterations", it)

    fig, axs = plt.subplots(1, 3, figsize=(16, 4.5))
    ax = axs[0]
    ax.plot(im[:, 0], im[:, 2] * 1e3, "b-", lw=1, label="implicit (IQN-ILS)")
    ax.plot(ex[:, 0], ex[:, 2] * 1e3, "r-", lw=1, label="explicit")
    ax.set(xlabel="time [s]", ylabel="tip deflection y [mm]", title="Tip deflection")
    ax.set_ylim(*(np.array([-1, 1]) * max(1.5 * np.abs(im[:, 2]).max() * 1e3, 0.05)))
    ax.legend()
    # force at the tip node in consecutive windows: explicit multiplies the error each step
    ax = axs[1]
    ex1 = read_watchpoint(stage / "explicit-dt1ms")
    ax.semilogy(np.arange(1, 6), np.abs(im[1:6, 3]), "bo-", label="implicit, Δt = 2.5 ms")
    for d, lab, c in ((ex, "explicit, Δt = 2.5 ms", "r"), (ex1, "explicit, Δt = 1 ms", "m")):
        if len(d) > 2:
            k = np.arange(1, len(d))
            ratio = d[2, 3] / d[1, 3]
            ax.semilogy(k, np.abs(d[1:, 3]), "s-", color=c, label=f"{lab}: ×{ratio:.0f} per window")
    ax.set(xlabel="time window number", ylabel="|Fx| at the tip node [N]",
           title=f"Explicit fails after {len(ex) - 1} windows; smaller Δt = worse")
    ax.legend(fontsize=8)
    ax = axs[2]
    ax.plot(it[:, 0] * dt, it[:, 1], "b-", lw=0.8)
    ax.set(xlabel="time [s]", ylabel="coupling iterations per window",
           title=f"Implicit: mean {it[:, 1].mean():.1f}, max. {int(it[:, 1].max())} iterations")
    for a in axs:
        a.grid(alpha=0.3)
    fig.suptitle("Stage 3: passive tail in a stream U = 0.2 m/s – explicit vs implicit coupling")
    fig.tight_layout()
    fig.savefig(RESULTS / "e3_explicit_vs_implicit.png", dpi=150)
    print(f"e3: explicit – {len(ex)} windows (up to t = {ex[-1, 0] if len(ex) else 0:.4f} s), "
          f"implicit – {len(im)} windows, mean {it[:, 1].mean():.2f} iterations, max {int(it[:, 1].max())}")


def read_case_txt(case):
    """Parameters from case.txt (new-fsi-case.sh): U_IN, DT, T_END, P0, f."""
    t = (Path(case) / "case.txt").read_text()
    g = lambda k: float(re.search(rf"{k} = ([-\d.eE+]+)", t).group(1))  # noqa: E731
    return {"U": g("U_IN"), "DT": g("DT"), "T": g("T_END"), "P0": g("P0"), "f": g("f")}


def last_cycles(t, y, f, n=1):
    """Mask of the last n full periods."""
    t_end = t[-1]
    return t >= t_end - n / f - 1e-9


def amplitude(t, y, f, n=2):
    """Amplitude = mean of the half peak-to-peak ranges in each of the last
    n periods (robust to differences between periods)."""
    period, t_end, amps = 1 / f, t[-1], []
    for k in range(n):
        m = (t > t_end - (k + 1) * period - 1e-9) & (t <= t_end - k * period + 1e-9)
        amps.append(0.5 * (y[m].max() - y[m].min()))
    return float(np.mean(amps))


def phase_lag(t, a, b, f):
    """Lag of b relative to a [s] from cross-correlation (last 2 periods)."""
    m = last_cycles(t, a, f, 2)
    aa, bb = a[m] - a[m].mean(), b[m] - b[m].mean()
    c = np.correlate(bb, aa, "full")
    k = np.argmax(c) - (len(aa) - 1)
    dt = t[1] - t[0]
    lag = k * dt
    period = 1 / f
    return (lag + period / 2) % period - period / 2


def e4_amplitudes(stage):
    """(tip amplitude in water, tip amplitude dry) over the last periods [m]."""
    stage = Path(stage)
    p = read_case_txt(stage / "water")
    w = read_watchpoint(stage / "water")
    d = read_ccx_dat(stage / "dry" / "dry.dat")
    return amplitude(w[:, 0], w[:, 2], p["f"]), amplitude(d[:, 0], d[:, 2], p["f"])


def actuation_signal(t, f, t_ramp=None):
    """p_L - p_R (without P0): positive = left chamber pressurised."""
    t_ramp = 1 / f if t_ramp is None else t_ramp
    return np.clip(t / t_ramp, 0, 1) * np.sin(2 * np.pi * f * t)


def cycle_means(t, fx, f):
    """Mean Fx in consecutive full periods: [(period centre, mean)]."""
    out, period = [], 1 / f
    k = 0
    while (k + 1) * period <= t[-1] + 1e-9:
        m = (t >= k * period) & (t < (k + 1) * period)
        out.append(((k + 0.5) * period, fx[m].mean()))
        k += 1
    return np.array(out)


def e4(stage):
    """Stage 4: actuation in still water vs dry; cycle-averaged thrust."""
    stage = Path(stage)
    p = read_case_txt(stage / "water")
    f = p["f"]
    w = read_watchpoint(stage / "water")
    d = read_ccx_dat(stage / "dry" / "dry.dat")
    # force on the WHOLE body (head + tail): the tail alone is not a closed surface,
    # so its Fx depends on the pressure reference level
    ft = read_forces(stage / "water" / "fluid-openfoam", "forcesBody")
    ang_w, ang_d = tip_angle_deg(w[:, 1], w[:, 2]), tip_angle_deg(d[:, 1], d[:, 2])
    A_w, A_d = amplitude(w[:, 0], w[:, 2], f), amplitude(d[:, 0], d[:, 2], f)
    # lag relative to the drive signal (deflection towards -y when p_L > 0)
    act_w = -actuation_signal(w[:, 0], f)
    act_d = -actuation_signal(d[:, 0], f)
    lag_w = phase_lag(w[:, 0], act_w, w[:, 2], f)
    lag_d = phase_lag(d[:, 0], act_d, d[:, 2], f)
    cm = cycle_means(ft[:, 0], ft[:, 1], f)
    sel = cm[:, 0] > 2 / f          # periods after the ramp and one start-up period
    thrust = -cm[sel, 1].mean()     # thrust = -Fx (the fish swims in -x)
    thrust_err = cm[sel, 1].std(ddof=1) / np.sqrt(sel.sum())

    save_csv("e4_tip_water_vs_dry.csv", "time,angle_water_deg,uy_water_m",
             np.column_stack([w[:, 0], ang_w, w[:, 2]]))
    save_csv("e4_tip_dry.csv", "time,angle_dry_deg,uy_dry_m", np.column_stack([d[:, 0], ang_d, d[:, 2]]))
    save_csv("e4_thrust_cycle.csv", "time,Fx_body_N_per_m,Fy_body_N_per_m", ft[:, :3])
    save_csv("e4_thrust_cycle_means.csv", "cycle_center_s,Fx_mean_N_per_m", cm)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(d[:, 0], ang_d, "r-", lw=1, label=f"dry (amplitude {A_d * 1e3:.1f} mm)")
    ax.plot(w[:, 0], ang_w, "b-", lw=1.5, label=f"in water (amplitude {A_w * 1e3:.1f} mm)")
    ax.set(xlabel="time [s]", ylabel="tip angle [°]",
           title=f"Stage 4: P0 = {p['P0'] / 1e3:.0f} kPa, f = {f:g} Hz, still water – "
                 f"phase lag {lag_w * 360 * f:.0f}° (dry {lag_d * 360 * f:.0f}°)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "e4_tip_angle_water_vs_dry.png", dpi=150)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(ft[:, 0], ft[:, 1], "k-", lw=0.6, label="body Fx (instantaneous, converged)")
    ax.step(cm[:, 0] + 0.5 / f, cm[:, 1], "r-", where="pre", lw=2, label="cycle mean")
    ax.axhline(0, color="gray", lw=0.8)
    ax.set(xlabel="time [s]", ylabel="Fx [N/m]  (negative = thrust)",
           title=f"Stage 4: axial force; mean thrust {thrust * 1e3:.0f} ± {thrust_err * 1e3:.0f} mN/m (cycles from t = 2 s)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "e4_thrust_cycle.png", dpi=150)
    print(f"e4: amplitude water {A_w * 1e3:.2f} mm, dry {A_d * 1e3:.2f} mm, "
          f"phase lag water {lag_w * 360 * f:.0f}°, dry {lag_d * 360 * f:.0f}°, "
          f"thrust {thrust * 1e3:.0f} ± {thrust_err * 1e3:.0f} mN/m, cycle means {np.round(cm[:, 1] * 1e3, 1)}")
    return A_w, A_d, thrust


def fsi_summary(case, n_cycles=2):
    """Summary of an FSI case.
    Forces: means over full periods from t = 2/f (after the ramp and one
    start-up period) – we return the mean of these periods and its standard
    error (the scatter between periods can be large, especially in still water).
    Amplitude: from the last n periods. St = f * A_pp / U."""
    p = read_case_txt(case)
    f = p["f"]
    w = read_watchpoint(case)
    out = {"U": p["U"], "f": f, "complete": abs(w[-1, 0] - p["T"]) < p["DT"]}
    for key, name in (("Fx_body", "forcesBody"), ("Fx_tail", "forcesTail")):
        F = read_forces(Path(case) / "fluid-openfoam", name)
        cm = cycle_means(F[:, 0], F[:, 1], f)
        cm = cm[cm[:, 0] > 2 / f]
        out[key] = cm[:, 1].mean()
        out[key + "_err"] = cm[:, 1].std(ddof=1) / np.sqrt(len(cm)) if len(cm) > 1 else np.nan
        out["n_cycles_avg"] = len(cm)
    out["A"] = amplitude(w[:, 0], w[:, 2], f, n_cycles)
    out["St"] = f * 2 * out["A"] / p["U"] if p["U"] > 0 else np.nan
    return out


def e5(stage):
    """Stage 5: actuation + inflow – thrust/drag balance and Strouhal number.
    The U = 0 point is stage 4 (same actuation, still water)."""
    stage = Path(stage)
    cases = [stage.parent / "04-fsi-actuated" / "water"]
    cases += sorted(stage.glob("U*"), key=lambda c: float(c.name[1:]))
    rows = []
    for case in cases:
        try:
            s = fsi_summary(case)
        except Exception as e:  # noqa: BLE001
            print(f"e5: {case} – no results ({e})")
            continue
        rows.append((s["U"], s["Fx_body"], s["Fx_body_err"], s["Fx_tail"], s["A"], s["St"],
                     s["n_cycles_avg"], s["complete"]))
    rows = np.array(rows, dtype=float)
    save_csv("e5_force_vs_inflow.csv",
             "U_m_s,Fx_body_N_per_m,Fx_body_stderr,Fx_tail_N_per_m,tip_amplitude_m,St,n_cycles,complete", rows)

    # balance speed: Fx_body(U) = 0 (linear interpolation between points)
    U, F, E = rows[:, 0], rows[:, 1], rows[:, 2]
    f_act = read_case_txt(cases[-1])["f"]
    u_eq, st_eq = np.nan, np.nan
    for i in range(len(U) - 1):
        if F[i] * F[i + 1] <= 0:
            u_eq = U[i] - F[i] * (U[i + 1] - U[i]) / (F[i + 1] - F[i])
            st_eq = f_act * 2 * np.interp(u_eq, U, rows[:, 4]) / u_eq
            break

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax1.errorbar(U, F * 1e3, yerr=E * 1e3, fmt="o-", capsize=4,
                 label="whole body (cycle mean ± std. error)")
    ax1.plot(U, rows[:, 3] * 1e3, "s--", alpha=0.6, label="tail only")
    rigid = RESULTS / "e2_mesh_convergence.csv"
    if rigid.exists():
        r = np.loadtxt(rigid, delimiter=",", skiprows=1)
        fx_rigid = r[(r[:, 6] == 0)][np.argmax(r[r[:, 6] == 0][:, 0]), 1]
        ax1.plot([0.2], [fx_rigid * 1e3], "kx", ms=10, mew=2, label="rigid body (stage 2)")
    ax1.axhline(0, color="gray", lw=0.8)
    if np.isfinite(u_eq):
        ax1.axvline(u_eq, color="r", ls=":", label=f"balance U ≈ {u_eq:.3f} m/s (uncertain)")
    ax1.set(xlabel="inflow speed U [m/s]", ylabel="mean Fx [mN/m]  (negative = thrust > drag)",
            title="Axial force balance")
    ax1.legend(fontsize=8)
    m = U > 0
    ax2.plot(U[m], rows[m, 5], "o-")
    ax2.axhspan(0.2, 0.4, color="green", alpha=0.15, label="typical for fish: 0.2–0.4")
    if np.isfinite(st_eq):
        ax2.plot([u_eq], [st_eq], "r*", ms=14, label=f"St at balance ≈ {st_eq:.1f}")
    ax2.set(xlabel="inflow speed U [m/s]", ylabel="St = f·A_pp/U", title="Strouhal number")
    ax2.legend(fontsize=8)
    for a_ in (ax1, ax2):
        a_.grid(alpha=0.3)
    fig.suptitle(f"Stage 5: actuation f = {f_act:g} Hz, P0 = 15 kPa, fixed head (2D, laminar)")
    fig.tight_layout()
    fig.savefig(RESULTS / "e5_force_vs_inflow.png", dpi=150)
    print(f"e5: U = {U}, Fx_body = {np.round(F * 1e3, 0)} ± {np.round(E * 1e3, 0)} mN/m, "
          f"St = {np.round(rows[:, 5], 2)}, U_eq = {u_eq:.4f} m/s, St_eq = {st_eq:.2f}")
    return u_eq, st_eq


def e6(stage):
    """Stage 6: thrust and amplitude vs frequency (still water)."""
    stage = Path(stage)
    cases = list(stage.glob("f*")) + [stage.parent / "04-fsi-actuated" / "water"]
    rows = []
    for case in cases:
        try:
            s = fsi_summary(case, n_cycles=2)
        except Exception as e:  # noqa: BLE001
            print(f"e6: {case} – no results ({e})")
            continue
        rows.append((s["f"], -s["Fx_body"], s["Fx_body_err"], -s["Fx_tail"], s["A"], s["complete"]))
    rows = np.array(sorted(rows), dtype=float)
    save_csv("e6_freq_sweep.csv", "f_Hz,thrust_body_N_per_m,thrust_stderr,thrust_tail_N_per_m,tip_amplitude_m,complete", rows)
    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.errorbar(rows[:, 0], rows[:, 1] * 1e3, yerr=rows[:, 2] * 1e3, fmt="o-b", capsize=4,
                 label="thrust (−body Fx, cycle mean ± std. error)")
    ax1.axhline(0, color="gray", lw=0.8)
    ax1.set(xlabel="actuation frequency f [Hz]", ylabel="thrust [mN/m]")
    ax1.tick_params(axis="y", colors="b")
    ax2 = ax1.twinx()
    ax2.plot(rows[:, 0], rows[:, 4] * 1e3, "s--r", label="tip amplitude")
    ax2.set_ylabel("tip amplitude [mm]", color="r")
    ax2.tick_params(axis="y", colors="r")
    ax1.axvline(3.39, color="gray", ls=":", lw=1)
    ax1.text(3.33, ax1.get_ylim()[0] * 0.9, "dry f₁\n3.39 Hz", ha="right", fontsize=8, color="gray")
    ax1.grid(alpha=0.3)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper right")
    ax1.set_title("Stage 6: frequency sweep (P0 = 15 kPa, still water)")
    fig.tight_layout()
    fig.savefig(RESULTS / "e6_freq_sweep.png", dpi=150)
    print(f"e6: f = {rows[:, 0]}, thrust = {np.round(rows[:, 1] * 1e3, 2)} mN/m, "
          f"amplitude = {np.round(rows[:, 4] * 1e3, 2)} mm")
    return rows


def meshq(case, name=None):
    """Quality of the deforming fluid mesh over time (checkMesh at every write).
    Requires the OpenFOAM environment (source env.sh). Returns an array
    [time, max. non-orthogonality, max. skewness, min. volume]."""
    import subprocess
    case = Path(case).resolve()
    fluid = case / "fluid-openfoam"
    name = name or str(case.relative_to(ROOT)).replace("/", "_")
    out = subprocess.run(["checkMesh", "-noTopology", "-time", "0:", "-case", str(fluid)],
                         capture_output=True, text=True).stdout
    num = r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)"
    rows, t = [], None
    for line in out.splitlines():
        if line.startswith("Time = "):
            t = float(line.split("=")[1])
            rec = [t, np.nan, np.nan, np.nan]
            rows.append(rec)
        elif t is not None and "non-orthogonality Max:" in line:
            rec[1] = float(re.search(r"Max: " + num, line).group(1))
        elif t is not None and "Max skewness =" in line:
            rec[2] = float(re.search(r"Max skewness = " + num, line).group(1))
        elif t is not None and "Min volume =" in line:
            rec[3] = float(re.search(r"Min volume = " + num, line).group(1))
    rows = np.array(rows)
    save_csv(f"meshq_{name}.csv", "time,max_nonortho_deg,max_skewness,min_volume_m3", rows)
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.5))
    for ax, k, lab, lim in ((axs[0], 1, "max. non-orthogonality [°]", 70),
                            (axs[1], 2, "max. skewness [-]", 4),
                            (axs[2], 3, "min. cell volume [m³]", None)):
        ax.plot(rows[:, 0], rows[:, k], "o-", ms=2)
        if lim:
            ax.axhline(lim, color="r", ls=":", label="checkMesh threshold")
            ax.legend(fontsize=8)
        ax.set(xlabel="time [s]", ylabel=lab)
        ax.grid(alpha=0.3)
    fig.suptitle(f"Fluid mesh quality over time: {case.relative_to(ROOT)}")
    fig.tight_layout()
    fig.savefig(RESULTS / f"meshq_{name}.png", dpi=120)
    print(f"meshq {name}: max. non-orthogonality {np.nanmax(rows[:, 1]):.1f}°, "
          f"max. skewness {np.nanmax(rows[:, 2]):.2f}, min. volume {np.nanmin(rows[:, 3]):.3e} m³")
    return rows


if __name__ == "__main__":
    globals()[sys.argv[1]](*sys.argv[2:])
