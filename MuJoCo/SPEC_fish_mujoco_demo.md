# SPEC v2: Demo MuJoCo – robot-ryba z hydraulicznym ogonem i systemem balastowym

> Instrukcja dla Claude Code. Umieść ten plik w folderze projektu i napisz:
> „Przeczytaj SPEC_fish_mujoco_demo.md i zrealizuj go etapami. Po każdym etapie uruchom testy i pokaż wyniki.”

## Zmiany v1 → v2 (przegląd przed implementacją, 2026-10-02)

Krytyczne (w v1 demo by nie zadziałało):
1. **Hydraulika – ogon w jedną stronę.** `p_i = max(0, (V_i − V0)/C)` przy starcie z `V_L = V_R = V0` i `u = sin` daje `V_L ≥ V0`, więc `p_R ≡ 0` i `τ ≥ 0` przez cały czas. → §4: model sprzężony z kątem ogona, `Δp` ze znakiem.
2. **Hydraulika – skręt przez `bias` w `u` = dryf.** Objętość całkuje przepływ, więc składowa stała rośnie bez końca, aż do `p_max`. → §6: generator zadaje objętość (`V_ref`), a nie przepływ.
3. **Ciśnienie nie zależało od ruchu ogona.** W SoFi napełnienie komory to zgięcie ogona. → §4: `Δp = (V_p − V_g(θ))/C_h`.
4. **Moment prostujący = 0, gdy `r` jest stały w świecie** (`r ∥ F`). → §5: `r` stały w układzie kadłuba, obracany macierzą `xmat`.
5. **Pęcherz nie dawał ujemnej pływalności** (dodatnia bez pęcherza + pęcherz tylko dodaje objętość). → §3/§5: neutralność w środku zakresu pęcherza.
6. **`import fishsim` nie działał** w `pytest` ani w `scripts/`. → §2: `pyproject.toml` + `pip install -e .`.

Ważne (testy byłyby niestabilne lub mylące):

7. Brak trymu wzdłużnego (x CG ≠ x CB → ryba nurkuje). → §3/§5.
8. Test prostowania mierzył wartość chwilową (fałszywy PASS przy przejściu przez 0). → §9: obwiednia.
9. Test „bez wody vx ≈ 0” mierzył głowę, a ta oscyluje (odrzut). → §9: COM całej ryby.
10. „Średnia vx > 0” w osi X świata, a ryba może się obrócić. → §9: postęp poziomy COM, rampa amplitudy.
11. Pęcherz max → ryba wylatuje nad wodę bez końca. → §5: zgrubne wygaszanie wyporu, limit `z_ref`.
12. PID `z → dV/dt` steruje potrójnym integratorem. → §6: kaskada PID → `V_ref` → pompa balastowa.
13. Stabilność jawnego sprzężenia: chodzi o sztywność sprężyny hydraulicznej, nie tylko o `τ_pump`. → §4.
14. Ten sam znak momentu na wszystkich przegubach = fala stojąca, a przy α = 90° siła Kutty = 0, więc ciąg nie jest pewny. → §3: pasywny koniec ogona, §7: diagnostyka fazy.

Zmiany v2.1 (wynik etapu 4, opis w README):
15. **Niepełna masa dołączona w MuJoCo daje fałszywy ciąg do tyłu i tonięcie.** → `added_mass="armature"`: m_A, I_A usunięte z modelu płynu i dodane jako `armature` (przekątna).
16. **Sztywność pasywnych przegubów liczona z rezonansu** (`passive_resonance_hz`) z bezwładnością razem z wodą, zamiast wpisanej na sztywno.

Drobne: półosie elipsoidy w MJCF; kolizje wewnątrz ryby; `fluidshape` na wszystkich geomach ciała; kod w korzeniu repo; środowisko `venv`; viewer (`viewer.lock()`, `set_texts`, PageUp).

## 0. Cel i kontekst

Zbuduj **uproszczoną, edukacyjną** symulację robota-ryby (ROV) w MuJoCo, która pokazuje możliwości programu:
- pływanie dzięki falującemu ogonowi (stateless fluid model MuJoCo, model elipsoidalny),
- hydrauliczny napęd ogona (pompa przepompowuje wodę między dwiema komorami, jak w SoFi z MIT),
- system balastowy (pęcherz o zmiennej objętości) i regulację głębokości,
- moment prostujący wynikający z przesunięcia środka wyporu nad środek masy.

To jest **demo możliwości, nie skalibrowany cyfrowy bliźniak**. Wszystkie parametry fizyczne to wartości zastępcze (placeholdery) i mają być tak oznaczone w kodzie.

Użytkownik to młody inżynier mechatronik, który się uczy. **Komentarze w kodzie po polsku**, wyjaśniające fizykę (co liczy dana linia i dlaczego), a nie tylko składnię.

## 1. Zasady pracy (ważne)

1. Pracuj etapami (sekcja 7). Po każdym etapie uruchom kod i testy, pokaż wynik, dopiero potem idź dalej.
2. Na starcie sprawdź zainstalowaną wersję `mujoco` (`python -c "import mujoco; print(mujoco.__version__)"`). Wymagane `mujoco >= 3.3.1` (od tej wersji viewer pasywny ma `set_texts`). Jeśli nie masz pewności co do nazwy atrybutu MJCF lub funkcji API, sprawdź dokumentację (mujoco.readthedocs.io: rozdziały *Fluid forces*, *XML Reference*, *Python bindings*), a nie zgaduj.
3. **Nie używaj `flex`/`flexcomp`** do ogona. Model płynu MuJoCo działa na sztywnych bryłach (per body / per geom), a nie na węzłach flexa. Ogon = łańcuch sztywnych segmentów ze sprężyną i tłumikiem w przegubach (pseudo-rigid-body model).
4. Nie wymyślaj „realistycznych” wartości i nie przedstawiaj ich jako zmierzonych. Każdy parametr fizyczny w configu ma komentarz `# PLACEHOLDER – do identyfikacji z pomiarów`.
5. Minimalne zależności: `mujoco`, `numpy`, `matplotlib`, `pytest`. Bez ROS, bez frameworków RL.
6. Jeśli coś nie działa zgodnie z oczekiwaniami fizycznymi (np. ryba nie płynie do przodu), **nie maskuj tego strojeniem na ślepo**. Opisz w README, co zaobserwowałeś i jaka jest prawdopodobna przyczyna.
7. Wielkości, które da się policzyć (objętość neutralna pęcherza, położenie CG/CB, warunek stabilności kroku), **licz analitycznie w kodzie**, nie dobieraj ręcznie.

### Fakty o MuJoCo sprawdzone w źródłach (2026-10, mujoco 3.14.0)

- Model płynu (`density`/`viscosity`) **nie liczy wyporu**. Wypór liczymy sami (§5).
- Masa dołączona w modelu elipsoidalnym jest tylko częściowa: są człony zależne od prędkości, ale **nie ma członu `−m_A·v̇`**, a macierz mas się nie zmienia. Skutek: segmenty ogona mają w symulacji mniejszą bezwładność niż w wodzie, a odrzut głowy jest przesadzony. To trzeba wpisać do „Ograniczeń”.
- Jeśli choć jeden geom ciała ma `fluidshape="ellipsoid"`, model pudełkowy (inertia-box) jest dla tego ciała wyłączony, a geomy z `fluidshape="none"` nie dostają żadnej siły płynu. Dlatego **każdy geom ciała ryby** musi mieć `fluidshape="ellipsoid"`.
- `implicit`/`implicitfast` całkują niejawnie tłumienie i pochodne sił płynu po prędkości. **Sztywność przegubów i momenty z Pythona są liczone jawnie.**
- Siła Kutty (siła nośna) wynosi zero, gdy płyta porusza się prostopadle do swojej powierzchni (α = 90°). Kiedy ryba stoi w miejscu, a ogon macha sztywno, ciąg dają tylko różnice faz między segmentami (§3).
- `data.xfrc_applied`: siła [0:3] i moment [3:6] w układzie świata, przyłożone w COM ciała (`xipos`).
- `data.subtree_linvel` liczy się tylko na żądanie. Przed odczytem wywołaj `mujoco.mj_subtreeVel(m, d)` albo licz prędkość z różnic `subtree_com`.
- Domyślnie `autolimits="true"`, więc samo `range` włącza limit przegubu.

## 2. Struktura projektu

Kod leży w **korzeniu repo** (`fish-sim-v0/`), bez dodatkowego folderu `fish_demo/`.

```
fish-sim-v0/
  README.md               # jak uruchomić, co pokazuje każdy scenariusz, ograniczenia modelu
  pyproject.toml          # pakiet fishsim + [tool.pytest.ini_options] pythonpath = ["."]
  requirements.txt        # mujoco>=3.3.1, numpy, matplotlib, pytest, -e .
  fishsim/
    __init__.py
    config.py             # jeden dataclass ze WSZYSTKIMI parametrami (placeholdery opisane)
    model_builder.py      # generuje MJCF (string XML) z configu – N segmentów ogona parametrycznie
    hydraulics.py         # model ODE: pompa + 2 komory, sprzężony z kątem ogona
    buoyancy.py           # wypór per body + pęcherz balastowy + moment prostujący
    controllers.py        # generator objętości ogona, skręt, kaskadowy regulator głębokości
    sim.py                # pętla: odczyt stanu -> hydraulika -> momenty -> MuJoCo -> logowanie
  scripts/
    check_api.py          # etap 0: wersja mujoco i szybkie sprawdzenie API
    run_viewer.py         # interaktywny podgląd z klawiaturą
    run_scenarios.py      # scenariusze headless, zapis wykresów do results/
    sweep_frequency.py    # przegląd częstotliwości ogona
  tests/
    test_sanity.py
  results/                # wykresy PNG, CSV z logami
```

Środowisko: systemowy Python nie ma `pip`, więc tworzymy venv:
`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
Dla Pythona 3.14 są gotowe wheele `mujoco` 3.14.0. Jeśli `venv` nie zadziała: `conda create -n fishsim python=3.12`.

## 3. Model MJCF (model_builder.py)

- `<option timestep="0.002" integrator="implicitfast" density="1000" viscosity="0.0009"/>`. Integrator `implicit`/`implicitfast` jest zalecany przy siłach płynu. Grawitacja włączona.
- **Głowa/kadłub**: body z `<freejoint/>`, geom elipsoida o długości ok. 0.25 m i promieniu 0.05 m (placeholder). Uwaga: `size` w MJCF to **półosie**, czyli `size="0.125 0.05 0.05"`.
- **Ogon**: N = 5 segmentów (parametr), zwężających się, połączonych przegubami `hinge` wokół osi pionowej (ruch w płaszczyźnie poziomej). Przeguby mają `stiffness` i `damping` (sztywność i tłumienie silikonu, placeholdery) oraz `range` ok. ±35°.
- **Napęd tylko na początku ogona**: domyślnie K = 3 pierwsze przeguby są napędzane, 2 ostatnie pasywne (parametr K). Pasywny koniec ogona opóźnia się w fazie i tworzy falę biegnącą, bez której model bezstanowy daje mały lub zerowy ciąg (siła Kutty = 0 przy α = 90°). Sztywność pasywnych przegubów dobierz tak, by częstotliwość własna końca ogona leżała w zakresie sweepu (0.5–3 Hz). W README opisz to jako rezonans.
- **Płetwa ogonowa**: płaska elipsoida na końcu ostatniego segmentu, cienka w osi bocznej (Y), wysoka w osi pionowej (Z), jak u prawdziwej ryby. Ogon macha w kierunku Y, więc duża powierzchnia płetwy „pcha” wodę na boki. Sprawdź orientację wizualnie w viewerze.
- **Wszystkie geomy ciał ryby** (bez wyjątku, patrz §1): `fluidshape="ellipsoid"`, `fluidcoef` jawnie wpisane (domyślne wg dokumentacji: blunt 0.5, slender 0.25, angular 1.5, Kutta 1.0, Magnus 1.0), z komentarzem, co znaczy każdy współczynnik. Geomy czysto wizualne umieszczaj w `worldbody`, nie w ciałach ryby.
- **Kolizje**: wyłącz kolizje między częściami ryby (`contype`/`conaffinity`), np. głowa ↔ segment 2. Zostaw kolizję ryby z podłogą.
- **Masy i pływalność** (liczone w kodzie, nie strojone):
  - Masę i objętość każdego ciała licz z geomów. `model_builder` wypisuje sumy.
  - Objętość neutralna pęcherza `V_bl_neutral = m_total/ρ − V_geomów` musi wypaść **w środku** `[V_bl_min, V_bl_max]`. Wtedy `V_min` → ryba tonie, `V_max` → wypływa. Jeśli nie wypada w środku, popraw gęstości geomów (placeholdery), a nie zakres pęcherza.
  - **Trym wzdłużny**: x środka ciężkości całej ryby ma się pokrywać z x środka wyporu całej ryby (tolerancja ~1 mm). Koryguj przesunięciem `x_cb` kadłuba albo małą masą trymującą w kadłubie. Etap 1 wypisuje oba punkty.
- **Aktuator**: jeden `fixed tendon` po K napędzanych przegubach ze współczynnikami `w_i` (malejącymi ku końcowi) i jeden `motor` na tym tendonie. Siła tendonu `F = A_eff·r_eff·Δp` rozkłada się automatycznie na `τ_i = w_i·F`, a długość tendonu `L = Σ w_i θ_i` to dokładnie ta sama wielkość, której potrzebuje hydraulika (§4). Bez `ctrlrange` (ograniczenie daje zawór przelewowy w Pythonie).
- Podłoga na z = −3 m i powierzchnia wody jako przezroczysta płaszczyzna wizualna na z = 0 (tylko wizualnie, bez kolizji). Kilka znaczników (np. kolumny) w scenie, żeby był widoczny ruch.

## 4. Hydraulika (hydraulics.py)

Uproszczony zamknięty układ jak w SoFi: pompa przepompowuje wodę z komory R do L i odwrotnie. Komory leżą po obu stronach ogona, więc **napełnienie komory zgina ogon**.

- Wejście: `u ∈ [−1, 1]` (komenda pompy). Pompa jako człon inercyjny I rzędu: `dQ/dt = (u·Q_max − Q)/τ_pump`.
- Stan objętości: `V_p` = objętość przepompowana z R do L. `V_L = V0 + V_p`, `V_R = V0 − V_p` (układ zamknięty, suma stała, sprawdź to w teście).
- Objętość „zajęta” przez zgięty ogon: `V_g = A_eff · r_eff · L`, gdzie `L = Σ w_i θ_i` (długość tendonu z §3).
- Różnica ciśnień (ze znakiem!) z podatności układu: `Δp = clip((V_p − V_g)/C_h, −p_max, +p_max)`. To jest **sprężyna hydrauliczna**: pompa zadaje objętość, ogon nadąża, a różnica się ściska.
- Zawór przelewowy: gdy `|Δp| = p_max` i `Q` pcha w tę samą stronę, przepływ idzie zaworem, więc `dV_p/dt = 0`. W przeciwnym razie `dV_p/dt = Q`.
- Ciśnienia do wykresów: `p_L = p_pre + Δp/2`, `p_R = p_pre − Δp/2` (`p_pre` = ciśnienie wstępne, placeholder; może być 0, wtedy jedno z ciśnień jest ujemne jako nadciśnienie względne – opisz to).
- Moment na ogonie: siła tendonu `F = A_eff · r_eff · Δp` (→ `data.ctrl`). Zgodność energetyczna: `Δp · dV_g = F · dL = Σ τ_i dθ_i`. Napisz to w komentarzu.
- Integracja jawnym Eulerem z krokiem MuJoCo. W komentarzu opisz **dwa** warunki stabilności:
  1. `dt ≪ τ_pump` (pompa jako człon I rzędu),
  2. sprężyna hydrauliczna liczona jawnie: sztywność na tendonie `k_h = (A_eff·r_eff)²/C_h`, częstotliwość `ω_n ≈ sqrt(k_h / I_eff)` (`I_eff` = bezwładność ogona widziana przez tendon; masa dołączona NIE jest w macierzy mas, więc `I_eff` jest małe). Warunek: `ω_n · dt < 0.5` (z zapasem względem granicy 2).
  `config` liczy `ω_n · dt` przy starcie i wypisuje ostrzeżenie, gdy warunek nie jest spełniony.
- Fizyczna lekcja do pokazania: przy stałym `Q_max` amplituda wychylenia spada wraz ze wzrostem częstotliwości, bo pompa nie nadąża. Po nasyceniu `u` amplituda `L ≈ Q_max/(2πf·A_eff·r_eff)`. Do tego dochodzi rezonans pasywnego końca ogona. Sweep w etapie 6 ma pokazać oba efekty.

## 5. Wypór i balast (buoyancy.py)

- **Nie używaj** `gravcomp` jako wyporu (to kompensacja grawitacji w COM, nie daje momentu prostującego ani zmiennej objętości). Licz wypór jawnie.
- Dla każdego body: `F_b = ρ · g · V_body · s(z)` w górę (V z objętości geomów). Dla segmentów ogona przyłóż w COM.
- Dla kadłuba: `F_b = ρ · g · (V_kadłuba + V_pęcherza) · s(z)`, przyłożona w środku wyporu CB.
  - CB jest **stały w układzie kadłuba**: `r_local = (x_cb, 0, z_cb)`, `z_cb` placeholder np. +1 cm (nad COM), `x_cb` z trymu (§3).
  - W układzie świata: `r_world = xmat_kadłuba · r_local`.
  - Przez `data.xfrc_applied` (siła i moment w układzie świata, w COM body) dodaj siłę `F_b` i moment `r_world × F_b`.
  - W komentarzu wyjaśnij: gdyby `r` było stałe w świecie, to `r ∥ F_b`, a moment = 0. Moment prostujący bierze się z tego, że przy przechyle `r` obraca się razem z kadłubem.
- Pęcherz: `V_pęcherza ∈ [V_min, V_max]`, pompa balastowa śledzi zadaną objętość: `dV/dt = clip(k_b·(V_ref − V), −q_bal_max, +q_bal_max)` (placeholdery).
- Powierzchnia wody: częściowe zanurzenie jest **poza zakresem demo**, ale żeby ryba nie odlatywała w nieskończoność, stosujemy zgrubne liniowe wygaszanie: `s(z) = clip((r_c − z)/(2·r_c), 0, 1)`, gdzie `z` = wysokość COM ciała, `r_c` = promień kadłuba. W README opisz to jako „łatkę”, nie model fizyczny.

## 6. Sterowanie (controllers.py)

- **Generator rytmu zadaje objętość, nie przepływ:**
  - `V_ref(t) = a(t) · A_V · sin(2π f t) + V_bias`, gdzie `a(t)` = rampa 0 → 1 przez pierwszą 1 s (miękki start, mniej asymetrii pierwszego uderzenia).
  - Komenda pompy: `u = clip((dV_ref/dt + K_v·(V_ref − V_p)) / Q_max, −1, 1)` (feed-forward + korekta proporcjonalna).
  - W komentarzu wyjaśnij, dlaczego bias w `u` (v1) powodował dryf: objętość całkuje przepływ.
- **Skręt**: `V_bias ≠ 0` (stałe ugięcie ogona = asymetria uderzeń).
- **Głębokość – kaskada:**
  - zewnętrzna pętla: PID `z_ref → V_ref_pęcherza = V_bl_neutral + PID(e)`, z anti-windup (clamping całki) i nasyceniem do `[V_min, V_max]`;
  - wewnętrzna: pompa balastowa z §5 śledzi `V_ref` z limitem szybkości.
  - W komentarzu wyjaśnij, dlaczego nie `z → dV/dt` wprost (wtedy P działa jak I, a obiekt staje się potrójnym integratorem).
  - Wzmocnienia dobierz eksperymentalnie, opisz w README, jak to zrobiłeś (np. najpierw P+D bez I, potem małe I).
- Ograniczenie `z_ref ≤ −0.3 m` w kontrolerze (żeby PID nie wyciągał ryby na powierzchnię).

## 7. Etapy realizacji

0. **Środowisko i API**: venv, instalacja, `scripts/check_api.py` wypisuje wersję `mujoco` i w kilku liniach sprawdza: (a) ciało o gęstości wody bez `xfrc_applied` tonie (potwierdza brak wyporu w modelu płynu), (b) `xfrc_applied` w górę = `m·g` zatrzymuje je, (c) `launch_passive` ma `key_callback` i `set_texts`.
1. **Model statyczny**: MJCF się ładuje, render w viewerze, ryba stoi w wodzie. Wypisz masy, objętości, wypadkową pływalność [N] przy `V_min`, `V_neutral`, `V_max`, położenie CG i CB całej ryby (x, z), oraz `ω_n · dt` z §4.
2. **Wypór i stabilność**: test zawieszenia (pęcherz w położeniu neutralnym → dryf pionowy mały, brak nurkowania), test prostowania (start z przechyłem 30° → wraca do pionu).
3. **Hydraulika offline**: sama hydraulika bez MuJoCo, z ogonem zastąpionym prostym modelem (sprężyna + tłumik + bezwładność na `L`). Wykres Q, p_L, p_R, Δp, F dla sinusa. Test zachowania objętości, zmiany znaku Δp i braku dryfu przy `V_bias`.
4. **Pływanie**: hydraulika + MuJoCo, ruch do przodu. Porównanie: woda włączona vs `density=0, viscosity=0` (wypór zostaje). Bez płynu prędkość COM ≈ 0 (zachowanie pędu – siły wewnętrzne nie przesuną środka masy). To pokazuje, że ciąg pochodzi z modelu płynu.
   **Jeśli ryba nie płynie** (zgodnie z §1.6): zanim cokolwiek zmienisz, zrób wykres θ_1 i θ_N w czasie (czy jest przesunięcie fazy?), sprawdź orientację płetwy w viewerze i znak `qfrc_fluid` na płetwie. Dopiero potem decyzja, co zmienić, opisana w README.
5. **Skręt i głębokość**: scenariusz skrętu (trajektoria XY) i skoki zadanej głębokości (−0.5 → −1.5 → −1.0 m).
6. **Sweep**: f = 0.5…3 Hz → średnia prędkość i amplituda kąta ogona. Wykres z dwiema osiami Y.
7. **Viewer interaktywny**: `mujoco.viewer.launch_passive` z `key_callback` (dostaje kod klawisza `int`, zgodny z GLFW, tylko wciśnięcie).
   - Strzałki ←/→ to skręt (`V_bias`), ↑/↓ to częstotliwość, PageUp/PageDown to głębokość zadana.
   - Callback działa w wątku viewera. Zmienia tylko zmienne sterujące w Pythonie, a zmiany w `data` rób pod `with viewer.lock():`.
   - PageUp ma wbudowaną funkcję (wybór rodzica zaznaczonego ciała), ale tylko gdy jakieś ciało jest zaznaczone. Odnotuj to w README.
   - Nakładka tekstowa przez `viewer.set_texts(...)` ze stanem (prędkość, głębokość, p_L, p_R, V_pęcherza, f, V_bias). Print w konsoli jako zapas.
   - Na macOS passive viewer wymaga uruchomienia przez `mjpython`. Na Linuksie z Waylandem GLFW działa przez XWayland; jeśli okno się nie otwiera, opisz obejście w README.

Orientacyjny czas (dla wykonawcy): etap 0–1 ok. 1 h, 2 ok. 1 h, 3 ok. 1 h, 4 od 1 h (gdy ryba płynie od razu) do 3 h (gdy trzeba diagnozować ciąg), 5 ok. 1–2 h (strojenie PID), 6 ok. 30 min, 7 ok. 1 h.

## 8. Wyniki (results/)

Każdy scenariusz zapisuje PNG + CSV:
- `s1_straight.png`: prędkość postępowa, kąt ogona (θ_1 i θ_N, widać fazę), Δp i ciśnienia.
- `s2_fluid_on_off.png`: porównanie prędkości COM z wodą i bez.
- `s3_turn.png`: trajektoria XY.
- `s4_depth.png`: głębokość zadana vs rzeczywista, objętość pęcherza (zadana i rzeczywista).
- `s5_sweep.png`: prędkość i amplituda vs częstotliwość.
- `s6_righting.png`: kąt przechyłu w czasie.

Nagrywanie wideo (offscreen, `MUJOCO_GL=egl`) jest **opcjonalne**. Jeśli nie działa w danym środowisku, pomiń bez walki i odnotuj.

## 9. Testy (tests/test_sanity.py)

Definicje pomiarów (używaj ich w testach i wykresach):
- **Prędkość postępowa** = poziome przesunięcie `subtree_com` ryby w ostatnich pełnych cyklach ogona ÷ czas. Pomijaj pierwsze 2 s (rampa + transient). Nie mierzy się głowy, bo oscyluje.
- **Przechył** = kąt między osią z kadłuba a osią z świata, `acos(z_body · z_world)`.

Testy:
- Model się ładuje, liczba przegubów ogona = N, liczba napędzanych = K, każdy geom ryby ma `fluidshape` = ellipsoid.
- Hydraulika: `V_L + V_R` stałe z dokładnością numeryczną; `|Δp| ≤ p_max` zawsze.
- Hydraulika: przy sinusie Δp (i moment) **zmienia znak** w każdym cyklu.
- Hydraulika: przy `V_bias ≠ 0` średnia `V_p` po 20 s jest stała (brak dryfu), równa `V_bias` ± tolerancja.
- Zawieszenie: |Δz| < 5 cm i |pochylenie| < 5° po 5 s bez napędu (próg dostosuj i uzasadnij).
- Pęcherz max → Δz > 0 w ciągu 2 s ze startu z −1.5 m (ryba nie dociera do powierzchni); pęcherz min → Δz < 0.
- Prostowanie: max |przechył| w oknie 4–5 s < połowa początkowego (obwiednia, nie wartość chwilowa).
- Woda włączona → prędkość postępowa > 0 (próg uzasadnij); woda wyłączona → |prędkość COM| < 1 mm/s.
- Brak NaN w stanie po 20 s symulacji.
- `ω_n · dt < 0.5` dla domyślnego configu.

## 10. README – obowiązkowa sekcja „Ograniczenia modelu”

Napisz uczciwie, czego model NIE robi:
- brak prawdziwego CFD (model bezstanowy, brak wiru i śladu),
- masa dołączona: MuJoCo liczy ją tylko częściowo (brak członu `−m_A·v̇`); w trybie `armature` dodajemy ją jako bezwładność, ale tylko na przekątnej i bez translacji kadłuba,
- ogon jako sztywne segmenty zamiast ciągłego silikonu,
- hydraulika jako sprężyna liniowa (bez nieliniowości silikonu, bez dynamiki zaworu),
- brak częściowego zanurzenia przy powierzchni (tylko zgrubne wygaszanie wyporu),
- brak kabla ROV (tether),
- wszystkie parametry niezidentyfikowane.

Dodaj krótki akapit: jak w przyszłości skalibrować model (pomiar kąta ogona vs ciśnienie → `C_h`, `A_eff·r_eff`; pomiar ciągu na uwięzi; nagranie trajektorii w basenie i dopasowanie `fluidcoef`).

## 11. Definition of done

- `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pytest` → wszystkie testy zielone.
- `python scripts/run_scenarios.py` → generuje 6 wykresów w `results/`.
- `python scripts/run_viewer.py` → interaktywne sterowanie działa.
- README pozwala osobie uczącej się zrozumieć, co pokazuje każdy wykres i jakie są ograniczenia.
