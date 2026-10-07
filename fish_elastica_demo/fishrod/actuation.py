"""Internal actuation: chamber pressure -> rest curvature of the segment with the chambers.

Physics. The bending moment in a Cosserat rod is  m = B·(κ − κ_rest)  (B – bending stiffness).
A chamber under pressure Δp bends its segment with a moment M = A_r·Δp. Instead of applying M
as an EXTERNAL moment, we write it into the constitutive law:

    κ_rest(s, t) = −A_r·Δp(t) / B₁(s)   in the chamber zone,   0 outside it
    (i.e. K_p(s) = A_r / B₁(s) – it follows from the chamber geometry, it is not an arbitrary constant)

then m = B·κ + M_chamber: the segment "wants" to bend by itself. The actuation force and moment are
INTERNAL: at every node they act equally and oppositely on the neighbouring elements, so
the net force and the net moment on the whole fish are zero by construction. Without water
the centre of mass stays in place and the angular momentum = 0 (checked in stage 2).

Equivalently: a pair of equal and opposite moments ±M at the zone boundaries (TorquePair) –
the only difference is that κ_rest acts "in the material frame", while the moment pair
is applied from outside in every step.

Sign: Δp > 0 (higher pressure in chamber L, on the +Y side) lengthens the left side,
so the tail bends to the RIGHT (−Y). In the PyElastica convention this is a rotation about −d1, i.e. κ₁ < 0.
Bending angle of the zone θ = −∫ κ₁ ds > 0 for a bend to the right.

How we change κ_rest during the simulation: rod.rest_kappa is a view into the PyElastica
memory block and is read in every step (compute_internal_forces_and_torques),
so an IN-PLACE assignment is enough (rest_kappa[0, idx] = ...). Assigning
rod.rest_kappa = new_array would detach the field from the block and have no effect at all.
"""

import numpy as np
import elastica as ea

from .build import voronoi_nodes


class ChamberActuator:
    """Hydraulics <-> rod link: angle θ from the chamber zone and writing κ_rest from Δp."""

    def __init__(self, rod, rc, zone, A_r: float):
        # Each Voronoi node k "is responsible" for the segment [s_k − Δl/2, s_k + Δl/2].
        # Weight w_k = what fraction of that segment lies in the chamber zone (0…1). Thanks to this
        # ∫κ_rest ds runs exactly over the zone length, regardless of whether its
        # boundaries fall on a node (without weights the 0.20–0.32 m zone with Δl = 8 mm would have
        # 16 nodes = 0.128 m, i.e. 7% too much).
        s_v = voronoi_nodes(rc)
        half = 0.5 * rod.rest_voronoi_lengths
        overlap = np.clip(np.minimum(s_v + half, zone[1]) - np.maximum(s_v - half, zone[0]), 0, None)
        w = overlap / (2 * half)
        self.idx = np.where(w > 1e-12)[0]
        self.w = w[self.idx]
        self.A_r = A_r
        self.rod = rod
        self.dp = 0.0
        # K_p(s) = A_r / B₁(s): rest curvature per pascal. After finalize rod.bend_matrix
        # is a view into the memory block (same values as before).
        self.K_p = A_r / rod.bend_matrix[0, 0, self.idx].copy()
        self.lengths = rod.rest_voronoi_lengths[self.idx].copy()
        self.zone_length = float(np.dot(self.w, self.lengths))

    def theta(self) -> float:
        """Bending angle of the chamber zone θ = −∫ κ₁ ds over the zone [rad] (> 0 = bend to the right)."""
        return float(-np.dot(self.rod.kappa[0, self.idx], self.w * self.lengths))

    def set_rest_curvature(self, dp: float) -> None:
        self.dp = float(dp)
        self.rod.rest_kappa[0, self.idx] = -self.K_p * self.w * self.dp

    def theory_theta(self, dp: float) -> float:
        """Static angle without external loads: κ = κ_rest, so θ = A_r·Δp·∫ds/B₁."""
        return float(dp * np.dot(self.K_p * self.w, self.w * self.lengths))

    @property
    def Lambda(self) -> float:
        """Λ = ∫ds/B₁ over the chamber zone [rad/(N·m)] – bending compliance of the zone."""
        return float(np.dot(self.w * self.w, self.lengths / self.rod.bend_matrix[0, 0, self.idx]))


class TorquePair(ea.NoForces):
    """Alternative: a pair of moments ±M (M = A_r·Δp) on the first and last element
    of the chamber zone. Net moment = 0 (in planar motion, where d1 of both elements = Z)."""

    def __init__(self, actuator: ChamberActuator, rc):
        super().__init__()
        self.act = actuator
        # elements on both sides of the zone (Voronoi node k lies between elements k and k+1)
        self.e0 = int(actuator.idx[0])            # element before the first node of the zone
        self.e1 = int(actuator.idx[-1]) + 1       # element after the last node of the zone

    def apply_torques(self, system, time=np.float64(0.0)):
        M = self.act.A_r * self.act.dp
        # Bend to the right (θ > 0): the rear element rotates about −Z relative to the front one.
        system.external_torques[0, self.e0] += M
        system.external_torques[0, self.e1] -= M


class SingleTorque(ea.NoForces):
    """WRONG (for comparison): a single moment −M at the rear end of the zone, without a pair.
    This is what "actuation" from external moments that do not cancel looks like: the fish in vacuum
    starts rotating as a whole (angular momentum grows), which breaks the laws of dynamics
    for an internal actuator."""

    def __init__(self, actuator: ChamberActuator, rc):
        super().__init__()
        self.act = actuator
        self.e1 = int(actuator.idx[-1]) + 1

    def apply_torques(self, system, time=np.float64(0.0)):
        system.external_torques[0, self.e1] -= self.act.A_r * self.act.dp
