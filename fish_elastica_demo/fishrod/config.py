"""All demo parameters in one place (SI units).

This is NOT a calibrated model. Values marked PLACEHOLDER have to be identified
from measurements (deflection vs pressure, natural frequency of the tail, speed in a pool).
"""

from dataclasses import dataclass, field, replace

import numpy as np


@dataclass
class RodConfig:
    """Geometry and material of the Cosserat rod.

    A Cosserat rod is a curve (the fish axis) with a coordinate frame "attached" to every
    point (directors d1, d2, d3). d3 is the direction tangent to the axis, d1 and d2 lie
    in the cross-section. This lets the rod describe four kinds of deformation:
    bending (2 axes), twisting, shear (2 directions) and stretching.
    Convention in this demo: fish axis along +X, d1 = +Z (up), d2 = d3 × d1.
    Bending about d1 (the vertical axis) = sideways bending of the tail, i.e. the swimming motion.
    """

    length: float = 0.4            # [m] fish length; PLACEHOLDER – to be identified from measurements
    n_elements: int = 100          # number of elements (discretisation, not physics)
    radius: float = 0.02           # [m] cross-section radius (uniform rod); PLACEHOLDER – to be identified from measurements
    density: float = 1050.0        # [kg/m³] silicone; PLACEHOLDER – to be identified from measurements
    # Young's modulus of soft silicone. The order of magnitude 1e5–1e6 Pa is a typical range for
    # casting silicones, but the specific value is not measured.
    youngs_modulus: float = 5e5    # [Pa] PLACEHOLDER – to be identified from measurements
    # Silicone is nearly incompressible (ν ≈ 0.5), hence G = E / (2(1 + ν)) = E/3.
    poisson_ratio: float = 0.5     # [-] PLACEHOLDER – to be identified from measurements

    @property
    def shear_modulus(self) -> float:
        return self.youngs_modulus / (2.0 * (1.0 + self.poisson_ratio))

    @property
    def element_length(self) -> float:
        return self.length / self.n_elements


@dataclass
class NumericsConfig:
    # Time step = dt_safety · dt_max (formula in build.stable_time_step).
    # Checked in stage 1 (undamped cantilever): with n = 50 instability appears
    # between 2× and 3× dt_max, with n = 100 only above 3×.
    # The formula is therefore conservative and 1.0 leaves a ~2× margin.
    dt_safety: float = 1.0
    # "Blow-up" threshold: maximum element elongation (dilatation e = l/l₀).
    max_dilatation: float = 1.5
    # How often the callback saves the state (saving is costly – array copies).
    save_every_s: float = 1e-3     # [s] interval between saves


@dataclass
class Stage1Config:
    """Stage 1: rod validation without water (cantilever)."""

    # Tip moment chosen so that the tip angle is large (π/3) – we also check
    # geometric nonlinearity, not just small deflections.
    tip_angle: float = np.pi / 3   # [rad] target tip angle from theory: θ = M·L/(E·I)
    ramp_time: float = 0.5         # [s] gentle ramp of the moment (no impact)
    t_static: float = 4.0          # [s] time to reach equilibrium
    # Damping only to reach the static state quickly (≈ 2·ω₁).
    damping: float = 10.0          # [1/s]
    # Free vibration: initial velocity shaped like the 1st mode.
    tip_velocity: float = 0.01     # [m/s] small amplitude -> linear range
    t_free: float = 6.0            # [s] ~4–5 periods


@dataclass
class FishConfig:
    """Fish shape and zones along the axis (s = 0 nose, s = L end of the caudal fin).

    ELLIPTICAL cross-section with semi-axes a (half width, sideways) and b (half height).
    PyElastica creates a rod with a circular cross-section; we give it an equivalent radius
    r = √(a·b) (same area -> correct mass and volume), and then overwrite the stiffness
    and rotational inertia matrices with the formulas for an ellipse (build.make_fish_rod).
    A laterally flattened tail (a < b) is SOFT sideways and stiff vertically –
    exactly what swimming needs.
    """

    # Profile: stations s/L and semi-axes [m] (linear interpolation). PLACEHOLDER – to be identified from measurements
    stations: tuple = (0.0, 0.08, 0.3, 0.5, 0.8, 0.9, 1.0)
    half_width: tuple = (0.012, 0.024, 0.024, 0.018, 0.008, 0.005, 0.004)    # a(s) [m]
    half_height: tuple = (0.018, 0.034, 0.034, 0.028, 0.014, 0.020, 0.030)   # b(s) [m] (caudal fin taller)
    # Fish discretisation. Stage 1: n = 50 gives ~1–2% error vs theory, while the stiff head
    # (E×20) with n = 100 shortens the step to ~5 µs (2 million steps for 10 s of swimming).
    # n = 50 -> step ~19 µs, 4× faster. For a convergence check: n_elements = 100.
    n_elements: int = 50
    # "ellipse" (flat cross-section, anisotropic stiffness) or "circle" (PyElastica default)
    cross_section: str = "ellipse"
    # Stiff head: Young's modulus × head_stiffness_factor for s < head_length.
    # Note: a larger E shortens the stable time step (dt ~ 1/√E), see build.stable_time_step.
    head_length: float = 0.12      # [m] PLACEHOLDER – to be identified from measurements
    head_stiffness_factor: float = 20.0   # [-] PLACEHOLDER – to be identified from measurements
    # Hydraulic chamber zone (s_start, s_end) [m]. PLACEHOLDER – to be identified from measurements
    chamber_zone: tuple = (0.20, 0.32)


@dataclass
class HydraulicsConfig:
    """Pump + two chambers (L, R) in a closed circuit – as in the MuJoCo and SOFA demos.

    A chamber under pressure Δp = p_L − p_R bends its segment with a moment M = A_eff·r_eff·Δp
    (A_eff – effective wall area, r_eff – lever arm about the bending axis).
    A segment bent by an angle θ "makes room" for a volume A_eff·r_eff·θ, and the excess liquid
    pushes the walls outward (compliance C_h): Δp = (V_p − A_eff·r_eff·θ) / C_h.
    The model (equations) is as in MuJoCo/fishsim/hydraulics.py. The values of A_eff, r_eff, C_h
    are NOT copied from MuJoCo (there r_eff = 5 cm, i.e. more than the whole width of this
    tail, and C_h = 8e-11 means walls much stiffer than silicone with E = 0.5 MPa).
    With the MuJoCo values the hydraulic spring k_h = A_r²/C_h would be ~60× stiffer than the
    bending of the chamber zone, and the explicit coupling with the rod fell into oscillation
    (checked in stage 2). Here we estimate them from the cross-section geometry in the middle of
    the chamber zone (s ≈ 0.26 m: a ≈ 13 mm, b ≈ 21 mm), still as placeholders:
      A_eff ≈ area of half an ellipse = π·a·b/2                        ≈ 4.3e-4 m²
      r_eff ≈ distance of the half-ellipse centroid from the axis = 4a/(3π) ≈ 5.5 mm
      C_h   ≈ thin-walled silicone cylinder: dV/dp ≈ V₀·2r/(E·t)
              (V₀ = 30 ml, r ≈ 15 mm, t = 4 mm, E = 0.5 MPa)        ≈ 4.5e-10 m³/Pa
    Then A_r²·Λ ≈ 0.16·C_h: most of the volume from the pump inflates the soft walls,
    the rest bends the tail; A_V = 8 ml gives θ ≈ 0.45 rad at Δp ≈ 15 kPa < p_max.
    """

    A_eff: float = 4.3e-4          # [m²] PLACEHOLDER – to be identified from measurements
    r_eff: float = 5.5e-3          # [m] PLACEHOLDER – to be identified from measurements
    C_h: float = 4.5e-10           # [m³/Pa] compliance (walls + compressibility); PLACEHOLDER – to be identified from measurements
    p_max: float = 50e3            # [Pa] relief valve on |p_L − p_R|; PLACEHOLDER – to be identified from measurements
    V0_chamber: float = 30e-6      # [m³] chamber volume with a straight tail; PLACEHOLDER – to be identified from measurements
    # The pump must deliver a peak flow of 2π·f·A_V, otherwise it saturates and the amplitude drops
    # (lesson from SOFA). With A_V = 8 ml and f = 3 Hz (upper end of the stage 5 sweep) that is 151 ml/s.
    Q_max: float = 160e-6          # [m³/s] PLACEHOLDER – to be identified from measurements
    tau_pump: float = 0.03         # [s] pump time constant; PLACEHOLDER – to be identified from measurements
    # Tail rhythm: prescribed pumped volume V_ref(t) = a(t)·(A_V·sin(2πft) + V_bias)
    tail_freq: float = 2.0         # [Hz]
    tail_volume_amp: float = 8e-6  # [m³] A_V, as in MuJoCo; PLACEHOLDER – to be identified from measurements
    tail_volume_bias: float = 0.0  # [m³] constant deflection (turning)
    K_v: float = 10.0              # [1/s] volume error correction (K_v·τ_pump < 0.5)
    ramp_time: float = 1.0         # [s] soft start of the amplitude
    # Hydraulics step: the pump ODE is computed every N rod steps, so that dt_h ≤ dt_hydraulics.
    # Conditions: dt_h ≪ τ_pump (30 ms) and ω_n·dt_h ≪ 1 for the "hydraulic spring" (~40 rad/s).
    # The rod step is ~1e-5 s, so computing the ODE in every step would only waste time.
    dt_hydraulics: float = 2e-4    # [s]

    @property
    def A_r(self) -> float:
        """A_eff·r_eff [m³/rad] – volume per radian of bending = moment per pascal."""
        return self.A_eff * self.r_eff


@dataclass
class Stage2Config:
    """Stage 2: actuation via rest curvature."""

    pressures: tuple = (0.0, 5e3, 10e3, 15e3, 20e3, 25e3, 30e3)   # [Pa] static Δp
    ramp_time: float = 0.5         # [s] gentle ramp of Δp (a step in κ_rest = an impact)
    volumes: tuple = (0.0, 2e-6, 4e-6, 8e-6, 12e-6, 16e-6)        # [m³] static V_p (coupling)
    t_static: float = 3.0          # [s]
    damping: float = 20.0          # [1/s] only to reach equilibrium quickly
    t_free: float = 3.0            # [s] free rod in vacuum with the pump running
    free_damping: float = 0.5      # [1/s] small numerical damping


@dataclass
class WaterConfig:
    """Water (fishrod/water.py). Density and viscosity are physical values, drag
    coefficients are placeholders."""

    model: str = "drag+reactive"   # "none" | "drag" | "drag+reactive" | "stokes_sbt"
    rho: float = 1000.0            # [kg/m³] fresh water (physical value)
    mu: float = 1.0e-3             # [Pa·s] water viscosity at 20 °C (physical value, only for stokes_sbt)
    # Normal drag: for a flat plate/cylinder at Re ~ 1e4 of order 1. PLACEHOLDER – to be identified from measurements
    C_n: float = 1.2               # [-]
    # Friction along the axis (boundary layer). PLACEHOLDER – to be identified from measurements
    C_t: float = 0.01              # [-]


@dataclass
class Stage3Config:
    """Stage 3: tail in water, head held fixed (tethered thrust)."""

    models: tuple = ("none", "drag", "drag+reactive")
    t_end: float = 6.0             # [s] 1 s pump ramp + steady state
    t_analyze: float = 3.0         # [s] analysis from this moment on (steady state)
    damping: float = 0.5           # [1/s] numerical damping (AnalyticalLinearDamper)


@dataclass
class Stage4Config:
    """Stage 4: free planar swimming (no gravity and buoyancy = neutral buoyancy)."""

    models: tuple = ("none", "drag", "drag+reactive", "stokes_sbt")
    t_end: float = 15.0            # [s] the "drag" model accelerates slowly (~10 s)
    # Numerical damping in free swimming:
    #  "laplace"    – LaplaceDissipationFilter: smooths only short-wavelength noise
    #                 (Laplacian of a constant velocity = 0), does NOT slow down the fish as a whole,
    #  "analytical" – AnalyticalLinearDamper: damps the ABSOLUTE velocity, i.e. acts
    #                 like an extra, non-physical linear water drag (for comparison).
    damper: str = "laplace"
    filter_order: int = 5          # 3–7 recommended in PyElastica; smaller = stronger filter
    analytical_damping: float = 0.5  # [1/s] as in stage 3
    save_every_s: float = 0.02     # [s] shape saving for the animation (50 frames/s)


@dataclass
class Stage5Config:
    """Stage 5: sweep of the tail-beat frequency and Young's modulus."""

    freqs: tuple = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)   # [Hz]
    E_factors: tuple = (0.5, 1.0, 2.0)              # Young's modulus multiplier (whole body)
    t_end: float = 12.0            # [s] at low f the fish accelerates more slowly
    # Natural frequency of the tail: head held fixed, pump stopped (hydraulics coupled),
    # velocity impulse on the tail, free vibration in vacuum.
    t_free: float = 4.0            # [s]
    tip_velocity: float = 0.05     # [m/s]


@dataclass
class BuoyancyConfig:
    """Buoyancy, ballast and depth controller (fishrod/buoyancy.py). Names and values of the
    ballast pump and the PID – as in MuJoCo/fishsim/config.py."""

    g: float = 9.81                # [m/s²]
    # Centre of gravity of the cross-section below the axis (heavy parts low) -> righting moment.
    h_g: float = 0.005             # [m] PLACEHOLDER – to be identified from measurements
    # Bladder: in the front part of the body above the longitudinal centre of mass (None = compute
    # from the mass), bladder buoyancy z_b above the axis.
    bladder_s: float | None = None  # [m]
    z_b: float = 0.01              # [m] PLACEHOLDER – to be identified from measurements
    V_min: float = 0.0             # [m³] PLACEHOLDER – to be identified from measurements
    V_max: float = 40e-6           # [m³] 40 ml; PLACEHOLDER – to be identified from measurements
    q_max: float = 10e-6           # [m³/s] max. flow of the ballast pump; PLACEHOLDER – to be identified from measurements
    k_bal: float = 5.0             # [1/s] V_ref tracking by the ballast pump
    kp: float = 200e-6             # [m³/m] 10 cm of error -> 20 ml
    ki: float = 20e-6              # [m³/(m·s)]
    kd: float = 300e-6             # [m³·s/m]
    dt_control: float = 0.01       # [s] controller period (100 Hz)


@dataclass
class Stage6Config:
    """Stage 6: 3D with gravity and buoyancy, depth setpoint steps, the fish swims (2 Hz)."""

    z0: float = -1.0               # [m] starting depth (z up, surface z = 0)
    # (time [s], z_ref [m]) – setpoint steps
    schedule: tuple = ((0.0, -1.0), (8.0, -1.5), (22.0, -0.7))
    t_end: float = 36.0            # [s]
    swim: bool = True              # the tail works (swimming + depth control)


@dataclass
class Config:
    rod: RodConfig = field(default_factory=RodConfig)
    numerics: NumericsConfig = field(default_factory=NumericsConfig)
    stage1: Stage1Config = field(default_factory=Stage1Config)
    fish: FishConfig = field(default_factory=FishConfig)
    hydraulics: HydraulicsConfig = field(default_factory=HydraulicsConfig)
    stage2: Stage2Config = field(default_factory=Stage2Config)
    water: WaterConfig = field(default_factory=WaterConfig)
    stage3: Stage3Config = field(default_factory=Stage3Config)
    stage4: Stage4Config = field(default_factory=Stage4Config)
    stage5: Stage5Config = field(default_factory=Stage5Config)
    buoyancy: BuoyancyConfig = field(default_factory=BuoyancyConfig)
    stage6: Stage6Config = field(default_factory=Stage6Config)


def fish_rod_config(cfg: "Config") -> RodConfig:
    """Fish rod parameters (material from cfg.rod, discretisation from cfg.fish)."""
    return replace(cfg.rod, n_elements=cfg.fish.n_elements)


def default_config(**overrides) -> Config:
    return replace(Config(), **overrides)
