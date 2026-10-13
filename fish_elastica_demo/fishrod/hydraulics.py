"""Tail hydraulics: constant-speed pump + two-state directional valves + two chambers L↔R
in a closed circuit + relief valve. The same ODE model as in the MuJoCo (fishsim/hydraulics.py) and SOFA
(fishsofa/hydraulics.py) demos; here coupled with the rod through the bending angle θ of the chamber zone.

Pure numpy, no PyElastica – can be tested on its own (tests/test_sanity.py).
"""

import numpy as np

from .config import HydraulicsConfig


def smooth_ramp(t: float, T: float) -> tuple[float, float, float]:
    """Soft start a(t) = ½(1 − cos(πt/T)) for 0 ≤ t < T. Returns (a, da/dt, d²a/dt²).
    Continuous together with its derivative, so neither volume nor flow jumps."""
    if t <= 0:
        return 0.0, 0.0, 0.0
    if T <= 0 or t >= T:
        return 1.0, 0.0, 0.0
    k = np.pi / T
    return 0.5 * (1 - np.cos(k * t)), 0.5 * k * np.sin(k * t), 0.5 * k * k * np.cos(k * t)


class TailRhythm:
    """Prescribed pumped volume V_ref(t) = a(t)·(A_V·sin(2πft + φ0) + V_bias) and the valve state.

    We prescribe VOLUME, not flow: volume is the integral of flow, so a flow rhythm
    would give a volume amplitude ∝ 1/f (a frequency sweep would mix two effects).

    The pump runs at constant speed; the valves only choose the direction, s = ±1
    (+1: R→L, −1: L→R; there is no closed state). Relay controller with hysteresis δ:
      e = V_ref − V_p;  e > δ -> s = +1;  e < −δ -> s = −1;  otherwise s unchanged.
    Start (and reset): s = +1.

    Hardware limits: the valve holds each state for at least valve_min_dwell (≤ 5 switches/s),
    and the frequency is clamped to [tail_freq_min, tail_freq_max]: above tail_freq_max the
    valve cannot switch 2 times per cycle. Here f_track ≈ 3.2 Hz > tail_freq_max, so inside the
    range the relay would like to track V_ref with many switches – the dwell time prevents it.
    """

    def __init__(self, hc: HydraulicsConfig, freq=None, amp=None, bias=None):
        self.hc = hc
        self.freq = self._clamp(hc.tail_freq if freq is None else freq)
        self.amp = hc.tail_volume_amp if amp is None else amp
        self.bias = hc.tail_volume_bias if bias is None else bias
        self.phase0 = 0.0           # [rad] phase offset – keeps φ continuous when f changes
        self.s = 1.0                # valve state, remembered between steps
        self.t_switch = -np.inf     # [s] time of the last valve switch

    def _clamp(self, freq: float) -> float:
        return float(np.clip(freq, self.hc.tail_freq_min, self.hc.tail_freq_max))

    def set_freq(self, freq: float, t: float):
        """Change the frequency during motion WITHOUT a phase jump: φ0 is chosen so that
        φ(t) = 2πf·t + φ0 stays continuous (a jump in V_ref would be a pump impact)."""
        freq = self._clamp(freq)
        self.phase0 += 2 * np.pi * (self.freq - freq) * t
        self.freq = freq

    def v_ref(self, t: float) -> tuple[float, float, float]:
        w = 2 * np.pi * self.freq
        a, da, dda = smooth_ramp(t, self.hc.ramp_time)
        s, c = np.sin(w * t + self.phase0), np.cos(w * t + self.phase0)
        base = self.amp * s + self.bias
        A = self.amp
        return (a * base, da * base + a * A * w * c,
                dda * base + 2 * da * A * w * c - a * A * w * w * s)

    def reset(self):
        self.phase0 = 0.0
        self.s = 1.0
        self.t_switch = -np.inf

    def command(self, t: float, V_p: float) -> float:
        if t - self.t_switch < self.hc.valve_min_dwell:
            return self.s           # the valve holds its state for at least valve_min_dwell
        e = self.v_ref(t)[0] - V_p
        d = self.hc.valve_hysteresis
        s = self.s
        if e > d:
            s = 1.0
        elif e < -d:
            s = -1.0
        if s != self.s:
            self.s, self.t_switch = s, t
        return self.s


class TailHydraulics:
    """States: Q – flow from R to L [m³/s], V_L, V_R – chamber volumes [m³].

    dQ/dt = (s·Q_const − Q) / τ_valve: the valves switch the direction of the constant pump
    flow, the reversal of the stream takes ~τ_valve. s = 0 only when there is no rhythm
    (pump switched off).

    Δp = p_L − p_R = (V_p − A_r·θ) / C_h,  V_p = ½(V_L − V_R)
      The pump pushed in V_p, the bent tail "made room" for A_r·θ; the excess inflates
      the compliant walls (C_h) – hence the pressure. This is a "hydraulic spring" with stiffness
      k_h = A_r²/C_h in series with the elasticity of the silicone.
    The relief valve connects the chambers: when |Δp| > p_max, it passes the excess to the chamber
    with the lower pressure (the sum V_L + V_R does not change – closed circuit).

    Integration: explicit Euler every dt_h (a dozen or so rod steps). Stable, because dt_h ≪ τ_valve.
    """

    def __init__(self, hc: HydraulicsConfig, rhythm: TailRhythm | None = None):
        self.hc = hc
        self.rhythm = rhythm
        self.Q = 0.0
        self.V_L = hc.V0_chamber
        self.V_R = hc.V0_chamber
        self.Q_valve = 0.0
        self.u = 0.0                # valve state s (±1), 0 = pump off
        self.n_switch = 0           # number of valve switches (sign changes of s)

    @property
    def V_p(self) -> float:
        return 0.5 * (self.V_L - self.V_R)

    def delta_p(self, theta: float) -> float:
        h = self.hc
        return float(np.clip((self.V_p - h.A_r * theta) / h.C_h, -h.p_max, h.p_max))

    def step(self, t: float, theta: float, dt: float) -> float:
        """Step from t to t + dt at bending angle θ. Returns Δp for the NEXT interval dt."""
        h = self.hc
        u = self.rhythm.command(t, self.V_p) if self.rhythm is not None else 0.0
        if u * self.u < 0:
            self.n_switch += 1
        self.u = u
        self.Q += dt * (self.u * h.Q_const - self.Q) / h.tau_valve
        self.V_L += self.Q * dt
        self.V_R -= self.Q * dt
        excess = self.V_p - h.A_r * theta
        limit = h.p_max * h.C_h            # excess volume corresponding to p_max
        vent = excess - np.clip(excess, -limit, limit)
        self.V_L -= vent
        self.V_R += vent
        self.Q_valve = vent / dt
        return self.delta_p(theta)
