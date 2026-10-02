"""Sterowanie: generator rytmu ogona (etap 3), skręt i głębokość (etap 5).

Dlaczego generator zadaje OBJĘTOŚĆ, a nie przepływ (zmiana względem SPEC v1):
objętość w komorze to CAŁKA z przepływu. Gdyby u(t) = A·sin(ωt) + bias, to
składowa stała `bias` całkowałaby się bez końca (V rośnie liniowo), aż zawór
przelewowy zablokuje ogon na jednej stronie. Nawet sam sinus startujący od zera
daje V(t) = A/ω·(1 − cos ωt) ≥ 0 – przesunięte w jedną stronę.
Zadając V_ref(t) i korygując błąd objętości, średnie ugięcie ogona jest pod kontrolą.
"""

import numpy as np


class TailRhythm:
    """V_ref(t) = a(t)·A_V·sin(2πft) + V_bias, komenda pompy z feed-forward + P.

    u = clip((dV_ref/dt + K_v·(V_ref − V_p)) / Q_max, −1, 1)
      dV_ref/dt        – przepływ, który "powinien" płynąć (feed-forward),
      K_v·(V_ref − V_p) – korekta, gdy pompa nie nadąża albo dryfuje.
    Gdy 2πf·A_V > Q_max, pompa się nasyca (|u| = 1) i amplituda spada – to jest
    lekcja z etapu 6: przy stałym wydatku pompy wyższa częstotliwość = mniejszy ruch.
    """

    def __init__(self, cfg, freq=None, amp=None, bias=None):
        self.cfg = cfg
        self.freq = cfg.tail_freq if freq is None else freq
        self.amp = cfg.tail_volume_amp if amp is None else amp
        self.bias = cfg.tail_volume_bias if bias is None else bias
        self.phase0 = 0.0   # [rad] przesunięcie fazy – utrzymuje ciągłość przy zmianie f

    def set_freq(self, freq: float, t: float):
        """Zmiana częstotliwości w trakcie ruchu BEZ skoku fazy.

        Faza φ(t) = 2π·f·t + φ0. Gdyby po prostu podmienić f, φ skoczyłoby o
        2π·(f_nowe − f_stare)·t – dla t = 60 s to setki radianów, czyli skok V_ref
        i uderzenie pompy. Dobieramy φ0 tak, żeby φ(t) było ciągłe.
        """
        self.phase0 += 2 * np.pi * (self.freq - freq) * t
        self.freq = freq

    def _ramp(self, t: float) -> tuple[float, float]:
        """Miękki start a(t) = ½(1 − cos(πt/T)) dla t < T, potem 1. Zwraca (a, da/dt)."""
        T = self.cfg.ramp_time
        if T <= 0 or t >= T:
            return 1.0, 0.0
        return 0.5 * (1 - np.cos(np.pi * t / T)), 0.5 * np.pi / T * np.sin(np.pi * t / T)

    def v_ref(self, t: float) -> tuple[float, float]:
        """(V_ref, dV_ref/dt) [m³, m³/s]."""
        w = 2 * np.pi * self.freq
        a, da = self._ramp(t)
        s, c = np.sin(w * t + self.phase0), np.cos(w * t + self.phase0)
        return a * self.amp * s + self.bias, self.amp * (da * s + a * w * c)

    def command(self, t: float, V_p: float) -> float:
        v, dv = self.v_ref(t)
        u = (dv + self.cfg.K_v * (v - V_p)) / self.cfg.Q_max
        return float(np.clip(u, -1.0, 1.0))


class DepthController:
    """Kaskada głębokości: PID z -> V_ref pęcherza; pompa balastowa śledzi V_ref (buoyancy.Bladder).

    Dlaczego nie PID z -> dV/dt wprost (SPEC v1): wtedy wyjście regulatora jest jeszcze
    raz całkowane przez pęcherz (V = ∫dV/dt), a siła wyporu ~ V daje przyspieszenie,
    które całkuje się dwa razy do z. Obiekt = potrójny integrator, a człon P działa
    jak I – trudny do stabilnego zestrojenia. Tu wyjście to OBJĘTOŚĆ, czyli wprost siła:
        F_net = ρ·g·(V_ref − V_neutral)   (po dojściu pęcherza do V_ref)
    więc PD działa jak sprężyna (K_p) i tłumik (K_d) na głębokość.

    Pochodna liczona z prędkości (−K_d·v_z), nie z uchybu: skok z_ref nie daje
    "kopnięcia" pochodnej. Anti-windup: całka rośnie tylko, gdy wyjście nie jest
    nasycone (albo gdy uchyb wyprowadza z nasycenia), i jest ograniczona.
    """

    def __init__(self, cfg, z_ref: float):
        self.cfg = cfg
        self.z_ref = z_ref
        self.integral = 0.0

    def set_reference(self, z_ref: float):
        # ograniczenie z SPEC §6: regulator nie wyciąga ryby na powierzchnię
        self.z_ref = min(z_ref, self.cfg.z_ref_max)

    def update(self, z: float, v_z: float, dt: float) -> float:
        c = self.cfg
        z_ref = min(self.z_ref, c.z_ref_max)
        e = z_ref - z                                   # >0: ryba za głęboko -> więcej wyporu
        v_pd = c.bladder_v_neutral + c.depth_kp * e - c.depth_kd * v_z
        v_out = v_pd + c.depth_ki * self.integral
        saturated_hi = v_out >= c.bladder_v_max
        saturated_lo = v_out <= c.bladder_v_min
        if not ((saturated_hi and e > 0) or (saturated_lo and e < 0)):
            self.integral += e * dt
            # całka nie może sama przesunąć wyjścia o więcej niż pół zakresu pęcherza
            i_max = 0.5 * (c.bladder_v_max - c.bladder_v_min) / max(c.depth_ki, 1e-30)
            self.integral = float(np.clip(self.integral, -i_max, i_max))
        v_out = v_pd + c.depth_ki * self.integral
        return float(np.clip(v_out, c.bladder_v_min, c.bladder_v_max))
