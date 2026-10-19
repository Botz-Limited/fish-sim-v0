# Stage 0 – solver validation: 2D circular cylinder at Re = 100.
# Mean drag coefficient C_D and Strouhal number St at three resolutions.
# Pass criteria (spec): C_D 1.3–1.45 and St 0.15–0.18 at the finest resolution.
#
# Run from WaterLily/:  julia --project=. -t 4 scripts/stage0_validation.jl [D1 D2 D3]
# Output: results/stage0_validation.csv, results/stage0_validation.png,
#         results/stage0_D<D>_timeseries.csv
using WaterLily, StaticArrays, Statistics, Printf, DataFrames, CSV, Plots
using FishLily        # this project (WaterLily/Project.toml) is the FishLily package

const RE = 100
const DOM = (24, 12)          # domain [D]: 24D × 12D (blockage 1/12)
const XC = 6                  # cylinder centre 6D from the inlet
const T_END = 120.0           # convective times D/U
const T_AVG = 60.0            # average over t ≥ T_AVG (shedding fully developed)

function circle_sim(D; T=Float32)
    # the Units machinery is used with L_phys = D = 1, U_phys = U = 1: grid <-> "D, U" units
    u = Units(D; U=1.0, Re=RE, L_phys=1.0, U_phys=1.0)
    R = T(D / 2); c = SA[T(XC * D), T(DOM[2] * D / 2)]
    body = AutoBody((x, t) -> sqrt(sum(abs2, x .- c)) - R)
    sim = Simulation((DOM[1] * D, DOM[2] * D), (one(T), zero(T)), D;
                     U=one(T), ν=T(nu_grid(u)), body, T, exitBC=true)
    # asymmetric start: a small cross-flow kick behind the cylinder triggers shedding early
    xs = round(Int, (XC + 1) * D):round(Int, (XC + 3) * D)
    sim.flow.u[xs, :, 2] .= T(0.1)
    return sim, u
end

"Strouhal number from the lift signal: mean period between upward zero crossings."
function strouhal(t, cl)
    m = cl .- mean(cl)
    up = [t[i] - m[i] * (t[i+1] - t[i]) / (m[i+1] - m[i]) for i in 1:length(m)-1 if m[i] < 0 <= m[i+1]]
    length(up) < 3 && return NaN, 0
    return 1 / mean(diff(up)), length(up) - 1     # D = U = 1
end

function run_case(D)
    sim, u = circle_sim(D)
    case = "stage0_D$(D)"
    pr = Progress(case, T_END)
    t, cd, cl, cdp, cdv = Float64[], Float64[], Float64[], Float64[], Float64[]
    wall0 = time(); steps = 0
    while sim_time(sim) < T_END
        sim_step!(sim; remeasure=false)
        steps += 1
        f = body_force(sim); F = f.F
        push!(t, sim_time(sim))
        push!(cd, coefficient(u, F[1])); push!(cl, coefficient(u, F[2]))
        push!(cdp, coefficient(u, f.Fp[1])); push!(cdv, coefficient(u, f.Fv[1]))
        progress_update!(pr, t[end], steps; Cd=cd[end], Cl=cl[end])
    end
    wall = time() - wall0
    progress_finish!(pr, t[end], steps, "done")
    m = t .>= T_AVG
    tw = t[m]; dt = diff(tw)
    tmean(y) = sum(0.5 .* (y[m][1:end-1] .+ y[m][2:end]) .* dt) / sum(dt)
    CD, CDp, CDv = tmean(cd), tmean(cdp), tmean(cdv)
    St, ncyc = strouhal(tw, cl[m])
    CL_amp = (maximum(cl[m]) - minimum(cl[m])) / 2
    CSV.write(joinpath(RESULTS_DIR, "$(case)_timeseries.csv"), DataFrame(t=t, Cd=cd, Cl=cl, Cd_p=cdp, Cd_v=cdv))
    @printf("D = %3d: C_D = %.4f (pressure %.4f, viscous %.4f)  St = %.4f (%d cycles)  C_L amp = %.3f  steps = %d  wall = %.1f s\n",
            D, CD, CDp, CDv, St, ncyc, CL_amp, steps, wall)
    return (; D, cells=(DOM[1] * D) * (DOM[2] * D), C_D=CD, C_D_p=CDp, C_D_v=CDv, St, C_L_amp=CL_amp, cycles=ncyc,
            steps, wall_s=wall, t, cd, cl)
end

Ds = isempty(ARGS) ? [16, 32, 64] : parse.(Int, ARGS)
mkpath(RESULTS_DIR)
res = [run_case(D) for D in Ds]
tab = DataFrame([(; r.D, r.cells, r.C_D, r.C_D_p, r.C_D_v, r.St, r.C_L_amp, r.cycles, r.steps, r.wall_s) for r in res])
fin = res[end]
tab.pass_CD = [1.3 <= r.C_D <= 1.45 for r in res]
tab.pass_St = [0.15 <= r.St <= 0.18 for r in res]
CSV.write(joinpath(RESULTS_DIR, "stage0_validation.csv"), tab)
println(tab)
pass = 1.3 <= fin.C_D <= 1.45 && 0.15 <= fin.St <= 0.18
println(pass ? "STAGE 0 PASS" : "STAGE 0 FAIL", @sprintf(" (finest D = %d: C_D = %.3f in [1.3,1.45], St = %.3f in [0.15,0.18])",
                                                    fin.D, fin.C_D, fin.St))

p1 = plot(xlabel="t U/D", ylabel="C_D", title="Circle Re=100: drag", legend=:topright)
p2 = plot(xlabel="t U/D", ylabel="C_L", title="lift", legend=:topright)
for r in res
    plot!(p1, r.t, r.cd, label="D=$(r.D)", lw=1)
    plot!(p2, r.t, r.cl, label="D=$(r.D)", lw=1)
end
hspan!(p1, [1.3, 1.45], alpha=0.15, c=:green, label="pass band")
ylims!(p1, 0.8, 2.0)
ylims!(p2, -0.6, 0.6)                    # the start-up kick gives a large initial C_L spike
p3 = plot([r.D for r in res], [r.C_D for r in res], m=:o, xlabel="D [cells]", ylabel="C_D", label="C_D", legend=:bottomright)
hspan!(p3, [1.3, 1.45], alpha=0.15, c=:green, label="pass")
p4 = plot([r.D for r in res], [r.St for r in res], m=:o, xlabel="D [cells]", ylabel="St", label="St", legend=:bottomright)
hspan!(p4, [0.15, 0.18], alpha=0.15, c=:green, label="pass")
plot(p1, p2, p3, p4, layout=(2, 2), size=(1100, 750))
savefig(joinpath(RESULTS_DIR, "stage0_validation.png"))
