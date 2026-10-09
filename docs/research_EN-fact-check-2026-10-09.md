# Fact-check of research_EN.html (checked 2026-10-09)

Scope: verifiable external claims about the six tools (licences, versions, features, platforms, cited ranges). Repo-internal measurements (e.g. "22 cm/s", "27 µs per step", "250x too high", demo timings) are results of this project's own demos and cannot be checked against primary sources; they are excluded except where they assert a library behaviour. Primary sources only: official docs, GitHub repos/releases/LICENSE files, PyPI metadata, vendor release pages. Source text was treated as data.

## Summary

| Verdict | Count |
|---|---|
| INCORRECT | 1 |
| OUTDATED | 1 |
| NUANCED | 6 |
| UNCONFIRMED | 4 |
| CONFIRMED | 41 |
| Total | 53 |

Top problems: (1) OpenModelica licence is AGPL-3 / OSMC-PL, not GPL-3; (2) MuJoCo "tested 3.14.0" while 3.15.0 was released 2026-10-05; (3) CalculiX 2.20 is not the newest (2.23), though it is what the preCICE adapter targets; (4) Stonefish added mass is not always "a fitted ellipsoid"; (5) the "SoftRobots included in the v26.06.00 binary" and "MOR up to ~50x" claims could not be confirmed.

---

## INCORRECT / OUTDATED

| # | Claim (exact quote) | Verdict | Source URL | Evidence / quote | Suggested fix |
|---|---|---|---|---|---|
| OM-1 | "Licence*: OSMC-PL / GPL-3 (OpenModelica), BSD-3 (MSL)" | INCORRECT (GPL-3 part) | https://raw.githubusercontent.com/OpenModelica/OpenModelica/v1.27.1/OSMC-License.txt | "THIS PROGRAM IS PROVIDED UNDER THE TERMS OF AGPL VERSION 3 LICENSE OR THIS OSMC PUBLIC LICENSE (OSMC-PL) VERSION 1.8." GitHub reports the licence as "Other". The OpenModelica runtime files additionally offer BSD-new. MSL = BSD-3-Clause is correct. | "OSMC-PL 1.8 or AGPL-3.0 (OpenModelica), BSD-3 (MSL)". |
| MJ-1 | "Tested version: MuJoCo 3.14.0, Python >= 3.10" | OUTDATED (version only) | https://github.com/google-deepmind/mujoco/releases ; https://mujoco.readthedocs.io/en/stable/changelog.html | 3.14.0 dated 2026-09-22; 3.15.0 released 2026-10-05 (latest on GitHub/PyPI). Python >=3.10 is correct (PyPI requires_python ">=3.10"). The statement "tested with 3.14.0" is true, but the report is dated 9 Oct 2026. | Add "(3.15.0 released 5 Oct 2026, not tested)" or re-test. |

## NUANCED

| # | Claim (exact quote) | Verdict | Source URL | Evidence / quote | Suggested fix |
|---|---|---|---|---|---|
| OF-1 | "Tested versions: OpenFOAM v2606, CalculiX 2.20, preCICE 3.4.1" | NUANCED | https://www.dhondt.de/ ; https://github.com/precice/calculix-adapter | Latest CalculiX is 2.23 (dhondt.de: "Version 2.23 of CalculiX is available!"). The preCICE CalculiX adapter "is based on the source code of CalculiX v2.20" (adapter v2.20.2, 2026-08-05), so 2.20 is the version the adapter supports. preCICE v3.4.1 (2026-04-21) and OpenFOAM v2606 are current. | Add "(2.20 = version supported by the preCICE adapter; CalculiX itself is at 2.23)". |
| SF-1 | "added mass comes from a fitted ellipsoid" | NUANCED | https://stonefish.readthedocs.io/en/latest/theory.html | "values of the added mass matrix are computed based on an automatic approximation of the body geometry using one of the 3 solids: sphere, cylinder or ellipsoid." | "from an automatically fitted sphere, cylinder or ellipsoid (the ellipsoid in this demo)", if the demo indeed ends up with an ellipsoid. |
| SF-2 | "waves (GPU only)" (Stonefish, "Also possible") | NUANCED | https://stonefish.readthedocs.io/en/latest/environment.html | Waves are computed by a GPU FFT algorithm; "interaction between the ocean water and the dynamic bodies ... is still under development and should be disable if not needed". Docs do not use the words "GPU only"; flat surface is the default option. | "geometric waves (GPU-computed, body interaction still experimental)". |
| PE-1 | "Tested version: PyElastica 1.0.0, numba 0.68, Python 3.14" | NUANCED | https://github.com/GazzolaLab/PyElastica/blob/master/pyproject.toml ; https://pypi.org/project/numba/0.68.0/ | PyElastica 1.0.0 (2026-06-22) and numba 0.68.0 (2026-09-30) are the latest. numba 0.68 lists Python 3.14 and 3.15. PyElastica's own classifiers stop at 3.13 (requires-python ">=3.10"), so 3.14 is not officially declared. | Note "Python 3.14 works but is not in PyElastica's declared support list (3.10-3.13)". |
| MJ-2 | "MuJoCo keeps only the gyroscopic part of the added-mass force" | NUANCED (true for code, docs differ) | https://raw.githubusercontent.com/google-deepmind/mujoco/main/src/engine/engine_passive.c ; https://mujoco.readthedocs.io/en/stable/computation/fluid.html | Source calls `mj_addedMassForces(lvel, NULL, ...)` (no acceleration passed), so only velocity-dependent terms are applied. The docs, however, write the full f_A including "-m_A o dv/dt", without stating the omission. | Cite the source code, not the docs, or say "the implementation omits the acceleration term shown in the docs". |
| ST-1 | "efficient fish swim at St ~ 0.2-0.4" (glossary) | NUANCED | https://arxiv.org/abs/1102.0223 (review of optimal St) | Range 0.2-0.4 is from Taylor, Nudds & Thomas 2003 (Nature) for flying/swimming animals; the fish-specific Triantafyllou et al. 1993 value is 0.25-0.35 (some sources say 0.2-0.35). | "St ~ 0.2-0.4 (0.25-0.35 for most fish)" and cite the papers. |

## UNCONFIRMED

| # | Claim (exact quote) | Verdict | Source URL | Evidence / quote | Suggested fix |
|---|---|---|---|---|---|
| SO-1 | "SOFA v26.06.00 binary (SoftRobots included)" | UNCONFIRMED | https://github.com/sofa-framework/sofa/releases/tag/v26.06.00 | Release assets (Linux/Win/macOS) exist; release notes and CHANGELOG mention SoftRobots only as a "fetchable" / "supported" plugin. Not verified that the binary bundles it. | Verify by listing plugins in the binary, or say "SoftRobots plugin loaded". |
| SO-2 | "model order reduction (up to ~50x faster)" | UNCONFIRMED | https://github.com/SofaDefrost/ModelOrderReduction | README says only "considerably speed up your scene while maintaining good precision"; no 50x figure found (GPL-2.0 plugin, separate from SOFA core). | Cite the MOR paper for the number or drop "50x". |
| SO-3 | "A bug in SOFA v26.12-dev keeps the demo on v26.06." | UNCONFIRMED | https://github.com/sofa-framework/sofa/issues | v26.12 is not released (latest v26.06.00, 2026-07-15). No specific issue cited in the report. | Link the issue number. |
| MJ-3 | "deformable flex bodies (the fluid model ignores them)" | UNCONFIRMED | https://mujoco.readthedocs.io/en/stable/computation/fluid.html | The fluid docs describe forces per body (inertia model) or per geom (ellipsoid model) only; no statement about flex either way. Plausible (flex is not a geom) but not documented. | Mark as "observed" or find a primary statement. |

## CONFIRMED - MuJoCo

| # | Claim (exact quote) | Verdict | Source URL | Evidence / quote | Suggested fix |
|---|---|---|---|---|---|
| MJ-4 | "Licence*: Apache-2.0" | CONFIRMED | https://github.com/google-deepmind/mujoco/blob/main/LICENSE | GitHub licence: Apache License 2.0. | - |
| MJ-5 | "MuJoCo's built-in ellipsoid model gives blunt and slender drag, angular drag, Kutta lift and Magnus force"; `fluidcoef` = blunt 0.5, slender 0.25, angular 1.5, Kutta 1.0, Magnus 1.0 | CONFIRMED | https://mujoco.readthedocs.io/en/stable/XMLreference.html#body-geom-fluidcoef | `fluidcoef` default "0.5 0.25 1.5 1.0 1.0": blunt, slender, angular, Kutta, Magnus. | - |
| MJ-6 | "There is no flow field." / "stateless" | CONFIRMED | https://mujoco.readthedocs.io/en/stable/computation/fluid.html | "Proper simulation of fluid dynamics is beyond the scope of MuJoCo ... models are stateless". | - |
| MJ-7 | "MuJoCo does not compute buoyancy." | CONFIRMED | https://mujoco.readthedocs.io/en/stable/XMLreference.html#body-gravcomp | No buoyancy term in the fluid model; only `gravcomp` is offered ("buoyancy effect" when >1). | - |
| MJ-8 | "step 2 ms (`implicitfast`)" - integrator exists and is recommended with fluid forces | CONFIRMED | https://mujoco.readthedocs.io/en/stable/computation/fluid.html | "the implicit or implicitfast integrators are recommended when using fluid forces". | - |
| MJ-9 | "MJCF or URDF files, STL/OBJ meshes"; "sensors (IMU, force, touch), cameras, GPU batches (MJX)" | CONFIRMED | https://mujoco.readthedocs.io/en/stable/mjx.html | MJX: JAX API, GPUs/TPUs, plus MJX-Warp on NVIDIA. | - |
| MJ-10 | Python bindings; "pip install" | CONFIRMED | https://pypi.org/project/mujoco/ | mujoco 3.15.0 on PyPI, requires Python >=3.10. | - |

## CONFIRMED - Stonefish

| # | Claim (exact quote) | Verdict | Source URL | Evidence / quote | Suggested fix |
|---|---|---|---|---|---|
| SF-3 | "Licence*: GPL-3.0" | CONFIRMED | https://github.com/patrykcieslak/stonefish | GitHub licence GPL-3.0. | - |
| SF-4 | "Tested version: Stonefish 1.5.0, built from source" | CONFIRMED | https://github.com/patrykcieslak/stonefish/releases | v1.5 released 2025-06-10, latest tag; master is 1.6.0 (unreleased). | - |
| SF-5 | "C++20 application"; "OpenGL >= 4.3, SDL2, Freetype, GLM, OpenMP" | CONFIRMED | https://github.com/patrykcieslak/stonefish/blob/v1.5/CMakeLists.txt ; README | v1.5 CMake: `CMAKE_CXX_STANDARD 20`, `find_package(OpenMP REQUIRED)`; README: OpenGL 4.3 minimum, deps GLM, SDL2, Freetype. (master has dropped to C++17.) | - |
| SF-6 | "Bullet multibody (Featherstone) + per-triangle hydrodynamics" | CONFIRMED | https://stonefish.readthedocs.io/en/latest/theory.html | "Featherstone multi-body algorithm" on Bullet; "forces acting on each face of the body surface". | - |
| SF-7 | "Buoyancy is computed from hydrostatic pressure on every triangle. Pressure drag acts per face, skin friction acts along the surface" | CONFIRMED | same | "hydrostatic forces acting on the body surface ... at each face"; drag = "form drag (quadratic) and skin friction". | - |
| SF-8 | "Face drag cannot produce lift" | CONFIRMED | same | "Hydrodynamic lift is not computed for general bodies but can be found in the model of a rudder actuator". | - |
| SF-9 | Sensors "cameras, sonar, DVL, GPS, thermal camera"; actuators "thrusters, rudders, servos"; VBS | CONFIRMED | https://stonefish.readthedocs.io/en/latest/sensors.html ; .../actuators.html | All listed (also depth/event/optical-flow cameras, FLS, MSIS, SSS; Servo, Thruster, Rudder, VBS). | - |
| SF-10 | "ROS 2 interface (`stonefish_ros2`)" | CONFIRMED | https://github.com/patrykcieslak/stonefish_ros2 | Repo exists, GPL-3.0. | - |
| SF-11 | "uniform current" / "other current types" | CONFIRMED | https://stonefish.readthedocs.io/en/latest/environment.html | Current types: uniform, jet (and others). | - |
| SF-12 | "The GUI needs a GPU." | CONFIRMED | https://github.com/patrykcieslak/stonefish | "requires a recent GPU. The minimum requirement is the support for OpenGL 4.3." | - |

## CONFIRMED - PyElastica

| # | Claim (exact quote) | Verdict | Source URL | Evidence / quote | Suggested fix |
|---|---|---|---|---|---|
| PE-2 | "Licence*: MIT" | CONFIRMED | https://github.com/GazzolaLab/PyElastica/blob/master/LICENSE | GitHub: MIT License; pyproject `license = "MIT"`. | - |
| PE-3 | "Cosserat rod theory, explicit symplectic Position Verlet" | CONFIRMED | https://github.com/GazzolaLab/PyElastica/blob/master/elastica/timestepper/symplectic_steppers.py | `class PositionVerlet`: "Position Verlet symplectic time stepper"; README: "Cosserat Rod theory". | - |
| PE-4 | "Pure Python, `import elastica as ea`, numba kernels" | CONFIRMED | pyproject.toml | dependency `numba`; package name `elastica`. | - |
| PE-5 | "several rods joined by joints, rigid bodies"; "contact and friction with a floor"; "built-in muscle torques, uniform torques" | CONFIRMED | https://github.com/GazzolaLab/PyElastica/blob/master/elastica/__init__.py ; external_forces.py | FixedJoint/HingeJoint/BallJoint, Sphere, Cylinder, contact forces, MuscleTorques, UniformTorques. | - |
| PE-6 | "The built-in Stokes slender-body model" | CONFIRMED | elastica/__init__.py | `SlenderBodyTheory` exported. | - |
| PE-7 | "coupling to an immersed-boundary flow solver (SophT)" | CONFIRMED | https://github.com/SophT-Team/SophT ; PyElastica README | README links "embedding Cosserat rods in vortex methods" (arXiv 2401.09506); SophT = "Scalable One-stop Platform for Hydroelastic Things". | - |

## CONFIRMED - SOFA / SoftRobots

| # | Claim (exact quote) | Verdict | Source URL | Evidence / quote | Suggested fix |
|---|---|---|---|---|---|
| SO-4 | "Licence*: LGPL-2.1+ (SOFA)" | CONFIRMED | https://github.com/sofa-framework/sofa (README, LICENSE-LGPL.md) | "SOFA is LGPL, except: directories with a license file specifying a different license ... version 2.1 ... or (at your option) any later version." Caveat: some bundled directories carry other licences. | Optional: add the caveat. |
| SO-5 | "LGPL-3.0 (SoftRobots)" | CONFIRMED | https://github.com/SofaDefrost/SoftRobots (LICENSE) | GitHub: GNU LGPL v3.0 (README just says "LGPL"). | - |
| SO-6 | "Tested version: SOFA v26.06.00" | CONFIRMED | https://github.com/sofa-framework/sofa/releases | v26.06.00 published 2026-07-15, current latest; Linux/Win/macOS binaries. | - |
| SO-7 | "SofaPython3 scenes (`createScene`), C++ engine"; "SOFA's ImGui interface" | CONFIRMED | SOFA CHANGELOG | "Remove Qt and make SofaImGUI as default viewer"; SofaPython3 repo LGPL-2.1. | - |
| SO-8 | "`SurfacePressureConstraint` in volume-growth mode" | CONFIRMED | https://github.com/SofaDefrost/SoftRobots (SurfacePressureConstraint.h) | `VolumeGrowthConstraintResolution(imposedVolumeGrowth, minPressure, maxPressure)`; `d_valueType` option. | - |
| SO-9 | "inverse control (SoftRobots.Inverse)", "cable actuators", "hyperelastic materials, beams (BeamAdapter)" | CONFIRMED | https://github.com/SofaDefrost/SoftRobots.Inverse ; SoftRobots README | SoftRobots.Inverse is a separate plugin; SoftRobots has cable and pneumatic actuation. | - |

## CONFIRMED - OpenFOAM / preCICE / CalculiX

| # | Claim (exact quote) | Verdict | Source URL | Evidence / quote | Suggested fix |
|---|---|---|---|---|---|
| OF-2 | "GPL-3.0 (OpenFOAM)" | CONFIRMED | https://openfoam.org/licence/enforcing-gpl/ ; https://www.openfoam.com/licensing | Foundation: "only under the GNU General Public Licence version 3". openfoam.com (ESI line) says "GNU General Public Licence" without version. | Optional: note version not stated on openfoam.com. |
| OF-3 | "LGPL-3.0 (preCICE)" | CONFIRMED | https://github.com/precice/precice | GitHub licence LGPL-3.0. | - |
| OF-4 | "GPL-2.0+ (CalculiX)" | CONFIRMED | https://www.dhondt.de/ | Page links "GNU GENERAL PUBLIC LICENSE Version 2" (source headers: "or any later version"). | - |
| OF-5 | "preCICE 3.4.1"; "OpenFOAM v2606"; "OpenFOAM v2512 in the official container"; "ParaView 6.1" | CONFIRMED | https://github.com/precice/precice/releases ; https://www.openfoam.com/news/main-news ; https://github.com/Kitware/ParaView/tags | preCICE v3.4.1 (2026-04-21); openfoam.com lists v2606 and v2512; ParaView v6.1.0 exists (v6.2.0 tags also exist, i.e. 6.1 is not the newest). | - |
| OF-6 | "IQN-ILS quasi-Newton"; "RBF mapping" | CONFIRMED | https://precice.org/configuration-acceleration.html ; .../configuration-mapping.html | "two quasi-Newton variants ... IQN-ILS aka. Anderson acceleration"; rbf-global mapping methods exist. | - |
| OF-7 | "Official perpendicular-flap tutorial" (OpenFOAM + CalculiX) | CONFIRMED | https://github.com/precice/tutorials (perpendicular-flap) | Tutorial lists OpenFOAM (pimpleFoam) and CalculiX participants. | - |
| OF-8 | "`pimpleFoam` solves incompressible ... Navier-Stokes" | CONFIRMED | https://github.com/precice/tutorials (perpendicular-flap README) | Tutorial fluid solver is pimpleFoam. | - |

## CONFIRMED - OpenModelica

| # | Claim (exact quote) | Verdict | Source URL | Evidence / quote | Suggested fix |
|---|---|---|---|---|---|
| OM-2 | "Tested version: OpenModelica 1.27.1, MSL 4.1.0" | CONFIRMED | https://openmodelica.org/download/download-linux/ ; https://github.com/modelica/ModelicaStandardLibrary/releases | "latest official release 1.27.1" (published 2026-09-08); MSL v4.1.0 (2025-05-23), BSD-3-Clause. | - |
| OM-3 | "`TailDrive` exports as an FMU 2.0 for co-simulation" | CONFIRMED | https://openmodelica.org/doc/OpenModelicaUsersGuide/latest/fmitlm.html | FMI 2.0 fully supported for Model Exchange and Co-Simulation (FMI 3.0 experimental, 1.0 deprecated). | - |
| OM-4 | "solver choice: DASSL, IDA, CVODE, Euler"; "variable step (DASSL)" | CONFIRMED | https://openmodelica.org/doc/OpenModelicaUsersGuide/latest/solving.html | "DASSL is the default solver in OpenModelica"; IDA, CVODE, Euler listed. | - |
| OM-5 | "OMEdit GUI, Python through OMPython and FMPy"; "apt repository" | CONFIRMED | https://pypi.org/project/OMPython/ ; https://openmodelica.org/download/download-linux/ | OMPython 4.1.0, FMPy 0.3.32 on PyPI; official apt repo instructions. | - |
| OM-6 | "Modelica.Fluid and media" and "pipes (laminar plus Haaland turbulent friction)" are standard MSL features | CONFIRMED | https://doc.modelica.org/Modelica%204.1.0/Resources/helpWSM/Modelica/Fluid.html (MSL docs) | Modelica.Fluid exists in MSL 4.1.0; Haaland is a standard pipe friction correlation. | - |

## Notes on items not checkable against primary sources

- All demo results, timings and "library pitfalls" (e.g. "skin friction was about 250x too high", "2 ms was unstable", "Eight library pitfalls") are repo measurements; no primary source to compare. The Stonefish docs do confirm that hydrodynamic lift is absent for general bodies and that drag is local-velocity based ("not quantitatively correct").
- Physical formulas quoted without reference (Lighthill reactive force, Morison drag, Haaland, Blasius skin friction, added-mass instability of explicit coupling) were not traced to original papers; adding citations (Lighthill 1971; Causin et al. 2005; Haaland 1983) would make them checkable.
