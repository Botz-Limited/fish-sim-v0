# fish-sim-v0 – SOFA

Educational simulations of a soft, hydraulically actuated robot fish tail.

| Branch | Directory | Tool | What it shows |
|---|---|---|---|
| `main` | `MuJoCo/` | MuJoCo | Whole fish: hydraulic tail, ballast bladder, swimming, turning, depth control |
| `sofa` | `SOFA/` | SOFA + SoftRobots | FEM of the silicone tail: chambers, p–V curve, flapping in air and water |
| `stonefish` | `Stonefish/` | Stonefish (C++) | Whole fish with geometry-based hydrodynamics: VBS, pressure/IMU sensors, currents, console + 3D viewer |
| `openfoam` | `OpenFOAM/` | OpenFOAM + preCICE + CalculiX | FSI: real water flow around the deforming tail, vortex wake, thrust, added mass |
| `openmodelica` | `FishRobot/` | OpenModelica | System model: DC motor → pump → pipes → chambers → tail, ballast, energy budget, FMU export |
| `pyelastica` | `fish_elastica_demo/` | PyElastica | Soft fish as a Cosserat rod: chamber-driven curvature, swimming, ballast, depth PID |

This branch holds `SOFA/`. Details and instructions: `SOFA/README.md`.
The test `test_dimensions_match_mujoco` is skipped here; it runs when `MuJoCo/` (from `main`) sits next to `SOFA/`.
