"""Testy sanity (headless). Uruchomienie:  source scripts/env.sh && pytest -q

Używają grubej siatki "test" generowanej raz do katalogu tymczasowego (nie dotykają meshes/).
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


# ----------------------------------------------------------------------------- siatka

def test_no_degenerate_tets(mesh):
    assert (mesh_gen.tet_volumes(mesh.points, mesh.tets) > 0).all()


def test_surfaces_closed_and_outward(report):
    # Zamknięte powierzchnie + dodatnia objętość ze znakiem = spójne normalne.
    assert report["open_edges"] == [0, 0, 0]
    # Zewnętrzna powierzchnia zamyka silikon RAZEM z wnękami.
    v_in = report["volume_solid_m3"] + report["volume_chamber_L_m3"] + report["volume_chamber_R_m3"]
    assert report["volume_outer_m3"] == pytest.approx(v_in, rel=1e-9)


def test_chambers_closed_positive_and_equal(mesh, report):
    v_L, v_R = report["volume_chamber_L_m3"], report["volume_chamber_R_m3"]
    # Konwencja SoftRobots (etap 0): normalne na zewnątrz wnęki -> objętość ze znakiem > 0.
    assert v_L > 0 and v_R > 0
    assert v_L == pytest.approx(v_R, rel=1e-12)
    # Objętość wnęki z geometrii: przekrój eliptyczny (półosie minus ścianka) przycięty
    # przez przegrodę – liczymy numerycznie, niezależnie od siatki. Siatka (płaskie
    # trójkąty na zakrzywionej powierzchni) daje trochę mniej.
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
    # Scena czyta tail.vtk, a pomiary używają tail_meta.npz – muszą mieć te same węzły.
    path = os.path.join(mesh_gen.mesh_dir(cfg, LEVEL, mesh_root), "tail.vtk")
    with open(path) as f:
        lines = f.read().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("POINTS"))
    n = int(lines[i].split()[1])
    pts = np.loadtxt(lines[i + 1:i + 1 + n])
    assert np.allclose(pts, mesh.points, atol=1e-8)


# ----------------------------------------------------------------------------- masa i ciężar

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
    # Bezwładność wody w komorach zostaje.
    assert mm.mass_water > 0
    assert mm.node_mass.sum() == pytest.approx(m_sil + mm.mass_water, rel=1e-9)


# ----------------------------------------------------------------------------- geometria pomiarów

def test_tip_angle_zero_for_straight_tail(mesh):
    base = geometry.base_center(mesh.points, mesh.base_nodes)
    assert geometry.tip_angle(mesh.points, base, mesh.fin_nodes) == pytest.approx(0.0, abs=1e-9)


def test_tip_angle_sign(mesh):
    base = geometry.base_center(mesh.points, mesh.base_nodes)
    x = mesh.points.copy()
    x[mesh.fin_nodes, 1] += 0.01   # przesunięcie płetwy w +Y
    assert geometry.tip_angle(x, base, mesh.fin_nodes) > 0


# ----------------------------------------------------------------------------- zgodność z MuJoCo

def test_dimensions_match_mujoco(cfg):
    path = os.path.join(PROJECT_DIR, "..", "MuJoCo", "fishsim", "config.py")
    if not os.path.exists(path):
        pytest.skip("brak MuJoCo/fishsim/config.py")
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


# ----------------------------------------------------------------------------- scena SOFA

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
    assert dz.min() < -1e-3                    # opada co najmniej 1 mm
    assert abs(dyn_log.tip[-1][1]) < 1e-6      # symetria: brak ruchu w bok


def test_static_sag_is_equilibrium(cfg, mesh_root):
    # Drugi krok StaticSolver nie może już nic zmienić (pierwszy trafił w równowagę).
    from fishsofa import headless
    st = headless.static_sag(cfg, LEVEL, mesh_root, n_steps=2)
    assert st.tip[-1][2] < 0
    assert np.allclose(st.tip[0], st.tip[1], atol=1e-6)


def test_warp_solver_matches_ldl(cfg, mesh_root):
    # Warp (rozkład w spoczynku + obroty + PCG) ma dawać tę samą trajektorię co dokładny LDL.
    from fishsofa import headless
    a = headless.run(TailConfig(linear_solver="ldl"), LEVEL, n_steps=30, mesh_root=mesh_root)
    b = headless.run(TailConfig(linear_solver="warp"), LEVEL, n_steps=30, mesh_root=mesh_root)
    za = np.array([p[2] for p in a.tip]); zb = np.array([p[2] for p in b.tip])
    assert np.max(np.abs(za - zb)) < 1e-3 * np.max(np.abs(za))


# ----------------------------------------------------------------------------- etap 2: komora

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
    # Etap 3: siatka i włókna są lustrzane względem płaszczyzny XZ, więc komora R ma dać
    # odbicie wyniku komory L: to samo ciśnienie i wydymanie, kąt z przeciwnym znakiem.
    # Spec wymaga < 5%; zmierzone ≤ 0.13% (reszta to moment zatrzymania trzymania, README).
    L, R = qs_curve, qs_curve_R
    assert np.all(np.array(R.tip_angle) > 0)
    assert np.array(R.tip_angle) == pytest.approx(-np.array(L.tip_angle), rel=0.01)
    assert np.array(R.p) == pytest.approx(np.array(L.p), rel=0.01)
    assert np.array(R.bulge) == pytest.approx(np.array(L.bulge), rel=0.01)


def test_chamber_sign_convention(qs_curve):
    # +ΔV w komorze L -> wnęka rośnie o zadaną objętość, ciśnienie dodatnie.
    assert qs_curve.dV[-1] == pytest.approx(12e-6, rel=1e-3)
    assert all(p > 0 for p in qs_curve.p)
    # Wydymanie na zewnątrz po stronie komory.
    assert qs_curve.bulge[-1] > 0


def test_pressure_increases_with_volume(qs_curve):
    assert np.all(np.diff(qs_curve.p) > 0)


def test_tip_bends_away_from_inflated_chamber(qs_curve):
    # Komora L (+Y) wydłuża lewy bok -> ogon zgina się w −Y: θ_tip < 0 i rośnie co do modułu.
    th = np.array(qs_curve.tip_angle)
    assert np.all(th < 0)
    assert np.all(np.diff(np.abs(th)) > 0)


def test_quasi_static_is_equilibrium(qs_curve):
    # Kryterium specu: energia kinetyczna < 1% pracy ciśnienia w każdym punkcie.
    assert max(qs_curve.ke_ratio) < 0.01


def test_pressure_units_independent_of_dt(mesh_root):
    # pressure z SOFA to p·dt (etap 0); po przeliczeniu w hydraulics.py ten sam stan
    # przy innym kroku musi dać to samo ciśnienie w Pa.
    from fishsofa import headless
    cfg = TailConfig(include_weight=False)
    a = headless.quasi_static_sweep(cfg, LEVEL, [8e-6], mesh_root=mesh_root, dt=0.05)
    b = headless.quasi_static_sweep(cfg, LEVEL, [8e-6], mesh_root=mesh_root, dt=0.025, ramp_steps=8)
    assert a.p[-1] == pytest.approx(b.p[-1], rel=0.01)


def test_cholmod_matches_ldl_with_chamber(mesh_root):
    # CHOLMOD to inny rozkład tej samej macierzy – wynik musi być ten sam co z LDL,
    # także z komorą (korekcja ograniczeń korzysta z rozkładu solvera).
    from fishsofa import headless
    a, b = (headless.quasi_static_sweep(TailConfig(include_weight=False, linear_solver=s), LEVEL,
                                        [8e-6], mesh_root=mesh_root) for s in ("ldl", "cholmod"))
    assert b.p[-1] == pytest.approx(a.p[-1], rel=1e-6)
    assert b.tip_angle[-1] == pytest.approx(a.tip_angle[-1], rel=1e-6)


def test_warp_is_replaced_by_ldl_with_chambers(cfg, mesh_root):
    # Warp z komorą daje błędną równowagę (README) – scena musi wymusić LDL.
    from fishsofa import headless
    from fishsofa.scene import build_tail
    Sofa = headless._sofa()
    root = Sofa.Core.Node("root")
    h = build_tail(root, TailConfig(linear_solver="warp"), LEVEL, mesh_root, chambers={"L": "volume"})
    assert h["tail"].getObject("linsolver").getClassName() == "SparseLDLSolver"


def test_hoop_fibers_work_in_tension_only(cfg, mesh_root):
    # elongationOnly to w SOFA v26.06 lista (jedna wartość na sprężynę); pojedyncze True
    # było po cichu ignorowane i włókna pracowały też na ściskanie.
    from fishsofa import headless
    from fishsofa.scene import build_tail
    Sofa = headless._sofa()
    root = Sofa.Core.Node("root")
    h = build_tail(root, TailConfig(hoop_fibers=True), LEVEL, mesh_root)
    ff = h["tail"].getChild("hoopFibers").getObject("springs")
    flags = np.array(ff.elongationOnly.value).ravel()
    assert len(flags) == len(ff.springsIndices1.value) and flags.all()


# ----------------------------------------------------------------------------- etap 4: hydraulika

def _offline(cfg, dp=0.0, cycles=4):
    """Model pompy bez SOFA, przy stałej różnicy ciśnień dp."""
    from fishsofa.hydraulics import TailHydraulics
    h, dt = TailHydraulics(cfg), 0.002
    T = cfg.prefill_time + cfg.ramp_time + cycles / cfg.tail_freq
    rows = [h.step(i * dt, dp, dt) for i in range(int(T / dt))]
    t = np.array([r.t for r in rows])
    steady = t > cfg.prefill_time + cfg.ramp_time + 1 / cfg.tail_freq
    return rows, steady


def test_pump_tracks_v_ref():
    # Bez nasycenia V_p śledzi V_ref (feed-forward z kompensacją opóźnienia pompy + P).
    cfg = TailConfig()
    rows, m = _offline(cfg)
    vp, vr, u = (np.array([getattr(r, k) for r in rows])[m] for k in ("V_p", "V_ref", "u"))
    assert np.abs(u).max() < 1
    assert np.abs(vp - vr).max() < 0.02 * cfg.tail_volume_amp


def test_pump_saturation_reduces_amplitude():
    # Za słaba pompa (Q_max z MuJoCo, 60 ml/s < 2π·f·A_V = 214 ml/s): |u| = 1, amplituda spada.
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
        # Zawór przelewa z wyższego ciśnienia do niższego: dp > 0 (L wyżej) -> V_p maleje.
        assert np.sign(-p.V_p) == (np.sign(dp) if should_open else 0)
    # Suma zadanych objętości = 2·prefill w każdym kroku, także przy pracującym zaworze.
    rows, _ = _offline(cfg, dp=1.5 * cfg.p_max, cycles=1)
    assert any(r.valve_open for r in rows)
    assert all(abs(r.dV_L + r.dV_R - 2 * r.prefill) < 1e-15 for r in rows)


def test_prefill_assertion():
    with pytest.raises(ValueError, match="V_prefill"):
        TailConfig(V_prefill=15e-6)   # < A_V (17 ml) + margines


def test_hydraulics_signals_are_continuous():
    # Żadnych skoków aktuacji: zadane objętości zmieniają się płynnie (także na granicy
    # prefill -> rytm i na końcu ramp).
    cfg = TailConfig()
    rows, _ = _offline(cfg, cycles=1)
    for k in ("dV_L", "dV_R"):
        v = np.array([getattr(r, k) for r in rows])
        assert np.abs(np.diff(v)).max() < 0.002 * cfg.Q_max * 1.5


@pytest.fixture(scope="session")
def flap_run(mesh_root):
    from fishsofa import headless
    # dt 5 ms (spec: dt ≤ 1/(50·f_max) ≈ 6 ms), żeby test był krótki; etap 4 liczy przy 2 ms.
    cfg = TailConfig(prefill_time=0.2, ramp_time=0.2, dt=0.005)
    return headless.run_flapping(cfg, LEVEL, 0.9, mesh_root=mesh_root), cfg


def test_flapping_keeps_total_volume(flap_run):
    # Układ zamknięty: zmierzone ΔV_L + ΔV_R = 2·V_prefill po prefillu (cavityVolume
    # odczytywane z opóźnieniem 1 kroku, stąd porównanie po zakończeniu rampy prefillu).
    r, cfg = flap_run
    m = r.log["t"] > cfg.prefill_time + 2 * cfg.dt
    s = r.log["dV_L"][m] + r.log["dV_R"][m]
    assert np.abs(s - 2 * cfg.V_prefill).max() < 1e-3 * 2 * cfg.V_prefill


def test_flapping_sign_and_motion(flap_run):
    # +V_p (wtłoczenie do L) -> θ < 0, jak w etapie 2; ogon faktycznie macha w obie strony.
    r, cfg = flap_run
    L = r.log
    m = L["t"] > cfg.prefill_time + cfg.ramp_time
    vp, th = L["V_p"][m], L["theta"][m]
    # Kąt opóźnia się za V_p (bezwładność ogona), więc korelacja nie jest bliska −1.
    assert np.corrcoef(vp, th)[0, 1] < -0.5
    assert th.min() < -np.radians(5) and th.max() > np.radians(5)
    assert np.all(np.isfinite(L["p_L"])) and not L["valve_open"].any()
