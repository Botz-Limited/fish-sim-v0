# Headless MP4 of the fish (CairoMakie, no display needed): vorticity, fish, readouts
# (t, f, U_in, valve s, V_p, θ, Fx, Fy, thrust, one-period mean thrust) and force arrow.
# The start-up (valve transient, NOTES.md item 8) is simulated without frames first.
#
#   julia --project=. -t 2 scripts/animate.jl                       # tethered, f=2 Hz, still water
#   julia --project=. -t 2 scripts/animate.jl --U 0.2               # same with inflow 0.2 m/s
#   julia --project=. -t 2 scripts/animate.jl --f 2.5 --n 128 --t0 2 --cycles 3 --out results/x.mp4
#
# Options [defaults]: --f [2.0] Hz, --U [0.0] m/s, --n [128], --t0 [2.0] s (start of the
# recording, after the valve transient), --cycles [3] tail periods recorded, --fpc [100]
# frames per tail period, --fps [30], --crf [23] (H.264 quality, higher = smaller file),
# --out [results/fish_tethered_f<f>[_U<U>].mp4].
# 1280×720. Video length = cycles·fpc/fps (3·100/30 = 10 s, i.e. 1.5 s of motion at 2 Hz,
# slowed down ≈ 6.7×).
#
# Works from the main environment (viz/ is stacked onto LOAD_PATH) or with --project=viz.
using FishLily
using Printf

function parse_args(args)
    o = Dict{String,Any}("f" => 2.0, "U" => 0.0, "n" => 128, "t0" => 2.0, "cycles" => 3.0,
                         "fpc" => 100, "fps" => 30, "crf" => 23, "out" => nothing)
    i = 1
    while i <= length(args)
        k = args[i][3:end]
        haskey(o, k) || error("unknown option $(args[i])")
        v = args[i+1]
        o[k] = k == "out" ? v : k in ("n", "fpc", "fps", "crf") ? parse(Int, v) : parse(Float64, v)
        i += 2
    end
    o
end

function main(args=ARGS)
    o = parse_args(args)
    f, U, n = o["f"], o["U"], o["n"]
    out = something(o["out"], joinpath(RESULTS_DIR, U > 0 ? @sprintf("fish_tethered_f%g_U%g.mp4", f, U) :
                                                          @sprintf("fish_tethered_f%g.mp4", f)))
    case = @sprintf("animate_tethered_f%g_U%g_n%d", f, U, n)
    fs = make_fish_sim(; n, U_in=U, name=case)
    driver = ValveDriver(f)
    println("animate: f = $f Hz, U_in = $U m/s, n = $n, grid = $(size(fs.sim.flow.p) .- 2), threads = $(Threads.nthreads())")
    m = FishLily._load_live()
    rec = Base.invokelatest(getglobal, m, :record_fish)
    xl, yl = U > 0 ? ((-0.6, 4.0), (-1.0, 1.0)) : ((-0.7, 2.3), (-0.9, 0.9))
    st = Base.invokelatest(rec, fs, driver; t_start=o["t0"], duration=o["cycles"] / f,
                           frame_dt=1 / (f * o["fpc"]), path=out, fps=o["fps"], crf=o["crf"],
                           case="tethered", xlims=xl, ylims=yl, size=(1280, 720))
    @printf("wrote %s (%.2f MB, %d frames, wall %.0f s)\n", st.path, st.bytes / 2^20, st.frames, st.wall)
    st.bytes > 10 * 2^20 && @warn "video larger than 10 MB – rerun with a higher --crf"
end

main()
