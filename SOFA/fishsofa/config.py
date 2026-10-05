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
    # Zakres roboczy przyrostu objętości jednej komory (etap 2: krzywa p–V, test
    # monotoniczności). 50 ml ≈ 55% objętości komory, ~16° zgięcia dla V4.
    dV_max: float = 50e-6          # [m³] PLACEHOLDER – do identyfikacji z pomiarów

    # ------------------------------------------------------------------ hydraulika antagonistyczna (etap 4)
    # Nazwy jak w MuJoCo/fishsim/config.py. Pompa przetacza ciecz z R do L: V_p > 0 to
    # wtłoczenie do L, ogon zgina się w −Y (w prawo) – tak jak +V_bias w MuJoCo (skręt
    # w prawo). Zadajemy OBJĘTOŚĆ V_ref(t), nie przepływ (uzasadnienie w hydraulics.py).
    tail_freq: float = 2.0          # [Hz] jak w MuJoCo
    # Świadome odstępstwo od MuJoCo (decyzja w etapie 4): komora SOFA ma 91 ml, a nie 30 ml
    # jak V0_chamber w MuJoCo, więc A_V = 8 ml z MuJoCo dałoby tu tylko ~±3° (README).
    # 17 ml to największa amplituda z zapasem przy V_prefill = 20 ml (patrz V_prefill).
    tail_volume_amp: float = 17e-6  # [m³] A_V; PLACEHOLDER – do identyfikacji z pomiarów
    tail_volume_bias: float = 0.0   # [m³] V_bias – stałe ugięcie ogona (skręt)
    K_v: float = 10.0               # [1/s] korekta błędu objętości; K_v·τ_pump < 0.5 (jak w MuJoCo)
    ramp_time: float = 1.0          # [s] miękki start amplitudy (po prefillu)
    # Pompa musi dać szczytowy przepływ 2π·f·A_V = 214 ml/s, inaczej się nasyca i amplituda
    # spada (lekcja etapu 6). MuJoCo ma 60 ml/s – za mało dla A_V = 17 ml.
    Q_max: float = 250e-6           # [m³/s] PLACEHOLDER – do identyfikacji z pomiarów
    tau_pump: float = 0.03          # [s] stała czasowa pompy, jak w MuJoCo; PLACEHOLDER – do identyfikacji z pomiarów
    p_max: float = 50e3             # [Pa] zawór przelewowy na |p_L − p_R|, jak w MuJoCo; PLACEHOLDER – do identyfikacji z pomiarów
    # Przepływ przez otwarty zawór: Q_valve = valve_conductance·(|Δp| − p_max). Wartość
    # dobrana tak, żeby zawór był „miękki” i stabilny przy jawnym odczycie ciśnienia
    # (10 kPa nadmiaru -> 10 ml/s). PLACEHOLDER – do identyfikacji z pomiarów
    valve_conductance: float = 1e-9  # [m³/(s·Pa)]
    # Wstępne napełnienie obu komór (rampa w prefill_time, przed rytmem). Komora nie może
    # zejść poniżej objętości spoczynkowej (kontakt ścianek nie jest modelowany), stąd
    # V_prefill > |V_bias| + A_V + prefill_margin. Górna granica z etapu 4: przy prefillu
    # > ~22 ml obie napełnione komory ściskają kręgosłup i ogon zaczyna się wyboczać
    # (README). 20 ml daje ~53 kPa ciśnienia wspólnego.
    V_prefill: float = 20e-6        # [m³] PLACEHOLDER – do identyfikacji z pomiarów
    prefill_time: float = 1.0       # [s]
    prefill_margin: float = 2e-6    # [m³]

    # ------------------------------------------------------------------ materiał (silikon)
    young_modulus: float = 3e5     # [Pa] silikon typu Dragon Skin / Ecoflex: rząd 1e5–1e6; PLACEHOLDER – do identyfikacji z pomiarów
    # Poisson 0.45, NIE 0.5: silikon jest prawie nieściśliwy, ale liniowe czworościany
    # przy ν → 0.5 „blokują się” (volumetric locking). Każdy element musi zachować
    # objętość, a 4 węzły dają za mało swobody, żeby jednocześnie zachować objętość
    # i się zginać, więc model staje się sztucznie sztywny.
    poisson_ratio: float = 0.45
    rho_silicone: float = 1100.0   # [kg/m³] jak rho_tail w MuJoCo; PLACEHOLDER – do identyfikacji z pomiarów

    # ------------------------------------------------------------------ warianty konstrukcji (etap 2)
    # „Kręgosłup”: przegroda między komorami na całej długości korpusu z materiału
    # sztywniejszego niż silikon (np. silikon twardszy albo z wkładką). Działa jak warstwa
    # nierozciągliwa w osi zginania: wydłużenie boku z ciśnieniem zamienia się w zgięcie.
    # Domyślna konstrukcja = wariant V4 z przeglądu (etap 2a, README): kręgosłup E×20
    # + włókna obwodowe. Bez nich ogon praktycznie się nie zgina (komora się wydyma).
    # Etap 1 (ugięcie pod ciężarem) był liczony jeszcze bez nich (V0).
    spine_E_factor: float = 20.0   # E_kręgosłupa / E_silikonu (1 = brak); PLACEHOLDER – do identyfikacji z pomiarów
    # Włókna obwodowe: oplot (nić, tkanina) na skórze ogona biegnący dookoła przekroju.
    # Nie pozwala ściance wydymać się na zewnątrz, a prawie nie usztywnia ogona osiowo
    # (zasada aktuatorów „fiber-reinforced”). Modelowane pierścieniami sprężyn (tylko
    # rozciąganie) na długości komór, tuż pod skórą (fishsofa/fibers.py).
    hoop_fibers: bool = True
    fiber_ring_spacing: float = 0.004   # [m] odstęp pierścieni wzdłuż ogona
    fiber_ring_points: int = 64         # punktów na pierścień
    fiber_inset: float = 0.0005         # [m] głębokość pod skórą (punkt musi leżeć w tetrze)
    # Sztywność membranowa oplotu w kierunku obwodowym = E_włókna · grubość warstwy [N/m]
    # (np. tkanina ~1 GPa × 0.2 mm = 2e5 N/m). PLACEHOLDER – do identyfikacji z pomiarów
    hoop_stiffness: float = 2e5
    include_weight: bool = True    # False = brak ciężaru (etap 2: krzywa p–V zależna tylko od materiału)

    # ------------------------------------------------------------------ numeryka
    dt: float = 0.002              # [s] krok czasu (etap 1: tylko ugięcie pod ciężarem)
    # Tłumienie Rayleigha w EulerImplicitSolver: C = α·M + β·K. Zastępuje tłumienie
    # materiałowe silikonu. Uwaga: niejawny Euler sam też tłumi (numerycznie, rośnie z dt).
    rayleigh_mass: float = 0.1       # α [1/s]; PLACEHOLDER – do identyfikacji z pomiarów
    rayleigh_stiffness: float = 0.01  # β [s]; PLACEHOLDER – do identyfikacji z pomiarów
    parallel_fem: bool = False     # ParallelTetrahedronFEMForceField (plugin MultiThreading)
    # Solver układu liniowego w każdym kroku niejawnego Eulera:
    #   "ldl" – bezpośredni rozkład LDLᵀ (dokładny, ale FEM korotacyjny zmienia macierz
    #           co krok, więc rozkład co krok – to dominuje czas, patrz README),
    #   "cg"  – gradient sprzężony na złożonej macierzy, startujący od rozwiązania
    #           z poprzedniego kroku (warm start),
    #   "warp" – PCG z prekondycjonerem: rozkład LDLᵀ raz w spoczynku, obracany co krok
    #           (patrz scene._add_warp_solver),
    #   "cholmod" – supernodalny rozkład Cholesky'ego z CHOLMOD (SuiteSparse), wtyczka
    #           SofaCHOLMOD zbudowana osobno dla v26.06 (README, „Instalacja”). Dokładny jak
    #           "ldl" (te same wyniki), ale gęste bloki liczy BLAS: 4.3× szybciej na coarse.
    # "warp" bez komór: 6–13× szybciej niż "ldl" przy tej samej trajektorii. Z komorą
    # SurfacePressureConstraint jest BŁĘDNY przy dużych odkształceniach (30 ml: ciśnienie
    # −25% względem "ldl", bo przybliżona podatność komory przesuwa równowagę), więc
    # scena z komorami zamienia "warp" na "ldl". Pomiary w README.
    linear_solver: str = "cholmod"
    warp_refactor_steps: int = 10**9  # co ile kroków ponowny rozkład (praktycznie: nigdy)
    cg_max_iterations: int = 1000
    cg_tolerance: float = 1e-12    # |r|²/|b|² (kwadrat residuum względnego!)
    cholmod_threads: int = 1       # wątki BLAS dla "cholmod"; 1–6 dają ten sam czas (README)

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
        if self.linear_solver not in ("ldl", "cg", "warp", "cholmod"):
            raise ValueError('linear_solver musi być "ldl", "cg", "warp" albo "cholmod"')
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
        if self.V_prefill <= abs(self.tail_volume_bias) + self.tail_volume_amp + self.prefill_margin:
            raise ValueError("V_prefill za małe: komora zeszłaby poniżej objętości spoczynkowej "
                             "(potrzeba V_prefill > |V_bias| + A_V + prefill_margin)")
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
