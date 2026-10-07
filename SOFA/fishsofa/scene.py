"""SOFA scene: soft FEM tail attached to the body.

GUI:      scripts/run_gui.sh [coarse|medium|fine]    (runSofa calls createScene;
          FISHSOFA_MODE=flap – flapping, default; sag – sag under own weight;
          FISHSOFA_ENV=air – default, water – water drag and apparent weight;
          FISHSOFA_MODE=replay – real-time playback of recording FISHSOFA_RECORDING)
Headless: fishsofa.headless (same build_tail function)

Stage 1: material only, no actuation – the tail sags under its own weight.
The structure (FreeMotionAnimationLoop + constraint solver + constraint correction) is
already what the SurfacePressureConstraint chambers of stage 2 require.

Scene tree:
  root                      FreeMotionAnimationLoop, BlockGaussSeidelConstraintSolver
  └─ tail                   integrator, linear solver, FEM, mass, fixation, weight
     └─ visu (GUI only)     outer surface for rendering
"""
import os

import numpy as np

from fishsofa import masses, mesh_gen
from fishsofa.config import TailConfig

# SOFA modules providing this scene's components. An explicit list (instead of the
# "Sofa.Component" meta-plugin) tells the reader where each component comes from.
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
    "Sofa.Component.SolidMechanics.Spring",           # StiffSpringForceField (fibers)
    "Sofa.Component.Topology.Container.Constant",     # MeshTopology (chamber surface)
]
GUI_PLUGINS = ["Sofa.GL.Component.Rendering3D", "Sofa.Component.Visual"]


def build_tail(root, cfg: TailConfig, level: str, mesh_root: str | None = None,
               solver: str = "dynamic", gui: bool = False, chambers: dict | None = None) -> dict:
    """Builds the tail under the root node. Returns component handles and mesh data.

    solver="dynamic" – EulerImplicitSolver (motion in time),
    solver="static"  – StaticSolver (equilibrium directly, Newton's method; no chambers).
    chambers – e.g. {"L": "volume", "R": "vented"}; modes in add_chamber().
    """
    chambers = chambers or {}
    if chambers and solver == "static":
        raise ValueError("chambers (Lagrange constraints) require solver='dynamic' – "
                         "StaticSolver does not work with FreeMotionAnimationLoop (stage 1)")
    folder = mesh_gen.ensure(cfg, level, mesh_root)
    mesh = mesh_gen.load(cfg, level, mesh_root)
    mm = masses.build(mesh, cfg)

    root.addObject("RequiredPlugin", pluginName=PLUGINS + (GUI_PLUGINS if gui else [])
                   + (["SoftRobots"] if chambers else []))
    root.dt = cfg.dt
    # SOFA gravity disabled – we compute the weight ourselves (see fishsofa/masses.py).
    root.gravity = [0.0, 0.0, 0.0]

    if solver == "dynamic":
        # Constrained animation loop: first a "free" motion (no constraints), then the
        # constraint solver computes Lagrange multipliers and corrects the motion. Stage 1
        # has no Lagrange constraints yet (chambers are added in stage 2).
        root.addObject("FreeMotionAnimationLoop")
        root.addObject("BlockGaussSeidelConstraintSolver", maxIterations=500, tolerance=1e-9)
    else:
        # StaticSolver in SOFA v26.06 does not work with FreeMotionAnimationLoop (verified:
        # the tail does not move), so statics uses the plain loop. Chambers with Lagrange
        # constraints in statics are a stage 2 topic.
        root.addObject("DefaultAnimationLoop")
    if gui:
        root.addObject("VisualStyle", displayFlags="showVisualModels showBehaviorModels")

    tail = root.addChild("tail")
    if solver not in ("dynamic", "static"):
        raise ValueError(solver)
    # Statics (Newton) always uses an exact factorization – warp is tuned for dynamics.
    linear_solver = cfg.linear_solver if solver == "dynamic" or cfg.linear_solver == "cholmod" else "ldl"
    if chambers and linear_solver == "warp":
        # Warp with a chamber shifts the equilibrium (30 ml: pressure −25%), see README.
        import Sofa
        Sofa.msg_warning("fishsofa", 'linear_solver="warp" is inaccurate with chambers – using "ldl"')
        linear_solver = "ldl"
    if linear_solver == "ldl":
        # Direct linear solver (LDLᵀ factorization of the sparse matrix). 3×3 blocks, since
        # each node has 3 degrees of freedom – faster than scalar.
        tail.addObject("SparseLDLSolver", name="linsolver", template="CompressedRowSparseMatrixMat3x3d")
    elif linear_solver == "cholmod":
        # CHOLMOD picks the elimination ordering itself (AMD/METIS); OrderingMethod is required
        # by the solver API but ignored (SofaCHOLMOD plugin README).
        root.addObject("RequiredPlugin", pluginName=["Sofa.Component.LinearSolver.Ordering", "SofaCHOLMOD"])
        tail.addObject("NaturalOrderingMethod", name="ordering")
        tail.addObject("EigenCholmodSupernodalLLT", name="linsolver", template="CompressedRowSparseMatrixMat3x3d",
                       numThreads=cfg.cholmod_threads, orderingMethod="@ordering")
    elif linear_solver == "cg":
        # Conjugate gradient on the assembled matrix. Assembled rather than "matrix-free",
        # because the chamber constraint correction (stage 2) needs the matrix.
        # Warm start: the previous step's solution as the starting point. threshold
        # (minimum pᵀAp) must be small – the default 1e-5 in SI units stops CG too early.
        tail.addObject("CGLinearSolver", name="linsolver", template="CompressedRowSparseMatrixMat3x3d",
                       iterations=cfg.cg_max_iterations, tolerance=cfg.cg_tolerance,
                       threshold=1e-30, warmStart=True)
    # "warp": components are added below, after the FEM, because they link to it (rotationFinder).
    if linear_solver != "warp":
        _add_ode_solver(tail, cfg, solver)

    tail.addObject("MeshVTKLoader", name="loader", filename=os.path.join(folder, "tail.vtk"))
    tail.addObject("TetrahedronSetTopologyContainer", name="topology", src="@loader")
    dofs = tail.addObject("MechanicalObject", name="dofs", template="Vec3d")

    # Corotational FEM (method="large"): finds each element's rotation and computes linear
    # elasticity in the rotated frame. Large tail bends thus do not cause the artificial
    # "swelling" of purely linear FEM.
    fem_name = "ParallelTetrahedronFEMForceField" if cfg.parallel_fem else "TetrahedronFEMForceField"
    if cfg.parallel_fem:
        root.addObject("RequiredPlugin", pluginName=["MultiThreading"])
    # Young's modulus per element: silicone or the stiffer "spine" in the septum.
    young = np.where(mesh.tet_region == 1, cfg.young_modulus * cfg.spine_E_factor, cfg.young_modulus)
    tail.addObject(fem_name, name="fem", method="large",
                   youngModulus=young.tolist(), poissonRatio=cfg.poisson_ratio)

    if linear_solver == "warp":
        _add_warp_solver(tail, cfg)
        _add_ode_solver(tail, cfg, solver)

    # Mass: consistent mass matrix with per-element density (silicone + chamber water).
    tail.addObject("MeshMatrixMass", name="mass", massDensity=mm.element_density.tolist())

    # Fixation: front-wall nodes are fixed (tail bolted to the body, which is also the
    # tethered thrust test rig). The "projective" constraint zeroes the motion of these
    # nodes directly in the system of equations.
    tail.addObject("FixedProjectiveConstraint", name="fixed", indices=mesh.base_nodes.tolist())

    # Weight (and buoyancy in water) as constant nodal forces.
    weight = mm.node_weight if cfg.include_weight else np.zeros_like(mm.node_weight)
    tail.addObject("ConstantForceField", name="weight",
                   indices=list(range(len(mesh.points))), forces=weight.tolist())

    if cfg.hoop_fibers:
        _add_hoop_fibers(tail, cfg)

    # Water drag (stage 5): forces on skin nodes, computed every step in Python
    # (controller.WaterDragController) and written into this ConstantForceField.
    # The skin shares nodes with the FEM, so no mapping is needed.
    water_ff = None
    if cfg.environment == "water" and solver == "dynamic":
        skin = np.unique(mesh.tri_outer)
        water_ff = tail.addObject("ConstantForceField", name="water", indices=skin.tolist(),
                                  forces=np.zeros((len(skin), 3)).tolist())

    if solver == "dynamic":
        # Constraint correction: tells the constraint solver how nodes respond to constraint
        # forces (uses the linear solver's factorization). With "warp" it links to the
        # preconditioner, not the PCG: PCG is "matrix-free" and cannot compute the
        # compliance J·A⁻¹·Jᵀ (SOFA maintainer's advice, SoftRobots discussion #252).
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
    """Hydraulic chamber L (+Y) or R (−Y) as a child node of the tail.

    mode="volume"   – SurfacePressureConstraint with valueType="volumeGrowth": we prescribe
                      the volume growth (the pump imposes volume, water is incompressible),
                      SOFA computes the required pressure (Lagrange multiplier),
    mode="pressure" – we prescribe the pressure (value = p·dt, see hydraulics.py),
    mode="vented"   – no component: unconstrained cavity, pressure 0, like a chamber
                      with an open port on the test rig. Returns None.
    The cavity surface is "glued" to the FEM by BarycentricMapping (its nodes are FEM
    nodes, so the mapping is exact); pressure forces return the same way.
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
    """Hoop fibers: rings of springs just under the skin, attached to the FEM.

    The first version placed springs on skin mesh edges, but the lofted mesh has no
    circumferential edges (they are axial and diagonal, 45–72°), so in practice there were no
    hoop fibers. Now the rings are separate points (fishsofa/fibers.py), and BarycentricMapping
    carries their motion from the tetrahedra they lie in and returns fiber forces to the FEM.
    """
    from fishsofa import fibers

    ring = fibers.hoop_rings(cfg)
    node = tail.addChild("hoopFibers")
    node.addObject("MechanicalObject", name="dofs", template="Vec3d", position=ring.points.tolist())
    # StiffSpringForceField also adds the spring stiffness matrix to the implicit system,
    # so stiff fibers do not hurt stability. elongationOnly: a thread does not push in compression.
    node.addObject("StiffSpringForceField", name="springs",
                   springsIndices1=ring.springs[:, 0].tolist(), springsIndices2=ring.springs[:, 1].tolist(),
                   stiffness=ring.stiffness.tolist(), damping=[0.0] * len(ring.springs),
                   lengths=ring.lengths.tolist(), elongationOnly=" ".join(["1"] * len(ring.springs)),
                   enabled=" ".join(["1"] * len(ring.springs)))
    node.addObject("BarycentricMapping", name="mapping", input="@../dofs", output="@dofs")


def _add_ode_solver(tail, cfg: TailConfig, solver: str):
    """Time integrator. Explicit link to the linear solver "linsolver": with "warp" the node
    has two linear solvers (PCG and the LDL in the preconditioner), and without the link the
    integrator would take the first one found – LDL – and PCG would not be used at all (as
    happened in the 1st attempt)."""
    if solver == "dynamic":
        # Implicit Euler: stable even with stiff FEM and a large step, since each step
        # solves a system with the matrix (M − dt·C − dt²·K).
        # Rayleigh: damping C = α·M + β·K, stands in for the silicone's material damping.
        tail.addObject("EulerImplicitSolver", name="odesolver",
                       rayleighMass=cfg.rayleigh_mass, rayleighStiffness=cfg.rayleigh_stiffness,
                       linearSolver="@linsolver")
    elif solver == "static":
        # Statics: finds the configuration where internal (FEM) forces balance the weight.
        # Corotational FEM is nonlinear, so the equilibrium is found by Newton-Raphson
        # (a separate component since v25.12). The first iteration usually "overshoots"
        # (warning "Line search failed at Newton iteration 0"), later ones converge.
        tail.addObject("NewtonRaphsonSolver", name="newton", maxNbIterationsNewton=30,
                       absoluteResidualStoppingThreshold=1e-6)
        tail.addObject("StaticSolver", name="odesolver", newtonSolver="@newton", linearSolver="@linsolver")


def _add_warp_solver(tail, cfg: TailConfig):
    """PCG with a "warp" preconditioner: the LDLᵀ factorization is computed ONCE, at rest.

    Idea (corotational FEM): the stiffness matrix of the deformed tail ≈ R·K₀·Rᵀ, where K₀
    is the rest matrix and R the element rotations. The (expensive) factorization of K₀ is
    done once, and each step only "rotates" it by the current R (cheap). Such a rotated
    factorization is not the exact inverse of the current matrix, so it serves as a
    preconditioner: PCG (conjugate gradient, no matrix assembly) brings the solution to
    the exact one in a few iterations.

    Key setting: a very large RotationMatrixSystem assemblingRate = the matrix is assembled
    only in the first step (at rest). With e.g. 15 the matrix was assembled in the deformed
    state, and the rotation from TetrahedronFEMForceField (computed relative to rest) was
    applied a second time – the simulation blew up (stage 1, README).
    Order of addition: objects targeted by "@..." links must already exist.
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
    """Entry point for runSofa. Mesh level from FISHSOFA_LEVEL (default coarse).

    FISHSOFA_MODE="flap" (default, stage 4): both chambers + L↔R pump, the tail flaps
    (prefill 1 s, then the rhythm with a 1 s ramp). FISHSOFA_MODE="sag" (stage 1): material only.
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
            spc.drawPressure = True   # SoftRobots draws the pressure on the chamber surface
        root.addObject(FlapController(name="flap", root=root, handles=h, cfg=cfg))
    elif mode == "replay":
        # Real-time playback of a recording from scripts/record.py (no physics).
        from fishsofa import replay
        replay.build(root, os.environ["FISHSOFA_RECORDING"], float(os.environ.get("FISHSOFA_SPEED", "1")))
    else:
        raise ValueError(f"FISHSOFA_MODE={mode!r}: allowed: flap, sag, replay")
    return root
