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


def check_dc_motor(sol):
    w, w_ref = sol["motor.w"], sol["w_analytic"][0]
    w_err = abs(w[-1] - w_ref) / w_ref
    p_err = np.max(np.abs(sol["P_balance_error"])) / np.max(np.abs(sol["battery.P_chem"]))
    plotting.series(sol["time"], [(w, "motor.w")], "prędkość [rad/s]",
                    "DCMotorNoLoad: rozruch silnika bez obciążenia (u = 0,6)", "dc_motor_no_load.png",
                    hlines=[(w_ref, "analitycznie")])
    return [("prędkość ustalona zgodna ze wzorem (< 1%)", w_err < 0.01, f"błąd {w_err:.1e}"),
            ("bilans mocy w każdej chwili (< 1% mocy szczytowej)", p_err < 0.01, f"max błąd {p_err:.1e}")]


def check_gear_pump(sol):
    w, dp, q, tau = sol["pump.w"], sol["pump.dp_pump"], sol["pump.V_flow"], sol["pump.flange.tau"]
    D, k_leak, eta = sol["pump.D"][0], sol["pump.k_leak"][0], sol["pump.eta_m"][0]
    q_err = np.max(np.abs(q - (D * w - k_leak * dp))) / np.max(np.abs(q))
    pumping = dp > 1e3
    tau_err = np.max(np.abs(tau[pumping] - D * dp[pumping] / eta) / np.abs(D * dp[pumping] / eta))
    p_mech_min = sol["pump.P_loss_mech"].min()
    bal = sol["pump.P_shaft"] - sol["pump.P_hyd"] - sol["pump.P_loss_leak"] - sol["pump.P_loss_mech"]
    bal_err = np.max(np.abs(bal)) / np.max(np.abs(sol["pump.P_shaft"]))
    plotting.series(dp / 1e3, [(q * 1e6, "V_flow")], "przepływ [ml/s]",
                    "GearPumpCharacteristic: przepływ vs przyrost ciśnienia (ω = 300 rad/s)",
                    "gear_pump_characteristic.png")
    return [("V_flow = D·ω − k_leak·Δp", q_err < 1e-6, f"błąd {q_err:.1e}"),
            ("tryb pompy: τ = D·Δp/η_m", tau_err < 1e-3, f"błąd {tau_err:.1e}"),
            ("straty tarcia ≥ 0 także w trybie silnika", p_mech_min >= -1e-12, f"min {p_mech_min:.2e} W"),
            ("bilans mocy pompy zamknięty", bal_err < 1e-6, f"błąd {bal_err:.1e}")]


def check_hydraulics_step(sol):
    t, u, pl, pr = sol["time"], sol["bridge.u_lim"], sol["p_L"], sol["p_R"]
    on = u > 0.25
    direction_ok = np.all(pl[on] - pr[on] > 0) and np.all(sol["motor.w"][on] > 0)
    vt = sol["chamberL.V"] + sol["chamberR.V"]
    drift = np.max(np.abs(vt - vt[0])) / vt[0]
    dpmax = np.max(pl - pr)
    limit = sol["reliefLR.p_set"][0] + sol["reliefLR.dp_open"][0]
    return [("kierunek: u > 0 ⇒ ω > 0 i p_L > p_R", bool(direction_ok), ""),
            ("V_L + V_R = const (< 1e-9 względnie)", drift < 1e-9, f"max dryf {drift:.1e}"),
            ("zawór ogranicza p_L − p_R ≤ p_set + dp_open", dpmax <= limit,
             f"max {dpmax / 1e3:.2f} kPa, granica {limit / 1e3:.1f} kPa")]


def check_tail_static_energy(sol):
    th, th_ref = sol["tail.theta"], sol["theta_analytic"][0]
    th_err = abs(th[-1] - th_ref) / th_ref
    e_err = np.max(np.abs(sol["E_balance_error"])) / sol["E_hyd"][-1]
    plotting.series(sol["time"], [(np.degrees(th), "θ")], "kąt ogona [°]",
                    "TailStaticEnergy: odpowiedź ogona na skok Δp = 30 kPa", "tail_static_energy.png",
                    hlines=[(np.degrees(th_ref), "D_tail·Δp/k")])
    return [("kąt statyczny θ = D_tail·Δp/k (< 1%)", th_err < 0.01, f"błąd {th_err:.1e}"),
            ("energia: hydrauliczna = kinetyczna + sprężysta + rozproszona (< 1%)", e_err < 0.01,
             f"max błąd {e_err:.1e}")]


def check_tail_direction(sol):
    t = sol["time"]
    late = t > 0.5
    ok = (np.all(sol["drive.theta"][late] > 0) and np.all(sol["drive.p_L"][late] > sol["drive.p_R"][late])
          and np.all(sol["drive.tau_tail"][late] > 0))
    vt = sol["V_total"]
    drift = np.max(np.abs(vt - vt[0])) / vt[0]
    return [("u > 0 ⇒ θ > 0, p_L > p_R, τ > 0", bool(ok), f"θ_końc = {np.degrees(sol['drive.theta'][-1]):.1f}°"),
            ("V_L + V_R = const z ruchomym ogonem (< 1e-9)", drift < 1e-9, f"max dryf {drift:.1e}")]


def check_flapping(sol, expect_relief):
    vt = sol["drive.chamberL.V"] + sol["drive.chamberR.V"]
    drift = np.max(np.abs(vt - vt[0])) / vt[0]
    q_relief = np.max(np.abs(sol["drive.reliefLR.V_flow"] - sol["drive.reliefRL.V_flow"]))
    q_pump = np.max(np.abs(sol["drive.pump.V_flow"]))
    frac = q_relief / q_pump
    if expect_relief:
        relief = ("zawór się otwiera (przepływ > 5% przepływu pompy)", frac > 0.05, f"{frac:.1%}")
    else:
        relief = ("zawór zamknięty (przepływ < 1% przepływu pompy)", frac < 0.01, f"{frac:.2%}")
    return [("V_L + V_R = const (< 1e-9)", drift < 1e-9, f"max dryf {drift:.1e}"), relief]


FLAP_VARS = ["time", "drive.chamberL.V", "drive.chamberR.V", "drive.reliefLR.V_flow", "drive.reliefRL.V_flow",
             "drive.pump.V_flow"]

def check_ballast_statics(sol):
    t = sol["time"]
    v_n, v_l, v_h = sol["fishNeutral.v_z"], sol["fishLight.v_z"], sol["fishHeavy.v_z"]
    rigid_drift = abs(sol["fishRigid.z"][-1] - sol["fishRigid.z"][0])
    comp_dev0 = abs(sol["fishComp.z"][0] + 3.0)
    comp_dev = abs(sol["fishComp.z"][-1] + 3.0)
    plotting.series(t, [(sol["fishNeutral.z"], "neutralna"), (sol["fishLight.z"], "+1 ml"),
                        (sol["fishHeavy.z"], "−1 ml"), (sol["fishComp.z"], "ściśliwy kadłub, start −3,01 m")],
                    "z [m]", "BallastStatics: ryba bez regulatora przy stałej objętości pęcherza",
                    "ballast_statics.png")
    return [("V_b neutralne ⇒ z' → 0", np.max(np.abs(v_n)) < 1e-9, f"max |z'| {np.max(np.abs(v_n)):.1e} m/s"),
            ("V_b większe ⇒ wynurzanie, mniejsze ⇒ tonięcie", v_l[-1] > 0.01 and v_h[-1] < -0.01,
             f"z' = {v_l[-1] * 100:+.1f} / {v_h[-1] * 100:+.1f} cm/s"),
            ("sztywny kadłub: równowaga obojętna (zostaje w miejscu)", rigid_drift < 1e-6,
             f"przesunięcie {rigid_drift:.1e} m"),
            ("ściśliwy kadłub: zaburzenie 1 cm rośnie > 10 razy", comp_dev > 10 * comp_dev0,
             f"{comp_dev0 * 100:.1f} cm -> {comp_dev * 100:.1f} cm po 60 s")]


def check_depth_control(sol):
    t, z = sol["time"], sol["fish.z"]
    a = (t > 10) & (t < 100)
    overshoot = (-1.5 - z[a].min()) / 1.0
    err_end = abs(z[-1] + 1.0)
    x, x_max = sol["syringe.x"], sol["syringe.x_max"][0]
    return [("przeregulowanie po skoku −0,5 → −1,5 m < 15%", overshoot < 0.15, f"{overshoot:.1%}"),
            ("błąd ustalony na −1,0 m < 2 cm", err_end < 0.02, f"{err_end * 100:.2f} cm"),
            ("tłok nie dotyka ograniczników", x.min() > 0 and x.max() < x_max,
             f"x ∈ [{x.min() * 1e3:.1f}, {x.max() * 1e3:.1f}] mm z [0, {x_max * 1e3:.0f}]")]


CHECKS = {
    "FishRobot.Tests.PipeLaminar": (["time", "pipe.dp", "dp_analytic", "pipe.Re"], check_pipe_laminar),
    "FishRobot.Tests.PipeQuadratic": (["time", "pipe.V_flow", "pipe.dp", "dp_exact"], check_pipe_quadratic),
    "FishRobot.Tests.PipeInertance": (["time", "pipe.V_flow", "Q_analytic"], check_pipe_inertance),
    "FishRobot.Tests.ChamberClosedLoop": (["time", "chamberL.V", "chamberR.V", "V_total", "chamberL.port.p",
                                           "chamberR.port.p", "E_stored", "E_dissipated"],
                                          check_chamber_closed_loop),
    "FishRobot.Tests.ChamberTableFromFile": (["time", "chamberTable.p_gauge", "chamberFile.p_gauge"],
                                             check_chamber_from_file),
    "FishRobot.Tests.DCMotorNoLoad": (["time", "motor.w", "w_analytic", "P_balance_error", "battery.P_chem"],
                                      check_dc_motor),
    "FishRobot.Tests.GearPumpCharacteristic": (["time", "pump.w", "pump.dp_pump", "pump.V_flow", "pump.flange.tau",
                                                "pump.D", "pump.k_leak", "pump.eta_m", "pump.P_loss_mech",
                                                "pump.P_shaft", "pump.P_hyd", "pump.P_loss_leak"],
                                               check_gear_pump),
    "FishRobot.Examples.HydraulicsStep": (["time", "bridge.u_lim", "p_L", "p_R", "motor.w", "chamberL.V",
                                           "chamberR.V", "reliefLR.p_set", "reliefLR.dp_open"],
                                          check_hydraulics_step),
    "FishRobot.Tests.TailStaticEnergy": (["time", "tail.theta", "theta_analytic", "E_balance_error", "E_hyd"],
                                         check_tail_static_energy),
    "FishRobot.Tests.TailDriveDirection": (["time", "drive.theta", "drive.p_L", "drive.p_R", "drive.tau_tail",
                                            "V_total"], check_tail_direction),
    "FishRobot.Examples.TailFlapping": (FLAP_VARS, lambda s: check_flapping(s, expect_relief=False)),
    "FishRobot.Examples.ReliefValveDemo": (FLAP_VARS, lambda s: check_flapping(s, expect_relief=True)),
    "FishRobot.Tests.BallastStatics": (["time", "fishNeutral.v_z", "fishLight.v_z", "fishHeavy.v_z", "fishNeutral.z",
                                        "fishLight.z", "fishHeavy.z", "fishRigid.z", "fishComp.z"],
                                       check_ballast_statics),
    "FishRobot.Examples.DepthControl": (["time", "fish.z", "syringe.x", "syringe.x_max"], check_depth_control),
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


def check_energy_closure(sol):
    """Każdy model z TailDrive: E_bateria = straty + ΔE_zmagazynowana (błąd < 1%)."""
    e_bat = sol["drive.E_battery"]
    err = np.max(np.abs(sol["drive.E_balance_error"])) / np.max(np.abs(e_bat))
    return [("bilans energii zamknięty (< 1% energii z baterii)", err < 0.01,
             f"max błąd {err:.1e}, E_bat = {e_bat[-1]:.2f} J")]


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
        # Bilans energii sprawdzamy wszędzie, gdzie jest podukład TailDrive o nazwie "drive".
        if "drive.E_balance_error" in mod.getSolutions():
            names = ["drive.E_battery", "drive.E_balance_error"]
            results += check_energy_closure(dict(zip(names, (np.asarray(x) for x in mod.getSolutions(names)))))
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
