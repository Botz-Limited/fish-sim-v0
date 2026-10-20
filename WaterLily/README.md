# WaterLily.jl – flow around a hydraulically actuated fish tail

2D (and one 3D) CFD of the fish from the other branches: rigid head, soft tail bent by a
chamber that a **constant pump + ±1 directional valve** fills and empties (same valve model as
MuJoCo / OpenFOAM: relay with δ = 1 ml, 0.2 s dwell, tail 1.5–2.5 Hz). WaterLily.jl solves
incompressible Navier–Stokes on a uniform Cartesian grid with an immersed boundary (BDIM), so
the bending tail and the swimming body need no remeshing.

**All physical numbers are PLACEHOLDER – the demo is qualitative.** Full design: `SPEC_fish_waterlily_demo.md`.
Detailed per-stage write-ups: `NOTES.md` (stages 0–1, problems), `results/stage2-4_summary.md`,
`results/stage6_summary.md`, `results/stage7_summary.md`, `gpu/README.md`, `viz/README.md`.

## Install (once, about 10 min)

```sh
curl -fsSL https://install.julialang.org | sh          # juliaup; this demo used Julia 1.13.2
cd WaterLily
julia --project=.   -e 'using Pkg; Pkg.instantiate()'  # solver + scripts (FishLily package)
julia --project=viz -e 'using Pkg; Pkg.instantiate()'  # live viewer / videos (Makie)
julia --project=.   -e 'using Pkg; Pkg.test()'         # 656 tests, about 2 min
```

GPU (optional, stage 7, AMD RX 7700 XT on Fedora): `gpu/setup_rocm_shim.sh`, then see `gpu/README.md`.

## Watch it live

```sh
# live window (vorticity, fish, progress bar, %, ETA, valve/forces), opens on the primary monitor
julia --project=. -t 2 scripts/live.jl --case tethered --f 2 --U 0.2 --t 4 --keep
# any stage script with the live window attached
FISH_LIVE=1 julia --project=. -t 2 scripts/stage2_tethered.jl
# live table (% done, ETA, readouts) of every running case, in a second terminal
julia --project=. scripts/progress.jl
# MP4 with readouts (headless)
julia --project=. -t 2 scripts/animate.jl --U 0.2
```

Every run prints `[case] 37.2 %  t=1.86/5.00 s  ETA 2m10s` and writes `results/progress/<case>.json`.

## Stages

Run from `WaterLily/` with `julia --project=. -t 4 scripts/<script>` (sweeps: 2 threads per
process, several processes; see `scripts/run_parallel.sh`). Wall times on a Ryzen 5 7600.

| # | Script | What | Result | Criterion |
|---|---|---|---|---|
| 0 | `stage0_validation.jl` | circle, Re = 100, D = 16/32/64 | St 0.174; C_D 1.286 | St PASS; C_D **FAIL** (band 1.3–1.45, viscous part under-resolved) |
| 1 | `stage1_rigid_fish.jl` | straight fish, U = 0.2 m/s | C_D 0.0373 (n=128), 0.0409 (n=256) | **FAIL** (8.6 % change, limit 5 %) – same cause |
| 2 | `stage2_tethered.jl` | 2 Hz tail in still water | thrust 1.47 N/m, 2.00 switches/cycle, reverse-Kármán jet | PASS |
| 3 | `stage3_inflow_sweep.jl` | U = 0.05–0.5 m/s, flapping vs rigid | self-propelled U* = 0.332 (n=128), 0.305 m/s (n=256) | PASS |
| 4 | `stage4_freq_sweep.jl` | f = 1.5–2.5 Hz at U* | St 0.35–0.37 at every f; best η 6.5 % at 2.25 Hz | PASS |
| 5 | `stage5_free_swim.jl` | 1-DOF surge from rest, 2 Hz | steady 0.361 m/s (1.72 L/s) at n=128, St 0.33 | PASS (+8.8 % vs U*, limit 25 %) |
| 6 | `stage6_coupled.jl` | tail angle from hydraulics + fluid load ODE | θ amplitude 0.93–0.97 × kinematic, Δp max 13–19 kPa, relief never opens | PASS (stable at 1.5/2/2.5 Hz) |
| 7 | `stage7_3d.jl` (GPU) | 3D fish, n=224, 67 M cells | no fin: drag 6 mN; caudal fin: thrust 22 mN | runs, wake images |

Key plots: `results/stage2_vorticity.png`, `results/stage3_inflow_sweep.png`,
`results/stage4_freq_sweep.png`, `results/stage5_free_swim_n*.png`,
`results/stage6_coupled_f*_n*.png`, `results/stage7_3d_n224_fin_lambda2.png`. Videos:
`results/fish_tethered_f2.mp4`, `results/fish_tethered_f2_U0.2.mp4`, `results/stage7_3d_n128_fin_3d.mp4` (3D, caudal fin, λ2 vortex cores; run with
`N=128 FIN=1 FRAME_T0=2 FRAME_DT=0.01`, then `julia --project=viz viz/render3d.jl stage7_3d_n128_fin`).

## Physics in one screen

- **Valve** (`src/valve.jl`): `V_ref = A_V·sin 2πft`; relay `e = V_ref − V_p`, switch at ±δ only
  after 0.2 s dwell; `dQ/dt = (s·Q_const − Q)/τ`, `dV_p/dt = Q`. Q_const 60 ml/s, A_V 8 ml, τ 0.02 s.
  Frequencies outside 1.5–2.5 Hz are rejected, not clamped.
- **Tail** (`src/geometry.jl`): midline `y = θ·h(x)`, uniform curvature on 10–110 mm, straight end;
  kinematic mode `θ = V_p/A_r` (A_r = 2e-5 m³/rad); coupled mode (stage 6)
  `(J+J_a)θ̈ + cθ̇ + k_eθ = A_r·Δp + Q_θ,fluid + J_a·θ̈_prev`, with added inertia J_a identified from the CFD.
- **Fish**: half-ellipse head 60 mm + tail 150 mm (30 → 10 mm thick), L = 0.21 m.
- **CFD**: n cells per body length (64/128/256), Re_sim = 5000 (not the real 4e4), Float32,
  forces from WaterLily `pressure_force`/`viscous_force` (sign flipped to "force on body").

## Simplifications and known problems

1. **2D section** for stages 0–6: 2D thrust is large and side forces about 10× the 3D value
   (stage 7). Per-metre forces (N/m); 3D values use b_eff (PLACEHOLDER).
2. **Viscous drag is under-resolved** on a uniform grid (stages 0–1 fail by this): drag is low,
   so U* and the free-swimming speed are upper bounds (≈ 0.3 m/s).
3. **Pressure in solid cells** (fixed): WaterLily leaves stale, huge pressure in cells deep inside a
   moving body; when the tail uncovered one, the force spiked (up to 1e8 N/m). `run_fish!` now
   calls `clean_pressure!` after each step for moving bodies (`NOTES.md`, last section).
4. **Valve lock-on transient** 0.8–3.1 s depending on f; all averages start after it.
5. Coupled-tail parameters (stiffness, damping, b_eff) are PLACEHOLDER; the identified added
   inertia J_a ≈ 5.7·J makes the explicit coupling unstable without the J_a correction.

## Layout

```
src/        FishLily package: params, units, valve, geometry, forces, sim (run_fish!), boxbody, progress, live hook
scripts/    stage0–7, live.jl, animate.jl, progress.jl, run_parallel.sh, shared libs
test/       Pkg.test() suite
viz/        Makie viewer (own environment): live window on the primary monitor, MP4/PNG
gpu/        AMDGPU environment, benchmark (3D 5.6×, 2D 1.9× vs CPU), ROCm shim script
results/    CSV, PNG, MP4, summaries
```

Versions: `versions.txt` (Julia 1.13.2, WaterLily 1.9.2, AMDGPU 2.8.0, Makie 0.24.16).
