"""Stage 0: measure the semantics of SurfacePressureConstraint (valueType="volumeGrowth").

Usage:  source SOFA/scripts/env.sh && python SOFA/scripts/probe_volume_growth.py

Questions it answers (hydraulics.py depends on them):
  1. Is `value` the TOTAL volume growth relative to the initial volume, or growth
     PER STEP? Test: hold `value` constant for many steps.
     Total -> the measured growth stops; per step -> it grows linearly.
  2. Sign: does a positive `value` enlarge the cavity and give positive pressure?
  3. Units of the `pressure` field: Pa or p·dt? Test: the same steady state at two
     different dt. Raw pressure independent of dt -> Pa; scales with dt -> p·dt.
     History: SOFA v26.06 returned the impulse λ = p·dt (the field description still says
     "divide by dt"). Since SOFA PR #6117 (master branch, v26.12) the constraint solver
     computes forces instead of impulses, so the field is in Pa.
  4. In valueType="pressure" mode, is `value` in the same units as the `pressure`
     field? Test: set as value what we read from the field.

Scene: the hollow "bunny" from the SoftRobots examples (mesh in mm, so here, as an
exception, we do NOT work in SI – units don't matter for answering the questions
above). Gravity is off, so that the chamber is the only load.
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
    # FreeMotionAnimationLoop: first a "free" motion without constraints, then the constraint
    # solver computes the Lagrange multipliers (here: chamber pressure) and corrects the motion.
    root.addObject("FreeMotionAnimationLoop")
    root.addObject("BlockGaussSeidelConstraintSolver", maxIterations=500, tolerance=1e-9)

    body = root.addChild("bunny")
    # Implicit Euler: stable with a stiff FEM; Rayleigh damping only to reach the steady
    # state quickly.
    body.addObject("EulerImplicitSolver", rayleighStiffness=0.1, rayleighMass=0.1)
    body.addObject("SparseLDLSolver", template="CompressedRowSparseMatrixMat3x3d")
    body.addObject("MeshVTKLoader", name="loader", filename=os.path.join(MESH, "Hollow_Stanford_Bunny.vtu"))
    body.addObject("TetrahedronSetTopologyContainer", src="@loader", name="container")
    body.addObject("MechanicalObject", name="dofs", template="Vec3d")
    body.addObject("UniformMass", totalMass=0.5)
    body.addObject("TetrahedronFEMForceField", method="large", youngModulus=18000, poissonRatio=0.3)
    body.addObject("BoxROI", name="base", box=[-5, -6, -5, 5, -4.5, 5])
    body.addObject("FixedProjectiveConstraint", indices="@base.indices")
    # Constraint correction: tells the constraint solver how the nodes respond to the
    # constraint force (uses the same matrix factorization as SparseLDLSolver).
    body.addObject("LinearSolverConstraintCorrection")

    cavity = body.addChild("cavity")
    cavity.addObject("MeshOBJLoader", name="loader", filename=os.path.join(MESH, "Hollow_Bunny_Body_Cavity.obj"))
    cavity.addObject("MeshTopology", src="@loader")
    cavity.addObject("MechanicalObject", name="dofs", template="Vec3d")
    spc = cavity.addObject("SurfacePressureConstraint", name="spc", valueType=value_type, value=[value])
    # The chamber surface moves with the FEM (barycentric interpolation in the tetras).
    cavity.addObject("BarycentricMapping")
    return spc


def run(dt, value_type, value, t_end, n_log=6, ramp=0.0):
    """ramp > 0: value rises linearly from 0 over `ramp` seconds (no actuation step)."""
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

    target = 40.0  # [mm³] – same value as in the PressureVsVolumeGrowthControl example
    print(f"Test 1+2: volumeGrowth, constant value = {target}, dt = 0.001, 1 s, step at t=0 (on purpose: we check holding a constant value)")
    v0, log = run(0.001, "volumeGrowth", target, 1.0)
    print(f"  initial cavity volume V0 = {v0:.2f}")
    print(f"  {'t [s]':>6} {'V-V0':>10} {'pressure (raw)':>18} {'pressure/dt':>12}")
    for t, dv, raw, p in log:
        print(f"  {t:6.3f} {dv:10.3f} {raw:18.6g} {p:12.6g}")
    dvs = [r[1] for r in log]
    total = abs(dvs[-1] - target) < 0.02 * target and abs(dvs[-1] - dvs[len(dvs) // 2]) < 0.02 * target
    print("  -> value = TOTAL growth relative to V0" if total else "  -> value does NOT behave like total growth")
    sign_ok = dvs[-1] > 0 and log[-1][3] > 0
    print(f"  -> sign: +value -> V grows: {dvs[-1] > 0}, pressure/dt > 0: {log[-1][3] > 0}")

    print("\nTest 3: the same at dt = 0.002 (comparison of the final state)")
    _, log2 = run(0.002, "volumeGrowth", target, 1.0)
    r1, r2 = log[-1], log2[-1]
    print(f"  dt=0.001: raw = {r1[2]:.6g}, /dt = {r1[3]:.6g}")
    print(f"  dt=0.002: raw = {r2[2]:.6g}, /dt = {r2[3]:.6g}")
    raw_ratio = r2[2] / r1[2]
    print(f"  raw ratio (dt 0.002 / 0.001) = {raw_ratio:.3f} (≈1 -> Pa, ≈2 -> p·dt)")
    in_pa = abs(raw_ratio - 1) < 0.05
    per_dt = abs(raw_ratio - 2) < 0.05

    print("\nTest 4: volumeGrowth 10 -> read p, then valueType=pressure (both with a 0.3 s ramp)")
    # In v26.06 setting value = p in Pa gave NaN: pressure mode expected p·dt, the
    # pressure was 1000x too large and the FEM blew up. Hence the same-units test.
    small, dt = 10.0, 0.001
    _, log_s = run(dt, "volumeGrowth", small, 1.0, ramp=0.3)
    raw_small = log_s[-1][2]
    _, log3 = run(dt, "pressure", raw_small, 1.0, ramp=0.3)
    dv3, raw3 = log3[-1][1], log3[-1][2]
    print(f"  volumeGrowth {small}: raw pressure = {raw_small:.6g}")
    print(f"  valueType=pressure, value = {raw_small:.6g}: V-V0 = {dv3:.3f} (expected ≈ {small}), "
          f"pressure field = {raw3:.6g}")
    pressure_mode_ok = bool(np.isfinite(dv3)) and abs(dv3 - small) < 0.02 * small

    print("\nSUMMARY")
    print(f"  value in volumeGrowth = total growth relative to V0:  {'YES' if total else 'NO'}")
    print(f"  positive sign (V grows, p > 0):                       {'YES' if sign_ok else 'NO'}")
    units = "Pa (SOFA master)" if in_pa else ("p·dt (SOFA v26.06)" if per_dt else "UNCLEAR")
    print(f"  pressure field units:                                 {units}")
    print(f"  pressure mode: value in the same units:               {'YES' if pressure_mode_ok else 'NO'}")
    return 0 if (total and sign_ok and (in_pa or per_dt) and pressure_mode_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
