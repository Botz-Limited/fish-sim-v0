# fish-sim-v0 – system model of a robotic fish in OpenModelica

A simplified, **educational and uncalibrated** model of a robotic fish in Modelica: DC motor → pump → pipes → chambers → tail, plus ballast and forward motion. Specification: [`SPEC_fish_openmodelica_demo.md`](SPEC_fish_openmodelica_demo.md). All design parameters are placeholders to be identified.

## Progress

| Stage | Scope | Status |
|---|---|---|
| 1 | Hydraulic connector, `Pipe`, `Reservoir`, `VolumeFlowSource` + tests | done |
| 2 | `Chamber` (p–V curve from a table or CSV), `ReliefValve` + tests | done |
| 3 | `Battery`, `HBridge`, `DCMotor`, `GearPump` → scenario `HydraulicsStep` | done |
| 4 | `TailEquivalent`, `CPG`, subsystem `TailDrive` → `TailFlapping`, `FrequencySweep` (`sweep.py`), `ReliefValveDemo` | done |
| 5 | Energy balance in `TailDrive` → `EnergyBudget` + balance closure test | done |
| 6 | `BallastSyringe`, `VerticalDynamics`, `DepthPID` (cascade) → `DepthControl`, test `BallastStatics` | done |
| 7 | `LighthillFin` (thrust, placeholder), `SurgeDynamics` → `SwimForward`, `sweep.py --swim`, tests `SurgeTerminalVelocity`, `FinPrescribedMotion` | done |
| 8 | `TailDriveFMU` → FMU 2.0 CS (`export_fmu.py`), FMPy loop and comparison with OpenModelica (`fmu_demo.py`) | done |
| 9 | (optional) `HydraulicsFluid` on `Modelica.Fluid` connectors → `HydraulicsMSLFluid`, comparison (`compare_fluid.py`) | done |
| 10 | Calibration: `FishRobot.Calibration` test benches and `calibrate.py` for steps 2–11 of the calibration plan | done, verified on synthetic measurements |

## Versions

| Tool | Version |
|---|---|
| OpenModelica (omc, OMEdit, OMSimulator) | 1.27.1 |
| Modelica Standard Library | 4.1.0 (units: `Modelica.Units.SI`) |
| OMPython | 4.1.0 (class `ModelicaSystemOMC`; the old `ModelicaSystem` is deprecated) |
| FMPy | 0.3.32 |
| Python | 3.14 |

## Installation (Ubuntu)

```bash
setup/install_system.sh   # sudo: OpenModelica apt repository, omc/OMEdit/OMSimulator, git, python3-venv
setup/install_user.sh     # no sudo: .venv from requirements.txt + MSL 4.1.0 via the omc package manager
```

## Running

```bash
.venv/bin/python scripts/check_tests.py          # all models from Tests/ and Examples/
.venv/bin/python scripts/check_tests.py Pipe     # only models with "Pipe" in the name
.venv/bin/python scripts/run_all.py              # all scenarios from Examples/ -> results/examples/
.venv/bin/python scripts/sweep.py               # frequency sweep 0.25–4 Hz -> results/sweep/
.venv/bin/python scripts/sweep.py --A 0.5 --n 30   # different command amplitude, denser grid
.venv/bin/python scripts/sweep.py --swim        # swimming speed vs frequency -> results/sweep/swim_sweep.*
.venv/bin/python scripts/export_fmu.py          # tail drive FMU -> results/fmu/TailDrive.fmu
.venv/bin/python scripts/fmu_demo.py            # FMU in an FMPy loop vs OpenModelica -> results/fmu/fmu_vs_om.png
.venv/bin/python scripts/compare_fluid.py       # custom hydraulics vs Modelica.Fluid -> results/fluid/fluid_vs_own.png
.venv/bin/python scripts/calibrate.py motor     # DC motor identification (synthetic measurement) -> results/calibration/
.venv/bin/python scripts/calibrate.py motor --data pomiar.csv --U 6 --t-step 0.01   # the same on a real measurement
.venv/bin/python scripts/calibrate.py pump      # pump identification (needs the result of the motor step)
.venv/bin/python scripts/calibrate.py pipe [--data punkty.csv --l 0.2]   # pipe identification from Δp(Q)
.venv/bin/python scripts/calibrate.py chamber [--data cykle.csv --V-rest 5e-6]   # chamber p–V curve -> CSV for Chamber
.venv/bin/python scripts/calibrate.py valve [--data punkty.csv]   # relief valve from Q(Δp), with poppet hysteresis
.venv/bin/python scripts/calibrate.py tail-static [--data punkty.csv --k small]   # tail D_tail and k
.venv/bin/python scripts/calibrate.py tail-dynamic [--data-air a.csv --data-water w.csv]   # J, c, J_added, c_h
.venv/bin/python scripts/calibrate.py thrust [--data punkty.csv --noise-abs 1e-4 --noise-rel 0.05]   # fin C_T
.venv/bin/python scripts/calibrate.py hull [--data-tow h.csv --data-coast w.csv --A 0.005 --m 1.0]   # C_d, m_added_x
.venv/bin/python scripts/calibrate.py ballast [--data-turns t.csv --data-depth d.csv --data-vertical v.csv]   # ballast and heave
```

Each model is checked (`checkModel`: number of equations = number of unknowns), compiled, simulated and compared with an analytical result. Models are processed in parallel (a separate process and a separate omc session per model). Plots go to `results/tests/`.

Performance settings are in `scripts/om_config.py`. Hydraulic variables in the models have `nominal` attributes (pressure 1e5 Pa, pressure difference 1e4 Pa, flow and volume 1e-5). The solver scales its tolerances with them; without them it would treat quantities of order 1e-5 m³ as if they were of order 1. In purely hydraulic tests this improved accuracy by several orders of magnitude (e.g. inertance: error from 1e-3 down to 2e-8). C code compilation runs in parallel on all cores, and the generated code is built with `-O2`, which gives about 8% faster simulation. `-O3`, `-march=native` and ccache gave no measurable gain.

## Opening in OMEdit

`File → Load Library…` (or `Open Model/Library File`) → select `FishRobot/package.mo`. In the library tree expand `FishRobot.Tests`, open a model and switch to the *Diagram* view. Hydraulic connectors are blue: a filled circle is `port_a`, an empty one is `port_b`.

`sweep.py` compiles the model once and then runs the built executable in parallel for each frequency (`scripts/om_fast.py`). It changes parameters via `-override` and reads results directly from the `.mat` files (`scripts/om_results.py`). 16 simulations take about 0.2 s plus about 1 s of compilation. In OpenModelica 1.27.1 `-override` does not change the experiment settings (`stopTime`, `tolerance`), so `om_fast` replaces them in a copy of the `_init.xml` file.

## Tail: formulation

The tail is a rotary piston with displacement `D_tail = A_eff·r_eff` (`Tail.HydraulicBender`):

- tail motion displaces fluid: `Q_L = D_tail·θ̇`, `Q_R = −D_tail·θ̇`,
- the pressure difference produces torque: `τ = D_tail·(p_L − p_R)`.

The same constant in both equations makes hydraulic power equal to mechanical power by definition. The chamber p–V curve describes only wall swelling with the tail blocked, so the water pushed by the pump splits into two parts: chamber swelling and tail motion. I rejected the "θ from the volume difference through stiffness" variant, because it ignores tail inertia and gives no torque to pass on, e.g. to MuJoCo.

## Hydraulics: why a custom package

`Modelica.Fluid` is powerful but heavy for a small system with incompressible water: it needs a medium model, an enthalpy balance and careful initialization. The custom `HydraulicPort` connector has only two variables:

- `p` – pressure (potential, equal at all ports in a node),
- `flow V_flow` – volume flow rate (sums to zero in a node).

Their product `p·V_flow` is power in watts, so the energy balance follows directly from the connections, like `v·i` in electrics. It is the simplest way to see how acausal connectors work.

The same circuit built on `Modelica.Fluid` and a comparison of both versions is described in [Modelica.Fluid instead of the custom package](#modelicafluid-instead-of-the-custom-package-stage-9).

**Direction convention:** pump command `u > 0` ⇒ the shaft turns in the positive direction (`ω > 0`) ⇒ the pump pushes water from chamber R to chamber L ⇒ `p_L > p_R`. In stage 4 the same sign gives a positive tail angle.

**Flow sign convention:** `V_flow > 0` means flow **into** the component through the given port. In two-port elements `V_flow` (without a port prefix) is the flow from `port_a` to `port_b`, and `dp = port_a.p − port_b.p`.

## What the test plots show (stages 1–3)

- **`pipe_laminar.png`** – pressure drop rises linearly with flow, following the Hagen–Poiseuille law `Δp = 128·μ·l·Q / (π·d⁴)`. The Reynolds number stays below 2300, so the laminar formula applies. Note the `d⁴`: a pipe half as wide gives 16 times the resistance.
- **`pipe_quadratic.png`** – with sinusoidal flow the Δp curve has "flat spots" near zero (the linear part dominates) and sharp peaks (the quadratic part dominates). The bottom panel shows the error of the regularization `Q·√(Q² + Q_small²)` instead of `|Q|·Q`. It is of order 10⁻⁴ Pa, and the simulation crosses zero without any events.
- **`pipe_turbulent_vs_msl.png`** – flow rises from zero to Re ≈ 12 700, and the same flow passes through `Hydraulics.Pipe` and through `Modelica.Fluid.Pipes.StaticPipe` (`DetailedPipeFlow`). Up to Re ≈ 1500 both curves are the Hagen–Poiseuille line (difference 0.00%). Above Re ≈ 4000 resistance grows almost with the square of flow, and the Haaland formula differs from Colebrook in MSL by less than 0.5%. In the transitional range the models interpolate differently (MSL starts the transition earlier) and differ by up to about 6%.
- **`pipe_inertance.png`** – after a step in pressure difference the flow does not jump, because the water column has mass. It rises exponentially with time constant `τ = L/R ≈ 0.5 s`, exactly like current in an RL circuit.

- **`chamber_closed_loop.png`** – two chambers connected by a pipe, starting at 8 ml and 3 ml. Fluid flows into the lower-pressure chamber, "overshoots" due to the inertia of the water column and oscillates with damping around 5.5 ml. It is an RLC circuit: the chambers are capacitance, the fluid column is inductance, pipe friction is resistance. The bottom panel shows that the total volume changes only at the level of 10⁻¹⁵ ml, i.e. within floating-point rounding.
- **`relief_valve_limit.png`** – a chamber filled ever faster. Gauge pressure rises slowly at first (soft silicone), then steeply (silicone stiffens). Once it exceeds `p_set`, the valve takes over the entire flow and pressure stops at `p_set + dp_open`, i.e. where the valve passes the nominal flow.

- **`dc_motor_no_load.png`** – motor start-up through the H-bridge at `u = 0.6`. Speed rises exponentially with the mechanical time constant `J·R/k²` to the analytical value. The power balance (cell = losses + increase of kinetic and magnetic energy) closes at every instant.
- **`gear_pump_characteristic.png`** – pump flow at constant speed decreases linearly with pressure rise. The slope is the leakage `k_leak`. At negative Δp the fluid itself helps the pump and the pump works as a hydraulic motor.

## Scenarios (`results/examples/`)

- **`hydraulics_step.png`** (scenario 1) – pump command ramps to 0.5, tail blocked:
  - The motor accelerates and the inrush current has a short peak: at low speed the back-EMF is small.
  - The pump moves water from chamber R to L. The pressure difference rises ever faster because the silicone stiffens.
  - At about 51 kPa the relief valve opens. From then on water circulates in the pump → valve loop, the chambers stand still and all pump power turns into heat.
  - After the command is removed, the bridge short-circuits the motor and the stretched chambers push water back, mainly through pump leakage. The motor then works as a dynamic brake, hence the negative current.
  - With placeholder parameters the motor is heavily oversized for the pump. Current under load is only about 0.35 A, so the parameters must be identified before drawing conclusions about drive sizing.

- **`hydraulics_msl_fluid.png`** (scenario 8, optional) – the same run as `hydraulics_step.png`, computed with `Modelica.Fluid` components. By eye the plots are identical. The differences are shown in `results/fluid/fluid_vs_own.png` (section below).

- **`tail_flapping.png`** (scenario 2) – 1 Hz sine, free tail:
  - The tail angle lags the command, because the pump first has to move the fluid.
  - Chamber pressures change in antiphase.
  - Battery current has twice the frequency and is negative at times. In each half-period the motor first accelerates and then brakes, returning energy to the battery.
  - The amplitude grows over 2 periods, because the CPG starts with a gentle ramp.
- **`relief_valve_demo.png`** (scenario 4) – full command at 0.25 Hz. The pressure difference reaches ±`p_set`, the valves open and the tail angle peaks flatten (about ±31°). The bottom panel shows that about 43% of the hydraulic energy delivered by the pump turns into heat in the valves. The rest is mainly pipe friction, because at full command the flow is turbulent.

- **`depth_control.png`** (scenario 6) – depth setpoint steps −0.5 → −1.5 → −1.0 m:
  - To go deeper, the controller first shrinks the bladder (the fish gets heavier), and before the target enlarges it again to brake. The fish descends at a constant speed of about 3 cm/s, because the setpoint filter turns the step into a ramp.
  - Overshoot about 6%, steady-state error at −1.0 m about 5 mm. The piston works in the 15–23 mm range of a 40 mm stroke, so it never reaches the end stops.
  - The feedforward is deliberately inaccurate (5.5 ml instead of 6 ml). The integral term removes the difference, but slowly (`Ti = 120 s`): at −1.5 m the fish hangs 2–4 cm too low for about 50 s.
  - The syringe motor draws current only while the piston moves (peaks about 0.2 A). Holding depth with a rigid hull costs nothing.

- **`swim_forward.png`** (scenario 7) – CPG 1 Hz, command amplitude 0.8, 120 s:
  - Thrust pulses at twice the frequency, because the fin pushes in both stroke directions. It drops to zero at times, when the tail reverses.
  - Speed rises slowly and settles at about 6.4 cm/s, when mean thrust (about 3 mN) equals hull drag. The time constant is about 20 s, because with small thrust the drag takes a long time to catch up.
  - Of the 216 J drawn from the battery, the fin gets only about 40 mJ, and useful work (against hull drag) is about 20 mJ, i.e. 0.01%. The rest is tail drive losses, described in scenario 5.

## Swimming forward (scenario 7)

**Note: the thrust model is the weakest link of the whole model.** `Propulsion.LighthillFin` follows Lighthill's elongated-body theory for a rigid fin rotated by angle θ:

- water velocity relative to the fin: `w = L·θ̇ + U·θ`,
- thrust: `T = ½·m_a·((L·θ̇)² − U²·θ²)`, where the added mass per metre is `m_a = C_T·ρ·π·s²/4`,
- torque braking the tail: `τ = m_a·U·L·w`.

The parameters `s_fin` and `C_T` are placeholders. They must be determined from a tethered thrust measurement or from the CFD/MuJoCo demo. The speed figures show trends, not design values.

**Energy consistency.** The fin does not add thrust "out of thin air". It takes power `P_fin = τ·θ̇` from the tail through the mechanical connector `TailDrive.flange_tail`, and at every instant `P_fin = T·U + P_wake`, where `P_wake = ½·m_a·U·w² ≥ 0` is the energy left in the vortex wake. The balance of the whole robot (battery → drive losses → wake → hull drag → kinetic energy) closes with an error of about 1e-6. For a sine, fin efficiency is `½·(1 − (U/Lω)²)`, i.e. at most 50%. With U ≪ L·ω it is close to 50%.

**`swim_sweep.png`** (`sweep.py --swim`, `A = 1`, 0.25–4 Hz, 150 s per point):

| f [Hz] | U [cm/s] | θ [°] | θ·f [°·Hz] | P_bat [W] |
|---|---|---|---|---|
| 0.25 | 7.6 | 31.1 | 7.8 | 1.1 |
| 0.5 | 8.5 | 16.9 | 8.5 | 1.25 |
| 1 | 8.0 | 7.7 | 7.7 | 2.9 |
| 2 | 7.3 | 3.4 | 6.9 | 7.9 |
| 4 | 6.6 | 1.6 | 6.2 | 16.6 |

**Lesson: faster flapping does not speed up the fish when the pump is the limit.** Mean thrust grows with the square of the trailing-edge speed, i.e. with (θ·f)². Above about 0.5 Hz the pump moves a fixed volume per half-period, so θ·f is almost constant (see scenario 3). Thrust and speed stand still or even drop slightly, while battery power rises 15 times, because the motor reverses the rotor ever more often. Below 0.5 Hz the relief valve is the limit: the amplitude stops growing, so θ·f and speed drop. With placeholder parameters the optimum is about 0.5 Hz. To swim faster you need more pump flow or a larger `D_tail`, not a higher frequency.

## Ballast and heave (scenario 6)

The syringe (`Buoyancy.BallastSyringe`) is an H-bridge, a DC motor, a gearbox, a lead screw and a piston with spring-damper end stops. Hydrostatic pressure pushes the piston in. `Buoyancy.VerticalDynamics` treats the fish as a point mass with added mass and quadratic drag: each millilitre above the neutral volume gives about 0.01 N of upward force.

**Lesson: a rigid hull is neutrally stable, a hull with air is unstable** (test `BallastStatics`). With a rigid hull buoyancy does not depend on depth, so the fish stays where it was put. An air pocket compresses with depth: a fish neutral at −3 m, moved 1 cm down, becomes heavier and after 60 s is 40 cm lower. Hence the need for active control.

**Cascade controller (`Control.DepthPID`).** There are three integrations from motor command to depth, so a single PID is hard to tune. The inner loop (P) sets the bladder volume, and the outer loop (`LimPID` with anti-windup) turns depth error into a volume setpoint. Tuning details and the `LimPID` initialization trap are in the model documentation.

`DCMotor` has an `initRotor` parameter. In the syringe the shaft is rigidly coupled to the piston through the gearbox, so only the piston has initial conditions. Otherwise the system would be overdetermined.

## Energy balance (scenario 5)

The `TailDrive` subsystem integrates each loss separately (`E_loss_*`) and computes stored energy (`E_stored`): rotor, inductance, chamber walls, tail. The variable `E_balance_error = E_battery − E_loss_total − ΔE_stored` must be close to zero. `check_tests.py` checks this automatically in every model with a `drive` subsystem; the error is of order 1e-6 of the battery energy. This is a test of the whole model: a wrong sign, a missing term or inconsistent equations in any component would break the balance.

The H-bridge is lossless. Ambient pressure power cancels out in a closed circuit, because volume circulates rather than disappears. Energy delivered by the tail axle to the outside (e.g. to the fin in scenario 7) is counted by a separate term `E_mech_out`; when nothing is connected it is zero.

**`energy_budget.png`** – 60 s of flapping at 1 Hz and command amplitude 0.8. The estimated run time of the tail drive alone is about 9.2 h at 1.8 W with a placeholder 16.3 Wh battery.

| Item | Share |
|---|---|
| motor: winding R·i² | 78.5% |
| pipes | 9.3% |
| motor: bearings | 8.4% |
| pump: friction | 2.7% |
| battery | 0.8% |
| tail (water and material) | 0.1% |

**Lesson: with a reversing pump, energy is eaten by reversing the rotor, not by the water.** At about 550 rad/s the rotor holds about 0.8 J of kinetic energy. Twice per period the motor has to dissipate it and build it up again, and the braking and accelerating current heats the winding. Check: with 10 times lower rotor inertia, battery energy drops more than 4 times, and the winding share from 79% to 4%, at the same tail amplitude. Design conclusions to verify with real parameters:

- a low-inertia motor (e.g. coreless),
- a gearbox and a slower motor, because kinetic energy grows with ω²,
- a unidirectional pump with a directional valve instead of reversing the pump.

## Frequency sweep (`results/sweep/`, scenario 3)

`frequency_sweep.png` and `frequency_sweep.csv` show full command (`A = 1`) at frequencies 0.25–4 Hz. The range starts at 0.25 Hz rather than 0.5 Hz as in the specification, so that the valve-limited region is visible with placeholder parameters.

**Lesson: two different bandwidth limits.**

- **Low frequencies (≤ about 0.4 Hz): the valve is the limit.** The pump has enough time to build up `p_set`. The valve opens (more than 20% of pump flow goes through the valves), and tail amplitude is limited by pressure: `θ ≈ D_tail·p_set / k_total`.
- **Higher frequencies: pump flow is the limit.** In a half-period the pump moves at most `Q_max/(2f)`, so amplitude falls as `1/f` (the product θ·f is almost constant). The valves stay closed.
- **Current rises with frequency even though amplitude falls.** The motor has to reverse the rotor ever more often, and much of the rotor's kinetic energy at each reversal turns into heat in the winding (`R·i²`). Fast flapping with a small pump is therefore inefficient. A larger pump or a gearbox would be better.

**CPG ramp and the pump as an integrator.** The pump integrates flow into volume. A sine switched on from zero would therefore give a volume offset `(1 − cos ωt)/ω`, and the tail would flap around a deflected position for many periods, because the offset leaks away only through pump leakage. That is why the CPG ramps up gently over 2 periods (`n_ramp`).

## FMU (stage 8)

`export_fmu.py` exports `Subsystems.TailDriveFMU` as an **FMU 2.0 Co-Simulation**: battery, H-bridge, motor, pump, pipes, chambers, valves and tail. The input is the command `u`, and the outputs are `theta`, `w_tail`, `tau_tail`, `p_L`, `p_R` and `i_motor`. `TailDriveFMU` is a thin wrapper around `TailDrive`. The mechanical connector `flange_tail` (angle and torque as a flow variable) cannot be exposed as a plain FMU input or output, so it stays inside, unconnected.

**Solver in the FMU: CVODE** (`--fmiFlags=s:cvode`). By default OpenModelica puts explicit Euler with a step equal to the communication step into a CS FMU. With stiff hydraulics and a 2 ms step such an FMU fails after about 0.1 s. CVODE chooses its own steps within each communication step, and the sundials libraries are packed into the FMU (1.8 MB).

`fmu_demo.py` runs the FMU in a Python loop via FMPy (`FMU2Slave`) with a 2 ms step. Python computes the CPG command with the same formula as `Control.CPG`. The result is compared with the `TailFlapping` scenario computed in OpenModelica (`fmu_vs_om.png`):

- command sampled **at mid-step** `u(t + h/2)`: max angle difference 0.016% of amplitude,
- command sampled **at the start of the step** `u(t)`: 0.62% of amplitude.

**Lesson: in co-simulation the input is constant over a communication step** (ZOH). Sampled at the start of the step it lags by h/2 = 1 ms on average, and at 1 Hz this gives a phase error of order 2π·f·h/2 ≈ 0.6%. Sampling at mid-step removes this delay. When coupling two simulators there is no such trick, because the input comes from the other simulator. Then the step has to be chosen for the fastest dynamics of the coupling.

**The FMU works only on the system it was built on.** It contains compiled binaries (`binaries/linux64`, glibc and sundials from this machine). On another system it has to be rebuilt (`export_fmu.py`).

**How to hook the FMU into the MuJoCo demo in the future** (not implemented):

1. Add a tail load torque input to `TailDriveFMU`: `Rotational.Sources.Torque` on `drive.flange_tail`. Then the FMU gets the water reaction and the inertia of the rest of the fish from MuJoCo, rather than just moving the tail in a vacuum.
2. In the MuJoCo loop, at each step: `fmu.setReal(u, tau_load)` → `fmu.doStep(t, h)` → read `tau_tail` → `data.ctrl[tail_joint] = tau_tail` (torque actuator on the tail joint) → `mujoco.mj_step`. The load torque for the next step is the torque that the water and the rest of the body exert on the tail joint in MuJoCo (the exact `mjData` fields depend on how the demo models the fluid).
3. Communication step equal to the MuJoCo step (e.g. 2 ms) or a multiple of it. The coupling is explicit (values from the previous step), so with a stiff tail the step must be small compared with the tail's natural period (below 0.17 s: 5.8 Hz without hydraulics, and chamber stiffness raises this frequency further).
4. Hydraulics in the FMU, body motion in MuJoCo. Then `J_added`, `c_h` and `LighthillFin` should not be counted twice, because the MuJoCo fluid model provides these effects.

## Modelica.Fluid instead of the custom package (stage 9)

`Examples.HydraulicsMSLFluid` is the `HydraulicsStep` circuit (battery, H-bridge, motor, pump, pipes, chambers, valves) with hydraulics on `Modelica.Fluid` connectors and the medium `Modelica.Media.Water.ConstantPropertyLiquidWater`. The components are in `FishRobot.HydraulicsFluid`. `compare_fluid.py` simulates both models and compares them (`results/fluid/fluid_vs_own.png`).

**What was taken from the library and what had to be written:**

| Element | Custom package | Modelica.Fluid version |
|---|---|---|
| Pipe | `Hydraulics.Pipe` | from the library: `Pipes.StaticPipe` (`DetailedPipeFlow`) + `Fittings.SimpleGenericOrifice` |
| Relief valve | `Hydraulics.ReliefValve` | assembled from the library: `Valves.ValveLinear` + `Sensors.RelativePressure` as the pilot line |
| Gear pump | `Hydraulics.GearPump` | **written** on `Interfaces.PartialTwoPortTransport`. MSL has only centrifugal pumps |
| Compliant chamber | `Hydraulics.Chamber` | **written** on `Vessels.BaseClasses.PartialLumpedVessel`. MSL vessels have a fixed volume or a free liquid surface |

**Complexity** (output of `compare_fluid.py`, 24 cores):

| | custom package | Modelica.Fluid |
|---|---|---|
| equations after flattening (of which trivial) | 185 (109) | 425 (222) |
| continuous states | 8 | 8 |
| compilation | about 1.1 s | about 1.4 s |
| 3 s simulation | about 0.02 s | about 0.15 s (about 6× longer) |

The equal number of states is a coincidence. The Fluid version additionally has the water temperature in each chamber, but lacks the elastic energy integrals `E_elastic` that we added to the custom chamber for the energy balance. Temperature changes by less than 0.01 K, so with constant-property water it contributes nothing, but the solver still has to compute it.

**Results:** pressures, pump flow and motor current differ by 0.03–0.5% of the signal maximum, valve flow by 0.9%. During fast pumping the flow reaches 16 ml/s and the Reynolds number in the 4 mm pipe about 5200, so the flow is turbulent. Pressure drop across the pipe: 3.08 kPa in the custom package, 3.07 kPa in Fluid. The valve characteristics differ by a few percent (described in `HydraulicsFluid.ReliefValve`), but in this circuit this is barely visible.

The first version of `Hydraulics.Pipe` computed friction only from the laminar formula. It then gave 1.8 kPa instead of 3.1 kPa, pressures differed from Fluid by 0.7–3.8%, and the shifted valve opening edge briefly caused up to 11% flow difference. Now the pipe has turbulent friction (Haaland formula, wall roughness) and a smooth transition between Re = 2000 and 4000. This is checked separately by the test `PipeTurbulentVsMSL`.

**Lessons:**

- **The library exposed a weakness of our model.** The Hagen–Poiseuille formula holds up to Re ≈ 2300, and in scenario 1 the flow is already turbulent. The first pipe version underestimated the resistance there by about 40%. Comparison with an independent implementation revealed a bug that the custom package's own tests could not catch, because they checked the model against its own assumptions. Tests that assume linear resistance (`PipeQuadratic`, `PipeInertance`) now explicitly set `useTurbulent = false`.
- **Regularization thresholds have to be checked per component.** The default `system.m_flow_small = 0.01 kg/s` is chosen for industrial plants, and for us it is the entire pump flow. In the model it is reduced to 1e-5 kg/s, but I checked that in this circuit it has no effect: `SimpleGenericOrifice` smooths the characteristic near zero according to `system.dp_small = 1 Pa`, and `DetailedPipeFlow` according to the Reynolds number. `m_flow_small` acts in other components (e.g. `Fittings` with `from_dp = false`) and in diagnostics. So at small flows you have to look into the component's code to see which threshold applies to it.
- **The Fluid connector carries more:** mass flow rate and stream variables (enthalpy, composition, `inStream()`). Every new component must define what flows out of each port. Also, only one element can be connected to each vessel port (`nPorts`).
- **Alias warnings** during compilation (`The model contains alias variables with redundant start and/or conflicting nominal values`) come from start values inside MSL (e.g. `medium.T` and `state.T`). They are harmless.
- **When to use `Modelica.Fluid`:** when temperature matters (oil heating, heat transfer), compressibility or two-phase flow, or when the model has to connect to other libraries based on `Modelica.Media`. In this project (incompressible water, a few components, energy balance as a test) the lightweight package is simpler and about 6× faster.

## Chamber p–V curve from a file

The placeholder p–V curve can be replaced with data from the SOFA demo or from a measurement without changing code. In `Chamber` set `tableOnFile = true`, and point `fileName` to `Modelica.Utilities.Files.loadResource("modelica://FishRobot/Resources/Data/<plik>.csv")`. The file must have one header line and columns `V [m³], p − p_ambient [Pa]`, and the curve must be increasing. Example: `FishRobot/Resources/Data/chamber_pV_placeholder.csv` and the test `ChamberTableFromFile`.

## Limitations

The model answers questions like "are the pump and battery sufficient" and "where does the energy go", not "how exactly does the water flow". Main simplifications:

- **Tail as 1 DOF.** `Tail.TailEquivalent` is a rigid beam rotated by angle θ with a spring, damping and added mass. A real silicone tail bends along its length (wave shape), which this model cannot capture.
- **Placeholder thrust.** `Propulsion.LighthillFin` is Lighthill's reactive theory for a rigid fin with an empirical coefficient `C_T`. It has no flow separation, no finite-length vortex wake and no effect of fin shape. The speed figures show trends, not design values.
- **No coupling between motions.** Forward motion (`SurgeDynamics`), heave (`VerticalDynamics`) and rotation are independent. Tail flapping does not deflect the hull (no yaw or recoil), ballast does not change drag or trim, and swimming speed produces no lift.
- **No spatial hydrodynamics.** Hull drag is `½·ρ·C_d·A·U²` with constant `C_d`, and added mass is constant. There is no flow around the body, no waves, no pool walls and no currents.
- **Lumped-parameter hydraulics.** Water is incompressible and at constant temperature. Chambers have a static p–V curve without hysteresis or silicone viscoelasticity. The pipe has laminar and turbulent friction, but the transition between them (Re 2000–4000) is only an interpolation, and unsteady (oscillating) flow is computed with the steady-state characteristic. Valves have no poppet dynamics.
- **Simplified electrics.** The battery is a voltage source with internal resistance, with no voltage drop as it discharges. The H-bridge is ideal (averaged PWM, no switching losses). The motor has no magnetic saturation or winding temperature.
- **Unidentified parameters.** All values marked `PLACEHOLDER` in the code are order-of-magnitude estimates. With the current parameters the motor is, for example, heavily oversized for the pump (scenario 1).

## Calibration plan

Parameters are best identified from the energy source towards the water. Each step uses elements identified earlier, e.g. the motor from step 1 later serves as a torque sensor (torque = `k·i`).

| Step | Element | Bench measurement | Parameters |
|---|---|---|---|
| 1 | Battery | open-circuit voltage and voltage under a known load, at several states of charge | `U_nom`, `R_int`, `capacity_Wh` |
| 2 | DC motor | winding resistance (meter, locked shaft); no-load speed at several voltages; coast-down after power is cut; current response to a voltage step with the shaft locked | `R`, `k`, `b`, `J`, `L` |
| 3 | Pump | flow (measuring cylinder or flow meter) at several speeds and pressures (throttle valve at the outlet); motor current gives torque | `D_rev`, `k_leak`, `eta_m` |
| 4 | Pipes | pressure drop at several flows (two pressure sensors); check at what flow the characteristic stops being linear | `l`, `d`, `zeta`, `roughness` (and whether the turbulent transition matches `Re_lam`, `Re_turb`) |
| 5 | Chambers | quasi-static filling with a syringe and a pressure sensor, tail blocked; several fill–empty cycles (hysteresis) | p–V curve (`table` or CSV file), `V_prefill` |
| 6 | Relief valves | opening pressure and flow above it (pump into a closed circuit) | `p_set`, `dp_open`, `V_flow_nominal` |
| 7 | Tail (static) | torque on the blocked tail (force gauge on an arm) vs pressure difference; angle of the free tail vs pressure difference | `D_tail` (from torque), `k` (from angle) |
| 8 | Tail (dynamic) | free vibration after deflection: in air (`J`, `c`), then in water (`J_added`, `c_h`) | `J`, `c`, `J_added`, `c_h` |
| 9 | Thrust | tethered thrust (force gauge) at several frequencies and amplitudes; ideally also with flow in a tunnel | `C_T`, `s_fin`, `L_tail` |
| 10 | Hull | towing at constant speed or coast-down (speed decay after the drive is switched off) | `C_d·A`, `m_added_x` |
| 11 | Ballast and heave | weighing in water at several piston positions; vertical coast after a bladder step; buoyancy as a function of depth | `V_b_neutral`, `V_air0`, `m_added_z`, `C_dz·A_z`, `lead`, `gear_ratio` |

After each step it is worth rerunning the corresponding test from `FishRobot.Tests` with the new parameters and comparing the run with the measurement. Steps 1–8 concern only the tail drive and can be done on a bench without water (except step 8). Steps 9–11 need a pool.

### Motor identification (step 2): `calibrate.py motor`

On the bench one start-up is enough: a voltage step from a power supply to the motor with a free shaft, recording current and speed. The bench model is `FishRobot.Calibration.MotorStep`. Each of the five parameters shapes a different part of the response, so all can be determined at once:

- `R` – current peak (the rotor is still at rest),
- `L` – current rise to the peak,
- `k` – steady-state speed,
- `b` – steady-state current,
- `J` – acceleration time.

`calibrate.py` compiles the model once and fits the parameters by least squares (`scipy.optimize.least_squares`). Each call runs the built executable with `-override`, and Jacobian columns are computed in parallel. Parameters are fitted on a logarithmic scale, because they are all positive and span 6 orders of magnitude. The measurement file is a CSV with a header and columns `time [s], i [A], w [rad/s]`. The result contains a ready-to-paste modifier for the model, the 1σ uncertainty of each parameter and the correlation matrix (`results/calibration/motor_step_fit.{txt,png}`).

Without `--data` the script checks the procedure itself. It creates a "measurement" from a model with known parameters (25–100% different from the placeholders), adds sensor noise (0.03 A and 2 rad/s) and fits, starting from the placeholders. The whole thing takes about 1.5 s. All parameters come back with an error below 1.5σ. In 20 repetitions with different noise the spread of results matches the reported uncertainty, and the mean error is close to zero:

| Parameter | 1σ uncertainty | Spread over 20 repetitions |
|---|---|---|
| `R` | 0.09% | 0.09% |
| `L` | 1.0% | 0.9% |
| `k` | 0.03% | 0.03% |
| `J` | 0.11% | 0.10% |
| `b` | 1.2% | 1.4% |

**Lesson: signal weights determine the uncertainty.** Current and speed have different units and different noise, so residuals have to be divided by each sensor's noise. The noise is usually unknown, so after the first fit the script estimates it from the residuals of each signal separately and fits again. The first version weighted the signals by 1% of their range. Current was then relatively twice as noisy as speed, and the common residual variance hid this. The uncertainty of `b`, determined mainly from the steady-state current, therefore came out too small: 1.0% against an actual spread of 1.6%.

The correlation matrix shows what the experiment does not distinguish well. `k` and `b` are correlated (−0.84), because both set the steady-state operating point, and `R` and `J` (−0.77), because together they give the mechanical time constant `J·R/k²`. The uncertainty of `b` and `L` is the largest: the steady-state current is only about 0.08 A, and the current rise lasts about 0.5 ms, i.e. a few samples at 5 kHz. On a real bench a longer steady-state recording (current averaging) and faster current sampling help. The step saves the motor parameters with covariance to `results/calibration/motor_params.json`, which step 3 uses.

### Pump identification (step 3): `calibrate.py pump`

The motor from step 2 drives the pump, which pushes water from a reservoir through a throttle valve back to the reservoir (`FishRobot.Calibration.PumpBench`). The operating point is set by the supply voltage and the valve setting, and at each point, once speed has settled, `U, i, w, Δp, Q` are measured. The measurement file is a CSV with these columns (SI units). The pump equations are linear in the unknown parameters, so linear regression is enough instead of fitting a simulation:

- `Q = D·ω − k_leak·Δp` gives `D_rev = 2π·D` and `k_leak`,
- `k·i − b·ω = D·Δp/η_m` gives `η_m`. The left side is the shaft torque computed from current, i.e. the motor works as a torque sensor.

The bench model is used here only to generate a synthetic measurement: 3 voltages × 5 valve settings, the "true" motor from step 2 and a pump different from the placeholders, plus noise on the averaged values. Result (`results/calibration/pump_fit.{txt,png}`):

| Parameter | 1σ uncertainty | Spread over 2000 repetitions | Mean error |
|---|---|---|---|
| `D_rev` | 0.14% | 0.14% | 0.00% |
| `k_leak` | 4.1% | 4.0% | −0.1% |
| `eta_m` | 0.77% | 0.65% | −0.33% |

**Lesson: sensor error does not average out.** `eta_m` has a fixed error of −0.33%, even without any noise. It comes from the motor parameters from step 2 (`b` came out 1.2% too small there), and the same torque error is present at every operating point. More points reduce only the part of the uncertainty that comes from scatter (0.63%), while the part from the motor (0.36%) remains. That is why the script reports both parts separately and accounts for the correlation of `k` and `b` from step 2. Motor friction `b·ω` is from 15% (at the highest Δp) to over 80% (valve open) of the torque from current, so an accurate `b` matters more here than step 2 alone would suggest. A second trap: viscous pump friction (proportional to ω) would be indistinguishable from the motor's `b`, because on this bench they always occur together. If the real pump has such friction, it will show up as a constant torque at `Δp ≈ 0` in the right-hand plot.

Leakage is the least accurate (about 4%): at 85 kPa it is only 2.5 ml/s against about 30 ml/s of displacement, and the flow meter noise is 0.1 ml/s. More points at high Δp and low speed, where leakage is a larger share of the flow, help.

### Pipe identification (step 4): `calibrate.py pipe`

The pump pushes water through the pipe under test, and at a dozen or so operating points the flow and the pressure drop are measured with a differential sensor (`FishRobot.Calibration.PipeBench`). The measurement file is a CSV with columns `Q [m³/s], dp [Pa]`. Length is measured with a ruler (`--l`), and we fit the hydraulic diameter `d`, the minor losses `zeta` and the roughness `roughness`. The characteristic is nonlinear and changes from laminar to turbulent, so here again we fit a simulation. The model has no inertance, so the flow ramp in time serves only to step through the operating points. The pressure sensor noise is relative (percent of reading), and Δp changes over 3 orders of magnitude, so residuals are computed as `ln(Δp_sim/Δp_meas)`.

Synthetic measurement: 20 points from 1 to 40 ml/s (Re about 350–14 000), noise 1% of reading. The "true" pipe has a diameter of 3.6 mm instead of the nominal 4 mm, `zeta = 2.5` and a smooth wall (5 µm). Results from 200 repetitions (`results/calibration/pipe_fit.{txt,png}`):

| Parameter | 1σ uncertainty | Spread | Mean error |
|---|---|---|---|
| `d` | 0.23% | 0.24% | 0.0% |
| `zeta` | 2.2% | 2.3% | 0.1% |
| `roughness` | 29% | 32% | −7% |

**Lesson: not every parameter can be determined from a given experiment.** The diameter is determined mainly by the laminar range, because resistance there grows as `1/d⁴`: 0.23% uncertainty in `d` is about 1% of resistance. For this hose the 4 mm placeholder gave almost 2 times too little resistance. Roughness has 29% uncertainty, because below Re of about 15 000 a smooth hose behaves almost like a perfectly smooth pipe and the wall barely affects friction. Such a parameter is better taken from tables than fitted. Check: with a table roughness of 1.5 µm, i.e. 3 times too small, `d` shifts by 0.25% and `zeta` by 3.4%, i.e. by 1–1.6σ. Diameter and `zeta` are strongly correlated (0.96), because both raise resistance over the whole range. If `d` were measured separately (e.g. from the volume of water in a length of hose), the uncertainty of `zeta` would drop.

The laminar–turbulent transition model (interpolation between `Re_lam` and `Re_turb`) is an assumption here, not a result. In the synthetic measurement it matches "reality" by definition. On a real measurement wrong transition thresholds will show up as a hump in the residuals in the grey band of the plot.

### Chamber p–V curve (step 5): `calibrate.py chamber`

A syringe (ideally a syringe pump) slowly pushes water into and draws it out of the chamber with the tail blocked, and a pressure sensor sits at the chamber. Several cycles from slight vacuum to the valve opening pressure. The measurement file is a time-ordered CSV with columns `dV [m³]` (syringe volume relative to rest) and `p [Pa]` (gauge pressure). The result is not a set of parameters but the whole curve: `results/calibration/chamber_pV.csv` in the format for `Chamber(tableOnFile = true, fileName = ...)`. The rest volume (`--V-rest`) does not follow from this measurement; it has to be taken from CAD or from weighing. In the model only its position relative to `V_prefill` matters anyway, i.e. how much water was added above rest when closing the circuit.

Processing:

1. Splitting into strokes between syringe reversals and discarding the first cycle. Silicone is stiffer on its first stretch (Mullins effect).
2. At 15 nodes, local linear regression separately for the filling and emptying branches, averaged over cycles.
3. Skeleton curve = mean of both branches. The script checks that it is increasing, because `Chamber` will not accept anything else.
4. Area of the hysteresis loop `∮ p dV` from the raw data, i.e. the energy lost in each cycle.
5. Check in Modelica: `FishRobot.Calibration.ChamberBench` with the generated file (`fileName` via `-override`) runs through the whole range.

Synthetic measurement: the "true" chamber is softer than the placeholder at first, then stiffens more. It has hysteresis with a half-width of `300 Pa + 6%·|p|`, a first filling 15% stiffer, and noise (150 Pa, 0.01 ml). Four cycles from −3 to +10 ml. Results (`results/calibration/chamber_fit.{txt,png}`):

- the curve at the nodes differs from the true skeleton curve by at most 0.17% of the pressure range, and after interpolation in `Chamber` by 0.53%,
- without discarding the first cycle: 1.7%,
- hysteresis loop: 25 mJ per cycle at full stroke.

**Lesson: the tips of the loop do not lie on the skeleton curve.** At the syringe reversal point both branches meet, because the hysteresis needs some volume to "switch over". Nodes at the very ends of the stroke gave an error of 4.8% of the range. That is why the table ends 1 ml before the reversal points (`--margin`), and beyond that `Chamber` extends the curve linearly, which with rising stiffness underestimates pressure. The syringe stroke must therefore be planned with a margin beyond the chamber's working range in the robot.

**Does the lack of hysteresis in the model matter?** In the `EnergyBudget` scenario the chambers work between 6 and 10 ml, i.e. 1–5 ml above rest, at 2–12 kPa. The synthetic chamber loses about 3.9 mJ in such a cycle. For two chambers at 1 Hz that is about 8 mW, i.e. about 0.4% of the tail drive power (1.8 W). That is more than the tail losses in the balance (0.1%), but less than the pipes and bearings. Real silicone may have a wider loop, so this number has to be recomputed from the measurement. If it turns out significant, `Chamber` has to be extended with viscoelastic damping.

### Relief valve (step 6): `calibrate.py valve`

The pump from step 3 pushes water through the valve into a reservoir. Flow is increased in small steps and then decreased, and at each point the flow and the pressure difference across the valve are measured (`FishRobot.Calibration.ValveBench`). The measurement file is a CSV with columns `dp [Pa], Q [m³/s], up` (1 for rising flow, 0 for falling). We fit `p_set`, `V_flow_nominal` and `dp_smooth` separately for both branches and jointly.

**`dp_open` is not fitted.** In the model the conductance of the open valve is `V_flow_nominal/dp_open`, so the measurement determines only this ratio. Doubling both parameters gives an identical characteristic, and the Jacobian then has two proportional columns. `dp_open` stays as the reference point (5 kPa).

Synthetic measurement: a valve with a weaker spring (`p_set` = 46 kPa instead of 50), higher conductance, a gentler opening and a 2 kPa poppet hysteresis (opens at 47 kPa, closes at 45 kPa). 15 points in each direction, flow meter noise 0.05 ml/s and sensor noise 100 Pa. Results (`results/calibration/valve_fit.{txt,png}`):

| | `p_set` | Uncertainty |
|---|---|---|
| opening branch | 46.97 kPa | ±0.10 kPa |
| closing branch | 45.08 kPa | ±0.11 kPa |
| joint | 46.06 kPa | ±0.72 kPa |

Hysteresis determined from the difference of the branches: 1.89 kPa against the true 2 kPa.

**Lesson: residuals show what the model cannot do.** In the joint fit the residuals form two bands of opposite sign (bottom panel of the plot). The noise estimated from the residuals comes out at 1.9 ml/s, almost 40 times the flow meter noise. It is not noise but the hysteresis, which a model with a single `p_set` lacks. The uncertainty of the joint `p_set` (±0.72 kPa) is therefore 7 times larger than that of either branch alone, but it is an honest measure: that is how far the model departs from the valve. With a 2 kPa hysteresis (4% of `p_set`) a single `p_set` from the middle is enough for the energy balance. If the valve is meant to limit chamber pressure with a margin, the opening branch is what matters. `dp_smooth` is poorly determined (±51%), because it depends on only a few points right at the opening. It affects only the shape of the knee of the characteristic, though. Its "tail" below `p_set` acts in the model as additional leakage (about 0.2 ml/s at 35 kPa), so a separately measured closed-valve leakage (`G_leak`, e.g. collecting drops for a few minutes) makes sense only if it is larger.

### Tail, static (step 7): `calibrate.py tail-static`

Two measurements with a pressure difference set by syringes and measured with a differential sensor:

- **tail blocked**, force gauge on an arm: `τ = D_tail·Δp`, a line through zero gives `D_tail`,
- **tail free**, angle from a camera or encoder: `k·θ = D_tail·Δp`, the slope gives `D_tail/k`, and `k` follows from `D_tail`.

The measurement file is a CSV with columns `dp_blocked, tau, dp_free, theta` (SI). The script also checks whether the angle is linear in Δp: it additionally fits a `Δp³` term and reports its t statistic. The model has a constant `k`, while real silicone usually stiffens at large angles.

### Tail, dynamic (step 8): `calibrate.py tail-dynamic`

The tail is deflected and released from rest, with the chambers open to the reservoir, so the hydraulics add no stiffness or damping (`FishRobot.Calibration.TailDecay`). First in air, where we fit `J` and `c`, then in water, where we fit `J_added`, `c` and `c_h` with `J` from air. The initial deflection is fitted as an auxiliary parameter. The measurement files are CSVs with columns `time, theta`.

**Inertia cannot be determined from free vibration without stiffness.** The equation divided by `J` contains only `k/J`, `c/J` and `c_h/J`, so doubling all parameters gives the same θ(t). That is why `k` comes from step 7, and its error carries over 1:1 to all dynamic parameters. The script reports separately the uncertainty from the fit and the total one (from `k` and, for `J_added`, from `J` in air). In water the linear damping `c` and the quadratic damping `c_h` are correlated (−0.75). Only the dependence of the decay on amplitude distinguishes them, so `c` comes out with about 7% uncertainty. Additional vibrations from a small deflection, where `c` dominates, would help.

Synthetic measurement: a tail with `D_tail` = 1.6e-5 m³/rad, stiffness 2.6 N·m/rad at small angles, rising with angle (`k·(1 + 0.6·θ²)`), and linear dynamics with this stiffness. 17 static points up to ±40 kPa (±14°), vibrations sampled at 500 Hz with 0.17° noise. Results (`results/calibration/tail_*`):

| `--k` | `k` passed to step 8 | `J`: error | `J`: total uncertainty |
|---|---|---|---|
| `line` (straight line over the whole range) | 2.657 (+2.2%) | +2.2% | ±0.72% |
| `small` (small angles, with the Δp³ term) | 2.546 (−2.1%) | −2.1% | ±1.30% |

**Lesson: model mismatch gives an error you cannot see in σ.** The straight line over the whole range is biased: over 500 repetitions +2.3% on average with a spread of only 0.6%. Its σ is small but false, because the error in `J` is 3 times the reported uncertainty. The small-angle stiffness has no bias (2.605 on average against the true 2.6), but a larger spread (1.5%). Here the error is within σ. Which variant to choose depends on the working range: at 1 Hz the tail flaps by about 8°, and with the valve open by about 31°. General rule: if the nonlinearity test raises an alarm, `k` has to be measured in the range of angles where the tail really works. If that range is large, `TailEquivalent` needs a nonlinear spring. The nonlinearity is hardly visible in the residual plot, but the test detects it (t = −3.5).

### Fin thrust (step 9): `calibrate.py thrust`

The fish is attached to a force gauge, in a pool (`U = 0`, tethered) and if possible in a water tunnel at several flow speeds. At each point mean thrust and tail angle amplitude are measured. In the tunnel the force gauge sees thrust minus hull drag, so at each speed the force with the tail at rest (tare) also has to be measured and subtracted. The measurement file is a CSV with columns `Theta [rad], f [Hz], U [m/s], T [N]`.

Mean thrust for a given angle sine is computed by `FishRobot.Calibration.ThrustBench` (`C_T = 1`). Thrust is linear in `C_T`, so `C_T` is determined by regression through zero. `s_fin` appears in the model only in the product `C_T·s_fin²`, which is why `s_fin` and `L_tail` are measured with a ruler. The script also checks the form of the model: it fits the static term and the speed penalty separately (`T = a·T(0) − b·(T(0) − T(U))`). In Lighthill's theory `b/a = 1`.

**Weights from the sensor noise model.** The force gauge noise has a constant part (`--noise-abs`, here 0.1 mN) and a relative part (`--noise-rel`, here 5%). At half amplitude thrust is about 0.3 mN, so the constant part dominates, and at full amplitude (about 3 mN) the relative part. Over 2000 repetitions ordinary regression underestimated the uncertainty of the tethered `C_T` (σ 2.95% with a spread of 3.86%). Regression weighted by relative noise only was even worse (spread 5.1%). Only weights from the full noise model give σ consistent with the spread (3.64% and 3.64%).

Synthetic measurement: a fin with `C_T = 0.6` and a speed penalty 1.5 times larger than in theory (e.g. due to flow separation). Amplitudes as in the frequency sweep (the pump limits θ·f), full and half command, 4 frequencies × 4 speeds (0–10 cm/s), 32 points in total. Results from 2000 repetitions (`results/calibration/thrust_fit.{txt,png}`):

| Estimator | Mean | Spread | σ |
|---|---|---|---|
| `C_T`, all points | 0.584 (−2.6%) | 2.0% | 2.3% |
| `C_T`, tethered only | 0.600 (0.0%) | 3.6% | 3.6% |
| speed penalty `b/a` | 1.50 | 0.12 | 0.14 |

**Lesson: a model of the wrong form gives a biased parameter, but it does not always matter.** `C_T` from all points is biased, because the model describes the drop of thrust with speed incorrectly. `C_T` from the tether alone does not have this problem, but has a larger spread. The script writes the tethered `C_T` into the model, because the robot swims slowly: at 1 Hz the trailing edge moves at about 63 cm/s, while the robot swims at 6 cm/s. The speed penalty there is about 1% of thrust, and a 50% error in it changes thrust by about 0.5%. It matters only for the maximum speed: thrust vanishes at `L·ω/√1.5` ≈ 51 cm/s instead of 63 cm/s. The form test detects `b/a = 1.5` (above 3σ) in only 74% of repetitions. It is decided by the few points with large `U²/(L·ω)²`, i.e. at low frequency and high flow speed (right-hand plot), not by the number of points.

### Hull (step 10): `calibrate.py hull`

Two measurements in a pool, both with the tail at rest:

- **towing** at constant speed, force gauge on a carriage: `F = ½·ρ·C_d·A·U²`. The area `A` is measured with a ruler (only the product `C_d·A` can be determined), and `C_d` comes from regression weighted by the force gauge noise model. File: `U [m/s], F [N]`.
- **coast-down** after release from the carriage, position from a camera above the pool (`FishRobot.Calibration.CoastDown`). File: `time [s], x [m]`, with `x = 0` at the moment of release.

**Coast-down depends only on `k_d/M`**, where `k_d = ½·ρ·C_d·A` and `M = m + m_added_x`. That is why `C_d` comes from towing, `m` from a scale (`--m`), and the coast-down gives the total mass `M`, and only from that the added mass `m_added_x = M − m`. The initial speed is fitted as an auxiliary parameter.

Synthetic measurement: `C_d = 0.4`, `A = 50 cm²`, `m = 1 kg`, `m_added_x = 0.08 kg`. Towing at 10 speeds 2–20 cm/s (noise 0.1 mN + 3%), coast-down from 15 cm/s for 20 s, camera 30 fps with 2 mm noise (`results/calibration/hull_fit.{txt,png}`):

- `C_d` = 0.402 ± 0.9%,
- total mass from the coast-down: uncertainty from the fit alone only 0.09%,
- `m_added_x` = 0.084 ± 0.010 kg (12%), of which 0.0097 kg comes from `C_d`, and 0.001 kg each from the fit and from weighing.

Over 200 repetitions the spread of `m_added_x` is 0.015 kg (about 18%), with a mean σ of 0.014 kg and no bias.

**Lesson: a small difference of large numbers.** Added mass is only 8% of the total mass, so every percent of error in `M` gives about 13% error in `m_added_x`. The camera determines `k_d/M` very precisely, but the error of `C_d` from towing carries over 1:1 into `M` and eats up all the precision. To improve `m_added_x`, drag has to be measured better (more towing points at the coast-down speeds, 5–15 cm/s), not the coast-down filmed longer. For swimming itself this is a minor concern: `m_added_x` affects only the acceleration time, and the steady-state speed depends only on `C_d·A`, which is determined to within 1%.

### Ballast and heave (step 11): `calibrate.py ballast`

Three measurements in a pool:

1. **Underwater weighing at several piston positions** (syringe motor revolution counter, 0 = bladder empty). The apparent weight `W = ρ·g·(V_b_neutral − A_piston·travel·n)` is linear in the number of revolutions `n`. The intercept is `ρ·g·V_b_neutral`, independent of piston geometry. The slope gives the piston travel per motor revolution, i.e. `lead/gear_ratio` (only this ratio), with the piston diameter from calipers. File: `turns, W [N]`.
2. **Weighing at several depths** with the piston fixed: `W = W0 + ρ·g·V_air0·(1 − p_atm/(p_atm + ρ·g·h))`, linear regression in `W0` and `V_air0`. File: `depth [m], W [N]`.
3. **Ascent after a bladder step** from neutral buoyancy (`FishRobot.Calibration.VerticalStep`), position from a pressure sensor in the hull. The force `ρ·g·dV` is known, so the terminal velocity determines the drag `C_dz`, and the acceleration time the mass `m + m_added_z`. File: `time [s], z [m]`, step at `t = 2 s`.

Synthetic measurement (underwater scale 1 mN, depth sensor 3 mm) (`results/calibration/ballast_fit.{txt,png}`):

| Parameter | Result | Uncertainty | Error |
|---|---|---|---|
| `V_b_neutral` | 7.29 ml | ±0.06 ml | +1.3% |
| piston travel | 33.1 µm/rev | ±0.8% | +1.3% |
| `V_air0` | 15.2 ml | ±0.7 ml | +1.2% |
| `m_added_z` | 0.595 kg | ±1.6% | −0.8% |
| `C_dz` | 1.304 | ±1.1% | +0.3% |

**Lesson 1: a known force gives the added mass.** In step 10 the coast-down determined only `k_d/M`, and the added mass came from a difference of large numbers with 18% uncertainty. Here the forcing `ρ·g·dV` is known from the piston position, so a single run determines both drag and mass, and `m_added_z` comes out with 1.6% uncertainty. The vertical added mass (60% of the fish's mass) is also much larger than along the axis (8%), so it is easier to measure.

**Lesson 2: a model can fit perfectly and still be wrong.** The air pocket in the hull (15 ml) expands during ascent. Over 0.5 m of travel from 1.5 m that is about 0.7 ml of extra buoyancy, almost as much as the bladder step itself (1 ml). Fitting a model without compressibility gives `C_dz` = 1.01 (true 1.3) and `m_added_z` = 0.71 kg (true 0.6), and the residuals are 3.0 mm, exactly the sensor noise. The growing buoyancy "hides" in the drag and the mass, so the residuals give nothing away. That is why `VerticalStep` has compressibility enabled, `V_air0` comes from measurement 2, and its uncertainty is added to the uncertainty of `C_dz` and `m_added_z` (by refitting at `V_air0 + σ`).

### Calibration summary

Each step has a bench model in `FishRobot.Calibration` (or a regression, where the relationships are linear), a synthetic measurement with known parameters and a check of whether the reported uncertainty matches the spread over repetitions. With real measurements it is enough to pass the CSV files (`--data...`). Lessons that recur across many steps:

- **Not every parameter can be determined from a given measurement.** Often only a ratio or a product is visible: `C_T·s_fin²`, `C_d·A`, `V_flow_nominal/dp_open`, `k/J`, `k_d/M`, `lead/gear_ratio`. The missing factor has to be measured another way (ruler, scale, a separate static measurement), and its error carries over into the result.
- **Signal and point weights must follow from the sensor noise model.** Otherwise the reported uncertainty is too small (motor, thrust).
- **The error of a sensor identified earlier does not average out.** The motor as a torque sensor for the pump, the tail's `k` for the dynamics, `C_d` for the added mass, `V_air0` for vertical drag.
- **A mismatch between model and reality gives an error that is not in σ.** Sometimes it is visible in the residuals (valve hysteresis, the laminar transition in the pipe), sometimes only in a form test (nonlinear tail stiffness, thrust as a function of speed), and sometimes not at all (compressibility during ascent). That is why a synthetic measurement with a "reality" richer than the model is a good way to check, before going to the pool, whether the measurement plan will let you determine the parameters at all.
