"""Water forces on the fish at high Reynolds numbers (Re ~ 1e4–1e5) – a LOCAL model.

Each rod element "feels" the water only through its own velocity (and the tail's
trailing edge through its own). No vortex wake and no tail–vortex interaction – the
results are qualitative. Real flow: coupling with the SophT solver (immersed boundary).

Models (config.WaterConfig.model):
  "none"           – vacuum,
  "drag"           – quadratic drag (Morison/Taylor),
  "drag+reactive"  – drag + Lighthill reactive force at the trailing edge,
  "stokes_sbt"     – built-in ea.SlenderBodyTheory (Stokes) – FOR COMPARISON ONLY, wrong physics.

1. Quadratic drag, per unit length, in the cross-section axes (d1 = vertical, d2 = lateral,
   d3 = fish axis). The element velocity relative to water v is split into components:
     f₂ = −½ ρ C_n h |v₂| v₂     lateral motion "sees" the section height h = 2b
     f₁ = −½ ρ C_n w |v₁| v₁     vertical motion "sees" the width w = 2a
     f₃ = −½ ρ C_t π d |v₃| v₃   sliding along the axis: friction on the perimeter π·d
   (the so-called cross-flow principle: the normal force depends only on the normal
   velocity component). For a flat tail h ≫ w, so lateral drag is large and vertical
   drag small – as intuition suggests. The element force is split half-and-half between its nodes.

2. Reactive force (large-amplitude elongated-body theory, Lighthill 1971,
   "Large-amplitude elongated-body theory of fish locomotion", Proc. R. Soc. B 179:125).
   The water around a cross-section moves with it in the transverse direction; its momentum
   per unit length is m_a·w, where w is the transverse velocity of the section, and the added mass
     m_a = ρ π h² / 4   (a plate of height h moved perpendicular to itself).
   A fish swimming forward "leaves" this momentum in the wake behind the trailing edge, so
   an opposite force acts on the fish (plus a pressure term):
     F_TE = m_a(L) · [ u·w − ½|w|²·t ]    at s = L (tail tip)
   t – tangent (from head to tail), u = v·t, w = v − u·t (transverse velocity vector).
   The term −½ m_a |w|² t is THRUST (forward, towards the head). The term u·w (u < 0 when
   swimming forward) opposes the lateral motion of the tail.
   We neglect the distributed term −d/dt ∫ m_a w n ds (inertia of the added mass along the body):
   it would require differentiating the velocity (noise), and PyElastica stores node mass as a
   scalar, so mass cannot be added only in the transverse direction. Consequence: the natural
   frequency of the tail in water comes out too high (in reality the added mass lowers it).
   Note: the reactive force need not dissipate energy – it is what propels the fish.
"""

import numpy as np
import elastica as ea
from numba import njit


@njit(cache=True)
def drag_kernel(vel, directors, lengths, half_w, half_h, rho, C_n, C_t, ext, total):
    """Quadratic drag for all elements. Adds to ext (nodal forces) and stores in
    total = [Fx, Fy, Fz, P] the force sum and the power (P ≤ 0 – dissipation)."""
    n = lengths.shape[0]
    for i in range(4):
        total[i] = 0.0
    for k in range(n):
        vx = 0.5 * (vel[0, k] + vel[0, k + 1])
        vy = 0.5 * (vel[1, k] + vel[1, k + 1])
        vz = 0.5 * (vel[2, k] + vel[2, k + 1])
        v1 = vx * directors[0, 0, k] + vy * directors[0, 1, k] + vz * directors[0, 2, k]
        v2 = vx * directors[1, 0, k] + vy * directors[1, 1, k] + vz * directors[1, 2, k]
        v3 = vx * directors[2, 0, k] + vy * directors[2, 1, k] + vz * directors[2, 2, k]
        a = half_w[k]
        b = half_h[k]
        # equivalent diameter of the ellipse perimeter (Ramanujan): π·d ≈ perimeter
        d_eq = (3.0 * (a + b) - np.sqrt((3.0 * a + b) * (a + 3.0 * b)))
        q = 0.5 * rho * lengths[k]
        f1 = -q * C_n * (2.0 * a) * abs(v1) * v1
        f2 = -q * C_n * (2.0 * b) * abs(v2) * v2
        f3 = -q * C_t * np.pi * d_eq * abs(v3) * v3
        for i in range(3):
            F = f1 * directors[0, i, k] + f2 * directors[1, i, k] + f3 * directors[2, i, k]
            ext[i, k] += 0.5 * F
            ext[i, k + 1] += 0.5 * F
            total[i] += F
        total[3] += f1 * v1 + f2 * v2 + f3 * v3


@njit(cache=True)
def reactive_kernel(vel, directors, m_a, ext, total):
    """Lighthill reactive force at the last node (trailing edge).
    Adds to ext and stores in total = [Fx, Fy, Fz, P]."""
    k = directors.shape[2] - 1
    v = vel[:, -1]
    t = directors[2, :, k]
    u = v[0] * t[0] + v[1] * t[1] + v[2] * t[2]
    w = v - u * t
    w2 = w[0] * w[0] + w[1] * w[1] + w[2] * w[2]
    P = 0.0
    for i in range(3):
        F = m_a * (u * w[i] - 0.5 * w2 * t[i])
        ext[i, -1] += F
        total[i] = F
        P += F * v[i]
    total[3] = P


class WaterForces(ea.NoForces):
    """Custom water force class (inherits from ea.NoForces, apply_forces method).

    After each call self.drag_total and self.reactive_total hold [Fx, Fy, Fz, power]
    – for logging (tethered thrust, energy dissipation test)."""

    def __init__(self, half_width, half_height, rho, C_n, C_t, reactive: bool, h_te: float):
        super().__init__()
        self.half_w = np.ascontiguousarray(half_width, dtype=np.float64)
        self.half_h = np.ascontiguousarray(half_height, dtype=np.float64)
        self.rho, self.C_n, self.C_t = float(rho), float(C_n), float(C_t)
        self.reactive = reactive
        # added mass per unit length at the trailing edge, m_a = ρπh²/4
        self.m_a = float(rho * np.pi * h_te**2 / 4.0)
        self.drag_total = np.zeros(4)
        self.reactive_total = np.zeros(4)

    def apply_forces(self, system, time=np.float64(0.0)):
        drag_kernel(system.velocity_collection, system.director_collection, system.lengths,
                    self.half_w, self.half_h, self.rho, self.C_n, self.C_t,
                    system.external_forces, self.drag_total)
        if self.reactive:
            reactive_kernel(system.velocity_collection, system.director_collection, self.m_a,
                            system.external_forces, self.reactive_total)


def add_water(sim, rod, cfg, half_width, half_height):
    """Adds the water model selected in cfg.water.model to the simulator. Returns the force
    object holder (or None) so that force sums can be read after each step."""
    wc = cfg.water
    if wc.model == "none":
        return None
    if wc.model == "stokes_sbt":
        # PyElastica: F = −4πμ/ln(L/r)·(I − ½ t tᵀ)·v·Δl – linear in v, no water density
        # (no fluid inertia, Re ≪ 1). For a fish at Re ~ 1e4 this is the wrong physics.
        sim.add_forcing_to(rod).using(ea.SlenderBodyTheory, dynamic_viscosity=wc.mu)
        return None
    if wc.model not in ("drag", "drag+reactive"):
        raise ValueError(f"unknown water model: {wc.model}")
    holder = {}
    sim.add_forcing_to(rod).using(
        _Recorded, holder=holder, half_width=half_width, half_height=half_height,
        rho=wc.rho, C_n=wc.C_n, C_t=wc.C_t, reactive=(wc.model == "drag+reactive"),
        h_te=2.0 * half_height[-1])
    return holder


class _Recorded(WaterForces):
    """WaterForces that, once created (PyElastica creates the object only in finalize),
    registers itself in `holder["water"]` so that the scenario can access it."""

    def __init__(self, holder, **kw):
        super().__init__(**kw)
        holder["water"] = self
