"""Tail hydraulics: first-order pump + two chambers L↔R in a closed circuit + relief
valve. The same ODE model as in the MuJoCo (fishsim/hydraulics.py) and SOFA
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
    """Prescribed pumped volume V_ref(t) = a(t)·(A_V·sin(2πft) + V_bias) and the pump command.

    We prescribe VOLUME, not flow: volume is the integral of flow, so u = A·sin(ωt)
    would give a volume amplitude ∝ 1/f (a frequency sweep would mix two effects).

    u = clip((dV_ref/dt + τ_pump·d²V_ref/dt² + K_v·(V_ref − V_p)) / Q_max, −1, 1)
    The τ_pump·d²V_ref/dt² term inverts the first-order pump lag (as in SOFA).
    """

    def __init__(self, hc: HydraulicsConfig, freq=None, amp=None, bias=None):
        self.hc = hc
        self.freq = hc.tail_freq if freq is None else freq
        self.amp = hc.tail_volume_amp if amp is None else amp
        self.bias = hc.tail_volume_bias if bias is None else bias

    def v_ref(self, t: float) -> tuple[float, float, float]:
        w = 2 * np.pi * self.freq
        a, da, dda = smooth_ramp(t, self.hc.ramp_time)
        s, c = np.sin(w * t), np.cos(w * t)
        base = self.amp * s + self.bias
        A = self.amp
        return (a * base, da * base + a * A * w * c,
                dda * base + 2 * da * A * w * c - a * A * w * w * s)

    def command(self, t: float, V_p: float) -> float:
        v, dv, ddv = self.v_ref(t)
        h = self.hc
        return float(np.clip((dv + h.tau_pump * ddv + h.K_v * (v - V_p)) / h.Q_max, -1.0, 1.0))


class TailHydraulics:
    """States: Q – pump flow from R to L [m³/s], V_L, V_R – chamber volumes [m³].

    Δp = p_L − p_R = (V_p − A_r·θ) / C_h,  V_p = ½(V_L − V_R)
      The pump pushed in V_p, the bent tail "made room" for A_r·θ; the excess inflates
      the compliant walls (C_h) – hence the pressure. This is a "hydraulic spring" with stiffness
      k_h = A_r²/C_h in series with the elasticity of the silicone.
    The relief valve connects the chambers: when |Δp| > p_max, it passes the excess to the chamber
    with the lower pressure (the sum V_L + V_R does not change – closed circuit).

    Integration: explicit Euler every dt_h (a dozen or so rod steps). Stable, because dt_h ≪ τ_pump.
    """

    def __init__(self, hc: HydraulicsConfig, rhythm: TailRhythm | None = None):
        self.hc = hc
        self.rhythm = rhythm
        self.Q = 0.0
        self.V_L = hc.V0_chamber
        self.V_R = hc.V0_chamber
        self.Q_valve = 0.0
        self.u = 0.0

    @property
    def V_p(self) -> float:
        return 0.5 * (self.V_L - self.V_R)

    def delta_p(self, theta: float) -> float:
        h = self.hc
        return float(np.clip((self.V_p - h.A_r * theta) / h.C_h, -h.p_max, h.p_max))

    def step(self, t: float, theta: float, dt: float) -> float:
        """Step from t to t + dt at bending angle θ. Returns Δp for the NEXT interval dt."""
        h = self.hc
        self.u = self.rhythm.command(t, self.V_p) if self.rhythm is not None else 0.0
        self.Q += dt * (self.u * h.Q_max - self.Q) / h.tau_pump
        self.V_L += self.Q * dt
        self.V_R -= self.Q * dt
        excess = self.V_p - h.A_r * theta
        limit = h.p_max * h.C_h            # excess volume corresponding to p_max
        vent = excess - np.clip(excess, -limit, limit)
        self.V_L -= vent
        self.V_R += vent
        self.Q_valve = vent / dt
        return self.delta_p(theta)
