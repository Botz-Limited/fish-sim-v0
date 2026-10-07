"""Wspólne parametry demo FSI (geometria, materiał, woda, siatki).

UWAGA: wszystkie liczby fizyczne poniżej to PLACEHOLDER – do identyfikacji
z pomiarów. Nie są skalibrowane względem żadnej realnej ryby ani prototypu.

Układ współrzędnych (widok z góry, przekrój 2D):
    x – oś ryby, od nasady ogona (x = 0) w stronę końcówki (x = L),
        napływ wody płynie w +x (ryba "płynie" w -x),
    y – w bok (lewa strona ryby y > 0, prawa y < 0),
    z – kierunek "rozpiętości"; model 2D ma grubość DEPTH (jedna warstwa).
Siły raportujemy na jednostkę rozpiętości [N/m], bo DEPTH = 1 m (jak w
tutorialu perpendicular-flap).
"""

# --- Geometria ogona -------------------------------------------------------
L = 0.15            # długość ogona [m]                 PLACEHOLDER – do identyfikacji z pomiarów
T_ROOT = 0.030      # grubość przy nasadzie [m]          PLACEHOLDER – do identyfikacji z pomiarów
T_TIP = 0.010       # grubość na końcówce [m]            PLACEHOLDER – do identyfikacji z pomiarów

# Komory (lewa/prawa), rozdzielone ścianką środkową
CH_X0 = 0.010       # początek komory (od nasady) [m]   PLACEHOLDER – do identyfikacji z pomiarów
CH_X1 = 0.110       # koniec komory [m]                  PLACEHOLDER – do identyfikacji z pomiarów
W_OUT = 0.003       # grubość ścianki zewnętrznej [m]    PLACEHOLDER – do identyfikacji z pomiarów
W_MID = 0.003       # grubość ścianki środkowej [m]      PLACEHOLDER – do identyfikacji z pomiarów
# Komora podzielona żebrami na krótkie cele (styl PneuNet). Jedna długa komora
# w 2D "balonuje": ścianka zewnętrzna wygina się jak membrana i ogon się
# skraca zamiast zginać (patrz NOTES.md, etap 1). Cele są połączone kanałem
# poza płaszczyzną przekroju, więc mają to samo ciśnienie.
N_CELLS = 10        # liczba cel w komorze [-]           PLACEHOLDER – do identyfikacji z pomiarów
RIB = 0.0015        # grubość żebra między celami [m]    PLACEHOLDER – do identyfikacji z pomiarów

# --- Sztywna "głowa" (półelipsa przed nasadą) -------------------------------
HEAD_A = 0.060      # półoś w kierunku x [m]             PLACEHOLDER – do identyfikacji z pomiarów
HEAD_B = T_ROOT / 2 # półoś w kierunku y = pół grubości nasady (gładkie przejście)

# --- Domena płynu (wielokrotności L) ----------------------------------------
UPSTREAM = 3.0 * L    # od czubka głowy do wlotu        PLACEHOLDER – sprawdzić wpływ granic
DOWNSTREAM = 8.0 * L  # od końcówki ogona do wylotu     PLACEHOLDER – sprawdzić wpływ granic
SIDE = 3.0 * L        # od osi do ścian bocznych        PLACEHOLDER – sprawdzić wpływ granic

DEPTH = 1.0         # grubość modelu 2D w z [m] (jak w tutorialu: siły w N/m)

# --- Materiał ogona (silikon) -----------------------------------------------
E_SOLID = 3.0e5     # moduł Younga [Pa] (zakres 1e5–1e6) PLACEHOLDER – do identyfikacji z pomiarów
NU_SOLID = 0.45     # współczynnik Poissona [-]          PLACEHOLDER – do identyfikacji z pomiarów
RHO_SOLID = 1070.0  # gęstość [kg/m^3]                   PLACEHOLDER – do identyfikacji z pomiarów

# --- Woda --------------------------------------------------------------------
RHO_FLUID = 1000.0  # gęstość [kg/m^3]
NU_FLUID = 1.0e-6   # lepkość kinematyczna [m^2/s]

# --- Siatki ------------------------------------------------------------------
SOLID_H = 1.0e-3    # rozmiar elementu ciała stałego [m]; zbieżność: 0.5/0.75/1.0 mm -> ugięcie
                    # przy 20 kPa 24.31/24.20/24.29 mm (< 0.5%), więc 1 mm wystarcza


def thickness(x):
    """Grubość ogona w punkcie x (liniowe zwężenie)."""
    return T_ROOT + (T_TIP - T_ROOT) * x / L
