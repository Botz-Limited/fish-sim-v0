# Live GLMakie window on a running fish case (vorticity, fish, progress bar with % and ETA,
# readouts t, f, valve s, V_p, θ, Fx, Fy, thrust, force arrow). The terminal shows the
# usual progress line. Window: primary monitor (DP-2 here), or FISHVIZ_MONITOR=<name>.
#
#   julia --project=. -t 2 scripts/live.jl --case tethered --f 2 --U 0 --n 128 --t 6
#   julia --project=. -t 2 scripts/live.jl --case tethered --f 2 --U 0.2 --t 4
#   julia --project=. -t 2 scripts/live.jl --case rigid --U 0.2 --t 4
#   julia --project=. -t 2 scripts/live.jl --case sine --f 2 --amp 20 --t 4
#
# Options (defaults in brackets):
#   --case   tethered [default] | rigid | sine     (tethered = valve-driven tail, fixed body;
#            sine = prescribed θ = amp·sin(2πft) instead of the valve)
#   --f      tail frequency [2.0] Hz (1.5–2.5 for the valve)
#   --U      inflow [0.0] m/s (tethered/sine), [0.2] for rigid
#   --n      cells per body length [128]
#   --t      physical end time [6.0] s
#   --Re     Re_sim [5000]
#   --amp    sine amplitude [20] deg
#   --keep   keep the window open after the run until it is closed
#   --fps    max. window refresh rate [5]
#   --screenshot PATH   save a screenshot of the window at the end
#
# Works from the main environment (--project=.): viz/ is stacked onto LOAD_PATH on demand.
# Also works with --project=viz.
using FishLily
using Printf

function parse_args(args)
    o = Dict{String,Any}("case" => "tethered", "f" => 2.0, "U" => nothing, "n" => 128, "t" => 6.0,
                         "Re" => RE_SIM_DEFAULT, "amp" => 20.0, "keep" => false, "fps" => 5.0,
                         "screenshot" => nothing)
    i = 1
    while i <= length(args)
        a = args[i]
        startswith(a, "--") || error("unexpected argument $a")
        k = a[3:end]
        if k == "keep"
            o[k] = true; i += 1; continue
        end
        i < length(args) || error("missing value for $a")
        v = args[i+1]
        o[k] = k in ("case", "screenshot") ? v : k == "n" ? parse(Int, v) : parse(Float64, v)
        i += 2
    end
    o
end

function main(args=ARGS)
    o = parse_args(args)
    case = o["case"]
    f = Float64(o["f"])
    U = o["U"] === nothing ? (case == "rigid" ? U_REF : 0.0) : Float64(o["U"])
    n = o["n"]; t_end = Float64(o["t"])
    driver = case == "tethered" ? ValveDriver(f) :
             case == "rigid"    ? RigidDriver() :
             case == "sine"     ? ThetaDriver(t -> deg2rad(o["amp"]) * min(t * f, 1.0) * sin(2π * f * t)) :
             error("unknown --case $case (tethered | rigid | sine)")
    name = @sprintf("live_%s_f%g_U%g_n%d", case, f, U, n)
    fs = make_fish_sim(; n, U_in=U, Re=o["Re"], name)
    println("case $case: f = $f Hz, U_in = $U m/s, n = $n, grid = $(size(fs.sim.flow.p) .- 2), t_end = $t_end s, threads = $(Threads.nthreads())")
    hook = maybe_live_hook(fs, t_end; driver, force=true, f=case == "rigid" ? nothing : f,
                           case, max_fps=o["fps"])
    if hook === nothing || hook.viewer.headless
        @warn "no live window (no display?) – running with terminal progress only"
    else
        geo = Base.invokelatest(FishLily._livefun(:window_geometry; viz=true), hook.viewer)
        println("live window at $(geo.pos), size $(geo.size) (FISHVIZ_MONITOR=$(get(ENV, "FISHVIZ_MONITOR", "<primary>")))")
    end
    status = "done"
    try
        df = run_fish!(fs, t_end; driver, case=name, on_frame=hook, frame_every=1)
        if nrow_(df) > 0
            tf = max(t_end - 2 / f, t_end / 2)
            @printf("mean thrust over t ≥ %.2f s: %.4f N/m   (mean Fy %.4f N/m)\n", tf,
                    cycle_mean(df, :thrust; t_from=tf), cycle_mean(df, :Fy; t_from=tf))
        end
    catch err
        status = err isa InterruptException ? "interrupted" : "failed"
        err isa InterruptException || rethrow(err)
    finally
        if hook !== nothing
            live_finish!(hook, status)
            o["screenshot"] === nothing || live_screenshot(hook, o["screenshot"])
            if o["keep"]
                println("window kept open – close it to exit")
                live_wait_close(hook)
            end
        end
    end
end
nrow_(df) = size(df, 1)

main()
