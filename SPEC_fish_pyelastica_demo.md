# SPEC: PyElastica demo – a soft fish as a Cosserat rod

> Instructions for Claude Code. Put this file in an empty project folder and write:
> "Read SPEC_fish_pyelastica_demo.md and implement it in stages. Start with a plan."

## 0. Goal and context

Build a **simplified, educational** simulation of a robotic fish in PyElastica, in which the body and the tail are a continuous, soft Cosserat rod (bending, twisting, shear, stretching). It should show what the other tools do not offer:
- continuous deformation of a slender tail at **low cost** (1D instead of 3D FEM),
- **free swimming** of a soft body (not only a clamped tail),
- how to model an **internal drive** (hydraulic chambers) so that it does not break the laws of dynamics,
- an own water force model for high Reynolds numbers (drag + reactive force),
- buoyancy and ballast on a deformable body.

This is **not** a calibrated model. Parameters are placeholders and must be marked as such.

The user is a young mechatronics engineer who is learning. **Code comments in Polish**, explaining the physics (what a given quantity means in Cosserat rod theory, where a given force comes from).

## 1. Working rules (important)

1. Work in stages (section 7). After each stage run the code and the tests, show the result, and only then move on.
2. **The PyElastica API has changed between versions** (e.g. the module `elastica.wrappers` → `elastica.modules`, imports via `import elastica as ea`, a separate damping module `Damping`). At the start determine the installed version and follow the repository examples **for that version** (`examples/`, e.g. the axial stretching and beam bending cases, "continuum snake", flagella).
3. **Do not use the built-in `SlenderBodyTheory` as the water model for the fish.** It is slender body theory for Stokes flow (no fluid inertia), i.e. for microorganisms with flagella, not for a fish at Re ~ 1e4–1e5. **Verify this in the source code** of the installed version (what parameters it takes, what formula it computes) and describe the result in the README. You may use it only in a comparison stage, to show that it gives the wrong physics for a fish.
4. PyElastica does not enforce units. Use **SI** consistently.
5. The integrator is explicit (e.g. `PositionVerlet`), so the time step is limited by the rod stiffness. Choose it deliberately (dependence on element length, Young's modulus, density), describe the formula in a comment, and always give the estimated computation time before a long run.
6. PyElastica does not save results automatically. Use callbacks with a reasonable saving frequency.
7. Do not invent "realistic" values. Every parameter: comment `# PLACEHOLDER – to be identified from measurements`.

## 2. Project structure

```
fish_elastica_demo/
  README.md
  requirements.txt              # pyelastica (pinned version), numpy, numba, matplotlib, pytest
  fishrod/
    config.py                   # dataclass with ALL parameters
    build.py                    # simulator (class with mixins), rod(s), BC, damping, callbacks
    hydraulics.py               # ODE model of the pump and chambers (as in the MuJoCo/Modelica demo)
    actuation.py                # internal drive: rest curvature from pressure
    water.py                    # own water forces (class inheriting from ea.NoForces)
    buoyancy.py                 # buoyancy per element + bladder in the head
    run.py                      # integration loop with a hydraulics step
  scripts/
    run_scenarios.py
    animate.py                  # 2D/3D matplotlib animation -> GIF/MP4
  tests/test_sanity.py
  results/
```

## 3. Rod model

- The fish as **a single rod** about 0.4 m long (placeholder), axis along X, about 50–100 elements.
- Radius varying along the length (tapering towards the tail), if the API version allows a per-element radius. If not: two rods (a stiffer "body" + a soft "tail") connected by a `FixedJoint`. Decide after checking the API and justify.
- Note on the cross-section: a real tail is **flat** (laterally flattened), while the Cosserat rod in PyElastica assumes a circular cross-section by default. Describe how this affects the stiffness and the water forces. If the API allows overriding the bending stiffness matrix (anisotropic stiffness), do it; otherwise note it as a limitation.
- Rigid front part (head) = a large Young's modulus or a large radius (depending on the chosen option).
- Young's modulus of silicone as a placeholder, density ~1000–1100 kg/m³.
- Internal damping: `AnalyticalLinearDamper` (describe that this is numerical-phenomenological damping, not the viscoelasticity of silicone).

## 4. Hydraulic drive – do it physically correctly

- The chambers are **internal**: the hydraulics must not produce a net force or moment on the whole fish. Adding external moments to elements (as in some examples) breaks this principle if the moments do not cancel.
- Recommended approach: pressure changes the **rest curvature** of the segment with the chambers: `κ_rest(s, t) = K_p · (p_L − p_R)` in the chamber zone (zero outside it). The rod itself "wants" to bend, and the net force and moment from the drive are zero by construction. Check in the API how to change the rest curvature during the simulation (a callback/forcing modifying the corresponding field), and describe it.
- Alternative for comparison (optional stage): pairs of equal and opposite moments at the boundaries of the chamber zone.
- Hydraulics: the same simple ODE model as in the other demos (first-order pump, closed L↔R circuit, chamber compliance, relief valve). Integrated every rod step or every N steps, with a description of the choice.

## 5. Water (water.py) – own force class

Implement a class inheriting from `ea.NoForces` with the method `apply_forces(system, time)`, which for each node/element computes:

1. **Quadratic drag (Morison/Taylor)**: decompose the relative velocity into the normal and tangential components with respect to the rod axis: `f_n = −½ ρ C_n d |v_n| v_n`, `f_t = −½ ρ C_t π d |v_t| v_t` (per unit length, `d` = local width/diameter). The coefficients are placeholders.
2. **Reactive force / added mass**: apply the simplification from Lighthill's elongated-body theory. Added mass per unit length `m_a(s) = ρ π h(s)²/4` (h = local height) for transverse motion. Choose and describe one of the implementations:
   - (a) simpler: the added mass added to the lateral inertia (if the API allows) or as a force `−m_a · a_n` from differentiating the velocity (beware of noise; filter),
   - (b) a reactive force concentrated at the trailing edge of the tail (Lighthill's large-amplitude theory). Describe the formula and the source.
3. A switch `water_model ∈ {"none", "drag", "drag+reactive", "stokes_sbt"}` in the config. `stokes_sbt` is for comparison only (rule 3).

**Limitation for the README:** this is a local model, without a vortex wake and without tail–vortex interaction. The results are qualitative. If the user wants a real flow, the next step is coupling with the SophT solver (the same research group, immersed boundary method). Do not implement this without the user's consent.

## 6. Buoyancy and ballast (buoyancy.py)

- On each element: buoyancy `ρ_w · g · V_elem` upwards + gravity `ρ_s · g · V_elem` downwards (built-in `GravityForces` or own, without double counting).
- Ballast bladder in the head zone: additional volume `V_b(t)`, limited by the speed of the ballast pump. Applied slightly above the axis (righting moment), if the API allows a moment; if not, describe the simplification.
- Depth PID (as in the MuJoCo demo), active only in scenario 6.

## 7. Implementation stages

1. **Rod validation (no water)**: a cantilever (`OneEndFixedBC`) under a tip moment → arc shape with `κ = M/(E·I)`; comparison with theory. Second validation: the first natural frequency of the cantilever vs the analytical formula `ω₁ = 1.875²·√(E·I/(ρ·A·L⁴))`.
2. **Drive via rest curvature**: static tail deflection vs pressure difference. Test: net force and moment from the drive ≈ 0 (check on a free rod in vacuum: the center of mass does not move).
3. **Clamped tail in water**: head fixed, sinusoidal pump. Comparison of the water models `none` / `drag` / `drag+reactive`: amplitude, phase, mean reaction force at the mount (qualitative tethered thrust).
4. **Free swimming 2D (flat)**: no gravity and no buoyancy (neutral buoyancy). Forward speed vs time. Comparison of the water models, including `stokes_sbt` as an example of wrong physics.
5. **Sweep**: frequency 0.5–3 Hz and Young's modulus ×0.5/×1/×2 → swimming speed. Pay attention to resonance (compare with the natural frequency from stage 1) and describe it in the README.
6. **3D + buoyancy + ballast**: gravity and buoyancy enabled, steps of the depth setpoint. Plot of the depth and of the bladder volume.
7. **(Optional) export to other demos**: equivalent stiffnesses for the MuJoCo segmented model (as in the SOFA demo) to `results/prbm.json`.

## 8. Results (results/)

PNG + CSV: `e1_cantilever_vs_theory.png`, `e1_natural_freq.png`, `e2_bend_vs_pressure.png`, `e3_tethered_models.png`, `e4_free_swim_speed.png`, `e5_sweep_freq_E.png`, `e6_depth_control.png`. GIF/MP4 animations: `free_swim.gif` (fish shape over time, top view) and optionally a 3D view from stage 6.

## 9. Tests (tests/test_sanity.py)

- Stage 1: arc shape and tip deflection consistent with theory < 2–5% (with sufficiently fine discretization); natural frequency < 5%.
- Without damping and without water: the total energy does not drift significantly (symplectic integrator).
- Internal drive: for a free rod in vacuum the center of mass stays in place (|Δx_cm| below a threshold).
- Hydraulics: `V_L + V_R = const`, pressure ≤ `p_max`.
- The water model dissipates energy (power of the drag forces ≤ 0).
- Free swimming with water: mean forward speed > 0; in vacuum ≈ 0.
- No NaN, no "explosion" (maximum element stretch below a threshold).

## 10. README – mandatory sections

- PyElastica version (pinned) and installation.
- A short explanation of Cosserat rod theory for a learner: what a Cosserat rod is, which deformations it accounts for, why it is a good approximation of a slender fish.
- An explanation of why `SlenderBodyTheory` (Stokes) does not fit a fish, with the comparison result from stage 4.
- What each plot shows, 2–3 sentences.
- **Limitations**: circular instead of flat cross-section (unless the stiffness was overridden), local water model without vortices, drive as rest curvature instead of full chamber mechanics, linear elasticity, unidentified parameters.
- Development path: coupling with SophT for a real flow, calibration against measurements (deflection vs pressure, natural frequency of the tail in water, swimming speed in a pool).

## 11. Definition of done

- `pytest` → all tests green.
- `python scripts/run_scenarios.py` → plots in `results/`.
- `python scripts/animate.py` → animation of the swimming fish.
- The README makes it possible to understand the results and the limitations.
