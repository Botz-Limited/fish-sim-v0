"""Etap 2a: przegląd wariantów konstrukcji ogona – który się zgina?

Uruchomienie:  source scripts/env.sh && python scripts/run_stage2_variants.py   (~10–15 min)

Problem (plan etapu 2): przy obecnej geometrii 30 ml w komorze L zgina ogon o < 0.1°,
bo cienka ścianka zewnętrzna wydyma się jak balon. Porównujemy warianty, każdy
quasi-statycznie (komora L, R odpowietrzona, bez ciężaru, siatka coarse):
  V0 obecny, V1 kręgosłup (przegroda E×20), V2 ścianka 8 mm,
  V3 włókna obwodowe na skórze, V4 kręgosłup + włókna.
Kryterium wyboru: 15° przy p ≤ 50 kPa (p_max zaworu w MuJoCo) i ΔV ≤ 50% objętości komory
(krzywe liczone do 80%, żeby było widać trend);
spośród spełniających – najmniejsze ciśnienie.

Wyniki: results/s2_variants.csv, results/s2_variants.png, tabela na ekranie.
"""
import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fishsofa import PROJECT_DIR, headless  # noqa: E402
from fishsofa.config import TailConfig  # noqa: E402

LEVEL = "coarse"
P_MAX = 50e3          # [Pa] jak p_max w MuJoCo/fishsim/config.py (PLACEHOLDER)
TARGET_DEG = 15.0
DV_TARGETS = np.arange(2.5e-6, 75e-6, 2.5e-6)
MAX_FRACTION_SWEEP = 0.8   # liczymy dalej niż kryterium, żeby było widać trend
MAX_FRACTION_OK = 0.5      # kryterium wyboru: ΔV ≤ 50% objętości komory
RESULTS = os.path.join(PROJECT_DIR, "results")

# Każdy wariant ustawia JAWNIE wszystkie przełączniki konstrukcji: domyślny config to
# już V4, więc samo „{}” nie byłoby wariantem obecnym (tak było w jednym przebiegu).
_BASE = {"spine_E_factor": 1.0, "hoop_fibers": False, "wall_thickness": 0.004}
VARIANTS = {
    "V0 obecny": {**_BASE},
    "V1 kręgosłup E×20": {**_BASE, "spine_E_factor": 20.0},
    "V2 ścianka 8 mm": {**_BASE, "wall_thickness": 0.008},
    "V3 włókna obwodowe": {**_BASE, "hoop_fibers": True},
    "V4 kręgosłup + włókna": {**_BASE, "spine_E_factor": 20.0, "hoop_fibers": True},
}

# Paleta kategoryczna (skill dataviz, tryb jasny), stała kolejność.
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def at_angle(curve, deg):
    """ΔV i p potrzebne do |θ| = deg (interpolacja liniowa); None, jeśli nie osiągnięto."""
    th = np.degrees(np.abs(curve.tip_angle))
    for k in range(1, len(th)):
        if th[k] >= deg > th[k - 1]:
            f = (deg - th[k - 1]) / (th[k] - th[k - 1])
            return (curve.dV[k - 1] + f * (curve.dV[k] - curve.dV[k - 1]),
                    curve.p[k - 1] + f * (curve.p[k] - curve.p[k - 1]))
    return None


def main():
    os.makedirs(RESULTS, exist_ok=True)
    curves, rows = {}, []
    for name, over in VARIANTS.items():
        cfg = TailConfig(include_weight=False, **over)
        print(f"[{name}] ...", flush=True)
        c = headless.quasi_static_sweep(cfg, LEVEL, DV_TARGETS, p_stop=P_MAX, max_fraction=MAX_FRACTION_SWEEP)
        curves[name] = c
        hit = at_angle(c, TARGET_DEG)
        k = int(np.argmax(np.abs(c.tip_angle)))
        rows.append({
            "wariant": name, "V0_ml": c.v0 * 1e6,
            "max_kat_deg": float(np.degrees(np.abs(c.tip_angle[k]))), "przy_dV_ml": c.dV[k] * 1e6,
            "p_przy_max_kPa": c.p[k] / 1e3, "dV_ostatni_ml": c.dV[-1] * 1e6, "p_ostatni_kPa": c.p[-1] / 1e3,
            "dV_15deg_ml": hit[0] * 1e6 if hit else float("nan"),
            "p_15deg_kPa": hit[1] / 1e3 if hit else float("nan"),
            "wydymanie_ostatnie_mm": c.bulge[-1] * 1e3, "czas_s": c.wall_s,
        })
        r = rows[-1]
        print(f"  V0 = {r['V0_ml']:.1f} ml, max |θ| = {r['max_kat_deg']:.2f}° przy ΔV = {r['przy_dV_ml']:.1f} ml "
              f"(p = {r['p_przy_max_kPa']:.1f} kPa); 15°: "
              + (f"ΔV = {r['dV_15deg_ml']:.1f} ml, p = {r['p_15deg_kPa']:.1f} kPa" if hit else "nie osiągnięto")
              + f"; wydymanie {r['wydymanie_ostatnie_mm']:.1f} mm; {r['czas_s']:.0f} s", flush=True)

    with open(os.path.join(RESULTS, "s2_variants.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
        f.write("\n# krzywe: wariant, dV_ml, p_kPa, theta_deg, wydymanie_mm\n")
        for name, c in curves.items():
            for a, b, t, g in zip(c.dV, c.p, c.tip_angle, c.bulge):
                f.write(f"# {name},{a * 1e6:.3f},{b / 1e3:.4f},{np.degrees(t):.4f},{g * 1e3:.3f}\n")

    ok = [r for r in rows if r["p_15deg_kPa"] == r["p_15deg_kPa"]
          and r["dV_15deg_ml"] <= MAX_FRACTION_OK * r["V0_ml"] and r["p_15deg_kPa"] <= P_MAX / 1e3]
    best = min(ok, key=lambda r: r["p_15deg_kPa"]) if ok else None
    print("\nWYBÓR:", f"{best['wariant']} (15° przy {best['p_15deg_kPa']:.1f} kPa, ΔV {best['dV_15deg_ml']:.1f} ml)"
          if best else "żaden wariant nie osiąga 15° w granicach p ≤ 50 kPa i ΔV ≤ 50% V0")
    plot(curves)


def plot(curves):
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK})
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), constrained_layout=True)
    panels = [("|θ_tip| [°]", lambda c: np.degrees(np.abs(c.tip_angle)), "Kąt końcówki"),
              ("ciśnienie [kPa]", lambda c: np.array(c.p) / 1e3, "Ciśnienie w komorze L"),
              ("wydymanie względem osi [mm]", lambda c: np.array(c.bulge) * 1e3, "Boczne wybrzuszenie (skóra względem osi)")]
    for ax, (ylab, fn, title) in zip(axes, panels):
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for col, (name, c) in zip(COLORS, curves.items()):
            ax.plot(np.array(c.dV) * 1e6, fn(c), color=col, linewidth=2, marker="o", markersize=4, label=name)
        ax.set_xlabel("przyrost objętości komory L, ΔV [ml]")
        ax.set_ylabel(ylab)
        ax.set_title(title, loc="left")
    axes[0].axhline(TARGET_DEG, color=INK2, linewidth=1, linestyle="--")
    axes[0].annotate("cel 15°", (0, TARGET_DEG), textcoords="offset points", xytext=(4, 4), color=INK2, fontsize=9)
    axes[1].axhline(P_MAX / 1e3, color=INK2, linewidth=1, linestyle="--")
    axes[1].annotate("p_max 50 kPa", (0, P_MAX / 1e3), textcoords="offset points", xytext=(4, -12),
                     color=INK2, fontsize=9)
    axes[0].legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.suptitle("Etap 2a – warianty konstrukcji (coarse, quasi-statycznie, komora R odpowietrzona, bez ciężaru)",
                 x=0.01, ha="left", color=INK, fontsize=11)
    fig.savefig(os.path.join(RESULTS, "s2_variants.png"), dpi=150, facecolor="white")


if __name__ == "__main__":
    main()
