# fish-sim-v0 / SOFA – miękki hydrauliczny ogon (SOFA + SoftRobots)

Edukacyjne demo FEM ogona robota-ryby. Specyfikacja: [SPEC_fish_sofa_demo.md](SPEC_fish_sofa_demo.md). **To nie jest skalibrowany model** – wszystkie parametry to placeholdery.

Stan: **etapy 0 (instalacja, API) i 1 (siatka, ugięcie pod ciężarem) zakończone.** Kolejne etapy: patrz spec, sekcja 8.

## Instalacja (Linux, sprawdzone na Fedorze 44)

| Co | Wersja / źródło |
|---|---|
| SOFA | **v26.06.00**, oficjalna binarka `SOFA_v26.06.00_Linux_Python3.12.zip` z [github.com/sofa-framework/sofa/releases](https://github.com/sofa-framework/sofa/releases) |
| SoftRobots, SoftRobots.Inverse, STLIB, SofaPython3 | **w oficjalnej binarce** (nie trzeba kompilować ani używać DefrostSofaBundle) |
| Licencje | SOFA: LGPL 2.1+ (`LICENSE-LGPL.md`); SoftRobots: **LGPL v3** (`plugins/SoftRobots/LICENSE`) |
| Python | **3.12** w środowisku conda `fishsofa` (systemowy Python 3.14 nie pasuje do binarki) |

```bash
# 1. SOFA poza repo (~230 MB do pobrania, ~800 MB po rozpakowaniu)
mkdir -p ~/sofa && cd ~/sofa
curl -LO https://github.com/sofa-framework/sofa/releases/download/v26.06.00/SOFA_v26.06.00_Linux_Python3.12.zip
unzip SOFA_v26.06.00_Linux_Python3.12.zip          # -> ~/sofa/SOFA_v26.06.00_Linux

# 2. Python 3.12 + zależności
conda create -n fishsofa python=3.12 numpy scipy pybind11 matplotlib pytest
conda run -n fishsofa pip install gmsh meshio

# 3. W każdej nowej powłoce (bash lub zsh), z katalogu repo:
source SOFA/scripts/env.sh
python SOFA/scripts/check_sofa.py           # kod 0 = wszystko jest
```

Inna lokalizacja SOFA: `SOFA_ROOT=/inna/sciezka source SOFA/scripts/env.sh`.

**Co trzeba było zrobić na Fedorze:** nic z `dnf`. Binarka jest budowana na Ubuntu, ale `ldd` pokazał tylko jeden brak: `libpython3.12.so.1.0`. Bierzemy go z condy. `env.sh` tworzy katalog `~/sofa/fishsofa-pylib/` z jednym dowiązaniem do tej biblioteki i dodaje go do `LD_LIBRARY_PATH`. Celowo nie dodajemy całego `$CONDA_PREFIX/lib`, bo wtedy `libstdc++` z condy przesłoniłaby systemową, co grozi błędami sterowników OpenGL w GUI. Odpowiednik ubuntowego `libopengl0` (`libglvnd-opengl`) był już zainstalowany.

## Uruchamianie

```bash
source SOFA/scripts/env.sh
python SOFA/scripts/check_sofa.py           # etap 0: nazwy komponentów i pól w tej wersji SOFA
python SOFA/scripts/probe_volume_growth.py  # etap 0: jak działa SurfacePressureConstraint (~2.5 min)
cd SOFA && pytest -q                        # testy (~25 s, gruba siatka "test" w katalogu tymczasowym)
python -m fishsofa.mesh_gen --level all     # etap 1: siatki do meshes/ (fine ~10 s)
python scripts/run_stage1.py                # etap 1: raport + wykres do results/ (~10 min, głównie fine)
scripts/run_gui.sh coarse                   # ogon w GUI; po Animate ugina się pod ciężarem
# GUI z przykładem SoftRobots (komora ciśnieniowa vs objętościowa):
$SOFA_ROOT/bin/runSofa -l SofaPython3 $SOFA_ROOT/plugins/SoftRobots/share/sofa/examples/SoftRobots/component/constraint/SurfacePressureConstraint/PressureVsVolumeGrowthControl.py
# to samo bez okna (np. 50 kroków):
$SOFA_ROOT/bin/runSofa -g batch -n 50 -l SofaPython3 <scena.py>
```

## Ustalenia z etapu 0

### Nazwy komponentów w SOFA v26.06 (`check_sofa.py`)

| Rola | Używamy | Uwagi |
|---|---|---|
| solver ograniczeń | `BlockGaussSeidelConstraintSolver` | `GenericConstraintSolver` **już nie istnieje**; jest też `NNCGConstraintSolver` |
| mocowanie | `FixedProjectiveConstraint` | `FixedConstraint` jeszcze działa (stara nazwa) |
| korekcja ograniczeń | `LinearSolverConstraintCorrection` | jest też `GenericConstraintCorrection` |
| solver liniowy | `SparseLDLSolver`, `template="CompressedRowSparseMatrixMat3x3d"` | bloki 3×3 są szybsze dla węzłów 3D (sugestia SOFA) |
| pozostałe | `FreeMotionAnimationLoop`, `EulerImplicitSolver`, `StaticSolver`, `TetrahedronFEMForceField`, `MeshMatrixMass`, `UniformMass`, `BoxROI`, `ConstantForceField`, `MeshVTKLoader`, `MeshGmshLoader`, `MeshSTLLoader`, `MeshOBJLoader`, `BarycentricMapping`, `SurfacePressureConstraint` | wszystkie są |

Pluginy: w Pythonie `SofaRuntime.importPlugin("Sofa.Component")` (meta-plugin ze wszystkimi standardowymi komponentami) + `"SoftRobots"`. W scenach: `RequiredPlugin` z polem **`pluginName`**, bo pole `name` jest przestarzałe.

### Jak działa `SurfacePressureConstraint` (`probe_volume_growth.py`)

Scena: pusty „królik” z przykładów SoftRobots, bez grawitacji.

1. **`valueType="volumeGrowth"`: `value` to przyrost CAŁKOWITY względem objętości początkowej** (`initialCavityVolume`), a nie przyrost na krok. Przy stałym `value = 40` zmierzone `cavityVolume − V0` = 40.000 od 0.25 s do 1.5 s. Zgadza się to z kodem SoftRobots (`dfree = V − V_initial`). Wniosek dla `hydraulics.py`: co krok zadajemy wprost `ΔV_L = V_prefill + V_p`, bez różniczkowania.
2. **Znak:** dodatnie `value` powiększa wnękę i daje dodatnie ciśnienie (przy siatce komory z przykładu; dla naszej siatki sprawdzi to test znaku w etapie 1–2, a w razie potrzeby jest pole `flipNormal`).
3. **Pole `pressure` to p·dt, a nie p.** Ten sam stan ustalony przy dt = 0.001 i 0.002 daje surowe `pressure` 2.2912 i 4.5824 (stosunek 2.000), a `pressure/dt` = 2291.2 w obu przypadkach. Powód: solver ograniczeń liczy **impuls** siły w kroku (λ = p·dt), nie siłę.
4. **W trybie `valueType="pressure"` wejście `value` też jest w jednostkach p·dt.** Zadanie `value = p` (bez ·dt) dało ciśnienie 1000× za duże przy dt = 1 ms i FEM wybuchł (NaN), nawet z rampą. `value = p·dt` odtwarza ten sam przyrost objętości (9.993 przy zadanym 10) przy obu dt.

Konsekwencje dla następnych etapów:
- `hydraulics.py` (zawór na Δp) i wszystkie wykresy ciśnienia muszą dzielić `pressure` przez `dt`,
- test „ten sam p → ugięcie ~1/E” (spec, sekcja 10) musi zadawać `value = p·dt`,
- w obu trybach `value` zmienia się rampą: przykład SoftRobots zadaje `volumeGrowth = 40` skokiem w pierwszym kroku i działa tylko dzięki dużemu tłumieniu.

Wydajność dla orientacji: królik z przykładu (dt = 1 ms) liczy się ~25 ms na krok na tej maszynie, ok. 40× wolniej niż czas rzeczywisty. SOFA sugeruje `ParallelTetrahedronFEMForceField` (plugin MultiThreading, maszyna ma 12 wątków) – do sprawdzenia w etapie 1.

### GUI

`runSofa` startuje pod Waylandem bez dodatkowych zmiennych. Domyślne GUI to **ImGui** (plugin SofaImGui). Przykład `PressureVsVolumeGrowthControl` działa: po **Animate** oba króliki się nadmuchują (sprawdzone ręcznie). Przy pierwszym uruchomieniu w logu pojawia się `[ERROR] [ImGuiGUIEngine] Cannot set window position/size from settings`. To tylko brak zapisanych ustawień okna, nieszkodliwe. Tryb `-g batch` działa (50 kroków przykładu w 5.9 s).

## Etap 1 – siatka ogona i ugięcie pod własnym ciężarem

### Geometria (`fishsofa/config.py`, `fishsofa/mesh_gen.py`)

Wymiary są przepisane z `MuJoCo/fishsim/config.py`; test `test_dimensions_match_mujoco` pilnuje zgodności. Korpus ma 0.20 m, przekrój eliptyczny 0.06 × 0.08 m na nasadzie, liniowo zwężający się do 0.4 na końcu. Płetwa to płytka 0.07 × 0.12 m o grubości 6 mm. Dwie komory leżą na długości 3 napędzanych segmentów MuJoCo (0.12 m), ze ścianką i przegrodą po 4 mm.

Jedno świadome odstępstwo: korzeń płetwy wchodzi 15 mm w koniec ogona, zamiast 2 mm jak w MuJoCo. W MuJoCo płetwa jest przyspawana sztywno. W FEM połączenie przez 2 mm byłoby przewężeniem ~6 × 40 mm, które działałoby jak zawias.

Jak powstaje siatka:
1. gmsh siatkuje **połowę** ogona (y ≥ 0) z jedną komorą.
2. Drugą połowę dostajemy przez **odbicie lustrzane**. Dzięki temu siatka jest dokładnie symetryczna, a test symetrii L/R w etapie 3 sprawdzi kod, nie przypadek w siatkowaniu.
3. Trójkąty wnęk są rozpoznawane geometrycznie po środku trójkąta, wewnątrz obrysu wnęki powiększonego o pół ścianki. Pierwsza wersja rozpoznawała je po bounding boxach gmsh, ale OpenCASCADE podaje dla powierzchni B-spline zbyt luźne bboxy i część wnęki trafiała do „skóry”. Wyłapał to test zamkniętości powierzchni.
4. Orientacja: skóra ma normalne na zewnątrz, wnęki na zewnątrz wnęki (konwencja SoftRobots z etapu 0).

Siatka jest zapisywana jako klasyczny VTK 4.2. meshio zapisuje VTK 5.1, na którym `MeshVTKLoader` z SOFA v26.06 kończy się segfaultem.

### Poziomy siatki (`results/s1_mesh_report.txt`)

| poziom | h przy powierzchni | czworościany | elem. na ściankę 4 mm | ugięcie końcówki Δz | statyka | dynamika |
|---|---|---|---|---|---|---|
| coarse | 4 mm | 28 112 | ~0.9 | −40.52 mm | 6 s | 0.77 s/krok |
| medium | 3 mm | 51 818 | ~1.1 | −40.73 mm | 17 s | 2.3 s/krok |
| fine | 2 mm | 142 096 | ~1.7 | −41.17 mm | 176 s | 19 s/krok |

Wszystkie poziomy: zero tetr o objętości ≤ 0, SICN (jakość czworościanu, 1 = idealny) ≥ 0.06, 1. percentyl ≈ 0.35–0.40, powierzchnie zamknięte, węzły symetryczne. „Elementy na ściankę” to grubość podzielona przez średnią krawędź tetr przy wnęce, czyli przybliżenie, nie liczenie warstw. Spec chciał ≥ 3; to by wymagało ~450k tetr. Decyzja: studium zbieżności (patrz spec, sekcja 4).

**Komory są duże:** 91.6 ml każda, przy 245 ml silikonu. Przy ściance 4 mm w przekroju 6 × 8 cm ogon jest w większości pusty. Woda w komorach (183 g) to ~40% masy ogona. W demo MuJoCo `V0_chamber` = 30 ml (też placeholder). Ten rozjazd trzeba rozstrzygnąć przy eksporcie PRBM (etap 7) albo przez grubsze ścianki.

### Masa i ciężar (`fishsofa/masses.py`)

Grawitacja SOFA jest wyłączona. Masa (silikon + woda z komór, przypisana do tetr przy ściankach wnęk) idzie do `MeshMatrixMass` jako gęstość na element. Ciężar idzie przez `ConstantForceField` na węzłach. Powód: w wodzie woda w komorach ma bezwładność, ale nie ma ciężaru (wypór = ciężar), a jeden wektor grawitacji SOFA tego nie rozróżni. W trybie `environment="water"` silikon ma ciężar pozorny `g·(1 − ρ_w/ρ_s)`.

### Co pokazuje `results/s1_sag.png`

- **Lewy wykres:** statyczne ugięcie końcówki pod ciężarem na trzech siatkach. Różnica coarse → fine to tylko 1.6% (−40.5 → −41.2 mm). Zginanie całego ogona pod ciężarem przenosi głównie skóra i rdzeń, a nie cienkie ścianki komór, więc gruba siatka wystarcza. To **nie** przesądza o etapie 2: tam ciśnienie odkształca właśnie ścianki, więc tam zbieżność trzeba zmierzyć osobno.
- **Prawy wykres:** ogon „puszczony” w t = 0 (ciężar włączony skokowo) na siatce coarse. Oscyluje wokół równowagi statycznej (linia przerywana) z okresem ~0.33 s, czyli pierwsza częstość własna w powietrzu to ~3 Hz, a drgania gasną przez tłumienie Rayleigha i numeryczne. Pierwsze wychylenie (−68 mm) jest ~1.7× większe od statycznego (dla nietłumionego układu przy skoku obciążenia byłoby 2×).

### GUI

`scripts/run_gui.sh coarse` otwiera ogon. Po **Animate** ogon opada i się kołysze (sprawdzone ręcznie). Ruch jest wolny, bo jeden krok to ~0.8 s – patrz „Otwarty problem” niżej.

### Statyka w SOFA v26.06

`StaticSolver` wymaga osobnego komponentu `NewtonRaphsonSolver` (od v25.12 parametry Newtona przeniesiono tam) i **nie działa z `FreeMotionAnimationLoop`** (ogon się nie rusza), więc statyka używa `DefaultAnimationLoop`. Pierwsza iteracja Newtona przestrzeliwuje (ostrzeżenie „Line search failed at Newton iteration 0”), kolejne zbiegają (residuum 42 → 0.13 → 0.006 → …). Drugi krok statyki nic już nie zmienia (test).

### Otwarty problem: wydajność dynamiki

Dynamika jest bardzo wolna: **coarse 383× wolniej niż czas rzeczywisty** (0.77 s na krok przy dt = 2 ms). Prawie cały czas zajmuje pełny rozkład LDLᵀ macierzy w każdym kroku, bo korotacyjny FEM zmienia macierz sztywności co krok. Sprawdzone bez sukcesu (na siatce test, 12k tetr, ~200 ms/krok):
- metody numeracji Metis, AMD i COLAMD (domyślna jest już dobra; bez numeracji jest 100× wolniej),
- wielowątkowość (`nbThreads`, `ParallelTetrahedronFEMForceField`) – bez zysku,
- `AsyncSparseLDLSolver` i PCG + `WarpPreconditioner` + Async (oba ~10 ms/krok, ale symulacja wybucha) – przyczyna niezdiagnozowana, nie maskowana,
- PCG + `WarpPreconditioner` + zwykły LDL – bez zysku (rozkład dalej co krok).

Dla etapów 4–6 (dziesiątki tysięcy kroków) trzeba to rozwiązać przed etapem 4: większy `dt` (niejawny Euler to znosi, a 3 Hz wymaga ~6 ms), poprawna konfiguracja warp/async albo grubsza siatka dla dynamiki.
