"""Uruchomienie FMU napędu ogona przez FMPy w pętli Pythona i porównanie z OpenModelica.

Pętla co-simulation z krokiem 2 ms: w każdym kroku Python liczy komendę CPG (ten sam wzór co
FishRobot.Control.CPG), podaje ją na wejście u, wywołuje doStep i odczytuje wyjścia. Tak samo
wyglądałoby sprzężenie z innym symulatorem (np. MuJoCo): zamiast CPG – sterownik, a wyjścia
FMU trafiają do drugiego symulatora.

Odniesienie: scenariusz FishRobot.Examples.TailFlapping (CPG A = 0,8, f = 1 Hz, 5 s) policzony w OpenModelica.
Test: max |θ_FMU − θ_OM| < 1% amplitudy kąta. Wyniki: results/fmu/fmu_vs_om.png.

Uruchomienie:  .venv/bin/python scripts/fmu_demo.py [--export]   (--export: zbuduj FMU od nowa)
"""

import argparse
import contextlib
import os
import shutil
import sys

import numpy as np
from fmpy import extract, read_model_description
from fmpy.fmi2 import FMU2Slave

import om_config as C
import plotting
from export_fmu import FMU_PATH, export

REF_MODEL = "FishRobot.Examples.TailFlapping"
OUTPUTS = ["theta", "w_tail", "tau_tail", "p_L", "p_R", "i_motor"]
A, F, N_RAMP, STOP, H = 0.8, 1.0, 2.0, 5.0, 2e-3  # jak w TailFlapping


def cpg(t):
    """Ten sam wzór co FishRobot.Control.CPG: rampa 3x² − 2x³ przez N_RAMP okresów, potem sinus."""
    x = t * F / N_RAMP
    ramp = np.where(x < 1, x**2 * (3 - 2 * x), 1.0)
    return np.clip(ramp * A * np.sin(2 * np.pi * F * t), -1, 1)


@contextlib.contextmanager
def quiet_c_stdout():
    """Wycisza stdout na poziomie deskryptora: runtime OpenModelica w FMU drukuje z C informacje o CVODE."""
    sys.stdout.flush()
    saved = os.dup(1)
    with open(os.devnull, "w") as devnull:
        os.dup2(devnull.fileno(), 1)
        try:
            yield
        finally:
            os.dup2(saved, 1)
            os.close(saved)


def run_fmu(path, sample_at_midpoint):
    """Pętla co-simulation. sample_at_midpoint: u(t + h/2) zamiast u(t) w kroku [t, t + h]."""
    md = read_model_description(str(path))
    vr = {v.name: v.valueReference for v in md.modelVariables}
    unzip_dir = extract(str(path))
    fmu = FMU2Slave(guid=md.guid, unzipDirectory=unzip_dir,
                    modelIdentifier=md.coSimulation.modelIdentifier, instanceName="tail_drive")
    try:
        with quiet_c_stdout():
            fmu.instantiate()
            fmu.setupExperiment(startTime=0.0)
            fmu.enterInitializationMode()
            fmu.exitInitializationMode()
        n = int(round(STOP / H))
        t = np.arange(n + 1) * H
        out = np.zeros((n + 1, len(OUTPUTS)))
        out[0] = fmu.getReal([vr[k] for k in OUTPUTS])
        for i in range(n):
            u = cpg(t[i] + H / 2) if sample_at_midpoint else cpg(t[i])
            fmu.setReal([vr["u"]], [float(u)])
            fmu.doStep(currentCommunicationPoint=t[i], communicationStepSize=H)
            out[i + 1] = fmu.getReal([vr[k] for k in OUTPUTS])
        fmu.terminate()
    finally:
        fmu.freeInstance()
        shutil.rmtree(unzip_dir, ignore_errors=True)
    return t, dict(zip(OUTPUTS, out.T))


def run_om():
    mod = C.make_system(REF_MODEL)
    mod.simulate()
    names = ["time", "drive.theta", "drive.i_motor"]
    return dict(zip(names, (np.asarray(x) for x in mod.getSolutions(names))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", action="store_true", help="zbuduj FMU od nowa")
    args = ap.parse_args()
    if args.export or not FMU_PATH.exists():
        print("eksport FMU ...")
        export()

    ref = run_om()
    # Komenda stała w kroku (ZOH) i próbkowana na początku kroku spóźnia się średnio o h/2 = 1 ms.
    # Próbkowanie w środku kroku usuwa to opóźnienie (błąd drugiego rzędu w h).
    t, fmu_mid = run_fmu(FMU_PATH, sample_at_midpoint=True)
    _, fmu_start = run_fmu(FMU_PATH, sample_at_midpoint=False)

    th_ref = np.interp(t, ref["time"], ref["drive.theta"])
    late = t >= N_RAMP / F  # amplituda po rampie
    amp = np.ptp(th_ref[late]) / 2
    err_mid = np.max(np.abs(fmu_mid["theta"] - th_ref)) / amp
    err_start = np.max(np.abs(fmu_start["theta"] - th_ref)) / amp

    plotting.panels(t, [
        ("kąt ogona [°]", [(np.degrees(th_ref), "OpenModelica (TailFlapping)"),
                           (np.degrees(fmu_mid["theta"]), "FMU + FMPy, krok 2 ms")]),
        ("różnica θ [% amplitudy]", [(100 * (fmu_mid["theta"] - th_ref) / amp, "u w środku kroku"),
                                     (100 * (fmu_start["theta"] - th_ref) / amp, "u na początku kroku")]),
        ("prąd silnika [A]", [(np.interp(t, ref["time"], ref["drive.i_motor"]), "OpenModelica"),
                              (fmu_mid["i_motor"], "FMU")]),
    ], "FMU napędu ogona (FMPy, co-simulation 2 ms) vs OpenModelica", "fmu_vs_om.png", subdir="fmu")

    ok = err_mid < 0.01
    print(f"amplituda θ = {np.degrees(amp):.2f}°")
    print(f"max |θ_FMU − θ_OM|: {100 * err_mid:.3f}% amplitudy (u w środku kroku), "
          f"{100 * err_start:.3f}% (u na początku kroku)")
    print(f"[{'OK ' if ok else 'BŁĄD'}] FMU zgodny z OpenModelica (< 1% amplitudy)")
    print(f"wykres: {C.RESULTS_DIR / 'fmu' / 'fmu_vs_om.png'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
