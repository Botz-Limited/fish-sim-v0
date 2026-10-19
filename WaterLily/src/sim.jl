# Simulation set-up and the lock-step CFD + valve loop.

"""
    FishSim

A WaterLily simulation of the fish plus everything needed to read it in
physical units. Fields: `sim` (WaterLily.Simulation), `units`, `origin`
(grid coordinates of the tail root at X = 0), `theta` (the `Track` the body
reads θ(t) from), `X` (`Track` or `nothing`), `U_in` [m/s], `name`.
"""
struct FishSim{S}
    sim::S
    units::Units
    origin::SVector{2,Float64}
    theta::Any
    X::Any
    U_in::Float64
    name::String
end

_round_up(x, m) = m * ceil(Int, x / m - 1e-9)

"""
    domain_dims(n, domain=DOMAIN) -> ((Nx, Ny), origin)

Grid size (rounded up to a multiple of 16 cells for the multigrid solver) and
grid coordinates of the tail root for a fish centred on y = Ny/2 with its nose
`domain.upstream` body lengths from the inlet.
"""
function domain_dims(n, domain::DomainParams=DOMAIN)
    Nx = _round_up((domain.upstream + 1 + domain.downstream) * n, 16)
    Ny = _round_up(2 * domain.side * n, 16)
    origin = SVector(domain.upstream * n + HEAD_A / L_BODY * n, Ny / 2)
    return (Nx, Ny), origin
end

"""
    make_fish_sim(; n=128, U_in=U_REF, Re=RE_SIM_DEFAULT, domain=DOMAIN,
                  theta=Track(), X=nothing, name="fish", T=Float32, mem=Array,
                  U=1.0, exitBC=U_in > 0) -> FishSim

Create the WaterLily simulation of one case.

- `n`      : cells per body length L_BODY.
- `U_in`   : inflow [m/s] in +x (0 = still water: closed slip-wall box).
             The velocity scale is always U_REF (see units.jl), so the grid
             inflow is U_in/U_REF·U.
- `Re`     : Re_sim = U_REF·L_BODY/ν_sim.
- `theta`  : θ(t_phys) [rad]; default a `Track` (driven by `run_fish!`), any
             function works for a prescribed motion.
- `X`      : `nothing` (fixed body) or a function/`Track` X(t_phys) [m].
- `exitBC` : convective outlet (recommended with inflow).
- `box`    : measure the body / integrate forces only in a box around the fish
             (default, identical results, see `BoxedBody`); `false` = full domain.
"""
function make_fish_sim(; n=128, U_in=U_REF, Re=RE_SIM_DEFAULT, domain::DomainParams=DOMAIN,
                       theta=Track(), X=nothing, name="fish", T::Type=Float32, mem=Array,
                       U=1.0, exitBC=U_in > 0, box=true)
    units = Units(n; U, Re)
    dims, origin = domain_dims(n, domain)
    uin = T(to_grid(units, :velocity, U_in))
    body = fish_body(theta, units, origin; X, T, box)
    sim = Simulation(dims, (uin, zero(T)), n; U=T(U), ν=T(nu_grid(units)), body, T, mem, exitBC)
    FishSim(sim, units, origin, theta, X, Float64(U_in), String(name))
end

"Physical time [s] of the simulation."
t_phys(fs::FishSim) = to_phys(fs.units, :time, Float64(WaterLily.time(fs.sim.flow)))

"Grid position of the tail root at physical time t."
function root_grid(fs::FishSim, t)
    X = fs.X === nothing ? 0.0 : Float64(fs.X(t))
    fs.origin + SVector(to_grid(fs.units, :length, X), 0.0)
end

"""
    readouts(fs::FishSim; moment=true) -> NamedTuple

Force/moment on the body at the current time, physical units per span:
`Fx, Fy` total force [N/m] (x = inflow direction, so Fx > 0 is drag and
`thrust = −Fx`), `Fpx, Fvx` pressure / viscous parts, `Cx` = Fx/(½ρU_REF²L_BODY),
`M` pressure moment on the TAIL about the tail root [N·m/m], CCW positive.
"""
function readouts(fs::FishSim; moment=true)
    u = fs.units
    f = body_force(fs.sim)
    Fx, Fy = force_phys(u, Float64(f.F[1])), force_phys(u, Float64(f.F[2]))
    M = NaN
    if moment
        x0 = root_grid(fs, t_phys(fs))
        M = moment_phys(u, Float64(tail_pressure_moment(fs.sim, x0)))
    end
    return (; Fx, Fy, Fpx=force_phys(u, Float64(f.Fp[1])), Fvx=force_phys(u, Float64(f.Fv[1])),
            thrust=-Fx, Cx=force_coeff(u, Float64(f.F[1])), M)
end

# --- drivers: what moves the tail ------------------------------------------------
#
# A driver implements
#   drive!(d, fs, t0, t1) -> NamedTuple   called BEFORE the CFD step t0 -> t1;
#        it must set the body's tracks (fs.theta, fs.X) for that step and
#        return the columns to log (must contain θ).
#   observe!(d, fs, t1, r)                called AFTER the step with the readouts r
#        (default: nothing; used by coupled / free-swimming drivers).

abstract type AbstractDriver end
observe!(::AbstractDriver, fs, t1, r) = nothing

"Rigid fish (θ = 0)."
struct RigidDriver <: AbstractDriver end
drive!(::RigidDriver, fs, t0, t1) = (; θ=0.0)

"""
    ValveDriver(f; p=VALVE, t_ramp=1/f)

Kinematic mode: valve model in physical time, θ = V_p/A_r.
"""
mutable struct ValveDriver <: AbstractDriver
    valve::Valve
    θ_prev::Float64
end
ValveDriver(f; p::ValveParams=VALVE, t_ramp=1/f) = ValveDriver(Valve(f; p, t_ramp), 0.0)
function drive!(d::ValveDriver, fs, t0, t1)
    st = valve_state(d.valve, t1)
    θ1 = theta_kinematic(st.V_p, d.valve.p)
    set_track!(fs.theta, t0, d.θ_prev, t1, θ1)
    d.θ_prev = θ1
    return (; V_ref=st.V_ref, V_p=st.V_p, Q=st.Q, s=st.s, θ=θ1)
end

"""
    ThetaDriver(θfun)

Prescribed tail angle θ(t_phys) (e.g. a sine for comparison), fed to the
body's `Track` step by step.
"""
struct ThetaDriver{F} <: AbstractDriver
    θ::F
end
function drive!(d::ThetaDriver, fs, t0, t1)
    θ1 = Float64(d.θ(t1))
    set_track!(fs.theta, t0, Float64(d.θ(t0)), t1, θ1)
    return (; θ=θ1)
end

"""
    run_fish!(fs, t_end; driver=RigidDriver(), case=fs.name, progress=true,
              moment=true, on_frame=nothing, frame_every=10,
              max_steps=typemax(Int), progress_dir=joinpath(RESULTS_DIR,"progress"))
        -> DataFrame

Advance the CFD to physical time `t_end` [s] in lock-step with the driver
(valve model in physical time). One log row per CFD step with columns
`t, <driver columns, e.g. V_ref V_p Q s θ>, Fx, Fy, Fpx, Fvx, thrust, Cx, M, X, step, wall`.

Live progress: an updating terminal line and `results/progress/<case>.json`
(set `progress=false` to disable).

`log_every` = k logs (and computes forces) only every k-th step; the
driver and the progress line still run every step. Note: `observe!` is then
also called only every k-th step, so coupled drivers need `log_every=1`.

`dt_max` caps the next CFD time step [grid units, cells/U]. WaterLily's CFL
only sees the fluid velocity: in still water it would take Δt = 10 (≈ 0.3 s
of tail motion at n=32) before the flow has started, so the cap is needed.

`pressure_fix` (default: on for a moving / deforming body, i.e. when the body is
re-measured) calls [`clean_pressure!`](@ref) after every CFD step, before the
readouts. Without it the n = 128 moving-body runs get rare one-step pressure
force spikes (NOTES.md, "Pressure spikes").

`on_frame(sim, row)` is called every
`frame_every` steps (e.g. a live viewer; `row` is the latest logged row).
With the environment variable FISH_LIVE=1 and no `on_frame`, the live GLMakie
viewer is opened automatically for this run (`maybe_live_hook`, viz/FishLive.jl). A NaN force aborts the run
(status "failed" in the progress file) with an error.
"""
function run_fish!(fs::FishSim, t_end; driver::AbstractDriver=RigidDriver(), case=fs.name,
                   progress=true, moment=true, on_frame=nothing, frame_every=10,
                   max_steps=typemax(Int), progress_dir=joinpath(RESULTS_DIR, "progress"),
                   dt_max=0.4, log_every=1, pressure_fix=nothing)
    sim, u = fs.sim, fs.units
    _cap_dt!(sim, dt_max)
    remeasure = !(driver isa RigidDriver) || fs.X !== nothing
    pfix = pressure_fix === nothing ? remeasure : Bool(pressure_fix)
    pr = Progress(case, t_end; dir=progress_dir, enabled=progress)
    # FISH_LIVE=1: open the live viewer automatically (see live.jl)
    auto_live = nothing
    if on_frame === nothing && live_requested()
        auto_live = maybe_live_hook(fs, t_end; driver, title=nothing, case)
        auto_live === nothing || (on_frame = auto_live; frame_every = 1)  # the viewer throttles itself
    end
    rows = NamedTuple[]
    steps = 0; wall0 = time(); row = (;)
    try
        while t_phys(fs) < t_end - 1e-12 && steps < max_steps
            t0 = t_phys(fs)
            t1 = to_phys(u, :time, Float64(sum(sim.flow.Δt)))
            cols = drive!(driver, fs, t0, t1)
            sim_step!(sim; remeasure)
            pfix && clean_pressure!(sim)
            _cap_dt!(sim, dt_max)
            steps += 1
            # forces cost ~2 full-domain passes: optionally only every `log_every` steps
            if steps % log_every == 0
                r = readouts(fs; moment)
                isfinite(r.Fx) || error("simulation diverged at t = $(t1) s (NaN force)")
                observe!(driver, fs, t1, r)
                X = fs.X === nothing ? 0.0 : Float64(fs.X(t1))
                row = merge((; t=t1), cols, r, (; X, step=steps, wall=time() - wall0))
                push!(rows, row)
            end
            progress_update!(pr, t1, steps; s=get(cols, :s, NaN), V_p=get(cols, :V_p, NaN),
                             θ=get(cols, :θ, NaN), Fx=get(row, :Fx, NaN))
            on_frame !== nothing && steps % frame_every == 0 && on_frame(sim, row)
        end
    catch err
        progress_finish!(pr, t_phys(fs), steps, "failed")
        live_finish!(auto_live, err isa InterruptException ? "interrupted" : "failed")
        rethrow(err)
    end
    progress_finish!(pr, t_phys(fs), steps, "done"; s=get(row, :s, NaN), V_p=get(row, :V_p, NaN),
            θ=get(row, :θ, NaN), Fx=get(row, :Fx, NaN))
    live_finish!(auto_live, "done")
    return DataFrame(rows)
end

"""
    clean_pressure!(sim; D_min=1e-4) -> sim

Remove stale pressure from (nearly) solid cells and re-level p. Call after a
CFD step; it does not change the velocity field of that step.

Why: in WaterLily 1.9.2 a cell deep inside the body has a Poisson diagonal
D = Σ face μ₀ that is exactly 0 or tiny (μ₀ cuts off only at d < −1 + √eps, so
D ≈ 1e-11…1e-17 in Float32). Its pressure is not a solution of anything:
with D tiny the Gauss–Seidel update r/D makes it huge (seen 3.7e11), and with
D = 0 the multigrid prolongation still adds coarse corrections to it every
iteration, so it random-walks (seen ±1e8). It is harmless while the cell stays
solid, but when the moving body uncovers the cell (D jumps to ≈ 1e-3…1e-1)
the stale value is the initial guess of the next solve: the residual is huge,
the solver hits its 32-iteration cap and the pressure near the surface is
garbage for that step (the one-step force spike) and noisy afterwards.

What: p = 0 in cells with |D| < `D_min` (fluid cells have |D| ≈ 4; |D| < 1e-4
means d < −0.95 cells, where the force kernel weight is < 0.6 %), and p is
shifted so that its mean over the first inside column (x = 1, the inlet /
left wall side, far from the body) is 0 – the fluid pressure is only defined
up to a constant and otherwise drifts. Falls back to the mean over all fluid
cells if that column is entirely solid.
"""
function clean_pressure!(sim; D_min=1e-4)
    P = sim.pois isa WaterLily.MultiLevelPoisson ? sim.pois.levels[1] : sim.pois
    p = sim.flow.p; T = eltype(p)
    R = WaterLily.inside(p)
    @views pin, Din = p[R], P.D[R]
    dmin = T(D_min)
    col = selectdim(pin, 1, 1); okc = abs.(selectdim(Din, 1, 1)) .>= dmin
    p0 = if any(okc)
        sum(col[okc]) / count(okc)
    else
        ok = abs.(Din) .>= dmin
        any(ok) ? sum(pin[ok]) / count(ok) : zero(T)
    end
    @. pin = ifelse(abs(Din) < dmin, zero(T), pin - p0)
    sim
end

"Cap the next time step of `sim` (the last entry of `flow.Δt`) at `dt_max`."
function _cap_dt!(sim, dt_max)
    Δt = sim.flow.Δt
    Δt[end] = min(Δt[end], eltype(Δt)(dt_max))
    sim
end

"""
    cycle_mean(df, col; t_from) -> mean of `df[!,col]` over t ≥ t_from,
time-weighted (CFD steps are not uniform).
"""
function cycle_mean(df, col; t_from=0.0)
    m = df.t .>= t_from
    t = df.t[m]; y = df[m, col]
    length(t) < 2 && return NaN
    dt = diff(t)
    sum(0.5 .* (y[1:end-1] .+ y[2:end]) .* dt) / sum(dt)
end

"Write a DataFrame to `results/<name>.csv` (creates the directory)."
function save_csv(df, name; dir=RESULTS_DIR)
    mkpath(dir); path = joinpath(dir, endswith(name, ".csv") ? name : name * ".csv")
    CSV.write(path, df); path
end
