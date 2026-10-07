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
  .venv/bin/python scripts/calibrate.py valve [--data punkty.csv]
  .venv/bin/python scripts/calibrate.py tail-static [--data punkty.csv --k small]
  .venv/bin/python scripts/calibrate.py tail-dynamic [--data-air a.csv --data-water w.csv]
  .venv/bin/python scripts/calibrate.py thrust [--data punkty.csv --noise-abs 1e-4 --noise-rel 0.05]
  .venv/bin/python scripts/calibrate.py hull [--data-tow h.csv --data-coast w.csv --A 0.005 --m 1.0]

Krok 6, zawór przelewowy (calibrate.py valve): charakterystyka Q(Δp) przy rosnącym i malejącym przepływie,
dopasowanie jak w kroku 4, osobno dla obu gałęzi (histereza grzybka) i wspólnie.

Krok 7, ogon statycznie (calibrate.py tail-static): moment na zablokowanym ogonie i kąt swobodnego ogona
przy zadanym Δp; regresja liniowa daje D_tail i k, test członu Δp³ wykrywa nieliniową sztywność.

Krok 8, ogon dynamicznie (calibrate.py tail-dynamic): drgania swobodne w powietrzu (J, c) i w wodzie
(J_added, c, c_h), dopasowanie symulacji TailDecay przy k z kroku 7 (z samego θ(t) wynikają tylko ilorazy przez J).

Krok 9, ciąg płetwy (calibrate.py thrust): średni ciąg na siłomierzu przy kilku f, Θ i U; ThrustBench liczy ciąg
dla C_T = 1, a C_T wynika z regresji ważonej modelem szumu siłomierza. Test postaci: kara za U² vs teoria.

Krok 10, kadłub (calibrate.py hull): C_d z holowania (regresja ważona), m_added_x z wybiegu CoastDown
(wybieg wyznacza tylko k_d/M, więc C_d i m pochodzą z innych pomiarów).

Pliki pomiaru: CSV z nagłówkiem; silnik: time [s], i [A], w [rad/s]; pompa: U [V], i [A], w [rad/s],
dp [Pa], Q [m³/s];
przewód: Q [m³/s], dp [Pa]; komora (w kolejności czasu): dV [m³], p [Pa];
zawór: dp [Pa], Q [m³/s], up (1 = przepływ rośnie);
ogon statycznie: dp_blocked [Pa], tau [N·m], dp_free [Pa], theta [rad]; ogon dynamicznie: time [s], theta [rad];
ciąg: Theta [rad], f [Hz], U [m/s], T [N];
kadłub: holowanie U [m/s], F [N]; wybieg time [s], x [m].
Wyniki -> results/calibration/.
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


# --- Krok 6: zawór przelewowy -----------------------------------------------------------------------

VALVE = {
    "model": "FishRobot.Calibration.ValveBench",
    "params": {"valve.p_set": (50e3, "Pa"), "valve.V_flow_nominal": (2e-5, "m³/s"), "valve.dp_smooth": (500.0, "Pa")},
    "signals": {"Q": ("m³/s", "przepływ")},
    # „prawdziwy” zawór: sprężyna słabsza od nominalnej, większa przewodność, łagodniejsze otwarcie
    # i histereza grzybka: otwiera się o hyst wyżej, niż się zamyka
    "true": {"valve.p_set": 46e3, "valve.V_flow_nominal": 1.4e-5, "valve.dp_smooth": 1500.0},
    "hyst": 2e3,
    "noise": {"Q": 5e-8, "dp": 100.0},  # przepływomierz 0,05 ml/s, czujnik różnicowy 100 Pa
    "dp_range": (35e3, 56e3), "n": 15,
    "component": "FishRobot.Hydraulics.ReliefValve valve",
}


def valve_main(args):
    exp = VALVE
    work_dir = om_fast.compile_model(exp["model"])
    lo, hi = 30e3, 60e3
    setup = {"dp_lo": lo, "dp_hi": hi}
    if args.data:
        data = np.genfromtxt(args.data, delimiter=",", names=True)
        dp, Q, up = data["dp"], data["Q"], data["up"].astype(bool)
        truth = None
    else:
        truth = exp["true"]
        grid = np.linspace(*exp["dp_range"], exp["n"])
        rng = np.random.default_rng(5)
        dp_parts, Q_parts, up_parts = [], [], []
        for direction, shift in ((True, exp["hyst"] / 2), (False, -exp["hyst"] / 2)):
            values = [truth[n] + (shift if n == "valve.p_set" else 0) for n in exp["params"]]
            q = simulate(work_dir, exp, values, f"true_{int(direction)}", setup, (grid - lo) / (hi - lo))["Q"]
            dp_parts.append(grid + rng.normal(0, exp["noise"]["dp"], grid.size))
            Q_parts.append(q + rng.normal(0, exp["noise"]["Q"], grid.size))
            up_parts.append(np.full(grid.size, direction))
        dp, Q, up = (np.concatenate(v) for v in (dp_parts, Q_parts, up_parts))
        np.savetxt(OUT / "valve_synthetic.csv", np.column_stack([dp, Q, up]), delimiter=",", header="dp,Q,up",
                   comments="", fmt="%.6g")

    def fit_subset(mask):
        order = np.argsort(dp[mask])
        t = (dp[mask][order] - lo) / (hi - lo)
        return fit(work_dir, exp, t, {"Q": Q[mask][order]}, setup)

    p_fit, sigma, cov, res, noise = fit_subset(np.ones_like(up))
    text = report(exp, p_fit, sigma, cov, res, noise, truth)
    branches = {}
    for name, mask in (("otwieranie", up), ("zamykanie", ~up)):
        pb, sb, *_ = fit_subset(mask)
        branches[name] = pb
        text += f"\ngałąź {name}: p_set = {pb[0] / 1e3:.2f} kPa ± {sb[0] * pb[0] / 1e3:.2f}"
    width = branches["otwieranie"][0] - branches["zamykanie"][0]
    text += f"\nhistereza grzybka: {width / 1e3:.2f} kPa" + (f" (prawdziwa {exp['hyst'] / 1e3:g} kPa)" if truth else "")
    print(text)
    (OUT / "valve_fit.txt").write_text(text + "\n")

    t_plot = np.linspace(0, 1, 301)
    dp_plot = lo + (hi - lo) * t_plot
    curves = {k: simulate(work_dir, exp, v, f"plot_{i}", setup, t_plot)["Q"]
              for i, (k, v) in enumerate([("fit", p_fit), ("start", [v for v, _ in exp["params"].values()]),
                                          *branches.items()])}
    fig, (ax, ax_r) = plotting.plt.subplots(2, 1, figsize=(9, 6.2), sharex=True, gridspec_kw={"height_ratios": [3, 1.3]})
    ax.plot(dp[up] / 1e3, Q[up] * 1e6, "^", color=plotting.SERIES[1], markersize=5, label="pomiar: otwieranie")
    ax.plot(dp[~up] / 1e3, Q[~up] * 1e6, "v", color=plotting.SERIES[2], markersize=5, label="pomiar: zamykanie")
    ax.plot(dp_plot / 1e3, curves["fit"] * 1e6, color=plotting.SERIES[0], label="dopasowanie (jedno p_set)")
    ax.plot(dp_plot / 1e3, curves["start"] * 1e6, color=plotting.SERIES[4], linestyle=(0, (4, 3)), linewidth=1.5,
            label="start (placeholdery)")
    ax.set_xlim(dp.min() / 1e3 - 1, dp.max() / 1e3 + 1)
    ax.set_ylim(-1, Q.max() * 1e6 * 1.1)
    ax.set_ylabel("Q [ml/s]")
    ax.legend(loc="upper left")
    src = "pomiar syntetyczny" if truth else args.data
    ax.set_title(f"Kalibracja zaworu przelewowego ({src})", loc="left", fontsize=11)
    q_fit = np.interp(dp, dp_plot, curves["fit"])
    ax_r.plot(dp[up] / 1e3, (Q[up] - q_fit[up]) * 1e6, "^", color=plotting.SERIES[1], markersize=4)
    ax_r.plot(dp[~up] / 1e3, (Q[~up] - q_fit[~up]) * 1e6, "v", color=plotting.SERIES[2], markersize=4)
    ax_r.axhline(0, color=plotting.TEXT_2, linewidth=0.8)
    ax_r.set_ylabel("reszty [ml/s]")
    ax_r.set_xlabel("Δp [kPa]")
    fig.align_ylabels((ax, ax_r))
    print(plotting.save(fig, "valve_fit.png", "calibration"))


# --- Krok 7: ogon statycznie ------------------------------------------------------------------------

TAIL_STATIC = {
    # „prawdziwy” ogon: sztywność rośnie z kątem k·(1 + beta·θ²), czego model (stałe k) nie ma
    "true": {"D_tail": 1.6e-5, "k": 2.6, "beta": 0.6},
    "dp": np.linspace(-40e3, 40e3, 17).tolist(),
    "noise": {"tau": 2e-3, "theta": 0.0035, "dp": 100.0},  # siłomierz [N·m], kąt [rad] (0,2°), Δp [Pa]
}


def tail_static_synthetic(seed=6):
    c = TAIL_STATIC
    D, k, beta = c["true"]["D_tail"], c["true"]["k"], c["true"]["beta"]
    dp = np.array(c["dp"])
    tau = D * dp
    theta = np.array([np.roots([k * beta, 0, k, -D * x])[-1].real for x in dp])  # k·θ·(1 + β·θ²) = D·Δp
    rng = np.random.default_rng(seed)
    noisy = lambda y, n: y + rng.normal(0, c["noise"][n], y.size)
    return noisy(dp, "dp"), noisy(tau, "tau"), noisy(dp, "dp"), noisy(theta, "theta")


def tail_static_fit(dp_b, tau, dp_f, theta):
    """Zablokowany ogon: τ = D_tail·Δp. Swobodny ogon: θ = (D_tail/k)·Δp. Obie proste przez zero."""
    def slope(x, y):
        s = y @ x / (x @ x)
        r = y - s * x
        return s, np.sqrt(r @ r / (len(x) - 1) / (x @ x)) / abs(s), r

    D, rel_D, r_tau = slope(dp_b, tau)
    sl, rel_s, r_theta = slope(dp_f, theta)
    # Test nieliniowości: współczynnik przy Δp³ w θ = a·Δp + b·Δp³ i jego statystyka t
    X = np.column_stack([dp_f, dp_f ** 3])
    ab, *_ = np.linalg.lstsq(X, theta, rcond=None)
    r3 = theta - X @ ab
    cov3 = np.linalg.inv(X.T @ X) * (r3 @ r3 / (len(theta) - 2))
    return {"D_tail": D, "rel_D": rel_D, "k": D / sl, "rel_k": np.hypot(rel_D, rel_s),
            "k0": D / ab[0], "rel_k0": np.hypot(rel_D, np.sqrt(cov3[0, 0]) / ab[0]), "t_cubic": ab[1] / np.sqrt(cov3[1, 1]), "r_tau": r_tau, "r_theta": r_theta,
            "slope": sl, "ab": ab}


def tail_static_main(args):
    if args.data:
        b = np.genfromtxt(args.data, delimiter=",", names=True)
        dp_b, tau, dp_f, theta = b["dp_blocked"], b["tau"], b["dp_free"], b["theta"]
        truth = None
    else:
        dp_b, tau, dp_f, theta = tail_static_synthetic()
        truth = TAIL_STATIC["true"]
        np.savetxt(OUT / "tail_static_synthetic.csv", np.column_stack([dp_b, tau, dp_f, theta]), delimiter=",",
                   header="dp_blocked,tau,dp_free,theta", comments="", fmt="%.6g")
    r = tail_static_fit(dp_b, tau, dp_f, theta)
    lines = [f"D_tail = {r['D_tail']:.5g} m³/rad ± {100 * r['rel_D']:.2f}%"
             + (f"   (prawdziwe {truth['D_tail']:.5g}, błąd {100 * (r['D_tail'] / truth['D_tail'] - 1):+.2f}%)" if truth else ""),
             f"k      = {r['k']:.5g} N·m/rad ± {100 * r['rel_k']:.2f}%   (prosta w całym zakresie ±{np.degrees(np.abs(theta).max()):.0f}°)"
             + (f"   (prawdziwe przy θ → 0: {truth['k']:.5g})" if truth else ""),
             f"test nieliniowości θ(Δp): t = {r['t_cubic']:.1f} dla członu Δp³"]
    if abs(r["t_cubic"]) > 3:
        lines.append(f"  -> charakterystyka nieliniowa (sztywność {'rośnie' if r['ab'][1] < 0 else 'maleje'} z kątem); "
                     f"przy małych kątach k = {r['k0']:.4g} N·m/rad ± {100 * r['rel_k0']:.1f}%. Model ma stałe k: wybierz wartość dla zakresu pracy.")
    lines.append(f"do modelu: FishRobot.Tail.TailEquivalent tail(D_tail={r['D_tail']:.5g}, k={r['k']:.5g});")
    text = "\n".join(lines)
    print(text)
    k_out = [r["k0"], r["rel_k0"]] if args.k == "small" else [r["k"], r["rel_k"]]
    text += f"\ndo kroku 8 idzie k = {k_out[0]:.5g} ± {100 * k_out[1]:.2f}% ({'małe kąty' if args.k == 'small' else 'prosta w całym zakresie'})"
    print(text.splitlines()[-1])
    (OUT / "tail_params.json").write_text(json.dumps({"D_tail": [r["D_tail"], r["rel_D"]], "k": k_out}, indent=1))
    (OUT / "tail_static_fit.txt").write_text(text + "\n")

    fig, axes = plotting.plt.subplots(2, 2, figsize=(10, 6), sharex="col", gridspec_kw={"height_ratios": [3, 1.3]})
    line = np.linspace(min(dp_b.min(), dp_f.min()), max(dp_b.max(), dp_f.max()), 50)
    axes[0, 0].plot(dp_b / 1e3, tau * 1e3, "o", color=plotting.SERIES[0], markersize=5, label="pomiar")
    axes[0, 0].plot(line / 1e3, r["D_tail"] * line * 1e3, color=plotting.TEXT_2, linewidth=1.2, label="D_tail·Δp")
    axes[0, 0].set_ylabel("moment [mN·m]")
    axes[0, 0].set_title("ogon zablokowany", loc="left", fontsize=10)
    axes[0, 1].plot(dp_f / 1e3, np.degrees(theta), "o", color=plotting.SERIES[1], markersize=5, label="pomiar")
    axes[0, 1].plot(line / 1e3, np.degrees(r["slope"] * line), color=plotting.TEXT_2, linewidth=1.2,
                    label="D_tail·Δp/k")
    axes[0, 1].set_ylabel("kąt [°]")
    axes[0, 1].set_title("ogon swobodny", loc="left", fontsize=10)
    axes[1, 0].plot(dp_b / 1e3, r["r_tau"] * 1e3, "o", color=plotting.SERIES[0], markersize=4)
    axes[1, 0].set_ylabel("reszty [mN·m]")
    axes[1, 1].plot(dp_f / 1e3, np.degrees(r["r_theta"]), "o", color=plotting.SERIES[1], markersize=4)
    axes[1, 1].set_ylabel("reszty [°]")
    for ax in axes[1]:
        ax.axhline(0, color=plotting.TEXT_2, linewidth=0.8)
        ax.set_xlabel("Δp = p_L − p_R [kPa]")
    for ax in axes[0]:
        ax.legend(loc="upper left")
    src = "pomiar syntetyczny" if truth else args.data
    fig.suptitle(f"Kalibracja ogona statycznie ({src})", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    print(plotting.save(fig, "tail_static_fit.png", "calibration"))


# --- Krok 8: ogon dynamicznie (drgania swobodne) ----------------------------------------------------

TAIL_DECAY = {
    "model": "FishRobot.Calibration.TailDecay",
    "signals": {"theta": ("rad", "kąt ogona")},
    "component": "FishRobot.Tail.TailEquivalent tail",
    "air": {"params": {"tail.J": (5e-4, "kg·m²"), "tail.c": (5e-3, "N·m·s/rad"), "theta0": (0.3, "rad")},
            "true": {"tail.J": 4e-4, "tail.c": 3e-3, "theta0": 0.35},
            "fixed": {"tail.J_added": 0.0, "tail.c_h": 0.0}},
    "water": {"params": {"tail.J_added": (1e-3, "kg·m²"), "tail.c": (5e-3, "N·m·s/rad"),
                         "tail.c_h": (1e-2, "N·m·s²/rad²"), "theta0": (0.3, "rad")},
              "true": {"tail.J_added": 1.4e-3, "tail.c": 6e-3, "tail.c_h": 2e-2, "theta0": 0.5},
              "fixed": {}},
    "k_true": 2.6,
    "dt": 2e-3, "t_end": 1.5, "noise": 0.003,  # enkoder/kamera 500 Hz, szum 0,17°
}


def tail_dynamic_main(args):
    c = TAIL_DECAY
    tail_file = OUT / "tail_params.json"
    if not tail_file.exists():
        raise SystemExit("brak results/calibration/tail_params.json – najpierw uruchom krok 7: calibrate.py tail-static")
    k, rel_k = json.loads(tail_file.read_text())["k"]
    work_dir = om_fast.compile_model(c["model"])
    t = np.arange(0, c["t_end"] + c["dt"] / 2, c["dt"])
    results = {}
    lines = []
    J_air = None
    for medium in ("air", "water"):
        e = c[medium]
        exp = {"model": c["model"], "signals": c["signals"], "params": e["params"], "component": c["component"]}
        setup = {"tail.k": k} | e["fixed"] | ({"tail.J": J_air[0]} if medium == "water" else {})
        if getattr(args, f"data_{medium}"):
            d = np.genfromtxt(getattr(args, f"data_{medium}"), delimiter=",", names=True)
            tt, meas = d["time"], {"theta": d["theta"]}
            truth = None
        else:
            truth = e["true"]
            # „prawdziwy” ogon ma prawdziwe k i J, a nie te z kalibracji
            true_setup = setup | {"tail.k": c["k_true"]} | ({"tail.J": c["air"]["true"]["tail.J"]} if medium == "water" else {})
            clean = simulate(work_dir, exp, [truth[n] for n in exp["params"]], f"true_{medium}", true_setup, t)
            tt = t
            meas = {"theta": clean["theta"] + np.random.default_rng(7 if medium == "air" else 8).normal(0, c["noise"], t.size)}
            np.savetxt(OUT / f"tail_decay_{medium}_synthetic.csv", np.column_stack([tt, meas["theta"]]), delimiter=",",
                       header="time,theta", comments="", fmt="%.6g")
        p_fit, sigma, cov, res, noise = fit(work_dir, exp, tt, meas, setup)
        results[medium] = (exp, p_fit, sigma)
        title = {"air": "w powietrzu", "water": "w wodzie"}[medium]
        lines += [f"=== drgania swobodne {title} (k = {k:.4g} N·m/rad z kroku 7) ===",
                  report(exp, p_fit, sigma, cov, res, noise, truth), ""]
        if medium == "air":
            J_air = (p_fit[0], sigma[0])
        sim_fit = simulate(work_dir, exp, p_fit, f"fit_{medium}", setup, tt)
        sim_start = simulate(work_dir, exp, [v for v, _ in exp["params"].values()], f"start_{medium}", setup, tt)
        src = "pomiar syntetyczny" if truth else getattr(args, f"data_{medium}")
        print(plot(exp, tt, meas, sim_fit, sim_start, f"Kalibracja ogona: drgania swobodne {title} ({src})",
                   f"tail_decay_{medium}.png"))

    # Niepewność całkowita: wszystkie parametry dynamiczne skalują się z k (z przebiegu wynikają tylko
    # ilorazy przez bezwładność), a J_added dodatkowo dziedziczy błąd J z pomiaru w powietrzu.
    lines.append("niepewność całkowita (dopasowanie ⊕ k z kroku 7 ⊕ J z powietrza dla J_added):")
    for medium in ("air", "water"):
        exp, p_fit, sigma = results[medium]
        for j, n in enumerate(exp["params"]):
            if n == "theta0":
                continue
            tot = np.hypot(sigma[j], rel_k)
            if n == "tail.J_added":
                tot = np.hypot(tot, J_air[0] * J_air[1] / p_fit[j])
            lines.append(f"  {medium:<6}{n:<14}{p_fit[j]:>12.5g}  ±{100 * sigma[j]:.2f}% z dopasowania, ±{100 * tot:.2f}% całkowicie")
    J, c_air = results["air"][1][0], results["air"][1][1]
    Ja, c_w, c_h = results["water"][1][:3]
    lines.append(f"do modelu: FishRobot.Tail.TailEquivalent tail(k={k:.5g}, J={J:.5g}, J_added={Ja:.5g}, "
                 f"c={c_w:.5g}, c_h={c_h:.5g});  (c z wody; w powietrzu c = {c_air:.4g})")
    text = "\n".join(lines)
    print(text)
    (OUT / "tail_dynamic_fit.txt").write_text(text + "\n")


# --- Krok 9: ciąg płetwy ----------------------------------------------------------------------------

THRUST = {
    "model": "FishRobot.Calibration.ThrustBench",
    # amplitudy jak w przeglądzie częstotliwości (pompa ogranicza θ·f), pełna i połowa komendy
    "f": [0.25, 0.5, 1.0, 2.0], "Theta_deg": [31.0, 17.0, 7.8, 3.5], "amp": [1.0, 0.5],
    "U": [0.0, 0.03, 0.06, 0.1],
    # „prawdziwa” płetwa: C_T = 0,6 i kara za prędkość kappa·U² zamiast U² (kappa = 1 w teorii Lighthilla)
    "true": {"C_T": 0.6, "kappa": 1.5},
    "noise_abs": 1e-4, "noise_rel": 0.05,  # siłomierz po uśrednieniu: 0,1 mN + 5% odczytu
}


def thrust_model(points, periods=4):
    """Średni ciąg z ThrustBench dla C_T = 1 w punktach (Theta, f, U), oraz ten sam ruch przy U = 0."""
    exp = THRUST
    work_dir = om_fast.compile_model(exp["model"])
    cases = []
    for j, (Th, f, U) in enumerate(points):
        for tag, u in (("U", U), ("0", 0.0)):
            cases.append((f"p{j}_{tag}", {"Theta": Th, "f": f, "U0": u, "fin.C_T": 1.0}, {"stopTime": periods / f}))
    sols = om_fast.run_many(work_dir, exp["model"], cases, ["time", "T_mean"])
    T = np.array([sol["T_mean"][-1] for sol in sols]).reshape(-1, 2)
    return T[:, 0], T[:, 1]  # T1(U), T1(0)


def thrust_main(args):
    c = THRUST
    if args.data:
        d = np.genfromtxt(args.data, delimiter=",", names=True)
        points = np.column_stack([d["Theta"], d["f"], d["U"]])
        T_meas = d["T"]
        truth = None
    else:
        points = np.array([(np.radians(th) * a, f, U) for f, th in zip(c["f"], c["Theta_deg"])
                           for a in c["amp"] for U in c["U"]])
        truth = c["true"]
    T1, T10 = thrust_model(points)
    if truth:
        T_true = truth["C_T"] * (T10 - truth["kappa"] * (T10 - T1))
        rng = np.random.default_rng(9)
        T_meas = T_true + rng.normal(0, 1, T_true.size) * (c["noise_abs"] + c["noise_rel"] * np.abs(T_true))
        np.savetxt(OUT / "thrust_synthetic.csv", np.column_stack([points, T_meas]), delimiter=",",
                   header="Theta,f,U,T", comments="", fmt="%.6g")
    U = points[:, 2]

    # Regresja ważona: szum siłomierza σ_i = szum stały + szum względny·T (specyfikacja czujnika).
    # Przy małym ciągu dominuje część stała, przy dużym względna; zwykła regresja traktowałaby wszystkie
    # punkty jednakowo i źle oceniała niepewność. σ_i liczymy z przewidywania modelu, a nie z pomiaru.
    def weights(x):
        return 1.0 / (args.noise_abs + args.noise_rel * np.abs(x * np.median(T_meas / T1))) ** 2

    def through_origin(x, y):
        w = weights(x)
        k = (w * x) @ y / ((w * x) @ x)
        r = y - k * x
        return k, np.sqrt((w * r) @ r / (len(x) - 1) / ((w * x) @ x)), r

    C_T, s_C, r_model = through_origin(T1, T_meas)
    tether = U == 0
    C_T0, s_C0, _ = through_origin(T1[tether], T_meas[tether]) if tether.sum() > 2 else (np.nan, np.nan, None)
    # Test postaci: T = a·T1(0) − b·(T1(0) − T1(U)); teoria Lighthilla: b = a
    sw = np.sqrt(weights(T1))
    X = np.column_stack([T10, -(T10 - T1)]) * sw[:, None]
    ab, *_ = np.linalg.lstsq(X, T_meas * sw, rcond=None)
    r_ab = T_meas * sw - X @ ab
    cov = np.linalg.inv(X.T @ X) * (r_ab @ r_ab / (len(T_meas) - 2))
    kappa = ab[1] / ab[0]
    s_kappa = kappa * np.sqrt(cov[1, 1] / ab[1] ** 2 + cov[0, 0] / ab[0] ** 2 - 2 * cov[0, 1] / (ab[0] * ab[1]))

    tr = (lambda v, ref: f"   (prawdziwe {ref:g}, błąd {100 * (v / ref - 1):+.1f}%)") if truth else (lambda v, ref: "")
    lines = [f"punkty: {len(T_meas)} (na uwięzi: {tether.sum()}), U do {U.max() * 100:.0f} cm/s",
             f"C_T (model Lighthilla, wszystkie punkty) = {C_T:.4f} ± {100 * s_C / C_T:.1f}%" + (tr(C_T, truth['C_T']) if truth else ""),
             f"C_T (tylko na uwięzi, U = 0)           = {C_T0:.4f} ± {100 * s_C0 / C_T0:.1f}%" + (tr(C_T0, truth['C_T']) if truth else ""),
             f"test postaci: kara za U² = {kappa:.2f} ± {s_kappa:.2f} × teoria (Lighthill: 1)"
             + (f"   (prawdziwe {truth['kappa']:g})" if truth else "")]
    if abs(kappa - 1) > 3 * s_kappa:
        lines.append("  -> postać modelu nie pasuje do pomiaru: ciąg maleje z prędkością inaczej niż w teorii Lighthilla.")
    # Konsekwencja dla pływania: przy jakiej prędkości ciąg znika (f = 1 Hz, L = L_tail z modelu)
    L = 0.1
    lines.append(f"ciąg znika przy U = L·ω/√kappa: przy 1 Hz {100 * L * 2 * np.pi / np.sqrt(max(kappa, 1e-9)):.0f} cm/s "
                 f"(teoria: {100 * L * 2 * np.pi:.0f} cm/s); robot pływa z ok. 6 cm/s, więc tam różnica w ciągu "
                 f"to {100 * (kappa - 1) * 0.064 ** 2 / ((L * 2 * np.pi) ** 2 - 0.064 ** 2):.1f}%")
    # Do modelu: C_T z uwięzi, jeśli jest. Robot pływa wolno (U << L·ω), a tam liczy się właśnie ciąg statyczny;
    # C_T ze wszystkich punktów jest obciążone, gdy postać zależności od U nie pasuje.
    best = C_T0 if np.isfinite(C_T0) else C_T
    lines.append(f"do modelu: FishRobot.Propulsion.LighthillFin fin(C_T={best:.4g});  "
                 f"({'z punktów na uwięzi' if np.isfinite(C_T0) else 'ze wszystkich punktów'}; s_fin i L_tail zmierzone linijką)")
    text = "\n".join(lines)
    print(text)
    (OUT / "thrust_fit.txt").write_text(text + "\n")

    fig, (ax, ax_r) = plotting.plt.subplots(1, 2, figsize=(10.5, 4.4))
    # Udział kary za prędkość w ciągu Lighthilla: x = U²/(L·ω)² (L z modelu, 0,1 m)
    x = U ** 2 / (L * 2 * np.pi * points[:, 1]) ** 2
    T_fit = C_T * T1
    sig = args.noise_abs + args.noise_rel * np.abs(T_fit)
    for j, u in enumerate(sorted(set(U))):
        sel = U == u
        ax.plot(T_fit[sel] * 1e3, T_meas[sel] * 1e3, "o", color=plotting.SERIES[j], markersize=5,
                label=f"U = {u * 100:g} cm/s")
        ax_r.errorbar(x[sel], 100 * r_model[sel] / T_fit[sel], yerr=100 * sig[sel] / T_fit[sel], fmt="o",
                      color=plotting.SERIES[j], markersize=5, elinewidth=0.8, capsize=0)
    lim = [0, max(T_meas.max(), T_fit.max()) * 1e3 * 1.08]
    ax.plot(lim, lim, color=plotting.TEXT_2, linewidth=1)
    ax.set_xlabel("model, C_T dopasowane [mN]")
    ax.set_ylabel("pomiar [mN]")
    ax.set_title("średni ciąg", loc="left", fontsize=10)
    ax.legend(loc="upper left")
    xx = np.linspace(0, x.max() * 1.05, 100)
    ax_r.plot(xx, -100 * (kappa - 1) * xx / (1 - xx), color=plotting.TEXT_2, linewidth=1.2,
              label=f"kara × {kappa:.2f}")
    ax_r.axhline(0, color=plotting.TEXT_2, linewidth=0.8, linestyle=(0, (2, 2)))
    ax_r.set_xlabel("U² / (L·ω)²  (udział kary za prędkość)")
    ax_r.set_ylabel("(pomiar − model)/model [%]")
    ax_r.set_title("reszty względem kary za prędkość", loc="left", fontsize=10)
    ax_r.legend(loc="upper right")
    src = "pomiar syntetyczny" if truth else args.data
    fig.suptitle(f"Kalibracja ciągu płetwy ({src})", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    print(plotting.save(fig, "thrust_fit.png", "calibration"))


# --- Krok 10: kadłub ---------------------------------------------------------------------------------

HULL = {
    "model": "FishRobot.Calibration.CoastDown",
    "rho": 998.2,
    "A": 0.005, "m": 1.0, "sigma_m": 1e-3,  # pole przekroju (linijka) [m²], masa z wagi [kg] ± 1 g
    "true": {"C_d": 0.4, "m_added_x": 0.08, "U_start": 0.15},
    "U_tow": np.linspace(0.02, 0.2, 10).tolist(),
    "noise_abs": 1e-4, "noise_rel": 0.03,  # siłomierz wózka: 0,1 mN + 3%
    "coast": {"t_end": 20.0, "dt": 1 / 30, "noise": 2e-3},  # kamera 30 kl./s, 2 mm
    "params": {"surge.m_added_x": (0.1, "kg"), "surge.U_start": (0.1, "m/s")},
    "signals": {"x": ("m", "położenie")},
    "component": "FishRobot.Propulsion.SurgeDynamics surge",
}


def hull_main(args):
    c = HULL
    work_dir = om_fast.compile_model(c["model"])
    q = 0.5 * c["rho"] * args.A
    # --- holowanie: F = q·C_d·U², regresja przez zero z wagami z modelu szumu siłomierza
    if args.data_tow:
        d = np.genfromtxt(args.data_tow, delimiter=",", names=True)
        U, F = d["U"], d["F"]
        truth = None
    else:
        truth = c["true"]
        U = np.array(c["U_tow"])
        F0 = q * truth["C_d"] * U ** 2
        F = F0 + np.random.default_rng(10).normal(0, 1, U.size) * (c["noise_abs"] + c["noise_rel"] * F0)
        np.savetxt(OUT / "hull_tow_synthetic.csv", np.column_stack([U, F]), delimiter=",", header="U,F",
                   comments="", fmt="%.6g")
    xr = q * U ** 2
    w = 1 / (args.noise_abs + args.noise_rel * xr * np.median(F / xr)) ** 2
    C_d = (w * xr) @ F / ((w * xr) @ xr)
    r_tow = F - C_d * xr
    rel_Cd = np.sqrt((w * r_tow) @ r_tow / (len(U) - 1) / ((w * xr) @ xr)) / C_d

    # --- wybieg: x(t) przy ustalonych C_d, A, m; dopasowanie m_added_x i prędkości początkowej
    exp = {k: c[k] for k in ("model", "params", "signals", "component")}
    setup = {"surge.C_d": C_d, "surge.A": args.A, "surge.m": args.m}
    if args.data_coast:
        d = np.genfromtxt(args.data_coast, delimiter=",", names=True)
        t, meas = d["time"], {"x": d["x"]}
    else:
        t = np.arange(0, c["coast"]["t_end"] + 1e-9, c["coast"]["dt"])
        true_setup = {"surge.C_d": truth["C_d"], "surge.A": args.A, "surge.m": args.m}
        clean = simulate(work_dir, exp, [truth["m_added_x"], truth["U_start"]], "true", true_setup, t)["x"]
        meas = {"x": clean + np.random.default_rng(11).normal(0, c["coast"]["noise"], t.size)}
        np.savetxt(OUT / "hull_coast_synthetic.csv", np.column_stack([t, meas["x"]]), delimiter=",",
                   header="time,x", comments="", fmt="%.6g")
    p_fit, sigma, cov, res, noise = fit(work_dir, exp, t, meas, setup)
    ma = p_fit[0]
    M = args.m + ma
    # Przebieg zależy tylko od k_d/M, więc błąd C_d przenosi się 1:1 na M; m_added_x = M − m.
    s_M_fit = ma * sigma[0]  # niepewność bezwzględna z dopasowania (M − m przy ustalonym m)
    s_ma = np.sqrt(s_M_fit ** 2 + (M * rel_Cd) ** 2 + args.sigma_m ** 2)

    tr = (lambda v, ref: f"   (prawdziwe {ref:g}, błąd {100 * (v / ref - 1):+.1f}%)") if truth else (lambda v, ref: "")
    lines = [f"holowanie: {len(U)} prędkości {U.min() * 100:.0f}–{U.max() * 100:.0f} cm/s",
             f"C_d = {C_d:.4f} ± {100 * rel_Cd:.2f}%   (A = {args.A:g} m² zmierzone; wyznaczalny jest tylko iloczyn C_d·A)"
             + (tr(C_d, truth["C_d"]) if truth else ""),
             "",
             "wybieg:",
             "\n".join(l for l in report(exp, p_fit, sigma, cov, res, noise, truth and {
                 "surge.m_added_x": truth["m_added_x"], "surge.U_start": truth["U_start"]}).splitlines()
                 if not l.startswith("do modelu")),
             "",
             f"m_added_x = {ma:.4f} kg ± {s_ma:.4f} kg ({100 * s_ma / ma:.0f}%), w tym: dopasowanie {s_M_fit:.4f}, "
             f"C_d z holowania {M * rel_Cd:.4f}, ważenie {args.sigma_m:.4f}"
             + (tr(ma, truth["m_added_x"]) if truth else ""),
             f"do modelu: FishRobot.Propulsion.SurgeDynamics surge(m={args.m:g}, C_d={C_d:.4g}, A={args.A:g}, "
             f"m_added_x={ma:.4g});"]
    text = "\n".join(lines)
    print(text)
    (OUT / "hull_fit.txt").write_text(text + "\n")

    sim_fit = simulate(work_dir, exp, p_fit, "fit", setup, t)
    fig, axes = plotting.plt.subplots(2, 2, figsize=(10.5, 6), gridspec_kw={"height_ratios": [3, 1.3]})
    uu = np.linspace(0, U.max() * 1.05, 100)
    axes[0, 0].plot(U * 100, F * 1e3, "o", color=plotting.SERIES[0], markersize=5, label="pomiar")
    axes[0, 0].plot(uu * 100, C_d * q * uu ** 2 * 1e3, color=plotting.TEXT_2, linewidth=1.2, label="½·ρ·C_d·A·U²")
    axes[0, 0].set_ylabel("opór [mN]")
    axes[0, 0].set_title("holowanie", loc="left", fontsize=10)
    axes[0, 0].legend(loc="upper left")
    sig_tow = args.noise_abs + args.noise_rel * C_d * xr
    axes[1, 0].errorbar(U * 100, 100 * r_tow / (C_d * xr), yerr=100 * sig_tow / (C_d * xr), fmt="o",
                        color=plotting.SERIES[0], markersize=4, elinewidth=0.8, capsize=0)
    axes[1, 0].set_ylabel("reszty [%]")
    axes[1, 0].set_xlabel("U [cm/s]")
    axes[0, 1].plot(t, meas["x"] * 100, ".", color="#b9b8b3", markersize=2, label="pomiar")
    axes[0, 1].plot(t, sim_fit["x"] * 100, color=plotting.SERIES[0], label="dopasowanie")
    axes[0, 1].set_ylabel("położenie [cm]")
    axes[0, 1].set_title("wybieg", loc="left", fontsize=10)
    axes[0, 1].legend(loc="upper left")
    axes[1, 1].plot(t, (meas["x"] - sim_fit["x"]) * 1e3, color=plotting.SERIES[0], linewidth=0.8)
    axes[1, 1].set_ylabel("reszty [mm]")
    axes[1, 1].set_xlabel("czas [s]")
    for ax in axes[1]:
        ax.axhline(0, color=plotting.TEXT_2, linewidth=0.8)
    src = "pomiar syntetyczny" if truth else f"{args.data_tow}, {args.data_coast}"
    fig.suptitle(f"Kalibracja kadłuba ({src})", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    print(plotting.save(fig, "hull_fit.png", "calibration"))


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
    v = sub.add_parser("valve", help="krok 6: zawór przelewowy z charakterystyki Q(Δp)")
    v.add_argument("--data", help="CSV z punktami (dp [Pa], Q [m³/s], up: 1 przy rosnącym przepływie, 0 przy malejącym)")
    ts = sub.add_parser("tail-static", help="krok 7: D_tail i k z momentu i kąta przy zadanym Δp")
    ts.add_argument("--data", help="CSV (dp_blocked, tau, dp_free, theta) w jednostkach SI; bez tej opcji: syntetyczny")
    ts.add_argument("--k", choices=["line", "small"], default="line",
                    help="które k zapisać dla kroku 8: prosta w całym zakresie albo sztywność przy małych kątach")
    td = sub.add_parser("tail-dynamic", help="krok 8: J, c, J_added, c_h z drgań swobodnych (wymaga kroku 7)")
    td.add_argument("--data-air", help="CSV (time, theta) – drgania w powietrzu")
    td.add_argument("--data-water", help="CSV (time, theta) – drgania w wodzie")
    th = sub.add_parser("thrust", help="krok 9: C_T płetwy ze średniego ciągu na siłomierzu")
    th.add_argument("--data", help="CSV (Theta [rad], f [Hz], U [m/s], T [N]); T po odjęciu tary przy nieruchomym ogonie")
    th.add_argument("--noise-abs", type=float, default=THRUST["noise_abs"], help="szum stały siłomierza [N]")
    th.add_argument("--noise-rel", type=float, default=THRUST["noise_rel"], help="szum względny siłomierza [–]")
    h = sub.add_parser("hull", help="krok 10: C_d z holowania, m_added_x z wybiegu")
    h.add_argument("--data-tow", help="CSV (U [m/s], F [N]) – holowanie ze stałą prędkością")
    h.add_argument("--data-coast", help="CSV (time [s], x [m]) – wybieg po puszczeniu, x = 0 w chwili puszczenia")
    h.add_argument("--A", type=float, default=HULL["A"], help="pole przekroju kadłuba [m²]")
    h.add_argument("--m", type=float, default=HULL["m"], help="masa ryby z wagi [kg]")
    h.add_argument("--sigma-m", type=float, default=HULL["sigma_m"], help="niepewność ważenia [kg]")
    h.add_argument("--noise-abs", type=float, default=HULL["noise_abs"], help="szum stały siłomierza [N]")
    h.add_argument("--noise-rel", type=float, default=HULL["noise_rel"], help="szum względny siłomierza [–]")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    {"motor": motor_main, "pump": pump_main, "pipe": pipe_main, "chamber": chamber_main, "valve": valve_main,
     "tail-static": tail_static_main, "tail-dynamic": tail_dynamic_main, "thrust": thrust_main, "hull": hull_main}[args.step](args)


if __name__ == "__main__":
    main()
