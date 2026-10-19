# All physical parameters of the demo, in SI units, in ONE place.
#
# NOTE: every physical number below is a PLACEHOLDER – to be identified from
# measurements. The values are copied from the other branches (MuJoCo
# `fishsim/config.py`, OpenFOAM `tools/params.py`) so that all demos describe
# the same fish and the same valve.
#
# Coordinate system (top view, 2D section, physical body frame):
#   x – fish axis; nose at x = -HEAD_A, tail root at x = 0, tail tip at x = L_TAIL.
#       The inflow goes in +x (the fish "swims" in -x).
#   y – sideways (left side of the fish y > 0).
# Forces are reported per unit span [N/m] (2D section).

# --- Geometry ------------------------------------------------------------------
const HEAD_A = 0.060        # [m] rigid head, half-ellipse semi-axis in x      # PLACEHOLDER – to be identified from measurements
const L_TAIL = 0.150        # [m] tail length                                    # PLACEHOLDER – to be identified from measurements
const T_ROOT = 0.030        # [m] tail thickness at the root                     # PLACEHOLDER – to be identified from measurements
const T_TIP  = 0.010        # [m] tail thickness at the tip                      # PLACEHOLDER – to be identified from measurements
const HEAD_B = T_ROOT / 2   # [m] head semi-axis in y = half root thickness (smooth joint)
const L_BODY = HEAD_A + L_TAIL   # [m] 0.21 m, length scale of the CFD

# Chamber region (bending is concentrated here, uniform curvature), from the
# tail root. Same as OpenFOAM CH_X0/CH_X1 = 0.010/0.110 m -> ξ = 0.067..0.733.
const CH_X0 = 0.010         # [m] chamber start                                  # PLACEHOLDER – to be identified from measurements
const CH_X1 = 0.110         # [m] chamber end                                    # PLACEHOLDER – to be identified from measurements

# --- Water ---------------------------------------------------------------------
const RHO = 1000.0          # [kg/m^3] water density
const NU_WATER = 1.0e-6     # [m^2/s] kinematic viscosity (real water; the CFD uses Re_sim, see units.jl)
const U_REF = 0.2           # [m/s] reference swimming speed (Re = U·L_BODY/ν ≈ 4.2e4) # PLACEHOLDER – to be identified from measurements
const RE_SIM_DEFAULT = 5000.0   # [-] simulated Reynolds number (documented simplification: 2D at 4e4 is not physical either)

# --- Valve and hydraulics (identical to MuJoCo fishsim/config.py) ---------------
"""
    ValveParams

Constant-speed pump + ±1 directional valve (relay with hysteresis and minimum
dwell) + first-order flow response. All fields SI; every value is a
PLACEHOLDER – to be identified from measurements.
"""
Base.@kwdef struct ValveParams
    Q_const::Float64   = 60e-6   # [m^3/s] constant pump flow (60 ml/s)                 # PLACEHOLDER – to be identified from measurements
    A_V::Float64       = 8e-6    # [m^3] amplitude of the volume reference V_ref (8 ml) # PLACEHOLDER – to be identified from measurements
    V_bias::Float64    = 0.0     # [m^3] constant offset of V_ref (steady tail bend)
    tau_valve::Float64 = 0.02    # [s] valve switching + flow reversal time constant    # PLACEHOLDER – to be identified from measurements
    delta::Float64     = 1e-6    # [m^3] relay hysteresis δ (1 ml)                      # PLACEHOLDER – to be identified from measurements
    min_dwell::Float64 = 0.2     # [s] minimum time between valve switches (<= 5/s)     # PLACEHOLDER – to be identified from measurements
    f_min::Float64     = 1.5     # [Hz] lowest allowed tail frequency (user decision, all demos; > f_track ≈ 1.19 Hz)
    f_max::Float64     = 2.5     # [Hz] highest allowed tail frequency = 1/(2·min_dwell)
    A_r::Float64       = 2e-5    # [m^3/rad] hydraulic lever A_eff·r_eff (4e-4 m² · 0.05 m) # PLACEHOLDER – to be identified from measurements
    C_h::Float64       = 8e-11   # [m^3/Pa] hydraulic compliance                        # PLACEHOLDER – to be identified from measurements
    p_max::Float64     = 50e3    # [Pa] relief valve opening pressure                   # PLACEHOLDER – to be identified from measurements
end

const VALVE = ValveParams()
const DT_VALVE = 1e-4       # [s] max. integration sub-step of the valve ODE (as make_actuation.py)

# --- Default fluid domain (multiples of L_BODY), measured in body lengths --------
# PLACEHOLDER – the boundary effect is checked in stage 1 (larger domain run).
Base.@kwdef struct DomainParams
    upstream::Float64   = 1.5   # [L_BODY] from the inlet to the nose
    downstream::Float64 = 4.0   # [L_BODY] from the tail tip to the outlet
    side::Float64       = 1.5   # [L_BODY] from the fish axis to each side wall
end
const DOMAIN = DomainParams()
