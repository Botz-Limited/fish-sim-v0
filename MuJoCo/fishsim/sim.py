"""Pętla symulacji ryby.

Kolejność w każdym kroku (dt = model.opt.timestep):
  1. hydraulika: odczyt długości tendonu L z MuJoCo -> komenda pompy u z generatora
     rytmu -> siła F = A·r·Δp na tendonie (data.ctrl) -> aktualizacja Q, V_L, V_R,
  2. pęcherz balastowy: V_bl zbliża się do V_ref (ograniczona szybkość pompy),
  3. wypór: siły i momenty do data.xfrc_applied (z bieżącej pozycji/orientacji),
  4. mj_step: MuJoCo dodaje grawitację, siły płynu, sprężyny przegubów i całkuje.
Siły z kroków 1 i 3 są liczone ze stanu na początku kroku (sprzężenie jawne).
"""

import mujoco
import numpy as np

from fishsim.buoyancy import Bladder, Buoyancy
from fishsim.config import FishConfig
from fishsim.controllers import DepthController, TailRhythm
from fishsim.hydraulics import TailHydraulics
from fishsim.model_builder import build_model

LOG_KEYS = ("t", "com", "heading", "tilt", "pitch", "v_bladder", "v_bladder_ref", "z_ref", "theta",
            "L", "u", "Q", "V_p", "V_ref", "dp", "p_L", "p_R", "F")


def quat_from_euler(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """Kwaternion [w, x, y, z] z kątów roll-pitch-yaw [rad] (kolejność Z-Y-X)."""
    q = np.zeros(4)
    mujoco.mju_euler2Quat(q, np.array([roll, pitch, yaw]), "XYZ")
    return q


class FishSim:
    def __init__(self, cfg: FishConfig | None = None, fluid: bool = True,
                 v_bladder: float | None = None, rhythm: TailRhythm | None = None,
                 depth: DepthController | None = None):
        """rhythm=None -> pompa ogona stoi (u = 0), ale hydraulika dalej działa jak
        sprężyna trzymająca ogon w pozycji wynikającej z V_p (układ zamknięty)."""
        self.cfg = cfg or FishConfig()
        self.model, self.info = build_model(self.cfg)
        if not fluid:
            # Wyłączamy model płynu MuJoCo (opór, nośność). Wypór liczymy sami,
            # więc zostaje – ryba dalej "unosi się", tylko nic jej nie hamuje.
            self.model.opt.density = 0.0
            self.model.opt.viscosity = 0.0
            # Bez wody nie ma też masy dołączonej (armature z apply_added_mass).
            # Sztywność silikonu zostaje – to własność materiału, nie wody.
            self.model.dof_armature[:] = 0.0
        self.data = mujoco.MjData(self.model)
        self.hull = self.model.body("hull").id
        self.buoyancy = Buoyancy(self.model, self.cfg, self.info.x_cb)
        self.bladder = Bladder(self.cfg, v_bladder)
        self.v_bladder_ref = self.bladder.volume
        self.hydraulics = TailHydraulics(self.cfg)
        self.rhythm = rhythm
        self.depth = depth
        self.u = 0.0
        self.tail_joints = [self.model.joint(f"tail{i}").id for i in range(self.cfg.n_segments)]
        self.tail_qpos = [self.model.jnt_qposadr[j] for j in self.tail_joints]
        mujoco.mj_forward(self.model, self.data)

    # ------------------------------------------------------------------ ustawianie stanu
    def set_pose(self, z: float | None = None, roll_deg=0.0, pitch_deg=0.0, yaw_deg=0.0):
        if z is not None:
            self.data.qpos[2] = z
        self.data.qpos[3:7] = quat_from_euler(*np.radians([roll_deg, pitch_deg, yaw_deg]))
        mujoco.mj_forward(self.model, self.data)

    def reset(self, z: float | None = None):
        """Powrót do stanu początkowego: MuJoCo + stany hydrauliki, pęcherza, regulatora.

        Potrzebne np. po Backspace w viewerze: viewer resetuje tylko data MuJoCo,
        a nasze stany w Pythonie (objętości komór, pęcherz, całka PID) by zostały.
        """
        mujoco.mj_resetData(self.model, self.data)
        if z is not None:
            self.data.qpos[2] = z
        self.hydraulics = TailHydraulics(self.cfg)
        self.bladder = Bladder(self.cfg)
        self.v_bladder_ref = self.bladder.volume
        if self.rhythm is not None:
            self.rhythm.phase0 = 0.0
        if self.depth is not None:
            self.depth.integral = 0.0
        mujoco.mj_forward(self.model, self.data)

    # ------------------------------------------------------------------ pomiary
    @property
    def time(self) -> float:
        return self.data.time

    def com(self) -> np.ndarray:
        """Środek masy CAŁEJ ryby (kadłub + ogon) w świecie [m]."""
        return self.data.subtree_com[self.hull].copy()

    def tilt(self) -> float:
        """Przechył [rad]: kąt między osią z kadłuba a pionem, acos(z_body · z_world)."""
        z_body = self.data.xmat[self.hull].reshape(3, 3)[:, 2]
        return float(np.arccos(np.clip(z_body[2], -1.0, 1.0)))

    def pitch(self) -> float:
        """Pochylenie [rad]: kąt osi x kadłuba (nosa) nad poziomem; >0 = nos w górę."""
        x_body = self.data.xmat[self.hull].reshape(3, 3)[:, 0]
        return float(np.arcsin(np.clip(x_body[2], -1.0, 1.0)))

    def heading(self) -> np.ndarray:
        """Kierunek nosa w płaszczyźnie poziomej (wektor jednostkowy [x, y])."""
        x_body = self.data.xmat[self.hull].reshape(3, 3)[:2, 0]
        return x_body / max(np.linalg.norm(x_body), 1e-12)

    def tail_length(self) -> float:
        """Długość tendonu L = Σ w_i·θ_i [rad] – to "widzi" hydraulika."""
        return float(self.data.ten_length[0])

    def state_ok(self) -> bool:
        return bool(np.all(np.isfinite(self.data.qpos)) and np.all(np.isfinite(self.data.qvel)))

    # ------------------------------------------------------------------ krok i przebieg
    def step(self):
        dt = self.model.opt.timestep
        self.u = 0.0 if self.rhythm is None else self.rhythm.command(self.time, self.hydraulics.V_p)
        self.data.ctrl[0] = self.hydraulics.step(self.u, self.tail_length(), dt)
        if self.depth is not None:
            # prędkość pionowa kadłuba (freejoint: qvel[0:3] w układzie świata)
            self.v_bladder_ref = self.depth.update(self.com()[2], self.data.qvel[2], dt)
        self.bladder.step(self.v_bladder_ref, dt)
        self.buoyancy.apply(self.data, self.bladder.volume)
        mujoco.mj_step(self.model, self.data)

    def run(self, duration: float, log_every: int = 5) -> dict:
        """Symuluje `duration` sekund. Zwraca log (tablice numpy) co `log_every` kroków."""
        n = int(round(duration / self.model.opt.timestep))
        log = {k: [] for k in LOG_KEYS}
        for i in range(n):
            if i % log_every == 0:
                self._log(log)
            self.step()
        self._log(log)
        return {k: np.array(v) for k, v in log.items()}

    def _log(self, log):
        log["t"].append(self.time)
        log["com"].append(self.com())
        log["tilt"].append(self.tilt())
        log["pitch"].append(self.pitch())
        log["v_bladder"].append(self.bladder.volume)
        log["v_bladder_ref"].append(self.v_bladder_ref)
        log["z_ref"].append(np.nan if self.depth is None else min(self.depth.z_ref, self.cfg.z_ref_max))
        log["heading"].append(self.heading())
        log["theta"].append(self.data.qpos[self.tail_qpos].copy())
        L = self.tail_length()
        hyd = self.hydraulics
        p_L, p_R = hyd.pressures(L)
        log["L"].append(L)
        log["u"].append(self.u)
        log["Q"].append(hyd.Q)
        log["V_p"].append(hyd.V_p)
        log["V_ref"].append(np.nan if self.rhythm is None else self.rhythm.v_ref(self.time)[0])
        log["dp"].append(hyd.delta_p(L))
        log["p_L"].append(p_L)
        log["p_R"].append(p_R)
        log["F"].append(hyd.force(L))


def forward_speed(log: dict, freq: float, t_skip: float = 2.0) -> float:
    """Prędkość postępowa [m/s] = przesunięcie poziome COM całej ryby w PEŁNYCH cyklach
    ogona po t_skip, rzutowane na średni kierunek nosa, podzielone przez czas.

    Dlaczego tak, a nie średnie vx głowy: głowa oscyluje na boki i w przód/tył (odrzut
    od ogona), a COM całej ryby przesuwa się tylko pod wpływem sił ZEWNĘTRZNYCH (płyn).
    Pełne cykle usuwają składową oscylacyjną, rzut na kierunek nosa – efekt lekkiego skrętu.
    """
    t = log["t"]
    period = 1.0 / freq
    n_cycles = int((t[-1] - t_skip) / period)
    if n_cycles < 1:
        raise ValueError("za krótki przebieg na pełny cykl ogona")
    t0, t1 = t[-1] - n_cycles * period, t[-1]
    i0, i1 = np.searchsorted(t, t0), len(t) - 1
    d = log["com"][i1, :2] - log["com"][i0, :2]
    h = log["heading"][i0:i1 + 1].mean(axis=0)
    h /= np.linalg.norm(h)
    return float(d @ h / (t[i1] - t[i0]))
