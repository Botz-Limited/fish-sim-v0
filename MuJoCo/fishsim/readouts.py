"""Odczyty na żywo dla viewera: siły wody na każdym ciele, strzałki sił, wiersze stanu.

MuJoCo podaje siły płynu tylko jako siły uogólnione (data.qfrc_fluid). Ryba wisi na
freejoincie, więc pierwsze trzy składowe to wypadkowa siła wody na całą rybę w układzie
świata. Żeby rozdzielić ją na ciała, FluidForces liczy siły płynu ponownie z "mokrym" tylko
jednym ciałem naraz (jego współczynniki fluidcoef zostają, pozostałe są zerowane) – wtedy
qfrc_fluid[0:3] to siła na to jedno ciało. To jeden mj_passive na ciało (7 na klatkę viewera),
na kopii data (symulacja nie widzi żadnej zmiany), na końcu współczynniki wracają.

Masa dołączona jest tu w armature (config.added_mass = "armature"), więc w geom_fluid nie ma
członów masy wirtualnej – siła płynu to opory, siła nośna Kutty i Magnusa. Lepki opór Stokesa
nie zależy od fluidcoef, więc przebiegi na ciało idą z lepkością 0; ta mała reszta (~1 mN)
nie jest rozdzielana na ciała, ale jest w sumie `total` (= pełne qfrc_fluid[0:3]).
"""
import mujoco
import numpy as np

from fishsim.buoyancy import fish_body_ids

# Kolumny model.geom_fluid: [0] = kształt (ellipsoid), [1:6] = fluidcoef
# (blunt, slender, angular, Kutta, Magnus), [6:12] = masa/bezwładność wirtualna.
_COEF = slice(1, 6)


class FluidForces:
    def __init__(self, model):
        self.m = model
        self.coef = model.geom_fluid[:, _COEF].copy()
        self.bodies = [int(b) for b in fish_body_ids(model)
                       if np.any(model.geom_fluid[model.geom_bodyid == b, 0] > 0)]
        self.geoms = {b: np.where(model.geom_bodyid == b)[0] for b in self.bodies}
        self.scratch = mujoco.MjData(model)

    def compute(self, data) -> dict:
        """{body id: siła wody [N] w układzie świata}; `data` nie jest zmieniane.
        Pełna siła na rybę (z oporem lepkim) zostaje w self.total."""
        m = self.m
        mujoco.mj_copyData(self.scratch, m, data)
        data = self.scratch
        mujoco.mj_forward(m, data)            # kinematyka i prędkości zgodne z bieżącym stanem
        self.total = data.qfrc_fluid[0:3].copy()
        visc = m.opt.viscosity
        out = {}
        try:
            m.opt.viscosity = 0.0
            for b in self.bodies:
                m.geom_fluid[:, _COEF] = 0.0
                m.geom_fluid[self.geoms[b], _COEF] = self.coef[self.geoms[b]]
                mujoco.mj_passive(m, data)
                out[b] = data.qfrc_fluid[0:3].copy()
        finally:
            m.opt.viscosity = visc
            m.geom_fluid[:, _COEF] = self.coef
        return out


def gravity_and_buoyancy(sim) -> np.ndarray:
    """Wypór minus ciężar całej ryby [N] (wektor w układzie świata)."""
    ids = fish_body_ids(sim.model)
    buoy = sim.data.xfrc_applied[ids, :3].sum(axis=0)
    weight = sim.model.body_mass[ids].sum() * sim.model.opt.gravity
    return buoy + weight


def draw_arrows(scn, arrows, width=0.008):
    """Strzałki w viewer.user_scn. arrows: lista (początek, wektor [m], rgba)."""
    scn.ngeom = 0
    for p, v, rgba in arrows:
        if scn.ngeom >= scn.maxgeom or np.linalg.norm(v) < 1e-4:
            continue
        g = scn.geoms[scn.ngeom]
        mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_ARROW, np.zeros(3), np.zeros(3), np.zeros(9),
                            np.asarray(rgba, dtype=np.float32))
        mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_ARROW, width, np.asarray(p, float), np.asarray(p + v, float))
        scn.ngeom += 1


WATER_RGBA = (1.00, 0.20, 0.80, 1.0)   # siła wody na ciało (magenta: zielone są słupki w scenie)
BUOY_RGBA = (0.10, 0.90, 1.00, 1.0)    # wypór − ciężar całej ryby (cyan)
ARROW_SCALE = 0.15                     # [m/N]: 1 N -> strzałka 15 cm (siły wody, do ~1.5 N)
BUOY_SCALE = 2.0                       # [m/N]: 10 mN -> 2 cm (wypór − ciężar jest ~100× mniejszy)


def force_arrows(sim, forces: dict, scale: float = ARROW_SCALE, buoy_scale: float = BUOY_SCALE) -> list:
    arrows = [(sim.data.xipos[b], scale * f, WATER_RGBA) for b, f in forces.items()]
    arrows.append((sim.com(), buoy_scale * gravity_and_buoyancy(sim), BUOY_RGBA))
    return arrows


def force_rows(sim, forces: dict, total=None) -> list:
    """Wiersze (nazwa, wartość) do nakładki: siły w mN, w układzie ryby (naprzód / w bok)."""
    head = sim.heading()                                 # jednostkowy kierunek ryby w XY
    side = np.array([-head[1], head[0]])
    total = sum(forces.values()) if total is None else total
    tail = sum(f for b, f in forces.items() if b != sim.hull)
    nb = gravity_and_buoyancy(sim)
    fwd = lambda f: 1e3 * float(f[:2] @ head)
    lat = lambda f: 1e3 * float(f[:2] @ side)
    return [
        ("water on fish", f"{fwd(total):+6.1f} fwd {lat(total):+6.1f} side mN"),
        ("water on tail+fin", f"{fwd(tail):+6.1f} fwd {lat(tail):+6.1f} side mN"),
        ("water on hull", f"{fwd(forces[sim.hull]):+6.1f} fwd {lat(forces[sim.hull]):+6.1f} side mN"),
        ("buoyancy - weight", f"{1e3 * nb[2]:+6.1f} mN (up +)"),
    ]


def drive_rows(sim) -> list:
    """Wiersze napędu: moment z hydrauliki, pompa, kąty segmentów ogona."""
    L = sim.tail_length()
    th = np.degrees([sim.data.qpos[a] for a in sim.tail_qpos])
    return [
        ("tail torque (hydr.)", f"{1e3 * sim.hydraulics.force(L):+6.1f} mN m"),
        ("pump u / flow Q", f"{sim.u:+5.2f} / {sim.hydraulics.Q * 1e6:+6.1f} ml/s"),
        ("tail joint angles", " ".join(f"{a:+3.0f}" for a in th) + " deg"),
    ]
