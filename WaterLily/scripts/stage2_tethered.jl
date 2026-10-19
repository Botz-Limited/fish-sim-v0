# Stage 2 – tethered fish, tail driven by the valve (kinematic mode θ = V_p/A_r), still water.
# f = 2 Hz. Discards the valve start-up transient (first 2 s), averages over 6 whole cycles.
# Pass criteria (spec): mean F_x thrust > 0, 2 ± 0.2 valve switches per tail cycle.
#
# Run from WaterLily/:  julia --project=. -t 4 scripts/stage2_tethered.jl
#   env N=64 for a quick check (default n = 128), FISH_LIVE=1 for the live viewer.
# Output: results/stage2_tethered.csv (summary), results/stage2_n<n>_timeseries.csv,
#         results/stage2_tethered.png (time series), results/stage2_vorticity.png (4 phases),
#         progress in results/progress/stage2_n<n>.json
using WaterLily, Statistics, Printf, DataFrames, CSV, Plots
using FishLily
include(joinpath(@__DIR__, "stage_common.jl"))

const F_TAIL = 2.0                                  # [Hz]
const N = parse(Int, get(ENV, "N", "128"))          # cells per L_BODY
const N_CYC = 6                                     # averaged cycles
const T_A, T_B = cycle_window(F_TAIL; n_cycles=N_CYC, t_skip=t_skip_valve(F_TAIL))  # 2.0 … 5.0 s
const T_END = T_B
const CASE = "stage2_n$(N)"

fs = make_fish_sim(; n=N, U_in=0.0, name=CASE)
# vorticity snapshots at 4 phases of the last cycle (phase of V_ref = sin 2πft)
snap_t = [T_B - 1 / F_TAIL + φ / F_TAIL for φ in (0.0, 0.25, 0.5, 0.75)]
snaps = VortSnaps(fs, snap_t)
extras = TailExtras(fs)
drv = ValveDriver(F_TAIL)
live = live_hook(fs, T_END; driver=drv, title="stage 2: tethered, still water, f = $(F_TAIL) Hz")   # FISH_LIVE=1
wall0 = time()
df = run_fish!(fs, T_END; driver=drv, case=CASE,
               on_frame=chain_hooks(pressure_fix!, snaps, extras, live), frame_every=1)
wall = time() - wall0
live_finish!(live)
ex = DataFrame(extras)
df.Qθ = ex.Qθ; df.Fx_tail_p = ex.Fx_tail_p          # same steps (log_every = 1, frame_every = 1)
df.θdot = df.Q ./ VALVE.A_r                         # θ̇ = Q/A_r exactly (kinematic mode)
df.P_in = -df.Qθ .* df.θdot                         # power into the fluid [W/m]
mkpath(RESULTS_DIR)
CSV.write(joinpath(RESULTS_DIR, "$(CASE)_timeseries.csv"), df)

# --- summary -------------------------------------------------------------------------------
wm(c) = window_mean(df, c, T_A, T_B)
thrust = wm(:thrust); Fy = wm(:Fy); Fx_tail = -wm(:Fx_tail_p); P = wm(:P_in)
sw = switches_in_window(df, F_TAIL, T_A, T_B)
θpp = cycle_peak_to_peak(df, :θ, F_TAIL, T_A, T_B)
A_tip = θpp * bend_h(FishGeom(), L_TAIL)
θmean = wm(:θ)
Fy_amp = cycle_peak_to_peak(df, :Fy, F_TAIL, T_A, T_B) / 2
M_amp = cycle_peak_to_peak(df, :M, F_TAIL, T_A, T_B) / 2
# convergence check: first half vs second half of the window
tm = (T_A + T_B) / 2
thr1, thr2 = window_mean(df, :thrust, T_A, tm), window_mean(df, :thrust, tm, T_B)
dims = size(fs.sim.flow.p) .- 2
pass_thrust = thrust > 0
pass_sw = abs(sw - 2) <= 0.2
summary = DataFrame(case=CASE, n=N, Nx=dims[1], Ny=dims[2], f=F_TAIL, t_avg_from=T_A, t_avg_to=T_B,
                    thrust_mean=thrust, thrust_1st_half=thr1, thrust_2nd_half=thr2,
                    tail_pressure_thrust=Fx_tail, Fy_mean=Fy, Fy_amp=Fy_amp, M_amp=M_amp,
                    theta_pp=θpp, theta_mean=θmean, A_tip_pp=A_tip, P_in_mean=P,
                    switches_per_cycle=sw, pass_thrust=pass_thrust, pass_switches=pass_sw,
                    steps=df.step[end], wall_s=wall)
CSV.write(joinpath(RESULTS_DIR, "stage2_tethered.csv"), summary)
@printf("\n%s  n=%d dims=%s  window %.2f–%.2f s (%d cycles)\n", CASE, N, dims, T_A, T_B, N_CYC)
@printf("  mean thrust −F_x = %.4f N/m  (1st/2nd half %.4f / %.4f)  tail pressure thrust %.4f N/m\n",
        thrust, thr1, thr2, Fx_tail)
@printf("  F_y mean %.4f, amp %.3f N/m; tail moment amp %.4f N·m/m; θ p-p %.3f rad (mean %.3f), A_tip p-p %.1f mm\n",
        Fy, Fy_amp, M_amp, θpp, θmean, 1e3A_tip)
@printf("  mean input power %.4f W/m; switches/cycle %.2f; steps %d; wall %.1f s\n", P, sw, df.step[end], wall)
@printf("  criterion mean thrust > 0: %s;  2 ± 0.2 switches/cycle: %s\n",
        pass_thrust ? "PASS" : "FAIL", pass_sw ? "PASS" : "FAIL")

# --- time series plot ----------------------------------------------------------------------
xl = (0, T_END)
vsp(p) = vspan!(p, [T_A, T_B], c=:gray, alpha=0.12, label="averaging window")
p1 = plot(df.t, 1e6df.V_ref, label="V_ref", ylabel="volume [ml]", xlims=xl, legend=:topright)
plot!(p1, df.t, 1e6df.V_p, label="V_p")
plot!(p1, df.t, 4 .* df.s, label="valve s (×4)", lt=:steppost, c=:black, lw=0.7)
p2 = plot(df.t, df.θ, label="θ", ylabel="θ [rad]", xlims=xl, c=:purple)
p3 = plot(df.t, df.thrust, label="thrust −F_x", ylabel="[N/m]", xlims=xl, lw=0.7)
hline!(p3, [thrust], c=:red, ls=:dash, label=@sprintf("mean %.4f", thrust)); vsp(p3)
p4 = plot(df.t, df.Fy, label="F_y", ylabel="[N/m]", xlims=xl, lw=0.7, c=:green)
p5 = plot(df.t, df.M, label="tail pressure moment M", ylabel="[N·m/m]", xlabel="t [s]", xlims=xl, lw=0.7, c=:brown)
plot(p1, p2, p3, p4, p5, layout=(5, 1), size=(1100, 1300), left_margin=8Plots.mm,
     plot_title="Stage 2: tethered fish, still water, f = $(F_TAIL) Hz, n = $N")
savefig(joinpath(RESULTS_DIR, "stage2_tethered.png"))

# --- vorticity snapshots ---------------------------------------------------------------------
if !isempty(snaps.ω)
    x, y = snap_coords(fs, snaps.ω[1])
    ix = findall(xx -> -0.10 <= xx <= 0.40, x); iy = findall(yy -> abs(yy) <= 0.15, y)
    ps = map(eachindex(snaps.ω)) do k
        ω = snaps.ω[k][ix, iy]
        heatmap(x[ix], y[iy], permutedims(ω), c=:balance, clims=(-60, 60), aspect_ratio=:equal,
                xlims=extrema(x[ix]), ylims=extrema(y[iy]), xlabel="x [m]", ylabel="y [m]",
                colorbar_title="ω [1/s]",
                title=@sprintf("phase %.2f  t = %.2f s  θ = %+.2f rad", (k - 1) / 4, snaps.t[k], snaps.θ[k]))
    end
    plot(ps..., layout=(2, 2), size=(1400, 800), margin=4Plots.mm,
         plot_title="Stage 2: vorticity, still water, f = $(F_TAIL) Hz, n = $N (body = blank)")
    savefig(joinpath(RESULTS_DIR, "stage2_vorticity.png"))
end
