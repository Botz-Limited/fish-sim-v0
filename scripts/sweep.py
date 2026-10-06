"""Scenariusz 3: przegląd częstotliwości machania (FrequencySweep) na modelu TailFlapping.

Model kompilowany jest raz; każda częstotliwość to osobne uruchomienie pliku wykonywalnego
(równolegle na wszystkich rdzeniach). Wyniki: results/sweep/frequency_sweep.{png,csv}.

Uruchomienie:  .venv/bin/python scripts/sweep.py [--A 1.0] [--fmin 0.5] [--fmax 4] [--n 15]
"""

import argparse
import csv
import time

import numpy as np

import om_config as C
import om_fast
import plotting

MODEL = "FishRobot.Examples.TailFlapping"
NAMES = ["time", "drive.theta", "drive.p_L", "drive.p_R", "drive.battery.i", "drive.i_motor",
         "drive.pump.V_flow", "drive.reliefLR.V_flow", "drive.reliefRL.V_flow", "drive.reliefLR.p_set"]


def metrics(sol, f, n_periods=3):
    """Wskaźniki z ostatnich n_periods okresów (po wygaśnięciu stanu przejściowego)."""
    t = sol["time"]
    win = t >= t[-1] - n_periods / f
    dp = sol["drive.p_L"] - sol["drive.p_R"]
    q_relief = np.abs(sol["drive.reliefLR.V_flow"] - sol["drive.reliefRL.V_flow"])
    return {
        "f_Hz": f,
        "theta_amp_deg": np.degrees(np.ptp(sol["drive.theta"][win]) / 2),
        "dp_peak_kPa": np.max(np.abs(dp[win])) / 1e3,
        "i_battery_mean_A": np.mean(sol["drive.battery.i"][win]),
        "i_motor_rms_A": np.sqrt(np.mean(sol["drive.i_motor"][win] ** 2)),
        "relief_share": np.mean(q_relief[win]) / np.mean(np.abs(sol["drive.pump.V_flow"][win])),
        "p_set_kPa": sol["drive.reliefLR.p_set"][0] / 1e3,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--A", type=float, default=1.0, help="amplituda komendy CPG")
    ap.add_argument("--fmin", type=float, default=0.25)
    ap.add_argument("--fmax", type=float, default=4.0)
    ap.add_argument("--n", type=int, default=16)
    args = ap.parse_args()

    t0 = time.perf_counter()
    work_dir = om_fast.compile_model(MODEL)
    t1 = time.perf_counter()
    freqs = np.linspace(args.fmin, args.fmax, args.n)
    # Czas symulacji: rampa CPG (2 okresy) + 6 okresów stanu ustalonego, co najmniej 4 s.
    cases = [(f"f{f:.3f}", {"cpg.f": f, "cpg.A": args.A}, {"stopTime": max(4.0, 8 / f)}) for f in freqs]
    results = om_fast.run_many(work_dir, MODEL, cases, NAMES)
    rows = [metrics(sol, f) for sol, f in zip(results, freqs)]
    t2 = time.perf_counter()

    out = C.RESULTS_DIR / "sweep"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "frequency_sweep.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    col = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    plotting.panels(col["f_Hz"], [
        ("amplituda ogona [°]", [(col["theta_amp_deg"], "θ")]),
        ("szczytowe |p_L − p_R| [kPa]", [(col["dp_peak_kPa"], "Δp"),
                                         (np.full_like(freqs, rows[0]["p_set_kPa"]), "p_set zaworu")]),
        ("prąd [A]", [(col["i_battery_mean_A"], "bateria (średni)"), (col["i_motor_rms_A"], "silnik (RMS)")]),
        ("udział zaworów [%]", [(100 * col["relief_share"], "przepływ zaworów / przepływ pompy")]),
    ], f"FrequencySweep: odpowiedź napędu ogona vs częstotliwość (A = {args.A})", "frequency_sweep.png",
        subdir="sweep", xlabel="częstotliwość machania [Hz]", marker="o")

    print(f"{'f [Hz]':>7} {'θ [°]':>7} {'Δp [kPa]':>9} {'I_bat [A]':>9} {'zawory':>7}")
    for r in rows:
        print(f"{r['f_Hz']:7.2f} {r['theta_amp_deg']:7.1f} {r['dp_peak_kPa']:9.1f} "
              f"{r['i_battery_mean_A']:9.3f} {100 * r['relief_share']:6.1f}%")
    print(f"\nkompilacja {t1 - t0:.1f} s, {len(freqs)} symulacji równolegle {t2 - t1:.1f} s -> {out}")


if __name__ == "__main__":
    main()
