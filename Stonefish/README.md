# Demo Stonefish – robot-ryba z segmentowym ogonem, balastem i czujnikami

Edukacyjna symulacja robota-ryby w bibliotece [Stonefish](https://github.com/patrykcieslak/stonefish) (C++, Uniwersytet w Gironie).
Specyfikacja: [SPEC_fish_stonefish_demo.md](SPEC_fish_stonefish_demo.md). Ten sam robot i ta sama hydraulika co w demo MuJoCo ([../MuJoCo](../MuJoCo/README.md)), żeby dało się porównać oba symulatory.

> **To nie jest skalibrowany model.** Każdy parametr fizyczny w [config/default.json](config/default.json) jest oznaczony `PLACEHOLDER – do identyfikacji z pomiarów`. Liczby z wykresów pokazują *mechanizmy*, a nie osiągi konkretnego robota.

![Aplikacja graficzna: ryba płynie 0.34 m/s, kamera podąża za głową](results/gui_s2_swim.png)

**Najważniejsze wnioski** (szczegóły niżej):

1. Sama hydrodynamika Stonefish „z geometrii” **nie daje ciągu** machającemu ogonowi (0.3 cm/s). Siła na ściankę działa wzdłuż prędkości względnej wody (czysty opór, bez siły nośnej), a domyślne tarcie jest ~250× za duże dla tak małego obiektu. Po dodaniu siły nośnej płetwy (własny model, [src/FinLift.cpp](src/FinLift.cpp)) i tarcia z teorii warstwy przyściennej ryba płynie 34 cm/s.
2. Stonefish 1.5 ma kilka nieudokumentowanych pułapek, które psują wyniki bez żadnego komunikatu: źle liczone prędkości w rozgałęzionym drzewie ogniw, bryły złożone bez dołączonego momentu bezwładności, domyślnie wyłączone prądy morskie, grawitacja nadpisywana po konstruktorze, a serwo bez działającego trybu momentu. Lista z objawami jest w sekcji [Pułapki Stonefish 1.5](#pułapki-stonefish-15).
3. Regulator głębokości działa na **zaszumionym czujniku ciśnienia** przez filtr dolnoprzepustowy. Nastawy z MuJoCo dawały tu cykl graniczny, a nastawy wyprowadzone z modelu pionu działają (przeregulowanie 3 cm).

---

## Spis treści

- [Wersje](#wersje)
- [Instalacja krok po kroku](#instalacja-krok-po-kroku)
- [Uruchomienie](#uruchomienie)
- [Struktura projektu i gdzie są parametry](#struktura-projektu-i-gdzie-są-parametry)
- [Model robota](#model-robota)
- [Jak Stonefish liczy siły wody z geometrii](#jak-stonefish-liczy-siły-wody-z-geometrii)
- [Diagnoza ciągu – dlaczego ryba początkowo nie płynęła](#diagnoza-ciągu--dlaczego-ryba-początkowo-nie-płynęła)
- [Hydraulika i sterowanie](#hydraulika-i-sterowanie)
- [Co pokazuje każdy wykres](#co-pokazuje-każdy-wykres)
- [Testy](#testy)
- [Pułapki Stonefish 1.5](#pułapki-stonefish-15)
- [Ograniczenia](#ograniczenia)
- [Porównanie z demo MuJoCo](#porównanie-z-demo-mujoco)
- [ROS 2 (etap 7)](#ros-2-etap-7)

---

## Wersje

| Składnik | Wersja |
|---|---|
| Stonefish | **1.5.0** (tag `v1.5`, commit `7d52673`, czerwiec 2025). Dokumentacja tej wersji to katalog `docs/` w repozytorium przy tym tagu (= stonefish.readthedocs.io, wersja 1.5). Gałąź `master` to już 1.6-dev z inną obsługą wątków – nie używana. |
| System | Fedora 44, Linux 7.2, KDE (Wayland) |
| Kompilator | GCC 16.2.1, CMake 4.3.0, C++20 |
| GPU | AMD Radeon RX 7700 XT, Mesa 26.2.3 (radeonsi), OpenGL 4.6 Core |
| Python (narzędzia) | 3.14, pakiety w [requirements.txt](requirements.txt) |
| JSON (C++) | nlohmann/json 3.11.3 (jeden nagłówek w `third_party/`, licencja MIT) |
| ROS 2 | nie instalowany – patrz [ROS 2](#ros-2-etap-7) |

## Instalacja krok po kroku

### 1. Zależności Stonefish

Stonefish wymaga: OpenGL ≥ 4.3 (sterownik GPU), SDL2, Freetype, GLM (≥ 0.9.9) i OpenMP (jest w GCC).

```bash
# Fedora
sudo dnf install cmake gcc-c++ SDL2-devel freetype-devel glm-devel mesa-libGL-devel
# Ubuntu
sudo apt install cmake g++ libsdl2-dev libfreetype-dev libglm-dev libgl-dev
glxinfo -B | grep "core profile version"     # powinno być ≥ 4.3
```

<details><summary>Bez uprawnień administratora (tak zrobiono na komputerze autora demo)</summary>

Pakiety `-devel` można rozpakować do katalogu domowego bez instalacji – biblioteki uruchomieniowe (`SDL2`, `freetype`) zwykle już są w systemie:

```bash
mkdir -p ~/rpms && cd ~/rpms && dnf download SDL2-devel freetype-devel glm-devel
mkdir -p ~/.local/opt/sfdeps && cd ~/.local/opt/sfdeps
for r in ~/rpms/*x86_64.rpm ~/rpms/*noarch.rpm; do rpm2cpio $r | cpio -idm; done
# dowiązania .so wskazują na pliki systemowe:
ln -sf /usr/lib64/libfreetype.so.6 usr/lib64/libfreetype.so
ln -sf /usr/lib64/libSDL2-2.0.so.0 usr/lib64/libSDL2-2.0.so
```
Plik `usr/lib64/cmake/SDL2/SDL2Config.cmake` z pakietu `sdl2-compat-devel` ma zaszyte ścieżki `/usr` – trzeba go zastąpić krótkim plikiem ustawiającym `SDL2_INCLUDE_DIRS` i `SDL2_LIBRARIES` na rozpakowany katalog. Potem do każdego `cmake` dodaje się `-DCMAKE_PREFIX_PATH=$HOME/.local/opt/sfdeps/usr`.
</details>

### 2. Biblioteka Stonefish 1.5 ze źródeł

```bash
git clone https://github.com/patrykcieslak/stonefish.git ~/src/stonefish
cd ~/src/stonefish && git checkout v1.5
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=$HOME/.local/opt/stonefish
cmake --build build -j$(nproc) && cmake --install build
```
Instalacja do katalogu domowego (bez `sudo`). Systemowo: pomiń `CMAKE_INSTALL_PREFIX` i użyj `sudo cmake --install build`.

Etap 1 SPEC (przykład z repozytorium): `cmake -S . -B build-tests -DBUILD_TESTS=ON && cmake --build build-tests`, potem `build-tests/Tests/UnderwaterTest` (okno z robotem GIRONA500) i `build-tests/Tests/ConsoleTest` (bez okna). Oba działają.

### 3. To demo

```bash
cd Stonefish/
cmake -S . -B build -DCMAKE_PREFIX_PATH=$HOME/.local/opt/stonefish   # (+ ;$HOME/.local/opt/sfdeps/usr bez sudo)
cmake --build build -j$(nproc)          # buduje się bez ostrzeżeń (-Wall -Wextra)
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```
Siatki i scenariusze XML są w repozytorium. Generator jest potrzebny tylko po zmianie geometrii: `.venv/bin/python tools/make_meshes.py`.

## Uruchomienie

### Aplikacja graficzna (podgląd w czasie rzeczywistym)

```bash
build/fish_gui config/s2_swim.json              # dowolny plik config/*.json
build/fish_gui config/s1_hover.json --out /tmp/log.csv   # opcjonalnie z logiem
```

| Klawisz | Działanie |
|---|---|
| Spacja | start/stop ogona (CPG) |
| ← / → | skręt: V_bias −/+ 0.5 ml (max ±4 ml), wyłącza regulator kursu |
| ↑ / ↓ | częstotliwość ogona ±0.25 Hz, bez skoku fazy |
| PgUp / PgDn | głębokość zadana −/+ 0.25 m (płycej/głębiej), włącza regulator głębokości |
| W S A D Q Z, mysz | kamera (klawisze biblioteki); kamera jest przyklejona do głowy ryby |
| H / C / K / Esc | panel / konsola komunikatów / lista klawiszy / wyjście |

Nakładka w prawym górnym rogu (czas, prędkość, głębokość prawdziwa i z czujnika, f, V_bias, p_L/p_R, woda w VBS, kurs) jest po angielsku i w ASCII, bo czcionka interfejsu nie musi mieć polskich znaków.

**Zrzuty ekranu:** biblioteka nie ma tej funkcji. W KDE: `spectacle -b -n -a -o plik.png` (aktywne okno), w GNOME: `gnome-screenshot -w`. Tak powstał `results/gui_s2_swim.png`.

**Ostrzeżenia przy starcie** `[ERROR] Failed to compile shader: hbaoBlur.frag, hbaoBlur2.frag, thermalVisualize.frag, sonarVisualize.frag` pojawiają się na sterowniku Mesa także w przykładach biblioteki. Dotyczą efektu cieniowania otoczenia (HBAO) oraz kamer termowizyjnej i sonarowej, których demo nie używa. Rendering działa (~800 FPS na RX 7700 XT).

### Aplikacja konsolowa (bez okna – scenariusze wsadowe, testy)

```bash
build/fish_console config/s2_swim.json                       # log -> results/logs/s2_swim.csv
build/fish_console config/s2_swim.json --out /tmp/a.csv --duration 30
build/fish_console config/s3_turn.json --set rhythm.volume_bias=-2e-6 --set rhythm.freq=1.5
.venv/bin/python tools/run_scenarios.py -j 8     # wszystkie scenariusze + przegląd częstotliwości + wykresy (~1 min)
tests/run_tests.sh                                # testy (~20 s)
```

Biblioteka rozróżnia oba tryby klasą aplikacji: `sf::GraphicalSimulationApp` (okno OpenGL, krok fizyki dopasowany do zegara) i `sf::ConsoleSimulationApp` (bez renderingu). W konsoli wywołujemy `Run(true, true, 1/sps)`, czyli stały krok liczony tak szybko, jak pozwala procesor: 5–8× szybciej niż czas rzeczywisty. W trybie konsolowym nie ma kamer, świateł ani fal, więc scenariusze ich nie używają.

### Zmiana parametrów bez rekompilacji

- **Liczby** (hydraulika, sterowanie, sztywności, tarcie, siła nośna, krok czasu): edytuj [config/default.json](config/default.json) albo plik scenariusza `config/sN_*.json` (nadpisuje tylko wybrane pola, scalanie *JSON merge-patch*), albo użyj `--set sekcja.klucz=wartość`.
- **Geometria, materiały, czujniki, przeguby, VBS** (to, co trafia do XML): zmień `config/default.json`, uruchom `tools/make_meshes.py`. Generator przelicza masę i położenie balastu (pływalność neutralna + trym) i wypełnia szablony.
- **Scenariusze XML** (położenie startowe, prąd, środowisko): szablony w [tools/templates/](tools/templates/), wygenerowane pliki w [data/scenarios/](data/scenarios/). Szablony są potrzebne, bo **Stonefish pozwala definiować materiały tylko w pliku głównym scenariusza**, a gęstości pochodzą z konfiguracji.

## Struktura projektu i gdzie są parametry

```
Stonefish/
  config/default.json        # WSZYSTKIE parametry z opisem (JSON z komentarzami //)
  config/s*.json, t_*.json    # scenariusze: tylko różnice względem default.json
  data/meshes/               # *_phy.obj (do fizyki, 320 trójkątów/elipsoidę), *_vis.obj (gładkie), vbs_*.obj
  data/scenarios/            # fish_base.scn (robot), world_base.scn (dno, słupy), s1…s5, t_internal (WYGENEROWANE)
  tools/templates/*.scn.in   # szablony XML z komentarzami – tu zmieniaj strukturę scenariuszy
  tools/make_meshes.py       # siatki + bilans mas + balast + XML
  tools/run_scenarios.py     # wszystkie przebiegi konsolowe -> results/logs/ -> wykresy
  tools/plot_logs.py         # CSV -> PNG + dane z wykresów (CSV) + results/summary.json
  src/FishSimManager.*       # ładuje scenariusz, pętla sterowania, log CSV
  src/Hydraulics.*           # pompa I rzędu + komory L/R + zawór przelewowy (ODE)
  src/TailDriver.*           # siła hydrauliki -> momenty w przegubach + sprężystość silikonu
  src/FinLift.*              # siła nośna płetwy (brakująca w Stonefish)
  src/Controllers.*          # CPG, filtr, PID głębokości (VBS), PI kursu
  src/Config.*, AppArgs.h    # wczytywanie JSON, linia poleceń
  src/main_gui.cpp, main_console.cpp
  tests/run_tests.sh, unit_tests.cpp, check_logs.py
  results/                   # wykresy PNG + CSV (pełne logi w results/logs/ – poza gitem)
```

## Model robota

| Element | Realizacja w Stonefish | Wartości (PLACEHOLDER) |
|---|---|---|
| Głowa | `base_link` typu `model`: siatka kadłuba (elipsoida 25×10×10 cm) zsumowana z płetwą grzbietową; `physics="submerged"` (wypór + opór + masa dołączona) | masa 1225 g, środek masy 8.9 mm pod osią |
| Balast | wliczony w `<mass>`, `<inertia>`, `<cg>` głowy (stal 453 g, 9.7×3.5×1.7 cm na dnie), wyliczony z warunków pływalności i trymu | – |
| Ogon | 5 ogniw `model` z silikonu (1100 kg/m³), przeguby `revolute` wokół osi Z, ±35°, `<damping>` 0.005 N·m·s/rad | segmenty 4 cm, zwężenie do 40% |
| Płetwa ogonowa | osobne ogniwo, przegub `fixed` z ostatnim segmentem; cienka w Y (6 mm), wysoka w Z (12 cm) | S = 66 cm² |
| Sprężystość silikonu | **brak w Stonefish** -> C++: moment −k·θ przez aktuator `motor` | napędzane 0.3 N·m/rad; pasywne liczone z rezonansu 3 Hz: 1.01 i 0.42 N·m/rad |
| Napęd hydrauliczny | aktuator `motor` w każdym przegubie, moment z C++ (sekcja „Hydraulika”) | jak w MuJoCo |
| VBS | aktuator `vbs` na głowie, siatki „pusty” 0.5 ml / „pełny” 40.5 ml, wydatek z C++ (`setFlowRate`) | pompa 10 ml/s |
| Czujniki | `pressure` (50 Hz, σ = 50 Pa ≈ 5 mm), `imu` (100 Hz, szum kątów 0.005–0.01 rad), `encoder` ×5 | – |
| Środowisko | ocean (woda 1000 kg/m³, bez fal), dno na 4 m, słupy co 1 m, skały; w s5 prąd jednorodny 5 cm/s w +Y | – |

**Bilans mas** (`make_meshes.py` i to samo policzone przez Stonefish przy starcie, porównaj z `[INFO] Bilans mas` w konsoli): masa suchej ryby 1567 g, objętość 1588 ml. Bez wody w VBS ryba jest **lekko dodatnio pływalna (+0.20 N)**, przy VBS w połowie (20.5 ml) neutralna (0.000 N), przy pełnym −0.20 N. Środek masy jest 7.2 mm pod środkiem wyporu, a w osi X wypada dokładnie pod nim (trym).

**Układ współrzędnych NED** (Stonefish): X do przodu, Y w prawo, **Z w dół**, czyli głębokość = +z. Siatki są eksportowane już w tym układzie, a początek układu każdego ogniwa leży na jego przegubie.

**Dlaczego taki krok czasu (0.5 ms, 2000 Hz).** Przy 2 ms (krok MuJoCo) sprężyny −k·θ liczone jawnie powodowały eksplozję symulacji w ułamku sekundy (θ = −30 rad). Lekkie, krótkie segmenty (Seg4: 36 g, I_zz ≈ 6·10⁻⁶ kg·m²) między dwiema sprężynami mają drgania własne o ω·dt > 2, a jawny schemat jest stabilny tylko dla ω·dt < 2. Przy 1000 Hz wszystko jest stabilne, 2000 Hz daje zapas ×2. Prędkość pływania przy 4000 Hz jest ta sama (34.08 cm/s), więc wynik nie zależy od kroku.

## Jak Stonefish liczy siły wody z geometrii

Według dokumentacji ([docs/theory.rst](https://github.com/patrykcieslak/stonefish/blob/v1.5/docs/theory.rst)) i artykułu autora (P. Cieślak, *Stonefish: An Advanced Open-Source Simulation Tool Designed for Marine Robotics, With a ROS Interface*, OCEANS 2019 Marseille) siły hydrodynamiczne liczone są **dla każdego trójkąta siatki fizycznej osobno**:

- **Wypór** – suma sił ciśnienia hydrostatycznego na ścianki. Przy pełnym zanurzeniu to ρ·g·V objętości siatki w środku wyporu. Działa też przy częściowym zanurzeniu i na falach.
- **Opór** – cytat z dokumentacji: *„The drag forces are calculated as a sum of forces acting on each face of the body surface. […] the computations implemented in the Stonefish library have to be based on the local velocity of fluid as if there was no body. The result is not quantitatively correct but it gives a good approximation and allows for effects not possible when using simple formulas, e.g., a water current acting on a part of the body.”* W kodzie (`SolidEntity::ComputeHydrodynamicForcesSubmerged`) ścianka, na którą „napływa” woda, dostaje siłę ∝ |v|·v·(v·n)·A, czyli **wzdłuż prędkości względnej** v, skalowaną polem rzutu ścianki. Dochodzi do tego tarcie liniowe ∝ v_t·A (składowa styczna). Współczynniki są szacowane automatycznie z elipsoidy zastępczej albo podawane w `<hydrodynamics>`.
- **Masa dołączona** – liczona z elipsoidy/walca/kuli dopasowanej do siatki, osobno dla trzech osi. Do silnika fizyki (Bullet) trafia jednak tylko **średnia z trzech osi** (dokumentacja: „a mean value is used for all of the axes”) i trzy dołączone momenty bezwładności.
- **Siła nośna** – tylko w aktuatorze `rudder` (płat sterowy), nie dla zwykłych brył.

**Różnica względem MuJoCo.** MuJoCo zastępuje każdą bryłę elipsoidą i liczy siły z kilku symbolicznych współczynników (`fluidcoef`: opór tępy i smukły, opór obrotowy, siła Kutty, siła Magnusa). Ten model **ma siłę nośną** (Kutta), ale nie wie nic o kształcie poza półosiami elipsoidy i nie zna prądów działających tylko na część bryły. Stonefish widzi rzeczywistą siatkę: prąd może działać na sam ogon, a wypór jest poprawny na powierzchni i na falach. Nie ma jednak siły nośnej, a jego opór jest kierunkowo „izotropowy” (zawsze wzdłuż prędkości). Dla pływania ogonem to kluczowe – patrz następna sekcja.

## Diagnoza ciągu – dlaczego ryba początkowo nie płynęła

SPEC §1.7: *„Jeśli ryba nie płynie do przodu, nie maskuj tego strojeniem na ślepo. Zdiagnozuj.”* Pierwsza wersja (wszystko domyślne z biblioteki) płynęła **0.3 cm/s**. Diagnoza krok po kroku:

1. **Orientacja płetwy** – poprawna: cienka w Y, wysoka w Z. Stonefish policzył dla niej masę dołączoną 528 g w osi Y i 11 g w osi X, czyli „widzi” płaską płytkę ustawioną bokiem.
2. **Typ fizyki brył** – `submerged` (wypór + opór + masa dołączona). `floating` nie ma masy dołączonej, `surface` nie ma sił wody.
3. **Siatki** – zamknięte, normalne na zewnątrz: objętości policzone przez Stonefish zgadzają się z `trimesh` co do 0.1 ml.
4. **Model sił** – tu jest przyczyna. Bilans sił w ruchu ustalonym (log `Fdrag_*`, `Fskin_all`, `fin_thrust` – rzuty na oś ryby, uśrednione):

| Wariant (CPG 2 Hz, 15 s) | Prędkość | Co wynika |
|---|---|---|
| Stonefish domyślnie (bez siły nośnej, tarcie z biblioteki) | **0.3 cm/s** | opór „wzdłuż prędkości” nie ma składowej do przodu dla płetwy ruszającej się na boki |
| + siła nośna płetwy | 1.5 cm/s | ciąg 0.097 N jest zjadany przez **tarcie 0.075 N** przy prędkości 1.7 cm/s |
| tarcie Blasiusa, bez siły nośnej | 2.7 cm/s | trochę ciągu „wiosłowego” (opór płetwy) – za mało |
| **tarcie Blasiusa + siła nośna (domyślnie)** | **34.0 cm/s** | ciąg 0.51 N = opór ciśnieniowy głowy 0.11 + segmentów 0.30 + płetwy 0.10 + tarcie 0.015 N |
| ogon zablokowany | 0.0 cm/s | ciąg pochodzi wyłącznie z ruchu ogona |

Dwie poprawki, obie z fizyki i obie wyłączalne w konfiguracji:

- **Tarcie** (`hydro.skin_friction`). Stonefish liczy tarcie liniowo, F = ρ·c·Σ A·v_t, i domyślnie przyjmuje c = 0.1·C_d ≈ 0.1 m/s. Dla ryby 0.5 m przy 0.2 m/s laminarna warstwa przyścienna (Blasius: C_f = 1.328/√Re, Re = 10⁵) daje ½ρ·C_f·U² ≈ ρ·c·U przy **c = ½·C_f·U_ref = 4.2·10⁻⁴ m/s**, czyli ~250× mniej. Ustawiamy to przez `SetHydrodynamicCoefficients` – odpowiednik atrybutu `<hydrodynamics viscous_drag>` z dokumentacji. Opór ciśnieniowy zostaje taki, jak go oszacowała biblioteka.
- **Siła nośna płetwy** (`fin_lift`, [src/FinLift.cpp](src/FinLift.cpp)). Model quasi-statyczny płaskiej płytki: C_L = ½·C_Lα·sin 2α (kształt jak w pomiarach machających płytek, Dickinson i in., *Science* 1999). Działa prostopadle do napływu w punkcie środka płetwy, C_Lα = 2.8/rad (wzór Helmbolda dla wydłużenia 2.2). Opór płetwy liczy dalej Stonefish z siatki, więc nic nie jest liczone podwójnie. Najpierw spróbowałem wbudowanego aktuatora `rudder`. Jego siła nośna rośnie liniowo z α aż do kąta przeciągnięcia i potem znika. Machająca płetwa przy starcie (α ≈ 90°) jest więc „przeciągnięta”: przy 35° dawał 1.7 cm/s, przy 89° 5.7 cm/s, a przy 90° (płytka bokiem do przepływu) siła nośna byłaby nawet największa, co jest niefizyczne.

Wynik nie zależy od numeryki: 4000 Hz daje 34.08 cm/s, hydrodynamika liczona co 40 kroków (domyślne 50 Hz biblioteki) daje 34.05 cm/s.

## Hydraulika i sterowanie

**Hydraulika** ([src/Hydraulics.cpp](src/Hydraulics.cpp)) – model 1:1 jak w MuJoCo: pompa jako człon I rzędu (u ∈ [−1,1], Q_max = 60 ml/s, τ = 30 ms), zamknięty układ komór L↔R (V_L + V_R = const), podatność Δp = (V_p − A_eff·r_eff·L)/C_h z zaworem przelewowym ±50 kPa. Moment na „tendonie” to F = A_eff·r_eff·Δp, a w przegubach τ_i = w_i·F (wagi 1, 0.7, 0.4 dla trzech napędzanych, 0 dla pasywnych) plus sprężystość −k_i·θ_i.

**Jak momenty trafiają do przegubów (kluczowa niewiadoma z SPEC §1.4).** Serwo (`servo`) w v1.5 ma w nagłówku tryb `ServoControlMode::TORQUE`, ale `Servo::Update` obsługuje go tak samo jak tryb prędkości, więc **trybu momentu de facto nie ma**. Użyty jest aktuator **`motor`**: jest w parserze XML v1.5, choć nie ma go w dokumentacji. Wywołuje `FeatherstoneEntity::DriveJoint` → `btMultiBody::addJointTorque`, czyli uogólnioną siłę przegubu. W algorytmie Featherstone'a działa ona na dziecko (+τ) i rodzica (−τ) jednocześnie, więc **napęd jest wewnętrzny**. Sprawdza to test `t_internal`: bez wody i grawitacji, przy machającym ogonie i głowie kiwającej się ±7.6°, środek masy przesuwa się o 0.085 mm w 3 s, a moment pędu L_z ≤ 4.5·10⁻⁶ kg·m²/s. Moment ustawiony w `SimulationStepCompleted` działa w następnym kroku (aktuatory są aktualizowane na początku kroku), czyli sprzężenie jest jawne, jak w MuJoCo.

**CPG** ([src/Controllers.cpp](src/Controllers.cpp)) zadaje **objętość**, a nie przepływ: V_ref = A_V·sin(2πft) + V_bias, u = (dV_ref/dt + K_v·(V_ref − V_p))/Q_max. SPEC proponuje u = A·sin + bias, ale objętość to całka z przepływu. Stały bias w u całkowałby się bez końca (ogon docisnąłby się do zaworu), a sam sinus daje ∫sin = 1 − cos ≥ 0, czyli przesunięcie w jedną stronę. To ta sama poprawka co w demo MuJoCo.

**Regulator głębokości** (scenariusz 4). Wejściem jest **odczyt czujnika ciśnienia** (gauge, 50 Hz, szum σ ≈ 5 mm wody) przeliczony na głębokość d = p/(ρg), a nie prawdziwe położenie z symulatora. Dalej:

- **Filtr dolnoprzepustowy I rzędu 1 Hz.** Człon D różniczkuje pomiar: różnica dwóch zaszumionych próbek co 20 ms daje szum prędkości ~√2·5 mm/0.02 s ≈ 0.35 m/s, większy niż prędkość ryby. Filtr tłumi szum ~4× (test jednostkowy), za to opóźnia pomiar o ~0.16 s. Na wykresie widać błąd „filtr − prawda” do 3 cm przy szybkim opadaniu.
- **PID → zadana objętość wody V_ref** (więcej wody = ciężej). Pompa VBS śledzi V_ref z ograniczonym wydatkiem 10 ml/s. Człon D działa na prędkość z filtru (bez „kopnięcia” przy skoku zadanej).
- **Nastawy z modelu, nie z MuJoCo.** Z nastawami z MuJoCo (kp = 200 ml/m) regulator wpadał w cykl graniczny ±10–40 cm: wyjście skakało między „pusty” a „pełny”, a pompa potrzebuje 4 s na pełny przebieg. Pion to m·z̈ = −ρg·ΔV, gdzie m ≈ 2.6 kg (ryba + woda w VBS + masa dołączona). Dla ω_n = 0.3 rad/s i ζ ≈ 1 wychodzi kp = ω_n²m/(ρg) ≈ 24 ml/m i kd = 2ζω_n·m/(ρg) ≈ 160 ml/(m/s). Warunek „pompa nadąża”: kp·A·ω < q_max.
- **Całkowanie warunkowe** (tylko gdy |e| < 0.2 m) plus zwykły anti-windup na nasyceniu. Przy skoku o 2 m wyjście *nie* jest nasycone przez większość przejazdu, więc zwykły anti-windup nie pomaga, a całka zbiera ∫e przez 20 s. Z nią przeregulowanie wynosiło 24 cm, bez niej 3 cm.

**Regulator kursu** (scenariusz 5): PI na odchyleniu z IMU → V_bias. Znak sprawdzony w scenariuszu 3: V_bias > 0 zgina ogon w lewo (−Y) i ryba skręca w lewo.

## Co pokazuje każdy wykres

Wszystko generuje `tools/run_scenarios.py`. Obok każdego PNG jest CSV z narysowanymi danymi, a liczby są w `results/summary.json`.

| Wykres | Co widać |
|---|---|
| [s1_hover_drift.png](results/s1_hover_drift.png) | Zawis bez napędu, VBS w połowie zakresu. Prawdziwa głębokość zmienia się o **0.05 mm w 5 s** i 0.2 mm w 10 s, dryf poziomy 0 – bilans wyporu i ciężaru policzony przez generator zgadza się z tym, co liczy Stonefish. Szary pas to odczyt czujnika ciśnienia (szum ±1 cm). |
| [s1_righting.png](results/s1_righting.png) | Start z przechyłem 30°. Moment prostujący (środek masy 7.2 mm pod środkiem wyporu) działa od razu: kołysanie wokół pionu z okresem 0.63 s, zgodnym z wysokością metacentryczną. Tłumienie jest **słabe**: 30° → 10° po 5 s → 6° po 18 s. Gładka elipsoida obracająca się wokół osi prawie nie stawia oporu, a Stonefish przyjmuje zerowy dołączony moment bezwładności wokół X. Płetwa grzbietowa (część siatki głowy) poprawiła to z 16° do 10° po 5 s. W MuJoCo (model `C_angular`) ryba wraca do pionu w 0.3 s. |
| [s2_speed_vs_locked.png](results/s2_speed_vs_locked.png) | Lewy panel: prędkość (średnia z okresu machania) dla pięciu wariantów z tabeli w „Diagnozie ciągu”: ogon zablokowany 0, sam Stonefish 0.3 cm/s, model domyślny **34 cm/s** po ~6 s. Prawy panel: bilans sił w ruchu ustalonym – największy opór dają segmenty ogona (machające na boki ścianki „wiosłują” też do tyłu). |
| [s3_trajectory.png](results/s3_trajectory.png) | Trajektorie XY przez 30 s dla V_bias = −3…+3 ml. Ugięcie ogona w lewo → skręt w lewo, a promień maleje z biasem: **20.4 / 10.1 / 6.6 m** dla 1 / 2 / 3 ml, symetrycznie w obie strony. Prędkość prawie się nie zmienia. Pierwsza wersja zahaczała o słupy i miała niesymetryczne promienie, dlatego start jest w x = −8 m. |
| [s4_depth_true_vs_measured.png](results/s4_depth_true_vs_measured.png) | Skoki głębokości 1 → 3 → 2 m. Górny panel: zadana, prawdziwa, pomiar i pomiar po filtrze. Środkowy: błąd pomiaru (czujnik ±1 cm szumu, filtr do 3 cm opóźnienia przy opadaniu). Dolny: woda w VBS i V_ref. Przeregulowanie **3.3 cm**, wejście w pas ±5 cm po **21 s** (o 2 m w dół) i **16 s** (o 1 m w górę), uchyb ustalony 0.2 cm. Woda w VBS mieści się w 1.8–39 ml (zakres 0.5–40.5 ml), a V_ref dochodzi do ograniczenia tylko na początku każdego skoku. |
| [s5_current_drift.png](results/s5_current_drift.png) | Prąd boczny 5 cm/s w +Y, pływanie 2 Hz, 30 s. **Bez regulatora** ryba ustawia się jak chorągiewka pod prąd (kurs −15°): ogon ma większą powierzchnię boczną niż głowa. Płynie wtedy lekko pod prąd (−1.0 m w Y). **Z regulatorem kursu** trzyma kurs ~+3° i jest znoszona z prądem (+1.0 m w Y). Lekcja: utrzymanie *kursu* to nie utrzymanie *toru* – do tego potrzebny pomiar położenia (DVL, GPS na powierzchni, wizja). |
| [s6_freq_sweep.png](results/s6_freq_sweep.png) | Przegląd 0.5–3 Hz przy tej samej amplitudzie zadanej (A_V = 8 ml), 60 s na punkt. Powyżej **Q_max/(2π·A_V) = 1.19 Hz** pompa się nasyca (prawy panel: 45–80% czasu |u| = 1), więc amplituda ogona spada (środkowy). Prędkość jest największa przy **1.75–2.25 Hz (33–34 cm/s)**. Ciekawostka: przy 0.75, 2.75 i 3 Hz ryba **rusza do tyłu** (−12…−13 cm/s), a potem **zawraca** (zmiana kursu ~200°) i płynie naprzód. Płaska płytka jest symetryczna przód–tył, więc siła nośna może pchać w obie strony. Kierunek zależy od fazy pochylenia płetwy względem jej ruchu bocznego, a ta od częstotliwości względem rezonansów ogona (symetryczna machająca płytka potrafi spontanicznie popłynąć w dowolną stronę: Vandenberghe, Childress, Zhang, *J. Fluid Mech.* 2004). Ruch do tyłu jest kierunkowo niestabilny (jak chorągiewka odwrócona tyłem), stąd zawracanie. |
| [gui_s2_swim.png](results/gui_s2_swim.png) | Zrzut z aplikacji graficznej (scenariusz 2, t = 6.4 s, 0.336 m/s). |

## Testy

`tests/run_tests.sh` (≈20 s) uruchamia:

1. **Testy jednostkowe** (`build/unit_tests`, bez symulatora): V_L + V_R = const i |p_L − p_R| ≤ p_max przy losowej pracy pompy (zawór faktycznie się otwiera); suma momentów TailDriver na wszystkie bryły = 0; wagi i wzór τ = w·F − k·θ; kierunek i wartość siły nośnej FinLift (ciąg przy ruchu bocznym w obie strony, zero przy α = 0° i 90°); filtr tłumi szum; anti-windup; ograniczenie z_min; ciągłość fazy CPG przy zmianie f.
2. **Każdy scenariusz ładuje się** bez błędów parsera.
3. **Przebiegi konsolowe i asercje** ([tests/check_logs.py](tests/check_logs.py)): brak NaN; s1: |Δz| po 5 s < 5 mm i dryf poziomy < 5 mm; prostowanie: przechył po 5 s < ½ początkowego; hydraulika w logu s2: V_L + V_R = const, |Δp| ≤ p_max; napęd wewnętrzny: suma momentów = 0, środek masy stoi (< 1 mm), L_z ≈ 0; s2: ogon ruchomy > 5 cm/s, zablokowany ≈ 0; s4: uchyb ustalony < 5 cm, VBS w zakresie.

Wynik na komputerze autora: **WSZYSTKIE TESTY PRZESZŁY**. Z CMake: `ctest --test-dir build`.

## Pułapki Stonefish 1.5

Znalezione w trakcie pracy (sprawdzone w źródłach biblioteki) i obejście każdej z nich:

| Problem | Objaw | Obejście w demo |
|---|---|---|
| `SolidEntity::getLinearVelocity/getAngularVelocity` dla ogniwa robota sumuje wkłady **wszystkich** ogniw o mniejszym indeksie, jakby drzewo było łańcuchem | Po dodaniu płetwy grzbietowej jako osobnego ogniwa przy głowie wszystkie segmenty za nim dostały złe prędkości, a więc **złe siły wody** (z tych prędkości liczy je biblioteka) i zły moment pędu w teście | Robot jest łańcuchem szeregowym, a płetwa grzbietowa jest częścią siatki głowy (suma brył) |
| `Compound::getAugmentedInertia()` zwraca bezwładność bez masy dołączonej | Głowa z balastem jako bryłą złożoną nie miała dołączonego momentu bezwładności | Głowa jako `model` z `<mass>/<inertia>/<cg>` wyliczonymi przez generator |
| Prądy z XML (`<current>`) są dodawane, ale `Ocean::currentsEnabled = false`, a nic w bibliotece nie wywołuje `EnableCurrents()` | Prąd 5 cm/s nie działał wcale (dryf 6 cm w 30 s) | `getOcean()->EnableCurrents()` po wczytaniu scenariusza |
| `setGravity()` w konstruktorze menedżera jest nadpisywane (`g = 9.81` w `InitializeSolver`) | Test „bez grawitacji” spadał na dno | `setGravity` na początku `BuildScenario()` |
| Serwo nie ma działającego trybu momentu | – | aktuator `motor` (nieopisany w dokumentacji, ale obsługiwany przez parser) |
| VBS: `initial` to objętość w m³, nie ułamek (przykład w dokumentacji ma `0.5`); woda w VBS **dodaje ciężar** | – | `initial` = 20.5e-6 m³; regulator: więcej wody = w dół |
| Domyślne współczynniki tarcia (c = 0.1 m/s) | Mała ryba praktycznie nie pływa | tarcie z Blasiusa (`hydro.skin_friction`) |
| Hydrodynamika domyślnie co `sps/50` kroków (50 Hz) | Siła schodkowa przy 2 Hz machania (tu bez wpływu na wynik) | `sim.fluid_prescaler = 1` |
| Materiały tylko w pliku głównym scenariusza | Nie da się ich trzymać w `fish_base.scn` | Scenariusze generowane z szablonów |
| Kompilacja shaderów HBAO/termo/sonar na Mesa | `[ERROR] Failed to compile shader` przy starcie GUI | Nieszkodliwe dla tego demo |
| Pakiet CMake akceptuje tylko dokładną wersję | `find_package(Stonefish 1.5)` nie znajduje 1.5.0 | `find_package(Stonefish)` + własne sprawdzenie wersji |

## Ograniczenia

1. **Ogon sztywno-segmentowy zamiast miękkiego.** 5 sztywnych ogniw ze sprężynami w przegubach (pseudo-rigid-body model). Stonefish nie symuluje ciał miękkich. Hydraulika steruje tylko kombinacją L = Σ w·θ, a kształt ogona wynika z bezwładności, sprężyn i wody.
2. **Hydrodynamika quasi-statyczna, bez śladu wirowego.** Siły zależą tylko od chwilowej prędkości ścianki („as if there was no body”). Nie ma wirów za płetwą, opóźnionego przeciągnięcia, oddziaływania brył przez wodę (płetwa nie „czuje” wody odepchniętej przez kadłub) ani efektów ściany i powierzchni. Siła nośna płetwy to dodany, jednopunktowy model płaskiej płytki, symetryczny przód–tył (stąd pływanie do tyłu w s6).
3. **Masa dołączona uśredniona** po osiach (ograniczenie biblioteki/Bullet). Ogon jest za ciężki w osi X i za lekki w osi Y, a dołączony moment bezwładności wokół osi X wynosi 0. Stąd słabo tłumione kołysanie w s1.
4. **Tarcie liniowe**, zlinearyzowane w U_ref = 0.2 m/s. Dla innych prędkości to przybliżenie.
5. **Hydraulika jako model zewnętrzny** (C++, sprzężenie jawne, krok 0.5 ms): liniowa podatność, idealny zawór, pompa I rzędu, bez strat i mocy.
6. **Parametry niezidentyfikowane** – wszystkie `PLACEHOLDER`. Sposób kalibracji (stół, ogon w wodzie, ciąg na uwięzi, basen) jest opisany w README demo MuJoCo i obowiązuje tu bez zmian. Dochodzi do tego pomiar tłumienia kołysania i promienia skrętu.
7. **Wydajność zależna od GPU.** Aplikacja graficzna wymaga OpenGL ≥ 4.3 (~800 FPS na RX 7700 XT, Mesa). Bez GPU działa tylko aplikacja konsolowa (5–8× szybciej niż czas rzeczywisty przy 2000 Hz).
8. **Brak fal i kamery w trybie konsolowym** – ograniczenie biblioteki, więc scenariusze ich nie używają.

## Porównanie z demo MuJoCo

Ten sam robot (geometria, gęstości, hydraulika, CPG, zakres pęcherza/VBS). Różnice tylko tam, gdzie wymusza je symulator.

| Wielkość | MuJoCo | Stonefish | Skąd różnica |
|---|---|---|---|
| Prędkość przy 2 Hz | 22 cm/s | **34 cm/s** | inny model oporu: MuJoCo liczy opór z elipsoid i współczynników `fluidcoef`, Stonefish z każdej ścianki; w Stonefish siła nośna płetwy pochodzi z dodanego modelu |
| Najlepsza częstotliwość | 1.5–1.75 Hz (24 cm/s) | 1.75–2.25 Hz (33–34 cm/s) | inna masa dołączona → inne rezonanse i faza fali na ogonie |
| Nasycenie pompy przy 2 Hz | 72% | 76% | ta sama hydraulika – zgodne |
| Amplituda płetwy przy 2 Hz | 35.7° | 37.4° | zgodne |
| Pływanie do tyłu | przy złej fazie fali (pierwsza wersja) | przy 0.75, 2.75, 3 Hz – potem zawraca | symetryczna płytka w obu modelach siły nośnej |
| Promień skrętu, V_bias = 3 ml | 2.0 m | 6.6 m | nie badane dokładnie; możliwe przyczyny: uśredniona masa dołączona głowy (w Stonefish 1.6 kg we wszystkich osiach), inny opór obrotu wokół pionu, inny kształt ugięcia ogona |
| Prostowanie z 30° | ~0.3 s | kołysanie, 10° po 5 s | MuJoCo ma tłumienie obrotu (`C_angular`), a Stonefish zerowy dołączony moment bezwładności wokół X |
| Zmiana głębokości o 1 m | ~35 s | ~16 s do ±5 cm | inne nastawy (tu wyprowadzone z modelu) i pomiar przez czujnik |
| Wypór | liczony ręcznie w Pythonie | **z siatki**, przez bibliotekę | – |
| Prąd na część ciała | brak | jest (s5: efekt chorągiewki) | – |
| Krok czasu | 2 ms | 0.5 ms | jawne sprężyny przegubów + lekkie segmenty |

Wniosek dla uczącego się: **żaden z tych modeli nie przewiduje prędkości prawdziwego robota** (22 vs 34 cm/s dla tych samych parametrów). Oba pokazują te same *mechanizmy* – nasycenie pompy, falę na ogonie, skręt przez bias, moment prostujący, regulację głębokości – a liczby trzeba skalibrować pomiarami.

## ROS 2 (etap 7)

Pominięty, jak dopuszcza SPEC. Na tym komputerze nie ma ROS 2, a Fedora nie jest platformą Tier 1 dla ROS 2 (jest nią Ubuntu). Pakiet [`stonefish_ros2`](https://github.com/patrykcieslak/stonefish_ros2) istnieje i jest rozwijany razem z biblioteką. Na Ubuntu 24.04 + ROS 2 Jazzy dalsze kroki wyglądałyby tak:

1. Zbudować Stonefish 1.5 systemowo (`sudo make install`).
2. Sklonować `stonefish_ros2` do workspace'u i `colcon build`.
3. Użyć `data/scenarios/fish_base.scn` w scenariuszu uzupełnionym o definicje interfejsów ROS dla czujników i aktuatorów (składnia w dokumentacji `stonefish_ros2`).
4. Przenieść CPG, hydraulikę i PID z `src/Controllers.cpp` do węzłów Pythona.

Model hydrauliki i siła nośna płetwy są w C++ po stronie symulatora (`FishSimManager`, `FinLift`), więc trzeba by je przenieść do węzła symulatora albo wystawić moment przegubów jako temat ROS.
