# Helpers shared by the stage 2–4 scripts (flapping tail driven by the valve).
# `include("stage_common.jl")` after `using WaterLily, FishLily, ...`.
#
# Contents:
#   window_mean / window_minmax   time-weighted means over whole tail cycles
#   cycle_window                  averaging window [t_a, t_b] made of whole cycles after the transient
#   TailExtras                    extra per-step readouts (tail generalized force Q_θ, tail pressure force)
#   VortSnaps                     vorticity snapshots at given times (for still-water pictures)
#   live_hook                     optional live viewer (env FISH_LIVE=1), see viz/README.md
#   job_args                      "run <case...>" / "report" command line of the sweep scripts
using WaterLily, FishLily, StaticArrays, DataFrames, CSV, Printf, Statistics

const T_TRANSIENT = 2.0   # [s] valve start-up transient (≈ 1.2–1.5 s, NOTES.md item 8) – discarded

"""
    cycle_window(f; n_cycles, t_skip=T_TRANSIENT) -> (t_a, t_b)

Averaging window of `n_cycles` whole tail cycles that starts at the first
cycle boundary (t = k/f, V_ref starts at t = 0) at or after `t_skip`.
"""
function cycle_window(f; n_cycles, t_skip=T_TRANSIENT)
    t_a = ceil(t_skip * f - 1e-9) / f
    return t_a, t_a + n_cycles / f
end

"""
    valve_lock_time(f) -> t [s]

End of the valve start-up transient: the time of the first switch after which every
switch interval is within 5 % of half a period (from the pure valve model, no CFD).
≈ 1.2 / 1.05 / 1.94 / 3.07 / 0.77 s at f = 1.5 / 1.75 / 2 / 2.25 / 2.5 Hz.
"""
function valve_lock_time(f; t_end=12.0)
    v = valve_series(f, t_end); ts = switch_times(v.t, v.s); d = diff(ts)
    bad = findall(x -> abs(x - 1 / (2f)) > 0.05 / (2f), d)
    isempty(bad) ? ts[1] : ts[bad[end]+1]
end
"Start of averaging: ≥ 2 s and after the valve has locked onto V_ref."
t_skip_valve(f) = max(T_TRANSIENT, valve_lock_time(f))

"Time-weighted (trapezoid) mean of `df[!,col]` over t_a ≤ t ≤ t_b."
function window_mean(df, col, t_a, t_b)
    m = (df.t .>= t_a) .& (df.t .<= t_b + 1e-9)
    t = df.t[m]; y = Float64.(df[m, col])
    length(t) < 2 && return NaN
    dt = diff(t)
    sum(0.5 .* (y[1:end-1] .+ y[2:end]) .* dt) / sum(dt)
end
window_mean(t::AbstractVector, y::AbstractVector, t_a, t_b) =
    window_mean(DataFrame(t=t, y=y), :y, t_a, t_b)

"Mean over the cycles in [t_a, t_b] of the per-cycle peak-to-peak of `col`."
function cycle_peak_to_peak(df, col, f, t_a, t_b)
    pp = Float64[]
    for k in 0:round(Int, (t_b - t_a) * f)-1
        c0 = t_a + k / f; c1 = c0 + 1 / f
        m = (df.t .>= c0) .& (df.t .< c1)
        count(m) > 2 && push!(pp, maximum(df[m, col]) - minimum(df[m, col]))
    end
    isempty(pp) ? NaN : mean(pp)
end

"Valve switches per tail cycle inside [t_a, t_b] (from the logged valve state `s`)."
function switches_in_window(df, f, t_a, t_b)
    ts = switch_times(df.t, df.s)
    count(t -> t_a <= t <= t_b, ts) / ((t_b - t_a) * f)
end

# --- pressure clean-up (workaround, see results/stage2-4_summary.md) ---------------------
#
# Found in stage 2/3 (moving body): cells deep inside the body have a (nearly) singular row
# in the pressure Poisson matrix: D = Σ face μ₀ is 0 or ≈ 3e-11 (WaterLily's μ₀ kernel cuts
# off only at d < −1 + √eps). Their pressure becomes huge (|p| up to 1e8–1e12 grid units)
# and stays there between steps. When the bending tail moves and such a cell gets larger face
# coefficients, the stale value is a huge residual for the next solve: the forces explode
# (F_x ~ 1e3–1e8 N/m) and at U = 0.05 m/s the flow itself was corrupted (Δt collapsed).
# The fluid pressure level also random-walks (p is only fixed up to a constant).
# Workaround, applied after EVERY step (no effect on the velocity field of that step):
#   p .-= mean(p over the inlet-side column)   -> reference p∞ = 0 far upstream
#   p[cells with |D| < D_MIN] = 0               -> no stale garbage in (nearly) solid cells
# Cells with |D| < 1e-4 (fluid cells have |D| ≈ 4) lie at d < −0.95 cells inside the surface,
# where the force kernel weight is < 0.6 %, so the readouts are not affected.

# This workaround now lives in src: `run_fish!` calls `FishLily.clean_pressure!` after every
# step, BEFORE the readouts, for a moving body (keyword `pressure_fix`, default on when the
# body is re-measured; NOTES.md "Pressure spikes"). The hook below is therefore a no-op, kept
# so the stage 2–4 scripts need no change. (Applying the clean-up twice is not bit-exact in
# Float32 – the second re-level shifts p by round-off – and the flow then drifts chaotically
# away from the old runs; with the no-op the flow is bit-identical to the old hook runs and
# only the readouts see the cleaned p one call earlier.)

"Hook `(sim,row)`: no-op since `run_fish!` cleans the pressure itself (see above)."
pressure_fix!(sim, row=nothing) = nothing

# --- extra readouts on the tail ---------------------------------------------------------
#
# Generalized force of the bending mode. The tail midline is y = θ·h(x) (geometry.jl), so a
# surface point moves sideways with v_y = θ̇·h(x) (small angle; the x-motion is second
# order). The work conjugate of θ is
#     Q_θ = ∫ f_y h(x) ds,     f = −p n  (pressure force on the body per area),
# and the power the tail puts into the fluid is   P = −Q_θ θ̇ = ∫ p (u_body·n) ds.
# (The plain tail moment about the root, M, weighs the forces with x instead of h(x) and is
# logged too; P_M = −M θ̇ would over-weight the root region and is only a cross-check.)

@inline function _qtheta_kernel(I, p, body, t, x0, xcut, len, g)
    T = eltype(p)
    x = WaterLily.loc(0, I, T)
    n = WaterLily.nds(body, x, t)
    xb = (x[1] - x0) * len                       # body-frame x [m] from the tail root
    ifelse(x[1] > xcut, p[I] * n[2] * T(bend_h(g, xb)), zero(T))
end

"""
    tail_qtheta(fs) -> Q_θ [N·m/m]  (generalized pressure force of the bending mode)

Uses `flow.σ` as scratch (free between steps).
"""
function tail_qtheta(fs::FishSim)
    sim = fs.sim; p, df, body = sim.flow.p, sim.flow.σ, sim.body
    T = eltype(p); t = WaterLily.time(sim.flow)
    x0 = T(root_grid(fs, t_phys(fs))[1])
    len = T(unit_factor(fs.units, :length)); g = FishGeom(T)
    df .= zero(T)
    WaterLily.@loop df[I] = _qtheta_kernel(I, p, body, t, x0, x0, len, g) over I ∈ WaterLily.inside(p)
    # the kernel sums (grid force) × h [m]  ->  N/m × m = N·m/m
    return force_phys(fs.units, -Float64(sum(df)))
end

"""
    TailExtras(fs)

Callable hook `(sim, row) -> nothing` for `run_fish!(...; on_frame, frame_every=1)` that
records per step: t, Q_θ (generalized force), Fx_tail_p (pressure force on the tail in x,
N/m). Collect with `DataFrame(te)`.
"""
mutable struct TailExtras
    fs::Any
    t::Vector{Float64}
    Qθ::Vector{Float64}
    Fx_tail::Vector{Float64}
end
TailExtras(fs) = TailExtras(fs, Float64[], Float64[], Float64[])
function (te::TailExtras)(sim, row)
    fs = te.fs
    push!(te.t, t_phys(fs))
    push!(te.Qθ, tail_qtheta(fs))
    xr = root_grid(fs, t_phys(fs))[1]
    push!(te.Fx_tail, force_phys(fs.units, Float64(tail_pressure_force(sim; xcut=xr)[1])))
    nothing
end
DataFrames.DataFrame(te::TailExtras) = DataFrame(t=te.t, Qθ=te.Qθ, Fx_tail_p=te.Fx_tail)

# --- vorticity snapshots -------------------------------------------------------------------

"""
    VortSnaps(fs, times)

Hook that stores the vorticity field ω [1/s] (body cells = NaN) the first time the
simulation passes each of `times` [s]. Fields after the run: `t`, `θ`, `ω` (vector of
matrices), plus the cell coordinates `x`, `y` [m] relative to the tail root.
"""
mutable struct VortSnaps
    fs::Any
    times::Vector{Float64}
    next::Int
    t::Vector{Float64}
    θ::Vector{Float64}
    ω::Vector{Matrix{Float64}}
end
VortSnaps(fs, times) = VortSnaps(fs, sort(collect(Float64, times)), 1, Float64[], Float64[], Matrix{Float64}[])
function (vs::VortSnaps)(sim, row)
    vs.next > length(vs.times) && return nothing
    fs = vs.fs; t = t_phys(fs)
    t + 1e-12 >= vs.times[vs.next] || return nothing
    σ = sim.flow.σ
    WaterLily.@inside σ[I] = WaterLily.curl(3, I, sim.flow.u)
    ω = Array(σ)[2:end-1, 2:end-1] .* unit_factor(fs.units, :frequency)
    measure_sdf!(σ, sim.body, WaterLily.time(sim.flow))
    d = Array(σ)[2:end-1, 2:end-1]
    ω = Float64.(ω); ω[d .< 0] .= NaN
    push!(vs.t, t); push!(vs.θ, get(row, :θ, NaN)); push!(vs.ω, ω)
    vs.next += 1
    nothing
end
"Cell-centre coordinates [m] relative to the tail root at X = 0."
function snap_coords(fs::FishSim, ω)
    L = unit_factor(fs.units, :length)
    x = ((1:size(ω, 1)) .+ 0.5 .- fs.origin[1]) .* L     # cell i (1-based, ghost removed) centre at i+0.5
    y = ((1:size(ω, 2)) .+ 0.5 .- fs.origin[2]) .* L
    x, y
end

# --- several hooks in one --------------------------------------------------------------------
"Combine on_frame hooks (each `(sim,row)`; `nothing` entries are skipped)."
chain_hooks(hs...) = (sim, row) -> (for h in hs; h === nothing || h(sim, row); end; nothing)

# --- optional live viewer --------------------------------------------------------------------
"""
    live_hook(fs, t_end; driver=nothing, title) -> hook or nothing

Live GLMakie view while the run computes, switched on with the environment variable
`FISH_LIVE=1` (FishLily.maybe_live_hook, src/live.jl). Returns `nothing` when it is off.
Our scripts pass their own `on_frame`, so run_fish!'s automatic viewer does not start and
this hook is chained in instead; call `live_finish!(hook)` after the run.
"""
live_hook(fs, t_end; driver=nothing, title=fs.name) = maybe_live_hook(fs, t_end; driver, title)

# --- command line of the sweep scripts -------------------------------------------------------
"""
    job_args(all_cases) -> (mode, cases)

`julia script.jl`                  run all cases, then report
`julia script.jl run c1 c2 ...`    run only these cases (one process per job in parallel)
`julia script.jl report`           only collect the per-case CSVs and make table + plots
"""
function job_args(all_cases)
    isempty(ARGS) && return :all, all_cases
    ARGS[1] == "report" && return :report, String[]
    ARGS[1] == "run" || error("usage: script.jl [run <case...> | report]")
    cases = ARGS[2:end]
    bad = setdiff(cases, all_cases)
    isempty(bad) || error("unknown cases $(bad); known: $(all_cases)")
    return :run, cases
end
