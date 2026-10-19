# Stage 6 – two-way coupled tail (summary)

Script `scripts/stage6_coupled.jl` with the helpers in `scripts/lib_coupled.jl`. The setup is the
tethered fish in still water, as in stage 2. Re_sim is 5000. The runs used 2 threads on a shared
machine, so wall times vary by about ±50 %. All physical numbers are PLACEHOLDERS.

## Model

    J·θ̈ + c·θ̇ + k_e·θ = A_r·Δp + M_fluid,   Δp = clip((V_p − A_r·θ)/C_h, ±p_max)

- **θ** is the tip slope of the bending shape y = θ·h(x), with h(L_TAIL) = 0.09 m. It is not a
  rigid rotation about the root.
- **M_fluid** is the generalized force of the pressure on the tail, Q_θ = −∫p·n_y·h(x) ds. This is
  the load that does work on θ. `tail_pressure_moment` is the moment about the root (lever arm x
  instead of h(x)). It is logged as `M`, and setting `COUPLE_FORCE=root` uses it instead, but it
  overstates the load on θ by about 2.4×.
- **3D scaling:** M = b_eff·M_2D with b_eff = 0.05 m (tail height, PLACEHOLDER).
- **Relief valve:** it works as in MuJoCo. The excess volume is vented, so V_p itself drops and the
  relay sees the reduced V_p.
- **Structural parameters (PLACEHOLDERS):**
  - J = ∫ρ_s·b·t(x)·h(x)² dx = 1.83e-4 kg·m² (silicone 1100 kg/m³, solid section of height b_eff).
  - k_e = 0.9 N·m/rad, which is 3 × the MuJoCo `stiffness_actuated` of 0.3.
  - c = 0.005 N·m·s/rad (MuJoCo `damping_joint`).
  - k_h = A_r²/C_h = 5 N·m/rad.
- **Stabilisation:** (J + J_a)·θ̈ + … = A_r·Δp + M_rest, with M_rest = M_meas,prev + J_a·a_prev.
  Here a_prev is the acceleration the CFD saw in the previous step, i.e. the jump of the
  piecewise-constant body velocity divided by Δt.
- **ODE integration:** the ODE is sub-stepped (≤ 1e-4 s) inside each CFD step with the implicit
  trapezoidal rule. Newton handles the piecewise-linear clip.
- **Spike guard** (added after the CFD bug below): a step with |Fx| > 100 N/m or |M_2D| > 20 N·m/m
  is not fed to the ODE. The previous load is held instead, and the step is counted in `n_reject`.

## (a) Prescribed-motion identification (n = 128, f = 2 Hz)

The prescribed motion was θ = 0.3·(0.75 sin ωt + 0.25 sin 3ωt). The 3rd harmonic is needed because
with a pure sine θ̈ = −ω²θ, so J_a and a stiffness term cannot be separated. The fit used
t ≥ 0.75 s. Files: `stage6_ident_n128.csv`, `stage6_ident_f2.0_n128.png` and the time series.

| load | J_a (2D) [kg·m] | c_a (2D) [kg·m/s] | R² | J_a (3D = ·b_eff) | c_a (3D) |
|---|---|---|---|---|---|
| Q_θ (generalized, used) | 0.0209 | 0.148 | 0.982 | **1.05e-3 kg·m²** | **7.4e-3 N·m·s/rad** |
| root moment | 0.0511 | 0.306 | 0.985 | 2.6e-3 | 1.5e-2 |

- **Sign check passes:** M_fluid ≈ −(J_a·θ̈ + c_a·θ̇) with J_a > 0 and c_a > 0, so the fluid load
  acts as added inertia plus positive damping.
- Adding a stiffness term gives k_a ≈ −1.3 N (2D). That is negligible, and J_a changes by −8 %.
- The fit is the same whether θ̈ comes from the CFD-seen finite difference or is analytic.
- J_a/J ≈ 5.7.
- Coupled natural frequency without fluid damping: √((k_h + k_e)/(J + J_a)) = 11 Hz.

## (b), (c) Coupled runs (t_end = 5 s, averages over t ≥ 2 s)

The kinematic reference is θ_kin = V_p/A_r from the same valve. `amp` is half the peak-to-peak
value; `amp1` is the fundamental Fourier amplitude. Table: `stage6_coupled_runs.csv`.

| case | status | amp / kin | amp1 / kin | lag [°] | max abs Δp [kPa] | wall |
|---|---|---|---|---|---|---|
| 2 Hz, n=64 | stable, clean | 0.318 / 0.333 = **0.95** | 0.88 | 1.7 | 13.5 | 19 s |
| 2.5 Hz, n=64 | stable, clean | 0.240 / 0.258 = **0.93** | 0.90 | 2.0 | 11.6 | 15 s |
| 1.5 Hz, n=64 | CFD spike at 4.16 s → NaN at 4.55 s | (θ cycles 0.42 before the spike) | | | | 20 s |
| 1.5 Hz, n=128 | stable, clean | 0.429 / 0.459 = **0.94** | 0.87 | 1.2 | 18.8 | 80 s |
| 2 Hz, n=128 (unguarded) | stable, but CFD spike at 0.387 s | 0.328 / 0.333 = **0.98** | 0.88 | 1.7 | 19.9 | 121 s (713 s under load) |
| 2 Hz, n=128 (guarded rerun) | CFD blow-up 3.09 s → NaN 3.52 s | | | | | 105 s |
| 2.5 Hz, n=128 | **invalid**: CFD corrupted from 0.186 s | | | | | 289 s |

- In every clean run the tail is stable: the growth rate of the per-cycle θ amplitude is
  |σ| < 0.005 /s. The amplitude is 2–7 % below kinematic, the phase lag is 1–2°, the valve makes
  2 switches per cycle, and the relief valve never opens (max abs Δp < 20 kPa < 50 kPa).
  **Criterion "stable, amplitude ≤ kinematic": PASS** for 2 Hz at n=64, 2.5 Hz at n=64,
  1.5 Hz at n=128, and also 2 Hz at n=128 for θ.
- The 3D fluid load is small (rms 0.1 N·m) next to A_r·Δp (≈ 0.4 N·m peak). Most of the hydraulic
  torque goes into the silicone spring k_e and the hydraulic spring. Fluid damping removes the
  11 Hz ringing that the valve switches excite (visible in Δp).
- **Sensitivity to J_a** (2 Hz, n=64):
  - no stabilisation (J_a = 0, explicit): NaN after 31 steps (t = 0.085 s), the expected
    added-mass instability;
  - J_a × 0.25 and × 0.5: stable, amplitude 0.93–0.94;
  - J_a × 2: NaN at 1.93 s.
  The scheme is therefore robust to underestimating J_a but not to overestimating it 2×. Use the
  identified value.

## CFD force spikes (WaterLily, moving body), same bug as in stage 5

Single-step pressure spikes occur. They are deterministic: the `box=false` run is bit-identical to
the box run. After a spike the pressure field keeps high-frequency noise.

| run | first spike |
|---|---|
| ident n=128 | none (clean) |
| coupled 2 Hz n=64 | none (clean) |
| coupled 2.5 Hz n=64 | none (clean) |
| coupled 1.5 Hz n=128 | none (pressure noise grows mildly after 3 s) |
| coupled 2 Hz n=128 | step 240, t = 0.3873 s: Fx 79 N/m, Fy −694 N/m, M_2D −51. After it the step-to-step noise in M is 20× higher and the mean thrust is biased (−14 N/m vs +1.2 at n=64), so **thrust from this run is not usable**; θ stays smooth. The guarded rerun rejects this spike but meets a CFD blow-up at 3.09 s and then diverges (θ cycles 0.32 → 0.87 rad). |
| coupled 2.5 Hz n=128 | t = 0.186 s: Fx 471 N/m; afterwards 10399 rejected steps → invalid (θ "amp" 0.49, thrust 109 N/m are artefacts). The first, unguarded attempt went NaN at 1.93 s. |
| coupled 1.5 Hz n=64 | t = 4.163 s: Fx 574 N/m, then runaway |
| kinematic 2 Hz n=128 (no coupling, `kin`) | blew up (Fx −6.8e8 N/m at t ≈ 4.19 s, 22 k steps); killed, no CSV |

The kinematic-only blow-up shows that the spikes are a CFD problem, not a coupling instability.
Once the pressure is corrupted, the coupling turns it into θ divergence: the guard holds the last
load but cannot fix a corrupted flow field.

During the prescribed-motion development at n=64, faster motion (rate 5.6 rad/s) also gave such
bursts (Poisson solver at 32 iterations, Δt collapse). The thin tail tip is only ~3 cells thick
at n=64.

## Simplifications and open points

- 2D strip × b_eff for a low-aspect-ratio tail (height 0.05 m, length 0.15 m) overestimates the
  added inertia; a 3D J_a would be smaller.
- Only the pressure load is used. Section rotation (an x-component of ∂X/∂θ) is neglected.
- The 2.5 Hz case at n=128 and a clean thrust comparison at n=128 need the CFD spike bug fixed first.

## Re-run after the pressure fix (`clean_pressure!` in `run_fish!`)

All previously spoiled runs re-done; 0 guard rejections, no spikes, all stable, 2 switches/cycle, relief valve never opens.

| run | θ amp / kinematic | phase lag | Δp max [kPa] | thrust [N/m] | growth [1/s] | wall |
|---|---|---|---|---|---|---|
| 1.5 Hz, n=64 | 0.425 / 0.458 (0.93) | 1.3° | 18.6 | 1.63 | +0.0007 | 21 s |
| 2.0 Hz, n=128 | 0.322 / 0.333 (0.97) | 1.7° | 15.1 | 0.91 | −0.008 | 88 s |
| 2.5 Hz, n=128 | 0.246 / 0.258 (0.95) | 2.1° | 13.6 | 0.81 | −0.005 | 89 s |

These rows supersede the "affected" entries above. Criterion (stable, amplitude ≤ kinematic): PASS at every frequency.
