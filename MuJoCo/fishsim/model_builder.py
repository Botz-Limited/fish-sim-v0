"""Generator modelu MJCF ryby z parametrów FishConfig.

Ryba = kadłub (elipsoida, freejoint) + łańcuch N sztywnych segmentów ogona
połączonych przegubami hinge (oś Z) + płetwa ogonowa na ostatnim segmencie.
Pierwsze K przegubów napędza jeden tendon (siła z modelu hydrauliki).

Masy NIE są strojone ręcznie. Liczymy je tak, żeby:
  1) ryba była neutralnie pływalna przy pęcherzu w połowie zakresu,
  2) środek wyporu i środek ciężkości całej ryby leżały na jednej pionowej
     linii (trym wzdłużny) – wtedy ryba w spoczynku nie nurkuje i nie zadziera nosa.
"""

from dataclasses import dataclass

import mujoco
import numpy as np

from fishsim.buoyancy import ellipsoid_volume
from fishsim.config import FishConfig


@dataclass
class TailGeom:
    """Jeden geom ogona: w którym body leży i gdzie (w układzie tego body)."""
    body: int          # indeks segmentu (0..N-1)
    pos_x: float       # [m] środek geomu w układzie segmentu
    semi_axes: tuple   # [m]
    density: float     # [kg/m³]
    rgba: tuple

    @property
    def volume(self) -> float:
        return ellipsoid_volume(self.semi_axes)

    @property
    def mass(self) -> float:
        return self.density * self.volume


@dataclass
class FishInfo:
    """Wielkości wyliczone przy budowie modelu (potrzebne dalej w symulacji)."""
    m_hull: float          # [kg] masa kadłuba z warunku neutralnej pływalności
    x_cb: float            # [m] położenie CB kadłuba w osi X (z warunku trymu)
    m_tail: float          # [kg] masa ogona z płetwą
    v_hull: float          # [m³]
    v_tail: float          # [m³]
    added_inertia: dict | None = None      # [kg·m²] masa dołączona dodana jako armature
    passive_stiffness: dict | None = None  # [N·m/rad] wyliczona z passive_resonance_hz


def segment_body_x(cfg: FishConfig, i: int) -> float:
    """Położenie przegubu i-tego segmentu w układzie kadłuba (ogon wyprostowany)."""
    return cfg.tail_attach_x - i * cfg.segment_length


def tail_geoms(cfg: FishConfig) -> list[TailGeom]:
    """Lista geomów ogona: N zwężających się segmentów + płetwa na ostatnim."""
    geoms = []
    n = cfg.n_segments
    for i in range(n):
        # liniowe zwężanie przekroju od 1.0 (nasada) do taper_last (koniec)
        s = 1.0 if n == 1 else 1.0 + (cfg.taper_last - 1.0) * i / (n - 1)
        rx = cfg.segment_length / 2 + cfg.segment_overlap
        geoms.append(TailGeom(i, -cfg.segment_length / 2,
                              (rx, cfg.segment_ry0 * s, cfg.segment_rz0 * s),
                              cfg.rho_tail, cfg.rgba_tail))
    # Płetwa: przednia krawędź tuż przy końcu ostatniego segmentu.
    fx = cfg.fin_semi_axes[0]
    geoms.append(TailGeom(n - 1, -cfg.segment_length - fx + cfg.segment_overlap,
                          cfg.fin_semi_axes, cfg.rho_fin, cfg.rgba_fin))
    return geoms


def compute_mass_properties(cfg: FishConfig) -> FishInfo:
    """Masa kadłuba i położenie CB z warunków równowagi (ogon wyprostowany).

    Równowaga sił (pęcherz w połowie zakresu):
        ρ·(V_hull + V_tail + V_neutral) = m_hull + m_tail
    Równowaga momentów wokół osi Y przez środek kadłuba (COM kadłuba w x = 0):
        ρ·(V_hull + V_neutral)·x_cb + Σ_ogon (ρ·V_g − m_g)·x_g = 0
    Ogon jest cięższy od wody (silikon), więc ciągnie w dół z tyłu; CB kadłuba
    musi przesunąć się lekko do tyłu (x_cb < 0), żeby to zrównoważyć.
    """
    rho = cfg.rho_water
    geoms = tail_geoms(cfg)
    v_hull = ellipsoid_volume(cfg.hull_semi_axes)
    v_tail = sum(g.volume for g in geoms)
    m_tail = sum(g.mass for g in geoms)
    m_hull = rho * (v_hull + v_tail + cfg.bladder_v_neutral) - m_tail
    if m_hull <= 0:
        raise ValueError("Ogon za ciężki: kadłub musiałby mieć ujemną masę")

    # nadwyżka ciężaru nad wyporem każdego geomu ogona × ramię w osi X
    tail_moment = sum((g.mass - rho * g.volume) * (segment_body_x(cfg, g.body) + g.pos_x)
                      for g in geoms)
    x_cb = tail_moment / (rho * (v_hull + cfg.bladder_v_neutral))
    return FishInfo(m_hull=m_hull, x_cb=x_cb, m_tail=m_tail, v_hull=v_hull, v_tail=v_tail)


def _fmt(values) -> str:
    # repr = najkrótszy zapis odtwarzający float dokładnie (bez zaokrągleń w XML,
    # które psułyby bilans sił liczony w Pythonie)
    return " ".join(repr(float(v)) for v in values)


def build_mjcf(cfg: FishConfig, info: FishInfo) -> str:
    """Zwraca model MJCF jako string XML."""
    fluid = f'fluidshape="ellipsoid" fluidcoef="{_fmt(cfg.fluidcoef)}"'
    # contype=1, conaffinity=0: części ryby nie kolidują ze sobą nawzajem
    # (1 & 0 = 0), ale kolidują z podłogą (conaffinity podłogi = 1).
    collide = 'contype="1" conaffinity="0"'

    # --- ogon: zagnieżdżone body, każde z przegubem w swoim początku
    geoms = tail_geoms(cfg)
    tail_xml = ""
    for i in reversed(range(cfg.n_segments)):
        actuated = i < cfg.n_actuated
        # pasywne: sztywność tymczasowa, właściwą liczy set_passive_stiffness() po kompilacji
        k = cfg.stiffness_actuated if actuated else 0.0
        geom_xml = "".join(
            f'<geom name="{"fin" if j == len(geoms) - 1 else f"seg{i}"}" type="ellipsoid" '
            f'pos="{g.pos_x!r} 0 0" size="{_fmt(g.semi_axes)}" density="{g.density}" '
            f'rgba="{_fmt(g.rgba)}" {fluid} {collide}/>'
            for j, g in enumerate(geoms) if g.body == i)
        pos_x = cfg.tail_attach_x if i == 0 else -cfg.segment_length
        tail_xml = (
            f'<body name="seg{i}" pos="{pos_x!r} 0 0">'
            f'<joint name="tail{i}" type="hinge" axis="0 0 1" '
            f'range="{-cfg.joint_range_deg} {cfg.joint_range_deg}" '
            f'stiffness="{k}" damping="{cfg.damping_joint}"/>'
            f'{geom_xml}{tail_xml}</body>'
        )

    # --- tendon: L = Σ w_i·θ_i po napędzanych przegubach
    tendon_joints = "".join(f'<joint joint="tail{i}" coef="{float(w)!r}"/>'
                            for i, w in enumerate(cfg.tendon_weights))

    # --- znaczniki w scenie (tylko wizualne), żeby było widać ruch ryby
    col_h = (-0.3 - cfg.floor_z) / 2
    markers = "".join(
        f'<geom type="cylinder" pos="{x} {y} {cfg.floor_z + col_h}" size="0.02 {col_h}" '
        f'rgba="0.3 0.8 0.4 1" contype="0" conaffinity="0"/>'
        for x in range(-1, 6) for y in (-1, 1))

    return f"""
<mujoco model="fish">
  <compiler angle="degree" autolimits="true"/>
  <!-- implicitfast: tłumienie przegubów i pochodne sił płynu po prędkości
       liczone niejawnie -> stabilnie przy siłach płynu -->
  <option timestep="{cfg.timestep}" integrator="implicitfast"
          density="{cfg.rho_water}" viscosity="{cfg.viscosity}" gravity="0 0 {-cfg.gravity}"/>
  <visual>
    <global offwidth="1280" offheight="720"/>
    <headlight ambient="0.4 0.4 0.4" diffuse="0.5 0.5 0.5"/>
  </visual>
  <asset>
    <texture name="sky" type="skybox" builtin="gradient" rgb1="0.3 0.55 0.75" rgb2="0.05 0.15 0.3" width="256" height="256"/>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.55 0.5 0.4" rgb2="0.45 0.4 0.32" width="256" height="256"/>
    <material name="grid" texture="grid" texrepeat="10 10"/>
  </asset>
  <worldbody>
    <light directional="true" pos="0 0 5" dir="0 0 -1" diffuse="0.6 0.6 0.6"/>
    <geom name="floor" type="plane" pos="0 0 {cfg.floor_z}" size="10 10 0.1" material="grid"
          contype="0" conaffinity="1"/>
    <!-- powierzchnia wody: tylko wizualnie (bez kolizji, bez fizyki) -->
    <geom name="water_surface" type="box" pos="0 0 0" size="10 10 0.001"
          rgba="0.3 0.6 0.9 0.25" contype="0" conaffinity="0"/>
    {markers}
    <body name="hull" pos="0 0 {cfg.start_depth}">
      <freejoint name="root"/>
      <camera name="track" mode="trackcom" pos="0.1 -1.0 0.35" xyaxes="1 0 0 0 0.35 1"/>
      <!-- masa kadłuba wyliczona z warunku neutralnej pływalności (nie gęstość!) -->
      <geom name="hull" type="ellipsoid" size="{_fmt(cfg.hull_semi_axes)}" mass="{float(info.m_hull)!r}"
            rgba="{_fmt(cfg.rgba_hull)}" {fluid} {collide}/>
      {tail_xml}
    </body>
  </worldbody>
  <tendon>
    <fixed name="tail_tendon">{tendon_joints}</fixed>
  </tendon>
  <actuator>
    <!-- siła na tendonie = A_eff·r_eff·Δp [N·m]; ctrl liczy hydraulika w Pythonie.
         Brak ctrlrange: ograniczenie daje zawór przelewowy (p_max). -->
    <motor name="tail_pump" tendon="tail_tendon" gear="1" ctrllimited="false"/>
  </actuator>
</mujoco>
"""


def _distal_bodies(model, body: int) -> list[int]:
    """Ciało `body` i wszystkie ciała za nim w łańcuchu (poruszane przez jego przegub)."""
    out = []
    for b in range(model.nbody):
        x = b
        while x > 0:
            if x == body:
                out.append(b)
                break
            x = model.body_parentid[x]
    return out


def apply_added_mass(model, data, cfg: FishConfig) -> dict:
    """Masa dołączona jako armature (tryb "armature", patrz config.added_mass).

    Dla każdego obrotowego stopnia swobody dodajemy bezwładność wody poruszanej
    przez ten stopień swobody, wokół jego osi (przekątna macierzy masy dołączonej):
        I_add = Σ_geomy ρ·(m_A,⊥·d² + I_A,oś)
    m_A, I_A to współczynniki, które MuJoCo samo liczy z kształtu elipsoidy
    (model.geom_fluid[:, 6:9] i [:, 9:12], mnożone przez gęstość wody),
    d – odległość środka geomu od osi obrotu, m_A,⊥ – masa dołączona w kierunku
    ruchu geomu przy tym obrocie.
    Pomijamy translacje kadłuba: ich stopnie swobody są w układzie ŚWIATA, a masa
    dołączona jest w układzie ryby (inna wzdłuż i w poprzek) – armature w świecie
    byłaby błędna po skręcie o 90°.
    Na koniec zerujemy m_A, I_A w modelu płynu, żeby MuJoCo nie liczyło już
    niekompletnego członu −ω×(m_A·v).
    """
    mujoco.mj_forward(model, data)
    rho = cfg.rho_water
    fluid = model.geom_fluid
    fish = [g for g in range(model.ngeom) if fluid[g, 0] == 1.0]
    added = {}
    # przeguby ogona (oś z segmentu ≈ oś z świata w pozycji startowej)
    for i in range(cfg.n_segments):
        j = model.joint(f"tail{i}").id
        bodies = _distal_bodies(model, model.jnt_bodyid[j])
        anchor = data.xanchor[j]
        I = 0.0
        for g in fish:
            if model.geom_bodyid[g] in bodies:
                d = np.linalg.norm((data.geom_xpos[g] - anchor)[:2])
                I += rho * (fluid[g, 7] * d**2 + fluid[g, 11])   # m_A,y·d² + I_A,z
        model.dof_armature[model.jnt_dofadr[j]] += I
        added[f"tail{i}"] = I
    # obroty kadłuba (stopnie swobody 3..5 freejointa są w układzie kadłuba)
    hull = model.body("hull").id
    com = data.xipos[hull]
    roll = pitch = yaw = 0.0
    for g in fish:
        dx = data.geom_xpos[g][0] - com[0]
        roll += rho * fluid[g, 9]                                # I_A,x
        pitch += rho * (fluid[g, 8] * dx**2 + fluid[g, 10])      # m_A,z·dx² + I_A,y
        yaw += rho * (fluid[g, 7] * dx**2 + fluid[g, 11])        # m_A,y·dx² + I_A,z
    dof = model.jnt_dofadr[model.joint("root").id]
    model.dof_armature[dof + 3:dof + 6] += (roll, pitch, yaw)
    added.update(roll=roll, pitch=pitch, yaw=yaw)
    model.geom_fluid[:, 6:12] = 0.0
    return added


def set_passive_stiffness(model, data, cfg: FishConfig) -> dict:
    """k = I·(2π·f_res)² dla każdego pasywnego przegubu.

    I = element przekątnej macierzy masy M_jj (z armature, czyli z masą dołączoną):
    bezwładność części ogona za przegubem przy "zamrożonych" pozostałych przegubach.
    To przybliżenie – w łańcuchu przeguby są sprzężone – ale wystarcza, żeby
    rezonans końca ogona trafił w okolice f_res.
    """
    mujoco.mj_forward(model, data)
    M = np.zeros((model.nv, model.nv))
    mujoco.mj_fullM(model, data, M)   # MuJoCo 3.14: sygnatura (m, d, dst)
    out = {}
    for i in range(cfg.n_actuated, cfg.n_segments):
        j = model.joint(f"tail{i}").id
        dof = model.jnt_dofadr[j]
        model.jnt_stiffness[j] = M[dof, dof] * (2 * np.pi * cfg.passive_resonance_hz) ** 2
        out[f"tail{i}"] = float(model.jnt_stiffness[j])
    return out


def build_model(cfg: FishConfig | None = None):
    """Buduje model. Zwraca (model, info)."""
    cfg = cfg or FishConfig()
    info = compute_mass_properties(cfg)
    model = mujoco.MjModel.from_xml_string(build_mjcf(cfg, info))
    data = mujoco.MjData(model)
    info.added_inertia = apply_added_mass(model, data, cfg) if cfg.added_mass == "armature" else {}
    info.passive_stiffness = set_passive_stiffness(model, data, cfg)
    return model, info


def describe(model, data, cfg: FishConfig, info: FishInfo) -> str:
    """Raport tekstowy etapu 1: masy, objętości, pływalność, CG/CB, stabilność kroku."""
    from fishsim.buoyancy import body_volumes, center_of_buoyancy, fish_body_ids, net_buoyancy
    from fishsim.hydraulics import euler_stability_margin, hydraulic_omega_n

    mujoco.mj_forward(model, data)
    ids = fish_body_ids(model)
    vols = body_volumes(model)
    hull = model.body("hull").id
    lines = ["Ciała ryby:", f"  {'body':<8}{'masa [g]':>10}{'V [ml]':>10}{'ρ_śr [kg/m³]':>14}"]
    for b in ids:
        lines.append(f"  {model.body(b).name:<8}{model.body_mass[b] * 1e3:>10.1f}"
                     f"{vols[b] * 1e6:>10.1f}{model.body_mass[b] / vols[b]:>14.0f}")
    m_tot = model.body_mass[ids].sum()
    lines.append(f"  {'SUMA':<8}{m_tot * 1e3:>10.1f}{vols[ids].sum() * 1e6:>10.1f}")

    lines.append("\nPływalność (wypór − ciężar):")
    for label, v in (("V_min", cfg.bladder_v_min), ("V_neutral", cfg.bladder_v_neutral),
                     ("V_max", cfg.bladder_v_max)):
        f = net_buoyancy(model, cfg, v)
        lines.append(f"  pęcherz {label:<10}{v * 1e6:6.1f} ml -> {f:+8.4f} N "
                     f"({f / (m_tot * cfg.gravity) * 100:+.2f}% ciężaru)")

    # Środki w układzie kadłuba (w pozycji startowej orientacja kadłuba = świat)
    origin = data.xipos[hull]
    cg = data.subtree_com[hull] - origin
    cb = center_of_buoyancy(model, data, cfg, cfg.bladder_v_neutral, info.x_cb) - origin
    lines.append("\nŚrodki względem COM kadłuba (pęcherz neutralny, ogon prosty):")
    lines.append(f"  CG całej ryby: x = {cg[0] * 1e3:+7.2f} mm, z = {cg[2] * 1e3:+6.2f} mm")
    lines.append(f"  CB całej ryby: x = {cb[0] * 1e3:+7.2f} mm, z = {cb[2] * 1e3:+6.2f} mm")
    lines.append(f"  trym: x_CB − x_CG = {(cb[0] - cg[0]) * 1e3:+.3f} mm (cel: |·| < 1 mm)")
    lines.append(f"  CB nad CG o {(cb[2] - cg[2]) * 1e3:.2f} mm (>0 -> moment prostujący)")
    lines.append(f"  x_cb kadłuba (z trymu) = {info.x_cb * 1e3:+.2f} mm")

    lines.append(f"\nMasa dołączona (tryb \"{cfg.added_mass}\"):")
    for k, v in (info.added_inertia or {}).items():
        lines.append(f"  {k:<6} +{v * 1e4:8.2f} kg·cm²")
    lines.append(f"Sztywność pasywnych przegubów (f_res = {cfg.passive_resonance_hz} Hz):")
    for k, v in (info.passive_stiffness or {}).items():
        lines.append(f"  {k:<6} k = {v:.3f} N·m/rad")

    lines.append("\nHydraulika – stabilność kroku (Euler jawny):")
    lines.append(f"  k_h = {cfg.k_hydraulic:.2f} N·m/rad, ω_n = {hydraulic_omega_n(model, data, cfg):.1f} rad/s"
                 f" ({hydraulic_omega_n(model, data, cfg) / (2 * np.pi):.1f} Hz)")
    margin = euler_stability_margin(model, data, cfg)
    lines.append(f"  ω_n·dt = {margin:.3f} (wymagane < 0.5; granica stabilności 2.0)"
                 + ("" if margin < 0.5 else "  <-- UWAGA: za duże!"))
    lines.append(f"  τ_pump/dt = {cfg.tau_pump / cfg.timestep:.0f} (wymagane ≫ 1)")
    return "\n".join(lines)
