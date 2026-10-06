# SPEC: Demo SOFA + SoftRobots – miękki hydrauliczny ogon robota-ryby

> Instrukcja dla Claude Code. Ten plik leży w folderze `SOFA/` repozytorium `fish-sim-v0` (obok `MuJoCo/`). Napisz:
> „Przeczytaj SOFA/SPEC_fish_sofa_demo.md i zrealizuj go etapami. Po każdym etapie uruchom testy i pokaż wyniki.”
> Zacznij w trybie planowania.

## 0. Cel i kontekst

Zbuduj **uproszczoną, edukacyjną** symulację miękkiego ogona robota-ryby w SOFA z pluginem SoftRobots. Ma pokazać to, czego MuJoCo nie umie:
- ciągłe odkształcenie silikonu (FEM na siatce czworościennej),
- dwie wewnętrzne komory hydrauliczne napędzane przez `SurfacePressureConstraint`,
- zależność ciśnienie–objętość–ugięcie (krzywa, którą da się potem zmierzyć na prawdziwym ogonie),
- wpływ wody na ruch ogona (uproszczony, własny model oporu, bo SOFA nie ma hydrodynamiki).

Opcjonalnie (etap 7): most do modelu MuJoCo, czyli eksport zastępczych sztywności przegubów (pseudo-rigid-body model, PRBM) do parametrów z `MuJoCo/fishsim/config.py`. Dlatego geometria ogona odpowiada ogonowi z demo MuJoCo (sekcja 4).

To jest **demo możliwości, nie skalibrowany model**. Wszystkie parametry fizyczne to placeholdery i mają być tak oznaczone.

Użytkownik to młody inżynier mechatronik, który się uczy. **Komentarze w kodzie po polsku**, wyjaśniające fizykę i rolę każdego komponentu SOFA (solver, mapping, constraint), a nie tylko składnię.

Zakres: tylko **ogon**, przymocowany do nieruchomego kadłuba. Balastu i pływania całego pojazdu tu nie ma, pokazuje je demo w `MuJoCo/`.

## 1. Zasady pracy (ważne)

1. Pracuj etapami (sekcja 8). Po każdym etapie uruchom scenę i testy, pokaż wynik, dopiero potem idź dalej.
2. **API SOFA zmienia się między wersjami** (nazwy komponentów, np. solvery ograniczeń, wymagane `RequiredPlugin`, funkcje inicjalizacji w SofaPython3). W etapie 0 ustal zainstalowaną wersję SOFA i zawsze sprawdzaj nazwy w dokumentacji / przykładach dołączonych do tej wersji (`plugins/SoftRobots/examples`, `examples/` w SOFA). Nie kopiuj kodu ze starych tutoriali w SofaPython2 (`createObject`, `createChild`). W SofaPython3 jest `addObject`, `addChild`.
3. Używaj **SofaPython3** (sceny `.py` z funkcją `createScene(rootNode)`), nie XML `.scn`.
4. Konsekwentne jednostki: **SI (m, kg, s, Pa)**. Zapisz to na górze `config.py`. Uwaga: wiele przykładów SoftRobots używa mm (i tolerancji solvera dobranych do mm). Nie mieszaj, a tolerancje przeskaluj (sekcja 5).
5. Nie wymyślaj „realistycznych” wartości i nie przedstawiaj ich jako zmierzonych. Każdy parametr: komentarz `# PLACEHOLDER – do identyfikacji z pomiarów`.
6. Jeśli symulacja „wybucha” lub zachowuje się niefizycznie, **nie maskuj tego** losowym strojeniem. Zdiagnozuj (krok czasowy, skok wartości aktuacji, stabilność jawnej siły oporu, jakość siatki, współczynnik Poissona, zbieżność solvera ograniczeń) i opisz w README.

## 2. Instalacja (zweryfikuj, nie zakładaj) – to jest etap 0

Środowisko docelowe: Fedora (Linux), systemowy Python jest nowszy niż wymaga SOFA, dostępna jest anaconda.

- Najnowsze oficjalne binarki SOFA wymagają konkretnej wersji Pythona (w ostatnich wydaniach 3.12) + numpy + scipy (+ pybind11) dla SofaPython3. Sprawdź stronę wydania (github.com/sofa-framework/sofa/releases). Utwórz środowisko z **dokładnie tą** wersją: `conda create -n fishsofa python=3.12`. Nie używaj systemowego Pythona.
- Binarki są budowane na Ubuntu. Sprawdź, czy `runSofa` startuje na Fedorze (brakujące biblioteki: `ldd`). Zanotuj w README, co trzeba było doinstalować.
- **Sprawdź, czy SoftRobots jest w oficjalnych binarkach tej wersji.** Jeśli nie, opcje to: kompilacja pluginu z SOFA albo DefrostSofaBundle (uwaga: ten bundle ma licencję tylko do zastosowań akademickich i może być starszy). Zanotuj w README, którą drogę wybrałeś i jaka jest licencja.
- **Uruchamianie bez GUI (pytest, skrypty):** `import Sofa` w zwykłym Pythonie wymaga zmiennych środowiskowych (`SOFA_ROOT`, `PYTHONPATH` wskazujący na `site-packages` SofaPython3 w katalogu SOFA, ewentualnie `LD_LIBRARY_PATH`). Zapisz je w `scripts/env.sh`; każdy skrypt i `pytest` uruchamiaj po `source scripts/env.sh`.
- Do generowania siatki: `pip install gmsh meshio` (w tym samym środowisku conda).
- Napisz `scripts/check_sofa.py`, który wypisuje: wersję SOFA, czy SoftRobots i SofaPython3 się ładują, oraz **faktyczne nazwy** komponentów użytych w sekcji 5 (solver ograniczeń, korekcja ograniczeń, `FixedProjectiveConstraint` lub odpowiednik, `SurfacePressureConstraint` i nazwy jego pól: `value`, `valueType`, `pressure`, `cavityVolume`, opcje rysowania ciśnienia).
- Uruchom przykład SoftRobots z komorą ciśnieniową (np. „Springy”/„PressureVsVolumeGrowthControl” z folderu przykładów `SurfacePressureConstraint`) **zanim** napiszesz własną scenę. Na tym przykładzie ustal i zapisz w README:
  - czy `value` przy `valueType="volumeGrowth"` to przyrost **całkowity** względem objętości początkowej, czy przyrost **na krok** (od tego zależy cały `hydraulics.py`),
  - znak: czy dodatnie `value` daje dodatnie `pressure` i rosnące `cavityVolume`, i jaka orientacja trójkątów komory jest wymagana.

**Gotowe, gdy:** `check_sofa.py` przechodzi, przykład z komorą działa headless, wyniki obu ustaleń są w README.

## 3. Struktura projektu

```
SOFA/
  SPEC_fish_sofa_demo.md
  README.md
  requirements.txt            # gmsh, meshio, numpy, scipy, matplotlib, pytest (SOFA osobno)
  fishsofa/
    config.py                 # WSZYSTKIE parametry (geometria, siatka, materiał, numeryka, woda, hydraulika)
    mesh_gen.py               # gmsh: połowa ogona z komorą -> odbicie lustrzane -> tetra + powierzchnie
    scene.py                  # createScene(root): ogon FEM + komory + mocowanie + kontrolery
    hydraulics.py             # pompa jako źródło objętości, układ zamknięty L<->R, zawór przelewowy
    water.py                  # siły oporu wody na trójkątach powierzchni zewnętrznej (czysty numpy, testowalny bez SOFA)
    geometry.py               # kąt końcówki, cięciwa, pomocnicze pomiary (wspólne dla testów i wykresów)
    controllers.py            # Sofa.Core.Controller: rytm, logowanie, aplikacja sił
    headless.py               # uruchamianie sceny z Pythona bez GUI (N kroków, zwrot logów)
  scripts/
    env.sh                    # SOFA_ROOT, PYTHONPATH itd. (sekcja 2)
    check_sofa.py             # etap 0
    run_gui.sh                # runSofa z odpowiednimi pluginami
    run_scenarios.py
    export_prbm.py            # etap 7 (opcjonalny) -> results/prbm.json
  meshes/                     # wygenerowane siatki (nie commitować, odtwarzalne z mesh_gen.py)
  tests/test_sanity.py
  results/
```

## 4. Geometria i siatka (mesh_gen.py)

**Układ osi** (taki sam jak w MuJoCo): X wzdłuż ryby, ogon wychodzi z kadłuba w kierunku **−X**; Y w bok (w tej osi ogon się zgina); Z w pionie (grawitacja w −Z). Początek układu: środek przedniej (przymocowanej) ściany ogona.

**Wymiary** = ogon z `MuJoCo/fishsim/config.py`. Liczby przepisz do `config.py` z komentarzem, skąd pochodzą (wszystkie PLACEHOLDER):
- długość korpusu ogona `n_segments · segment_length` = 5 × 0.04 = 0.20 m,
- przekrój na nasadzie: grubość (Y) 2·`segment_ry0` = 0.06 m, wysokość (Z) 2·`segment_rz0` = 0.08 m, liniowe zwężenie do `taper_last` = 0.4 na końcu,
- płetwa ogonowa na końcu: wymiary z `fin_semi_axes` (długość 0.07 m, grubość 0.006 m, wysokość 0.12 m), cienka w Y, wysoka w Z.

**Komory** (lewa +Y i prawa −Y, symetryczne względem płaszczyzny XZ), oddzielone przegrodą środkową. Nowe parametry w `config.py` (PLACEHOLDER):
- długość komory = długość `n_actuated` napędzanych segmentów z MuJoCo (3 × 0.04 = 0.12 m), od `chamber_x_start` (mała odległość od przymocowanej ściany),
- `wall_thickness` (ścianka zewnętrzna), `septum_thickness` (przegroda), `chamber_end_wall` (ścianki czołowe).
- Komory są zamknięte (bez kanałów doprowadzających); dopływ cieczy modeluje tylko `volumeGrowth`.
- Opcjonalnie: sztywniejsza „kręgosłupowa” warstwa w przegrodzie jako osobny materiał (jeśli łatwe; jeśli nie, pomiń i odnotuj).

**Siatka:**
- Generuj **połowę** ogona (y ≥ 0) z jedną komorą i odbij ją lustrzanie względem XZ. Wtedy siatka jest dokładnie symetryczna i test symetrii sprawdza kod, a nie przypadek w siatkowaniu.
- Liniowe czworościany przy zginaniu cienkiej warstwy są za sztywne (shear locking), jeśli na grubości są 1–2 elementy. Wymagaj **≥ 3 elementów na grubość** ścianek komór, przegrody i płetwy: lokalne zagęszczenie w gmsh (pola rozmiaru), grubsze elementy w środku bryły.
- Rozmiar: realny cel to ≤ ~20k czworościanów. Zapisz w raporcie liczbę elementów i elementy na grubość każdej ścianki. Dodaj grubszą siatkę testową (`mesh_size_test` w configu), żeby `pytest` był szybki.
- **Decyzja z etapu 1:** ≥ 3 elementy na ściankę 4 mm i ≤ 20k elementów nie dadzą się spełnić razem (ogon 0.2 m: 4 mm → ~28k, 2 mm → ~140k, 1.3 mm → ~450k tetr). Zamiast tego **studium zbieżności**: poziomy `coarse` / `medium` / `fine` (4/3/2 mm przy powierzchniach) i `test` (6 mm, tylko pytest). Etap 2 (statyka p–V) liczony na wszystkich trzech, żeby zmierzyć, o ile gruba siatka zawyża sztywność. Etapy dynamiczne na najgrubszej, z podanym błędem.
- **Ustalone w etapie 1:** `MeshVTKLoader` (SOFA v26.06) nie czyta VTK 5.1 z meshio (segfault), więc siatka jest zapisywana jako klasyczny VTK 4.2. `StaticSolver` wymaga osobnego `NewtonRaphsonSolver` (od v25.12) i nie działa z `FreeMotionAnimationLoop`.
- Wnęki komór **nie są** siatkowane (puste w środku bryły).
- Eksport:
  - siatka objętościowa tetra (format, który wczyta loader SOFA w tej wersji: `MeshGmshLoader` lub `MeshVTKLoader`; jeśli wersja formatu `.msh` sprawia problem, eksportuj VTK przez meshio),
  - powierzchnie trójkątne komór L i R (STL/OBJ) do `SurfacePressureConstraint`, zbudowane z **tych samych węzłów** co siatka tetra, z orientacją ustaloną w etapie 0,
  - powierzchnia zewnętrzna = trójkąty brzegowe siatki tetra (te same węzły), normalne **na zewnątrz** (do sił wody i wizualizacji).
- Raport jakości (`results/s1_mesh_report.txt`): brak czworościanów o objętości ≤ 0, rozkład jakości (np. stosunek promieni), liczba elementów, elementy na grubość ścianek, zgodność orientacji normalnych.

## 5. Scena SOFA (scene.py)

- Pętla animacji z ograniczeniami (`FreeMotionAnimationLoop` + odpowiedni solver ograniczeń dla tej wersji SOFA), bo `SurfacePressureConstraint` jest ograniczeniem Lagrange'a. **Tolerancja solvera ograniczeń w SI:** objętości są rzędu 1e-6 m³, więc tolerancje z przykładów w mm są o rzędy wielkości złe. Dobierz tolerancję względem skali (np. 1e-3 × typowe ΔV) i loguj liczbę iteracji i osiągnięty błąd w każdym kroku.
- Integrator `EulerImplicitSolver` + bezpośredni solver liniowy (np. `SparseLDLSolver`) + odpowiednia korekcja ograniczeń.
- **Krok czasowy** `dt` w configu. Punkt startowy: `dt ≤ 1/(50·f_max)` ≈ 6 ms dla f_max = 3 Hz, skorygowany wg warunku stabilności oporu wody (sekcja 7). Raportuj stosunek czasu symulacji do czasu rzeczywistego (bez obietnicy „czasu rzeczywistego”).
- **Tłumienie materiałowe:** `rayleighStiffness` i `rayleighMass` w `EulerImplicitSolver` jako PLACEHOLDER w configu. W komentarzu wyjaśnij, że niejawny Euler dodaje też tłumienie numeryczne (rosnące z `dt`), więc amplituda w powietrzu (etap 4) zależy od `dt`. Sprawdź to raz: amplituda przy `dt` i `dt/2` i wynik w README.
- Materiał: `TetrahedronFEMForceField` z `method="large"` (korotacyjny, duże obroty), moduł Younga silikonu jako placeholder (rząd 1e5–1e6 Pa), Poisson **0.45, nie 0.5** (przy 0.5 liniowe tetra blokują się, tzw. volumetric locking; wyjaśnij to w komentarzu). Opcjonalnie wariant hiperelastyczny jako rozszerzenie, nie wymagany.
- Masa: `MeshMatrixMass` / `UniformMass` z gęstością silikonu `rho_tail` z MuJoCo (1100 kg/m³, placeholder). **Plus masa wody w komorach** (ρ_wody · objętość komory, rozłożona na węzły ścianek komór): ogon z napełnionymi komorami jest cięższy niż sam silikon.
- **Otoczenie**: jeden przełącznik `environment = "air" | "water"` w configu, ustawia razem grawitację i opór:
  - `"air"`: pełna grawitacja na silikon + wodę w komorach, brak oporu wody,
  - `"water"`: efektywna grawitacja silikonu `g·(1 − ρ_wody/ρ_silikonu)`, woda w komorach neutralna (wypór = ciężar), opór wody włączony (sekcja 7).
- Mocowanie: węzły przedniej ściany ogona (x = 0) unieruchomione (`FixedProjectiveConstraint` lub odpowiednik w danej wersji). To odpowiada ogonowi przykręconemu do kadłuba i jednocześnie **stanowisku pomiaru ciągu na uwięzi**.
- Komory: dwa węzły-dzieci, każdy z `MeshTopology` + `MechanicalObject` + `SurfacePressureConstraint` + `BarycentricMapping` do siatki FEM (przy wspólnych węzłach mapowanie jest dokładne).

**Definicje pomiarów** (`geometry.py`, używane wszędzie tak samo):
- **kąt końcówki** θ_tip = atan2(Δy, −Δx) cięciwy od środka przedniej ściany do środka płetwy (centroid węzłów płetwy); θ_tip > 0 = ogon wygięty w +Y (w lewo),
- znak zgodny z MuJoCo: dodatnie `V_bias` ma zginać ogon w tę samą stronę co w `MuJoCo/fishsim` (tam +V_bias = skręt w prawo). Zapisz w README, która komora odpowiada +V_bias,
- **ciąg**: średnia po cyklu składowej +X wypadkowej siły wody na ogon (siła działa na wodę w −X, reakcja pcha rybę w +X).

## 6. Hydraulika (hydraulics.py)

Woda jest praktycznie nieściśliwa, więc **pompa wymusza objętość, a nie ciśnienie**. Dlatego używamy `SurfacePressureConstraint` z `valueType="volumeGrowth"`. SOFA sama policzy ciśnienie potrzebne do uzyskania danej objętości (pole `pressure`, tylko do odczytu). To jest fizycznie poprawniejsze dla hydrauliki niż sterowanie ciśnieniem, opisz to w komentarzu.

**Ustalone w etapie 0 (SOFA v26.06, README):** `value` to przyrost **całkowity** względem `initialCavityVolume`. Pole `pressure` to **p·dt** (impuls z solvera ograniczeń), więc ciśnienie = `pressure / dt`. W trybie `valueType="pressure"` wejście `value` też podajemy jako p·dt. Każde ciśnienie w kodzie, logach i na wykresach jest w Pa, a przeliczenie robimy w jednym miejscu (funkcja w `hydraulics.py`).

- **Rytm jak w MuJoCo:** zadajemy przepompowaną objętość `V_ref(t) = V_bias + A_V·r(t)·sin(2πft)` (rampa `r(t)` przez `ramp_time`), a nie sinus komendy pompy. Komenda: `u = sat((dV_ref/dt + K_v·(V_ref − V_p)) / Q_max, −1, 1)`, gdzie `V_p = ∫Q dt`. Nazwy i wartości parametrów jak w `MuJoCo/fishsim/config.py` (`tail_freq`, `tail_volume_amp`, `tail_volume_bias`, `K_v`, `ramp_time`, `Q_max`, `tau_pump`). Uzasadnienie w komentarzu: sinus w `u` dawałby amplitudę objętości ∝ 1/f, więc przegląd częstotliwości mieszałby dwa efekty.
- Pompa jako człon I rzędu: `dQ/dt = (u·Q_max − Q)/τ_pump`.
- Układ zamknięty: `ΔV_L = V_prefill + V_p`, `ΔV_R = V_prefill − V_p`.
- **Wstępne napełnienie:** obie komory startują z `V_prefill > 0` (rampa w pierwszej sekundzie), żeby żadna nie była „zasysana” poniżej objętości spoczynkowej. Kontakt ścianek komory nie jest modelowany, więc `config.py` sprawdza asercją: `V_prefill > |V_bias| + A_V + margines`.
- **Zawór przelewowy na różnicy ciśnień:** pompa w układzie zamkniętym pracuje przeciw `Δp = p_L − p_R`, nie przeciw ciśnieniu jednej komory. Gdy `|Δp| > p_max` (nazwa jak w MuJoCo), zawór przepuszcza ciecz z komory o wyższym ciśnieniu do drugiej (suma objętości bez zmian), tak jak w `MuJoCo/fishsim/hydraulics.py`. Ciśnienie odczytujesz po rozwiązaniu kroku, więc zawór działa z opóźnieniem 1 kroku. Opisz to w komentarzu. Loguj, kiedy zawór był aktywny.
- **Nigdy nie skacz z wartością aktuacji.** Zawsze rampy lub ciągłe sygnały, bo skoki są znaną przyczyną eksplozji symulacji ciśnieniowych.

## 7. Woda (water.py) – uproszczenie, uczciwie opisane

SOFA nie ma modelu płynu. Zaimplementuj w kontrolerze (`onAnimateBeginEvent`) prosty **model oporu lokalnego** na każdym trójkącie powierzchni zewnętrznej. Obliczenia w `water.py` jako czyste funkcje numpy (wejście: pozycje, prędkości, trójkąty; wyjście: siły węzłowe), żeby dało się je testować bez SOFA:

- prędkość trójkąta `v` (średnia z węzłów), normalna zewnętrzna `n`, pole `A`,
- siła normalna: `F_n = −½ ρ C_n A (v·n)|v·n| n`,
- siła styczna (mała): `F_t = −½ ρ C_t A |v_t| v_t`,
- rozdział siły po równo na 3 węzły trójkąta, aplikacja przez `ConstantForceField` (pole `forces` aktualizowane co krok) bezpośrednio na węzłach FEM (powierzchnia zewnętrzna ma te same węzły, mapowanie niepotrzebne).
- Przy `environment="water"` grawitacja jest efektywna (sekcja 5). Opisz to.
- Opcjonalnie (rozszerzenie): masa dodana jako zwiększenie masy węzłów powierzchniowych.

**Stabilność (obowiązkowo):** siła liczona z prędkości z poprzedniego kroku to jawne tłumienie. Dla węzła o masie `m` i współczynniku `c = ρ·C_n·A_węzła·|v_n|` jawny krok jest stabilny tylko przy `c·dt/m` wyraźnie < 1. Cienka płetwa ma lekkie węzły i dużą powierzchnię, więc to tu wybuchnie najpierw. Loguj `max(c·dt/m)` w każdym kroku. Jeśli przekracza ~0.5: zmniejsz `dt` i opisz w README, nie obcinaj sił. Rozszerzenie (nie wymagane): opór jako `Sofa.Core.ForceField` w Pythonie z członem tłumienia w macierzy układu (niejawnie).

**Ograniczenie do wypisania w README:** ten model ma tylko opór. Pomija masę dodaną (o ile nie dodasz rozszerzenia), siłę nośną i wiry, a właśnie efekty reaktywne dominują w ciągu ryb (teoria Lighthilla). Liczba ciągu z tego demo jest więc **jakościowa**, nie ilościowa.

## 8. Etapy realizacji

Każdy etap kończy się: testy zielone + wykres(y) z sekcji 9 + 2–3 zdania obserwacji w README.

0. **Instalacja i API** (sekcja 2). **Gotowe, gdy:** `check_sofa.py` przechodzi, ustalenia o `volumeGrowth` w README.
1. **Siatka**: generacja, raport jakości, podgląd w GUI SOFA (sam materiał, bez aktuacji, `environment="air"`, ogon ugina się pod grawitacją w −Z). **Gotowe, gdy:** raport bez błędów, ≥ 3 elementy na grubość ścianek, 100 kroków bez NaN.
2. **Pojedyncza komora, quasi-statycznie**: rampa `volumeGrowth` w komorze L od 0 do `dV_max` (bez prefillu), `environment="air"`, grawitacja wyłączona (`g = 0`), żeby krzywa zależała tylko od materiału i geometrii. Komora R **odpowietrzona**: bez ograniczenia objętości (ciśnienie 0), jak na stanowisku pomiarowym z otwartym drugim króćcem. Quasi-statycznie = wolna rampa (`ramp_static_time`, np. 5 s) i kryterium: energia kinetyczna < 1% energii odkształcenia w każdym punkcie pomiaru; alternatywnie `StaticSolver`, jeśli działa z ograniczeniami w tej wersji. Wykresy: ciśnienie vs objętość, kąt końcówki vs objętość. To najważniejszy wynik demo: tę samą krzywą zmierzysz na prawdziwym ogonie.
   - **Ustalone w etapie 2:** pseudo-statyka (niejawny Euler, dt = 50 ms, LDL) daje ten sam stan co wolna rampa przy dt = 2 ms, 5–25× taniej. Solver „warp” z komorą przesuwa równowagę (−25% ciśnienia przy 30 ml), więc z komorami tylko LDL. Konstrukcja z etapu 1 prawie się nie zgina (komora się wybrzusza); przegląd wariantów wybrał V4 = kręgosłup w przegrodzie (E×20) + włókna obwodowe (README, etap 2a).
   - **Ustalone po etapie 2 (wydajność):** domyślny solver liniowy to CHOLMOD (`EigenCholmodSupernodalLLT`, wtyczka SofaCHOLMOD z master zbudowana dla v26.06): dokładny jak LDL, także z komorami, 4.3× (coarse) do 15× (fine) szybciej. Zostajemy na SOFA v26.06, bo SOFA master (v26.12-dev) daje błędną, drgającą równowagę przy komorze ze sztywnymi włóknami (README, „Wydajność: CHOLMOD”).
3. **Symetria**: to samo dla komory R. Wyniki muszą być lustrzane (test).
   - **Ustalone w etapie 3:** błąd symetrii ≤ 0.75% (kąt, coarse, przy 5 ml), ≤ 0.023% (ciśnienie); resztka pochodzi z kryterium końca trzymania punktu, nie z siatki (README, etap 3).
4. **Hydraulika antagonistyczna**: rytm `V_ref(t)` z sekcji 6, układ zamknięty L↔R, prefill, `environment="air"`. Wykres: kąt końcówki, p_L, p_R, Δp, aktywność zaworu. **Gotowe, gdy:** ustalony cykl po rozbiegu, suma zmierzonych objętości komór stała (test), sprawdzenie wpływu `dt` (sekcja 5).
   - **Ustalone w etapie 4:** komora SOFA (91 ml) ≠ MuJoCo (30 ml), więc A_V = 17 ml, V_prefill = 20 ml, Q_max = 250 ml/s (decyzja: widoczny ruch). Prefill > ~22 ml wybocza kręgosłup (ciśnienie wspólne). Komenda pompy ma dodaną kompensację opóźnienia τ_pump·d²V_ref/dt² (bez niej 16% przeregulowania przy 2 Hz). Wynik: ±12.7° przy dt 2 ms, −5% względem dt 1 ms (README, etap 4).
5. **Woda**: to samo z `environment="water"`. Porównanie amplitudy i przesunięcia fazowego z wodą vs bez. Ciąg (definicja w sekcji 5) = jakościowy „ciąg na uwięzi”. **Gotowe, gdy:** `max(c·dt/m)` < 0.5 przez cały przebieg.
   - **Ustalone w etapie 5:** opór jawny wymaga dt = 0.5 ms (max(c·dt/m) = 0.27; przy 1 ms 0.54 na płetwie, wynik różni się o 1.4% amplitudy i 5% ciągu). W wodzie amplituda 0.55× powietrza (±7.3°), faza +30°, ciąg +67 mN (jakościowo), Δp prawie bez zmian (README, etap 5).
6. **Przeglądy** (protokół: każdy punkt = osobna symulacja, 2 cykle rozbiegu + 3 cykle uśredniania; podaj czas obliczeń całego przeglądu):
   - częstotliwość 0.5–3 Hz (te same punkty co `MuJoCo/scripts/sweep_frequency.py`) → amplituda końcówki, średni ciąg, max |Δp|, czas aktywności zaworu. Porównaj kształt z `MuJoCo/results/s5_sweep.png`.
   - moduł Younga ×0.5, ×1, ×2, w dwóch wariantach:
     a) quasi-statycznie (jak etap 2): ten sam ΔV → ciśnienie skaluje się ~liniowo z E, a **ugięcie prawie się nie zmienia**,
     b) dynamicznie w wodzie przy 2 Hz: tu E zmienia amplitudę i fazę, bo przesuwa rezonans ogona względem częstotliwości machania.
   Lekcja do README: przy sterowaniu objętością jednorodny liniowy materiał bez obciążeń zewnętrznych ugina się tak samo przy każdym E; sztywność decyduje o **wymaganym ciśnieniu** (pompa, zawór, szczelność), a o ruchu dopiero przez obciążenia (woda, bezwładność, grawitacja). Dla kontrastu jeden punkt w trybie `valueType="pressure"`: to samo p → ugięcie ~1/E.
   - **Ustalone w etapie 6:** w wodzie brak rezonansu (amplituda maleje z f), ciąg ma maksimum ~2.25 Hz, powyżej nasyca się pompa (Q_max), zawór nie otwiera się. Prawo skalowania z E potwierdzone (README, etap 6). Przegląd liczony równolegle (`fishsofa/parallel.py`): 68 min zamiast ~7 h.
7. **(Opcjonalnie) Eksport PRBM** (`export_prbm.py`) → `results/prbm.json`, klucze odpowiadające polom `MuJoCo/fishsim/config.py`:
   - `joint_x` [m] – położenia N = 5 przegubów (co `segment_length`),
   - `stiffness` [N·m/rad] – sztywność każdego przegubu. Wyznacz ją z **osobnych przypadków obciążenia** (komory bez aktuacji, mała boczna siła na płetwie przez `ConstantForceField`): moment w przekroju przegubu / kąt względny sąsiednich segmentów. Sama aktuacja ciśnieniem nie wystarczy, bo nie rozdziela sztywności poszczególnych przegubów,
   - `A_eff_r_eff` [m³] – moment na przegubach napędzanych na jednostkę Δp (z etapów 2–3),
   - `C_h` [m³/Pa] – podatność komór dV/dp przy zablokowanym ogonie, `V0_chamber` [m³],
   - `tendon_weights` – względny udział przegubów napędzanych w ugięciu od ciśnienia.
   Opisz metodę i przybliżenia (liniowość, mały kąt, segmenty sztywne). Uwaga: MuJoCo dziś przyjmuje jedno `stiffness_actuated` i liczy sztywności pasywne z `passive_resonance_hz`, więc wczytanie `prbm.json` po stronie MuJoCo to osobna, przyszła praca (wypisz ją w README, nie implementuj tutaj).

## 9. Wyniki (results/)

PNG + CSV: `s1_mesh_report.txt`, `s2_pv_curve.png`, `s2_tip_angle.png`, `s3_symmetry.png`, `s4_air_flapping.png`, `s5_water_vs_air.png`, `s6_freq_sweep.png`, `s6_young_sweep.png` (oba warianty a/b), opcjonalnie `prbm.json`. Zrzut ekranu z GUI ze zgiętym ogonem (jeśli da się zrobić automatycznie; jeśli nie, instrukcja w README jak go zrobić ręcznie).

## 10. Testy (tests/test_sanity.py, uruchamiane headless)

Testy używają grubej siatki testowej (`mesh_size_test`). Budżet: cały `pytest` < ~3 min. Uruchamianie: `source scripts/env.sh && pytest -q`.

- Siatka: brak czworościanów o objętości ≤ 0; normalne powierzchni zewnętrznej na zewnątrz; siatka lustrzana (węzły parami symetryczne względem XZ).
- Scena się inicjalizuje i robi 100 kroków bez NaN i bez „eksplozji” (max przemieszczenie węzła < długość ogona); solver ograniczeń zbiega w każdym kroku.
- Znak aktuacji: +ΔV w L → `pressure` > 0, `cavityVolume` rośnie, θ_tip ma znak zgodny z definicją z sekcji 5.
- Symetria: θ_tip dla L(+ΔV) ≈ −θ_tip dla R(+ΔV), błąd < 5%.
- Monotoniczność: na 0…`dV_max` większe ΔV → większe ugięcie i większe ciśnienie.
- Hydraulika (jednostkowo, bez SOFA): `V_p` śledzi `V_ref`, zawór nie zmienia sumy objętości, asercja prefillu łapie zbyt małe `V_prefill`.
- Hydraulika (w scenie): zmierzone `cavityVolume_L + cavityVolume_R` stałe w granicach tolerancji solvera.
- Woda (jednostkowo, `water.py` na syntetycznych prędkościach): moc oporu F·v ≤ 0 na każdym trójkącie; zerowa prędkość → zerowa siła.
- Woda (w scenie): amplituda z wodą < amplituda bez wody przy tej samej komendzie; `max(c·dt/m)` < 0.5.
- Moduł Younga ×2 przy tym samym ΔV (quasi-statycznie, g = 0): ciśnienie ×2 (±10%), ugięcie zmienia się < 5%.
- Moduł Younga ×2 przy tym samym ciśnieniu (`valueType="pressure"`, `value = p·dt`): ugięcie ~×0.5 (±15%).
- Jednostki ciśnienia: ten sam stan ustalony przy `dt` i `2·dt` daje to samo ciśnienie w Pa (pilnuje dzielenia przez `dt`).

## 11. README – obowiązkowe sekcje

- Jak zainstalować (dokładna wersja SOFA, wersja Pythona, skąd SoftRobots, licencja, co trzeba było doinstalować na Fedorze, `scripts/env.sh`).
- Jak uruchomić GUI i scenariusze headless.
- Ustalenia z etapu 0 (semantyka i znak `volumeGrowth`).
- Co pokazuje każdy wykres, w 2–3 zdaniach dla osoby uczącej się.
- Lekcja z etapu 6: sterowanie objętością vs ciśnieniem i rola modułu Younga.
- Numeryka: wybrane `dt` i dlaczego (stabilność oporu, tłumienie numeryczne), stosunek czasu symulacji do rzeczywistego.
- **Ograniczenia modelu**: brak CFD i efektów reaktywnych (o ile nie dodano masy dodanej), jawny opór wody (ograniczenie kroku), ogon przymocowany (brak swobodnego pływania), liniowy materiał korotacyjny zamiast hiperelastycznego, niezidentyfikowane parametry, brak kontaktu ścianek komór, komory bez kanałów doprowadzających.
- Jak kalibrować: pomiar krzywej p–V i kąta ugięcia na prawdziwym ogonie (etap 2, drugi króciec otwarty), dopasowanie modułu Younga, pomiar ciągu na wadze w wannie i porównanie z etapem 5.

## 12. Definition of done

- `source scripts/env.sh && pytest -q` (headless) → wszystkie testy zielone.
- `python scripts/run_scenarios.py` → wykresy w `results/`.
- `scripts/run_gui.sh` → widać ogon machający w GUI SOFA, z wizualizacją ciśnienia w komorach (jeśli ta wersja SoftRobots ją ma; sprawdź w etapie 0, inaczej kolorowanie komór wg ciśnienia z kontrolera).
- README pozwala zrozumieć wyniki i ograniczenia bez czytania kodu.
