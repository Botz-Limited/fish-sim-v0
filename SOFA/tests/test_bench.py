"""Tests of the aquarium test-stand config (pure Python, no SOFA). Run:  pytest -q tests/test_bench.py"""
import numpy as np
import pytest

from fishsofa import fibers
from fishsofa.config import TailConfig, bench_config


def test_default_mount_and_geometry_unchanged():
    c = TailConfig()
    assert (c.mount, c.geometry) == ("fixed", "param")
    # param geometry: regions 0/1 only, same moduli as before the region table
    assert list(c.region_young([0, 1])) == [c.young_modulus, c.young_modulus * c.spine_E_factor]
    assert list(c.region_density([0, 1])) == [c.rho_silicone] * 2


def test_bench_uses_step_geometry_and_stand():
    c = bench_config()
    assert (c.mount, c.environment, c.geometry) == ("bench", "water", "step")
    assert c.step_tip_start == pytest.approx(0.180)


def test_bench_fallback_lengths_match_step():
    c = bench_config(geometry="param")
    assert c.tail_length == pytest.approx(0.220, abs=1e-3)           # root -> body end (STEP x 240–460 mm)
    tip = -c.fin_center_x + c.fin_semi_x
    assert tip == pytest.approx(0.260, abs=1e-3)                     # root -> fin tip (STEP x 500.3 mm)
    assert c.ry0 * c.taper_last * 2 == pytest.approx(0.0078, abs=5e-4)  # end width


def test_region_materials_are_ordered_by_stiffness():
    c = bench_config()
    e = c.region_young([0, 2, 3, 4, 5])
    assert e[0] < e[1] < e[2] < e[3]          # body < tubes < stiff tip < fin plastic
    assert e[4] == c.young_fin                # holder plate rigid
    assert c.region_density([4])[0] == c.rho_fin


def test_bench_valve_switches_at_peaks_only():
    c = bench_config()
    f_track = c.Q_const / (2 * np.pi * c.tail_volume_amp)
    assert f_track < c.tail_freq                                     # 2 switches per cycle
    assert c.Q_const / (4 * c.tail_freq) == pytest.approx(c.tail_volume_amp, rel=0.01)


def test_tube_rings_lie_on_the_tube_wall():
    c = bench_config()
    a, b = np.array([0.0, 0.015, 0.015]), np.array([-0.050, 0.012, 0.012])
    tubes = {"axis": np.array([[a, b]]), "radius": np.array([[0.0167, 0.012]])}
    r = fibers.tube_rings(c, tubes)
    assert r.n_rings == 12                                           # every 4 mm, 4 mm from the ends
    ax = (b - a) / np.linalg.norm(b - a)
    w = r.points - a
    s = w @ ax
    rad = np.linalg.norm(w - np.outer(s, ax), axis=1)
    expect = 0.0167 + (0.012 - 0.0167) * s / np.linalg.norm(b - a) - c.fiber_inset
    assert np.allclose(rad, expect, atol=1e-9)
    assert (r.stiffness > 0).all()


def test_bench_mount_rejects_bad_values():
    with pytest.raises(ValueError):
        bench_config(mount_mass=0.0)
    with pytest.raises(ValueError):
        TailConfig(mount="clamped")
    with pytest.raises(ValueError):
        TailConfig(geometry="stl")
