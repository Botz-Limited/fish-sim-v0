"""
    FishLily

Core of the WaterLily.jl demo of a hydraulically actuated robot-fish tail:
parameters, grid/physical units, valve model, fish geometry (AutoBody),
force readouts and the lock-step CFD + valve loop.

`WaterLily/Project.toml` is the FishLily package, so from `WaterLily/`:

    julia --project=. -t 4 -e 'using FishLily'

From another environment that has WaterLily, StaticArrays, DataFrames, CSV:
`include("<path>/src/FishLily.jl"); using .FishLily`.
"""
module FishLily

using WaterLily
using StaticArrays
using DataFrames
using CSV
using Printf

"Directory for CSV/PNG results (WaterLily/results)."
const RESULTS_DIR = normpath(joinpath(@__DIR__, "..", "results"))

include("params.jl")
include("units.jl")
include("valve.jl")
include("boxbody.jl")
include("geometry.jl")
include("forces.jl")
include("progress.jl")
include("live.jl")
include("sim.jl")

# parameters
export HEAD_A, HEAD_B, L_TAIL, T_ROOT, T_TIP, L_BODY, CH_X0, CH_X1, RHO, NU_WATER, U_REF,
       RE_SIM_DEFAULT, ValveParams, VALVE, DT_VALVE, DomainParams, DOMAIN, RESULTS_DIR
# units
export Units, unit_factor, to_grid, to_phys, nu_grid, nu_sim, coefficient
# valve
export check_freq, f_track, Valve, vref, advance!, valve_state, theta_kinematic, chamber_dp,
       valve_series, switch_times, switches_per_cycle, min_switch_gap
# geometry
export FishGeom, bend_h, bend_dh, tail_tip_displacement, tail_thickness, fish_sdf_straight,
       fish_sdf, bend_inverse, fish_body, Track, set_track!, BoxedBody, unbox
# forces
export body_force, tail_pressure_moment, tail_pressure_force, force_phys, moment_phys, force_coeff
# progress
export Progress, progress_update!, progress_finish!
# simulation
export FishSim, domain_dims, make_fish_sim, clean_pressure!, t_phys, root_grid, readouts, AbstractDriver,
       RigidDriver, ValveDriver, ThetaDriver, drive!, observe!, run_fish!, cycle_mean, save_csv
# live viewer hook (FISH_LIVE=1)
export VIZ_DIR, live_requested, maybe_live_hook, live_finish!, LiveHook, live_screenshot, live_wait_close

end # module
