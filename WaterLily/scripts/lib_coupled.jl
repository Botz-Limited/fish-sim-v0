# Stage 6 helpers: two-way coupled tail (hydraulics + tail ODE + WaterLily fluid load).
#
# Included by scripts/stage6_coupled.jl (after `using WaterLily, FishLily, StaticArrays`).
# Nothing here changes src/: the driver plugs into `run_fish!` via the
# `AbstractDriver` interface (drive! before the CFD step, observe! after it).
#
# Tail ODE (spec 3.3), generalized coordinate θ = tip slope angle of the bending
# shape y = θ·h(x) (src/geometry.jl):
#
#   J·θ̈ + c·θ̇ + k_e·θ = A_r·Δp + M_fluid,      Δp = clip((V_p − A_r·θ)/C_h, ±p_max)
#
# Relief valve as in MuJoCo `TailHydraulics.step`: when |V_p − A_r·θ| would exceed
# p_max·C_h, the excess volume is vented to the other chamber, i.e. V_p itself is
# reduced (and the relay then sees the reduced V_p). This is done by subtracting the
# vented volume from the streaming `Valve`'s node volume `v.V`.
#
# Fluid load. θ is not a rigid rotation about the root: a surface point moves by
# ∂X/∂θ ≈ (0, h(x)), with h(L_TAIL) = 0.09 m < L_TAIL. The load that is work-conjugate
# to θ is the generalized force Q_θ = ∫ f_y·h(x) ds (force ON the body).
# `tail_pressure_moment` (moment about the root, lever x instead of h(x)) is also logged
# and can be used for the coupling (COUPLE_FORCE=root), but it overstates the load on θ.
# Both are pressure-only and per metre of span (2D); the 3D load is b_eff·(2D value).
#
# Added-inertia stabilisation (partitioned coupling, one fluid solve per CFD step):
#   (J + J_a)·θ̈ + c·θ̇ + k_e·θ = A_r·Δp + M_rest,   M_rest = M_meas,prev + J_a·a_prev
# where a_prev is the tail acceleration the CFD saw in the previous step (jump of the
# piecewise-constant body velocity divided by the step). With a true added inertia J_a*
# the error recursion is a_k = (… + (J_a − J_a*)·a_{k−1})/(J + J_a): stable for
# |J_a − J_a*| < J + J_a, i.e. the estimate may be off by almost a factor 2.
#
# The ODE (stiff hydraulic spring k_h = A_r²/C_h = 5 N·m/rad) is sub-stepped inside
# each CFD step with the implicit trapezoidal rule (A-stable, no numerical damping),
# solved by Newton on the piecewise-linear clip (exact in ≤ 3 iterations).

using WaterLily, StaticArrays, FishLily

# ------------------------------------------------------------------------------------
# Tail structural parameters (3D tail).  ALL PLACEHOLDER – to be identified from measurements.
# ------------------------------------------------------------------------------------
const RHO_SILICONE = 1100.0   # [kg/m^3] as MuJoCo rho_tail                            # PLACEHOLDER – to be identified from measurements
const B_EFF  = 0.05           # [m] effective span (tail height): M_3D = B_EFF·M_2D      # PLACEHOLDER – to be identified from measurements
const K_E    = 0.9            # [N·m/rad] silicone bending stiffness = 3 × 0.3 (MuJoCo stiffness_actuated, 3 actuated joints) # PLACEHOLDER – to be identified from measurements
const C_STRUCT = 0.005        # [N·m·s/rad] material damping (MuJoCo damping_joint)      # PLACEHOLDER – to be identified from measurements
const DT_ODE = 1e-4           # [s] max. ODE sub-step (= valve node step)
# Spike guard (see results/stage6_summary.md): WaterLily occasionally gives a single-step
# pressure-force spike with the moving body at n=128 (also seen in stage 5, identical
# with box=false). A measurement with |Fx| > SPIKE_FX [N/m] or |M_2D| > SPIKE_M [N·m/m]
# (normal values: |Fx| < 60, |M_2D| < 8) is NOT fed to the ODE: the previous fluid load
# is held for that step and the rejection is counted (column `n_reject`).
const SPIKE_FX = 100.0
const SPIKE_M = 20.0

"""
    tail_inertia(; rho=RHO_SILICONE, b=B_EFF, N=2000) -> J [kg·m²]

Generalized inertia of the silicone tail for θ: J = ∫ ρ·b·t(x)·h(x)² dx over the
tail (solid section of height b, linear thickness taper t(x)).
"""
function tail_inertia(; rho=RHO_SILICONE, b=B_EFF, N=2000)
    g = FishGeom(Float64); dx = L_TAIL / N
    sum(rho * b * tail_thickness((i - 0.5) * dx) * bend_h(g, (i - 0.5) * dx)^2 * dx for i in 1:N)
end

Base.@kwdef struct TailParams
    J::Float64 = tail_inertia()
    c::Float64 = C_STRUCT
    k_e::Float64 = K_E
    b_eff::Float64 = B_EFF
end

# ------------------------------------------------------------------------------------
# Generalized fluid force on θ (pressure part), grid units, per span
# ------------------------------------------------------------------------------------
@inline function _masked_pgen(I, p, body, t, ox, oy, lf, X, g)
    T = eltype(p)
    x = WaterLily.loc(0, I, T)
    n = WaterLily.nds(body, x, t)
    xb = (x[1] - ox) * lf - X                 # body-frame x [m]
    h = bend_h(g, xb) / lf                    # lateral displacement per rad [cells]
    ifelse(xb > zero(T), p[I] * n[2] * h, zero(T))
end

"""
    tail_generalized_force(fs) -> Q_θ in physical units [N·m/m] (per span)

Q_θ = −∫ p n_y h(x) ds over the tail (force ON the body, outward normal n), the
pressure load work-conjugate to θ. Uses `flow.σ` as scratch (free between steps).
"""
function tail_generalized_force(fs)
    sim = fs.sim; p, df, body = sim.flow.p, sim.flow.σ, sim.body
    T = eltype(p); t = WaterLily.time(sim.flow); tp = t_phys(fs)
    X = fs.X === nothing ? zero(T) : T(fs.X(tp))
    g = FishGeom(T); lf = T(unit_factor(fs.units, :length))
    ox, oy = T(fs.origin[1]), T(fs.origin[2])
    df .= zero(T)
    WaterLily.@loop df[I] = _masked_pgen(I, p, body, t, ox, oy, lf, X, g) over I ∈ WaterLily.bbox(body, WaterLily.inside(p))
    return moment_phys(fs.units, -Float64(sum(df)))
end

# ------------------------------------------------------------------------------------
# Prescribed-motion driver that also records the generalized force (identification)
# ------------------------------------------------------------------------------------
mutable struct IdentDriver{F} <: AbstractDriver
    θ::F
    rate_prev::Float64
    a_cfd::Float64
    Qgen::Vector{Float64}
end
IdentDriver(θ) = IdentDriver(θ, 0.0, 0.0, Float64[])
function FishLily.drive!(d::IdentDriver, fs, t0, t1)
    θ0, θ1 = Float64(d.θ(t0)), Float64(d.θ(t1))
    set_track!(fs.theta, t0, θ0, t1, θ1)
    rate = (θ1 - θ0) / (t1 - t0)
    d.a_cfd = (rate - d.rate_prev) / (t1 - t0)
    d.rate_prev = rate
    return (; θ=θ1, rate, a_cfd=d.a_cfd)
end
FishLily.observe!(d::IdentDriver, fs, t1, r) = push!(d.Qgen, tail_generalized_force(fs))

# ------------------------------------------------------------------------------------
# Coupled driver
# ------------------------------------------------------------------------------------
"""
    CoupledDriver(f; tail=TailParams(), J_a, force=:gen, p=VALVE, t_ramp=1/f)

Two-way coupled tail. `J_a` [kg·m²] is the 3D added-inertia estimate used for the
stabilisation (2D identified value × b_eff). `force = :gen` (generalized force,
default) or `:root` (tail_pressure_moment about the root).
"""
mutable struct CoupledDriver <: AbstractDriver
    valve::Valve
    tail::TailParams
    J_a::Float64
    force::Symbol
    θ::Float64          # state at the end of the last driven step
    ω::Float64
    rate_prev::Float64  # body angular rate the CFD used in the previous step
    a_cfd::Float64      # acceleration seen by the CFD in the current step
    a_prev::Float64     # ... in the previous (already measured) step
    M_meas::Float64     # last measured fluid load (3D) [N·m]
    M_rest::Float64
    V_vent::Float64     # total vented volume (signed) [m^3]
    t_relief::Float64   # time with the relief valve open [s]
    θmax_abort::Float64
    n_reject::Int
    log::Vector{NTuple{5,Float64}}   # (t, θ, dp, M_2D measured, Fx) – survives a failed run
end
function CoupledDriver(f; tail::TailParams=TailParams(), J_a, force::Symbol=:gen,
                       p::ValveParams=VALVE, t_ramp=1/f, θmax_abort=1.5)
    force in (:gen, :root) || throw(ArgumentError("force must be :gen or :root"))
    CoupledDriver(Valve(f; p, t_ramp), tail, Float64(J_a), force, 0.0, 0.0, 0.0, 0.0, 0.0,
                  0.0, 0.0, 0.0, 0.0, θmax_abort, 0, NTuple{5,Float64}[])
end

# one implicit-trapezoid sub-step of the tail ODE, V_p known at both ends
function _ode_substep(θa, ωa, Va, Vb, h, Jt, c, k, Mr, p::ValveParams)
    Ar, Ch, pm = p.A_r, p.C_h, p.p_max
    Fa = Ar * chamber_dp(Va, θa, p) - c * ωa - k * θa + Mr
    θb = θa + h * ωa                       # predictor
    for _ in 1:6
        ωb = 2 * (θb - θa) / h - ωa
        e = (Vb - Ar * θb) / Ch
        dpb = clamp(e, -pm, pm)
        Fb = Ar * dpb - c * ωb - k * θb + Mr
        R = Jt * (ωb - ωa) * 2 / h - (Fa + Fb)
        dkh = abs(e) < pm ? Ar^2 / Ch : 0.0
        dR = Jt * 4 / h^2 + dkh + c * 2 / h + k
        δ = R / dR
        θb -= δ
        abs(δ) < 1e-13 && break
    end
    ωb = 2 * (θb - θa) / h - ωa
    return θb, ωb
end

function FishLily.drive!(d::CoupledDriver, fs, t0, t1)
    tp, p, v = d.tail, d.valve.p, d.valve
    Jt = tp.J + d.J_a
    d.M_rest = d.M_meas + d.J_a * d.a_prev
    θ0 = d.θ
    nsub = max(1, ceil(Int, (t1 - t0) / DT_ODE - 1e-9)); h = (t1 - t0) / nsub
    limit = p.p_max * p.C_h
    Va = valve_state(v, t0).V_p
    for i in 1:nsub
        tb = t0 + i * h
        Vb = valve_state(v, tb).V_p
        d.θ, d.ω = _ode_substep(d.θ, d.ω, Va, Vb, h, Jt, tp.c, tp.k_e, d.M_rest, p)
        excess = Vb - p.A_r * d.θ                 # relief valve: vent the excess volume
        vent = excess - clamp(excess, -limit, limit)
        if vent != 0
            v.V -= vent; d.V_vent += vent; d.t_relief += h
            Vb -= vent
        end
        Va = Vb
    end
    abs(d.θ) < d.θmax_abort || error("coupled tail diverged: |θ| = $(abs(d.θ)) rad at t = $(t1) s")
    set_track!(fs.theta, t0, θ0, t1, d.θ)
    rate = (d.θ - θ0) / (t1 - t0)
    d.a_cfd = (rate - d.rate_prev) / (t1 - t0)
    d.rate_prev = rate
    st = valve_state(v, t1)
    dp = chamber_dp(st.V_p, d.θ, p)
    return (; V_ref=st.V_ref, V_p=st.V_p, Q=st.Q, s=st.s, θ=d.θ, ω=d.ω, dp, M_rest=d.M_rest,
            a_cfd=d.a_cfd, V_vent=d.V_vent, t_relief=d.t_relief, n_reject=d.n_reject)
end

function FishLily.observe!(d::CoupledDriver, fs, t1, r)
    M2 = d.force === :gen ? tail_generalized_force(fs) : r.M
    st = valve_state(d.valve, t1)
    push!(d.log, (t1, d.θ, chamber_dp(st.V_p, d.θ, d.valve.p), M2, r.Fx))
    if abs(r.Fx) > SPIKE_FX || abs(M2) > SPIKE_M || !isfinite(M2)
        d.n_reject += 1                 # hold the previous load (and a_prev) for this step
        @warn "spike rejected" t1 M2 Fx = r.Fx maxlog = 20
        return nothing
    end
    d.M_meas = d.tail.b_eff * M2
    d.a_prev = d.a_cfd
    nothing
end

# ------------------------------------------------------------------------------------
# Analysis helpers
# ------------------------------------------------------------------------------------
"Linear interpolation of (xs, ys) at x (xs sorted)."
function interp1(xs, ys, x)
    i = clamp(searchsortedlast(xs, x), 1, length(xs) - 1)
    w = (x - xs[i]) / (xs[i+1] - xs[i])
    (1 - w) * ys[i] + w * ys[i+1]
end

"Complex amplitude of the fundamental at frequency f over t ≥ t_from (whole cycles, trapezoid)."
function fundamental(t, y, f; t_from)
    ncyc = floor(Int, (t[end] - t_from) * f)
    ncyc < 1 && return complex(NaN)
    t_to = t_from + ncyc / f
    m = (t .>= t_from) .& (t .<= t_to)
    tt = t[m]; yy = y[m]
    z = yy .* cis.(-2π * f .* tt)
    s = sum(0.5 .* (z[1:end-1] .+ z[2:end]) .* diff(tt))
    return 2 * s / (tt[end] - tt[1])
end

"Half peak-to-peak amplitude over t ≥ t_from."
function halfpp(t, y; t_from)
    m = t .>= t_from
    (maximum(y[m]) - minimum(y[m])) / 2
end

"""
    live_hook(fs, t_end; title) -> nothing

Live viewer: run with env FISH_LIVE=1. `run_fish!` then opens the GLMakie viewer by
itself when `on_frame === nothing` (FishLily `maybe_live_hook`, viz/FishLive.jl), so this
returns `nothing` on purpose and is kept only as the one place to customise it.
"""
live_hook(fs, t_end; title="") = nothing
