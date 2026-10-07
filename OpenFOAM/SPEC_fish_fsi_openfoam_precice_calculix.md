# SPEC: Demo FSI – miękki ogon ryby w wodzie (OpenFOAM + preCICE + CalculiX)

> Instrukcja dla Claude Code. Umieść ten plik w pustym folderze projektu i napisz:
> „Przeczytaj SPEC_fish_fsi_openfoam_precice_calculix.md i zrealizuj go etapami. Zacznij od planu.”
> Ten projekt wymaga Linuksa (natywnie, WSL2 albo VM/Docker). Obliczenia trwają długo, więc etapy mają być małe.

## 0. Cel i kontekst

Zbuduj **uproszczoną, edukacyjną** symulację FSI (fluid–structure interaction) miękkiego ogona ryby napędzanego hydraulicznie. Ma pokazać to, czego nie potrafią MuJoCo ani SOFA:
- prawdziwy przepływ wody (Navier–Stokes, OpenFOAM) wokół odkształcającego się ogona,
- dwukierunkowe sprzężenie: woda odkształca ogon, ogon zmienia przepływ (preCICE),
- ślad wirowy za ogonem i ciąg/opór liczony z ciśnienia i naprężeń na powierzchni,
- **efekt masy dodanej** i to, dlaczego sprzężenie silikon–woda wymaga schematu niejawnego (implicit coupling).

To demo **2D** (przekrój ogona w widoku z góry), z możliwym rozszerzeniem do 3D na końcu. To **nie jest** skalibrowany model. Parametry są placeholderami i muszą być tak oznaczone.

Użytkownik to młody inżynier mechatronik, który się uczy. **Komentarze po polsku** w plikach konfiguracyjnych (`#` w OpenFOAM, `**` w CalculiX, `<!-- -->` w XML preCICE) wyjaśniające, co robi każdy blok i dlaczego.

## 1. Zasady pracy (ważne)

1. **Nie pisz od zera. Zacznij od oficjalnego tutorialu preCICE `perpendicular-flap` (fluid-openfoam + solid-calculix)**, uruchom go bez zmian, a dopiero potem modyfikuj krok po kroku. Każda modyfikacja = osobny etap z działającym wynikiem.
2. **Zgodność wersji to największe ryzyko.** preCICE v3 wymaga tutoriali i adapterów w wersjach dla v3. Adapter OpenFOAM domyślnie wspiera najnowsze OpenFOAM z openfoam.com (nie openfoam.org). Użyj zestawu wersji z aktualnej **preCICE Distribution** (precice.org → Distribution) i zapisz dokładne wersje w README. Nie mieszaj wersji „na oko”.
3. Preferowana instalacja: pakiety z preCICE Distribution / demo VM preCICE albo pakiety .deb (preCICE, adapter CalculiX) + oficjalne repozytorium OpenFOAM.com. Sprawdź aktualne instrukcje na precice.org, nie zakładaj.
4. Etapy obliczeniowe: najpierw **zgrubna siatka i krótki czas** (sekundy symulacji, minuty obliczeń). Dopiero gdy działa, zagęszczaj. Zawsze podaj użytkownikowi szacowany czas obliczeń, zanim uruchomisz coś dłuższego niż ~15 min.
5. Jeśli sprzężenie się rozbiega, **nie zgaduj losowo**. Diagnozuj: krok czasowy, schemat sprzężenia, relaksacja, jakość siatki po deformacji. Wynik diagnozy zapisuj w `NOTES.md`.
6. Nie wymyślaj „realistycznych” wartości. Każdy parametr: komentarz `PLACEHOLDER – do identyfikacji z pomiarów`.

## 2. Struktura projektu

```
fish_fsi_demo/
  README.md
  NOTES.md                  # dziennik: co się rozbiegło, dlaczego, jak naprawione
  versions.txt              # dokładne wersje preCICE, adapterów, OpenFOAM, CalculiX
  00-reference-flap/        # kopia oficjalnego tutorialu perpendicular-flap (bez zmian)
  01-solid-only/            # CalculiX sam: ogon z komorami, ciśnienie, bez wody
  02-fluid-only/            # OpenFOAM sam: sztywny ogon, przepływ, sprawdzenie siatki i oporu
  03-fsi-passive/           # FSI: ogon pasywny w strumieniu (bez aktuacji)
  04-fsi-actuated/          # FSI: ogon napędzany ciśnieniem w komorach, woda stojąca
  05-fsi-inflow/            # FSI: napęd + napływ (ryba płynąca) -> bilans ciąg/opór
  tools/
    make_geometry.py        # gmsh: geometria 2D ogona z komorami (dla CalculiX i OpenFOAM)
    postprocess.py          # siły, kąt końcówki, wykresy -> results/
    pv_snapshots.py         # opcjonalnie: pvpython, zrzuty pola wirowości
  results/
```

## 3. Model fizyczny (uproszczony)

- **Geometria 2D**: ogon jako zwężający się pasek ok. 0.15 m długości, grubość 0.03 → 0.01 m (placeholder), przymocowany przednią krawędzią do **nieruchomej sztywnej „głowy”** (półelipsa). W środku dwie podłużne komory (lewa/prawa) rozdzielone ścianką środkową.
- **Domena płynu**: prostokąt wokół, min. ~3 długości ogona przed, ~8 za, ~3 po bokach (placeholdery, sprawdź wpływ granic).
- **Woda**: ρ = 1000 kg/m³, ν ≈ 1e-6 m²/s.
- **Liczba Reynoldsa**: przy realnej prędkości i rozmiarze Re wynosi rząd 1e4–1e5, czyli przepływ jest turbulentny. **Demo celowo liczy laminarnie** (`pimpleFoam`, laminar) i to jest uproszczenie do opisania w README. Opcjonalnie: wariant z obniżonym Re (np. większa lepkość) jako „poprawny laminarnie” punkt odniesienia. Opisz kompromis.
- **Ciało stałe (CalculiX)**: materiał liniowo sprężysty, ale **analiza nieliniowa geometrycznie** (`NLGEOM`), bo ugięcia są duże. Moduł Younga silikonu ~1e5–1e6 Pa, Poisson 0.45, ρ ~1070 kg/m³ (placeholdery). Elementy jak w tutorialu (sprawdź, jakich używa aktualna wersja i dlaczego).
- **Aktuacja**: ciśnienie na ściankach komór przez `*DLOAD` z `*AMPLITUDE` (sinus w czasie, przeciwna faza L/R, start rampą od zera). **Różnica względem demo SOFA**: tu wymuszamy ciśnienie, a nie objętość. Opisz w README, co to oznacza fizycznie (pompa hydrauliczna wymusza raczej objętość, więc to przybliżenie).

## 4. Kluczowe zagadnienia numeryczne (wyjaśnić w README)

1. **Masa dodana**: gęstość silikonu ≈ gęstość wody. W takim przypadku jawne sprzężenie (explicit) jest niestabilne. Użyj **sprzężenia niejawnego** (`serial-implicit` lub `parallel-implicit`) z akceleracją quasi-Newton (IQN-ILS). Etap 3 ma to zademonstrować: uruchom raz explicit (pokaż, że się rozbiega), raz implicit.
2. **Ruch siatki**: OpenFOAM deformuje siatkę płynu (`dynamicMotionSolverFvMesh`, `displacementLaplacian` z dyfuzyjnością rosnącą przy ciele). Przy dużych amplitudach komórki się degenerują. Ogranicz amplitudę ogona (np. końcówka ≤ ~15–20% długości) i monitoruj `checkMesh`-owe metryki jakości w czasie. Opisz, że duże amplitudy wymagają innych technik (np. remeshing, overset), które są poza zakresem demo.
3. **Mapowanie danych** na interfejsie: siatki ciała stałego i płynu się nie pokrywają. Wyjaśnij wybraną metodę mapowania (z tutorialu) w komentarzu w `precice-config.xml`.
4. **Krok czasowy**: ten sam w obu solverach (lub zgodny z preCICE v3), z ograniczeniem liczby Couranta w OpenFOAM.

## 5. Etapy realizacji

0. **Instalacja + referencja**: zainstaluj zgodny zestaw, uruchom `perpendicular-flap` (OpenFOAM–CalculiX) bez zmian. Porównaj przemieszczenie z danymi referencyjnymi tutorialu (jeśli dostępne). Zapisz `versions.txt`.
1. **Tylko ciało stałe** (`01-solid-only`): geometria ogona z komorami w CalculiX, quasi-statyczna rampa ciśnienia w komorze L. Wykres: kąt/ugięcie końcówki vs ciśnienie. Test symetrii L/R.
2. **Tylko płyn** (`02-fluid-only`): sztywny prosty ogon w napływie U (placeholder ~0.2 m/s). Opór, rozkład ciśnienia, test zbieżności siatki na 2–3 gęstościach (zgrubnie). Sprawdź, czy granice domeny nie wpływają na wynik.
3. **FSI pasywne** (`03-fsi-passive`): ogon bez aktuacji w napływie. Demonstracja: explicit vs implicit coupling (masa dodana). Wykres: przemieszczenie końcówki i liczba iteracji sprzężenia na krok.
4. **FSI z napędem, woda stojąca** (`04-fsi-actuated`): sinus ciśnienia w komorach, U = 0. Ciąg = uśredniona po cyklu siła na interfejsie w kierunku osi ryby. Porównaj amplitudę końcówki z etapem 1 przy tym samym ciśnieniu (lekcja: woda tłumi i opóźnia ruch).
5. **FSI z napędem i napływem** (`05-fsi-inflow`): 2–3 prędkości napływu. Bilans: przy jakiej prędkości średnia siła X ≈ 0 (szacunek prędkości pływania ryby z przymocowaną głową). Policz liczbę Strouhala `St = f·A/U` i porównaj z zakresem typowym dla ryb (literatura podaje ok. 0.2–0.4; sprawdź źródło i je zacytuj w README).
6. **Przegląd częstotliwości**: tylko 3–4 punkty (to drogie). Ciąg i amplituda vs f.
7. **(Opcjonalnie) 3D**: jedno z poprzednich ustawień w 3D, zgrubna siatka. Tylko jeśli użytkownik potwierdzi czas obliczeń.

## 6. Wyniki (results/)

PNG + CSV:
- `e1_tip_vs_pressure.png`
- `e2_mesh_convergence.png`
- `e3_explicit_vs_implicit.png` (z liczbą iteracji sprzężenia)
- `e4_tip_angle_water_vs_dry.png`, `e4_thrust_cycle.png`
- `e5_force_vs_inflow.png` (+ wartość St)
- `e6_freq_sweep.png`
- zrzuty pola wirowości ze śladu za ogonem (pvpython lub ręczna instrukcja dla ParaView w README).

## 7. Testy / kryteria poprawności

Zautomatyzuj w `tools/check_results.py`:
- Etap 0: przemieszczenie końcówki flapu zgodne z referencją tutorialu w rozsądnej tolerancji.
- Etap 1: symetria L/R (< 5%), monotoniczność ugięcia vs ciśnienie.
- Etap 2: opór zmienia się < ~5–10% między dwiema najgęstszymi siatkami (jeśli nie, opisz).
- Etap 3: implicit zbiega w ograniczonej liczbie iteracji na krok; explicit pokazuje narastanie błędu/rozbieganie.
- Każdy etap FSI: brak ujemnych objętości komórek (sprawdź log OpenFOAM), brak NaN, residua preCICE poniżej progu.
- Etap 4: amplituda w wodzie < amplituda „na sucho” przy tym samym ciśnieniu.

## 8. README – obowiązkowe sekcje

- Dokładne wersje i jak odtworzyć instalację.
- Jak uruchomić każdy etap (`./run.sh` w katalogach fluid i solid, jak w tutorialach preCICE) i ile to trwało na tej maszynie.
- Co pokazuje każdy wykres, 2–3 zdania dla osoby uczącej się.
- **Ograniczenia modelu**: 2D zamiast 3D (brak efektów końcówek płetwy), przepływ laminarny przy realnie turbulentnym Re, głowa nieruchoma (brak swobodnego pływania i odrzutu głowy), wymuszenie ciśnieniem zamiast objętością, materiał liniowy, ograniczona amplituda przez deformację siatki, niezidentyfikowane parametry.
- Jak to wykorzystać przy projekcie: porównanie wariantów geometrii płetwy i sztywności (względnie, nie absolutnie), walidacja ciągu z modelu MuJoCo/SOFA, plan pomiaru ciągu na uwięzi w wannie.

## 9. Definition of done

- Etapy 0–5 działają i każdy ma wykres w `results/`.
- `tools/check_results.py` przechodzi lub każdy niespełniony warunek jest wyjaśniony w `NOTES.md`.
- README pozwala osobie uczącej się odtworzyć wyniki i rozumieć ograniczenia.
