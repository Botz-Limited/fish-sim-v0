"""Hydraulika komór: jednostki ciśnienia (etap 2) i układ antagonistyczny L↔R (etap 4).

Jednostki – ustalone w etapie 0 (scripts/probe_volume_growth.py): SurfacePressureConstraint
w SOFA v26.06 podaje w polu `pressure` impuls z solvera ograniczeń λ = p·dt, a nie p.
W trybie valueType="pressure" wejście `value` też jest w jednostkach p·dt.
Wszystkie przeliczenia robimy TYLKO tutaj, żeby w reszcie kodu ciśnienie było w Pa.

Układ antagonistyczny (etap 4, spec sekcja 6). Woda jest praktycznie nieściśliwa, więc
pompa wymusza OBJĘTOŚĆ, a nie ciśnienie: komory dostają valueType="volumeGrowth",
a SOFA liczy ciśnienie potrzebne do tej objętości. Reszta tego pliku to czysty numpy
(bez SOFA), żeby dało się ją testować osobno:
  TailRhythm     – V_ref(t) i komenda pompy (port MuJoCo/fishsim/controllers.py),
  ClosedLoopPump – pompa I rzędu + zawór przelewowy na różnicy ciśnień,
  TailHydraulics – prefill + rytm + pompa -> zadane przyrosty objętości obu komór.
"""
from dataclasses import dataclass

import numpy as np


def pressure_pa(spc, dt: float) -> float:
    """Ciśnienie w komorze [Pa] z pola `pressure` komponentu SurfacePressureConstraint."""
    return float(np.atleast_1d(spc.pressure.value)[0]) / dt


def pressure_input(p_pa: float, dt: float) -> float:
    """Wartość `value` dla valueType="pressure", odpowiadająca ciśnieniu p_pa [Pa]."""
    return p_pa * dt


def smooth_ramp(t: float, T: float) -> tuple[float, float, float]:
    """Miękki start a(t) = ½(1 − cos(πt/T)) dla 0 ≤ t < T, 0 przed, 1 po.
    Zwraca (a, da/dt, d²a/dt²).

    Ciągła razem z pochodną, więc ani objętość, ani przepływ nie skaczą (skoki aktuacji
    to znana przyczyna eksplozji symulacji ciśnieniowych)."""
    if t <= 0:
        return 0.0, 0.0, 0.0
    if T <= 0 or t >= T:
        return 1.0, 0.0, 0.0
    k = np.pi / T
    return 0.5 * (1 - np.cos(k * t)), 0.5 * k * np.sin(k * t), 0.5 * k * k * np.cos(k * t)


class TailRhythm:
    """V_ref(t) = a(t)·(A_V·sin(2πft) + V_bias), komenda pompy z feed-forward + P.

    Dlaczego objętość, a nie sinus komendy pompy: objętość to całka z przepływu, więc
    u = A·sin(ωt) dawałoby amplitudę objętości ∝ 1/f (przegląd częstotliwości w etapie 6
    mieszałby dwa efekty), a składowa stała całkowałaby się bez końca.

    u = clip((dV_ref/dt + τ_pump·d²V_ref/dt² + K_v·(V_ref − V_p)) / Q_max, −1, 1)
    Gdy 2πf·A_V > Q_max, pompa się nasyca (|u| = 1) i amplituda spada.

    Człon τ_pump·d²V_ref/dt² (nie ma go w MuJoCo) odwraca opóźnienie pompy I rzędu: bez
    niego przy 2 Hz (ωτ = 0.38) pętla przeregulowuje – V_p dochodziło do 1.16·A_V
    (19.7 ml przy A_V = 17 ml), a komora R prawie do objętości spoczynkowej. Z nim
    błąd śledzenia ~1% A_V (test test_pump_tracks_v_ref).
    Różnica względem MuJoCo: tu rampa a(t) mnoży też V_bias (w MuJoCo bias wchodzi
    od razu), żeby niezerowy bias nie dał skoku objętości.
    """

    def __init__(self, cfg, freq=None, amp=None, bias=None):
        self.cfg = cfg
        self.freq = cfg.tail_freq if freq is None else freq
        self.amp = cfg.tail_volume_amp if amp is None else amp
        self.bias = cfg.tail_volume_bias if bias is None else bias

    def v_ref(self, t: float) -> tuple[float, float, float]:
        """(V_ref, dV_ref/dt, d²V_ref/dt²) [m³, m³/s, m³/s²]; t liczone od startu rytmu."""
        w = 2 * np.pi * self.freq
        a, da, dda = smooth_ramp(t, self.cfg.ramp_time)
        s, c = np.sin(w * t), np.cos(w * t)
        base = self.amp * s + self.bias
        A = self.amp
        return (a * base, da * base + a * A * w * c,
                dda * base + 2 * da * A * w * c - a * A * w * w * s)

    def command(self, t: float, V_p: float) -> float:
        v, dv, ddv = self.v_ref(t)
        c = self.cfg
        u = (dv + c.tau_pump * ddv + c.K_v * (v - V_p)) / c.Q_max
        return float(np.clip(u, -1.0, 1.0))


class ClosedLoopPump:
    """Pompa przetaczająca ciecz z R do L w układzie zamkniętym + zawór przelewowy.

    Stany: Q – przepływ pompy [m³/s] (człon I rzędu, dQ/dt = (u·Q_max − Q)/τ_pump),
           V_p – objętość przepompowana z R do L [m³].
    Jawny Euler: stabilny i dokładny, bo dt ≪ τ_pump (2 ms vs 30 ms).

    Zawór przelewowy łączy komory: pompa w układzie zamkniętym pracuje przeciw
    Δp = p_L − p_R, więc zawór patrzy na Δp, nie na ciśnienie jednej komory. Gdy
    |Δp| > p_max, przepuszcza Q_valve = valve_conductance·(|Δp| − p_max) z komory
    o wyższym ciśnieniu do drugiej. Suma objętości się nie zmienia – zawór zmienia
    tylko V_p. Ciśnienie znamy dopiero po rozwiązaniu kroku SOFA, więc zawór reaguje
    na Δp z poprzedniego kroku (opóźnienie 1 kroku).
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.Q = 0.0
        self.V_p = 0.0
        self.Q_valve = 0.0      # [m³/s], > 0 = z L do R
        self.valve_open = False

    def step(self, u: float, dp: float, dt: float):
        c = self.cfg
        self.Q += dt * (float(np.clip(u, -1.0, 1.0)) * c.Q_max - self.Q) / c.tau_pump
        self.V_p += self.Q * dt
        excess = abs(dp) - c.p_max
        self.valve_open = excess > 0
        self.Q_valve = np.sign(dp) * c.valve_conductance * excess if self.valve_open else 0.0
        self.V_p -= self.Q_valve * dt


@dataclass
class HydraulicsState:
    t: float
    V_ref: float
    V_p: float
    u: float
    Q: float
    Q_valve: float
    valve_open: bool
    prefill: float
    dV_L: float      # zadany przyrost objętości komory L [m³]
    dV_R: float


class TailHydraulics:
    """Prefill obu komór, potem rytm: ΔV_L = prefill + V_p, ΔV_R = prefill − V_p.

    Faza 1 (0 … prefill_time): obie komory napełniane rampą do V_prefill, pompa stoi.
    Faza 2: rytm z własną rampą amplitudy (ramp_time), czas rytmu liczony od końca
    prefillu. Kontakt ścianek komory nie jest modelowany, dlatego config pilnuje
    V_prefill > |V_bias| + A_V + margines (komora nie zejdzie poniżej spoczynku).
    """

    def __init__(self, cfg, rhythm: TailRhythm | None = None):
        self.cfg = cfg
        self.rhythm = rhythm or TailRhythm(cfg)
        self.pump = ClosedLoopPump(cfg)

    def step(self, t: float, dp: float, dt: float) -> HydraulicsState:
        """Krok od t do t + dt. dp = p_L − p_R [Pa] z poprzedniego kroku.
        Zwraca stan z zadanymi objętościami na koniec kroku (t + dt)."""
        c = self.cfg
        t_r = t - c.prefill_time
        u = self.rhythm.command(t_r, self.pump.V_p) if t_r >= 0 else 0.0
        self.pump.step(u, dp, dt)
        prefill = c.V_prefill * smooth_ramp(t + dt, c.prefill_time)[0]
        V_ref = self.rhythm.v_ref(t_r + dt)[0] if t_r + dt >= 0 else 0.0
        p = self.pump
        return HydraulicsState(t + dt, V_ref, p.V_p, u, p.Q, p.Q_valve, p.valve_open,
                               prefill, prefill + p.V_p, prefill - p.V_p)
