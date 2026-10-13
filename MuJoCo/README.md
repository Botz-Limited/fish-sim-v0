# fish-sim-v0

Edukacyjne demo MuJoCo: robot-ryba z hydraulicznym ogonem i pęcherzem balastowym.
Specyfikacja: [SPEC_fish_mujoco_demo.md](SPEC_fish_mujoco_demo.md). **To nie jest skalibrowany cyfrowy bliźniak** – wszystkie parametry to placeholdery.

## Uruchomienie

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pytest -q                              # testy
.venv/bin/python scripts/check_api.py            # etap 0: sprawdzenie API MuJoCo
.venv/bin/python scripts/show_model.py --viewer  # etap 1: model statyczny
.venv/bin/python scripts/run_scenarios.py        # wszystkie wykresy do results/
.venv/bin/python scripts/sweep_frequency.py      # sam przegląd częstotliwości
.venv/bin/python scripts/run_viewer.py           # interaktywny viewer
```

## Viewer – sterowanie

| Klawisz | Działanie |
|---|---|
| ← / → | skręt: `V_bias` −/+ 0.5 ml (→ = w prawo), max ±4 ml |
| ↑ / ↓ | częstotliwość ogona ±0.25 Hz (1.5…2.5 Hz – zakres zaworu), bez skoku fazy |
| PgUp / PgDn | głębokość zadana ±0.25 m (najpłycej −0.3 m) |
| Spacja | stop/start ogona (ryba wytraca prędkość ślizgiem) |
| Backspace | reset (wbudowany; skrypt resetuje też hydraulikę, pęcherz i całkę PID) |

Nakładka w lewym górnym rogu (czas, prędkość, głębokość/zadana, f, V_bias, p_L/p_R, objętość pęcherza) jest **po angielsku**: wbudowana czcionka MuJoCo ma tylko znaki ASCII 32–126, więc polskie litery i strzałki wyświetlały się błędnie. Test `test_viewer_overlay_text_is_ascii` pilnuje, żeby tak zostało. Ten sam stan co 1 s w konsoli.

**Odczyty sił i napędu** (`fishsim/readouts.py`), pod stanem w tej samej nakładce:
- napęd: moment z hydrauliki na ogonie [mN·m], sterowanie pompy u i przepływ Q, kąty 5 przegubów ogona;
- siły wody [mN] na całą rybę, na ogon+płetwę i na kadłub, w układzie ryby (`fwd` = naprzód, `side` = w bok), oraz wypór − ciężar;
- strzałki w scenie: magenta = siła wody na każde ciało (1 N = 15 cm), cyan = wypór − ciężar przy środku masy (10 mN = 2 cm).

MuJoCo podaje siłę płynu tylko łącznie (`qfrc_fluid`), więc siła na każde ciało jest liczona ponownie na kopii `data`, z „mokrym” tylko jednym ciałem naraz. Symulacja nie widzi tych obliczeń (test `test_fluid_forces_per_body_add_up_and_leave_sim_untouched`).
Opcje: `--speed 0.5` (2× wolniej niż czas rzeczywisty), `--font 200` (większy tekst, np. na ekranie 2K).

- **PageUp** ma wbudowaną funkcję viewera (wybór rodzica zaznaczonego ciała), ale tylko gdy jakieś ciało jest zaznaczone (podwójny klik). Nie zaznaczaj ciał podczas sterowania.
- **macOS:** passive viewer wymaga `mjpython scripts/run_viewer.py`.
- **Linux/Wayland:** komunikat `Failed to load plugin 'libdecor-gtk.so'` to tylko ostrzeżenie o dekoracjach okna – viewer działa. Jeśli okno się nie otwiera, spróbuj wymusić XWayland (GLFW wybiera X11, gdy nie widzi Waylanda): `env -u WAYLAND_DISPLAY .venv/bin/python scripts/run_viewer.py`.
- **Bez okna:** `scripts/run_viewer.py --selftest` – te same klasy sterowania, skrypt klawiszy, wydruk stanu.

## Co pokazuje każdy wykres (`results/`)

Każdy PNG ma obok CSV z danymi. Wszystko generuje `scripts/run_scenarios.py`.

| Plik | Co widać | Na co patrzeć |
|---|---|---|
| `s1_straight.png` | pływanie na wprost przy 2 Hz: prędkość COM, kąty przegubów, ciśnienia | prędkość ustala się na ~23 cm/s po ~2 s; w powiększeniu koniec ogona (θ5) **spóźnia się** względem nasady – to fala biegnąca do tyłu, która daje ciąg; Δp dochodzi do p_max tylko przy starcie (pierwszy stan zaworu trwa ≥ 0.2 s przy małym V_ref, otwiera się zawór przelewowy); w ustalonym pływaniu ≤ 41 kPa |
| `s2_fluid_on_off.png` | ta sama ryba: woda / bez wody / domyślny model MuJoCo | bez wody prędkość = 0 (zachowanie pędu), więc ciąg pochodzi z sił płynu; zielona linia pokazuje, ile traci domyślny model masy dołączonej |
| `s3_turn.png` | trajektorie XY dla V_bias = −3…+3 ml | ugięcie ogona w prawo -> okrąg w prawo; promień maleje ze wzrostem V_bias |
| `s4_depth.png` | skoki głębokości −0.5 -> −1.5 -> −1.0 m podczas pływania | pęcherz na ograniczeniu (0 / 40 ml) = maksymalna siła; zmiana o 1 m trwa ~35 s; anti-windup trzyma przeregulowanie ~3 cm |
| `s5_sweep.png` | prędkość i amplituda ogona dla f = 1.5…2.5 Hz (zakres zaworu) | maksimum prędkości ~1.75 Hz; zawór przełącza się tylko w szczytach (2 razy na cykl), a amplituda L spada z f |
| `s6_righting.png` | start z przechyłem 30° | wraca do pionu w ~0.3 s (CB nad CG); przechył pobudza wolne, słabo tłumione kołysanie wzdłużne |
| `h3_hydraulics.png`, `h3_offline_sweep.png` | sama hydraulika bez MuJoCo (etap 3), 1.5 Hz | Δp zmienia znak co cykl; przepływ to ±Q_const, zawór przełącza się w szczytach; skręt V_bias daje stałe przesunięcie bez dryfu; amplituda spada z f i leży pod trójkątem `Q_const/(4f·A·r)` |

## Ograniczenia modelu

Czego ten model **nie robi** (i co z tego wynika):

1. **Brak prawdziwego CFD.** Model płynu MuJoCo jest bezstanowy i quasi-statyczny: siła na każdej elipsoidzie zależy tylko od jej chwilowej prędkości. Nie ma wirów, śladu za płetwą, opóźnienia przepływu ani oddziaływania między bryłami (płetwa nie „czuje” wody odepchniętej przez kadłub). U prawdziwych ryb ciąg w dużej części pochodzi z wirów zrzucanych z płetwy.
2. **Masa dołączona tylko w przybliżeniu.** MuJoCo liczy ją częściowo (bez członu `−m_A·v̇`), co dawało fałszywy ciąg do tyłu. W trybie `added_mass="armature"` dodajemy ją jako bezwładność, ale:
   - tylko **przekątna** macierzy (bez sprzężeń między przegubami i kadłubem),
   - liczona raz, dla **wyprostowanego** ogona,
   - **bez translacji** kadłuba (te stopnie swobody są w układzie świata), więc ryba rozpędza się szybciej niż prawdziwa (0 -> 23 cm/s w ~1.5 s).
3. **Ogon jako sztywne segmenty** (pseudo-rigid-body model) zamiast ciągłego silikonu. Napędzane przeguby mają mody wewnętrzne 0.6–1.1 Hz, bo hydraulika steruje tylko kombinacją `L = Σw·θ` (patrz etap 6).
4. **Hydraulika liniowa:** stała podatność `C_h`, idealny zawór przelewowy, pompa o stałym wydatku, a przełączenie zaworu kierunkowego jako człon I rzędu (`τ_valve`) z minimalnym czasem stanu 0.2 s. Brak nieliniowości silikonu, strat przepływu, kawitacji, mocy i sprawności pompy.
5. **Brak częściowego zanurzenia.** Przy powierzchni wypór jest tylko zgrubnie wygaszany (liniowo w pasie ±5 cm), żeby ryba nie odlatywała. Nie ma fal ani efektów powierzchni.
6. **Brak kabla ROV (tether)**, prądów wody, dna wpływającego na przepływ.
7. **Sprzężenie jawne** hydrauliki z MuJoCo: działa przy `ω_n·dt ≈ 0.05` (sprawdzane w testach), ale bardzo sztywny układ (sama ciecz bez podatnych ścianek) wymagałby mniejszego kroku albo całkowania niejawnego.
8. **Wszystkie parametry są niezidentyfikowane** (`# PLACEHOLDER` w `fishsim/config.py`). Liczby z wykresów (23 cm/s, 1.75 Hz, 35 s na 1 m) pokazują *mechanizmy*, nie osiągi konkretnego robota.

### Jak w przyszłości skalibrować model

1. **Ogon na stole (bez wody):** zadawać ciśnienie i mierzyć kąt ogona -> `A_eff·r_eff` (nachylenie moment/ciśnienie) i sztywności przegubów; zmierzyć objętość przetłoczoną na radian -> `C_h`.
2. **Ogon w wodzie, kadłub unieruchomiony:** sweep częstotliwości z pomiarem kąta końca ogona -> rzeczywisty rezonans (`passive_resonance_hz`) i tłumienie.
3. **Ciąg na uwięzi:** ryba na czujniku siły, pomiar średniego ciągu vs f i amplituda -> pierwsza weryfikacja modelu płynu.
4. **Trajektoria w basenie:** nagranie kamerą (prędkość, promień skrętu, czas zmiany głębokości) i dopasowanie `fluidcoef` (najpierw `C_blunt` i `C_slender` do prędkości ustalonej, potem `C_Kutta` do skrętu).
5. Pęcherz: pomiar wydatku pompy balastowej (`q_bal_max`) i wypadkowej pływalności przy pustym/pełnym pęcherzu (waga podwodna).

## Obserwacje z etapów

### Etap 1 – model statyczny
- Masy są **liczone**, nie strojone: masa kadłuba wynika z neutralnej pływalności przy pęcherzu w połowie zakresu, a przesunięcie środka wyporu kadłuba `x_cb ≈ −4.7 mm` – z trymu wzdłużnego (silikonowy ogon jest cięższy od wody i ciągnie tył w dół).
- Liczby w MJCF muszą być zapisane z pełną precyzją. Zaokrąglenie masy do 6 cyfr dawało resztkową siłę ~3·10⁻⁵ N przy „neutralnym” pęcherzu.

### Etap 2 – wypór i stabilność (`results/s6_righting.png`)
- Prostowanie z 30° trwa ~0.3 s do pierwszego przejścia przez pion; potem słabo tłumione kołysanie < 5°.
- Przechył sprzęga się z **pochyleniem** (±0.6°, okres ~2.2 s, wolno gasnące). Powód: długi ogon daje dużą bezwładność wokół osi Y przy małym momencie prostującym (CB tylko ~8 mm nad CG całej ryby), a model płynu słabo tłumi wolne obroty.
- Zawieszenie przy neutralnym pęcherzu: dryf 0.000 cm w 5 s – równowaga jest dokładna z konstrukcji, więc próg testu zaostrzono z 5 cm do 5 mm.

### Etap 3 – hydraulika offline (`results/h3_hydraulics.png`, `results/h3_offline_sweep.png`)
- Model sprzężony: `Δp = (V_p − A·r·L)/C_h` – pompa zadaje objętość, ogon „robi miejsce”, nadmiar ściska układ. Δp zmienia znak w każdym cyklu (w v1 było zawsze ≥ 0).
- Generator zadaje objętość `V_ref`, nie przepływ. Skręt `V_bias = 3 ml` przy 1.5 Hz daje stałe przesunięcie średniej `V_p` = 2.99 ml bez dryfu (przy 2 Hz 3.06 ml, przy 2.5 Hz 2.8 ml – zależy od tego, gdzie wypadają szczyty; to nie całkowanie).
- **Pompa o stałych obrotach + zawory kierunkowe ±1.** Przepływ to zawsze `±Q_const` (60 ml/s), płynnej komendy nie ma. Regulator przekaźnikowy z histerezą `δ = 1 ml` przełącza zawór, gdy `|V_ref − V_p| > δ`.
- Dwa reżimy, granica `f_track = Q_const/(2π·A_V) ≈ 1.19 Hz`:
  - **poniżej** – `V_p` mogłoby śledzić `V_ref` piłą, ale zawór musiałby przełączać się ~26 razy na cykl przy 0.5 Hz i ~9 przy 1 Hz, a drgania przekaźnika pobudzały mody ogona (L 37° zamiast 23° przy 1 Hz),
  - **powyżej** – zawór przełącza się tylko w szczytach (2 razy na cykl), objętość to trójkąt o amplitudzie trochę **pod** `Q_const/(4f)` (6.7 ml zamiast 7.5 ml przy 2 Hz; różnicę zjada czas przełączania `τ_valve`).
- **Ograniczenia zaworu:** prawdziwy zawór przełącza się najwyżej ~5 razy/s, więc każdy stan trwa ≥ `valve_min_dwell = 0.2 s`. Stąd zakres częstotliwości `tail_freq_min…tail_freq_max = 1.5…2.5 Hz`: dolna granica nad `f_track` (patrz niżej), górna `1/(2·0.2 s)` – wyżej zawór nie zdąży przełączyć się 2 razy na cykl. Generator obcina zadaną częstotliwość do tego zakresu.
- **Dlaczego nie 1.25 Hz:** tuż nad `f_track` zawór przełączał się 3–4 razy na cykl, a średnia `V_p` z pojedynczego cyklu skakała 0.1…5.1 ml przy `V_bias = 3 ml` (skręt szarpany), do tego ryba płynęła wolniej (20.5 cm/s) niż przy 1.5 Hz. Od 1.5 Hz wzwyż – równo 2 przełączenia i stała średnia.
- Z jednym stałym wydatkiem przy przełączaniu tylko w szczytach nie da się wybrać jednocześnie f i amplitudy: amplituda wynika z f. Mniejszą amplitudę przy danym f daje tylko częstsze przełączanie.
- Ciśnienia są małe (±9 kPa przy p_max = 50 kPa), bo zastępczy ogon ma tylko sprężynę silikonu i umowne tłumienie. Z wodą (etap 4) obciążenie wzrośnie.

### Etap 4 – pływanie (`results/s1_straight.png`, `results/s2_fluid_on_off.png`)

**Wynik:** 23 cm/s przy 2 Hz (~0.4 długości ciała/s), bez wody 0.00 cm/s. Ale pierwsza wersja **nie pływała** – poniżej diagnoza, bo to najciekawsza lekcja z całego demo.

1. **Objaw:** z domyślnym modelem płynu MuJoCo ryba płynęła 0.5–3 cm/s, przy 3 Hz *do tyłu*, a przy 1 Hz stale tonęła (3.5 cm/s) mimo idealnie zrównoważonego wyporu.
2. **Pomiar zamiast strojenia:** bilans sił pionowych – wypór = ciężar co do 10⁻⁵ N, średnia siła płynu ≈ 0, a mimo to ryba opada ze stałą prędkością. Czyli machanie ogonem samo wytwarza średnią siłę w dół, równoważoną przez opór przy tej prędkości.
3. **Przyczyna:** MuJoCo liczy masę dołączoną elipsoid (`geom_fluid[6:12]` – np. płetwa: 239 g wody vs 29 g własnej masy!), ale w sile płynu zostawia tylko człon `−ω×(m_A·v)`, a człon `−m_A·v̇` jest w źródle wyłączony. W przepływie potencjalnym oba człony razem dają zerową średnią siłę w cyklu; sam pierwszy daje niefizyczną siłę ~`m_A·ω²·d` – dla płetwy machającej wokół przegubu: zawsze do tyłu.
4. **Poprawka (tryb `added_mass="armature"`):** zerujemy `m_A, I_A` w modelu płynu, a bezwładność wody dodajemy jako `armature` przegubów ogona i obrotów kadłuba (przekątna macierzy masy dołączonej, z tych samych współczynników MuJoCo – nic nie zgadujemy). Same te zmiany: +6–7 cm/s i koniec tonięcia.
5. **Druga lekcja – rezonans:** z wodą koniec ogona jest ~3× cięższy, więc pasywne przeguby o sztywności dobranej „na sucho” miały rezonans < 1 Hz. Powyżej rezonansu faza dąży do 180° i fala biegnie do głowy → ciąg do tyłu. Dlatego sztywność pasywna jest teraz **liczona** z zadanej częstotliwości rezonansu `passive_resonance_hz` (3 Hz) i bezwładności z wodą.
6. Porównanie trybów jest na `s2_fluid_on_off.png` (zielona linia = domyślny MuJoCo: 5.1 cm/s).

Ograniczenia tej poprawki: masa dołączona tylko na przekątnej (bez sprzężeń między przegubami) i bez translacji kadłuba (te stopnie swobody są w układzie świata). Dlatego ryba rozpędza się szybciej niż prawdziwa (0 → 23 cm/s w ~1.5 s).

### Etap 5 – skręt i głębokość (`results/s3_turn.png`, `results/s4_depth.png`)

**Skręt.** Stałe ugięcie ogona `V_bias` (zadana objętość, nie przepływ) daje skręt w stronę ugięcia ogona, jak u prawdziwej ryby. Zależność jest prawie liniowa i symetryczna: ±1.5 ml → ∓3.1…3.3°/s, ±3 ml → ∓6.6…6.8°/s. Prędkość postępowa spada przy ciasnym skręcie, bo część ciągu idzie na bok.

**Głębokość – jak dobrałem wzmocnienia** (skok −1.0 → −1.5 m, metryki: przeregulowanie, czas wejścia w ±5 cm, uchyb końcowy):
1. Sam P (kp = 20…100 ml/m): przeregulowanie tylko ~5 cm – opór pionowy (kwadratowy) sam tłumi ruch. Większe kp = szybciej (16 s → 9 s).
2. PD: kd usuwa przeregulowanie. kp = 200 ml/m, kd = 300 ml·s/m → 0 cm przeregulowania, 6.3 s przy zawisie.
3. Podczas pływania pojawia się uchyb ~1 cm: pływanie daje małą średnią siłę pionową z płynu (pęcherz w równowadze ma 21.8 ml zamiast 20). Małe ki = 20 ml/(m·s) usuwa go kosztem ~3 cm przeregulowania.

Obserwacje z `s4_depth.png`:
- Podczas pływania zmiana głębokości o 1 m trwa ~35 s, a w zawisie ~6 s. Pęcherz siedzi na ograniczeniu (0 ml albo 40 ml), więc siła jest stała (±0.196 N), a opór pionowy jest dużo większy, bo siła oporu ∝ |v|·v_z, a |v| zawiera prędkość do przodu (23 cm/s). To fizyczne ograniczenie pęcherza, nie regulatora.
- Anti-windup: całka nie rośnie, gdy pęcherz jest nasycony, inaczej po 30 s nasycenia przeregulowanie byłoby duże.
- Pochylenie zmienia się o ~0.5° przy zmianie objętości pęcherza: wypór pęcherza działa w CB kadłuba (`x_cb ≈ −4.7 mm`), więc zmienia trym.

### Etap 6 – przegląd częstotliwości (`results/s5_sweep.png`, `scripts/sweep_frequency.py`)

Zakres: 1.5…2.5 Hz (zawór ≤ 5 przełączeń/s, patrz etap 3).

| f [Hz] | 1.5 | 1.75 | 2.0 | 2.25 | 2.5 |
|---|---|---|---|---|---|
| prędkość [cm/s] | 24.2 | 24.6 | 23.1 | 21.1 | 18.9 |
| amplituda L [°] | 26.9 | 22.4 | 19.0 | 17.4 | 16.9 |
| przełączeń zaworu na cykl | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |

Maksimum prędkości: **24.6 cm/s przy 1.75 Hz**. Sterowanie prędkością częstotliwością daje więc tylko ~19…25 cm/s.

- **Pompa nie nadąża:** powyżej `f_track = Q_const/(2π·A_V) ≈ 1.19 Hz` zawór przełącza się tylko w szczytach, a amplituda `L` (to, czym steruje hydraulika) spada ~1/f. Prędkość rośnie z f do ~1.75 Hz, potem maleje.
- **1.25 Hz (poza zakresem):** za blisko `f_track` – zawór dokładał 1–2 przełączenia na cykl, L = 30.7° zamiast ~23°, ruch nierówny z cyklu na cykl, 20.5 cm/s.
- **Poniżej `f_track` (przed ograniczeniem zakresu)** przekaźnik pobudzał ogon: przy 1 Hz L = 37° zamiast ~23° (zawór ~8 przełączeń/cykl). Większe δ albo minimalny czas stanu zaworu tylko pogarszały sprawę (40–45°) – stąd dolna granica częstotliwości zamiast strojenia przekaźnika.
- **Porównanie ze starym modelem (płynna pompa `u·Q_max`):** prędkość przy 2 Hz 23.1 vs 22.1 cm/s, maksimum przesunęło się z 1.5 Hz (23.6 cm/s) na 1.75 Hz (24.6 cm/s). Przełączanie tylko w szczytach daje trójkąt objętości, który przenosi więcej objętości na cykl niż nasycona płynna pompa.
- **Rezonans:** faza końca ogona przechodzi przez 90° przy ~2 Hz. To **niżej** niż `passive_resonance_hz = 3 Hz`, bo ta wartość jest liczona przy nieruchomym kadłubie i „zamrożonych” pozostałych przegubach. W pełnym modelu kadłub się odrzuca, a sprężyna hydrauliczna (ω_n ≈ 3.6 Hz) sprzęga się z ogonem.
- **Mody wewnętrzne napędzanych przegubów** (0.62 / 0.84 / 1.09 Hz, sztywność silikonu 0.3 N·m/rad przy masie z wodą): hydraulika steruje tylko kombinacją `L = Σw·θ`, a przeguby mogą ruszać się przeciwnie do siebie. Dlatego dolny zakres i drgania przekaźnika są problematyczne. `stiffness_actuated` to placeholder sprzed dodania masy dołączonej – do identyfikacji z pomiarów, nie strojony.
