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

import numpy as np


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
    # 13 ml: with Q_const = 100 ml/s (7.7·A_V) the strokes reach ≈ ±16.5 ml, below V_prefill − margin = 18 ml.
    tail_volume_amp: float = 13e-6  # [m³] A_V; PLACEHOLDER – to be identified from measurements
    tail_volume_bias: float = 0.0   # [m³] V_bias – constant tail deflection (turning)
    ramp_time: float = 1.0          # [s] soft start of the amplitude (after the prefill)
    # Constant-speed pump + directional valves (s = ±1, no closed state), hysteresis relay
    # (hydraulics.TailRhythm). V_p tracks V_ref only while 2π·f·A_V < Q_const; above
    # f_track = Q_const/(2π·A_V) the valve switches only at the peaks and the amplitude drops
    # to ≈ Q_const/(4f). Decision (13.10.2026): Q_const = 7.5·A_V on every branch (MuJoCo ratio
    # 60/8) -> f_track ≈ 1.2 Hz < tail_freq_min, so the relay switches twice per cycle.
    Q_const: float = 100e-6         # [m³/s] pump flow (replaces Q_max); PLACEHOLDER – to be identified from measurements
    tau_valve: float = 0.02         # [s] valve switching + stream reversal (replaces tau_pump); PLACEHOLDER – to be identified from measurements
    valve_hysteresis: float = 1e-6  # [m³] δ – relay hysteresis on V_ref − V_p; PLACEHOLDER – to be identified from measurements
    # The valve switches at most ~5 times/s, so every valve state lasts at least 0.2 s.
    valve_min_dwell: float = 0.2    # [s] minimum time between valve switches; PLACEHOLDER – to be identified from measurements
    # Lowest allowed flapping frequency (all demos). Above f_track ≈ 1.2 Hz the relay switches
    # exactly twice per cycle.
    # User decision (13.10.2026): 1.5 Hz, not 1.25 Hz – at 1.25 Hz the valve adds extra switches
    # per cycle and the turn bias is jerky from cycle to cycle.
    tail_freq_min: float = 1.5      # [Hz]
    # 2 switches per cycle with every state ≥ valve_min_dwell -> f ≤ 1/(2·valve_min_dwell) = 2.5 Hz.
    tail_freq_max: float = 2.5      # [Hz]
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

    # ------------------------------------------------------------------ mount (boundary condition at the root)
    # "fixed" – front wall clamped, 0 DOF (tail bolted to the body; stages 1–6).
    # "bench" – aquarium test stand (video VID_20261026_105654.mp4, bench_config()): the front
    #           wall is bolted to a rigid holder that has 2 DOF – sway (translation along Y,
    #           perpendicular to the tail, horizontal) and yaw (rotation about the vertical Z axis
    #           in a bearing). Surge, heave, roll and pitch are locked.
    mount: str = "fixed"
    # Yaw bearing axis: vertical line through (mount_pivot_x, 0, ·), i.e. ahead of the tail root
    # (+X, towards the holder). PLACEHOLDER – to be measured on the stand.
    mount_pivot_x: float = 0.10    # [m]
    # Moving part of the stand (holder ring + tube + bracket; the tail itself is NOT included):
    # mass for sway, moment of inertia about the bearing axis for yaw. PLACEHOLDER – to be measured.
    mount_mass: float = 0.4        # [kg]
    mount_inertia_z: float = 4e-3  # [kg·m²]
    # Return springs of the stand (0 = free, as the stand looks in the video). PLACEHOLDER – to be measured.
    mount_k_sway: float = 0.0      # [N/m]
    mount_k_yaw: float = 0.0       # [N·m/rad]
    # Bearing / guide friction as Rayleigh mass damping of the holder: c_sway = α·mount_mass,
    # c_yaw = α·mount_inertia_z. Water drag on the holder is not modeled. PLACEHOLDER – to be measured.
    mount_damping: float = 1.0     # α [1/s]

    # ------------------------------------------------------------------ geometry source
    # "param" – the parametric tail above (ellipse, linear taper, 2 chambers with a septum),
    # "step"  – mesh of the CAD model step_file (fishsofa/step_mesh.py): 8 tubes (4 per side
    #           = chambers L/R), silicone body, plastic fins, stiff tail tip, holder plate.
    #           The parametric dimensions above are then unused (only validated).
    geometry: str = "param"
    step_file: str = "cad/Fish_Tail.step"   # relative to the SOFA/ directory
    step_tip_start: float = 0.180  # [m] stiff tip from here to the body end (fin root inside the body)
    step_plate_thickness: float = 0.003  # [m] holder plate closing the tube front ends (rigid, base nodes)
    # Materials of the STEP regions. All PLACEHOLDER – to be identified from measurements.
    # Body silicone: young_modulus / rho_silicone above.
    young_tube: float = 6e5        # [Pa] tube wall (×2 the body; unknown silicone)
    young_tip: float = 3e6         # [Pa] stiff tail tip (×10 the body)
    young_fin: float = 2e9         # [Pa] fin plates (plastic sheet, e.g. PETG)
    rho_fin: float = 1270.0        # [kg/m³] (PETG)
    # Mesh levels of the STEP tail: (fTetWild target edge length [m], envelope ε relative to the
    # bounding-box diagonal ≈ 0.3 m -> 1e-3 ≈ 0.3 mm). Tube walls are ~3 mm and fins 2 mm thick.
    step_mesh_levels: dict = field(default_factory=lambda: {
        "test": (0.006, 1e-3),   # ε·0.3 m must stay < OVERLAP (0.5 mm) or joints leak
        "coarse": (0.004, 1e-3),
        "medium": (0.003, 1e-3),
        "fine": (0.002, 5e-4),
    })

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
        if self.mount not in ("fixed", "bench"):
            raise ValueError('mount must be "fixed" or "bench"')
        if self.geometry not in ("param", "step"):
            raise ValueError('geometry must be "param" or "step"')
        if self.mount == "bench" and (self.mount_mass <= 0 or self.mount_inertia_z <= 0):
            raise ValueError("mount_mass and mount_inertia_z must be > 0 for the bench mount")
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
        # tail_freq is also used directly (cycle length in scripts and analysis), so a value
        # outside the valve range is an error here, not a silent clamp as in TailRhythm.
        if not self.tail_freq_min <= self.tail_freq <= self.tail_freq_max:
            raise ValueError("tail_freq outside [tail_freq_min, tail_freq_max] (valve switching limit)")
        if self.tail_freq_max > 1 / (2 * self.valve_min_dwell) + 1e-12:
            raise ValueError("tail_freq_max > 1/(2·valve_min_dwell): the valve cannot switch twice per cycle")
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

    def region_young(self, region):
        """Young's modulus [Pa] per material region (tet_region of mesh_gen / step_mesh)."""
        region = np.asarray(region)
        e = np.full(region.shape, self.young_modulus)                      # 0 body silicone
        e[region == 1] = self.young_modulus * self.spine_E_factor          # 1 spine (param geometry)
        e[region == 2] = self.young_tube                                   # 2 tubes (step)
        e[region == 3] = self.young_tip                                    # 3 stiff tip (step)
        e[region == 4] = self.young_fin                                    # 4 fins (step)
        e[region == 5] = self.young_fin                                    # 5 holder plate (rigid, step)
        return e

    def region_density(self, region):
        """Density [kg/m³] per material region (holder plate: its nodes are all constrained)."""
        region = np.asarray(region)
        rho = np.full(region.shape, self.rho_silicone)
        rho[region == 4] = self.rho_fin
        return rho


def bench_config(**overrides) -> TailConfig:
    """Aquarium test stand (video VID_20261026_105654.mp4, 26.10.2026) with the tail of Fish_Tail.step.

    Boundary conditions read from the video:
      - tail fully submerged in still water, caudal fin vertical, its top edge ~10–15 mm below
        the surface (tail axis ~80 mm deep; the free surface is not modeled),
      - tail root bolted to a holder with 2 DOF: sway (Y) + yaw about a vertical bearing (Z),
        everything else locked (mount="bench", parameters mount_* above),
      - flapping ≈ 0.5 Hz (period ≈ 2.0 s from the fin position, 30–68 s of the video).

    Geometry: the CAD model itself (geometry="step", fishsofa/step_mesh.py). Lengths from the
    tail root = front ends of the tubes (STEP x = 240.0 mm): tubes 0–50 mm, body 50–220 mm,
    caudal fin 180–260.3 mm (front 40 mm inside the body end), ventral fin 73–134 mm.
    Stiffer tail tip from 180 mm (where the fin plate sits in the body) and plastic fins.

    The parametric fields below only matter with geometry="param" (fallback: same lengths,
    elliptical section, taper 0.117 = STEP end width 7.8 mm).
    """
    params = dict(
        environment="water",
        mount="bench",
        geometry="step",
        # fallback parametric tail: 8 × 27.5 = 220 mm, chambers 2 × 27.5 = 55 mm (tubes: 50 mm)
        n_segments=8,
        n_actuated=2,
        segment_length=0.0275,
        ry0=0.0333,                # [m] half width of the tube bundle at the root
        rz0=0.0545,                # [m] half height of the tube bundle at the root
        taper_last=0.117,
        fin_semi_x=0.040,          # [m] 80.3 mm / 2
        fin_semi_z=0.066,          # [m] 132.7 mm / 2
        fin_root_overlap=0.040,    # [m] fin x 420–460 mm lies inside the body
        chamber_x_start=0.004,
        # Valve at 0.5 Hz: Q_const = 4·f·A_V -> triangle amplitude ≈ A_V with the valve switching
        # at the peaks only (2× per cycle), f_track = Q/(2π·A_V) ≈ 0.32 Hz < 0.5 Hz. Same idea as
        # Q = 7.5·A_V at 1.5–2.5 Hz in the swim demos. PLACEHOLDER – measure the pump flow.
        tail_freq=0.5,
        tail_freq_min=0.5,
        Q_const=26e-6,
        ramp_time=2.0,             # [s] one cycle at 0.5 Hz
        # The 8 tubes have no wrap of their own here; hoop fibers stay on (stand-in, unknown
        # whether the red tubes are reinforced). PLACEHOLDER.
        hoop_fibers=True,
    )
    params.update(overrides)
    return TailConfig(**params)
