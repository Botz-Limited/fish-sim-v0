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


CHECKS = {
    "FishRobot.Tests.PipeLaminar": (["time", "pipe.dp", "dp_analytic", "pipe.Re"], check_pipe_laminar),
    "FishRobot.Tests.PipeQuadratic": (["time", "pipe.V_flow", "pipe.dp", "dp_exact"], check_pipe_quadratic),
    "FishRobot.Tests.PipeInertance": (["time", "pipe.V_flow", "Q_analytic"], check_pipe_inertance),
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
