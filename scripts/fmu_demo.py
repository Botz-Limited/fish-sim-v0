"""Uruchomienie FMU napędu ogona przez FMPy w pętli Pythona i porównanie z OpenModelica.

Pętla co-simulation z krokiem 2 ms: w każdym kroku Python liczy zadaną objętość V_ref i regulator przekaźnikowy
z histerezą i minimalnym czasem stanu zaworu 0,2 s (ten sam wzór co FishRobot.Control.CPG) na podstawie wyjścia V_p, podaje kierunek zaworów ±1 na
wejście u, wywołuje doStep i odczytuje wyjścia. Tak samo
wyglądałoby sprzężenie z innym symulatorem (np. MuJoCo): zamiast CPG – sterownik, a wyjścia
FMU trafiają do drugiego symulatora.

Odniesienie: scenariusz FishRobot.Examples.TailFlapping (A_V = 4 ml, f = 1,5 Hz, 5 s) policzony w OpenModelica.
W OpenModelica przekaźnik przełącza dokładnie w chwili zdarzenia, a w pętli FMU dopiero na granicy kroku
(opóźnienie do 2 ms, czyli ok. Q_const·h ≈ 0,07 ml objętości). Kolejne przełączenia wypadają więc trochę inaczej
i przebiegi rozjeżdżają się w czasie (przekaźnik pobudza rezonans ogona, więc porównanie punkt po punkcie traci
sens). Test porównuje statystyki z ostatnich 3 okresów: amplituda i RMS kąta (różnica < 5%) oraz liczbę
przełączeń zaworów na cykl.
Wyniki: results/fmu/fmu_vs_om.png.

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
OUTPUTS = ["theta", "w_tail", "tau_tail", "p_L", "p_R", "i_motor", "V_p"]
A_V, F, N_RAMP, STOP, H, DELTA, DWELL = 4e-6, 1.5, 2.0, 5.0, 2e-3, 1e-6, 0.2  # jak w TailFlapping
TOL = 0.05


def v_ref(t):
    """Ten sam wzór co FishRobot.Control.CPG: rampa 3x² − 2x³ przez N_RAMP okresów, potem sinus."""
    x = t * F / N_RAMP
    ramp = np.where(x < 1, x**2 * (3 - 2 * x), 1.0)
    return ramp * A_V * np.sin(2 * np.pi * F * t)


class Relay:
    """Regulator przekaźnikowy z histerezą δ i minimalnym czasem stanu zaworu; start s = +1."""

    def __init__(self, delta=DELTA, dwell=DWELL):
        self.delta, self.dwell, self.s, self.t_switch = delta, dwell, 1.0, -np.inf

    def __call__(self, t, e):
        # Na granicy kroku: czas porównujemy z tolerancją, żeby 0,2 s = 100 kroków nie przesunęło się o krok.
        if t - self.t_switch < self.dwell - 1e-9:
            return self.s
        s = 1.0 if e > self.delta else -1.0 if e < -self.delta else self.s
        if s != self.s:
            self.s, self.t_switch = s, t
        return self.s


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


def run_fmu(path):
    """Pętla co-simulation; V_ref próbkowane w środku kroku [t, t + h] (ZOH spóźniałby się średnio o h/2)."""
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
        u_log = np.ones(n + 1)
        out[0] = fmu.getReal([vr[k] for k in OUTPUTS])
        relay = Relay()
        i_vp = OUTPUTS.index("V_p")
        for i in range(n):
            u = relay(t[i], v_ref(t[i] + H / 2) - out[i, i_vp])
            u_log[i + 1] = u
            fmu.setReal([vr["u"]], [float(u)])
            fmu.doStep(currentCommunicationPoint=t[i], communicationStepSize=H)
            out[i + 1] = fmu.getReal([vr[k] for k in OUTPUTS])
        fmu.terminate()
    finally:
        fmu.freeInstance()
        shutil.rmtree(unzip_dir, ignore_errors=True)
    res = dict(zip(OUTPUTS, out.T))
    res["n_switch"] = np.concatenate([[0], np.cumsum(np.abs(np.diff(u_log)) > 0)])
    return t, res


def run_om():
    mod = C.make_system(REF_MODEL)
    mod.simulate()
    names = ["time", "drive.theta", "drive.i_motor", "drive.n_switch"]
    return dict(zip(names, (np.asarray(x) for x in mod.getSolutions(names))))


def stats(t, theta, n_switch, periods=3):
    """Amplituda i RMS kąta oraz przełączenia na cykl w ostatnich `periods` okresach."""
    win = t >= t[-1] - periods / F
    return {"amp": np.ptp(theta[win]) / 2, "rms": np.sqrt(np.mean(theta[win] ** 2)),
            "sw": (n_switch[-1] - n_switch[win][0]) / periods}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", action="store_true", help="zbuduj FMU od nowa")
    args = ap.parse_args()
    if args.export or not FMU_PATH.exists():
        print("eksport FMU ...")
        export()

    ref = run_om()
    t, fmu = run_fmu(FMU_PATH)
    th_ref = np.interp(t, ref["time"], ref["drive.theta"])
    s_om = stats(ref["time"], ref["drive.theta"], ref["drive.n_switch"])
    s_fmu = stats(t, fmu["theta"], fmu["n_switch"])

    plotting.panels(t, [
        ("tail angle [°]", [(np.degrees(th_ref), "OpenModelica (TailFlapping)"),
                           (np.degrees(fmu["theta"]), "FMU + FMPy, 2 ms step")]),
        ("valve switches", [(np.interp(t, ref["time"], ref["drive.n_switch"]), "OpenModelica (events)"),
                            (fmu["n_switch"], "FMU (relay at step boundaries)")]),
        ("motor current [A]", [(np.interp(t, ref["time"], ref["drive.i_motor"]), "OpenModelica"),
                              (fmu["i_motor"], "FMU")]),
    ], "Tail drive FMU (FMPy, co-simulation 2 ms) vs OpenModelica", "fmu_vs_om.png", subdir="fmu")

    err_amp = abs(s_fmu["amp"] / s_om["amp"] - 1)
    err_rms = abs(s_fmu["rms"] / s_om["rms"] - 1)
    ok = err_amp < TOL and err_rms < TOL
    print(f"amplituda θ: OM {np.degrees(s_om['amp']):.2f}°, FMU {np.degrees(s_fmu['amp']):.2f}° ({100 * err_amp:.1f}%)")
    print(f"RMS θ: OM {np.degrees(s_om['rms']):.2f}°, FMU {np.degrees(s_fmu['rms']):.2f}° ({100 * err_rms:.1f}%)")
    print(f"przełączenia zaworów na cykl: OM {s_om['sw']:.1f}, FMU {s_fmu['sw']:.1f}")
    print(f"[{'OK ' if ok else 'BŁĄD'}] FMU zgodny z OpenModelica (amplituda i RMS kąta < {100 * TOL:g}%)")
    print(f"wykres: {C.RESULTS_DIR / 'fmu' / 'fmu_vs_om.png'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
