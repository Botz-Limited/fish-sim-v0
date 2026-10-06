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


PLOTS = {
    "FishRobot.Examples.HydraulicsStep": (
        ["time", "bridge.u_lim", "p_L", "p_R", "Q_pump", "Q_relief", "i_motor", "i_battery", "motor.w"],
        plot_hydraulics_step),
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
