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

**Actuation changed (13.10.2026):** `make_actuation.py` now generates the chamber
pressure from a constant-speed pump + ±1 valve model (section 3). The valve holds
each state ≥ 0.2 s (≤ 5 switches/s), so the tail frequency is limited to
**1.5–2.5 Hz**; the stage 4–6 case setups were moved into that range (stages 4/5:
1 → 1.5 Hz, stage 6: 1.75 / 2 / 2.5 Hz). All FSI results below were computed with the
**old sinusoidal pressure at the old frequencies** (0.5 / 1 / 1.5 / 2 Hz) and have not
been re-run.

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
  06-freq-sweep/          FSI: f = 1.75 / 2 / 2.5 Hz (1.5 Hz = stage 4)
  tools/
    params.py             ALL physical and geometric parameters (placeholders)
    make_geometry.py      gmsh: 2D tail geometry with chambers -> CalculiX and OpenFOAM
    make_actuation.py     chamber pressure waveform (*AMPLITUDE/*DLOAD): valve model (default) or old sine
    test_make_actuation.py  quick checks of the valve model (python tools/test_make_actuation.py)
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
- Actuation: pressure on the cell walls (`*DLOAD` + `*AMPLITUDE`), from the
  **valve model** (default since 2026-10-13, see below): constant-speed pump
  with a constant flow `Q_const` + directional valves with only two states
  (s = ±1). p_L = max(0, Δp), p_R = max(0, −Δp). The old sine
  (p_L = P0·r(t)·max(0, sin 2πft), p_R = P0·r(t)·max(0, −sin 2πft)) is kept as
  `make_actuation.py --waveform sine`. Ramp r(t) over the first period in both.

### Actuation: constant pump + ±1 valves (valve model)

The real hardware is a pump with **constant speed and constant flow `Q_const`**
(replaces `Q_max` of the other demos) and directional valves that only choose the
flow direction: s = +1 (R→L) or s = −1 (L→R), there is no closed state.
`tools/make_actuation.py` simulates this before the run and writes the result as
the `*AMPLITUDE` table (1 ms sampling, CalculiX interpolates linearly):

    V_ref = r(t)·A_V·sin 2πft                     pumped-volume reference (as in the other demos)
    e = V_ref − V_p;  e > δ → s = +1;  e < −δ → s = −1;  otherwise s unchanged (start s = +1)
    the relay is ignored until t − t_switch ≥ valve_min_dwell = 0.2 s (valve ≤ 5 switches/s)
    dQ/dt = (s·Q_const − Q)/τ_valve,  dV_p/dt = Q
    Δp = clip(V_p/C_h, ±p_max)

**Volume → pressure.** This case prescribes pressure, so it had no volume–pressure
relation. We use the hydraulic spring of the other demos, Δp = (V_p − A_r·L)/C_h,
with a **rigid-tail assumption** (A_r·L = 0): one lumped stiffness 1/C_h, with
C_h = A_V/P0 = 5.3·10⁻¹⁰ m³/Pa by default (`--compliance`). A perfectly tracked
V_ref would then give exactly the old peak P0 = 15 kPa, so both waveforms are
comparable. The rigid-tail assumption ignores that a bending tail “makes room” for
fluid (it overestimates the pressure for a given volume); full volume coupling
would need the chamber volume from CalculiX at every step – not done.

Values (all PLACEHOLDER, as in MuJoCo): `Q_const` = 60 ml/s, A_V = 8 ml,
`tau_valve` = 20 ms, δ = 1 ml, p_max = 50 kPa, `valve_min_dwell` = 0.2 s. The 2D
model has no real chamber volume, so A_V and `Q_const` only set the ratio
**f_track = Q_const/(2π·A_V) ≈ 1.19 Hz**.

**Frequency range 1.5–2.5 Hz** (`TAIL_FREQ_MIN`, `TAIL_FREQ_MAX`). Below f_track the
relay would have to follow V_ref with a sawtooth (many switches per cycle), which a
valve limited to 5 switches/s cannot do; at 1.25 Hz the dwell-limited valve still
adds 1–2 extra switches per cycle, hence the minimum of 1.5 Hz (user decision, the same
on all demos). The maximum 1/(2·valve_min_dwell) = 2.5 Hz is 2 switches per cycle with
each state held 0.2 s. `make_actuation.py` **rejects** a valve-waveform frequency
outside the range with an error (no silent clamping – the case name and `case.txt`
would no longer match the actuation). P0 = 0 (passive) and `--waveform sine` are not
limited.

| f | valve switches / cycle | min. gap between switches | V_p amplitude (triangle Q_const/(4f)) | peak Δp (steady) |
|---|---|---|---|---|
| 1.5 Hz | 2.0 | 0.200 s | 9.2 ml (10.0) | 17.2 kPa |
| 1.75 Hz | 2.1 | 0.200 s | 7.7 ml (8.6) | 14.5 kPa |
| 2 Hz | 2.1 | 0.200 s | 6.7 ml (7.5) | 12.5 kPa |
| 2.25 Hz | 2.1 | 0.200 s | 5.8 ml (6.7) | 11.0 kPa |
| 2.5 Hz | 2.0 | 0.200 s | 5.2 ml (6.0) | 10.8 kPa |

(P0 = 15 kPa, 8 s; switches counted after the ramp; the ~2.1 includes the switches
during the start-up transient.) In the whole range the valve switches only at the
peaks, the volume and pressure are triangular, lag V_ref, and the amplitude falls
as 1/f (“end of tracking”, formerly “the pump saturates”). At exactly 2.5 Hz the
dwell equals half a period, so the switch times are locked to the dwell and the
triangle keeps a small constant offset (+0.6 ml, ≈ +1.1 kPa) left from the start-up.
The relief valve stays as a separate safeguard (not reached here, max. ≈ 17 kPa).

> **The FSI results in section 6 (stages 4–6) were computed with the OLD sinusoidal
> pressure at the old frequencies** (stages 4/5: 1 Hz, stage 6: 0.5 / 1.5 / 2 Hz;
> `--waveform sine`) and have not been re-run with the valve model or the new
> frequencies. To reproduce them, add `--waveform sine` and the old `--freq` to the
> `make_actuation.py` line in `solid-calculix/run.sh` (and restore the old end
> times: stage 6 f0.5 had T_END = 16 s). Expected differences with the valve model:
> triangular instead of sinusoidal pressure, a smaller and later stroke at higher f,
> and much weaker motion than at the old 1 Hz point, which sat on the resonance in
> water (~1 Hz, stage 6) – 1 Hz is now outside the valve range.

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
approximation; SOFA (the neighbouring demo) prescribes volume. The valve model
(above) gets closer: the pressure follows a pumped volume, but through a fixed
stiffness with a rigid tail, not through the actual chamber deformation.

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
   without water. HHT damping ∝ (ω·Δt)³ – negligible in the 0.5–2.5 Hz band.

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
| 6 | `06-freq-sweep/run_all.sh` | old sweep: f = 0.5 Hz (16 s): 102 min, 1.5 Hz: 22 min, 2 Hz: 16 min (new 1.75 / 2 / 2.5 Hz: 4.6 / 4 / 3.2 s, not run) |
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
`tools/new-fsi-case.sh my-case --u 0.15 --p0 15000 --freq 1.5 --t-end 5 && my-case/run.sh`
(valve waveform: f within 1.5–2.5 Hz).

---

## 6. Results – what each plot shows

All forces per metre of span (2D model). Parameters = placeholders,
so the numbers are for comparisons, not predictions. Stages 4–6 use the **old
sinusoidal pressure** (`--waveform sine`) at the **old frequencies** (0.5–2 Hz), not
the valve model and its 1.5–2.5 Hz range (section 3); the case directories now hold
the new setups (the old `06-freq-sweep/f0.5` and `f1.5` became `f2.5` and `f1.75`).

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
Tip angle under a sinusoidal pressure (old actuation, `--waveform sine`; P0 = 15 kPa, f = 1 Hz) in water and
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
Amplitude and mean thrust vs frequency (still water, P0 = 15 kPa, old sinusoidal
actuation at the old points 0.5 / 1 / 1.5 / 2 Hz – the valve range is now
1.5–2.5 Hz with a triangular, lagging pressure; the new sweep 1.5 / 1.75 / 2 / 2.5 Hz
has not been run). Note: the whole valve range lies **above the resonance in water
(~1 Hz)**, where the old sweep already showed a fast drop of amplitude.
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
- **Pressure actuation**, not volume actuation (section 3). The valve model
  converts pumped volume to pressure with a fixed stiffness and a rigid tail;
  the published FSI results still use the old sine.
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
