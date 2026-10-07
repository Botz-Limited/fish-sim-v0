"""Building the PyElastica simulator: rod, boundary conditions, damping, callbacks.

PyElastica 1.0.0: the simulator is a class composed of mixins (elastica.modules),
each mixin adds one feature: Constraints (boundary conditions), Forcing (external
forces), Damping (damping), CallBacks (saving results), Connections (joints).
"""

import numpy as np
import elastica as ea

from .config import FishConfig, RodConfig

# Directions in the global frame: fish along +X, "up" = +Z.
DIRECTION = np.array([1.0, 0.0, 0.0])
NORMAL = np.array([0.0, 0.0, 1.0])


class FishSimulator(
    ea.BaseSystemCollection,
    ea.Constraints,
    ea.Forcing,
    ea.Damping,
    ea.CallBacks,
    ea.Connections,
):
    """A collection of objects (rods) + operations on them, executed in every step."""


def make_rod(rc: RodConfig, start=np.zeros(3)) -> ea.CosseratRod:
    """A straight, uniform rod along +X (stage 1)."""
    return ea.CosseratRod.straight_rod(
        rc.n_elements,
        np.asarray(start, dtype=float),
        DIRECTION.copy(),
        NORMAL.copy(),
        rc.length,
        rc.radius,
        rc.density,
        youngs_modulus=rc.youngs_modulus,
        shear_modulus=rc.shear_modulus,
    )


def fish_profile(fc: FishConfig, rc: RodConfig, s):
    """Cross-section semi-axes a(s) (half width) and b(s) (half height) [m]."""
    st = np.asarray(fc.stations) * rc.length
    return np.interp(s, st, fc.half_width), np.interp(s, st, fc.half_height)


def element_centers(rc: RodConfig):
    dl = rc.element_length
    return (np.arange(rc.n_elements) + 0.5) * dl


def voronoi_nodes(rc: RodConfig):
    """Positions s of the Voronoi nodes (interior rod nodes) – this is where κ and κ_rest live."""
    return np.arange(1, rc.n_elements) * rc.element_length


def section_half_axes(rc: RodConfig, fc: FishConfig):
    """Cross-section semi-axes (a – sideways, b – vertical) at the element centres [m]."""
    a, b = fish_profile(fc, rc, element_centers(rc))
    if fc.cross_section == "circle":
        a = b = np.sqrt(a * b)        # circle with the same area
    elif fc.cross_section != "ellipse":
        raise ValueError(f"unknown cross-section: {fc.cross_section}")
    return a, b


def make_fish_rod(rc: RodConfig, fc: FishConfig, start=np.zeros(3)) -> ea.CosseratRod:
    """A single rod with a varying cross-section (tapering towards the tail) and a stiff head.

    Why one rod and not two connected with a FixedJoint: PyElastica 1.0 accepts
    radius and density as per-element arrays, and the stiffness matrices can be overwritten
    per element. A single rod has no joint (a joint is an extra "penalty spring"
    that stiffens the system and shortens the stable step).

    Notation: d1 = +Z (vertical), d2 = −Y (sideways), d3 = fish axis.
      bending about d1 = tail sideways (swimming motion)  -> stiffness E·I₁, I₁ = π a³ b / 4
      bending about d2 = tail up-down                     -> stiffness E·I₂, I₂ = π a b³ / 4
      twisting about d3                                   -> G·J, J = π a³ b³ / (a² + b²)
    For a circle (a = b = r): I₁ = I₂ = π r⁴/4, J = π r⁴/2 – what PyElastica computes by default.
    """
    s_e = element_centers(rc)
    a, b = section_half_axes(rc, fc)
    r_eq = np.sqrt(a * b)             # equivalent radius: π r² = π a b
    rod = ea.CosseratRod.straight_rod(
        rc.n_elements, np.asarray(start, dtype=float), DIRECTION.copy(), NORMAL.copy(),
        rc.length, r_eq, rc.density,
        youngs_modulus=rc.youngs_modulus, shear_modulus=rc.shear_modulus,
    )
    E = np.where(s_e < fc.head_length, fc.head_stiffness_factor, 1.0) * rc.youngs_modulus
    G = E / (2.0 * (1.0 + rc.poisson_ratio))
    A = np.pi * a * b
    I1 = np.pi * a**3 * b / 4.0
    I2 = np.pi * a * b**3 / 4.0
    J = np.pi * a**3 * b**3 / (a**2 + b**2)
    dl = rod.rest_lengths

    # Bending/twist stiffness B per element, then a length-weighted average on the
    # Voronoi nodes (PyElastica does the same in rod/factory_function.py).
    B_e = np.array([E * I1, E * I2, G * J])
    B_v = (B_e[:, 1:] * dl[1:] + B_e[:, :-1] * dl[:-1]) / (dl[1:] + dl[:-1])
    # Shear/stretch S: α_c·G·A (shear, α_c = 27/28 as in PyElastica), E·A (stretch)
    alpha_c = 27.0 / 28.0
    S_e = np.array([alpha_c * G * A, alpha_c * G * A, E * A])
    # Mass second moment of inertia of the cross-section (rotational inertia of an element): ρ·I·Δl
    J_e = rc.density * np.array([I1, I2, I1 + I2]) * dl

    # We overwrite IN PLACE (before finalize – then the data goes into the memory block).
    rod.bend_matrix[...] = 0.0
    rod.shear_matrix[...] = 0.0
    rod.mass_second_moment_of_inertia[...] = 0.0
    rod.inv_mass_second_moment_of_inertia[...] = 0.0
    for i in range(3):
        rod.bend_matrix[i, i, :] = B_v[i]
        rod.shear_matrix[i, i, :] = S_e[i]
        rod.mass_second_moment_of_inertia[i, i, :] = J_e[i]
        rod.inv_mass_second_moment_of_inertia[i, i, :] = 1.0 / J_e[i]
    return rod


def stable_time_step(rod: ea.CosseratRod, safety: float) -> float:
    """Estimate of the maximum stable step for the explicit PositionVerlet.

    An explicit integrator is stable when dt < 2/ω_max, where ω_max is the highest
    vibration frequency of the DISCRETE rod. Two sources of high frequencies:

    1. Longitudinal (stretching) wave within one element:
         c = √(E/ρ)  (speed of sound in the material),  ω_max ≈ 2c/Δl
         ->  dt < Δl / c
    2. Bending of the shortest wave (length ~2Δl), Euler-Bernoulli beam:
         ω = k²·√(EI/(ρA)),  k = 2/Δl,  √(EI/(ρA)) = (r/2)·c  for a circle
         ->  ω_max ≈ 2·r·c / Δl²  ->  dt < Δl² / (r·c)
       Bending is the stricter limit when Δl < r (fine mesh, thick rod).
    (Shear: c_s = √(G/ρ) < c, so it does not limit.)

    We compute it for the worst element (max E/ρ and max r), with a margin `safety` < 1.
    Practical conclusion: dt ~ Δl², i.e. a 2× finer mesh = a 4× smaller step
    and 8× longer computation.
    """
    dl = rod.rest_lengths
    rho = rod.density
    area = np.pi * rod.radius**2
    # The effective E and "bending radius" are read from the stiffness matrices, so that the
    # formula also works after overwriting the stiffness (taper, flat cross-section, stiff head).
    EA = rod.shear_matrix[2, 2, :]
    E = EA / area
    c = np.sqrt(E / rho)
    EI_max = np.maximum(rod.bend_matrix[0, 0, :], rod.bend_matrix[1, 1, :])
    # √(EI/(ρA)) on the Voronoi nodes, compared with the neighbouring elements
    rhoA = rho * area
    bend_speed = np.sqrt(EI_max / np.minimum(rhoA[:-1], rhoA[1:]))
    dl_v = rod.rest_voronoi_lengths
    dt_axial = np.min(dl / c)
    dt_bend = np.min(dl_v**2 / (2.0 * bend_speed))
    return safety * min(dt_axial, dt_bend)


class EndpointTorque(ea.NoForces):
    """A concentrated moment on the last element (constant in the global frame).

    In PyElastica external torques are written in the MATERIAL FRAME of the element
    (axes d1, d2, d3), so the global moment has to be rotated with the director matrix:
    τ_local = Q · τ_global, where the rows of Q are d1, d2, d3.
    """

    def __init__(self, torque_global, ramp_time: float = 0.0):
        super().__init__()
        self.torque = np.asarray(torque_global, dtype=float)
        self.ramp_time = ramp_time

    def apply_torques(self, system, time=np.float64(0.0)):
        a = 1.0 if self.ramp_time <= 0 else min(1.0, float(time) / self.ramp_time)
        system.external_torques[:, -1] += a * (system.director_collection[..., -1] @ self.torque)


class RodRecorder(ea.CallBackBaseClass):
    """Saves the rod state every `step_skip` steps (PyElastica saves nothing on its own)."""

    def __init__(self, step_skip: int, store: dict, velocities: bool = False, energy: bool = False):
        super().__init__()
        self.every = step_skip
        self.store = store
        self.velocities = velocities
        self.energy = energy
        for k in ("time", "position", "velocity", "energy"):
            store.setdefault(k, [])

    def make_callback(self, system, time, current_step: int):
        if current_step % self.every:
            return
        self.store["time"].append(float(time))
        self.store["position"].append(system.position_collection.copy())
        if self.velocities:
            self.store["velocity"].append(system.velocity_collection.copy())
        if self.energy:
            self.store["energy"].append(total_energy(system))


def total_energy(rod) -> float:
    """Mechanical energy of the rod: kinetic (translation + rotation of the cross-sections)
    + elastic (bending/twisting + shear/stretching)."""
    return float(
        rod.compute_translational_energy()
        + rod.compute_rotational_energy()
        + rod.compute_bending_energy()
        + rod.compute_shear_energy()
    )


def angular_momentum(rod) -> np.ndarray:
    """Total angular momentum about the centre of mass [kg·m²/s] in the global frame:
    node motion  Σ mᵢ (xᵢ − x_c) × vᵢ  +  rotation of the cross-sections  Σ Qₑᵀ (Jₑ ωₑ / eₑ).
    (ω and J are in the material frame, e = element dilatation – as in PyElastica.)"""
    x_c = rod.compute_position_center_of_mass()
    r = rod.position_collection - x_c[:, None]
    L = np.sum(rod.mass * np.cross(r.T, rod.velocity_collection.T).T, axis=1)
    J = np.einsum("iik->ik", rod.mass_second_moment_of_inertia)
    spin_local = J * rod.omega_collection / rod.dilatation
    L += np.einsum("jik,jk->i", rod.director_collection, spin_local)
    return L
