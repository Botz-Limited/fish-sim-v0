"""Etap 9 (opcja): ten sam obwód na własnym pakiecie (HydraulicsStep) i na Modelica.Fluid (HydraulicsMSLFluid).

Porównuje wyniki (ciśnienia, przepływy, prąd silnika) i złożoność (równania, stany, czas kompilacji
i symulacji). Wykres: results/fluid/fluid_vs_own.png.

Uruchomienie:  .venv/bin/python scripts/compare_fluid.py
"""

import re
import sys
import time

import numpy as np

import om_config as C
import plotting

OWN = "FishRobot.Examples.HydraulicsStep"
FLUID = "FishRobot.Examples.HydraulicsMSLFluid"
SIGNALS = ["time", "bridge.u_lim", "p_L", "p_R", "Q_pump", "Q_relief", "i_motor", "pipeL.dp", "pipeL.Re"]
# Dopuszczalna różnica (względem maksimum przebiegu z własnego pakietu). Większość różnicy daje
# turbulentny opór rury w DetailedPipeFlow (Re do ok. 5200), patrz README.
TOLERANCE = {"p_L": 0.05, "p_R": 0.05, "Q_pump": 0.05, "i_motor": 0.05}
SIM_REPEATS = 5


def run(model):
    t0 = time.perf_counter()
    mod = C.make_system(model)
    t_build = time.perf_counter() - t0
    t_sim = min(_timed(mod.simulate) for _ in range(SIM_REPEATS))
    msg = mod.sendExpression(f"checkModel({model})")
    m = re.search(r"has (\d+) equation\(s\) and (\d+) variable\(s\)\.\s*(\d+) of these are trivial", msg)
    # Stany ciągłe: zmienne z classType="rSta" w opisie modelu (_init.xml).
    init_xml = next((C.BUILD_DIR / model).glob("*_init.xml")).read_text()
    states = sorted(re.search(r'name = "([^"]+)"', block).group(1)
                    for block in init_xml.split("<ScalarVariable")[1:] if 'classType = "rSta"' in block)
    sol = dict(zip(SIGNALS, (np.asarray(x) for x in mod.getSolutions(SIGNALS))))
    return {"sol": sol, "build": t_build, "sim": t_sim, "eq": int(m.group(1)), "trivial": int(m.group(3)),
            "states": states}


def _timed(fn):
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0


def main():
    own, fluid = run(OWN), run(FLUID)
    t = own["sol"]["time"]
    # Siatka czasu jest ta sama (Interval = 1 ms), ale zdarzenia mogą dodać punkty – interpolujemy.
    on_own = {k: np.interp(t, fluid["sol"]["time"], v) for k, v in fluid["sol"].items()}

    print(f"{'':28s}{'własny pakiet':>16s}{'Modelica.Fluid':>16s}")
    print(f"{'równania (po spłaszczeniu)':28s}{own['eq']:>16d}{fluid['eq']:>16d}")
    print(f"{'  w tym trywialne':28s}{own['trivial']:>16d}{fluid['trivial']:>16d}")
    print(f"{'stany ciągłe':28s}{len(own['states']):>16d}{len(fluid['states']):>16d}")
    print(f"{'kompilacja [s]':28s}{own['build']:>16.2f}{fluid['build']:>16.2f}")
    print(f"{'symulacja 3 s [s]':28s}{own['sim']:>16.3f}{fluid['sim']:>16.3f}")
    print(f"  stany tylko we Fluid: {sorted(set(fluid['states']) - set(own['states']))}")
    print(f"  stany tylko we własnym pakiecie: {sorted(set(own['states']) - set(fluid['states']))}")
    print(f"  max Re w przewodzie L: {own['sol']['pipeL.Re'].max():.0f}; "
          f"max spadek ciśnienia: własny {np.abs(own['sol']['pipeL.dp']).max() / 1e3:.2f} kPa, "
          f"Fluid {np.abs(on_own['pipeL.dp']).max() / 1e3:.2f} kPa")

    failed = 0
    for name, tol in TOLERANCE.items():
        ref = own["sol"][name]
        err = np.max(np.abs(on_own[name] - ref)) / np.max(np.abs(ref))
        ok = err < tol
        failed += not ok
        print(f"  [{'OK ' if ok else 'BŁĄD'}] {name}: max różnica {err:.2%} maksimum (granica {tol:.0%})")

    s, f = own["sol"], on_own
    plotting.panels(t, [
        ("komenda u [-]", [(s["bridge.u_lim"], "u")]),
        ("nadciśnienie [kPa]", [(s["p_L"] / 1e3, "L własny"), (f["p_L"] / 1e3, "L Fluid"),
                                (s["p_R"] / 1e3, "R własny"), (f["p_R"] / 1e3, "R Fluid")]),
        ("przepływ [ml/s]", [(s["Q_pump"] * 1e6, "pompa własny"), (f["Q_pump"] * 1e6, "pompa Fluid"),
                             (s["Q_relief"] * 1e6, "zawory własny"), (f["Q_relief"] * 1e6, "zawory Fluid")]),
        ("spadek ciśn.\nprzewód L [kPa]", [(s["pipeL.dp"] / 1e3, "własny (laminarny)"),
                                           (f["pipeL.dp"] / 1e3, "Fluid (DetailedPipeFlow)")]),
        ("prąd silnika [A]", [(s["i_motor"], "własny"), (f["i_motor"], "Fluid")]),
    ], "HydraulicsStep: własny pakiet vs Modelica.Fluid", "fluid_vs_own.png", subdir="fluid")
    print(f"Wykres: {C.RESULTS_DIR / 'fluid' / 'fluid_vs_own.png'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
