# Stage 7: 3D fish on the AMD GPU (WaterLily 1.9.2 + AMDGPU, Float32)

Script: `scripts/stage7_3d.jl` (+ `scripts/lib_3d.jl`). For how to run it, see `gpu/README.md` § Stage 7.
All geometric and valve numbers are PLACEHOLDERS.

## Set-up
- Body: the 2D top-view profile with elliptic cross-sections. The height is K_H = 5/3 × the width,
  so the head and tail root are 0.050 m high and the tail tapers to 0.017 m at the tip. Mean height
  b_eff = 0.0346 m. Two variants were run: without a fin, and with a caudal fin (`FIN=1`).
  The fin is a thin rounded plate in the tail's straight frame: x = 0.120–0.165 m from the root
  (15 mm past the tail tip), 0.06 m span (±0.03 m), 6 mm thick (about 6 cells). It bends with the
  distal tail.
- Tail bending: the same map as 2D, y = θ·h(x), applied to (x, y). z is unchanged.
- θ(t): the valve model in kinematic mode at f = 2.0 Hz. The tethered fish sits in a uniform inflow
  U = 0.2 m/s with Re_sim = 5000, the same settings as 2D.
- Domain: 0.75 L upstream, 2.25 L downstream, ±0.75 L sideways, ±0.5 L vertically.
  The side boundaries are slip/free-stream and the outlet is convective.
- Grid: **896×336×224 = 67.4 M cells**, n = 224 cells/L (0.94 mm). This is the largest grid that
  fits in 12 GiB: 8.5 GiB is used.
- Run: t = 0…4.0 s, **3248 steps**, **wall time 36.3 min**, **665 ms/step**, about 100 Mcell-steps/s.
  Forces are computed every step. The Δt cap (0.4) and the CFL limit set Δt at about 0.34.
- Averages are taken over t ≥ 2.0 s, which skips the valve start-up transient (NOTES.md item 8).

## Forces (time mean, t ≥ 2 s; Fx > 0 = drag, thrust = −Fx)

| case | Fx [N] | Fx pressure [N] | Fx viscous [N] | Fy mean [N] | Fy rms [N] | θ amplitude [rad] |
|---|---|---|---|---|---|---|
| 3D, n = 224 (real fish) | **+0.0060** (net drag) | +0.0008 | +0.0052 | 0.0001 | 0.13 | 0.333 |
| 2D, n = 128, × b_eff = 0.0346 m | **−0.039** (net thrust) | −0.042 | +0.0033 | −0.15 | 1.53 | 0.333 |

Per span, the 2D values are Fx' = −1.13 N/m. Multiplied by the maximum height of 0.05 m instead of
b_eff, this gives −0.056 N. The vertical force Fz is about 0, as expected from symmetry
(rms 5e-6 N).

Qualitative comparison:
- **The sign of the net force differs (no fin).** In 2D the flapping tail gives a net thrust at 0.2 m/s.
  In 3D the fish without a fin has a small net drag of +6 mN. The pressure (thrust) part is almost
  zero in 3D: +0.8 mN in 3D against −42 mN in 2D×b_eff. The tail in 3D is low (17–50 mm high) and
  has no caudal fin. Flow escapes over and under it (the 3D relief effect), so it pushes far less
  water than a 2D strip of the same height.
- **The lateral force is about 12× smaller in 3D** (rms 0.13 N against 1.53 N). The reason is the same:
  a finite-height body has much less added mass than the 2D strip. The spikes at each valve switch
  are visible in both.
- **The viscous drag is larger in 3D** (5.2 against 3.3 mN). The 3D body is wetted all around, and
  the 3D grid is finer relative to the boundary layer. The note on under-resolved skin friction from
  stage 1 still applies.
- Conclusion: the 2D model with a "per metre × b_eff" correction greatly overestimates the thrust
  of this body without a fin. With the caudal fin, 3D reaches about 57 % of the 2D × b_eff thrust
  (see below).

## No fin vs caudal fin (3D, n = 224, identical settings, t ≥ 2 s)

| | no fin | caudal fin | 2D × b_eff (reference) |
|---|---|---|---|
| Fx total [N] | +0.0060 | **−0.0221** | −0.0391 |
| Fx pressure [N] | +0.0008 | −0.0288 | −0.0424 |
| Fx viscous [N] | +0.0052 | +0.0066 | +0.0033 |
| Fy rms [N] | 0.13 | 0.65 | 1.53 |
| net | **drag 6 mN** | **thrust 22 mN** | thrust 39 mN |
| steps / wall time / ms per step | 3248 / 36.3 min / 665 | 5541 / 66.5 min / 716 | – |

- **The fin turns the net drag into a net thrust of 22 mN.** The pressure thrust rises from about 0
  to 29 mN, while the viscous drag rises slightly (+1.4 mN) because the wetted area is larger.
  The fish with a fin reaches about 57 % of the 2D × b_eff thrust. The fin also raises the lateral
  force rms 5×, to 0.65 N.
- **The fin run is about 1.8× more expensive.** The fin tip moves faster, so the CFL condition cuts
  the mean Δt from 0.26 to 0.15 grid units (5541 instead of 3248 steps). The cost per step is
  almost the same. This is over the 30–45 min target. The case can be rerun at N=192 (about
  2× cheaper) if needed.
- **The fin's wake is much richer** (`*_fin_wake_slices.png`, `*_fin_lambda2.png`): large
  alternating vortex loops, about 0.06 m tall and spreading ±0.12 m sideways, with strong ω_x pairs
  in the cross-flow slice.

## Wake images
- `stage7_3d_n224_wake_slices.png`: three slices at t = 4.0 s with the body outline.
  - z = 0, ω_z (top view): a reverse-Kármán-like row of alternating vortices, about 0.2 m wide.
  - y = 0, ω_y (side view): small ring cross-sections behind the tip.
  - x = 0.255 m, ω_x (cross-flow): counter-rotating pairs, the legs of the vortex loops.
- `stage7_3d_n224_wake_phases.png`: z = 0 slices of ω_z at 4 phases of the last tail cycle.
- `stage7_3d_n224_lambda2.png`: λ2-criterion vortex cores, shown as a 3D point cloud and as top and
  side projections, at t = 4 s. The threshold is λ2 < 2 % of the strongest wake core (−140 1/s²).
  The cores form a chain of alternating, closed vortex loops (rings) shed to either side.
  This is used instead of a rendered isosurface, to keep the plotting light (Plots/GR).
- `stage7_3d_n224_forces.png`: time series of θ, thrust (3D, plus 2D × b_eff), Fy and Fz.
- The caudal-fin variant has the same four images with the suffix `_fin`
  (`stage7_3d_n224_fin_{forces,wake_slices,wake_phases,lambda2}.png`). In its y = 0 slice the fin
  is not cut, because the tail is bent out of that plane at t = 4 s.

## Files
`stage7_3d_n224_timeseries.csv`, `_info.txt`, `_snapshots.jls` and `_lambda2.jls` (Julia Serialization,
slices and the ×2-downsampled λ2 field), `stage7_3d_n224.log`, `stage7_2d_ref_n128_timeseries.csv`/`.log`,
`stage7_summary.csv` (one row per case, plus a `net` column). The `_fin` files follow the same
pattern.

## Problems / notes
- FishLily is loaded by `include`ing only five source files into a module `Fish3D`; it is not
  `Pkg.develop`ed into the gpu env (see `gpu/README.md`). The 2D `Track` θ(t) holds mutable state
  and so is not GPU-safe. It is replaced by isbits map structs: `sim.body` is swapped each step and
  holds the new scalars (t0, θ0, rate).
- Elliptic sections are made by evaluating the 2D profile SDF at ρ = √(y² + (z/K_H)²). This is a
  pseudo-SDF: the surface is exact, and WaterLily renormalises d by |∇d|.
- A `WaterLily.bbox` method limits measure! and the force integrals to a box around the fish.
- The first second of the run includes the impulsive start (Fx spike) and the valve start-up
  transient (θ offset about −0.18 rad). Both are excluded from the averages.
- The 2D reference ran on 1 CPU thread (1.9 min). It uses the same valve, inflow and Re_sim.
