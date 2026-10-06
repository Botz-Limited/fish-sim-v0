# fish-sim-v0 – model systemowy robota-ryby w OpenModelica

Uproszczony, **edukacyjny i nieskalibrowany** model robota-ryby w Modelice: silnik DC → pompa → przewody → komory → ogon, plus balast i ruch do przodu. Specyfikacja: [`SPEC_fish_openmodelica_demo.md`](SPEC_fish_openmodelica_demo.md). Wszystkie parametry konstrukcyjne to placeholdery do identyfikacji.

## Stan prac

| Etap | Zakres | Status |
|---|---|---|
| 1 | Złącze hydrauliczne, `Pipe`, `Reservoir`, `VolumeFlowSource` + testy | gotowe |
| 2 | `Chamber` (krzywa p–V z tabeli lub CSV), `ReliefValve` + testy | gotowe |
| 3 | Silnik DC + `GearPump` → `HydraulicsStep` | – |
| 4 | `TailEquivalent` → `TailFlapping`, `FrequencySweep`, `ReliefValveDemo` | – |
| 5 | Bilans energii → `EnergyBudget` | – |
| 6 | Balast + pion → `DepthControl` | – |
| 7 | Surge → `SwimForward` | – |
| 8 | FMU + FMPy | – |

## Wersje

| Narzędzie | Wersja |
|---|---|
| OpenModelica (omc, OMEdit, OMSimulator) | 1.27.1 |
| Modelica Standard Library | 4.1.0 (jednostki: `Modelica.Units.SI`) |
| OMPython | 4.1.0 (klasa `ModelicaSystemOMC`; stara `ModelicaSystem` jest przestarzała) |
| FMPy | 0.3.32 |
| Python | 3.14 |

## Instalacja (Ubuntu)

```bash
setup/install_system.sh   # sudo: repozytorium apt OpenModelica, omc/OMEdit/OMSimulator, git, python3-venv
setup/install_user.sh     # bez sudo: .venv z requirements.txt + MSL 4.1.0 przez menedżer pakietów omc
```

## Uruchamianie

```bash
.venv/bin/python scripts/check_tests.py          # wszystkie modele z Tests/ i Examples/
.venv/bin/python scripts/check_tests.py Pipe     # tylko modele zawierające "Pipe" w nazwie
```

Każdy model jest sprawdzany (`checkModel`: liczba równań = liczba niewiadomych), kompilowany, symulowany i porównywany z wynikiem analitycznym. Modele są przetwarzane równolegle (osobny proces i osobna sesja omc na model). Wykresy trafiają do `results/tests/`.

Ustawienia wydajności są w `scripts/om_config.py`. Kompilacja kodu C idzie równolegle na wszystkich rdzeniach, a wygenerowany kod jest budowany z `-O2`, co daje ok. 8% szybszą symulację. `-O3`, `-march=native` i ccache nie dały mierzalnego zysku.

## Otwieranie w OMEdit

`File → Load Library…` (lub `Open Model/Library File`) → wskaż `FishRobot/package.mo`. W drzewie bibliotek rozwiń `FishRobot.Tests`, otwórz model i przełącz na widok *Diagram*. Złącza hydrauliczne są niebieskie: pełne kółko to `port_a`, puste to `port_b`.

## Hydraulika: dlaczego własny pakiet

`Modelica.Fluid` jest potężne, ale ciężkie dla małego układu z nieściśliwą wodą: wymaga modelu medium, bilansu entalpii i starannej inicjalizacji. Własne złącze `HydraulicPort` ma tylko dwie zmienne:

- `p` – ciśnienie (potencjał, w węźle równe we wszystkich portach),
- `flow V_flow` – przepływ objętościowy (w węźle sumuje się do zera).

Ich iloczyn `p·V_flow` to moc w watach, więc bilans energii wynika wprost z połączeń, tak jak `v·i` w elektryce. To najprostszy sposób, żeby zobaczyć, jak działają złącza akauzalne.

**Konwencja znaków:** `V_flow > 0` oznacza przepływ **do** komponentu przez dany port. W elementach dwuportowych `V_flow` (bez prefiksu portu) to przepływ od `port_a` do `port_b`, a `dp = port_a.p − port_b.p`.

## Co pokazują wykresy (etapy 1–2)

- **`pipe_laminar.png`** – spadek ciśnienia rośnie liniowo z przepływem, zgodnie z prawem Hagena–Poiseuille’a `Δp = 128·μ·l·Q / (π·d⁴)`. Liczba Reynoldsa pozostaje poniżej 2300, więc wzór laminarny obowiązuje. Zwróć uwagę na `d⁴`: dwa razy węższy przewód daje 16 razy większy opór.
- **`pipe_quadratic.png`** – przy przepływie sinusoidalnym krzywa Δp ma „spłaszczenia” przy zerze (dominuje część liniowa) i ostre szczyty (dominuje część kwadratowa). Dolny panel pokazuje błąd regularyzacji `Q·√(Q² + Q_small²)` zamiast `|Q|·Q`. Jest rzędu 10⁻⁴ Pa, a symulacja przechodzi przez zero bez żadnych zdarzeń.
- **`pipe_inertance.png`** – po skoku różnicy ciśnień przepływ nie zmienia się skokowo, bo słup wody ma masę. Narasta wykładniczo ze stałą czasową `τ = L/R ≈ 0,5 s`, dokładnie jak prąd w obwodzie RL.

- **`chamber_closed_loop.png`** – dwie komory połączone przewodem, na starcie 8 ml i 3 ml. Ciecz przelewa się do komory o niższym ciśnieniu, „przestrzeliwuje” przez bezwładność słupa wody i oscyluje z tłumieniem wokół 5,5 ml. To obwód RLC: komory to pojemność, słup cieczy to indukcyjność, opór rury to rezystancja. Dolny panel pokazuje, że suma objętości zmienia się tylko na poziomie 10⁻¹⁵ ml, czyli w granicach zaokrągleń komputera.
- **`relief_valve_limit.png`** – komora napełniana coraz szybciej. Nadciśnienie rośnie najpierw powoli (miękki silikon), potem stromo (silikon sztywnieje). Gdy przekroczy `p_set`, zawór przejmuje cały przepływ i ciśnienie zatrzymuje się na `p_set + dp_open`, czyli tam, gdzie zawór przepuszcza przepływ nominalny.

## Krzywa p–V komory z pliku

Placeholderową krzywą p–V można zastąpić danymi z demo SOFA albo z pomiaru bez zmiany kodu. Ustaw w `Chamber` parametr `tableOnFile = true`, a `fileName` wskaż przez `Modelica.Utilities.Files.loadResource("modelica://FishRobot/Resources/Data/<plik>.csv")`. Plik ma mieć jedną linię nagłówka i kolumny `V [m³], p − p_ambient [Pa]`, a krzywa musi być rosnąca. Wzór: `FishRobot/Resources/Data/chamber_pV_placeholder.csv` i test `ChamberTableFromFile`.

## Ograniczenia

Model jest jednowymiarowy, o skupionych parametrach. Parametry nie są zidentyfikowane. Pełna lista ograniczeń i plan kalibracji pojawią się wraz z kolejnymi etapami.
