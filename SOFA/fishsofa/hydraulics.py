"""Chamber hydraulics: pressure units (stage 2) and the antagonistic L↔R system (stage 4).

Units – established in stage 0 (scripts/probe_volume_growth.py): in SOFA v26.06 the
`pressure` field of SurfacePressureConstraint holds the constraint-solver impulse λ = p·dt,
not p. With valueType="pressure" the `value` input is also in units of p·dt.
All conversions are done ONLY here, so that pressure is in Pa in the rest of the code.

Antagonistic system (stage 4, spec section 6). Water is practically incompressible, so
the pump imposes VOLUME, not pressure: the chambers get valueType="volumeGrowth",
and SOFA computes the pressure needed for that volume. The rest of this file is pure numpy
(no SOFA), so it can be tested on its own:
  TailRhythm     – V_ref(t) (port of MuJoCo/fishsim/controllers.py) and the hysteresis
                   relay choosing the valve direction s = ±1,
  ClosedLoopPump – constant-speed pump + directional valves (first-order switching lag)
                   + relief valve on the pressure difference,
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
    """V_ref(t) = a(t)·(A_V·sin(2πft) + V_bias) and the valve command (hysteresis relay).

    Why volume rather than a sinusoidal pump command: volume is the integral of flow, so
    u = A·sin(ωt) would give a volume amplitude ∝ 1/f (the frequency sweep in stage 6
    would mix two effects), and a constant offset would integrate without bound.

    The pump runs at constant speed; directional valves only choose the flow direction,
    s = +1 (R -> L) or s = −1 (L -> R) – there is no closed valve state. Relay with
    hysteresis δ = valve_hysteresis, s is kept between steps:
        e = V_ref − V_p;  e > δ -> s = +1;  e < −δ -> s = −1;  otherwise s unchanged.
    While 2πf·A_V < Q_const the relay tracks V_ref with a sawtooth (band ±δ plus an
    overshoot ~Q_const·tau_valve) at the cost of many valve switches per cycle. Above
    f_track = Q_const/(2π·A_V) tracking ends: the valve switches only at the peaks (2× per
    cycle), V_p is a triangle with amplitude ≈ Q_const/(4f) (less the tau_valve losses).
    Difference from MuJoCo: here the ramp a(t) also multiplies V_bias (in MuJoCo the bias
    applies immediately), so that a nonzero bias does not cause a volume jump.

    Hardware limits (as in MuJoCo): the valve holds each state for at least valve_min_dwell
    (≤ 5 switches/s), and the frequency is clamped to [tail_freq_min, tail_freq_max].
    Below the range tracking would need fast switching the valve cannot do; above it the
    valve cannot switch twice per cycle. With Q_const = 100 ml/s f_track ≈ 1.2 Hz lies below
    the range, so the relay switches at the peaks only (2× per cycle; ≈ 2.7× at 1.5 Hz).
    """

    def __init__(self, cfg, freq=None, amp=None, bias=None):
        self.cfg = cfg
        self.freq = self._clamp(cfg.tail_freq if freq is None else freq)
        self.amp = cfg.tail_volume_amp if amp is None else amp
        self.bias = cfg.tail_volume_bias if bias is None else bias
        self.reset()

    def reset(self):
        """Relay state back to the start value s = +1, phase offset zeroed."""
        self.s = 1
        self.t_switch = -np.inf   # [s] time of the last valve switch
        self.phase0 = 0.0         # [rad] phase offset – keeps the phase continuous when f changes

    def _clamp(self, freq: float) -> float:
        return float(np.clip(freq, self.cfg.tail_freq_min, self.cfg.tail_freq_max))

    def set_freq(self, freq: float, t: float):
        """Change the frequency during motion WITHOUT a phase jump (frequency clamped).

        Phase φ(t) = 2π·f·t + φ0; φ0 is chosen so that φ(t) stays continuous."""
        freq = self._clamp(freq)
        self.phase0 += 2 * np.pi * (self.freq - freq) * t
        self.freq = freq

    def v_ref(self, t: float) -> tuple[float, float]:
        """(V_ref, dV_ref/dt) [m³, m³/s]; t measured from the start of the rhythm."""
        w = 2 * np.pi * self.freq
        a, da, _ = smooth_ramp(t, self.cfg.ramp_time)
        sn, cs = np.sin(w * t + self.phase0), np.cos(w * t + self.phase0)
        base = self.amp * sn + self.bias
        return a * base, da * base + a * self.amp * w * cs

    def command(self, t: float, V_p: float) -> int:
        """Valve state s ∈ {+1, −1} for the step starting at t (relay with hysteresis,
        state held for at least valve_min_dwell after each switch)."""
        if t - self.t_switch < self.cfg.valve_min_dwell:
            return self.s
        e = self.v_ref(t)[0] - V_p
        d = self.cfg.valve_hysteresis
        s = self.s
        if e > d:
            s = 1
        elif e < -d:
            s = -1
        if s != self.s:
            self.s, self.t_switch = s, t
        return self.s


class ClosedLoopPump:
    """Constant-speed pump + directional valves in a closed R <-> L circuit + relief valve.

    States: Q – flow [m³/s], V_p – volume pumped from R to L [m³].
    Valve command s ∈ {+1, −1} (R -> L / L -> R); s = 0 only means "pump off" (before the
    rhythm), never a valve state. Valve switching + reversal of the stream is a first-order
    lag: dQ/dt = (s·Q_const − Q)/tau_valve.
    Explicit Euler: stable and accurate, since dt ≪ tau_valve (2 ms vs 20 ms).

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

    def step(self, s: int, dp: float, dt: float):
        c = self.cfg
        self.Q += dt * (float(np.sign(s)) * c.Q_const - self.Q) / c.tau_valve
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
    u: int           # valve state s = ±1 (R -> L / L -> R); 0 = pump off (prefill)
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

    def reset(self):
        """Back to the start of the simulation (relay s = +1, pump state zeroed)."""
        self.rhythm.reset()
        self.pump = ClosedLoopPump(self.cfg)

    def step(self, t: float, dp: float, dt: float) -> HydraulicsState:
        """Step from t to t + dt. dp = p_L − p_R [Pa] from the previous step.
        Returns the state with the prescribed volumes at the end of the step (t + dt)."""
        c = self.cfg
        t_r = t - c.prefill_time
        u = self.rhythm.command(t_r, self.pump.V_p) if t_r >= 0 else 0
        self.pump.step(u, dp, dt)
        prefill = c.V_prefill * smooth_ramp(t + dt, c.prefill_time)[0]
        V_ref = self.rhythm.v_ref(t_r + dt)[0] if t_r + dt >= 0 else 0.0
        p = self.pump
        return HydraulicsState(t + dt, V_ref, p.V_p, u, p.Q, p.Q_valve, p.valve_open,
                               prefill, prefill + p.V_p, prefill - p.V_p)
