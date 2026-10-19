# Force / moment readouts.
#
# WaterLily 1.9.2 metric functions (not exported, call as WaterLily.xxx):
#   pressure_force(sim), viscous_force(sim), total_force(sim)        -> ∫ τ·n ds
#   pressure_moment(x₀,sim), viscous_moment(x₀,sim), total_moment(x₀,sim)
# with n the OUTWARD body normal and τ = p·I − 2νS (kinematic, grid units).
# Hence the force ON THE BODY is MINUS these (checked against the hydrostatic
# test in WaterLily/test/test_metrics.jl: pressure_force = +∫∇p dV).
# Everything below returns the force on the body, in grid units or converted.

"""
    body_force(sim) -> (; Fp, Fv, F)

Force on the body (pressure, viscous, total) in grid units (per unit span),
as 2-vectors.
"""
function body_force(sim)
    Fp = -WaterLily.pressure_force(sim)
    Fv = -WaterLily.viscous_force(sim)
    return (; Fp, Fv, F=Fp .+ Fv)
end

# 2D cross product r × n (scalar, z-component)
@inline _cross2(r, n) = r[1] * n[2] - r[2] * n[1]

@inline function _masked_pmoment(I, p, body, t, x₀, xcut)
    T = eltype(p)
    x = WaterLily.loc(0, I, T)
    n = WaterLily.nds(body, x, t)
    ifelse(x[1] > xcut, p[I] * _cross2(x - x₀, n), zero(T))
end
@inline function _masked_pforce(I, i, p, body, t, xcut)
    T = eltype(p)
    x = WaterLily.loc(0, I, T)
    n = WaterLily.nds(body, x, t)
    ifelse(x[1] > xcut, p[I] * n[i], zero(T))
end

"""
    tail_pressure_moment(sim, x₀; xcut=x₀[1]) -> M (grid units)

Pressure moment (z) ON the body about point `x₀` (grid), integrated only over
the surface with x > `xcut` (grid), i.e. the tail when x₀ is the tail root.
Positive = counter-clockwise (bends the tail towards +y).
"""
function tail_pressure_moment(sim, x₀; xcut=x₀[1])
    p, df, body = sim.flow.p, sim.flow.σ, sim.body
    T = eltype(p); t = WaterLily.time(sim.flow)
    x0 = SVector{2,T}(x₀...); xc = T(xcut)
    df .= zero(T)
    WaterLily.@loop df[I] = _masked_pmoment(I, p, body, t, x0, xc) over I ∈ WaterLily.bbox(body, WaterLily.inside(p))
    return -sum(df)        # force on body = −∫p n ds
end

"""
    tail_pressure_force(sim; xcut) -> SVector (grid units)

Pressure force on the part of the body with x > `xcut` (grid).
"""
function tail_pressure_force(sim; xcut)
    p, df, body = sim.flow.p, sim.flow.σ, sim.body
    T = eltype(p); t = WaterLily.time(sim.flow); xc = T(xcut)
    F = zeros(T, 2)
    for i in 1:2
        df .= zero(T)
        WaterLily.@loop df[I] = _masked_pforce(I, i, p, body, t, xc) over I ∈ WaterLily.bbox(body, WaterLily.inside(p))
        F[i] = -sum(df)
    end
    return SVector{2,T}(F)
end

"Force (grid, per span) -> N/m."
force_phys(u::Units, F) = to_phys(u, :force, F)
"Moment (grid, per span) -> N·m/m."
moment_phys(u::Units, M) = to_phys(u, :moment, M)
"""
    force_coeff(u, F; U_phys=u.U_phys, L_phys=u.L_phys)

Force coefficient F/(½ ρ U² L) from a grid force; reference speed/length in SI.
"""
force_coeff(u::Units, F; U_phys=u.U_phys, L_phys=u.L_phys) =
    force_phys(u, F) ./ (0.5 * u.rho * U_phys^2 * L_phys)
