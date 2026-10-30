# Stage 8 – CAD tail on the aquarium test stand (3D)

The same setup as the SOFA bench (`bench_config()`, sofa branch), from the video
`VID_20261026_105654.mp4`: only the tail, fully submerged in still water, valve at 0.5 Hz,
tail root bolted to a holder that can sway (y) and yaw about a vertical bearing 0.10 m ahead
of the root. **All physical numbers are PLACEHOLDER.**

## What was done

1. `cad/step_to_sdf.py`: `Fish_Tail.step` (the same file as `SOFA/cad/`) -> signed distance field on a
   1 mm grid. Same parts as SOFA: 8 tubes (filled: their lumen is chamber water), body (front
   pocket filled), caudal + ventral fin, 3 mm holder plate. gmsh triangulates each part, ray parity
   voxelizes at 0.5 mm (no booleans: the STEP parts overlap), then an EDT gives the distance.
   Volume 480.3 ml + 9.1 ml of fin outside the body (SOFA mesh: chambers 42.6/42.7 ml per side).
2. `scripts/lib_bench.jl`: GPU-capable body (trilinear SDF in device arrays, Adapt rules), map =
   holder sway/yaw + tail bending, box-restricted measure, 2-DOF holder ODE.
3. `scripts/stage8_bench.jl run|plot`, frames for `viz/render3d.jl`, 14 tests in `test/runtests.jl`.

## Model

- Tail bending is **prescribed** (kinematic mode, as stages 2–5 and 7): θ = V_p/A_r, uniform
  curvature on 0–180 mm (tubes + soft body), straight stiff tip with the caudal fin (from the
  video). A_r is set so that θ ≈ ±0.35 rad (≈ 20°, fin tip ±6 cm). SOFA computes the bending
  from the chamber pressure; here the fluid does not bend the tail.
- Valve: Q_const 26 ml/s, A_V 13 ml (SOFA bench). Q = 4·f·A_V, so V_p is a triangle (switches at the peaks only).
- Holder (MOUNT=bench): (M + M_a) q̈ = Q_fluid + M_a q̈_prev − S θ̈ − C q̇, with q = (sway, yaw).
  M is the holder (0.4 kg, 4e-3 kg m², SOFA values) plus the tail (0.516 kg at 1050 kg/m³).
  S is the tail's own inertia while it flaps. Q_fluid is F_y and M_z about the pivot (pressure + viscous).
  M_a is the strip-theory added mass (1.61 kg in sway, 3× the tail): it only stabilises the
  explicit coupling, the same fix as stage 6. Springs 0, damping α = 1/s.
- CFD: n = 128 cells per 0.26 m (2.03 mm), 336×192×160 = 10.3 M cells, Re_sim = 5000
  (U scale 0.1 m/s, L 0.26 m; the real value is ≈ 2.6e4). Domain 0.6 L ahead of the root, 2 L behind, ±0.75 L sideways,
  ±0.6 L vertically, all walls slip. The fins (2 mm = 1 cell) are thickened to 2.5 cells (pad 1.54 mm per side),
  otherwise the immersed boundary leaks through them.

## Results (t ≥ 2 s, CPU 12 threads; 840M iGPU is 3.4× slower here)

| case | wall | θ amp | mean thrust | F_y peak | M_z peak | holder sway | holder yaw |
|---|---|---|---|---|---|---|---|
| `stage8_bench_n128_fixed` (clamped) | 25 min | 0.355 rad | 30.6 mN | ±3.3 N | ±0.96 N m | – | – |
| `stage8_bench_n128_bench` (free) | 12 min | 0.355 rad | 4.0 mN | ±2.3 N | ±0.69 N m | ±7.9 mm | ±7.1° |

- **Free holder:** it recoils against the tail, so the yaw is opposite to θ, about 1/3 of the tail angle.
  The fin moves less relative to the water, and the mean thrust drops 7.6× compared with the clamped tail.
  The mean sway is 0.3 mm, so there is no drift in 6 s.
- **Force peaks at every valve reversal (2–3 N, about 50 ms long)** come from the prescribed
  kinematics: the chamber flow reverses in τ = 20 ms, so the tail's angular velocity
  flips almost instantly. The added mass of the water (~1.6 kg) then gives a large impulse.
  The real tail is compliant and would smooth this, so the peaks are an upper bound. Between reversals,
  |F_y| is 0.1–0.3 N.
- Video: `stage8_bench_n128_bench_3d.mp4` (t = 2–6 s, real time, λ2 vortex cores). Plots:
  `stage8_bench_n128_*_forces.png`, `_wake_phases.png`, `_wake_slices.png`; table `stage8_summary.csv`.

## Known limits

1. Bending is prescribed, not from the chamber pressure; there is no fluid–structure coupling of the tail (SOFA has it, without fluid).
2. Not modelled: the holder ring and bracket in the water, the free surface 10–15 mm above the fin, and the tank walls.
3. n = 128 only, so there is no grid convergence check. The fins are thickened by 1.5 mm per side, and the viscous drag is under-resolved (stages 0–1).
4. Small-angle holder equations; the strip-theory M_a is an estimate (used only for stability).

Rerun: `python cad/step_to_sdf.py`, then
`BACKEND=cpu MOUNT=bench FRAME_DT=0.05 FRAME_T0=2 julia --project=. -t 12 scripts/stage8_bench.jl run`,
`BACKEND=cpu MOUNT=fixed julia --project=. -t 12 scripts/stage8_bench.jl run`,
`julia --project=. scripts/stage8_bench.jl plot`, `julia --project=viz viz/render3d.jl stage8_bench_n128_bench 20`.
