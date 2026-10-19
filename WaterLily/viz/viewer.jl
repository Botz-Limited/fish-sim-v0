# Live GLMakie viewer (included by FishViz.jl; not a standalone script).
#
# A run loop pushes frames:
#     v = LiveViewer(sim; t_end=5.0, time_of=sim->t_phys(sim), time_unit="s", title="fish")
#     hook = on_frame(v)                      # (sim, readouts) -> Bool
#     while ...; step...; every N steps: hook(sim, readouts); end
#     finish!(v, sim, readouts); wait_close(v)   # optional: keep the window until the user closes it
#
# update! is throttled to `max_fps` (default 5): calls in between only cost a time check, so
# the loop may call it every step. Rendering happens on the calling (main) thread.

"""
    LiveViewer(sim; t_end, t0=time_of(sim), time_of=sim_time, time_unit="", max_fps=5,
               max_px=384, headless=!has_display(), window_title="FishViz live",
               print_every=2.0, kwargs...)

Live window showing vorticity + body + readouts + progress bar
`37.2 %  t=1.86/5.00 s  ETA 2m10s`. `kwargs` go to [`FlowPanel`](@ref) (`clims`, `title`,
`arrow`, `stride`, `origin`, `xlims`, `ylims`, `size`, ...). The field is downsampled to at most
`max_px` samples along the longer side to keep a refresh cheap. Without a display (or if GLMakie
fails to open a window) it runs headless: progress is printed to the terminal every
`print_every` seconds and nothing is drawn.
"""
mutable struct LiveViewer
    panel::Union{FlowPanel,Nothing}
    screen::Any
    headless::Bool
    t0::Float64
    t_end::Float64
    time_of::Any
    time_unit::String
    min_dt::Float64
    print_every::Float64
    wall0::Float64
    last_render::Float64
    last_print::Float64
    frames::Int
    render_time::Float64
    field_time::Float64
    closed_by_user::Bool
end

function LiveViewer(sim; t_end, time_of=sim_time, t0=time_of(sim), time_unit="", max_fps=5, max_px=384,
                    headless=!has_display(), window_title="FishViz live", print_every=2.0,
                    size=(1280, 720), monitor=get(ENV, "FISHVIZ_MONITOR", nothing), kwargs...)
    panel = nothing; screen = nothing
    headless = headless || !GL_LOADED[]
    if !headless
        try
            panel = FlowPanel(sim; max_px, show_progress=true, size, kwargs...)
            # no background renderloop: GLMakie's fps renderloop busy-waits on its timer whenever the
            # sim task yields (measured ~50 ms per frame); we draw synchronously in update! instead
            screen = GLMakie.Screen(; title=window_title, renderloop=manual_renderloop,
                                    focus_on_show=false, visible=false)
            display(screen, panel.fig)
            place_on_monitor!(screen; monitor)
        catch err
            @warn "FishViz: could not open a GLMakie window, running headless (progress in terminal only)" exception = err
            headless = true; panel = nothing; screen = nothing
        end
    else
        @info "FishViz: no display (DISPLAY/WAYLAND_DISPLAY unset) or headless=true, live viewer runs headless: progress in terminal only. Use record_vorticity for a video."
    end
    v = LiveViewer(panel, screen, headless, Float64(t0), Float64(t_end), time_of, time_unit,
                   1 / max_fps, print_every, time(), -Inf, -Inf, 0, 0.0, 0.0, false)
    update!(v, sim, (;); force=true)
    v.frames = 0; v.render_time = v.field_time = 0.0     # timing stats exclude the first (compiling) frame
    v
end

# ---------------------------------------------------------------------------------------------
# window placement (multi-monitor): centre on the primary monitor (or FISHVIZ_MONITOR=<name>)


"Renderloop that does nothing: frames are drawn by `render_now!` from `update!`."
manual_renderloop(screen) = nothing

"Poll window events and draw one frame synchronously (GLMakie internals, tested with GLMakie 0.13)."
function render_now!(screen)
    isopen(screen) || return
    GLMakie.pollevents(screen, Makie.RegularRenderTick)
    isopen(screen) || return                  # user may have closed it in this poll
    GLMakie.poll_updates(screen)
    GLMakie.render_frame(screen)
    GLFW.SwapBuffers(GLMakie.to_native(screen))
    nothing
end

# (not wrapped by GLFW.jl; defined only when GLMakie/GLFW is loaded since ccall types resolve at definition)
GL_LOADED[] && @eval function monitor_workarea(m)
    x = Ref{Cint}(); y = Ref{Cint}(); w = Ref{Cint}(); h = Ref{Cint}()
    ccall((:glfwGetMonitorWorkarea, GLFW.libglfw), Cvoid,
          (GLFW.Monitor, Ref{Cint}, Ref{Cint}, Ref{Cint}, Ref{Cint}), m, x, y, w, h)
    (Int(x[]), Int(y[]), Int(w[]), Int(h[]))
end

"List `(name, workarea=(x,y,w,h), primary)` of the monitors GLFW sees."
function monitors()
    p = GLFW.GetMonitorName(GLFW.GetPrimaryMonitor())
    [(name=GLFW.GetMonitorName(m), workarea=monitor_workarea(m), primary=GLFW.GetMonitorName(m) == p)
     for m in GLFW.GetMonitors()]
end

"""
    pick_monitor(name=nothing)

Monitor named `name` (e.g. "DP-2", from `FISHVIZ_MONITOR`) if given and present, else the
primary monitor reported by the window system, else the first one.
"""
function pick_monitor(name=nothing)
    ms = GLFW.GetMonitors()
    isempty(ms) && return nothing
    if name !== nothing && !isempty(name)
        i = findfirst(m -> GLFW.GetMonitorName(m) == name, ms)
        i === nothing ? @warn("FishViz: monitor $name not found, have $(GLFW.GetMonitorName.(ms)); using primary") :
                        return ms[i]
    end
    p = GLFW.GetPrimaryMonitor()
    p.handle == C_NULL ? first(ms) : p
end

"""
    place_on_monitor!(screen; monitor=ENV["FISHVIZ_MONITOR"] or nothing, fill=0.9)

Shrink the (still hidden) GLMakie window to fit `fill` of the monitor work area if needed,
centre it there, then show it. Returns `(monitor_name, window_pos)` or `nothing`.
"""
function place_on_monitor!(screen; monitor=get(ENV, "FISHVIZ_MONITOR", nothing), fill=0.9)
    win = GLMakie.to_native(screen)
    res = nothing
    try
        m = pick_monitor(monitor)
        if m !== nothing
            wx, wy, ww, wh = monitor_workarea(m)
            w, h = GLFW.GetWindowSize(win)
            k = min(1.0, fill * ww / w, fill * wh / h)
            if k < 1
                w, h = floor(Int, k * w), floor(Int, k * h)
                GLFW.SetWindowSize(win, w, h)
            end
            x, y = wx + (ww - w) ÷ 2, wy + (wh - h) ÷ 2
            GLFW.SetWindowPos(win, x, y)
            res = (GLFW.GetMonitorName(m), (x, y))
        end
    catch err
        @warn "FishViz: window placement failed" exception = err
    end
    GLFW.ShowWindow(win)
    res
end

"Current window position and size (window-system pixels)."
window_geometry(v) = (pos=GLFW.GetWindowPos(GLMakie.to_native(v.screen)), size=GLFW.GetWindowSize(GLMakie.to_native(v.screen)))

Base.isopen(v::LiveViewer) = v.headless || (v.screen !== nothing && isopen(v.screen))

function progress_of(v::LiveViewer, sim)
    t = Float64(v.time_of(sim))
    frac = clamp((t - v.t0) / (v.t_end - v.t0), 0.0, 1.0)
    el = time() - v.wall0
    eta = frac > 1e-6 ? el / frac * (1 - frac) : Inf
    t, frac, eta
end

"""
    update!(v::LiveViewer, sim, readouts=(;); force=false, status="running") -> Bool

Push the current state. Returns `true` if a frame was drawn (at most `max_fps` per second
unless `force`). `readouts` is a NamedTuple or a function `sim -> NamedTuple` (a function is
only evaluated when a frame is actually drawn). Must be called from the main thread. If the
user closed the window it does nothing (check `isopen(v)` to stop the run if you want).
"""
function update!(v::LiveViewer, sim, readouts=(;); force::Bool=false, status::AbstractString="running")
    now = time()
    if v.headless
        (force || now - v.last_print ≥ v.print_every) || return false
        v.last_print = now
        t, frac, eta = progress_of(v, sim)
        print(stderr, "\r[live] ", progress_string(100frac, t, v.t_end, eta, v.time_unit), "  ", status, "   ")
        status != "running" && println(stderr)
        return true
    end
    (force || now - v.last_render ≥ v.min_dt) || return false
    if !isopen(v.screen)
        v.closed_by_user || @info "FishViz: viewer window closed, simulation continues"
        v.closed_by_user = true
        return false
    end
    v.last_render = now
    t, frac, eta = progress_of(v, sim)
    P = v.panel
    refresh!(P, sim, readouts)
    v.field_time += time() - now
    P.progress[] = frac
    P.progress_text[] = progress_string(100frac, t, v.t_end, eta, v.time_unit)
    P.status[] = status == "running" ? @sprintf("running   wall %s", fmt_dur(now - v.wall0)) :
                 @sprintf("%s   wall %s", status, fmt_dur(now - v.wall0))
    render_now!(v.screen)
    v.frames += 1
    v.render_time += time() - now
    true
end

"`on_frame(v)` -> closure `(sim, readouts) -> update!(v, sim, readouts)` for the core run loop."
on_frame(v::LiveViewer) = (sim, readouts=(;)) -> update!(v, sim, readouts)

"Final forced refresh with a status text (e.g. \"done\", \"failed: …\")."
finish!(v::LiveViewer, sim, readouts=(;); status="done") = update!(v, sim, readouts; force=true, status)

"Save what the window shows (GLMakie colorbuffer) or, headless, nothing."
function screenshot(v::LiveViewer, path)
    v.headless && (@warn "headless viewer: no screenshot"; return nothing)
    mkpath(dirname(abspath(path)))
    save(path, Makie.colorbuffer(v.screen))
    path
end

"Block until the user closes the window (no-op headless)."
function wait_close(v::LiveViewer)
    v.headless && return
    while isopen(v.screen)
        render_now!(v.screen)
        sleep(0.05)
    end
end

Base.close(v::LiveViewer) = (v.screen !== nothing && isopen(v.screen) && close(v.screen); nothing)

"Mean wall time per drawn `update!` call [ms]: (total, of which field extraction + readouts)."
render_ms(v::LiveViewer) = v.frames == 0 ? (0.0, 0.0) : (1e3 * v.render_time / v.frames, 1e3 * v.field_time / v.frames)

"""
    run_live(sim, step!, readouts; t_end, frame_dt, time_of=sim_time, kwargs...) -> LiveViewer

Standalone driver: opens a [`LiveViewer`](@ref), then repeatedly `step!(sim, t + frame_dt)` and
`update!`, until `time_of(sim) ≥ t_end` (or the window is closed when `stop_on_close=true`).
"""
function run_live(sim, step!, readouts; t_end, frame_dt, time_of=sim_time, stop_on_close=true,
                  keep_open=false, kwargs...)
    v = LiveViewer(sim; t_end, time_of, kwargs...)
    while time_of(sim) < t_end - 1e-9
        step!(sim, min(time_of(sim) + frame_dt, t_end))
        update!(v, sim, readouts)
        stop_on_close && !isopen(v) && (@info "window closed: stopping"; break)
    end
    finish!(v, sim, readouts)
    keep_open && wait_close(v)
    v
end
run_live(sim, readouts; kwargs...) = run_live(sim, (s, t) -> sim_step!(s, t; remeasure=true), readouts; kwargs...)
