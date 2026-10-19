# NOTES – FishLily core, stages 0–1

Working notes: problems found, how they were solved, measured wall times.
Machine: 12-thread CPU shared with other jobs; every run used `julia -t 4`,
WaterLily 1.9.2, Julia 1.13.2, Float32.

## Layout

- `Project.toml` is now the **FishLily package** (added `name`/`uuid`/`version`),
  so `julia --project=. -e 'using FishLily'` works and
  `julia --project=. -e 'using Pkg; Pkg.test()'` runs `test/runtests.jl`.
  No packages were added.
- `src/FishLily.jl` includes `params.jl`, `units.jl`, `valve.jl`, `boxbody.jl`,
  `geometry.jl`, `forces.jl`, `progress.jl`, `live.jl`, `sim.jl`.
- Live viewer / MP4 of the fish: `FISH_LIVE=1` for any script using `run_fish!`,
  `scripts/live.jl`, `scripts/animate.jl`; see viz/README.md ("The fish").
- `scripts/stage0_validation.jl`, `scripts/stage1_rigid_fish.jl`, `scripts/progress.jl`.

## Problems and solutions

1. **Ellipse SDF near the nose.** The first-order formula `k0(k0−1)/k1` gave
   |∇sdf| up to 1.18 at 2 mm inside the slender nose (radius of curvature
   b²/a = 3.75 mm). Replaced it with a 4-iteration closest-point method on the
   ellipse (practically exact). Now the test |∇sdf| ≈ 1 ± 0.12 within 2 mm of
   the surface passes everywhere, for straight and bent (θ ≤ 0.5 rad) fish.
2. **Tail taper.** The tail is an "uneven capsule" (exact SDF): root circle
   r = 15 mm, tip circle r = 5 mm centred at 145 mm, so the rounded tip ends at
   exactly L_TAIL. With tangent lines between the circles, the thickness is
   ≤ 4 % below the linear 30 → 10 mm taper (test tolerance 5 %).
3. **Bending map.** `y = θ·h(x)` with uniform curvature on the chamber region
   (x = 10…110 mm, ξ = 0.067…0.733) and a straight distal part, so
   h(L_TAIL) = 0.09 m and the tip displacement is θ·0.09 m. The inverse map is
   one Gauss–Newton step to the foot point on the midline and the
   distance normal to the tangent there, so the thickness is measured normal
   to the midline. The lateral offset used in that step is clamped (±30 mm)
   so the far field is not distorted (the far-field pseudo-SDF only
   underestimates the distance, never puts body where there is none).
4. **Time step in still water.** WaterLily's CFL only uses the fluid velocity:
   in still water the first steps would be Δt = 10 grid units (≈ 0.3 s of tail
   motion at n = 32). `run_fish!` caps Δt (`dt_max = 0.4` cells/U, default).
   With inflow the CFL and the cap are about equal.
5. **Body motion between CFD steps.** WaterLily measures the body at the END
   of a step (t₁ = sum(Δt)) and computes the body velocity by differentiating
   the map in time. The valve is therefore advanced to t₁ before each step and
   θ(t) is fed through a piecewise-linear `Track` (θ₀ at t₀ → θ₁ at t₁), so
   position and velocity of the body are consistent over the step.
6. **Force sign.** WaterLily's `pressure_force`/`viscous_force`/`total_force`
   return ∫τ·n ds with the outward normal, i.e. MINUS the force on the body
   (checked with a hydrostatic field: test "force sign/scale" reproduces
   −area·ê_y within 3 %). `body_force` returns the force on the body.
   `Fx > 0` = drag (inflow is +x); `thrust = −Fx`.
7. **Tail moment.** `tail_pressure_moment` integrates −p (r × n) only over
   the surface with x > x_root (the head is excluded), CCW positive. It uses
   `flow.σ` as scratch (free between steps).
8. **Valve start-up transient (port fidelity, not changed).** The valve model
   (identical to MuJoCo / OpenFOAM) needs ≈ 1.2–1.5 s after start before the
   switches lock onto the V_ref peaks: in that time the valve switches at the
   dwell limit and V_p (hence θ) has a mean offset of −0.14 … −0.21 rad
   (f = 2 Hz). After it the mean is ≈ 0 at 1.5 and 2 Hz, but a permanent bias
   of +0.031 rad remains at 2.5 Hz. Consequence for stages 2–4: discard at
   least the first ~2 s (not just the 1-period ramp) when averaging.
9. **Added-mass force spikes.** At each valve switch dQ/dt is large
   (θ̈ ≈ 2Q_const/(A_r·τ_valve) ≈ 300 rad/s²), which gives lateral force
   spikes of ≈ ±180 N/m (n = 128, still water). Physical for this valve model
   (consistent with an added-mass estimate ≈ 100–200 N/m), not a numerical
   problem; use cycle averages for thrust.
10. **`update!` name clash.** WaterLily exports `update!` (MeanFlow);
    the progress functions are called `progress_update!`/`progress_finish!`.

## Stage 0 – circle Re = 100 (domain 24D × 12D, centre 6D from inlet, average t U/D ≥ 60)

| D [cells] | C_D | C_D pressure | C_D viscous | St | wall [s] |
|---|---|---|---|---|---|
| 16 | 1.248 | 1.072 | 0.176 | 0.174 | 16 |
| 32 | 1.266 | 1.055 | 0.211 | 0.175 | 104 |
| 64 | 1.286 | 1.055 | 0.231 | 0.174 | 1196 |

Criteria at the finest D = 64: **St 0.174 PASS** (0.15–0.18), **C_D 1.286
FAIL** (1.3–1.45; 1 % below the band).

Diagnosis: the pressure part is converged (1.055 at D = 32 and 64), the
viscous part is not (0.176 → 0.211 → 0.231). Richardson extrapolation of the
viscous part (ratio of increments 0.57) gives ≈ 0.257, i.e. C_D ≈ 1.31 at
infinite resolution – inside the band, so the solver itself is fine; the
finite-resolution viscous force read-out is what fails the criterion.
Literature total for an unconfined cylinder at Re = 100 is ≈ 1.33–1.35 (e.g.
Park et al. 1998: 1.33), of which roughly a quarter is skin friction; the
pressure part here is already ≈ 1.0–1.05, so the missing ≈ 0.1 is mostly the
viscous part (0.21 here, expected ≈ 0.3; literature split quoted from memory,
not re-checked). The
viscous force is read from the strain rate on the BDIM-smeared interface,
which converges slowly (+0.02 in C_D per doubling of D, not geometric).
A larger domain (32D × 24D, D = 32, separate diagnostic run to t = 80) lowers C_D to 1.213 (pressure 1.009,
viscous 0.205): the 24D × 12D box adds ≈ 0.05 by blockage, which partly hides
the viscous deficit. The criterion is reported as failed, not loosened.

## Stage 1 – rigid fish, U_REF = 0.2 m/s, Re_sim = 5000 (t = 8.4 s, average t ≥ 4.2 s)

| case | n | grid | C_D | C_D p | C_D v | steps | wall [s] |
|---|---|---|---|---|---|---|---|
| default domain | 64 | 416×192 | 0.0376 | 0.0273 | 0.0103 | 1280 | 8.9 |
| default domain | 128 | 832×384 | 0.0373 | 0.0233 | 0.0140 | 2560 | 35.4 |
| default domain | 256 | 1664×768 | 0.0409 | 0.0231 | 0.0178 | 5120 | 280.7 |
| large domain (3/8/3 L) | 128 | 1536×768 | 0.0366 | 0.0228 | 0.0138 | 2560 | 127.3 |

C_D change n = 128 → 256: **8.6 % – FAIL** (< 5 % required). Domain: default
(1.5 L upstream, 4 L downstream, ±1.5 L) → large changes C_D by 2.0 %.

Diagnosis: the **pressure part is converged** (0.0233 → 0.0231, −1 %); the
**viscous part is not** (0.0103 → 0.0140 → 0.0178), still far below the
Blasius flat-plate value 2·1.328/√5000 = 0.0376. At Re_sim = 5000 the
boundary layer is δ ≈ 5L/√Re ≈ 0.07 L thick at the trailing edge, i.e. a few
cells (and much thinner near the nose), while BDIM smears the interface over
±1 cell. Check at Re_sim = 1000 (`RE_SIM=1000`, results/stage1_rigid_fish_Re1000.*):
C_D = 0.0838 / 0.0909 / 0.0975 for n = 64/128/256 (change 6.7 %, still FAIL);
pressure part 0.0419/0.0409/0.0415 converged, viscous 0.042/0.050/0.056
converging slowly (≈ first order). So the slow convergence is the viscous
force on the immersed boundary, not just the Reynolds number.

Consequences / options (not applied, need a decision):
- Thrust and lateral forces of the flapping tail (stages 2–4) are pressure
  dominated → expected to be much better converged than the rigid-body drag.
- The self-propelled speed U* (stage 3) and the free-swimming speed (stage 5)
  depend on the body drag, which is underestimated (viscous part) → U* will be
  biased high. Recommend: report U* at n = 128 and 256, or add a skin-friction
  correction (e.g. Blasius/ITTC for the viscous part) clearly marked.
- Alternatives: a control-volume momentum balance for the drag; n = 512 for a
  single rigid case (≈ 5 M cells, est. > 40 min with 4 threads).

## Wall times (4 threads)

- tests (`Pkg.test()`): ≈ 15 s incl. load, of which the CFD smoke test ≈ 8 s.
- stage 0: 16 / 32 / 64 cells per D: 16 s / 104 s / 1196 s (total 22 min; a first run took 24 min).
  At D = 64 Δt is limited by viscosity (5ν term in the CFL), ≈ 38 k steps.
- stage 1: n = 64 / 128 / 256: 8 s / 33 s / 267 s, large domain n = 128: 122 s
  (total 7.3 min; first run 7.7 min). Re_sim = 1000 check (n = 64/128/256): 9 s / 35 s / 300 s. Rigid body: `remeasure=false`, forces every 4th step.
- moving tail (valve, still water, n = 128, 834×386 cells): 528 steps for
  0.8 s of physical time in 42 s (≈ 12.5 steps/s ≈ 53 s wall per physical
  second) – ≈ 6× slower per step than the rigid body, because the AutoBody is
  re-measured over the whole domain every step (map + ForwardDiff) and the
  forces + tail moment cost three more full-domain passes. **Fixed, see
  "Box-restricted measure" below (≈ 7× faster).**

## Box-restricted measure (performance)

`fish_body` now returns a `BoxedBody` (src/boxbody.jl) wrapping the AutoBody
with a grid box around the fish: nose…tip (+ x-shift of the bent tip),
y from the axis to θ·h(L_TAIL), ± root half-thickness, + (2+ϵ) + 4 cells,
following θ(t) and X(t). `WaterLily.measure!` is specialised for it: the
far-field reset (μ₀=1, μ₁=0, V=0) is done only on the union of the old and
new box (so cells a moving body has left are cleaned), the SDF and the BDIM
fill (verbatim WaterLily 1.9.2 code) only inside the new box, then the same
BCs. A self-check grows the box (and counts it in `body.regrow[]`) if any
cell on the box edge is still in the band, so a too-small box cannot cut the
body. `WaterLily.bbox` (the hook WaterLily's own force integrals use) returns
the box, so `pressure_force`/`viscous_force`/`tail_pressure_moment` also only
loop over it; outside the box `nds = 0` exactly. `flow.σ` is only valid in
the box after measuring – WaterLily uses it purely as scratch.
`make_fish_sim(...; box=false)` / `fish_body(...; box=false)` gives the old
full-domain AutoBody.

Equality (ValveDriver f = 2 Hz, n = 128, 50 steps, Float32): forces Fx, Fy, M,
Fpx, Fvx and the final fields u, p, μ₀, μ₁, V are **bit-identical** to the
full measure, both for the fixed body in still water and for a body moving
with X(t) = −0.3 m/s · t at U_in = 0.2 m/s (box moved by 18 cells). Test
"box-restricted measure == full measure" in test/runtests.jl (n = 48, 30 steps,
both cases) checks the same with `==`. Box self-check never triggered.

Speed, still water, ValveDriver 2 Hz, forces + tail moment every step,
`julia -t 2`, machine shared with other jobs:

| n | full measure | box | speed-up | rigid (no remeasure) |
|---|---|---|---|---|
| 128 (834×386) | 7.2 steps/s | 55.1 steps/s | 7.7× | 88.6 steps/s |
| 256 (1664×768) | 1.9 steps/s | 12.1 steps/s | 6.4× | 18.1 steps/s |

Remaining per-step cost at n = 256 (ms): measure 3.1, Poisson
coefficient update 3.1, readouts 6.6, `mom_step!` 60 (the flow solve; with a
moving body the pressure solver needs more iterations than for the rigid one).

## Pressure spikes with a moving body (root cause + fix)

Symptom: rare ONE-step pressure-force spikes for a moving / deforming body at n = 128
(stage 5 free swim t = 0.769 s, Fx 8.2e3 / Fy −5.8e4 N/m; stage 6 coupled 2 Hz step 240,
t = 0.387 s; stage 6 `kin 2.0` blow-up at 4.19 s; 1.5 Hz n = 64 at 4.16 s), deterministic,
identical with `box=false`, not cured by `dt_max = 0.2`.

**Root cause: stale pressure in (nearly) solid cells of the Poisson system.** A cell deep
inside the body has a Poisson diagonal D = Σ face μ₀ that is exactly 0 or tiny (WaterLily
1.9.2's μ₀ kernel cuts off only at d < −1 + √eps, so in Float32 D ≈ 1e-11…1e-17). Its
pressure is not a solution of anything:
- D tiny → the Gauss–Seidel update r·iD (iD up to 1e16) makes it huge;
- D = 0 → the multigrid `prolongate!` + `increment!` still add the coarse correction to it
  every V-cycle, so it random-walks.
Harmless while the cell stays solid (zero coupling, zero force-kernel weight), but when the
moving body uncovers it, D jumps to 1e-3…1e-1 and the stale value is the initial guess of
the next solve: huge residual, the solver hits its 32-iteration cap, garbage pressure near the
surface for that step (the spike) and noise afterwards. The other hypotheses (Poisson cap
"by itself", Float32 coordinates, SDF quality, ForwardDiff body velocity, driver ordering)
are not needed: the spike disappears with the clean-up alone, everything else unchanged.

Evidence (stage 6 coupled 2 Hz n = 128, reproducer
`CoupledDriver` + `make_fish_sim(n=128, U_in=0)` stepped by hand, 16 s wall to step 240):

| step | cell (302,187) D | p there | pois.n (pred, corr) | Fx [N/m] | max abs p |
|---|---|---|---|---|---|
| 238 | 0 | 7.2 | 1, 1 | −2.3 | 5.6e7 (another solid cell, (255,199)) |
| 239 | −5.9e-17 (iD −1.7e16) | **3.7e11** | 2, 2 | −1.6 | 3.7e11 |
| 240 | −4.5e-3 (uncovered) | −4.9e3 | **32**, 7 | **79.5** (Fy −694) | 9.4e7 |

Before the spike max abs p in the domain was already 5.6e7 (grid units; fluid values ≈ 20),
all in cells with D = 0.

**Fix (src/sim.jl):** `clean_pressure!(sim; D_min=1e-4)` (exported) sets p = 0 in cells with
abs(D) < 1e-4 (fluid cells have abs(D) ≈ 4; these cells lie at d < −0.95 cells, force-kernel
weight < 0.6 %) and re-levels p to zero mean over the first inside column (inlet / left wall;
falls back to the mean over fluid cells). `run_fish!` calls it after every `sim_step!`,
before the readouts, keyword `pressure_fix` (default `nothing` = on exactly when the body is
re-measured, i.e. moving / deforming; rigid fixed body unchanged). This is the stage 2–4
`pressure_fix!` workaround moved into src; the hook in scripts/stage_common.jl is now a
no-op (a second application is not bit-exact in Float32 and makes the chaotic flow drift).

Results after the fix:
- stage 6 coupled 2 Hz n = 128, 0–5 s: max pois.n 3 (never 32), max abs Fx 33 N/m, max abs
  Fy 211 N/m, 0 spike rejections; t ≥ 2 s: thrust 0.75 N/m (n = 64: 1.21; spiky run: −14.5),
  θ half-amplitude 0.322 (kinematic 0.333). Before: spike at step 240, solver at 32 iterations.
- stage 5 n = 128, t ≤ 1 s (same domain, UPSTREAM = 15.6): max abs Fx 34.6 N/m, max abs Fy
  175 N/m, 0 guard rejections (before: 8.2e3 / 5.8e4 at 0.769 s).
- stage 2 n = 128 (4084 steps): flow bit-identical to the old hook run (same steps and Δt);
  readouts differ by at most 0.007 N/m (Fx) / 0.010 N/m (Fy); thrust mean 1.4731 unchanged,
  Fy_amp 191.301 → 191.304, M_amp 14.8445 → 14.8450. Stages 3–4 (same hook) likewise.
- stage 6 coupled 1.5 Hz n = 64, 0–5 s (J_a from stage6_ident_n128.csv, as the original run):
  without the clean-up the old failure is reproduced bit-exactly (θ = 1.50500 rad at
  t = 4.5516 s); with it: max pois.n 6, max abs Fx 40 N/m, 0 rejections, t ≥ 2 s thrust
  1.54 N/m, θ half-amplitude 0.425 (kinematic 0.459).
- `kin 2.0` n = 128 is the same flow as stage 2 n = 128 (ValveDriver 2 Hz, still water),
  which has always been clean with the clean-up (4084 steps to 5 s).
- tests 656/656.

To redo (they were run without the clean-up): stage 5 n = 128, stage 6 coupled n = 128 at
2 and 2.5 Hz (and `kin 2.0` if wanted), stage 6 coupled 1.5 Hz n = 64.
