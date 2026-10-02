"""Wypór i pęcherz balastowy.

MuJoCo NIE liczy wyporu (model płynu daje tylko opór i siły nośne – sprawdzone
w scripts/check_api.py). Wypór (prawo Archimedesa) liczymy sami: F_b = ρ·g·V.

Etap 1: objętości i bilans sił w spoczynku.
Etap 2: siły wyporu przykładane w każdym kroku przez data.xfrc_applied
        oraz pęcherz balastowy z ograniczoną szybkością pompy.
"""

import numpy as np


def ellipsoid_volume(semi_axes) -> float:
    """Objętość elipsoidy o półosiach a, b, c: V = 4/3·π·a·b·c [m³]."""
    a, b, c = semi_axes
    return 4.0 / 3.0 * np.pi * a * b * c


def body_volumes(model) -> np.ndarray:
    """Objętość wypierana przez każde ciało (suma objętości jego geomów) [m³].

    Ryba składa się wyłącznie z elipsoid, więc liczymy dokładnie ze wzoru.
    Geomy innych typów (np. podłoga w worldbody) pomijamy – nie są w wodzie
    jako ciała ruchome.
    """
    import mujoco

    vol = np.zeros(model.nbody)
    for g in range(model.ngeom):
        if model.geom_type[g] == mujoco.mjtGeom.mjGEOM_ELLIPSOID:
            vol[model.geom_bodyid[g]] += ellipsoid_volume(model.geom_size[g])
    vol[0] = 0.0  # worldbody jest nieruchomy – wypór nie ma na co działać
    return vol


def body_volume_centroids(model) -> np.ndarray:
    """Środek objętości każdego ciała w JEGO układzie (body frame) [m].

    To jest punkt przyłożenia wyporu (środek wyporu ciała). Przy jednorodnej
    gęstości pokrywa się ze środkiem masy, ale gdy np. płetwa ma inną gęstość
    niż segment, do którego jest przyczepiona – już nie.
    """
    import mujoco

    moment = np.zeros((model.nbody, 3))
    vol = np.zeros(model.nbody)
    for g in range(model.ngeom):
        if model.geom_type[g] == mujoco.mjtGeom.mjGEOM_ELLIPSOID:
            b = model.geom_bodyid[g]
            v = ellipsoid_volume(model.geom_size[g])
            moment[b] += v * model.geom_pos[g]
            vol[b] += v
    out = np.zeros((model.nbody, 3))
    mask = vol > 0
    out[mask] = moment[mask] / vol[mask, None]
    return out


def fish_body_ids(model) -> np.ndarray:
    """Id wszystkich ciał ryby (kadłub + segmenty ogona)."""
    hull = model.body("hull").id
    return np.array([b for b in range(model.nbody) if model.body_rootid[b] == hull])


def net_buoyancy(model, cfg, v_bladder: float) -> float:
    """Wypadkowa siła pionowa w spoczynku: wypór − ciężar [N]. >0 -> ryba wypływa."""
    ids = fish_body_ids(model)
    volume = body_volumes(model)[ids].sum() + v_bladder
    mass = model.body_mass[ids].sum()
    return cfg.rho_water * cfg.gravity * volume - mass * cfg.gravity


def center_of_buoyancy(model, data, cfg, v_bladder: float, x_cb: float) -> np.ndarray:
    """Środek wyporu całej ryby w układzie świata [m] (wymaga mj_forward).

    CB = średnia położeń punktów przyłożenia wyporu ważona objętościami:
      - segmenty ogona: wypór w środku objętości segmentu,
      - kadłub + pęcherz: wypór w punkcie r_local = (x_cb, 0, z_cb) w UKŁADZIE
        KADŁUBA, obróconym do świata macierzą orientacji kadłuba (xmat).
    """
    hull = model.body("hull").id
    vol = body_volumes(model)
    centroids = body_volume_centroids(model)
    moment = np.zeros(3)
    total = 0.0
    for b in fish_body_ids(model):
        if b == hull:
            v = vol[b] + v_bladder
            r_world = data.xmat[b].reshape(3, 3) @ np.array([x_cb, 0.0, cfg.z_cb])
            point = data.xipos[b] + r_world
        else:
            v = vol[b]
            point = data.xpos[b] + data.xmat[b].reshape(3, 3) @ centroids[b]
        moment += v * point
        total += v
    return moment / total


def surface_factor(z: float, r_c: float) -> float:
    """Zgrubne wygaszanie wyporu przy powierzchni (ŁATKA, nie model fizyczny).

    s = 1 głęboko pod wodą, s = 0 wysoko nad wodą, liniowo w pasie ±r_c wokół z = 0.
    Prawdziwe częściowe zanurzenie (objętość pod linią wody) jest poza zakresem demo;
    to tylko zabezpieczenie, żeby ryba z pełnym pęcherzem nie odlatywała w nieskończoność.
    """
    return float(np.clip((r_c - z) / (2.0 * r_c), 0.0, 1.0))


class Buoyancy:
    """Przykłada wypór do każdego ciała ryby przez data.xfrc_applied.

    xfrc_applied[b] = [Fx, Fy, Fz, Mx, My, Mz] w układzie ŚWIATA, przyłożone w COM ciała
    (xipos). Wypór działa w środku wyporu (CB), który zwykle nie leży w COM, więc
    oprócz siły trzeba dodać moment M = r × F, gdzie r = wektor COM -> CB.
    """

    def __init__(self, model, cfg, x_cb: float):
        self.cfg = cfg
        self.ids = fish_body_ids(model)
        self.hull = model.body("hull").id
        self.volumes = body_volumes(model)
        self.centroids = body_volume_centroids(model)
        # CB kadłuba w UKŁADZIE KADŁUBA – stały względem bryły, obraca się razem z nią.
        self.r_cb_local = np.array([x_cb, 0.0, cfg.z_cb])
        self.r_c = cfg.hull_semi_axes[2]  # promień kadłuba do wygaszania przy powierzchni

    def apply(self, data, v_bladder: float):
        rho_g = self.cfg.rho_water * self.cfg.gravity
        for b in self.ids:
            R = data.xmat[b].reshape(3, 3)  # orientacja ciała: kolumny = osie ciała w świecie
            if b == self.hull:
                volume = self.volumes[b] + v_bladder
                # r w świecie = R · r_local. Gdyby r było stałe w ŚWIECIE (CB zawsze
                # pionowo nad COM), to r ∥ F i r × F = 0 – żadnego momentu prostującego.
                # Moment pojawia się, bo przy przechyle r obraca się razem z kadłubem
                # i dostaje składową poziomą (ramię siły).
                point = data.xipos[b] + R @ self.r_cb_local
            else:
                volume = self.volumes[b]
                point = data.xpos[b] + R @ self.centroids[b]
            force = np.array([0.0, 0.0, rho_g * volume * surface_factor(point[2], self.r_c)])
            r = point - data.xipos[b]
            data.xfrc_applied[b, :3] = force
            data.xfrc_applied[b, 3:] = np.cross(r, force)


class Bladder:
    """Pęcherz balastowy: objętość śledzi wartość zadaną z ograniczoną szybkością.

    dV/dt = clip(k_bal·(V_ref − V), −q_bal_max, +q_bal_max), V ∈ [V_min, V_max].
    Daleko od celu pompa pracuje na maksimum (nasycenie), blisko celu zwalnia
    proporcjonalnie – jak prosty regulator P z ograniczeniem wydatku.
    """

    def __init__(self, cfg, volume: float | None = None):
        self.cfg = cfg
        self.volume = cfg.bladder_v_neutral if volume is None else volume

    def step(self, v_ref: float, dt: float) -> float:
        c = self.cfg
        rate = np.clip(c.k_bal * (v_ref - self.volume), -c.q_bal_max, c.q_bal_max)
        self.volume = float(np.clip(self.volume + rate * dt, c.bladder_v_min, c.bladder_v_max))
        return self.volume
