"""Scenariusze headless: każdy zapisuje PNG + CSV do results/.

  .venv/bin/python scripts/run_scenarios.py            # wszystkie
  .venv/bin/python scripts/run_scenarios.py s6         # wybrane (po prefiksie nazwy)

Kolejne etapy dopisują scenariusze s1–s5.
"""

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # bez okna – tylko zapis do pliku
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from fishsim.config import FishConfig  # noqa: E402
from fishsim.controllers import DepthController, TailRhythm  # noqa: E402
from fishsim.hydraulics import simulate_offline  # noqa: E402
from fishsim.sim import FishSim, forward_speed  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"


def save_csv(path: Path, columns: dict):
    """Zapisuje kolumny (nazwa -> tablica 1D) do CSV."""
    names = list(columns)
    rows = np.column_stack([np.asarray(columns[n], dtype=float) for n in names])
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(names)
        w.writerows(rows.tolist())


def cycle_average(t, x, period):
    """Średnia krocząca po jednym okresie ogona – usuwa oscylację w obrębie cyklu."""
    n = max(1, int(round(period / (t[1] - t[0]))))
    out = np.full(len(x), np.nan)   # na brzegach brak pełnego cyklu -> NaN zamiast artefaktu
    out[n // 2:n // 2 + len(x) - n + 1] = np.convolve(x, np.ones(n) / n, mode="valid")
    return out


def com_speed(log, period):
    """Prędkość pozioma COM w kierunku nosa, uśredniona po cyklu [m/s]."""
    t = log["t"]
    v = np.gradient(log["com"][:, :2], t, axis=0)
    v_fwd = np.einsum("ij,ij->i", v, log["heading"])
    return cycle_average(t, v_fwd, period)


def s1_straight():
    """Pływanie na wprost: prędkość, kąty ogona (faza), ciśnienia."""
    cfg = FishConfig()
    sim = FishSim(cfg, rhythm=TailRhythm(cfg))
    log = sim.run(20.0)
    t, T = log["t"], 1.0 / cfg.tail_freq
    v = com_speed(log, T)
    th = np.degrees(log["theta"])
    fig, ax = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    ax[0].plot(t, v * 100)
    ax[0].set_ylabel("prędkość COM [cm/s]\n(średnia z cyklu)")
    ax[0].set_title(f"s1: pływanie na wprost, f = {cfg.tail_freq} Hz – "
                    f"ustalona prędkość {forward_speed(log, cfg.tail_freq) * 100:.1f} cm/s")
    zoom = t >= t[-1] - 3 * T
    for i in (0, cfg.n_actuated - 1, cfg.n_segments - 1):
        kind = "napędzany" if i < cfg.n_actuated else "pasywny"
        ax[1].plot(t, th[:, i], label=f"θ{i + 1} ({kind})")
    ax[1].set_ylabel("kąt przegubu [°]")
    ax[1].legend(loc="upper left", fontsize=8)
    ax[2].plot(t, log["p_L"] / 1e3, label="p_L")
    ax[2].plot(t, log["p_R"] / 1e3, label="p_R")
    ax[2].plot(t, log["dp"] / 1e3, "k", lw=0.8, label="Δp")
    ax[2].axhline(cfg.p_max / 1e3, color="r", ls=":", lw=1, label="±p_max (zawór)")
    ax[2].axhline(-cfg.p_max / 1e3, color="r", ls=":", lw=1)
    ax[2].set_ylabel("ciśnienie [kPa]")
    ax[2].set_xlabel("czas [s]")
    ax[2].legend(loc="upper left", fontsize=8)
    for a in ax:
        a.grid(alpha=0.3)
    # wstawka: ostatnie 3 cykle, żeby było widać opóźnienie fazy wzdłuż ogona
    ins = ax[1].inset_axes([0.62, 0.08, 0.36, 0.84])
    for i in (0, cfg.n_actuated - 1, cfg.n_segments - 1):
        ins.plot(t[zoom], th[zoom, i])
    ins.set_title("ostatnie 3 cykle", fontsize=8)
    ins.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(RESULTS / "s1_straight.png", dpi=110)
    plt.close(fig)
    save_csv(RESULTS / "s1_straight.csv",
             {"t": t, "v_fwd": v, **{f"theta{i + 1}_deg": th[:, i] for i in range(cfg.n_segments)},
              "p_L": log["p_L"], "p_R": log["p_R"], "dp": log["dp"], "F": log["F"], "u": log["u"]})
    return f"v = {forward_speed(log, cfg.tail_freq) * 100:.1f} cm/s, max|Δp| = {np.abs(log['dp']).max() / 1e3:.1f} kPa"


def s2_fluid_on_off():
    """Ciąg pochodzi z modelu płynu: woda on/off + porównanie z domyślną masą dołączoną MuJoCo."""
    runs = [("woda włączona (masa dołączona jako armature)", dict(), True),
            ("woda wyłączona (density = viscosity = 0)", dict(), False),
            ("woda, domyślny model MuJoCo (niepełna masa dołączona)", dict(added_mass="mujoco"), True)]
    fig, ax = plt.subplots(figsize=(10, 5))
    cols, summary = {}, []
    for label, kw, fluid in runs:
        cfg = FishConfig(**kw)
        log = FishSim(cfg, fluid=fluid, rhythm=TailRhythm(cfg)).run(20.0)
        v = com_speed(log, 1.0 / cfg.tail_freq)
        ax.plot(log["t"], v * 100, label=label)
        cols["t"] = log["t"]
        cols[label.split(" (")[0].replace(" ", "_")] = v
        summary.append(f"{forward_speed(log, cfg.tail_freq) * 100:+.2f}")
    ax.set_xlabel("czas [s]")
    ax.set_ylabel("prędkość COM [cm/s] (średnia z cyklu)")
    ax.set_title("s2: bez wody środek masy stoi – ciąg pochodzi z sił płynu")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(RESULTS / "s2_fluid_on_off.png", dpi=110)
    plt.close(fig)
    save_csv(RESULTS / "s2_fluid_on_off.csv", cols)
    return "v [cm/s] woda / bez wody / MuJoCo domyślnie: " + " / ".join(summary)


def s3_turn():
    """Skręt: stałe ugięcie ogona V_bias -> trajektoria XY po okręgu."""
    fig, ax = plt.subplots(figsize=(8, 8))
    cols, summary = {}, []
    for bias_ml in (-3.0, -1.5, 0.0, 1.5, 3.0):
        cfg = FishConfig(tail_volume_bias=bias_ml * 1e-6)
        log = FishSim(cfg, rhythm=TailRhythm(cfg)).run(60.0, log_every=10)
        xy = log["com"][:, :2]
        yaw = np.unwrap(np.arctan2(log["heading"][:, 1], log["heading"][:, 0]))
        late = log["t"] > 10
        rate = np.polyfit(log["t"][late], yaw[late], 1)[0]
        ax.plot(xy[:, 0], xy[:, 1], label=f"V_bias = {bias_ml:+.1f} ml ({np.degrees(rate):+.1f}°/s)")
        ax.plot(*xy[-1], "o", color=ax.lines[-1].get_color())
        cols["t"] = log["t"]
        cols[f"x_bias{bias_ml:+.1f}"], cols[f"y_bias{bias_ml:+.1f}"] = xy[:, 0], xy[:, 1]
        summary.append(f"{bias_ml:+.1f} ml: {np.degrees(rate):+.1f}°/s")
    ax.plot(0, 0, "k*", ms=12, label="start (nos w +X)")
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title("s3: skręt – trajektoria COM w 60 s\n"
                 "V_bias > 0: ogon ugięty w prawo -> skręt w prawo (zgodnie z zegarem)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(RESULTS / "s3_turn.png", dpi=110)
    plt.close(fig)
    save_csv(RESULTS / "s3_turn.csv", cols)
    return "prędkość kątowa: " + ", ".join(summary)


def s4_depth():
    """Głębokość: skoki z_ref −0.5 -> −1.5 -> −1.0 m podczas pływania (kaskada PID -> pęcherz)."""
    cfg = FishConfig()
    depth = DepthController(cfg, -0.5)
    sim = FishSim(cfg, rhythm=TailRhythm(cfg), depth=depth)
    sim.set_pose(z=-0.5)
    schedule = [(0.0, -0.5), (5.0, -1.5), (70.0, -1.0)]
    logs = []
    for (t0, z_ref), nxt in zip(schedule, schedule[1:] + [(130.0, None)]):
        depth.set_reference(z_ref)
        logs.append(sim.run(nxt[0] - t0, log_every=10))
    log = {k: np.concatenate([lg[k] for lg in logs]) for k in logs[0]}
    t = log["t"]
    fig, ax = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    ax[0].plot(t, log["z_ref"], "k--", lw=1, label="z zadane")
    ax[0].plot(t, log["com"][:, 2], label="z rzeczywiste (COM)")
    ax[0].set_ylabel("głębokość [m]")
    ax[0].set_title("s4: regulacja głębokości podczas pływania (PID -> V_ref pęcherza)")
    ax[1].plot(t, log["v_bladder_ref"] * 1e6, "k--", lw=1, label="V_ref (wyjście PID)")
    ax[1].plot(t, log["v_bladder"] * 1e6, label="V pęcherza (pompa, max 10 ml/s)")
    ax[1].axhline(cfg.bladder_v_neutral * 1e6, color="gray", ls=":", lw=1, label="V neutralne")
    ax[1].set_ylabel("objętość [ml]")
    ax[2].plot(t, np.degrees(log["pitch"]), color="tab:orange")
    ax[2].set_ylabel("pochylenie [°]")
    ax[2].set_xlabel("czas [s]")
    for a in ax:
        a.grid(alpha=0.3)
        if a.get_legend_handles_labels()[0]:
            a.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(RESULTS / "s4_depth.png", dpi=110)
    plt.close(fig)
    save_csv(RESULTS / "s4_depth.csv", {"t": t, "z_ref": log["z_ref"], "z": log["com"][:, 2],
                                        "v_bladder_ref": log["v_bladder_ref"],
                                        "v_bladder": log["v_bladder"], "pitch_deg": np.degrees(log["pitch"])})
    e1 = log["com"][(t > 60) & (t < 70), 2].mean() + 1.5
    e2 = log["com"][t > 120, 2].mean() + 1.0
    return f"uchyb ustalony: {e1 * 100:+.1f} cm przy −1.5 m, {e2 * 100:+.1f} cm przy −1.0 m"


def s5_sweep():
    """Przegląd częstotliwości (logika w scripts/sweep_frequency.py)."""
    import sweep_frequency  # ten sam katalog scripts/ jest na sys.path

    rows = sweep_frequency.run_sweep(np.arange(0.5, 3.0 + 1e-9, 0.25))
    sweep_frequency.plot_sweep(rows, RESULTS / "s5_sweep.png")
    sweep_frequency.save_rows(rows, RESULTS / "s5_sweep.csv")
    best = max(rows, key=lambda r: r["v"])
    return f"maks. prędkość {best['v'] * 100:.1f} cm/s przy {best['f']:.2f} Hz"


def s6_righting():
    """Start z przechyłem 30° -> moment prostujący (CB nad CG) przywraca pion."""
    sim = FishSim()
    sim.set_pose(roll_deg=30.0)
    log = sim.run(10.0)
    t = log["t"]
    tilt = np.degrees(log["tilt"])
    pitch = np.degrees(log["pitch"])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    ax1.plot(t, tilt, label="przechył (kąt osi z kadłuba od pionu)")
    ax1.axhline(15.0, color="gray", ls="--", lw=1, label="próg testu: połowa początkowego")
    ax1.axvspan(4.0, 5.0, color="tab:green", alpha=0.15, label="okno testu (obwiednia)")
    ax1.set_ylabel("przechył [°]")
    ax1.legend(loc="upper right")
    ax1.set_title("s6: prostowanie z przechyłu 30° (CB 1 cm nad COM kadłuba)")
    ax2.plot(t, pitch, color="tab:orange", label="pochylenie (nos w górę > 0)")
    ax2.set_ylabel("pochylenie [°]")
    ax2.set_xlabel("czas [s]")
    ax2.legend(loc="upper right")
    for ax in (ax1, ax2):
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "s6_righting.png", dpi=110)
    plt.close(fig)
    save_csv(RESULTS / "s6_righting.csv",
             {"t": t, "tilt_deg": tilt, "pitch_deg": pitch, "com_z": log["com"][:, 2]})
    w = (t >= 4) & (t <= 5)
    return f"max przechył w 4–5 s: {tilt[w].max():.2f}° (start 30°)"


def h3_hydraulics():
    """Etap 3: sama hydraulika + zastępczy ogon (bez MuJoCo). Sinus 1 Hz, od 5 s V_bias = 3 ml."""
    cfg = FishConfig(tail_freq=1.0)
    log = simulate_offline(cfg, TailRhythm(cfg), 8.0,
                           bias_schedule=lambda t: 3e-6 if t >= 5.0 else 0.0)
    t = log["t"]
    ml, kpa = 1e6, 1e-3
    fig, ax = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
    ax[0].plot(t, log["V_ref"] * ml, "k--", lw=1, label="V_ref (zadana)")
    ax[0].plot(t, log["V_p"] * ml, label="V_p (przepompowana)")
    ax[0].plot(t, log["V_g"] * ml, label="V_g = A·r·L (zajęta przez ogon)")
    ax[0].set_ylabel("objętość [ml]")
    ax[0].set_title("h3: hydraulika offline – f = 1 Hz, od t = 5 s skręt (V_bias = 3 ml)")
    ax[1].plot(t, log["Q"] * ml, label="Q pompy")
    ax[1].plot(t, log["u"] * cfg.Q_max * ml, "k--", lw=1, label="u·Q_max (komenda)")
    ax[1].axhline(cfg.Q_max * ml, color="r", ls=":", lw=1, label="±Q_max")
    ax[1].axhline(-cfg.Q_max * ml, color="r", ls=":", lw=1)
    ax[1].set_ylabel("przepływ [ml/s]")
    ax[2].plot(t, log["p_L"] * kpa, label="p_L")
    ax[2].plot(t, log["p_R"] * kpa, label="p_R")
    ax[2].plot(t, log["dp"] * kpa, "k", lw=1, label="Δp = p_L − p_R")
    ax[2].set_ylabel("ciśnienie [kPa]\n(względem p_pre)")
    ax[3].plot(t, log["F"], label="F na tendonie [N·m]")
    ax3b = ax[3].twinx()
    ax3b.plot(t, np.degrees(log["L"]), color="tab:green", label="L ogona [°]")
    ax3b.set_ylabel("L [°]", color="tab:green")
    ax[3].set_ylabel("F [N·m]")
    ax[3].set_xlabel("czas [s]")
    for a in ax:
        a.grid(alpha=0.3)
        a.axvline(5.0, color="gray", lw=0.8)
        a.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS / "h3_hydraulics.png", dpi=110)
    plt.close(fig)
    save_csv(RESULTS / "h3_hydraulics.csv", log)

    # Mini-sweep offline: amplituda vs częstotliwość (pełny sweep z wodą – etap 6)
    freqs = np.linspace(0.5, 3.0, 11)
    amps = []
    for f in freqs:
        lg = simulate_offline(cfg, TailRhythm(cfg, freq=f), 10.0)
        L = lg["L"][lg["t"] > 6.0]
        amps.append((L.max() - L.min()) / 2)
    amps = np.degrees(amps)
    target = np.degrees(cfg.tail_volume_amp / (cfg.A_eff * cfg.r_eff))
    fs = np.linspace(0.5, 3.0, 200)
    sat = np.degrees(cfg.Q_max / (2 * np.pi * fs * cfg.A_eff * cfg.r_eff))
    fig, a = plt.subplots(figsize=(8, 4.5))
    a.plot(freqs, amps, "o-", label="amplituda L (symulacja offline)")
    a.axhline(target, color="k", ls="--", lw=1, label="zadana A_V/(A·r)")
    a.plot(fs, sat, "r:", label="granica pompy Q_max/(2πf·A·r)")
    a.set_ylim(0, target * 1.6)
    a.set_xlabel("częstotliwość [Hz]")
    a.set_ylabel("amplituda L [°]")
    a.set_title("h3: pompa nie nadąża – amplituda spada powyżej ~1.2 Hz")
    a.grid(alpha=0.3)
    a.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "h3_offline_sweep.png", dpi=110)
    plt.close(fig)
    late = t >= 6.0
    return (f"średnie V_p po skręcie: {log['V_p'][late].mean() * ml:.3f} ml (zadane 3.000), "
            f"amplituda 0.5 Hz / 3 Hz: {amps[0]:.1f}° / {amps[-1]:.1f}°")


SCENARIOS = {
    "s1_straight": s1_straight,
    "s2_fluid_on_off": s2_fluid_on_off,
    "s3_turn": s3_turn,
    "s4_depth": s4_depth,
    "s5_sweep": s5_sweep,
    "h3_hydraulics": h3_hydraulics,
    "s6_righting": s6_righting,
}


def main(selected: list[str]):
    RESULTS.mkdir(exist_ok=True)
    for name, fn in SCENARIOS.items():
        if selected and not any(name.startswith(s) for s in selected):
            continue
        print(f"{name}: {fn()}  -> results/{name}.png")


if __name__ == "__main__":
    main(sys.argv[1:])
