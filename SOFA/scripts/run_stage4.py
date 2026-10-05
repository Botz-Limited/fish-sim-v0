"""Etap 4: hydraulika antagonistyczna – ogon macha w powietrzu.

Uruchomienie:  source scripts/env.sh && python scripts/run_stage4.py   (~30 min)
               python scripts/run_stage4.py --plot-only                (tylko wykres z CSV)

Siatka coarse (etapy dynamiczne, błąd siatki z etapu 2: kąt +5%), powietrze, ciężar
włączony, komory pełne wody. Przebieg: 0–1 s prefill obu komór do V_prefill, potem rytm
V_ref(t) = a(t)·A_V·sin(2πft) z rampą 1 s, łącznie 4.5 s (5 pełnych cykli po rampie).
Ten sam przebieg przy dt i dt/2: niejawny Euler tłumi numerycznie (rośnie z dt), więc
porównanie amplitud pokazuje, ile z tłumienia to numeryka.

Wyniki w results/: s4_air_flapping.png, s4_air_flapping.csv, s4_summary.txt.
"""
import csv
import os
import sys
from dataclasses import replace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fishsofa import PROJECT_DIR, headless  # noqa: E402
from fishsofa.config import TailConfig  # noqa: E402

LEVEL = "coarse"
T_END = 4.5
RESULTS = os.path.join(PROJECT_DIR, "results")
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"   # paleta dataviz, stała kolejność
COLS = ("t", "V_ref", "V_p", "u", "Q", "Q_valve", "valve_open", "dV_L", "dV_R", "p_L", "p_R", "theta",
        "cs_iterations", "cs_error")


def main():
    os.makedirs(RESULTS, exist_ok=True)
    base = TailConfig(environment="air")
    runs = {}
    for dt in (base.dt, base.dt / 2):
        cfg = replace(base, dt=dt)
        print(f"[dt = {dt * 1e3:g} ms] {int(T_END / dt)} kroków...", flush=True)
        runs[dt] = headless.run_flapping(cfg, LEVEL, T_END, progress_every=int(0.5 / dt))
    with open(os.path.join(RESULTS, "s4_air_flapping.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dt_ms"] + list(COLS))
        for dt, r in runs.items():
            for i in range(len(r.log["t"])):
                w.writerow([f"{dt * 1e3:g}"] + [f"{r.log[k][i]:.9g}" for k in COLS])
    txt = summary(runs, base)
    print("\n" + txt)
    with open(os.path.join(RESULTS, "s4_summary.txt"), "w") as f:
        f.write(txt + "\n")
    plot({dt: r.log for dt, r in runs.items()}, base)


def summary(runs, cfg):
    (dt1, r1), (dt2, r2) = runs.items()
    lines = ["Etap 4 – hydraulika antagonistyczna w powietrzu (coarse, V4, ciężar włączony)",
             f"f = {cfg.tail_freq} Hz, A_V = {cfg.tail_volume_amp * 1e6:g} ml, V_prefill = "
             f"{cfg.V_prefill * 1e6:g} ml, Q_max = {cfg.Q_max * 1e6:g} ml/s, p_max = {cfg.p_max / 1e3:g} kPa", ""]
    for dt, r in runs.items():
        L, c = r.log, r.cycles
        m = L["t"] >= cfg.prefill_time + cfg.ramp_time
        dp = L["p_L"] - L["p_R"]
        s = L["dV_L"][m] + L["dV_R"][m]
        lines += [f"dt = {dt * 1e3:g} ms: {r.ms_per_step:.0f} ms/krok = {r.ms_per_step / (dt * 1e3):.0f}× wolniej "
                  "niż czas rzeczywisty",
                  "  amplituda θ w kolejnych cyklach [°]: "
                  + ", ".join(f"{np.degrees(a):.2f}" for a in c["amplitude_per_cycle"]),
                  f"  ustalony cykl: zmiana amplitudy w ostatnim cyklu {100 * c.get('steady_change', np.nan):.2f}%; "
                  f"średni kąt w ostatnim cyklu {np.degrees(c['mean_per_cycle'][-1]):+.3f}°",
                  f"  opóźnienie fazy θ względem −V_ref: {c.get('phase_lag_deg', np.nan):.1f}°",
                  f"  V_p: {L['V_p'][m].min() * 1e6:+.2f} … {L['V_p'][m].max() * 1e6:+.2f} ml "
                  f"(V_ref ±{cfg.tail_volume_amp * 1e6:g} ml); |u| = 1 w {100 * np.mean(np.abs(L['u'][m]) >= 1):.1f}% kroków",
                  f"  p_L, p_R: {min(L['p_L'][m].min(), L['p_R'][m].min()) / 1e3:.1f} … "
                  f"{max(L['p_L'][m].max(), L['p_R'][m].max()) / 1e3:.1f} kPa; |Δp| max {np.abs(dp[m]).max() / 1e3:.1f} kPa; "
                  f"zawór otwarty w {int(L['valve_open'].sum())} krokach",
                  f"  suma zmierzonych ΔV_L + ΔV_R: {s.min() * 1e6:.4f} … {s.max() * 1e6:.4f} ml "
                  f"(zadane {2 * cfg.V_prefill * 1e6:g} ml)",
                  f"  solver ograniczeń: max {np.nanmax(L['cs_iterations']):.0f} iteracji, "
                  f"max błąd {np.nanmax(L['cs_error']):.1e}", ""]
    a1, a2 = r1.cycles["amplitude_per_cycle"][-1], r2.cycles["amplitude_per_cycle"][-1]
    lines.append(f"wpływ dt: amplituda w ostatnim cyklu {np.degrees(a1):.3f}° (dt {dt1 * 1e3:g} ms) vs "
                 f"{np.degrees(a2):.3f}° (dt {dt2 * 1e3:g} ms): różnica {100 * (a1 / a2 - 1):+.2f}%")
    return "\n".join(lines)


def _style(ax):
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def plot(logs, cfg):
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK})
    (dt1, L), (dt2, L2) = logs.items()
    fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True, constrained_layout=True)
    for ax in axes:
        _style(ax)
        ax.axvspan(0, cfg.prefill_time, color=GRID, alpha=0.5, linewidth=0)
    a, b, c, d = axes
    t = L["t"]

    a.plot(t, np.degrees(L["theta"]), color=BLUE, linewidth=2, label=f"dt = {dt1 * 1e3:g} ms")
    a.plot(L2["t"], np.degrees(L2["theta"]), color=ORANGE, linewidth=1.5, linestyle="--",
           label=f"dt = {dt2 * 1e3:g} ms")
    a.set_ylabel("kąt końcówki θ [°]")
    a.set_title("Kąt końcówki (ujemny = zgięcie w −Y, w prawo; komora L = +V_bias)", loc="left", fontsize=10)
    a.legend(frameon=False, labelcolor=INK, loc="upper left", ncol=2)
    a.text(cfg.prefill_time / 2, 0.02, "prefill", transform=a.get_xaxis_transform(), ha="center",
           color=INK2, fontsize=9)

    b.plot(t, L["p_L"] / 1e3, color=BLUE, linewidth=2, label="p_L")
    b.plot(t, L["p_R"] / 1e3, color=ORANGE, linewidth=2, label="p_R")
    b.set_ylabel("ciśnienie [kPa]")
    b.set_title("Ciśnienie w komorach", loc="left", fontsize=10)
    b.legend(frameon=False, labelcolor=INK, loc="lower right", ncol=2)

    dp = (L["p_L"] - L["p_R"]) / 1e3
    c.plot(t, dp, color=GREEN, linewidth=2)
    n_open = int(L["valve_open"].sum())
    c.set_ylabel("Δp = p_L − p_R [kPa]")
    c.set_title(f"Różnica ciśnień (zawór przelewowy otwiera się przy |Δp| > {cfg.p_max / 1e3:g} kPa; "
                f"otwarty w {n_open} krokach)", loc="left", fontsize=10)
    for t0, t1 in _spans(t, L["valve_open"] > 0):
        c.axvspan(t0, t1, color=ORANGE, alpha=0.25, linewidth=0)

    d.plot(t, L["V_ref"] * 1e6, color=INK2, linewidth=1.5, linestyle="--", label="V_ref (zadane)")
    d.plot(t, L["V_p"] * 1e6, color=BLUE, linewidth=2, label="V_p (pompa)")
    d.set_ylabel("objętość [ml]")
    d.set_xlabel("czas [s]")
    d.set_title("Objętość przepompowana z R do L", loc="left", fontsize=10)
    d.legend(frameon=False, labelcolor=INK, loc="upper left", ncol=2)

    fig.suptitle(f"Etap 4 – machanie w powietrzu: f = {cfg.tail_freq:g} Hz, A_V = {cfg.tail_volume_amp * 1e6:g} ml, "
                 f"V_prefill = {cfg.V_prefill * 1e6:g} ml\nsiatka {LEVEL}, V4, E = {cfg.young_modulus:.0e} Pa "
                 "(PLACEHOLDER), ciężar włączony", x=0.01, ha="left", color=INK, fontsize=11)
    fig.savefig(os.path.join(RESULTS, "s4_air_flapping.png"), dpi=150, facecolor="white")
    plt.close(fig)


def _spans(t, mask):
    """Przedziały czasu, w których mask jest prawdą (do zaznaczenia pracy zaworu)."""
    out, start = [], None
    for ti, m in zip(t, mask):
        if m and start is None:
            start = ti
        if not m and start is not None:
            out.append((start, ti))
            start = None
    if start is not None:
        out.append((start, t[-1]))
    return out


def plot_from_csv():
    logs = {}
    with open(os.path.join(RESULTS, "s4_air_flapping.csv")) as f:
        for row in csv.DictReader(f):
            d = logs.setdefault(float(row["dt_ms"]) * 1e-3, {k: [] for k in COLS})
            for k in COLS:
                d[k].append(float(row[k]))
    plot({dt: {k: np.array(v) for k, v in d.items()} for dt, d in logs.items()}, TailConfig())


if __name__ == "__main__":
    if "--plot-only" in sys.argv:
        plot_from_csv()
    else:
        main()
