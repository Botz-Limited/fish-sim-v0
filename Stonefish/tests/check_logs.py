#!/usr/bin/env python3
"""Asercje na logach z aplikacji konsolowej (wywołuje tests/run_tests.sh).

    check_logs.py <katalog z logami>

Progi są celowo luźne w stosunku do obecnych wyników (README) – test ma wykryć
zepsucie modelu, a nie drobną zmianę parametru.
"""

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from fishcfg import load_config  # noqa: E402
from fishlog import read_log  # noqa: E402

LOGS = Path(sys.argv[1])
CFG = load_config()
failures = 0


def check(ok, what):
    global failures
    print(f"  [{' OK ' if ok else 'FAIL'}] {what}")
    failures += not ok


def at(d, t):
    return int(np.argmin(np.abs(d.t - t)))


logs = {p.stem: read_log(p) for p in sorted(LOGS.glob("*.csv"))}

print("Brak NaN/inf w logach:")
for name, d in logs.items():
    bad = [k for k, v in d.items() if not np.all(np.isfinite(v))]
    check(not bad, f"{name}: {len(d.t)} wierszy" + (f", NaN w {bad}" if bad else ""))

print("Scenariusz 1 – zawis i prostowanie:")
d = logs["s1_hover"]
i5 = at(d, 5.0)
dz = abs(d.z[i5] - d.z[0])
check(dz < 0.005, f"|Δz| po 5 s = {dz * 1e3:.2f} mm < 5 mm (start poziomo)")
dxy = math.hypot(d.x[i5] - d.x[0], d.y[i5] - d.y[0])
check(dxy < 0.005, f"dryf poziomy po 5 s = {dxy * 1e3:.2f} mm < 5 mm")
d = logs["s1_righting"]
i5 = at(d, 5.0)
r0, r5 = math.degrees(d.roll[0]), math.degrees(d.roll[i5])
check(abs(r5) < 0.5 * abs(r0), f"przechył po 5 s {r5:+.2f}° < połowa początkowego ({r0:.1f}°)")

print("Hydraulika (log scenariusza 2):")
d = logs["s2_swim"]
h = CFG["hydraulics"]
vsum = d.V_L + d.V_R
check(np.ptp(vsum) < 1e-12, f"V_L + V_R = const (rozrzut {np.ptp(vsum):.1e} m³)")
dp = np.abs(d.p_L - d.p_R)
check(dp.max() <= h["p_max"] * (1 + 1e-6) + 0.02, f"|p_L − p_R| ≤ p_max (max {dp.max() / 1e3:.2f} kPa, p_max {h['p_max'] / 1e3:.0f} kPa)")

print("Napęd wewnętrzny (bez sił wody i grawitacji):")
d = logs["t_internal"]
check(np.abs(d.tau_sum).max() < 1e-12, f"suma momentów od napędu na wszystkie bryły = 0 (max {np.abs(d.tau_sum).max():.1e} N·m)")
drift = math.hypot(np.ptp(d.com_x), np.ptp(d.com_y))
yaw_amp = math.degrees(np.ptp(d.yaw)) / 2
check(drift < 1e-3 and yaw_amp > 2.0,
      f"środek masy stoi ({drift * 1e3:.3f} mm), choć głowa kiwa się o ±{yaw_amp:.1f}°")
check(np.abs(d.Lz).max() < 1e-4, f"moment pędu L_z ≈ 0 (max {np.abs(d.Lz).max():.1e} kg·m²/s)")

print("Scenariusz 2 – pływanie:")
v = {}
for name in ("s2_swim", "s2_swim_locked"):
    d = logs[name]
    m = d.t > d.t[-1] - 5
    v[name] = float(np.mean(d.v_fwd[m]))
check(v["s2_swim"] > 0.05, f"ogon ruchomy: średnia prędkość {v['s2_swim'] * 100:.1f} cm/s > 5 cm/s")
check(abs(v["s2_swim_locked"]) < 0.005, f"ogon zablokowany: {v['s2_swim_locked'] * 100:.2f} cm/s ≈ 0")

print("Scenariusz 4 – głębokość:")
d = logs["s4_depth"]
sched = load_config(ROOT / "config" / "s4_depth.json")["depth"]["schedule"]
m = d.t > d.t[-1] - 10
err = float(np.mean(np.abs(d.z[m] - sched[-1][1])))
check(err < 0.05, f"uchyb ustalony {err * 100:.2f} cm < 5 cm (zadana {sched[-1][1]} m)")
vmin, vmax = CFG["vbs"]["v_min"], CFG["vbs"]["v_max"]
check(d.vbs_V.min() >= vmin - 1e-12 and d.vbs_V.max() <= vmax + 1e-12,
      f"VBS w zakresie: {d.vbs_V.min() * 1e6:.2f}…{d.vbs_V.max() * 1e6:.2f} ml (dozwolone {vmin * 1e6}…{vmax * 1e6} ml)")

print("\nWszystkie asercje przeszły." if not failures else f"\n{failures} asercji NIE przeszło.")
sys.exit(1 if failures else 0)
