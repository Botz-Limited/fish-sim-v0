# Grid <-> physical unit conversion. SINGLE SOURCE OF TRUTH: scripts never
# hand-convert, they call `to_grid` / `to_phys`.
#
# Scales:
#   length    1 L_phys (= L_BODY, 0.21 m)  <->  n cells
#   velocity  1 U_phys (= U_REF, 0.2 m/s)   <->  U grid units (default U = 1)
#   time      derived: t_phys = t_grid · (L_phys/n) / (U_phys/U)
#   density   ρ (water); WaterLily's pressure is kinematic (p/ρ), so
#             p_phys = ρ · (U_phys/U)^2 · p_grid
#   force     per unit span: F'[N/m] = ρ (U_phys/U)^2 (L_phys/n) F_grid
#   moment    per unit span: M'[N]   = ρ (U_phys/U)^2 (L_phys/n)^2 M_grid
#
# Velocity scale choice: U_phys = U_REF for EVERY case, also in still water
# (inflow 0). Rationale: the units (and Re_sim) are then identical across
# stages 2–6 and results are directly comparable; the inflow is just a BC
# value U_in/U_REF·U. (The tail tip speed, ≈ 2π·f·0.036 m ≈ 0.45 m/s at 2 Hz,
# is of the same order, and WaterLily picks Δt from the CFL condition anyway.)
#
# Viscosity: ν_grid = U·n/Re_sim, Re_sim = U_phys·L_phys/ν_sim (default 5000,
# a documented simplification). Time is NOT rescaled: one physical second of
# tail motion is one physical second of flow, only the viscosity is raised.

"""
    Units(n; U=1, Re=RE_SIM_DEFAULT, L_phys=L_BODY, U_phys=U_REF, rho=RHO)

Conversion between physical SI quantities and WaterLily grid units for a
resolution of `n` cells per `L_phys`.
"""
struct Units
    n::Float64       # cells per L_phys
    U::Float64       # grid velocity scale
    Re::Float64      # simulated Reynolds number U_phys·L_phys/ν_sim
    L_phys::Float64  # [m]
    U_phys::Float64  # [m/s]
    rho::Float64     # [kg/m^3]
end
Units(n; U=1.0, Re=RE_SIM_DEFAULT, L_phys=L_BODY, U_phys=U_REF, rho=RHO) =
    Units(Float64(n), Float64(U), Float64(Re), Float64(L_phys), Float64(U_phys), Float64(rho))

# scale factors: phys = factor · grid
_len(u::Units)  = u.L_phys / u.n                        # [m per cell]
_vel(u::Units)  = u.U_phys / u.U                        # [m/s per grid velocity]
_time(u::Units) = _len(u) / _vel(u)                     # [s per grid time]

"""
    unit_factor(u::Units, q::Symbol)

Physical value of one grid unit of quantity `q`, so `phys = unit_factor·grid`.
Quantities: `:length, :velocity, :time, :frequency, :acceleration, :pressure,
:force` (per span, N/m), `:moment` (per span, N), `:area` (m^2), `:nu` (m^2/s).
"""
function unit_factor(u::Units, q::Symbol)
    q === :length       && return _len(u)
    q === :velocity     && return _vel(u)
    q === :time         && return _time(u)
    q === :frequency    && return 1 / _time(u)
    q === :acceleration && return _vel(u) / _time(u)
    q === :pressure     && return u.rho * _vel(u)^2
    q === :force        && return u.rho * _vel(u)^2 * _len(u)
    q === :moment       && return u.rho * _vel(u)^2 * _len(u)^2
    q === :area         && return _len(u)^2
    q === :nu           && return _len(u) * _vel(u)
    throw(ArgumentError("unknown quantity $q"))
end

"""
    to_grid(u::Units, q::Symbol, x)   physical (SI) -> grid units
    to_phys(u::Units, q::Symbol, x)   grid units -> physical (SI)

Works on numbers and arrays (broadcast).
"""
to_grid(u::Units, q::Symbol, x) = x ./ unit_factor(u, q)
to_phys(u::Units, q::Symbol, x) = x .* unit_factor(u, q)

"Grid viscosity ν = U·n/Re_sim."
nu_grid(u::Units) = u.U * u.n / u.Re
"Physical viscosity actually simulated, ν_sim = U_phys·L_phys/Re_sim [m^2/s]."
nu_sim(u::Units) = u.U_phys * u.L_phys / u.Re

"""
    coefficient(u::Units, F_grid; L=u.n, U=u.U)

Force coefficient C = F/(½ U² L) from a grid force (per span). Default
reference length is L_phys (n cells) and velocity U_phys. Pass e.g. `U=` the
inflow grid velocity to normalize with a different speed.
"""
coefficient(u::Units, F_grid; L=u.n, U=u.U) = F_grid ./ (0.5 * U^2 * L)
