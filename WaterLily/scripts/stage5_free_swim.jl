# Stage 5 – free swimming, 1-DOF surge, still water (spec 3.4).
#
# The fish starts at rest in a closed box of still water (slip walls, U_in = 0), the valve
# drives the tail at f = 2 Hz (kinematic mode, θ = V_p/A_r), and the body x-position X(t)
# is integrated from the fluid force on the body. The body moves through the grid via the
# AutoBody map (`make_fish_sim(; X=Track())`), the inflow is NOT changed.
#
# Signs (all in the fixed lab/grid frame, x to the right):
#   - The fish points to −x (nose at x = −HEAD_A of the body frame), so it swims towards −x.
#   - X(t) [m] = x-offset of the body (tail root) from its start position; X < 0 when swimming.
#   - u = dX/dt [m/s] (lab frame, < 0 when swimming); U_swim = −u > 0 is the swimming speed.
#   - Fx = x-force ON THE BODY from `readouts` (`body_force`), positive in +x. The same
#     quantity as the "drag" Fx of stages 1–3 (inflow +x), so thrust = −Fx; when the fish
#     moves forward (u < 0) its drag points to +x. Equation of motion: m·dX²/dt² = Fx.
#   - m = ρ·A, A = 2D section area of the straight fish (from the SDF), neutrally buoyant.
#
# Coupling: explicit, the force of the previous CFD step drives the current step
# (symplectic Euler: u₁ = u₀ + a·Δt, X₁ = X₀ + u₁·Δt; the body `Track` X(t) is linear over
# the step with rate u₁, so the body position and velocity seen by WaterLily are consistent).
# The measured force already contains the surge added-mass reaction −m_a·a, so the explicit
# scheme has the amplification factor −m_a/m ≈ −0.16 for this slender body (m_a ≈ ρπb²,
# b = T_ROOT/2) – stable. Optional semi-implicit form (env ADDED_MASS=1):
#   (m + m_a)·a_n = Fx_{n−1} + m_a·a_{n−1}
# which cancels the added-mass part of the lagged force to first order.
#
# Domain: closed box, long upstream (in front of the nose, −x) so the fish can swim several
# body lengths before reaching the wall (no recentring). The run stops early (warning, the
# progress file then says "failed") if the nose gets within WALL_MARGIN body lengths of the wall.
#
# Run from WaterLily/:  julia --project=. -t 2 scripts/stage5_free_swim.jl
#   env: N (128), T_END [s] (8.0), F_TAIL [Hz] (2.0), UPSTREAM [L] (auto), DT_MAX (0.4),
#        ADDED_MASS (0/1), FISH_LIVE (0/1: live viewer), CASE (name suffix)
# Output: results/stage5_free_swim<suffix>.csv/.png/.log, live progress in
#         results/progress/stage5_free_swim<suffix>.json
using WaterLily, Statistics, Printf, DataFrames, CSV, Plots
using FishLily

const N = parse(Int, get(ENV, "N", "128"))
const T_END = parse(Float64, get(ENV, "T_END", "8.0"))           # [s] physical time
const F_TAIL = check_freq(parse(Float64, get(ENV, "F_TAIL", "2.0")))  # [Hz] valve range 1.5–2.5
const DT_MAX = parse(Float64, get(ENV, "DT_MAX", "0.4"))         # [cells/U] Δt cap
const ADDED_MASS = get(ENV, "ADDED_MASS", "0") == "1"
# Force glitch guard [N/m]: at n = 128 the pressure force has rare ONE-step spikes of
# 10³–10⁵ N/m (both Fx and Fy, also with the full-domain measure and with dt_max = 0.2, so
# not the box measure and not the explicit coupling – the spike appears while u is still
# smooth). Fed to the body they kick it to −1…+3 m/s. Physical peaks (valve switches,
# added mass) are ≤ ≈ 40 N/m, so |Fx| > FX_GUARD is treated as a glitch: the body keeps the
# previous force for that step (counted, column `rejected`). The fluid itself still sees it.
const FX_GUARD = parse(Float64, get(ENV, "FX_GUARD", "100.0"))
const T_TRANSIENT = 2.0      # [s] valve start-up transient, discarded in averages (NOTES 8)
const N_AVG_CYCLES = 4       # steady speed = mean over the last whole cycles
const WALL_MARGIN = 0.5      # [L_BODY] stop when the nose is this close to the front wall
# Swimming distance budget: the n = 64 run reached a steady U ≈ 0.36 m/s after ≈ 2.5 s and swam
# 13.5 L_BODY in 9 s, so the front wall is put 1.5 L + 0.37 m/s · T_END ahead of the nose.
const U_EST = 0.37           # [m/s] upper estimate of the swimming speed (from the n = 64 run)
const UPSTREAM = parse(Float64, get(ENV, "UPSTREAM", string(round(1.5 + U_EST * T_END / L_BODY; digits=1))))
const DOMAIN5 = DomainParams(upstream=UPSTREAM, downstream=1.5, side=1.5)
const CASE = "stage5_free_swim" * (N == 128 ? "" : "_n$N") * get(ENV, "CASE", "")

# --- mass: 2D section area from the SDF ------------------------------------------------
"Area [m²] of the straight fish section, by sampling the SDF on a fine grid (cell h [m])."
function section_area(; h=1e-4)
    g = FishGeom(Float64)
    xs = (-HEAD_A + h/2):h:L_TAIL
    ys = (-T_ROOT/2 + h/2):h:(T_ROOT/2)
    h^2 * count(fish_sdf_straight(g, x, y) < 0 for x in xs, y in ys)
end
const AREA = section_area()
const MASS = RHO * AREA                      # [kg/m] per unit span, neutrally buoyant
const M_ADDED = RHO * π * (T_ROOT / 2)^2     # [kg/m] surge added mass estimate ρπb²

# --- free-swimming driver --------------------------------------------------------------
mutable struct FreeSwimDriver <: AbstractDriver
    valve::ValveDriver
    m::Float64        # body mass [kg/m]
    m_a::Float64      # added mass used semi-implicitly [kg/m] (0 = plain explicit)
    X::Float64        # [m]
    u::Float64        # [m/s] dX/dt
    a::Float64        # [m/s²] acceleration used in the last step
    F_prev::Float64   # [N/m] Fx on the body after the last step
    X_stop::Float64   # [m] stop (WallReached) when X < X_stop
    pending::NamedTuple
    log::Vector{NamedTuple}   # own log, so the data survive an early stop
    n_rejected::Int           # steps whose force was rejected by the glitch guard
end
FreeSwimDriver(f; m=MASS, m_a=0.0, X_stop=-Inf) =
    FreeSwimDriver(ValveDriver(f), m, m_a, 0.0, 0.0, 0.0, 0.0, X_stop, (;), NamedTuple[], 0)
struct WallReached <: Exception
    t::Float64
end

function FishLily.drive!(d::FreeSwimDriver, fs, t0, t1)
    cols = drive!(d.valve, fs, t0, t1)           # sets fs.theta for this step
    dt = t1 - t0
    a = (d.F_prev + d.m_a * d.a) / (d.m + d.m_a) # explicit (m_a = 0) or semi-implicit
    u1 = d.u + a * dt
    X1 = d.X + u1 * dt
    set_track!(fs.X, t0, d.X, t1, X1)
    d.X, d.u, d.a = X1, u1, a
    d.pending = merge(cols, (; X=X1, u=u1, U_swim=-u1, a, F_used=d.F_prev))
    return d.pending
end
function FishLily.observe!(d::FreeSwimDriver, fs, t1, r)
    # glitch guard (see header): a non-physical one-step pressure spike is not fed to the body
    rejected = abs(r.Fx) > FX_GUARD
    rejected ? (d.n_rejected += 1) : (d.F_prev = r.Fx)
    push!(d.log, merge((; t=t1), d.pending, r, (; rejected)))
    d.X < d.X_stop && throw(WallReached(t1))
    nothing
end

# --- live viewer (FISH_LIVE=1) -----------------------------------------------------------
# TODO: switch to the FISH_LIVE helper once it is documented at the end of viz/README.md.
function live_hook(fs)
    get(ENV, "FISH_LIVE", "0") == "1" || return nothing
    @warn "FISH_LIVE=1: live-viewer helper not available yet in viz/ (see viz/README.md), running without it"
    return nothing
end

# --- run -------------------------------------------------------------------------------
const BOX = get(ENV, "BOX", "1") == "1"     # box-restricted body measurement (src default); BOX=0 = full domain
fs = make_fish_sim(; n=N, U_in=0.0, domain=DOMAIN5, X=Track(), name=CASE, box=BOX)
dims = size(fs.sim.flow.p) .- 2
x_wall_nose = -(UPSTREAM - WALL_MARGIN) * L_BODY    # X at which the nose is WALL_MARGIN from the wall
drv = FreeSwimDriver(F_TAIL; m_a=ADDED_MASS ? M_ADDED : 0.0, X_stop=x_wall_nose)
@printf("%s: n=%d grid %s, upstream %.1f L, f=%.2f Hz, T_END=%.1f s\n", CASE, N, dims, UPSTREAM, F_TAIL, T_END)
@printf("area A=%.4e m², m=ρA=%.3f kg/m, m_a≈ρπb²=%.3f kg/m (m_a/m=%.3f), coupling: %s\n",
        AREA, MASS, M_ADDED, M_ADDED / MASS, ADDED_MASS ? "semi-implicit added mass" : "explicit")

hook = live_hook(fs)
wall0 = time()
try
    run_fish!(fs, T_END; driver=drv, case=CASE, moment=false, log_every=1, dt_max=DT_MAX,
              on_frame=hook, frame_every=5)
catch err
    err isa WallReached || rethrow(err)
    @warn @sprintf("nose within %.1f L of the front wall at t=%.2f s, run stopped early", WALL_MARGIN, err.t)
end
wall = time() - wall0
df = DataFrame(drv.log)
df.step = 1:nrow(df)
df.X_L = df.X ./ L_BODY
df.tip = tail_tip_displacement.(df.θ)

# --- analysis --------------------------------------------------------------------------
T = 1 / F_TAIL
t_last = df.t[end]
n_cyc = floor(Int, t_last * F_TAIL + 1e-6)
"time-weighted mean of column `col` over [ta, tb]"
wmean(col, ta, tb) = (m = (df.t .>= ta) .& (df.t .<= tb); cycle_mean(df[m, :], col; t_from=ta))
# per-cycle means (cycle k = [(k-1)T, kT])
cyc_t = [(k - 0.5) * T for k in 1:n_cyc]
cyc_U = [wmean(:U_swim, (k - 1) * T, k * T) for k in 1:n_cyc]
cyc_F = [wmean(:Fx, (k - 1) * T, k * T) for k in 1:n_cyc]
k_avg = max(1, min(N_AVG_CYCLES, n_cyc - ceil(Int, T_TRANSIENT * F_TAIL)))
ta, tb = (n_cyc - k_avg) * T, n_cyc * T
U_steady = wmean(:U_swim, ta, tb)
U_prev = n_cyc - 2k_avg >= 0 ? wmean(:U_swim, (n_cyc - 2k_avg) * T, ta) : NaN   # drift check
m_avg = (df.t .>= ta) .& (df.t .<= tb)
A_tip = maximum(df.tip[m_avg]) - minimum(df.tip[m_avg])         # peak-to-peak tip excursion [m]
St = F_TAIL * A_tip / U_steady
Fx_mean = wmean(:Fx, ta, tb)

# stage 3 U* (another script); generic reader: a column named U_star/Ustar, or the sign change of F_x(U)
function stage3_ustar()
    files = filter(f -> startswith(f, "stage3_") && endswith(f, ".csv"), readdir(RESULTS_DIR))
    for f in files
        d = CSV.read(joinpath(RESULTS_DIR, f), DataFrame)
        for c in names(d)
            if lowercase(replace(c, "_" => "", "*" => "star")) in ("ustar", "ustarms")
                v = filter(isfinite, collect(skipmissing(d[!, c])))
                isempty(v) || return (Float64(v[1]), f, c)
            end
        end
    end
    return nothing
end
us = stage3_ustar()

io = IOBuffer()
@printf(io, "%s  n=%d grid=%s  f=%.2f Hz  t_end=%.2f s  steps=%d  wall=%.0f s (%.1f s per phys. s)\n",
        CASE, N, dims, F_TAIL, t_last, nrow(df), wall, wall / t_last)
@printf(io, "m=%.3f kg/m (A=%.3e m²), m_a≈%.3f kg/m, coupling %s, dt_max=%.2f\n",
        MASS, AREA, M_ADDED, ADDED_MASS ? "semi-implicit" : "explicit", DT_MAX)
@printf(io, "glitch guard |Fx| > %.0f N/m: %d of %d steps rejected (t = %s)\n", FX_GUARD, drv.n_rejected, nrow(df),
        join([@sprintf("%.3f", x) for x in df.t[df.rejected]][1:min(end, 10)], ", "))
@printf(io, "distance swum: %.3f m = %.2f L_BODY\n", -df.X[end], -df.X_L[end])
@printf(io, "steady speed (mean over cycles %d..%d, t=%.2f..%.2f s): U = %.4f m/s = %.2f L/s\n",
        n_cyc - k_avg + 1, n_cyc, ta, tb, U_steady, U_steady / L_BODY)
@printf(io, "previous %d cycles: U = %.4f m/s (drift %.1f %%)\n", k_avg, U_prev, 100 * (U_steady - U_prev) / U_steady)
@printf(io, "mean Fx over the same cycles: %.4f N/m (≈ 0 if steady)\n", Fx_mean)
@printf(io, "A_tip (peak-to-peak) = %.4f m, St = f·A_tip/U = %.3f\n", A_tip, St)
println(io, "per-cycle mean U_swim [m/s]: ", join([@sprintf("%.3f", x) for x in cyc_U], " "))
if us === nothing
    println(io, "NOTE: no results/stage3_*.csv with a U* column yet – compare U by hand with stage 3 U* " *
                "(criterion: |U − U*|/U* < 25 %).")
    crit = "n/a"
else
    Ustar, f3, c3 = us
    dev = (U_steady - Ustar) / Ustar
    crit = abs(dev) < 0.25 ? "PASS" : "FAIL"
    @printf(io, "stage 3 U* = %.4f m/s (%s, column %s): deviation %+.1f %% (criterion < 25 %%): %s\n",
            Ustar, f3, c3, 100dev, crit)
end
println(io, "Caveat: body viscous drag is under-predicted at this resolution (stage 1: viscous C_D " *
            "converges slowly, below Blasius) -> the free-swimming speed is biased high.")
report = String(take!(io))
print(report)

mkpath(RESULTS_DIR)
out = select(df, :t, :X, :u, :Fx, :θ, :s, :V_p, :U_swim, :X_L, :tip, :Fpx, :Fvx, :Fy, :a, :V_ref, :Q, :rejected, :step)
CSV.write(joinpath(RESULTS_DIR, "$CASE.csv"), out)
write(joinpath(RESULTS_DIR, "$CASE.log"), report)

# --- plot ------------------------------------------------------------------------------
ttl = @sprintf("Free swimming, f = %.1f Hz, n = %d", F_TAIL, N)
p1 = plot(df.t, df.X_L, xlabel="t [s]", ylabel="X [L_BODY]", label="X (tail root, lab frame)",
          title=ttl, legend=:topright, lw=1.5)
p2 = plot(df.t, df.U_swim, xlabel="t [s]", ylabel="U_swim = −dX/dt [m/s]", label="instantaneous", lw=0.8, c=:gray)
plot!(p2, cyc_t, cyc_U, m=:o, label="cycle mean", lw=2, c=:blue)
hline!(p2, [U_steady], ls=:dash, c=:blue, label=@sprintf("steady %.3f m/s", U_steady))
us === nothing || hline!(p2, [us[1]], ls=:dot, c=:red, lw=2, label=@sprintf("stage 3 U* %.3f m/s", us[1]))
vspan!(p2, [0, T_TRANSIENT], c=:orange, alpha=0.15, label="valve transient")
p3 = plot(df.t, rad2deg.(df.θ), xlabel="t [s]", ylabel="θ [deg]", label="tail angle θ", lw=1)
p4 = plot(df.t, df.Fx, xlabel="t [s]", ylabel="Fx on body [N/m]", label="Fx (+x; thrust < 0)", lw=0.6, c=:gray)
plot!(p4, cyc_t, cyc_F, m=:o, label="cycle mean", c=:black, lw=2)
plot(p1, p2, p3, p4, layout=(2, 2), size=(1500, 900), margin=5Plots.mm)
savefig(joinpath(RESULTS_DIR, "$CASE.png"))
println("wrote results/$CASE.csv, .png, .log")
