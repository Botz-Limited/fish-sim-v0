"""
    FishViz

Visualisation layer for 2D WaterLily simulations (fish demo), independent of the fish model.

- [`record_vorticity`](@ref): headless MP4 (CairoMakie) of the vorticity field, the solid body,
  a text panel of live readouts and an optional force arrow; prints progress to the terminal.
- [`snapshot`](@ref): one PNG of the same view.
- [`LiveViewer`](@ref) + [`update!`](@ref) / [`on_frame`](@ref): live GLMakie window that a run
  loop pushes frames into (throttled to `max_fps`), with a progress bar and ETA. Without a
  display it falls back to a progress line in the terminal. [`run_live`](@ref) drives a sim itself.

Generic inputs:
- `sim`        any 2D `WaterLily.Simulation` (CPU or GPU arrays);
- `readouts`   `sim -> NamedTuple` (or a ready NamedTuple). Values may be numbers, strings,
               `(value, "unit")` tuples or `nothing` (line skipped). Keys are used as labels,
               e.g. `(t=(1.23,"s"), f=(2.0,"Hz"), s=+1, V_p=(3.1,"ml"), θ=(12.0,"deg"), Fx=(0.01,"N"))`;
- `arrow`      optional `sim -> (F=(Fx,Fy),)` or `(F=..., at=(x,y))` with `at` in plot units
               (x/L, y/L); default position is the body centroid. See [`pressure_force_arrow`](@ref).
- `time_of`    `sim -> current time` in the units used for `duration`, `frame_dt`, `t_end`
               (default `WaterLily.sim_time`, i.e. convective time tU/L).

Plot coordinates are `x/L`, `y/L` (grid cells divided by `sim.L`, shifted by `origin` cells);
vorticity is shown as ω·L/U (`sim.L`, `sim.U`).
"""
module FishViz

using WaterLily
using WaterLily: inside, @inside, curl, sim_time, sdf, measure_sdf!
using Makie
using Printf
import CairoMakie
import WaterLily: update!

export record_vorticity, snapshot, LiveViewer, update!, on_frame, finish!, screenshot,
       wait_close, run_live, pressure_force_arrow, has_display, format_readouts

const RGBAf = Makie.RGBAf

# ---------------------------------------------------------------------------------------------
# formatting helpers

fmtnum(x::Integer) = string(x)
fmtnum(x::Bool) = string(x)
function fmtnum(x::Real)
    isfinite(x) || return string(x)
    a = abs(x)
    (a != 0 && (a < 1e-3 || a >= 1e5)) ? @sprintf("%+.3e", x) : @sprintf("%+.4f", x)[1:min(end, 9)]
end
fmtnum(x) = string(x)
fmtval(v::Tuple{<:Any,<:AbstractString}) = fmtnum(v[1]) * " " * v[2]
fmtval(v::AbstractString) = v
fmtval(v) = fmtnum(v)

"""
    format_readouts(nt::NamedTuple) -> String

One line per entry, `label  value [unit]`; `nothing` values are skipped, `""` gives a blank
line (keys like `_1 = ""` can be used as spacers).
"""
function format_readouts(nt::NamedTuple)
    isempty(nt) && return ""
    w = maximum(length ∘ string, keys(nt))
    lines = String[]
    for (k, v) in pairs(nt)
        v === nothing && continue
        if v == ""
            push!(lines, "")
        else
            push!(lines, rpad(string(k), w + 2) * fmtval(v))
        end
    end
    join(lines, "\n")
end

function fmt_dur(s::Real)
    isfinite(s) || return "--"
    s = round(Int, max(s, 0))
    s < 60 && return "$(s)s"
    s < 3600 && return @sprintf("%dm%02ds", s ÷ 60, s % 60)
    @sprintf("%dh%02dm", s ÷ 3600, (s % 3600) ÷ 60)
end

progress_string(pct, t, t_end, eta, unit) =
    @sprintf("%5.1f %%  t=%.2f/%.2f%s  ETA %s", pct, t, t_end, isempty(unit) ? "" : " " * unit, fmt_dur(eta))

const MONO_CANDIDATES = ("DejaVu Sans Mono", "Noto Sans Mono", "Liberation Mono", "Ubuntu Mono", "Menlo", "Consolas")
const _mono = Ref{Any}(nothing)
function monofont()
    _mono[] === nothing || return _mono[]
    for name in MONO_CANDIDATES
        f = Makie.FreeTypeAbstraction.findfont(name)
        f === nothing || return (_mono[] = f)
    end
    _mono[] = :regular
end

"True if a graphical display seems available (X11/Wayland on Linux; assumed on macOS/Windows)."
has_display() = !Sys.islinux() || haskey(ENV, "DISPLAY") || haskey(ENV, "WAYLAND_DISPLAY")

# GLMakie (GLFW) fails in __init__ without a display, so it is loaded only when one exists.
const GL_LOADED = Ref(false)
if has_display()
    try
        @eval import GLMakie
        @eval const GLFW = GLMakie.GLFW
        GL_LOADED[] = true
    catch err
        @warn "FishViz: GLMakie could not be loaded; live viewer will run headless" exception = err
    end
end

# ---------------------------------------------------------------------------------------------
# field extraction (device -> downsampled CPU)

host(x) = Array(x)
maybe_value(x) = x   # Dual numbers are not expected here (ForwardDiff sims are not visualised)

"""Buffers + geometry of the (downsampled) plotted field."""
struct FieldGrid{A}
    ωdev::A                 # device scratch array, same size as sim.flow.p (we never touch sim.flow.σ)
    stride::Int
    ii::StepRange{Int,Int}  # sampled indices into inside(...) array
    jj::StepRange{Int,Int}
    xs::Vector{Float32}     # plot coordinates of the samples
    ys::Vector{Float32}
end

function FieldGrid(sim; stride=:auto, max_px=1024, origin=(0, 0))
    ndims(sim.flow.p) == 2 || error("FishViz supports 2D simulations only (got $(ndims(sim.flow.p))D)")
    n = size(sim.flow.p) .- 2
    s = stride === :auto ? max(1, cld(maximum(n), max_px)) : Int(stride)
    ii, jj = 1:s:n[1], 1:s:n[2]
    L = Float32(sim.L)
    xs = Float32[(i - 0.5f0 - origin[1]) / L for i in ii]
    ys = Float32[(j - 0.5f0 - origin[2]) / L for j in jj]
    FieldGrid(similar(sim.flow.p), s, ii, jj, xs, ys)
end

"Vorticity ω·L/U on the sampled grid (Float32 matrix)."
function vorticity!(out::Matrix{Float32}, g::FieldGrid, sim)
    a = g.ωdev
    u = sim.flow.u
    @inside a[I] = curl(3, I, u)
    c = host(@view a[inside(a)])
    k = Float32(sim.L / sim.U)
    @inbounds for (q, j) in enumerate(g.jj), (p, i) in enumerate(g.ii)
        out[p, q] = k * c[i, j]
    end
    out
end

"Body signed distance (in plot units) on the sampled grid, evaluated on the CPU at the sample points."
function body_sdf!(out::Matrix{Float32}, g::FieldGrid, sim)
    body = sim.body
    t = WaterLily.time(sim)
    L = Float32(sim.L)
    T = eltype(sim.flow.p)
    Threads.@threads for q in eachindex(g.jj)
        j = g.jj[q]
        @inbounds for (p, i) in enumerate(g.ii)
            x = WaterLily.SVector{2,T}(i - 0.5, j - 0.5)
            out[p, q] = Float32(sdf(body, x, t)) / L
        end
    end
    out
end

has_body(sim) = !(sim.body isa WaterLily.NoBody)

function centroid(sd::Matrix{Float32}, g::FieldGrid)
    sx = sy = 0.0; n = 0
    @inbounds for q in axes(sd, 2), p in axes(sd, 1)
        if sd[p, q] < 0
            sx += g.xs[p]; sy += g.ys[q]; n += 1
        end
    end
    n == 0 ? (sum(extrema(g.xs)) / 2, sum(extrema(g.ys)) / 2) : (sx / n, sy / n)
end

"""
    pressure_force_arrow(sim) -> (F = (Fx, Fy),)

Pressure force on the body from `WaterLily.pressure_force` (grid units, ρ=1), drawn at the body
centroid. Convenience default for the `arrow` keyword; the fish model should pass its own
(e.g. physical F_x, F_y).
"""
pressure_force_arrow(sim) = (F = Tuple(Float64.(Array(WaterLily.pressure_force(sim)))[1:2]),)

# ---------------------------------------------------------------------------------------------
# the shared figure: flow axis + readout panel (+ optional progress bar)

mutable struct FlowPanel
    fig::Figure
    ax::Axis
    grid::FieldGrid
    ω::Observable{Matrix{Float32}}
    sd::Observable{Matrix{Float32}}
    text::Observable{String}
    status::Observable{String}
    progress::Observable{Float64}
    progress_text::Observable{String}
    apos::Observable{Vector{Point2f}}
    adir::Observable{Vector{Vec2f}}
    arrow_label::Observable{String}
    arrow::Any
    arrow_scale::Any
    arrow_len::Float64
    arrow_window::Int
    arrow_unit::String
    Fmax::Float64
    Fhist::Vector{Float64}
    show_body::Bool
end

"""
    FlowPanel(sim; kwargs...)

Build the figure. Keywords: `size=(1280,720)`, `clims=(-10,10)` (ω·L/U), `colormap`, `stride`,
`max_px`, `origin=(0,0)` (grid cells mapped to x=y=0), `xlims`, `ylims` (plot units, crop),
`title`, `body_color`, `arrow`, `arrow_scale=:auto` (plot units per force unit, or `:auto` =
90th percentile of |F| over the last `arrow_window` frames ↦ `arrow_len`, capped at 2·`arrow_len`), `arrow_len=0.6`, `arrow_color`, `arrow_unit=""`,
`show_progress=false`.
"""
function FlowPanel(sim; size=(1280, 720), clims=(-10, 10), colormap=:balance, stride=:auto, max_px=1024,
                   origin=(0, 0), xlims=nothing, ylims=nothing, title="",
                   body_color=RGBAf(0.25, 0.25, 0.28, 1), arrow=nothing, arrow_scale=:auto, arrow_len=0.6,
                   arrow_color=:darkorange, arrow_unit="", arrow_window=100, show_progress=false, fontsize=15)
    g = FieldGrid(sim; stride, max_px, origin)
    nx, ny = length(g.xs), length(g.ys)
    ω = Observable(vorticity!(zeros(Float32, nx, ny), g, sim))
    show_body = has_body(sim)
    sd = Observable(show_body ? body_sdf!(zeros(Float32, nx, ny), g, sim) : ones(Float32, nx, ny))

    fig = Figure(; size, fontsize, backgroundcolor=:white, figure_padding=12)
    ax = Axis(fig[1, 1]; aspect=DataAspect(), title, titlealign=:left, xlabel="x / L", ylabel="y / L",
              titlesize=fontsize + 3)
    hm = heatmap!(ax, g.xs, g.ys, ω; colormap, colorrange=clims, interpolate=true,
                  lowclip=Makie.to_colormap(colormap)[1], highclip=Makie.to_colormap(colormap)[end])
    if show_body
        contourf!(ax, g.xs, g.ys, sd; levels=[0f0], colormap=[body_color], extendlow=:auto)
        contour!(ax, g.xs, g.ys, sd; levels=[0f0], color=:black, linewidth=1)
    end
    xl = something(xlims, (g.xs[1], g.xs[end])); yl = something(ylims, (g.ys[1], g.ys[end]))
    limits!(ax, xl..., yl...)

    apos = Observable([Point2f(0, 0)]); adir = Observable([Vec2f(0, 0)])
    arrow_label = Observable("")
    if arrow !== nothing
        arrows2d!(ax, apos, adir; color=arrow_color, shaftwidth=4, tipwidth=14, tiplength=14)
        text!(ax, 0.01, 0.02; text=arrow_label, space=:relative, color=arrow_color, fontsize=fontsize - 2,
              align=(:left, :bottom))
    end

    # side panel: one hidden axis with text! (no Labels -> changing text never triggers a relayout)
    side = GridLayout(fig[1, 2]; tellheight=false, valign=:center)
    font = monofont()
    tax = Axis(side[1, 1]; height=round(Int, 0.66 * size[2]), limits=(0, 1, 0, 1), backgroundcolor=:transparent)
    hidedecorations!(tax); hidespines!(tax)
    status = Observable("")
    text!(tax, 0.0, 1.0; text=status, font, fontsize, align=(:left, :top), color=:gray30)
    ybox = show_progress ? 0.2 : 0.0
    poly!(tax, Rect2f(0, ybox, 1, 0.93 - ybox); color=RGBAf(0.96, 0.95, 0.93, 1), strokecolor=:gray70, strokewidth=1)
    text = Observable("")
    text!(tax, 0.04, 0.91; text, font, fontsize, align=(:left, :top), color=:black)
    progress = Observable(0.0); progress_text = Observable("")
    if show_progress
        poly!(tax, Rect2f(0, 0.09, 1, 0.06); color=:gray88, strokecolor=:gray60, strokewidth=1)
        poly!(tax, lift(p -> Rect2f(0, 0.09, clamp(p, 0, 1), 0.06), progress); color=RGBAf(0.2, 0.55, 0.3, 1))
        text!(tax, 0.0, 0.0; text=progress_text, font, fontsize, align=(:left, :bottom))
    end
    Colorbar(side[2, 1], hm; vertical=false, flipaxis=false, label="vorticity ω·L/U", height=10,
             labelsize=fontsize - 1, ticklabelsize=fontsize - 2, tellwidth=false)
    colsize!(fig.layout, 2, Fixed(round(Int, 0.27 * size[1])))
    rowgap!(fig.layout, 6)

    FlowPanel(fig, ax, g, ω, sd, text, status, progress, progress_text, apos, adir, arrow_label,
              arrow, arrow_scale, Float64(arrow_len), Int(arrow_window), String(arrow_unit), 0.0, Float64[], show_body)
end

quantile90(v) = (w = sort(v); w[clamp(ceil(Int, 0.9 * length(w)), 1, length(w))])

eval_readouts(r::Function, sim) = r(sim)
eval_readouts(r::NamedTuple, sim) = r
eval_readouts(::Nothing, sim) = (;)

"Recompute fields from `sim` and push them + readouts into the observables."
function refresh!(P::FlowPanel, sim, readouts)
    # fresh arrays: GLMakie skips texture uploads when an observable is notified with the same array
    P.ω[] = vorticity!(similar(P.ω[]), P.grid, sim)
    P.show_body && (P.sd[] = body_sdf!(similar(P.sd[]), P.grid, sim))
    P.text[] = format_readouts(eval_readouts(readouts, sim))
    if P.arrow !== nothing
        a = P.arrow(sim)
        F = Float64.(a.F)
        at = haskey(a, :at) ? a.at : (P.show_body ? centroid(P.sd[], P.grid) : (0.0, 0.0))
        nF = hypot(F...)
        if P.arrow_scale === :auto
            # 90th percentile of the last `arrow_window` frames: start-up spikes do not shrink the arrow
            push!(P.Fhist, nF); length(P.Fhist) > P.arrow_window && popfirst!(P.Fhist)
            P.Fmax = quantile90(P.Fhist)
            k = P.Fmax > 0 ? min(P.arrow_len / P.Fmax, 2 * P.arrow_len / max(nF, eps())) : 0.0
            P.arrow_label[] = @sprintf("arrow: force%s, %.2f L ≙ %.3g%s (auto scale)", "", P.arrow_len, P.Fmax,
                                       isempty(P.arrow_unit) ? "" : " " * P.arrow_unit)
        else
            k = Float64(P.arrow_scale)
            P.arrow_label[] = @sprintf("arrow: force, 1 L ≙ %.3g%s", 1 / k, isempty(P.arrow_unit) ? "" : " " * P.arrow_unit)
        end
        P.apos[] = [Point2f(at...)]
        P.adir[] = [Vec2f(k .* F...)]
    end
    P
end

# ---------------------------------------------------------------------------------------------
# headless recording

"""
    record_vorticity(sim, step!, readouts; duration, frame_dt, fps=30, path="viz/out/vorticity.mp4",
                     clims=(-10,10), time_of=sim_time, time_unit="", arrow=nothing, crf=23,
                     size=(1280,720), px_per_unit=1, progress=true, kwargs...) -> NamedTuple

Advance `sim` by `duration` (in `time_of` units) in `frame_dt` increments, calling
`step!(sim, t_target)` before each frame (it must advance the sim until `time_of(sim) ≥ t_target`;
default for `time_of = sim_time` is `(s,t) -> sim_step!(s, t; remeasure=true)`), and write one
MP4 frame each time with CairoMakie (no display needed). Video length = duration/frame_dt/fps s.
Prints `xx.x %  frame k/N  ... ETA` to stderr. Extra `kwargs` go to [`FlowPanel`](@ref)
(`title`, `stride`, `origin`, `xlims`, `ylims`, `arrow_scale`, `arrow_unit`, `colormap`, ...).
Returns `(path, frames, wall_sim, wall_render, ms_per_frame_render, bytes)`.
"""
function record_vorticity(sim, step!, readouts; duration, frame_dt, fps=30, path="viz/out/vorticity.mp4",
                          time_of=sim_time, time_unit="", crf=23, progress=true, px_per_unit=1, kwargs...)
    P = FlowPanel(sim; kwargs...)
    nframes = max(1, round(Int, duration / frame_dt))
    t0 = time_of(sim)
    mkpath(dirname(abspath(path)))
    wsim = 0.0; wren = 0.0; wall0 = time()
    tlast = time()
    Makie.record(P.fig, path, 1:nframes; framerate=fps, compression=crf, backend=CairoMakie, px_per_unit) do k
        ts = time()
        k > 1 && step!(sim, t0 + (k - 1) * frame_dt)
        tr = time(); wsim += tr - ts
        t = time_of(sim)
        P.status[] = @sprintf("t = %.3f %s", t, time_unit)
        refresh!(P, sim, readouts)
        wren += time() - tr   # (frame encoding happens after this block; included in the ETA below)
        if progress && (time() - tlast > 0.5 || k == nframes)
            tlast = time()
            el = time() - wall0
            @printf(stderr, "\r[record] %5.1f %%  frame %d/%d  t=%.2f%s  sim %.0f ms/frame  ETA %s   ",
                    100k / nframes, k, nframes, t, time_unit, 1e3wsim / k, fmt_dur(el / k * (nframes - k)))
            k == nframes && println(stderr)
        end
    end
    wall = time() - wall0
    bytes = filesize(path)
    progress && @printf(stderr, "[record] wrote %s: %d frames, %.1f MB, wall %.1f s (sim %.1f s, render+encode %.1f s = %.0f ms/frame)\n",
                        path, nframes, bytes / 2^20, wall, wsim, wall - wsim, 1e3(wall - wsim) / nframes)
    (; path, frames=nframes, wall, wall_sim=wsim, wall_render=wall - wsim,
       ms_per_frame_render=1e3(wall - wsim) / nframes, bytes)
end

record_vorticity(sim, readouts; kwargs...) =
    record_vorticity(sim, (s, t) -> sim_step!(s, t; remeasure=true), readouts; kwargs...)

"""
    snapshot(sim, path="viz/out/snapshot.png"; readouts=nothing, title="", kwargs...) -> path

PNG of the current state (CairoMakie). `kwargs` as for [`FlowPanel`](@ref).
"""
function snapshot(sim, path="viz/out/snapshot.png"; readouts=nothing, time_unit="", time_of=sim_time,
                  px_per_unit=1, kwargs...)
    P = FlowPanel(sim; kwargs...)
    P.status[] = @sprintf("t = %.3f %s", time_of(sim), time_unit)
    refresh!(P, sim, readouts)
    mkpath(dirname(abspath(path)))
    save(path, P.fig; backend=CairoMakie, px_per_unit)
    path
end

include("viewer.jl")

end # module
