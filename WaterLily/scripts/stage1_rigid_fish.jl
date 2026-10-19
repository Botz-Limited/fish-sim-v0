# Stage 1 – rigid (straight) fish in a uniform inflow U_REF at Re_sim.
# Drag coefficient C_D = F_x/(½ ρ U_REF² L_BODY) vs resolution n = 64/128/256
# cells per body length, plus one run in a larger domain (boundary effect).
# Pass criterion (spec): C_D change < 5 % between the two finest resolutions.
#
# Run from WaterLily/:  julia --project=. -t 4 scripts/stage1_rigid_fish.jl [case names...]
# Diagnostic: RE_SIM=1000 julia ... runs at another Re_sim (outputs get a _Re1000 suffix).
# Output: results/stage1_rigid_fish.csv/.png, results/stage1_<case>_timeseries.csv,
#         live progress in results/progress/stage1_*.json
using WaterLily, Statistics, Printf, DataFrames, CSV, Plots
using FishLily        # this project (WaterLily/Project.toml) is the FishLily package

const T_CONV = L_BODY / U_REF          # one convective time [s] (1.05 s)
const T_END = 8 * T_CONV               # [s]  PLACEHOLDER – long enough for a periodic wake
const T_AVG = 4 * T_CONV               # average over t ≥ T_AVG

const RE = parse(Float64, get(ENV, "RE_SIM", string(RE_SIM_DEFAULT)))
const SUFFIX = RE == RE_SIM_DEFAULT ? "" : "_Re$(round(Int, RE))"

const LARGE = DomainParams(upstream=3.0, downstream=8.0, side=3.0)

function run_case(name, n, domain)
    fs = make_fish_sim(; n, U_in=U_REF, domain, name, Re=RE)
    # small cross-flow kick in the near wake (same physical region for every n)
    # so that a possible wake instability starts at the same time on every grid
    u = fs.units
    x0 = round(Int, fs.origin[1] + to_grid(u, :length, L_TAIL + 0.02))
    x1 = round(Int, fs.origin[1] + to_grid(u, :length, L_TAIL + 0.10))
    fs.sim.flow.u[x0:x1, :, 2] .= 0.05f0
    wall0 = time()
    df = run_fish!(fs, T_END; case=name, moment=false, log_every=4)
    wall = time() - wall0
    CSV.write(joinpath(RESULTS_DIR, "$(name)_timeseries.csv"), df)
    Cd = cycle_mean(df, :Cx; t_from=T_AVG)
    sc = 1 / (0.5 * RHO * U_REF^2 * L_BODY)
    Cdp = cycle_mean(df, :Fpx; t_from=T_AVG) * sc
    Cdv = cycle_mean(df, :Fvx; t_from=T_AVG) * sc
    m = df.t .>= T_AVG
    Cl_amp = (maximum(df.Fy[m]) - minimum(df.Fy[m])) / 2 * sc
    dims = size(fs.sim.flow.p) .- 2
    @printf("%-22s n=%3d dims=%s  C_D=%.4f (p %.4f, v %.4f)  C_L amp=%.4f  steps=%d  wall=%.1f s\n",
            name, n, dims, Cd, Cdp, Cdv, Cl_amp, df.step[end], wall)
    return (; case=name, n, Nx=dims[1], Ny=dims[2], domain=string(domain.upstream, "/", domain.downstream, "/", domain.side),
            C_D=Cd, C_D_p=Cdp, C_D_v=Cdv, C_L_amp=Cl_amp, steps=df.step[end], wall_s=wall), df
end

cases = [("stage1_n64" * SUFFIX, 64, DOMAIN), ("stage1_n128" * SUFFIX, 128, DOMAIN), ("stage1_n256" * SUFFIX, 256, DOMAIN),
         ("stage1_n128_large" * SUFFIX, 128, LARGE)]
sel = isempty(ARGS) ? cases : filter(c -> c[1] in ARGS, cases)
mkpath(RESULTS_DIR)
out = [run_case(c...) for c in sel]
tab = DataFrame([o[1] for o in out])
CSV.write(joinpath(RESULTS_DIR, "stage1_rigid_fish$(SUFFIX).csv"), tab)
println(tab)

get_cd(name) = (i = findfirst(==(name), tab.case); i === nothing ? NaN : tab.C_D[i])
c128, c256, cL = get_cd("stage1_n128" * SUFFIX), get_cd("stage1_n256" * SUFFIX), get_cd("stage1_n128_large" * SUFFIX)
dres = abs(c256 - c128) / abs(c256)
ddom = abs(cL - c128) / abs(cL)
@printf("C_D change n=128 -> 256: %.2f %% (criterion < 5 %%): %s\n", 100dres, dres < 0.05 ? "PASS" : "FAIL")
@printf("C_D change domain default -> large (n=128): %.2f %% (reported)\n", 100ddom)

p1 = plot(xlabel="t [s]", ylabel="C_D (on L_BODY, U_REF)", title="Rigid fish, Re_sim = $(round(Int, RE))")
for (o, df) in out
    plot!(p1, df.t, df.Cx, label=o.case, lw=1)
end
vline!(p1, [T_AVG], c=:gray, ls=:dash, label="averaging from")
ns = [o[1].n for o in out if o[1].domain == string(DOMAIN.upstream, "/", DOMAIN.downstream, "/", DOMAIN.side)]
cds = [o[1].C_D for o in out if o[1].domain == string(DOMAIN.upstream, "/", DOMAIN.downstream, "/", DOMAIN.side)]
p2 = plot(ns, cds, m=:o, xscale=:log2, xticks=(ns, string.(ns)), xlabel="n (cells per L_BODY)",
          ylabel="mean C_D", label="default domain", legend=:topright)
isfinite(cL) && scatter!(p2, [128], [cL], m=:diamond, label="large domain")
dd = [o[1] for o in out if o[1].domain == string(DOMAIN.upstream, "/", DOMAIN.downstream, "/", DOMAIN.side)]
p3 = plot(ns, [d.C_D_p for d in dd], m=:o, xscale=:log2, xticks=(ns, string.(ns)), label="pressure part",
          xlabel="n (cells per L_BODY)", ylabel="C_D part", legend=:right, ylims=(0, :auto))
plot!(p3, ns, [d.C_D_v for d in dd], m=:s, label="viscous part")
hline!(p3, [2 * 1.328 / sqrt(RE)], ls=:dash, c=:gray, label="Blasius plate, both sides")
plot(p1, p2, p3, layout=(1, 3), size=(1600, 450), margin=5Plots.mm)
savefig(joinpath(RESULTS_DIR, "stage1_rigid_fish$(SUFFIX).png"))
