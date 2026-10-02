"""Hydraulika ogona: pompa + dwie komory, sprzężone z kątem ogona.

Etap 1: analiza stabilności kroku całkowania (sprężyna hydrauliczna).
Etap 3: model ODE pompy i komór (TailHydraulics) + prosty model ogona do testów
        bez MuJoCo (LumpedTail).

Sprężyna hydrauliczna: pompa wtłacza objętość V_p, a ogon "zajmuje" objętość
V_g = A_eff·r_eff·L (L = Σ w_i·θ_i – długość tendonu). Różnica ściska ciecz
i ścianki: Δp = (V_p − V_g)/C_h. Siła na tendonie F = A_eff·r_eff·Δp, więc
dF/dL = −(A_eff·r_eff)²/C_h = −k_h, czyli sprężyna o sztywności k_h.
"""

import numpy as np


def tendon_jacobian(model, cfg) -> np.ndarray:
    """dL/dq – jak długość tendonu L = Σ w_i·θ_i zależy od prędkości uogólnionych.

    Tendon jest typu "fixed", więc Jacobian to po prostu wagi w_i
    na pozycjach DOF-ów napędzanych przegubów, zero gdzie indziej.
    """
    J = np.zeros(model.nv)
    for i, w in enumerate(cfg.tendon_weights):
        J[model.jnt_dofadr[model.joint(f"tail{i}").id]] = w
    return J


def hydraulic_omega_n(model, data, cfg) -> float:
    """Częstotliwość własna sprężyny hydraulicznej [rad/s] (wymaga mj_forward).

    Bezwładność widziana przez tendon: I_eff = 1 / (J·M⁻¹·Jᵀ), gdzie M to macierz
    mas CAŁEJ ryby (kadłub się odrzuca, więc nie jest nieruchomą podstawą).
    Uwaga: MuJoCo nie dodaje masy dołączonej wody do M, więc I_eff jest mniejsze
    niż w rzeczywistości, a ω_n – większe. To najgorszy przypadek dla stabilności.
    """
    import mujoco

    J = tendon_jacobian(model, cfg)
    Minv_J = np.zeros(model.nv)
    mujoco.mj_solveM(model, data, Minv_J.reshape(1, -1), J.reshape(1, -1))
    inv_I_eff = J @ Minv_J
    return float(np.sqrt(cfg.k_hydraulic * inv_I_eff))


def euler_stability_margin(model, data, cfg) -> float:
    """ω_n·dt dla sprężyny hydraulicznej liczonej jawnie (Euler).

    Oscylator liczony jawnie jest stabilny dla ω_n·dt < 2. Wymagamy < 0.5,
    żeby błąd fazy i sztuczne tłumienie/wzmocnienie były małe.
    """
    return hydraulic_omega_n(model, data, cfg) * cfg.timestep


class TailHydraulics:
    """Pompa + dwie komory (L, R) w układzie zamkniętym, jak w SoFi.

    Stany:
      Q        – przepływ pompy z R do L [m³/s] (człon inercyjny I rzędu),
      V_L, V_R – objętości cieczy w komorach [m³]; V_L + V_R = const (układ zamknięty).
    Wejścia w każdym kroku: komenda pompy u ∈ [−1, 1] i długość tendonu L [rad].
    Wyjście: siła na tendonie F = A_eff·r_eff·Δp [N·m] (-> data.ctrl).

    Integracja: jawny Euler z krokiem MuJoCo. Działa, bo:
      1) dt ≪ τ_pump (np. 0.002 s vs 0.03 s): człon I rzędu liczony jawnie jest
         stabilny dla dt < 2·τ_pump, a dokładny dla dt ≪ τ_pump;
      2) sprężyna hydrauliczna (k_h) jest liczona jawnie razem z MuJoCo – stabilna
         dla ω_n·dt < 2, a wymagamy < 0.5 (patrz euler_stability_margin).
    Przestałaby działać przy bardzo sztywnym układzie (małe C_h, np. sama ciecz bez
    podatnych ścianek: C_h ~ V/K_wody ~ 1e-14 m³/Pa -> ω_n ~ 10⁴ rad/s) – wtedy trzeba
    by mniejszego kroku albo całkowania niejawnego.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.Ar = cfg.A_eff * cfg.r_eff   # [m³/rad] objętość "zajęta" przez ogon na radian L
        self.Q = 0.0
        self.V_L = cfg.V0_chamber
        self.V_R = cfg.V0_chamber
        self.Q_valve = 0.0                # [m³/s] przepływ przez zawór przelewowy, >0 = z L do R (do logów)

    @property
    def V_p(self) -> float:
        """Objętość przepompowana z R do L względem stanu początkowego [m³]."""
        return 0.5 * (self.V_L - self.V_R)

    def delta_p(self, L: float) -> float:
        """Różnica ciśnień p_L − p_R [Pa] ze ZNAKIEM (v1 obcinało do ≥ 0 – błąd)."""
        # Pompa wtłoczyła V_p, ogon zgięty o L "zrobił miejsce" na A·r·L.
        # Nadmiar ściska ciecz i rozpycha ścianki (podatność C_h) -> ciśnienie.
        return (self.V_p - self.Ar * L) / self.cfg.C_h

    def pressures(self, L: float) -> tuple[float, float]:
        """(p_L, p_R) [Pa] względem ciśnienia wstępnego p_pre."""
        dp = self.delta_p(L)
        return self.cfg.p_pre + dp / 2, self.cfg.p_pre - dp / 2

    def force(self, L: float) -> float:
        """Siła na tendonie F = A_eff·r_eff·Δp [N·m] (= moment na przegubie przy w_i = 1)."""
        return self.Ar * self.delta_p(L)

    def step(self, u: float, L: float, dt: float) -> float:
        """Jeden krok Eulera. Zwraca siłę F do przyłożenia w TYM kroku MuJoCo.

        Siła liczona ze stanu na początku kroku (jawnie), potem aktualizacja stanu.
        """
        c = self.cfg
        F = self.force(L)
        u = float(np.clip(u, -1.0, 1.0))
        # pompa: rozpędza się do u·Q_max ze stałą czasową τ_pump
        self.Q += dt * (u * c.Q_max - self.Q) / c.tau_pump
        # pompa przetacza ciecz z R do L (suma objętości się nie zmienia)
        self.V_L += self.Q * dt
        self.V_R -= self.Q * dt
        # Zawór przelewowy łączy komory: gdy |Δp| przekroczyłoby p_max, przepuszcza
        # nadmiar z komory o wyższym ciśnieniu do drugiej (też bez zmiany sumy).
        excess = self.V_p - self.Ar * L
        limit = c.p_max * c.C_h          # maksymalny "nadmiar" objętości przy p_max
        vent = excess - np.clip(excess, -limit, limit)
        self.V_L -= vent
        self.V_R += vent
        self.Q_valve = vent / dt
        return F


class LumpedTail:
    """Zastępczy ogon do testów hydrauliki BEZ MuJoCo (etap 3).

    Jeden stopień swobody L (długość tendonu): I·L'' + c·L' + k·L = F.
      I – bezwładność ogona widziana przez tendon (z MuJoCo: k_h/ω_n²),
      c – tłumienie zastępujące wodę (PLACEHOLDER, w MuJoCo zrobi to model płynu),
      k – sztywność silikonu.
    Całkowanie półjawnym Eulerem (najpierw prędkość, potem położenie) – stabilne
    dla oscylatora przy ω·dt < 2, tak jak sprężyna hydrauliczna w pełnym modelu.
    """

    def __init__(self, inertia=2.4e-4, damping=0.02, stiffness=0.3):
        self.I, self.c, self.k = inertia, damping, stiffness
        self.L = 0.0
        self.dL = 0.0

    def step(self, F: float, dt: float) -> float:
        ddL = (F - self.c * self.dL - self.k * self.L) / self.I
        self.dL += ddL * dt
        self.L += self.dL * dt
        return self.L


def simulate_offline(cfg, rhythm, duration: float, tail: LumpedTail | None = None,
                     bias_schedule=None) -> dict:
    """Hydraulika + zastępczy ogon, bez MuJoCo. Zwraca log (tablice numpy).

    bias_schedule(t) -> V_bias albo None (stały bias z rytmu).
    """
    dt = cfg.timestep
    hyd = TailHydraulics(cfg)
    tail = tail or LumpedTail()
    keys = ("t", "u", "Q", "Q_valve", "V_L", "V_R", "V_p", "V_ref", "V_g", "L", "dp", "p_L", "p_R", "F")
    log = {k: [] for k in keys}
    for i in range(int(round(duration / dt))):
        t = i * dt
        if bias_schedule is not None:
            rhythm.bias = bias_schedule(t)
        u = rhythm.command(t, hyd.V_p)
        p_L, p_R = hyd.pressures(tail.L)
        row = dict(t=t, u=u, Q=hyd.Q, Q_valve=hyd.Q_valve, V_L=hyd.V_L, V_R=hyd.V_R,
                   V_p=hyd.V_p, V_ref=rhythm.v_ref(t)[0], V_g=hyd.Ar * tail.L, L=tail.L,
                   dp=hyd.delta_p(tail.L), p_L=p_L, p_R=p_R)
        F = hyd.step(u, tail.L, dt)
        row["F"] = F
        for k in keys:
            log[k].append(row[k])
        tail.step(F, dt)
    return {k: np.array(v) for k, v in log.items()}
