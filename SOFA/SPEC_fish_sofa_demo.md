# SPEC: SOFA + SoftRobots demo – soft hydraulic tail of a robot fish

> Instructions for Claude Code. This file lives in the `SOFA/` folder of the `fish-sim-v0` repository (next to `MuJoCo/`). Type:
> "Read SOFA/SPEC_fish_sofa_demo.md and implement it in stages. After each stage run the tests and show the results."
> Start in plan mode.

## 0. Goal and context

Build a **simplified, educational** simulation of a robot fish's soft tail in SOFA with the SoftRobots plugin. It should show what MuJoCo cannot do:
- continuous deformation of silicone (FEM on a tetrahedral mesh),
- two internal hydraulic chambers driven by `SurfacePressureConstraint`,
- the pressure–volume–deflection relationship (a curve that can later be measured on the real tail),
- the effect of water on tail motion (a simplified, custom drag model, because SOFA has no hydrodynamics).

Optional (stage 7): a bridge to the MuJoCo model, i.e. export of equivalent joint stiffnesses (pseudo-rigid-body model, PRBM) to the parameters in `MuJoCo/fishsim/config.py`. That is why the tail geometry matches the tail from the MuJoCo demo (section 4).

This is a **capability demo, not a calibrated model**. All physical parameters are placeholders and must be marked as such.

The user is a young mechatronics engineer who is learning. **Code comments in English**, explaining the physics and the role of each SOFA component (solver, mapping, constraint), not just the syntax.

Scope: only the **tail**, attached to a fixed body. Ballast and swimming of the whole vehicle are not here; the demo in `MuJoCo/` shows them.

## 1. Working rules (important)

1. Work in stages (section 8). After each stage run the scene and the tests, show the result, and only then move on.
2. **The SOFA API changes between versions** (component names, e.g. constraint solvers, required `RequiredPlugin`, initialization functions in SofaPython3). In stage 0 determine the installed SOFA version and always check names in the documentation / examples shipped with that version (`plugins/SoftRobots/examples`, `examples/` in SOFA). Do not copy code from old SofaPython2 tutorials (`createObject`, `createChild`). SofaPython3 has `addObject`, `addChild`.
3. Use **SofaPython3** (`.py` scenes with a `createScene(rootNode)` function), not XML `.scn`.
4. Consistent units: **SI (m, kg, s, Pa)**. State this at the top of `config.py`. Note: many SoftRobots examples use mm (and solver tolerances tuned for mm). Do not mix them, and rescale the tolerances (section 5).
5. Do not invent "realistic" values and do not present them as measured. Every parameter: comment `# PLACEHOLDER – to be identified from measurements`.
6. If the simulation "explodes" or behaves unphysically, **do not mask it** with random tuning. Diagnose it (time step, jump in actuation value, stability of the explicit drag force, mesh quality, Poisson's ratio, constraint solver convergence) and describe it in the README.

## 2. Installation (verify, do not assume) – this is stage 0

Target environment: Fedora (Linux), the system Python is newer than SOFA requires, anaconda is available.

- The latest official SOFA binaries require a specific Python version (3.12 in recent releases) + numpy + scipy (+ pybind11) for SofaPython3. Check the release page (github.com/sofa-framework/sofa/releases). Create an environment with **exactly** that version: `conda create -n fishsofa python=3.12`. Do not use the system Python.
- The binaries are built on Ubuntu. Check whether `runSofa` starts on Fedora (missing libraries: `ldd`). Note in the README what had to be installed additionally.
- **Check whether SoftRobots is in the official binaries of this version.** If not, the options are: building the plugin with SOFA, or DefrostSofaBundle (note: this bundle is licensed for academic use only and may be older). Note in the README which route you chose and what the license is.
- **Running without GUI (pytest, scripts):** `import Sofa` in plain Python requires environment variables (`SOFA_ROOT`, `PYTHONPATH` pointing to the SofaPython3 `site-packages` in the SOFA directory, possibly `LD_LIBRARY_PATH`). Put them in `scripts/env.sh`; run every script and `pytest` after `source scripts/env.sh`.
- For mesh generation: `pip install gmsh meshio` (in the same conda environment).
- Write `scripts/check_sofa.py`, which prints: the SOFA version, whether SoftRobots and SofaPython3 load, and the **actual names** of the components used in section 5 (constraint solver, constraint correction, `FixedProjectiveConstraint` or equivalent, `SurfacePressureConstraint` and the names of its fields: `value`, `valueType`, `pressure`, `cavityVolume`, pressure drawing options).
- Run a SoftRobots example with a pressure chamber (e.g. "Springy"/"PressureVsVolumeGrowthControl" from the `SurfacePressureConstraint` examples folder) **before** writing your own scene. Using this example, determine and record in the README:
  - whether `value` with `valueType="volumeGrowth"` is the **total** growth relative to the initial volume, or the growth **per step** (all of `hydraulics.py` depends on this),
  - the sign: whether a positive `value` gives a positive `pressure` and an increasing `cavityVolume`, and what orientation of the chamber triangles is required.

**Done when:** `check_sofa.py` passes, the chamber example runs headless, the results of both findings are in the README.

## 3. Project structure

```
SOFA/
  SPEC_fish_sofa_demo.md
  README.md
  requirements.txt            # gmsh, meshio, numpy, scipy, matplotlib, pytest (SOFA separately)
  fishsofa/
    config.py                 # ALL parameters (geometry, mesh, material, numerics, water, hydraulics)
    mesh_gen.py               # gmsh: half of the tail with a chamber -> mirror -> tetra + surfaces
    scene.py                  # createScene(root): FEM tail + chambers + fixture + controllers
    hydraulics.py             # pump as a volume source, closed L<->R circuit, relief valve
    water.py                  # water drag forces on the outer surface triangles (pure numpy, testable without SOFA)
    geometry.py               # tip angle, chord, helper measurements (shared by tests and plots)
    controllers.py            # Sofa.Core.Controller: rhythm, logging, force application
    headless.py               # running the scene from Python without GUI (N steps, returns logs)
  scripts/
    env.sh                    # SOFA_ROOT, PYTHONPATH etc. (section 2)
    check_sofa.py             # stage 0
    run_gui.sh                # runSofa with the right plugins
    run_scenarios.py
    export_prbm.py            # stage 7 (optional) -> results/prbm.json
  meshes/                     # generated meshes (do not commit, reproducible from mesh_gen.py)
  tests/test_sanity.py
  results/
```

## 4. Geometry and mesh (mesh_gen.py)

**Axes** (same as in MuJoCo): X along the fish, the tail extends from the body in the **−X** direction; Y sideways (the tail bends about this axis); Z vertical (gravity in −Z). Origin: center of the front (attached) wall of the tail.

**Dimensions** = the tail from `MuJoCo/fishsim/config.py`. Copy the numbers into `config.py` with a comment on where they come from (all PLACEHOLDER):
- tail body length `n_segments · segment_length` = 5 × 0.04 = 0.20 m,
- cross-section at the root: thickness (Y) 2·`segment_ry0` = 0.06 m, height (Z) 2·`segment_rz0` = 0.08 m, linear taper to `taper_last` = 0.4 at the end,
- caudal fin at the end: dimensions from `fin_semi_axes` (length 0.07 m, thickness 0.006 m, height 0.12 m), thin in Y, tall in Z.

**Chambers** (left +Y and right −Y, symmetric about the XZ plane), separated by a central septum. New parameters in `config.py` (PLACEHOLDER):
- chamber length = length of the `n_actuated` actuated segments from MuJoCo (3 × 0.04 = 0.12 m), starting at `chamber_x_start` (a small distance from the attached wall),
- `wall_thickness` (outer wall), `septum_thickness` (septum), `chamber_end_wall` (end walls).
- The chambers are closed (no supply channels); fluid inflow is modeled only by `volumeGrowth`.
- Optional: a stiffer "spine" layer in the septum as a separate material (if easy; if not, skip it and note it).

**Mesh:**
- Generate **half** of the tail (y ≥ 0) with one chamber and mirror it about XZ. Then the mesh is exactly symmetric and the symmetry test checks the code, not a coincidence of meshing.
- Linear tetrahedra are too stiff in bending of a thin layer (shear locking) if there are 1–2 elements across the thickness. Require **≥ 3 elements across the thickness** of the chamber walls, the septum and the fin: local refinement in gmsh (size fields), coarser elements inside the solid.
- Size: a realistic target is ≤ ~20k tetrahedra. Record in the report the element count and the elements across the thickness of each wall. Add a coarser test mesh (`mesh_size_test` in the config) so that `pytest` is fast.
- **Decision from stage 1:** ≥ 3 elements per 4 mm wall and ≤ 20k elements cannot both be met (0.2 m tail: 4 mm → ~28k, 2 mm → ~140k, 1.3 mm → ~450k tets). Instead, a **convergence study**: levels `coarse` / `medium` / `fine` (4/3/2 mm at the surfaces) and `test` (6 mm, pytest only). Stage 2 (p–V statics) is computed on all three to measure how much the coarse mesh overestimates stiffness. Dynamic stages on the coarsest, with the error stated.
- **Determined in stage 1:** `MeshVTKLoader` (SOFA v26.06) cannot read VTK 5.1 from meshio (segfault), so the mesh is written as legacy VTK 4.2. `StaticSolver` requires a separate `NewtonRaphsonSolver` (since v25.12) and does not work with `FreeMotionAnimationLoop`.
- The chamber cavities are **not** meshed (hollow inside the solid).
- Export:
  - tetra volume mesh (a format the SOFA loader of this version can read: `MeshGmshLoader` or `MeshVTKLoader`; if the `.msh` format version causes problems, export VTK via meshio),
  - triangle surfaces of chambers L and R (STL/OBJ) for `SurfacePressureConstraint`, built from **the same nodes** as the tetra mesh, with the orientation determined in stage 0,
  - outer surface = boundary triangles of the tetra mesh (same nodes), normals pointing **outward** (for water forces and visualization).
- Quality report (`results/s1_mesh_report.txt`): no tetrahedra with volume ≤ 0, quality distribution (e.g. radius ratio), element count, elements across wall thickness, consistency of normal orientation.

## 5. SOFA scene (scene.py)

- Animation loop with constraints (`FreeMotionAnimationLoop` + the appropriate constraint solver for this SOFA version), because `SurfacePressureConstraint` is a Lagrange constraint. **Constraint solver tolerance in SI:** volumes are of order 1e-6 m³, so the tolerances from mm examples are wrong by orders of magnitude. Choose the tolerance relative to scale (e.g. 1e-3 × typical ΔV) and log the iteration count and the achieved error at every step.
- Integrator `EulerImplicitSolver` + a direct linear solver (e.g. `SparseLDLSolver`) + the appropriate constraint correction.
- **Time step** `dt` in the config. Starting point: `dt ≤ 1/(50·f_max)` ≈ 6 ms for f_max = 3 Hz, adjusted by the water drag stability condition (section 7). Report the ratio of simulation time to real time (without promising "real time").
- **Material damping:** `rayleighStiffness` and `rayleighMass` in `EulerImplicitSolver` as PLACEHOLDER in the config. Explain in a comment that implicit Euler also adds numerical damping (growing with `dt`), so the amplitude in air (stage 4) depends on `dt`. Check this once: amplitude at `dt` and `dt/2`, result in the README.
- Material: `TetrahedronFEMForceField` with `method="large"` (corotational, large rotations), silicone Young's modulus as a placeholder (order 1e5–1e6 Pa), Poisson **0.45, not 0.5** (at 0.5 linear tets lock, so-called volumetric locking; explain this in a comment). Optionally a hyperelastic variant as an extension, not required.
- Mass: `MeshMatrixMass` / `UniformMass` with the silicone density `rho_tail` from MuJoCo (1100 kg/m³, placeholder). **Plus the mass of the water in the chambers** (ρ_water · chamber volume, distributed over the chamber wall nodes): a tail with filled chambers is heavier than the silicone alone.
- **Environment**: a single switch `environment = "air" | "water"` in the config, sets gravity and drag together:
  - `"air"`: full gravity on silicone + water in the chambers, no water drag,
  - `"water"`: effective silicone gravity `g·(1 − ρ_water/ρ_silicone)`, water in the chambers neutral (buoyancy = weight), water drag enabled (section 7).
- Fixture: nodes of the front wall of the tail (x = 0) fixed (`FixedProjectiveConstraint` or the equivalent in the given version). This corresponds to a tail bolted to the body and at the same time to a **tethered thrust measurement rig**.
- Chambers: two child nodes, each with `MeshTopology` + `MechanicalObject` + `SurfacePressureConstraint` + `BarycentricMapping` to the FEM mesh (with shared nodes the mapping is exact).

**Measurement definitions** (`geometry.py`, used the same way everywhere):
- **tip angle** θ_tip = atan2(Δy, −Δx) of the chord from the center of the front wall to the center of the fin (centroid of the fin nodes); θ_tip > 0 = tail bent toward +Y (to the left),
- sign consistent with MuJoCo: a positive `V_bias` must bend the tail to the same side as in `MuJoCo/fishsim` (there +V_bias = turn to the right). Record in the README which chamber corresponds to +V_bias,
- **thrust**: cycle average of the +X component of the resultant water force on the tail (the force acts on the water in −X, the reaction pushes the fish in +X).

## 6. Hydraulics (hydraulics.py)

Water is practically incompressible, so **the pump imposes volume, not pressure**. That is why we use `SurfacePressureConstraint` with `valueType="volumeGrowth"`. SOFA itself computes the pressure needed to reach the given volume (the `pressure` field, read-only). This is physically more correct for hydraulics than pressure control; describe it in a comment.

**Determined in stage 0 (SOFA v26.06, README):** `value` is the **total** growth relative to `initialCavityVolume`. The `pressure` field is **p·dt** (an impulse from the constraint solver), so pressure = `pressure / dt`. In `valueType="pressure"` mode the `value` input is also given as p·dt. Every pressure in the code, logs and plots is in Pa, and the conversion is done in one place (a function in `hydraulics.py`).

- **Rhythm as in MuJoCo:** we prescribe the pumped volume `V_ref(t) = V_bias + A_V·r(t)·sin(2πft)` (ramp `r(t)` over `ramp_time`), not a sine of the pump command. Command: `u = sat((dV_ref/dt + K_v·(V_ref − V_p)) / Q_max, −1, 1)`, where `V_p = ∫Q dt`. Parameter names and values as in `MuJoCo/fishsim/config.py` (`tail_freq`, `tail_volume_amp`, `tail_volume_bias`, `K_v`, `ramp_time`, `Q_max`, `tau_pump`). Rationale in a comment: a sine in `u` would give a volume amplitude ∝ 1/f, so the frequency sweep would mix two effects.
- Pump as a first-order element: `dQ/dt = (u·Q_max − Q)/τ_pump`.
- Closed circuit: `ΔV_L = V_prefill + V_p`, `ΔV_R = V_prefill − V_p`.
- **Prefill:** both chambers start with `V_prefill > 0` (ramp in the first second), so that neither is "sucked" below its rest volume. Contact between chamber walls is not modeled, so `config.py` checks with an assertion: `V_prefill > |V_bias| + A_V + margin`.
- **Relief valve on the pressure difference:** a pump in a closed circuit works against `Δp = p_L − p_R`, not against the pressure of one chamber. When `|Δp| > p_max` (name as in MuJoCo), the valve passes fluid from the higher-pressure chamber to the other (total volume unchanged), just like in `MuJoCo/fishsim/hydraulics.py`. You read the pressure after the step is solved, so the valve acts with a 1-step delay. Describe this in a comment. Log when the valve was active.
- **Never jump the actuation value.** Always use ramps or continuous signals, because jumps are a known cause of explosions in pressure simulations.

## 7. Water (water.py) – a simplification, honestly described

SOFA has no fluid model. Implement in a controller (`onAnimateBeginEvent`) a simple **local drag model** on each triangle of the outer surface. The computations in `water.py` as pure numpy functions (input: positions, velocities, triangles; output: nodal forces), so they can be tested without SOFA:

- triangle velocity `v` (mean of the nodes), outward normal `n`, area `A`,
- normal force: `F_n = −½ ρ C_n A (v·n)|v·n| n`,
- tangential force (small): `F_t = −½ ρ C_t A |v_t| v_t`,
- split the force equally over the 3 nodes of the triangle, apply through `ConstantForceField` (the `forces` field updated every step) directly on the FEM nodes (the outer surface has the same nodes, no mapping needed).
- With `environment="water"` gravity is effective (section 5). Describe this.
- Optional (extension): added mass as an increase of the surface node masses.

**Stability (mandatory):** a force computed from the previous step's velocity is explicit damping. For a node with mass `m` and coefficient `c = ρ·C_n·A_node·|v_n|` the explicit step is stable only when `c·dt/m` is clearly < 1. The thin fin has light nodes and a large area, so this is where it will blow up first. Log `max(c·dt/m)` at every step. If it exceeds ~0.5: reduce `dt` and describe it in the README, do not clip the forces. Extension (not required): drag as a Python `Sofa.Core.ForceField` with a damping term in the system matrix (implicit).

**Limitation to state in the README:** this model has drag only. It neglects added mass (unless you add the extension), lift and vortices, and it is exactly the reactive effects that dominate fish thrust (Lighthill's theory). The thrust number from this demo is therefore **qualitative**, not quantitative.

## 8. Implementation stages

Each stage ends with: tests green + plot(s) from section 9 + 2–3 sentences of observations in the README.

0. **Installation and API** (section 2). **Done when:** `check_sofa.py` passes, findings about `volumeGrowth` in the README.
1. **Mesh**: generation, quality report, preview in the SOFA GUI (material only, no actuation, `environment="air"`, the tail sags under gravity in −Z). **Done when:** report without errors, ≥ 3 elements across wall thickness, 100 steps without NaN.
2. **Single chamber, quasi-static**: `volumeGrowth` ramp in chamber L from 0 to `dV_max` (no prefill), `environment="air"`, gravity off (`g = 0`), so that the curve depends only on material and geometry. Chamber R **vented**: no volume constraint (pressure 0), as on a measurement rig with the second port open. Quasi-static = slow ramp (`ramp_static_time`, e.g. 5 s) and the criterion: kinetic energy < 1% of strain energy at every measurement point; alternatively `StaticSolver`, if it works with constraints in this version. Plots: pressure vs volume, tip angle vs volume. This is the most important result of the demo: you will measure the same curve on the real tail.
   - **Determined in stage 2:** pseudo-statics (implicit Euler, dt = 50 ms, LDL) gives the same state as a slow ramp at dt = 2 ms, 5–25× cheaper. The "warp" solver with a chamber shifts the equilibrium (−25% pressure at 30 ml), so with chambers only LDL. The design from stage 1 barely bends (the chamber bulges); a sweep of variants chose V4 = spine in the septum (E×20) + hoop fibers (README, stage 2a).
   - **Determined after stage 2 (performance):** the default linear solver is CHOLMOD (`EigenCholmodSupernodalLLT`, SofaCHOLMOD plugin from master built for v26.06): as accurate as LDL, also with chambers, 4.3× (coarse) to 15× (fine) faster. We stay on SOFA v26.06, because SOFA master (v26.12-dev) gives a wrong, oscillating equilibrium for a chamber with stiff fibers (README, "Performance: CHOLMOD").
3. **Symmetry**: the same for chamber R. The results must be mirrored (test).
   - **Determined in stage 3:** symmetry error ≤ 0.75% (angle, coarse, at 5 ml), ≤ 0.023% (pressure); the residual comes from the end-of-hold criterion for a point, not from the mesh (README, stage 3).
4. **Antagonistic hydraulics**: rhythm `V_ref(t)` from section 6, closed circuit L↔R, prefill, `environment="air"`. Plot: tip angle, p_L, p_R, Δp, valve activity. **Done when:** a steady cycle after the run-up, the sum of measured chamber volumes constant (test), check of the effect of `dt` (section 5).
   - **Determined in stage 4:** SOFA chamber (91 ml) ≠ MuJoCo (30 ml), so A_V = 17 ml, V_prefill = 20 ml, Q_max = 250 ml/s (decision: visible motion). Prefill > ~22 ml buckles the spine (common pressure). The pump command has an added lag compensation τ_pump·d²V_ref/dt² (without it 16% overshoot at 2 Hz). Result: ±12.7° at dt 2 ms, −5% relative to dt 1 ms (README, stage 4).
5. **Water**: the same with `environment="water"`. Comparison of amplitude and phase shift with water vs without. Thrust (definition in section 5) = qualitative "tethered thrust". **Done when:** `max(c·dt/m)` < 0.5 throughout the run.
   - **Determined in stage 5:** explicit drag requires dt = 0.5 ms (max(c·dt/m) = 0.27; at 1 ms 0.54 on the fin, the result differs by 1.4% in amplitude and 5% in thrust). In water the amplitude is 0.55× that in air (±7.3°), phase +30°, thrust +67 mN (qualitative), Δp almost unchanged (README, stage 5).
6. **Sweeps** (protocol: each point = a separate simulation, 2 run-up cycles + 3 averaging cycles; give the computation time of the whole sweep):
   - frequency 0.5–3 Hz (the same points as `MuJoCo/scripts/sweep_frequency.py`) → tip amplitude, mean thrust, max |Δp|, valve active time. Compare the shape with `MuJoCo/results/s5_sweep.png`.
   - Young's modulus ×0.5, ×1, ×2, in two variants:
     a) quasi-static (as in stage 2): the same ΔV → pressure scales ~linearly with E, and **deflection barely changes**,
     b) dynamic in water at 2 Hz: here E changes amplitude and phase, because it shifts the tail's resonance relative to the flapping frequency.
   Lesson for the README: under volume control a homogeneous linear material without external loads deflects the same at any E; stiffness determines the **required pressure** (pump, valve, sealing), and affects motion only through loads (water, inertia, gravity). For contrast, one point in `valueType="pressure"` mode: the same p → deflection ~1/E.
   - **Determined in stage 6:** in water there is no resonance (amplitude decreases with f), thrust has a maximum at ~2.25 Hz, above that the pump saturates (Q_max), the valve does not open. The scaling law with E is confirmed (README, stage 6). The sweep is computed in parallel (`fishsofa/parallel.py`): 68 min instead of ~7 h.
7. **(Optional) PRBM export** (`export_prbm.py`) → `results/prbm.json`, keys corresponding to the fields of `MuJoCo/fishsim/config.py`:
   - `joint_x` [m] – positions of the N = 5 joints (every `segment_length`),
   - `stiffness` [N·m/rad] – stiffness of each joint. Determine it from **separate load cases** (chambers not actuated, a small lateral force on the fin via `ConstantForceField`): moment in the joint cross-section / relative angle of adjacent segments. Pressure actuation alone is not enough, because it does not separate the stiffnesses of the individual joints,
   - `A_eff_r_eff` [m³] – moment on the actuated joints per unit Δp (from stages 2–3),
   - `C_h` [m³/Pa] – chamber compliance dV/dp with the tail locked, `V0_chamber` [m³],
   - `tendon_weights` – relative contribution of the actuated joints to the deflection from pressure.
   Describe the method and approximations (linearity, small angle, rigid segments). Note: MuJoCo currently takes a single `stiffness_actuated` and computes passive stiffnesses from `passive_resonance_hz`, so loading `prbm.json` on the MuJoCo side is separate, future work (list it in the README, do not implement it here).

## 9. Results (results/)

PNG + CSV: `s1_mesh_report.txt`, `s2_pv_curve.png`, `s2_tip_angle.png`, `s3_symmetry.png`, `s4_air_flapping.png`, `s5_water_vs_air.png`, `s6_freq_sweep.png`, `s6_young_sweep.png` (both variants a/b), optionally `prbm.json`. A GUI screenshot with the bent tail (if it can be done automatically; if not, instructions in the README on how to take it manually).

## 10. Tests (tests/test_sanity.py, run headless)

The tests use the coarse test mesh (`mesh_size_test`). Budget: the whole `pytest` < ~3 min. Run: `source scripts/env.sh && pytest -q`.

- Mesh: no tetrahedra with volume ≤ 0; outer surface normals point outward; mirrored mesh (nodes pairwise symmetric about XZ).
- The scene initializes and runs 100 steps without NaN and without "explosion" (max node displacement < tail length); the constraint solver converges at every step.
- Actuation sign: +ΔV in L → `pressure` > 0, `cavityVolume` increases, θ_tip has the sign consistent with the definition in section 5.
- Symmetry: θ_tip for L(+ΔV) ≈ −θ_tip for R(+ΔV), error < 5%.
- Monotonicity: on 0…`dV_max` larger ΔV → larger deflection and larger pressure.
- Hydraulics (unit, without SOFA): `V_p` tracks `V_ref`, the valve does not change the total volume, the prefill assertion catches a too small `V_prefill`.
- Hydraulics (in the scene): measured `cavityVolume_L + cavityVolume_R` constant within the solver tolerance.
- Water (unit, `water.py` on synthetic velocities): drag power F·v ≤ 0 on every triangle; zero velocity → zero force.
- Water (in the scene): amplitude with water < amplitude without water for the same command; `max(c·dt/m)` < 0.5.
- Young's modulus ×2 at the same ΔV (quasi-static, g = 0): pressure ×2 (±10%), deflection changes < 5%.
- Young's modulus ×2 at the same pressure (`valueType="pressure"`, `value = p·dt`): deflection ~×0.5 (±15%).
- Pressure units: the same steady state at `dt` and `2·dt` gives the same pressure in Pa (guards the division by `dt`).

## 11. README – mandatory sections

- How to install (exact SOFA version, Python version, where SoftRobots comes from, license, what had to be installed additionally on Fedora, `scripts/env.sh`).
- How to run the GUI and the headless scenarios.
- Findings from stage 0 (semantics and sign of `volumeGrowth`).
- What each plot shows, in 2–3 sentences for a learner.
- Lesson from stage 6: volume vs pressure control and the role of Young's modulus.
- Numerics: chosen `dt` and why (drag stability, numerical damping), ratio of simulation time to real time.
- **Model limitations**: no CFD and no reactive effects (unless added mass was added), explicit water drag (time step limit), tail attached (no free swimming), linear corotational material instead of hyperelastic, unidentified parameters, no contact between chamber walls, chambers without supply channels.
- How to calibrate: measure the p–V curve and the deflection angle on the real tail (stage 2, second port open), fit Young's modulus, measure thrust on a scale in a tub and compare with stage 5.

## 12. Definition of done

- `source scripts/env.sh && pytest -q` (headless) → all tests green.
- `python scripts/run_scenarios.py` → plots in `results/`.
- `scripts/run_gui.sh` → the tail is visibly flapping in the SOFA GUI, with pressure visualization in the chambers (if this SoftRobots version has it; check in stage 0, otherwise color the chambers by pressure from the controller).
- The README makes it possible to understand the results and limitations without reading the code.
