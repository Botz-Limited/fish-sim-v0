# fish-sim-v0 / SOFA – soft hydraulic tail (SOFA + SoftRobots)

Educational FEM demo of a robot-fish tail. Specification: [SPEC_fish_sofa_demo.md](SPEC_fish_sofa_demo.md). **This is not a calibrated model** – all parameters are placeholders.

Status: **stages 0 (installation, API), 1 (mesh, sag under own weight), 2 (chamber L quasi-static), 3 (L/R symmetry), 4 (flapping in air), 5 (water) and 6 (sweeps) complete; CHOLMOD solver (4–15× faster) added after stage 2, OpenBLAS from conda and parallel sweeps after stage 4.** Stage 7 (optional PRBM export to MuJoCo) deliberately skipped (decision 6.10.2026); method description: spec, section 8.

## Installation (Linux x86_64, tested on Fedora 44 and EndeavourOS/Arch)

**On a new machine one command is enough** (prerequisite: conda, e.g. [Miniforge](https://github.com/conda-forge/miniforge)):

```bash
git clone <repo> && cd fish-sim-v0
SOFA/scripts/setup.sh --install-deps     # ~2 min + 230 MB download; missing packages via sudo dnf/apt
source SOFA/scripts/env.sh               # in every new shell (bash or zsh)
SOFA/scripts/run_gui.sh                  # GUI: tail flaps (Animate)
```

`setup.sh` skips steps already done. In order:
1. Checks system dependencies: compiler, cmake, ninja, SuiteSparse/CHOLMOD, Eigen and the OpenGL/X11 libraries for gmsh and the GUI. Without `--install-deps` it only prints the `dnf` or `apt` command.
2. Downloads the SOFA v26.06.00 binary to `~/sofa` and verifies its SHA-256 checksum.
3. Creates the conda environment `fishsofa` from `environment.yml`.
4. Builds the CHOLMOD plugin.
5. Runs `check_sofa.py` and `pytest`.

Directory other than `~/sofa`: `FISHSOFA_HOME=/path` for `setup.sh` **and** `env.sh`. Clean-install test (5.10.2026, separate directory and separate conda environment): 1 min 43 s, 33/33 tests. EndeavourOS (6.10.2026, from scratch, with Miniforge): 1 min 58 s, 33/33.

| What | Version / source |
|---|---|
| SOFA | **v26.06.00**, official binary `SOFA_v26.06.00_Linux_Python3.12.zip` from [github.com/sofa-framework/sofa/releases](https://github.com/sofa-framework/sofa/releases), SHA-256 in `setup.sh` |
| SoftRobots, SoftRobots.Inverse, STLIB, SofaPython3 | **in the official binary** (no need to compile or use DefrostSofaBundle) |
| SofaCHOLMOD | sources in the repo: `third_party/SofaCHOLMOD`, from SOFA master, commit `6c3e21f`; described in `VENDORED.md`. Built for v26.06 by `scripts/build_cholmod_plugin.sh` (solver `"cholmod"`, default) |
| Licenses | SOFA and SofaCHOLMOD: LGPL 2.1+ (`LICENSE-LGPL.md`); SoftRobots: **LGPL v3** (`plugins/SoftRobots/LICENSE`) |
| Python | **3.12** in the conda environment `fishsofa`; packages pinned in `requirements.txt` (system Python 3.14 does not match the binary) |
| Meshes | generated on first use into `SOFA/meshes/` (gmsh, deterministic; not in the repo) |

**Why this way:**
- The SOFA binary is built on Ubuntu. On Fedora `ldd` showed only one missing library: `libpython3.12.so.1.0`, which we take from conda.
  - `env.sh` creates the directory `~/sofa/fishsofa-pylib/` with a single symlink to that library and adds it to `LD_LIBRARY_PATH`.
  - We deliberately do not add the whole `$CONDA_PREFIX/lib`, because then conda's `libstdc++` would shadow the system one, which risks OpenGL driver errors in the GUI.
- System packages are needed only for the CHOLMOD plugin (compiler and headers, including Boost: the SOFA binary's CMake configs require it, and the binary does not include it) and for the graphics libraries used by gmsh from pip.

## Running

```bash
source SOFA/scripts/env.sh
python SOFA/scripts/check_sofa.py           # stage 0: component and field names in this SOFA version
python SOFA/scripts/probe_volume_growth.py  # stage 0: how SurfacePressureConstraint works (~2.5 min)
cd SOFA && pytest -q                        # tests (~3 min, coarse "test" mesh in a temporary directory)
python -m fishsofa.mesh_gen --level all     # stage 1: meshes into meshes/ (fine ~10 s)
python scripts/run_stage1.py                # stage 1: report + plot into results/ (~10 min, mostly fine)
python scripts/run_stage2_variants.py       # stage 2a: construction variants (~10 min)
python scripts/run_stage2.py                # stage 2: p–V curve and angle, 3 meshes (~25 min)
python scripts/run_stage3.py                # stage 3: L/R symmetry (~3 min)
python scripts/run_stage4.py                # stage 4: flapping in air (~25 min)
python scripts/run_stage5.py                # stage 5: water vs air (3 simulations at once, ~30 min)
python scripts/run_stage6.py                # stage 6: f and E sweeps (19 simulations, ~1 h on 12 threads)
python scripts/run_stage1.py --plot-only    # any run_stage*.py: redraw the plots from results/*.csv only
FISHSOFA_ENV=water scripts/run_gui.sh       # GUI: tail flaps in water
scripts/run_gui.sh coarse                   # tail in GUI; after Animate it sags under its own weight
# GUI with a SoftRobots example (pressure vs volume chamber):
$SOFA_ROOT/bin/runSofa -l SofaPython3 $SOFA_ROOT/plugins/SoftRobots/share/sofa/examples/SoftRobots/component/constraint/SurfacePressureConstraint/PressureVsVolumeGrowthControl.py
# the same without a window (e.g. 50 steps):
$SOFA_ROOT/bin/runSofa -g batch -n 50 -l SofaPython3 <scene.py>
```

## Findings from stage 0

### Component names in SOFA v26.06 (`check_sofa.py`)

| Role | We use | Notes |
|---|---|---|
| constraint solver | `BlockGaussSeidelConstraintSolver` | `GenericConstraintSolver` **no longer exists**; there is also `NNCGConstraintSolver` |
| fixing | `FixedProjectiveConstraint` | `FixedConstraint` still works (old name) |
| constraint correction | `LinearSolverConstraintCorrection` | there is also `GenericConstraintCorrection` |
| linear solver | `SparseLDLSolver`, `template="CompressedRowSparseMatrixMat3x3d"` | 3×3 blocks are faster for 3D nodes (SOFA suggestion) |
| others | `FreeMotionAnimationLoop`, `EulerImplicitSolver`, `StaticSolver`, `TetrahedronFEMForceField`, `MeshMatrixMass`, `UniformMass`, `BoxROI`, `ConstantForceField`, `MeshVTKLoader`, `MeshGmshLoader`, `MeshSTLLoader`, `MeshOBJLoader`, `BarycentricMapping`, `SurfacePressureConstraint` | all present |

Plugins: in Python `SofaRuntime.importPlugin("Sofa.Component")` (meta-plugin with all standard components) + `"SoftRobots"`. In scenes: `RequiredPlugin` with the field **`pluginName`**, because the `name` field is deprecated.

### How `SurfacePressureConstraint` works (`probe_volume_growth.py`)

Scene: the hollow "bunny" from the SoftRobots examples, without gravity.

1. **`valueType="volumeGrowth"`: `value` is the TOTAL growth relative to the initial volume** (`initialCavityVolume`), not the growth per step. With a constant `value = 40` the measured `cavityVolume − V0` = 40.000 from 0.25 s to 1.5 s. This matches the SoftRobots code (`dfree = V − V_initial`). Conclusion for `hydraulics.py`: every step we set `ΔV_L = V_prefill + V_p` directly, without differentiating.
2. **Sign:** a positive `value` enlarges the cavity and gives positive pressure (with the example's chamber mesh; for our mesh the sign test in stages 1–2 will check this, and if needed there is the `flipNormal` field).
3. **The `pressure` field is p·dt, not p.** The same steady state at dt = 0.001 and 0.002 gives raw `pressure` 2.2912 and 4.5824 (ratio 2.000), and `pressure/dt` = 2291.2 in both cases. Reason: the constraint solver computes the force **impulse** over the step (λ = p·dt), not the force.
4. **In `valueType="pressure"` mode the `value` input is also in units of p·dt.** Setting `value = p` (without ·dt) gave a pressure 1000× too large at dt = 1 ms and the FEM blew up (NaN), even with a ramp. `value = p·dt` reproduces the same volume growth (9.993 for a target of 10) at both dt.

Consequences for the next stages:
- `hydraulics.py` (valve on Δp) and all pressure plots must divide `pressure` by `dt`,
- the test "same p → deflection ~1/E" (spec, section 10) must set `value = p·dt`,
- in both modes `value` changes via a ramp: the SoftRobots example sets `volumeGrowth = 40` as a step in the first step and works only thanks to heavy damping.

Performance for orientation: the example bunny (dt = 1 ms) takes ~25 ms per step on this machine, about 40× slower than real time. SOFA suggests `ParallelTetrahedronFEMForceField` (MultiThreading plugin, the machine has 12 threads) – to be checked in stage 1.

### GUI

`runSofa` starts under Wayland without extra variables. The default GUI is **ImGui** (SofaImGui plugin). The `PressureVsVolumeGrowthControl` example works: after **Animate** both bunnies inflate (checked manually). On first launch the log shows `[ERROR] [ImGuiGUIEngine] Cannot set window position/size from settings`. This is only missing saved window settings, harmless. The `-g batch` mode works (50 steps of the example in 5.9 s).

## Stage 1 – tail mesh and sag under its own weight

### Geometry (`fishsofa/config.py`, `fishsofa/mesh_gen.py`)

Dimensions are copied from `MuJoCo/fishsim/config.py`; the test `test_dimensions_match_mujoco` enforces consistency. The body is 0.20 m long, with an elliptical cross-section of 0.06 × 0.08 m at the root, tapering linearly to 0.4 at the end. The fin is a 0.07 × 0.12 m plate, 6 mm thick. The two chambers span the length of 3 actuated MuJoCo segments (0.12 m), with a wall and septum of 4 mm each.

One deliberate deviation: the fin root enters 15 mm into the tail end, instead of 2 mm as in MuJoCo. In MuJoCo the fin is rigidly welded. In FEM a 2 mm connection would be a ~6 × 40 mm constriction that would act as a hinge.

How the mesh is built:
1. gmsh meshes **half** of the tail (y ≥ 0) with one chamber.
2. The other half is obtained by **mirroring**. This makes the mesh exactly symmetric, so the L/R symmetry test in stage 3 checks the code, not a meshing accident.
3. Cavity triangles are identified geometrically by the triangle centroid, inside the cavity outline enlarged by half a wall. The first version identified them by gmsh bounding boxes, but OpenCASCADE reports overly loose bboxes for B-spline surfaces and part of the cavity ended up in the "skin". The surface closedness test caught this.
4. Orientation: the skin has outward normals, the cavities point out of the cavity (SoftRobots convention from stage 0).

The mesh is saved as legacy VTK 4.2. meshio writes VTK 5.1, on which `MeshVTKLoader` from SOFA v26.06 segfaults.

### Mesh levels (`results/s1_mesh_report.txt`)

| level | h at surface | tetrahedra | elem. per 4 mm wall | tip deflection Δz | statics | dynamics |
|---|---|---|---|---|---|---|
| coarse | 4 mm | 28 112 | ~0.9 | −40.52 mm | 6 s | 0.77 s/step |
| medium | 3 mm | 51 818 | ~1.1 | −40.73 mm | 17 s | 2.3 s/step |
| fine | 2 mm | 142 096 | ~1.7 | −41.17 mm | 176 s | 19 s/step |

All levels: zero tets with volume ≤ 0, SICN (tetrahedron quality, 1 = ideal) ≥ 0.06, 1st percentile ≈ 0.35–0.40, closed surfaces, symmetric nodes. "Elements per wall" is the thickness divided by the mean tet edge near the cavity, i.e. an approximation, not a layer count. The spec wanted ≥ 3; that would require ~450k tets. Decision: a convergence study (see spec, section 4).

**The chambers are large:** 91.6 ml each, with 245 ml of silicone. With a 4 mm wall in a 6 × 8 cm cross-section the tail is mostly hollow. The water in the chambers (183 g) is ~40% of the tail mass. In the MuJoCo demo `V0_chamber` = 30 ml (also a placeholder). This mismatch must be resolved at PRBM export (stage 7) or with thicker walls.

### Mass and weight (`fishsofa/masses.py`)

SOFA gravity is disabled. Mass (silicone + water in the chambers, assigned to tets near the cavity walls) goes into `MeshMatrixMass` as a per-element density. Weight is applied via `ConstantForceField` on the nodes. Reason: in water, the water in the chambers has inertia but no weight (buoyancy = weight), and a single SOFA gravity vector cannot distinguish that. In `environment="water"` mode the silicone has apparent weight `g·(1 − ρ_w/ρ_s)`.

### What `results/s1_sag.png` shows

- **Left plot:** static tip sag under its own weight on three meshes. The coarse → fine difference is only 1.6% (−40.5 → −41.2 mm). Bending of the whole tail under its weight is carried mainly by the skin and core, not by the thin chamber walls, so the coarse mesh is sufficient. This does **not** settle stage 2: there the pressure deforms precisely the walls, so convergence must be measured separately there.
- **Right plot:** the tail "released" at t = 0 (weight applied as a step) on the coarse mesh. It oscillates around the static equilibrium (dashed line) with a period of ~0.33 s, i.e. the first natural frequency in air is ~3 Hz, and the oscillations decay through Rayleigh and numerical damping. The first excursion (−68 mm) is ~1.7× larger than the static one (an undamped system under a step load would give 2×).

### GUI

`scripts/run_gui.sh coarse` opens the tail. After **Animate** the tail drops and sways (checked manually). The motion is slow because one step takes ~0.8 s – see "Open problem" below.

### Statics in SOFA v26.06

`StaticSolver` requires a separate `NewtonRaphsonSolver` component (Newton parameters were moved there in v25.12) and **does not work with `FreeMotionAnimationLoop`** (the tail does not move), so statics uses `DefaultAnimationLoop`. The first Newton iteration overshoots (warning "Line search failed at Newton iteration 0"), the following ones converge (residual 42 → 0.13 → 0.006 → …). A second static step changes nothing (test).

### Dynamics performance: "warp" solver (before stage 2; limitation with chambers below)

The default `SparseLDLSolver` does a full LDLᵀ factorization of the matrix every step, because corotational FEM changes the stiffness matrix every step. That gave 383× slower than real time on coarse.

**Solution** (from the SOFA documentation and code on GitHub, `fishsofa/scene.py:_add_warp_solver`, `linear_solver="warp"`, default):
1. The LDLᵀ factorization is computed **once, in the rest state**: `RotationMatrixSystem` with a very large `assemblingRate`.
2. Every step it is only "rotated" by the current element rotations (`WarpPreconditioner`, `rotationFinder=@fem`). For corotational FEM the stiffness of the deformed tail ≈ R·K₀·Rᵀ.
3. The rotated factorization is the preconditioner for PCG (`PCGLinearSolver` + `PreconditionedMatrixFreeSystem`), which brings the result to the exact one in a few iterations.
4. The chamber constraint correction links the preconditioner (`LinearSolverConstraintCorrection linearSolver=@warp`), because PCG alone does not assemble the matrix.

| mesh | LDL (dt 2 ms) | warp (dt 2 ms) | speedup |
|---|---|---|---|
| test (12k tets) | 196 ms/step | 31 ms/step | 6.2× |
| coarse (28k) | 726 ms/step | 84 ms/step | 8.6× |
| medium (52k) | 2306 ms/step | 260 ms/step | 8.9× |
| fine (142k) | 19 337 ms/step | 1510 ms/step | 12.8× |

**Accuracy:** the tip trajectory on coarse over 0.4 s is identical to LDL (difference < 0.001 mm; test `test_warp_solver_matches_ldl`).

**But with a chamber warp is wrong** (checked in the stage 2 plan, test mesh, 30 ml in chamber L, steady state):

| solver | pressure |
|---|---|
| LDL, slow ramp, dt 2 ms | 1950.4 Pa |
| LDL, pseudo-static dt 10 / 50 ms | 1950.4 Pa |
| warp, dt 2 ms | **1471 Pa (−25%)** |

At 5 ml the difference was 1.7%, so the error grows with deformation. Cause: the constraint correction uses the approximate compliance J·A_warp⁻¹·Jᵀ, so the distribution of the pressure force over the nodes is wrong and the equilibrium shifts. Therefore **the default solver is `"ldl"` again**, and a scene with chambers forces LDL (test `test_warp_is_replaced_by_ldl_with_chambers`). Warp is useful only without chambers. For dynamics with chambers the solution is CHOLMOD (section below), which from then on is the default solver.

Three bugs in earlier attempts (stage 1), for future readers:
- `assemblingRate=15` (as in the SOFA example): the matrix is assembled in the deformed state, and the rotation from `TetrahedronFEMForceField` (computed relative to rest) is applied a second time, so the simulation blows up.
- Missing explicit link `EulerImplicitSolver linearSolver=@linsolver`: the integrator took the first solver in the node (the LDL from the preconditioner) and PCG was not used.
- `@…` links in SofaPython3 must point to objects that already exist, so creation order matters.

**Larger time step** (warp, coarse): dt 5 ms gives a 2× shorter total time, but the trajectory difference is 3.4 mm (~5% of amplitude). At dt 10 ms it is 3.5× faster, but with a 7.8 mm difference (~11%). Implicit Euler at a large step damps motion numerically. The default stays 2 ms; a larger step only deliberately, with the error stated.

**Tried without gain:** Metis/AMD/COLAMD ordering (the default is good), `nbThreads`, `ParallelTetrahedronFEMForceField` (matrix assembly stays sequential), CG on the assembled matrix (~10%), `AsyncSparseLDLSolver` alone (unstable, as the SOFA documentation admits).

**Unused options:**
- Model order reduction (ModelOrderReduction plugin, in the binary) gives up to ~50×, but requires offline training and works only within the trained range. A candidate only for stage 6.

### Performance: CHOLMOD (after stage 2, default solver)

`linear_solver="cholmod"`: `EigenCholmodSupernodalLLT` from the SofaCHOLMOD plugin. This is the same exact matrix factorization as LDL, only supernodal: the dense blocks are computed by an optimized BLAS (OpenBLAS via FlexiBLAS). Unlike warp it **works with chambers**, because the constraint correction gets the exact factorization. Measurement: dt 2 ms, with chamber L and fibers, 1 BLAS thread (4 and 6 threads give the same time):

| mesh | LDL | CHOLMOD | speedup | pressure LDL = CHOLMOD |
|---|---|---|---|---|
| coarse | 871 ms/step | 203 ms/step | 4.3× | yes (10588.97 Pa) |
| medium | 2447 ms/step | 471 ms/step | 5.2× | yes (14642.81 Pa) |
| fine | 19785 ms/step | 1324 ms/step | **15×** | yes (13071.41 Pa) |

Agreement with LDL is enforced by the test `test_cholmod_matches_ldl_with_chamber`. The tests (25) now take ~63 s instead of ~82 s.

**Why the master plugin on v26.06, and not all of SOFA master.** I built SOFA master (v26.12-dev, commit `6c3e21f`, 5.10.2026) together with SofaPython3, SoftRobots and STLIB in their master versions. It works, but has **a bug in the coupling of a chamber with stiff fibers**:
- with tension-only fibers (V4) the tail does not reach equilibrium but keeps vibrating (pressure ±0.5%), and the mean pressure is ~9% lower than in v26.06 (test mesh, 8 ml: 2790 instead of 3056 Pa);
- with fibers that also act in compression the simulation diverges (v26.06: stable, 3633 Pa);
- without fibers both versions give identical pressure (1321.52 Pa). The forces are identical too (the same load applied as nodal forces gives the same angle), and the fibers are correctly mapped (position difference < 1e-16 m). A minimal scene with a stiff mapped spring without a chamber works in both versions.

v26.06 comes to rest (velocity 1e-13 m/s), and with the same forces that is a true equilibrium. So we stay on v26.06. The likely cause is the switch of constraints from impulses to forces (SOFA PR #6117), but I have not confirmed it. Other changes in master, should we ever migrate: the `pressure` field and the pressure-mode input of `SurfacePressureConstraint` are in Pa, not p·dt (the probe `probe_volume_growth.py` detects both conventions), `NewtonRaphsonSolver` is removed (statics: `StaticEquilibriumIntegrationScheme` with `alwaysAdvanceNewton=True`), integrators have new names (`EulerImplicitIntegrationScheme`, module `Sofa.Component.IntegrationScheme.Backward`).

**How the plugin is built** (`scripts/build_cholmod_plugin.sh`): sources of the plugin alone from master (copied into `third_party/SofaCHOLMOD`, because master gets rewritten), compiled against the headers of the v26.06 binary with two fixes. (1) A newer `EigenSolverFactory.h`, because the plugin uses the `registerProxyType` template, which was added after v26.06. This is a pure header addition, with no change in class layout, so SOFA does not need rebuilding. (2) `FindCHOLMOD.cmake` without SuiteSparse's CMake config, because the Fedora config refers to non-existent `*_static.cmake` files. `env.sh` appends the plugin directory to `SOFA_PLUGIN_PATH`; `runSofa` sees it the same way.

### Performance: OpenBLAS from conda and parallel sweeps (6.10.2026, EndeavourOS)

**Step profile** (flapping, coarse, CHOLMOD, `py-spy --native`): 45% system matrix assembly (of which FEM 34%), 30% CHOLMOD factorization, 8% symbolic analysis of the matrix pattern, 6% constraint solver. All on one core.

**1. BLAS: 2.2× faster on Arch.** Supernodal CHOLMOD computes the dense blocks in BLAS. On Fedora the BLAS is OpenBLAS (via FlexiBLAS), but on Arch the system `libblas.so.3` is the reference, unoptimized netlib BLAS. There a step took 470 ms instead of ~200 ms. Now OpenBLAS comes from conda (`environment.yml`: `libblas=*=*openblas`), and `env.sh` symlinks it in the `fishsofa-pylib` directory (like libpython), independent of the system: **470 → 217 ms/step**, result identical to the last digit.

**2. Symbolic analysis every step – checked, no gain.** SOFA removes exact zeros from the matrix, and `elongationOnly` fibers in the slack state have zero stiffness, so the matrix pattern changes and CHOLMOD repeats the analysis. I tried a patch in the plugin (analysis only when the new pattern is not a subset of the previous one). Measurement: the analysis repeats only in the first ~300 steps (prefill, when successive fibers tension for the first time), never afterwards, even without the patch. In steady motion both variants give 204–206 ms/step, so I reverted the patch (the plugin stays unchanged).

**3. One simulation = one core, so sweeps run in parallel.** Matrix assembly in SOFA is sequential (`ParallelTetrahedronFEMForceField` does not change that), CHOLMOD blocks are too small for many BLAS threads, and successive time steps depend on the previous ones. That is why `top` shows ~1/12 of the CPU per simulation. The sweep points (stages 5–6), however, are independent: `fishsofa/parallel.py` runs them in separate processes (up to 10 at once on 12 threads, ~0.5 GB RAM each; `FISHSOFA_WORKERS` changes the limit). `env.sh` sets `OPENBLAS_NUM_THREADS=1` so the processes do not fight over cores.

Remaining reserves, unused: model order reduction (ModelOrderReduction, requires training), higher-order elements (fewer nodes for the same pressure accuracy, but SOFA does not have them for corotational FEM with chambers), custom parallel FEM matrix assembly (a change in SOFA's C++).

## Stage 2a – why the tail did not bend and what helped

**Problem:** with the stage 1 geometry (V0: 4 mm walls, homogeneous silicone) 72 ml in chamber L bends the tail by only 1.3°. The fluid goes into bulging the outer wall (like a balloon) and into deflecting the septum towards chamber R, not into elongating the left side of the tail. Only elongation of one side produces bending.

**Variant sweep** (`scripts/run_stage2_variants.py`, coarse, quasi-static, chamber R vented, no weight; `results/s2_variants.png`, `.csv`):

| variant | max \|θ\| (at ΔV) | p at max | 15° at |
|---|---|---|---|
| V0 current | 1.3° (72.5 ml) | 7.2 kPa | – |
| V1 spine E×20 | 2.8° (72.5 ml) | 13.4 kPa | – |
| V2 wall 8 mm | 0.6° (47.5 ml) | 9.1 kPa | – |
| V3 hoop fibers | 9.0° (72.5 ml) | 10.4 kPa | – |
| **V4 spine + fibers** | **31° (72.5 ml)** | 33.8 kPa | **47.0 ml, 17.5 kPa** |

What the plot shows:
- Each element alone gives little. The hoop fibers stop the wall from bulging, and the spine (septum E×20 along the whole length) acts as an inextensible layer on the bending axis. Only together do they turn the injected volume into elongation of the side, i.e. into bending.
- A thicker wall **makes things worse**: the chamber is smaller and the tail stiffer.
- This is the same principle real soft actuators use: fiber reinforcement and a strain-limiting layer.

**Choice:** V4. V4 misses the criterion (15° at p ≤ 50 kPa and ΔV ≤ 50% of chamber volume) by a hair: 51.4% of the volume at 17.5 kPa. User decision: V4 unchanged, because the pressure has a large margin and the overshoot is within the coarse mesh uncertainty. V4 is now the default construction in `config.py`. Stage 1 was still computed for V0.

**How it is modeled:**
- **Spine:** tets with centroid at |y| ≤ septum/2 get E×20 (`spine_E_factor`, PLACEHOLDER). With ~1 element across the septum thickness this is an approximation; the mesh report gives the region volume relative to nominal.
- **Fibers:** rings of points every 4 mm along the chambers, 0.5 mm below the skin, connected by tension-only springs (`StiffSpringForceField elongationOnly`). They are attached to the FEM via `BarycentricMapping`. The stiffness corresponds to a membrane K = 2·10⁵ N/m (e.g. fabric ~1 GPa × 0.2 mm, PLACEHOLDER). In the simulation the thread elongates < 0.15%.
- Two bugs caught along the way: `elongationOnly=True` is silently ignored in SOFA v26.06, because it is a list with one value per spring, and SOFA reads `"1 1 1 …"` (test `test_hoop_fibers_work_in_tension_only`). In addition, after changing the default config to V4, the variant "V0 = {}" was computed as V4, so now every variant sets all switches explicitly.
- The first version of the fibers placed springs on the skin mesh edges. The loft mesh, however, has no hoop edges (only axial and diagonal at 45–72°), so in practice there was no reinforcement and V3/V4 looked useless. This was caught by the complete absence of any change in bulging.

**Note on the "bulging" measure:** it is the displacement of the outermost skin node on the chamber side **relative to the tail axis**, and with chamber R vented the axis also moves, because the septum deflects towards R. Measuring the fiber ring showed that the V4 wall itself moves outward by only ~0.4 mm at 8 ml.

**Chamber R mode** (test mesh, V4, 12 ml in L): vented −3.0°, closed (constant volume) −2.6°, antagonistic (ΔV_R = −ΔV_L, i.e. pump operation) −2.8°. The R mode changes the result by ~15%.

## Stage 2 – chamber L quasi-static: p–V curve and tip angle

`scripts/run_stage2.py`. Construction V4, chamber L gets a prescribed volume growth of 0…50 ml, chamber R is vented (pressure 0, like the second port open on the test rig), no weight. Computed pseudo-statically: implicit Euler with dt = 50 ms and LDL (stage 2 results were still computed with LDL; CHOLMOD gives the same numbers). After each point the volume is held until kinetic energy < 1% of the pressure work ∫p dV; in practice it comes out ≤ 0.4%. This method gives the same state as a slow ramp at dt = 2 ms (checked on the test mesh: 1950.4 Pa in both cases), and is 5–25× cheaper. `StaticSolver` is ruled out because it does not work with the chamber's Lagrange constraints.

### Results (`results/s2_pv_curve.png`, `results/s2_tip_angle.png`, `results/s2_curves.csv`)

| mesh | p at 50 ml | θ_tip at 50 ml | time |
|---|---|---|---|
| coarse (28k tets) | 19.3 kPa | −16.3° | 35 s |
| medium (52k) | 18.4 kPa | −15.7° | 1.7 min |
| fine (142k) | 16.1 kPa | −15.4° | 16 min |

- **The p–V curve** (`s2_pv_curve.png`) is almost linear at first and increasingly steep. A tail bent by 15° is harder to bend further, and the fibers carry more and more force. At 50 ml ~16 kPa is needed, i.e. 1/3 of the valve opening pressure from MuJoCo (50 kPa). The pump has margin.
- **Tip angle** (`s2_tip_angle.png`): chamber L (+Y) elongates the left side, so the tail bends towards **−Y** (θ < 0, to the right). The relation is also slightly convex: ~0.25°/ml at first and ~0.45°/ml at 50 ml. You will measure the same curve on the real tail (volume-dosing syringe, pressure gauge, photo from above), and this is the main result of the demo.

### Mesh convergence (`results/s2_convergence.txt`)

| | p @ 25 ml | θ @ 25 ml | p @ 50 ml | θ @ 50 ml |
|---|---|---|---|---|
| coarse vs fine | +26.6% | +4.8% | +20.3% | +5.9% |
| medium vs fine | +19.9% | +2.7% | +14.5% | +2.5% |

**The angle converges well** (coarse already within ~5%). **The pressure converges poorly**: even medium is 15–20% too high, and fine is probably not the limit yet either. The angle follows from kinematics (how much volume was injected and how long the side is), while the pressure follows from the stiffness of the thin walls, and with ~1–2 elements across the thickness those are too stiff (locking of linear tetrahedra). Conclusions:
- for the shape of the motion (angle, stages 4–6) coarse is sufficient, with an error of ~5%,
- pressures from coarse are overestimated by ~20–25%; for comparisons with pressure measurements this error must be stated, or computed on fine,
- more accurate pressure would require quadratic elements or ≥ 3 elements per wall (~450k tets), which the SOFA binary cannot handle here in reasonable time.

### How to measure it on a real tail (calibration)

1. Tail bolted to the table by its root, chamber R with its port open.
2. Syringe or dosing pump into chamber L in 5 ml increments, pressure gauge at the inlet and a photo from above (angle of the chord from the root to the fin center, same as `geometry.tip_angle`).
3. Fitting: first `young_modulus` to the p–V curve (pressure scales ~linearly with E), then `spine_E_factor` and `hoop_stiffness` to the θ–V curve. On the coarse mesh, account for its +20% on pressure.

## Stage 3 – symmetry: chamber R as the mirror of chamber L

`scripts/run_stage3.py` (~3 min with CHOLMOD). Same conditions as in stage 2: V4, no weight, the other chamber vented, 5…50 ml. Computed separately for chamber L and R, on three mesh levels. The mesh is mirrored by construction: every node has a pair in the reflection about the XZ plane, at a distance of 0.0 m. The fiber rings are symmetric too.

**Result** (`results/s3_symmetry.png`, `.csv`, `.txt`): at 50 ml on fine chamber R gives p = 16.050 kPa and θ = +15.352°, and chamber L the same 16.050 kPa and −15.352°. Largest symmetry error over the whole range:

| mesh | angle | pressure | bulging |
|---|---|---|---|
| coarse | 0.75% | 0.023% | 0.14% |
| medium | 0.11% | 0.008% | 0.014% |
| fine | 0.34% | 0.012% | 0.11% |

The spec requires < 5%; the test `test_chamber_R_mirrors_L` enforces 1% on the test mesh.

**Where the residual error comes from:** not the mesh, but the criterion for ending the hold of a point (kinetic energy < 1% of pressure work). The L and R simulations stop at slightly different moments of the decaying motion. That is why the error is largest at the first point (5 ml), where the post-ramp motion is largest relative to the deflection. At 30–50 ml it drops to 1e-5…1e-7%. On fine it stays at ~1e-3%: this is round-off noise of the matrix factorization with a different element order in the mirrored half.

**CHOLMOD check:** the L curve from this stage (CHOLMOD) differs from stage 2 (LDL) by ≤ 0.0006% in angle and ≤ 0.0002% in pressure on all levels. The stage 2 results do not need recomputation.

## Stage 4 – antagonistic hydraulics: flapping in air

`scripts/run_stage4.py` (~25 min). Coarse mesh, air, weight on, chambers full of water. Sequence: 0–1 s prefill of both chambers to 20 ml, then the V_ref(t) rhythm with a 1 s ramp, 4.5 s in total. The pump transfers fluid from R to L (`fishsofa/hydraulics.py`), and the SOFA controller (`fishsofa/controller.py`) sets the volume growth of both chambers every step: ΔV_L = prefill + V_p, ΔV_R = prefill − V_p. **+V_p (chamber L) bends the tail towards −Y, to the right. This corresponds to +V_bias in MuJoCo ("turn right").**

### Parameters: why not 1:1 with MuJoCo
The SOFA chamber is 91 ml, while in MuJoCo `V0_chamber` = 30 ml. A_V = 8 ml from MuJoCo would give ~±3° here. In addition, Q_max = 60 ml/s cannot keep up at 2 Hz (2π·f·A_V is needed), so it would come out even less. The largest motion that fits safely was chosen: **A_V = 17 ml, V_prefill = 20 ml, Q_max = 250 ml/s**. The other values are as in MuJoCo: f = 2 Hz, K_v = 10 1/s, τ_pump = 30 ms, p_max = 50 kPa.

**Upper prefill limit: spine buckling.** Filling both chambers elongates the tail lengthwise, and the stiff spine is then compressed. Static measurement on the coarse mesh:

| prefill | common pressure | symmetric state |
|---|---|---|
| 10 ml | 25 kPa | straight |
| 20 ml | 53 kPa | straight |
| 24 ml | 64 kPa | θ = 0.02°, and Δp has the wrong sign (L more filled, yet lower pressure) |
| 30 ml | 78 kPa | θ = 0.34°: the tail bends with no volume difference |

±15° would require a prefill > 24 ml, i.e. already in this range. Design conclusion: with construction V4 the prefill limits the amplitude, because the common pressure loads the spine axially.

**Pump lag compensation (change relative to MuJoCo).** The MuJoCo command, u = (dV_ref/dt + K_v·(V_ref − V_p))/Q_max, overshot at 2 Hz: V_p reached 1.16·A_V, i.e. 19.7 ml, and chamber R nearly reached its rest volume. This happened even without pump saturation (Q_max 400 ml/s: 1.17×). The first-order pump has ωτ = 0.38, so feedforward alone lags. The added term τ_pump·d²V_ref/dt² inverts this lag: the tracking error drops to 1.2% of A_V, without saturation (test `test_pump_tracks_v_ref`). **The same problem exists in MuJoCo** (`MuJoCo/fishsim/controllers.py`); I changed nothing there.

### Results (`results/s4_air_flapping.png`, `.csv`, `results/s4_summary.txt`)

| | dt = 2 ms | dt = 1 ms |
|---|---|---|
| θ amplitude (steady cycle) | **±12.66°** | ±13.33° |
| amplitude change in the last cycle | 0.00% | 0.00% |
| θ phase lag relative to −V_ref | 50° | 47° |
| p_L, p_R | 50.1–56.4 kPa | 50.2–56.3 kPa |
| \|Δp\| max | 5.7 kPa (valve does not open) | 5.5 kPa |
| ΔV_L + ΔV_R measured (target 40 ml) | 39.9991–40.0025 ml | 39.9992–40.0003 ml |
| constraint solver | ≤ 30 iterations, error ≤ 2e-9 | ≤ 28 iterations |
| compute time | 198 ms/step = **99× slower than real time** | 181 ms/step = 181× |

Observations:
- The cycle settles already in the second cycle after the ramp, and the mean angle is 0.000°: with a 20 ml prefill there is no buckling.
- The angle lags the volume by ~50°, while in statics there would be no lag. The lag is due to the inertia of the tail with water in the chambers, not the pump (V_p coincides with V_ref, bottom panel of the plot).
- The pressure difference is small (±5.7 kPa) against the common pressure of 53 kPa. In the antagonistic system the motion is driven by the difference, and it is still far from 50 kPa.

**Effect of dt (spec, section 5):** at dt = 2 ms the amplitude is 5.1% smaller than at 1 ms. Implicit Euler damps numerically and this damping grows with dt. For stages 5–6 this is a known systematic error (−5% of amplitude). If comparisons are to be quantitative, compute at 1 ms, at the cost of 2× longer run time.

**GUI (checked 5.10.2026: the tail flaps):** `scripts/run_gui.sh` (default `flap` mode, Animate) shows the same sequence with the chamber pressures drawn (`drawPressure`). The first second is the prefill (the tail almost stands still), and 1 s of simulation takes ~2 min to compute. Sag under its own weight from stage 1: `scripts/run_gui.sh coarse sag`.

## Stage 5 – water: drag, tethered thrust

`scripts/run_stage5.py` (~60 min wall-clock, 3 simulations at once). Same sequence as in stage 4 (coarse, prefill 20 ml, 2 Hz, A_V = 17 ml), but `environment="water"`: the silicone has apparent weight g·(1 − ρ_w/ρ_s), the water in the chambers has inertia without weight, and water drag acts on the skin. GUI: `FISHSOFA_ENV=water scripts/run_gui.sh`.

### Drag model (`fishsofa/water.py`, `controller.WaterDragController`)

Each skin triangle gets a force depending only on its own velocity v (average of its 3 nodes), outward normal n and area A:
- normal F_n = −½ρ·C_n·A·(v·n)|v·n|·n (pressure drag),
- tangential F_t = −½ρ·C_t·A·|v_t|·v_t (skin friction).

The triangle force goes 1/3 to each of its nodes, through a `ConstantForceField` "water" updated at the start of every step. C_n = 1 and C_t = 0.01 are PLACEHOLDERs. C_n acts on each side of the surface, so a thin plate in cross-flow has C_d ≈ 2·C_n ≈ 2, like a flat plate (test `test_drag_on_flat_plate`). The functions are pure numpy and have tests without SOFA: drag power F·v ≤ 0 on every triangle, zero velocity gives zero force.

**Stability.** A force computed from the previous step's velocity is explicit damping. A node with mass m and local coefficient c = ρ·C_n·A_node·|v_n| is stable only for c·dt/m clearly < 1. The worst are the fin nodes (6 mm thick, light and with a large area):

| dt | max(c·dt/m) in the steady cycle |
|---|---|
| 2 ms | ~0.7 (test mesh), too much |
| 1 ms | **0.536**, momentarily at peak fin velocity, just above 0.5 |
| 0.5 ms | **0.272**, the stage result |

Between 1 ms and 0.5 ms the amplitude differs by 1.4%, and the thrust by 5%. Forces are not clipped. The 0.5 ms step costs 2×. The cheaper route would be implicit: drag as a `ForceField` with a damping term in the system matrix (an extension from the spec, not done).

### Results (`results/s5_water_vs_air.png`, `.csv`, `results/s5_summary.txt`)

| | air (dt 1 ms) | water (dt 0.5 ms) |
|---|---|---|
| θ amplitude (steady cycle) | ±13.33° | **±7.32°** (0.55×) |
| θ phase lag relative to −V_ref | 47° | 77° (+30°) |
| \|Δp\| max | 5.5 kPa | 5.6 kPa |
| tethered thrust (mean F_x) | – | **+67 mN** |
| lateral force F_y | – | ±755 mN |
| mean drag power | – | 125 mW |

Observations:
- **Same volume command, almost half the flapping.** In air the tail (with its ~3 Hz natural frequency, stage 1) is close to resonance at 2 Hz and inertia amplifies the motion beyond the static excursion. Water damps this amplification and shifts the phase by +30°: the angle lags the volume even more.
- **Δp barely changes.** The chamber pressure is set mainly by the stiffness of the tail and walls (order of 10⁴ Pa), and the water forces are small compared with the elastic forces. For the pump and valve, water changes little at these parameters.
- **Thrust is ~10× smaller than the lateral force**, and its F_x component pulses at 2f (two "pushes" per cycle, one for each sideways stroke). On average +67 mN. This is only qualitative: the model has drag only, without added mass and without a vortex wake, and those effects dominate fish thrust (Lighthill). The real tail will probably give a different number; for comparison use a measurement on a scale in a tub (section "How to calibrate").
- 361–408 ms/step with 3 parallel processes and 11 processes together with stage 6 (alone ~220 ms). Water at dt 0.5 ms computes ~800× slower than real time.

## Stage 6 – sweeps: frequency and Young's modulus

`scripts/run_stage6.py`: 19 independent simulations (coarse mesh) run in parallel via `fishsofa/parallel.py`. **Time for the whole sweep: 68 min wall-clock**, including 444 CPU-min of the dynamic simulations alone, i.e. 6.5× faster than sequentially (8 processes at once alongside 3 from stage 5). Results: `results/s6_freq_sweep.png/.csv`, `results/s6_young_sweep.png/.csv`, `results/s6_summary.txt`.

### a) Frequency 0.5–3 Hz in water (`s6_freq_sweep.png`)

Same points as `MuJoCo/scripts/sweep_frequency.py` (every 0.25 Hz), same volume amplitude A_V = 17 ml. Protocol: prefill 1 s, 2 run-in cycles (the first is the amplitude ramp), 3 averaging cycles. Step: 1 ms up to 2 Hz, above that 1 ms·2/f.

| f [Hz] | 0.5 | 1.0 | 1.5 | 2.0 | 2.25 | 2.5 | 3.0 |
|---|---|---|---|---|---|---|---|
| θ amplitude [°] | 11.8 | 10.8 | 8.9 | 7.2 | 6.5 | 5.7 | 4.3 |
| phase lag [°] | 17 | 40 | 61 | 77 | 84 | 91 | 106 |
| thrust [mN] | 1.5 | 19.6 | 45.9 | 63.2 | **67.9** | 62.8 | 47.0 |
| \|Δp\| max [kPa] | 1.7 | 3.5 | 4.9 | 5.7 | 5.9 | 5.9 | 5.4 |
| pump saturated [% of time] | 0 | 0 | 0 | 0 | 18 | 36 | 53 |

What the plot shows:
- **Amplitude decreases with f over the whole range.** In water the tail has no resonance: drag grows with the square of velocity and damps it more strongly than in air (where the natural frequency is ~3 Hz, stage 1). At low f the angle approaches the quasi-static one (~12°, compare stage 2) and barely lags the volume.
- **Thrust peaks at ~2.25 Hz.** It rises because fin velocity rises (drag ~ v²), and falls because the amplitude decreases and from 2.25 Hz the pump saturates: the required peak flow 2π·f·A_V (240 ml/s at 2.25 Hz, plus pump lag compensation) exceeds Q_max = 250 ml/s.
- **The valve opens nowhere:** |Δp| ≤ 6 kPa versus p_max = 50 kPa. With this construction the limit is pump capacity, not pressure.
- **Comparison with MuJoCo** (`MuJoCo/results/s5_sweep.png`, rescaled dashed line on the plot, shape only): MuJoCo has an amplitude peak at 1.5 Hz, SOFA has no peak. Reasons: MuJoCo models a swimming fish with added mass and passive resonance (`passive_resonance_hz`), while here the tail is clamped, with drag only, which at this stiffness damps the resonance completely. The drop above 2 Hz (pump saturation) looks similar in both.
- **Drag stability:** max(c·dt/m) is 0.52 at 1.75 Hz and 0.54 at 2 Hz (dt 1 ms), everywhere else < 0.5. Stage 5 measured the effect of such an exceedance: at dt/2 amplitude +1.4%, thrust +5%. A better rule for the future: dt = 1 ms·min(1, 1.6/f).

### b) Silicone Young's modulus ×0.5 / ×1 / ×2 (`s6_young_sweep.png`)

Only the silicone is changed (together with the spine, because its E is 20× the silicone). The hoop fibers are a different material and their stiffness stays.

| | E×0.5 | E×1 | E×2 |
|---|---|---|---|
| **volume control**, 40 ml: pressure | 7.1 kPa | 14.2 kPa | 27.9 kPa |
| same case: angle | −11.35° | −11.35° | −11.16° |
| **pressure control**, 8 kPa: angle | −12.91° | −6.03° | −2.73° |
| **dynamic in water, 2 Hz**: amplitude | ±5.8° | ±7.2° | ±8.2° |
| same case: phase lag | 96° | 77° | 59° |

**Lesson: volume control vs pressure control.**
- The pump imposes **volume**. When the whole construction is "one material times k" and there are no external loads, the equilibrium at a prescribed ΔV does not depend on k at all: the same shape, only pressure ×k. This is seen here almost exactly (the angle at 40 ml differs by < 2%, the pressure scales 0.50 / 1 / 1.97). The deviation at 10 ml for E×0.5 (−1.68° vs −1.93°) comes from the fibers, which do not scale: with soft silicone they are relatively stiffer. The test `test_young_x2_same_volume_doubles_pressure_keeps_angle` also scales the fibers and checks the law exactly.
- Stiffness therefore determines the **required pressure**: choice of pump, valve, sealing, silicone fatigue. It affects the motion only through external loads: water, inertia, weight.
- **With pressure control it is the opposite:** the same p gives a deflection ~1/E (8 kPa: 12.9° / 6.0° / 2.7°, test `test_young_x2_same_pressure_halves_angle`). Even faster than 1/E, because the p–V curve stiffens (stage 2), and the soft tail goes deeper into its nonlinear part.
- **Dynamically in water E does change the motion:** a stiffer tail has a higher natural frequency, so at 2 Hz it lags the volume less (59° vs 96°) and "loses" less motion to drag. The soft tail flaps less at the same volume, because with its slower response the water takes away a larger part of the motion.

## Real-time preview: recording, playback, video

Live in the GUI the tail moves 100–800× slower than in reality (a step takes 200–400 ms to compute and simulates 0.5–2 ms). So we compute the motion offline, save it and replay it at true speed:

```bash
source SOFA/scripts/env.sh
python SOFA/scripts/record.py               # air + water recordings, in parallel (~40 min) -> SOFA/recordings/*.npz
SOFA/scripts/run_replay.sh                  # SOFA GUI: real-time water replay, looped
SOFA/scripts/run_replay.sh SOFA/recordings/air.npz 0.25   # air, 4× slowed down
pip install pyvista==0.49.0                 # once, only for video
python SOFA/scripts/render_video.py         # video -> SOFA/results/flapping.mp4 (~3 min)
```

- **Recording** (`scripts/record.py`, `headless.run_flapping(record_fps=60)`): positions of all nodes every 1/60 s of simulation time, pressures and angle. ~25 MB per recording, the `recordings/` directory is outside the repo. Steps as in stages 4–5: air 1 ms, water 0.5 ms.
- **Replay in the GUI** (`fishsofa/replay.py`, mode `FISHSOFA_MODE=replay`): a scene without physics, visual models only. The controller picks the frame by wall-clock time, so the speed does not depend on rendering speed. The skin is semi-transparent, and the chambers are colored by pressure (blue = lowest in the rhythm phase, red = highest; the scale excludes the prefill, because the motion is driven by the ±6 kPa difference against the common ~53 kPa). The camera is rotated with the mouse as usual.
- **Video** (`scripts/render_video.py`, PyVista + ffmpeg): air and water side by side, top view, common pressure scale, θ(t) with a cursor underneath. First the whole 4.5 s run in real time, then the last cycle 4× slowed down.

### Readouts in the GUI: values, forces, colored skin

Both GUI modes show live values in the 3D view (on by default; `FISHSOFA_OVERLAY=0` turns them off):

| What | Replay (`run_replay.sh`) | Live (`run_gui.sh`) |
|---|---|---|
| Text panel: time, pump volume V_p, p_L, p_R, Δp, tip angle, tip displacement, max \|u\| | ✓ | ✓ |
| Net water force on the tail F_x (thrust), F_y, \|F\|; F_y on each of 8 slices | ✓ (water) | ✓ (water) |
| Arrows: water force on each of 8 tail slices | ✓ (water) | ✓ (water) |
| Skin colored with a legend, changing every loop: displacement \|u\| → water load [Pa] → von Mises stress [kPa] | ✓ | – |
| Plain dark background (`BackgroundSetting`) instead of the logo pattern | ✓ | ✓ |

- **Text** (`fishsofa/hud.py`): a column of `OglLabel`s. The overlay font is SOFA's built-in bitmap font (ASCII only, so "dp" and "deg"); it cannot be changed from the scene, hence the plain background.
- **Data fields:** the replay controller also exposes every value as a Data field (groups *Hydraulics*, *Displacement*, *Forces on the tail*). Double-click `replay` in the Scene Graph to see them in the ImGui component window.
- **Forces in replay:** the recording stores only node positions and a log, so the per-node water forces are recomputed with the simulation's drag model (`water.drag`) from velocities obtained by differentiating the positions.
- **Stress** (`fishsofa/fields.py`): von Mises stress per tetrahedron from the node positions, with the same corotational linear model as the FEM (rotation removed by polar decomposition, Hooke's law with the per-element E), averaged to the nodes by volume. It is the stress in the silicone only (hoop fibers excluded). Computed once per recording (~10 s) and cached as `recordings/<name>.stress.npz`. The color scale ends at the 95th percentile: the 20× stiffer spine carries the peak stress and saturates red.
- **Camera:** `fishsofa/scene.py.view` (SOFA's camera file, read by the GUI next to the scene) gives a top view of the whole tail.
- **Slower playback:** `SOFA/scripts/run_replay.sh SOFA/recordings/water.npz 0.5` (half speed, used for the report video).
- Tests: `pytest -q tests/test_fields.py` (rotation gives no stress, uniaxial strain matches Hooke's law, slice forces sum to the total).
