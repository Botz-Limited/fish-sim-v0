# SPEC: Demo OpenModelica – model systemowy robota-ryby (elektryka + hydraulika + mechanika + balast)

> Instrukcja dla Claude Code. Umieść ten plik w pustym folderze projektu i napisz:
> „Przeczytaj SPEC_fish_openmodelica_demo.md i zrealizuj go etapami. Zacznij od planu.”

## 0. Cel i kontekst

Zbuduj **uproszczony, edukacyjny** model systemowy robota-ryby w języku Modelica, uruchamiany w OpenModelica. Ma pokazać to, w czym Modelica jest najlepsza, a czego nie dają MuJoCo, SOFA ani CFD:
- **modelowanie wielodziedzinowe i akauzalne**: silnik DC → pompa → przewody → komory → ogon, połączone złączami fizycznymi (napięcie/prąd, moment/prędkość, ciśnienie/przepływ), a nie strzałkami sygnałów,
- **bilans energii**: gdzie ucieka energia z baterii (straty w silniku, pompie, przewodach, zaworze, wodzie),
- **dynamika hydrauliki**: pasmo pompy, sztywność komór, działanie zaworu przelewowego,
- **system balastowy**: tłok/strzykawka napędzana silnikiem i śrubą, regulacja głębokości,
- **eksport FMU**, żeby model hydrauliki dało się podpiąć do innych symulatorów (np. demo MuJoCo).

Geometria i hydrodynamika są tu **mocno uproszczone** (modele 1D o skupionych parametrach). Ten model odpowiada na pytania typu „czy pompa i bateria wystarczą”, a nie „jak dokładnie płynie woda”.

To **nie jest** skalibrowany model. Parametry to placeholdery i mają być tak oznaczone.

Użytkownik to młody inżynier mechatronik, który się uczy. **Komentarze i opisy po polsku**: komentarze w kodzie Modelica (`//` i stringi opisowe parametrów) oraz adnotacje `Documentation` w każdym modelu wyjaśniające równania fizyczne.

## 1. Zasady pracy (ważne)

1. Pracuj etapami (sekcja 7). Po każdym etapie: `checkModel` bez błędów (liczba równań = liczba niewiadomych), symulacja, wykres, test. Dopiero potem dalej.
2. Na starcie ustal wersje: OpenModelica (`omc --version`), Modelica Standard Library (MSL), OMPython. Jednostki SI z MSL 4.x to `Modelica.Units.SI`; w starszym MSL 3.2.x było `Modelica.SIunits`. **API OMPython zmieniało się ostatnio** (klasy sesji), więc sprawdź dokumentację zainstalowanej wersji, zamiast kopiować starsze przykłady.
3. **Nie używaj komercyjnych bibliotek** (np. Modelon Hydraulics). Tylko MSL + własny lekki pakiet.
4. Hydraulikę napisz jako **własny mały pakiet** (`FishHydraulics`) z prostym złączem (ciśnienie `p` jako potencjał, przepływ objętościowy `V_flow` jako zmienna przepływowa `flow`). Uzasadnienie w README: `Modelica.Fluid` jest potężne, ale ciężkie (media, inicjalizacja, entalpia) dla małego układu z nieściśliwą wodą, a własny pakiet uczy, jak działają złącza akauzalne. Opcjonalnie (etap 8): ten sam obwód na `Modelica.Fluid` do porównania.
5. Dobre praktyki numeryczne: dla `|x|·x` używaj `smooth`/`noEvent` lub regularyzacji w pobliżu zera (opisz dlaczego: zdarzenia i nieróżniczkowalność spowalniają solver). Jawne `initial equation`. Unikaj niepotrzebnych pętli algebraicznych.
6. Nie wymyślaj „realistycznych” wartości. Każdy parametr ma w opisie `PLACEHOLDER – do identyfikacji`.

## 2. Struktura projektu

```
fish_modelica_demo/
  README.md
  FishRobot/                    # pakiet Modelica (struktura katalogowa: package.mo + package.order)
    package.mo
    Interfaces/                 # złącze HydraulicPort, bazowe klasy 2-portowe
    Hydraulics/                 # GearPump, Chamber, Pipe, ReliefValve, CheckValve (opcja), Reservoir
    Tail/                       # TailEquivalent (1 DOF, rotacyjny)
    Buoyancy/                   # BallastSyringe, VerticalDynamics
    Propulsion/                 # SurgeDynamics (1D ruch do przodu)
    Control/                    # CPG (sinus), DepthPID z anti-windup
    Examples/                   # modele scenariuszy (każdy z annotation experiment(...))
    Tests/                      # małe modele testowe komponentów
  scripts/
    run_all.py                  # OMPython: kompilacja, symulacja, wykresy -> results/
    sweep.py                    # przeglądy parametrów
    export_fmu.py               # eksport FMU podukładu hydraulika+ogon
    fmu_demo.py                 # FMPy: uruchomienie FMU z Pythona (pętla co-sim)
    check_tests.py              # automatyczne asercje na wynikach
  results/
```

## 3. Komponenty

### 3.1 Elektryka i napęd pompy (MSL)
- Bateria jako źródło napięcia z rezystancją wewnętrzną (placeholder), mostek H jako idealne sterowane źródło napięcia `u·U_bat`, `u ∈ [−1, 1]`.
- Silnik DC z MSL (np. `Modelica.Electrical.Machines` lub obwód R-L + `Modelica.Electrical.Analog.Basic.RotationalEMF` + inercja wirnika). Wybierz prostszy wariant i uzasadnij.

### 3.2 Hydraulika (`FishHydraulics`, własne)
- `GearPump`: wyporowa, odwracalna. `V_flow = D·ω − k_leak·Δp`, moment `τ = D·Δp/η_m`. Złącze rotacyjne z MSL po stronie wału.
- `Chamber`: komora silikonowa z **nieliniową podatnością** `p = f(V)` z tabeli (`Modelica.Blocks.Tables.CombiTable1Ds`). Tabelę placeholderową zrób tak, żeby dało się ją podmienić na krzywą p–V z demo SOFA albo z pomiaru. Wyjście: objętość `V` (do modelu ogona).
- `Pipe`: strata ciśnienia laminarno-turbulentna (`Δp = R_lam·V_flow + R_turb·|V_flow|·V_flow`, regularyzowane), opcjonalnie inertancja słupa cieczy.
- `ReliefValve`: zawór przelewowy z charakterystyką gładką (bez twardego przełączania), ciśnienie otwarcia `p_set`.
- Układ zamknięty jak w SoFi (MIT): pompa przepompowuje wodę między komorą L i R. Komory startują wstępnie napełnione (`V_prefill`).

### 3.3 Ogon (`TailEquivalent`, 1 DOF)
- Równoważny ruch obrotowy kąta ogona θ: `(J + J_added)·θ̈ = τ_hyd − k·θ − c·θ̇ − c_h·|θ̇|·θ̇`.
- `τ_hyd = A_eff·r_eff·(p_L − p_R)` **lub** (lepiej, opisz różnicę) `θ` wynika z różnicy objętości komór przez sztywność układu. Wybierz jedno sformułowanie, zachowaj spójność energetyczną (praca hydrauliczna = praca mechaniczna) i wyjaśnij to w dokumentacji.
- Złącze `Modelica.Mechanics.Rotational`, żeby moc była liczona automatycznie.
- Masa dodana `J_added` i tłumienie hydrodynamiczne `c_h` to placeholdery.

### 3.4 Napęd do przodu (`SurgeDynamics`, 1D)
- `(m + m_added_x)·dU/dt = T − ½·ρ·C_d·A·|U|·U`.
- Ciąg `T`: **jawnie oznaczony placeholderowy model empiryczny** w funkcji prędkości bocznej końcówki ogona (np. kwadratowy w `L·θ̇`). Opisz w Documentation, że to najsłabsze ogniwo modelu i że jego parametr trzeba wyznaczyć z pomiaru ciągu na uwięzi lub z demo CFD/MuJoCo.

### 3.5 Balast (`BallastSyringe` + `VerticalDynamics`)
- Strzykawka/tłok: silnik DC → śruba pociągowa (`Modelica.Mechanics.Rotational` → `Translational` przez `IdealGearR2T`) → objętość pęcherza `V_b = A_tłoka·x`, ograniczniki skrajnych położeń.
- Ruch pionowy: `(m + m_added_z)·z̈ = ρ·g·(V_hull + V_b) − m·g − ½·ρ·C_dz·A_z·|ż|·ż`.
- Opcjonalnie: ściśliwość kadłuba/powietrza z głębokością (zmiana `V_hull` z ciśnieniem) jako lekcja, dlaczego nieskompensowany balast jest niestabilny w pionie. Jeśli dodasz, zrób przełącznik.

### 3.6 Sterowanie (`Control`)
- CPG: `u(t) = A·sin(2π f t) + bias` z nasyceniem i rampą startową.
- `DepthPID`: `z_ref → prędkość silnika strzykawki`, anti-windup, nasycenie. Możesz użyć `Modelica.Blocks.Continuous.LimPID` i opisać jego parametry.

## 4. Bilans energii (kluczowa funkcja demo)

Dodaj w modelu scenariusza zmienne mocy i energii (całki): energia z baterii, straty w rezystancji silnika, straty pompy (przecieki + η_m), straty w przewodach, w zaworze przelewowym, moc rozproszona w wodzie przez ogon (`c·θ̇² + c_h·|θ̇|·θ̇²`), praca napędu do przodu `T·U`. Sprawdź zamknięcie bilansu (suma strat + zmiana energii zmagazynowanej = energia z baterii) z błędem numerycznym < 1%. To jest test poprawności całego modelu.

## 5. Scenariusze (`Examples/`)

1. `HydraulicsStep`: skok (rampa) komendy pompy, ogon zablokowany → ciśnienia, przepływ, prąd silnika.
2. `TailFlapping`: sinus komendy, ogon swobodny → kąt ogona, ciśnienia, prąd.
3. `FrequencySweep` (przez `sweep.py`): f = 0.5…4 Hz → amplituda ogona, szczytowe ciśnienie, średni prąd. **Lekcja**: gdzie pasmo jest ograniczone przez przepływ pompy, a gdzie przez zawór przelewowy.
4. `ReliefValveDemo`: za duża amplituda komendy → zawór się otwiera, widać stratę energii.
5. `EnergyBudget`: 60 s pływania → wykres kołowy/słupkowy rozkładu energii + szacowany czas pracy na baterii (pojemność to placeholder).
6. `DepthControl`: skoki zadanej głębokości (−0.5 → −1.5 → −1.0 m) → głębokość, objętość pęcherza, prąd silnika strzykawki.
7. `SwimForward`: CPG + surge → prędkość ustalona vs częstotliwość (z jawnym zastrzeżeniem o modelu ciągu).
8. **(Opcjonalnie)** `HydraulicsMSLFluid`: obwód z etapu 1 zbudowany z `Modelica.Fluid` + `Modelica.Media.Water.ConstantPropertyLiquidWater`, porównanie wyników i złożoności.

## 6. FMU

- `export_fmu.py`: wyeksportuj podukład „mostek H + silnik + pompa + komory + ogon” jako **FMU 2.0 Co-Simulation** (wejście: komenda `u`; wyjścia: kąt i prędkość ogona, moment, `p_L`, `p_R`, prąd).
- `fmu_demo.py`: uruchom FMU przez **FMPy** w pętli Pythona z krokiem 2 ms i porównaj z wynikiem z OpenModelica (powinny się pokrywać).
- Zanotuj w README: FMU zawiera skompilowane binaria i **działa tylko na systemie, na którym go zbudowano**. Opisz, jak w przyszłości podpiąć go pod demo MuJoCo (moment z FMU → aktuator przegubu), ale samego podpięcia nie implementuj, chyba że użytkownik poprosi.

## 7. Etapy realizacji

1. Szkielet pakietu, złącze hydrauliczne, `Pipe` + `Reservoir` + test (prawo Hagena–Poiseuille’a dla laminarnej części: sprawdź spadek ciśnienia analitycznie).
2. `Chamber` + `ReliefValve` + testy (zachowanie objętości w układzie zamkniętym, `p ≤ p_set + tolerancja`).
3. Silnik DC + `GearPump` → scenariusz 1.
4. `TailEquivalent` → scenariusze 2–4.
5. Bilans energii → scenariusz 5 (test zamknięcia bilansu).
6. Balast + pion → scenariusz 6.
7. Surge → scenariusz 7.
8. FMU + FMPy.
9. (Opcjonalnie) wariant `Modelica.Fluid`.

## 8. Testy (`scripts/check_tests.py`)

- Każdy model z `Examples/` i `Tests/` przechodzi `checkModel` (zbilansowany) i się symuluje.
- Rura: Δp zgodne z wzorem analitycznym (< 1%).
- Układ zamknięty: `V_L + V_R = const` (< 1e-9 względnie).
- Zawór: ciśnienie nie przekracza `p_set` o więcej niż założona tolerancja charakterystyki.
- Statyka balastu: przy `V_b` neutralnym ż → 0; większe `V_b` → wynurzanie.
- Bilans energii zamknięty < 1%.
- FMU vs OpenModelica: różnica kąta ogona < 1% amplitudy.
- Kierunki: dodatnia komenda pompy → dodatni kąt ogona (konwencja opisana w README).

## 9. README – obowiązkowe sekcje

- Wersje (OpenModelica, MSL, OMPython, FMPy) i instalacja.
- Jak otworzyć pakiet w **OMEdit** i zobaczyć diagramy połączeń (to najlepszy sposób, żeby zrozumieć model akauzalny). Proste ikony komponentów, żeby diagram był czytelny.
- Jak uruchomić `run_all.py`, `sweep.py`, `export_fmu.py`.
- Co pokazuje każdy wykres, 2–3 zdania dla osoby uczącej się.
- **Ograniczenia**: ogon jako 1 DOF, ciąg z empirycznego placeholderu, brak sprzężenia ruchów (surge, pion i obrót niezależne), brak hydrodynamiki przestrzennej, parametry niezidentyfikowane.
- **Plan kalibracji**: które parametry zmierzyć na stole (rezystancja i stała silnika, wydajność pompy vs ciśnienie, krzywa p–V komory, moment/kąt ogona, ciąg na uwięzi) i w jakiej kolejności.

## 10. Definition of done

- `python scripts/run_all.py` kompiluje i symuluje wszystkie scenariusze, zapisuje wykresy w `results/`.
- `python scripts/check_tests.py` przechodzi.
- FMU działa w FMPy.
- Pakiet otwiera się w OMEdit z czytelnymi diagramami.
