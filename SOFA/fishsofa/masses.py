"""Masa (bezwładność) i ciężar ogona, liczone w Pythonie, a nie przez grawitację SOFA.

Dlaczego nie zwykłe `root.gravity`: SOFA mnoży jeden wektor grawitacji przez całą
masę węzła. U nas węzeł ma dwa rodzaje masy:
  - silikon: ma bezwładność i ciężar (w wodzie: ciężar pozorny g·(1 − ρ_w/ρ_s)),
  - wodę w komorach: zawsze ma bezwładność (trzeba ją rozpędzić razem z ogonem),
    ale w wodzie jej ciężar znosi wypór, więc ciężaru „nie ma”.
Jednym wektorem grawitacji nie da się tego rozdzielić. Dlatego grawitacja SOFA = 0,
masa idzie do komponentu masy (gęstość na element), a ciężar jako siły węzłowe
w ConstantForceField.

Masa węzłowa (lumped): każdy czworościan oddaje 1/4 swojej masy każdemu wierzchołkowi.
Dla liniowych czworościanów to są dokładnie sumy wierszy spójnej macierzy masy, której
używa MeshMatrixMass, więc ciężar i bezwładność pochodzą z tej samej masy.
"""
from dataclasses import dataclass

import numpy as np

from fishsofa.config import TailConfig
from fishsofa.mesh_gen import TailMesh, surface_volume, tet_volumes


@dataclass
class MassModel:
    element_density: np.ndarray  # (M,) [kg/m³] silikon + rozłożona woda z komór
    node_mass: np.ndarray        # (N,) [kg] masa węzłowa (bezwładność)
    node_weight: np.ndarray      # (N, 3) [N] siła ciężaru (+ wyporu) na węzeł
    mass_silicone: float         # [kg]
    mass_water: float            # [kg] woda w komorach


def build(mesh: TailMesh, cfg: TailConfig) -> MassModel:
    vol = tet_volumes(mesh.points, mesh.tets)
    rho_s = np.full(len(vol), cfg.rho_silicone)
    rho_w = np.zeros(len(vol))

    # Woda w komorach: masa ρ_w·V_wnęki rozłożona równomiernie (wg objętości) na
    # czworościany dotykające ścianek wnęki. To przybliżenie: prawdziwa woda porusza się
    # razem ze ściankami, więc „przyklejenie” jej do ścianek oddaje bezwładność.
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
        # Wypór wody na silikon: ciężar pozorny. Woda w komorach: ciężar = wypór -> 0.
        weight[:, 2] = -cfg.gravity * (1.0 - cfg.rho_water / cfg.rho_silicone) * m_sil
    return MassModel(density, m_sil + m_wat, weight, float(m_sil.sum()), m_water)
