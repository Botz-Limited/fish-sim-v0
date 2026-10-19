# Stage 3 – inflow sweep. Tethered fish, tail driven by the valve (kinematic mode), f = 2 Hz,
# inflow U = 0.05 … 0.3 m/s. Mean net force F_x(U) (= drag − thrust; F_x > 0 is drag),
# interpolated self-propelled speed U* where mean F_x = 0. For comparison the rigid
# (straight) fish drag at the same U. n = 128 for all U, n = 256 for the two U that bracket U*.
# Pass criterion (spec): F_x decreases with U … i.e. the net THRUST decreases (F_x increases),
# and a sign change exists (or is reported).
#
# Run from WaterLily/:
#   julia --project=. -t 4 scripts/stage3_inflow_sweep.jl                 # all n=128 cases, then
#                                                                         #   n=256 bracket, then report
#   julia --project=. -t 2 scripts/stage3_inflow_sweep.jl run flap_U0.10_n128 rigid_U0.10_n128
#   julia --project=. scripts/stage3_inflow_sweep.jl report               # table + U* + plot
#   scripts/run_parallel.sh -j 2 -t 2 scripts/stage3_inflow_sweep.jl <cases...>   (parallel)
#   env FISH_LIVE=1 for the live viewer.
# Output: results/stage3_cases/<case>.csv (one row per case), results/stage3_<case>_timeseries.csv,
#         results/stage3_inflow_sweep.csv, results/stage3_Ustar.csv, results/stage3_inflow_sweep.png
using WaterLily, Statistics, Printf, DataFrames, CSV, Plots
using FishLily
include(joinpath(@__DIR__, "stage_common.jl"))

const F_TAIL = 2.0
const US = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]   # [m/s]; spec range 0.05–0.3, 0.4/0.5 added because U* > 0.3 at n = 64
const NS = [128, 256]
const N_CYC = 6
const CASE_DIR = joinpath(RESULTS_DIR, "stage3_cases")

casename(kind, U, n) = @sprintf("%s_U%.2f_n%d", kind, U, n)
const ALL = [casename(k, U, n) for k in ("flap", "rigid") for U in US for n in (64, NS...)]   # n = 64: quick checks

function parse_case(c)
    m = match(r"^(flap|rigid)_U([0-9.]+)_n(\d+)$", c)
    m === nothing && error("bad case name $c")
    return m[1], parse(Float64, m[2]), parse(Int, m[3])
end

"Start of the averaging: valve transient (≥ 2 s, valve locked) and ≥ 1.5 flow-through times of the body."
t_skip(U) = max(t_skip_valve(F_TAIL), 1.5 * L_BODY / U)

function run_flap(name, U, n)
    fs = make_fish_sim(; n, U_in=U, name="stage3_" * name)
    t_a, t_b = cycle_window(F_TAIL; n_cycles=N_CYC, t_skip=t_skip(U))
    drv = ValveDriver(F_TAIL)
    live = live_hook(fs, t_b; driver=drv, title=@sprintf("stage 3: U = %.2f m/s, f = %.1f Hz, n = %d", U, F_TAIL, n))   # FISH_LIVE=1
    wall0 = time()
    df = run_fish!(fs, t_b; driver=drv, case=fs.name,
                   on_frame=chain_hooks(pressure_fix!, live), frame_every=1)
    wall = time() - wall0
    live_finish!(live)
    CSV.write(joinpath(RESULTS_DIR, "$(fs.name)_timeseries.csv"), df)
    tm = (t_a + t_b) / 2
    Fx = window_mean(df, :Fx, t_a, t_b)
    row = (; case=name, kind="flap", U, n, f=F_TAIL, t_avg_from=t_a, t_avg_to=t_b,
           Fx_mean=Fx, Fx_1st_half=window_mean(df, :Fx, t_a, tm), Fx_2nd_half=window_mean(df, :Fx, tm, t_b),
           Fpx_mean=window_mean(df, :Fpx, t_a, t_b), Fvx_mean=window_mean(df, :Fvx, t_a, t_b),
           Fy_mean=window_mean(df, :Fy, t_a, t_b),
           theta_pp=cycle_peak_to_peak(df, :θ, F_TAIL, t_a, t_b),
           switches_per_cycle=switches_in_window(df, F_TAIL, t_a, t_b),
           steps=df.step[end], wall_s=wall)
    return row
end

function run_rigid(name, U, n)
    fs = make_fish_sim(; n, U_in=U, name="stage3_" * name)
    T_conv = L_BODY / U
    t_a, t_b = 4T_conv, 8T_conv                              # as stage 1
    # same near-wake kick as stage 1, so a wake instability starts the same way on every grid
    u = fs.units
    x0 = round(Int, fs.origin[1] + to_grid(u, :length, L_TAIL + 0.02))
    x1 = round(Int, fs.origin[1] + to_grid(u, :length, L_TAIL + 0.10))
    fs.sim.flow.u[x0:x1, :, 2] .= 0.05f0 * Float32(U / U_REF)
    live = live_hook(fs, t_b; title=@sprintf("stage 3: rigid fish, U = %.2f m/s, n = %d", U, n))   # FISH_LIVE=1
    wall0 = time()
    df = run_fish!(fs, t_b; case=fs.name, moment=false, log_every=4, on_frame=live)
    wall = time() - wall0
    live_finish!(live)
    CSV.write(joinpath(RESULTS_DIR, "$(fs.name)_timeseries.csv"), df)
    tm = (t_a + t_b) / 2
    return (; case=name, kind="rigid", U, n, f=0.0, t_avg_from=t_a, t_avg_to=t_b,
            Fx_mean=window_mean(df, :Fx, t_a, t_b), Fx_1st_half=window_mean(df, :Fx, t_a, tm),
            Fx_2nd_half=window_mean(df, :Fx, tm, t_b),
            Fpx_mean=window_mean(df, :Fpx, t_a, t_b), Fvx_mean=window_mean(df, :Fvx, t_a, t_b),
            Fy_mean=window_mean(df, :Fy, t_a, t_b), theta_pp=0.0, switches_per_cycle=NaN,
            steps=df.step[end], wall_s=wall)
end

function run_case(name)
    kind, U, n = parse_case(name)
    row = kind == "flap" ? run_flap(name, U, n) : run_rigid(name, U, n)
    mkpath(CASE_DIR)
    CSV.write(joinpath(CASE_DIR, name * ".csv"), DataFrame([row]))
    @printf("\n%-20s U=%.2f n=%d  mean F_x = %+.4f N/m (halves %+.4f / %+.4f; p %+.4f, v %+.4f)  wall %.0f s\n",
            name, U, n, row.Fx_mean, row.Fx_1st_half, row.Fx_2nd_half, row.Fpx_mean, row.Fvx_mean, row.wall_s)
    row
end

"Linear interpolation of the zero of y(x) (first sign change, y increasing or not)."
function zero_crossing(x, y)
    for i in 1:length(x)-1
        if sign(y[i]) != sign(y[i+1]) && isfinite(y[i]) && isfinite(y[i+1])
            return x[i] - y[i] * (x[i+1] - x[i]) / (y[i+1] - y[i]), i
        end
    end
    return NaN, 0
end

load_cases() = isdir(CASE_DIR) ?
    reduce(vcat, [CSV.read(joinpath(CASE_DIR, f), DataFrame) for f in readdir(CASE_DIR) if endswith(f, ".csv")]; init=DataFrame()) :
    DataFrame()

"U* from the flapping cases at resolution n -> (U*, bracket index into the sorted table)."
function ustar(tab, n)
    t = sort(tab[(tab.kind .== "flap") .& (tab.n .== n), :], :U)
    nrow(t) < 2 && return NaN, (NaN, NaN)
    u, i = zero_crossing(t.U, t.Fx_mean)
    return u, i == 0 ? (NaN, NaN) : (t.U[i], t.U[i+1])
end

function report()
    tab = load_cases()
    nrow(tab) == 0 && (println("no stage 3 cases found in $CASE_DIR"); return)
    sort!(tab, [:kind, :n, :U])
    CSV.write(joinpath(RESULTS_DIR, "stage3_inflow_sweep.csv"), tab)
    show(stdout, tab[:, [:case, :U, :n, :Fx_mean, :Fx_1st_half, :Fx_2nd_half, :Fpx_mean, :Fvx_mean,
                         :theta_pp, :switches_per_cycle, :steps, :wall_s]]; allrows=true, allcols=true)
    println()
    us = DataFrame(n=Int[], U_star=Float64[], U_lo=Float64[], U_hi=Float64[], monotonic=Bool[])
    for n in NS
        u, (lo, hi) = ustar(tab, n)
        t = sort(tab[(tab.kind .== "flap") .& (tab.n .== n), :], :U)
        mono = nrow(t) >= 2 && all(diff(t.Fx_mean) .> 0)
        nrow(t) >= 2 && push!(us, (n, u, lo, hi, mono))
        nrow(t) >= 2 && @printf("n = %d: U* = %.4f m/s (bracket %.2f–%.2f), net thrust decreases monotonically with U: %s\n",
                               n, u, lo, hi, mono ? "yes" : "NO")
    end
    CSV.write(joinpath(RESULTS_DIR, "stage3_Ustar.csv"), us)

    p = plot(xlabel="inflow U [m/s]", ylabel="mean F_x [N/m]  (> 0 drag, < 0 net thrust)",
             title="Stage 3: tethered fish, f = $(F_TAIL) Hz, Re_sim(U_REF) = $(round(Int, RE_SIM_DEFAULT))",
             legend=:topleft, size=(900, 600), xlims=(0, maximum(US) + 0.02))
    hline!(p, [0], c=:black, lw=0.5, label="")
    for (kind, n, mk, c) in (("flap", 128, :o, 1), ("flap", 256, :s, 2), ("rigid", 128, :d, 3), ("rigid", 256, :utriangle, 4))
        t = sort(tab[(tab.kind .== kind) .& (tab.n .== n), :], :U)
        nrow(t) == 0 && continue
        lbl = kind == "flap" ? "valve-driven tail, n = $n" : "rigid fish (drag), n = $n"
        plot!(p, t.U, t.Fx_mean, m=mk, c=c, label=lbl, ls=kind == "rigid" ? :dash : :solid)
    end
    for r in eachrow(us)
        isfinite(r.U_star) && vline!(p, [r.U_star], c=r.n == 128 ? 1 : 2, ls=:dot,
                                     label=@sprintf("U* = %.3f m/s (n = %d)", r.U_star, r.n))
    end
    savefig(p, joinpath(RESULTS_DIR, "stage3_inflow_sweep.png"))
    return tab, us
end

mode, cases = job_args(ALL)
mkpath(RESULTS_DIR)
if mode == :run
    foreach(run_case, cases)
elseif mode == :report
    report()
else    # everything, serially
    foreach(run_case, [casename(k, U, 128) for k in ("flap", "rigid") for U in US])
    tab, us = report()
    r = us[us.n .== 128, :]
    if nrow(r) == 1 && isfinite(r.U_star[1])
        foreach(run_case, [casename(k, U, 256) for k in ("flap", "rigid") for U in (r.U_lo[1], r.U_hi[1])])
        report()
    else
        println("no sign change at n = 128 – n = 256 bracket runs skipped")
    end
end
