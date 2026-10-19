# Stand-in demo for FishViz: a heaving + pitching ellipse (AutoBody with a sinusoidal map) in
# a uniform stream. Proves record_vorticity / snapshot / LiveViewer before the fish model exists.
#
#   julia -t 4 --project=viz viz/demo_standin.jl            # video + snapshot + live window
#   julia -t 4 --project=viz viz/demo_standin.jl --no-live  # video + snapshot only
#   julia -t 4 --project=viz viz/demo_standin.jl --no-record  # live window only
#
# Outputs: viz/out/standin.mp4, viz/out/standin_snapshot.png, viz/out/viewer_screenshot.png
include(joinpath(@__DIR__, "FishViz.jl"))
using .FishViz, WaterLily, StaticArrays, LinearAlgebra, Printf

const OUT = joinpath(@__DIR__, "out")

"""Ellipse (chord L, thickness 0.15L) heaving h = 0.25L sin(ωt) and pitching θ = 15° sin(ωt+π/2)."""
function foil_sim(; L=48, Re=500, U=1, T_conv=3.0, mem=Array)
    a, b = L / 2, 0.075L
    c0 = SA[1.5L, 1.5L]
    Ω = 2π * U / (T_conv * L)                      # angular frequency in grid time
    heave(t) = 0.25L * sin(Ω * t)
    pitch(t) = deg2rad(15) * sin(Ω * t + π / 2)
    ellipse(x, t) = (norm(SA[x[1] / a, x[2] / b]) - 1) * b   # approximate SDF, exact near the minor axis
    function map(x, t)
        θ = pitch(t); s, c = sincos(θ)
        ξ = x - c0 - SA[0, heave(t)]
        SA[c * ξ[1] + s * ξ[2], -s * ξ[1] + c * ξ[2]]
    end
    sim = Simulation((6L, 3L), (U, 0), L; ν=U * L / Re, body=AutoBody(ellipse, map), T=Float32, mem)
    info = (; L, U, Ω, heave, pitch, f_conv=1 / T_conv)
    sim, info
end

# readout callback: labelled values (convective units here; the fish will use physical units)
function make_readouts(info)
    sim -> begin
        tg = WaterLily.time(sim)
        F = WaterLily.pressure_force(sim)
        q = 0.5 * info.U^2 * info.L
        (t     = (sim_time(sim), "L/U"),
         f     = (info.f_conv, "U/L"),
         h     = (info.heave(tg) / info.L, "L"),
         θ     = (rad2deg(info.pitch(tg)), "deg"),
         _1    = "",
         C_x   = -F[1] / q,          # + = thrust
         C_y   = F[2] / q,
         steps = length(sim.flow.Δt) - 1)
    end
end

function main(; live=true, record=true)
    mkpath(OUT)
    println("threads: ", Threads.nthreads())

    # ---- 1. MP4 (headless, CairoMakie) ---------------------------------------------------
    sim, info = foil_sim()
    record || @goto live
    sim_step!(sim, 2.0; remeasure=true)            # skip the impulsive start
    st = record_vorticity(sim, make_readouts(info); duration=9.0, frame_dt=0.04, fps=30,
                          path=joinpath(OUT, "standin.mp4"), clims=(-8, 8),
                          title="Stand-in: heaving + pitching ellipse, Re = 500 (2D WaterLily)",
                          arrow=pressure_force_arrow, time_unit="L/U")
    @show st

    # ---- 2. PNG snapshot -------------------------------------------------------------------
    t = @elapsed snapshot(sim, joinpath(OUT, "standin_snapshot.png"); readouts=make_readouts(info),
                          clims=(-8, 8), title="Stand-in snapshot", arrow=pressure_force_arrow, time_unit="L/U")
    @printf("snapshot: %.2f s\n", t)

    # ---- 3. live viewer + overhead measurement ---------------------------------------------
    @label live
    t_end = 8.0
    # baseline: same run without viewer (also compiles the loop)
    simA, _ = foil_sim(); sim_step!(simA, 0.5)
    simA, _ = foil_sim()
    wall_base = @elapsed while sim_time(simA) < t_end; sim_step!(simA; remeasure=true); end
    nsteps = length(simA.flow.Δt) - 1
    @printf("baseline: %d steps to t=%.1f in %.2f s (%.1f ms/step)\n", nsteps, t_end, wall_base, 1e3wall_base / nsteps)

    if live && has_display()      # warm-up window: compile the GL draw path so timings are steady-state
        simW, infoW = foil_sim(; L=16)
        tw = time()
        w = LiveViewer(simW; t_end=1.0, arrow=pressure_force_arrow, title="warm-up")
        for _ in 1:3; sim_step!(simW); update!(w, simW, make_readouts(infoW); force=true); end
        close(w)
        @printf("first window (open + compile GL draw path): %.1f s\n", time() - tw)
    end
    simB, infoB = foil_sim()
    v = LiveViewer(simB; t_end, time_unit="L/U", clims=(-8, 8), arrow=pressure_force_arrow,
                   title="Live: heaving + pitching ellipse", headless=!live || !has_display())
    hook = on_frame(v)
    rd = make_readouts(infoB)
    wall_live = @elapsed while sim_time(simB) < t_end
        sim_step!(simB; remeasure=true)
        hook(simB, rd)            # called every step; throttled inside to max_fps
    end
    finish!(v, simB, rd)
    @printf("live:     %d steps in %.2f s -> overhead %+.1f %%  (%d frames drawn, %.1f ms/frame of which fields %.1f ms, %.1f fps)\n",
            length(simB.flow.Δt) - 1, wall_live, 100(wall_live / wall_base - 1), v.frames,
            FishViz.render_ms(v)..., v.frames / wall_live)
    if !v.headless
        screenshot(v, joinpath(OUT, "viewer_screenshot.png"))
        println("window: ", FishViz.window_geometry(v), "  monitors: ", FishViz.monitors())
        println("screenshot: ", joinpath(OUT, "viewer_screenshot.png"))
        close(v)
    end
    nothing
end

main(; live=!("--no-live" in ARGS), record=!("--no-record" in ARGS))
