"""Running the scene from Python, without the GUI (tests, scenario scripts).

Requires `source scripts/env.sh` (Sofa modules from the SOFA binary on PYTHONPATH).
"""
import time
from dataclasses import dataclass, field

import numpy as np

from fishsofa import geometry
from fishsofa.config import TailConfig

_PLUGINS_LOADED = False


def _sofa():
    """Imports SOFA only on first use – the rest of the package works without SOFA."""
    global _PLUGINS_LOADED
    import Sofa
    import Sofa.Core
    import Sofa.Simulation
    import SofaRuntime
    if not _PLUGINS_LOADED:
        SofaRuntime.importPlugin("Sofa.Component")
        _PLUGINS_LOADED = True
    return Sofa


@dataclass
class RunLog:
    t: list = field(default_factory=list)          # [s]
    tip: list = field(default_factory=list)        # fin centroid displacement [m] (3,)
    max_disp: list = field(default_factory=list)   # max |u| over nodes [m]
    tip_angle: list = field(default_factory=list)  # [rad]
    ms_per_step: float = float("nan")
    init_s: float = float("nan")
    has_nan: bool = False
    x_final: np.ndarray | None = None


def run(cfg: TailConfig, level: str, n_steps: int, mesh_root: str | None = None,
        log_every: int = 1, solver: str = "dynamic") -> RunLog:
    Sofa = _sofa()
    from fishsofa.scene import build_tail

    root = Sofa.Core.Node("root")
    t0 = time.perf_counter()
    h = build_tail(root, cfg, level, mesh_root, solver=solver)
    Sofa.Simulation.init(root)
    log = RunLog(init_s=time.perf_counter() - t0)

    mesh, dofs = h["mesh"], h["dofs"]
    x0 = np.array(dofs.position.value)
    base = geometry.base_center(x0, mesh.base_nodes)
    t1 = time.perf_counter()
    for i in range(1, n_steps + 1):
        Sofa.Simulation.animate(root, root.dt.value)
        if i % log_every == 0 or i == n_steps:
            x = np.array(dofs.position.value)
            if not np.all(np.isfinite(x)):
                log.has_nan = True
                break
            log.t.append(i * root.dt.value)
            log.tip.append(geometry.tip_displacement(x, x0, mesh.fin_nodes))
            log.max_disp.append(float(np.linalg.norm(x - x0, axis=1).max()))
            log.tip_angle.append(geometry.tip_angle(x, base, mesh.fin_nodes))
    log.ms_per_step = 1e3 * (time.perf_counter() - t1) / max(1, i)
    log.x_final = np.array(dofs.position.value)
    Sofa.Simulation.unload(root)
    return log


def static_sag(cfg: TailConfig, level: str, mesh_root: str | None = None, n_steps: int = 1) -> RunLog:
    """Static sag under weight: one StaticSolver (Newton) step = equilibrium state."""
    return run(cfg, level, n_steps, mesh_root, solver="static")


# ----------------------------------------------------------------------------- stage 2: quasi-statics

@dataclass
class QuasiStaticCurve:
    dV_target: list = field(default_factory=list)  # [m³]
    dV: list = field(default_factory=list)         # measured cavity volume growth [m³]
    p: list = field(default_factory=list)          # [Pa]
    tip_angle: list = field(default_factory=list)  # [rad]
    bulge: list = field(default_factory=list)      # outer wall bulging [m]
    ke_ratio: list = field(default_factory=list)   # kinetic energy / pressure work
    v0: float = float("nan")                       # cavity volume at rest [m³]
    wall_s: float = float("nan")


def _bulge_probe(mesh, cfg: TailConfig, side: int):
    """Nodes for measuring bulging: the outermost skin node on the chamber side and the
    node closest to the axis (y = z = 0), both in the cross-section at mid-chamber length."""
    x1, x2 = cfg.chamber_x_range
    xm = 0.5 * (x1 + x2)
    pts = mesh.points
    near = np.abs(pts[:, 0] - xm) < 0.6 * mesh.h_wall
    skin = np.zeros(len(pts), bool)
    skin[np.unique(mesh.tri_outer)] = True
    outer = np.flatnonzero(near & skin)
    outer = outer[np.argmax(side * pts[outer, 1])]
    cand = np.flatnonzero(near)
    center = cand[np.argmin(pts[cand, 1] ** 2 + pts[cand, 2] ** 2)]
    return outer, center


def quasi_static_sweep(cfg: TailConfig, level: str, dV_targets, side: str = "L",
                       mesh_root: str | None = None, dt: float = 0.05, ramp_steps: int = 4,
                       max_hold_steps: int = 60, ke_tol: float = 0.01,
                       p_stop: float | None = None, max_fraction: float | None = None,
                       mode: str = "volume") -> QuasiStaticCurve:
    """Pressure–volume–angle curve for one chamber (the other vented), quasi-statically.

    mode="volume" (default): dV_targets are volume increments [m³] (the pump imposes volume).
    mode="pressure": dV_targets are pressures [Pa] (valueType="pressure", input p·dt);
    stage 6 compares both modes when the Young's modulus changes.

    "Pseudo-static" method: implicit Euler with a large step (dt = 50 ms). Inertia
    (M/dt²) is then small compared to stiffness, so each step lands almost immediately
    at equilibrium. Verified in the stage 2 plan: same final state as a slow ramp with
    dt = 2 ms (1950.4 Pa in both), at 5–25× lower cost. Statics (StaticSolver) is
    ruled out, since it does not work with the chamber's Lagrange constraints.

    "Quasi-static" criterion (spec, stage 2): after reaching each point we hold the volume
    until kinetic energy < ke_tol · pressure work ∫p dV (for a quasi-static process the
    pressure work ≈ stored strain energy).
    Always an exact solver ("cholmod" or "ldl") – "warp" with a chamber gives a wrong
    equilibrium (README).
    """
    from dataclasses import replace

    from fishsofa import hydraulics
    from fishsofa.scene import build_tail

    Sofa = _sofa()
    exact = cfg.linear_solver if cfg.linear_solver in ("ldl", "cholmod") else "ldl"
    cfg = replace(cfg, dt=dt, linear_solver=exact)
    other = "R" if side == "L" else "L"
    root = Sofa.Core.Node("root")
    h = build_tail(root, cfg, level, mesh_root, chambers={side: mode, other: "vented"})
    Sofa.Simulation.init(root)
    spc, dofs, mesh, m = h["chambers"][side], h["dofs"], h["mesh"], h["masses"].node_mass
    x0 = np.array(dofs.position.value)
    base = geometry.base_center(x0, mesh.base_nodes)
    i_out, i_cen = _bulge_probe(mesh, cfg, +1 if side == "L" else -1)
    sgn = 1.0 if side == "L" else -1.0

    res = QuasiStaticCurve(v0=float(spc.initialCavityVolume.value))
    work, p_prev, dV_prev, target_prev = 0.0, 0.0, 0.0, 0.0
    t0 = time.perf_counter()
    for target in dV_targets:
        if max_fraction is not None and target > max_fraction * res.v0:
            break
        steps = 0
        while True:
            steps += 1
            frac = min(1.0, steps / ramp_steps)
            target_now = target_prev + frac * (target - target_prev)
            spc.value = [target_now if mode == "volume" else hydraulics.pressure_input(target_now, dt)]
            Sofa.Simulation.animate(root, dt)
            x = np.array(dofs.position.value)
            v = np.array(dofs.velocity.value)
            dV = float(spc.cavityVolume.value) - res.v0
            p = hydraulics.pressure_pa(spc, dt)
            work += 0.5 * (p + p_prev) * (dV - dV_prev)   # ∫p dV (trapezoidal rule)
            p_prev, dV_prev = p, dV
            ke = 0.5 * float((m * (v ** 2).sum(axis=1)).sum())
            ratio = ke / work if work > 0 else float("inf")
            # steps > ramp_steps: at least one hold step, because SOFA computes cavityVolume
            # BEFORE solving the step (the reading lags by one step).
            if (steps > ramp_steps and ratio < ke_tol) or steps >= ramp_steps + max_hold_steps:
                break
        res.dV_target.append(target)
        res.dV.append(dV)
        res.p.append(p)
        res.tip_angle.append(geometry.tip_angle(x, base, mesh.fin_nodes))
        u = x - x0
        res.bulge.append(sgn * (u[i_out, 1] - u[i_cen, 1]))
        res.ke_ratio.append(ratio)
        target_prev = target
        if p_stop is not None and p > p_stop:
            break
    res.wall_s = time.perf_counter() - t0
    Sofa.Simulation.unload(root)
    return res


# ----------------------------------------------------------------------------- stage 4: flapping

@dataclass
class FlapRun:
    log: dict                     # numpy arrays, keys from controller.LOG_KEYS
    dt: float
    ms_per_step: float
    cycles: dict                  # metrics from cycle_metrics()
    frames: dict | None = None    # recording for playback (record_fps), see run_flapping


def run_flapping(cfg: TailConfig, level: str, t_end: float, mesh_root: str | None = None,
                 progress_every: int = 0, record_fps: float | None = None) -> FlapRun:
    """Antagonistic L↔R system: prefill, then the rhythm V_ref(t) (hydraulics.TailHydraulics).

    Both chambers in volumeGrowth mode, dynamics (implicit Euler, cfg.dt), weight per
    cfg.environment. Exact solver ("cholmod" or "ldl") – warp with chambers is wrong.

    record_fps: record node positions every 1/record_fps of simulation time (float32), for
    real-time playback (scripts/record.py, replay mode in scene.py).
    """
    from dataclasses import replace

    from fishsofa.controller import FlapController
    from fishsofa.scene import build_tail

    Sofa = _sofa()
    if cfg.linear_solver not in ("ldl", "cholmod"):
        cfg = replace(cfg, linear_solver="ldl")
    root = Sofa.Core.Node("root")
    h = build_tail(root, cfg, level, mesh_root, chambers={"L": "volume", "R": "volume"})
    ctrl = root.addObject(FlapController(name="flap", root=root, handles=h, cfg=cfg))
    Sofa.Simulation.init(root)
    n = int(round(t_end / cfg.dt))
    every = max(1, int(round(1.0 / (record_fps * cfg.dt)))) if record_fps else 0
    frames = {"t": [], "x": []} if every else None
    if every:
        frames["t"].append(0.0)
        frames["x"].append(np.array(h["dofs"].position.value, dtype=np.float32))
    t0 = time.perf_counter()
    for i in range(n):
        Sofa.Simulation.animate(root, cfg.dt)
        if every and (i + 1) % every == 0:
            frames["t"].append((i + 1) * cfg.dt)
            frames["x"].append(np.array(h["dofs"].position.value, dtype=np.float32))
        if progress_every and (i + 1) % progress_every == 0:
            el = time.perf_counter() - t0
            print(f"  t = {(i + 1) * cfg.dt:.2f} s, {1e3 * el / (i + 1):.0f} ms/step", flush=True)
    ms = 1e3 * (time.perf_counter() - t0) / n
    log = {k: np.array(v, dtype=float) for k, v in ctrl.log.items()}
    if h["water"] is not None:   # same instants as the pump log (both controllers run at step start)
        log.update({k: np.array(v, dtype=float) for k, v in h["water"].log.items() if k != "t"})
    Sofa.Simulation.unload(root)
    if frames:
        frames = {"t": np.array(frames["t"]), "x": np.stack(frames["x"])}
    return FlapRun(log, cfg.dt, ms, cycle_metrics(log, cfg), frames)


def cycle_metrics(log: dict, cfg: TailConfig) -> dict:
    """Angle amplitude in each full cycle after the ramp, and phase relative to V_ref.

    Cycles are counted from the end of the amplitude ramp (prefill_time + ramp_time). Cycle
    amplitude = (max − min)/2 of the angle. Phase from the first harmonic over the last 2
    cycles: how much the angle lags −V_ref (+V_p bends the tail toward −Y, so −V_ref is the
    reference).
    """
    t, th, vref = log["t"], log["theta"], log["V_ref"]
    T = 1.0 / cfg.tail_freq
    t_start = cfg.prefill_time + cfg.ramp_time
    n_cyc = int((t[-1] - t_start) // T)
    amps, means = [], []
    for k in range(n_cyc):
        m = (t >= t_start + k * T) & (t < t_start + (k + 1) * T)
        amps.append(0.5 * (th[m].max() - th[m].min()))
        means.append(th[m].mean())
    out = {"amplitude_per_cycle": amps, "mean_per_cycle": means}
    if n_cyc >= 2:
        m = (t >= t_start + (n_cyc - 2) * T) & (t < t_start + n_cyc * T)
        e = np.exp(-2j * np.pi * cfg.tail_freq * t[m])
        z_th, z_ref = (th[m] * e).sum(), (-vref[m] * e).sum()
        out["phase_lag_deg"] = float(np.degrees(np.angle(z_ref / z_th)) % 360)
        out["steady_change"] = abs(amps[-1] / amps[-2] - 1)
    return out
