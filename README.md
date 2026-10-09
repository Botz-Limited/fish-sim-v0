# fish-sim-v0

Educational simulations of a soft, hydraulically actuated robot fish tail.

| Branch | Directory | Tool | What it shows |
|---|---|---|---|
| `main` | `MuJoCo/` | MuJoCo | Whole fish: hydraulic tail, ballast bladder, swimming, turning, depth control |
| `sofa` | `SOFA/` | SOFA + SoftRobots | FEM of the silicone tail: chambers, p–V curve, flapping in air and water |
| `stonefish` | `Stonefish/` | Stonefish (C++) | Whole fish with geometry-based hydrodynamics: VBS, pressure/IMU sensors, currents, console + 3D viewer |
| `openfoam` | `OpenFOAM/` | OpenFOAM + preCICE + CalculiX | FSI: real water flow around the deforming tail, vortex wake, thrust, added mass |
| `openmodelica` | `FishRobot/` | OpenModelica | System model: DC motor → pump → pipes → chambers → tail, ballast, energy budget, FMU export |
| `pyelastica` | `fish_elastica_demo/` | PyElastica | Soft fish as a Cosserat rod: chamber-driven curvature, swimming, ballast, depth PID |

Each branch holds only its own demo. This branch holds `MuJoCo/`; details and instructions: `MuJoCo/README.md`.

## Documentation

A report comparing all six tools covers inputs, outputs, working principle, GUI screenshots and demo videos (`docs/media/`), CAD import, choosing and setting parameters, and a capability matrix:

- English: [`docs/research_EN.pdf`](docs/research_EN.pdf) · [`docs/research_EN.html`](docs/research_EN.html)
- Polski: [`docs/research_PL.pdf`](docs/research_PL.pdf) · [`docs/research_PL.html`](docs/research_PL.html)

Rebuild the PDFs after editing the HTML: `docs/build_pdf.sh` (needs Google Chrome).
