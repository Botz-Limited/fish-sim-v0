"""Etap 6: przeglądy – częstotliwość machania i moduł Younga.

Uruchomienie:  source scripts/env.sh && python scripts/run_stage6.py   (~1 h, do 10 symulacji naraz)
               python scripts/run_stage6.py --plot-only                (tylko wykresy z CSV)

Każdy punkt to osobna symulacja (siatka coarse), wszystkie liczone równolegle
(fishsofa/parallel.py, jedna symulacja = jeden rdzeń):

1. Częstotliwość 0.5–3 Hz co 0.25 Hz (te same punkty co MuJoCo/scripts/sweep_frequency.py),
   w wodzie. Protokół (spec, etap 6): prefill 1 s, potem 2 cykle rozbiegu (pierwszy to rampa
   amplitudy) i 3 cykle uśredniania. Krok: dt = 1 ms do 2 Hz, wyżej 1 ms·2/f, bo prędkość
   płetwy rośnie z f, a z nią max(c·dt/m) jawnego oporu (etap 5).
2. Moduł Younga silikonu ×0.5, ×1, ×2:
   a) quasi-statycznie, sterowanie objętością (jak etap 2: komora L, R odpowietrzona, g = 0),
   b) dla kontrastu quasi-statycznie, sterowanie CIŚNIENIEM (valueType="pressure"),
   c) dynamicznie w wodzie przy 2 Hz (×1 to punkt 2 Hz z przeglądu częstotliwości).
   Zmieniamy tylko silikon (z kręgosłupem, bo ten jest E×20 silikonu); włókna obwodowe to
   inny materiał i ich sztywność zostaje – stąd małe odstępstwa od idealnego skalowania.

Wyniki w results/: s6_freq_sweep.png/.csv, s6_young_sweep.png/.csv, s6_summary.txt.
"""
import csv
import os
import sys
import time
from dataclasses import replace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fishsofa import PROJECT_DIR, headless, parallel  # noqa: E402
from fishsofa.config import TailConfig  # noqa: E402

LEVEL = "coarse"
RESULTS = os.path.join(PROJECT_DIR, "results")
MUJOCO_SWEEP = os.path.join(os.path.dirname(PROJECT_DIR), "MuJoCo", "results", "s5_sweep.csv")
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"   # paleta dataviz, stała kolejność
FREQS = [round(f, 2) for f in np.arange(0.5, 3.0 + 1e-9, 0.25)]
E_FACTORS = (0.5, 1.0, 2.0)
QS_VOLUMES = [10e-6, 20e-6, 30e-6, 40e-6]   # [m³] tryb objętościowy
QS_PRESSURES = [2e3, 4e3, 6e3, 8e3]          # [Pa] tryb ciśnieniowy
N_WARMUP, N_AVG = 2, 3                      # cykle rozbiegu (w tym rampa) i uśredniania
FREQ_COLS = ("f", "dt_ms", "amp_deg", "phase_deg", "thrust_mN", "dp_max_kPa", "valve_frac", "pump_sat_frac",
             "stability_max", "ms_per_step")


def flap_cfg(f: float, e_factor: float = 1.0) -> TailConfig:
    base = TailConfig(environment="water")
    return replace(base, tail_freq=f, ramp_time=1.0 / f, dt=1e-3 * min(1.0, 2.0 / f),
                   young_modulus=base.young_modulus * e_factor)


def flap_t_end(cfg: TailConfig) -> float:
    return cfg.prefill_time + (N_WARMUP + N_AVG) / cfg.tail_freq


def qs_cfg(e_factor: float) -> TailConfig:
    base = TailConfig(include_weight=False)
    return replace(base, young_modulus=base.young_modulus * e_factor)


def main():
    os.makedirs(RESULTS, exist_ok=True)
    jobs = {}
    # Najdłuższe symulacje najpierw (niskie f), żeby procesy kończyły się mniej więcej razem.
    for f in FREQS:
        cfg = flap_cfg(f)
        jobs[("freq", f)] = (headless.run_flapping, dict(cfg=cfg, level=LEVEL, t_end=flap_t_end(cfg)))
    for k in (0.5, 2.0):
        cfg = flap_cfg(2.0, k)
        jobs[("young_dyn", k)] = (headless.run_flapping, dict(cfg=cfg, level=LEVEL, t_end=flap_t_end(cfg)))
    for k in E_FACTORS:
        jobs[("young_qs_volume", k)] = (headless.quasi_static_sweep,
                                        dict(cfg=qs_cfg(k), level=LEVEL, dV_targets=QS_VOLUMES))
        jobs[("young_qs_pressure", k)] = (headless.quasi_static_sweep,
                                          dict(cfg=qs_cfg(k), level=LEVEL, dV_targets=QS_PRESSURES, mode="pressure"))
    t0 = time.perf_counter()
    res = parallel.run_all(_call, {k: dict(fn=fn, kw=kw) for k, (fn, kw) in jobs.items()}, label="Etap 6: ")
    wall_min = (time.perf_counter() - t0) / 60

    freq_rows = [freq_metrics(f, res[("freq", f)]) for f in FREQS]
    _write_csv("s6_freq_sweep.csv", FREQ_COLS, freq_rows)
    dyn = {1.0: freq_metrics(2.0, res[("freq", 2.0)])}
    dyn.update({k: freq_metrics(2.0, res[("young_dyn", k)]) for k in (0.5, 2.0)})
    young_rows = []
    for k in E_FACTORS:
        for mode, targets in (("volume", QS_VOLUMES), ("pressure", QS_PRESSURES)):
            c = res[(f"young_qs_{mode}", k)]
            for i in range(len(c.dV)):
                young_rows.append({"variant": f"qs_{mode}", "E_factor": k, "target": targets[i], "dV_ml": 1e6 * c.dV[i],
                                   "p_kPa": c.p[i] / 1e3, "theta_deg": np.degrees(c.tip_angle[i])})
        d = dyn[k]
        young_rows.append({"variant": "dyn_water_2Hz", "E_factor": k, "target": np.nan, "dV_ml": np.nan,
                           "p_kPa": d["dp_max_kPa"], "theta_deg": d["amp_deg"], "phase_deg": d["phase_deg"]})
    _write_csv("s6_young_sweep.csv", ("variant", "E_factor", "target", "dV_ml", "p_kPa", "theta_deg", "phase_deg"),
               young_rows)
    cpu_min = sum(r.ms_per_step * len(r.log["t"]) for k, r in res.items() if k[0] in ("freq", "young_dyn")) / 6e4
    txt = summary(freq_rows, young_rows, wall_min, cpu_min)
    print("\n" + txt)
    with open(os.path.join(RESULTS, "s6_summary.txt"), "w") as f:
        f.write(txt + "\n")
    plot_freq(freq_rows)
    plot_young(young_rows)


def _call(fn, kw):
    """Wywołanie w procesie roboczym (parallel.run_all przekazuje kwargs)."""
    return fn(**kw)


def freq_metrics(f: float, r) -> dict:
    """Metryki z N_AVG ostatnich cykli: amplituda kąta, ciąg (średnie F_x), max |Δp|,
    udział czasu z otwartym zaworem i z nasyconą pompą (|u| = 1)."""
    L, cfg = r.log, flap_cfg(f)
    T = 1.0 / f
    t1 = L["t"][-1] + r.dt
    m = L["t"] >= t1 - N_AVG * T - 1e-9
    amps = []
    for k in range(N_AVG):
        mk = (L["t"] >= t1 - (N_AVG - k) * T - 1e-9) & (L["t"] < t1 - (N_AVG - k - 1) * T - 1e-9)
        amps.append(0.5 * (L["theta"][mk].max() - L["theta"][mk].min()))
    return {"f": f, "dt_ms": r.dt * 1e3, "amp_deg": float(np.degrees(np.mean(amps))),
            "phase_deg": r.cycles.get("phase_lag_deg", np.nan),
            "thrust_mN": 1e3 * float(L["F_x"][m].mean()),
            "dp_max_kPa": float(np.abs(L["p_L"][m] - L["p_R"][m]).max() / 1e3),
            "valve_frac": float(L["valve_open"][m].mean()), "pump_sat_frac": float(np.mean(np.abs(L["u"][m]) >= 1)),
            "stability_max": float(np.nanmax(L["stability"])), "ms_per_step": r.ms_per_step,
            "amp_change": abs(amps[-1] / amps[-2] - 1)}


def _write_csv(name, cols, rows):
    with open(os.path.join(RESULTS, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([_fmt(r.get(c, np.nan)) for c in cols])


def _fmt(v):
    return v if isinstance(v, str) else f"{v:.6g}"


def _read_csv(name):
    with open(os.path.join(RESULTS, name)) as f:
        return [{k: (v if k == "variant" else float(v)) for k, v in row.items()} for row in csv.DictReader(f)]


def summary(freq_rows, young_rows, wall_min=np.nan, cpu_min=np.nan) -> str:
    lines = ["Etap 6 – przeglądy (coarse, V4, woda dla dynamiki)",
             f"czas obliczeń całego przeglądu: {wall_min:.0f} min (zegar), symulacje dynamiczne razem "
             f"{cpu_min:.0f} min CPU – równolegle {cpu_min / wall_min:.1f}× szybciej niż po kolei", "",
             "a) częstotliwość (A_V = 17 ml, 2 cykle rozbiegu + 3 uśredniania):",
             "   f [Hz]  dt [ms]  amplituda [°]  faza [°]  ciąg [mN]  |Δp| max [kPa]  zawór [%]  pompa nasycona [%]  max(c·dt/m)"]
    for r in freq_rows:
        lines.append(f"   {r['f']:5.2f}  {r['dt_ms']:6.3f}  {r['amp_deg']:12.2f}  {r['phase_deg']:8.1f}  {r['thrust_mN']:9.2f}"
                     f"  {r['dp_max_kPa']:14.1f}  {100 * r['valve_frac']:9.1f}  {100 * r['pump_sat_frac']:18.1f}"
                     f"  {r['stability_max']:11.3f}")
    lines += ["", "b) moduł Younga silikonu (×0.5 / ×1 / ×2):"]
    for variant, desc in (("qs_volume", "quasi-statycznie, sterowanie objętością (komora L, g = 0)"),
                          ("qs_pressure", "quasi-statycznie, sterowanie ciśnieniem")):
        lines.append(f"   {desc}:")
        rows = [r for r in young_rows if r["variant"] == variant]
        for t in sorted({r["target"] for r in rows}):
            rr = {r["E_factor"]: r for r in rows if r["target"] == t}
            lab = f"ΔV = {t * 1e6:.0f} ml" if variant == "qs_volume" else f"p = {t / 1e3:.0f} kPa"
            lines.append(f"     {lab}: " + "; ".join(
                f"E×{k:g}: p {rr[k]['p_kPa']:.2f} kPa, θ {rr[k]['theta_deg']:+.2f}°, ΔV {rr[k]['dV_ml']:.1f} ml"
                for k in E_FACTORS if k in rr))
    lines.append("   dynamicznie w wodzie, 2 Hz: " + "; ".join(
        f"E×{r['E_factor']:g}: ±{r['theta_deg']:.2f}°, faza {r['phase_deg']:.0f}°, |Δp| max {r['p_kPa']:.1f} kPa"
        for r in young_rows if r["variant"] == "dyn_water_2Hz"))
    return "\n".join(lines)


def _style(ax):
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def _rc():
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK})


def plot_freq(rows):
    _rc()
    f = np.array([r["f"] for r in rows])
    get = lambda k: np.array([r[k] for r in rows])
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), constrained_layout=True)
    for ax in axes.flat:
        _style(ax)
        ax.set_xlabel("częstotliwość f [Hz]")
    a, b, c, d = axes.flat
    a.plot(f, get("amp_deg"), "o-", color=BLUE, linewidth=2, label="SOFA: amplituda θ (woda)")
    if os.path.exists(MUJOCO_SWEEP):
        mj = np.genfromtxt(MUJOCO_SWEEP, delimiter=",", names=True)
        scale = get("amp_deg").max() / mj["amp_fin"].max()
        a.plot(mj["f"], mj["amp_fin"] * scale, "s--", color=INK2, linewidth=1.2, markersize=4,
               label=f"MuJoCo: amp_fin × {scale:.2f} (tylko kształt)")
    a.set_ylabel("amplituda kąta końcówki [°]")
    a.set_title("Amplituda (ta sama amplituda objętości A_V)", loc="left", fontsize=10)
    a.legend(frameon=False, labelcolor=INK, fontsize=9)

    b.plot(f, get("thrust_mN"), "o-", color=GREEN, linewidth=2)
    b.axhline(0, color=INK2, linewidth=0.8)
    b.set_ylabel("ciąg na uwięzi [mN]")
    b.set_title("Średni ciąg (model oporu – tylko jakościowo)", loc="left", fontsize=10)

    c.plot(f, get("dp_max_kPa"), "o-", color=ORANGE, linewidth=2)
    c.axhline(TailConfig().p_max / 1e3, color=INK2, linewidth=1, linestyle="--")
    c.text(f[0], TailConfig().p_max / 1e3, " p_max zaworu", color=INK2, va="bottom", fontsize=9)
    c.set_ylabel("max |Δp| [kPa]")
    c.set_title("Różnica ciśnień między komorami", loc="left", fontsize=10)

    d.plot(f, 100 * get("valve_frac"), "o-", color=ORANGE, linewidth=2, label="zawór otwarty")
    d.plot(f, 100 * get("pump_sat_frac"), "o-", color=BLUE, linewidth=2, label="pompa nasycona |u| = 1")
    d.set_ylabel("udział czasu [%]")
    d.set_title("Ograniczenia hydrauliki", loc="left", fontsize=10)
    d.legend(frameon=False, labelcolor=INK, fontsize=9)
    fig.suptitle("Etap 6a – przegląd częstotliwości w wodzie (siatka coarse, V4, A_V = 17 ml, Q_max = 250 ml/s, "
                 "parametry PLACEHOLDER)", x=0.01, ha="left", color=INK, fontsize=11)
    fig.savefig(os.path.join(RESULTS, "s6_freq_sweep.png"), dpi=150, facecolor="white")
    plt.close(fig)


def plot_young(rows):
    _rc()
    colors = {0.5: ORANGE, 1.0: BLUE, 2.0: GREEN}
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6), constrained_layout=True)
    for ax in axes:
        _style(ax)
    a, b, c = axes
    for k in E_FACTORS:
        v = [r for r in rows if r["variant"] == "qs_volume" and r["E_factor"] == k]
        a.plot([r["dV_ml"] for r in v], [r["p_kPa"] for r in v], "o-", color=colors[k], linewidth=2,
               label=f"E×{k:g}: ciśnienie [kPa]")
        a.plot([r["dV_ml"] for r in v], [-r["theta_deg"] for r in v], "s--", color=colors[k], linewidth=1.2,
               markersize=4, label=f"E×{k:g}: |θ| [°]")
        p = [r for r in rows if r["variant"] == "qs_pressure" and r["E_factor"] == k]
        b.plot([r["p_kPa"] for r in p], [-r["theta_deg"] for r in p], "o-", color=colors[k], linewidth=2,
               label=f"E×{k:g}")
    a.set_xlabel("wtłoczona objętość ΔV [ml]")
    a.set_ylabel("ciśnienie [kPa]  /  |θ| [°]")
    a.set_title("a) Sterowanie objętością: kąt prawie ten sam,\nciśnienie ~ E", loc="left", fontsize=10)
    a.legend(frameon=False, labelcolor=INK, fontsize=8, ncol=2)
    b.set_xlabel("zadane ciśnienie p [kPa]")
    b.set_ylabel("|θ| [°]")
    b.set_title("b) Sterowanie ciśnieniem: kąt ~ 1/E", loc="left", fontsize=10)
    b.legend(frameon=False, labelcolor=INK, fontsize=9)
    d = sorted((r for r in rows if r["variant"] == "dyn_water_2Hz"), key=lambda r: r["E_factor"])
    x = np.arange(len(d))
    c.bar(x - 0.2, [r["theta_deg"] for r in d], 0.4, color=BLUE, label="amplituda θ [°]")
    c2 = c.twinx()
    c2.bar(x + 0.2, [r["phase_deg"] for r in d], 0.4, color=ORANGE, label="opóźnienie fazy [°]")
    c2.spines["top"].set_visible(False)
    c.set_xticks(x, [f"E×{r['E_factor']:g}" for r in d])
    c.set_ylabel("amplituda θ [°]", color=BLUE)
    c2.set_ylabel("opóźnienie fazy względem −V_ref [°]", color=ORANGE)
    c.set_title("c) Dynamicznie w wodzie, 2 Hz: E zmienia\namplitudę i fazę (rezonans ogona)", loc="left", fontsize=10)
    fig.suptitle("Etap 6b – moduł Younga silikonu ×0.5 / ×1 / ×2 (siatka coarse, V4; włókna obwodowe bez zmian)",
                 x=0.01, ha="left", color=INK, fontsize=11)
    fig.savefig(os.path.join(RESULTS, "s6_young_sweep.png"), dpi=150, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    if "--plot-only" in sys.argv:
        fr, yr = _read_csv("s6_freq_sweep.csv"), _read_csv("s6_young_sweep.csv")
        plot_freq(fr)
        plot_young(yr)
    else:
        main()
