"""Etap 0: sprawdzenie instalacji SOFA i faktycznych nazw komponentów.

Uruchomienie:  source SOFA/scripts/env.sh && python SOFA/scripts/check_sofa.py

Po co: API SOFA zmienia się między wersjami (np. GenericConstraintSolver został
zastąpiony przez BlockGaussSeidelConstraintSolver i inne, FixedConstraint przez
FixedProjectiveConstraint). Zamiast zgadywać, próbujemy utworzyć każdy komponent
w małej scenie i wypisujemy, która nazwa istnieje w fabryce obiektów tej wersji.

Kod wyjścia 0 = każdy wymagany komponent ma co najmniej jedną działającą nazwę.
"""
import os
import sys

import Sofa
import Sofa.Core
import Sofa.Simulation
import SofaRuntime

# Rola w scenie ogona (sekcja 5 specu) -> nazwy do sprawdzenia, w kolejności preferencji,
# oraz węzeł, w którym komponent tworzymy (część potrzebuje MechanicalObject w kontekście,
# żeby SOFA mogła wydedukować szablon, np. Vec3d).
CANDIDATES = [
    # (rola, wymagany?, węzeł, [nazwy])
    ("pętla animacji z ograniczeniami", True, "root", ["FreeMotionAnimationLoop"]),
    ("solver ograniczeń Lagrange'a", True, "root",
     ["BlockGaussSeidelConstraintSolver", "GenericConstraintSolver",
      "NNCGConstraintSolver", "ProjectedGaussSeidelConstraintSolver"]),
    ("integrator niejawny", True, "fem", ["EulerImplicitSolver"]),
    ("solver statyczny (opcja dla etapu 2)", False, "fem", ["StaticSolver"]),
    ("bezpośredni solver liniowy", True, "fem", ["SparseLDLSolver"]),
    ("korekcja ograniczeń", True, "fem",
     ["GenericConstraintCorrection", "LinearSolverConstraintCorrection"]),
    ("stan mechaniczny (węzły)", True, "root", ["MechanicalObject"]),
    ("topologia tetra", True, "fem", ["TetrahedronSetTopologyContainer", "MeshTopology"]),
    ("FEM korotacyjny", True, "fem", ["TetrahedronFEMForceField"]),
    ("masa", True, "fem", ["MeshMatrixMass", "UniformMass"]),
    ("mocowanie węzłów", True, "fem", ["FixedProjectiveConstraint", "FixedConstraint"]),
    ("wybór węzłów prostopadłościanem", True, "fem", ["BoxROI"]),
    ("siły węzłowe (opór wody)", True, "fem", ["ConstantForceField"]),
    ("loader siatki objętościowej", True, "root", ["MeshVTKLoader", "MeshGmshLoader"]),
    ("loader powierzchni komory", True, "root", ["MeshSTLLoader", "MeshOBJLoader"]),
    ("komora ciśnieniowa (SoftRobots)", True, "sub", ["SurfacePressureConstraint"]),
    ("mapowanie komory na FEM", True, "sub", ["BarycentricMapping"]),
]

# Pola SurfacePressureConstraint, z których korzystają hydraulika i testy.
SPC_FIELDS = ["value", "valueType", "pressure", "cavityVolume", "initialCavityVolume",
              "volumeGrowth", "maxPressure", "minPressure", "maxVolumeGrowth",
              "minVolumeGrowth", "maxVolumeGrowthVariation", "flipNormal",
              "drawPressure", "drawScale"]


# Prawdziwe pliki siatek z binarki SOFA – loader bez pliku zgłasza błąd już przy tworzeniu.
_SHARE = os.path.join(os.environ.get("SOFA_ROOT", ""), "share", "sofa", "mesh")
_SPRINGY = os.path.join(os.environ.get("SOFA_ROOT", ""), "plugins", "SoftRobots", "lib", "python3",
                        "site-packages", "softrobots", "parts", "bunny", "mesh")
EXTRA_ARGS = {
    "MeshVTKLoader": {"filename": os.path.join(_SPRINGY, "Springy.vtk")},
    "MeshGmshLoader": {"filename": os.path.join(_SHARE, "liver2.msh")},
    "MeshSTLLoader": {"filename": os.path.join(_SPRINGY, "Springy_Cavity.stl")},
    "MeshOBJLoader": {"filename": os.path.join(_SPRINGY, "Hollow_Bunny_Body_Cavity.obj")},
    # Mapowanie łączy dwa stany mechaniczne – bez linków SOFA nie wydedukuje szablonu.
    "BarycentricMapping": {"input": "@../dofs", "output": "@dofs"},
}


def build_context():
    """Mała scena: root -> fem (MechanicalObject) -> sub (MechanicalObject).

    Nic tu nie jest symulowane – węzły dają tylko kontekst do tworzenia komponentów.
    Każdy komponent dostaje świeży kontekst, żeby np. dwie masy nie trafiły do jednego węzła.
    """
    root = Sofa.Core.Node("root")
    fem = root.addChild("fem")
    fem.addObject("MechanicalObject", name="dofs", template="Vec3d", position=[[0, 0, 0]])
    sub = fem.addChild("sub")
    sub.addObject("MechanicalObject", name="dofs", template="Vec3d", position=[[0, 0, 0]])
    return {"root": root, "fem": fem, "sub": sub}


def try_create(where, name):
    # Trzymamy referencję do całego słownika: gdyby root został zwolniony przez Pythona,
    # węzeł-dziecko straciłby rodzica i linki typu "@../dofs" nie miałyby celu.
    ctx = build_context()
    node = ctx[where]
    try:
        return node.addObject(name, name=f"probe_{name}", **EXTRA_ARGS.get(name, {})), None
    except Exception as e:  # SofaPython3 rzuca ValueError, gdy fabryka nie zna nazwy
        return None, str(e).strip().splitlines()[-1]


def main():
    # "Sofa.Component" to meta-plugin ładujący wszystkie standardowe moduły komponentów.
    for plugin in ("Sofa.Component", "SoftRobots"):
        SofaRuntime.importPlugin(plugin)
    print(f"Python: {sys.version.split()[0]}")
    print(f"SOFA_ROOT: {os.environ.get('SOFA_ROOT')}")
    print(f"Wersja SOFA: {Sofa.GetVersion()}")

    missing_required = []
    spc = None

    print("\nKomponenty (✓ = istnieje, - = brak w tej wersji):")
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
        print("\nPola SurfacePressureConstraint:")
        all_fields = {d.getName(): d for d in spc.getDataFields()}
        for f in SPC_FIELDS:
            if f in all_fields:
                help_txt = " ".join(all_fields[f].getHelp().split())
                print(f"  ✓ {f:26s} {help_txt[:90]}")
            else:
                print(f"  - {f:26s} (brak)")
                if f in ("value", "valueType", "pressure", "cavityVolume"):
                    missing_required.append(f"pole SurfacePressureConstraint.{f}")
        opts = all_fields.get("valueType")
        if opts is not None:
            print(f"  valueType domyślnie: {opts.value}")

    if missing_required:
        print("\nBRAK wymaganych:", ", ".join(missing_required))
        return 1
    print("\nOK: wszystkie wymagane komponenty i pola są dostępne.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
