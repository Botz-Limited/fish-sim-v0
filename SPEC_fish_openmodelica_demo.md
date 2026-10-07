# SPEC: OpenModelica demo – system model of a robotic fish (electrics + hydraulics + mechanics + ballast)

> Instructions for Claude Code. Put this file in an empty project folder and write:
> "Read SPEC_fish_openmodelica_demo.md and implement it in stages. Start with a plan."

## 0. Goal and context

Build a **simplified, educational** system model of a robotic fish in the Modelica language, run in OpenModelica. It should show what Modelica does best and what MuJoCo, SOFA and CFD do not offer:
- **multi-domain, acausal modelling**: DC motor → pump → pipes → chambers → tail, connected by physical connectors (voltage/current, torque/speed, pressure/flow), not by signal arrows,
- **energy balance**: where the battery energy goes (losses in the motor, pump, pipes, valve, water),
- **hydraulic dynamics**: pump bandwidth, chamber stiffness, relief valve operation,
- **ballast system**: a piston/syringe driven by a motor and a lead screw, depth control,
- **FMU export**, so the hydraulic model can be plugged into other simulators (e.g. the MuJoCo demo).

Geometry and hydrodynamics are **heavily simplified** here (1D lumped-parameter models). This model answers questions like "are the pump and battery sufficient", not "how exactly does the water flow".

This is **not** a calibrated model. Parameters are placeholders and must be marked as such.

The user is a young mechatronics engineer who is learning. **Comments and descriptions in Polish**: comments in the Modelica code (`//` and parameter description strings) and `Documentation` annotations in every model explaining the physical equations.

## 1. Working rules (important)

1. Work in stages (section 7). After each stage: `checkModel` without errors (number of equations = number of unknowns), simulation, plot, test. Only then move on.
2. Pin the versions at the start: OpenModelica (`omc --version`), Modelica Standard Library (MSL), OMPython. SI units in MSL 4.x are `Modelica.Units.SI`; in the older MSL 3.2.x they were `Modelica.SIunits`. **The OMPython API has changed recently** (session classes), so check the documentation of the installed version instead of copying older examples.
3. **Do not use commercial libraries** (e.g. Modelon Hydraulics). Only MSL + an own lightweight package.
4. Write the hydraulics as an **own small package** (`FishHydraulics`) with a simple connector (pressure `p` as the potential, volume flow `V_flow` as the `flow` variable). Justification in the README: `Modelica.Fluid` is powerful but heavy (media, initialization, enthalpy) for a small system with incompressible water, and an own package teaches how acausal connectors work. Optionally (stage 8): the same circuit on `Modelica.Fluid` for comparison.
5. Good numerical practice: for `|x|·x` use `smooth`/`noEvent` or regularization near zero (explain why: events and non-differentiability slow the solver down). Explicit `initial equation`. Avoid unnecessary algebraic loops.
6. Do not invent "realistic" values. Every parameter has `PLACEHOLDER – do identyfikacji` in its description.

## 2. Project structure

```
fish_modelica_demo/
  README.md
  FishRobot/                    # Modelica package (directory structure: package.mo + package.order)
    package.mo
    Interfaces/                 # HydraulicPort connector, base 2-port classes
    Hydraulics/                 # GearPump, Chamber, Pipe, ReliefValve, CheckValve (optional), Reservoir
    Tail/                       # TailEquivalent (1 DOF, rotational)
    Buoyancy/                   # BallastSyringe, VerticalDynamics
    Propulsion/                 # SurgeDynamics (1D forward motion)
    Control/                    # CPG (sine), DepthPID with anti-windup
    Examples/                   # scenario models (each with annotation experiment(...))
    Tests/                      # small component test models
  scripts/
    run_all.py                  # OMPython: compile, simulate, plot -> results/
    sweep.py                    # parameter sweeps
    export_fmu.py               # FMU export of the hydraulics+tail subsystem
    fmu_demo.py                 # FMPy: run the FMU from Python (co-sim loop)
    check_tests.py              # automatic assertions on the results
  results/
```

## 3. Components

### 3.1 Electrics and pump drive (MSL)
- Battery as a voltage source with internal resistance (placeholder), H-bridge as an ideal controlled voltage source `u·U_bat`, `u ∈ [−1, 1]`.
- DC motor from MSL (e.g. `Modelica.Electrical.Machines` or an R-L circuit + `Modelica.Electrical.Analog.Basic.RotationalEMF` + rotor inertia). Pick the simpler option and justify it.

### 3.2 Hydraulics (`FishHydraulics`, own)
- `GearPump`: positive displacement, reversible. `V_flow = D·ω − k_leak·Δp`, torque `τ = D·Δp/η_m`. MSL rotational connector on the shaft side.
- `Chamber`: silicone chamber with **nonlinear compliance** `p = f(V)` from a table (`Modelica.Blocks.Tables.CombiTable1Ds`). Make the placeholder table so that it can be replaced by a p–V curve from the SOFA demo or from a measurement. Output: volume `V` (for the tail model).
- `Pipe`: laminar-turbulent pressure loss (`Δp = R_lam·V_flow + R_turb·|V_flow|·V_flow`, regularized), optionally the inertance of the liquid column.
- `ReliefValve`: relief valve with a smooth characteristic (no hard switching), opening pressure `p_set`.
- Closed circuit as in SoFi (MIT): the pump moves water between chamber L and R. The chambers start pre-filled (`V_prefill`).

### 3.3 Tail (`TailEquivalent`, 1 DOF)
- Equivalent rotational motion of the tail angle θ: `(J + J_added)·θ̈ = τ_hyd − k·θ − c·θ̇ − c_h·|θ̇|·θ̇`.
- `τ_hyd = A_eff·r_eff·(p_L − p_R)` **or** (better, describe the difference) `θ` follows from the difference of the chamber volumes through the system stiffness. Pick one formulation, keep it energy-consistent (hydraulic work = mechanical work) and explain it in the documentation.
- `Modelica.Mechanics.Rotational` connector, so power is computed automatically.
- Added mass `J_added` and hydrodynamic damping `c_h` are placeholders.

### 3.4 Forward propulsion (`SurgeDynamics`, 1D)
- `(m + m_added_x)·dU/dt = T − ½·ρ·C_d·A·|U|·U`.
- Thrust `T`: an **explicitly marked placeholder empirical model** as a function of the lateral speed of the tail tip (e.g. quadratic in `L·θ̇`). State in Documentation that this is the weakest link of the model and that its parameter must be determined from a tethered thrust measurement or from the CFD/MuJoCo demo.

### 3.5 Ballast (`BallastSyringe` + `VerticalDynamics`)
- Syringe/piston: DC motor → lead screw (`Modelica.Mechanics.Rotational` → `Translational` via `IdealGearR2T`) → bladder volume `V_b = A_piston·x`, end stops.
- Vertical motion: `(m + m_added_z)·z̈ = ρ·g·(V_hull + V_b) − m·g − ½·ρ·C_dz·A_z·|ż|·ż`.
- Optionally: compressibility of the hull/air with depth (`V_hull` changing with pressure) as a lesson in why uncompensated ballast is vertically unstable. If you add it, make it switchable.

### 3.6 Control (`Control`)
- CPG: `u(t) = A·sin(2π f t) + bias` with saturation and a start-up ramp.
- `DepthPID`: `z_ref → syringe motor speed`, anti-windup, saturation. You may use `Modelica.Blocks.Continuous.LimPID` and describe its parameters.

## 4. Energy balance (key feature of the demo)

Add power and energy variables (integrals) to the scenario model: energy from the battery, losses in the motor resistance, pump losses (leakage + η_m), losses in the pipes, in the relief valve, power dissipated into the water by the tail (`c·θ̇² + c_h·|θ̇|·θ̇²`), forward propulsion work `T·U`. Check that the balance closes (sum of losses + change of stored energy = energy from the battery) with a numerical error < 1%. This is the correctness test of the whole model.

## 5. Scenarios (`Examples/`)

1. `HydraulicsStep`: step (ramp) of the pump command, tail locked → pressures, flow, motor current.
2. `TailFlapping`: sine command, tail free → tail angle, pressures, current.
3. `FrequencySweep` (via `sweep.py`): f = 0.5…4 Hz → tail amplitude, peak pressure, mean current. **Lesson**: where the bandwidth is limited by the pump flow and where by the relief valve.
4. `ReliefValveDemo`: command amplitude too large → the valve opens, the energy loss is visible.
5. `EnergyBudget`: 60 s of swimming → pie/bar chart of the energy breakdown + estimated battery run time (capacity is a placeholder).
6. `DepthControl`: steps of the depth setpoint (−0.5 → −1.5 → −1.0 m) → depth, bladder volume, syringe motor current.
7. `SwimForward`: CPG + surge → steady speed vs frequency (with an explicit caveat about the thrust model).
8. **(Optional)** `HydraulicsMSLFluid`: the stage 1 circuit built from `Modelica.Fluid` + `Modelica.Media.Water.ConstantPropertyLiquidWater`, comparison of results and complexity.

## 6. FMU

- `export_fmu.py`: export the "H-bridge + motor + pump + chambers + tail" subsystem as an **FMU 2.0 Co-Simulation** (input: command `u`; outputs: tail angle and speed, torque, `p_L`, `p_R`, current).
- `fmu_demo.py`: run the FMU through **FMPy** in a Python loop with a 2 ms step and compare with the OpenModelica result (they should match).
- Note in the README: the FMU contains compiled binaries and **only works on the system it was built on**. Describe how to plug it into the MuJoCo demo in the future (torque from the FMU → joint actuator), but do not implement the hookup itself unless the user asks.

## 7. Implementation stages

1. Package skeleton, hydraulic connector, `Pipe` + `Reservoir` + test (Hagen–Poiseuille law for the laminar part: check the pressure drop analytically).
2. `Chamber` + `ReliefValve` + tests (volume conservation in a closed circuit, `p ≤ p_set + tolerance`).
3. DC motor + `GearPump` → scenario 1.
4. `TailEquivalent` → scenarios 2–4.
5. Energy balance → scenario 5 (balance closure test).
6. Ballast + vertical motion → scenario 6.
7. Surge → scenario 7.
8. FMU + FMPy.
9. (Optional) `Modelica.Fluid` variant.

## 8. Tests (`scripts/check_tests.py`)

- Every model in `Examples/` and `Tests/` passes `checkModel` (balanced) and simulates.
- Pipe: Δp matches the analytical formula (< 1%).
- Closed circuit: `V_L + V_R = const` (< 1e-9 relative).
- Valve: pressure does not exceed `p_set` by more than the assumed characteristic tolerance.
- Ballast statics: at neutral `V_b` ż → 0; larger `V_b` → ascent.
- Energy balance closed < 1%.
- FMU vs OpenModelica: tail angle difference < 1% of the amplitude.
- Directions: positive pump command → positive tail angle (convention described in the README).

## 9. README – mandatory sections

- Versions (OpenModelica, MSL, OMPython, FMPy) and installation.
- How to open the package in **OMEdit** and see the connection diagrams (the best way to understand an acausal model). Simple component icons so the diagram is readable.
- How to run `run_all.py`, `sweep.py`, `export_fmu.py`.
- What each plot shows, 2–3 sentences for a learner.
- **Limitations**: tail as 1 DOF, thrust from an empirical placeholder, no coupling between motions (surge, vertical and rotation independent), no spatial hydrodynamics, unidentified parameters.
- **Calibration plan**: which parameters to measure on the bench (motor resistance and constant, pump flow vs pressure, chamber p–V curve, tail torque/angle, tethered thrust) and in what order.

## 10. Definition of done

- `python scripts/run_all.py` compiles and simulates all scenarios, saves plots in `results/`.
- `python scripts/check_tests.py` passes.
- The FMU runs in FMPy.
- The package opens in OMEdit with readable diagrams.
