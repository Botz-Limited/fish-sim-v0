# Stage 4 – frequency sweep at the self-propelled speed U* (n = 128 value from stage 3).
# Tethered fish, valve-driven tail (kinematic mode), f = 1.5 … 2.5 Hz step 0.25.
# Per f: mean net force F_x, tail pressure thrust T, tip amplitude A_tip (peak-to-peak),
# Strouhal number St = f·A_tip/U*, mean input power P, Froude efficiency η = T·U*/P,
# valve switches per cycle. Pass criterion (spec): St reported per f; runs independent.
#
# Definitions (see stage_common.jl):
#   T    = D_rigid(U*) − mean F_x,net: the rigid-fish drag at U* (stage 3, same n, interpolated)
#          plus the measured net thrust (at U* the net force is ≈ 0, so the net thrust alone
#          cannot be used). Assumes the flapping body has the drag of the rigid one.
#          Also logged: T_tail_p = −mean F_x,p over the tail surface (x > root, p∞ = 0 at the
#          inlet) and eta_tail_p – it came out NEGATIVE (the open cut at the root and the
#          tail's own pressure drag dominate), so it is NOT used as thrust.
#   P    = mean(−Q_θ·θ̇), Q_θ = ∫ f_y h(x) ds the generalized pressure force of the bending
#          mode y = θ·h(x), θ̇ = Q/A_r (exact in kinematic mode) – i.e. P = ∫ p (u_body·n) ds,
#          the power the tail puts into the fluid (pressure part; the viscous part is neglected).
#          Cross-check P_M = mean(−M·θ̇) with M the tail moment about the root (rigid-flap
#          approximation, over-weights the root region).
#
# Run from WaterLily/:
#   julia --project=. -t 4 scripts/stage4_freq_sweep.jl                   # all f serially + report
#   scripts/run_parallel.sh -j 2 -t 2 scripts/stage4_freq_sweep.jl f1.50 f1.75 f2.00 f2.25 f2.50
#   julia --project=. scripts/stage4_freq_sweep.jl report
#   env U_STAR=0.35 to override U* (default: results/stage3_Ustar.csv, n = 128), N=64 for checks,
#   FISH_LIVE=1 for the live viewer.
# Output: results/stage4_cases/<case>.csv, results/stage4_<case>_n<n>_timeseries.csv,
#         results/stage4_freq_sweep.csv, results/stage4_freq_sweep.png
using WaterLily, Statistics, Printf, DataFrames, CSV, Plots
using FishLily
include(joinpath(@__DIR__, "stage_common.jl"))

const FS = [1.5, 1.75, 2.0, 2.25, 2.5]
const N = parse(Int, get(ENV, "N", "128"))
const N_CYC = 6
const CASE_DIR = joinpath(RESULTS_DIR, "stage4_cases")
casename(f) = @sprintf("f%.2f", f)
const ALL = casename.(FS)

function read_ustar()
    haskey(ENV, "U_STAR") && return parse(Float64, ENV["U_STAR"])
    path = joinpath(RESULTS_DIR, "stage3_Ustar.csv")
    isfile(path) || error("$path not found – run stage 3 first (or set U_STAR)")
    t = CSV.read(path, DataFrame)
    r = t[t.n .== 128, :]
    (nrow(r) == 1 && isfinite(r.U_star[1])) || error("no finite n = 128 U* in $path")
    return r.U_star[1]
end

function run_case(name)
    f = parse(Float64, name[2:end]); check_freq(f)
    U = read_ustar()
    tag = "stage4_$(name)_n$(N)"
    fs = make_fish_sim(; n=N, U_in=U, name=tag)
    t_a, t_b = cycle_window(f; n_cycles=N_CYC, t_skip=max(t_skip_valve(f), 1.5 * L_BODY / U))
    drv = ValveDriver(f)
    extras = TailExtras(fs)
    live = live_hook(fs, t_b; driver=drv, title=@sprintf("stage 4: f = %.2f Hz, U* = %.3f m/s, n = %d", f, U, N))   # FISH_LIVE=1
    wall0 = time()
    df = run_fish!(fs, t_b; driver=drv, case=tag, on_frame=chain_hooks(pressure_fix!, extras, live), frame_every=1)
    wall = time() - wall0
    live_finish!(live)
    ex = DataFrame(extras)
    nrow(ex) == nrow(df) || error("extras/log length mismatch")
    df.Qθ = ex.Qθ; df.Fx_tail_p = ex.Fx_tail_p
    df.θdot = df.Q ./ VALVE.A_r
    df.P_in = -df.Qθ .* df.θdot
    df.P_M = -df.M .* df.θdot
    CSV.write(joinpath(RESULTS_DIR, "$(tag)_timeseries.csv"), df)
    wm(c) = window_mean(df, c, t_a, t_b)
    tm = (t_a + t_b) / 2
    θpp = cycle_peak_to_peak(df, :θ, f, t_a, t_b)
    A_tip = θpp * bend_h(FishGeom(), L_TAIL)
    T = -wm(:Fx_tail_p); P = wm(:P_in)
    row = (; case=name, f, U_star=U, n=N, t_avg_from=t_a, t_avg_to=t_b,
           Fx_net=wm(:Fx), Fx_net_1st_half=window_mean(df, :Fx, t_a, tm), Fx_net_2nd_half=window_mean(df, :Fx, tm, t_b),
           thrust_net=-wm(:Fx), T_tail_p=T, theta_pp=θpp, theta_mean=wm(:θ), A_tip_pp=A_tip,
           St=f * A_tip / U, P_in=P, P_M=wm(:P_M), eta_tail_p=T * U / P,
           Fy_amp=cycle_peak_to_peak(df, :Fy, f, t_a, t_b) / 2,
           switches_per_cycle=switches_in_window(df, f, t_a, t_b), steps=df.step[end], wall_s=wall)
    mkpath(CASE_DIR)
    CSV.write(joinpath(CASE_DIR, "$(name)_n$(N).csv"), DataFrame([row]))
    @printf("\n%s f=%.2f U*=%.3f n=%d: F_x net %+.4f N/m, T_tail %.4f N/m, A_tip %.1f mm, St %.3f, P %.3f W/m (P_M %.3f), η_tail_p %.3f, sw/cyc %.2f, wall %.0f s\n",
            name, f, U, N, row.Fx_net, T, 1e3A_tip, row.St, P, row.P_M, row.eta_tail_p, row.switches_per_cycle, wall)
    row
end

function report()
    isdir(CASE_DIR) || (println("no stage 4 cases"); return)
    tab = reduce(vcat, [CSV.read(joinpath(CASE_DIR, x), DataFrame) for x in readdir(CASE_DIR) if endswith(x, ".csv")])
    sort!(tab, [:n, :f])
    # thrust at (near) self-propulsion: T = D_rigid(U*) − F_x,net  (rigid-fish drag from stage 3,
    # same n, linear interpolation in U); η = T·U*/P
    s3 = CSV.read(joinpath(RESULTS_DIR, "stage3_inflow_sweep.csv"), DataFrame)
    function d_rigid(U, n)
        r = sort(s3[(s3.kind .== "rigid") .& (s3.n .== n), :], :U)
        i = findlast(<=(U), r.U); (i === nothing || i == nrow(r)) && return NaN
        r.Fx_mean[i] + (U - r.U[i]) * (r.Fx_mean[i+1] - r.Fx_mean[i]) / (r.U[i+1] - r.U[i])
    end
    tab.D_rigid = [d_rigid(r.U_star, r.n) for r in eachrow(tab)]
    tab.T = tab.D_rigid .- tab.Fx_net
    tab.eta = tab.T .* tab.U_star ./ tab.P_in
    CSV.write(joinpath(RESULTS_DIR, "stage4_freq_sweep.csv"), tab)
    show(stdout, tab[:, [:case, :n, :f, :U_star, :Fx_net, :Fx_net_1st_half, :Fx_net_2nd_half, :T_tail_p, :A_tip_pp,
                         :St, :P_in, :P_M, :D_rigid, :T, :eta, :eta_tail_p, :switches_per_cycle, :wall_s]]; allrows=true, allcols=true)
    println()
    t = tab[tab.n .== maximum(tab.n), :]
    kw = (m=:o, xlabel="tail frequency f [Hz]", legend=:best)
    p1 = plot(t.f, t.Fx_net, label="net F_x (> 0 drag)", ylabel="[N/m]"; kw...)
    plot!(p1, t.f, t.T, m=:s, label="thrust T = D_rigid(U*) − F_x,net")
    plot!(p1, t.f, -t.T_tail_p, m=:d, ls=:dash, label="tail pressure force F_x,p,tail (> 0 drag)"); hline!(p1, [0], c=:black, lw=0.5, label="")
    p2 = plot(t.f, 1e3t.A_tip_pp, label="A_tip (peak-to-peak)", ylabel="[mm]"; kw...)
    p3 = plot(t.f, t.St, label="St = f·A_tip/U*", ylabel="St [-]"; kw...)
    p4 = plot(t.f, t.P_in, label="P = ∫p(u_b·n)ds", ylabel="[W/m]"; kw...)
    plot!(p4, t.f, t.P_M, m=:s, ls=:dash, label="−M·θ̇ (rigid-flap approx.)")
    p5 = plot(t.f, t.eta, label="η = T·U*/P", ylabel="η [-]"; kw...)
    p6 = plot(t.f, t.switches_per_cycle, label="valve switches / cycle", ylabel="[-]", ylims=(0, 3); kw...)
    plot(p1, p2, p3, p4, p5, p6, layout=(2, 3), size=(1500, 800), margin=5Plots.mm,
         plot_title=@sprintf("Stage 4: frequency sweep at U* = %.3f m/s (n = %d)", t.U_star[1], t.n[1]))
    savefig(joinpath(RESULTS_DIR, "stage4_freq_sweep.png"))
    tab
end

mode, cases = job_args(ALL)
mkpath(RESULTS_DIR)
if mode == :run
    foreach(run_case, cases)
elseif mode == :report
    report()
else
    foreach(run_case, ALL)
    report()
end
