"""Chamber hydraulics: pressure units (stage 2) and the antagonistic L↔R system (stage 4).

Units – established in stage 0 (scripts/probe_volume_growth.py): in SOFA v26.06 the
`pressure` field of SurfacePressureConstraint holds the constraint-solver impulse λ = p·dt,
not p. With valueType="pressure" the `value` input is also in units of p·dt.
All conversions are done ONLY here, so that pressure is in Pa in the rest of the code.

Antagonistic system (stage 4, spec section 6). Water is practically incompressible, so
the pump imposes VOLUME, not pressure: the chambers get valueType="volumeGrowth",
and SOFA computes the pressure needed for that volume. The rest of this file is pure numpy
(no SOFA), so it can be tested on its own:
  TailRhythm     – V_ref(t) and the pump command (port of MuJoCo/fishsim/controllers.py),
  ClosedLoopPump – first-order pump + relief valve on the pressure difference,
  TailHydraulics – prefill + rhythm + pump -> prescribed volume growth of both chambers.
"""
from dataclasses import dataclass

import numpy as np


def pressure_pa(spc, dt: float) -> float:
    """Chamber pressure [Pa] from the `pressure` field of a SurfacePressureConstraint."""
    return float(np.atleast_1d(spc.pressure.value)[0]) / dt


def pressure_input(p_pa: float, dt: float) -> float:
    """The `value` input for valueType="pressure" corresponding to pressure p_pa [Pa]."""
    return p_pa * dt


def smooth_ramp(t: float, T: float) -> tuple[float, float, float]:
    """Soft start a(t) = ½(1 − cos(πt/T)) for 0 ≤ t < T, 0 before, 1 after.
    Returns (a, da/dt, d²a/dt²).

    Continuous together with its derivative, so neither volume nor flow jumps (actuation
    jumps are a known cause of blow-ups in pressure-driven simulations)."""
    if t <= 0:
        return 0.0, 0.0, 0.0
    if T <= 0 or t >= T:
        return 1.0, 0.0, 0.0
    k = np.pi / T
    return 0.5 * (1 - np.cos(k * t)), 0.5 * k * np.sin(k * t), 0.5 * k * k * np.cos(k * t)


class TailRhythm:
    """V_ref(t) = a(t)·(A_V·sin(2πft) + V_bias), pump command with feed-forward + P.

    Why volume rather than a sinusoidal pump command: volume is the integral of flow, so
    u = A·sin(ωt) would give a volume amplitude ∝ 1/f (the frequency sweep in stage 6
    would mix two effects), and a constant offset would integrate without bound.

    u = clip((dV_ref/dt + τ_pump·d²V_ref/dt² + K_v·(V_ref − V_p)) / Q_max, −1, 1)
    When 2πf·A_V > Q_max, the pump saturates (|u| = 1) and the amplitude drops.

    The τ_pump·d²V_ref/dt² term (absent in MuJoCo) inverts the first-order pump lag: without
    it, at 2 Hz (ωτ = 0.38) the loop overshoots – V_p reached 1.16·A_V
    (19.7 ml with A_V = 17 ml), and chamber R nearly its rest volume. With it the
    tracking error is ~1% of A_V (test test_pump_tracks_v_ref).
    Difference from MuJoCo: here the ramp a(t) also multiplies V_bias (in MuJoCo the bias
    applies immediately), so that a nonzero bias does not cause a volume jump.
    """

    def __init__(self, cfg, freq=None, amp=None, bias=None):
        self.cfg = cfg
        self.freq = cfg.tail_freq if freq is None else freq
        self.amp = cfg.tail_volume_amp if amp is None else amp
        self.bias = cfg.tail_volume_bias if bias is None else bias

    def v_ref(self, t: float) -> tuple[float, float, float]:
        """(V_ref, dV_ref/dt, d²V_ref/dt²) [m³, m³/s, m³/s²]; t measured from the start of the rhythm."""
        w = 2 * np.pi * self.freq
        a, da, dda = smooth_ramp(t, self.cfg.ramp_time)
        s, c = np.sin(w * t), np.cos(w * t)
        base = self.amp * s + self.bias
        A = self.amp
        return (a * base, da * base + a * A * w * c,
                dda * base + 2 * da * A * w * c - a * A * w * w * s)

    def command(self, t: float, V_p: float) -> float:
        v, dv, ddv = self.v_ref(t)
        c = self.cfg
        u = (dv + c.tau_pump * ddv + c.K_v * (v - V_p)) / c.Q_max
        return float(np.clip(u, -1.0, 1.0))


class ClosedLoopPump:
    """Pump transferring fluid from R to L in a closed circuit + relief valve.

    States: Q – pump flow [m³/s] (first-order lag, dQ/dt = (u·Q_max − Q)/τ_pump),
            V_p – volume pumped from R to L [m³].
    Explicit Euler: stable and accurate, since dt ≪ τ_pump (2 ms vs 30 ms).

    The relief valve connects the chambers: in a closed circuit the pump works against
    Δp = p_L − p_R, so the valve looks at Δp, not at the pressure of one chamber. When
    |Δp| > p_max, it passes Q_valve = valve_conductance·(|Δp| − p_max) from the
    higher-pressure chamber to the other. The total volume does not change – the valve
    only changes V_p. The pressure is known only after the SOFA step is solved, so the
    valve reacts to Δp from the previous step (1-step delay).
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.Q = 0.0
        self.V_p = 0.0
        self.Q_valve = 0.0      # [m³/s], > 0 = from L to R
        self.valve_open = False

    def step(self, u: float, dp: float, dt: float):
        c = self.cfg
        self.Q += dt * (float(np.clip(u, -1.0, 1.0)) * c.Q_max - self.Q) / c.tau_pump
        self.V_p += self.Q * dt
        excess = abs(dp) - c.p_max
        self.valve_open = excess > 0
        self.Q_valve = np.sign(dp) * c.valve_conductance * excess if self.valve_open else 0.0
        self.V_p -= self.Q_valve * dt


@dataclass
class HydraulicsState:
    t: float
    V_ref: float
    V_p: float
    u: float
    Q: float
    Q_valve: float
    valve_open: bool
    prefill: float
    dV_L: float      # prescribed volume growth of chamber L [m³]
    dV_R: float


class TailHydraulics:
    """Prefill of both chambers, then the rhythm: ΔV_L = prefill + V_p, ΔV_R = prefill − V_p.

    Phase 1 (0 … prefill_time): both chambers ramp-filled to V_prefill, pump idle.
    Phase 2: rhythm with its own amplitude ramp (ramp_time), rhythm time measured from the
    end of the prefill. Chamber wall contact is not modeled, so the config enforces
    V_prefill > |V_bias| + A_V + margin (the chamber never goes below its rest volume).
    """

    def __init__(self, cfg, rhythm: TailRhythm | None = None):
        self.cfg = cfg
        self.rhythm = rhythm or TailRhythm(cfg)
        self.pump = ClosedLoopPump(cfg)

    def step(self, t: float, dp: float, dt: float) -> HydraulicsState:
        """Step from t to t + dt. dp = p_L − p_R [Pa] from the previous step.
        Returns the state with the prescribed volumes at the end of the step (t + dt)."""
        c = self.cfg
        t_r = t - c.prefill_time
        u = self.rhythm.command(t_r, self.pump.V_p) if t_r >= 0 else 0.0
        self.pump.step(u, dp, dt)
        prefill = c.V_prefill * smooth_ramp(t + dt, c.prefill_time)[0]
        V_ref = self.rhythm.v_ref(t_r + dt)[0] if t_r + dt >= 0 else 0.0
        p = self.pump
        return HydraulicsState(t + dt, V_ref, p.V_p, u, p.Q, p.Q_valve, p.valve_open,
                               prefill, prefill + p.V_p, prefill - p.V_p)
