"""Buoyancy, weight and ballast bladder on a deformable body + depth controller.

A custom class instead of ea.GravityForces (so that weight is not counted twice): for each
element simultaneously
    weight     m_e·g     downward, applied at the center of gravity of the cross-section,
    buoyancy   ρ_w·g·V_e upward,   applied at the volume centroid (on the rod axis).
With ρ_s = ρ_w the two forces cancel (neutral buoyancy of the body itself).

Righting moment: the center of gravity of the cross-section lies h_g BELOW the axis (heavy
components – battery, pump – mounted low). When the fish tilts, weight and buoyancy no longer
act along the same vertical line and a couple appears that turns the fish back "dorsal side
up". Without it (center of gravity = center of buoyancy) the fish would have no stability
at all in roll and pitch.

Bladder: an extra volume V_b(t) displacing water, in the front part of the body just behind
the stiff head, above the LONGITUDINAL center of mass, with its buoyancy applied z_b above
the axis. If the bladder were in the nose itself, changing V_b would pitch the fish nose
up/down (checked by estimate: ~0.6 rad at V_b = 30 ml and h_g = 5 mm).

Moment of a force applied off the axis: in PyElastica external torques are written in the
material frame of the element, so we compute  τ_loc = r_loc × (Q·F),  where
r_loc = (offset, 0, 0) along d1 (cross-section vertical) and Q is the director matrix.
"""

import numpy as np
import elastica as ea
from numba import njit


@njit(cache=True)
def buoyancy_kernel(directors, volume, mass_e, rho_w, g, h_g,
                    bladder_idx, bladder_V, z_b, ext_f, ext_t, total):
    """Forces and torques from weight, body buoyancy and the bladder. total = [net F_z]."""
    n = volume.shape[0]
    total[0] = 0.0
    for k in range(n):
        W = mass_e[k] * g                     # element weight [N]
        B = rho_w * g * volume[k]             # element buoyancy [N]
        if k == bladder_idx:
            Bb = rho_w * g * bladder_V
        else:
            Bb = 0.0
        Fz = B + Bb - W
        ext_f[2, k] += 0.5 * Fz
        ext_f[2, k + 1] += 0.5 * Fz
        total[0] += Fz
        # torque from the weight applied at r = −h_g·d1 and from the bladder at r = +z_b·d1
        # F_loc = Q·(0, 0, F) = F·(Q[0,2], Q[1,2], Q[2,2]);  r_loc = (r, 0, 0)
        # r_loc × F_loc = (0, −r·F_loc,z, r·F_loc,y)
        q1 = directors[1, 2, k]
        q2 = directors[2, 2, k]
        # weight: r = −h_g, F = −W ;  bladder: r = +z_b, F = +Bb
        rF = (-h_g) * (-W) + z_b * Bb
        ext_t[1, k] += -rF * q2
        ext_t[2, k] += rF * q1


class Bladder:
    """Ballast bladder: the volume tracks V_ref with a limited pump rate.
    dV/dt = clip(k_bal·(V_ref − V), −q_max, +q_max),  V ∈ [V_min, V_max] (as in MuJoCo)."""

    def __init__(self, bc, V0: float):
        self.bc = bc
        self.V = float(V0)

    def step(self, V_ref: float, dt: float) -> float:
        b = self.bc
        q = float(np.clip(b.k_bal * (V_ref - self.V), -b.q_max, b.q_max))
        self.V = float(np.clip(self.V + q * dt, b.V_min, b.V_max))
        return self.V


class DepthPID:
    """Depth cascade (port of MuJoCo/fishsim/controllers.py: DepthController):
    PID on z -> bladder volume setpoint V_ref; the ballast pump tracks V_ref.

        V_ref = V_neutral + K_p·e − K_d·v_z + K_i·∫e,    e = z_ref − z

    The D term is computed from velocity (−K_d·v_z), not from the error derivative – a step
    in z_ref causes no "kick". Anti-windup: the integral does not grow when the output is
    saturated in the direction in which the integral would deepen the saturation.
    """

    def __init__(self, bc, V_neutral: float, z_ref: float):
        self.bc = bc
        self.V_neutral = V_neutral
        self.z_ref = z_ref
        self.integral = 0.0

    def update(self, z: float, v_z: float, dt: float) -> float:
        b = self.bc
        e = self.z_ref - z
        v_pd = self.V_neutral + b.kp * e - b.kd * v_z
        v_out = v_pd + b.ki * self.integral
        sat_hi = v_out >= b.V_max and e > 0
        sat_lo = v_out <= b.V_min and e < 0
        if not (sat_hi or sat_lo):
            self.integral += e * dt
        return float(np.clip(v_pd + b.ki * self.integral, b.V_min, b.V_max))


class BuoyancyForces(ea.NoForces):
    """Weight + body buoyancy + bladder (volume from the Bladder object, updated in the hook)."""

    def __init__(self, holder, density, rho_w, g, h_g, bladder_idx, z_b, bladder):
        super().__init__()
        self.holder = holder
        self.rho_w, self.g, self.h_g, self.z_b = float(rho_w), float(g), float(h_g), float(z_b)
        self.bladder_idx = int(bladder_idx)
        self.bladder = bladder
        self.density = density
        self.total = np.zeros(1)
        self.ext_f_dummy = None
        holder["buoyancy"] = self

    def apply_forces(self, system, time=np.float64(0.0)):
        # element volume and mass in the rest configuration (silicone ~ incompressible)
        if self.ext_f_dummy is None:
            self.volume = np.ascontiguousarray(system.volume, dtype=np.float64)
            self.mass_e = self.density * self.volume
            self.ext_f_dummy = True
        buoyancy_kernel(system.director_collection, self.volume, self.mass_e, self.rho_w,
                        self.g, self.h_g, self.bladder_idx, self.bladder.V, self.z_b,
                        system.external_forces, system.external_torques, self.total)

    def apply_torques(self, system, time=np.float64(0.0)):
        pass   # torques are added by apply_forces (one kernel, one pass over the elements)
