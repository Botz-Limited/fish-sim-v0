# Stage 8 – the CAD tail (Fish_Tail.step) on the aquarium test stand, 3D (see lib_bench.jl).
#
# Once per checkout (Python with gmsh, numpy, scipy, e.g. the SOFA env `fishsofa`, ~20 s):
#   python cad/step_to_sdf.py
# Modes (first argument), run from WaterLily/:
#   run  : 3D CFD   ROCM_PATH=<rocm> julia --project=gpu -t 1 scripts/stage8_bench.jl run
#                   (CPU: BACKEND=cpu julia --project=. -t 8 scripts/stage8_bench.jl run)
#   plot : figures + summary (FishLily env, Plots)   julia --project=. scripts/stage8_bench.jl plot
# Environment variables (run): N (cells per tail length L_REF = 0.26 m, default 128), T_END [s] (6.0),
#   MOUNT (bench = holder free in sway + yaw, fixed = clamped; default bench), BACKEND (gpu/cpu),
#   CASE (default stage8_bench_n<N>_<MOUNT>), MAX_STEPS (debug), T_AVG (start of averaging, 2.0 s),
#   FRAME_DT [s] (0 = off; > 0 dumps λ2 + body SDF for the video, viz/render3d.jl), FRAME_T0, FRAME_STRIDE (2).
# Outputs: results/<case>_timeseries.csv, _info.txt, _snapshots.jls, progress file,
#   with FRAME_DT > 0 also results/frames/<case>/frame_NNNN.jls; plot: results/stage8_*.png, stage8_summary.csv.

const MODE = length(ARGS) >= 1 ? ARGS[1] : "run"
envf(k, d) = parse(Float64, get(ENV, k, string(d)))
envi(k, d) = parse(Int, get(ENV, k, string(d)))

const N = envi("N", 128)
const T_END = envf("T_END", 6.0)
const MOUNT = lowercase(get(ENV, "MOUNT", "bench"))
const T_AVG = envf("T_AVG", 2.0)
const CASE = get(ENV, "CASE", "stage8_bench_n$(N)_$(MOUNT)")
const FRAME_DT = envf("FRAME_DT", 0.0)
const FRAME_T0 = envf("FRAME_T0", 0.0)
const FRAME_STRIDE = envi("FRAME_STRIDE", 2)
MOUNT in ("bench", "fixed") || error("MOUNT must be bench or fixed")

if MODE == "run"
    const BACKEND = lowercase(get(ENV, "BACKEND", "gpu"))
    BACKEND == "gpu" && using AMDGPU          # load AMDGPU BEFORE WaterLily (activates the ext)
end
using WaterLily, StaticArrays, Printf, Serialization
MODE == "plot" && using Plots, CSV, DataFrames, Statistics
include(joinpath(@__DIR__, "lib_bench.jl"))
using .Bench3D
const B = Bench3D

# ---------------------------------------------------------------------------------
"Dump downsampled λ2 [1/s²] and body SDF [cells] for one video frame (host copies)."
function save_frame(bs, dir, i, t, θ, q, ld)
    sim, u = bs.sim, bs.units
    s = FRAME_STRIDE; tf = B.unit_factor(u, :time)
    l2 = Array(B.lambda2!(sim))[2:s:end-1, 2:s:end-1, 2:s:end-1] ./ Float32(tf^2)
    sd = Array(B.sdf_field!(sim))[2:s:end-1, 2:s:end-1, 2:s:end-1]
    serialize(joinpath(dir, @sprintf("frame_%04d.jls", i)),
              Dict("l2" => l2, "sdf" => sd, "t" => t, "θ" => θ, "Fx" => ld.F[1], "Fy" => ld.F[2],
                   "sway" => q[1], "yaw" => q[2], "Mz" => ld.M[3],
                   "stride" => s, "origin" => Vector(bs.origin), "lf" => B.unit_factor(u, :length),
                   "n" => N, "x_tip" => B.L_REF, "box" => ((-0.12, 0.55), (-0.18, 0.18), (-0.09, 0.09)),
                   "caption" => "WaterLily.jl 3D: CAD tail (Fish_Tail.step) on the test stand, still water, " *
                                "valve 0.5 Hz, holder $(MOUNT == "bench" ? "free in sway + yaw" : "clamped")"))
end

function run_bench()
    if BACKEND == "gpu"
        AMDGPU.functional() || error("AMDGPU not functional (ROCM_PATH?)")
        mem = ROCArray; sync = AMDGPU.synchronize; dev = string(AMDGPU.device())
    else
        mem = Array; sync = () -> nothing; dev = "CPU $(Threads.nthreads()) threads"
    end
    vp = B.BENCH_VALVE
    B.check_freq(B.BENCH_FREQ; p=vp)
    bs = B.make_bench_sim(; n=N, mem)
    sim, u = bs.sim, bs.units
    props = B.tail_props(bs.grid)
    H = B.Holder(props; fixed=MOUNT == "fixed")
    dims = size(sim.flow.p) .- 2
    ncell = prod(dims)
    @printf("[%s] grid %s = %.1f M cells, n = %d cells/L_REF (%.2f mm), fin pad %.2f mm, Re_sim = %.0f, f = %.2f Hz, mount = %s, %s\n",
            CASE, join(dims, "×"), ncell / 1e6, N, 1e3 * B.unit_factor(u, :length), 1e3 * bs.pad, u.Re,
            B.BENCH_FREQ, MOUNT, dev)
    @printf("[%s] tail: V = %.1f ml, m = %.3f kg, I_pivot = %.3g kg m², added mass (strip) sway %.2f kg, yaw %.3g kg m²\n",
            CASE, 1e6props.V, props.m, props.Ip, props.Ma[1, 1], props.Ma[2, 2])
    flush(stdout)

    valve = B.Valve(B.BENCH_FREQ; p=vp)
    θprev = 0.0
    tf = B.unit_factor(u, :time)
    max_steps = envi("MAX_STEPS", typemax(Int))
    P = 1 / B.BENCH_FREQ
    t_snaps = sort([T_END - 0.75P, T_END - 0.5P, T_END - 0.25P, T_END])
    snaps = Dict{String,Any}[]
    rows = NamedTuple[]
    pr = B.Progress(CASE, T_END; dir=joinpath(B.RESULTS_DIR, "progress"))
    steps = 0; wall0 = time(); twarm = NaN; isnap = 1
    fdir = joinpath(B.RESULTS_DIR, "frames", CASE); iframe = 1; t_frame = FRAME_T0
    FRAME_DT > 0 && mkpath(fdir)
    Q = SVector(0.0, 0.0)                    # fluid load (F_y, M_z) of the last step
    B._cap_dt!(sim, 0.4)
    try
        while B.t_phys(bs) < T_END - 1e-12 && steps < max_steps
            t0g = Float64(WaterLily.time(sim.flow)); t1g = Float64(sum(sim.flow.Δt))
            t0 = t0g * tf; t1 = t1g * tf
            st = B.valve_state(valve, t1)
            θ1 = B.theta_kinematic(st.V_p, vp)
            θdd = (st.s * vp.Q_const - st.Q) / vp.tau_valve / vp.A_r     # θ̈ = Q̇/A_r
            q0, q1 = B.holder_step!(H, t1 - t0, Q, θdd)
            sim.body = B.retrack(sim.body, bs.grid, u, bs.origin, t0g, t1g, θprev, θ1, q0, q1)
            θprev = θ1
            sim_step!(sim; remeasure=true)
            B.clean_pressure!(sim)
            B._cap_dt!(sim, 0.4)
            steps += 1
            ld = B.body_loads(bs, q1[1])
            isfinite(ld.F[1]) || error("diverged at t = $t1 s (NaN force)")
            Q = SVector(ld.F[2], ld.M[3])
            push!(rows, (; t=t1, V_ref=st.V_ref, V_p=st.V_p, Q=st.Q, s=st.s, θ=θ1, θdd,
                          sway=H.q[1], yaw=H.q[2], v_sway=H.v[1], v_yaw=H.v[2],
                          Fx=ld.F[1], Fy=ld.F[2], Fz=ld.F[3], Fpx=ld.Fp[1], Fpy=ld.Fp[2],
                          Mx=ld.M[1], My=ld.M[2], Mz=ld.M[3], thrust=-ld.F[1],
                          dt_grid=Float64(sim.flow.Δt[end - 1]), pois=Int(sim.pois.n[end]), step=steps,
                          wall=time() - wall0))
            steps == 5 && (sync(); twarm = time() - wall0)
            B.progress_update!(pr, t1, steps; s=st.s, V_p=st.V_p, θ=θ1, Fx=ld.F[1], Fy=ld.F[2])
            if isnap <= length(t_snaps) && t1 >= t_snaps[isnap] - 1e-9
                d = B.slices(bs); d["t"] = t1; d["θ"] = θ1; d["sway"] = H.q[1]; d["yaw"] = H.q[2]
                push!(snaps, d); isnap += 1
            end
            if FRAME_DT > 0 && t1 >= t_frame - 1e-9
                save_frame(bs, fdir, iframe, t1, θ1, H.q, ld)
                iframe += 1; t_frame += FRAME_DT
            end
        end
    catch err
        B.progress_finish!(pr, B.t_phys(bs), steps, "failed")
        rethrow(err)
    end
    sync()
    wall = time() - wall0
    B.progress_finish!(pr, B.t_phys(bs), steps, "done")
    serialize(joinpath(B.RESULTS_DIR, "$(CASE)_snapshots.jls"),
              Dict("snaps" => snaps, "origin" => Vector(bs.origin), "n" => N, "dims" => collect(dims),
                   "lf" => B.unit_factor(u, :length), "mount" => MOUNT))
    path = joinpath(B.RESULTS_DIR, "$(CASE)_timeseries.csv")
    open(path, "w") do io
        ks = keys(rows[1]); println(io, join(ks, ","))
        for r in rows
            println(io, join((v isa Integer ? string(v) : @sprintf("%.8g", v) for v in values(r)), ","))
        end
    end
    msstep = 1e3 * (wall - twarm) / max(steps - 5, 1)
    m = [r.t >= T_AVG for r in rows]
    tt = [r.t for r in rows][m]
    mean_tw(col) = (y = [getfield(r, col) for r in rows][m]; dt = diff(tt);
                    sum(0.5 .* (y[1:end-1] .+ y[2:end]) .* dt) / sum(dt))
    info = Dict("case" => CASE, "grid" => join(dims, "x"), "Mcells" => ncell / 1e6, "n" => N,
                "steps" => steps, "wall_s" => wall, "ms_per_step" => msstep, "t_end" => B.t_phys(bs),
                "f" => B.BENCH_FREQ, "mount" => MOUNT, "Re_sim" => u.Re, "fin_pad_mm" => 1e3 * bs.pad,
                "tail_V_ml" => 1e6 * props.V, "tail_m_kg" => props.m, "Ma_sway_kg" => props.Ma[1, 1],
                "Fx_mean" => mean_tw(:Fx), "Fy_mean" => mean_tw(:Fy), "Mz_mean" => mean_tw(:Mz),
                "T_AVG" => T_AVG, "device" => dev)
    open(joinpath(B.RESULTS_DIR, "$(CASE)_info.txt"), "w") do io
        for k in sort(collect(keys(info))); println(io, k, " = ", info[k]); end
    end
    @printf("[%s] %d steps, wall %.1f min, %.0f ms/step; mean(t≥%.1f s) Fx = %.4g N (thrust %+.4g N), Fy = %.3g N, Mz = %.3g N m\n",
            CASE, steps, wall / 60, msstep, T_AVG, info["Fx_mean"], -info["Fx_mean"], info["Fy_mean"], info["Mz_mean"])
end

# ---------------------------------------------------------------------------------
function tmean(df, col; t_from)
    m = df.t .>= t_from; t = df.t[m]; y = df[m, col]
    length(t) < 2 && return NaN
    dt = diff(t); sum(0.5 .* (y[1:end-1] .+ y[2:end]) .* dt) / sum(dt)
end
trms(df, col; t_from) = (m = df.t .>= t_from; sqrt(tmean(DataFrame(t=df.t, y=df[!, col] .^ 2), :y; t_from)))
amp(df, col; t_from) = (y = df[df.t .>= t_from, col]; (maximum(y) - minimum(y)) / 2)

"Grid index -> physical coordinate [m] relative to the tail root (cell centres at I − 1.5)."
coord(i, o, lf) = (i - 1.5 - o) * lf

function slice_panel(A, S, o1, o2, lf; title, xlab, ylab, clim, xlims=nothing, ylims=nothing)
    x = coord.(1:size(A, 1), o1, lf); y = coord.(1:size(A, 2), o2, lf)
    p = heatmap(x, y, permutedims(clamp.(A, -clim, clim)); c=:RdBu, clims=(-clim, clim), aspect_ratio=:equal,
                title, xlabel=xlab, ylabel=ylab, colorbar_title="ω [1/s]", titlefontsize=9, guidefontsize=8,
                tickfontsize=7)
    contour!(p, x, y, permutedims(S); levels=[0.0], c=:black, lw=1.2, colorbar_entry=false)
    xlims !== nothing && xlims!(p, xlims); ylims !== nothing && ylims!(p, ylims)
    p
end

function plot_stage8()
    R = B.RESULTS_DIR
    cases = split(get(ENV, "CASES", "stage8_bench_n128_bench,stage8_bench_n128_fixed"), ",")
    cases = [c for c in cases if isfile(joinpath(R, "$(c)_timeseries.csv"))]
    isempty(cases) && error("no stage 8 results found")
    gr(); default(fontfamily="sans-serif", dpi=150)
    summary = NamedTuple[]
    for c in cases
        df = CSV.read(joinpath(R, "$(c)_timeseries.csv"), DataFrame)
        p1 = plot(df.t, df.θ; label="θ tail angle [rad]", c=:black, legend=:topright,
                  title="$c: CAD tail on the stand, valve 0.5 Hz, still water", titlefontsize=9)
        plot!(p1, df.t, 1e6 .* df.V_p ./ 13; label="V_p / 13 ml", c=:gray, ls=:dash)
        p2 = plot(df.t, 1e3 .* df.Fy; label="Fy (side) [mN]", c=3, legend=:topright)
        plot!(p2, df.t, 1e3 .* df.thrust; label="thrust −Fx [mN]", c=1)
        hline!(p2, [0]; c=:gray, ls=:dash, label="")
        p3 = plot(df.t, 1e3 .* df.Mz; label="Mz about the pivot [mN m]", c=2, legend=:topright)
        p4 = plot(df.t, 1e3 .* df.sway; label="holder sway [mm]", c=4, xlabel="t [s]", legend=:topright)
        plot!(twinx(p4), df.t, rad2deg.(df.yaw); label="holder yaw [°]", c=5, legend=:bottomright)
        plot(p1, p2, p3, p4; layout=(4, 1), size=(1000, 1100), left_margin=5Plots.mm, right_margin=12Plots.mm)
        savefig(joinpath(R, "$(c)_forces.png"))
        info = Dict(split(l, " = ")[1] => split(l, " = ")[2] for l in eachline(joinpath(R, "$(c)_info.txt")))
        push!(summary, (; case=c, mount=info["mount"], grid=info["grid"], Mcells=parse(Float64, info["Mcells"]),
                        steps=parse(Int, info["steps"]), wall_min=parse(Float64, info["wall_s"]) / 60,
                        θ_amp=amp(df, :θ; t_from=T_AVG), thrust_mean=-tmean(df, :Fx; t_from=T_AVG),
                        Fy_amp=amp(df, :Fy; t_from=T_AVG), Mz_amp=amp(df, :Mz; t_from=T_AVG),
                        sway_amp_mm=1e3amp(df, :sway; t_from=T_AVG), yaw_amp_deg=rad2deg(amp(df, :yaw; t_from=T_AVG)),
                        sway_mean_mm=1e3tmean(df, :sway; t_from=T_AVG)))
        sn = deserialize(joinpath(R, "$(c)_snapshots.jls"))
        o, lf = sn["origin"], sn["lf"]; snaps = sn["snaps"]
        isempty(snaps) && continue
        clim = 15.0; xl = (-0.12, 0.55)
        ps = [slice_panel(d["wz_zmid"], d["sdf_zmid"], o[1], o[2], lf; clim, xlims=xl, ylims=(-0.2, 0.2),
                          title=@sprintf("top view z = 0, t = %.2f s, θ = %+.2f, sway %+.1f mm, yaw %+.1f°", d["t"], d["θ"],
                                         1e3d["sway"], rad2deg(d["yaw"])), xlab="x [m]", ylab="y [m]") for d in snaps]
        plot(ps...; layout=(length(ps), 1), size=(1000, 330 * length(ps)))
        savefig(joinpath(R, "$(c)_wake_phases.png"))
        s = snaps[end]
        py = slice_panel(s["wy_ymid"], s["sdf_ymid"], o[1], o[3], lf; clim, xlims=xl,
                         title="side view y = 0: ω_y", xlab="x [m]", ylab="z [m]")
        px = slice_panel(s["wx_xwake"], s["sdf_xwake"], o[2], o[3], lf; clim,
                         title=@sprintf("cross-flow x = %.3f m (6 cm behind the fin tip): ω_x", s["x_wake"]),
                         xlab="y [m]", ylab="z [m]")
        plot(py, px; layout=(2, 1), size=(1000, 800))
        savefig(joinpath(R, "$(c)_wake_slices.png"))
    end
    sdf = DataFrame(summary)
    CSV.write(joinpath(R, "stage8_summary.csv"), sdf)
    show(stdout, sdf; allcols=true); println()
    println("plots written to ", R)
end

if MODE == "run"
    run_bench()
elseif MODE == "plot"
    plot_stage8()
else
    error("unknown mode $MODE (run | plot)")
end
