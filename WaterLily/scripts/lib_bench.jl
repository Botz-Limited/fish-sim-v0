# Stage 8 – the CAD tail (Fish_Tail.step) on the aquarium test stand, 3D, GPU or CPU.
#
# Same setup as the SOFA bench (bench_config() on the sofa branch, video VID_20261026_105654.mp4):
#   - only the tail, fully submerged in still water (free surface and tank walls not modelled),
#   - 0.5 Hz, constant pump + ±1 valve (relay), Q_const = 4·f·A_V as in SOFA,
#   - tail root bolted to a holder with 2 DOF: sway (y) + yaw about a vertical bearing 0.10 m
#     ahead of the root; surge, heave, roll, pitch locked. MOUNT=fixed clamps the holder.
#
# Geometry: signed distance field of the CAD model on a 1 mm grid (cad/step_to_sdf.py ->
# cad/tail_sdf.bin/.json): body + filled tubes + holder plate (`rest`) and the two 2 mm fin
# plates (`fin`), trilinear interpolation. With CFD cells of 1–2 mm a 2 mm plate is 1–2 cells
# thick and the immersed boundary (kernel half width ε = 1 cell) lets flow through it, so the
# fins are thickened to FIN_MIN_CELLS cells in the CFD (FIN_PAD, documented in the summary).
#
# Body frame (meters): x along the tail (root = front ends of the tubes at 0, fin tip at
# 0.260 m), y sideways, z up. Holder frame = body frame of the straight tail.
#
# Tail deformation is PRESCRIBED (the fluid does not bend the tail, unlike SOFA): midline
# y = θ·h(x), uniform curvature on [BEND_X0, BEND_X1] (tubes + soft body, read from the video:
# the whole silicone body bends, the stiff tip with the caudal fin stays straight), the same
# h(x) and bend_inverse as the 2D/3D fish (src/geometry.jl). θ = V_p/A_r from the valve.
#
# Holder (MOUNT=bench): q = (s, ψ) sway [m], yaw [rad], small angles, linear equations
#   (M + M_a) q̈ₙ₊₁ = Qₙ + M_a q̈ₙ − S θ̈ − C q̇ − K q
#   M   rigid mass matrix of holder + tail (tail from the SDF volume × RHO_TAIL),
#   S   coupling of the bending to (s, ψ): ∫ρ h dV, ∫ρ h (x − x_p) dV (tail inertia while flapping),
#   Qₙ  fluid force F_y and moment M_z about the pivot from the CFD (pressure + viscous),
#   M_a strip-theory added mass (ρπ(H/2)² per length, H = local height of the tail): the fluid
#       added mass is ~3× the solid mass, an explicit coupling without M_a diverges (stage 6:
#       same fix for the tail angle). M_a only stabilises; the CFD supplies the real fluid load.
# GPU: the body is an AutoBody of an isbits map and an SDF struct holding two device arrays
# (Adapt rules below); the map is replaced every step with the new linear tracks (θ, s, ψ).

module Bench3D

using WaterLily, StaticArrays, Printf   # Matrix \ comes with LinearAlgebra, loaded by WaterLily
# Adapt is a dependency of WaterLily (via KernelAbstractions), not of these environments: take the loaded module
const Adapt = Base.loaded_modules[Base.PkgId(Base.UUID("79e6a3ab-5dfb-504d-930d-738a2a938a0e"), "Adapt")]
const FD = WaterLily.ForwardDiff

const RESULTS_DIR = normpath(joinpath(@__DIR__, "..", "results"))
const CAD_DIR = normpath(joinpath(@__DIR__, "..", "cad"))
const SRC = normpath(joinpath(@__DIR__, "..", "src"))
include(joinpath(SRC, "params.jl"))
include(joinpath(SRC, "units.jl"))
include(joinpath(SRC, "valve.jl"))
include(joinpath(SRC, "geometry.jl"))
include(joinpath(SRC, "progress.jl"))

# --- parameters (all PLACEHOLDER – to be identified from measurements) -------------
const L_REF = 0.260              # [m] tail length root -> fin tip (STEP 240.0 -> 500.3 mm), CFD length scale
const U_BENCH = 0.1              # [m/s] velocity scale (peak fin speed ≈ 2π·0.5·0.06 ≈ 0.19 m/s)   # PLACEHOLDER
const BEND_X0 = 0.0              # [m] bending region start (tube front ends)                         # PLACEHOLDER
const BEND_X1 = 0.180            # [m] bending region end = stiff tip start (SOFA step_tip_start)     # PLACEHOLDER
const THETA_AMP = 0.35           # [rad] target tip-slope amplitude (≈ 20°, fin ±6 cm, from the video) # PLACEHOLDER
const BENCH_FREQ = 0.5           # [Hz] (video: period ≈ 2.0 s)
# valve as SOFA bench_config(): A_V 13 ml, Q_const = 4·f·A_V = 26 ml/s (switches at the peaks only);
# A_r chosen so that the V_p amplitude ≈ A_V gives THETA_AMP.
const BENCH_VALVE = ValveParams(; Q_const=26e-6, A_V=13e-6, f_min=0.5, f_max=2.5, A_r=13e-6 / THETA_AMP)
# holder (SOFA bench_config mount_*): pivot ahead of the root, mass, inertia, springs, damping
const PIVOT_X = -0.10            # [m] yaw bearing axis (x in the body frame; y = 0)               # PLACEHOLDER
const MOUNT_MASS = 0.4           # [kg] moving part of the stand (sway)                            # PLACEHOLDER
const MOUNT_IZ = 4e-3            # [kg m²] its inertia about the bearing axis (yaw)                # PLACEHOLDER
const MOUNT_K_SWAY = 0.0         # [N/m]                                                           # PLACEHOLDER
const MOUNT_K_YAW = 0.0          # [N m/rad]                                                       # PLACEHOLDER
const MOUNT_DAMPING = 1.0        # [1/s] c = α·mass (bearing / guide friction)                     # PLACEHOLDER
const RHO_TAIL = 1050.0          # [kg/m³] mean of silicone (1100) and chamber water (SOFA rho_silicone) # PLACEHOLDER
const FIN_MIN_CELLS = 2.5        # [cells] minimum fin thickness in the CFD (numerical choice)

"Bending geometry: only x0, x1 and clampdy of FishGeom are used by bend_h / bend_inverse."
bench_geom(T=Float64) = FishGeom{T}(0, 0, 0, 0, 0, BEND_X0, BEND_X1, L_REF, 0.08)

# --- CAD signed distance field -------------------------------------------------------
"SDF grid on the host: fields `rest`, `fin` [m], voxel 1 at `origin` [m], spacing `h` [m]."
struct TailGrid
    rest::Array{Float32,3}
    fin::Array{Float32,3}
    origin::SVector{3,Float64}
    h::Float64
    meta::Dict{String,Any}
end

function _json_flat(s)
    # minimal reader for the flat tail_sdf.json (numbers, strings, number lists, one nested dict)
    d = Dict{String,Any}()
    for m in eachmatch(r"\"(\w+)\":\s*(\[[^\]]*\]|\"[^\"]*\"|[-+0-9.eE]+)", s)
        k, v = m.captures
        d[k] = startswith(v, "[") ? (occursin('"', v) ? strip.(split(strip(v, ['[', ']']), ','), Ref([' ', '\n', '"'])) :
                                     parse.(Float64, split(strip(v, ['[', ']']), ','))) :
               startswith(v, "\"") ? strip(v, '"') : parse(Float64, v)
    end
    d
end

function load_tail_sdf(dir=CAD_DIR)
    jp = joinpath(dir, "tail_sdf.json"); bp = joinpath(dir, "tail_sdf.bin")
    isfile(bp) || error("$bp missing: run `python cad/step_to_sdf.py` (env with gmsh, e.g. fishsofa)")
    meta = _json_flat(read(jp, String))
    n = Int.(meta["dims"]); N = prod(n)
    raw = Vector{Float32}(undef, 2N)
    read!(bp, raw)
    TailGrid(reshape(raw[1:N], n...), reshape(raw[N+1:end], n...),
             SVector{3}(meta["origin"]...), meta["h"], meta)
end

"Trilinear interpolation in a 3D array at fractional (1-based) index q; outside: edge value + distance."
@inline function _trilin(A, q1, q2, q3, h)
    n1, n2, n3 = size(A)
    c1 = clamp(q1, one(q1), oftype(q1, n1)); c2 = clamp(q2, one(q2), oftype(q2, n2)); c3 = clamp(q3, one(q3), oftype(q3, n3))
    e2 = (q1 - c1)^2 + (q2 - c2)^2 + (q3 - c3)^2                 # beyond the grid box
    out = e2 > 0 ? sqrt(e2) * h : zero(e2)                         # (no sqrt(0): its derivative is NaN)
    i = min(unsafe_trunc(Int, FD.value(c1)), n1 - 1); j = min(unsafe_trunc(Int, FD.value(c2)), n2 - 1)   # c ≥ 1: trunc = floor, no InexactError (GPU hostcalls)
    k = min(unsafe_trunc(Int, FD.value(c3)), n3 - 1)
    a = c1 - i; b = c2 - j; c = c3 - k
    @inbounds begin
        v00 = A[i, j, k] * (1 - a) + A[i+1, j, k] * a
        v10 = A[i, j+1, k] * (1 - a) + A[i+1, j+1, k] * a
        v01 = A[i, j, k+1] * (1 - a) + A[i+1, j, k+1] * a
        v11 = A[i, j+1, k+1] * (1 - a) + A[i+1, j+1, k+1] * a
    end
    (v00 * (1 - b) + v10 * b) * (1 - c) + (v01 * (1 - b) + v11 * b) * c + out
end

"SDF of the straight CAD tail (body frame, meters in) -> grid cells out; negative inside."
struct TailSDF{T,A<:AbstractArray{T,3}} <: Function
    rest::A
    fin::A
    o::SVector{3,T}      # body-frame coordinates of voxel 1 [m]
    invh::T              # 1/voxel size [1/m]
    h::T                 # voxel size [m]
    pad::T               # fin thickening [m]
    inv_lf::T            # CFD cells per m
end

@inline function (s::TailSDF{T})(ξ, t) where {T}
    q1 = (ξ[1] - s.o[1]) * s.invh + 1; q2 = (ξ[2] - s.o[2]) * s.invh + 1; q3 = (ξ[3] - s.o[3]) * s.invh + 1
    dr = _trilin(s.rest, q1, q2, q3, s.h)
    df = _trilin(s.fin, q1, q2, q3, s.h) - s.pad
    min(dr, df) * s.inv_lf
end

Adapt.adapt_structure(to, s::TailSDF) =
    TailSDF(Adapt.adapt(to, s.rest), Adapt.adapt(to, s.fin), s.o, s.invh, s.h, s.pad, s.inv_lf)

"World (grid) -> straight body frame [m]: holder sway s and yaw ψ about the pivot, then the bending."
struct BenchMap{T} <: Function
    g::FishGeom{T}
    o::SVector{3,T}      # grid coordinates of the tail root at rest
    lf::T                # m per cell
    xp::T                # pivot x [m] (body frame)
    t0::T                # grid time of the track start
    θ0::T; rθ::T         # θ track [rad], rate per grid time
    s0::T; rs::T         # sway track [m]
    ψ0::T; rψ::T         # yaw track [rad]
end

@inline function (m::BenchMap)(x, t)
    τ = t - m.t0
    θ = m.θ0 + m.rθ * τ; s = m.s0 + m.rs * τ; ψ = m.ψ0 + m.rψ * τ
    X = (x[1] - m.o[1]) * m.lf; Y = (x[2] - m.o[2]) * m.lf; Z = (x[3] - m.o[3]) * m.lf
    dx = X - m.xp; dy = Y - s
    cψ, sψ = cos(ψ), sin(ψ)
    xb = m.xp + cψ * dx + sψ * dy
    yb = -sψ * dx + cψ * dy
    xr, yr = bend_inverse(m.g, xb, yb, θ)
    SVector(xr, yr, Z)
end

"Grid box (lo, hi) of the cells the body can touch: kept in the map's owner, used by bbox."
struct BenchBody{F<:TailSDF,M<:BenchMap} <: WaterLily.AbstractBody
    body::AutoBody{F,M}
    lo::NTuple{3,Int}
    hi::NTuple{3,Int}
end
WaterLily.measure(b::BenchBody, x, t; fastd²=Inf) = WaterLily.measure(b.body, x, t; fastd²)
WaterLily.sdf(b::BenchBody, x, t=0; kwargs...) = WaterLily.sdf(b.body, x, t; kwargs...)
WaterLily.bbox(b::BenchBody, R::CartesianIndices{3}) =
    CartesianIndices(ntuple(i -> max(first(R.indices[i]), b.lo[i]):min(last(R.indices[i]), b.hi[i]), 3))
Adapt.adapt_structure(to, b::BenchBody) =
    BenchBody(AutoBody(Adapt.adapt(to, b.body.sdf), b.body.map), b.lo, b.hi)

# --- tail mass properties (host) -----------------------------------------------------
"""
    tail_props(grid) -> NamedTuple

From the straight-tail SDF (no fin thickening), with the holder pivot at PIVOT_X:
volume, mass m = RHO_TAIL·V, static moment m(x_c − x_p), inertia about the pivot axis (z),
bending coupling S = (∫ρh dV, ∫ρh(x − x_p) dV), strip-theory added mass matrix M_a and the
height profile H(x).
"""
function tail_props(G::TailGrid; rho=RHO_TAIL, rho_w=RHO, xp=PIVOT_X)
    g = bench_geom(Float64)
    n = size(G.rest); h = G.h; dV = h^3
    xs = [G.origin[1] + (i - 1) * h for i in 1:n[1]]
    ys = [G.origin[2] + (j - 1) * h for j in 1:n[2]]
    zs = [G.origin[3] + (k - 1) * h for k in 1:n[3]]
    V = 0.0; Sx = 0.0; Ixx = 0.0; Iyy = 0.0; S1 = 0.0; S2 = 0.0
    H = zeros(n[1])
    for i in 1:n[1]
        x = xs[i]; r = x - xp; hx = bend_h(g, x)
        zmin, zmax = Inf, -Inf
        for k in 1:n[3], j in 1:n[2]
            if min(G.rest[i, j, k], G.fin[i, j, k]) < 0
                V += dV; Sx += r * dV; Ixx += r^2 * dV; Iyy += ys[j]^2 * dV
                S1 += hx * dV; S2 += hx * r * dV
                zmin = min(zmin, zs[k]); zmax = max(zmax, zs[k])
            end
        end
        H[i] = zmax > zmin ? zmax - zmin + h : 0.0
    end
    ma = [rho_w * π * (Hi / 2)^2 * h for Hi in H]          # lateral added mass per voxel slice [kg]
    rs = xs .- xp
    Ma = [sum(ma) sum(ma .* rs); sum(ma .* rs) sum(ma .* rs .^ 2)]
    m = rho * V
    (; V, m, static=rho * Sx, Ip=rho * (Ixx + Iyy), S=SVector(rho * S1, rho * S2), Ma, xs, H)
end

# --- holder dynamics (host) ----------------------------------------------------------
"2-DOF holder state and matrices; `fixed=true` keeps it at rest."
mutable struct Holder
    fixed::Bool
    M::Matrix{Float64}       # holder + tail rigid mass matrix in (s, ψ)
    Ma::Matrix{Float64}      # added-mass estimate (stabilisation)
    S::SVector{2,Float64}    # bending coupling
    C::Matrix{Float64}
    K::Matrix{Float64}
    q::SVector{2,Float64}
    v::SVector{2,Float64}
    a::SVector{2,Float64}
end

function Holder(props; fixed=false, mass=MOUNT_MASS, Iz=MOUNT_IZ, ks=MOUNT_K_SWAY, kψ=MOUNT_K_YAW,
                α=MOUNT_DAMPING)
    M = [mass + props.m props.static; props.static Iz + props.Ip]
    C = α * [mass 0.0; 0.0 Iz]
    K = [ks 0.0; 0.0 kψ]
    z = SVector(0.0, 0.0)
    Holder(fixed, M, props.Ma, props.S, C, K, z, z, z)
end

"""
    holder_step!(H, dt, Q, θdd) -> (q0, q1)

Advance (s, ψ) over dt [s] with the generalized fluid load Q = (F_y, M_z) [N, N m] of the last
CFD step and the bending acceleration θdd [rad/s²]; semi-implicit Euler, added-mass corrected.
"""
function holder_step!(H::Holder, dt, Q, θdd)
    q0 = H.q
    H.fixed && return q0, q0
    rhs = SVector{2}(Q) + SVector{2}(H.Ma * H.a) - H.S * θdd - SVector{2}(H.C * H.v) - SVector{2}(H.K * H.q)
    a = SVector{2}((H.M + H.Ma) \ rhs)
    H.a = a; H.v = H.v + dt * a; H.q = H.q + dt * H.v
    q0, H.q
end

# --- domain and simulation -----------------------------------------------------------
"Domain in tail lengths L_REF: ahead of the root, behind it, ±side (y), ±vertical (z)."
Base.@kwdef struct BenchDomain
    upstream::Float64 = 0.6      # the holder pivot is 0.38 L ahead of the root
    downstream::Float64 = 2.0
    side::Float64 = 0.75
    vert::Float64 = 0.6
end

_round_up(x, m) = m * ceil(Int, x / m - 1e-9)

function bench_dims(n, d::BenchDomain=BenchDomain())
    Nx = _round_up((d.upstream + d.downstream) * n, 16)
    Ny = _round_up(2d.side * n, 16)
    Nz = _round_up(2d.vert * n, 16)
    (Nx, Ny, Nz), SVector(d.upstream * n, Ny / 2, Nz / 2)
end

struct BenchSim{S}
    sim::S
    units::Units
    origin::SVector{3,Float64}   # loc coordinates of the tail root at rest
    grid::TailGrid               # host copy of the SDF (boxes, mass properties)
    pad::Float64                 # fin thickening [m]
end

"Conservative grid box of the moved, bent tail (host): body-frame box corners at 16 x stations."
function body_box(G::TailGrid, units::Units, origin, θ, s, ψ; margin=6)
    g = bench_geom(Float64)
    lf = unit_factor(units, :length)
    n = size(G.rest); h = G.h; o = G.origin
    x0, x1 = o[1], o[1] + (n[1] - 1) * h
    y0, y1 = o[2], o[2] + (n[2] - 1) * h
    z0, z1 = o[3], o[3] + (n[3] - 1) * h
    lo = [Inf, Inf]; hi = [-Inf, -Inf]
    for x in range(x0, x1; length=16), y in (y0, y1)
        # bent: midline (x, θh) + normal offset y; then holder rigid motion
        hx = bend_h(g, x); m = θ * bend_dh(g, x); nrm = sqrt(1 + m^2)
        xb = x - m * y / nrm; yb = θ * hx + y / nrm
        dx = xb - PIVOT_X
        X = PIVOT_X + cos(ψ) * dx - sin(ψ) * yb
        Y = s + sin(ψ) * dx + cos(ψ) * yb
        lo .= min.(lo, (X, Y)); hi .= max.(hi, (X, Y))
    end
    # cell I has its centre at I − 1.5 (grid coords)
    gx(v, d) = origin[d] + v / lf + 1.5
    ((floor(Int, gx(lo[1], 1)) - margin, floor(Int, gx(lo[2], 2)) - margin, floor(Int, gx(z0, 3)) - margin),
     (ceil(Int, gx(hi[1], 1)) + margin, ceil(Int, gx(hi[2], 2)) + margin, ceil(Int, gx(z1, 3)) + margin))
end

function make_body(G::TailGrid, units::Units, origin; T=Float32, mem=Array, pad=0.0,
                   t0=0.0, θ0=0.0, rθ=0.0, s0=0.0, rs=0.0, ψ0=0.0, rψ=0.0, box=nothing)
    lf = unit_factor(units, :length)
    sdf = TailSDF{T,typeof(mem(T.(G.rest)))}(mem(T.(G.rest)), mem(T.(G.fin)), SVector{3,T}(G.origin...),
                                              T(1 / G.h), T(G.h), T(pad), T(1 / lf))
    map = BenchMap{T}(bench_geom(T), SVector{3,T}(origin...), T(lf), T(PIVOT_X), T(t0), T(θ0), T(rθ),
                      T(s0), T(rs), T(ψ0), T(rψ))
    lo, hi = box === nothing ? body_box(G, units, origin, θ0, s0, ψ0) : box
    BenchBody(AutoBody(sdf, map), lo, hi)
end

"Same SDF arrays, new tracks (grid times) and box: no copy of the device arrays."
function retrack(b::BenchBody, G::TailGrid, units::Units, origin, t0g, t1g, θ0, θ1, q0, q1)
    m = b.body.map; T = typeof(m.lf)
    dt = t1g - t0g
    r(a, c) = dt > 0 ? (c - a) / dt : 0.0
    map = BenchMap{T}(m.g, m.o, m.lf, m.xp, T(t0g), T(θ0), T(r(θ0, θ1)), T(q0[1]), T(r(q0[1], q1[1])),
                      T(q0[2]), T(r(q0[2], q1[2])))
    # box covering both ends of the step
    b0 = body_box(G, units, origin, θ0, q0[1], q0[2]); b1 = body_box(G, units, origin, θ1, q1[1], q1[2])
    BenchBody(AutoBody(b.body.sdf, map), min.(b0[1], b1[1]), max.(b0[2], b1[2]))
end

"Fin thickening [m] so that the 2 mm plates are ≥ FIN_MIN_CELLS cells thick at n cells per L_REF."
fin_pad(n; plate=0.002, min_cells=FIN_MIN_CELLS) = max(0.0, (min_cells * L_REF / n - plate) / 2)

function make_bench_sim(; n=128, Re=RE_SIM_DEFAULT, domain=BenchDomain(), T=Float32, mem=Array,
                        pad=fin_pad(n), grid=load_tail_sdf())
    units = Units(n; Re, L_phys=L_REF, U_phys=U_BENCH)
    dims, origin = bench_dims(n, domain)
    body = make_body(grid, units, origin; T, mem, pad)
    sim = Simulation(dims, (zero(T), zero(T), zero(T)), n; U=one(T), ν=T(nu_grid(units)), body, T, mem,
                     exitBC=false)
    BenchSim(sim, units, SVector{3,Float64}(origin), grid, Float64(pad))
end

t_phys(bs::BenchSim) = to_phys(bs.units, :time, Float64(WaterLily.time(bs.sim.flow)))

"Pivot position in loc coordinates (cell I has its centre at I − 1.5) for the current sway s [m]."
pivot_loc(bs::BenchSim, s) = bs.origin .+ SVector(PIVOT_X, s, 0.0) ./ unit_factor(bs.units, :length)

"""
Force [N] and moment about the pivot [N m] ON the tail (pressure + viscous), 3-vectors.
(WaterLily returns the load of the body on the fluid, hence the sign flips, as in stage 7.)
"""
function body_loads(bs::BenchSim, s)
    sim, u = bs.sim, bs.units
    T = eltype(sim.flow.p)
    x0 = SVector{3,T}(pivot_loc(bs, s)...)
    Fp = -WaterLily.pressure_force(sim); Fv = -WaterLily.viscous_force(sim)
    Mp = -WaterLily.pressure_moment(x0, sim); Mv = -WaterLily.viscous_moment(x0, sim)
    cf = unit_factor(u, :pressure) * unit_factor(u, :area)
    cm = cf * unit_factor(u, :length)
    (; F=cf .* Float64.(Fp .+ Fv), Fp=cf .* Float64.(Fp), M=cm .* Float64.(Mp .+ Mv), Mp=cm .* Float64.(Mp))
end

_cap_dt!(sim, dt_max) = (Δt = sim.flow.Δt; Δt[end] = min(Δt[end], eltype(Δt)(dt_max)); sim)

"""
Pressure clean-up for moving bodies (same as FishLily.clean_pressure!, src/sim.jl, written with
broadcasts so it also runs on the GPU): p = 0 deep inside the body, mean over the first column = 0.
"""
function clean_pressure!(sim; D_min=1e-4)
    P = sim.pois isa WaterLily.MultiLevelPoisson ? sim.pois.levels[1] : sim.pois
    p = sim.flow.p; T = eltype(p)
    R = WaterLily.inside(p)
    @views pin, Din = p[R], P.D[R]
    dmin = T(D_min)
    col = selectdim(pin, 1, 1); okc = abs.(selectdim(Din, 1, 1)) .>= dmin
    nc = count(okc)
    p0 = nc > 0 ? sum(col .* okc) / nc : zero(T)
    @. pin = ifelse(abs(Din) < dmin, zero(T), pin - p0)
    sim
end

# --- field output ----------------------------------------------------------------------
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

"Slices through the root axis: z = 0 (top view), y = 0 (side view), x at a wake station."
function slices(bs::BenchSim; x_wake=L_REF + 0.06)
    sim = bs.sim; o = bs.origin
    k = round(Int, o[3] + 1.5); j = round(Int, o[2] + 1.5)
    iw = round(Int, o[1] + x_wake / unit_factor(bs.units, :length) + 1.5)
    out = Dict{String,Any}()
    tf = unit_factor(bs.units, :time)
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
