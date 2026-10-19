# Optional live viewer hook (GLMakie window), loaded lazily from viz/.
#
# FishLily itself does not depend on Makie. When the environment variable
# FISH_LIVE=1 is set, `run_fish!` (and `maybe_live_hook`) load
# `viz/FishLive.jl` on demand: the viz environment (which has GLMakie and
# `FishLily` dev'ed in) is appended to LOAD_PATH, so this also works from a
# script started with `--project=.` (all shared packages have identical
# versions in both manifests). Without FISH_LIVE nothing is loaded.
#
# Environment variables:
#   FISH_LIVE=1           open the live window for every run_fish! call
#   FISH_LIVE_KEEP=1      keep the window open after the run until it is closed
#   FISHVIZ_MONITOR=name  monitor (default: primary, here DP-2)

"Directory of the visualisation environment (WaterLily/viz)."
const VIZ_DIR = normpath(joinpath(@__DIR__, "..", "viz"))

_envflag(k) = lowercase(get(ENV, k, "0")) in ("1", "true", "yes", "on")
"True if the live viewer was requested with the environment variable FISH_LIVE=1."
live_requested() = _envflag("FISH_LIVE")

const _LIVE_MOD = Ref{Any}(nothing)

function _load_live()
    _LIVE_MOD[] === nothing || return _LIVE_MOD[]
    VIZ_DIR in LOAD_PATH || push!(LOAD_PATH, VIZ_DIR)
    _LIVE_MOD[] = Base.include(Main, joinpath(VIZ_DIR, "FishLive.jl"))
end

"""
    LiveHook

Callable `(sim, row) -> Bool` returned by [`maybe_live_hook`](@ref); pass it as
`on_frame` to `run_fish!` (or call it from your own loop) and end with
[`live_finish!`](@ref). `hook.viewer` is the `FishViz.LiveViewer`.
"""
struct LiveHook
    viewer::Any
    frame::Any       # (sim, row) -> Bool
    finish::Any      # status -> nothing
end
(h::LiveHook)(sim, row) = Base.invokelatest(h.frame, sim, row)

"""
    live_finish!(hook, status="done")

Final frame with a status text; with FISH_LIVE_KEEP=1 waits until the window is
closed. No-op for anything that is not a `LiveHook` (e.g. `nothing`).
"""
live_finish!(h::LiveHook, status="done") = (Base.invokelatest(h.finish, String(status)); nothing)
live_finish!(::Any, status="done") = nothing

"""
    maybe_live_hook(fs, t_end; driver=nothing, f=<from a ValveDriver>, force=false, kwargs...)
        -> LiveHook or nothing

If FISH_LIVE=1 (or `force=true`), open the live GLMakie viewer for the fish
simulation `fs` (vorticity, fish, progress bar with % and ETA, readouts t, f,
valve s, V_p, θ, Fx, Fy, thrust, force arrow) and return a hook for the run loop:

    hook = maybe_live_hook(fs, t_end; driver)          # nothing unless FISH_LIVE=1
    ... in the loop, after a step: hook === nothing || hook(fs.sim, row)
    live_finish!(hook)

`run_fish!` does this by itself when it is called without `on_frame`, so stage
scripts that use `run_fish!` need no change at all. Extra `kwargs` go to
`FishLive.fish_viewer` / `FishViz.LiveViewer` (`title`, `xlims`, `ylims`, `clims`, `max_fps`, ...).
If the viewer cannot be loaded the run continues without it (a warning is printed).
"""
function maybe_live_hook(fs, t_end; driver=nothing, f=_driver_freq(driver), force=false, kwargs...)
    (force || live_requested()) || return nothing
    try
        _load_live()
        v, frame, finish = Base.invokelatest(_livefun(:fish_viewer), fs; t_end=Float64(t_end), f, kwargs...)
        return LiveHook(v, frame, finish)
    catch err
        @warn "FishLily: live viewer could not be opened, continuing without it" exception = (err, catch_backtrace())
        return nothing
    end
end

# a function of the lazily loaded FishLive module (or of FishViz with `viz=true`), looked up
# in the latest world (the module was defined after the caller's world started)
function _livefun(name::Symbol; viz=false)
    m = _load_live()
    viz && (m = Base.invokelatest(getglobal, m, :FV))
    Base.invokelatest(getglobal, m, name)
end

"Save a PNG of the live window only (not the desktop). No-op for `nothing`."
live_screenshot(h::LiveHook, path) = Base.invokelatest(_livefun(:screenshot; viz=true), h.viewer, path)
live_screenshot(::Nothing, path) = nothing

"Block until the user closes the live window. No-op for `nothing`."
live_wait_close(h::LiveHook) = (Base.invokelatest(_livefun(:wait_close; viz=true), h.viewer); nothing)
live_wait_close(::Nothing) = nothing

_driver_freq(::Nothing) = nothing
function _driver_freq(d)
    hasproperty(d, :valve) && hasproperty(d.valve, :f) && return Float64(d.valve.f)
    hasproperty(d, :f) && getproperty(d, :f) isa Real && return Float64(getproperty(d, :f))
    nothing
end
