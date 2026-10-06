"""Kompiluje i symuluje wszystkie scenariusze z FishRobot.Examples, zapisuje wykresy w results/examples/.

Uruchomienie:  .venv/bin/python scripts/run_all.py [fragment_nazwy ...]
"""

import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import om_config as C
import plotting


def plot_hydraulics_step(sol):
    t = sol["time"]
    plotting.panels(t, [
        ("komenda u [-]", [(sol["bridge.u_lim"], "u")]),
        ("nadciśnienie [kPa]", [(sol["p_L"] / 1e3, "komora L"), (sol["p_R"] / 1e3, "komora R")]),
        ("przepływ [ml/s]", [(sol["Q_pump"] * 1e6, "pompa R→L"), (sol["Q_relief"] * 1e6, "zawory L→R")]),
        ("prąd [A]", [(sol["i_motor"], "silnik"), (sol["i_battery"], "bateria")]),
        ("prędkość [rad/s]", [(sol["motor.w"], "wał silnika")]),
    ], "HydraulicsStep: rampa komendy pompy, ogon zablokowany", "hydraulics_step.png")


def plot_tail_flapping(sol):
    t = sol["time"]
    plotting.panels(t, [
        ("komenda u [-]", [(sol["cpg.y"], "u")]),
        ("kąt ogona [°]", [(np.degrees(sol["drive.theta"]), "θ")]),
        ("nadciśnienie [kPa]", [(sol["drive.p_L"] / 1e3, "komora L"), (sol["drive.p_R"] / 1e3, "komora R")]),
        ("prąd [A]", [(sol["drive.i_motor"], "silnik"), (sol["drive.battery.i"], "bateria")]),
    ], "TailFlapping: sinus 1 Hz, ogon swobodny", "tail_flapping.png")


def plot_relief_valve_demo(sol):
    t = sol["time"]
    dp = (sol["drive.p_L"] - sol["drive.p_R"]) / 1e3
    plotting.panels(t, [
        ("kąt ogona [°]", [(np.degrees(sol["drive.theta"]), "θ")]),
        ("p_L − p_R [kPa]", [(dp, "Δp"), (np.full_like(t, sol["drive.reliefLR.p_set"][0] / 1e3), "p_set"),
                             (np.full_like(t, -sol["drive.reliefLR.p_set"][0] / 1e3), "−p_set")]),
        ("przepływ [ml/s]", [(sol["drive.pump.V_flow"] * 1e6, "pompa"),
                             ((sol["drive.reliefLR.V_flow"] - sol["drive.reliefRL.V_flow"]) * 1e6, "zawory")]),
        ("energia [J]", [(sol["E_pump_hyd"], "oddana przez pompę"), (sol["E_relief"], "stracona w zaworach")]),
    ], "ReliefValveDemo: A = 1 przy 0,25 Hz – zawór przelewowy się otwiera", "relief_valve_demo.png")


LOSSES = [
    ("drive.E_loss_motor_cu", "silnik: uzwojenie R·i²"),
    ("drive.E_loss_motor_fric", "silnik: łożyska"),
    ("drive.E_loss_battery", "bateria: rezystancja wewnętrzna"),
    ("drive.E_loss_pump_leak", "pompa: przeciek"),
    ("drive.E_loss_pump_mech", "pompa: tarcie (η_m)"),
    ("drive.E_loss_pipes", "przewody"),
    ("drive.E_loss_relief", "zawory przelewowe"),
    ("drive.E_loss_tail", "ogon: woda i materiał"),
]


def plot_energy_budget(sol):
    e_bat = sol["drive.E_battery"][-1]
    d_stored = sol["drive.E_stored"][-1] - sol["drive.E_stored0"][-1]
    err = sol["drive.E_balance_error"][-1]
    runtime_h = sol["t_runtime"][-1] / 3600
    p_mean = sol["P_battery_mean"][-1]
    plotting.hbar([label for _, label in LOSSES], [sol[k][-1] for k, _ in LOSSES],
                  f"EnergyBudget: gdzie idzie energia z baterii (60 s, 1 Hz) – razem {e_bat:.1f} J",
                  "energy_budget.png",
                  note=(f"Średnia moc z baterii {p_mean:.2f} W → szacowany czas pracy napędu ogona "
                        f"{runtime_h:.1f} h (pojemność {sol['capacity_Wh'][-1]:.1f} Wh – placeholder).  "
                        f"Zmiana energii zmagazynowanej {d_stored * 1e3:.1f} mJ, błąd bilansu {err * 1e3:.3f} mJ."))
    rows = [(label, sol[k][-1]) for k, label in LOSSES]
    print(f"  {'pozycja':34} {'energia [J]':>11} {'udział':>7}")
    for label, v in sorted(rows, key=lambda r: -r[1]):
        print(f"  {label:34} {v:11.3f} {100 * v / e_bat:6.1f}%")
    print(f"  {'ΔE zmagazynowana':34} {d_stored:11.4f}\n  {'energia z ogniwa':34} {e_bat:11.3f}"
          f"\n  błąd bilansu {err:.2e} J ({abs(err) / e_bat:.1e}); czas pracy ≈ {runtime_h:.1f} h przy {p_mean:.2f} W")


def plot_depth_control(sol):
    t = sol["time"]
    plotting.panels(t, [
        ("głębokość z [m]", [(sol["fish.z"], "z"), (sol["controller.refLimiter.y"], "zadana (po filtrze)"),
                             (sol["depthReference.y[1]"], "zadana (skoki)")]),
        ("pęcherz [ml]", [(sol["syringe.V_b"] * 1e6, "V_b"), (sol["controller.V_ref"] * 1e6, "V_ref (z PID)")]),
        ("prędkość pionowa [cm/s]", [(sol["fish.v_z"] * 100, "z'")]),
        ("prąd [A]", [(sol["syringe.i_motor"], "silnik strzykawki")]),
    ], "DepthControl: skoki zadanej głębokości −0,5 → −1,5 → −1,0 m", "depth_control.png")


def plot_swim_forward(sol):
    t = sol["time"]
    plotting.panels(t, [
        ("kąt ogona [°]", [(np.degrees(sol["drive.theta"]), "θ")]),
        ("ciąg [mN]", [(sol["fin.T"] * 1e3, "T (chwilowy)"), (sol["surge.F_drag"] * 1e3, "opór kadłuba")]),
        ("prędkość [cm/s]", [(sol["surge.U"] * 100, "U")]),
        ("energia z baterii [J]", [(sol["drive.E_battery"], "z baterii")]),
        ("energia za ogonem [mJ]", [(sol["drive.E_mech_out"] * 1e3, "oddana płetwie"),
                                    (sol["E_drag"] * 1e3, "praca przeciw oporowi (użyteczna)"),
                                    (sol["E_wake"] * 1e3, "ślad wirowy")]),
    ], "SwimForward: CPG 1 Hz, A = 0,8 – ciąg płetwy i pływanie do przodu (model ciągu: placeholder)",
        "swim_forward.png")
    e_bat, e_drag = sol["drive.E_battery"][-1], sol["E_drag"][-1]
    print(f"  U_końc = {sol['surge.U'][-1] * 100:.1f} cm/s, droga {sol['surge.x'][-1]:.2f} m; "
          f"energia z baterii {e_bat:.1f} J, do płetwy {sol['drive.E_mech_out'][-1]:.2f} J, "
          f"użyteczna {e_drag:.2f} J ({e_drag / e_bat:.2%})")


PLOTS = {
    "FishRobot.Examples.HydraulicsStep": (
        ["time", "bridge.u_lim", "p_L", "p_R", "Q_pump", "Q_relief", "i_motor", "i_battery", "motor.w"],
        plot_hydraulics_step),
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
