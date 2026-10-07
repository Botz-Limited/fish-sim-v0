"""Przeglądy częstotliwości machania.

  scenariusz 3 (domyślnie): FrequencySweep na modelu TailFlapping -> results/sweep/frequency_sweep.{png,csv}
  scenariusz 7 (--swim):    prędkość ustalona vs częstotliwość na SwimForward -> results/sweep/swim_sweep.{png,csv}

Model kompilowany jest raz; każda częstotliwość to osobne uruchomienie pliku wykonywalnego
(równolegle na wszystkich rdzeniach).

Uruchomienie:  .venv/bin/python scripts/sweep.py [--swim] [--A 1.0] [--fmin 0.5] [--fmax 4] [--n 15]
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


SWIM_MODEL = "FishRobot.Examples.SwimForward"
SWIM_NAMES = ["time", "surge.U", "drive.theta", "drive.E_battery", "drive.E_mech_out", "E_thrust", "E_drag",
              "fin.L_tail", "surge.m", "drive.reliefLR.V_flow", "drive.reliefRL.V_flow", "drive.pump.V_flow"]
SWIM_STOP = 150.0  # stała czasowa rozpędzania to ok. 20 s, więc 150 s z zapasem wystarcza do stanu ustalonego


def swim_metrics(sol, f, n_periods=3):
    """Wskaźniki pływania z ostatnich n_periods okresów; zbieżność: porównanie z poprzednim oknem."""
    t = sol["time"]
    last = t >= t[-1] - n_periods / f
    prev = (t >= t[-1] - 2 * n_periods / f) & ~last
    dt = t[-1] - t[last][0]

    def rate(name):  # średnia moc w oknie z przyrostu energii
        return (sol[name][-1] - sol[name][last][0]) / dt

    u, u_prev = np.mean(sol["surge.U"][last]), np.mean(sol["surge.U"][prev])
    p_bat, p_fin, p_thrust, p_drag = (rate(k) for k in ["drive.E_battery", "drive.E_mech_out", "E_thrust", "E_drag"])
    q_relief = np.abs(sol["drive.reliefLR.V_flow"] - sol["drive.reliefRL.V_flow"])
    return {
        "f_Hz": f,
        "U_cm_s": 100 * u,
        "U_converged": abs(u / u_prev - 1) < 0.01,
        "theta_amp_deg": np.degrees(np.ptp(sol["drive.theta"][last]) / 2),
        "theta_f_deg_Hz": np.degrees(np.ptp(sol["drive.theta"][last]) / 2) * f,
        "U_bound_cm_s": 100 * sol["fin.L_tail"][0] * 2 * np.pi * f,
        "P_battery_W": p_bat,
        "P_fin_mW": 1e3 * p_fin,
        "eta_fin": p_thrust / p_fin,
        "eta_total": p_drag / p_bat,
        "COT": p_bat / (sol["surge.m"][0] * 9.80665 * u),
        "relief_share": np.mean(q_relief[last]) / np.mean(np.abs(sol["drive.pump.V_flow"][last])),
    }


def swim_sweep(args, t0):
    work_dir = om_fast.compile_model(SWIM_MODEL)
    t1 = time.perf_counter()
    freqs = np.linspace(args.fmin, args.fmax, args.n)
    cases = [(f"swim{f:.3f}", {"cpg.f": f, "cpg.A": args.A}, {"stopTime": SWIM_STOP, "stepSize": 0.01})
             for f in freqs]
    results = om_fast.run_many(work_dir, SWIM_MODEL, cases, SWIM_NAMES)
    rows = [swim_metrics(sol, f) for sol, f in zip(results, freqs)]
    t2 = time.perf_counter()

    out = C.RESULTS_DIR / "sweep"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "swim_sweep.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    col = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    plotting.panels(col["f_Hz"], [
        ("steady speed [cm/s]", [(col["U_cm_s"], "U")]),
        ("tail", [(col["theta_amp_deg"], "θ amplitude [°]"), (col["theta_f_deg_Hz"], "θ·f [°·Hz]")]),
        ("battery power [W]", [(col["P_battery_W"], "mean")]),
        ("overall efficiency [%]", [(100 * col["eta_total"], "P_drag / P_bat")]),
    ], f"SwimForward: steady speed vs frequency (A = {args.A}; thrust model: placeholder)",
        "swim_sweep.png", subdir="sweep", xlabel="flapping frequency [Hz]", marker="o")

    print(f"{'f [Hz]':>7} {'U [cm/s]':>9} {'θ [°]':>7} {'θ·f':>6} {'P_bat [W]':>9} {'P_fin [mW]':>10} "
          f"{'η_płetwa':>8} {'η_całość':>9} {'COT':>6} {'zawory':>7}")
    for r in rows:
        flag = "" if r["U_converged"] else "  (niezbieżne!)"
        print(f"{r['f_Hz']:7.2f} {r['U_cm_s']:9.2f} {r['theta_amp_deg']:7.1f} {r['theta_f_deg_Hz']:6.1f} "
              f"{r['P_battery_W']:9.2f} {r['P_fin_mW']:10.3f} {100 * r['eta_fin']:7.1f}% "
              f"{100 * r['eta_total']:8.3f}% {r['COT']:6.0f} {100 * r['relief_share']:6.1f}%{flag}")
    print(f"\nkompilacja {t1 - t0:.1f} s, {len(freqs)} symulacji równolegle {t2 - t1:.1f} s -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--swim", action="store_true", help="scenariusz 7: pływanie (SwimForward) zamiast samego ogona")
    ap.add_argument("--A", type=float, default=1.0, help="amplituda komendy CPG")
    ap.add_argument("--fmin", type=float, default=0.25)
    ap.add_argument("--fmax", type=float, default=4.0)
    ap.add_argument("--n", type=int, default=16)
    args = ap.parse_args()

    t0 = time.perf_counter()
    if args.swim:
        return swim_sweep(args, t0)
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
        ("tail amplitude [°]", [(col["theta_amp_deg"], "θ")]),
        ("peak |p_L − p_R| [kPa]", [(col["dp_peak_kPa"], "Δp"),
                                         (np.full_like(freqs, rows[0]["p_set_kPa"]), "valve p_set")]),
        ("current [A]", [(col["i_battery_mean_A"], "battery (mean)"), (col["i_motor_rms_A"], "motor (RMS)")]),
        ("valve share [%]", [(100 * col["relief_share"], "valve flow / pump flow")]),
    ], f"FrequencySweep: tail drive response vs frequency (A = {args.A})", "frequency_sweep.png",
        subdir="sweep", xlabel="flapping frequency [Hz]", marker="o")

    print(f"{'f [Hz]':>7} {'θ [°]':>7} {'Δp [kPa]':>9} {'I_bat [A]':>9} {'zawory':>7}")
    for r in rows:
        print(f"{r['f_Hz']:7.2f} {r['theta_amp_deg']:7.1f} {r['dp_peak_kPa']:9.1f} "
              f"{r['i_battery_mean_A']:9.3f} {100 * r['relief_share']:6.1f}%")
    print(f"\nkompilacja {t1 - t0:.1f} s, {len(freqs)} symulacji równolegle {t2 - t1:.1f} s -> {out}")


if __name__ == "__main__":
    main()
