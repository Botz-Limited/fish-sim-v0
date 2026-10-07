"""Sanity tests (headless). Run:  source scripts/env.sh && pytest -q

They use the coarse "test" mesh, generated once into a temporary directory (meshes/ is untouched).
"""
import importlib.util
import os

import numpy as np
import pytest

from fishsofa import PROJECT_DIR, geometry, masses, mesh_gen
from fishsofa.config import TailConfig

LEVEL = "test"


@pytest.fixture(scope="session")
def cfg():
    return TailConfig()


@pytest.fixture(scope="session")
def mesh_root(tmp_path_factory, cfg):
    root = str(tmp_path_factory.mktemp("meshes"))
    mesh_gen.ensure(cfg, LEVEL, root)
    return root


@pytest.fixture(scope="session")
def mesh(cfg, mesh_root):
    return mesh_gen.load(cfg, LEVEL, mesh_root)


@pytest.fixture(scope="session")
def report(mesh, cfg):
    return mesh_gen.quality_report(mesh, cfg)


# ----------------------------------------------------------------------------- mesh

def test_no_degenerate_tets(mesh):
    assert (mesh_gen.tet_volumes(mesh.points, mesh.tets) > 0).all()


def test_surfaces_closed_and_outward(report):
    # Closed surfaces + positive signed volume = consistent normals.
    assert report["open_edges"] == [0, 0, 0]
    # The outer surface encloses the silicone TOGETHER with the cavities.
    v_in = report["volume_solid_m3"] + report["volume_chamber_L_m3"] + report["volume_chamber_R_m3"]
    assert report["volume_outer_m3"] == pytest.approx(v_in, rel=1e-9)


def test_chambers_closed_positive_and_equal(mesh, report):
    v_L, v_R = report["volume_chamber_L_m3"], report["volume_chamber_R_m3"]
    # SoftRobots convention (stage 0): normals pointing out of the cavity -> signed volume > 0.
    assert v_L > 0 and v_R > 0
    assert v_L == pytest.approx(v_R, rel=1e-12)
    # Cavity volume from geometry: elliptical cross-section (semi-axes minus wall) clipped
    # by the septum – computed numerically, independent of the mesh. The mesh (flat
    # triangles on a curved surface) gives slightly less.
    cfg = TailConfig()
    x1, x2 = cfg.chamber_x_range
    xs = np.linspace(x2, x1, 401)
    def area(x):
        s = cfg.scale_at(x)
        a, b = cfg.ry0 * s - cfg.wall_thickness, cfg.rz0 * s - cfg.wall_thickness
        y0 = cfg.septum_thickness / 2
        y = np.linspace(y0, a, 2001)
        return np.trapezoid(2 * b * np.sqrt(np.clip(1 - (y / a) ** 2, 0, None)), y)
    v_exact = np.trapezoid([area(x) for x in xs], xs)
    assert v_L == pytest.approx(v_exact, rel=0.05)


def test_chambers_on_correct_side(mesh, cfg):
    yL = mesh.points[np.unique(mesh.tri_chamber_L), 1]
    yR = mesh.points[np.unique(mesh.tri_chamber_R), 1]
    assert yL.min() >= cfg.septum_thickness / 2 - 1e-9
    assert yR.max() <= -cfg.septum_thickness / 2 + 1e-9


def test_mesh_is_mirror_symmetric(report):
    assert report["mirror_symmetric"]


def test_base_nodes_at_x0(mesh):
    assert len(mesh.base_nodes) > 0
    assert np.allclose(mesh.points[mesh.base_nodes, 0], 0.0)


def test_fin_nodes_behind_tail(mesh, cfg):
    assert len(mesh.fin_nodes) > 0
    assert (mesh.points[mesh.fin_nodes, 0] < -cfg.tail_length).all()


def test_vtk_file_matches_npz(mesh, cfg, mesh_root):
    # The scene reads tail.vtk, and measurements use tail_meta.npz – they must share the same nodes.
    path = os.path.join(mesh_gen.mesh_dir(cfg, LEVEL, mesh_root), "tail.vtk")
    with open(path) as f:
        lines = f.read().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("POINTS"))
    n = int(lines[i].split()[1])
    pts = np.loadtxt(lines[i + 1:i + 1 + n])
    assert np.allclose(pts, mesh.points, atol=1e-8)


# ----------------------------------------------------------------------------- mass and weight

def test_total_mass(mesh, cfg, report):
    mm = masses.build(mesh, cfg)
    expected = (cfg.rho_silicone * report["volume_solid_m3"]
                + cfg.rho_water * (report["volume_chamber_L_m3"] + report["volume_chamber_R_m3"]))
    assert mm.node_mass.sum() == pytest.approx(expected, rel=1e-9)
    assert -mm.node_weight[:, 2].sum() == pytest.approx(cfg.gravity * expected, rel=1e-9)


def test_water_weight_excludes_chamber_water(mesh, report):
    cfg_w = TailConfig(environment="water")
    mm = masses.build(mesh, cfg_w)
    m_sil = cfg_w.rho_silicone * report["volume_solid_m3"]
    expected = cfg_w.gravity * (1 - cfg_w.rho_water / cfg_w.rho_silicone) * m_sil
    assert -mm.node_weight[:, 2].sum() == pytest.approx(expected, rel=1e-9)
    # The inertia of the chamber water remains.
    assert mm.mass_water > 0
    assert mm.node_mass.sum() == pytest.approx(m_sil + mm.mass_water, rel=1e-9)


# ----------------------------------------------------------------------------- measurement geometry

def test_tip_angle_zero_for_straight_tail(mesh):
    base = geometry.base_center(mesh.points, mesh.base_nodes)
    assert geometry.tip_angle(mesh.points, base, mesh.fin_nodes) == pytest.approx(0.0, abs=1e-9)


def test_tip_angle_sign(mesh):
    base = geometry.base_center(mesh.points, mesh.base_nodes)
    x = mesh.points.copy()
    x[mesh.fin_nodes, 1] += 0.01   # shift the fin toward +Y
    assert geometry.tip_angle(x, base, mesh.fin_nodes) > 0


# ----------------------------------------------------------------------------- consistency with MuJoCo

def test_dimensions_match_mujoco(cfg):
    path = os.path.join(PROJECT_DIR, "..", "MuJoCo", "fishsim", "config.py")
    if not os.path.exists(path):
        pytest.skip("MuJoCo/fishsim/config.py not found")
    spec = importlib.util.spec_from_file_location("mujoco_fish_config", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    m = mod.FishConfig()
    assert cfg.n_segments == m.n_segments
    assert cfg.n_actuated == m.n_actuated
    assert cfg.segment_length == m.segment_length
    assert (cfg.ry0, cfg.rz0, cfg.taper_last) == (m.segment_ry0, m.segment_rz0, m.taper_last)
    assert (cfg.fin_semi_x, cfg.fin_thickness / 2, cfg.fin_semi_z) == pytest.approx(m.fin_semi_axes)
    assert cfg.rho_silicone == m.rho_tail


# ----------------------------------------------------------------------------- SOFA scene

@pytest.fixture(scope="session")
def dyn_log(cfg, mesh_root):
    from fishsofa import headless
    return headless.run(cfg, LEVEL, n_steps=100, mesh_root=mesh_root)


def test_scene_runs_100_steps_without_nan(dyn_log, cfg):
    assert not dyn_log.has_nan
    assert len(dyn_log.t) == 100
    assert max(dyn_log.max_disp) < cfg.tail_length


def test_tail_sags_down_under_weight(dyn_log):
    dz = np.array([p[2] for p in dyn_log.tip])
    assert dz.min() < -1e-3                    # drops at least 1 mm
    assert abs(dyn_log.tip[-1][1]) < 1e-6      # symmetry: no sideways motion


def test_static_sag_is_equilibrium(cfg, mesh_root):
    # A second StaticSolver step must change nothing (the first one hit the equilibrium).
    from fishsofa import headless
    st = headless.static_sag(cfg, LEVEL, mesh_root, n_steps=2)
    assert st.tip[-1][2] < 0
    assert np.allclose(st.tip[0], st.tip[1], atol=1e-6)


def test_warp_solver_matches_ldl(cfg, mesh_root):
    # Warp (rest factorization + rotations + PCG) must give the same trajectory as exact LDL.
    from fishsofa import headless
    a = headless.run(TailConfig(linear_solver="ldl"), LEVEL, n_steps=30, mesh_root=mesh_root)
    b = headless.run(TailConfig(linear_solver="warp"), LEVEL, n_steps=30, mesh_root=mesh_root)
    za = np.array([p[2] for p in a.tip]); zb = np.array([p[2] for p in b.tip])
    assert np.max(np.abs(za - zb)) < 1e-3 * np.max(np.abs(za))


# ----------------------------------------------------------------------------- stage 2: chamber

@pytest.fixture(scope="session")
def qs_curve(mesh_root):
    from fishsofa import headless
    cfg = TailConfig(include_weight=False)
    return headless.quasi_static_sweep(cfg, LEVEL, [4e-6, 8e-6, 12e-6], mesh_root=mesh_root)


@pytest.fixture(scope="session")
def qs_curve_R(mesh_root):
    from fishsofa import headless
    cfg = TailConfig(include_weight=False)
    return headless.quasi_static_sweep(cfg, LEVEL, [4e-6, 8e-6, 12e-6], side="R", mesh_root=mesh_root)


def test_chamber_R_mirrors_L(qs_curve, qs_curve_R):
    # Stage 3: mesh and fibers are mirror-symmetric about the XZ plane, so chamber R must give
    # the mirror image of chamber L: same pressure and bulging, angle with opposite sign.
    # Spec requires < 5%; measured ≤ 0.13% (the rest comes from when the hold stops, README).
    L, R = qs_curve, qs_curve_R
    assert np.all(np.array(R.tip_angle) > 0)
    assert np.array(R.tip_angle) == pytest.approx(-np.array(L.tip_angle), rel=0.01)
    assert np.array(R.p) == pytest.approx(np.array(L.p), rel=0.01)
    assert np.array(R.bulge) == pytest.approx(np.array(L.bulge), rel=0.01)


def test_chamber_sign_convention(qs_curve):
    # +ΔV in chamber L -> the cavity grows by the prescribed volume, pressure is positive.
    assert qs_curve.dV[-1] == pytest.approx(12e-6, rel=1e-3)
    assert all(p > 0 for p in qs_curve.p)
    # Outward bulging on the chamber side.
    assert qs_curve.bulge[-1] > 0


def test_pressure_increases_with_volume(qs_curve):
    assert np.all(np.diff(qs_curve.p) > 0)


def test_tip_bends_away_from_inflated_chamber(qs_curve):
    # Chamber L (+Y) lengthens the left side -> the tail bends toward −Y: θ_tip < 0, growing in magnitude.
    th = np.array(qs_curve.tip_angle)
    assert np.all(th < 0)
    assert np.all(np.diff(np.abs(th)) > 0)


def test_quasi_static_is_equilibrium(qs_curve):
    # Spec criterion: kinetic energy < 1% of pressure work at every point.
    assert max(qs_curve.ke_ratio) < 0.01


def test_pressure_units_independent_of_dt(mesh_root):
    # SOFA's pressure is p·dt (stage 0); after conversion in hydraulics.py the same state
    # with a different step must give the same pressure in Pa.
    from fishsofa import headless
    cfg = TailConfig(include_weight=False)
    a = headless.quasi_static_sweep(cfg, LEVEL, [8e-6], mesh_root=mesh_root, dt=0.05)
    b = headless.quasi_static_sweep(cfg, LEVEL, [8e-6], mesh_root=mesh_root, dt=0.025, ramp_steps=8)
    assert a.p[-1] == pytest.approx(b.p[-1], rel=0.01)


def test_cholmod_matches_ldl_with_chamber(mesh_root):
    # CHOLMOD is a different factorization of the same matrix – the result must match LDL,
    # also with a chamber (the constraint correction uses the solver's factorization).
    from fishsofa import headless
    a, b = (headless.quasi_static_sweep(TailConfig(include_weight=False, linear_solver=s), LEVEL,
                                        [8e-6], mesh_root=mesh_root) for s in ("ldl", "cholmod"))
    assert b.p[-1] == pytest.approx(a.p[-1], rel=1e-6)
    assert b.tip_angle[-1] == pytest.approx(a.tip_angle[-1], rel=1e-6)


def test_warp_is_replaced_by_ldl_with_chambers(cfg, mesh_root):
    # Warp with a chamber gives a wrong equilibrium (README) – the scene must force LDL.
    from fishsofa import headless
    from fishsofa.scene import build_tail
    Sofa = headless._sofa()
    root = Sofa.Core.Node("root")
    h = build_tail(root, TailConfig(linear_solver="warp"), LEVEL, mesh_root, chambers={"L": "volume"})
    assert h["tail"].getObject("linsolver").getClassName() == "SparseLDLSolver"


def test_hoop_fibers_work_in_tension_only(cfg, mesh_root):
    # In SOFA v26.06 elongationOnly is a list (one value per spring); a single True
    # was silently ignored and the fibers also worked in compression.
    from fishsofa import headless
    from fishsofa.scene import build_tail
    Sofa = headless._sofa()
    root = Sofa.Core.Node("root")
    h = build_tail(root, TailConfig(hoop_fibers=True), LEVEL, mesh_root)
    ff = h["tail"].getChild("hoopFibers").getObject("springs")
    flags = np.array(ff.elongationOnly.value).ravel()
    assert len(flags) == len(ff.springsIndices1.value) and flags.all()


# ----------------------------------------------------------------------------- stage 4: hydraulics

def _offline(cfg, dp=0.0, cycles=4):
    """Pump model without SOFA, at a constant pressure difference dp."""
    from fishsofa.hydraulics import TailHydraulics
    h, dt = TailHydraulics(cfg), 0.002
    T = cfg.prefill_time + cfg.ramp_time + cycles / cfg.tail_freq
    rows = [h.step(i * dt, dp, dt) for i in range(int(T / dt))]
    t = np.array([r.t for r in rows])
    steady = t > cfg.prefill_time + cfg.ramp_time + 1 / cfg.tail_freq
    return rows, steady


def test_pump_tracks_v_ref():
    # Without saturation V_p tracks V_ref (feed-forward with pump-lag compensation + P).
    cfg = TailConfig()
    rows, m = _offline(cfg)
    vp, vr, u = (np.array([getattr(r, k) for r in rows])[m] for k in ("V_p", "V_ref", "u"))
    assert np.abs(u).max() < 1
    assert np.abs(vp - vr).max() < 0.02 * cfg.tail_volume_amp


def test_pump_saturation_reduces_amplitude():
    # Pump too weak (Q_max from MuJoCo, 60 ml/s < 2π·f·A_V = 214 ml/s): |u| = 1, amplitude drops.
    cfg = TailConfig(Q_max=60e-6)
    rows, m = _offline(cfg)
    vp, u = (np.array([getattr(r, k) for r in rows])[m] for k in ("V_p", "u"))
    assert np.mean(np.abs(u) >= 1) > 0.5
    assert vp.max() < 0.5 * cfg.tail_volume_amp


def test_valve_opens_only_above_p_max_and_keeps_volume_sum():
    from fishsofa.hydraulics import ClosedLoopPump
    cfg = TailConfig()
    for dp, should_open in ((0.9 * cfg.p_max, False), (1.2 * cfg.p_max, True), (-1.2 * cfg.p_max, True)):
        p = ClosedLoopPump(cfg)
        p.step(0.0, dp, 0.002)
        assert p.valve_open == should_open
        # The valve relieves from higher to lower pressure: dp > 0 (L higher) -> V_p decreases.
        assert np.sign(-p.V_p) == (np.sign(dp) if should_open else 0)
    # Sum of prescribed volumes = 2·prefill at every step, also while the valve is open.
    rows, _ = _offline(cfg, dp=1.5 * cfg.p_max, cycles=1)
    assert any(r.valve_open for r in rows)
    assert all(abs(r.dV_L + r.dV_R - 2 * r.prefill) < 1e-15 for r in rows)


def test_prefill_assertion():
    with pytest.raises(ValueError, match="V_prefill"):
        TailConfig(V_prefill=15e-6)   # < A_V (17 ml) + margin


def test_hydraulics_signals_are_continuous():
    # No actuation jumps: prescribed volumes change smoothly (also at the
    # prefill -> rhythm boundary and at the end of the ramps).
    cfg = TailConfig()
    rows, _ = _offline(cfg, cycles=1)
    for k in ("dV_L", "dV_R"):
        v = np.array([getattr(r, k) for r in rows])
        assert np.abs(np.diff(v)).max() < 0.002 * cfg.Q_max * 1.5


@pytest.fixture(scope="session")
def flap_run(mesh_root):
    from fishsofa import headless
    # dt 5 ms (spec: dt ≤ 1/(50·f_max) ≈ 6 ms) to keep the test short; stage 4 runs at 2 ms.
    cfg = TailConfig(prefill_time=0.2, ramp_time=0.2, dt=0.005)
    return headless.run_flapping(cfg, LEVEL, 0.9, mesh_root=mesh_root), cfg


def test_flapping_keeps_total_volume(flap_run):
    # Closed circuit: measured ΔV_L + ΔV_R = 2·V_prefill after the prefill (cavityVolume
    # is read with a 1-step delay, hence the comparison after the prefill ramp ends).
    r, cfg = flap_run
    m = r.log["t"] > cfg.prefill_time + 2 * cfg.dt
    s = r.log["dV_L"][m] + r.log["dV_R"][m]
    assert np.abs(s - 2 * cfg.V_prefill).max() < 1e-3 * 2 * cfg.V_prefill


def test_flapping_sign_and_motion(flap_run):
    # +V_p (pumping into L) -> θ < 0, as in stage 2; the tail actually flaps both ways.
    r, cfg = flap_run
    L = r.log
    m = L["t"] > cfg.prefill_time + cfg.ramp_time
    vp, th = L["V_p"][m], L["theta"][m]
    # The angle lags V_p (tail inertia), so the correlation is not close to −1.
    assert np.corrcoef(vp, th)[0, 1] < -0.5
    assert th.min() < -np.radians(5) and th.max() > np.radians(5)
    assert np.all(np.isfinite(L["p_L"])) and not L["valve_open"].any()


# ----------------------------------------------------------------------------- stage 5: water

def test_drag_dissipates_on_every_triangle(mesh):
    # Drag always removes energy: F·v ≤ 0 on every triangle, for arbitrary velocities.
    from fishsofa import water
    rng = np.random.default_rng(0)
    v = rng.normal(size=mesh.points.shape)
    f, vt, _, _ = water.triangle_forces(mesh.points, v, mesh.tri_outer, 1000.0, 1.0, 0.01)
    assert np.all(np.einsum("ij,ij->i", f, vt) <= 1e-15)
    assert water.drag(mesh.points, v, mesh.tri_outer, 1000.0, 1.0, 0.01).power < 0


def test_drag_zero_velocity_gives_zero_force(mesh):
    from fishsofa import water
    d = water.drag(mesh.points, np.zeros_like(mesh.points), mesh.tri_outer, 1000.0, 1.0, 0.01)
    assert np.all(d.node_forces == 0) and np.all(d.node_damping == 0)


def test_drag_on_flat_plate():
    # Thin 1 m² plate (two sides) moving perpendicular at 1 m/s: F = ½ρ·(2C_n)·A·v².
    from fishsofa import water
    x = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                  [0, 0, -1e-3], [1, 0, -1e-3], [1, 1, -1e-3], [0, 1, -1e-3]], float)
    top = [[0, 1, 2], [0, 2, 3]]                 # normal +z
    bottom = [[4, 6, 5], [4, 7, 6]]              # normal −z
    v = np.tile([0.0, 0.0, 1.0], (8, 1))
    d = water.drag(x, v, np.array(top + bottom), 1000.0, 1.0, 0.0)
    np.testing.assert_allclose(d.total, [0, 0, -1000.0], atol=1e-9)


@pytest.fixture(scope="session")
def water_run(mesh_root):
    from fishsofa import headless
    # Same rhythm as flap_run, but in water. dt 1 ms: drag is explicit, and at 5 ms
    # max(c·dt/m) would exceed 0.5 on the fin (stage 5, README).
    cfg = TailConfig(environment="water", prefill_time=0.2, ramp_time=0.2, dt=0.001)
    return headless.run_flapping(cfg, LEVEL, 0.9, mesh_root=mesh_root), cfg


def test_water_reduces_amplitude(flap_run, water_run):
    # Same volume command: in water the tail deflects less (drag). The air reference
    # uses dt 5 ms, i.e. more numerical damping – the test is conservative.
    (ra, ca), (rw, cw) = flap_run, water_run
    amp = lambda r, c: np.abs(r.log["theta"][r.log["t"] > c.prefill_time + c.ramp_time]).max()
    assert amp(rw, cw) < 0.9 * amp(ra, ca)


def test_water_drag_explicit_step_is_stable(water_run):
    r, _ = water_run
    assert np.all(np.isfinite(r.log["theta"]))
    assert r.log["stability"].max() < 0.5
    assert np.all(r.log["drag_power"] <= 0)


# ----------------------------------------------------------------------------- stage 6: Young's modulus

def _qs_point(mesh_root, k, target, mode):
    """One quasi-static point (chamber L, g = 0) with E and fiber stiffness scaled ×k.
    Both are scaled so that the whole structure is "one material" times k."""
    from fishsofa import headless
    base = TailConfig(include_weight=False)
    cfg = TailConfig(include_weight=False, young_modulus=k * base.young_modulus,
                     hoop_stiffness=k * base.hoop_stiffness)
    c = headless.quasi_static_sweep(cfg, LEVEL, [target], mesh_root=mesh_root, mode=mode)
    return c.p[-1], c.tip_angle[-1]


def test_young_x2_same_volume_doubles_pressure_keeps_angle(mesh_root):
    # Volume control: the equilibrium at a prescribed ΔV does not depend on the stiffness
    # scale; only the required pressure changes (∝ E).
    p1, th1 = _qs_point(mesh_root, 1.0, 10e-6, "volume")
    p2, th2 = _qs_point(mesh_root, 2.0, 10e-6, "volume")
    assert abs(p2 / p1 - 2.0) < 0.2
    assert abs(th2 / th1 - 1.0) < 0.05


def test_young_x2_same_pressure_halves_angle(mesh_root):
    # Pressure control (value = p·dt): same p -> deflection ~1/E.
    _, th1 = _qs_point(mesh_root, 1.0, 4e3, "pressure")
    _, th2 = _qs_point(mesh_root, 2.0, 4e3, "pressure")
    assert abs(th2 / th1 - 0.5) < 0.5 * 0.15
