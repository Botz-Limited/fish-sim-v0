"""Etap 0: pomiar semantyki SurfacePressureConstraint (valueType="volumeGrowth").

Uruchomienie:  source SOFA/scripts/env.sh && python SOFA/scripts/probe_volume_growth.py

Pytania, na które odpowiada (od nich zależy hydraulics.py):
  1. Czy `value` to przyrost objętości CAŁKOWITY względem objętości początkowej,
     czy przyrost NA KROK? Test: trzymamy stałe `value` przez wiele kroków.
     Całkowity -> zmierzony przyrost się zatrzymuje; na krok -> rośnie liniowo.
  2. Znak: czy dodatnie `value` powiększa wnękę i daje dodatnie ciśnienie?
  3. Jednostki pola `pressure`: Pa czy p·dt? Test: ten sam stan ustalony przy dwóch
     różnych dt. Surowe pressure niezależne od dt -> Pa; skaluje się z dt -> p·dt.
     Historia: SOFA v26.06 dawała impuls λ = p·dt (opis pola nadal mówi „podziel
     przez dt”). Od SOFA PR #6117 (gałąź master, v26.12) solver ograniczeń liczy
     siły zamiast impulsów, więc pole jest w Pa.
  4. Czy w trybie valueType="pressure" `value` jest w tych samych jednostkach co pole
     `pressure`? Test: zadajemy jako value to, co odczytaliśmy z pola.

Scena: pusty w środku „królik” z przykładów SoftRobots (siatka w mm, więc tu
wyjątkowo NIE pracujemy w SI – do odpowiedzi na powyższe pytania jednostki nie mają
znaczenia). Grawitacja wyłączona, żeby jedynym obciążeniem była komora.
"""
import os
import sys

import numpy as np
import Sofa
import Sofa.Core
import Sofa.Simulation
import SofaRuntime

MESH = os.path.join(os.environ["SOFA_ROOT"], "plugins", "SoftRobots", "lib", "python3",
                    "site-packages", "softrobots", "parts", "bunny", "mesh")


def build(root, dt, value_type, value):
    root.dt = dt
    root.gravity = [0, 0, 0]
    # FreeMotionAnimationLoop: najpierw ruch „swobodny” bez ograniczeń, potem solver
    # ograniczeń liczy mnożniki Lagrange'a (tu: ciśnienie w komorze) i koryguje ruch.
    root.addObject("FreeMotionAnimationLoop")
    root.addObject("BlockGaussSeidelConstraintSolver", maxIterations=500, tolerance=1e-9)

    body = root.addChild("bunny")
    # Niejawny Euler: stabilny przy sztywnym FEM; tłumienie Rayleigha tylko po to,
    # żeby szybko dojść do stanu ustalonego.
    body.addObject("EulerImplicitSolver", rayleighStiffness=0.1, rayleighMass=0.1)
    body.addObject("SparseLDLSolver", template="CompressedRowSparseMatrixMat3x3d")
    body.addObject("MeshVTKLoader", name="loader", filename=os.path.join(MESH, "Hollow_Stanford_Bunny.vtu"))
    body.addObject("TetrahedronSetTopologyContainer", src="@loader", name="container")
    body.addObject("MechanicalObject", name="dofs", template="Vec3d")
    body.addObject("UniformMass", totalMass=0.5)
    body.addObject("TetrahedronFEMForceField", method="large", youngModulus=18000, poissonRatio=0.3)
    body.addObject("BoxROI", name="base", box=[-5, -6, -5, 5, -4.5, 5])
    body.addObject("FixedProjectiveConstraint", indices="@base.indices")
    # Korekcja ograniczeń: mówi solverowi ograniczeń, jak węzły zareagują na siłę
    # ograniczenia (używa tej samej faktoryzacji macierzy co SparseLDLSolver).
    body.addObject("LinearSolverConstraintCorrection")

    cavity = body.addChild("cavity")
    cavity.addObject("MeshOBJLoader", name="loader", filename=os.path.join(MESH, "Hollow_Bunny_Body_Cavity.obj"))
    cavity.addObject("MeshTopology", src="@loader")
    cavity.addObject("MechanicalObject", name="dofs", template="Vec3d")
    spc = cavity.addObject("SurfacePressureConstraint", name="spc", valueType=value_type, value=[value])
    # Powierzchnia komory porusza się razem z FEM (interpolacja barycentryczna w tetrach).
    cavity.addObject("BarycentricMapping")
    return spc


def run(dt, value_type, value, t_end, n_log=6, ramp=0.0):
    """ramp > 0: value rośnie liniowo od 0 przez `ramp` sekund (bez skoku aktuacji)."""
    root = Sofa.Core.Node("root")
    spc = build(root, dt, value_type, 0.0 if ramp > 0 else value)
    Sofa.Simulation.init(root)
    v0 = float(spc.initialCavityVolume.value)
    n = int(round(t_end / dt))
    log = []
    for i in range(1, n + 1):
        if ramp > 0:
            spc.value = [value * min(1.0, i * dt / ramp)]
        Sofa.Simulation.animate(root, dt)
        if i % max(1, n // n_log) == 0 or i == n:
            raw = float(np.atleast_1d(spc.pressure.value)[0])
            log.append((i * dt, float(spc.cavityVolume.value) - v0, raw, raw / dt))
    Sofa.Simulation.unload(root)
    return v0, log


def main():
    for p in ("Sofa.Component", "SoftRobots"):
        SofaRuntime.importPlugin(p)

    target = 40.0  # [mm³] – ta sama wartość co w przykładzie PressureVsVolumeGrowthControl
    print(f"Test 1+2: volumeGrowth, stałe value = {target}, dt = 0.001, 1 s, skok w t=0 (celowo: sprawdzamy trzymanie stałej wartości)")
    v0, log = run(0.001, "volumeGrowth", target, 1.0)
    print(f"  objętość początkowa wnęki V0 = {v0:.2f}")
    print(f"  {'t [s]':>6} {'V-V0':>10} {'pressure (surowe)':>18} {'pressure/dt':>12}")
    for t, dv, raw, p in log:
        print(f"  {t:6.3f} {dv:10.3f} {raw:18.6g} {p:12.6g}")
    dvs = [r[1] for r in log]
    total = abs(dvs[-1] - target) < 0.02 * target and abs(dvs[-1] - dvs[len(dvs) // 2]) < 0.02 * target
    print("  -> value = przyrost CAŁKOWITY względem V0" if total else "  -> value NIE zachowuje się jak przyrost całkowity")
    sign_ok = dvs[-1] > 0 and log[-1][3] > 0
    print(f"  -> znak: +value -> V rośnie: {dvs[-1] > 0}, pressure/dt > 0: {log[-1][3] > 0}")

    print("\nTest 3: to samo przy dt = 0.002 (porównanie stanu końcowego)")
    _, log2 = run(0.002, "volumeGrowth", target, 1.0)
    r1, r2 = log[-1], log2[-1]
    print(f"  dt=0.001: surowe = {r1[2]:.6g}, /dt = {r1[3]:.6g}")
    print(f"  dt=0.002: surowe = {r2[2]:.6g}, /dt = {r2[3]:.6g}")
    raw_ratio = r2[2] / r1[2]
    print(f"  stosunek surowych (dt 0.002 / 0.001) = {raw_ratio:.3f} (≈1 -> Pa, ≈2 -> p·dt)")
    in_pa = abs(raw_ratio - 1) < 0.05
    per_dt = abs(raw_ratio - 2) < 0.05

    print("\nTest 4: volumeGrowth 10 -> odczyt p, potem valueType=pressure (oba z rampą 0.3 s)")
    # W v26.06 zadanie value = p w Pa dawało NaN: tryb pressure oczekiwał p·dt,
    # ciśnienie było 1000x za duże i FEM wybuchał. Stąd test na tych samych jednostkach.
    small, dt = 10.0, 0.001
    _, log_s = run(dt, "volumeGrowth", small, 1.0, ramp=0.3)
    raw_small = log_s[-1][2]
    _, log3 = run(dt, "pressure", raw_small, 1.0, ramp=0.3)
    dv3, raw3 = log3[-1][1], log3[-1][2]
    print(f"  volumeGrowth {small}: surowe pressure = {raw_small:.6g}")
    print(f"  valueType=pressure, value = {raw_small:.6g}: V-V0 = {dv3:.3f} (oczekiwane ≈ {small}), "
          f"pole pressure = {raw3:.6g}")
    pressure_mode_ok = bool(np.isfinite(dv3)) and abs(dv3 - small) < 0.02 * small

    print("\nPODSUMOWANIE")
    print(f"  value w volumeGrowth = przyrost całkowity względem V0: {'TAK' if total else 'NIE'}")
    print(f"  znak dodatni (V rośnie, p > 0):                      {'TAK' if sign_ok else 'NIE'}")
    units = "Pa (SOFA master)" if in_pa else ("p·dt (SOFA v26.06)" if per_dt else "NIEJASNE")
    print(f"  jednostki pola pressure:                              {units}")
    print(f"  tryb pressure: value w tych samych jednostkach:       {'TAK' if pressure_mode_ok else 'NIE'}")
    return 0 if (total and sign_ok and (in_pa or per_dt) and pressure_mode_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
