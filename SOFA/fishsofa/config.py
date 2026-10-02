"""Wszystkie parametry demo SOFA w jednym miejscu.

JEDNOSTKI: wyłącznie SI – metry, kilogramy, sekundy, paskale (m, kg, s, Pa).
Uwaga: przykłady SoftRobots często używają milimetrów. Tu NIE mieszamy jednostek.

UWAGA: to jest demo możliwości SOFA, nie skalibrowany model. Każda wartość fizyczna
oznaczona PLACEHOLDER jest zgadnięta "na rząd wielkości" i wymaga identyfikacji
z pomiarów prawdziwego ogona. Nie traktuj ich jako danych.

Układ współrzędnych (taki sam jak w MuJoCo/fishsim/config.py):
  +X – do przodu (w stronę kadłuba); ogon wychodzi z kadłuba w kierunku -X,
  +Y – lewa burta; w tej osi ogon się zgina,
  +Z – do góry; grawitacja działa w -Z.
Początek układu: środek przedniej (przymocowanej do kadłuba) ściany ogona.
"""

from dataclasses import dataclass, field


@dataclass
class TailConfig:
    # ------------------------------------------------------------------ otoczenie
    rho_water: float = 1000.0      # [kg/m³] woda słodka (wartość fizyczna, nie placeholder)
    gravity: float = 9.81          # [m/s²]
    # "air"   – pełny ciężar silikonu i wody w komorach, brak oporu wody,
    # "water" – ciężar pozorny silikonu g·(1 − ρ_wody/ρ_silikonu), woda w komorach
    #           ma bezwładność, ale nie ma ciężaru (wypór = ciężar), opór wody włączony.
    environment: str = "air"
    chambers_filled: bool = True   # komory pełne wody (masa wody liczona do bezwładności)

    # ------------------------------------------------------------------ geometria ogona
    # Wymiary przepisane z MuJoCo/fishsim/config.py, żeby eksport PRBM (etap 7) miał sens:
    #   długość = n_segments · segment_length, przekrój = 2·segment_ry0 × 2·segment_rz0,
    #   zwężenie taper_last, płetwa = 2·fin_semi_axes. Test test_dimensions_match_mujoco
    #   pilnuje, żeby obie konfiguracje się nie rozjechały.
    n_segments: int = 5            # N segmentów w MuJoCo (tu tylko do długości i PRBM)
    n_actuated: int = 3            # K napędzanych segmentów w MuJoCo -> długość komór
    segment_length: float = 0.04   # [m] PLACEHOLDER – do identyfikacji z pomiarów
    ry0: float = 0.030             # [m] półoś przekroju w Y (grubość) na nasadzie; PLACEHOLDER – do identyfikacji z pomiarów
    rz0: float = 0.040             # [m] półoś przekroju w Z (wysokość) na nasadzie; PLACEHOLDER – do identyfikacji z pomiarów
    taper_last: float = 0.4        # [-] skala przekroju na końcu ogona względem nasady
    # Przekrój zwęża się liniowo od 1.0 w x = 0 do taper_last w x = −L. W MuJoCo skala
    # dotyczy środków segmentów (elipsoid), więc to przybliżenie tego samego kształtu.

    # Płetwa ogonowa: eliptyczna płytka o stałej grubości, w płaszczyźnie XZ.
    fin_semi_x: float = 0.035      # [m] PLACEHOLDER – do identyfikacji z pomiarów
    fin_semi_z: float = 0.060      # [m] PLACEHOLDER – do identyfikacji z pomiarów
    fin_thickness: float = 0.006   # [m] 2·fin_semi_axes[1] z MuJoCo; PLACEHOLDER – do identyfikacji z pomiarów
    # Świadome odstępstwo od MuJoCo: w MuJoCo płetwa zachodzi na ogon 2 mm, ale tam jest
    # przyspawana sztywno. W FEM połączenie przez 2 mm byłoby przewężeniem ~6×40 mm,
    # czyli niechcianym zawiasem. Dlatego korzeń płetwy wchodzi głębiej w koniec ogona.
    fin_root_overlap: float = 0.015  # [m]

    # ------------------------------------------------------------------ komory hydrauliczne
    chamber_x_start: float = 0.01  # [m] grubość ścianki czołowej przy mocowaniu; PLACEHOLDER – do identyfikacji z pomiarów
    wall_thickness: float = 0.004  # [m] ścianka zewnętrzna komory; PLACEHOLDER – do identyfikacji z pomiarów
    septum_thickness: float = 0.004  # [m] przegroda między komorami L i R; PLACEHOLDER – do identyfikacji z pomiarów
    # Długość komory = długość napędzanych segmentów MuJoCo (liczona w __post_init__).

    # ------------------------------------------------------------------ materiał (silikon)
    young_modulus: float = 3e5     # [Pa] silikon typu Dragon Skin / Ecoflex: rząd 1e5–1e6; PLACEHOLDER – do identyfikacji z pomiarów
    # Poisson 0.45, NIE 0.5: silikon jest prawie nieściśliwy, ale liniowe czworościany
    # przy ν → 0.5 „blokują się” (volumetric locking). Każdy element musi zachować
    # objętość, a 4 węzły dają za mało swobody, żeby jednocześnie zachować objętość
    # i się zginać, więc model staje się sztucznie sztywny.
    poisson_ratio: float = 0.45
    rho_silicone: float = 1100.0   # [kg/m³] jak rho_tail w MuJoCo; PLACEHOLDER – do identyfikacji z pomiarów

    # ------------------------------------------------------------------ numeryka
    dt: float = 0.002              # [s] krok czasu (etap 1: tylko ugięcie pod ciężarem)
    # Tłumienie Rayleigha w EulerImplicitSolver: C = α·M + β·K. Zastępuje tłumienie
    # materiałowe silikonu. Uwaga: niejawny Euler sam też tłumi (numerycznie, rośnie z dt).
    rayleigh_mass: float = 0.1       # α [1/s]; PLACEHOLDER – do identyfikacji z pomiarów
    rayleigh_stiffness: float = 0.01  # β [s]; PLACEHOLDER – do identyfikacji z pomiarów
    parallel_fem: bool = False     # ParallelTetrahedronFEMForceField (plugin MultiThreading)

    # Poziomy siatki do studium zbieżności: (rozmiar elementu przy powierzchniach,
    # rozmiar daleko od nich) [m]. Przy ściance 4 mm: coarse ≈ 1 element na grubość,
    # fine ≈ 2. Trzy elementy (~1.3 mm) dawałyby ~450k tetr – za dużo na to demo.
    mesh_levels: dict = field(default_factory=lambda: {
        "test": (0.006, 0.010),    # tylko do pytest (szybko, niedokładnie)
        "coarse": (0.004, 0.008),
        "medium": (0.003, 0.006),
        "fine": (0.002, 0.006),
    })
    mesh_dir: str = "meshes"       # względem katalogu SOFA/

    # pola wyliczane w __post_init__ (nie ustawiaj ręcznie)
    tail_length: float = field(init=False)
    chamber_length: float = field(init=False)

    def __post_init__(self):
        if self.environment not in ("air", "water"):
            raise ValueError('environment musi być "air" albo "water"')
        if not 1 <= self.n_actuated <= self.n_segments:
            raise ValueError("n_actuated musi być w zakresie 1..n_segments")
        if not 0.0 < self.poisson_ratio < 0.5:
            raise ValueError("poisson_ratio musi być w (0, 0.5) – patrz komentarz o lockingu")
        self.tail_length = self.n_segments * self.segment_length
        self.chamber_length = self.n_actuated * self.segment_length
        x_end = self.chamber_x_start + self.chamber_length
        if x_end >= self.tail_length:
            raise ValueError("komora wychodzi poza ogon")
        # Najwęższe miejsce komory (koniec): musi zostać miejsce na ściankę i przegrodę.
        s = self.scale_at(-x_end)
        if self.ry0 * s - self.wall_thickness <= self.septum_thickness / 2:
            raise ValueError("ścianka + przegroda nie mieszczą się w przekroju na końcu komory")
        if self.fin_root_overlap >= 2 * self.fin_semi_x:
            raise ValueError("fin_root_overlap większy niż płetwa")

    def scale_at(self, x: float) -> float:
        """Skala przekroju ogona w punkcie x (x ≤ 0): 1 na nasadzie, taper_last na końcu."""
        return 1.0 + (self.taper_last - 1.0) * (-x) / (self.n_segments * self.segment_length)

    @property
    def chamber_x_range(self) -> tuple:
        """(x_przód, x_tył) komory; x_przód > x_tył, bo ogon idzie w -X."""
        return (-self.chamber_x_start, -(self.chamber_x_start + self.chamber_length))

    @property
    def fin_center_x(self) -> float:
        """Środek płetwy: przednia krawędź wchodzi fin_root_overlap w koniec ogona."""
        return -self.tail_length - self.fin_semi_x + self.fin_root_overlap
