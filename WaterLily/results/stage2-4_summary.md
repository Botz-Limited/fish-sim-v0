# Stages 2–4 – valve-driven tail: tethered thrust, inflow sweep, frequency sweep

WaterLily 1.9.2, Julia 1.13.2, Float32, Re_sim = 5000 (on U_REF = 0.2 m/s, L_BODY = 0.21 m),
kinematic tail mode θ = V_p/A_r, box-restricted `measure!` (src/boxbody.jl) active for all runs
below. All physical parameters are PLACEHOLDERS. Forces are per unit span (2D): N/m.
Sign convention: F_x > 0 is drag (inflow in +x), thrust = −F_x.

Averaging: the valve start-up transient is discarded (window starts at ≥ 2 s **and** after the
valve has locked onto V_ref, see "Problems" 2), plus ≥ 1.5 flow-through times L_BODY/U with
inflow. Means are time-weighted over **6 whole tail cycles**; the "halves" columns are the
means over the first and the last 3 cycles (convergence check).

Scripts: `scripts/stage2_tethered.jl`, `scripts/stage3_inflow_sweep.jl`,
`scripts/stage4_freq_sweep.jl`, shared helpers `scripts/stage_common.jl`, parallel runner
`scripts/run_parallel.sh` (`-j JOBS -t THREADS SCRIPT CASE...`, then `SCRIPT report`).
All scripts accept `FISH_LIVE=1` (live viewer via `FishLily.maybe_live_hook`).

## Criteria

| Stage | Criterion (spec) | Result | |
|---|---|---|---|
| 2 | mean F_x is thrust (> 0) | mean thrust 1.47 N/m (halves 1.66 / 1.28) | **PASS** |
| 2 | 2 ± 0.2 valve switches per cycle | 2.00 | **PASS** |
| 3 | net thrust decreases with U, sign change exists | sign change between 0.30 and 0.40 m/s at n = 128 and 256; monotonic for U ≥ 0.10 m/s; 0.05 → 0.10 m/s is flat (−1.509 vs −1.513 N/m, inside the noise of the U = 0.05 run, halves −1.83 / −1.19) | **PASS** (with that remark; the script's strict check prints "NO" for n = 128) |
| 4 | St reported per f; runs independent → parallel | St 0.35–0.37 for all 5 f, run as separate processes | **PASS** |
| 4 | 2 switches/cycle at every f (extra check) | 2.00 at all f (after the f = 2.25 Hz window fix) | **PASS** |

## Stage 2 – tethered, still water, f = 2 Hz, n = 128 (832 × 384 cells)

`results/stage2_tethered.{csv,png}`, `results/stage2_vorticity.png`, `results/stage2_n128_timeseries.csv`

| quantity | value |
|---|---|
| averaging window | 2.0–5.0 s (6 cycles) |
| mean thrust −F_x | **1.473 N/m** (1st / 2nd half 1.664 / 1.284) |
| tail-only pressure thrust (x > root) | 1.426 N/m |
| mean F_y | 0.05 N/m (amplitude ≈ 191 N/m, dominated by the switch spikes) |
| tail pressure moment amplitude | 14.8 N·m/m (spikes) |
| θ peak-to-peak / mean | 0.667 rad / 0.000 rad |
| tip amplitude A_tip (p-p) | 60.0 mm |
| mean input power P (definition: stage 4) | 1.47 W/m |
| valve switches / cycle | 2.00 |
| CFD steps / wall | 4084 / 131 s (`-t 4`) |

The thrust time series is a train of spikes at the valve switches (≈ +35…+48 N/m, the
added-mass response to θ̈ ≈ 300 rad/s², NOTES item 9) with a weakly negative force between
them; the mean is a small difference of large numbers, hence the ±13 % difference of the two
halves. Vorticity snapshots at 4 phases of the last cycle show a reverse-Kármán-like jet of
vortex pairs going downstream (+x) and slightly to −y (the wake is deflected: a 2D tethered
still-water wake is not symmetric after 5 s), plus the starting vortices near the head.

## Stage 3 – inflow sweep, f = 2 Hz

`results/stage3_inflow_sweep.{csv,png}`, `results/stage3_Ustar.csv`, per case
`results/stage3_cases/*.csv` and `results/stage3_<case>_timeseries.csv`.
The spec range 0.05–0.30 m/s did **not** contain the sign change (n = 64 pre-check), so
U = 0.40 and 0.50 m/s were added. Rigid-fish runs: 8 L/U, averaged over the second half (as stage 1).

Mean F_x [N/m] (> 0 drag, < 0 net thrust):

| U [m/s] | flap n=128 | (halves) | flap n=256 | rigid n=128 | rigid n=256 | flap n=64 (pre-check) |
|---|---|---|---|---|---|---|
| 0.05 | −1.509 | −1.83 / −1.19 | | 0.0195 | | −1.657 |
| 0.10 | −1.513 | −1.53 / −1.50 | | 0.0542 | | −1.697 |
| 0.15 | −1.427 | −1.38 / −1.47 | | 0.0998 | | −1.609 |
| 0.20 | −1.085 | −0.93 / −1.24 | | 0.1568 | | −1.275 |
| 0.30 | −0.179 | −0.17 / −0.19 | **−0.026** | 0.3103 | 0.3279 | −0.272 |
| 0.40 | +0.382 | +0.36 / +0.41 | **+0.488** | 0.5055 | 0.5164 | +0.378 |
| 0.50 | +0.957 | +0.95 / +0.97 | | 0.7424 | | +1.080 |

Rigid C_D at U = 0.2 m/s, n = 128: 0.1568/(½ρU²L) = 0.0373 – identical to stage 1.

**Self-propelled speed (linear interpolation of mean F_x = 0):**

| n | U* [m/s] | bracket |
|---|---|---|
| 128 | **0.332** | 0.30–0.40 |
| 256 | **0.305** | 0.30–0.40 |

U* drops by 8 % from n = 128 to 256, and it is still biased **high**: the viscous drag is
under-predicted at finite resolution (stage 1: viscous part 0.0140 → 0.0178 for n = 128 → 256,
Blasius ≈ 0.0376 for the plate alone). The viscous part of F_x rises with n here as well
(flap U = 0.3: F_v,x 0.141 → 0.194 N/m), while the pressure part changes less. Expect U* to fall
further with resolution; a converged value is probably below 0.3 m/s. Note also
that the flapping fish has MORE drag than the rigid one at high U (at 0.5 m/s the "flap" F_x
exceeds the rigid drag): at St ≈ 0.24 the tail stroke is too slow to produce net thrust
there, and the bending body adds drag.

## Stage 4 – frequency sweep at U* = 0.332 m/s (n = 128)

`results/stage4_freq_sweep.{csv,png}`, per case `results/stage4_cases/*.csv`,
`results/stage4_f<f>_n128_timeseries.csv`.

| f [Hz] | F_x net [N/m] | A_tip p-p [mm] | St = f·A_tip/U* | P [W/m] | −M·θ̇ [W/m] | T [N/m] | η = T·U*/P | switches/cycle |
|---|---|---|---|---|---|---|---|---|
| 1.50 | +0.227 | 82.4 | 0.373 | 2.24 | 5.91 | 0.146 | 0.022 | 2.00 |
| 1.75 | +0.081 | 69.7 | 0.367 | 2.23 | 5.83 | 0.291 | 0.043 | 2.00 |
| 2.00 | +0.002 | 60.0 | 0.362 | 2.19 | 5.69 | 0.371 | 0.056 | 2.00 |
| 2.25 | −0.046 | 52.2 | 0.354 | 2.13 | 5.52 | 0.419 | **0.065** | 2.00 |
| 2.50 | +0.117 | 46.5 | 0.350 | 2.14 | 5.53 | 0.255 | 0.040 | 2.00 |

Definitions (documented in the script header):
- **P** = mean of −Q_θ·θ̇ = ∫ p (u_body·n) ds, pressure power the tail puts into the fluid.
  Q_θ = ∫ f_y h(x) ds is the generalized pressure force of the bending mode y = θ·h(x)
  (exactly conjugate to θ for this kinematics), θ̇ = Q/A_r exactly in kinematic mode.
  Viscous power neglected. The cross-check −M·θ̇ (tail moment about the root, i.e. a rigid
  flap rotating about the root) is 2.6× larger because it weights the forces with x instead of
  h(x) = x − 0.06 m on the distal part – it is not the right power for this bending shape.
- **T** = D_rigid(U*) − F_x,net: rigid-fish drag at U* from stage 3 (n = 128, interpolated:
  0.373 N/m) plus the measured net thrust. At U* the net force is ≈ 0, so the net thrust
  alone cannot be used. Assumes the flapping body has the rigid body's drag (it does not
  exactly – see stage 3 – so η is indicative).
- The requested alternative "pressure thrust on the tail" (x > root, p∞ = 0 at the inlet) is
  logged as `T_tail_p` / `eta_tail_p`, but it is **negative** at 4 of 5 frequencies (the open
  cut at the root and the tail's own pressure drag dominate), so it is not used as thrust.

Observations: St is almost independent of f (0.35–0.37) because the valve produces a triangle
wave whose amplitude is ∝ Q_const/f (A_tip 82 → 47 mm), so f·A_tip ≈ const. The power is also
almost flat (2.1–2.2 W/m). Thrust and efficiency peak at **2.25 Hz** (η ≈ 6.5 %); 2.5 Hz is
worse (the valve has a permanent +0.03 rad bias there, NOTES item 8, and the amplitude is
smallest). The low η (a few %) reflects the valve's triangle/jerk kinematics (large reactive
spikes, P counts their dissipated part) and the 2D, Re_sim = 5000 set-up; it is not a
quantitative prediction. Consistency: at f = 2 Hz and U* the net force is +0.002 N/m ≈ 0.

## Wall times (machine shared with 4 other agents; `-t 2` per process unless noted)

| run | wall |
|---|---|
| stage 2, n = 128 (`-t 4`) | 131 s (4084 steps) |
| stage 3, n = 128: 7 flap + 7 rigid, 2 jobs × 2 threads | 17.6 min total (flap 120–280 s, rigid 28–255 s each) |
| stage 3, n = 256: 2 flap + 2 rigid, 1 job × 2 threads | 28.7 min total (flap 775 / 596 s, rigid 171 / 131 s) |
| stage 4, n = 128: 5 f, 1 job × 2 threads (parallel to the n = 256 runs) | 21.7 min + 4 min rerun of f = 2.25 Hz (221–283 s each) |
| n = 64 pre-checks | 20–55 s per case |

## Problems found

1. **Garbage pressure in (nearly) solid cells – src/WaterLily issue, worked around in the
   scripts, not fixed in src.** With a moving body, cells deep inside the body have a
   (nearly) singular row in the pressure Poisson matrix: D = Σ face μ₀ is 0 or ≈ 3e-11
   (WaterLily's `μ₀(d,ϵ)` only cuts off below d/ϵ < −1 + √eps, which for Float32 leaves
   μ₀ ≈ 3e-11). Their pressure grows to 1e6–1e12 (grid units) and stays between steps; when the
   tail moves and such a cell gets bigger coefficients, the stale value is a huge residual
   for the next solve. Effects seen at n = 64: F_x jumps to 1e3–1e8 N/m (still water at
   t ≈ 3.8 s; U = 0.3 m/s at 3.5–4 s), and at U = 0.05 m/s the flow itself was corrupted
   (Δt collapsed, 26 k instead of 3.3 k steps). The fluid pressure level also random-walks.
   Workaround in `scripts/stage_common.jl` (`pressure_fix!`, run after every step as an
   `on_frame` hook): re-level p to the mean of the inlet-side column (p∞ = 0) and set p = 0
   in cells with |D| < 1e-4 (fluid cells have |D| ≈ 4; those cells lie ≥ 0.95 cells inside
   the surface, force-kernel weight < 0.6 %). After it no spikes beyond the physical switch
   spikes in any run. **Suggested src fix:** do the same inside `run_fish!` for moving
   bodies, or zero μ₀ below ~1e-4 in the box measure. The stage 5 free-swimming runs
   (|F_y| > 1000 spikes in the other agent's debug files) may be the same issue.
2. **Valve lock-in at 2.25 Hz takes 3.1 s, not 1.2–1.5 s.** From the pure valve model the
   switches are regular (within 5 % of a half period) only after t = 1.21 / 1.05 / 1.94 /
   3.07 / 0.77 s at f = 1.5 / 1.75 / 2 / 2.25 / 2.5 Hz. The first f = 2.25 Hz run (window from
   2.2 s) gave 2.17 switches/cycle and inconsistent halves (−0.50 / −0.02 N/m); the window now
   starts after `valve_lock_time(f)` (helper in stage_common.jl) and the rerun gives 2.00.
   NOTES item 8 ("discard ~2 s") should say "≥ 3.1 s at 2.25 Hz".
3. **U* outside the spec's inflow range** (0.05–0.3 m/s): 0.40 and 0.50 m/s were added.
4. The tail-only pressure x-force is not a usable thrust (negative), see stage 4.
5. zsh does not split `$cases` – call `run_parallel.sh` with explicit arguments or from bash.

## Caveats

- 2D section, Re_sim = 5000 (not 4.2e4), kinematic tail (no fluid feedback on θ), Float32.
- U* is biased high by the under-resolved viscous drag; n = 256 lowers it by 8 % and it is not
  converged. Report it as "≈ 0.3 m/s, upper bound", not as a prediction.
- Still-water thrust (stage 2) is a mean of large switch spikes; the two halves differ by
  ±13 %. n = 64 gave 1.54 N/m vs 1.47 N/m at n = 128.
- Stage 4 at n = 128 only; the U* used is the n = 128 value (0.332 m/s).
- η uses the rigid-body drag as the thrust at self-propulsion and the pressure power only.
- Blockage: side walls at ±1.5 L (stage 1: domain effect on drag ≈ 2 %).
