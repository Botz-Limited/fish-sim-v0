# NOTES – diagnosis log

What diverged / did not work, why, and how it was fixed. Newest at the bottom.

## Stage 1 – a single long chamber "balloons" (2026-10-06)

**Symptom.** First version: one chamber of 100 mm × ~4–11 mm on each side.
Pressure ramp in chamber L: at ~0.5 kPa the tip moved by −20 mm
along x (shortening!) and +11 mm in y (bending *towards* the pressurised chamber),
then `*ERROR: increment size smaller than minimum`.

**Diagnosis.** The outer wall (3 mm) between the chamber ends is a beam with a
100 mm span loaded by pressure. Deflection of a clamped beam:
w = p·l⁴ / (384·E·I), I = t³/12 (per metre of depth).
For p = 500 Pa, l = 0.1 m, E = 3e5 Pa, t = 3 mm: w ≈ 0.19 m – the wall bulges
like a membrane. The bulging wall pulls the chamber ends together (McKibben
muscle effect), so the pressurised side *shortens*. In 3D, real actuators
prevent this with ribs (PneuNet) or a fibre braid (SOFA demo).

**Fix.** The chamber is split into cells by ribs (`N_CELLS`, `RIB` in
`tools/params.py`). The wall span drops from 100 mm to ~8.6 mm, so the
deflection ∝ l⁴ drops ~18 000 times. The cells are connected by a channel
outside the cross-section plane (same pressure).

## Stage 1 – collapse of the middle wall (2026-10-06)

**Symptom.** 6 cells of 15 mm, middle wall 2 mm: bending now in the right
direction, but loss of convergence at ~16 kPa, tip deflection only 11 mm.

**Diagnosis.** The same formula for the middle wall (t = 2 mm, l = 15 mm,
p = 16 kPa) gives w ≈ 10 mm – more than the height of the neighbouring chamber. The wall
collapses into the empty chamber on the other side, and the model has no contact.

**Fix.** 10 cells of 8.65 mm, ribs 1.5 mm, middle wall 3 mm
(w ≈ 0.35 mm). Result: nearly linear response ~1.2 mm/kPa, 24 mm (16% L)
at 20 kPa. Convergence is lost only above ~21 kPa, so the working range
is 0–20 kPa (`P_MAX`).

## Stage 1 – solid mesh convergence (2026-10-06)

Tip deflection at 20 kPa (chamber L) for element size h:
h = 0.5 mm: 24.31 mm (8152 el.), 0.75 mm: 24.20 mm (3596 el.), 1.0 mm: 24.29 mm (2559 el.).
Spread < 0.5%, so h = 1.0 mm was chosen – CalculiX is the most expensive part of
every coupling iteration, and fewer elements = shorter FSI runs.

## Stage 0 – FPE in preCICE with Eigen 5 (2026-10-06)

**Symptom.** The reference perpendicular-flap crashed after the 1st step: `Floating point
exception` in the OpenFOAM processes, stack: `Eigen::internal::triSolveKernelLxK` <-
`RadialBasisFctSolver<CompactPolynomialC6>::solveConsistent` (RBF mapping).

**Diagnosis.** Arch ships Eigen 5.0.1, and preCICE 3.4 picks Eigen 5 if
it is available. The new vectorised triangular-solve kernel in
Eigen 5 raises a floating-point exception flag, and OpenFOAM by default
traps such exceptions (FOAM_SIGFPE) and aborts the run.

**Fix.** preCICE rebuilt with Eigen 3.4.0 (the version used in the
official preCICE .deb packages). The FPE trap in OpenFOAM stays enabled,
because it is useful when coupling diverges (a NaN stops the run
immediately). Alternative (worse): `export FOAM_SIGFPE=false`.

After the fix: perpendicular-flap matches the tutorial reference (max. relative
tip displacement error 0.83%, on average 2.01 coupling iterations per
window vs 2.012 in the reference). Time: 34 s (fluid 4 MPI processes, CalculiX 2 threads).

## CalculiX performance – PARDISO instead of SPOOLES (2026-10-06)

CalculiX is the most expensive part of every coupling iteration (fluid ~20 ms/step on
4 processes, solid ~3–4 Newton iterations per increment). Test: 20
dynamic increments, NLGEOM, 2559 el. C3D8I, time per Newton iteration:

| threads | SPOOLES | PARDISO (MKL) |
|---|---|---|
| 1 | 158 ms | 123 ms |
| 2 | 130 ms | 81 ms |
| 4 | 121 ms (**wrong result!**) | 69 ms |

Multi-threaded SPOOLES with 4 threads gave a different (wrong) tip
deflection (−3.4 mm instead of −7.9 mm) and converged in a different number of iterations –
a known SPOOLES MT problem. PARDISO gives identical results for 1/2/4 threads.
CalculiX's iterative solvers were ~15–20x slower.

Decision: `ccx_preCICE` built with PARDISO (MKL from `pip install mkl-devel` into the
venv – no sudo), 2 threads. The old version is kept as `ccx_preCICE_spooles`.

## Stage 3 – CalculiX diverges already in the 2nd FSI window (2026-10-06)

**Symptom.** First FSI test (passive tail, U = 0.2 m/s): window 1 converges
(23 coupling iterations), in window 2 CalculiX does not converge in the Newton loop
("largest correction to disp 7.8e-2"), then `corrupted double-linked list`.

**Diagnosis.** The VTU export from preCICE showed that the interface forces are
physical (−1.4 N/m in window 1, −51 N/m in window 2 – the jump is the added-mass effect:
moving the wall by 2e-5 m in one step produces a large pressure). Test without
preCICE: the same load (−51 N/m as nodal forces on Nsurface) in a
dynamic step with NLGEOM also diverges. Test matrix:

| variant | result |
|---|---|
| C3D8I + NLGEOM (original) | divergence |
| C3D8I without NLGEOM | convergence |
| C3D8I + NLGEOM, force 10x smaller | convergence, but slow |
| C3D8 + NLGEOM | convergence |
| SPOOLES instead of PARDISO / ALPHA = −0.1 | divergence (not the solver) |

The culprits are the incompatible-mode elements (C3D8I – expanded in CalculiX into
extra massless nodes) combined with NLGEOM and nodal forces; the largest
corrections appeared exactly in those extra nodes.

**Fix.** C3D8 elements (full integration). Shear-locking check
on stage 1 (20 kPa): C3D8I 24.28 mm, C3D8 24.14 mm (−0.6%), C3D8R 24.63 mm.
The difference is negligible, and C3D8 is ~2x faster.

## Stage 3/4 – CalculiX diverging in longer runs (2026-10-06)

**Symptom.** Implicit stage 3 crashed in window 44 (t = 0.11 s): in one coupling
iteration the interface force jumps ~1000x, Newton in CalculiX does not converge
(residuals of 77 kN at one node), then `corrupted double-linked list`.

**Diagnosis.**
1. Acceleration tests on a short run (0.2 s): IQN-ILS as in the tutorial
   (QR2 1e-2, relaxation 0.5) – crash in window 66; IQN-IMVJ – crash in window 58.
   Changing the acceleration does not help.
2. Key test: stage 4 "dry" (CalculiX alone, without water and without preCICE)
   also diverged at t = 1.58 s – the number of Newton iterations jumped 4/9/4/9.
   So the problem lies in the dynamics of the solid itself: Newmark scheme without
   damping (ALPHA = 0) + NLGEOM + very soft material – the axial modes
   (~30 Hz, period ~12 steps) are not damped and "rock" the iterations.

**Fix.** `*DYNAMIC, ALPHA=-0.2` (HHT scheme). Short FSI test: 79/79
windows without errors; "dry": the full 4 s (previously crashed at 1.58 s).
HHT numerical damping ∝ (ω·Δt)³: for 1 Hz and Δt = 2.5 ms practically zero,
so it does not change the response in the actuation band. Real silicone has
material damping anyway, which the model does not include.

## Stage 3 – result: explicit vs implicit (2026-10-06)

- **Implicit** (parallel-implicit + IQN-ILS): 1200 windows (3 s) in 592 s,
  on average 4.7 coupling iterations per window, max. 17 (only at the start, before
  IQN builds up history). The tail vibrates in the vortex wake, amplitude grows to ~0.15 mm.
- **Explicit** (serial-explicit): the force at the tip node changes sign and grows
  ×13 per window (Δt = 2.5 ms); after 2 windows CalculiX diverges.
- **Explicit with Δt = 1 ms: ×40 per window** – a smaller time step makes things worse.
  This is the classic result for the added-mass instability (Causin, Gerbeau, Nobile
  2005, CMAME 194): with solid density ~ fluid density the explicit scheme is
  unstable for every Δt, and the amplification factor grows as Δt decreases.

## Stage 4 – post-processing trap: forces from every iteration (2026-10-06)

**Symptom.** Plot of the tail force Fx: oscillations of ±300 N/m at
~20–25 Hz in bursts every half period, "thrust" 5.4 N/m – 40x more than the drag
of the whole body at 0.2 m/s from stage 2.

**Diagnosis.** The spectrum gave infinite frequencies (division by Δt = 0):
in `postProcessing/forces*/0/force.dat` each instant appears several times.
With implicit coupling the adapter rewinds OpenFOAM to the checkpoint and the step
is recomputed in every coupling iteration – and the `forces` function
writes a row every time, including for non-converged iterations.

**Fix.** `read_forces()` keeps the last row for each instant
(= the converged value). After the fix: force ±3.7 N/m, no 20 Hz oscillations.
Second fix: thrust computed from the force on the **whole** body (head + tail) – the
tail alone is not a closed surface, so its Fx depends on the pressure
reference level.

## Stage 4 – amplitude in water LARGER than dry (2026-10-06)

At f = 1 Hz, P0 = 15 kPa: dry 20.7 mm, in water 26.5 mm, phase
lag in water 62° (dry ~0°). The spec assumed "water damps", but this depends
on the frequency relative to resonance:
- dry f₁ = 3.39 Hz (CalculiX, `*FREQUENCY`), so 1 Hz is
  quasi-static operation (amplification ~1.1),
- added mass lowers the natural frequency; 2D estimate (added mass ~6x the tail
  mass): f₁,water ≈ 3.39/√7 ≈ 1.3 Hz – 1 Hz actuation is close to the resonance in water,
  so the amplitude grows and the phase shifts towards 90°.
Water at the same time damps (energy leaves into the vortex wake) and "delays" the motion –
this is visible in the phase. The frequency sweep (stage 6) shows the trend.

The mean thrust in still water is small and after 3 periods had not yet
settled (cycle means: −12.6, −467.5, −91.9, +78.4 mN/m – large thrust
from the starting vortex, then decay). That is why stages 4 and 6 were recomputed with
8 periods.

## Stage 4 – quality of the deforming fluid mesh (2026-10-06)

`python tools/postprocess.py meshq 04-fsi-actuated/water` (checkMesh at every
write): at the largest deflection (tip angle 13.5°, deflection 26.5 mm =
18% L, t ≈ 1.9 s) max. non-orthogonality 63° (checkMesh threshold 70°), max.
skewness 4.1 (threshold 4), min. cell volume drops from 3.1e-7 to 1.7e-7 m³ –
no negative volumes. This is the practical limit of Laplacian mesh deformation
for this geometry: larger amplitudes (higher P0 or closer to
resonance) require remeshing or overset meshes.

## Stage 5 – actuation gives net drag; balance only at U ≈ 0.02 m/s (2026-10-07)

Mean Fx of the whole body (cycles from t = 2 s, ± standard error of the cycle means):
U = 0 (stage 4): −87 ± 99, U = 0.05: +100 ± 32, U = 0.1: +292 ± 14,
U = 0.2: +416 ± 18 mN/m. For comparison, rigid body at 0.2 m/s: +132 mN/m.

- Flapping **increases** drag ~3x (at 0.2 m/s): pressure part 338 vs 86
  mN/m, friction 66 vs 44 mN/m (thinner boundary layer during lateral motion –
  Bone–Lighthill effect).
- The lateral force has a std. deviation of 8–13 N/m, i.e. ~30x more than the mean
  axial force: the tail mainly "pushes" water sideways.
- Balance (mean Fx = 0) from interpolation: U ≈ 0.023 m/s, St ≈ 2.4 – far
  outside the fish range of 0.2–0.4. Large uncertainty: in still water the spread
  of the cycle means is ±230 mN/m.

**Interpretation (hypothesis, not fully verified).** An actuator with two
uniform chambers bends the tail like a cantilever: the whole tail deflects in one
phase (standing wave), the tip is blunt (10 mm), and the rigid head is
fixed. Fish produce thrust with a wave travelling along the body and a sharp, flexible
caudal fin with the right phase of deflection and angle of attack. Directions to
check in the model: chambers driven with a phase shift along the length
(travelling wave), a thinner/sharp tip or a separate flexible caudal fin,
higher frequency. The model limitations (2D, laminar) may also overestimate
drag.

Visualisation: at U = 0.2 m/s the wake is a single row of vortices close to the axis; at
U = 0.05 m/s (St ≈ 1.1) the wake is asymmetric and deflected downwards – typical for
very large St.

Fix along the way: `pv_snapshots.py` was colouring the magnitude of the vorticity vector (only
positive values) – `VectorMode = "Component"` must be set explicitly.

## Stage 6 – resonance in water ~1 Hz (2026-10-07)

Tip amplitude (mean of the half peak-to-peak ranges over the last 2 periods):
0.5 Hz: 20.7 mm, 1 Hz: 28.3 mm, 1.5 Hz: 14.8 mm, 2 Hz: 3.1 mm. Maximum at
1 Hz – the resonance in water is lower than the earlier estimate of 1.3 Hz, i.e.
the added mass in 2D is ~10x the tail mass ((3.39/1)² − 1), not ~6x.
Mean thrust (cycles from t = 2/f): 0 ± 5, 87 ± 99, −142 ± 61, −23 ± 32 mN/m –
only the drag at 1.5 Hz is significant.

Note on the definition: the amplitude was previously computed as half the range over
the single last period (stage 4: 25.8 mm), now as the mean over the last 2 periods
(28.3 mm) – the same definition for water and "dry" and in all stages.
