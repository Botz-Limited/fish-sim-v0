"""Shared parameters of the FSI demo (geometry, material, water, meshes).

NOTE: all physical numbers below are PLACEHOLDER – to be identified from
measurements. They are not calibrated against any real fish or prototype.

Coordinate system (top view, 2D section):
    x – fish axis, from the tail root (x = 0) towards the tip (x = L);
        the inflow goes in +x (the fish "swims" in -x),
    y – sideways (left side of the fish y > 0, right side y < 0),
    z – "span" direction; the 2D model has thickness DEPTH (one layer).
Forces are reported per unit span [N/m], because DEPTH = 1 m (as in the
perpendicular-flap tutorial).
"""

# --- Tail geometry -----------------------------------------------------------
L = 0.15            # tail length [m]                    PLACEHOLDER – to be identified from measurements
T_ROOT = 0.030      # thickness at the root [m]          PLACEHOLDER – to be identified from measurements
T_TIP = 0.010       # thickness at the tip [m]           PLACEHOLDER – to be identified from measurements

# Chambers (left/right), separated by a middle wall
CH_X0 = 0.010       # chamber start (from the root) [m]  PLACEHOLDER – to be identified from measurements
CH_X1 = 0.110       # chamber end [m]                    PLACEHOLDER – to be identified from measurements
W_OUT = 0.003       # outer wall thickness [m]           PLACEHOLDER – to be identified from measurements
W_MID = 0.003       # middle wall thickness [m]          PLACEHOLDER – to be identified from measurements
# The chamber is split by ribs into short cells (PneuNet style). A single long
# chamber "balloons" in 2D: the outer wall bulges like a membrane and the tail
# shortens instead of bending (see NOTES.md, stage 1). The cells are connected
# by a channel outside the section plane, so they share the same pressure.
N_CELLS = 10        # number of cells per chamber [-]    PLACEHOLDER – to be identified from measurements
RIB = 0.0015        # rib thickness between cells [m]    PLACEHOLDER – to be identified from measurements

# --- Rigid "head" (half-ellipse in front of the root) ------------------------
HEAD_A = 0.060      # semi-axis in x [m]                 PLACEHOLDER – to be identified from measurements
HEAD_B = T_ROOT / 2 # semi-axis in y = half the root thickness (smooth transition)

# --- Fluid domain (multiples of L) -------------------------------------------
UPSTREAM = 3.0 * L    # from the head nose to the inlet   PLACEHOLDER – check the boundary effect
DOWNSTREAM = 8.0 * L  # from the tail tip to the outlet   PLACEHOLDER – check the boundary effect
SIDE = 3.0 * L        # from the axis to the side walls   PLACEHOLDER – check the boundary effect

DEPTH = 1.0         # 2D model thickness in z [m] (as in the tutorial: forces in N/m)

# --- Tail material (silicone) ------------------------------------------------
E_SOLID = 3.0e5     # Young's modulus [Pa] (range 1e5–1e6) PLACEHOLDER – to be identified from measurements
NU_SOLID = 0.45     # Poisson's ratio [-]                  PLACEHOLDER – to be identified from measurements
RHO_SOLID = 1070.0  # density [kg/m^3]                     PLACEHOLDER – to be identified from measurements

# --- Water -------------------------------------------------------------------
RHO_FLUID = 1000.0  # density [kg/m^3]
NU_FLUID = 1.0e-6   # kinematic viscosity [m^2/s]

# --- Meshes ------------------------------------------------------------------
SOLID_H = 1.0e-3    # solid element size [m]; convergence: 0.5/0.75/1.0 mm -> deflection
                    # at 20 kPa 24.31/24.20/24.29 mm (< 0.5%), so 1 mm is enough


def thickness(x):
    """Tail thickness at position x (linear taper)."""
    return T_ROOT + (T_TIP - T_ROOT) * x / L
