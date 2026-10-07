"""Sanity tests (spec section 9), grouped by stage."""

from dataclasses import replace

import numpy as np
import pytest

from fishrod import scenarios as S
from fishrod.config import default_config
from fishrod.hydraulics import TailHydraulics, TailRhythm
from fishrod.run import SimulationBlowUp
from fishrod.buoyancy import Bladder
from fishrod.water import drag_kernel

# n = 50 is enough for the spec thresholds (error ~1/n) and runs 4× faster than n = 100.
N_TEST = 50


@pytest.fixture(scope="module")
def cfg():
    return S.coarse(default_config(), N_TEST)


# ---------------------------------------------------------------- stage 1
def test_cantilever_arc_matches_theory(cfg):
    r = S.cantilever_arc(cfg, verbose=False)
    assert r["tip_err"] < 0.02
    assert r["shape_err"] < 0.02
    # curvature is constant along the rod and equal to M/(EI)
    np.testing.assert_allclose(r["kappa"], r["kappa_th"], rtol=0.01)


def test_natural_frequency_and_energy(cfg):
    r = S.cantilever_free_vibration(cfg, verbose=False)
    assert r["freq_err"] < 0.05
    # without damping and water the energy does not drift (symplectic integrator)
    assert r["energy_drift"] < 0.005
    assert np.all(np.isfinite(r["y_tip"]))


def test_blow_up_is_detected(cfg):
    # a too large step (3× the estimate) must be detected instead of computing on
    bad = replace(cfg, numerics=replace(cfg.numerics, dt_safety=3.0),
                  stage1=replace(cfg.stage1, t_free=1.0))
    with pytest.raises(SimulationBlowUp):
        S.cantilever_free_vibration(bad, verbose=False)


# ---------------------------------------------------------------- stage 2
@pytest.fixture(scope="module")
def fish_cfg():
    return default_config()


def test_rest_curvature_static_bend(fish_cfg):
    r = S.static_bend_pressure(fish_cfg, 20e3)
    # with no external loads the rod takes exactly its rest shape
    assert abs(r["theta"] - r["theta_th"]) < 1e-3 * abs(r["theta_th"])
    assert abs(r["tip_y"] - r["tip_y_th"]) < 0.02 * abs(r["tip_y_th"])
    assert r["theta"] > 0      # Δp > 0 (chamber L) bends the tail to the right
    assert r["tip_y"] < 0


def test_hydraulic_coupling_static(fish_cfg):
    r = S.static_bend_volume(fish_cfg, 8e-6)
    assert abs(r["dp"] - r["dp_th"]) < 0.01 * r["dp_th"]
    assert abs(r["theta"] - r["theta_th"]) < 0.01 * r["theta_th"]


@pytest.fixture(scope="module")
def vacuum(fish_cfg):
    cfg = replace(fish_cfg, stage2=replace(fish_cfg.stage2, t_free=1.5))
    return {m: S.free_vacuum(cfg, m) for m in ("rest_curvature", "single_torque")}


def test_internal_actuation_keeps_center_of_mass(vacuum):
    r = vacuum["rest_curvature"]
    assert np.max(np.abs(r["theta"])) > np.radians(5)     # the tail really beats
    assert np.max(np.linalg.norm(r["x_cm"], axis=1)) < 1e-6 * r["length"]
    assert np.max(np.abs(r["L"])) < 1e-8


def test_unbalanced_torque_is_detected(vacuum):
    # a single external torque does not move the center of mass (no net force) but
    # rotates the whole fish – which is why angular momentum is checked too
    r = vacuum["single_torque"]
    assert np.max(np.linalg.norm(r["x_cm"], axis=1)) < 1e-6 * r["length"]
    assert np.max(np.abs(r["L"][:, 2])) > 1e-4


def test_hydraulics_closed_loop_and_relief_valve(fish_cfg):
    """Tail locked (θ = 0), the pump pushes a constant 32 ml: without the valve
    Δp = V/C_h ≈ 71 kPa. The valve must hold p_max and the total chamber volume must
    stay constant (closed circuit)."""
    hc = fish_cfg.hydraulics
    hyd = TailHydraulics(hc, TailRhythm(hc, amp=0.0, bias=4 * hc.tail_volume_amp))
    V0 = hyd.V_L + hyd.V_R
    dps = []
    for i in range(20000):
        dps.append(hyd.step(i * 1e-4, 0.0, 1e-4))
        assert abs(hyd.V_L + hyd.V_R - V0) < 1e-15
    dps = np.array(dps)
    assert np.max(np.abs(dps)) <= hc.p_max * (1 + 1e-9)
    assert np.max(np.abs(dps)) > 0.99 * hc.p_max     # the valve actually opened


# ---------------------------------------------------------------- stage 3
def test_drag_dissipates_energy():
    """Drag power P = Σ F·v ≤ 0 for any velocities and cross-section orientations."""
    rng = np.random.default_rng(0)
    n = 30
    for _ in range(50):
        vel = rng.normal(size=(3, n + 1))
        Q = np.empty((3, 3, n))
        for k in range(n):
            q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
            Q[..., k] = q.T                       # rows = d1, d2, d3 (orthonormal)
        ext = np.zeros((3, n + 1))
        total = np.zeros(4)
        drag_kernel(vel, Q, rng.uniform(0.005, 0.01, n), rng.uniform(0.002, 0.03, n),
                    rng.uniform(0.002, 0.03, n), 1000.0, 1.2, 0.01, ext, total)
        assert total[3] <= 0.0
        # power from the nodal forces is also ≤ 0 (element force split in half)
        assert np.sum(ext * vel) <= 1e-12


@pytest.fixture(scope="module")
def tethered_runs(fish_cfg):
    cfg = replace(fish_cfg, stage3=replace(fish_cfg.stage3, t_end=3.0, t_analyze=2.0))
    return {m: S.tethered(cfg, m) for m in ("none", "drag+reactive")}


def test_tethered_water_damps_and_pushes(tethered_runs):
    vac, wat = tethered_runs["none"], tethered_runs["drag+reactive"]
    assert abs(vac["thrust"]) < 1e-9              # no force on the mount in vacuum
    assert wat["thrust"] > 0.01                   # water gives thrust towards the head [N]
    assert wat["amp_tip"] < vac["amp_tip"]        # water damps the tail motion
    assert np.max(wat["P_drag"]) <= 0.0           # drag only dissipates energy


# ---------------------------------------------------------------- stage 4
@pytest.fixture(scope="module")
def swims(fish_cfg):
    cfg = replace(fish_cfg, stage4=replace(fish_cfg.stage4, t_end=4.0))
    return {m: S.free_swim(cfg, m) for m in ("none", "drag+reactive")}


def test_free_swim_moves_forward_in_water(swims):
    r = swims["drag+reactive"]
    assert r["U_final"] > 0.05                  # [m/s] swims forward (nose first)
    assert np.all(np.isfinite(r["frames"]))
    assert np.max(r["z_max"]) < 1e-9            # planar motion (no gravity)


def test_free_swim_in_vacuum_does_not_move(swims):
    r = swims["none"]
    assert abs(r["U_final"]) < 1e-3
    assert r["distance"] < 0.01 * r["length"]


# ---------------------------------------------------------------- stage 5
def test_tail_natural_frequency_scales_with_stiffness(fish_cfg):
    """f_n ∝ √E for the silicone alone; the hydraulic spring (independent of E) makes
    the ratio slightly smaller than √2."""
    cfg = replace(fish_cfg, stage5=replace(fish_cfg.stage5, t_free=2.0))
    f1 = S.tail_natural_frequency(cfg, 1.0)["f_n"]
    f2 = S.tail_natural_frequency(cfg, 2.0)["f_n"]
    assert 1.25 < f2 / f1 < np.sqrt(2) * 1.01


# ---------------------------------------------------------------- stage 6
def test_neutral_buoyancy_hovers(fish_cfg):
    r = S.depth_control(fish_cfg, depth_pid=False, t_end=2.0, swim=False)
    assert abs(r["z"][-1] - r["z"][0]) < 2e-3        # [m] stays in place
    assert np.max(np.abs(r["pitch"])) < 1.0          # [°] bladder above the center of mass does not pitch the fish


def test_extra_bladder_volume_rises(fish_cfg):
    r = S.depth_control(fish_cfg, depth_pid=False, t_end=2.0, swim=False, V_offset=5e-6)
    assert r["z"][-1] - r["z"][0] > 0.02             # +5 ml -> rises


def test_bladder_rate_limit_and_range(fish_cfg):
    bc = fish_cfg.buoyancy
    b = Bladder(bc, 0.5 * (bc.V_min + bc.V_max))
    dt = 1e-3
    V_prev = b.V
    for i in range(20000):
        V = b.step(bc.V_max * 2 if i < 10000 else -1.0, dt)
        assert abs(V - V_prev) <= bc.q_max * dt * (1 + 1e-12)
        assert bc.V_min <= V <= bc.V_max
        V_prev = V
