# SPEC: WaterLily.jl demo – flow around a hydraulically actuated fish tail

Branch `waterlily`, directory `WaterLily/`. Same fish and the same valve model as the other
branches (MuJoCo on `main`, OpenFOAM, PyElastica, ...). **All physical numbers are
PLACEHOLDER – to be identified from measurements.** The demo is educational and qualitative.

## 1. Why WaterLily (what it adds to the set)

WaterLily.jl is a Julia CFD solver for incompressible Navier–Stokes on a **uniform Cartesian
grid** with the **Boundary Data Immersion Method** (BDIM): bodies are described by a signed
distance function (SDF) plus a coordinate map, so a **moving / deforming body needs no
remeshing**. The same code runs on CPU threads and on GPUs (KernelAbstractions; AMD via
AMDGPU.jl). Compared to the others:

- vs MuJoCo / PyElastica / Stonefish: real flow field (wake, vortices, pressure on the surface)
  instead of a drag formula;
- vs OpenFOAM + preCICE + CalculiX: no mesh, no coupling library, one language, ~100 lines
  per case, fast enough for parameter sweeps and **free swimming** (body moves through the water);
- limits: tail kinematics are prescribed (or a low-order ODE coupled to the flow), no solid FEM;
  uniform grid ⇒ thin boundary layers are under-resolved (implicit LES); 2D by default.

## 2. Geometry and parameters (`src/params.jl`)

Same 2D top-view section as the OpenFOAM branch (`OpenFOAM/tools/params.py`):

| Name | Value | Note |
|---|---|---|
| `HEAD_A` | 0.060 m | rigid head, half-ellipse in x |
| `L_TAIL` | 0.150 m | tail length, thickness 0.030 → 0.010 m (linear taper) |
| `L_BODY` | 0.210 m | head + tail, length scale of the CFD |
| `ρ`, `ν` | 1000 kg/m³, 1e-6 m²/s | water |
| `U_REF` | 0.2 m/s | reference swimming speed (Re = U·L_BODY/ν ≈ 4.2e4) |

Valve model (identical to MuJoCo `fishsim/config.py`): `Q_const` 60 ml/s, `A_V` 8 ml,
`tau_valve` 0.02 s, δ 1 ml, `valve_min_dwell` 0.2 s, `p_max` 50 kPa, tail frequency limited to
**1.5–2.5 Hz** (reject outside, no silent clamping). Hydraulic lever `A_r = A_eff·r_eff = 2e-5
m³/rad` (MuJoCo), so `A_V` ↔ 0.4 rad of bending; `C_h` 8e-11 m³/Pa.

Units: the solver runs in grid units. `src/units.jl` converts: `n` cells per `L_BODY`,
velocity scale `U` (grid), time `t_grid = t_phys·U_REF/L_BODY·(n/U)…` – one function pair
`to_grid`/`to_phys` used everywhere; never hand-convert in scripts. Re is a parameter
(default `Re_sim = 5000`, a documented simplification: 2D at 4e4 is not physical either).

## 3. Model

### 3.1 Valve and hydraulics (`src/valve.jl`) – port of MuJoCo / OpenFOAM `make_actuation.py`
    V_ref = r(t)·A_V·sin 2πft + V_bias        r = ramp over first period
    relay: e = V_ref − V_p; e > δ → s=+1; e < −δ → s=−1; ignored until t − t_switch ≥ dwell
    dQ/dt = (s·Q_const − Q)/tau_valve,  dV_p/dt = Q
Exact exponential step for Q, trapezoid for V_p (as `make_actuation.py`). Metric: valve
switches per tail cycle.

### 3.2 Tail kinematics
Midline of the tail `y(ξ,t) = θ(t)·h(ξ)`, ξ = x/L_TAIL ∈ [0,1], bending concentrated over the
chamber region (curvature uniform on 0.07–0.73 of the tail, straight distal part). Tip angle
from volume: **kinematic mode** θ = V_p/A_r (chamber volume becomes bending one-to-one);
**coupled mode** (stage 6) θ from the ODE below. The body is `AutoBody(sdf, map)`; the map
bends the tail by inverting the midline (thickness measured normal to the midline, small-angle
OK up to ~0.5 rad; check SDF quality with a test).

### 3.3 Coupled tail (stage 6)
    J·θ̈ + c·θ̇ + k_e·θ = A_r·Δp + M_fluid(t),   Δp = clip((V_p − A_r·θ)/C_h, ±p_max)
`M_fluid` = pressure moment about the tail root from WaterLily. Water-like density ⇒ added
mass ≫ J ⇒ explicit coupling is unstable: use an added-inertia estimate `J_a` on the left and
subtract it from the measured moment (`J_a·θ̈_prev`), report if it still diverges.

### 3.4 Free swimming (stage 5)
1-DOF surge: `m·ẍ = F_x,fluid`, m = ρ·area (neutrally buoyant 2D section). Implement by moving
the body through still water (body map with `x(t)`), not by changing inflow.

## 4. Stages (each: script `scripts/stageN_*.jl`, CSV + PNG in `results/`, tests in `test/`)

| # | Name | Content | Pass criteria |
|---|---|---|---|
| 0 | validation | circle Re=100: C_D, St at 3 resolutions | C_D 1.3–1.45, St 0.15–0.18 at finest |
| 1 | rigid fish | straight fish in inflow: C_D vs resolution (n = 64/128/256), domain size check | C_D change < 5 % between two finest |
| 2 | tethered tail, still water | kinematic mode, f = 2 Hz: thrust, lateral force, vorticity snapshots, switches/cycle | mean F_x > 0 (thrust), 2 ± 0.2 switches/cycle |
| 3 | inflow sweep | U = 0.05…0.3 m/s at f=2 Hz: mean F_x(U), interpolate self-propelled speed U* | F_x decreases with U, sign change exists or reported |
| 4 | frequency sweep | f = 1.5…2.5 Hz step 0.25 at U*: thrust, St = f·A_tip/U, input power, Froude efficiency | St reported per f; runs independent → parallel |
| 5 | free swimming | 1-DOF surge from rest, f = 2 Hz: x(t), u(t), steady speed vs stage 3 U* | steady speed within 25 % of U* |
| 6 | coupled tail | hydraulics + fluid moment ODE, compare θ amplitude vs kinematic mode | stable run, amplitude ≤ kinematic |
| 7 | optional 3D / GPU | 3D body (elliptic sections), AMDGPU if ROCm works, else coarse CPU | runs, wake image |

Plus `scripts/animate.jl` (vorticity movie with live readouts: t, f, s, V_p, θ, F_x; like the
PyElastica animation) and `scripts/viewer.jl` (live GLMakie view while simulating, if
WaterLilyMakie/GLMakie is available).

### Live progress (user requirement)
Every run shows live progress: a terminal line `[case] 37.2 %  t=1.86/5.00 s  ETA 2m10s`,
a progress file `results/progress/<case>.json` (pct, t, ETA, status, latest readouts),
`scripts/progress.jl` = live table of all running cases, and the GLMakie live viewer
(vorticity + body + progress bar + readouts) driven by the `on_frame(sim, readouts)` hook.

## 5. Tests (`test/runtests.jl`, `julia --project -e 'using Pkg; Pkg.test()'`)
Valve: 2 switches/cycle at 1.5/2/2.5 Hz, dwell ≥ 0.2 s, rejection outside range, triangle
amplitude ≈ Q_const/(4f). Geometry: SDF sign inside/outside, |∇sdf| ≈ 1 near surface, tail tip
displacement equals θ·h(1). Units round-trip. Fast CFD smoke test (coarse circle, < 30 s).

## 6. Performance
CPU: `julia -t auto` (12 threads). Sweeps run independent cases as **separate processes**
(`scripts/run_parallel.sh`, N_jobs × threads ≤ 12). Record wall times in README. GPU optional.

## 7. Deliverables
`README.md` (install, run, physics, results table, simplifications, versions), `Project.toml`
+ `Manifest.toml` (pinned), `versions.txt`, results PNG/CSV, root `README.md` row.
