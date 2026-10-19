# Stage 6 – two-way coupled tail: hydraulics + tail ODE + WaterLily fluid load.
#
#   J·θ̈ + c·θ̇ + k_e·θ = A_r·Δp + M_fluid,   Δp = clip((V_p − A_r·θ)/C_h, ±p_max)
#
# (model, stabilisation and parameters: scripts/lib_coupled.jl; spec section 3.3)
#
# Run from WaterLily/ (still water, tethered fish, as stage 2):
#   N=64  julia --project=. -t 2 scripts/stage6_coupled.jl ident [f=2.0] [θ0=0.3]
#         (a) prescribed sine θ = θ0 sin 2πft -> fit M_fluid = −J_a θ̈ − c_a θ̇ − k_a θ + m0
#   N=128 julia --project=. -t 2 scripts/stage6_coupled.jl coupled 2.0
#         (b) coupled run at f (uses J_a from results/stage6_ident_n<N>.csv, else n=128; or env IDENT_FILE)
#   N=128 julia --project=. -t 2 scripts/stage6_coupled.jl kin 2.0
#         kinematic-mode CFD run (θ = V_p/A_r) for the M_fluid comparison (optional)
# Env: N (cells per L_BODY, default 64), T_END [s] (default 3 ident / 5 coupled),
#      COUPLE_FORCE = gen (default, generalized force) | root (tail_pressure_moment),
#      JA_SCALE (multiplies the J_a estimate; stabilisation-robustness test, default 1),
#      FISH_LIVE=1 live GLMakie viewer (opened by run_fish!, viz/FishLive.jl; FISH_LIVE_KEEP=1 keeps the window).
# Outputs: results/stage6_*.csv / .png
using WaterLily, StaticArrays, Statistics, Printf, DataFrames, CSV, Plots
using FishLily
include(joinpath(@__DIR__, "lib_coupled.jl"))

const N = parse(Int, get(ENV, "N", "64"))
const T_TRANS = 2.0           # [s] valve start-up transient, discarded in averages (NOTES 8)
const P = VALVE

ident_file(n) = joinpath(RESULTS_DIR, "stage6_ident_n$(n).csv")
tag(f) = @sprintf("f%.1f_n%d", f, N)

# ------------------------------------------------------------------------------ (a)
function run_ident(f=2.0, θ0=0.3)
    t_end = parse(Float64, get(ENV, "T_END", "3.0"))
    T1 = 1 / f
    # fundamental + 3rd harmonic (like the valve's triangle-ish θ): a pure sine makes
    # θ̈ = −ω²θ collinear with θ, so J_a and a stiffness term k_a could not be separated
    a3 = parse(Float64, get(ENV, "H3", "0.25"))
    θfun(t) = (t < T1 ? 0.5 * (1 - cos(π * t / T1)) : 1.0) * θ0 *
              ((1 - a3) * sin(2π * f * t) + a3 * sin(6π * f * t))
    case = "stage6_ident_" * tag(f)
    fs = make_fish_sim(; n=N, U_in=0.0, name=case, box=get(ENV, "BOX", "1") == "1")
    d = IdentDriver(θfun)
    wall0 = time()
    df = run_fish!(fs, t_end; driver=d, case, on_frame=live_hook(fs, t_end))
    wall = time() - wall0
    df.M_gen = d.Qgen
    # analytic θ̇, θ̈ at t1 (for comparison with the CFD-seen finite differences)
    df.thd = [ForwardDiffDeriv(θfun, t, 1) for t in df.t]
    df.thdd = [ForwardDiffDeriv(θfun, t, 2) for t in df.t]
    save_csv(df, case * "_timeseries")
    m = df.t .>= T1 + 0.25          # after the ramp
    res = NamedTuple[]
    for (lab, col) in (("gen", :M_gen), ("root", :M)), (alab, acol, vcol) in (("cfd", :a_cfd, :rate), ("analytic", :thdd, :thd)),
        withk in (false, true)
        X = hcat(-df[m, acol], -df[m, vcol], withk ? -df[m, :θ] : zeros(count(m)), ones(count(m)))
        withk || (X = X[:, [1, 2, 4]])
        y = df[m, col]
        β = X \ y
        withk || (β = [β[1], β[2], 0.0, β[3]])
        Xf = hcat(-df[m, acol], -df[m, vcol], -df[m, :θ], ones(count(m)))
        r2 = 1 - sum(abs2, y - Xf * β) / sum(abs2, y .- mean(y))
        push!(res, (; force=lab, accel=alab, model=withk ? "J_a,c_a,k_a" : "J_a,c_a", J_a_2D=β[1], c_a_2D=β[2],
                    k_a_2D=β[3], m0_2D=β[4], R2=r2))
        @printf("%-4s %-8s %-11s J_a=%.4g kg·m (2D)  c_a=%.4g kg·m/s  k_a=%.4g N  R²=%.3f\n", lab, alab,
                res[end].model, β[1], β[2], β[3], r2)
    end
    tab = DataFrame(res)
    tab.n .= N; tab.f .= f; tab.θ0 .= θ0; tab.h3 .= a3; tab.wall_s .= wall; tab.steps .= df.step[end]
    tab.J_a_3D = tab.J_a_2D .* B_EFF; tab.c_a_3D = tab.c_a_2D .* B_EFF
    CSV.write(ident_file(N), tab)
    # plot: measured vs fitted (generalized force, cfd accel)
    r = res[1]
    fit = -r.J_a_2D .* df.a_cfd .- r.c_a_2D .* df.rate .- r.k_a_2D .* df.θ .+ r.m0_2D
    p1 = plot(df.t, df.M_gen, label="Q_θ measured (2D)", xlabel="t [s]", ylabel="N·m/m", lw=1,
              title=@sprintf("prescribed θ = %.2f(%.2f sin ωt + %.2f sin 3ωt), f=%.1f Hz, n=%d", θ0, 1 - a3, a3, f, N))
    plot!(p1, df.t, fit, label=@sprintf("fit: J_a=%.3g, c_a=%.3g", r.J_a_2D, r.c_a_2D), ls=:dash)
    plot!(p1, df.t, df.M, label="M_root measured (2D)", lw=1, alpha=0.6)
    p2 = scatter(df.a_cfd[m], df.M_gen[m] .+ r.c_a_2D .* df.rate[m] .+ r.k_a_2D .* df.θ[m], ms=1.5,
                 xlabel="θ̈ seen by CFD [rad/s²]", ylabel="Q_θ + c_a θ̇ + k_a θ [N·m/m]", label="")
    plot!(p2, sort(df.a_cfd[m]), -r.J_a_2D .* sort(df.a_cfd[m]) .+ r.m0_2D, label="−J_a θ̈", lw=2)
    plot(p1, p2, layout=(1, 2), size=(1400, 450), margin=5Plots.mm)
    savefig(joinpath(RESULTS_DIR, case * ".png"))
    @printf("ident wall %.1f s, %d steps\n", wall, df.step[end])
    return tab
end

# derivative of a scalar function by complex-step-free central differences (θfun is smooth)
function ForwardDiffDeriv(fun, t, k; h=1e-4)
    k == 1 ? (fun(t + h) - fun(t - h)) / 2h : (fun(t + h) - 2fun(t) + fun(t - h)) / h^2
end

function load_Ja()
    file = get(ENV, "IDENT_FILE", isfile(ident_file(N)) ? ident_file(N) : ident_file(128))
    isfile(file) || error("no identification file; run `ident` first")
    tab = CSV.read(file, DataFrame)
    fl = get(ENV, "COUPLE_FORCE", "gen")
    row = tab[(tab.force .== fl) .& (tab.accel .== "cfd") .& (tab.model .== "J_a,c_a"), :][1, :]
    return row.J_a_2D, row.c_a_2D, file
end

kin_series(f, t_end) = valve_series(f, t_end + 0.1; p=P)

# ------------------------------------------------------------------------------ (b)
function run_coupled(f=2.0)
    t_end = parse(Float64, get(ENV, "T_END", "5.0"))
    force = Symbol(get(ENV, "COUPLE_FORCE", "gen"))
    jas = parse(Float64, get(ENV, "JA_SCALE", "1.0"))
    Ja2, ca2, file = load_Ja()
    tail = TailParams()
    J_a = jas * Ja2 * tail.b_eff
    sfx = (force === :gen ? "" : "_root") * (jas == 1 ? "" : @sprintf("_Ja%.2g", jas)) * (get(ENV, "BOX", "1") == "1" ? "" : "_nobox")
    case = "stage6_coupled_" * tag(f) * sfx
    @printf("J = %.3g kg·m², J_a = %.3g kg·m² (from %s, ×%.2g), k_e = %.2g, k_h = %.2g N·m/rad, c = %.3g, b_eff = %.3g m\n",
            tail.J, J_a, basename(file), jas, tail.k_e, P.A_r^2 / P.C_h, tail.c, tail.b_eff)
    ωn = sqrt((P.A_r^2 / P.C_h + tail.k_e) / (tail.J + J_a))
    @printf("coupled natural frequency (no fluid damping) %.2f Hz\n", ωn / 2π)
    fs = make_fish_sim(; n=N, U_in=0.0, name=case, box=get(ENV, "BOX", "1") == "1")
    d = CoupledDriver(f; tail, J_a, force)
    wall0 = time(); status = "stable"; err = nothing
    df = try
        run_fish!(fs, t_end; driver=d, case, on_frame=live_hook(fs, t_end))
    catch e
        status = "diverged"; err = sprint(showerror, e); @warn "run failed" err
        nothing
    end
    wall = time() - wall0
    if df === nothing
        lg = DataFrame(d.log, [:t, :θ, :dp, :M_2D, :Fx])
        save_csv(lg, case * "_partial_timeseries")
        # growth of θ: half amplitude per cycle up to the failure
        g = [let m = (lg.t .>= (i - 1) / f) .& (lg.t .< i / f); any(m) ? (maximum(lg.θ[m]) - minimum(lg.θ[m])) / 2 : NaN end
             for i in 1:ceil(Int, lg.t[end] * f)]
        @printf("failed at t=%.4f s after %d steps; θ half-amplitude per cycle: %s\n", lg.t[end], nrow(lg),
                join([@sprintf("%.3f", x) for x in g], " "))
        println("last 8 logged steps:"); show(stdout, last(lg, 8)); println()
        res = (; case, f, n=N, status, err, fail_t=lg.t[end], steps=nrow(lg), n_reject=d.n_reject, wall_s=wall)
        file = joinpath(RESULTS_DIR, "stage6_coupled_runs.csv")
        tab = isfile(file) ? CSV.read(file, DataFrame) : DataFrame()
        nrow(tab) > 0 && (tab = tab[tab.case .!= case, :])
        CSV.write(file, vcat(tab, DataFrame([res]); cols=:union))
        return res
    end
    vs = kin_series(f, t_end)
    df.θ_kin = [interp1(vs.t, vs.V_p, t) / P.A_r for t in df.t]
    # recompute the logged fluid load series: M_rest = M_meas,prev + J_a a_prev  ⇒  M_meas,k = M_rest,k+1 − J_a a_k
    Mm = similar(df.θ); Mm .= NaN
    for k in 1:nrow(df)-1
        Mm[k] = df.M_rest[k+1] - J_a * df.a_cfd[k]
    end
    df.M_fluid_3D = Mm
    df.M_root_3D = tail.b_eff .* df.M
    save_csv(df, case * "_timeseries")
    res = analyse(df, f, d, wall, case, status, J_a)
    plot_run(df, f, res, case)
    return res
end

function analyse(df, f, d, wall, case, status, J_a)
    t = df.t
    Aθ, Ak = halfpp(t, df.θ; t_from=T_TRANS), halfpp(t, df.θ_kin; t_from=T_TRANS)
    zθ, zk = fundamental(t, df.θ, f; t_from=T_TRANS), fundamental(t, df.θ_kin, f; t_from=T_TRANS)
    lag = rad2deg(angle(zk / zθ))            # > 0: θ lags θ_kin
    m = t .>= T_TRANS
    # growth: ratio of θ half-amplitude in the last cycle vs the first cycle after the transient
    cyc(i) = (t .>= T_TRANS + (i - 1) / f) .& (t .< T_TRANS + i / f)
    ncyc = floor(Int, (t[end] - T_TRANS) * f)
    amp(i) = (maximum(df.θ[cyc(i)]) - minimum(df.θ[cyc(i)])) / 2
    growth = ncyc >= 2 ? log(amp(ncyc) / amp(1)) / ((ncyc - 1) / f) : NaN
    relief = (df.t_relief[end] - interp1(t, df.t_relief, T_TRANS)) / (t[end] - T_TRANS)
    res = (; case, f, n=N, status, J_a=J_a, J=d.tail.J, k_e=d.tail.k_e, b_eff=d.tail.b_eff,
           theta_amp=Aθ, theta_kin_amp=Ak, amp_ratio=Aθ / Ak, theta1_amp=abs(zθ), theta1_kin_amp=abs(zk),
           amp1_ratio=abs(zθ) / abs(zk), phase_lag_deg=lag,
           theta_mean=cycle_mean(df, :θ; t_from=T_TRANS), dp_max_kPa=maximum(abs.(df.dp[m])) / 1e3,
           dp_rms_kPa=sqrt(cycle_mean(transform(df, :dp => ByRow(abs2) => :dp2), :dp2; t_from=T_TRANS)) / 1e3,
           relief_open_frac=relief, V_vent_total_ml=df.V_vent[end] * 1e6,
           M_fluid_rms=sqrt(mean(abs2, filter(isfinite, df.M_fluid_3D[m]))),
           thrust_mean=cycle_mean(df, :thrust; t_from=T_TRANS), growth_rate_per_s=growth,
           switches_per_cycle=switches_per_cycle(t, df.s, f; t_from=T_TRANS), n_reject=d.n_reject,
           steps=df.step[end], wall_s=wall)
    for (k, v) in pairs(res)
        v isa AbstractFloat ? @printf("  %-20s %.4g\n", k, v) : println("  ", rpad(k, 20), " ", v)
    end
    file = joinpath(RESULTS_DIR, "stage6_coupled_runs.csv")
    tab = isfile(file) ? CSV.read(file, DataFrame) : DataFrame()
    nrow(tab) > 0 && (tab = tab[tab.case .!= case, :])
    tab = vcat(tab, DataFrame([res]); cols=:union)
    CSV.write(file, tab)
    return res
end

function plot_run(df, f, res, case)
    t = df.t
    p1 = plot(t, df.θ_kin, label="kinematic θ = V_p,valve/A_r", c=:gray, ls=:dash, ylabel="θ [rad]",
              title=@sprintf("%s: amp %.3f vs kin %.3f rad (×%.2f), lag %.0f°", case, res.theta_amp,
                             res.theta_kin_amp, res.amp_ratio, res.phase_lag_deg), titlefontsize=9)
    plot!(p1, t, df.θ, label="coupled θ", c=:blue)
    vspan!(p1, [0, T_TRANS], c=:gray, alpha=0.1, label="transient")
    p2 = plot(t, df.dp ./ 1e3, label="Δp", ylabel="Δp [kPa]", c=:red)
    hline!(p2, [-1, 1] .* P.p_max / 1e3, ls=:dot, c=:black, label="±p_max")
    p3 = plot(t, df.M_fluid_3D, label="M_fluid (3D = b_eff·2D, used)", ylabel="N·m", c=:green, lw=1)
    plot!(p3, t, df.M_root_3D, label="root moment ×b_eff", c=:orange, lw=1, alpha=0.6)
    plot!(p3, t, P.A_r .* df.dp, label="A_r·Δp", c=:red, lw=1, alpha=0.5)
    p4 = plot(t, df.thrust, label="thrust (2D) [N/m]", xlabel="t [s]", ylabel="N/m", c=:purple, lw=1)
    plot(p1, p2, p3, p4, layout=(4, 1), size=(1200, 1100), margin=4Plots.mm, legend=:topright)
    savefig(joinpath(RESULTS_DIR, case * ".png"))
end

# ------------------------------------------------------------------------------ kinematic CFD reference
function run_kin(f=2.0)
    t_end = parse(Float64, get(ENV, "T_END", "5.0"))
    vs = kin_series(f, t_end)
    θk(t) = interp1(vs.t, vs.V_p, t) / P.A_r
    case = "stage6_kin_" * tag(f)
    fs = make_fish_sim(; n=N, U_in=0.0, name=case, box=get(ENV, "BOX", "1") == "1")
    d = IdentDriver(θk)
    wall0 = time()
    df = run_fish!(fs, t_end; driver=d, case, on_frame=live_hook(fs, t_end))
    wall = time() - wall0
    df.M_gen = d.Qgen
    df.M_fluid_3D = B_EFF .* d.Qgen
    save_csv(df, case * "_timeseries")
    @printf("kin %s: thrust mean %.4g N/m, M_fluid_3D rms %.4g N·m, wall %.1f s\n", case,
            cycle_mean(df, :thrust; t_from=T_TRANS), sqrt(mean(abs2, df.M_fluid_3D[df.t .>= T_TRANS])), wall)
end

mode = isempty(ARGS) ? "ident" : ARGS[1]
fa = length(ARGS) >= 2 ? parse(Float64, ARGS[2]) : 2.0
mkpath(RESULTS_DIR)
if mode == "ident"
    run_ident(fa, length(ARGS) >= 3 ? parse(Float64, ARGS[3]) : 0.3)
elseif mode == "coupled"
    run_coupled(check_freq(fa))
elseif mode == "kin"
    run_kin(check_freq(fa))
else
    error("unknown mode $mode (ident | coupled | kin)")
end
