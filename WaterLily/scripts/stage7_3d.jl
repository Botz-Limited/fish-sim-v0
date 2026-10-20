# Stage 7 – 3D fish (elliptic sections) on the AMD GPU, tethered in inflow.
#
# Modes (first argument), run from WaterLily/:
#   run   : 3D CFD (GPU env)   ROCM_PATH=$PWD/gpu/rocm-shim julia --project=gpu -t 1 scripts/stage7_3d.jl run
#   ref2d : 2D reference, same valve/inflow (FishLily env, CPU)
#           julia --project=. -t 1 scripts/stage7_3d.jl ref2d
#   plot  : figures + summary numbers (FishLily env, uses Plots)
#           julia --project=. scripts/stage7_3d.jl plot
# Environment variables (run): N (cells per body length, default 160), T_END [s] (4.0),
#   F [Hz] (2.0), U_IN [m/s] (0.2), FIN (0/1, caudal fin, default 0), BACKEND (gpu/cpu),
#   CASE (default stage7_3d_n<N>[_fin]), MAX_STEPS (debug), T_AVG (start of averaging, 2.0 s),
#   FRAME_DT [s] (0 = off; > 0 dumps λ2 + body SDF every FRAME_DT for the video, viz/render3d.jl),
#   FRAME_T0 [s] (first frame, 0.0), FRAME_STRIDE (downsampling of the dumped fields, 2).
#
# Outputs: results/<case>_timeseries.csv, results/<case>_snapshots.jls (slices),
#   results/<case>_lambda2.jls (downsampled λ2 at t_end), progress file
#   results/progress/<case>.json, with FRAME_DT > 0 also results/frames/<case>/frame_NNNN.jls;
#   plot mode: results/stage7_*.png, results/stage7_summary.csv.

const MODE = length(ARGS) >= 1 ? ARGS[1] : "run"
envf(k, d) = parse(Float64, get(ENV, k, string(d)))
envi(k, d) = parse(Int, get(ENV, k, string(d)))

const N = envi("N", 160)
const T_END = envf("T_END", 4.0)
const FREQ = envf("F", 2.0)
const U_IN = envf("U_IN", 0.2)
const FIN = envi("FIN", 0) == 1
const T_AVG = envf("T_AVG", 2.0)
const CASE = get(ENV, "CASE", "stage7_3d_n$(N)" * (FIN ? "_fin" : ""))
const FRAME_DT = envf("FRAME_DT", 0.0)
const FRAME_T0 = envf("FRAME_T0", 0.0)
const FRAME_STRIDE = envi("FRAME_STRIDE", 2)

if MODE == "run"
    const BACKEND = lowercase(get(ENV, "BACKEND", "gpu"))
    BACKEND == "gpu" && using AMDGPU          # load AMDGPU BEFORE WaterLily (activates the ext)
end
using WaterLily, StaticArrays, Printf, Serialization
MODE == "ref2d" && using FishLily
MODE == "plot" && using Plots, CSV, DataFrames, Statistics
include(joinpath(@__DIR__, "lib_3d.jl"))
using .Fish3D
using .Fish3D: HEAD_A, L_TAIL
const F3 = Fish3D

# ---------------------------------------------------------------------------------
"Dump downsampled λ2 [1/s²] and body SDF [cells] for one video frame (host copies)."
function save_frame(fs, dir, i, t, θ, f)
    sim, u = fs.sim, fs.units
    s = FRAME_STRIDE; tf = F3.unit_factor(u, :time)
    l2 = Array(F3.lambda2!(sim))[2:s:end-1, 2:s:end-1, 2:s:end-1] ./ Float32(tf^2)
    sd = Array(F3.sdf_field!(sim))[2:s:end-1, 2:s:end-1, 2:s:end-1]
    serialize(joinpath(dir, @sprintf("frame_%04d.jls", i)),
              Dict("l2" => l2, "sdf" => sd, "t" => t, "θ" => θ, "Fx" => f.F[1], "Fy" => f.F[2],
                   "stride" => s, "origin" => Vector(fs.origin), "lf" => F3.unit_factor(u, :length),
                   "n" => N, "fin" => FIN))
end

function run3d()
    if BACKEND == "gpu"
        AMDGPU.functional() || error("AMDGPU not functional (ROCM_PATH=gpu/rocm-shim?)")
        mem = ROCArray; sync = AMDGPU.synchronize; dev = string(AMDGPU.device())
    else
        mem = Array; sync = () -> nothing; dev = "CPU $(Threads.nthreads()) threads"
    end
    F3.check_freq(FREQ)
    fs = F3.make_fish_sim3(; n=N, U_in=U_IN, mem, fin=FIN)
    sim, u = fs.sim, fs.units
    dims = size(sim.flow.p) .- 2
    ncell = prod(dims)
    @printf("[%s] grid %s = %.1f M cells, n = %d cells/L (%.2f mm), Re_sim = %.0f, f = %.2f Hz, U = %.2f m/s, fin = %s, %s\n",
            CASE, join(dims, "×"), ncell / 1e6, N, 1e3 * F3.unit_factor(u, :length), u.Re, FREQ, U_IN, FIN, dev)
    if BACKEND == "gpu"
        try
            fr, tot = AMDGPU.info()
            @printf("[%s] GPU memory in use after allocation: %.2f / %.2f GiB\n", CASE, (tot - fr) / 2^30, tot / 2^30)
        catch
        end
    end
    flush(stdout)

    valve = F3.Valve(FREQ)
    θprev = 0.0
    tf = F3.unit_factor(u, :time)
    max_steps = envi("MAX_STEPS", typemax(Int))
    # snapshots: 4 phases of the last tail cycle (quarter periods) + the end
    P = 1 / FREQ
    t_snaps = sort([T_END - 0.75P, T_END - 0.5P, T_END - 0.25P, T_END])
    snaps = Dict{String,Any}[]
    rows = NamedTuple[]
    pr = F3.Progress(CASE, T_END; dir=joinpath(F3.RESULTS_DIR, "progress"))
    steps = 0; wall0 = time(); twarm = NaN; isnap = 1
    fdir = joinpath(F3.RESULTS_DIR, "frames", CASE); iframe = 1; t_frame = FRAME_T0
    FRAME_DT > 0 && mkpath(fdir)
    F3._cap_dt!(sim, 0.4)
    try
        while F3.t_phys(fs) < T_END - 1e-12 && steps < max_steps
            t0g = Float64(WaterLily.time(sim.flow)); t1g = Float64(sum(sim.flow.Δt))
            t1 = t1g * tf
            st = F3.valve_state(valve, t1)
            θ1 = F3.theta_kinematic(st.V_p)
            sim.body = F3.retrack(sim.body, t0g, θprev, t1g, θ1)     # isbits body, new scalars
            θprev = θ1
            sim_step!(sim; remeasure=true)
            F3._cap_dt!(sim, 0.4)
            steps += 1
            f = F3.body_force3(fs)
            isfinite(f.F[1]) || error("diverged at t = $t1 s (NaN force)")
            push!(rows, (; t=t1, V_ref=st.V_ref, V_p=st.V_p, Q=st.Q, s=st.s, θ=θ1,
                          Fx=f.F[1], Fy=f.F[2], Fz=f.F[3], Fpx=f.Fp[1], Fvx=f.Fv[1],
                          thrust=-f.F[1], dt_grid=Float64(sim.flow.Δt[end - 1]),
                          pois=Int(sim.pois.n[end]), step=steps, wall=time() - wall0))
            steps == 5 && (sync(); twarm = time() - wall0)
            F3.progress_update!(pr, t1, steps; s=st.s, V_p=st.V_p, θ=θ1, Fx=f.F[1], Fy=f.F[2])
            if isnap <= length(t_snaps) && t1 >= t_snaps[isnap] - 1e-9
                d = F3.slices(fs); d["t"] = t1; d["θ"] = θ1
                push!(snaps, d); isnap += 1
            end
            if FRAME_DT > 0 && t1 >= t_frame - 1e-9
                save_frame(fs, fdir, iframe, t1, θ1, f)
                iframe += 1; t_frame += FRAME_DT
            end
        end
    catch err
        F3.progress_finish!(pr, F3.t_phys(fs), steps, "failed")
        rethrow(err)
    end
    sync()
    wall = time() - wall0
    F3.progress_finish!(pr, F3.t_phys(fs), steps, "done")
    # λ2 field at the end (downsampled ×2 on the host)
    l2 = Array(F3.lambda2!(sim))[2:end-1, 2:end-1, 2:end-1]
    l2d = l2[1:2:end, 1:2:end, 1:2:end]
    serialize(joinpath(F3.RESULTS_DIR, "$(CASE)_lambda2.jls"),
              Dict("l2" => l2d, "stride" => 2, "origin" => Vector(fs.origin), "n" => N,
                   "lf" => F3.unit_factor(u, :length), "tf" => F3.unit_factor(u, :time), "t" => F3.t_phys(fs)))
    serialize(joinpath(F3.RESULTS_DIR, "$(CASE)_snapshots.jls"),
              Dict("snaps" => snaps, "origin" => Vector(fs.origin), "n" => N, "dims" => collect(dims),
                   "lf" => F3.unit_factor(u, :length), "fin" => FIN))
    # CSV (hand-written; no CSV.jl in the gpu env)
    path = joinpath(F3.RESULTS_DIR, "$(CASE)_timeseries.csv")
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
                "steps" => steps, "wall_s" => wall, "ms_per_step" => msstep, "t_end" => F3.t_phys(fs),
                "f" => FREQ, "U_in" => U_IN, "fin" => FIN, "Re_sim" => u.Re,
                "Fx_mean" => mean_tw(:Fx), "Fy_mean" => mean_tw(:Fy), "Fz_mean" => mean_tw(:Fz),
                "Fpx_mean" => mean_tw(:Fpx), "Fvx_mean" => mean_tw(:Fvx),
                "T_AVG" => T_AVG, "device" => dev)
    open(joinpath(F3.RESULTS_DIR, "$(CASE)_info.txt"), "w") do io
        for k in sort(collect(keys(info))); println(io, k, " = ", info[k]); end
    end
    @printf("[%s] %d steps, wall %.1f s (%.1f min), %.1f ms/step; mean(t≥%.1f s) Fx = %.4g N (pressure %.4g, viscous %.4g), Fy = %.3g N\n",
            CASE, steps, wall, wall / 60, msstep, T_AVG, info["Fx_mean"], info["Fpx_mean"], info["Fvx_mean"], info["Fy_mean"])
end

# ---------------------------------------------------------------------------------
function ref2d()
    n2 = envi("N2D", 128)
    case = "stage7_2d_ref_n$(n2)"
    fs = FishLily.make_fish_sim(; n=n2, U_in=U_IN, name=case)
    df = FishLily.run_fish!(fs, T_END; driver=FishLily.ValveDriver(FREQ), case, moment=false, log_every=2)
    FishLily.save_csv(df, "$(case)_timeseries")
    Fx = FishLily.cycle_mean(df, :Fx; t_from=T_AVG)
    @printf("[%s] mean(t≥%.1f s) Fx' = %.4g N/m (pressure %.4g, viscous %.4g)\n", case, T_AVG, Fx,
            FishLily.cycle_mean(df, :Fpx; t_from=T_AVG), FishLily.cycle_mean(df, :Fvx; t_from=T_AVG))
end

# ---------------------------------------------------------------------------------
# --- plots (FishLily env: Plots, CSV, DataFrames) ----------------------------------
function tmean(df, col; t_from)
    m = df.t .>= t_from; t = df.t[m]; y = df[m, col]
    length(t) < 2 && return NaN
    dt = diff(t); sum(0.5 .* (y[1:end-1] .+ y[2:end]) .* dt) / sum(dt)
end
trms(df, col; t_from) = sqrt(tmean(transform(df, col => (x -> x .^ 2) => :_sq), :_sq; t_from))

"Grid index -> physical coordinate [m] relative to the tail root (cell centres, loc(0,I) = I − 1.5)."
coord(i, o, lf) = (i - 1.5 - o) * lf

function slice_panel(A, S, ax1, ax2, o1, o2, lf; title, xlab, ylab, clim, xlims=nothing, ylims=nothing)
    x = coord.(1:size(A, 1), o1, lf); y = coord.(1:size(A, 2), o2, lf)
    p = heatmap(x, y, permutedims(clamp.(A, -clim, clim)); c=:RdBu, clims=(-clim, clim), aspect_ratio=:equal,
                title, xlabel=xlab, ylabel=ylab, colorbar_title="ω [1/s]", titlefontsize=9, guidefontsize=8,
                tickfontsize=7)
    contour!(p, x, y, permutedims(S); levels=[0.0], c=:black, lw=1.2, colorbar_entry=false)
    xlims !== nothing && xlims!(p, xlims); ylims !== nothing && ylims!(p, ylims)
    p
end

function plot_stage7()
    R = Fish3D.RESULTS_DIR
    cases = split(get(ENV, "CASES", "stage7_3d_n224,stage7_3d_n224_fin"), ",")
    cases = [c for c in cases if isfile(joinpath(R, "$(c)_timeseries.csv"))]
    isempty(cases) && error("no 3D results found")
    ref2 = joinpath(R, "stage7_2d_ref_n128_timeseries.csv")
    df2 = isfile(ref2) ? CSV.read(ref2, DataFrame) : nothing
    b_eff = Fish3D.mean_height(); b_max = Fish3D.HEAD_H
    @printf("b_eff (mean body height) = %.4f m, max height = %.3f m\n", b_eff, b_max)
    gr(); default(fontfamily="sans-serif", dpi=150)
    summary = NamedTuple[]
    # ---- time series ----
    for c in cases
        df = CSV.read(joinpath(R, "$(c)_timeseries.csv"), DataFrame)
        p1 = plot(df.t, df.θ; label="θ (tail angle)", ylabel="θ [rad]", c=:black, legend=:topright,
                  title="$c: valve-driven tail, f = $(FREQ) Hz, U = $(U_IN) m/s (tethered)", titlefontsize=9)
        p2 = plot(df.t, df.thrust; label="3D thrust −Fx", c=1, ylabel="force [N]", legend=:bottomright)
        plot!(p2, df.t, -df.Fpx; label="pressure part", c=1, ls=:dot, lw=0.8)
        if df2 !== nothing
            plot!(p2, df2.t, -df2.Fx .* b_eff; label="2D −Fx'·b_eff (b_eff=$(round(b_eff, digits=3)) m)", c=2, alpha=0.7)
        end
        hline!(p2, [0]; c=:gray, ls=:dash, label="")
        vspan!(p2, [T_AVG, maximum(df.t)]; c=:gray, alpha=0.08, label="averaging window")
        p3 = plot(df.t, df.Fy; label="3D lateral Fy", c=3, ylabel="force [N]", xlabel="t [s]", legend=:bottomright)
        plot!(p3, df.t, df.Fz; label="3D vertical Fz", c=4)
        df2 !== nothing && plot!(p3, df2.t, df2.Fy .* b_eff; label="2D Fy'·b_eff", c=2, alpha=0.6)
        plot(p1, p2, p3; layout=(3, 1), size=(1000, 900), left_margin=5Plots.mm)
        savefig(joinpath(R, "$(c)_forces.png"))
        info = Dict(split(l, " = ")[1] => split(l, " = ")[2] for l in eachline(joinpath(R, "$(c)_info.txt")))
        push!(summary, (; case=c, grid=info["grid"], Mcells=parse(Float64, info["Mcells"]),
                        steps=parse(Int, info["steps"]), wall_min=parse(Float64, info["wall_s"]) / 60,
                        ms_per_step=parse(Float64, info["ms_per_step"]),
                        Fx_mean=tmean(df, :Fx; t_from=T_AVG), Fpx_mean=tmean(df, :Fpx; t_from=T_AVG),
                        Fvx_mean=tmean(df, :Fvx; t_from=T_AVG), Fy_mean=tmean(df, :Fy; t_from=T_AVG),
                        Fy_rms=trms(df, :Fy; t_from=T_AVG), Fz_rms=trms(df, :Fz; t_from=T_AVG),
                        θ_amp=(maximum(df.θ[df.t.>=T_AVG]) - minimum(df.θ[df.t.>=T_AVG])) / 2))
    end
    if df2 !== nothing
        Fx2 = tmean(df2, :Fx; t_from=T_AVG)
        push!(summary, (; case="stage7_2d_ref_n128 (×b_eff)", grid="-", Mcells=NaN, steps=nrow(df2), wall_min=NaN,
                        ms_per_step=NaN, Fx_mean=Fx2 * b_eff, Fpx_mean=tmean(df2, :Fpx; t_from=T_AVG) * b_eff,
                        Fvx_mean=tmean(df2, :Fvx; t_from=T_AVG) * b_eff, Fy_mean=tmean(df2, :Fy; t_from=T_AVG) * b_eff,
                        Fy_rms=trms(df2, :Fy; t_from=T_AVG) * b_eff, Fz_rms=NaN,
                        θ_amp=(maximum(df2.θ[df2.t.>=T_AVG]) - minimum(df2.θ[df2.t.>=T_AVG])) / 2))
        @printf("2D: Fx' = %.4g N/m (×b_eff %.4g N, ×b_max %.4g N)\n", Fx2, Fx2 * b_eff, Fx2 * b_max)
    end
    sdf = DataFrame(summary)
    sdf.net = [isfinite(x) ? (x < 0 ? "net thrust" : "net drag") : "" for x in sdf.Fx_mean]
    CSV.write(joinpath(R, "stage7_summary.csv"), sdf)
    show(stdout, sdf; allcols=true); println()
    # ---- wake slices ----
    for c in cases
        sn = deserialize(joinpath(R, "$(c)_snapshots.jls"))
        o, lf = sn["origin"], sn["lf"]; snaps = sn["snaps"]
        isempty(snaps) && continue
        s = snaps[end]
        clim = 30.0
        xl = (-0.08, 0.6)
        pz = slice_panel(s["wz_zmid"], s["sdf_zmid"], 1, 2, o[1], o[2], lf; clim, xlims=xl,
                         title="top view z = 0: ω_z  (t = $(round(s["t"], digits=3)) s)", xlab="x [m]", ylab="y [m]")
        py = slice_panel(s["wy_ymid"], s["sdf_ymid"], 1, 3, o[1], o[3], lf; clim, xlims=xl,
                         title="side view y = 0: ω_y", xlab="x [m]", ylab="z [m]")
        px = slice_panel(s["wx_xwake"], s["sdf_xwake"], 2, 3, o[2], o[3], lf; clim,
                         title="cross-flow x = $(round(L_TAIL + s["x_wake"] - L_TAIL, digits=3)) m behind root: ω_x",
                         xlab="y [m]", ylab="z [m]")
        plot(pz, py, px; layout=grid(3, 1; heights=[0.3, 0.3, 0.4]), size=(1000, 1250))
        savefig(joinpath(R, "$(c)_wake_slices.png"))
        # phases of the last cycle (top view)
        ps = [slice_panel(d["wz_zmid"], d["sdf_zmid"], 1, 2, o[1], o[2], lf; clim, xlims=xl,
                          title="z = 0, t = $(round(d["t"], digits=3)) s, θ = $(round(d["θ"], digits=2))",
                          xlab="x [m]", ylab="y [m]") for d in snaps]
        plot(ps...; layout=(length(ps), 1), size=(1000, 300 * length(ps)))
        savefig(joinpath(R, "$(c)_wake_phases.png"))
    end
    # ---- λ2 vortex cores (3D point cloud; light alternative to an isosurface) ----
    for c in cases
        f = joinpath(R, "$(c)_lambda2.jls"); isfile(f) || continue
        L = deserialize(f); l2 = L["l2"]; st = L["stride"]; o = L["origin"]; lf = L["lf"]; tf = L["tf"]
        l2p = l2 ./ tf^2                              # [1/s²]
        # threshold: 2 % of the strongest vortex core in the wake (x > tail tip + 3 cm)
        xs = [coord((i - 1) * st + 2, o[1], lf) for i in 1:size(l2p, 1)]
        iw = findfirst(>(L_TAIL + 0.03), xs)
        thr = 0.02 * minimum(l2p[iw:end, :, :])
        idx = findall(<(thr), l2p)
        idx = length(idx) > 60000 ? idx[round.(Int, range(1, length(idx), length=60000))] : idx
        X = [coord((I[1] - 1) * st + 2, o[1], lf) for I in idx]
        Y = [coord((I[2] - 1) * st + 2, o[2], lf) for I in idx]
        Z = [coord((I[3] - 1) * st + 2, o[3], lf) for I in idx]
        # body surface points (straight-section ellipses, bent by θ at t_end) for orientation
        sn = deserialize(joinpath(R, "$(c)_snapshots.jls")); θe = isempty(sn["snaps"]) ? 0.0 : sn["snaps"][end]["θ"]
        g = Fish3D.FishGeom(Float64); bx = Float64[]; by = Float64[]; bz = Float64[]
        for x in range(-HEAD_A + 0.002, L_TAIL - 0.002, length=60), φ in range(0, 2π, length=24)
            w = 0.0; a, b = 0.0, 0.05
            for _ in 1:40; m = (a + b) / 2; Fish3D.fish_sdf_straight(g, x, m) < 0 ? (a = m) : (b = m); end
            w = a; yc = θe * Fish3D.bend_h(g, x)
            push!(bx, x); push!(by, yc + w * cos(φ)); push!(bz, Fish3D.K_H * w * sin(φ))
        end
        if get(sn, "fin", false)          # caudal fin plate (mid-surface), bent like the tail
            for x in range(Fish3D.FIN_X0, Fish3D.FIN_X1, length=12), z in range(-Fish3D.FIN_HH, Fish3D.FIN_HH, length=16)
                push!(bx, x); push!(by, θe * Fish3D.bend_h(g, x)); push!(bz, z)
            end
        end
        ttl = "λ2 < $(round(thr, sigdigits=2)) 1/s² (2 % of strongest wake core), t = $(round(L["t"], digits=2)) s"
        p1 = scatter(X, Y, Z; marker_z=Z, ms=1.0, msw=0, c=:coolwarm, label="", camera=(25, 30),
                     xlabel="x [m]", ylabel="y [m]", zlabel="z [m]", title="oblique view: " * ttl, titlefontsize=9,
                     colorbar=false, xlims=(-0.08, 0.6), ylims=(-0.15, 0.15), zlims=(-0.1, 0.1))
        scatter!(p1, bx, by, bz; ms=0.8, msw=0, c=:black, label="")
        p2 = scatter(X, Y; marker_z=Z, ms=1.2, msw=0, c=:coolwarm, label="", aspect_ratio=:equal, xlabel="x [m]",
                     ylabel="y [m]", title="top projection (colour = z)", titlefontsize=9, colorbar=false,
                     xlims=(-0.08, 0.6), ylims=(-0.15, 0.15))
        scatter!(p2, bx, by; ms=0.8, msw=0, c=:black, label="")
        p3 = scatter(X, Z; marker_z=Y, ms=1.2, msw=0, c=:coolwarm, label="", aspect_ratio=:equal, xlabel="x [m]",
                     ylabel="z [m]", title="side projection (colour = y)", titlefontsize=9, colorbar=false,
                     xlims=(-0.08, 0.6), ylims=(-0.1, 0.1))
        scatter!(p3, bx, bz; ms=0.8, msw=0, c=:black, label="")
        pl = [p1, p2, p3]
        plot(pl...; layout=grid(3, 1; heights=[0.5, 0.25, 0.25]), size=(1000, 1500))
        savefig(joinpath(R, "$(c)_lambda2.png"))
    end
    println("plots written to ", R)
end

if MODE == "run"
    run3d()
elseif MODE == "ref2d"
    ref2d()
elseif MODE == "plot"
    plot_stage7()
else
    error("unknown mode $MODE (run | ref2d | plot)")
end
