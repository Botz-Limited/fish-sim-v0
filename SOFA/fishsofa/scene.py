"""Scena SOFA: miękki ogon FEM przymocowany do kadłuba.

GUI:      scripts/run_gui.sh [coarse|medium|fine]    (runSofa wywołuje createScene;
          FISHSOFA_MODE=flap – machanie, domyślnie; sag – ugięcie pod ciężarem;
          FISHSOFA_ENV=air – domyślnie, water – opór wody i ciężar pozorny)
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
    "Sofa.Component.SolidMechanics.Spring",           # StiffSpringForceField (włókna)
    "Sofa.Component.Topology.Container.Constant",     # MeshTopology (powierzchnia komory)
]
GUI_PLUGINS = ["Sofa.GL.Component.Rendering3D", "Sofa.Component.Visual"]


def build_tail(root, cfg: TailConfig, level: str, mesh_root: str | None = None,
               solver: str = "dynamic", gui: bool = False, chambers: dict | None = None) -> dict:
    """Buduje ogon w węźle root. Zwraca uchwyty do komponentów i dane siatki.

    solver="dynamic" – EulerImplicitSolver (ruch w czasie),
    solver="static"  – StaticSolver (od razu stan równowagi, metoda Newtona; bez komór).
    chambers – np. {"L": "volume", "R": "vented"}; tryby w add_chamber().
    """
    chambers = chambers or {}
    if chambers and solver == "static":
        raise ValueError("komory (ograniczenia Lagrange'a) wymagają solver='dynamic' – "
                         "StaticSolver nie działa z FreeMotionAnimationLoop (etap 1)")
    folder = mesh_gen.ensure(cfg, level, mesh_root)
    mesh = mesh_gen.load(cfg, level, mesh_root)
    mm = masses.build(mesh, cfg)

    root.addObject("RequiredPlugin", pluginName=PLUGINS + (GUI_PLUGINS if gui else [])
                   + (["SoftRobots"] if chambers else []))
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
    if solver not in ("dynamic", "static"):
        raise ValueError(solver)
    # Statyka (Newton) zawsze z dokładnym rozkładem – warp jest zestrojony pod dynamikę.
    linear_solver = cfg.linear_solver if solver == "dynamic" or cfg.linear_solver == "cholmod" else "ldl"
    if chambers and linear_solver == "warp":
        # Warp z komorą przesuwa równowagę (30 ml: ciśnienie −25%), patrz README.
        import Sofa
        Sofa.msg_warning("fishsofa", 'linear_solver="warp" z komorami jest niedokładny – używam "ldl"')
        linear_solver = "ldl"
    if linear_solver == "ldl":
        # Bezpośredni solver liniowy (rozkład LDLᵀ macierzy rzadkiej). Bloki 3×3, bo każdy
        # węzeł ma 3 stopnie swobody – tak jest szybciej niż skalarnie.
        tail.addObject("SparseLDLSolver", name="linsolver", template="CompressedRowSparseMatrixMat3x3d")
    elif linear_solver == "cholmod":
        # CHOLMOD sam wybiera porządek eliminacji (AMD/METIS); OrderingMethod jest wymagany
        # przez API solvera, ale ignorowany (README wtyczki SofaCHOLMOD).
        root.addObject("RequiredPlugin", pluginName=["Sofa.Component.LinearSolver.Ordering", "SofaCHOLMOD"])
        tail.addObject("NaturalOrderingMethod", name="ordering")
        tail.addObject("EigenCholmodSupernodalLLT", name="linsolver", template="CompressedRowSparseMatrixMat3x3d",
                       numThreads=cfg.cholmod_threads, orderingMethod="@ordering")
    elif linear_solver == "cg":
        # Gradient sprzężony na złożonej (assembled) macierzy. Złożona macierz, a nie
        # wersja „matrix-free”, bo korekcja ograniczeń komór (etap 2) potrzebuje macierzy.
        # Warm start: rozwiązanie z poprzedniego kroku jako punkt startowy. threshold
        # (minimalne pᵀAp) musi być małe – domyślne 1e-5 w jednostkach SI zatrzymuje CG za wcześnie.
        tail.addObject("CGLinearSolver", name="linsolver", template="CompressedRowSparseMatrixMat3x3d",
                       iterations=cfg.cg_max_iterations, tolerance=cfg.cg_tolerance,
                       threshold=1e-30, warmStart=True)
    # "warp": komponenty dodajemy niżej, po FEM, bo linkują się do niego (rotationFinder).
    if linear_solver != "warp":
        _add_ode_solver(tail, cfg, solver)

    tail.addObject("MeshVTKLoader", name="loader", filename=os.path.join(folder, "tail.vtk"))
    tail.addObject("TetrahedronSetTopologyContainer", name="topology", src="@loader")
    dofs = tail.addObject("MechanicalObject", name="dofs", template="Vec3d")

    # Korotacyjny FEM (method="large"): dla każdego elementu wyznacza jego obrót i liczy
    # sprężystość liniową w układzie obróconym. Dzięki temu duże zgięcia ogona nie dają
    # sztucznego „puchnięcia”, jak w czysto liniowym FEM.
    fem_name = "ParallelTetrahedronFEMForceField" if cfg.parallel_fem else "TetrahedronFEMForceField"
    if cfg.parallel_fem:
        root.addObject("RequiredPlugin", pluginName=["MultiThreading"])
    # Moduł Younga na element: silikon albo sztywniejszy „kręgosłup” w przegrodzie.
    young = np.where(mesh.tet_region == 1, cfg.young_modulus * cfg.spine_E_factor, cfg.young_modulus)
    tail.addObject(fem_name, name="fem", method="large",
                   youngModulus=young.tolist(), poissonRatio=cfg.poisson_ratio)

    if linear_solver == "warp":
        _add_warp_solver(tail, cfg)
        _add_ode_solver(tail, cfg, solver)

    # Masa: spójna macierz masy z gęstością na element (silikon + woda z komór).
    tail.addObject("MeshMatrixMass", name="mass", massDensity=mm.element_density.tolist())

    # Mocowanie: węzły przedniej ściany nieruchome (ogon przykręcony do kadłuba,
    # jednocześnie stanowisko pomiaru ciągu na uwięzi). Constraint „projekcyjny”
    # zeruje ruch tych węzłów bezpośrednio w układzie równań.
    tail.addObject("FixedProjectiveConstraint", name="fixed", indices=mesh.base_nodes.tolist())

    # Ciężar (i wypór w wodzie) jako stałe siły węzłowe.
    weight = mm.node_weight if cfg.include_weight else np.zeros_like(mm.node_weight)
    tail.addObject("ConstantForceField", name="weight",
                   indices=list(range(len(mesh.points))), forces=weight.tolist())

    if cfg.hoop_fibers:
        _add_hoop_fibers(tail, cfg)

    # Opór wody (etap 5): siły na węzłach skóry, liczone co krok w Pythonie
    # (controller.WaterDragController) i wpisywane do tego ConstantForceField.
    # Skóra ma te same węzły co FEM, więc mapowanie nie jest potrzebne.
    water_ff = None
    if cfg.environment == "water" and solver == "dynamic":
        skin = np.unique(mesh.tri_outer)
        water_ff = tail.addObject("ConstantForceField", name="water", indices=skin.tolist(),
                                  forces=np.zeros((len(skin), 3)).tolist())

    if solver == "dynamic":
        # Korekcja ograniczeń: mówi solverowi ograniczeń, jak węzły zareagują na siły
        # ograniczeń (używa faktoryzacji solvera liniowego). Przy "warp" link do
        # prekondycjonera, nie do PCG: PCG jest „matrix-free” i nie umie policzyć
        # podatności J·A⁻¹·Jᵀ (wskazówka opiekuna SOFA, SoftRobots discussion #252).
        if linear_solver == "warp":
            tail.addObject("LinearSolverConstraintCorrection", linearSolver="@warp")
        else:
            tail.addObject("LinearSolverConstraintCorrection")

    spcs = {side: add_chamber(tail, folder, side, mode, cfg) for side, mode in chambers.items()}

    if gui:
        visu = tail.addChild("visu")
        visu.addObject("MeshOBJLoader", name="loader", filename=os.path.join(folder, "outer.obj"))
        visu.addObject("OglModel", src="@loader", color=[0.95, 0.70, 0.30, 1.0])
        visu.addObject("BarycentricMapping")

    h = {"tail": tail, "dofs": dofs, "mesh": mesh, "masses": mm, "folder": folder,
         "chambers": spcs, "dt": cfg.dt, "water": None}
    if water_ff is not None:
        from fishsofa.controller import WaterDragController
        h["water"] = root.addObject(WaterDragController(name="waterDrag", root=root, handles=h,
                                                        force_field=water_ff, cfg=cfg))
    return h


def add_chamber(tail, folder: str, side: str, mode: str, cfg: TailConfig):
    """Komora hydrauliczna L (+Y) albo R (−Y) jako węzeł-dziecko ogona.

    mode="volume"   – SurfacePressureConstraint z valueType="volumeGrowth": zadajemy
                      przyrost objętości (pompa wymusza objętość, woda jest nieściśliwa),
                      SOFA liczy potrzebne ciśnienie (mnożnik Lagrange'a),
    mode="pressure" – zadajemy ciśnienie (value = p·dt, patrz hydraulics.py),
    mode="vented"   – brak komponentu: wnęka bez ograniczenia, ciśnienie 0, jak komora
                      z otwartym króćcem na stanowisku pomiarowym. Zwraca None.
    Powierzchnia wnęki jest „przyklejona” do FEM przez BarycentricMapping (jej węzły to
    węzły FEM, więc mapowanie jest dokładne); siły ciśnienia wracają tą samą drogą.
    """
    if mode == "vented":
        return None
    if mode not in ("volume", "pressure"):
        raise ValueError(mode)
    node = tail.addChild(f"chamber{side}")
    node.addObject("MeshOBJLoader", name="loader", filename=os.path.join(folder, f"chamber_{side}.obj"))
    node.addObject("MeshTopology", name="topology", src="@loader")
    node.addObject("MechanicalObject", name="dofs", template="Vec3d")
    spc = node.addObject("SurfacePressureConstraint", name="spc", value=[0.0],
                         valueType="volumeGrowth" if mode == "volume" else "pressure")
    node.addObject("BarycentricMapping", name="mapping")
    return spc


def _add_hoop_fibers(tail, cfg: TailConfig):
    """Oplot obwodowy: pierścienie sprężyn tuż pod skórą, przyczepione do FEM.

    Pierwsza wersja kładła sprężyny na krawędziach siatki skóry, ale siatka z loftu nie
    ma krawędzi obwodowych (są osiowe i ukośne 45–72°), więc oplotu w praktyce nie było.
    Teraz pierścienie są osobnymi punktami (fishsofa/fibers.py), a BarycentricMapping
    przenosi ich ruch z czworościanów, w których leżą, i oddaje siły włókien do FEM.
    """
    from fishsofa import fibers

    ring = fibers.hoop_rings(cfg)
    node = tail.addChild("hoopFibers")
    node.addObject("MechanicalObject", name="dofs", template="Vec3d", position=ring.points.tolist())
    # StiffSpringForceField dodaje też macierz sztywności sprężyn do układu niejawnego,
    # więc sztywne włókna nie psują stabilności. elongationOnly: nić nie pcha przy ściskaniu.
    node.addObject("StiffSpringForceField", name="springs",
                   springsIndices1=ring.springs[:, 0].tolist(), springsIndices2=ring.springs[:, 1].tolist(),
                   stiffness=ring.stiffness.tolist(), damping=[0.0] * len(ring.springs),
                   lengths=ring.lengths.tolist(), elongationOnly=" ".join(["1"] * len(ring.springs)),
                   enabled=" ".join(["1"] * len(ring.springs)))
    node.addObject("BarycentricMapping", name="mapping", input="@../dofs", output="@dofs")


def _add_ode_solver(tail, cfg: TailConfig, solver: str):
    """Integrator czasu. Jawny link do solvera liniowego "linsolver": przy "warp" w węźle
    są dwa solvery liniowe (PCG i LDL w prekondycjonerze), a bez linku integrator wziąłby
    pierwszy znaleziony – LDL – i PCG nie byłby w ogóle używany (tak było w 1. próbie)."""
    if solver == "dynamic":
        # Niejawny (implicit) Euler: stabilny nawet przy sztywnym FEM i dużym kroku,
        # bo w każdym kroku rozwiązuje układ z macierzą (M − dt·C − dt²·K).
        # Rayleigh: tłumienie C = α·M + β·K, zastępuje tłumienie materiałowe silikonu.
        tail.addObject("EulerImplicitSolver", name="odesolver",
                       rayleighMass=cfg.rayleigh_mass, rayleighStiffness=cfg.rayleigh_stiffness,
                       linearSolver="@linsolver")
    elif solver == "static":
        # Statyka: szuka położenia, w którym siły wewnętrzne (FEM) równoważą ciężar.
        # FEM korotacyjny jest nieliniowy, więc równowagę liczy metoda Newtona-Raphsona
        # (od v25.12 osobny komponent). Pierwsza iteracja zwykle „przestrzeliwuje”
        # (ostrzeżenie „Line search failed at Newton iteration 0”), kolejne już zbiegają.
        tail.addObject("NewtonRaphsonSolver", name="newton", maxNbIterationsNewton=30,
                       absoluteResidualStoppingThreshold=1e-6)
        tail.addObject("StaticSolver", name="odesolver", newtonSolver="@newton", linearSolver="@linsolver")


def _add_warp_solver(tail, cfg: TailConfig):
    """PCG z prekondycjonerem „warp”: rozkład LDLᵀ liczony RAZ, w stanie spoczynku.

    Idea (korotacyjny FEM): macierz sztywności odkształconego ogona ≈ R·K₀·Rᵀ, gdzie K₀
    to macierz w spoczynku, a R to obroty elementów. Rozkład K₀ (drogi) robimy raz,
    a w każdym kroku tylko „obracamy” go o aktualne R (tanie). Taki obrócony rozkład nie
    jest dokładną odwrotnością aktualnej macierzy, więc służy jako prekondycjoner:
    PCG (gradient sprzężony, bez składania macierzy) kilkoma iteracjami doprowadza
    rozwiązanie do dokładnego.

    Kluczowe ustawienie: assemblingRate RotationMatrixSystem bardzo duże = macierz
    złożona tylko w pierwszym kroku (spoczynek). Przy np. 15 macierz była składana
    w stanie odkształconym, a obrót z TetrahedronFEMForceField (liczony względem
    spoczynku) nakładał się drugi raz – symulacja wybuchała (etap 1, README).
    Kolejność dodawania: obiekty, do których prowadzą linki „@…”, muszą już istnieć.
    """
    tail.addObject("MatrixLinearSystem", name="sys", template="CompressedRowSparseMatrixMat3x3d")
    tail.addObject("SparseLDLSolver", name="ldl", template="CompressedRowSparseMatrixMat3x3d",
                   linearSystem="@sys")
    tail.addObject("RotationMatrixSystem", name="rot", assemblingRate=cfg.warp_refactor_steps,
                   rotationFinder="@fem")
    tail.addObject("WarpPreconditioner", name="warp", linearSystem="@rot", linearSolver="@ldl")
    tail.addObject("PreconditionedMatrixFreeSystem", name="mfs", assemblingRate=1,
                   preconditionerSystem="@rot")
    tail.addObject("PCGLinearSolver", name="linsolver", linearSystem="@mfs", preconditioner="@warp",
                   iterations=cfg.cg_max_iterations, tolerance=cfg.cg_tolerance)


def createScene(root):
    """Wejście dla runSofa. Poziom siatki z FISHSOFA_LEVEL (domyślnie coarse).

    FISHSOFA_MODE="flap" (domyślnie, etap 4): obie komory + pompa L↔R, ogon macha
    (prefill 1 s, potem rytm z rampą 1 s). FISHSOFA_MODE="sag" (etap 1): sam materiał.
    """
    level = os.environ.get("FISHSOFA_LEVEL", "coarse")
    mode = os.environ.get("FISHSOFA_MODE", "flap")
    cfg = TailConfig(environment=os.environ.get("FISHSOFA_ENV", "air"))
    if mode == "sag":
        build_tail(root, cfg, level, gui=True)
    elif mode == "flap":
        from fishsofa.controller import FlapController
        h = build_tail(root, cfg, level, gui=True, chambers={"L": "volume", "R": "volume"})
        for spc in h["chambers"].values():
            spc.drawPressure = True   # SoftRobots rysuje ciśnienie na powierzchni komory
        root.addObject(FlapController(name="flap", root=root, handles=h, cfg=cfg))
    else:
        raise ValueError(f"FISHSOFA_MODE={mode!r}: dozwolone flap, sag")
    return root
