# FishLive: FishViz bound to the FishLily fish model (live window + MP4 helpers).
#
# Loaded either
#   - from the viz environment:  julia --project=viz ...   include("viz/FishLive.jl"); using .FishLive
#   - lazily by FishLily (FISH_LIVE=1 / maybe_live_hook) from the main environment, which
#     appends viz/ to LOAD_PATH first (see src/live.jl).
# Returns the module (last expression), so `m = include(".../FishLive.jl")` works.
module FishLive

using FishLily
using WaterLily
using Printf

include(joinpath(@__DIR__, "FishViz.jl"))      # own copy of the FishViz module
using .FishViz: LiveViewer, finish!, screenshot, wait_close, record_vorticity, snapshot, update!
const FV = FishViz

export fish_viewer, fish_readouts, fish_arrow, fish_title, record_fish, FV

"Plot origin (grid cells) so that x/L = y/L = 0 is the tail root (L = L_BODY)."
plot_origin(fs) = (fs.origin[1], fs.origin[2])   # FishViz maps sample i (cell centre i - 0.5) to (i - 0.5 - origin)/L

"""
    ThrustMean(f)

Running time-weighted mean of the thrust over the last tail period 1/f (s), or over the
last 0.5 s without a frequency. The instantaneous thrust oscillates strongly (added mass,
valve switches), the one-cycle mean is what matters.
"""
mutable struct ThrustMean
    window::Float64
    t::Vector{Float64}
    y::Vector{Float64}
end
ThrustMean(f) = ThrustMean(f === nothing ? 0.5 : 1 / f, Float64[], Float64[])
function push_mean!(m::ThrustMean, t, y)
    (isfinite(t) && isfinite(y)) || return NaN
    if !isempty(m.t) && t <= m.t[end]
        m.t[end] = t; m.y[end] = y
    else
        push!(m.t, t); push!(m.y, y)
    end
    while length(m.t) > 2 && m.t[2] < t - m.window
        popfirst!(m.t); popfirst!(m.y)
    end
    length(m.t) < 2 && return NaN
    span = m.t[end] - m.t[1]
    span < 0.9 * m.window && return NaN          # not a full window yet
    s = 0.0
    for i in 1:length(m.t)-1
        s += 0.5 * (m.y[i] + m.y[i+1]) * (m.t[i+1] - m.t[i])
    end
    s / span
end

"""
    fish_readouts(fs, row; f=nothing, tm=nothing) -> NamedTuple for FishViz

`row` is a log row of `run_fish!` (t, s, V_p [m³], θ [rad], Fx, Fy, thrust [N/m], ...).
"""
function fish_readouts(fs, row; f=nothing, mean_thrust=NaN)
    g(k) = (v = get(row, k, nothing); v isa Real && isfinite(v) ? Float64(v) : nothing)
    t = something(g(:t), t_phys(fs))
    s = g(:s)
    Vp = g(:V_p); θ = g(:θ)
    (t        = (t, "s"),
     f        = f === nothing ? nothing : (Float64(f), "Hz"),
     U_in     = (fs.U_in, "m/s"),
     _1       = "",
     valve_s  = s === nothing ? nothing : (s > 0 ? "+1" : "-1"),
     V_p      = Vp === nothing ? nothing : (1e6Vp, "ml"),
     θ        = θ === nothing ? nothing : (rad2deg(θ), "deg"),
     _2       = "",
     Fx       = g(:Fx) === nothing ? nothing : (g(:Fx), "N/m"),
     Fy       = g(:Fy) === nothing ? nothing : (g(:Fy), "N/m"),
     thrust   = g(:thrust) === nothing ? nothing : (g(:thrust), "N/m"),
     thrust_avg = isfinite(mean_thrust) ? (mean_thrust, "N/m") : "(1 period) …",
     _3       = "",
     n        = (round(Int, fs.units.n), "cells/L"))
end

"Force arrow: total force on the fish (Fx, Fy) [N/m], drawn at the body centroid."
fish_arrow(row) = (F=(Float64(get(row, :Fx, 0.0)), Float64(get(row, :Fy, 0.0))),)

function fish_title(fs; f=nothing, case=fs.name)
    @sprintf("%s:  f = %s,  U_in = %.2f m/s,  n = %d,  Re_sim = %.0f", case,
             f === nothing ? "–" : @sprintf("%.2f Hz", f), fs.U_in, round(Int, fs.units.n), fs.units.Re)
end

# still water: zoom on the fish (the flow stays near it); with inflow: whole domain (wake)
default_xlims(fs) = fs.U_in > 0 ? nothing : (-0.7, 2.3)
default_ylims(fs) = fs.U_in > 0 ? nothing : (-1.0, 1.0)

const CURRENT = Ref{Any}(nothing)     # the open viewer (closed when a new one is opened)

"""
    fish_viewer(fs; t_end, f=nothing, title=nothing, case=fs.name, max_fps=5, kwargs...)
        -> (viewer, frame(sim,row)->Bool, finish(status))

Open the live window for `fs` (FishViz.LiveViewer on the primary monitor, or
FISHVIZ_MONITOR). `frame` is meant as `on_frame` of `run_fish!` (it is throttled to
`max_fps`, so it may be called every step); `finish(status)` draws the final frame
and, with FISH_LIVE_KEEP=1, waits until the window is closed. `kwargs` go to
`LiveViewer`/`FlowPanel` (`xlims`, `ylims`, `clims`, `max_px`, `size`, ...).
"""
function fish_viewer(fs; t_end, f=nothing, title=nothing, case=fs.name, max_fps=5, max_px=768,
                     window_title="FishLily live – $(case)", clims=(-10, 10),
                     xlims=default_xlims(fs), ylims=default_ylims(fs), kwargs...)
    CURRENT[] === nothing || try close(CURRENT[]) catch end
    last = Ref{Any}((;))
    tm = ThrustMean(f)
    mt = Ref(NaN)
    readouts = sim -> fish_readouts(fs, last[]; f, mean_thrust=mt[])
    arrow = sim -> fish_arrow(last[])
    v = LiveViewer(fs.sim; t_end=Float64(t_end), t0=0.0, time_of=_ -> t_phys(fs), time_unit="s",
                   title=something(title, fish_title(fs; f, case)), arrow, arrow_unit="N/m",
                   origin=plot_origin(fs), max_fps, max_px, window_title, clims, xlims, ylims, kwargs...)
    CURRENT[] = v
    frame = (sim, row) -> begin
        if row isa NamedTuple && haskey(row, :thrust)
            last[] = row
            mt[] = push_mean!(tm, Float64(row.t), Float64(row.thrust))
        end
        update!(v, sim, readouts)
    end
    finish = status -> begin
        finish!(v, fs.sim, readouts; status)
        lowercase(get(ENV, "FISH_LIVE_KEEP", "0")) in ("1", "true", "yes") && wait_close(v)
        nothing
    end
    v, frame, finish
end

"""
    record_fish(fs, driver; t_start, duration, frame_dt, path, f=nothing, case=fs.name,
                fps=30, kwargs...) -> NamedTuple

Headless MP4 (CairoMakie) of the fish: first runs `run_fish!` (no rendering) up to
`t_start` [s] (e.g. past the valve transient), then records `duration` seconds of
physical time with one frame every `frame_dt` s. Readouts and force arrow as in the
live viewer. `kwargs` go to `FishViz.record_vorticity` (`xlims`, `ylims`, `clims`, `crf`, ...).
"""
function record_fish(fs, driver; t_start, duration, frame_dt, path, f=FishLily._driver_freq(driver),
                     case=fs.name, fps=30, title=nothing, progress_case=case, clims=(-10, 10), kwargs...)
    if t_start > t_phys(fs)
        println("[record] simulating the start-up 0 → $(t_start) s (no frames)…")
        run_fish!(fs, t_start; driver, case=progress_case, progress=true, on_frame=(s, r) -> nothing)
    end
    last = Ref{Any}((;))
    tm = ThrustMean(f); mt = Ref(NaN)
    # prime the thrust mean with one cycle before the first frame
    step! = (sim, t_target) -> begin
        df = run_fish!(fs, t_target; driver, case=progress_case, progress=false,
                       on_frame=(s, r) -> nothing)        # (no automatic FISH_LIVE window here)
        for r in eachrow(df)
            mt[] = push_mean!(tm, Float64(r.t), Float64(r.thrust))
        end
        size(df, 1) > 0 && (last[] = NamedTuple(df[end, :]))
    end
    step!(fs.sim, t_phys(fs) + 1e-9)              # one step: fill `last`
    readouts = sim -> fish_readouts(fs, last[]; f, mean_thrust=mt[])
    arrow = sim -> fish_arrow(last[])
    record_vorticity(fs.sim, step!, readouts; duration, frame_dt, fps, path, time_of=_ -> t_phys(fs),
                     time_unit="s", title=something(title, fish_title(fs; f, case)), arrow, arrow_unit="N/m",
                     origin=plot_origin(fs), clims, kwargs...)
end

end # module FishLive
