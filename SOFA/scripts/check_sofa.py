"""Stage 0: check the SOFA installation and the actual component names.

Usage:  source SOFA/scripts/env.sh && python SOFA/scripts/check_sofa.py

Why: the SOFA API changes between versions (e.g. GenericConstraintSolver was replaced
by BlockGaussSeidelConstraintSolver and others, FixedConstraint by
FixedProjectiveConstraint). Instead of guessing, we try to create each component
in a small scene and print which name exists in this version's object factory.

Exit code 0 = every required component has at least one working name.
"""
import os
import sys

import Sofa
import Sofa.Core
import Sofa.Simulation
import SofaRuntime

# Role in the tail scene (spec section 5) -> names to check, in order of preference,
# plus the node in which the component is created (some need a MechanicalObject in the
# context so that SOFA can deduce the template, e.g. Vec3d).
CANDIDATES = [
    # (role, required?, node, [names])
    ("constrained animation loop", True, "root", ["FreeMotionAnimationLoop"]),
    ("Lagrange constraint solver", True, "root",
     ["BlockGaussSeidelConstraintSolver", "GenericConstraintSolver",
      "NNCGConstraintSolver", "ProjectedGaussSeidelConstraintSolver"]),
    ("implicit integrator", True, "fem", ["EulerImplicitSolver"]),
    ("static solver (option for stage 2)", False, "fem", ["StaticSolver"]),
    ("direct linear solver", True, "fem", ["SparseLDLSolver"]),
    ("constraint correction", True, "fem",
     ["GenericConstraintCorrection", "LinearSolverConstraintCorrection"]),
    ("mechanical state (nodes)", True, "root", ["MechanicalObject"]),
    ("tetra topology", True, "fem", ["TetrahedronSetTopologyContainer", "MeshTopology"]),
    ("corotational FEM", True, "fem", ["TetrahedronFEMForceField"]),
    ("mass", True, "fem", ["MeshMatrixMass", "UniformMass"]),
    ("node fixing", True, "fem", ["FixedProjectiveConstraint", "FixedConstraint"]),
    ("node selection by box", True, "fem", ["BoxROI"]),
    ("nodal forces (water drag)", True, "fem", ["ConstantForceField"]),
    ("volume mesh loader", True, "root", ["MeshVTKLoader", "MeshGmshLoader"]),
    ("chamber surface loader", True, "root", ["MeshSTLLoader", "MeshOBJLoader"]),
    ("pressure chamber (SoftRobots)", True, "sub", ["SurfacePressureConstraint"]),
    ("chamber-to-FEM mapping", True, "sub", ["BarycentricMapping"]),
]

# SurfacePressureConstraint fields used by the hydraulics and the tests.
SPC_FIELDS = ["value", "valueType", "pressure", "cavityVolume", "initialCavityVolume",
              "volumeGrowth", "maxPressure", "minPressure", "maxVolumeGrowth",
              "minVolumeGrowth", "maxVolumeGrowthVariation", "flipNormal",
              "drawPressure", "drawScale"]


# Real mesh files from the SOFA binary – a loader without a file fails already on creation.
_SHARE = os.path.join(os.environ.get("SOFA_ROOT", ""), "share", "sofa", "mesh")
_SPRINGY = os.path.join(os.environ.get("SOFA_ROOT", ""), "plugins", "SoftRobots", "lib", "python3",
                        "site-packages", "softrobots", "parts", "bunny", "mesh")
EXTRA_ARGS = {
    "MeshVTKLoader": {"filename": os.path.join(_SPRINGY, "Springy.vtk")},
    "MeshGmshLoader": {"filename": os.path.join(_SHARE, "liver2.msh")},
    "MeshSTLLoader": {"filename": os.path.join(_SPRINGY, "Springy_Cavity.stl")},
    "MeshOBJLoader": {"filename": os.path.join(_SPRINGY, "Hollow_Bunny_Body_Cavity.obj")},
    # The mapping links two mechanical states – without links SOFA cannot deduce the template.
    "BarycentricMapping": {"input": "@../dofs", "output": "@dofs"},
}


def build_context():
    """Small scene: root -> fem (MechanicalObject) -> sub (MechanicalObject).

    Nothing is simulated here – the nodes only provide a context for creating components.
    Each component gets a fresh context, so that e.g. two masses don't end up in one node.
    """
    root = Sofa.Core.Node("root")
    fem = root.addChild("fem")
    fem.addObject("MechanicalObject", name="dofs", template="Vec3d", position=[[0, 0, 0]])
    sub = fem.addChild("sub")
    sub.addObject("MechanicalObject", name="dofs", template="Vec3d", position=[[0, 0, 0]])
    return {"root": root, "fem": fem, "sub": sub}


def try_create(where, name):
    # Keep a reference to the whole dict: if Python freed root, the child node would
    # lose its parent and links like "@../dofs" would have no target.
    ctx = build_context()
    node = ctx[where]
    try:
        return node.addObject(name, name=f"probe_{name}", **EXTRA_ARGS.get(name, {})), None
    except Exception as e:  # SofaPython3 raises ValueError when the factory does not know the name
        return None, str(e).strip().splitlines()[-1]


def main():
    # "Sofa.Component" is a meta-plugin that loads all standard component modules.
    for plugin in ("Sofa.Component", "SoftRobots"):
        SofaRuntime.importPlugin(plugin)
    print(f"Python: {sys.version.split()[0]}")
    print(f"SOFA_ROOT: {os.environ.get('SOFA_ROOT')}")
    print(f"SOFA version: {Sofa.GetVersion()}")

    missing_required = []
    spc = None

    print("\nComponents (✓ = exists, - = missing in this version):")
    for role, required, where, names in CANDIDATES:
        found = []
        for n in names:
            obj, err = try_create(where, n)
            found.append((n, obj is not None))
            if n == "SurfacePressureConstraint" and obj is not None:
                spc = obj
        ok = [n for n, f in found if f]
        mark = ", ".join(("✓ " if f else "- ") + n for n, f in found)
        print(f"  {role:38s} {mark}")
        if required and not ok:
            missing_required.append(role)

    if spc is not None:
        print("\nSurfacePressureConstraint fields:")
        all_fields = {d.getName(): d for d in spc.getDataFields()}
        for f in SPC_FIELDS:
            if f in all_fields:
                help_txt = " ".join(all_fields[f].getHelp().split())
                print(f"  ✓ {f:26s} {help_txt[:90]}")
            else:
                print(f"  - {f:26s} (missing)")
                if f in ("value", "valueType", "pressure", "cavityVolume"):
                    missing_required.append(f"field SurfacePressureConstraint.{f}")
        opts = all_fields.get("valueType")
        if opts is not None:
            print(f"  valueType default: {opts.value}")

    if missing_required:
        print("\nMISSING required:", ", ".join(missing_required))
        return 1
    print("\nOK: all required components and fields are available.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
