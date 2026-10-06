# fish-sim-v0 – model systemowy robota-ryby w OpenModelica

Uproszczony, **edukacyjny i nieskalibrowany** model robota-ryby w Modelice: silnik DC → pompa → przewody → komory → ogon, plus balast i ruch do przodu. Specyfikacja: [`SPEC_fish_openmodelica_demo.md`](SPEC_fish_openmodelica_demo.md). Wszystkie parametry konstrukcyjne to placeholdery do identyfikacji.

## Stan prac

| Etap | Zakres | Status |
|---|---|---|
| 1 | Złącze hydrauliczne, `Pipe`, `Reservoir`, `VolumeFlowSource` + testy | gotowe |
| 2 | `Chamber` (krzywa p–V z tabeli lub CSV), `ReliefValve` + testy | gotowe |
| 3 | `Battery`, `HBridge`, `DCMotor`, `GearPump` → scenariusz `HydraulicsStep` | gotowe |
| 4 | `TailEquivalent`, `CPG`, podukład `TailDrive` → `TailFlapping`, `FrequencySweep` (`sweep.py`), `ReliefValveDemo` | gotowe |
| 5 | Bilans energii w `TailDrive` → `EnergyBudget` + test zamknięcia bilansu | gotowe |
| 6 | `BallastSyringe`, `VerticalDynamics`, `DepthPID` (kaskada) → `DepthControl`, test `BallastStatics` | gotowe |
| 7 | `LighthillFin` (ciąg, placeholder), `SurgeDynamics` → `SwimForward`, `sweep.py --swim`, testy `SurgeTerminalVelocity`, `FinPrescribedMotion` | gotowe |
| 8 | FMU + FMPy | – |

## Wersje

| Narzędzie | Wersja |
|---|---|
| OpenModelica (omc, OMEdit, OMSimulator) | 1.27.1 |
| Modelica Standard Library | 4.1.0 (jednostki: `Modelica.Units.SI`) |
| OMPython | 4.1.0 (klasa `ModelicaSystemOMC`; stara `ModelicaSystem` jest przestarzała) |
| FMPy | 0.3.32 |
| Python | 3.14 |

## Instalacja (Ubuntu)

```bash
setup/install_system.sh   # sudo: repozytorium apt OpenModelica, omc/OMEdit/OMSimulator, git, python3-venv
setup/install_user.sh     # bez sudo: .venv z requirements.txt + MSL 4.1.0 przez menedżer pakietów omc
```

## Uruchamianie

```bash
.venv/bin/python scripts/check_tests.py          # wszystkie modele z Tests/ i Examples/
.venv/bin/python scripts/check_tests.py Pipe     # tylko modele zawierające "Pipe" w nazwie
.venv/bin/python scripts/run_all.py              # wszystkie scenariusze z Examples/ -> results/examples/
.venv/bin/python scripts/sweep.py               # przegląd częstotliwości 0,25–4 Hz -> results/sweep/
.venv/bin/python scripts/sweep.py --A 0.5 --n 30   # inna amplituda komendy, gęstsza siatka
.venv/bin/python scripts/sweep.py --swim        # prędkość pływania vs częstotliwość -> results/sweep/swim_sweep.*
```

Każdy model jest sprawdzany (`checkModel`: liczba równań = liczba niewiadomych), kompilowany, symulowany i porównywany z wynikiem analitycznym. Modele są przetwarzane równolegle (osobny proces i osobna sesja omc na model). Wykresy trafiają do `results/tests/`.

Ustawienia wydajności są w `scripts/om_config.py`. W modelach zmienne hydrauliczne mają atrybuty `nominal` (ciśnienie 1e5 Pa, różnica ciśnień 1e4 Pa, przepływ i objętość 1e-5). Solver skaluje nimi tolerancje, a bez nich wielkości rzędu 1e-5 m³ traktowałby jak wielkości rzędu 1. W testach czysto hydraulicznych poprawiło to dokładność o kilka rzędów (np. inertancja: błąd z 1e-3 do 2e-8). Kompilacja kodu C idzie równolegle na wszystkich rdzeniach, a wygenerowany kod jest budowany z `-O2`, co daje ok. 8% szybszą symulację. `-O3`, `-march=native` i ccache nie dały mierzalnego zysku.

## Otwieranie w OMEdit

`File → Load Library…` (lub `Open Model/Library File`) → wskaż `FishRobot/package.mo`. W drzewie bibliotek rozwiń `FishRobot.Tests`, otwórz model i przełącz na widok *Diagram*. Złącza hydrauliczne są niebieskie: pełne kółko to `port_a`, puste to `port_b`.

`sweep.py` kompiluje model raz, a potem uruchamia gotowy plik wykonywalny równolegle dla każdej częstotliwości (`scripts/om_fast.py`). Parametry zmienia przez `-override`, a wyniki czyta bezpośrednio z plików `.mat` (`scripts/om_results.py`). 16 symulacji zajmuje ok. 0,2 s plus ok. 1 s kompilacji. W OpenModelica 1.27.1 `-override` nie zmienia ustawień eksperymentu (`stopTime`, `tolerance`), więc `om_fast` podmienia je w kopii pliku `_init.xml`.

## Ogon: sformułowanie

Ogon to tłok obrotowy o wydajności `D_tail = A_eff·r_eff` (`Tail.HydraulicBender`):

- ruch ogona wypiera ciecz: `Q_L = D_tail·θ̇`, `Q_R = −D_tail·θ̇`,
- różnica ciśnień daje moment: `τ = D_tail·(p_L − p_R)`.

Ta sama stała w obu równaniach sprawia, że moc hydrauliczna jest z definicji równa mechanicznej. Krzywa p–V komory opisuje tylko pęcznienie ścianek przy zablokowanym ogonie, więc woda przetłoczona przez pompę dzieli się na dwie części: pęcznienie komór i ruch ogona. Wariant „θ z różnicy objętości przez sztywność” odrzuciłem, bo pomija bezwładność ogona i nie daje momentu do przekazania np. do MuJoCo.

## Hydraulika: dlaczego własny pakiet

`Modelica.Fluid` jest potężne, ale ciężkie dla małego układu z nieściśliwą wodą: wymaga modelu medium, bilansu entalpii i starannej inicjalizacji. Własne złącze `HydraulicPort` ma tylko dwie zmienne:

- `p` – ciśnienie (potencjał, w węźle równe we wszystkich portach),
- `flow V_flow` – przepływ objętościowy (w węźle sumuje się do zera).

Ich iloczyn `p·V_flow` to moc w watach, więc bilans energii wynika wprost z połączeń, tak jak `v·i` w elektryce. To najprostszy sposób, żeby zobaczyć, jak działają złącza akauzalne.

**Konwencja kierunków:** komenda pompy `u > 0` ⇒ wał kręci się w kierunku dodatnim (`ω > 0`) ⇒ pompa tłoczy wodę z komory R do komory L ⇒ `p_L > p_R`. W etapie 4 ten sam znak da dodatni kąt ogona.

**Konwencja znaków przepływu:** `V_flow > 0` oznacza przepływ **do** komponentu przez dany port. W elementach dwuportowych `V_flow` (bez prefiksu portu) to przepływ od `port_a` do `port_b`, a `dp = port_a.p − port_b.p`.

## Co pokazują wykresy testów (etapy 1–3)

- **`pipe_laminar.png`** – spadek ciśnienia rośnie liniowo z przepływem, zgodnie z prawem Hagena–Poiseuille’a `Δp = 128·μ·l·Q / (π·d⁴)`. Liczba Reynoldsa pozostaje poniżej 2300, więc wzór laminarny obowiązuje. Zwróć uwagę na `d⁴`: dwa razy węższy przewód daje 16 razy większy opór.
- **`pipe_quadratic.png`** – przy przepływie sinusoidalnym krzywa Δp ma „spłaszczenia” przy zerze (dominuje część liniowa) i ostre szczyty (dominuje część kwadratowa). Dolny panel pokazuje błąd regularyzacji `Q·√(Q² + Q_small²)` zamiast `|Q|·Q`. Jest rzędu 10⁻⁴ Pa, a symulacja przechodzi przez zero bez żadnych zdarzeń.
- **`pipe_inertance.png`** – po skoku różnicy ciśnień przepływ nie zmienia się skokowo, bo słup wody ma masę. Narasta wykładniczo ze stałą czasową `τ = L/R ≈ 0,5 s`, dokładnie jak prąd w obwodzie RL.

- **`chamber_closed_loop.png`** – dwie komory połączone przewodem, na starcie 8 ml i 3 ml. Ciecz przelewa się do komory o niższym ciśnieniu, „przestrzeliwuje” przez bezwładność słupa wody i oscyluje z tłumieniem wokół 5,5 ml. To obwód RLC: komory to pojemność, słup cieczy to indukcyjność, opór rury to rezystancja. Dolny panel pokazuje, że suma objętości zmienia się tylko na poziomie 10⁻¹⁵ ml, czyli w granicach zaokrągleń komputera.
- **`relief_valve_limit.png`** – komora napełniana coraz szybciej. Nadciśnienie rośnie najpierw powoli (miękki silikon), potem stromo (silikon sztywnieje). Gdy przekroczy `p_set`, zawór przejmuje cały przepływ i ciśnienie zatrzymuje się na `p_set + dp_open`, czyli tam, gdzie zawór przepuszcza przepływ nominalny.

- **`dc_motor_no_load.png`** – rozruch silnika przez mostek H przy `u = 0,6`. Prędkość narasta wykładniczo ze stałą czasową mechaniczną `J·R/k²` do wartości analitycznej. Bilans mocy (ogniwo = straty + przyrost energii kinetycznej i magnetycznej) zamyka się w każdej chwili.
- **`gear_pump_characteristic.png`** – przepływ pompy przy stałej prędkości maleje liniowo z przyrostem ciśnienia. Nachylenie to przeciek `k_leak`. Przy ujemnym Δp ciecz sama pomaga pompie i pompa działa jak silnik hydrauliczny.

## Scenariusze (`results/examples/`)

- **`hydraulics_step.png`** (scenariusz 1) – komenda pompy rośnie do 0,5, ogon jest zablokowany:
  - Silnik się rozpędza, a prąd rozruchowy ma krótki szczyt: przy małej prędkości napięcie indukowane jest małe.
  - Pompa przetłacza wodę z komory R do L. Różnica ciśnień rośnie coraz szybciej, bo silikon sztywnieje.
  - Przy ok. 51 kPa otwiera się zawór przelewowy. Od tej chwili woda krąży w pętli pompa → zawór, komory stoją, a cała moc pompy idzie w ciepło.
  - Po zdjęciu komendy mostek zwiera silnik, a napięte komory wypychają wodę z powrotem, głównie przez przeciek pompy. Silnik działa wtedy jak hamulec prądnicowy, stąd ujemny prąd.
  - Przy placeholderowych parametrach silnik jest mocno przewymiarowany względem pompy. Prąd pod obciążeniem to tylko ok. 0,14 A, więc parametry trzeba zidentyfikować, zanim wyciągnie się wnioski o doborze napędu.

- **`tail_flapping.png`** (scenariusz 2) – sinus 1 Hz, ogon swobodny:
  - Kąt ogona jest opóźniony względem komendy, bo pompa najpierw musi przetłoczyć ciecz.
  - Ciśnienia w komorach zmieniają się w przeciwfazie.
  - Prąd baterii ma podwójną częstotliwość i chwilami jest ujemny. W każdej połówce okresu silnik najpierw rozpędza się, a potem hamuje, oddając energię do baterii.
  - Amplituda rośnie przez 2 okresy, bo CPG zaczyna od łagodnej rampy.
- **`relief_valve_demo.png`** (scenariusz 4) – pełna komenda przy 0,25 Hz. Różnica ciśnień dochodzi do ±`p_set`, zawory się otwierają, a szczyty kąta ogona się spłaszczają (ok. ±31°). Dolny panel pokazuje, że ponad połowa energii hydraulicznej oddanej przez pompę idzie w ciepło w zaworach.

- **`depth_control.png`** (scenariusz 6) – skoki zadanej głębokości −0,5 → −1,5 → −1,0 m:
  - Żeby zejść głębiej, regulator najpierw zmniejsza pęcherz (ryba robi się cięższa), a przed celem zwiększa go z powrotem, żeby wyhamować. Ryba opada ze stałą prędkością ok. 3 cm/s, bo filtr zadanej zamienia skok na rampę.
  - Przeregulowanie ok. 6%, błąd ustalony na −1,0 m ok. 5 mm. Tłok pracuje w zakresie 15–23 mm z 40 mm skoku, więc nie dochodzi do ograniczników.
  - Sprzężenie w przód jest celowo niedokładne (5,5 ml zamiast 6 ml). Różnicę usuwa człon całkujący, ale wolno (`Ti = 120 s`): na −1,5 m ryba przez ok. 50 s wisi 2–4 cm za nisko.
  - Prąd silnika strzykawki płynie tylko podczas ruchu tłoka (szczyty ok. 0,2 A). Utrzymanie głębokości przy sztywnym kadłubie nic nie kosztuje.

- **`swim_forward.png`** (scenariusz 7) – CPG 1 Hz, amplituda komendy 0,8, 120 s:
  - Ciąg pulsuje z podwójną częstotliwością, bo płetwa pcha w obu kierunkach machnięcia. Chwilami spada do zera, gdy ogon zawraca.
  - Prędkość rośnie powoli i ustala się na ok. 6,4 cm/s, gdy średni ciąg (ok. 3 mN) zrówna się z oporem kadłuba. Stała czasowa to ok. 20 s, bo przy małym ciągu opór długo nie dorównuje mu.
  - Z 207 J pobranych z baterii płetwa dostaje tylko ok. 40 mJ, a pracę użyteczną (przeciw oporowi kadłuba) daje ok. 20 mJ, czyli 0,01%. Reszta to straty napędu ogona, opisane w scenariuszu 5.

## Pływanie do przodu (scenariusz 7)

**Uwaga: model ciągu to najsłabsze ogniwo całego modelu.** `Propulsion.LighthillFin` ma postać z teorii wydłużonego ciała Lighthilla dla sztywnej płetwy obracanej o kąt θ:

- prędkość wody względem płetwy: `w = L·θ̇ + U·θ`,
- ciąg: `T = ½·m_a·((L·θ̇)² − U²·θ²)`, gdzie masa dodana na metr to `m_a = C_T·ρ·π·s²/4`,
- moment hamujący ogon: `τ = m_a·U·L·w`.

Parametry `s_fin` i `C_T` są placeholderami. Trzeba je wyznaczyć z pomiaru ciągu na uwięzi albo z demo CFD/MuJoCo. Liczby prędkości pokazują trendy, a nie wartości do projektowania.

**Spójność energetyczna.** Płetwa nie dodaje ciągu „z powietrza”. Pobiera z ogona moc `P_fin = τ·θ̇` przez złącze mechaniczne `TailDrive.flange_tail`, a w każdej chwili zachodzi `P_fin = T·U + P_wake`, gdzie `P_wake = ½·m_a·U·w² ≥ 0` to energia zostawiona w śladzie wirowym. Bilans całego robota (bateria → straty napędu → ślad → opór kadłuba → energia kinetyczna) zamyka się z błędem ok. 1e-6. Dla sinusa sprawność płetwy wynosi `½·(1 − (U/Lω)²)`, czyli najwyżej 50%. Przy U ≪ L·ω jest ona bliska 50%.

**`swim_sweep.png`** (`sweep.py --swim`, `A = 1`, 0,25–4 Hz, 150 s na punkt):

| f [Hz] | U [cm/s] | θ [°] | θ·f [°·Hz] | P_bat [W] |
|---|---|---|---|---|
| 0,25 | 7,8 | 31,4 | 7,9 | 1,0 |
| 0,5 | 8,6 | 17,2 | 8,6 | 1,1 |
| 1 | 8,1 | 7,8 | 7,8 | 2,8 |
| 2 | 7,3 | 3,5 | 6,9 | 7,9 |
| 4 | 6,7 | 1,6 | 6,2 | 16,6 |

**Lekcja: szybsze machanie nie przyspiesza ryby, gdy ogranicza pompa.** Średni ciąg rośnie z kwadratem prędkości krawędzi spływu, czyli z (θ·f)². Powyżej ok. 0,5 Hz pompa przetłacza w półokresie stałą objętość, więc θ·f jest prawie stałe (patrz scenariusz 3). Ciąg i prędkość stoją w miejscu, a nawet lekko maleją, a moc z baterii rośnie 16 razy, bo silnik coraz częściej zawraca wirnik. Poniżej 0,5 Hz ogranicza zawór przelewowy: amplituda przestaje rosnąć, więc θ·f i prędkość spadają. Przy placeholderowych parametrach optimum to ok. 0,5 Hz. Żeby płynąć szybciej, trzeba zwiększyć przepływ pompy albo `D_tail`, a nie częstotliwość.

## Balast i pion (scenariusz 6)

Strzykawka (`Buoyancy.BallastSyringe`) to mostek H, silnik DC, przekładnia, śruba pociągowa i tłok z ogranicznikami sprężysto-tłumiącymi. Ciśnienie hydrostatyczne wpycha tłok. `Buoyancy.VerticalDynamics` traktuje rybę jak punkt materialny z masą dodaną i oporem kwadratowym: każdy mililitr ponad objętość neutralną daje ok. 0,01 N siły w górę.

**Lekcja: sztywny kadłub ma równowagę obojętną, kadłub z powietrzem – niestabilną** (test `BallastStatics`). Przy sztywnym kadłubie wypór nie zależy od głębokości, więc ryba zostaje tam, gdzie ją postawiono. Kieszeń powietrza ściska się z głębokością: ryba neutralna na −3 m, przesunięta o 1 cm w dół, robi się cięższa i po 60 s jest 40 cm niżej. Stąd potrzeba aktywnej regulacji.

**Regulator kaskadowy (`Control.DepthPID`).** Od komendy silnika do głębokości są trzy całkowania, więc jeden PID jest trudny do nastrojenia. Pętla wewnętrzna (P) ustawia objętość pęcherza, a zewnętrzna (`LimPID` z anti-windupem) zamienia błąd głębokości na zadaną objętość. Szczegóły nastaw i pułapka inicjalizacji `LimPID` są w dokumentacji modelu.

`DCMotor` ma parametr `initRotor`. W strzykawce wał jest sztywno połączony z tłokiem przez przekładnię, więc warunki początkowe ma tylko tłok. Inaczej układ byłby nadokreślony.

## Bilans energii (scenariusz 5)

Podukład `TailDrive` całkuje osobno każdą stratę (`E_loss_*`) i liczy energię zmagazynowaną (`E_stored`): wirnik, indukcyjność, ścianki komór, ogon. Zmienna `E_balance_error = E_battery − E_loss_total − ΔE_stored` musi być bliska zeru. `check_tests.py` sprawdza to automatycznie w każdym modelu z podukładem `drive`; błąd wynosi ok. 2e-6 energii z baterii. To test całego modelu: zły znak, brakujący człon albo niespójne równania w dowolnym komponencie rozjechałyby bilans.

Mostek H jest bezstratny. Moc ciśnienia otoczenia znosi się w obiegu zamkniętym, bo objętość krąży, a nie znika. Energię oddaną przez oś ogona na zewnątrz (np. płetwie w scenariuszu 7) liczy osobny człon `E_mech_out`; bez podłączenia jest zerowa.

**`energy_budget.png`** – 60 s machania przy 1 Hz i amplitudzie komendy 0,8. Szacowany czas pracy samego napędu ogona to ok. 9,6 h przy 1,7 W i placeholderowej baterii 16,3 Wh.

| Pozycja | Udział |
|---|---|
| silnik: uzwojenie R·i² | 82,6% |
| silnik: łożyska | 8,9% |
| przewody | 5,5% |
| pompa: tarcie | 1,9% |
| bateria | 0,8% |
| ogon (woda i materiał) | 0,1% |

**Lekcja: przy odwracalnej pompie energię zjada zawracanie wirnika, a nie woda.** Przy ok. 600 rad/s wirnik ma ok. 0,9 J energii kinetycznej. Dwa razy na okres silnik musi ją wytracić i odbudować, a prąd hamowania i rozpędzania grzeje uzwojenie. Sprawdzenie: przy 10 razy mniejszej bezwładności wirnika energia z baterii spada 5 razy, a udział uzwojenia z 82% do 4%, przy tej samej amplitudzie ogona. Wnioski projektowe do zweryfikowania na prawdziwych parametrach:

- silnik o małej bezwładności (np. bezrdzeniowy),
- przekładnia i wolniejszy silnik, bo energia kinetyczna rośnie z ω²,
- pompa jednokierunkowa z zaworem rozdzielającym zamiast zawracania pompy.

## Przegląd częstotliwości (`results/sweep/`, scenariusz 3)

`frequency_sweep.png` i `frequency_sweep.csv` pokazują pełną komendę (`A = 1`) przy częstotliwościach 0,25–4 Hz. Zakres zaczyna się od 0,25 Hz, a nie od 0,5 Hz jak w specyfikacji, żeby przy placeholderowych parametrach było widać obszar ograniczony przez zawór.

**Lekcja: dwa różne ograniczenia pasma.**

- **Niskie częstotliwości (≤ ok. 0,4 Hz): ogranicza zawór.** Pompa ma dość czasu, żeby wytworzyć `p_set`. Zawór się otwiera (ponad 20% przepływu pompy idzie przez zawory), a amplituda ogona jest ograniczona ciśnieniem: `θ ≈ D_tail·p_set / k_całk`.
- **Wyższe częstotliwości: ogranicza przepływ pompy.** W półokresie pompa przetłacza najwyżej `Q_max/(2f)`, więc amplituda spada jak `1/f` (iloczyn θ·f jest prawie stały). Zawory pozostają zamknięte.
- **Prąd rośnie z częstotliwością, choć amplituda maleje.** Silnik musi coraz częściej zawracać wirnik, a energia kinetyczna wirnika przy każdym zawróceniu w dużej części idzie w ciepło w uzwojeniu (`R·i²`). Szybkie machanie małą pompą jest więc nieefektywne. Lepsza byłaby większa pompa albo przekładnia.

**Rampa CPG a pompa jako integrator.** Pompa całkuje przepływ do objętości. Sinus włączony od zera dałby więc przesunięcie objętości `(1 − cos ωt)/ω`, a ogon machałby wokół wychylonego położenia przez wiele okresów, bo przesunięcie wycieka tylko przez przeciek pompy. Dlatego CPG narasta łagodnie przez 2 okresy (`n_ramp`).

## Krzywa p–V komory z pliku

Placeholderową krzywą p–V można zastąpić danymi z demo SOFA albo z pomiaru bez zmiany kodu. Ustaw w `Chamber` parametr `tableOnFile = true`, a `fileName` wskaż przez `Modelica.Utilities.Files.loadResource("modelica://FishRobot/Resources/Data/<plik>.csv")`. Plik ma mieć jedną linię nagłówka i kolumny `V [m³], p − p_ambient [Pa]`, a krzywa musi być rosnąca. Wzór: `FishRobot/Resources/Data/chamber_pV_placeholder.csv` i test `ChamberTableFromFile`.

## Ograniczenia

Model jest jednowymiarowy, o skupionych parametrach. Parametry nie są zidentyfikowane. Ciąg pochodzi z placeholderowego modelu płetwy (wyżej). Ruchy do przodu, w pionie i obrót są niezależne: machanie nie odchyla kadłuba, a balast nie wpływa na pływanie. Pełna lista ograniczeń i plan kalibracji pojawią się wraz z kolejnymi etapami.
