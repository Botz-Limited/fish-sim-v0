"""Automatyczne testy pakietu FishRobot.

Dla każdego modelu z FishRobot.Tests i FishRobot.Examples:
  1. checkModel – model musi być zbilansowany (liczba równań = liczba niewiadomych),
  2. kompilacja i symulacja z ustawieniami z annotation(experiment(...)),
  3. asercje fizyczne (jeśli zdefiniowane w CHECKS),
  4. wykres porównawczy w results/tests/.

Uruchomienie:  .venv/bin/python scripts/check_tests.py [fragment_nazwy ...]
"""

import re
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import om_config as C
import plotting

PACKAGES = ["FishRobot.Tests", "FishRobot.Examples"]


# ---------------------------------------------------------------- asercje

def check_pipe_laminar(sol):
    dp, ref = sol["pipe.dp"], sol["dp_analytic"]
    mask = ref > 1e-3 * ref.max()  # pomijamy chwilę t = 0, gdzie oba są zerem
    err = np.max(np.abs(dp[mask] - ref[mask]) / ref[mask])
    plotting.compare(sol["time"], dp, ref, "Δp [Pa]", "PipeLaminar: Δp w rurze vs Hagen–Poiseuille",
                     "pipe_laminar.png", sim_label="symulacja pipe.dp", ref_label="analitycznie 128μlQ/(πd⁴)")
    return [("Δp zgodne z Hagenem–Poiseuille’em (< 1%)", err < 0.01, f"max błąd względny {err:.2e}"),
            ("zakres laminarny (Re < 2300)", sol["pipe.Re"].max() < 2300, f"Re_max = {sol['pipe.Re'].max():.0f}")]


def check_pipe_quadratic(sol):
    q, dp, ref = sol["pipe.V_flow"], sol["pipe.dp"], sol["dp_exact"]
    mask = np.abs(q) > 100 * 1e-8  # 100 * V_flow_small
    err = np.max(np.abs(dp[mask] - ref[mask]) / np.abs(ref[mask]))
    plotting.compare(sol["time"], dp, ref, "Δp [Pa]", "PipeQuadratic: Δp przy przepływie zmieniającym kierunek",
                     "pipe_quadratic.png", sim_label="symulacja (regularyzowana)", ref_label="R_lam·Q + R_turb·|Q|·Q")
    return [("Δp zgodne z charakterystyką bez regularyzacji (< 1%)", err < 0.01, f"max błąd względny {err:.2e}")]


def check_pipe_inertance(sol):
    q, ref = sol["pipe.V_flow"], sol["Q_analytic"]
    q_end = ref[-1]
    err = np.max(np.abs(q - ref)) / q_end
    plotting.compare(sol["time"], q * 1e6, ref * 1e6, "Q [ml/s]", "PipeInertance: narastanie przepływu po skoku Δp",
                     "pipe_inertance.png", sim_label="symulacja pipe.V_flow", ref_label="analitycznie dp/R·(1−e^(−t/τ))")
    return [("Q(t) zgodne z rozwiązaniem analitycznym (< 1% Q_ust)", err < 0.01, f"max błąd {err:.2e} Q_ust")]


def check_chamber_closed_loop(sol):
    t, vl, vr, vt = sol["time"], sol["chamberL.V"], sol["chamberR.V"], sol["V_total"]
    drift = np.max(np.abs(vt - vt[0])) / vt[0]
    v_eq = vt[0] / 2  # identyczne krzywe p–V -> równowaga przy równych objętościach
    eq_err = max(abs(vl[-1] - v_eq), abs(vr[-1] - v_eq)) / v_eq
    dp0 = abs(sol["chamberL.port.p"][0] - sol["chamberR.port.p"][0])
    dp_end = abs(sol["chamberL.port.p"][-1] - sol["chamberR.port.p"][-1]) / dp0
    # Energia: to, co ubyło ze ścianek i słupa cieczy, musi się rozproszyć w rurze.
    e_lost = sol["E_stored"][0] - sol["E_stored"][-1]
    e_err = abs(e_lost - sol["E_dissipated"][-1]) / e_lost
    plotting.series(t, [(vl * 1e6, "V_L"), (vr * 1e6, "V_R")], "objętość [ml]",
                    "ChamberClosedLoop: wymiana cieczy między komorami", "chamber_closed_loop.png",
                    hlines=[(v_eq * 1e6, "równowaga")],
                    bottom=((vt - vt[0]) * 1e6, "odchyłka\nV_L+V_R [ml]"))
    return [("V_L + V_R = const (< 1e-9 względnie)", drift < 1e-9, f"max dryf {drift:.1e}"),
            ("równowaga: V_L = V_R, p_L = p_R (< 0,1%)", eq_err < 1e-3 and dp_end < 1e-3,
             f"błąd objętości {eq_err:.1e}, |p_L − p_R| = {dp_end:.1e} różnicy początkowej"),
            ("energia: ubytek zmagazynowanej = rozproszona w rurze (< 1%)", e_err < 0.01,
             f"błąd {e_err:.1e}")]


def check_relief_valve(sol):
    t, pg, q_src, q_valve = sol["time"], sol["chamber.p_gauge"], sol["source.V_flow"], sol["valve.V_flow"]
    p_set, dp_open = sol["valve.p_set"][0], sol["valve.dp_open"][0]
    q_err = abs(q_valve[-1] - q_src[-1]) / q_src[-1]
    plotting.series(t, [(pg / 1e3, "nadciśnienie w komorze")], "Δp [kPa]",
                    "ReliefValveLimit: zawór przelewowy ogranicza ciśnienie", "relief_valve_limit.png",
                    hlines=[(p_set / 1e3, "p_set"), ((p_set + dp_open) / 1e3, "p_set + dp_open")])
    return [("p ≤ p_set + dp_open", pg.max() <= p_set + dp_open,
             f"max {pg.max() / 1e3:.2f} kPa, granica {(p_set + dp_open) / 1e3:.1f} kPa"),
            ("zawór otwarty: cały przepływ uchodzi przez zawór (< 1%)", q_err < 0.01, f"różnica {q_err:.1e}")]


def check_chamber_from_file(sol):
    a, b = sol["chamberTable.p_gauge"], sol["chamberFile.p_gauge"]
    diff = np.max(np.abs(a - b))
    return [("krzywa z CSV = krzywa z parametru", diff < 1e-6, f"max różnica {diff:.1e} Pa")]


CHECKS = {
    "FishRobot.Tests.PipeLaminar": (["time", "pipe.dp", "dp_analytic", "pipe.Re"], check_pipe_laminar),
    "FishRobot.Tests.PipeQuadratic": (["time", "pipe.V_flow", "pipe.dp", "dp_exact"], check_pipe_quadratic),
    "FishRobot.Tests.PipeInertance": (["time", "pipe.V_flow", "Q_analytic"], check_pipe_inertance),
    "FishRobot.Tests.ChamberClosedLoop": (["time", "chamberL.V", "chamberR.V", "V_total", "chamberL.port.p",
                                           "chamberR.port.p", "E_stored", "E_dissipated"],
                                          check_chamber_closed_loop),
    "FishRobot.Tests.ChamberTableFromFile": (["time", "chamberTable.p_gauge", "chamberFile.p_gauge"],
                                             check_chamber_from_file),
    "FishRobot.Tests.ReliefValveLimit": (["time", "chamber.p_gauge", "source.V_flow", "valve.V_flow",
                                          "valve.p_set", "valve.dp_open"], check_relief_valve),
}


# ---------------------------------------------------------------- uruchamianie

def list_models():
    """Lista modeli z pakietów testowych (jedna krótka sesja omc)."""
    from OMPython import OMCSessionLocal

    omc = OMCSessionLocal()
    omc.sendExpression(f'loadModel(Modelica, {{"{C.MSL_VERSION}"}})')
    omc.sendExpression(f'loadFile("{C.model_file().as_posix()}")')
    models = []
    for pkg in PACKAGES:
        if not omc.sendExpression(f"isPackage({pkg})"):
            continue
        for name in omc.sendExpression(f"getClassNames({pkg})"):
            full = f"{pkg}.{name}"
            if omc.sendExpression(f"isModel({full})"):
                models.append(full)
    return models


def run_one(model):
    """Sprawdza jeden model; działa w osobnym procesie (osobna sesja omc)."""
    results = []
    try:
        mod = C.make_system(model)
        msg = mod.sendExpression(f"checkModel({model})")
        m = re.search(r"has (\d+) equation\(s\) and (\d+) variable\(s\)", msg or "")
        balanced = bool(m) and m.group(1) == m.group(2)
        results.append(("checkModel: zbilansowany", balanced,
                        f"{m.group(1)} równań / {m.group(2)} zmiennych" if m else msg))
        mod.simulate()
        results.append(("symulacja", True, ""))
        if model in CHECKS:
            names, fn = CHECKS[model]
            sol = dict(zip(names, (np.asarray(x) for x in mod.getSolutions(names))))
            results += fn(sol)
    except Exception as exc:  # błąd kompilacji/symulacji = test niezaliczony
        results.append(("kompilacja/symulacja", False, str(exc).splitlines()[0][:200]))
    return model, results


def main():
    models = list_models()
    if len(sys.argv) > 1:
        models = [m for m in models if any(f in m for f in sys.argv[1:])]
    # Każdy model w osobnym procesie: kompilacje i symulacje idą równolegle.
    with ProcessPoolExecutor(max_workers=min(len(models), C.NUM_PROCS) or 1) as pool:
        outcomes = list(pool.map(run_one, models))

    failed = 0
    for model, results in outcomes:
        print(model)
        for name, ok, detail in results:
            failed += not ok
            print(f"  [{'OK ' if ok else 'BŁĄD'}] {name}" + (f" – {detail}" if detail else ""))
    print(f"\n{len(models)} modeli, {failed} niezaliczonych asercji")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
