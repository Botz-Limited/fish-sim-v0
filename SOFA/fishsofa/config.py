"""All parameters of the SOFA demo in one place.

UNITS: SI only – meters, kilograms, seconds, pascals (m, kg, s, Pa).
Note: SoftRobots examples often use millimeters. We do NOT mix units here.

NOTE: this is a demo of SOFA's capabilities, not a calibrated model. Every physical value
marked PLACEHOLDER is an order-of-magnitude guess and has to be identified from
measurements of a real tail. Do not treat them as data.

Coordinate frame (same as in MuJoCo/fishsim/config.py):
  +X – forward (towards the body); the tail extends from the body along -X,
  +Y – port side; the tail bends along this axis,
  +Z – up; gravity acts along -Z.
Origin: center of the front wall of the tail (the one attached to the body).
"""

from dataclasses import dataclass, field


@dataclass
class TailConfig:
    # ------------------------------------------------------------------ environment
    rho_water: float = 1000.0      # [kg/m³] fresh water (physical value, not a placeholder)
    gravity: float = 9.81          # [m/s²]
    # "air"   – full weight of the silicone and of the water in the chambers, no water drag,
    # "water" – apparent weight of the silicone g·(1 − ρ_water/ρ_silicone), water in the chambers
    #           has inertia but no weight (buoyancy = weight), water drag enabled.
    environment: str = "air"
    chambers_filled: bool = True   # chambers full of water (water mass counted in the inertia)
    # Water drag (environment="water", fishsofa/water.py). C_n is applied to EACH side of the
    # surface, so a plate in cross-flow has C_d ≈ 2·C_n ≈ 2 (flat plate).
    drag_C_n: float = 1.0          # [-] PLACEHOLDER – to be identified from measurements
    drag_C_t: float = 0.01         # [-] skin friction, order of C_f at Re ~ 1e4–1e5; PLACEHOLDER – to be identified from measurements

    # ------------------------------------------------------------------ tail geometry
    # Dimensions copied from MuJoCo/fishsim/config.py so that the PRBM export (stage 7) makes sense:
    #   length = n_segments · segment_length, cross-section = 2·segment_ry0 × 2·segment_rz0,
    #   taper taper_last, fin = 2·fin_semi_axes. The test test_dimensions_match_mujoco
    #   makes sure the two configurations do not drift apart.
    n_segments: int = 5            # N segments in MuJoCo (here only for length and PRBM)
    n_actuated: int = 3            # K actuated segments in MuJoCo -> chamber length
    segment_length: float = 0.04   # [m] PLACEHOLDER – to be identified from measurements
    ry0: float = 0.030             # [m] cross-section semi-axis in Y (thickness) at the root; PLACEHOLDER – to be identified from measurements
    rz0: float = 0.040             # [m] cross-section semi-axis in Z (height) at the root; PLACEHOLDER – to be identified from measurements
    taper_last: float = 0.4        # [-] cross-section scale at the tail end relative to the root
    # The cross-section tapers linearly from 1.0 at x = 0 to taper_last at x = −L. In MuJoCo the
    # scale applies to segment centers (ellipsoids), so this approximates the same shape.

    # Caudal fin: elliptical plate of constant thickness, in the XZ plane.
    fin_semi_x: float = 0.035      # [m] PLACEHOLDER – to be identified from measurements
    fin_semi_z: float = 0.060      # [m] PLACEHOLDER – to be identified from measurements
    fin_thickness: float = 0.006   # [m] 2·fin_semi_axes[1] from MuJoCo; PLACEHOLDER – to be identified from measurements
    # Deliberate deviation from MuJoCo: in MuJoCo the fin overlaps the tail by 2 mm, but there it
    # is welded rigidly. In FEM a 2 mm joint would be a ~6×40 mm neck, i.e. an unwanted
    # hinge. Therefore the fin root reaches deeper into the tail end.
    fin_root_overlap: float = 0.015  # [m]

    # ------------------------------------------------------------------ hydraulic chambers
    chamber_x_start: float = 0.01  # [m] thickness of the front wall at the mount; PLACEHOLDER – to be identified from measurements
    wall_thickness: float = 0.004  # [m] outer wall of the chamber; PLACEHOLDER – to be identified from measurements
    septum_thickness: float = 0.004  # [m] septum between chambers L and R; PLACEHOLDER – to be identified from measurements
    # Chamber length = length of the actuated MuJoCo segments (computed in __post_init__).
    # Working range of the volume increase of one chamber (stage 2: p–V curve, monotonicity
    # test). 50 ml ≈ 55% of the chamber volume, ~16° of bending for V4.
    dV_max: float = 50e-6          # [m³] PLACEHOLDER – to be identified from measurements

    # ------------------------------------------------------------------ antagonistic hydraulics (stage 4)
    # Names as in MuJoCo/fishsim/config.py. The pump moves fluid from R to L: V_p > 0 means
    # pumping into L, the tail bends towards −Y (to the right) – same as +V_bias in MuJoCo (right
    # turn). We prescribe VOLUME V_ref(t), not flow rate (rationale in hydraulics.py).
    tail_freq: float = 2.0          # [Hz] as in MuJoCo
    # Deliberate deviation from MuJoCo (decision in stage 4): the SOFA chamber holds 91 ml, not 30 ml
    # like V0_chamber in MuJoCo, so the MuJoCo A_V = 8 ml would give only ~±3° here (README).
    # 17 ml is the largest amplitude with margin at V_prefill = 20 ml (see V_prefill).
    tail_volume_amp: float = 17e-6  # [m³] A_V; PLACEHOLDER – to be identified from measurements
    tail_volume_bias: float = 0.0   # [m³] V_bias – constant tail deflection (turning)
    K_v: float = 10.0               # [1/s] volume error correction; K_v·τ_pump < 0.5 (as in MuJoCo)
    ramp_time: float = 1.0          # [s] soft start of the amplitude (after the prefill)
    # The pump must deliver a peak flow of 2π·f·A_V = 214 ml/s, otherwise it saturates and the
    # amplitude drops (lesson from stage 6). MuJoCo has 60 ml/s – too little for A_V = 17 ml.
    Q_max: float = 250e-6           # [m³/s] PLACEHOLDER – to be identified from measurements
    tau_pump: float = 0.03          # [s] pump time constant, as in MuJoCo; PLACEHOLDER – to be identified from measurements
    p_max: float = 50e3             # [Pa] relief valve on |p_L − p_R|, as in MuJoCo; PLACEHOLDER – to be identified from measurements
    # Flow through the open valve: Q_valve = valve_conductance·(|Δp| − p_max). Value
    # chosen so that the valve is "soft" and stable with explicit pressure readout
    # (10 kPa excess -> 10 ml/s). PLACEHOLDER – to be identified from measurements
    valve_conductance: float = 1e-9  # [m³/(s·Pa)]
    # Pre-filling of both chambers (ramp over prefill_time, before the rhythm). A chamber must not
    # drop below its rest volume (wall contact is not modeled), hence
    # V_prefill > |V_bias| + A_V + prefill_margin. Upper bound from stage 4: with a prefill
    # > ~22 ml both filled chambers compress the spine and the tail starts to buckle
    # (README). 20 ml gives ~53 kPa of common pressure.
    V_prefill: float = 20e-6        # [m³] PLACEHOLDER – to be identified from measurements
    prefill_time: float = 1.0       # [s]
    prefill_margin: float = 2e-6    # [m³]

    # ------------------------------------------------------------------ material (silicone)
    young_modulus: float = 3e5     # [Pa] Dragon Skin / Ecoflex type silicone: order 1e5–1e6; PLACEHOLDER – to be identified from measurements
    # Poisson 0.45, NOT 0.5: silicone is nearly incompressible, but linear tetrahedra
    # "lock" as ν → 0.5 (volumetric locking). Every element must preserve
    # volume, and 4 nodes give too few degrees of freedom to preserve volume and bend
    # at the same time, so the model becomes artificially stiff.
    poisson_ratio: float = 0.45
    rho_silicone: float = 1100.0   # [kg/m³] as rho_tail in MuJoCo; PLACEHOLDER – to be identified from measurements

    # ------------------------------------------------------------------ design variants (stage 2)
    # "Spine": the septum between the chambers along the whole body, made of a material
    # stiffer than the silicone (e.g. harder silicone or with an insert). It acts as an
    # inextensible layer on the bending axis: elongation of the pressurized side turns into bending.
    # Default design = variant V4 from the sweep (stage 2a, README): spine E×20
    # + hoop fibers. Without them the tail barely bends (the chamber bulges).
    # Stage 1 (sag under own weight) was still computed without them (V0).
    spine_E_factor: float = 20.0   # E_spine / E_silicone (1 = none); PLACEHOLDER – to be identified from measurements
    # Hoop fibers: a wrap (thread, fabric) on the tail skin running around the cross-section.
    # It keeps the wall from bulging outwards while barely stiffening the tail axially
    # (the principle of "fiber-reinforced" actuators). Modeled as rings of springs (tension
    # only) along the chambers, just below the skin (fishsofa/fibers.py).
    hoop_fibers: bool = True
    fiber_ring_spacing: float = 0.004   # [m] spacing of the rings along the tail
    fiber_ring_points: int = 64         # points per ring
    fiber_inset: float = 0.0005         # [m] depth below the skin (the point must lie inside a tet)
    # Membrane stiffness of the wrap in the hoop direction = E_fiber · layer thickness [N/m]
    # (e.g. fabric ~1 GPa × 0.2 mm = 2e5 N/m). PLACEHOLDER – to be identified from measurements
    hoop_stiffness: float = 2e5
    include_weight: bool = True    # False = no weight (stage 2: p–V curve depends on the material only)

    # ------------------------------------------------------------------ numerics
    dt: float = 0.002              # [s] time step (stage 1: sag under own weight only)
    # Rayleigh damping in EulerImplicitSolver: C = α·M + β·K. Stands in for the material
    # damping of silicone. Note: implicit Euler also damps by itself (numerically, grows with dt).
    rayleigh_mass: float = 0.1       # α [1/s]; PLACEHOLDER – to be identified from measurements
    rayleigh_stiffness: float = 0.01  # β [s]; PLACEHOLDER – to be identified from measurements
    parallel_fem: bool = False     # ParallelTetrahedronFEMForceField (MultiThreading plugin)
    # Linear system solver in every implicit Euler step:
    #   "ldl" – direct LDLᵀ factorization (exact, but corotational FEM changes the matrix
    #           every step, so it is refactorized every step – this dominates runtime, see README),
    #   "cg"  – conjugate gradient on the assembled matrix, starting from the solution
    #           of the previous step (warm start),
    #   "warp" – PCG with a preconditioner: LDLᵀ factorization once at rest, rotated every step
    #           (see scene._add_warp_solver),
    #   "cholmod" – supernodal Cholesky factorization with CHOLMOD (SuiteSparse), plugin
    #           SofaCHOLMOD built separately for v26.06 (README, "Installation"). As exact as
    #           "ldl" (same results), but dense blocks are computed by BLAS: 4.3× faster on coarse.
    # "warp" without chambers: 6–13× faster than "ldl" for the same trajectory. With a chamber,
    # SurfacePressureConstraint is WRONG at large deformations (30 ml: pressure
    # −25% vs "ldl", because the approximate chamber compliance shifts the equilibrium), so
    # the scene with chambers replaces "warp" with "ldl". Measurements in the README.
    linear_solver: str = "cholmod"
    warp_refactor_steps: int = 10**9  # refactorization interval in steps (in practice: never)
    cg_max_iterations: int = 1000
    cg_tolerance: float = 1e-12    # |r|²/|b|² (square of the relative residual!)
    cholmod_threads: int = 1       # BLAS threads for "cholmod"; 1–6 give the same time (README)

    # Mesh levels for the convergence study: (element size near surfaces,
    # size far from them) [m]. With a 4 mm wall: coarse ≈ 1 element across the thickness,
    # fine ≈ 2. Three elements (~1.3 mm) would give ~450k tets – too many for this demo.
    mesh_levels: dict = field(default_factory=lambda: {
        "test": (0.006, 0.010),    # for pytest only (fast, inaccurate)
        "coarse": (0.004, 0.008),
        "medium": (0.003, 0.006),
        "fine": (0.002, 0.006),
    })
    mesh_dir: str = "meshes"       # relative to the SOFA/ directory

    # fields computed in __post_init__ (do not set manually)
    tail_length: float = field(init=False)
    chamber_length: float = field(init=False)

    def __post_init__(self):
        if self.linear_solver not in ("ldl", "cg", "warp", "cholmod"):
            raise ValueError('linear_solver must be "ldl", "cg", "warp" or "cholmod"')
        if self.environment not in ("air", "water"):
            raise ValueError('environment must be "air" or "water"')
        if not 1 <= self.n_actuated <= self.n_segments:
            raise ValueError("n_actuated must be in the range 1..n_segments")
        if not 0.0 < self.poisson_ratio < 0.5:
            raise ValueError("poisson_ratio must be in (0, 0.5) – see the comment on locking")
        self.tail_length = self.n_segments * self.segment_length
        self.chamber_length = self.n_actuated * self.segment_length
        x_end = self.chamber_x_start + self.chamber_length
        if x_end >= self.tail_length:
            raise ValueError("chamber extends beyond the tail")
        # Narrowest point of the chamber (its end): there must be room for the wall and the septum.
        s = self.scale_at(-x_end)
        if self.ry0 * s - self.wall_thickness <= self.septum_thickness / 2:
            raise ValueError("wall + septum do not fit in the cross-section at the chamber end")
        if self.V_prefill <= abs(self.tail_volume_bias) + self.tail_volume_amp + self.prefill_margin:
            raise ValueError("V_prefill too small: the chamber would drop below its rest volume "
                             "(need V_prefill > |V_bias| + A_V + prefill_margin)")
        if self.fin_root_overlap >= 2 * self.fin_semi_x:
            raise ValueError("fin_root_overlap larger than the fin")

    def scale_at(self, x: float) -> float:
        """Tail cross-section scale at point x (x ≤ 0): 1 at the root, taper_last at the end."""
        return 1.0 + (self.taper_last - 1.0) * (-x) / (self.n_segments * self.segment_length)

    @property
    def chamber_x_range(self) -> tuple:
        """(x_front, x_back) of the chamber; x_front > x_back, because the tail runs along -X."""
        return (-self.chamber_x_start, -(self.chamber_x_start + self.chamber_length))

    @property
    def fin_center_x(self) -> float:
        """Fin center: the front edge reaches fin_root_overlap into the tail end."""
        return -self.tail_length - self.fin_semi_x + self.fin_root_overlap
