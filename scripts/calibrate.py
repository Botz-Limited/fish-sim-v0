"""Identyfikacja parametrów z pomiarów na stole (plan kalibracji z README).

Krok 2, silnik DC (calibrate.py motor): skok napięcia z zasilacza na silnik z wolnym wałem, mierzony prąd
i prędkość. Dopasowanie symulacji metodą najmniejszych kwadratów: model z FishRobot.Calibration kompilujemy
raz, a każde wywołanie funkcji celu to uruchomienie gotowego pliku wykonywalnego z -override (om_fast).
Parametry dopasowujemy w skali logarytmicznej: wszystkie są dodatnie, a ich wartości różnią się
o wiele rzędów (J ~ 1e-6, R ~ 1). Jakobian liczymy różnicami skończonymi, wszystkie kolumny równolegle.

Krok 3, pompa (calibrate.py pump): punkty pracy w stanie ustalonym przy kilku napięciach i nastawach zaworu
dławiącego. Równania pompy są liniowe w parametrach, więc wystarcza regresja liniowa. Silnik z kroku 2
służy jako czujnik momentu, a jego niepewność przenosi się na sprawność pompy.

Krok 4, przewód (calibrate.py pipe): charakterystyka Δp(Q) od laminarnej do turbulentnej, dopasowanie
symulacji jak w kroku 2, ale reszty w skali logarytmicznej (szum czujnika ciśnienia jest względny).

Krok 5, komora (calibrate.py chamber): krzywa p–V z kilku cykli strzykawki, bez dopasowania parametrów.
Pierwszy cykl jest odrzucany (efekt Mullinsa), gałęzie napełniania i opróżniania uśredniane do krzywej
szkieletowej, a wynik zapisywany jako CSV dla Chamber(tableOnFile=true) i sprawdzany w ChamberBench.

  .venv/bin/python scripts/calibrate.py motor                   # pomiar syntetyczny (znane parametry + szum)
  .venv/bin/python scripts/calibrate.py motor --data pomiar.csv --U 6 --t-step 0.01
  .venv/bin/python scripts/calibrate.py pump [--data punkty.csv]
  .venv/bin/python scripts/calibrate.py pipe [--data punkty.csv --l 0.2]
  .venv/bin/python scripts/calibrate.py chamber [--data cykle.csv --V-rest 5e-6]

Pliki pomiaru: CSV z nagłówkiem; silnik: time [s], i [A], w [rad/s]; pompa: U [V], i [A], w [rad/s],
dp [Pa], Q [m³/s];
przewód: Q [m³/s], dp [Pa]; komora (w kolejności czasu): dV [m³], p [Pa]. Wyniki -> results/calibration/.
"""

import argparse
import json
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
    "component": "FishRobot.Electrical.DCMotor motor",
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
    """Najmniejsze kwadraty w zmiennych x = ln(p). Zwraca (p, względna niepewność 1σ, kowariancja ln(p), wynik, szum sygnałów)."""
    names = list(exp["params"])
    # Wagi sygnałów: najpierw 1% zakresu pomiaru, a po pierwszym dopasowaniu odchylenie standardowe
    # reszt danego sygnału (oszacowanie szumu czujnika). Dopiero wtedy reszty wszystkich sygnałów mają
    # wariancję ok. 1 i wspólne s² w kowariancji jest uczciwe. Przy wagach z zakresu sygnał mniej
    # zaszumiony zaniżałby s², a parametry wyznaczane głównie z bardziej zaszumionego (tu b z prądu)
    # dostawałyby za małą niepewność.
    scale = {s: 0.01 * np.ptp(y) for s, y in meas.items()}

    if exp.get("log"):  # szum względny (np. % odczytu): reszty ln(sim/pomiar) mają wtedy stałą wariancję
        scale = {s: 0.01 for s in meas}

    def residuals_from(sim):
        if exp.get("log"):
            return np.concatenate([np.log(sim[s] / meas[s]) / scale[s] for s in meas])
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
    return np.exp(res.x), sigma, cov, res, scale


def report(exp, p_fit, sigma, cov, res, noise, truth=None):
    names = list(exp["params"])
    corr = cov / np.outer(sigma, sigma)
    wn = max(10, max(len(n) for n in names) + 2)
    lines = [f"{'parametr':<{wn}}{'start':>12}{'dopasowany':>13}{'±1σ':>9}" + (f"{'prawdziwy':>13}{'błąd':>9}" if truth else "")]
    for j, n in enumerate(names):
        p0, unit = exp["params"][n]
        line = f"{n:<{wn}}{p0:>12.4g}{p_fit[j]:>13.5g}{100 * sigma[j]:>8.2f}%"
        if truth:
            line += f"{truth[n]:>13.5g}{100 * (p_fit[j] / truth[n] - 1):>8.2f}%"
        lines.append(f"{line}   [{unit}]")
    lines.append("")
    lines.append("korelacje ln(p):")
    lines.append(" " * wn + "".join(f"{n.split('.')[-1][:9]:>10}" for n in names))
    for j, n in enumerate(names):
        lines.append(f"{n:<{wn}}" + "".join(f"{corr[j, k]:>10.2f}" for k in range(len(names))))
    lines.append("")
    unit = (lambda s: "(względnie)") if exp.get("log") else (lambda s: exp["signals"][s][0])
    lines.append("szum oszacowany z reszt: " + ", ".join(f"{s} {v:.3g} {unit(s)}" for s, v in noise.items()))
    lines.append(f"iteracje: {res.nfev} wywołań funkcji; "
                 f"RMS reszt: {np.sqrt(np.mean(res.fun ** 2)):.3f} (w jednostkach szumu, powinno być ok. 1)")
    mod = ", ".join(f"{n.split('.')[-1]}={p_fit[j]:.5g}" for j, n in enumerate(names))
    lines.append(f"do modelu: {exp['component']}({mod});")
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


def motor_main(args):
    exp = MOTOR
    setup = {"U": args.U, "t_step": args.t_step}
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

    p_fit, sigma, cov, res, noise = fit(work_dir, exp, t, meas, setup)
    t2 = time.perf_counter()

    text = report(exp, p_fit, sigma, cov, res, noise, truth)
    text += f"\nczas: kompilacja {t1 - t0:.1f} s, dopasowanie {t2 - t1:.1f} s"
    print(text)
    (OUT / "motor_step_fit.txt").write_text(text + "\n")
    # Dla kolejnych kroków (silnik jako czujnik momentu): wartości i kowariancja ln(p)
    (OUT / "motor_params.json").write_text(json.dumps(
        {"names": list(exp["params"]), "values": p_fit.tolist(), "cov_ln": cov.tolist()}, indent=1))

    sim_fit = simulate(work_dir, exp, p_fit, "fit", setup, t)
    sim_start = simulate(work_dir, exp, [v for v, _ in exp["params"].values()], "start", setup, t)
    src = "pomiar syntetyczny" if truth else args.data
    print(plot(exp, t, meas, sim_fit, sim_start, f"Kalibracja silnika: skok {args.U:g} V, wolny wał ({src})",
               "motor_step_fit.png"))


# --- Krok 3: pompa ---------------------------------------------------------------------------------

PUMP = {
    "model": "FishRobot.Calibration.PumpBench",
    "params": {"pump.D_rev": (3e-7, "m³/obr"), "pump.k_leak": (2e-11, "m³/(s·Pa)"), "pump.eta_m": (0.8, "–")},
    "true": {"pump.D_rev": 3.6e-7, "pump.k_leak": 3e-11, "pump.eta_m": 0.7},
    # szum wartości uśrednionych w stanie ustalonym (kilka sekund zapisu na punkt)
    "noise": {"i": 0.005, "w": 0.5, "dp": 200.0, "Q": 1e-7},
    "U": [3.0, 6.0, 9.0],
    "G": np.geomspace(4e-10, 1e-8, 5).tolist(),
}
PUMP_SIGNALS = ["i", "w", "dp", "Q"]


def pump_synthetic(seed=2):
    """Punkty pracy z PumpBench: „prawdziwy” silnik z kroku 2 i „prawdziwa” pompa, plus szum czujników."""
    work_dir = om_fast.compile_model(PUMP["model"])
    params = PUMP["true"] | MOTOR["true"]
    cases = [(f"U{u:g}_G{j}", params | {"U": u, "G_throttle": g}, None)
             for u in PUMP["U"] for j, g in enumerate(PUMP["G"])]
    sols = om_fast.run_many(work_dir, PUMP["model"], cases, ["time", *PUMP_SIGNALS])
    U = np.array([c[1]["U"] for c in cases])
    rng = np.random.default_rng(seed)
    meas = {s: np.array([sol[s][-1] for sol in sols]) for s in PUMP_SIGNALS}  # stan ustalony (koniec przebiegu)
    meas = {s: y + rng.normal(0.0, PUMP["noise"][s], y.size) for s, y in meas.items()}
    return U, meas


def pump_fit(meas, motor):
    """Regresja liniowa na punktach pracy. motor: wartości i kowariancja ln(p) silnika z kroku 2.

    Q = D·w − k_leak·Δp          -> D, k_leak (zwykłe najmniejsze kwadraty, 2 parametry)
    τ = k·i − b·w = c·Δp,  c = D/η_m  -> η_m = D/c
    Niepewność c ma dwa źródła: rozrzut punktów i niepewność k, b silnika (ten sam błąd we wszystkich punktach,
    więc nie uśrednia się przy większej liczbie punktów).
    """
    w, dp, Q, i = meas["w"], meas["dp"], meas["Q"], meas["i"]
    X = np.column_stack([w, -dp])
    beta, *_ = np.linalg.lstsq(X, Q, rcond=None)
    rQ = Q - X @ beta
    cov_q = np.linalg.inv(X.T @ X) * (rQ @ rQ / (len(Q) - 2))
    D, k_leak = beta

    m = dict(zip(motor["names"], motor["values"]))
    im = {n: j for j, n in enumerate(motor["names"])}
    k, b = m["motor.k"], m["motor.b"]
    tau = k * i - b * w
    c = tau @ dp / (dp @ dp)
    r_tau = tau - c * dp
    var_c_pts = (r_tau @ r_tau / (len(dp) - 1)) / (dp @ dp)
    g = np.array([k * (i @ dp), -b * (w @ dp)]) / (dp @ dp)  # dc/d ln k, dc/d ln b
    S = np.array(motor["cov_ln"])[np.ix_([im["motor.k"], im["motor.b"]], [im["motor.k"], im["motor.b"]])]
    var_c_motor = g @ S @ g
    eta = D / c

    rel = {"pump.D_rev": np.sqrt(cov_q[0, 0]) / D, "pump.k_leak": np.sqrt(cov_q[1, 1]) / k_leak}
    rel_c_pts, rel_c_motor = np.sqrt(var_c_pts) / c, np.sqrt(var_c_motor) / c
    # ln η = ln D − ln c; D i c pochodzą z niezależnych pomiarów (przepływ vs prąd), więc wariancje się sumują
    rel["pump.eta_m"] = np.sqrt(rel["pump.D_rev"] ** 2 + rel_c_pts ** 2 + rel_c_motor ** 2)
    values = {"pump.D_rev": 2 * np.pi * D, "pump.k_leak": k_leak, "pump.eta_m": eta}
    extra = {"rel_c_pts": rel_c_pts, "rel_c_motor": rel_c_motor, "rQ": rQ, "r_tau": r_tau, "tau": tau, "c": c,
             "D": D, "k_leak": k_leak}
    return values, rel, extra


def pump_report(values, rel, extra, truth=None):
    lines = [f"{'parametr':<13}{'start':>11}{'dopasowany':>13}{'±1σ':>9}" + (f"{'prawdziwy':>13}{'błąd':>9}" if truth else "")]
    for n, v in values.items():
        p0, unit = PUMP["params"][n]
        line = f"{n:<13}{p0:>11.4g}{v:>13.5g}{100 * rel[n]:>8.2f}%"
        if truth:
            line += f"{truth[n]:>13.5g}{100 * (v / truth[n] - 1):>8.2f}%"
        lines.append(f"{line}   [{unit}]")
    lines.append("")
    lines.append(f"niepewność c = D/η_m: z rozrzutu punktów {100 * extra['rel_c_pts']:.2f}%, "
                 f"z niepewności silnika (k, b) {100 * extra['rel_c_motor']:.2f}%")
    lines.append(f"RMS reszt: przepływ {np.sqrt(np.mean(extra['rQ'] ** 2)) * 1e6:.3f} ml/s, "
                 f"moment {np.sqrt(np.mean(extra['r_tau'] ** 2)) * 1e3:.3f} mN·m")
    mod = ", ".join(f"{n.split('.')[-1]}={v:.5g}" for n, v in values.items())
    lines.append(f"do modelu: FishRobot.Hydraulics.GearPump pump({mod});")
    return "\n".join(lines)


def pump_plot(U, meas, extra, title, name):
    fig, (ax_q, ax_t) = plotting.plt.subplots(1, 2, figsize=(10, 4.2))
    dp = meas["dp"] / 1e3
    leak = (meas["Q"] - extra["D"] * meas["w"]) * 1e6  # przepływ minus wyparcie geometryczne = przeciek
    line = np.linspace(0, dp.max() * 1.05, 50)
    for j, u in enumerate(sorted(set(U))):
        sel = U == u
        ax_q.plot(dp[sel], leak[sel], "o", color=plotting.SERIES[j], markersize=5, label=f"U = {u:g} V")
        ax_t.plot(dp[sel], extra["tau"][sel] * 1e3, "o", color=plotting.SERIES[j], markersize=5, label=f"U = {u:g} V")
    ax_q.plot(line, -line * 1e3 * extra["k_leak"] * 1e6, color=plotting.TEXT_2, linewidth=1.2, label="−k_leak·Δp")
    ax_q.set_xlabel("Δp [kPa]")
    ax_q.set_ylabel("Q − D·ω [ml/s]  (przeciek)")
    ax_t.plot(line, line * 1e3 * extra["c"] * 1e3, color=plotting.TEXT_2, linewidth=1.2, label="D·Δp/η_m")
    ax_t.set_xlabel("Δp [kPa]")
    ax_t.set_ylabel("k·i − b·ω [mN·m]  (moment na wale)")
    for ax in (ax_q, ax_t):
        ax.legend(loc="best")
    fig.suptitle(title, x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    return plotting.save(fig, name, "calibration")


def pump_main(args):
    motor_file = OUT / "motor_params.json"
    if not motor_file.exists():
        raise SystemExit("brak results/calibration/motor_params.json – najpierw uruchom krok 2: calibrate.py motor")
    motor = json.loads(motor_file.read_text())
    if args.data:
        data = np.genfromtxt(args.data, delimiter=",", names=True)
        U = data["U"]
        meas = {s: data[s] for s in PUMP_SIGNALS}
        truth = None
    else:
        U, meas = pump_synthetic()
        truth = PUMP["true"]
        np.savetxt(OUT / "pump_bench_synthetic.csv", np.column_stack([U, *(meas[s] for s in PUMP_SIGNALS)]),
                   delimiter=",", header="U,i,w,dp,Q", comments="", fmt="%.6g")
    values, rel, extra = pump_fit(meas, motor)
    text = pump_report(values, rel, extra, truth)
    print(text)
    (OUT / "pump_fit.txt").write_text(text + "\n")
    src = "pomiar syntetyczny" if truth else args.data
    print(pump_plot(U, meas, extra, f"Kalibracja pompy: {len(U)} punktów pracy ({src})", "pump_fit.png"))


# --- Krok 4: przewód -------------------------------------------------------------------------------

PIPE = {
    "model": "FishRobot.Calibration.PipeBench",
    "params": {"pipe.d": (4e-3, "m"), "pipe.zeta": (1.5, "–"), "pipe.roughness": (2.5e-5, "m")},
    "signals": {"dp": ("Pa", "spadek ciśnienia")},
    "log": True,
    # „prawdziwy” przewód: wąż o średnicy wewnętrznej mniejszej od nominalnej, gładki, z kilkoma złączkami
    "true": {"pipe.d": 3.6e-3, "pipe.zeta": 2.5, "pipe.roughness": 5e-6},
    "noise_rel": 0.01,  # czujnik różnicowy: 1% odczytu
    "Q": np.geomspace(1e-6, 4e-5, 20).tolist(),  # 1–40 ml/s, Re ok. 350–14 000
    "component": "FishRobot.Hydraulics.Pipe pipe",
}


def pipe_plot(Q, dp, sim_fit, sim_start, d_fit, title, name):
    nu = 1.002e-3 / 998.2
    fig, (ax, ax_r) = plotting.plt.subplots(2, 1, figsize=(9, 6.2), sharex=True, gridspec_kw={"height_ratios": [3, 1.3]})
    q = Q * 1e6
    # Zakres przejściowy Re 2000–4000 przy dopasowanej średnicy: Q = Re·ν·π·d/4
    q_re = [re * nu * np.pi * d_fit / 4 * 1e6 for re in (2000, 4000)]
    for a in (ax, ax_r):
        a.axvspan(*q_re, color=plotting.GRID, alpha=0.7, linewidth=0)
    ax.annotate("przejście\nRe 2000–4000", (np.sqrt(q_re[0] * q_re[1]), 0.97), xycoords=("data", "axes fraction"),
                ha="center", va="top", color=plotting.TEXT_2, fontsize=9)
    ax.plot(q, dp / 1e3, "o", color="#9a9994", markersize=4, label="pomiar")
    ax.plot(q, sim_start["dp"] / 1e3, color=plotting.SERIES[1], linestyle=(0, (4, 3)), linewidth=1.5,
            label="start (placeholdery)")
    ax.plot(q, sim_fit["dp"] / 1e3, color=plotting.SERIES[0], label="dopasowanie")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylabel("Δp [kPa]")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, borderaxespad=0.2)
    ax.set_title(title, loc="left", fontsize=11, pad=26)
    ax_r.plot(q, (dp / sim_fit["dp"] - 1) * 100, "o-", color=plotting.SERIES[0], markersize=3, linewidth=0.8)
    ax_r.axhline(0, color=plotting.TEXT_2, linewidth=0.8)
    ax_r.set_ylabel("reszty [%]")
    ax_r.set_xlabel("Q [ml/s]")
    fig.align_ylabels((ax, ax_r))
    return plotting.save(fig, name, "calibration")


def pipe_main(args):
    exp = PIPE
    work_dir = om_fast.compile_model(exp["model"])
    if args.data:
        data = np.genfromtxt(args.data, delimiter=",", names=True)
        order = np.argsort(data["Q"])
        Q, dp = data["Q"][order], data["dp"][order]
        truth = None
    else:
        Q = np.array(exp["Q"])
        truth = exp["true"]
    setup = {"l": args.l, "Q_max": Q[-1]}
    t = Q / Q[-1]  # w PipeBench chwila t odpowiada przepływowi Q_max·t
    if truth:
        clean = simulate(work_dir, exp, [truth[p] for p in exp["params"]], "true", setup, t)["dp"]
        dp = clean * (1 + np.random.default_rng(3).normal(0.0, exp["noise_rel"], clean.size))
        np.savetxt(OUT / "pipe_synthetic.csv", np.column_stack([Q, dp]), delimiter=",", header="Q,dp",
                   comments="", fmt="%.6g")

    p_fit, sigma, cov, res, noise = fit(work_dir, exp, t, {"dp": dp}, setup)
    text = report(exp, p_fit, sigma, cov, res, noise, truth)
    print(text)
    (OUT / "pipe_fit.txt").write_text(text + "\n")
    sim_fit = simulate(work_dir, exp, p_fit, "fit", setup, t)
    sim_start = simulate(work_dir, exp, [v for v, _ in exp["params"].values()], "start", setup, t)
    src = "pomiar syntetyczny" if truth else args.data
    print(pipe_plot(Q, dp, sim_fit, sim_start, p_fit[0], f"Kalibracja przewodu: l = {args.l:g} m ({src})",
                    "pipe_fit.png"))


# --- Krok 5: komora ---------------------------------------------------------------------------------

CHAMBER = {
    "model": "FishRobot.Calibration.ChamberBench",
    # „prawdziwa” komora: krzywa szkieletowa p = E·V0·(exp(ΔV/V0) − 1), histereza i efekt Mullinsa
    "E": 0.8e9, "V0": 3e-6,             # sztywność przy ΔV = 0 [Pa/m³] i skala usztywniania [m³]
    "h0": 300.0, "h1": 0.06,           # półszerokość pętli: h0 + h1·|p| [Pa]
    "x_h": 0.3e-6,                     # objętość, na której histereza „przełącza się” po zawróceniu [m³]
    "mullins": 1.15,                   # pierwsze napełnienie o 15% sztywniejsze
    "stroke": (-3e-6, 10e-6), "cycles": 4, "n_stroke": 200,
    "noise_p": 150.0, "noise_V": 1e-8,  # czujnik ciśnienia [Pa], rozdzielczość strzykawki [m³]
}


def chamber_backbone(x, c=CHAMBER):
    return c["E"] * c["V0"] * (np.exp(x / c["V0"]) - 1)


def chamber_synthetic(seed=4):
    """Kilka cykli strzykawki ΔV: 0 → max → min → max ... z histerezą (model „play” z wygładzeniem)."""
    c = CHAMBER
    lo, hi = c["stroke"]
    path = [np.linspace(0, hi, c["n_stroke"])]
    for k in range(c["cycles"]):
        path += [np.linspace(hi, lo, 2 * c["n_stroke"])[1:], np.linspace(lo, hi, 2 * c["n_stroke"])[1:]]
    path.append(np.linspace(hi, 0, c["n_stroke"])[1:])
    x = np.concatenate(path)
    first_max = c["n_stroke"] - 1
    p = np.empty_like(x)
    y = 0.0  # przesunięcie histerezy: dąży do ±(h0 + h1·|p|) w kierunku ruchu
    for n in range(len(x)):
        pb = chamber_backbone(x[n]) * (c["mullins"] if n <= first_max else 1.0)
        if n:
            dx = x[n] - x[n - 1]
            target = np.sign(dx) * (c["h0"] + c["h1"] * abs(pb))
            y += (target - y) * (1 - np.exp(-abs(dx) / c["x_h"]))
        p[n] = pb + y
    rng = np.random.default_rng(seed)
    return x + rng.normal(0, c["noise_V"], x.size), p + rng.normal(0, c["noise_p"], x.size)


def chamber_process(x, p, skip=2, n_nodes=15, margin=1e-6):
    """Podział na suwy (między zawróceniami strzykawki), odrzucenie pierwszych `skip` suwów,
    średnie gałęzie napełniania i opróżniania w węzłach, krzywa szkieletowa i pole pętli."""
    xs = np.convolve(x, np.ones(9) / 9, mode="same")  # wygładzenie tylko do wykrycia kierunku
    direction = np.sign(np.diff(xs))
    direction[direction == 0] = 1
    cut = np.flatnonzero(np.diff(direction)) + 1
    strokes = [(a, b) for a, b in zip(np.r_[0, cut], np.r_[cut, len(x) - 1]) if b - a > 20][skip:]
    # Zakres węzłów: mediana skrajnych położeń suwów (szum położenia nie przesuwa końców tabeli),
    # pomniejszona o margines. W punkcie zawrócenia obie gałęzie spotykają się na czubku pętli, a nie na
    # krzywej szkieletowej: histereza potrzebuje ok. x_h, żeby się „przełączyć”.
    lo = np.median([x[a:b + 1].min() for a, b in strokes]) + margin
    hi = np.median([x[a:b + 1].max() for a, b in strokes]) - margin
    nodes = np.linspace(lo, hi, n_nodes)
    half = (hi - lo) / (n_nodes - 1) / 2
    branch = {1: [], -1: []}
    for a, b in strokes:
        xx, pp = x[a:b + 1], p[a:b + 1]
        d = 1 if xx[-1] > xx[0] else -1
        order = np.argsort(xx)
        # tylko węzły, które ten suw w całości pokrywa (suwy częściowe nie zaniżają końców)
        inside = (nodes >= xx.min() - half) & (nodes <= xx.max() + half)
        row = np.full(n_nodes, np.nan)
        # lokalna regresja liniowa w oknie wokół węzła zamiast interpolacji punktowej (mniej szumu)
        for j in np.flatnonzero(inside):
            win = np.abs(xx - nodes[j]) <= half
            if win.sum() >= 3:
                row[j] = np.polyval(np.polyfit(xx[win] - nodes[j], pp[win], 1), 0.0)
        branch[d].append(row)
    load, unload = (np.nanmean(branch[d], axis=0) for d in (1, -1))
    backbone = (load + unload) / 2
    # Energia tracona w cyklu: ∮ p dV wzdłuż drogi strzykawki, po parach suwów (tam i z powrotem)
    # z surowych danych, w pełnym zakresie suwu (węzły są przycięte o margines, więc zaniżałyby pętlę).
    cycles = [np.sum((p[a + 1:c + 1] + p[a:c]) / 2 * np.diff(x[a:c + 1]))
              for (a, _), (_, c) in zip(strokes[0::2], strokes[1::2])]
    loop = abs(np.mean(cycles))
    return {"nodes": nodes, "load": load, "unload": unload, "backbone": backbone, "loop": loop,
            "strokes": strokes, "monotone": bool(np.all(np.diff(backbone) > 0))}


def chamber_main(args):
    c = CHAMBER
    if args.data:
        data = np.genfromtxt(args.data, delimiter=",", names=True)
        x, p = data["dV"], data["p"]
        truth = False
    else:
        x, p = chamber_synthetic()
        truth = True
        np.savetxt(OUT / "chamber_synthetic.csv", np.column_stack([x, p]), delimiter=",", header="dV,p",
                   comments="", fmt="%.6g")
    r = chamber_process(x, p, skip=args.skip, margin=args.margin)
    if not r["monotone"]:
        print("UWAGA: krzywa szkieletowa nie jest rosnąca – Chamber jej nie przyjmie. Zmniejsz liczbę węzłów.")
    V = args.V_rest + r["nodes"]
    csv_path = OUT / "chamber_pV.csv"
    np.savetxt(csv_path, np.column_stack([V, r["backbone"]]), delimiter=",", header="V_m3,p_gauge_Pa",
               comments="", fmt="%.6g")

    # Sprawdzenie w Modelice: komora z tableOnFile = true i tym plikiem przechodzi przez cały zakres
    work_dir = om_fast.compile_model(c["model"])
    sol = om_fast.run(work_dir, c["model"], "check", {"fileName": csv_path.as_posix(), "V_min": V[0],
                                                       "V_max": V[-1]}, None, ["V", "p"])
    p_model_nodes = np.interp(V, sol["V"], sol["p"])
    span = np.ptp(r["backbone"])
    lines = [
        f"suwy użyte: {len(r['strokes'])} (pominięte pierwsze {args.skip}), węzły: {len(V)}, "
        f"ΔV {r['nodes'][0] * 1e6:.2f} … {r['nodes'][-1] * 1e6:.2f} ml",
        f"pętla histerezy (pełny suw ΔV {x.min() * 1e6:.1f} … {x.max() * 1e6:.1f} ml): {r['loop'] * 1e3:.1f} mJ na cykl",
        f"Modelica (tableOnFile) vs węzły krzywej: max {np.max(np.abs(p_model_nodes - r['backbone'])):.2g} Pa",
    ]
    if truth:
        xm = sol["V"] - args.V_rest
        err = np.max(np.abs(sol["p"] - chamber_backbone(xm))) / span
        err_nodes = np.max(np.abs(r["backbone"] - chamber_backbone(r["nodes"]))) / span
        r0 = chamber_process(x, p, skip=args.skip, margin=0.0)
        err_no_margin = np.max(np.abs(r0["backbone"] - chamber_backbone(r0["nodes"]))) / np.ptp(r0["backbone"])
        lines.append(f"węzły vs prawdziwa krzywa szkieletowa: max {100 * err_nodes:.2f}% zakresu "
                     f"(bez marginesu od zawróceń: {100 * err_no_margin:.1f}%)")
        lines.append(f"Modelica vs prawdziwa krzywa szkieletowa (między węzłami też): max {100 * err:.2f}% zakresu")
        lines.append(f"ta sama krzywa z pierwszym suwem (Mullins): "
                     f"{100 * np.max(np.abs(chamber_process(x, p, skip=0, margin=args.margin)['backbone'] - chamber_backbone(r['nodes']))) / span:.1f}% zakresu")
    lines.append(f"plik dla Chamber(tableOnFile=true, fileName=...): {csv_path}")
    text = "\n".join(lines)
    print(text)
    (OUT / "chamber_fit.txt").write_text(text + "\n")

    fig, ax = plotting.plt.subplots(figsize=(9, 5.5))
    ax.plot(x * 1e6, p / 1e3, ".", color="#cfceca", markersize=2, label="pomiar")
    a, b = r["strokes"][0]
    ax.plot(x[:a] * 1e6, p[:a] / 1e3, ".", color=plotting.SERIES[3], markersize=2, label="pominięte (pierwszy cykl)")
    ax.plot(r["nodes"] * 1e6, r["load"] / 1e3, "^", color=plotting.SERIES[1], markersize=6, label="napełnianie")
    ax.plot(r["nodes"] * 1e6, r["unload"] / 1e3, "v", color=plotting.SERIES[2], markersize=6, label="opróżnianie")
    ax.plot(xm_all := (sol["V"] - args.V_rest) * 1e6, sol["p"] / 1e3, color=plotting.SERIES[0],
            label="Chamber z wyznaczoną krzywą")
    tab = np.loadtxt(C.PACKAGE_DIR / "Resources/Data/chamber_pV_placeholder.csv", delimiter=",", skiprows=1)
    ax.plot((tab[:, 0] - 5e-6) * 1e6, tab[:, 1] / 1e3, color=plotting.SERIES[4], linestyle=(0, (4, 3)),
            linewidth=1.5, label="placeholder (spoczynek 5 ml)")
    ax.set_xlim(x.min() * 1e6 - 0.3, x.max() * 1e6 + 0.3)
    ax.set_ylim(min(p.min(), r["backbone"].min()) / 1e3 - 3, p.max() / 1e3 + 5)
    ax.set_xlabel("ΔV ze strzykawki [ml]")
    ax.set_ylabel("nadciśnienie [kPa]")
    ax.legend(loc="upper left")
    src = "pomiar syntetyczny" if truth else args.data
    ax.set_title(f"Kalibracja komory: krzywa p–V ({src})", loc="left", fontsize=11)
    print(plotting.save(fig, "chamber_fit.png", "calibration"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="step", required=True)
    m = sub.add_parser("motor", help="krok 2: silnik DC ze skoku napięcia")
    m.add_argument("--data", help="CSV z pomiarem (time, i, w); bez tej opcji: pomiar syntetyczny")
    m.add_argument("--U", type=float, default=6.0, help="napięcie zasilacza po skoku [V]")
    m.add_argument("--t-step", type=float, default=0.01, help="chwila skoku napięcia w pomiarze [s]")
    p = sub.add_parser("pump", help="krok 3: pompa z punktów pracy (wymaga wyniku kroku 2)")
    p.add_argument("--data", help="CSV z punktami pracy (U, i, w, dp, Q); bez tej opcji: pomiar syntetyczny")
    q = sub.add_parser("pipe", help="krok 4: przewód z charakterystyki Δp(Q)")
    q.add_argument("--data", help="CSV z punktami (Q [m³/s], dp [Pa]); bez tej opcji: pomiar syntetyczny")
    q.add_argument("--l", type=float, default=0.2, help="zmierzona długość przewodu [m]")
    k = sub.add_parser("chamber", help="krok 5: krzywa p–V komory z cykli strzykawki")
    k.add_argument("--data", help="CSV w kolejności czasu (dV [m³], p [Pa]); bez tej opcji: pomiar syntetyczny")
    k.add_argument("--V-rest", type=float, default=5e-6,
                   help="objętość komory w spoczynku (CAD lub ważenie) [m³]; tabela ma V = V_rest + ΔV")
    k.add_argument("--skip", type=int, default=2, help="liczba pierwszych suwów do pominięcia (efekt Mullinsa)")
    k.add_argument("--margin", type=float, default=1e-6,
                   help="odstęp węzłów od punktów zawrócenia strzykawki [m³] (czubki pętli histerezy)")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    {"motor": motor_main, "pump": pump_main, "pipe": pipe_main, "chamber": chamber_main}[args.step](args)


if __name__ == "__main__":
    main()
