# Stage 7 – 3D fish for WaterLily on the GPU (AMDGPU) or CPU.
#
# Loading strategy (documented choice): FishLily is NOT `Pkg.develop`ed into the
# gpu env, because its deps (Plots, DataFrames, CSV, JLD2, ParametricBodies)
# would bloat the GPU environment and could perturb its resolution. Instead this
# module `include`s only the dependency-light FishLily source files
# (params, units, valve, geometry, progress), which need nothing beyond
# WaterLily, StaticArrays and Printf. The same file therefore loads in the gpu
# env (`--project=gpu`) and in the FishLily env (`--project=.`, used for plots).
#
# 3D body (physical body frame, meters): x fish axis (nose at -HEAD_A, tail root
# at 0, tip at L_TAIL), y sideways (top-view profile of the 2D model), z up.
#   cross-section at x: ellipse, half-width w(x) = 2D profile half-thickness,
#   half-height h(x) = K_H·w(x)  (K_H = HEAD_H/T_ROOT, so the head/root is
#   0.05 m high and the tail height tapers 0.05 -> 0.017 m with the width).
#   Implemented as the 2D profile SDF evaluated at (x, ρ), ρ = √(y² + (z/K_H)²):
#   the zero level set is exact; the distance is off by ≤ K_H away from it, and
#   WaterLily's `measure` renormalises d by |∇d| (pseudo-SDF correction).
#   Optional caudal fin: a thin rounded plate at the tail end (FIN=1).
# Bending: the 2D map y = θ·h(x) is applied to (x, y); z is untouched.
#
# GPU safety: the body is an `AutoBody` of two isbits callable structs
# (`FishSDF3`, `FishMap3`). θ(t) is piecewise linear over each CFD step
# (θ0 at t0 -> θ1 at t1, same as the 2D `Track`), and the valve (CPU,
# mutable) is advanced on the host; before each step a NEW isbits map with
# the scalars (t0, θ0, rate) replaces `sim.body` (Simulation is mutable; the
# body type does not change, so no kernel is recompiled).

module Fish3D

using WaterLily, StaticArrays, Printf
using Serialization

const RESULTS_DIR = normpath(joinpath(@__DIR__, "..", "results"))
const SRC = normpath(joinpath(@__DIR__, "..", "src"))
include(joinpath(SRC, "params.jl"))
include(joinpath(SRC, "units.jl"))
include(joinpath(SRC, "valve.jl"))
include(joinpath(SRC, "geometry.jl"))
include(joinpath(SRC, "progress.jl"))

# --- 3D parameters (all PLACEHOLDER – to be identified from measurements) ----------
const HEAD_H = 0.050            # [m] full body height at head / tail root            # PLACEHOLDER
const K_H = HEAD_H / T_ROOT     # [-] height/width ratio of the elliptic sections (5/3)
# optional caudal fin (rounded thin plate in the straight reference frame)
const FIN_X0 = 0.120            # [m] fin start (from the tail root)                  # PLACEHOLDER
const FIN_X1 = 0.165            # [m] fin end (15 mm behind the tail tip)             # PLACEHOLDER
const FIN_HH = 0.030            # [m] fin half height (span 0.06 m)                   # PLACEHOLDER
const FIN_HT = 0.002            # [m] fin half thickness core (+ FIN_R rounding)      # PLACEHOLDER
const FIN_R  = 0.001            # [m] fin edge rounding                               # PLACEHOLDER

"3D domain in body lengths: upstream of the nose, downstream of the tail tip, ±side (y), ±vert (z)."
Base.@kwdef struct Domain3
    upstream::Float64 = 0.75
    downstream::Float64 = 2.25
    side::Float64 = 0.75
    vert::Float64 = 0.5
end

_round_up(x, m) = m * ceil(Int, x / m - 1e-9)

function domain_dims3(n, d::Domain3=Domain3())
    Nx = _round_up((d.upstream + 1 + d.downstream) * n, 16)
    Ny = _round_up(2d.side * n, 16)
    Nz = _round_up(2d.vert * n, 16)
    origin = SVector(d.upstream * n + HEAD_A / L_BODY * n, Ny / 2, Nz / 2)
    return (Nx, Ny, Nz), origin
end

# --- body ------------------------------------------------------------------------
struct FishSDF3{T} <: Function
    g::FishGeom{T}
    kh::T
    inv_lf::T            # cells per m
    fin::Bool
    lo::NTuple{3,Int}    # bounding box (grid indices) of all cells that can be near the body
    hi::NTuple{3,Int}
end

@inline function _rbox(px, py, pz, cx, hx, hy, hz, r)
    qx = abs(px - cx) - hx; qy = abs(py) - hy; qz = abs(pz) - hz
    out = sqrt(max(qx, zero(qx))^2 + max(qy, zero(qy))^2 + max(qz, zero(qz))^2)
    out + min(max(qx, max(qy, qz)), zero(qx)) - r
end

@inline function (s::FishSDF3{T})(ξ, t) where {T}
    x, y, z = ξ[1], ξ[2], ξ[3]
    ρ = sqrt(y^2 + (z / s.kh)^2 + T(1e-12))      # ε keeps the gradient finite on the axis
    d = fish_sdf_straight(s.g, x, ρ)
    if s.fin
        df = _rbox(x, y, z, T((FIN_X0 + FIN_X1) / 2), T((FIN_X1 - FIN_X0) / 2),
                   T(FIN_HT), T(FIN_HH), T(FIN_R))
        d = min(d, df)
    end
    d * s.inv_lf
end

struct FishMap3{T} <: Function
    g::FishGeom{T}
    o::SVector{3,T}      # grid coords of the tail root
    lf::T                # m per cell
    t0::T                # grid time of the track start
    θ0::T                # θ at t0 [rad]
    rate::T              # dθ/dt per grid time unit
end

@inline function (m::FishMap3)(x, t)
    xb = (x[1] - m.o[1]) * m.lf
    yb = (x[2] - m.o[2]) * m.lf
    zb = (x[3] - m.o[3]) * m.lf
    θ = m.θ0 + m.rate * (t - m.t0)
    xr, yr = bend_inverse(m.g, xb, yb, θ)
    SVector(xr, yr, zb)
end

const FishBody3 = AutoBody{<:FishSDF3,<:FishMap3}

# Restrict measure!/forces to a box around the fish (cells outside stay fluid).
function WaterLily.bbox(b::AutoBody{<:FishSDF3,<:FishMap3}, R::CartesianIndices{3})
    lo, hi = b.sdf.lo, b.sdf.hi
    CartesianIndices(ntuple(i -> max(first(R.indices[i]), lo[i]):min(last(R.indices[i]), hi[i]), 3))
end

"Bounding box (grid) for |θ| ≤ θmax plus a margin in cells."
function body_box(units::Units, origin; θmax=0.7, fin=false, margin=5)
    n_per_m = 1 / unit_factor(units, :length)
    g = FishGeom(Float64)
    xend = fin ? max(L_TAIL, FIN_X1) : L_TAIL
    ymax = θmax * bend_h(g, xend) + T_ROOT
    zmax = fin ? max(FIN_HH, HEAD_H / 2) : HEAD_H / 2
    lo = (floor(Int, origin[1] - HEAD_A * n_per_m) - margin,
          floor(Int, origin[2] - ymax * n_per_m) - margin,
          floor(Int, origin[3] - zmax * n_per_m) - margin)
    hi = (ceil(Int, origin[1] + xend * n_per_m) + margin,
          ceil(Int, origin[2] + ymax * n_per_m) + margin,
          ceil(Int, origin[3] + zmax * n_per_m) + margin)
    lo, hi
end

function fish_body3(units::Units, origin; T=Float32, fin=false, t0=0.0, θ0=0.0, rate=0.0, box=nothing)
    g = FishGeom(T)
    lf = T(unit_factor(units, :length))
    lo, hi = box === nothing ? body_box(units, origin; fin) : box
    sdf = FishSDF3{T}(g, T(K_H), inv(lf), fin, lo, hi)
    map = FishMap3{T}(g, SVector{3,T}(origin...), lf, T(t0), T(θ0), T(rate))
    AutoBody(sdf, map)
end

"Replace the map of `body` by a linear θ track (grid times)."
function retrack(body::AutoBody, t0g, θ0, t1g, θ1)
    m = body.map; T = typeof(m.lf)
    rate = t1g > t0g ? (θ1 - θ0) / (t1g - t0g) : 0.0
    AutoBody(body.sdf, FishMap3{T}(m.g, m.o, m.lf, T(t0g), T(θ0), T(rate)))
end

"Mean body height b_eff = (1/L_BODY)∫H(x)dx [m] (H = full height of the section)."
function mean_height(; npts=4001)
    g = FishGeom(Float64)
    xs = range(-HEAD_A, L_TAIL; length=npts)
    # half width at x: bisection on the straight 2D SDF along y
    hw(x) = begin
        fish_sdf_straight(g, x, 0.0) >= 0 && return 0.0
        a, b = 0.0, 0.05
        for _ in 1:50
            c = (a + b) / 2
            fish_sdf_straight(g, x, c) < 0 ? (a = c) : (b = c)
        end
        (a + b) / 2
    end
    H = [2K_H * hw(x) for x in xs]
    sum(H) * step(xs) / L_BODY
end

# --- simulation ------------------------------------------------------------------
struct FishSim3{S}
    sim::S
    units::Units
    origin::SVector{3,Float64}
    U_in::Float64
end

function make_fish_sim3(; n=128, U_in=U_REF, Re=RE_SIM_DEFAULT, domain=Domain3(), T=Float32,
                        mem=Array, fin=false)
    units = Units(n; Re)
    dims, origin = domain_dims3(n, domain)
    body = fish_body3(units, origin; T, fin)
    uin = T(to_grid(units, :velocity, U_in))
    sim = Simulation(dims, (uin, zero(T), zero(T)), n; U=one(T), ν=T(nu_grid(units)), body, T, mem,
                     exitBC=U_in > 0)
    FishSim3(sim, units, SVector{3,Float64}(origin), Float64(U_in))
end

t_phys(fs::FishSim3) = to_phys(fs.units, :time, Float64(WaterLily.time(fs.sim.flow)))
force_factor3(u::Units) = unit_factor(u, :pressure) * unit_factor(u, :area)   # N per grid force

"Force ON the body [N] (3-vectors): pressure, viscous, total. x = inflow direction."
function body_force3(fs::FishSim3)
    Fp = -WaterLily.pressure_force(fs.sim)
    Fv = -WaterLily.viscous_force(fs.sim)
    c = force_factor3(fs.units)
    (; Fp=c .* Float64.(Fp), Fv=c .* Float64.(Fv), F=c .* Float64.(Fp .+ Fv))
end

_cap_dt!(sim, dt_max) = (Δt = sim.flow.Δt; Δt[end] = min(Δt[end], eltype(Δt)(dt_max)); sim)

# --- field output ----------------------------------------------------------------
"Vorticity component i at cell centres into flow.σ (grid units)."
function vort!(sim, i)
    σ, u = sim.flow.σ, sim.flow.u
    σ .= 0
    WaterLily.@loop σ[I] = WaterLily.ω(I, u)[i] over I ∈ WaterLily.inside(σ)
    σ
end
function lambda2!(sim)
    σ, u = sim.flow.σ, sim.flow.u
    σ .= 0
    WaterLily.@loop σ[I] = WaterLily.λ₂(I, u) over I ∈ WaterLily.inside(σ)
    σ
end
function sdf_field!(sim)
    σ = sim.flow.σ
    WaterLily.measure_sdf!(σ, sim.body, WaterLily.time(sim.flow))
    σ
end

"Mid-plane slices (host arrays): z through the fish axis, y through the axis, x at a wake station."
function slices(fs::FishSim3; x_wake=L_TAIL + 0.5L_BODY)
    sim = fs.sim; o = fs.origin
    k = round(Int, o[3] + 1.5); j = round(Int, o[2] + 1.5)   # loc(0,I) = I .- 1.5: cell nearest the axis
    iw = round(Int, o[1] + x_wake / unit_factor(fs.units, :length) + 1.5)
    out = Dict{String,Any}()
    tf = unit_factor(fs.units, :time)                # ω_phys = ω_grid / tf  [1/s]
    for (i, nm) in ((3, "wz_zmid"), (2, "wy_ymid"), (1, "wx_xwake"))
        σ = Array(vort!(sim, i))
        out[nm] = nm == "wz_zmid" ? σ[:, :, k] ./ tf : nm == "wy_ymid" ? σ[:, j, :] ./ tf : σ[iw, :, :] ./ tf
    end
    σ = Array(sdf_field!(sim))
    out["sdf_zmid"] = σ[:, :, k]; out["sdf_ymid"] = σ[:, j, :]; out["sdf_xwake"] = σ[iw, :, :]
    out["k"] = k; out["j"] = j; out["iw"] = iw; out["x_wake"] = x_wake
    out
end

end # module
