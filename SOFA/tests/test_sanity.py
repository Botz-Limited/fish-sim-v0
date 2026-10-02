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
