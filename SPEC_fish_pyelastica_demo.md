# SPEC: Demo PyElastica – miękka ryba jako pręt Cosserata

> Instrukcja dla Claude Code. Umieść ten plik w pustym folderze projektu i napisz:
> „Przeczytaj SPEC_fish_pyelastica_demo.md i zrealizuj go etapami. Zacznij od planu.”

## 0. Cel i kontekst

Zbuduj **uproszczoną, edukacyjną** symulację robota-ryby w PyElastica, w której ciało i ogon to ciągły, miękki pręt Cosserata (zginanie, skręcanie, ścinanie, rozciąganie). Ma pokazać to, czego nie dają pozostałe narzędzia:
- ciągłe odkształcenie smukłego ogona przy **niskim koszcie** (1D zamiast 3D FEM),
- **swobodne pływanie** miękkiego ciała (nie tylko ogon przymocowany),
- jak modelować **napęd wewnętrzny** (hydrauliczne komory) tak, by nie łamał zasad dynamiki,
- własny model sił wody dla dużych liczb Reynoldsa (opór + siła reaktywna),
- wypór i balast na ciele odkształcalnym.

To **nie jest** skalibrowany model. Parametry to placeholdery i mają być tak oznaczone.

Użytkownik to młody inżynier mechatronik, który się uczy. **Komentarze w kodzie po polsku**, wyjaśniające fizykę (co oznacza dana wielkość w teorii prętów Cosserata, skąd bierze się dana siła).

## 1. Zasady pracy (ważne)

1. Pracuj etapami (sekcja 7). Po każdym etapie uruchom kod i testy, pokaż wynik, dopiero potem dalej.
2. **API PyElastica zmieniało się między wersjami** (np. moduł `elastica.wrappers` → `elastica.modules`, importy przez `import elastica as ea`, osobny moduł tłumienia `Damping`). Na starcie ustal zainstalowaną wersję i wzoruj się na przykładach z repozytorium **dla tej wersji** (`examples/`, np. przypadki osiowego rozciągania, zginania belki, „continuum snake”, wiciowce).
3. **Nie używaj wbudowanego `SlenderBodyTheory` jako modelu wody dla ryby.** To teoria smukłego ciała dla przepływu Stokesa (brak bezwładności płynu), czyli dla mikroorganizmów z wiciami, a nie dla ryby przy Re ~ 1e4–1e5. **Zweryfikuj to w kodzie źródłowym** zainstalowanej wersji (jakie przyjmuje parametry, jaki wzór liczy) i opisz wynik w README. Możesz użyć go wyłącznie w etapie porównawczym, żeby pokazać, że daje złą fizykę dla ryby.
4. PyElastica nie wymusza jednostek. Używaj **SI** konsekwentnie.
5. Integrator jest jawny (np. `PositionVerlet`), więc krok czasowy jest ograniczony sztywnością pręta. Wyznacz go świadomie (zależność od długości elementu, modułu Younga, gęstości), opisz wzór w komentarzu i zawsze podaj szacowany czas obliczeń przed długim przebiegiem.
6. PyElastica nie zapisuje wyników automatycznie. Użyj callbacków z rozsądną częstotliwością zapisu.
7. Nie wymyślaj „realistycznych” wartości. Każdy parametr: komentarz `# PLACEHOLDER – do identyfikacji z pomiarów`.

## 2. Struktura projektu

```
fish_elastica_demo/
  README.md
  requirements.txt              # pyelastica (wersja przypięta), numpy, numba, matplotlib, pytest
  fishrod/
    config.py                   # dataclass ze WSZYSTKIMI parametrami
    build.py                    # symulator (klasa z mixinami), pręt(y), BC, tłumienie, callbacki
    hydraulics.py               # model ODE pompy i komór (jak w demo MuJoCo/Modelica)
    actuation.py                # napęd wewnętrzny: krzywizna spoczynkowa z ciśnienia
    water.py                    # własne siły wody (klasa dziedzicząca po ea.NoForces)
    buoyancy.py                 # wypór per element + pęcherz w głowie
    run.py                      # pętla integracji z krokiem hydrauliki
  scripts/
    run_scenarios.py
    animate.py                  # animacja 2D/3D matplotlib -> GIF/MP4
  tests/test_sanity.py
  results/
```

## 3. Model pręta

- Ryba jako **jeden pręt** o długości ok. 0.4 m (placeholder), oś wzdłuż X, ok. 50–100 elementów.
- Promień zmienny wzdłuż długości (zwężenie ku ogonowi), jeśli wersja API pozwala na promień per element. Jeśli nie: dwa pręty (sztywniejsze „ciało” + miękki „ogon”) połączone `FixedJoint`. Zdecyduj po sprawdzeniu API i uzasadnij.
- Uwaga na przekrój: prawdziwy ogon jest **płaski** (spłaszczony bocznie), a pręt Cosserata w PyElastica zakłada domyślnie przekrój kołowy. Opisz, jak to wpływa na sztywność i siły wody. Jeśli API pozwala nadpisać macierz sztywności zginania (anizotropowa sztywność), zrób to, inaczej odnotuj jako ograniczenie.
- Sztywna przednia część (głowa) = duży moduł Younga lub duży promień (zależnie od wybranej opcji).
- Moduł Younga silikonu jako placeholder, gęstość ~1000–1100 kg/m³.
- Tłumienie wewnętrzne: `AnalyticalLinearDamper` (opisz, że to numeryczno-fenomenologiczne tłumienie, a nie lepkosprężystość silikonu).

## 4. Napęd hydrauliczny – zrób to fizycznie poprawnie

- Komory są **wewnętrzne**: hydraulika nie może dawać wypadkowej siły ani momentu na całą rybę. Dodawanie zewnętrznych momentów do elementów (jak w niektórych przykładach) łamie tę zasadę, jeśli momenty się nie znoszą.
- Zalecane podejście: ciśnienie zmienia **krzywiznę spoczynkową** odcinka z komorami: `κ_rest(s, t) = K_p · (p_L − p_R)` w strefie komór (zero poza nią). Pręt sam „chce” się wygiąć, a wypadkowa siła i moment z napędu są zerowe z konstrukcji. Sprawdź w API, jak zmieniać krzywiznę spoczynkową w trakcie symulacji (callback/forcing modyfikujący odpowiednie pole), i opisz to.
- Alternatywa do porównania (etap opcjonalny): pary równych i przeciwnych momentów na granicach strefy komór.
- Hydraulika: ten sam prosty model ODE co w pozostałych demach (pompa I rzędu, układ zamknięty L↔R, podatność komór, zawór przelewowy). Integrowana co krok pręta lub co N kroków, z opisem wyboru.

## 5. Woda (water.py) – własna klasa sił

Zaimplementuj klasę dziedziczącą po `ea.NoForces` z metodą `apply_forces(system, time)`, która dla każdego węzła/elementu liczy:

1. **Opór kwadratowy (Morison/Taylor)**: rozłóż prędkość względną na składową normalną i styczną do osi pręta: `f_n = −½ ρ C_n d |v_n| v_n`, `f_t = −½ ρ C_t π d |v_t| v_t` (na jednostkę długości, `d` = szerokość/średnica lokalna). Współczynniki to placeholdery.
2. **Siła reaktywna / masa dodana**: zastosuj uproszczenie z teorii Lighthilla dla wydłużonego ciała. Masa dodana na jednostkę długości `m_a(s) = ρ π h(s)²/4` (h = lokalna wysokość) dla ruchu poprzecznego. Wybierz i opisz jedną z implementacji:
   - (a) prostsza: masa dodana doliczona do bocznej bezwładności (jeśli API pozwala) lub jako siła `−m_a · a_n` z różniczkowania prędkości (uważaj na szum; filtruj),
   - (b) siła reaktywna skupiona na krawędzi spływu ogona (teoria dużych amplitud Lighthilla). Opisz wzór i źródło.
3. Przełącznik `water_model ∈ {"none", "drag", "drag+reactive", "stokes_sbt"}` w configu. `stokes_sbt` służy wyłącznie do porównania (zasada 3).

**Ograniczenie do README:** to model lokalny, bez śladu wirowego i bez interakcji ogona z wirami. Wyniki są jakościowe. Jeśli użytkownik zechce prawdziwy przepływ, kolejnym krokiem jest sprzężenie z solverem SophT (ta sama grupa badawcza, metoda immersed boundary). Nie implementuj tego bez zgody użytkownika.

## 6. Wypór i balast (buoyancy.py)

- Na każdy element: wypór `ρ_w · g · V_elem` w górę + grawitacja `ρ_s · g · V_elem` w dół (wbudowane `GravityForces` lub własne, bez podwójnego liczenia).
- Pęcherz balastowy w strefie głowy: dodatkowa objętość `V_b(t)`, ograniczona szybkością pompy balastowej. Przyłożony nieco powyżej osi (moment prostujący), jeśli API pozwala na moment; jeśli nie, opisz uproszczenie.
- PID głębokości (jak w demo MuJoCo), aktywny tylko w scenariuszu 6.

## 7. Etapy realizacji

1. **Walidacja pręta (bez wody)**: belka wspornikowa (`OneEndFixedBC`) pod momentem na końcu → kształt łuku z `κ = M/(E·I)`; porównanie z teorią. Druga walidacja: pierwsza częstotliwość własna wspornika vs wzór analityczny `ω₁ = 1.875²·√(E·I/(ρ·A·L⁴))`.
2. **Napęd przez krzywiznę spoczynkową**: statyczne ugięcie ogona vs różnica ciśnień. Test: wypadkowa siła i moment z napędu ≈ 0 (sprawdź na swobodnym pręcie w próżni: środek masy się nie przesuwa).
3. **Ogon przymocowany w wodzie**: głowa unieruchomiona, sinus pompy. Porównanie modeli wody `none` / `drag` / `drag+reactive`: amplituda, faza, średnia siła reakcji w mocowaniu (jakościowy ciąg na uwięzi).
4. **Swobodne pływanie 2D (płasko)**: bez grawitacji i wyporu (neutralna pływalność). Prędkość postępowa vs czas. Porównanie modeli wody, w tym `stokes_sbt` jako przykład złej fizyki.
5. **Przegląd**: częstotliwość 0.5–3 Hz i moduł Younga ×0.5/×1/×2 → prędkość pływania. Zwróć uwagę na rezonans (porównaj z częstotliwością własną z etapu 1) i opisz to w README.
6. **3D + wypór + balast**: grawitacja i wypór włączone, skoki zadanej głębokości. Wykres głębokości i objętości pęcherza.
7. **(Opcjonalnie) eksport do innych dem**: sztywności równoważne dla modelu segmentowego MuJoCo (jak w demo SOFA) do `results/prbm.json`.

## 8. Wyniki (results/)

PNG + CSV: `e1_cantilever_vs_theory.png`, `e1_natural_freq.png`, `e2_bend_vs_pressure.png`, `e3_tethered_models.png`, `e4_free_swim_speed.png`, `e5_sweep_freq_E.png`, `e6_depth_control.png`. Animacje GIF/MP4: `free_swim.gif` (kształt ryby w czasie, widok z góry) oraz opcjonalnie widok 3D z etapu 6.

## 9. Testy (tests/test_sanity.py)

- Etap 1: kształt łuku i ugięcie końcówki zgodne z teorią < 2–5% (przy dostatecznie gęstej dyskretyzacji); częstotliwość własna < 5%.
- Bez tłumienia i bez wody: energia całkowita nie dryfuje znacząco (integrator symplektyczny).
- Napęd wewnętrzny: dla swobodnego pręta w próżni środek masy stoi w miejscu (|Δx_cm| poniżej progu).
- Hydraulika: `V_L + V_R = const`, ciśnienie ≤ `p_max`.
- Model wody rozprasza energię (moc sił oporu ≤ 0).
- Swobodne pływanie z wodą: średnia prędkość postępowa > 0; w próżni ≈ 0.
- Brak NaN, brak „eksplozji” (maksymalne rozciągnięcie elementu poniżej progu).

## 10. README – obowiązkowe sekcje

- Wersja PyElastica (przypięta) i instalacja.
- Krótkie wyjaśnienie teorii prętów Cosserata dla osoby uczącej się: co to jest pręt Cosserata, jakie odkształcenia uwzględnia, dlaczego to dobre przybliżenie smukłej ryby.
- Wyjaśnienie, dlaczego `SlenderBodyTheory` (Stokes) nie pasuje do ryby, z wynikiem porównania z etapu 4.
- Co pokazuje każdy wykres, 2–3 zdania.
- **Ograniczenia**: przekrój kołowy zamiast płaskiego (o ile nie nadpisano sztywności), lokalny model wody bez wirów, napęd jako krzywizna spoczynkowa zamiast pełnej mechaniki komór, liniowa sprężystość, niezidentyfikowane parametry.
- Ścieżka rozwoju: sprzężenie z SophT dla prawdziwego przepływu, kalibracja na pomiarach (ugięcie vs ciśnienie, częstotliwość własna ogona w wodzie, prędkość pływania w basenie).

## 11. Definition of done

- `pytest` → wszystkie testy zielone.
- `python scripts/run_scenarios.py` → wykresy w `results/`.
- `python scripts/animate.py` → animacja pływającej ryby.
- README pozwala zrozumieć wyniki i ograniczenia.
