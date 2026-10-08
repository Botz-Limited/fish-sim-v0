#!/usr/bin/env python3
"""Assertions on the logs from the console application (called by tests/run_tests.sh).

    check_logs.py <log directory>

The thresholds are deliberately loose relative to the current results (README) – the test is meant to detect
a broken model, not a small parameter change.
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

print("No NaN/inf in the logs:")
for name, d in logs.items():
    bad = [k for k, v in d.items() if not np.all(np.isfinite(v))]
    check(not bad, f"{name}: {len(d.t)} rows" + (f", NaN in {bad}" if bad else ""))

print("Scenario 1 – hover and righting:")
d = logs["s1_hover"]
i5 = at(d, 5.0)
dz = abs(d.z[i5] - d.z[0])
check(dz < 0.005, f"|Δz| after 5 s = {dz * 1e3:.2f} mm < 5 mm (level start)")
dxy = math.hypot(d.x[i5] - d.x[0], d.y[i5] - d.y[0])
check(dxy < 0.005, f"horizontal drift after 5 s = {dxy * 1e3:.2f} mm < 5 mm")
d = logs["s1_righting"]
i5 = at(d, 5.0)
r0, r5 = math.degrees(d.roll[0]), math.degrees(d.roll[i5])
check(abs(r5) < 0.5 * abs(r0), f"roll after 5 s {r5:+.2f}° < half of the initial ({r0:.1f}°)")

print("Hydraulics (scenario 2 log):")
d = logs["s2_swim"]
h = CFG["hydraulics"]
vsum = d.V_L + d.V_R
check(np.ptp(vsum) < 1e-12, f"V_L + V_R = const (spread {np.ptp(vsum):.1e} m³)")
dp = np.abs(d.p_L - d.p_R)
check(dp.max() <= h["p_max"] * (1 + 1e-6) + 0.02, f"|p_L − p_R| ≤ p_max (max {dp.max() / 1e3:.2f} kPa, p_max {h['p_max'] / 1e3:.0f} kPa)")

print("Internal actuation (no water forces or gravity):")
d = logs["t_internal"]
check(np.abs(d.tau_sum).max() < 1e-12, f"sum of drive torques on all bodies = 0 (max {np.abs(d.tau_sum).max():.1e} N·m)")
drift = math.hypot(np.ptp(d.com_x), np.ptp(d.com_y))
yaw_amp = math.degrees(np.ptp(d.yaw)) / 2
check(drift < 1e-3 and yaw_amp > 2.0,
      f"center of mass stays put ({drift * 1e3:.3f} mm), although the head swings by ±{yaw_amp:.1f}°")
check(np.abs(d.Lz).max() < 1e-4, f"angular momentum L_z ≈ 0 (max {np.abs(d.Lz).max():.1e} kg·m²/s)")

print("Scenario 2 – swimming:")
v = {}
for name in ("s2_swim", "s2_swim_locked"):
    d = logs[name]
    m = d.t > d.t[-1] - 5
    v[name] = float(np.mean(d.v_fwd[m]))
check(v["s2_swim"] > 0.05, f"tail moving: mean speed {v['s2_swim'] * 100:.1f} cm/s > 5 cm/s")
check(abs(v["s2_swim_locked"]) < 0.005, f"tail locked: {v['s2_swim_locked'] * 100:.2f} cm/s ≈ 0")

print("Scenario 4 – depth:")
d = logs["s4_depth"]
sched = load_config(ROOT / "config" / "s4_depth.json")["depth"]["schedule"]
m = d.t > d.t[-1] - 10
err = float(np.mean(np.abs(d.z[m] - sched[-1][1])))
check(err < 0.05, f"steady-state error {err * 100:.2f} cm < 5 cm (reference {sched[-1][1]} m)")
vmin, vmax = CFG["vbs"]["v_min"], CFG["vbs"]["v_max"]
check(d.vbs_V.min() >= vmin - 1e-12 and d.vbs_V.max() <= vmax + 1e-12,
      f"VBS in range: {d.vbs_V.min() * 1e6:.2f}…{d.vbs_V.max() * 1e6:.2f} ml (allowed {vmin * 1e6}…{vmax * 1e6} ml)")

print("\nAll assertions passed." if not failures else f"\n{failures} assertion(s) FAILED.")
sys.exit(1 if failures else 0)
