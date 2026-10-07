"""Kompiluje i symuluje wszystkie scenariusze z FishRobot.Examples, zapisuje wykresy w results/examples/.

Uruchomienie:  .venv/bin/python scripts/run_all.py [fragment_nazwy ...]
"""

import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import om_config as C
import plotting


def plot_hydraulics_step(sol, title="HydraulicsStep: pump command ramp, tail locked",
                         name="hydraulics_step.png"):
    t = sol["time"]
    plotting.panels(t, [
        ("command u [-]", [(sol["bridge.u_lim"], "u")]),
        ("gauge pressure [kPa]", [(sol["p_L"] / 1e3, "chamber L"), (sol["p_R"] / 1e3, "chamber R")]),
        ("flow [ml/s]", [(sol["Q_pump"] * 1e6, "pump R→L"), (sol["Q_relief"] * 1e6, "valves L→R")]),
        ("current [A]", [(sol["i_motor"], "motor"), (sol["i_battery"], "battery")]),
        ("speed [rad/s]", [(sol["motor.w"], "motor shaft")]),
    ], title, name)


def plot_tail_flapping(sol):
    t = sol["time"]
    plotting.panels(t, [
        ("command u [-]", [(sol["cpg.y"], "u")]),
        ("tail angle [°]", [(np.degrees(sol["drive.theta"]), "θ")]),
        ("gauge pressure [kPa]", [(sol["drive.p_L"] / 1e3, "chamber L"), (sol["drive.p_R"] / 1e3, "chamber R")]),
        ("current [A]", [(sol["drive.i_motor"], "motor"), (sol["drive.battery.i"], "battery")]),
    ], "TailFlapping: 1 Hz sine, tail free", "tail_flapping.png")


def plot_relief_valve_demo(sol):
    t = sol["time"]
    dp = (sol["drive.p_L"] - sol["drive.p_R"]) / 1e3
    plotting.panels(t, [
        ("tail angle [°]", [(np.degrees(sol["drive.theta"]), "θ")]),
        ("p_L − p_R [kPa]", [(dp, "Δp"), (np.full_like(t, sol["drive.reliefLR.p_set"][0] / 1e3), "p_set"),
                             (np.full_like(t, -sol["drive.reliefLR.p_set"][0] / 1e3), "−p_set")]),
        ("flow [ml/s]", [(sol["drive.pump.V_flow"] * 1e6, "pump"),
                             ((sol["drive.reliefLR.V_flow"] - sol["drive.reliefRL.V_flow"]) * 1e6, "valves")]),
        ("energy [J]", [(sol["E_pump_hyd"], "delivered by pump"), (sol["E_relief"], "lost in valves")]),
    ], "ReliefValveDemo: A = 1 at 0.25 Hz – relief valve opens", "relief_valve_demo.png")


LOSSES = [
    ("drive.E_loss_motor_cu", "motor: winding R·i²"),
    ("drive.E_loss_motor_fric", "motor: bearings"),
    ("drive.E_loss_battery", "battery: internal resistance"),
    ("drive.E_loss_pump_leak", "pump: leakage"),
    ("drive.E_loss_pump_mech", "pump: friction (η_m)"),
    ("drive.E_loss_pipes", "pipes"),
    ("drive.E_loss_relief", "relief valves"),
    ("drive.E_loss_tail", "tail: water and material"),
]


def plot_energy_budget(sol):
    e_bat = sol["drive.E_battery"][-1]
    d_stored = sol["drive.E_stored"][-1] - sol["drive.E_stored0"][-1]
    err = sol["drive.E_balance_error"][-1]
    runtime_h = sol["t_runtime"][-1] / 3600
    p_mean = sol["P_battery_mean"][-1]
    plotting.hbar([label for _, label in LOSSES], [sol[k][-1] for k, _ in LOSSES],
                  f"EnergyBudget: where the battery energy goes (60 s, 1 Hz) – total {e_bat:.1f} J",
                  "energy_budget.png",
                  note=(f"Mean battery power {p_mean:.2f} W → estimated tail drive runtime "
                        f"{runtime_h:.1f} h (capacity {sol['capacity_Wh'][-1]:.1f} Wh – placeholder).  "
                        f"Change in stored energy {d_stored * 1e3:.1f} mJ, balance error {err * 1e3:.3f} mJ."))
    rows = [(label, sol[k][-1]) for k, label in LOSSES]
    print(f"  {'pozycja':34} {'energia [J]':>11} {'udział':>7}")
    for label, v in sorted(rows, key=lambda r: -r[1]):
        print(f"  {label:34} {v:11.3f} {100 * v / e_bat:6.1f}%")
    print(f"  {'ΔE zmagazynowana':34} {d_stored:11.4f}\n  {'energia z ogniwa':34} {e_bat:11.3f}"
          f"\n  błąd bilansu {err:.2e} J ({abs(err) / e_bat:.1e}); czas pracy ≈ {runtime_h:.1f} h przy {p_mean:.2f} W")


def plot_depth_control(sol):
    t = sol["time"]
    plotting.panels(t, [
        ("depth z [m]", [(sol["fish.z"], "z"), (sol["controller.refLimiter.y"], "setpoint (filtered)"),
                             (sol["depthReference.y[1]"], "setpoint (steps)")]),
        ("bladder [ml]", [(sol["syringe.V_b"] * 1e6, "V_b"), (sol["controller.V_ref"] * 1e6, "V_ref (from PID)")]),
        ("vertical speed [cm/s]", [(sol["fish.v_z"] * 100, "z'")]),
        ("current [A]", [(sol["syringe.i_motor"], "syringe motor")]),
    ], "DepthControl: depth setpoint steps −0.5 → −1.5 → −1.0 m", "depth_control.png")


def plot_swim_forward(sol):
    t = sol["time"]
    plotting.panels(t, [
        ("tail angle [°]", [(np.degrees(sol["drive.theta"]), "θ")]),
        ("thrust [mN]", [(sol["fin.T"] * 1e3, "T (instantaneous)"), (sol["surge.F_drag"] * 1e3, "hull drag")]),
        ("speed [cm/s]", [(sol["surge.U"] * 100, "U")]),
        ("battery energy [J]", [(sol["drive.E_battery"], "from battery")]),
        ("energy past the tail [mJ]", [(sol["drive.E_mech_out"] * 1e3, "delivered to fin"),
                                    (sol["E_drag"] * 1e3, "work against drag (useful)"),
                                    (sol["E_wake"] * 1e3, "vortex wake")]),
    ], "SwimForward: CPG 1 Hz, A = 0.8 – fin thrust and forward swimming (thrust model: placeholder)",
        "swim_forward.png")
    e_bat, e_drag = sol["drive.E_battery"][-1], sol["E_drag"][-1]
    print(f"  U_końc = {sol['surge.U'][-1] * 100:.1f} cm/s, droga {sol['surge.x'][-1]:.2f} m; "
          f"energia z baterii {e_bat:.1f} J, do płetwy {sol['drive.E_mech_out'][-1]:.2f} J, "
          f"użyteczna {e_drag:.2f} J ({e_drag / e_bat:.2%})")


PLOTS = {
    "FishRobot.Examples.HydraulicsStep": (
        ["time", "bridge.u_lim", "p_L", "p_R", "Q_pump", "Q_relief", "i_motor", "i_battery", "motor.w"],
        plot_hydraulics_step),
    "FishRobot.Examples.HydraulicsMSLFluid": (
        ["time", "bridge.u_lim", "p_L", "p_R", "Q_pump", "Q_relief", "i_motor", "i_battery", "motor.w"],
        lambda sol: plot_hydraulics_step(sol, "HydraulicsMSLFluid: the same circuit on Modelica.Fluid",
                                         "hydraulics_msl_fluid.png")),
    "FishRobot.Examples.TailFlapping": (
        ["time", "cpg.y", "drive.theta", "drive.p_L", "drive.p_R", "drive.i_motor", "drive.battery.i"],
        plot_tail_flapping),
    "FishRobot.Examples.ReliefValveDemo": (
        ["time", "drive.theta", "drive.p_L", "drive.p_R", "drive.reliefLR.p_set", "drive.pump.V_flow",
         "drive.reliefLR.V_flow", "drive.reliefRL.V_flow", "E_pump_hyd", "E_relief"],
        plot_relief_valve_demo),
    "FishRobot.Examples.EnergyBudget": (
        ["time", "drive.E_battery", "drive.E_stored", "drive.E_stored0", "drive.E_balance_error", "t_runtime",
         "P_battery_mean", "capacity_Wh"] + [k for k, _ in LOSSES],
        plot_energy_budget),
    "FishRobot.Examples.DepthControl": (
        ["time", "fish.z", "controller.refLimiter.y", "depthReference.y[1]", "syringe.V_b", "controller.V_ref",
         "fish.v_z", "syringe.i_motor"],
        plot_depth_control),
    "FishRobot.Examples.SwimForward": (
        ["time", "drive.theta", "fin.T", "surge.F_drag", "surge.U", "surge.x", "drive.E_battery", "drive.E_mech_out",
         "E_drag", "E_wake"],
        plot_swim_forward),
}


def run_one(model):
    mod = C.make_system(model)
    mod.simulate()
    if model in PLOTS:
        names, fn = PLOTS[model]
        sol = dict(zip(names, (np.asarray(x) for x in mod.getSolutions(names))))
        fn(sol)
    return model


def main():
    models = list(PLOTS)
    if len(sys.argv) > 1:
        models = [m for m in models if any(f in m for f in sys.argv[1:])]
    with ProcessPoolExecutor(max_workers=min(len(models), C.NUM_PROCS) or 1) as pool:
        for model in pool.map(run_one, models):
            print(f"[OK] {model}")
    print(f"Wykresy: {C.RESULTS_DIR / 'examples'}")


if __name__ == "__main__":
    main()
