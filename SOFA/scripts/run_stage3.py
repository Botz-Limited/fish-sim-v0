"""Etap 3: symetria – komora R ma dać lustrzane odbicie wyniku komory L.

Uruchomienie:  source scripts/env.sh && python scripts/run_stage3.py   (~10 min)
               python scripts/run_stage3.py --plot-only                (tylko wykres z CSV)

Te same warunki co etap 2 (V4, bez ciężaru, druga komora odpowietrzona), osobno dla L
i dla R, na trzech poziomach siatki. Siatka i włókna są lustrzane względem płaszczyzny
XZ, więc oczekujemy: p_R = p_L, wydymanie R = L, θ_R = −θ_L.

Przy okazji kontrola CHOLMOD: krzywa L z tego skryptu (solver "cholmod") kontra
results/s2_curves.csv (etap 2 liczony jeszcze z "ldl").

Wyniki w results/: s3_symmetry.png, s3_symmetry.csv, s3_symmetry.txt.
"""
import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fishsofa import PROJECT_DIR, headless, mesh_gen  # noqa: E402
from fishsofa.config import TailConfig  # noqa: E402

LEVELS = ["coarse", "medium", "fine"]
RESULTS = os.path.join(PROJECT_DIR, "results")
COLORS = {"coarse": "#2a78d6", "medium": "#eb6834", "fine": "#1baf7a"}   # jak w etapie 2
SIDE_COLORS = {"L": "#2a78d6", "R": "#eb6834"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
FLOOR = 1e-7   # [%] – dolna granica skali log (dokładna zgodność = 0)


def asymmetry(L, R):
    """Błędy symetrii w każdym punkcie [%]: kąt, ciśnienie, wydymanie."""
    thL, thR = np.array(L["theta"]), np.array(R["theta"])
    pL, pR = np.array(L["p"]), np.array(R["p"])
    bL, bR = np.array(L["bulge"]), np.array(R["bulge"])
    return (np.abs(thL + thR) / np.abs(thL) * 100, np.abs(pR - pL) / pL * 100,
            np.abs(bR - bL) / np.abs(bL) * 100)


def main():
    os.makedirs(RESULTS, exist_ok=True)
    cfg = TailConfig(include_weight=False)
    targets = np.arange(5e-6, cfg.dV_max + 1e-12, 5e-6)
    data = {}
    for lv in LEVELS:
        mesh_gen.ensure(cfg, lv)
        for side in ("L", "R"):
            c = headless.quasi_static_sweep(cfg, lv, targets, side=side, ramp_steps=3)
            data[lv, side] = {"dV": c.dV, "p": c.p, "theta": c.tip_angle, "bulge": c.bulge}
            print(f"[{lv} {side}] ΔV = {c.dV[-1] * 1e6:.1f} ml -> p = {c.p[-1] / 1e3:.3f} kPa, "
                  f"θ = {np.degrees(c.tip_angle[-1]):+.3f}°; {c.wall_s:.0f} s", flush=True)

    with open(os.path.join(RESULTS, "s3_symmetry.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["level", "side", "dV_ml", "p_kPa", "theta_deg", "bulge_mm"])
        for (lv, side), d in data.items():
            for a, b, t, u in zip(d["dV"], d["p"], d["theta"], d["bulge"]):
                w.writerow([lv, side, f"{a * 1e6:.6f}", f"{b / 1e3:.8f}", f"{np.degrees(t):.8f}", f"{u * 1e3:.8f}"])

    lines = ["Etap 3 – symetria L/R (V4, bez ciężaru, druga komora odpowietrzona)",
             "maksymalny błąd symetrii na 5…50 ml: |θL+θR|/|θL|, |pR−pL|/pL, |bR−bL|/|bL|", ""]
    for lv in LEVELS:
        e_th, e_p, e_b = asymmetry(data[lv, "L"], data[lv, "R"])
        lines.append(f"  {lv:6s}: θ {e_th.max():.2e}%, p {e_p.max():.2e}%, wydymanie {e_b.max():.2e}%")
    lines += ["", "Kontrola CHOLMOD (etap 3) vs LDL (etap 2, results/s2_curves.csv), komora L:"]
    s2 = _read_s2()
    for lv in LEVELS:
        if lv not in s2:
            continue
        d = data[lv, "L"]
        n = min(len(d["p"]), len(s2[lv]["p"]))
        dp = np.abs(np.array(d["p"][:n]) / np.array(s2[lv]["p"][:n]) - 1).max() * 100
        dth = np.abs(np.array(d["theta"][:n]) / np.array(s2[lv]["theta"][:n]) - 1).max() * 100
        lines.append(f"  {lv:6s}: max różnica p {dp:.2e}%, θ {dth:.2e}%")
    txt = "\n".join(lines)
    print("\n" + txt)
    with open(os.path.join(RESULTS, "s3_symmetry.txt"), "w") as f:
        f.write(txt + "\n")
    plot(data, cfg)


def _read_s2():
    out = {}
    path = os.path.join(RESULTS, "s2_curves.csv")
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for row in csv.DictReader(f):
            d = out.setdefault(row["level"], {"p": [], "theta": []})
            d["p"].append(float(row["p_kPa"]) * 1e3)
            d["theta"].append(np.radians(float(row["theta_deg"])))
    return out


def _style(ax):
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def plot(data, cfg):
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK})
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(14, 4.6), constrained_layout=True)
    for ax in (a, b, c):
        _style(ax)

    # Panel 1: krzywe kąta dla fine – L linią, odbite R znacznikami (nakładają się).
    L, R = data["fine", "L"], data["fine", "R"]
    x = np.r_[0, np.array(L["dV"]) * 1e6]
    a.plot(x, np.r_[0, np.degrees(L["theta"])], color=SIDE_COLORS["L"], linewidth=2,
           label="komora L: θ")
    a.plot(np.r_[0, np.array(R["dV"]) * 1e6], np.r_[0, -np.degrees(R["theta"])], linestyle="none",
           marker="o", markersize=8, markerfacecolor="none", markeredgewidth=2,
           color=SIDE_COLORS["R"], label="komora R: −θ")
    e_th = asymmetry(L, R)[0].max()
    a.set_xlabel("przyrost objętości komory, ΔV [ml]")
    a.set_ylabel("kąt końcówki [°]")
    a.set_title(f"fine: θ(L) i −θ(R) – max różnica {e_th:.1e}%", loc="left", fontsize=10)
    a.legend(frameon=False, labelcolor=INK)

    # Panele 2–3: błąd symetrii na trzech poziomach siatki (skala log).
    for ax, k, name in ((b, 0, "kąta |θL+θR| / |θL|"), (c, 1, "ciśnienia |pR−pL| / pL")):
        for lv in LEVELS:
            err = np.maximum(asymmetry(data[lv, "L"], data[lv, "R"])[k], FLOOR)
            ax.plot(np.array(data[lv, "L"]["dV"]) * 1e6, err, color=COLORS[lv], linewidth=2,
                    marker="o", markersize=5, label=lv)
        ax.set_yscale("log")
        ax.set_xlabel("przyrost objętości komory, ΔV [ml]")
        ax.set_ylabel("błąd symetrii [%]")
        ax.set_title(f"Błąd symetrii {name}", loc="left", fontsize=10)
        ax.legend(frameon=False, labelcolor=INK)

    fig.suptitle("Etap 3 – symetria: komora R daje lustrzane odbicie komory L\n"
                 f"V4; E = {cfg.young_modulus:.0e} Pa (PLACEHOLDER); druga komora odpowietrzona; bez ciężaru; "
                 f"błąd 0 rysowany jako {FLOOR:g}%", x=0.01, ha="left", color=INK, fontsize=11)
    fig.savefig(os.path.join(RESULTS, "s3_symmetry.png"), dpi=150, facecolor="white")
    plt.close(fig)


def plot_from_csv():
    data = {}
    with open(os.path.join(RESULTS, "s3_symmetry.csv")) as f:
        for row in csv.DictReader(f):
            d = data.setdefault((row["level"], row["side"]), {"dV": [], "p": [], "theta": [], "bulge": []})
            d["dV"].append(float(row["dV_ml"]) * 1e-6)
            d["p"].append(float(row["p_kPa"]) * 1e3)
            d["theta"].append(np.radians(float(row["theta_deg"])))
            d["bulge"].append(float(row["bulge_mm"]) * 1e-3)
    plot(data, TailConfig())


if __name__ == "__main__":
    if "--plot-only" in sys.argv:
        plot_from_csv()
    else:
        main()
