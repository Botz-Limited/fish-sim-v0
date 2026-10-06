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
