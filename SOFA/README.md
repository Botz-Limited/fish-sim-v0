# fish-sim-v0 / SOFA – miękki hydrauliczny ogon (SOFA + SoftRobots)

Edukacyjne demo FEM ogona robota-ryby. Specyfikacja: [SPEC_fish_sofa_demo.md](SPEC_fish_sofa_demo.md). **To nie jest skalibrowany model** – wszystkie parametry to placeholdery.

Stan: **etapy 0 (instalacja, API), 1 (siatka, ugięcie pod ciężarem), 2 (komora L quasi-statycznie), 3 (symetria L/R), 4 (machanie w powietrzu), 5 (woda) i 6 (przeglądy) zakończone; solver CHOLMOD (4–15× szybciej) dodany po etapie 2, OpenBLAS z condy i równoległe przeglądy po etapie 4.** Etap 7 (opcjonalny eksport PRBM do MuJoCo) świadomie pominięty (decyzja 6.10.2026); opis metody: spec, sekcja 8.

## Instalacja (Linux x86_64, sprawdzone na Fedorze 44 i EndeavourOS/Arch)

**Na nowym komputerze wystarczy jedna komenda** (potrzebna wcześniej: conda, np. [Miniforge](https://github.com/conda-forge/miniforge)):

```bash
git clone <repo> && cd fish-sim-v0
SOFA/scripts/setup.sh --install-deps     # ~2 min + pobranie 230 MB; brakujące pakiety przez sudo dnf/apt
source SOFA/scripts/env.sh               # w każdej nowej powłoce (bash lub zsh)
SOFA/scripts/run_gui.sh                  # GUI: ogon macha (Animate)
```

`setup.sh` pomija kroki już zrobione. Kolejno:
1. Sprawdza zależności systemowe: kompilator, cmake, ninja, SuiteSparse/CHOLMOD, Eigen oraz biblioteki OpenGL/X11 dla gmsh i GUI. Bez `--install-deps` tylko wypisuje komendę `dnf` albo `apt`.
2. Pobiera binarkę SOFA v26.06.00 do `~/sofa` i sprawdza sumę SHA-256.
3. Tworzy środowisko conda `fishsofa` z `environment.yml`.
4. Buduje wtyczkę CHOLMOD.
5. Uruchamia `check_sofa.py` i `pytest`.

Inny katalog niż `~/sofa`: `FISHSOFA_HOME=/sciezka` dla `setup.sh` **i** `env.sh`. Test czystej instalacji (5.10.2026, osobny katalog i osobne środowisko conda): 1 min 43 s, 33/33 testów. EndeavourOS (6.10.2026, od zera, z Miniforge): 1 min 58 s, 33/33.

| Co | Wersja / źródło |
|---|---|
| SOFA | **v26.06.00**, oficjalna binarka `SOFA_v26.06.00_Linux_Python3.12.zip` z [github.com/sofa-framework/sofa/releases](https://github.com/sofa-framework/sofa/releases), SHA-256 w `setup.sh` |
| SoftRobots, SoftRobots.Inverse, STLIB, SofaPython3 | **w oficjalnej binarce** (nie trzeba kompilować ani używać DefrostSofaBundle) |
| SofaCHOLMOD | źródła w repo: `third_party/SofaCHOLMOD`, z SOFA master, commit `6c3e21f`; opis w `VENDORED.md`. Budowane dla v26.06 przez `scripts/build_cholmod_plugin.sh` (solver `"cholmod"`, domyślny) |
| Licencje | SOFA i SofaCHOLMOD: LGPL 2.1+ (`LICENSE-LGPL.md`); SoftRobots: **LGPL v3** (`plugins/SoftRobots/LICENSE`) |
| Python | **3.12** w środowisku conda `fishsofa`; pakiety przypięte w `requirements.txt` (systemowy Python 3.14 nie pasuje do binarki) |
| Siatki | generowane przy pierwszym użyciu do `SOFA/meshes/` (gmsh, deterministycznie; nie ma ich w repo) |

**Dlaczego tak:**
- Binarka SOFA jest budowana na Ubuntu. Na Fedorze `ldd` pokazał tylko jeden brak: `libpython3.12.so.1.0`, który bierzemy z condy.
  - `env.sh` tworzy katalog `~/sofa/fishsofa-pylib/` z jednym dowiązaniem do tej biblioteki i dodaje go do `LD_LIBRARY_PATH`.
  - Celowo nie dodajemy całego `$CONDA_PREFIX/lib`, bo wtedy `libstdc++` z condy przesłoniłaby systemową, co grozi błędami sterowników OpenGL w GUI.
- Pakiety systemowe są potrzebne tylko do wtyczki CHOLMOD (kompilator i nagłówki, w tym Boost: wymagają go configi CMake binarki SOFA, a binarka go nie zawiera) oraz do bibliotek graficznych, których używa gmsh z pip.

## Uruchamianie

```bash
source SOFA/scripts/env.sh
python SOFA/scripts/check_sofa.py           # etap 0: nazwy komponentów i pól w tej wersji SOFA
python SOFA/scripts/probe_volume_growth.py  # etap 0: jak działa SurfacePressureConstraint (~2.5 min)
cd SOFA && pytest -q                        # testy (~3 min, gruba siatka "test" w katalogu tymczasowym)
python -m fishsofa.mesh_gen --level all     # etap 1: siatki do meshes/ (fine ~10 s)
python scripts/run_stage1.py                # etap 1: raport + wykres do results/ (~10 min, głównie fine)
python scripts/run_stage2_variants.py       # etap 2a: warianty konstrukcji (~10 min)
python scripts/run_stage2.py                # etap 2: krzywa p–V i kąt, 3 siatki (~25 min)
python scripts/run_stage3.py                # etap 3: symetria L/R (~3 min)
python scripts/run_stage4.py                # etap 4: machanie w powietrzu (~25 min)
python scripts/run_stage5.py                # etap 5: woda vs powietrze (3 symulacje naraz, ~30 min)
python scripts/run_stage6.py                # etap 6: przeglądy f i E (19 symulacji, ~1 h na 12 wątkach)
FISHSOFA_ENV=water scripts/run_gui.sh       # GUI: ogon macha w wodzie
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

### Wydajność dynamiki: solver „warp” (przed etapem 2; ograniczenie z komorami niżej)

Domyślny `SparseLDLSolver` robi pełny rozkład LDLᵀ macierzy w każdym kroku, bo korotacyjny FEM zmienia macierz sztywności co krok. To dawało 383× wolniej niż czas rzeczywisty na coarse.

**Rozwiązanie** (z dokumentacji i kodu SOFA na GitHubie, `fishsofa/scene.py:_add_warp_solver`, `linear_solver="warp"`, domyślne):
1. Rozkład LDLᵀ liczony **raz, w stanie spoczynku**: `RotationMatrixSystem` z bardzo dużym `assemblingRate`.
2. W każdym kroku tylko „obracany” o aktualne obroty elementów (`WarpPreconditioner`, `rotationFinder=@fem`). Dla korotacyjnego FEM sztywność odkształconego ogona ≈ R·K₀·Rᵀ.
3. Obrócony rozkład jest prekondycjonerem dla PCG (`PCGLinearSolver` + `PreconditionedMatrixFreeSystem`), który kilkoma iteracjami doprowadza wynik do dokładnego.
4. Korekcja ograniczeń komór linkuje prekondycjoner (`LinearSolverConstraintCorrection linearSolver=@warp`), bo sam PCG nie składa macierzy.

| siatka | LDL (dt 2 ms) | warp (dt 2 ms) | przyspieszenie |
|---|---|---|---|
| test (12k tetr) | 196 ms/krok | 31 ms/krok | 6.2× |
| coarse (28k) | 726 ms/krok | 84 ms/krok | 8.6× |
| medium (52k) | 2306 ms/krok | 260 ms/krok | 8.9× |
| fine (142k) | 19 337 ms/krok | 1510 ms/krok | 12.8× |

**Dokładność:** trajektoria końcówki na coarse przez 0.4 s jest identyczna z LDL (różnica < 0.001 mm; test `test_warp_solver_matches_ldl`).

**Ale z komorą warp jest błędny** (sprawdzone w planie etapu 2, siatka test, 30 ml w komorze L, stan ustalony):

| solver | ciśnienie |
|---|---|
| LDL, wolna rampa, dt 2 ms | 1950.4 Pa |
| LDL, pseudo-statyka dt 10 / 50 ms | 1950.4 Pa |
| warp, dt 2 ms | **1471 Pa (−25%)** |

Przy 5 ml różnica była 1.7%, więc błąd rośnie z odkształceniem. Przyczyna: korekcja ograniczeń używa przybliżonej podatności J·A_warp⁻¹·Jᵀ, więc rozkład siły ciśnienia na węzły jest zły i równowaga się przesuwa. Dlatego **domyślny solver to znowu `"ldl"`**, a scena z komorami wymusza LDL (test `test_warp_is_replaced_by_ldl_with_chambers`). Warp jest użyteczny tylko bez komór. Dla dynamiki z komorami rozwiązaniem jest CHOLMOD (sekcja niżej), który od tej pory jest domyślnym solverem.

Trzy błędy wcześniejszych prób (etap 1), dla przyszłych czytelników:
- `assemblingRate=15` (jak w przykładzie SOFA): macierz składana w stanie odkształconym, a obrót z `TetrahedronFEMForceField` (liczony względem spoczynku) nakłada się drugi raz, więc symulacja wybucha.
- Brak jawnego linku `EulerImplicitSolver linearSolver=@linsolver`: integrator brał pierwszy solver w węźle (LDL z prekondycjonera) i PCG nie był używany.
- Linki `@…` w SofaPython3 muszą wskazywać obiekty, które już istnieją, więc kolejność tworzenia ma znaczenie.

**Większy krok czasu** (warp, coarse): dt 5 ms daje 2× krótszy czas całości, ale różnica trajektorii to 3.4 mm (~5% amplitudy). Przy dt 10 ms jest 3.5× szybciej, ale z różnicą 7.8 mm (~11%). Niejawny Euler przy dużym kroku tłumi ruch numerycznie. Domyślnie zostaje 2 ms; większy krok tylko świadomie, z podanym błędem.

**Sprawdzone bez zysku:** numeracja Metis/AMD/COLAMD (domyślna jest dobra), `nbThreads`, `ParallelTetrahedronFEMForceField` (składanie macierzy zostaje sekwencyjne), CG na złożonej macierzy (~10%), sam `AsyncSparseLDLSolver` (niestabilny, co dokumentacja SOFA przyznaje).

**Niewykorzystane opcje:**
- Redukcja rzędu modelu (plugin ModelOrderReduction, w binarce) daje nawet ~50×, ale wymaga treningu offline i działa tylko w wytrenowanym zakresie. To kandydat dopiero na etap 6.

### Wydajność: CHOLMOD (po etapie 2, domyślny solver)

`linear_solver="cholmod"`: `EigenCholmodSupernodalLLT` z wtyczki SofaCHOLMOD. To ten sam dokładny rozkład macierzy co LDL, tylko supernodalny: gęste bloki liczy zoptymalizowany BLAS (OpenBLAS przez FlexiBLAS). W przeciwieństwie do warp **działa z komorami**, bo korekcja ograniczeń dostaje dokładny rozkład. Pomiar: dt 2 ms, z komorą L i włóknami, 1 wątek BLAS (4 i 6 wątków dają ten sam czas):

| siatka | LDL | CHOLMOD | przyspieszenie | ciśnienie LDL = CHOLMOD |
|---|---|---|---|---|
| coarse | 871 ms/krok | 203 ms/krok | 4.3× | tak (10588.97 Pa) |
| medium | 2447 ms/krok | 471 ms/krok | 5.2× | tak (14642.81 Pa) |
| fine | 19785 ms/krok | 1324 ms/krok | **15×** | tak (13071.41 Pa) |

Zgodność z LDL pilnuje test `test_cholmod_matches_ldl_with_chamber`. Testy (25) trwają teraz ~63 s zamiast ~82 s.

**Dlaczego wtyczka z master na v26.06, a nie cała SOFA master.** Zbudowałem SOFA master (v26.12-dev, commit `6c3e21f`, 5.10.2026) razem z SofaPython3, SoftRobots i STLIB w wersjach master. Działa, ale ma **błąd w połączeniu komory ze sztywnymi włóknami**:
- z włóknami tylko na rozciąganie (V4) ogon nie dochodzi do równowagi, tylko stale drga (ciśnienie ±0.5%), a średnie ciśnienie jest o ~9% niższe niż w v26.06 (siatka test, 8 ml: 2790 zamiast 3056 Pa);
- z włóknami działającymi też na ściskanie symulacja się rozbiega (v26.06: stabilnie, 3633 Pa);
- bez włókien obie wersje dają identyczne ciśnienie (1321.52 Pa). Siły też są identyczne (to samo obciążenie zadane siłami węzłowymi daje ten sam kąt), a włókna są poprawnie zmapowane (różnica pozycji < 1e-16 m). Minimalna scena ze sztywną zmapowaną sprężyną bez komory działa w obu wersjach.

v26.06 dochodzi do spoczynku (prędkość 1e-13 m/s), a przy tych samych siłach to jest prawdziwa równowaga. Dlatego zostajemy na v26.06. Prawdopodobna przyczyna to przejście ograniczeń z impulsów na siły (SOFA PR #6117), ale tego nie potwierdziłem. Inne zmiany w master, gdyby kiedyś przechodzić: pole `pressure` i wejście trybu ciśnienia `SurfacePressureConstraint` są w Pa, a nie p·dt (sonda `probe_volume_growth.py` rozpoznaje obie konwencje), `NewtonRaphsonSolver` jest usunięty (statyka: `StaticEquilibriumIntegrationScheme` z `alwaysAdvanceNewton=True`), integratory mają nowe nazwy (`EulerImplicitIntegrationScheme`, moduł `Sofa.Component.IntegrationScheme.Backward`).

**Jak zbudowana jest wtyczka** (`scripts/build_cholmod_plugin.sh`): źródła samej wtyczki z master (skopiowane do `third_party/SofaCHOLMOD`, bo master bywa przepisywany), skompilowane na nagłówkach binarki v26.06 z dwiema poprawkami. (1) Nowszy `EigenSolverFactory.h`, bo wtyczka używa szablonu `registerProxyType`, który doszedł po v26.06. To czysty dodatek w nagłówku, bez zmiany układu klasy, więc SOFA nie trzeba przebudowywać. (2) `FindCHOLMOD.cmake` bez configu CMake z SuiteSparse, bo config z Fedory odwołuje się do nieistniejących plików `*_static.cmake`. `env.sh` dopisuje katalog wtyczki do `SOFA_PLUGIN_PATH`; tak samo widzi ją `runSofa`.

### Wydajność: OpenBLAS z condy i równoległe przeglądy (6.10.2026, EndeavourOS)

**Profil kroku** (machanie, coarse, CHOLMOD, `py-spy --native`): 45% składanie macierzy układu (w tym FEM 34%), 30% rozkład CHOLMOD, 8% analiza symboliczna wzorca macierzy, 6% solver ograniczeń. Wszystko na jednym rdzeniu.

**1. BLAS: 2.2× szybciej na Archu.** CHOLMOD supernodalny liczy gęste bloki w BLAS. Na Fedorze BLAS to OpenBLAS (przez FlexiBLAS), a na Archu systemowy `libblas.so.3` to wzorcowy, nieoptymalizowany BLAS z netlib. Tam krok trwał 470 ms zamiast ~200 ms. Teraz OpenBLAS przychodzi z condy (`environment.yml`: `libblas=*=*openblas`), a `env.sh` dowiązuje go w katalogu `fishsofa-pylib` (tak jak libpython), niezależnie od systemu: **470 → 217 ms/krok**, wynik identyczny co do ostatniej cyfry.

**2. Analiza symboliczna co krok – sprawdzone, bez zysku.** SOFA wyrzuca z macierzy dokładne zera, a włókna `elongationOnly` w stanie luźnym mają zerową sztywność, więc wzorzec macierzy zmienia się i CHOLMOD powtarza analizę. Spróbowałem łatki we wtyczce (analiza tylko, gdy nowy wzorzec nie jest podzbiorem poprzedniego). Pomiar: analiza powtarza się tylko w pierwszych ~300 krokach (prefill, gdy kolejne włókna napinają się pierwszy raz), potem już nigdy, także bez łatki. W ustalonym ruchu oba warianty dają 204–206 ms/krok, więc łatkę wycofałem (wtyczka zostaje bez zmian).

**3. Jedna symulacja = jeden rdzeń, więc przeglądy liczymy równolegle.** Składanie macierzy w SOFA jest sekwencyjne (`ParallelTetrahedronFEMForceField` tego nie zmienia), bloki CHOLMOD są za małe na wiele wątków BLAS, a kolejne kroki czasu zależą od poprzednich. Dlatego `top` pokazuje ~1/12 procesora na symulację. Za to punkty przeglądów (etapy 5–6) są niezależne: `fishsofa/parallel.py` liczy je w osobnych procesach (do 10 naraz na 12 wątkach, ~0.5 GB RAM każdy; `FISHSOFA_WORKERS` zmienia limit). `env.sh` ustawia `OPENBLAS_NUM_THREADS=1`, żeby procesy nie walczyły o rdzenie.

Pozostałe rezerwy, nieużyte: redukcja rzędu modelu (ModelOrderReduction, wymaga treningu), elementy wyższego rzędu (mniej węzłów przy tej samej dokładności ciśnienia, ale SOFA ich nie ma dla korotacyjnego FEM z komorami), własne równoległe składanie macierzy FEM (zmiana w C++ SOFA).

## Etap 2a – dlaczego ogon się nie zginał i co pomogło

**Problem:** przy geometrii z etapu 1 (V0: ścianki 4 mm, jednorodny silikon) 72 ml w komorze L zgina ogon tylko o 1.3°. Ciecz idzie w wybrzuszanie ścianki zewnętrznej (jak balon) i w uginanie przegrody w stronę komory R, a nie w wydłużanie lewego boku ogona. Dopiero wydłużenie jednego boku daje zgięcie.

**Przegląd wariantów** (`scripts/run_stage2_variants.py`, coarse, quasi-statycznie, komora R odpowietrzona, bez ciężaru; `results/s2_variants.png`, `.csv`):

| wariant | max \|θ\| (przy ΔV) | p przy max | 15° przy |
|---|---|---|---|
| V0 obecny | 1.3° (72.5 ml) | 7.2 kPa | – |
| V1 kręgosłup E×20 | 2.8° (72.5 ml) | 13.4 kPa | – |
| V2 ścianka 8 mm | 0.6° (47.5 ml) | 9.1 kPa | – |
| V3 włókna obwodowe | 9.0° (72.5 ml) | 10.4 kPa | – |
| **V4 kręgosłup + włókna** | **31° (72.5 ml)** | 33.8 kPa | **47.0 ml, 17.5 kPa** |

Co pokazuje wykres:
- Każdy element osobno daje mało. Włókna obwodowe nie pozwalają ściance się wybrzuszać, a kręgosłup (przegroda E×20 na całej długości) działa jak nierozciągliwa warstwa w osi zginania. Dopiero razem zamieniają wtłoczoną objętość w wydłużenie boku, czyli w zgięcie.
- Grubsza ścianka **pogarsza** sprawę: komora jest mniejsza, a ogon sztywniejszy.
- To ta sama zasada, której używają prawdziwe miękkie aktuatory: oplot włóknem i warstwa ograniczająca odkształcenie (strain-limiting layer).

**Wybór:** V4. Kryterium (15° przy p ≤ 50 kPa i ΔV ≤ 50% objętości komory) V4 przekracza o włos: 51.4% objętości przy 17.5 kPa. Decyzja użytkownika: V4 bez zmian, bo ciśnienie ma duży zapas, a przekroczenie mieści się w niepewności siatki coarse. V4 jest teraz domyślną konstrukcją w `config.py`. Etap 1 był liczony jeszcze dla V0.

**Jak to jest modelowane:**
- **Kręgosłup:** tetry ze środkiem w |y| ≤ septum/2 dostają E×20 (`spine_E_factor`, PLACEHOLDER). Przy ~1 elemencie na grubość przegrody to przybliżenie; raport siatki podaje objętość regionu względem nominalnej.
- **Włókna:** pierścienie punktów co 4 mm na długości komór, 0.5 mm pod skórą, połączone sprężynami pracującymi tylko na rozciąganie (`StiffSpringForceField elongationOnly`). Do FEM są przyczepione przez `BarycentricMapping`. Sztywność odpowiada membranie K = 2·10⁵ N/m (np. tkanina ~1 GPa × 0.2 mm, PLACEHOLDER). W symulacji nić wydłuża się < 0.15%.
- Dwa błędy złapane po drodze: `elongationOnly=True` jest w SOFA v26.06 po cichu ignorowane, bo to lista z jedną wartością na sprężynę, a SOFA czyta `"1 1 1 …"` (test `test_hoop_fibers_work_in_tension_only`). Do tego po zmianie domyślnego configu na V4 wariant „V0 = {}” liczył się jako V4, więc teraz każdy wariant ustawia wszystkie przełączniki jawnie.
- Pierwsza wersja włókien kładła sprężyny na krawędziach siatki skóry. Siatka z loftu nie ma jednak krawędzi obwodowych (są tylko osiowe i ukośne 45–72°), więc oplotu w praktyce nie było i V3/V4 wyglądały na bezużyteczne. Wyłapał to brak jakiejkolwiek zmiany wybrzuszenia.

**Uwaga do miary „wybrzuszenia”:** to przesunięcie skrajnego węzła skóry po stronie komory **względem osi** ogona, a przy odpowietrzonej komorze R oś też się przesuwa, bo przegroda ugina się w stronę R. Pomiar pierścienia włókien pokazał, że sama ścianka V4 wychodzi na zewnątrz tylko o ~0.4 mm przy 8 ml.

**Tryb komory R** (siatka test, V4, 12 ml w L): odpowietrzona −3.0°, zamknięta (stała objętość) −2.6°, antagonistyczna (ΔV_R = −ΔV_L, czyli praca pompy) −2.8°. Tryb R zmienia wynik o ~15%.

## Etap 2 – komora L quasi-statycznie: krzywa p–V i kąt końcówki

`scripts/run_stage2.py`. Konstrukcja V4, komora L dostaje zadany przyrost objętości 0…50 ml, komora R jest odpowietrzona (ciśnienie 0, jak drugi króciec otwarty na stanowisku), bez ciężaru. Liczone pseudo-statycznie: niejawny Euler z dt = 50 ms i LDL (wyniki etapu 2 policzone jeszcze z LDL; CHOLMOD daje te same liczby). Po każdym punkcie objętość jest trzymana, aż energia kinetyczna < 1% pracy ciśnienia ∫p dV; w praktyce wychodzi ≤ 0.4%. Ta metoda daje ten sam stan co wolna rampa przy dt = 2 ms (sprawdzone na siatce test: 1950.4 Pa w obu przypadkach), a jest 5–25× tańsza. `StaticSolver` odpada, bo nie działa z ograniczeniami Lagrange'a komory.

### Wyniki (`results/s2_pv_curve.png`, `results/s2_tip_angle.png`, `results/s2_curves.csv`)

| siatka | p przy 50 ml | θ_tip przy 50 ml | czas |
|---|---|---|---|
| coarse (28k tetr) | 19.3 kPa | −16.3° | 35 s |
| medium (52k) | 18.4 kPa | −15.7° | 1.7 min |
| fine (142k) | 16.1 kPa | −15.4° | 16 min |

- **Krzywa p–V** (`s2_pv_curve.png`) jest prawie liniowa na początku i coraz bardziej stroma. Ogon zgięty o 15° trudniej dalej zginać, a włókna przenoszą coraz więcej siły. Przy 50 ml potrzeba ~16 kPa, czyli 1/3 ciśnienia otwarcia zaworu z MuJoCo (50 kPa). Pompa ma zapas.
- **Kąt końcówki** (`s2_tip_angle.png`): komora L (+Y) wydłuża lewy bok, więc ogon zgina się w **−Y** (θ < 0, w prawo). Zależność też jest lekko wypukła: ~0.25°/ml na początku i ~0.45°/ml przy 50 ml. Tę samą krzywą zmierzysz na prawdziwym ogonie (strzykawka dozująca objętość, manometr, zdjęcie z góry), i to jest główny wynik demo.

### Zbieżność siatki (`results/s2_convergence.txt`)

| | p @ 25 ml | θ @ 25 ml | p @ 50 ml | θ @ 50 ml |
|---|---|---|---|---|
| coarse vs fine | +26.6% | +4.8% | +20.3% | +5.9% |
| medium vs fine | +19.9% | +2.7% | +14.5% | +2.5% |

**Kąt zbiega dobrze** (coarse już w ~5%). **Ciśnienie zbiega słabo**: nawet medium jest 15–20% za wysoko, a fine pewnie też jeszcze nie jest granicą. Kąt wynika z kinematyki (ile objętości wtłoczono i jak długi jest bok), a ciśnienie ze sztywności cienkich ścianek, a te przy ~1–2 elementach na grubość są za sztywne (locking liniowych czworościanów). Wnioski:
- do kształtu ruchu (kąt, etapy 4–6) wystarczy coarse, z błędem ~5%,
- ciśnienia z coarse są zawyżone o ~20–25%; do porównań z pomiarem ciśnienia trzeba podawać ten błąd albo liczyć na fine,
- dokładniejsze ciśnienie wymagałoby elementów kwadratowych albo ≥ 3 elementów na ściankę (~450k tetr), czego binarka SOFA tu nie udźwignie w rozsądnym czasie.

### Jak to zmierzyć na prawdziwym ogonie (kalibracja)

1. Ogon przykręcony nasadą do stołu, komora R z otwartym króćcem.
2. Strzykawka lub pompa dozująca w komorę L po 5 ml, manometr na wlocie i zdjęcie z góry (kąt cięciwy od nasady do środka płetwy, tak jak `geometry.tip_angle`).
3. Dopasowanie: najpierw `young_modulus` do krzywej p–V (ciśnienie skaluje się ~liniowo z E), potem `spine_E_factor` i `hoop_stiffness` do krzywej θ–V. Na grubej siatce trzeba uwzględnić jej +20% na ciśnieniu.

## Etap 3 – symetria: komora R jako lustro komory L

`scripts/run_stage3.py` (~3 min z CHOLMOD). Te same warunki co w etapie 2: V4, bez ciężaru, druga komora odpowietrzona, 5…50 ml. Liczone osobno dla komory L i R, na trzech poziomach siatki. Siatka jest lustrzana z konstrukcji: każdy węzeł ma parę w odbiciu względem płaszczyzny XZ, w odległości 0.0 m. Pierścienie włókien też są symetryczne.

**Wynik** (`results/s3_symmetry.png`, `.csv`, `.txt`): przy 50 ml na fine komora R daje p = 16.050 kPa i θ = +15.352°, a komora L te same 16.050 kPa i −15.352°. Największy błąd symetrii na całym zakresie:

| siatka | kąt | ciśnienie | wydymanie |
|---|---|---|---|
| coarse | 0.75% | 0.023% | 0.14% |
| medium | 0.11% | 0.008% | 0.014% |
| fine | 0.34% | 0.012% | 0.11% |

Spec wymaga < 5%; test `test_chamber_R_mirrors_L` pilnuje 1% na siatce test.

**Skąd resztkowy błąd:** to nie siatka, tylko kryterium końca trzymania punktu (energia kinetyczna < 1% pracy ciśnienia). Symulacje L i R zatrzymują się w trochę innym momencie zanikającego ruchu. Dlatego błąd jest największy w pierwszym punkcie (5 ml), gdzie ruch po rampie jest największy względem ugięcia. Przy 30–50 ml spada do 1e-5…1e-7%. Na fine zostaje na poziomie ~1e-3%: to szum zaokrągleń rozkładu macierzy przy innej kolejności elementów w lustrzanej połowie.

**Kontrola CHOLMOD:** krzywa L z tego etapu (CHOLMOD) różni się od etapu 2 (LDL) o ≤ 0.0006% w kącie i ≤ 0.0002% w ciśnieniu na wszystkich poziomach. Wyniki etapu 2 nie wymagają przeliczenia.

## Etap 4 – hydraulika antagonistyczna: machanie w powietrzu

`scripts/run_stage4.py` (~25 min). Siatka coarse, powietrze, ciężar włączony, komory pełne wody. Przebieg: 0–1 s prefill obu komór do 20 ml, potem rytm V_ref(t) z rampą 1 s, łącznie 4.5 s. Pompa przetacza ciecz z R do L (`fishsofa/hydraulics.py`), a kontroler SOFA (`fishsofa/controller.py`) co krok ustawia przyrost objętości obu komór: ΔV_L = prefill + V_p, ΔV_R = prefill − V_p. **+V_p (komora L) zgina ogon w −Y, w prawo. To odpowiada +V_bias w MuJoCo („skręt w prawo”).**

### Parametry: dlaczego nie 1:1 z MuJoCo
Komora SOFA ma 91 ml, a w MuJoCo `V0_chamber` = 30 ml. A_V = 8 ml z MuJoCo dałoby tu ~±3°. Do tego Q_max = 60 ml/s nie nadąża przy 2 Hz (potrzeba 2π·f·A_V), więc wyszłoby jeszcze mniej. Wybrany jest największy ruch, który się bezpiecznie mieści: **A_V = 17 ml, V_prefill = 20 ml, Q_max = 250 ml/s**. Pozostałe wartości są jak w MuJoCo: f = 2 Hz, K_v = 10 1/s, τ_pump = 30 ms, p_max = 50 kPa.

**Górna granica prefillu: wyboczenie kręgosłupa.** Napełnienie obu komór wydłuża ogon wzdłuż, a sztywny kręgosłup jest wtedy ściskany. Pomiar statyczny na siatce coarse:

| prefill | ciśnienie wspólne | stan symetryczny |
|---|---|---|
| 10 ml | 25 kPa | prosty |
| 20 ml | 53 kPa | prosty |
| 24 ml | 64 kPa | θ = 0.02°, a Δp ma zły znak (L bardziej napełniona, a ciśnienie niższe) |
| 30 ml | 78 kPa | θ = 0.34°: ogon wygina się bez różnicy objętości |

±15° wymagałoby prefillu > 24 ml, czyli już w tym zakresie. Wniosek projektowy: przy konstrukcji V4 prefill ogranicza amplitudę, bo ciśnienie wspólne obciąża kręgosłup osiowo.

**Kompensacja opóźnienia pompy (zmiana względem MuJoCo).** Komenda z MuJoCo, u = (dV_ref/dt + K_v·(V_ref − V_p))/Q_max, przy 2 Hz przeregulowywała: V_p dochodziło do 1.16·A_V, czyli 19.7 ml, i komora R prawie do objętości spoczynkowej. Działo się tak nawet bez nasycenia pompy (Q_max 400 ml/s: 1.17×). Pompa I rzędu ma ωτ = 0.38, więc samo sprzężenie w przód jest spóźnione. Dodany człon τ_pump·d²V_ref/dt² odwraca to opóźnienie: błąd śledzenia spada do 1.2% A_V, bez nasycenia (test `test_pump_tracks_v_ref`). **Ten sam problem jest w MuJoCo** (`MuJoCo/fishsim/controllers.py`), tam nic nie zmieniałem.

### Wyniki (`results/s4_air_flapping.png`, `.csv`, `results/s4_summary.txt`)

| | dt = 2 ms | dt = 1 ms |
|---|---|---|
| amplituda θ (ustalony cykl) | **±12.66°** | ±13.33° |
| zmiana amplitudy w ostatnim cyklu | 0.00% | 0.00% |
| opóźnienie fazy θ względem −V_ref | 50° | 47° |
| p_L, p_R | 50.1–56.4 kPa | 50.2–56.3 kPa |
| \|Δp\| max | 5.7 kPa (zawór nie otwiera się) | 5.5 kPa |
| ΔV_L + ΔV_R zmierzone (zadane 40 ml) | 39.9991–40.0025 ml | 39.9992–40.0003 ml |
| solver ograniczeń | ≤ 30 iteracji, błąd ≤ 2e-9 | ≤ 28 iteracji |
| czas obliczeń | 198 ms/krok = **99× wolniej niż czas rzeczywisty** | 181 ms/krok = 181× |

Obserwacje:
- Cykl ustala się już w drugim cyklu po rampie, a średni kąt wynosi 0.000°: przy prefillu 20 ml wyboczenia nie ma.
- Kąt opóźnia się o ~50° za objętością, a przy statyce opóźnienia nie byłoby. Za opóźnienie odpowiada bezwładność ogona z wodą w komorach, a nie pompa (V_p pokrywa się z V_ref, dolny panel wykresu).
- Różnica ciśnień jest mała (±5.7 kPa) na tle ciśnienia wspólnego 53 kPa. W układzie antagonistycznym ruch steruje różnica, a i tak do 50 kPa daleko.

**Wpływ dt (spec, sekcja 5):** przy dt = 2 ms amplituda jest o 5.1% mniejsza niż przy 1 ms. Niejawny Euler tłumi numerycznie i to tłumienie rośnie z dt. Dla etapów 5–6 to znany błąd systematyczny (−5% amplitudy). Jeśli porównania mają być ilościowe, trzeba liczyć przy 1 ms, kosztem 2× dłuższego czasu.

**GUI (sprawdzone 5.10.2026: ogon macha):** `scripts/run_gui.sh` (domyślnie tryb `flap`, Animate) pokazuje ten sam przebieg z rysowaniem ciśnienia komór (`drawPressure`). Pierwsza sekunda to prefill (ogon prawie stoi), a 1 s symulacji liczy się ~2 min. Ugięcie pod ciężarem z etapu 1: `scripts/run_gui.sh coarse sag`.

## Etap 5 – woda: opór, ciąg na uwięzi

`scripts/run_stage5.py` (~60 min zegarowo, 3 symulacje naraz). Ten sam przebieg co w etapie 4 (coarse, prefill 20 ml, 2 Hz, A_V = 17 ml), ale `environment="water"`: silikon ma ciężar pozorny g·(1 − ρ_w/ρ_s), woda w komorach ma bezwładność bez ciężaru, a na skórę działa opór wody. GUI: `FISHSOFA_ENV=water scripts/run_gui.sh`.

### Model oporu (`fishsofa/water.py`, `controller.WaterDragController`)

Każdy trójkąt skóry dostaje siłę zależną tylko od własnej prędkości v (średnia z 3 węzłów), normalnej zewnętrznej n i pola A:
- normalna F_n = −½ρ·C_n·A·(v·n)|v·n|·n (opór ciśnieniowy),
- styczna F_t = −½ρ·C_t·A·|v_t|·v_t (tarcie skóry).

Siła trójkąta idzie po 1/3 na jego węzły, przez `ConstantForceField` "water" aktualizowany na początku każdego kroku. C_n = 1 i C_t = 0.01 to PLACEHOLDER. C_n działa na każdą stronę powierzchni, więc cienka płytka w przepływie poprzecznym ma C_d ≈ 2·C_n ≈ 2, jak płaska płytka (test `test_drag_on_flat_plate`). Funkcje są czystym numpy i mają testy bez SOFA: moc oporu F·v ≤ 0 na każdym trójkącie, zerowa prędkość daje zerową siłę.

**Stabilność.** Siła liczona z prędkości z poprzedniego kroku to jawne tłumienie. Węzeł o masie m i lokalnym współczynniku c = ρ·C_n·A_węzła·|v_n| jest stabilny tylko przy c·dt/m wyraźnie < 1. Najgorsze są węzły płetwy (6 mm grubości, lekkie i o dużej powierzchni):

| dt | max(c·dt/m) w ustalonym cyklu |
|---|---|
| 2 ms | ~0.7 (siatka test), za dużo |
| 1 ms | **0.536**, chwilowo w szczycie prędkości płetwy, tuż powyżej 0.5 |
| 0.5 ms | **0.272**, wynik etapu |

Między 1 ms a 0.5 ms amplituda różni się o 1.4%, a ciąg o 5%. Siły nie są obcinane. Krok 0.5 ms kosztuje 2×. Tańsza droga byłaby niejawna: opór jako `ForceField` z członem tłumienia w macierzy układu (rozszerzenie ze specu, niezrobione).

### Wyniki (`results/s5_water_vs_air.png`, `.csv`, `results/s5_summary.txt`)

| | powietrze (dt 1 ms) | woda (dt 0.5 ms) |
|---|---|---|
| amplituda θ (ustalony cykl) | ±13.33° | **±7.32°** (0.55×) |
| opóźnienie fazy θ względem −V_ref | 47° | 77° (+30°) |
| \|Δp\| max | 5.5 kPa | 5.6 kPa |
| ciąg na uwięzi (średnie F_x) | – | **+67 mN** |
| siła boczna F_y | – | ±755 mN |
| średnia moc oporu | – | 125 mW |

Obserwacje:
- **Ta sama komenda objętości, prawie dwa razy mniejsze machanie.** W powietrzu ogon (z ~3 Hz częstością własną, etap 1) przy 2 Hz jest blisko rezonansu i bezwładność wzmacnia ruch ponad wychylenie statyczne. Woda tłumi to wzmocnienie i przesuwa fazę o +30°: kąt jeszcze bardziej spóźnia się za objętością.
- **Δp prawie się nie zmienia.** Ciśnienie w komorach ustala głównie sztywność ogona i ścianek (rząd 10⁴ Pa), a siły wody są małe w porównaniu z siłami sprężystymi. Dla pompy i zaworu woda niewiele zmienia przy tych parametrach.
- **Ciąg jest ~10× mniejszy niż siła boczna**, a jego składowa F_x pulsuje z 2f (dwa „pchnięcia” na cykl, po jednym na każdy ruch w bok). Średnio +67 mN. To tylko jakościowo: model ma sam opór, bez masy dodanej i bez śladu wirowego, a to te efekty dominują w ciągu ryb (Lighthill). Prawdziwy ogon da prawdopodobnie inną liczbę; do porównania służy pomiar na wadze w wannie (sekcja „Jak kalibrować”).
- 361–408 ms/krok przy 3 równoległych procesach i 11 procesach razem z etapem 6 (pojedynczo ~220 ms). Woda przy dt 0.5 ms liczy się ~800× wolniej niż czas rzeczywisty.

## Etap 6 – przeglądy: częstotliwość i moduł Younga

`scripts/run_stage6.py`: 19 niezależnych symulacji (siatka coarse) liczonych równolegle przez `fishsofa/parallel.py`. **Czas całego przeglądu: 68 min zegarowo**, w tym 444 min CPU samych symulacji dynamicznych, czyli 6.5× szybciej niż po kolei (8 procesów naraz obok 3 z etapu 5). Wyniki: `results/s6_freq_sweep.png/.csv`, `results/s6_young_sweep.png/.csv`, `results/s6_summary.txt`.

### a) Częstotliwość 0.5–3 Hz w wodzie (`s6_freq_sweep.png`)

Te same punkty co `MuJoCo/scripts/sweep_frequency.py` (co 0.25 Hz), ta sama amplituda objętości A_V = 17 ml. Protokół: prefill 1 s, 2 cykle rozbiegu (pierwszy to rampa amplitudy), 3 cykle uśredniania. Krok: 1 ms do 2 Hz, wyżej 1 ms·2/f.

| f [Hz] | 0.5 | 1.0 | 1.5 | 2.0 | 2.25 | 2.5 | 3.0 |
|---|---|---|---|---|---|---|---|
| amplituda θ [°] | 11.8 | 10.8 | 8.9 | 7.2 | 6.5 | 5.7 | 4.3 |
| opóźnienie fazy [°] | 17 | 40 | 61 | 77 | 84 | 91 | 106 |
| ciąg [mN] | 1.5 | 19.6 | 45.9 | 63.2 | **67.9** | 62.8 | 47.0 |
| \|Δp\| max [kPa] | 1.7 | 3.5 | 4.9 | 5.7 | 5.9 | 5.9 | 5.4 |
| pompa nasycona [% czasu] | 0 | 0 | 0 | 0 | 18 | 36 | 53 |

Co pokazuje wykres:
- **Amplituda spada z f przez cały zakres.** W wodzie ogon nie ma rezonansu: opór rośnie z kwadratem prędkości i tłumi go silniej niż w powietrzu (tam częstość własna to ~3 Hz, etap 1). Przy niskim f kąt dochodzi do quasi-statycznego (~12°, porównaj etap 2) i prawie nie spóźnia się za objętością.
- **Ciąg ma maksimum przy ~2.25 Hz.** Rośnie, bo rośnie prędkość płetwy (opór ~ v²), a spada, bo maleje amplituda i od 2.25 Hz pompa się nasyca: potrzebny szczytowy przepływ 2π·f·A_V (240 ml/s przy 2.25 Hz, plus kompensacja opóźnienia pompy) przekracza Q_max = 250 ml/s.
- **Zawór nie otwiera się nigdzie:** |Δp| ≤ 6 kPa wobec p_max = 50 kPa. Przy tej konstrukcji ograniczeniem jest wydajność pompy, nie ciśnienie.
- **Porównanie z MuJoCo** (`MuJoCo/results/s5_sweep.png`, na wykresie przeskalowana linia przerywana, tylko kształt): MuJoCo ma pik amplitudy przy 1.5 Hz, SOFA nie ma piku. Przyczyny: MuJoCo modeluje pływającą rybę z masą dodaną i rezonansem pasywnym (`passive_resonance_hz`), a tu ogon jest przymocowany, z samym oporem, który przy tej sztywności tłumi rezonans całkowicie. Spadek powyżej 2 Hz (nasycenie pompy) wygląda w obu podobnie.
- **Stabilność oporu:** max(c·dt/m) wynosi 0.52 przy 1.75 Hz i 0.54 przy 2 Hz (dt 1 ms), wszędzie indziej < 0.5. Etap 5 zmierzył skutek takiego przekroczenia: przy dt/2 amplituda +1.4%, ciąg +5%. Lepsza reguła na przyszłość: dt = 1 ms·min(1, 1.6/f).

### b) Moduł Younga silikonu ×0.5 / ×1 / ×2 (`s6_young_sweep.png`)

Zmieniany jest tylko silikon (z kręgosłupem, bo jego E to 20× silikon). Włókna obwodowe to inny materiał i ich sztywność zostaje.

| | E×0.5 | E×1 | E×2 |
|---|---|---|---|
| **sterowanie objętością**, 40 ml: ciśnienie | 7.1 kPa | 14.2 kPa | 27.9 kPa |
| ten sam przypadek: kąt | −11.35° | −11.35° | −11.16° |
| **sterowanie ciśnieniem**, 8 kPa: kąt | −12.91° | −6.03° | −2.73° |
| **dynamicznie w wodzie, 2 Hz**: amplituda | ±5.8° | ±7.2° | ±8.2° |
| ten sam przypadek: opóźnienie fazy | 96° | 77° | 59° |

**Lekcja: sterowanie objętością a sterowanie ciśnieniem.**
- Pompa wymusza **objętość**. Gdy cała konstrukcja jest „jednym materiałem razy k” i nie ma obciążeń zewnętrznych, równowaga przy zadanym ΔV w ogóle nie zależy od k: ten sam kształt, tylko ciśnienie ×k. Tu widać to prawie dokładnie (kąt przy 40 ml różni się o < 2%, ciśnienie skaluje się 0.50 / 1 / 1.97). Odstępstwo przy 10 ml dla E×0.5 (−1.68° vs −1.93°) pochodzi od włókien, które się nie skalują: przy miękkim silikonie są relatywnie sztywniejsze. Test `test_young_x2_same_volume_doubles_pressure_keeps_angle` skaluje też włókna i sprawdza prawo dokładnie.
- Sztywność decyduje więc o **wymaganym ciśnieniu**: dobór pompy, zaworu, szczelności, zmęczenie silikonu. Na ruch wpływa dopiero przez obciążenia zewnętrzne: wodę, bezwładność, ciężar.
- **Przy sterowaniu ciśnieniem jest odwrotnie:** ten sam p daje ugięcie ~1/E (8 kPa: 12.9° / 6.0° / 2.7°, test `test_young_x2_same_pressure_halves_angle`). Nawet szybciej niż 1/E, bo krzywa p–V się usztywnia (etap 2), a miękki ogon wchodzi głębiej w jej nieliniową część.
- **Dynamicznie w wodzie E jednak zmienia ruch:** sztywniejszy ogon ma wyższą częstość własną, więc przy 2 Hz mniej spóźnia się za objętością (59° vs 96°) i mniej ruchu „gubi” na oporze. Miękki ogon przy tej samej objętości macha mniej, bo woda przy jego wolniejszej odpowiedzi zabiera większą część ruchu.

## Podgląd w czasie rzeczywistym: nagranie, odtwarzanie, wideo

Na żywo ogon w GUI rusza się 100–800× wolniej niż w rzeczywistości (krok liczy się 200–400 ms, a symuluje 0.5–2 ms). Dlatego ruch liczymy offline, zapisujemy i odtwarzamy w prawdziwym tempie:

```bash
source SOFA/scripts/env.sh
python SOFA/scripts/record.py               # nagrania powietrze + woda, równolegle (~40 min) -> SOFA/recordings/*.npz
SOFA/scripts/run_replay.sh                  # GUI SOFA: odtwarzanie wody w czasie rzeczywistym, w pętli
SOFA/scripts/run_replay.sh SOFA/recordings/air.npz 0.25   # powietrze, 4× zwolnione
pip install pyvista==0.49.0                 # raz, tylko do wideo
python SOFA/scripts/render_video.py         # wideo -> SOFA/results/flapping.mp4 (~3 min)
```

- **Nagranie** (`scripts/record.py`, `headless.run_flapping(record_fps=60)`): pozycje wszystkich węzłów co 1/60 s czasu symulacji, ciśnienia i kąt. ~25 MB na nagranie, katalog `recordings/` jest poza repo. Kroki jak w etapach 4–5: powietrze 1 ms, woda 0.5 ms.
- **Odtwarzanie w GUI** (`fishsofa/replay.py`, tryb `FISHSOFA_MODE=replay`): scena bez fizyki, same modele wizualne. Kontroler wybiera klatkę według zegara ściennego, więc tempo nie zależy od szybkości rysowania. Skóra jest półprzezroczysta, a komory mają kolor wg ciśnienia (niebieski = najniższe w fazie rytmu, czerwony = najwyższe; skala bez prefillu, bo ruch steruje różnica ±6 kPa na tle wspólnych ~53 kPa). Kamerę obraca się myszą jak zwykle.
- **Wideo** (`scripts/render_video.py`, PyVista + ffmpeg): powietrze i woda obok siebie, widok z góry, wspólna skala ciśnień, pod spodem θ(t) z kursorem. Najpierw cały przebieg 4.5 s w czasie rzeczywistym, potem ostatni cykl 4× zwolniony.
