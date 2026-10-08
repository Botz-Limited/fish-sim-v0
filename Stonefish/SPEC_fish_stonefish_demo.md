# SPEC: Demo Stonefish – robot-ryba z segmentowym ogonem, balastem i czujnikami

> Instrukcja dla Claude Code. Umieść ten plik w pustym folderze projektu i napisz:
> „Przeczytaj SPEC_fish_stonefish_demo.md i zrealizuj go etapami. Zacznij od planu.”
> Wymagany Linux (Ubuntu) z GPU obsługującym nowoczesny OpenGL (sprawdź wymagania w dokumentacji Stonefish). Bez GPU działa tylko tryb konsolowy.

## 0. Cel i kontekst

Zbuduj **uproszczoną, edukacyjną** symulację robota-ryby (ROV) w bibliotece Stonefish (C++, Uniwersytet w Gironie). Ma pokazać to, w czym Stonefish jest mocny w porównaniu z MuJoCo:
- **hydrodynamika liczona z geometrii** (siatki brył), a nie z symbolicznych współczynników,
- gotowy aktuator **Variable Buoyancy System (VBS)** do regulacji głębokości,
- **czujniki morskie** (ciśnienie/głębokość, IMU, opcjonalnie DVL, kamera) z szumem,
- **środowisko oceaniczne**: prądy, opcjonalnie fale, realistyczny rendering podwodny,
- opcjonalna integracja z **ROS 2**.

Ogon to łańcuch sztywnych segmentów (Stonefish nie symuluje ciał miękkich). Napęd hydrauliczny to własny model ODE przeliczany na momenty w przegubach.

To **nie jest** skalibrowany model. Parametry to placeholdery i mają być tak oznaczone.

Użytkownik to młody inżynier mechatronik, który się uczy. **Komentarze po polsku** w C++ i w plikach XML scenariuszy, wyjaśniające fizykę i rolę każdego elementu.

## 1. Zasady pracy (ważne)

1. Pracuj etapami (sekcja 7). Po każdym etapie zbuduj, uruchom, pokaż wynik.
2. **Ustal wersję Stonefish i trzymaj się dokumentacji tej wersji** (stonefish.readthedocs.io, przełącznik wersji). Składnia XML i API C++ różnią się między wersjami. Nie zgaduj nazw tagów, atrybutów ani metod. Sprawdzaj w dokumentacji, nagłówkach (`include/Stonefish/...`) i dołączonych przykładach.
3. Scenariusz definiuj w **XML** (szybkie zmiany bez rekompilacji), a C++ używaj tylko tam, gdzie trzeba rozszerzyć bibliotekę (model hydrauliki, sterowanie, logowanie).
4. **Kluczowa niewiadoma do sprawdzenia na starcie**: jakie tryby sterowania ma aktuator `Servo` w tej wersji (pozycja, prędkość, moment?). Model hydrauliki generuje **moment**. Jeśli serwo nie ma trybu momentowego, zaimplementuj przyłożenie momentu inaczej (np. własny aktuator albo pary momentów przykładane do sąsiednich ogniw przez API brył) i opisz, co wybrałeś. Momenty muszą działać **między** ogniwami (akcja = reakcja), bo napęd jest wewnętrzny.
5. Dwie aplikacje: graficzna (podgląd) i **konsolowa** (bez renderingu, do testów i scenariuszy wsadowych). Sprawdź w dokumentacji, jak biblioteka to rozróżnia.
6. Nie wymyślaj „realistycznych” wartości. Każdy parametr: komentarz `PLACEHOLDER – do identyfikacji z pomiarów`.
7. Jeśli ryba nie płynie do przodu, **nie maskuj tego** strojeniem na ślepo. Zdiagnozuj (orientacja płetwy, typ fizyki brył, siatki kolizyjne/fizyczne) i opisz w README.

## 2. Instalacja

- Zbuduj Stonefish ze źródeł (CMake) według instrukcji dla danej wersji. Zależności zapisz w README.
- Opcjonalnie później: pakiet `stonefish_ros2` (sprawdź, czy istnieje i działa z twoją dystrybucją ROS 2; jeśli są problemy, pomiń ten etap i opisz).
- Siatki (głowa, segmenty, płetwa): wygeneruj proste bryły w Pythonie (`trimesh`) lub Blenderze (skrypt), eksport OBJ. Osobne siatki: **fizyczna** (uproszczona, do hydrodynamiki) i **wizualna** (opcjonalnie gładsza).

## 3. Struktura projektu

```
fish_stonefish_demo/
  README.md
  CMakeLists.txt
  data/
    meshes/                  # head.obj, seg1..segN.obj, fin.obj, bladder.obj (fizyczne i wizualne)
    scenarios/
      fish_base.scn          # wspólna definicja robota (include)
      s1_hover.scn
      s2_swim.scn
      s3_turn.scn
      s4_depth.scn
      s5_current.scn
  tools/
    make_meshes.py           # generacja siatek z parametrów
    plot_logs.py             # CSV -> wykresy
  src/
    main_gui.cpp             # aplikacja graficzna
    main_console.cpp         # aplikacja konsolowa (scenariusze wsadowe, testy)
    FishSimManager.{h,cpp}   # ładuje scenariusz, pętla sterowania, logowanie CSV
    Hydraulics.{h,cpp}       # model ODE pompy i komór
    TailDriver.{h,cpp}       # momenty z hydrauliki -> przeguby
    Controllers.{h,cpp}      # CPG, skręt, PID głębokości (sterowanie VBS)
  tests/
    run_tests.sh             # uruchamia konsolowe scenariusze z asercjami
  results/
```

## 4. Model robota (XML)

- **Głowa** (`base_link`): bryła opływowa ~0.25 m (placeholder), typ fizyki odpowiedni dla ciała zanurzonego (sprawdź nazwę w dokumentacji), materiał i gęstość tak, by cała ryba była **lekko dodatnio pływalna** bez VBS.
- **Ogon**: N = 4–5 segmentów (`link`), przeguby `revolute` wokół osi pionowej, z limitami ok. ±35°. Sprawdź, czy przeguby wspierają sprężystość/tłumienie; jeśli nie, dodaj je w C++ jako moment `−k·θ − c·θ̇` (sztywność i tłumienie silikonu, placeholdery).
- **Płetwa ogonowa**: cienka w osi Y, wysoka w osi Z, na końcu ostatniego segmentu.
- **VBS**: aktuator `VariableBuoyancy` na głowie, z siatkami określającymi zakres objętości (sprawdź w dokumentacji, jak definiuje się zakres i prędkość zmian). Umieść tak, by środek wyporu był powyżej środka masy (moment prostujący).
- **Czujniki**: czujnik ciśnienia (głębokość, z szumem), IMU na głowie, enkodery przegubów ogona. Opcjonalnie kamera z przodu (pokaz renderingu).
- **Środowisko**: ocean z wodą, opcjonalnie prąd (scenariusz 5), dno, kilka obiektów referencyjnych (skały/słupy), żeby było widać ruch.

## 5. Hydraulika i sterowanie (C++)

- `Hydraulics`: pompa I rzędu (`u ∈ [−1,1]`, `Q_max`, `τ_pump`), układ zamknięty L↔R, podatność komór `p = (V − V0)/C` z nasyceniem `p_max` (zawór przelewowy), moment `τ = A_eff·r_eff·(p_L − p_R)` rozłożony na przeguby (wagi w configu). Ten sam model co w pozostałych demach, żeby dało się porównać.
- `Controllers`: CPG `u = A·sin(2πft) + bias`; PID głębokości: **wejściem jest odczyt z czujnika ciśnienia** (nie prawdziwa pozycja z symulatora), wyjściem komenda VBS. Lekcja: regulator działa na zaszumionym pomiarze, jak w prawdziwym robocie. Dodaj prosty filtr dolnoprzepustowy i opisz, dlaczego.
- Parametry w jednym pliku konfiguracyjnym (YAML lub JSON) ładowanym przy starcie, bez rekompilacji.
- Logowanie CSV: czas, pozycja/orientacja głowy (prawdziwa), odczyty czujników, kąty przegubów, `p_L`, `p_R`, `Q`, komenda i stan VBS.
- Sterowanie klawiaturą w aplikacji graficznej (jeśli API to umożliwia; jeśli nie, sterowanie przez plik/konfigurację i opis w README).

## 6. Scenariusze

1. `s1_hover`: bez napędu, VBS neutralny → dryf pionowy; start z przechyłem 30° → powrót do pionu.
2. `s2_swim`: CPG 1–2 Hz → ruch do przodu. Porównanie z wariantem, w którym ogon jest zablokowany (prędkość ≈ 0), żeby pokazać, że ciąg pochodzi z ruchu ogona.
3. `s3_turn`: bias CPG → trajektoria po łuku (XY).
4. `s4_depth`: skoki zadanej głębokości (−1 → −3 → −2 m), PID na czujniku ciśnienia → głębokość prawdziwa vs mierzona, stan VBS.
5. `s5_current`: stały prąd boczny → dryf; utrzymanie kursu przez bias (prosty regulator kursu na IMU, opcjonalnie).
6. **Przegląd** (aplikacja konsolowa): częstotliwość 0.5–3 Hz → średnia prędkość i amplituda ogona (lekcja: ograniczenie przepływu pompy).
7. **(Opcjonalnie) ROS 2**: ten sam robot w `stonefish_ros2`, publikacja czujników, CPG i PID jako węzły w Pythonie, nagranie rosbag.

## 7. Etapy realizacji

1. Instalacja + uruchomienie przykładowego scenariusza z repozytorium Stonefish.
2. Siatki + statyczny robot w scenie (graficznie), wypisanie masy, objętości, wypadkowej pływalności.
3. `s1_hover` w aplikacji konsolowej + test.
4. Przeguby ogona, sprężystość, hydraulika, przyłożenie momentów → `s2_swim`.
5. `s3_turn`, `s4_depth`, `s5_current`.
6. Przegląd częstotliwości + wykresy.
7. (Opcjonalnie) ROS 2.

## 8. Wyniki (results/)

PNG + CSV: `s1_hover_drift.png`, `s1_righting.png`, `s2_speed_vs_locked.png`, `s3_trajectory.png`, `s4_depth_true_vs_measured.png`, `s5_current_drift.png`, `s6_freq_sweep.png`. Zrzuty ekranu lub krótkie nagranie z aplikacji graficznej (jeśli łatwe; jeśli nie, instrukcja w README).

## 9. Testy (tests/run_tests.sh, aplikacja konsolowa)

- Scenariusze ładują się bez błędów parsera.
- `s1`: |Δz| po 5 s poniżej progu; przechył po 5 s < połowa początkowego.
- Hydraulika: `V_L + V_R = const`, `p ≤ p_max`.
- Napęd wewnętrzny: suma momentów od hydrauliki na cały robot = 0 (sprawdź w logu lub teście jednostkowym `TailDriver`).
- `s2`: średnia prędkość z ruchomym ogonem > 0, z zablokowanym ≈ 0.
- `s4`: błąd ustalony głębokości poniżej progu, VBS nie przekracza zakresu.
- Brak NaN w logach.

## 10. README – obowiązkowe sekcje

- Wersje (Stonefish, kompilator, ewentualnie ROS 2) i instalacja krok po kroku.
- Jak uruchomić aplikację graficzną i konsolową, jak zmieniać parametry bez rekompilacji.
- Krótko: jak Stonefish liczy siły hydrodynamiczne z geometrii (na podstawie dokumentacji/publikacji autora, z cytatem) i czym to się różni od modelu elipsoidalnego MuJoCo.
- Co pokazuje każdy wykres, 2–3 zdania.
- **Ograniczenia**: ogon sztywno-segmentowy zamiast miękkiego, hydrodynamika quasi-statyczna (bez śladu wirowego), hydraulika jako model zewnętrzny, parametry niezidentyfikowane, wydajność zależna od GPU.
- Porównanie z demo MuJoCo na tych samych parametrach (jeśli użytkownik ma oba): różnice w prędkości pływania i możliwe przyczyny.

## 11. Definition of done

- Projekt buduje się przez CMake bez ostrzeżeń krytycznych.
- Aplikacja graficzna pokazuje pływającą rybę; konsolowa generuje logi i wykresy.
- `tests/run_tests.sh` przechodzi.
- README pozwala osobie uczącej się odtworzyć wyniki i zrozumieć ograniczenia.
