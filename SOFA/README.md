# fish-sim-v0 / SOFA – miękki hydrauliczny ogon (SOFA + SoftRobots)

Edukacyjne demo FEM ogona robota-ryby. Specyfikacja: [SPEC_fish_sofa_demo.md](SPEC_fish_sofa_demo.md). **To nie jest skalibrowany model** – wszystkie parametry to placeholdery.

Stan: **etapy 0 (instalacja, API), 1 (siatka, ugięcie pod ciężarem) i 2 (komora L quasi-statycznie) zakończone.** Kolejne etapy: patrz spec, sekcja 8.

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
python scripts/run_stage2_variants.py       # etap 2a: warianty konstrukcji (~10 min)
python scripts/run_stage2.py                # etap 2: krzywa p–V i kąt, 3 siatki (~25 min)
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

Przy 5 ml różnica była 1.7%, więc błąd rośnie z odkształceniem. Przyczyna: korekcja ograniczeń używa przybliżonej podatności J·A_warp⁻¹·Jᵀ, więc rozkład siły ciśnienia na węzły jest zły i równowaga się przesuwa. Dlatego **domyślny solver to znowu `"ldl"`**, a scena z komorami wymusza LDL (test `test_warp_is_replaced_by_ldl_with_chambers`). Warp jest użyteczny tylko bez komór. Dla dynamiki z komorami (etapy 4–6) wydajność trzeba będzie rozwiązać inaczej.

Trzy błędy wcześniejszych prób (etap 1), dla przyszłych czytelników:
- `assemblingRate=15` (jak w przykładzie SOFA): macierz składana w stanie odkształconym, a obrót z `TetrahedronFEMForceField` (liczony względem spoczynku) nakłada się drugi raz, więc symulacja wybucha.
- Brak jawnego linku `EulerImplicitSolver linearSolver=@linsolver`: integrator brał pierwszy solver w węźle (LDL z prekondycjonera) i PCG nie był używany.
- Linki `@…` w SofaPython3 muszą wskazywać obiekty, które już istnieją, więc kolejność tworzenia ma znaczenie.

**Większy krok czasu** (warp, coarse): dt 5 ms daje 2× krótszy czas całości, ale różnica trajektorii to 3.4 mm (~5% amplitudy). Przy dt 10 ms jest 3.5× szybciej, ale z różnicą 7.8 mm (~11%). Niejawny Euler przy dużym kroku tłumi ruch numerycznie. Domyślnie zostaje 2 ms; większy krok tylko świadomie, z podanym błędem.

**Sprawdzone bez zysku:** numeracja Metis/AMD/COLAMD (domyślna jest dobra), `nbThreads`, `ParallelTetrahedronFEMForceField` (składanie macierzy zostaje sekwencyjne), CG na złożonej macierzy (~10%), sam `AsyncSparseLDLSolver` (niestabilny, co dokumentacja SOFA przyznaje).

**Niewykorzystane opcje:**
- `EigenCholmodSupernodalLLT` (plugin SofaCHOLMOD, dokładny i 4–11× szybszy rozkład) jest dopiero w gałęzi master SOFA, nie w binarce v26.06.
- Redukcja rzędu modelu (plugin ModelOrderReduction, w binarce) daje nawet ~50×, ale wymaga treningu offline i działa tylko w wytrenowanym zakresie. To kandydat dopiero na etap 6.

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

`scripts/run_stage2.py`. Konstrukcja V4, komora L dostaje zadany przyrost objętości 0…50 ml, komora R jest odpowietrzona (ciśnienie 0, jak drugi króciec otwarty na stanowisku), bez ciężaru. Liczone pseudo-statycznie: niejawny Euler z dt = 50 ms i LDL. Po każdym punkcie objętość jest trzymana, aż energia kinetyczna < 1% pracy ciśnienia ∫p dV; w praktyce wychodzi ≤ 0.4%. Ta metoda daje ten sam stan co wolna rampa przy dt = 2 ms (sprawdzone na siatce test: 1950.4 Pa w obu przypadkach), a jest 5–25× tańsza. `StaticSolver` odpada, bo nie działa z ograniczeniami Lagrange'a komory.

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
