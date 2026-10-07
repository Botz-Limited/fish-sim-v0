"""Time integration loop.

A manual loop instead of ea.integrate: no tqdm progress bar (overhead), the ability to
call our own code every N steps (hydraulics, depth controller), NaN checks
and a run-time estimate before a long run.
"""

import time as _time

import numpy as np
import elastica as ea


class SimulationBlowUp(RuntimeError):
    pass


def integrate(sim, rods, dt: float, t_end: float, hook=None, hook_every: int = 1,
              check_every: int = 2000, max_dilatation: float = 1.5,
              verbose: bool = True, label: str = "") -> float:
    """Integrates `sim` from t = 0 to t_end with step dt (PositionVerlet).

    hook(t, dt_hook) – called every `hook_every` steps BEFORE the rod step
    (e.g. a step of the hydraulics ODE and writing the new rest curvature).
    Every `check_every` steps we check for NaN and element stretching (dilatation
    e = l/l₀ > max_dilatation) – then we stop with an exception instead of computing
    meaningless numbers. A NaN check alone is not enough: with too large a step the
    solution can grow to 1e20 without producing NaN for thousands of steps.
    """
    stepper = ea.PositionVerlet()
    n_steps = int(round(t_end / dt))
    t = np.float64(0.0)
    t_wall0 = _time.perf_counter()
    estimate_at = min(n_steps, 2000)
    for i in range(n_steps):
        if hook is not None and i % hook_every == 0:
            hook(float(t), hook_every * dt)
        t = stepper.step(sim, t, dt)
        if i + 1 == estimate_at and verbose and n_steps > 50_000:
            per_step = (_time.perf_counter() - t_wall0) / estimate_at
            print(f"  [{label}] {n_steps:,} steps, dt = {dt:.2e} s, "
                  f"estimated run time ≈ {per_step * n_steps:.0f} s", flush=True)
        if (i + 1) % check_every == 0:
            for rod in rods:
                if not np.all(np.isfinite(rod.position_collection)):
                    raise SimulationBlowUp(f"NaN at t = {float(t):.4f} s (dt = {dt:.2e})")
                e_max = float(np.max(rod.dilatation))
                if e_max > max_dilatation:
                    raise SimulationBlowUp(f"element stretched {e_max:.2f}× at "
                                           f"t = {float(t):.4f} s (dt = {dt:.2e})")
    return float(t)
