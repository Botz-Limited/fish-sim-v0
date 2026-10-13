"""Testy sanity (SPEC §9). Kolejne etapy dopisują tu swoje testy."""

import mujoco
import numpy as np
import pytest

from fishsim.buoyancy import (body_volumes, center_of_buoyancy, ellipsoid_volume,
                              fish_body_ids, net_buoyancy)
from fishsim.config import FishConfig
from fishsim.hydraulics import euler_stability_margin
from fishsim.model_builder import build_model, tail_geoms
from fishsim.readouts import FluidForces, drive_rows, force_rows


@pytest.fixture(scope="module")
def fish():
    cfg = FishConfig()
    model, info = build_model(cfg)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    return cfg, model, data, info


# ---------------------------------------------------------------- etap 1: model statyczny

def test_model_loads_with_n_tail_joints(fish):
    cfg, model, _, _ = fish
    hinges = [j for j in range(model.njnt) if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE]
    assert len(hinges) == cfg.n_segments


def test_tendon_spans_k_actuated_joints(fish):
    cfg, model, _, _ = fish
    assert model.ntendon == 1 and model.nu == 1
    assert model.tendon_num[0] == cfg.n_actuated
    assert model.actuator_trntype[0] == mujoco.mjtTrn.mjTRN_TENDON


def test_every_fish_geom_uses_ellipsoid_fluid_model(fish):
    # SPEC §1: jeden geom bez fluidshape w ciele = zero sił płynu na tym geomie.
    # geom_fluid[:, 0] to współczynnik interakcji: 1 dla fluidshape="ellipsoid".
    _, model, _, _ = fish
    fish_bodies = set(fish_body_ids(model))
    for g in range(model.ngeom):
        if model.geom_bodyid[g] in fish_bodies:
            assert model.geom_fluid[g, 0] == 1.0, model.geom(g).name


def test_masses_match_analytic_values(fish):
    # MuJoCo liczy masę z gęstości·objętości geomu – sprawdzamy, że to ta sama
    # objętość, której używamy do wyporu (inaczej bilans sił się rozjedzie).
    cfg, model, _, info = fish
    m_seg = {i: 0.0 for i in range(cfg.n_segments)}
    for g in tail_geoms(cfg):
        m_seg[g.body] += g.mass
    for i, m in m_seg.items():
        assert model.body(f"seg{i}").mass[0] == pytest.approx(m, rel=1e-6)
    assert model.body("hull").mass[0] == pytest.approx(info.m_hull, rel=1e-6)
    vol = body_volumes(model)
    assert vol[model.body("hull").id] == pytest.approx(ellipsoid_volume(cfg.hull_semi_axes))


def test_neutral_buoyancy_in_middle_of_bladder_range(fish):
    cfg, model, _, _ = fish
    weight = model.body_mass[fish_body_ids(model)].sum() * cfg.gravity
    assert abs(net_buoyancy(model, cfg, cfg.bladder_v_neutral)) < 1e-9 * weight
    assert net_buoyancy(model, cfg, cfg.bladder_v_min) < 0   # pęcherz pusty -> tonie
    assert net_buoyancy(model, cfg, cfg.bladder_v_max) > 0   # pęcherz pełny -> wypływa


def test_longitudinal_trim_and_cb_above_cg(fish):
    cfg, model, data, info = fish
    hull = model.body("hull").id
    cg = data.subtree_com[hull]
    cb = center_of_buoyancy(model, data, cfg, cfg.bladder_v_neutral, info.x_cb)
    assert abs(cb[0] - cg[0]) < 1e-3   # trym wzdłużny: < 1 mm
    assert cb[2] - cg[2] > 0            # CB nad CG -> moment prostujący


def test_hydraulic_spring_step_is_stable(fish):
    cfg, model, data, _ = fish
    assert euler_stability_margin(model, data, cfg) < 0.5


def test_no_self_collisions_at_start(fish):
    _, _, data, _ = fish
    assert data.ncon == 0


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        FishConfig(n_actuated=6)
    with pytest.raises(ValueError):
        FishConfig(bladder_v_min=1e-5, bladder_v_max=1e-5)


def test_trim_holds_for_other_tail_material():
    # Trym liczony z równań, nie strojony: musi działać też dla innego materiału
    # i innej liczby segmentów.
    cfg = FishConfig(rho_tail=1200.0, rho_fin=1050.0, n_segments=4, n_actuated=2)
    model, info = build_model(cfg)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    cg = data.subtree_com[model.body("hull").id]
    cb = center_of_buoyancy(model, data, cfg, cfg.bladder_v_neutral, info.x_cb)
    assert abs(cb[0] - cg[0]) < 1e-3
    assert abs(net_buoyancy(model, cfg, cfg.bladder_v_neutral)) < 1e-9


# ---------------------------------------------------------------- etap 2: wypór i stabilność

from fishsim.buoyancy import Buoyancy  # noqa: E402
from fishsim.sim import FishSim  # noqa: E402


def test_righting_moment_opposes_roll(fish):
    # Luka v1 nr 4: CB musi być stały w UKŁADZIE KADŁUBA. Przechylamy rybę o +10°
    # wokół osi X i sprawdzamy, że moment wyporu na kadłub ma znak przeciwny (prostuje).
    sim = FishSim()
    sim.set_pose(roll_deg=10.0)
    sim.buoyancy.apply(sim.data, sim.bladder.volume)
    assert sim.data.xfrc_applied[sim.hull, 3] < 0


def test_suspension_neutral_bladder_holds_depth():
    # Bilans sił i momentów jest spełniony analitycznie (etap 1), więc dryf może pochodzić
    # tylko z błędu numerycznego. Próg 5 mm zamiast 5 cm z SPEC: niezrównoważenie rzędu
    # 0.1% zakresu pęcherza (~0.0002 N) dawałoby już ~1.5 mm w 5 s, a 5 cm ukryłoby
    # błąd znaku w trymie.
    sim = FishSim()
    log = sim.run(5.0)
    assert abs(log["com"][-1, 2] - log["com"][0, 2]) < 5e-3
    assert np.degrees(np.abs(log["pitch"]).max()) < 5.0


def test_righting_from_30_deg_roll():
    # Obwiednia (max w oknie 4–5 s), a nie wartość chwilowa: słabo tłumione
    # kołysanie mogłoby akurat przechodzić przez zero w t = 5 s.
    sim = FishSim()
    sim.set_pose(roll_deg=30.0)
    log = sim.run(5.0)
    window = (log["t"] >= 4.0) & (log["t"] <= 5.0)
    assert np.degrees(log["tilt"][window].max()) < 15.0


@pytest.mark.parametrize("which, sign", [("max", +1), ("min", -1)])
def test_bladder_extremes_rise_and_sink(which, sign):
    cfg = FishConfig()
    v = cfg.bladder_v_max if which == "max" else cfg.bladder_v_min
    sim = FishSim(cfg, v_bladder=v)
    sim.v_bladder_ref = v
    sim.set_pose(z=-1.5)
    log = sim.run(2.0)
    dz = log["com"][-1, 2] - log["com"][0, 2]
    assert sign * dz > 0.02          # wyraźny ruch we właściwą stronę (> 2 cm)
    assert log["com"][:, 2].max() < -0.5   # ...ale bez dotarcia do powierzchni


def test_full_bladder_does_not_fly_out_of_water():
    # Wygaszanie wyporu przy powierzchni (łatka z SPEC §5): ryba z pełnym pęcherzem
    # ma się zatrzymać tuż pod/przy powierzchni, a nie lecieć w górę bez końca.
    cfg = FishConfig()
    sim = FishSim(cfg, v_bladder=cfg.bladder_v_max)
    sim.v_bladder_ref = cfg.bladder_v_max
    sim.set_pose(z=-0.3)
    log = sim.run(15.0)
    assert log["com"][:, 2].max() < cfg.hull_semi_axes[2]
    assert sim.state_ok()


# ---------------------------------------------------------------- etap 3: hydraulika offline

from fishsim.controllers import TailRhythm  # noqa: E402
from fishsim.hydraulics import LumpedTail, TailHydraulics, simulate_offline  # noqa: E402


@pytest.fixture(scope="module")
def offline_low():
    cfg = FishConfig(tail_freq=1.5)
    return cfg, simulate_offline(cfg, TailRhythm(cfg), 10.0)


def test_hydraulics_total_volume_conserved(offline_low):
    cfg, log = offline_low
    total = log["V_L"] + log["V_R"]
    assert np.abs(total - 2 * cfg.V0_chamber).max() < 1e-15


def test_pressure_difference_changes_sign_every_cycle(offline_low):
    # Luka v1 nr 1: max(0, ·) dawało Δp ≥ 0 przez cały czas (ogon w jedną stronę).
    cfg, log = offline_low
    t, dp, T = log["t"], log["dp"], 1.0 / cfg.tail_freq
    for k in range(2, 12):   # pełne cykle po rampie
        cycle = (t >= k * T) & (t < (k + 1) * T)
        assert dp[cycle].max() > 0 and dp[cycle].min() < 0, f"cykl {k}"


def test_relief_valve_limits_pressure_on_blocked_tail():
    # Ogon zablokowany (ogromna bezwładność), pompa na 100%: bez zaworu Δp rosłoby
    # bez końca. Zawór ma utrzymać |Δp| ≤ p_max, a nadmiar przepuścić między komorami.
    cfg = FishConfig()
    hyd = TailHydraulics(cfg)
    dps, vents = [], []
    for _ in range(int(1.0 / cfg.timestep)):
        hyd.step(1.0, 0.0, cfg.timestep)
        dps.append(hyd.delta_p(0.0))
        vents.append(hyd.Q_valve)
    assert max(abs(p) for p in dps) <= cfg.p_max * (1 + 1e-12)
    assert dps[-1] == pytest.approx(cfg.p_max)
    assert max(vents) > 0        # zawór faktycznie pracuje (przepuszcza ciecz z L do R)
    assert hyd.V_L + hyd.V_R == pytest.approx(2 * cfg.V0_chamber, abs=1e-15)


def test_offline_pressure_within_limit(offline_low):
    cfg, log = offline_low
    assert np.abs(log["dp"]).max() <= cfg.p_max


def test_volume_bias_gives_offset_without_drift():
    # Luka v1 nr 2: bias w komendzie przepływu całkował się bez końca.
    # Teraz V_bias to zadane przesunięcie objętości: średnia stała w czasie.
    cfg = FishConfig(tail_volume_bias=3e-6)
    log = simulate_offline(cfg, TailRhythm(cfg), 20.0)
    t, vp = log["t"], log["V_p"]
    early = vp[(t >= 5) & (t < 10)].mean()
    late = vp[(t >= 15) & (t < 20)].mean()
    # ±0.1 ml: przy 2 przełączeniach na cykl średnia zależy też od tego, gdzie wypadają szczyty
    assert early == pytest.approx(3e-6, abs=1e-7)
    # dryf < 0.1 ml na 10 s; resztę różnicy daje piła przekaźnika, nie całkowanie biasu
    assert late == pytest.approx(early, abs=1e-7)


def _switches_per_cycle(log, f, t_from=6.0):
    u = log["u"][log["t"] > t_from]
    return np.count_nonzero(np.diff(u)) / ((log["t"][-1] - t_from) * f)


def test_valve_state_is_only_plus_minus_one(offline_low):
    # Zawory nie mają stanu zamkniętego: pompa zawsze tłoczy w którąś stronę.
    _, log = offline_low
    assert set(np.unique(log["u"])) == {-1, 1}


def test_valve_holds_each_state_for_min_dwell():
    # Zawór przełącza się najwyżej ~5 razy/s: między przełączeniami ≥ valve_min_dwell.
    cfg = FishConfig()
    for f in (cfg.tail_freq_min, 2.0, cfg.tail_freq_max):
        log = simulate_offline(cfg, TailRhythm(cfg, freq=f), 10.0)
        t_sw = log["t"][1:][np.diff(log["u"]) != 0]
        assert np.diff(t_sw).min() >= cfg.valve_min_dwell - 1e-9, f


def test_frequency_clamped_to_valve_range():
    cfg = FishConfig()
    assert TailRhythm(cfg, freq=0.5).freq == cfg.tail_freq_min
    assert TailRhythm(cfg, freq=3.0).freq == cfg.tail_freq_max
    r = TailRhythm(cfg)
    r.set_freq(10.0, 3.7)
    assert r.freq == cfg.tail_freq_max
    assert cfg.tail_freq_max <= 1 / (2 * cfg.valve_min_dwell)   # 2 przełączenia na cykl


def test_amplitude_drops_when_valves_switch_only_at_peaks():
    # Lekcja fizyczna: przy stałym Q_const amplituda spada z częstotliwością.
    # Powyżej f = Q_const/(2π·A_V) zawór przełącza się tylko w szczytach (2 razy na cykl),
    # objętość to trójkąt o amplitudzie ≤ Q_const/(4f) (mniej o czas przełączania τ_valve).
    cfg = FishConfig()

    def run(f):
        log = simulate_offline(cfg, TailRhythm(cfg, freq=f), 10.0)
        vp = log["V_p"][log["t"] > 6.0]
        return (vp.max() - vp.min()) / 2, _switches_per_cycle(log, f)

    (v_low, _), (v_mid, sw_mid), (v_high, sw_high) = run(1.5), run(2.0), run(2.5)
    assert v_low > v_mid > v_high
    assert sw_mid == pytest.approx(2, abs=0.1) and sw_high == pytest.approx(2, abs=0.1)
    for f, v in ((2.0, v_mid), (2.5, v_high)):
        assert 0.7 * cfg.Q_const / (4 * f) < v <= cfg.Q_const / (4 * f)


def test_lumped_tail_is_stable_with_hydraulic_spring():
    tail = LumpedTail()
    cfg = FishConfig()
    log = simulate_offline(cfg, TailRhythm(cfg), 20.0, tail=tail)
    assert np.all(np.isfinite(log["L"])) and np.abs(log["L"]).max() < 1.0


# ---------------------------------------------------------------- etap 4: pływanie

from fishsim.sim import forward_speed  # noqa: E402


@pytest.fixture(scope="module")
def swim_logs():
    out = {}
    for fluid in (True, False):
        cfg = FishConfig()
        sim = FishSim(cfg, fluid=fluid, rhythm=TailRhythm(cfg))
        out[fluid] = (cfg, sim, sim.run(20.0))
    return out


def test_swims_forward_with_fluid(swim_logs):
    # Próg 5 cm/s: ~4× poniżej obecnych ~22 cm/s, ale powyżej tego, co dawał model
    # z niepełną masą dołączoną (~4 cm/s) – test złapie powrót tamtego artefaktu
    # albo odwrócenie fali na ogonie (ryba płynąca do tyłu).
    cfg, _, log = swim_logs[True]
    assert forward_speed(log, cfg.tail_freq) > 0.05


def test_no_fluid_center_of_mass_stays(swim_logs):
    # Bez sił zewnętrznych w poziomie (wypór i ciężar są pionowe) pęd całej ryby się
    # nie zmienia: machanie ogonem przesuwa tylko części względem siebie.
    cfg, _, log = swim_logs[False]
    assert abs(forward_speed(log, cfg.tail_freq)) < 1e-3


def test_no_nan_after_20s_swimming(swim_logs):
    for _, sim, log in swim_logs.values():
        assert sim.state_ok()
        assert np.all(np.isfinite(log["dp"]))


def test_swimming_pressure_and_joint_limits(swim_logs):
    cfg, _, log = swim_logs[True]
    # Zawór przelewowy pracuje tylko przy starcie: pierwszy skok zaworu trwa ≥ valve_min_dwell,
    # a V_ref w rampie jest jeszcze małe. Log Δp jest liczony po ruchu ogona w mj_step,
    # przed kolejnym upustem – stąd 1%. W ustalonym pływaniu zawór przelewowy milczy.
    dp, t = np.abs(log["dp"]), log["t"]
    assert dp.max() <= cfg.p_max * 1.01
    assert dp[t > 3.0].max() < cfg.p_max
    assert np.degrees(np.abs(log["theta"])).max() <= cfg.joint_range_deg + 1.0


def test_added_mass_moved_from_fluid_model_to_armature():
    # Tryb "armature": MuJoCo nie może już liczyć niepełnego członu −ω×(m_A·v)
    # (zerowe m_A, I_A w geom_fluid), a bezwładność wody siedzi w armature.
    model, info = build_model(FishConfig())
    assert np.all(model.geom_fluid[:, 6:12] == 0.0)
    assert np.all(model.dof_armature[model.jnt_dofadr[model.joint("tail0").id]:] > 0)
    model_mj, _ = build_model(FishConfig(added_mass="mujoco"))
    assert model_mj.geom_fluid[model_mj.geom("fin").id, 7] > 0
    assert np.all(model_mj.dof_armature == 0.0)


def test_passive_joints_resonate_at_configured_frequency():
    # Sztywność pasywna wyliczona z f_res: sprawdzamy odwrotnie, ω = sqrt(k/M_jj).
    cfg = FishConfig(passive_resonance_hz=2.5)
    model, _ = build_model(cfg)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    M = np.zeros((model.nv, model.nv))
    mujoco.mj_fullM(model, data, M)
    for i in range(cfg.n_actuated, cfg.n_segments):
        j = model.joint(f"tail{i}").id
        dof = model.jnt_dofadr[j]
        f = np.sqrt(model.jnt_stiffness[j] / M[dof, dof]) / (2 * np.pi)
        assert f == pytest.approx(2.5, rel=1e-9)


# ---------------------------------------------------------------- etap 5: skręt i głębokość

from fishsim.controllers import DepthController  # noqa: E402


def _yaw_rate(log, t_from=10.0):
    yaw = np.unwrap(np.arctan2(log["heading"][:, 1], log["heading"][:, 0]))
    late = log["t"] > t_from
    return np.degrees(np.polyfit(log["t"][late], yaw[late], 1)[0])


@pytest.mark.parametrize("bias_ml, expect", [(3.0, -1), (-3.0, +1), (0.0, 0)])
def test_volume_bias_turns_fish(bias_ml, expect):
    # V_bias > 0 -> ogon ugięty w prawo (θ > 0 obraca ogon leżący w −X w stronę −Y)
    # -> skręt w prawo, czyli ujemna prędkość kątowa wokół +Z.
    cfg = FishConfig(tail_volume_bias=bias_ml * 1e-6)
    log = FishSim(cfg, rhythm=TailRhythm(cfg)).run(20.0, log_every=10)
    rate = _yaw_rate(log)
    if expect == 0:
        assert abs(rate) < 0.3
    else:
        assert expect * rate > 2.0


def test_depth_step_hover_settles_without_big_overshoot():
    cfg = FishConfig()
    sim = FishSim(cfg, depth=DepthController(cfg, -1.5))
    sim.set_pose(z=-1.0)
    log = sim.run(40.0, log_every=10)
    z, t = log["com"][:, 2], log["t"]
    assert -1.5 - z.min() < 0.05                        # przeregulowanie < 5 cm
    assert np.abs(z[t > 30] + 1.5).max() < 0.02         # po 30 s w paśmie ±2 cm


def test_depth_reference_clamped_below_surface():
    cfg = FishConfig()
    ctrl = DepthController(cfg, -1.0)
    ctrl.set_reference(0.5)
    assert ctrl.z_ref == cfg.z_ref_max


def test_depth_anti_windup_stops_integral_when_saturated():
    # Ryba "przyklejona" 2 m za głęboko: wyjście nasycone na V_max. Bez anti-windup całka
    # rosłaby bez końca i po odklejeniu dawała ogromne przeregulowanie.
    cfg = FishConfig()
    ctrl = DepthController(cfg, -1.0)
    for _ in range(int(60.0 / cfg.timestep)):
        v = ctrl.update(z=-3.0, v_z=0.0, dt=cfg.timestep)
    assert v == cfg.bladder_v_max
    assert ctrl.integral == 0.0      # całka zamrożona od pierwszego kroku (od razu nasycenie)


# ---------------------------------------------------------------- etap 6: sweep

def test_sweep_speed_peaks_inside_range_and_pump_limits_amplitude():
    # Lekcja z etapu 6: prędkość rośnie, dopóki pompa nadąża, potem spada, bo
    # przy stałym Q_const amplituda L (to, czym steruje pompa) maleje z częstotliwością.
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import sweep_frequency

    rows = {r["f"]: r for r in sweep_frequency.run_sweep([1.5, 1.75, 2.5], duration=16.0)}
    assert rows[1.75]["v"] > rows[2.5]["v"] and rows[1.5]["v"] > rows[2.5]["v"]
    assert rows[1.5]["amp_L"] > rows[1.75]["amp_L"] > rows[2.5]["amp_L"]
    assert all(r["switches"] <= 4 for r in rows.values())   # zawór ≤ 5/s: bez drgania


# ---------------------------------------------------------------- etap 7: viewer (logika bez okna)

def _viewer_module():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import run_viewer
    return run_viewer


def test_viewer_keys_change_controls_with_limits():
    rv = _viewer_module()
    cfg = FishConfig()
    c = rv.ViewerControls(cfg)
    for _ in range(20):
        c.on_key(rv.KEY_RIGHT)
        c.on_key(rv.KEY_PAGE_UP)
        c.on_key(rv.KEY_DOWN)
    assert c.bias == pytest.approx(c.BIAS_MAX)
    assert c.z_ref == cfg.z_ref_max            # nie wyżej niż −0.3 m
    assert c.freq == cfg.tail_freq_min
    c.on_key(999)                               # nieznany klawisz – bez zmian, bez wyjątku
    sim = rv.make_sim(cfg)
    c.apply(sim)
    assert sim.rhythm.bias == c.bias and sim.rhythm.freq == c.freq and sim.depth.z_ref == c.z_ref


def test_frequency_change_keeps_reference_continuous():
    # Zmiana f w trakcie ruchu nie może dawać skoku V_ref (inaczej uderzenie pompy).
    cfg = FishConfig(ramp_time=0.0)
    r = TailRhythm(cfg, freq=2.0)
    t = 37.3
    before = r.v_ref(t)[0]
    r.set_freq(1.75, t)
    assert r.v_ref(t)[0] == pytest.approx(before, abs=1e-15)
    assert r.freq == 1.75


def test_sim_reset_restores_python_states():
    rv = _viewer_module()
    cfg = FishConfig()
    sim = rv.make_sim(cfg)
    sim.run(3.0)
    sim.reset(z=cfg.start_depth)
    assert sim.time == 0.0
    assert sim.hydraulics.V_p == 0.0 and sim.hydraulics.Q == 0.0
    assert sim.bladder.volume == cfg.bladder_v_neutral
    assert sim.depth.integral == 0.0
    assert sim.rhythm.s == 1 and sim.rhythm.phase0 == 0.0


def test_viewer_overlay_text_is_ascii():
    # Czcionka nakładki MuJoCo ma tylko znaki ASCII 32–126 (bez polskich liter i strzałek).
    rv = _viewer_module()
    cfg = FishConfig()
    sim = rv.make_sim(cfg)
    rows = rv.status_lines(sim, rv.ViewerControls(cfg), 0.1) + drive_rows(sim)
    rows += force_rows(sim, FluidForces(sim.model).compute(sim.data))
    texts = [t for row in rows for t in row] + list(rv.HELP_TEXT)
    for t in texts:
        assert all(32 <= ord(ch) <= 126 or ch == "\n" for ch in t), repr(t)


def test_fluid_forces_per_body_add_up_and_leave_sim_untouched():
    # Siły na ciała sumują się do pełnej siły płynu na rybę (bez oporu lepkiego, ~1 mN),
    # a liczenie ich (na kopii data) nie zmienia przebiegu symulacji.
    rv = _viewer_module()
    cfg = FishConfig()
    a, b = rv.make_sim(cfg), rv.make_sim(cfg)
    fluid = FluidForces(b.model)
    worst, biggest = 0.0, 0.0
    for i in range(int(4.0 / cfg.timestep)):
        a.step()
        b.step()
        if i % 50 == 0:
            f = fluid.compute(b.data)
            assert set(f) == set(int(x) for x in fish_body_ids(b.model))
            worst = max(worst, np.abs(sum(f.values()) - fluid.total).max())
            biggest = max(biggest, np.abs(fluid.total).max())
    assert biggest > 0.05                       # ogon naprawdę pcha wodę
    assert worst < 3e-3
    np.testing.assert_array_equal(a.data.qpos, b.data.qpos)
