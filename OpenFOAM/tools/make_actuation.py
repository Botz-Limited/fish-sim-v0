#!/usr/bin/env python3
"""Generuje pliki aktuacji dla CalculiX: ciśnienie w komorach L/R.

Przebieg (pompa naprzemiennie pompuje lewą i prawą komorę):
    p_L(t) = P0 * r(t) * max(0,  sin(2*pi*f*t))
    p_R(t) = P0 * r(t) * max(0, -sin(2*pi*f*t))
    r(t)   = rampa 0 -> 1 przez pierwsze T_RAMP sekund (łagodny start,
             bez uderzenia ciśnieniem, które pobudziłoby drgania własne)
Ciśnienie w komorze nie może być ujemne (podciśnienie zapadałoby komory),
stąd półfale sinusa w przeciwnej fazie.

Zapisuje:
    amplitude.inc – definicje *AMPLITUDE (dane modelu, przed *STEP)
    dload.inc     – *DLOAD na ściankach komór (dane kroku, wewnątrz *STEP)
Przy P0 = 0 pliki są puste (ogon pasywny).

Użycie:
    python tools/make_actuation.py <katalog> --p0 PA --freq HZ --t-end S [--t-ramp S]
"""
import argparse
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--p0", type=float, required=True, help="amplituda ciśnienia [Pa]")
    ap.add_argument("--freq", type=float, default=1.0, help="częstotliwość [Hz]")
    ap.add_argument("--t-end", type=float, required=True, help="czas końcowy [s]")
    ap.add_argument("--t-ramp", type=float, default=None, help="czas rampy [s] (domyślnie 1 okres)")
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)
    amp, dl = a.outdir / "amplitude.inc", a.outdir / "dload.inc"

    if a.p0 == 0:
        amp.write_text("** Ogon pasywny: brak aktuacji\n")
        dl.write_text("** Ogon pasywny: brak ciśnienia w komorach\n")
        print("aktuacja: brak (P0 = 0)")
        return

    t_ramp = a.t_ramp if a.t_ramp is not None else 1.0 / a.freq
    # 64 punkty na okres – CalculiX interpoluje liniowo między punktami
    t = np.linspace(0.0, a.t_end, int(np.ceil(a.t_end * a.freq * 64)) + 1)
    r = np.clip(t / t_ramp, 0.0, 1.0)
    s = np.sin(2 * np.pi * a.freq * t)
    curves = {"AMP_L": r * np.maximum(0.0, s), "AMP_R": r * np.maximum(0.0, -s)}

    with open(amp, "w") as f:
        f.write(f"** Aktuacja (generowana przez tools/make_actuation.py – nie edytować)\n")
        f.write(f"** f = {a.freq} Hz, rampa {t_ramp} s; wartości to mnożnik P0 (0..1)\n")
        for name, y in curves.items():
            # TIME=TOTAL TIME: czas liczony od początku analizy (a nie kroku)
            f.write(f"*AMPLITUDE, NAME={name}, TIME=TOTAL TIME\n")
            for i in range(0, len(t), 4):
                f.write(", ".join(f"{tt:.6g}, {yy:.6g}" for tt, yy in zip(t[i:i + 4], y[i:i + 4])) + "\n")

    with open(dl, "w") as f:
        f.write("** Ciśnienie w komorach: P0 * amplituda(t)\n")
        f.write(f"** P0 = {a.p0:g} Pa   PLACEHOLDER – do identyfikacji z pomiarów\n")
        f.write("*DLOAD, AMPLITUDE=AMP_L\n")
        f.write(f"SchL, P, {a.p0:g}\n")
        f.write("*DLOAD, AMPLITUDE=AMP_R\n")
        f.write(f"SchR, P, {a.p0:g}\n")
    print(f"aktuacja: P0 = {a.p0:g} Pa, f = {a.freq} Hz, rampa {t_ramp} s")


if __name__ == "__main__":
    main()
