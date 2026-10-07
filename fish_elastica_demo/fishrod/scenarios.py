"""Scenarios for the successive stages. They return data (dicts of numpy arrays) – plots and CSV
are produced by scripts/run_scenarios.py, and the tests call the same functions with smaller settings."""

from dataclasses import replace

import numpy as np
import elastica as ea

from .actuation import ChamberActuator, SingleTorque, TorquePair
from .buoyancy import Bladder, BuoyancyForces, DepthPID
from .build import (FishSimulator, EndpointTorque, RodRecorder, angular_momentum,
                    element_centers, fish_profile, make_fish_rod, make_rod,
                    section_half_axes, stable_time_step, total_energy)
from .config import Config, fish_rod_config
from .hydraulics import TailHydraulics, TailRhythm, smooth_ramp
from .run import integrate
from .water import add_water


# ---------------------------------------------------------------- stage 1: validation
def bending_stiffness(rc) -> float:
    """E·I for a circular cross-section: I = π r⁴ / 4."""
    return rc.youngs_modulus * np.pi * rc.radius**4 / 4.0


def cantilever_arc(cfg: Config, verbose: bool = True) -> dict:
    """Cantilever (left end clamped) with a moment M at the right end.

    Theory: in pure bending the bending moment is the same in every cross-section,
    so the curvature κ = M/(E·I) is constant and the axis takes the shape of a CIRCULAR
    ARC of radius R = E·I/M. This solution is exact also for large deflections
    (geometric nonlinearity), which makes it a good check of the Cosserat rod.
    Point on the arc at arc length s:  x = R·sin(s/R),  y = R·(1 − cos(s/R)).
    """
    rc, s1 = cfg.rod, cfg.stage1
    EI = bending_stiffness(rc)
    M = s1.tip_angle * EI / rc.length

    sim = FishSimulator()
    rod = make_rod(rc)
    sim.append(rod)
    sim.constrain(rod).using(ea.OneEndFixedBC, constrained_position_idx=(0,),
                             constrained_director_idx=(0,))
    # Moment about +Z -> deflection in the XY plane (sideways, like a fish tail).
    sim.add_forcing_to(rod).using(EndpointTorque, torque_global=[0.0, 0.0, M],
                                  ramp_time=s1.ramp_time)
    dt = stable_time_step(rod, cfg.numerics.dt_safety)
    sim.dampen(rod).using(ea.AnalyticalLinearDamper, uniform_damping_constant=s1.damping,
                          time_step=dt)
    sim.finalize()
    integrate(sim, [rod], dt, s1.t_static, max_dilatation=cfg.numerics.max_dilatation,
              verbose=verbose, label="stage1 arc")

    s = np.linspace(0.0, rc.length, rc.n_elements + 1)
    R = EI / M
    x_th, y_th = R * np.sin(s / R), R * (1.0 - np.cos(s / R))
    x, y = rod.position_collection[0].copy(), rod.position_collection[1].copy()
    tip_th = np.hypot(x_th[-1], y_th[-1])
    tip_err = np.hypot(x[-1] - x_th[-1], y[-1] - y_th[-1]) / tip_th
    shape_err = np.max(np.hypot(x - x_th, y - y_th)) / rc.length
    kappa = rod.kappa[0].copy()   # curvature about d1 (= Z axis) at the Voronoi nodes
    return dict(s=s, x=x, y=y, x_th=x_th, y_th=y_th, M=M, EI=EI, R=R, dt=dt,
                kappa=kappa, kappa_th=M / EI, tip_err=tip_err, shape_err=shape_err)


def cantilever_mode_shape(x, L):
    """1st mode shape of a cantilever (Euler-Bernoulli), normalized to 1 at the tip."""
    bL = 1.875104068711961
    b = bL / L
    sig = (np.cosh(bL) + np.cos(bL)) / (np.sinh(bL) + np.sin(bL))
    phi = np.cosh(b * x) - np.cos(b * x) - sig * (np.sinh(b * x) - np.sin(b * x))
    return phi / phi[-1]


def natural_frequency_theory(rc) -> float:
    """ω₁ = 1.875²·√(E·I / (ρ·A·L⁴))  [rad/s]."""
    A = np.pi * rc.radius**2
    return 1.875104068711961**2 * np.sqrt(bending_stiffness(rc) / (rc.density * A * rc.length**4))


def cantilever_free_vibration(cfg: Config, verbose: bool = True) -> dict:
    """Free vibration of a cantilever WITHOUT damping and without water.

    At the start we impose a transverse velocity shaped like the 1st mode, so the rod
    vibrates mainly in the 1st mode. The frequency is measured from the zero crossings
    of the tip displacement. Side benefit: without damping the total energy should be
    constant (PositionVerlet is symplectic – the energy error oscillates, it does not grow).
    """
    rc, s1 = cfg.rod, cfg.stage1
    sim = FishSimulator()
    rod = make_rod(rc)
    sim.append(rod)
    sim.constrain(rod).using(ea.OneEndFixedBC, constrained_position_idx=(0,),
                             constrained_director_idx=(0,))
    dt = stable_time_step(rod, cfg.numerics.dt_safety)
    store: dict = {}
    every = max(1, int(round(cfg.numerics.save_every_s / dt)))
    sim.collect_diagnostics(rod).using(RodRecorder, step_skip=every, store=store, energy=True)
    # Initial velocity BEFORE finalize: finalize already calls the callback (sample at t = 0).
    x0 = rod.position_collection[0].copy()
    rod.velocity_collection[1, :] = s1.tip_velocity * cantilever_mode_shape(x0, rc.length)
    sim.finalize()
    E0 = total_energy(rod)
    integrate(sim, [rod], dt, s1.t_free, max_dilatation=cfg.numerics.max_dilatation,
              verbose=verbose, label="stage1 vibration")

    t = np.array(store["time"])
    y_tip = np.array([p[1, -1] for p in store["position"]])
    energy = np.array(store["energy"])
    # Zero crossings (linear interpolation) -> period = 2 × the spacing between them.
    yc = y_tip - y_tip.mean()
    idx = np.where(np.sign(yc[:-1]) * np.sign(yc[1:]) < 0)[0]
    tz = t[idx] - yc[idx] * (t[idx + 1] - t[idx]) / (yc[idx + 1] - yc[idx])
    period = 2.0 * np.mean(np.diff(tz))
    omega_sim = 2.0 * np.pi / period
    omega_th = natural_frequency_theory(rc)
    return dict(t=t, y_tip=y_tip, energy=energy, E0=E0, dt=dt,
                omega_sim=omega_sim, omega_th=omega_th,
                freq_err=abs(omega_sim - omega_th) / omega_th,
                energy_drift=np.max(np.abs(energy - E0)) / E0)


def coarse(cfg: Config, n_elements: int) -> Config:
    """Copy of the configuration with a different number of elements (faster tests, convergence study)."""
    return replace(cfg, rod=replace(cfg.rod, n_elements=n_elements))


# ---------------------------------------------------------------- stage 2: internal actuation
def build_fish(cfg: Config, clamped: bool, damping: float, actuation: str = "rest_curvature"):
    """Fish in vacuum (no water, no gravity). Returns (sim, rod, actuator, dt, rc).

    clamped=True: head clamped (first node and first element), as on a test bench.
    actuation: "rest_curvature" (recommended), "torque_pair" (equivalent), "single_torque" (WRONG).
    """
    rc = fish_rod_config(cfg)
    sim = FishSimulator()
    rod = make_fish_rod(rc, cfg.fish)
    sim.append(rod)
    if clamped:
        sim.constrain(rod).using(ea.OneEndFixedBC, constrained_position_idx=(0,),
                                 constrained_director_idx=(0,))
    dt = stable_time_step(rod, cfg.numerics.dt_safety)
    holder = {}
    if actuation == "torque_pair":
        sim.add_forcing_to(rod).using(_LazyForcing, holder=holder, forcing_cls=TorquePair, rc=rc)
    elif actuation == "single_torque":
        sim.add_forcing_to(rod).using(_LazyForcing, holder=holder, forcing_cls=SingleTorque, rc=rc)
    elif actuation != "rest_curvature":
        raise ValueError(actuation)
    if damping > 0:
        sim.dampen(rod).using(ea.AnalyticalLinearDamper, uniform_damping_constant=damping,
                              time_step=dt)
    return sim, rod, holder, dt, rc


class _LazyForcing(ea.NoForces):
    """Forcing whose actual object is created only after finalize (once the actuator is known)."""

    def __init__(self, holder, forcing_cls, rc):
        super().__init__()
        self.holder, self.cls, self.rc, self.inner = holder, forcing_cls, rc, None

    def apply_torques(self, system, time=np.float64(0.0)):
        if self.inner is None:
            self.inner = self.cls(self.holder["actuator"], self.rc)
        self.inner.apply_torques(system, time)


def _finish(sim, rod, holder, cfg, rc, actuation="rest_curvature"):
    sim.finalize()
    act = ChamberActuator(rod, rc, cfg.fish.chamber_zone, cfg.hydraulics.A_r)
    holder["actuator"] = act
    if actuation != "rest_curvature":
        # with torque actuation κ_rest stays zero – we only store Δp
        act.set_rest_curvature = lambda dp: setattr(act, "dp", float(dp))
    return act


def theory_shape(cfg: Config, dp: float, n: int = 4000):
    """Static shape from theory: without loads κ(s) = κ_rest(s) = −A_r·Δp / (E·I₁(s))
    in the chamber zone; tangent angle φ(s) = ∫κ ds, position = ∫(cos φ, sin φ) ds."""
    rc, fc = fish_rod_config(cfg), cfg.fish
    s = np.linspace(0.0, rc.length, n)
    a, b = fish_profile(fc, rc, s)
    if fc.cross_section == "circle":
        a = b = np.sqrt(a * b)
    B1 = rc.youngs_modulus * np.pi * a**3 * b / 4.0
    z0, z1 = fc.chamber_zone
    kappa = np.where((s >= z0) & (s <= z1), -cfg.hydraulics.A_r * dp / B1, 0.0)
    phi = np.concatenate([[0.0], np.cumsum(0.5 * (kappa[1:] + kappa[:-1]) * np.diff(s))])
    ds = np.diff(s)
    x = np.concatenate([[0.0], np.cumsum(ds * np.cos(0.5 * (phi[1:] + phi[:-1])))])
    y = np.concatenate([[0.0], np.cumsum(ds * np.sin(0.5 * (phi[1:] + phi[:-1])))])
    return x, y, -phi[-1]


def static_bend_pressure(cfg: Config, dp: float, verbose: bool = False) -> dict:
    """Head clamped, prescribed Δp (no pump) -> static tail deflection."""
    s2 = cfg.stage2
    sim, rod, holder, dt, rc = build_fish(cfg, clamped=True, damping=s2.damping)
    act = _finish(sim, rod, holder, cfg, rc)

    def hook(t, dt_h):
        act.set_rest_curvature(dp * smooth_ramp(t, s2.ramp_time)[0])

    every = max(1, int(cfg.hydraulics.dt_hydraulics / dt))
    integrate(sim, [rod], dt, s2.t_static, hook=hook, hook_every=every,
              max_dilatation=cfg.numerics.max_dilatation, verbose=verbose,
              label=f"stage2 Δp={dp:.0f}")
    x_th, y_th, phi_tip = theory_shape(cfg, dp)
    return dict(dp=dp, theta=act.theta(), theta_th=act.theory_theta(dp),
                x=rod.position_collection[0].copy(), y=rod.position_collection[1].copy(),
                x_th=x_th, y_th=y_th, tip_y=float(rod.position_collection[1, -1]),
                tip_y_th=float(y_th[-1]), dt=dt)


def static_bend_volume(cfg: Config, V_p: float, verbose: bool = False) -> dict:
    """Head clamped, the pump has transferred V_p and stopped -> hydraulics <-> rod coupling.

    Theory (steady state, κ = κ_rest):  θ = A_r·Δp·Λ,  Λ = ∫ds/B₁  and
    V_p = A_r·θ + C_h·Δp   ->   Δp = V_p / (C_h + A_r²·Λ).
    Part of the volume goes into bending the tail (A_r²Λ), part into bulging the walls (C_h).
    """
    s2, hc = cfg.stage2, cfg.hydraulics
    sim, rod, holder, dt, rc = build_fish(cfg, clamped=True, damping=s2.damping)
    act = _finish(sim, rod, holder, cfg, rc)
    # The pump transfers V_p smoothly (a rhythm with zero amplitude and constant V_bias, with a ramp);
    # a ready-made V_p at the start would be a pressure step V_p/C_h (~25 kPa per ml) and a shock.
    hyd = TailHydraulics(hc, TailRhythm(hc, amp=0.0, bias=V_p))
    every = max(1, int(hc.dt_hydraulics / dt))

    def hook(t, dt_h):
        act.set_rest_curvature(hyd.step(t, act.theta(), dt_h))

    integrate(sim, [rod], dt, s2.t_static, hook=hook, hook_every=every,
              max_dilatation=cfg.numerics.max_dilatation, verbose=verbose, label="stage2 V_p")
    Lam = act.Lambda
    dp_th = V_p / (hc.C_h + hc.A_r**2 * Lam)
    return dict(V_p=V_p, V_p_sim=hyd.V_p, dp=act.dp, dp_th=dp_th, theta=act.theta(),
                theta_th=hc.A_r * dp_th * Lam)


def free_vacuum(cfg: Config, actuation: str = "rest_curvature", verbose: bool = False) -> dict:
    """Free fish in vacuum, the pump runs rhythmically. Internal actuation cannot move
    the center of mass or rotate the fish as a whole (momentum and angular momentum = 0)."""
    s2, hc = cfg.stage2, cfg.hydraulics
    sim, rod, holder, dt, rc = build_fish(cfg, clamped=False, damping=s2.free_damping,
                                          actuation=actuation)
    act = _finish(sim, rod, holder, cfg, rc, actuation)
    hyd = TailHydraulics(hc, TailRhythm(hc))
    every = max(1, int(hc.dt_hydraulics / dt))
    log = {k: [] for k in ("t", "x_cm", "L", "theta", "dp", "V_sum", "heading", "u")}
    rec_every = max(1, int(round(cfg.numerics.save_every_s / (every * dt))))
    counter = [0]
    x0 = rod.compute_position_center_of_mass().copy()
    snapshots = []

    def hook(t, dt_h):
        dp = hyd.step(t, act.theta(), dt_h)
        act.set_rest_curvature(dp)
        if counter[0] % rec_every == 0:
            log["t"].append(t)
            log["x_cm"].append(rod.compute_position_center_of_mass() - x0)
            log["L"].append(angular_momentum(rod))
            log["theta"].append(act.theta())
            log["dp"].append(dp)
            log["V_sum"].append(hyd.V_L + hyd.V_R)
            d3 = rod.director_collection[2, :, 0]       # head axis
            log["heading"].append(np.arctan2(d3[1], d3[0]))
            log["u"].append(hyd.u)
            if t >= s2.t_free - 1.0 / hc.tail_freq and len(snapshots) < 8 \
                    and counter[0] % (rec_every * 60) == 0:
                snapshots.append(rod.position_collection[:2].copy())
        counter[0] += 1

    integrate(sim, [rod], dt, s2.t_free, hook=hook, hook_every=every,
              max_dilatation=cfg.numerics.max_dilatation, verbose=verbose,
              label=f"stage2 vacuum {actuation}")
    out = {k: np.array(v) for k, v in log.items()}
    out.update(actuation=actuation, mass=float(rod.mass.sum()), length=rc.length,
               snapshots=snapshots, dt=dt, hydraulics_every=every)
    return out


# ---------------------------------------------------------------- stage 3: tethered tail in water
def head_indices(rc, fc):
    """Nodes and elements of the stiff head (to be held fixed)."""
    n_e = int(np.sum(element_centers(rc) < fc.head_length))
    return tuple(range(n_e + 1)), tuple(range(n_e))


def steady_amplitude_phase(t, y, ref, f):
    """Amplitude and phase of the 1st harmonic of signal y relative to signal ref (projection on sin/cos)."""
    w = 2 * np.pi * f
    def h1(x):
        c = 2 * np.mean(x * np.cos(w * t))
        s = 2 * np.mean(x * np.sin(w * t))
        return np.hypot(c, s), np.arctan2(c, s)
    A, ph = h1(y - y.mean())
    _, ph_ref = h1(ref - ref.mean())
    return A, np.degrees((ph - ph_ref + np.pi) % (2 * np.pi) - np.pi)


def tethered(cfg: Config, model: str, verbose: bool = False) -> dict:
    """Head held fixed, the pump flaps the tail sinusoidally, water according to `model`.

    Tethered thrust: the force with which the mount must hold the fish. From the momentum
    balance R + F_water = dP/dt; in steady periodic motion the mean dP/dt = 0, so the
    mean reaction = −mean(F_water). Thrust T = −mean(F_water,x) > 0 when the water
    pushes the fish towards the head (head at x = 0, tail towards +X, the fish "swims" in −X).
    """
    s3, hc = cfg.stage3, cfg.hydraulics
    cfg = replace(cfg, water=replace(cfg.water, model=model))
    rc = fish_rod_config(cfg)
    sim = FishSimulator()
    rod = make_fish_rod(rc, cfg.fish)
    sim.append(rod)
    pos_idx, dir_idx = head_indices(rc, cfg.fish)
    sim.constrain(rod).using(ea.FixedConstraint, constrained_position_idx=pos_idx,
                             constrained_director_idx=dir_idx)
    a, b = section_half_axes(rc, cfg.fish)
    water = add_water(sim, rod, cfg, a, b)
    dt = stable_time_step(rod, cfg.numerics.dt_safety)
    if s3.damping > 0:
        sim.dampen(rod).using(ea.AnalyticalLinearDamper, uniform_damping_constant=s3.damping,
                              time_step=dt)
    holder = {}
    act = _finish(sim, rod, holder, cfg, rc)
    hyd = TailHydraulics(hc, TailRhythm(hc))
    every = max(1, int(hc.dt_hydraulics / dt))
    rec_every = max(1, int(round(cfg.numerics.save_every_s / (every * dt))))
    keys = ("t", "tip_y", "theta", "dp", "V_ref", "F_drag", "F_react", "P_drag", "P_react", "u")
    log = {k: [] for k in keys}
    snaps = []
    counter = [0]

    def hook(t, dt_h):
        dp = hyd.step(t, act.theta(), dt_h)
        act.set_rest_curvature(dp)
        if counter[0] % rec_every == 0:
            log["t"].append(t)
            log["tip_y"].append(rod.position_collection[1, -1])
            log["theta"].append(act.theta())
            log["dp"].append(dp)
            log["V_ref"].append(hyd.rhythm.v_ref(t)[0])
            log["u"].append(hyd.u)
            w = water.get("water") if water is not None else None
            log["F_drag"].append(w.drag_total[:3].copy() if w is not None else np.zeros(3))
            log["F_react"].append(w.reactive_total[:3].copy() if w is not None else np.zeros(3))
            log["P_drag"].append(w.drag_total[3] if w is not None else 0.0)
            log["P_react"].append(w.reactive_total[3] if w is not None and w.reactive else 0.0)
            if t >= s3.t_end - 1.0 / hc.tail_freq and counter[0] % (rec_every * 50) == 0:
                snaps.append(rod.position_collection[:2].copy())
        counter[0] += 1

    integrate(sim, [rod], dt, s3.t_end, hook=hook, hook_every=every,
              max_dilatation=cfg.numerics.max_dilatation, verbose=verbose,
              label=f"stage3 {model}")
    out = {k: np.array(v) for k, v in log.items()}
    m = out["t"] >= s3.t_analyze
    F = out["F_drag"] + out["F_react"]
    # Phase of the tip deflection to the RIGHT (−y) relative to V_ref: V_p > 0 bends the tail
    # to the right, so 0° = the tail follows the pump, negative = lag (inertia, water).
    amp, phase = steady_amplitude_phase(out["t"][m], -out["tip_y"][m], out["V_ref"][m], hc.tail_freq)
    out.update(model=model, snapshots=snaps, dt=dt, amp_tip=amp, phase_tip=phase,
               thrust=float(-np.mean(F[m, 0])),
               thrust_drag=float(-np.mean(out["F_drag"][m, 0])),
               thrust_react=float(-np.mean(out["F_react"][m, 0])),
               lateral_amp=float(0.5 * np.ptp(F[m, 1])),
               theta_amp=float(0.5 * np.ptp(out["theta"][m])),
               dp_amp=float(0.5 * np.ptp(out["dp"][m])))
    return out


# ---------------------------------------------------------------- stage 4: free swimming
def _yaw(e) -> float:
    return float(np.arctan2(e[1], e[0]))


def heading_vector(rod) -> np.ndarray:
    """The fish's "forward" direction: from tail to nose along the stiff head (−d3 of element 0)."""
    return -rod.director_collection[2, :, 0]


def free_swim(cfg: Config, model: str, damper: str | None = None, verbose: bool = False) -> dict:
    """Free fish in water (no gravity or buoyancy), the pump flaps the tail.

    Forward speed U = v_cm · ê, ê – nose direction. At the start the fish may turn slightly
    (the first tail stroke is asymmetric), so we measure speed along the fish axis rather
    than along −X. Averaging over a period removes the fluctuations at the flapping rhythm.
    """
    s4, hc = cfg.stage4, cfg.hydraulics
    damper = damper or s4.damper
    cfg = replace(cfg, water=replace(cfg.water, model=model))
    rc = fish_rod_config(cfg)
    sim = FishSimulator()
    rod = make_fish_rod(rc, cfg.fish)
    sim.append(rod)
    a, b = section_half_axes(rc, cfg.fish)
    water = add_water(sim, rod, cfg, a, b)
    dt = stable_time_step(rod, cfg.numerics.dt_safety)
    if damper == "laplace":
        sim.dampen(rod).using(ea.LaplaceDissipationFilter, filter_order=s4.filter_order)
    elif damper == "analytical":
        sim.dampen(rod).using(ea.AnalyticalLinearDamper,
                              uniform_damping_constant=s4.analytical_damping, time_step=dt)
    elif damper != "none":
        raise ValueError(damper)
    holder = {}
    act = _finish(sim, rod, holder, cfg, rc)
    hyd = TailHydraulics(hc, TailRhythm(hc))
    every = max(1, int(hc.dt_hydraulics / dt))
    rec_every = max(1, int(round(cfg.numerics.save_every_s / (every * dt))))
    frame_every = max(1, int(round(s4.save_every_s / (every * dt))))
    log = {k: [] for k in ("t", "x_cm", "v_cm", "heading", "theta", "dp", "z_max")}
    frames, frame_t = [], []
    counter = [0]

    def hook(t, dt_h):
        dp = hyd.step(t, act.theta(), dt_h)
        act.set_rest_curvature(dp)
        c = counter[0]
        if c % rec_every == 0:
            log["t"].append(t)
            log["x_cm"].append(rod.compute_position_center_of_mass())
            log["v_cm"].append(rod.compute_velocity_center_of_mass())
            log["heading"].append(heading_vector(rod))
            log["theta"].append(act.theta())
            log["dp"].append(dp)
            log["z_max"].append(np.max(np.abs(rod.position_collection[2])))
        if c % frame_every == 0:
            frames.append(rod.position_collection.copy())
            frame_t.append(t)
        counter[0] += 1

    integrate(sim, [rod], dt, s4.t_end, hook=hook, hook_every=every,
              max_dilatation=cfg.numerics.max_dilatation, verbose=verbose,
              label=f"stage4 {model}/{damper}")
    out = {k: np.array(v) for k, v in log.items()}
    U = np.einsum("ij,ij->i", out["v_cm"], out["heading"])
    T = 1.0 / hc.tail_freq
    n_win = max(1, int(round(T / (out["t"][1] - out["t"][0]))))
    # moving average over the PREVIOUS period (at the beginning – over what is available)
    cs = np.concatenate([[0.0], np.cumsum(U)])
    i = np.arange(1, len(U) + 1)
    U_avg = (cs[i] - cs[np.maximum(i - n_win, 0)]) / np.minimum(i, n_win)
    tail = out["t"] >= s4.t_end - 2.0          # last 2 s – (nearly) steady speed
    disp = out["x_cm"][-1] - out["x_cm"][0]
    # Tail tip amplitude in the fish frame (last 2 periods): deviation of the tip from the
    # line through the center of mass in the nose direction. Strouhal number St = f·(2A)/U –
    # fish swim most efficiently at St ≈ 0.2–0.4.
    fr = np.array(frames)
    ft = np.array(frame_t)
    lastp = ft >= s4.t_end - 2 * T
    lat = []
    for p in fr[lastp]:
        e = -(p[:2, -1] - p[:2, 0])
        e /= np.linalg.norm(e)
        c = p[:2].mean(axis=1)
        r = p[:2, -1] - c
        lat.append(e[0] * r[1] - e[1] * r[0])    # 2D cross product (z component)
    tip_amp = 0.5 * float(np.ptp(lat)) if lat else 0.0
    U_end = float(np.mean(U[tail]))
    out.update(tip_amp=tip_amp,
               strouhal=float(hc.tail_freq * 2 * tip_amp / U_end) if U_end > 1e-3 else np.nan)
    out.update(model=model, damper=damper, U=U, U_avg=U_avg, dt=dt,
               U_final=float(np.mean(U[tail])),
               distance=float(np.linalg.norm(disp[:2])),
               frames=np.array(frames), frame_t=np.array(frame_t),
               length=rc.length, mass=float(rod.mass.sum()),
               heading_change=float(np.degrees(np.angle(np.exp(1j * (
                   _yaw(out["heading"][-1]) - _yaw(out["heading"][0])))))),
               reynolds=float(abs(np.mean(U[tail])) * rc.length * cfg.water.rho / cfg.water.mu))
    return out


# ---------------------------------------------------------------- stage 5: sweep of f and E
def sweep_config(cfg: Config, freq: float, E_factor: float) -> Config:
    return replace(cfg,
                   rod=replace(cfg.rod, youngs_modulus=cfg.rod.youngs_modulus * E_factor),
                   hydraulics=replace(cfg.hydraulics, tail_freq=freq),
                   stage4=replace(cfg.stage4, t_end=cfg.stage5.t_end))


def sweep_point(cfg: Config, freq: float, E_factor: float) -> dict:
    r = free_swim(sweep_config(cfg, freq, E_factor), "drag+reactive")
    # the summary results need neither frames nor full time histories
    return dict(freq=freq, E_factor=E_factor, U=r["U_final"], tip_amp=r["tip_amp"],
                strouhal=r["strouhal"], theta_amp=float(0.5 * np.ptp(r["theta"][-int(len(r["theta"]) / 6):])),
                dp_amp=float(0.5 * np.ptp(r["dp"][-int(len(r["dp"]) / 6):])), length=r["length"])


def tail_natural_frequency(cfg: Config, E_factor: float = 1.0) -> dict:
    """Natural frequency of the fish tail: head held fixed, pump stopped, vacuum.

    The hydraulics are coupled (closed chambers = a "hydraulic spring" k_h = A_r²/C_h
    added to the stiffness of the chamber zone), because that is what the tail looks like in operation.
    Start: transverse velocity growing quadratically from the end of the head to the tail tip
    (approximately the 1st mode). Frequency from the zero crossings of the tip deflection.
    Water is not included here: in water the added mass would lower f_n, and our model
    (without distributed added mass) does not have this effect.
    """
    s5, hc = cfg.stage5, cfg.hydraulics
    cfg = replace(cfg, rod=replace(cfg.rod, youngs_modulus=cfg.rod.youngs_modulus * E_factor))
    rc = fish_rod_config(cfg)
    sim = FishSimulator()
    rod = make_fish_rod(rc, cfg.fish)
    sim.append(rod)
    pos_idx, dir_idx = head_indices(rc, cfg.fish)
    sim.constrain(rod).using(ea.FixedConstraint, constrained_position_idx=pos_idx,
                             constrained_director_idx=dir_idx)
    dt = stable_time_step(rod, cfg.numerics.dt_safety)
    x = rod.position_collection[0].copy()
    sh = cfg.fish.head_length
    rod.velocity_collection[1, :] = s5.tip_velocity * np.clip((x - sh) / (rc.length - sh), 0, None) ** 2
    holder = {}
    act = _finish(sim, rod, holder, cfg, rc)
    hyd = TailHydraulics(hc)          # no rhythm: pump stopped, chambers closed
    every = max(1, int(hc.dt_hydraulics / dt))
    t_log, y_log = [], []

    def hook(t, dt_h):
        act.set_rest_curvature(hyd.step(t, act.theta(), dt_h))
        t_log.append(t)
        y_log.append(rod.position_collection[1, -1])

    integrate(sim, [rod], dt, s5.t_free, hook=hook, hook_every=every,
              max_dilatation=cfg.numerics.max_dilatation, verbose=False)
    t, y = np.array(t_log), np.array(y_log)
    yc = y - y.mean()
    idx = np.where(np.sign(yc[:-1]) * np.sign(yc[1:]) < 0)[0]
    tz = t[idx] - yc[idx] * (t[idx + 1] - t[idx]) / (yc[idx + 1] - yc[idx])
    f_n = 1.0 / (2.0 * np.mean(np.diff(tz)))
    return dict(E_factor=E_factor, f_n=float(f_n), t=t, y=y)


# ---------------------------------------------------------------- stage 6: 3D, buoyancy, ballast
def z_reference(schedule, t: float) -> float:
    z = schedule[0][1]
    for t_i, z_i in schedule:
        if t >= t_i:
            z = z_i
    return z


def depth_control(cfg: Config, verbose: bool = False, t_end: float | None = None,
                  depth_pid: bool = True, V_offset: float = 0.0, swim: bool | None = None) -> dict:
    """Fish in 3D: weight + buoyancy + bladder, depth PID controller, the tail is working.

    Neutral bladder volume (buoyancy = weight):  ρ_w·(V_body + V_n) = m  ->
    V_n = m/ρ_w − V_body. With ρ_s > ρ_w the body sinks on its own and the bladder must make up for it.
    depth_pid=False: the bladder is held at V_n + V_offset (buoyancy test).
    """
    s6, hc, bc = cfg.stage6, cfg.hydraulics, cfg.buoyancy
    t_end = s6.t_end if t_end is None else t_end
    swim = s6.swim if swim is None else swim
    cfg = replace(cfg, water=replace(cfg.water, model="drag+reactive"))
    rc = fish_rod_config(cfg)
    sim = FishSimulator()
    rod = make_fish_rod(rc, cfg.fish, start=np.array([0.0, 0.0, s6.z0]))
    sim.append(rod)
    a, b = section_half_axes(rc, cfg.fish)
    water = add_water(sim, rod, cfg, a, b)

    mass = float(rod.mass.sum())
    V_body = float(rod.volume.sum())
    V_n = mass / cfg.water.rho - V_body
    if not (bc.V_min < V_n < bc.V_max):
        raise ValueError(f"neutral bladder volume {V_n*1e6:.1f} ml is outside the bladder range")
    s_e = element_centers(rc)
    m_e = rc.density * rod.volume
    s_b = float(np.sum(m_e * s_e) / np.sum(m_e)) if bc.bladder_s is None else bc.bladder_s
    bladder_idx = int(np.argmin(np.abs(s_e - s_b)))
    bladder = Bladder(bc, V_n + V_offset)
    holder = {}
    sim.add_forcing_to(rod).using(BuoyancyForces, holder=holder, density=rc.density,
                                  rho_w=cfg.water.rho, g=bc.g, h_g=bc.h_g,
                                  bladder_idx=bladder_idx, z_b=bc.z_b, bladder=bladder)
    dt = stable_time_step(rod, cfg.numerics.dt_safety)
    sim.dampen(rod).using(ea.LaplaceDissipationFilter, filter_order=cfg.stage4.filter_order)
    act = _finish(sim, rod, holder, cfg, rc)
    hyd = TailHydraulics(hc, TailRhythm(hc) if swim else None)
    pid = DepthPID(bc, V_n, z_reference(s6.schedule, 0.0))
    every = max(1, int(hc.dt_hydraulics / dt))
    ctrl_every = max(1, int(round(bc.dt_control / (every * dt))))
    rec_every = max(1, int(round(0.02 / (every * dt))))
    log = {k: [] for k in ("t", "z", "z_ref", "V_b", "V_ref", "pitch", "roll", "U", "x_cm")}
    counter = [0]
    V_ref = [bladder.V]

    def hook(t, dt_h):
        c = counter[0]
        act.set_rest_curvature(hyd.step(t, act.theta(), dt_h))
        if c % ctrl_every == 0:
            x_cm = rod.compute_position_center_of_mass()
            v_cm = rod.compute_velocity_center_of_mass()
            if depth_pid:
                pid.z_ref = z_reference(s6.schedule, t)
                V_ref[0] = pid.update(x_cm[2], v_cm[2], ctrl_every * dt_h)
        bladder.step(V_ref[0], dt_h)
        if c % rec_every == 0:
            x_cm = rod.compute_position_center_of_mass()
            v_cm = rod.compute_velocity_center_of_mass()
            d1 = rod.director_collection[0, :, bladder_idx]   # cross-section "up"
            d3 = rod.director_collection[2, :, bladder_idx]   # axis (towards the tail)
            e = -d3
            log["t"].append(t)
            log["z"].append(x_cm[2])
            log["z_ref"].append(pid.z_ref)
            log["V_b"].append(bladder.V)
            log["V_ref"].append(V_ref[0])
            # pitch: angle of the axis above horizontal (+ = nose up); roll: sideways tilt of d1 from vertical
            log["pitch"].append(np.degrees(np.arcsin(np.clip(e[2], -1, 1))))
            side = np.cross(e, np.array([0.0, 0.0, 1.0]))
            n_side = np.linalg.norm(side)
            log["roll"].append(np.degrees(np.arcsin(np.clip(np.dot(d1, side / n_side), -1, 1)))
                               if n_side > 1e-9 else 0.0)
            log["U"].append(float(np.dot(v_cm, e)))
            log["x_cm"].append(x_cm)
        counter[0] += 1

    integrate(sim, [rod], dt, t_end, hook=hook, hook_every=every,
              max_dilatation=cfg.numerics.max_dilatation, verbose=verbose, label="stage6 depth")
    out = {k: np.array(v) for k, v in log.items()}
    out.update(V_neutral=V_n, mass=mass, V_body=V_body, s_bladder=s_e[bladder_idx], dt=dt,
               length=rc.length)
    return out
