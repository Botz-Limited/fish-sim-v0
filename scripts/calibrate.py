"""Identyfikacja parametrów z pomiarów na stole (plan kalibracji z README).

Dopasowanie metodą najmniejszych kwadratów: model z FishRobot.Calibration kompilujemy raz, a każde
wywołanie funkcji celu to uruchomienie gotowego pliku wykonywalnego z -override (om_fast).
Parametry dopasowujemy w skali logarytmicznej: wszystkie są dodatnie, a ich wartości różnią się
o wiele rzędów (J ~ 1e-6, R ~ 1). Jakobian liczymy różnicami skończonymi, wszystkie kolumny równolegle.

Krok 2 (silnik DC): skok napięcia z zasilacza na silnik z wolnym wałem, mierzony prąd i prędkość.

  .venv/bin/python scripts/calibrate.py                         # pomiar syntetyczny (znane parametry + szum)
  .venv/bin/python scripts/calibrate.py --data pomiar.csv --U 6 --t-step 0.01

Plik pomiaru: CSV z nagłówkiem i kolumnami time [s], i [A], w [rad/s]. Wyniki -> results/calibration/.
"""

import argparse
import time

import numpy as np
from scipy.optimize import least_squares

import om_config as C
import om_fast
import plotting

OUT = C.RESULTS_DIR / "calibration"

MOTOR = {
    "model": "FishRobot.Calibration.MotorStep",
    # parametr: (wartość startowa = placeholder z DCMotor, jednostka)
    "params": {"motor.R": (1.0, "Ω"), "motor.L": (5e-4, "H"), "motor.k": (0.01, "V·s/rad"),
               "motor.J": (5e-6, "kg·m²"), "motor.b": (1e-6, "N·m·s/rad")},
    # sygnał: (jednostka, opis)
    "signals": {"i": ("A", "prąd"), "w": ("rad/s", "prędkość")},
    # pomiar syntetyczny: „prawdziwy” silnik i szum czujników (odchylenie standardowe)
    "true": {"motor.R": 1.6, "motor.L": 8e-4, "motor.k": 0.0125, "motor.J": 3.5e-6, "motor.b": 2e-6},
    "noise": {"i": 0.03, "w": 2.0},
}


def simulate(work_dir, exp, values, tag, setup, t):
    """Jedno uruchomienie modelu; zwraca sygnały przeliczone na chwile pomiaru t."""
    params = dict(zip(exp["params"], values)) | setup
    sol = om_fast.run(work_dir, exp["model"], tag, params, {"stopTime": t[-1]}, ["time", *exp["signals"]])
    return {s: np.interp(t, sol["time"], sol[s]) for s in exp["signals"]}


def synthetic_data(work_dir, exp, setup, t_end=0.3, dt=2e-4, seed=1):
    """„Pomiar” z modelu o znanych parametrach z szumem gaussowskim (do sprawdzenia całej procedury)."""
    t = np.arange(0.0, t_end + dt / 2, dt)
    clean = simulate(work_dir, exp, [exp["true"][p] for p in exp["params"]], "true", setup, t)
    rng = np.random.default_rng(seed)
    return t, {s: y + rng.normal(0.0, exp["noise"][s], y.size) for s, y in clean.items()}


def fit(work_dir, exp, t, meas, setup):
    """Najmniejsze kwadraty w zmiennych x = ln(p). Zwraca (p, względna niepewność 1σ, korelacje, wynik, szum sygnałów)."""
    names = list(exp["params"])
    # Wagi sygnałów: najpierw 1% zakresu pomiaru, a po pierwszym dopasowaniu odchylenie standardowe
    # reszt danego sygnału (oszacowanie szumu czujnika). Dopiero wtedy reszty wszystkich sygnałów mają
    # wariancję ok. 1 i wspólne s² w kowariancji jest uczciwe. Przy wagach z zakresu sygnał mniej
    # zaszumiony zaniżałby s², a parametry wyznaczane głównie z bardziej zaszumionego (tu b z prądu)
    # dostawałyby za małą niepewność.
    scale = {s: 0.01 * np.ptp(y) for s, y in meas.items()}

    def residuals_from(sim):
        return np.concatenate([(sim[s] - meas[s]) / scale[s] for s in meas])

    def fun(x):
        return residuals_from(simulate(work_dir, exp, np.exp(x), "fun", setup, t))

    h = 1e-4  # krok w ln(p): 0,01% wartości parametru, dużo więcej niż błąd całkowania przy tolerancji 1e-8

    def jac(x):
        cases = [(f"jac{j}", dict(zip(names, np.exp(x + h * np.eye(len(x))[j]))) | setup, {"stopTime": t[-1]})
                 for j in range(len(x))] + [("jac_base", dict(zip(names, np.exp(x))) | setup, {"stopTime": t[-1]})]
        sols = om_fast.run_many(work_dir, exp["model"], cases, ["time", *exp["signals"]])
        r = [residuals_from({s: np.interp(t, sol["time"], sol[s]) for s in meas}) for sol in sols]
        return np.column_stack([(r[j] - r[-1]) / h for j in range(len(x))])

    x = np.log([exp["params"][p][0] for p in names])
    nfev = 0
    for _ in range(2):
        res = least_squares(fun, x, jac=jac, method="trf", x_scale=1.0, xtol=1e-10, ftol=1e-10)
        x, nfev = res.x, nfev + res.nfev
        r = dict(zip(meas, np.split(res.fun, len(meas))))
        scale = {s: scale[s] * np.std(r[s]) for s in meas}
    res.fun, res.jac, res.nfev = fun(x), jac(x), nfev  # reszty i jakobian przy końcowych wagach
    # Kowariancja ln(p) ≈ s²·(JᵀJ)⁻¹, s² = wariancja reszt. Odchylenie ln(p) to względna niepewność p.
    dof = res.fun.size - len(x)
    cov = np.linalg.inv(res.jac.T @ res.jac) * (res.fun @ res.fun / dof)
    sigma = np.sqrt(np.diag(cov))
    return np.exp(res.x), sigma, cov / np.outer(sigma, sigma), res, scale


def report(exp, p_fit, sigma, corr, res, noise, truth=None):
    names = list(exp["params"])
    lines = [f"{'parametr':<10}{'start':>12}{'dopasowany':>13}{'±1σ':>9}" + (f"{'prawdziwy':>13}{'błąd':>9}" if truth else "")]
    for j, n in enumerate(names):
        p0, unit = exp["params"][n]
        line = f"{n:<10}{p0:>12.4g}{p_fit[j]:>13.5g}{100 * sigma[j]:>8.2f}%"
        if truth:
            line += f"{truth[n]:>13.5g}{100 * (p_fit[j] / truth[n] - 1):>8.2f}%"
        lines.append(f"{line}   [{unit}]")
    lines.append("")
    lines.append("korelacje ln(p):")
    lines.append(" " * 10 + "".join(f"{n.split('.')[-1]:>7}" for n in names))
    for j, n in enumerate(names):
        lines.append(f"{n:<10}" + "".join(f"{corr[j, k]:>7.2f}" for k in range(len(names))))
    lines.append("")
    lines.append("szum oszacowany z reszt: " + ", ".join(f"{s} {v:.3g} {exp['signals'][s][0]}" for s, v in noise.items()))
    lines.append(f"iteracje: {res.nfev} wywołań funkcji; "
                 f"RMS reszt: {np.sqrt(np.mean(res.fun ** 2)):.3f} (w jednostkach szumu, powinno być ok. 1)")
    mod = ", ".join(f"{n.split('.')[-1]}={p_fit[j]:.5g}" for j, n in enumerate(names))
    lines.append(f"do modelu: FishRobot.Electrical.DCMotor motor({mod});")
    return "\n".join(lines)


def plot(exp, t, meas, sim_fit, sim_start, title, name):
    sig = list(exp["signals"])
    fig, axes = plotting.plt.subplots(len(sig) + 1, 1, figsize=(9, 2.3 * (len(sig) + 1) + 0.6), sharex=True)
    for ax, s in zip(axes, sig):
        unit, label = exp["signals"][s]
        ax.plot(t, meas[s], ".", color="#b9b8b3", markersize=2, label="pomiar")
        ax.plot(t, sim_start[s], color=plotting.SERIES[1], linestyle=(0, (4, 3)), linewidth=1.5,
                label="start (placeholdery)")
        ax.plot(t, sim_fit[s], color=plotting.SERIES[0], label="dopasowanie")
        ax.set_ylabel(f"{label} [{unit}]")
    axes[0].legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, borderaxespad=0.2)
    axes[0].set_title(title, loc="left", fontsize=11, pad=26)
    for j, s in enumerate(sig):
        r = (meas[s] - sim_fit[s]) / np.ptp(meas[s]) * 100
        axes[-1].plot(t, r, color=plotting.SERIES[j], linewidth=0.8, label=exp["signals"][s][1])
    axes[-1].set_ylabel("reszty [% zakresu]")
    axes[-1].legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
    axes[-1].set_xlabel("czas [s]")
    fig.align_ylabels(axes)
    return plotting.save(fig, name, "calibration")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", help="CSV z pomiarem (time, i, w); bez tej opcji: pomiar syntetyczny")
    ap.add_argument("--U", type=float, default=6.0, help="napięcie zasilacza po skoku [V]")
    ap.add_argument("--t-step", type=float, default=0.01, help="chwila skoku napięcia w pomiarze [s]")
    args = ap.parse_args()

    exp = MOTOR
    setup = {"U": args.U, "t_step": args.t_step}
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    work_dir = om_fast.compile_model(exp["model"])
    t1 = time.perf_counter()

    if args.data:
        data = np.genfromtxt(args.data, delimiter=",", names=True)
        t = data["time"]
        meas = {s: data[s] for s in exp["signals"]}
        truth = None
    else:
        t, meas = synthetic_data(work_dir, exp, setup)
        truth = exp["true"]
        np.savetxt(OUT / "motor_step_synthetic.csv", np.column_stack([t, meas["i"], meas["w"]]),
                   delimiter=",", header="time,i,w", comments="", fmt="%.6g")

    p_fit, sigma, corr, res, noise = fit(work_dir, exp, t, meas, setup)
    t2 = time.perf_counter()

    text = report(exp, p_fit, sigma, corr, res, noise, truth)
    text += f"\nczas: kompilacja {t1 - t0:.1f} s, dopasowanie {t2 - t1:.1f} s"
    print(text)
    (OUT / "motor_step_fit.txt").write_text(text + "\n")

    sim_fit = simulate(work_dir, exp, p_fit, "fit", setup, t)
    sim_start = simulate(work_dir, exp, [v for v, _ in exp["params"].values()], "start", setup, t)
    src = "pomiar syntetyczny" if truth else args.data
    print(plot(exp, t, meas, sim_fit, sim_start, f"Kalibracja silnika: skok {args.U:g} V, wolny wał ({src})",
               "motor_step_fit.png"))


if __name__ == "__main__":
    main()
