#!/usr/bin/env python3
"""Checks of the valve actuation model (tools/make_actuation.py).

Run from the OpenFOAM/ directory:   python tools/test_make_actuation.py
(also works with pytest). Fast: no CFD/FEM, only the valve ODE.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import make_actuation as ma  # noqa: E402

SCRIPT = Path(__file__).parent / "make_actuation.py"


def run_valve(freq, t_end=6.0):
    return ma.valve_model(t_end, freq, 1.0 / freq, ma.Q_CONST, ma.VOLUME_AMP,
                          ma.TAU_VALVE, ma.HYSTERESIS)


def test_valve_holds_each_state_for_min_dwell():
    for f in (ma.TAIL_FREQ_MIN, 2.0, ma.TAIL_FREQ_MAX):
        t, _, _, _, s = run_valve(f)
        t_sw = t[1:][np.diff(s) != 0]
        assert len(t_sw) > 4, f"{f} Hz: valve hardly switches"
        gap = np.diff(t_sw).min()
        assert gap >= ma.VALVE_MIN_DWELL - 1e-9, f"{f} Hz: min. gap {gap:.4f} s"


def test_two_switches_per_cycle_above_tracking_limit():
    """In the whole range the valve switches only at the peaks (~2 per cycle)."""
    for f in (1.5, 1.75, 2.0, 2.25, 2.5):
        t, _, _, _, s = run_valve(f, t_end=8.0)
        after = t >= 2.0 / f
        sw = np.count_nonzero(np.diff(s[after]) != 0) / ((t[-1] - 2.0 / f) * f)
        assert 1.8 <= sw <= 2.3, f"{f} Hz: {sw:.2f} switches/cycle"


def test_frequency_range():
    f_track = ma.Q_CONST / (2 * np.pi * ma.VOLUME_AMP)
    assert ma.TAIL_FREQ_MIN >= f_track
    assert ma.TAIL_FREQ_MIN == 1.5          # user decision (all demos)
    assert ma.TAIL_FREQ_MAX <= 1.0 / (2 * ma.VALVE_MIN_DWELL) + 1e-12
    assert ma.check_freq(ma.TAIL_FREQ_MIN) == ma.TAIL_FREQ_MIN
    assert ma.check_freq(ma.TAIL_FREQ_MAX) == ma.TAIL_FREQ_MAX
    for bad in (0.5, 1.0, 1.25, 3.0):
        try:
            ma.check_freq(bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad} Hz accepted")


def _cli(*args):
    with tempfile.TemporaryDirectory() as d:
        return subprocess.run([sys.executable, str(SCRIPT), d, *args],
                              capture_output=True, text=True)


def test_cli_rejects_out_of_range_frequency():
    for f in ("0.5", "1.25", "3.0"):
        r = _cli("--p0", "15000", "--freq", f, "--t-end", "1")
        assert r.returncode != 0 and "outside the valve range" in r.stderr, r.stderr
    # passive tail and the old sine waveform are not limited
    assert _cli("--p0", "0", "--freq", "1", "--t-end", "1").returncode == 0
    assert _cli("--p0", "15000", "--freq", "1", "--t-end", "1", "--waveform", "sine").returncode == 0
    assert _cli("--p0", "15000", "--freq", "1.5", "--t-end", "2").returncode == 0


def test_pressure_below_relief_valve():
    p0 = 15e3
    c_h = ma.VOLUME_AMP / p0
    for f in (ma.TAIL_FREQ_MIN, ma.TAIL_FREQ_MAX):
        _, _, v, _, _ = run_valve(f)
        assert np.abs(v / c_h).max() < ma.P_MAX, f"{f} Hz: relief valve opens"


if __name__ == "__main__":
    tests = [(n, fn) for n, fn in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}: {e}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
