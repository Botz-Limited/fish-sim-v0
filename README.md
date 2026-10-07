# fish-sim-v0 – SOFA

Educational simulations of a soft, hydraulically actuated robot fish tail.

| Branch | Directory | Tool | What it shows |
|---|---|---|---|
| `main` | `MuJoCo/` | MuJoCo | Whole fish: hydraulic tail, ballast bladder, swimming, turning, depth control |
| `sofa` | `SOFA/` | SOFA + SoftRobots | FEM of the silicone tail: chambers, p–V curve, flapping in air and water |
| `openfoam` | `OpenFOAM/` | OpenFOAM + preCICE + CalculiX | FSI: real water flow around the deforming tail, vortex wake, thrust, added mass |

This branch holds `SOFA/`. Details and instructions: `SOFA/README.md`.
The test `test_dimensions_match_mujoco` is skipped here; it runs when `MuJoCo/` (from `main`) sits next to `SOFA/`.
