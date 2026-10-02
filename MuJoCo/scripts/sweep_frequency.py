"""Etap 6: przegląd częstotliwości ogona -> prędkość i amplituda.

  .venv/bin/python scripts/sweep_frequency.py                   # 0.5…3 Hz co 0.25
  .venv/bin/python scripts/sweep_frequency.py --fmin 1 --fmax 2 --step 0.1

Dwa efekty do zobaczenia na wykresie:
  1) pompa nie nadąża: powyżej f_sat = Q_max/(2π·A_V) amplituda ruchu napędzanego
     przegubu spada ~1/f (stały wydatek pompy rozkłada się na krótszy cykl),
  2) rezonans ogona: amplituda płetwy ma maksimum, a faza końca ogona względem
     nasady przechodzi przez ~90°. UWAGA: passive_resonance_hz liczone przy
     "zamrożonych" pozostałych przegubach i nieruchomym kadłubie – w pełnym modelu
     (swobodny kadłub + sprężyna hydrauliczna) maksimum wypada niżej.
Prędkość to wypadkowa: rośnie z f, dopóki pompa nadąża, potem spada.
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from fishsim.config import FishConfig  # noqa: E402
from fishsim.controllers import TailRhythm  # noqa: E402
from fishsim.sim import FishSim, forward_speed  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"


def amplitude(x):
    """Amplituda (pół rozpiętości międzyszczytowej)."""
    return 0.5 * (np.max(x) - np.min(x))


def phase_lag_deg(t, a, b, freq):
    """Opóźnienie fazy sygnału b względem a przy częstotliwości freq [°] (rzut na e^{−iωt})."""
    w = np.exp(-2j * np.pi * freq * t)
    return float(np.degrees(np.angle(np.sum(a * w) / np.sum(b * w))))


def run_sweep(freqs, duration=20.0, t_measure=10.0, cfg_kwargs=None):
    """Dla każdej f: prędkość ustalona, amplitudy θ1 i kąta płetwy, faza końca ogona."""
    rows = []
    for f in freqs:
        cfg = FishConfig(tail_freq=float(f), **(cfg_kwargs or {}))
        log = FishSim(cfg, rhythm=TailRhythm(cfg)).run(duration)
        late = log["t"] >= t_measure
        th = log["theta"][late]
        fin = th.sum(axis=1)   # kąt płetwy względem kadłuba = suma kątów przegubów
        rows.append(dict(
            f=float(f),
            v=forward_speed(log, f, t_skip=t_measure),
            amp_L=np.degrees(amplitude(log["L"][late])),
            amp_theta1=np.degrees(amplitude(th[:, 0])),
            amp_fin=np.degrees(amplitude(fin)),
            lag_tip=phase_lag_deg(log["t"][late], th[:, 0], th[:, -1], f),
            u_sat=float(np.mean(np.abs(log["u"][late]) >= 1.0)),
        ))
    return rows


def plot_sweep(rows, path, cfg=None):
    cfg = cfg or FishConfig()
    f = np.array([r["f"] for r in rows])
    v = np.array([r["v"] for r in rows]) * 100
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(f, v, "o-", color="tab:blue", label="prędkość postępowa")
    ax.set_xlabel("częstotliwość machania [Hz]")
    ax.set_ylabel("prędkość [cm/s]", color="tab:blue")
    ax.tick_params(axis="y", colors="tab:blue")
    ax2 = ax.twinx()
    ax2.plot(f, [r["amp_L"] for r in rows], "s--", color="tab:orange",
             label="amplituda L = Σw·θ (to steruje pompa)")
    ax2.plot(f, [r["amp_theta1"] for r in rows], ".:", color="tab:red", lw=1, label="amplituda θ1")
    ax2.plot(f, [r["amp_fin"] for r in rows], "^--", color="tab:green", label="amplituda kąta płetwy (Σθ)")
    ax2.set_ylabel("amplituda [°]")
    f_sat = cfg.Q_max / (2 * np.pi * cfg.tail_volume_amp)
    for x, txt in ((f_sat, f"pompa nasyca się\nf ≈ {f_sat:.2f} Hz"),
                   (cfg.passive_resonance_hz,
                    f"f_res z configu\n{cfg.passive_resonance_hz} Hz (przybliżenie\nprzy sztywnym kadłubie)")):
        if f.min() <= x <= f.max():
            ax.axvline(x, color="gray", ls=":", lw=1)
            ax.text(x, ax.get_ylim()[1] * 0.97, txt, ha="center", va="top", fontsize=8,
                    bbox=dict(fc="white", ec="none", alpha=0.8))
    lines = ax.get_lines()[:1] + ax2.get_lines()
    ax.legend(lines, [ln.get_label() for ln in lines], loc="lower right", fontsize=8)
    ax.set_title("s5: przegląd częstotliwości – prędkość i amplituda ogona")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def save_rows(rows, path):
    import csv
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def print_rows(rows):
    print(f"{'f [Hz]':>7}{'v [cm/s]':>10}{'L [°]':>8}{'θ1 [°]':>9}{'płetwa [°]':>12}{'faza końca [°]':>16}{'nasycenie u':>13}")
    for r in rows:
        print(f"{r['f']:7.2f}{r['v'] * 100:10.2f}{r['amp_L']:8.1f}{r['amp_theta1']:9.1f}{r['amp_fin']:12.1f}"
              f"{r['lag_tip']:16.0f}{r['u_sat'] * 100:12.0f}%")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fmin", type=float, default=0.5)
    ap.add_argument("--fmax", type=float, default=3.0)
    ap.add_argument("--step", type=float, default=0.25)
    args = ap.parse_args(argv)
    freqs = np.arange(args.fmin, args.fmax + 1e-9, args.step)
    rows = run_sweep(freqs)
    print_rows(rows)
    RESULTS.mkdir(exist_ok=True)
    plot_sweep(rows, RESULTS / "s5_sweep.png")
    save_rows(rows, RESULTS / "s5_sweep.csv")
    print("zapisano results/s5_sweep.png")
    return rows


if __name__ == "__main__":
    main(sys.argv[1:])
