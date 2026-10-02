"""Scena SOFA: miękki ogon FEM przymocowany do kadłuba.

GUI:      scripts/run_gui.sh [coarse|medium|fine]    (runSofa wywołuje createScene)
Headless: fishsofa.headless (ta sama funkcja build_tail)

Etap 1: sam materiał, bez aktuacji – ogon ugina się pod własnym ciężarem.
Struktura (FreeMotionAnimationLoop + solver ograniczeń + korekcja ograniczeń) jest
już taka, jakiej wymagają komory SurfacePressureConstraint z etapu 2.

Drzewo sceny:
  root                      FreeMotionAnimationLoop, BlockGaussSeidelConstraintSolver
  └─ tail                   integrator, solver liniowy, FEM, masa, mocowanie, ciężar
     └─ visu (tylko GUI)    powierzchnia zewnętrzna do rysowania
"""
import os

import numpy as np

from fishsofa import masses, mesh_gen
from fishsofa.config import TailConfig

# Moduły SOFA z komponentami tej sceny. Jawna lista (zamiast meta-pluginu
# "Sofa.Component") mówi czytelnikowi, skąd jest każdy komponent.
PLUGINS = [
    "Sofa.Component.AnimationLoop",                   # FreeMotionAnimationLoop
    "Sofa.Component.Constraint.Lagrangian.Solver",    # BlockGaussSeidelConstraintSolver
    "Sofa.Component.Constraint.Lagrangian.Correction",  # LinearSolverConstraintCorrection
    "Sofa.Component.Constraint.Projective",           # FixedProjectiveConstraint
    "Sofa.Component.ODESolver.Backward",              # EulerImplicitSolver, StaticSolver
    "Sofa.Component.LinearSolver.Direct",             # SparseLDLSolver
    "Sofa.Component.IO.Mesh",                         # MeshVTKLoader, MeshOBJLoader
    "Sofa.Component.Topology.Container.Dynamic",      # TetrahedronSetTopologyContainer
    "Sofa.Component.StateContainer",                  # MechanicalObject
    "Sofa.Component.SolidMechanics.FEM.Elastic",      # TetrahedronFEMForceField
    "Sofa.Component.Mass",                            # MeshMatrixMass
    "Sofa.Component.MechanicalLoad",                  # ConstantForceField
    "Sofa.Component.Mapping.Linear",                  # BarycentricMapping
]
GUI_PLUGINS = ["Sofa.GL.Component.Rendering3D", "Sofa.Component.Visual"]


def build_tail(root, cfg: TailConfig, level: str, mesh_root: str | None = None,
               solver: str = "dynamic", gui: bool = False) -> dict:
    """Buduje ogon w węźle root. Zwraca uchwyty do komponentów i dane siatki.

    solver="dynamic" – EulerImplicitSolver (ruch w czasie),
    solver="static"  – StaticSolver (od razu stan równowagi, metoda Newtona).
    """
    folder = mesh_gen.ensure(cfg, level, mesh_root)
    mesh = mesh_gen.load(cfg, level, mesh_root)
    mm = masses.build(mesh, cfg)

    root.addObject("RequiredPlugin", pluginName=PLUGINS + (GUI_PLUGINS if gui else []))
    root.dt = cfg.dt
    # Grawitacja SOFA wyłączona – ciężar liczymy sami (patrz fishsofa/masses.py).
    root.gravity = [0.0, 0.0, 0.0]

    if solver == "dynamic":
        # Pętla animacji z ograniczeniami: najpierw ruch „swobodny” (bez ograniczeń),
        # potem solver ograniczeń liczy mnożniki Lagrange'a i koryguje ruch. W etapie 1
        # nie ma jeszcze ograniczeń Lagrange'a (komory dochodzą w etapie 2).
        root.addObject("FreeMotionAnimationLoop")
        root.addObject("BlockGaussSeidelConstraintSolver", maxIterations=500, tolerance=1e-9)
    else:
        # StaticSolver w SOFA v26.06 nie działa z FreeMotionAnimationLoop (sprawdzone:
        # ogon się nie rusza), więc statyka używa zwykłej pętli. Komory z ograniczeniami
        # Lagrange'a w statyce to temat etapu 2.
        root.addObject("DefaultAnimationLoop")
    if gui:
        root.addObject("VisualStyle", displayFlags="showVisualModels showBehaviorModels")

    tail = root.addChild("tail")
    if solver == "dynamic":
        # Niejawny (implicit) Euler: stabilny nawet przy sztywnym FEM i dużym kroku,
        # bo w każdym kroku rozwiązuje układ z macierzą (M − dt·C − dt²·K).
        # Rayleigh: tłumienie C = α·M + β·K, zastępuje tłumienie materiałowe silikonu.
        tail.addObject("EulerImplicitSolver", name="odesolver",
                       rayleighMass=cfg.rayleigh_mass, rayleighStiffness=cfg.rayleigh_stiffness)
    elif solver == "static":
        # Statyka: szuka położenia, w którym siły wewnętrzne (FEM) równoważą ciężar.
        # FEM korotacyjny jest nieliniowy, więc równowagę liczy metoda Newtona-Raphsona
        # (od v25.12 osobny komponent). Pierwsza iteracja zwykle „przestrzeliwuje”
        # (ostrzeżenie „Line search failed at Newton iteration 0”), kolejne już zbiegają.
        tail.addObject("NewtonRaphsonSolver", name="newton", maxNbIterationsNewton=30,
                       absoluteResidualStoppingThreshold=1e-6)
        tail.addObject("StaticSolver", name="odesolver", newtonSolver="@newton")
    else:
        raise ValueError(solver)
    # Bezpośredni solver liniowy (rozkład LDLᵀ macierzy rzadkiej). Bloki 3×3, bo każdy
    # węzeł ma 3 stopnie swobody – tak jest szybciej niż skalarnie.
    tail.addObject("SparseLDLSolver", name="linsolver", template="CompressedRowSparseMatrixMat3x3d")

    tail.addObject("MeshVTKLoader", name="loader", filename=os.path.join(folder, "tail.vtk"))
    tail.addObject("TetrahedronSetTopologyContainer", name="topology", src="@loader")
    dofs = tail.addObject("MechanicalObject", name="dofs", template="Vec3d")

    # Korotacyjny FEM (method="large"): dla każdego elementu wyznacza jego obrót i liczy
    # sprężystość liniową w układzie obróconym. Dzięki temu duże zgięcia ogona nie dają
    # sztucznego „puchnięcia”, jak w czysto liniowym FEM.
    fem_name = "ParallelTetrahedronFEMForceField" if cfg.parallel_fem else "TetrahedronFEMForceField"
    if cfg.parallel_fem:
        root.addObject("RequiredPlugin", pluginName=["MultiThreading"])
    tail.addObject(fem_name, name="fem", method="large",
                   youngModulus=cfg.young_modulus, poissonRatio=cfg.poisson_ratio)

    # Masa: spójna macierz masy z gęstością na element (silikon + woda z komór).
    tail.addObject("MeshMatrixMass", name="mass", massDensity=mm.element_density.tolist())

    # Mocowanie: węzły przedniej ściany nieruchome (ogon przykręcony do kadłuba,
    # jednocześnie stanowisko pomiaru ciągu na uwięzi). Constraint „projekcyjny”
    # zeruje ruch tych węzłów bezpośrednio w układzie równań.
    tail.addObject("FixedProjectiveConstraint", name="fixed", indices=mesh.base_nodes.tolist())

    # Ciężar (i wypór w wodzie) jako stałe siły węzłowe.
    tail.addObject("ConstantForceField", name="weight",
                   indices=list(range(len(mesh.points))), forces=mm.node_weight.tolist())

    if solver == "dynamic":
        # Korekcja ograniczeń: mówi solverowi ograniczeń, jak węzły zareagują na siły
        # ograniczeń (używa faktoryzacji z SparseLDLSolver).
        tail.addObject("LinearSolverConstraintCorrection")

    if gui:
        visu = tail.addChild("visu")
        visu.addObject("MeshOBJLoader", name="loader", filename=os.path.join(folder, "outer.obj"))
        visu.addObject("OglModel", src="@loader", color=[0.95, 0.70, 0.30, 1.0])
        visu.addObject("BarycentricMapping")

    return {"tail": tail, "dofs": dofs, "mesh": mesh, "masses": mm, "folder": folder}


def createScene(root):
    """Wejście dla runSofa. Poziom siatki z FISHSOFA_LEVEL (domyślnie coarse)."""
    level = os.environ.get("FISHSOFA_LEVEL", "coarse")
    cfg = TailConfig()
    build_tail(root, cfg, level, gui=True)
    return root
