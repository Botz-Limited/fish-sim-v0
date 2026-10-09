# fish-sim-v0 / OpenFOAM – FSI of a soft tail in water (OpenFOAM + preCICE + CalculiX)

Educational demo of **fluid–structure interaction** (FSI) for a soft,
hydraulically actuated fish tail. Specification:
[SPEC_fish_fsi_openfoam_precice_calculix.md](SPEC_fish_fsi_openfoam_precice_calculix.md).
**This is not a calibrated model** – all physical parameters are
placeholders (`tools/params.py`, `PLACEHOLDER` comments in the files).

What it shows that MuJoCo and SOFA cannot:
- real water flow (Navier–Stokes, OpenFOAM) around the deforming tail,
- two-way coupling: the water deforms the tail, the tail changes the flow (preCICE),
- the vortex wake and thrust/drag computed from pressure and stresses on the surface,
- the **added mass** effect and why silicone–water coupling requires an implicit scheme.

Status: **stages 0–6 completed** (7.10.2026); `tools/check_results.py`: 47 PASS,
1 FAIL (E4 – amplitude in water larger than dry, because the 1 Hz actuation hits
the resonance in water; explained in NOTES.md). Stage 7 (3D) not run – requires
confirming the computation time.

Log of problems and their diagnoses: [NOTES.md](NOTES.md). Exact versions: [versions.txt](versions.txt).

---

## 1. Installation (Arch Linux / EndeavourOS)

```bash
# once, requires a password (~1 GB, mostly ParaView):
sudo pacman -S --needed openmpi scotch gcc-fortran arpack ccache git-lfs \
     paraview python-matplotlib python-pandas python-scipy
OpenFOAM/setup.sh            # the rest without sudo, ~1.5 h (mostly compiling OpenFOAM)
source OpenFOAM/env.sh       # in every new shell (bash or zsh)
```

`setup.sh` skips steps that are already done. It installs into `~/opt/fsi` (preCICE,
CalculiX, Python venv) and `~/OpenFOAM/OpenFOAM-v2606`.

| Component | Version | Notes |
|---|---|---|
| preCICE | **3.4.1** | from source, Release, `-O3 -march=native`, **Eigen 3.4.0** (Eigen 5 from Arch causes an FPE, see NOTES) |
| OpenFOAM | **v2606** (openfoam.com) | from source, `-O3 -march=native`, ccache, system OpenMPI 5 |
| OpenFOAM adapter | **1.4.0** | release “v1812–v2606-newer” |
| CalculiX + adapter | **2.20** + **2.20.2** | adapter 2.20.2 requires ccx 2.20; **PARDISO** solver (Intel MKL from pip) |
| preCICE tutorials | `develop` @ `e3188113` | the latest release (v202404.0) is from 2024, older than adapter 1.4 |

Why this set: compatible with preCICE v3 – the newest preCICE, an OpenFOAM adapter
declaring support for OpenFOAM up to v2606, a CalculiX adapter for preCICE v3.
The latest official “preCICE Distribution” (v2404.0) contains older versions
(preCICE 3.1.1, OF adapter 1.3.0) – newer releases keep v3 compatibility.

**Performance (Ryzen AI 5 PRO 340, 6 cores / 12 threads, 27 GB RAM):**
- fluid: 4 MPI processes (`decomposeParDict`, scotch), ~20 ms/step at ~21k cells,
- solid: CalculiX with PARDISO on 2 threads – **1.6x faster than SPOOLES**,
  and SPOOLES with 4 threads even gave wrong results (NOTES.md),
- typically ~0.6–1 s per FSI time window (5–6 coupling iterations).

---

## 2. Structure

```
OpenFOAM/
  README.md  NOTES.md  versions.txt  setup.sh  env.sh  run_parallel.sh
  00-reference-flap/      official perpendicular-flap tutorial (OpenFOAM + CalculiX), unchanged
  01-solid-only/          CalculiX alone: tail with chambers, pressure ramp, no water
  02-fluid-only/          OpenFOAM alone: rigid tail in inflow, mesh convergence, domain boundaries
  03-fsi-passive/         FSI: passive tail in a stream; explicit/ vs implicit/
  04-fsi-actuated/        FSI: chamber pressure actuation, still water; water/ vs dry/
  05-fsi-inflow/          FSI: actuation + inflow U = 0.05 / 0.1 / 0.2 m/s
  06-freq-sweep/          FSI: f = 0.5 / 1.5 / 2 Hz (1 Hz = stage 4)
  tools/
    params.py             ALL physical and geometric parameters (placeholders)
    make_geometry.py      gmsh: 2D tail geometry with chambers -> CalculiX and OpenFOAM
    make_actuation.py     chamber pressure waveform (*AMPLITUDE/*DLOAD)
    fluid-base/           OpenFOAM case template (commented)
    precice-base/         precice-config templates (implicit/explicit), fsi.inp, config.yml
    new-fsi-case.sh       creates an FSI case from the templates (parameters: U, dt, T, P0, f, scheme)
    postprocess.py        forces, tip angle, plots -> results/
    pv_snapshots.py       pvbatch: vorticity field snapshots -> results/
    check_results.py      automatic correctness criteria (SPEC, section 7)
  results/                PNG + CSV
```

Each FSI case has the same layout as the preCICE tutorials: `fluid-openfoam/run.sh`,
`solid-calculix/run.sh` (they can be started in two terminals) and
`run.sh` one level up, which starts both at once.

---

## 3. Physical model

```
           y
           ^        head (rigid, fixed)               tail (silicone, CalculiX)
           |        ________________________________________________
 inflow U  |      /                    |  [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]  chamber L (10 cells) \
 -------> -+-----(                     |================================== middle wall         |  -> vortex wake
           |      \____________________|  [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]  chamber R            /
           |    x = -0.06              x = 0 (root)                                  x = L = 0.15
```

- **2D** (tail cross-section seen from above). The model is 1 m thick in z, so
  **all forces are in N/m** (per metre of span) – as in the tutorial.
- Tail: 0.15 m, thickness 0.03 → 0.01 m. Two chambers (L/R) divided by ribs into
  10 cells (PneuNet style) – a single long chamber “ballooned” instead of bending
  the tail (NOTES.md, stage 1).
- Water: ρ = 1000 kg/m³, ν = 1e-6 m²/s.
- Silicone: E = 3e5 Pa, ν = 0.45, ρ = 1070 kg/m³, linear elastic, **NLGEOM**
  analysis (large deflections). C3D8 elements, one layer in z, z displacement
  locked (plane strain).
- Actuation: pressure on the cell walls (`*DLOAD` + `*AMPLITUDE`):
  p_L = P0·r(t)·max(0, sin 2πft), p_R = P0·r(t)·max(0, −sin 2πft), ramp r(t)
  over the first period.

### Simplifications you need to understand

**Laminar flow at a turbulent Re.** For U = 0.2 m/s and a body length of
0.21 m: Re = U·L/ν ≈ 4·10⁴, so the real flow is transitional/turbulent. The demo
computes laminar flow (`pimpleFoam`, `simulationType laminar`). In 2D, laminar
flow at this Re gives a regular vortex street, but friction drag and
boundary-layer separation carry errors. A “laminar-correct” variant = lower Re
(e.g. ν = 1e-4 → Re ≈ 400) at the cost of realism.

**Pressure instead of volume.** We prescribe the pressure in the chambers. A
(positive-displacement) hydraulic pump rather prescribes *volume* – with
prescribed pressure the tail can “give way” under the water load, whereas with
prescribed volume the pressure rises when the water resists. This is an
approximation; SOFA (the neighbouring demo) prescribes volume.

---

## 4. Key numerical issues

1. **Added mass → implicit coupling.** Silicone density ≈ water density.
   When the tail accelerates it must also accelerate the water around it – in 2D
   this “added mass” is several times larger than the tail's own mass. With explicit
   coupling (one data exchange per step) the force error is multiplied in every step
   by a factor ~ m_added/m_body > 1, so it grows exponentially – **regardless of
   the time step**. Stage 3 demonstrates this. Solution: `parallel-implicit` with
   **IQN-ILS** acceleration (interface quasi-Newton).
2. **Mesh motion.** `dynamicMotionSolverFvMesh` + `displacementLaplacian` with
   diffusivity `quadratic inverseDistance (tail head)`: cells near the body
   move almost rigidly, and the deformation is absorbed by the large cells further out.
   Tip amplitude limited to ~15% L. Larger amplitudes require
   remeshing or overset meshes – outside the scope of the demo.
3. **Mapping** (`precice-config.xml`): RBF (compact-polynomial C6, radius
   5 mm), forces `conservative` (conserved sum = conserved thrust), displacements
   `consistent`. CalculiX provides only nodes (no connectivity), hence RBF.
   preCICE 3.4 automatically picks the “partition-of-unity” variant.
4. **Time step.** The same in both solvers: preCICE window = `DELTA_T`
   (`system/caseParams`) = `*DYNAMIC` increment in `fsi.inp` = 2.5 ms. Max. Courant
   number ~0.85 (at U = 0.2 m/s), at the tip corners.
5. **Numerical damping in CalculiX** (`*DYNAMIC, ALPHA=-0.2`, HHT scheme).
   Without it the undamped axial modes of the soft tail made Newton diverge – even
   without water. HHT damping ∝ (ω·Δt)³ – negligible in the 0.5–2 Hz band.

---

## 5. Running and timings (this machine)

```bash
source OpenFOAM/env.sh
cd OpenFOAM
python tools/check_results.py      # checks all criteria and refreshes the plots
```

| Stage | Command | Time |
|---|---|---|
| 0 | `cd 00-reference-flap/fluid-openfoam && ./run.sh -parallel` + in a second terminal `cd 00-reference-flap/solid-calculix && ./run.sh`; then `python tools/postprocess.py e0 00-reference-flap` | 34 s |
| 1 | `01-solid-only/run.sh` | ~10 s |
| 2 | `02-fluid-only/run_all.sh` (4 variants) | 7 min |
| 3 | `03-fsi-passive/run_all.sh` | 10 min (explicit 20 s, implicit 592 s) |
| 4 | `04-fsi-actuated/run_all.sh` | 16 min for 4 s; 8 s version: 80 min (in parallel with stage 5) |
| 5 | `05-fsi-inflow/run_all.sh` | 30 min per speed on its own; 2 h in parallel with stage 4 |
| 6 | `06-freq-sweep/run_all.sh` | f = 0.5 Hz (16 s): 102 min, 1.5 Hz: 22 min, 2 Hz: 16 min |
| 4–6 | `setsid nohup ./run_parallel.sh &` (two queues in parallel, logs in `logs/`) | 3 h 47 min |

Vorticity snapshots: `pvbatch tools/pv_snapshots.py 05-fsi-inflow/U0.1 e5_vorticity_U0.1 4`.
Manually in ParaView: open `<case>/fluid-openfoam/fluid-openfoam.foam`
(built-in reader), field `vorticity`, component Z, range e.g. ±20 1/s.
Ready-made GUI state: `FSI_CASE=05-fsi-inflow/U0.2 paraview --script=tools/pv_gui.py` – vorticity,
plus **force readouts that follow the animation time**: a text box with the water force on the
body (head + tail) and on the tail alone (total, pressure and viscous x/y, mN/m), the moment on
the tail about its root, and arrows of the total force at the body and tail centroids (black =
body, magenta = tail). Values come from `postProcessing/forcesBody` and `forcesTail`,
interpolated to the shown time. Play is slowed down (`PV_FRAMES_PER_STEP`, default 2 frames per
saved step); `PV_FONT` sets the text size.

New case (e.g. a different speed):
`tools/new-fsi-case.sh my-case --u 0.15 --p0 15000 --freq 1 --t-end 5 && my-case/run.sh`.

---

## 6. Results – what each plot shows

All forces per metre of span (2D model). Parameters = placeholders,
so the numbers are for comparisons, not predictions.

### Stage 0 – reference `e0_flap_tip.png`
Tip displacement of an elastic flap in a channel (official preCICE tutorial)
compared with the tutorial's reference results. Max. relative error
**0.83%**, on average 2.01 coupling iterations per window (reference 2.012):
the installation behaves exactly as for the preCICE authors.

### Stage 1 – tail alone `e1_tip_vs_pressure.png`
Tip deflection and angle under increasing pressure in chamber L or R (dry,
quasi-static, NLGEOM). Almost linear response, ~1.2 mm/kPa: at 20 kPa
**24 mm (16% L) and 9°**. L/R asymmetry 0.36%. Solid mesh convergence
(0.5/0.75/1.0 mm) – difference < 0.5%. Before this worked, the chamber had to be
divided into cells (NOTES.md, stage 1).

### Stage 2 – fluid alone `e2_mesh_convergence.png`, `e2_vorticity_fine_0.png`
Rigid body in a 0.2 m/s inflow: drag over time, mesh convergence and pressure
distribution. Mean drag **0.13 N/m** (~2/3 pressure, ~1/3 friction); change
between the medium and fine mesh 1.0%, a 1.5x domain changes the result by 3.8%.
Cp = 1 at the stagnation point on the nose. Vorticity snapshot: a classic
Kármán vortex street behind the blunt tip – a “drag” wake.

### Stage 3 – explicit vs implicit `e3_explicit_vs_implicit.png`
Passive tail in a stream. Implicit (IQN-ILS): 3 s without problems, on average
**4.7 coupling iterations** per window, the tail vibrates in the vortex wake (~0.15 mm).
Explicit: the force at the tip node changes sign and grows **×13 per window** – after 2
windows it is over. With **Δt = 1 ms it is worse: ×40 per window**. This is the
added mass effect: with silicone density ≈ water density, explicit coupling is
unstable for every time step (Causin, Gerbeau, Nobile 2005).

### Stage 4 – actuation in still water `e4_tip_angle_water_vs_dry.png`, `e4_thrust_cycle.png`
Tip angle under a sinusoidal pressure (P0 = 15 kPa, f = 1 Hz) in water and
dry. **In water the amplitude is larger** (28.3 vs 20.0 mm) and lags
by ~71°. The water adds mass and lowers the tail's natural frequency from 3.39 Hz
(dry) to around 1 Hz (stage 6), so the 1 Hz actuation hits the resonance in water.
The axial force oscillates ±4 N/m, and the mean thrust is **87 ± 99 mN/m** – not
distinguishable from zero. Quality of the deforming mesh: `meshq_04-fsi-actuated_water.png`
(at peak deflection non-orthogonality 63°, skewness 4.1 – the limit of the method).

### Stage 5 – actuation + inflow `e5_force_vs_inflow.png`, `e5_vorticity_U0.05_0.png`, `e5_vorticity_U0.2_0.png`
Mean X force on the whole body vs inflow speed (U = 0 is stage 4).
**The tail produces net drag**: +100, +292, +416 mN/m at 0.05 / 0.1 / 0.2 m/s;
at 0.2 m/s that is ~3x more than the rigid body. Balance (mean Fx = 0)
appears only at **U ≈ 0.02 m/s, i.e. St ≈ 2.4** – far outside the fish range
**St ≈ 0.2–0.4** (Taylor, Nudds, Thomas 2003, *Nature* 425:707–711;
Triantafyllou, Triantafyllou, Grosenbaugh 1993, *J. Fluids Struct.* 7:205–224).
Conclusion for the project: an actuator with two uniform chambers bends the tail
“in one phase” (standing wave) and has a blunt tip – in this model it pushes water
mainly sideways (lateral force ±8–13 N/m) instead of backwards. Directions to
check: a travelling wave (chambers phase-shifted along the tail), a sharp/
flexible caudal fin (NOTES.md, stage 5).

### Stage 6 – frequency sweep `e6_freq_sweep.png`
Amplitude and mean thrust vs frequency (still water, P0 = 15 kPa).
Amplitude: 20.7 / **28.3** / 14.8 / 3.1 mm at 0.5 / 1 / 1.5 / 2 Hz –
**resonance in water ~1 Hz**, above it the response drops quickly (the water mass
dominates). Thrust: 0 ± 5, 87 ± 99, −142 ± 61, −23 ± 32 mN/m – only at 1.5 Hz
is the result significant, and it is drag. Lesson: the operating frequency must be
chosen relative to the resonance *in water*, which for a soft tail lies ~3x lower than
dry.

### Vorticity field snapshots
`pvbatch tools/pv_snapshots.py <case> <name> [N]` – red = counter-clockwise
vortex, blue = clockwise. Manually in ParaView: open
`fluid-openfoam/fluid-openfoam.foam`, field `vorticity`, component Z, range ±20 1/s.

---

## 7. Model limitations

- **2D instead of 3D** – no fin-tip effects (edge vortices), forces per
  metre of span; in 3D the thrust per unit span will be smaller.
- **Laminar flow** at a realistically transitional/turbulent Re (section 3).
- **Fixed head** – no free swimming, recoil or head yaw;
  the “balance speed” from stage 5 is only an estimate for a tethered fish.
- **Pressure actuation**, not volume actuation (section 3).
- **Linear elastic material** (with NLGEOM); silicone at large strains
  is hyperelastic, and there is no material damping.
- **Limited amplitude** due to fluid mesh deformation (~15% L).
- **2D chambers** – in 3D the cells are connected by a channel; it is not visible in the cross-section.
- **Unidentified parameters** – every number is a placeholder.

## 8. How to use this in the project

- **Relative comparisons**, not absolute: the effect of fin geometry (taper,
  length, number of cells), stiffness (E) and frequency on thrust and amplitude.
  Change `tools/params.py`, generate a case with `new-fsi-case.sh`, compare.
- **Validation of the MuJoCo/SOFA models**: dry amplitude (stage 1/4 dry) and in water
  (stage 4), plus the averaged thrust (stages 4–6) as a reference point for simpler
  drag/added-mass models.
- **Tethered measurement plan in a tank**: head mounted on a force sensor
  (1-axis load cell), actuation with prescribed pressure and frequency, camera from
  above (tip angle). Measure: mean X force in still water (comparison with
  stage 4/6), tip amplitude dry and in water, and with flow (channel
  or towing) – the speed at which the mean force ≈ 0 (stage 5). From the measurements
  identify E and damping, and replace the placeholders.
