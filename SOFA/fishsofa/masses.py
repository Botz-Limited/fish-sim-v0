"""Mass (inertia) and weight of the tail, computed in Python rather than via SOFA gravity.

Why not plain `root.gravity`: SOFA multiplies a single gravity vector by the whole
mass of a node. Here a node carries two kinds of mass:
  - silicone: has inertia and weight (in water: apparent weight g·(1 − ρ_w/ρ_s)),
  - water in the chambers: always has inertia (it must be accelerated along with the tail),
    but in water its weight is cancelled by buoyancy, so it "has no" weight.
A single gravity vector cannot separate the two. Therefore SOFA gravity = 0, the
mass goes into the mass component (density per element), and the weight is applied as
nodal forces in a ConstantForceField.

Nodal (lumped) mass: each tetrahedron gives 1/4 of its mass to each vertex.
For linear tetrahedra these are exactly the row sums of the consistent mass matrix
used by MeshMatrixMass, so weight and inertia come from the same mass.
"""
from dataclasses import dataclass

import numpy as np

from fishsofa.config import TailConfig
from fishsofa.mesh_gen import TailMesh, surface_volume, tet_volumes


@dataclass
class MassModel:
    element_density: np.ndarray  # (M,) [kg/m³] silicone + distributed chamber water
    node_mass: np.ndarray        # (N,) [kg] nodal mass (inertia)
    node_weight: np.ndarray      # (N, 3) [N] weight (+ buoyancy) force per node
    mass_silicone: float         # [kg]
    mass_water: float            # [kg] water in the chambers


def build(mesh: TailMesh, cfg: TailConfig) -> MassModel:
    vol = tet_volumes(mesh.points, mesh.tets)
    rho_s = np.full(len(vol), cfg.rho_silicone)
    rho_w = np.zeros(len(vol))

    # Water in the chambers: mass ρ_w·V_cavity distributed uniformly (by volume) over the
    # tetrahedra touching the cavity walls. An approximation: real water moves together
    # with the walls, so "gluing" it to the walls captures its inertia.
    m_water = 0.0
    if cfg.chambers_filled:
        for tri in (mesh.tri_chamber_L, mesh.tri_chamber_R):
            v_cav = surface_volume(mesh.points, tri)
            touch = np.isin(mesh.tets, np.unique(tri)).any(axis=1)
            rho_w[touch] += cfg.rho_water * v_cav / vol[touch].sum()
            m_water += cfg.rho_water * v_cav

    density = rho_s + rho_w

    def lump(rho):
        m = np.zeros(len(mesh.points))
        np.add.at(m, mesh.tets.ravel(), np.repeat(rho * vol / 4.0, 4))
        return m

    m_sil, m_wat = lump(rho_s), lump(rho_w)
    weight = np.zeros((len(mesh.points), 3))
    if cfg.environment == "air":
        weight[:, 2] = -cfg.gravity * (m_sil + m_wat)
    else:
        # Buoyancy on the silicone: apparent weight. Water in the chambers: weight = buoyancy -> 0.
        weight[:, 2] = -cfg.gravity * (1.0 - cfg.rho_water / cfg.rho_silicone) * m_sil
    return MassModel(density, m_sil + m_wat, weight, float(m_sil.sum()), m_water)
