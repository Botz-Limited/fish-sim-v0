"""Wszystkie parametry symulacji w jednym miejscu.

UWAGA: to jest demo możliwości MuJoCo, nie cyfrowy bliźniak. Każda wartość fizyczna
oznaczona PLACEHOLDER jest zgadnięta "na rząd wielkości" i wymaga identyfikacji
z pomiarów prawdziwego robota. Nie traktuj ich jako danych.

Układ współrzędnych ryby (układ kadłuba):
  +X – do przodu (nos), -X – w stronę ogona,
  +Y – lewa burta, +Z – do góry.
Ogon macha w płaszczyźnie XY (przeguby wokół osi Z).
"""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class FishConfig:
    # ------------------------------------------------------------------ środowisko
    rho_water: float = 1000.0      # [kg/m³] gęstość wody słodkiej (wartość fizyczna, nie placeholder)
    viscosity: float = 0.0009      # [Pa·s] lepkość dynamiczna wody ~25°C
    gravity: float = 9.81          # [m/s²]
    timestep: float = 0.002        # [s] krok MuJoCo; ten sam krok dla hydrauliki (Euler jawny)
    floor_z: float = -3.0          # [m] dno basenu
    start_depth: float = -1.0      # [m] z startowe środka kadłuba

    # ------------------------------------------------------------------ kadłub
    # Elipsoida; w MJCF `size` to PÓŁOSIE, więc długość 0.25 m -> półoś 0.125 m.
    hull_semi_axes: tuple = (0.125, 0.05, 0.05)  # [m] PLACEHOLDER – do identyfikacji z pomiarów
    # Środek wyporu (CB) nad środkiem masy (COM) kadłuba, w układzie kadłuba.
    # Ciężkie elementy (akumulator, pompa) są nisko, więc COM leży poniżej środka
    # geometrycznego, a CB jest w środku geometrycznym -> CB nad COM.
    # W modelu COM kadłuba leży w środku elipsoidy (MuJoCo liczy go z geomu),
    # a CB przesuwamy o z_cb w górę – dla fizyki liczy się tylko ich WZGLĘDNE położenie.
    z_cb: float = 0.01             # [m] PLACEHOLDER – do identyfikacji z pomiarów
    # x_cb NIE jest parametrem: liczy go model_builder z warunku trymu wzdłużnego.

    # ------------------------------------------------------------------ ogon
    n_segments: int = 5            # N – liczba sztywnych segmentów ogona
    n_actuated: int = 3            # K – ile pierwszych przegubów napędza hydraulika (reszta pasywna)
    tail_attach_x: float = -0.11   # [m] położenie 1. przegubu względem środka kadłuba
    segment_length: float = 0.04   # [m] odległość między przegubami; PLACEHOLDER – do identyfikacji z pomiarów
    # Półosie przekroju 1. segmentu (Y – grubość, Z – wysokość); ogon jest
    # spłaszczony bocznie jak u ryby. Kolejne segmenty zwężają się liniowo.
    segment_ry0: float = 0.030     # [m] PLACEHOLDER – do identyfikacji z pomiarów
    segment_rz0: float = 0.040     # [m] PLACEHOLDER – do identyfikacji z pomiarów
    taper_last: float = 0.4        # [-] skala przekroju ostatniego segmentu względem 1.
    segment_overlap: float = 0.002 # [m] geomy zachodzą na siebie, żeby nie było szczelin w renderze
    rho_tail: float = 1100.0       # [kg/m³] silikon (Ecoflex/Dragon Skin ~1070–1140); PLACEHOLDER – do identyfikacji z pomiarów

    # Płetwa ogonowa: cienka w Y, wysoka w Z (płaszczyzna płetwy = XZ),
    # więc przy machaniu w Y pcha wodę dużą powierzchnią.
    fin_semi_axes: tuple = (0.035, 0.003, 0.06)  # [m] PLACEHOLDER – do identyfikacji z pomiarów
    rho_fin: float = 1100.0        # [kg/m³] PLACEHOLDER – do identyfikacji z pomiarów

    # Przeguby (pseudo-rigid-body model silikonu): sprężyna + tłumik w każdym przegubie.
    joint_range_deg: float = 35.0  # [deg] ograniczenie wychylenia każdego przegubu
    # Napędzane przeguby są sztywniejsze (ścianki komór hydraulicznych).
    stiffness_actuated: float = 0.3  # [N·m/rad] PLACEHOLDER – do identyfikacji z pomiarów
    # Pasywne przeguby: sztywność NIE jest podawana wprost, tylko LICZONA z zadanej
    # częstotliwości rezonansu: k = I·(2π·f_res)², gdzie I to bezwładność części ogona
    # za przegubem RAZEM z masą dołączoną wody (patrz added_mass). Pierwsza wersja
    # (k = 0.1 z oszacowania bez wody) dawała rezonans < 1 Hz po dodaniu masy wody,
    # a powyżej rezonansu fala na ogonie biegnie do głowy i ryba płynie do tyłu.
    passive_resonance_hz: float = 3.0  # [Hz] PLACEHOLDER – do identyfikacji z pomiarów
    damping_joint: float = 0.005     # [N·m·s/rad] tłumienie materiałowe silikonu; PLACEHOLDER – do identyfikacji z pomiarów

    # ------------------------------------------------------------------ model płynu MuJoCo
    # fluidcoef = [C_blunt, C_slender, C_angular, C_Kutta, C_Magnus] – domyślne z dokumentacji:
    #   C_blunt   – opór ciśnieniowy (czołowy) przy ruchu prostopadłym do dużej ściany,
    #   C_slender – opór przy ruchu wzdłuż smukłego kształtu (tarcie/opływ),
    #   C_angular – opór obrotowy (tłumienie obrotu bryły w płynie),
    #   C_Kutta   – siła nośna z cyrkulacji (warunek Kutty) przy kącie natarcia,
    #   C_Magnus  – siła Magnusa od obrotu bryły poruszającej się w płynie.
    fluidcoef: tuple = (0.5, 0.25, 1.5, 1.0, 1.0)  # PLACEHOLDER – do identyfikacji z pomiarów (dopasowanie do trajektorii)

    # Masa dołączona (added mass) – woda, którą bryła musi rozpędzić razem ze sobą.
    # MuJoCo liczy współczynniki m_A, I_A dla każdej elipsoidy, ale w sile płynu
    # zostawia tylko człon −ω×(m_A·v), a pomija −m_A·v̇ (wyłączony w źródle). Sam
    # pierwszy człon daje NIEFIZYCZNĄ średnią siłę dla machającej płetwy (u nas:
    # ciąg do tyłu i tonięcie). Tryby:
    #   "armature" – usuwamy oba człony z modelu płynu, a masę dołączoną dodajemy
    #                jako bezwładność (armature) przegubów i obrotów kadłuba
    #                (przekątna macierzy masy dołączonej; translacje pominięte),
    #   "mujoco"   – zachowanie domyślne MuJoCo (do porównania w README).
    added_mass: str = "armature"

    # ------------------------------------------------------------------ pęcherz balastowy
    # Zmienna objętość wypierana przez rybę. Masy są liczone tak, żeby ryba była
    # neutralna DOKŁADNIE w środku zakresu: V_min -> tonie, V_max -> wypływa.
    bladder_v_min: float = 0.0     # [m³] PLACEHOLDER – do identyfikacji z pomiarów
    bladder_v_max: float = 40e-6   # [m³] 40 ml; PLACEHOLDER – do identyfikacji z pomiarów
    q_bal_max: float = 10e-6       # [m³/s] maks. wydatek pompy balastowej (10 ml/s); PLACEHOLDER – do identyfikacji z pomiarów
    k_bal: float = 5.0             # [1/s] wzmocnienie śledzenia V_ref przez pompę balastową

    # Regulator głębokości (kaskada PID -> V_ref pęcherza). Wzmocnienia dobrane
    # eksperymentalnie w etapie 5 – opis metody w README.
    depth_kp: float = 200e-6       # [m³/m] 10 cm uchybu -> 20 ml (pół zakresu pęcherza)
    depth_ki: float = 20e-6        # [m³/(m·s)] usuwa uchyb od siły pionowej przy pływaniu (~1 cm)
    depth_kd: float = 300e-6       # [m³·s/m] tłumienie: bez przeregulowania przy zawisie
    z_ref_max: float = -0.3        # [m] najpłytsza dozwolona głębokość zadana

    # ------------------------------------------------------------------ hydraulika ogona
    # Siła na tendonie F = A_eff·r_eff·Δp  [N·m], bo długość tendonu L = Σ w_i·θ_i jest w radianach.
    A_eff: float = 4e-4            # [m²] efektywna powierzchnia ścianki komory; PLACEHOLDER – do identyfikacji z pomiarów
    r_eff: float = 0.05            # [m] efektywne ramię siły względem osi zgięcia; PLACEHOLDER – do identyfikacji z pomiarów
    # Sztywność sprężyny hydraulicznej na tendonie: k_h = (A_eff·r_eff)²/C_h.
    # C_h dobrane tak, żeby k_h = 5 N·m/rad (wyraźnie sztywniej niż przeguby).
    C_h: float = 8e-11             # [m³/Pa] podatność układu (ścianki + ściśliwość); PLACEHOLDER – do identyfikacji z pomiarów
    p_max: float = 50e3            # [Pa] ciśnienie otwarcia zaworu przelewowego; PLACEHOLDER – do identyfikacji z pomiarów
    V0_chamber: float = 30e-6      # [m³] objętość każdej komory przy ogonie prostym (30 ml); PLACEHOLDER – do identyfikacji z pomiarów
    p_pre: float = 0.0             # [Pa] ciśnienie wstępne obu komór (tylko do wykresów p_L, p_R)
    Q_max: float = 60e-6           # [m³/s] maks. wydatek pompy ogona (60 ml/s); PLACEHOLDER – do identyfikacji z pomiarów
    tau_pump: float = 0.03         # [s] stała czasowa rozpędzania pompy; PLACEHOLDER – do identyfikacji z pomiarów
    tendon_weight_last: float = 0.4  # [-] waga w_K ostatniego napędzanego przegubu (w_1 = 1, liniowo)

    # ------------------------------------------------------------------ rytm ogona (generator objętości)
    # Zadajemy OBJĘTOŚĆ przepompowaną V_ref(t), nie przepływ – patrz controllers.py.
    # A_V = 8 ml odpowiada L ≈ A_V/(A_eff·r_eff) = 0.4 rad wychylenia tendonu.
    tail_freq: float = 2.0          # [Hz] częstotliwość machania (punkt pracy; patrz sweep)
    tail_volume_amp: float = 8e-6   # [m³] amplituda A_V; PLACEHOLDER – do identyfikacji z pomiarów
    tail_volume_bias: float = 0.0   # [m³] V_bias – stałe ugięcie ogona (skręt)
    K_v: float = 10.0               # [1/s] korekta błędu objętości; K_v·τ_pump < 0.5, żeby pętla nie oscylowała
    ramp_time: float = 1.0          # [s] miękki start amplitudy

    # ------------------------------------------------------------------ wygląd
    rgba_hull: tuple = (0.95, 0.55, 0.15, 1.0)
    rgba_tail: tuple = (0.95, 0.70, 0.30, 1.0)
    rgba_fin: tuple = (0.90, 0.35, 0.10, 0.9)

    # pola wyliczane w __post_init__ (nie ustawiaj ręcznie)
    tendon_weights: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        if self.added_mass not in ("armature", "mujoco"):
            raise ValueError('added_mass musi być "armature" albo "mujoco"')
        if not 1 <= self.n_actuated <= self.n_segments:
            raise ValueError("n_actuated (K) musi być w zakresie 1..n_segments (N)")
        if not self.bladder_v_min < self.bladder_v_max:
            raise ValueError("bladder_v_min musi być < bladder_v_max")
        # Wagi rozkładu siły tendonu na przeguby: malejące ku końcowi ogona,
        # bo komory hydrauliczne są największe przy nasadzie ogona.
        if self.n_actuated == 1:
            self.tendon_weights = np.array([1.0])
        else:
            self.tendon_weights = np.linspace(1.0, self.tendon_weight_last, self.n_actuated)

    @property
    def bladder_v_neutral(self) -> float:
        """Objętość pęcherza, przy której ryba ma zerową wypadkową pływalność [m³]."""
        return 0.5 * (self.bladder_v_min + self.bladder_v_max)

    @property
    def k_hydraulic(self) -> float:
        """Sztywność sprężyny hydraulicznej widziana przez tendon [N·m/rad]."""
        return (self.A_eff * self.r_eff) ** 2 / self.C_h
