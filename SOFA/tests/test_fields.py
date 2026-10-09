"""Tests of the GUI readout fields (pure numpy, no SOFA). Run:  pytest -q tests/test_fields.py"""
import numpy as np

from fishsofa import fields, hud

X0 = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float)
TET = np.array([[0, 1, 2, 3]])
E, NU = np.array([3e5]), 0.45


def _rot(th):
    return np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]])


def test_rigid_rotation_has_no_stress():
    assert fields.von_mises(X0, X0 @ _rot(0.7).T, TET, E, NU)[0] < 1e-6


def test_uniaxial_strain_matches_hooke_and_ignores_rotation():
    x = X0.copy()
    x[:, 0] *= 1.01                                  # 1 % strain in x, no lateral contraction
    lam = E[0] * NU / ((1 + NU) * (1 - 2 * NU))
    mu = E[0] / (2 * (1 + NU))
    expected = abs((lam + 2 * mu) * 0.01 - lam * 0.01)
    assert np.isclose(fields.von_mises(X0, x, TET, E, NU)[0], expected)
    assert np.isclose(fields.von_mises(X0, x @ _rot(1.2).T, TET, E, NU)[0], expected)


def test_node_areas_sum_to_surface_area():
    tris = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]])
    total = 1.5 + np.sqrt(3) / 2                     # three right triangles + the slanted face
    assert np.isclose(fields.node_areas(X0, tris, 4).sum(), total)


def test_sections_conserve_total_force():
    rng = np.random.default_rng(0)
    pts = rng.uniform(-0.25, 0.0, size=(200, 3))
    f = rng.normal(size=(200, 3))
    s = hud.Sections(pts, np.arange(200), n=8)
    assert np.allclose(s.forces(f).sum(axis=0), f.sum(axis=0))
