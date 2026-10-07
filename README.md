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
| 8 | `TailDriveFMU` → FMU 2.0 CS (`export_fmu.py`), pętla FMPy i porównanie z OpenModelica (`fmu_demo.py`) | gotowe |
| 9 | (opcja) `HydraulicsFluid` na złączach `Modelica.Fluid` → `HydraulicsMSLFluid`, porównanie (`compare_fluid.py`) | gotowe |

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
.venv/bin/python scripts/export_fmu.py          # FMU napędu ogona -> results/fmu/TailDrive.fmu
.venv/bin/python scripts/fmu_demo.py            # FMU w pętli FMPy vs OpenModelica -> results/fmu/fmu_vs_om.png
.venv/bin/python scripts/compare_fluid.py       # własna hydraulika vs Modelica.Fluid -> results/fluid/fluid_vs_own.png
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

Ten sam obwód zbudowany na `Modelica.Fluid` i porównanie obu wersji opisuje sekcja [Modelica.Fluid zamiast własnego pakietu](#modelicafluid-zamiast-własnego-pakietu-etap-9).

**Konwencja kierunków:** komenda pompy `u > 0` ⇒ wał kręci się w kierunku dodatnim (`ω > 0`) ⇒ pompa tłoczy wodę z komory R do komory L ⇒ `p_L > p_R`. W etapie 4 ten sam znak da dodatni kąt ogona.

**Konwencja znaków przepływu:** `V_flow > 0` oznacza przepływ **do** komponentu przez dany port. W elementach dwuportowych `V_flow` (bez prefiksu portu) to przepływ od `port_a` do `port_b`, a `dp = port_a.p − port_b.p`.

## Co pokazują wykresy testów (etapy 1–3)

- **`pipe_laminar.png`** – spadek ciśnienia rośnie liniowo z przepływem, zgodnie z prawem Hagena–Poiseuille’a `Δp = 128·μ·l·Q / (π·d⁴)`. Liczba Reynoldsa pozostaje poniżej 2300, więc wzór laminarny obowiązuje. Zwróć uwagę na `d⁴`: dwa razy węższy przewód daje 16 razy większy opór.
- **`pipe_quadratic.png`** – przy przepływie sinusoidalnym krzywa Δp ma „spłaszczenia” przy zerze (dominuje część liniowa) i ostre szczyty (dominuje część kwadratowa). Dolny panel pokazuje błąd regularyzacji `Q·√(Q² + Q_small²)` zamiast `|Q|·Q`. Jest rzędu 10⁻⁴ Pa, a symulacja przechodzi przez zero bez żadnych zdarzeń.
- **`pipe_turbulent_vs_msl.png`** – przepływ rośnie od zera do Re ≈ 12 700, a ten sam przepływ płynie przez `Hydraulics.Pipe` i przez `Modelica.Fluid.Pipes.StaticPipe` (`DetailedPipeFlow`). Do Re ≈ 1500 obie krzywe to prosta Hagena–Poiseuille’a (różnica 0,00%). Powyżej Re ≈ 4000 opór rośnie prawie z kwadratem przepływu, a wzór Haalanda różni się od Colebrooka w MSL o mniej niż 0,5%. W zakresie przejściowym modele interpolują inaczej (MSL zaczyna przejście wcześniej) i różnią się do ok. 6%.
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
  - Przy placeholderowych parametrach silnik jest mocno przewymiarowany względem pompy. Prąd pod obciążeniem to tylko ok. 0,35 A, więc parametry trzeba zidentyfikować, zanim wyciągnie się wnioski o doborze napędu.

- **`hydraulics_msl_fluid.png`** (scenariusz 8, opcjonalny) – ten sam przebieg co `hydraulics_step.png`, policzony na komponentach `Modelica.Fluid`. Na oko wykresy są identyczne. Różnice pokazuje `results/fluid/fluid_vs_own.png` (sekcja niżej).

- **`tail_flapping.png`** (scenariusz 2) – sinus 1 Hz, ogon swobodny:
  - Kąt ogona jest opóźniony względem komendy, bo pompa najpierw musi przetłoczyć ciecz.
  - Ciśnienia w komorach zmieniają się w przeciwfazie.
  - Prąd baterii ma podwójną częstotliwość i chwilami jest ujemny. W każdej połówce okresu silnik najpierw rozpędza się, a potem hamuje, oddając energię do baterii.
  - Amplituda rośnie przez 2 okresy, bo CPG zaczyna od łagodnej rampy.
- **`relief_valve_demo.png`** (scenariusz 4) – pełna komenda przy 0,25 Hz. Różnica ciśnień dochodzi do ±`p_set`, zawory się otwierają, a szczyty kąta ogona się spłaszczają (ok. ±31°). Dolny panel pokazuje, że ok. 43% energii hydraulicznej oddanej przez pompę idzie w ciepło w zaworach. Reszta to głównie tarcie w przewodach, bo przy pełnej komendzie przepływ jest turbulentny.

- **`depth_control.png`** (scenariusz 6) – skoki zadanej głębokości −0,5 → −1,5 → −1,0 m:
  - Żeby zejść głębiej, regulator najpierw zmniejsza pęcherz (ryba robi się cięższa), a przed celem zwiększa go z powrotem, żeby wyhamować. Ryba opada ze stałą prędkością ok. 3 cm/s, bo filtr zadanej zamienia skok na rampę.
  - Przeregulowanie ok. 6%, błąd ustalony na −1,0 m ok. 5 mm. Tłok pracuje w zakresie 15–23 mm z 40 mm skoku, więc nie dochodzi do ograniczników.
  - Sprzężenie w przód jest celowo niedokładne (5,5 ml zamiast 6 ml). Różnicę usuwa człon całkujący, ale wolno (`Ti = 120 s`): na −1,5 m ryba przez ok. 50 s wisi 2–4 cm za nisko.
  - Prąd silnika strzykawki płynie tylko podczas ruchu tłoka (szczyty ok. 0,2 A). Utrzymanie głębokości przy sztywnym kadłubie nic nie kosztuje.

- **`swim_forward.png`** (scenariusz 7) – CPG 1 Hz, amplituda komendy 0,8, 120 s:
  - Ciąg pulsuje z podwójną częstotliwością, bo płetwa pcha w obu kierunkach machnięcia. Chwilami spada do zera, gdy ogon zawraca.
  - Prędkość rośnie powoli i ustala się na ok. 6,4 cm/s, gdy średni ciąg (ok. 3 mN) zrówna się z oporem kadłuba. Stała czasowa to ok. 20 s, bo przy małym ciągu opór długo nie dorównuje mu.
  - Z 216 J pobranych z baterii płetwa dostaje tylko ok. 40 mJ, a pracę użyteczną (przeciw oporowi kadłuba) daje ok. 20 mJ, czyli 0,01%. Reszta to straty napędu ogona, opisane w scenariuszu 5.

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
| 0,25 | 7,6 | 31,1 | 7,8 | 1,1 |
| 0,5 | 8,5 | 16,9 | 8,5 | 1,25 |
| 1 | 8,0 | 7,7 | 7,7 | 2,9 |
| 2 | 7,3 | 3,4 | 6,9 | 7,9 |
| 4 | 6,6 | 1,6 | 6,2 | 16,6 |

**Lekcja: szybsze machanie nie przyspiesza ryby, gdy ogranicza pompa.** Średni ciąg rośnie z kwadratem prędkości krawędzi spływu, czyli z (θ·f)². Powyżej ok. 0,5 Hz pompa przetłacza w półokresie stałą objętość, więc θ·f jest prawie stałe (patrz scenariusz 3). Ciąg i prędkość stoją w miejscu, a nawet lekko maleją, a moc z baterii rośnie 15 razy, bo silnik coraz częściej zawraca wirnik. Poniżej 0,5 Hz ogranicza zawór przelewowy: amplituda przestaje rosnąć, więc θ·f i prędkość spadają. Przy placeholderowych parametrach optimum to ok. 0,5 Hz. Żeby płynąć szybciej, trzeba zwiększyć przepływ pompy albo `D_tail`, a nie częstotliwość.

## Balast i pion (scenariusz 6)

Strzykawka (`Buoyancy.BallastSyringe`) to mostek H, silnik DC, przekładnia, śruba pociągowa i tłok z ogranicznikami sprężysto-tłumiącymi. Ciśnienie hydrostatyczne wpycha tłok. `Buoyancy.VerticalDynamics` traktuje rybę jak punkt materialny z masą dodaną i oporem kwadratowym: każdy mililitr ponad objętość neutralną daje ok. 0,01 N siły w górę.

**Lekcja: sztywny kadłub ma równowagę obojętną, kadłub z powietrzem – niestabilną** (test `BallastStatics`). Przy sztywnym kadłubie wypór nie zależy od głębokości, więc ryba zostaje tam, gdzie ją postawiono. Kieszeń powietrza ściska się z głębokością: ryba neutralna na −3 m, przesunięta o 1 cm w dół, robi się cięższa i po 60 s jest 40 cm niżej. Stąd potrzeba aktywnej regulacji.

**Regulator kaskadowy (`Control.DepthPID`).** Od komendy silnika do głębokości są trzy całkowania, więc jeden PID jest trudny do nastrojenia. Pętla wewnętrzna (P) ustawia objętość pęcherza, a zewnętrzna (`LimPID` z anti-windupem) zamienia błąd głębokości na zadaną objętość. Szczegóły nastaw i pułapka inicjalizacji `LimPID` są w dokumentacji modelu.

`DCMotor` ma parametr `initRotor`. W strzykawce wał jest sztywno połączony z tłokiem przez przekładnię, więc warunki początkowe ma tylko tłok. Inaczej układ byłby nadokreślony.

## Bilans energii (scenariusz 5)

Podukład `TailDrive` całkuje osobno każdą stratę (`E_loss_*`) i liczy energię zmagazynowaną (`E_stored`): wirnik, indukcyjność, ścianki komór, ogon. Zmienna `E_balance_error = E_battery − E_loss_total − ΔE_stored` musi być bliska zeru. `check_tests.py` sprawdza to automatycznie w każdym modelu z podukładem `drive`; błąd jest rzędu 1e-6 energii z baterii. To test całego modelu: zły znak, brakujący człon albo niespójne równania w dowolnym komponencie rozjechałyby bilans.

Mostek H jest bezstratny. Moc ciśnienia otoczenia znosi się w obiegu zamkniętym, bo objętość krąży, a nie znika. Energię oddaną przez oś ogona na zewnątrz (np. płetwie w scenariuszu 7) liczy osobny człon `E_mech_out`; bez podłączenia jest zerowa.

**`energy_budget.png`** – 60 s machania przy 1 Hz i amplitudzie komendy 0,8. Szacowany czas pracy samego napędu ogona to ok. 9,2 h przy 1,8 W i placeholderowej baterii 16,3 Wh.

| Pozycja | Udział |
|---|---|
| silnik: uzwojenie R·i² | 78,5% |
| przewody | 9,3% |
| silnik: łożyska | 8,4% |
| pompa: tarcie | 2,7% |
| bateria | 0,8% |
| ogon (woda i materiał) | 0,1% |

**Lekcja: przy odwracalnej pompie energię zjada zawracanie wirnika, a nie woda.** Przy ok. 550 rad/s wirnik ma ok. 0,8 J energii kinetycznej. Dwa razy na okres silnik musi ją wytracić i odbudować, a prąd hamowania i rozpędzania grzeje uzwojenie. Sprawdzenie: przy 10 razy mniejszej bezwładności wirnika energia z baterii spada ponad 4 razy, a udział uzwojenia z 79% do 4%, przy tej samej amplitudzie ogona. Wnioski projektowe do zweryfikowania na prawdziwych parametrach:

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

## FMU (etap 8)

`export_fmu.py` eksportuje `Subsystems.TailDriveFMU` jako **FMU 2.0 Co-Simulation**: bateria, mostek H, silnik, pompa, przewody, komory, zawory i ogon. Wejście to komenda `u`, a wyjścia to `theta`, `w_tail`, `tau_tail`, `p_L`, `p_R` i `i_motor`. `TailDriveFMU` to cienkie opakowanie `TailDrive`. Złącza mechanicznego `flange_tail` (kąt i moment jako zmienna przepływowa) nie da się wystawić jako zwykłego wejścia lub wyjścia FMU, więc zostaje w środku niepodłączone.

**Solver w FMU: CVODE** (`--fmiFlags=s:cvode`). Domyślnie OpenModelica wkłada do FMU CS jawną metodę Eulera z krokiem równym krokowi komunikacji. Przy sztywnej hydraulice i kroku 2 ms taki FMU pada po ok. 0,1 s. CVODE dobiera kroki wewnątrz każdego kroku komunikacji, a biblioteki sundials są spakowane do FMU (1,8 MB).

`fmu_demo.py` uruchamia FMU w pętli Pythona przez FMPy (`FMU2Slave`) z krokiem 2 ms. Komendę CPG liczy Python tym samym wzorem co `Control.CPG`. Wynik porównuje ze scenariuszem `TailFlapping` policzonym w OpenModelica (`fmu_vs_om.png`):

- komenda próbkowana **w środku kroku** `u(t + h/2)`: max różnica kąta 0,016% amplitudy,
- komenda próbkowana **na początku kroku** `u(t)`: 0,62% amplitudy.

**Lekcja: w co-simulation wejście jest stałe w kroku komunikacji** (ZOH). Próbkowane na początku kroku spóźnia się średnio o h/2 = 1 ms, a przy 1 Hz daje to błąd fazy rzędu 2π·f·h/2 ≈ 0,6%. Próbkowanie w środku kroku usuwa to opóźnienie. Przy sprzężeniu dwóch symulatorów takiego triku nie ma, bo wejście pochodzi z drugiego symulatora. Wtedy krok trzeba dobrać do najszybszej dynamiki sprzężenia.

**FMU działa tylko na systemie, na którym go zbudowano.** Zawiera skompilowane binaria (`binaries/linux64`, glibc i sundials z tej maszyny). Na innym systemie trzeba go zbudować od nowa (`export_fmu.py`).

**Jak w przyszłości podpiąć FMU pod demo MuJoCo** (niezaimplementowane):

1. W `TailDriveFMU` dodać wejście momentu obciążenia ogona: `Rotational.Sources.Torque` na `drive.flange_tail`. Wtedy FMU dostaje od MuJoCo reakcję wody i bezwładność reszty ryby, a nie tylko rusza ogonem w próżni.
2. W pętli MuJoCo w każdym kroku: `fmu.setReal(u, tau_load)` → `fmu.doStep(t, h)` → odczyt `tau_tail` → `data.ctrl[przegub_ogona] = tau_tail` (aktuator momentowy na przegubie ogona) → `mujoco.mj_step`. Moment obciążenia na kolejny krok to moment, jakim woda i reszta ciała działają na przegub ogona w MuJoCo (konkretne pola `mjData` zależą od tego, jak demo modeluje płyn).
3. Krok komunikacji równy krokowi MuJoCo (np. 2 ms) albo jego wielokrotność. Sprzężenie jest jawne (wartości z poprzedniego kroku), więc przy sztywnym ogonie krok musi być mały w porównaniu z okresem drgań własnych ogona (poniżej 0,17 s: 5,8 Hz bez hydrauliki, a sztywność komór jeszcze tę częstotliwość podnosi).
4. Hydraulika w FMU, a ruch ciała w MuJoCo. Wtedy `J_added`, `c_h` i `LighthillFin` nie powinny być liczone podwójnie, bo te efekty da wtedy model płynu w MuJoCo.

## Modelica.Fluid zamiast własnego pakietu (etap 9)

`Examples.HydraulicsMSLFluid` to obwód z `HydraulicsStep` (bateria, mostek H, silnik, pompa, przewody, komory, zawory) z hydrauliką na złączach `Modelica.Fluid` i medium `Modelica.Media.Water.ConstantPropertyLiquidWater`. Komponenty są w `FishRobot.HydraulicsFluid`. `compare_fluid.py` liczy oba modele i porównuje je (`results/fluid/fluid_vs_own.png`).

**Co wzięto z biblioteki, a co trzeba było dopisać:**

| Element | Własny pakiet | Wersja Modelica.Fluid |
|---|---|---|
| Przewód | `Hydraulics.Pipe` | z biblioteki: `Pipes.StaticPipe` (`DetailedPipeFlow`) + `Fittings.SimpleGenericOrifice` |
| Zawór przelewowy | `Hydraulics.ReliefValve` | złożony z biblioteki: `Valves.ValveLinear` + `Sensors.RelativePressure` jako linia sterująca |
| Pompa zębata | `Hydraulics.GearPump` | **dopisana** na `Interfaces.PartialTwoPortTransport`. MSL ma tylko pompy wirowe |
| Komora podatna | `Hydraulics.Chamber` | **dopisana** na `Vessels.BaseClasses.PartialLumpedVessel`. Naczynia MSL mają stałą objętość albo swobodne lustro cieczy |

**Złożoność** (wynik `compare_fluid.py`, 24 rdzenie):

| | własny pakiet | Modelica.Fluid |
|---|---|---|
| równania po spłaszczeniu (w tym trywialne) | 185 (109) | 425 (222) |
| stany ciągłe | 8 | 8 |
| kompilacja | ok. 1,1 s | ok. 1,4 s |
| symulacja 3 s | ok. 0,02 s | ok. 0,15 s (ok. 6× dłużej) |

Liczba stanów jest równa przypadkiem. Wersja Fluid ma dodatkowo temperaturę wody w każdej komorze, a nie ma całek energii sprężystej `E_elastic`, które dodaliśmy we własnej komorze do bilansu energii. Temperatura zmienia się o mniej niż 0,01 K, więc przy wodzie o stałych właściwościach niczego nie wnosi, ale solver i tak musi ją liczyć.

**Wyniki:** ciśnienia, przepływ pompy i prąd silnika różnią się o 0,03–0,5% maksimum przebiegu, przepływ przez zawory o 0,9%. Przy szybkim pompowaniu przepływ dochodzi do 16 ml/s, a liczba Reynoldsa w przewodzie 4 mm do ok. 5200, więc przepływ jest turbulentny. Spadek ciśnienia na przewodzie: 3,08 kPa we własnym pakiecie, 3,07 kPa we Fluid. Zawory różnią się charakterystyką o kilka procent (opis w `HydraulicsFluid.ReliefValve`), ale w tym obwodzie prawie tego nie widać.

Pierwsza wersja `Hydraulics.Pipe` liczyła tarcie tylko ze wzoru laminarnego. Dawała wtedy 1,8 kPa zamiast 3,1 kPa, ciśnienia różniły się od Fluid o 0,7–3,8%, a przesunięte zbocze otwarcia zaworów dawało chwilowo do 11% różnicy przepływu. Teraz przewód ma tarcie turbulentne (wzór Haalanda, chropowatość ścianki) i gładkie przejście między Re = 2000 a 4000. Osobno sprawdza to test `PipeTurbulentVsMSL`.

**Lekcje:**

- **Biblioteka pokazała słabość naszego modelu.** Wzór Hagena–Poiseuille’a obowiązuje do Re ≈ 2300, a w scenariuszu 1 przepływ jest już turbulentny. Pierwsza wersja przewodu zaniżała tam opór o ok. 40%. Porównanie z niezależną implementacją wskazało błąd, którego testy własnego pakietu nie mogły złapać, bo sprawdzały model z jego własnymi założeniami. Testy, które zakładają opór liniowy (`PipeQuadratic`, `PipeInertance`), mają teraz jawnie `useTurbulent = false`.
- **Progi regularyzacji trzeba sprawdzać per komponent.** Domyślne `system.m_flow_small = 0,01 kg/s` jest dobrane do instalacji przemysłowych, a u nas to cały przepływ pompy. W modelu jest zmniejszone do 1e-5 kg/s, ale sprawdziłem, że w tym obwodzie nie ma to wpływu: `SimpleGenericOrifice` wygładza charakterystykę w okolicy zera według `system.dp_small = 1 Pa`, a `DetailedPipeFlow` według liczby Reynoldsa. `m_flow_small` działa w innych komponentach (np. `Fittings` z `from_dp = false`) i w diagnostyce. Przy małych przepływach trzeba więc zajrzeć do kodu komponentu, który próg go dotyczy.
- **Złącze Fluid przenosi więcej:** masowe natężenie przepływu i zmienne strumieniowe (entalpia, skład, `inStream()`). Każdy dopisany komponent musi określić, co wypływa z każdego portu. Do każdego portu naczynia można też podłączyć tylko jeden element (`nPorts`).
- **Ostrzeżenia o aliasach** przy kompilacji (`The model contains alias variables with redundant start and/or conflicting nominal values`) pochodzą z wartości startowych wewnątrz MSL (np. `medium.T` i `state.T`). Są nieszkodliwe.
- **Kiedy brać `Modelica.Fluid`:** gdy liczy się temperatura (nagrzewanie oleju, wymiana ciepła), ściśliwość albo przepływ dwufazowy, albo gdy model ma się łączyć z innymi bibliotekami opartymi na `Modelica.Media`. W tym projekcie (nieściśliwa woda, kilka komponentów, bilans energii jako test) lekki pakiet jest prostszy i ok. 6× szybszy.

## Krzywa p–V komory z pliku

Placeholderową krzywą p–V można zastąpić danymi z demo SOFA albo z pomiaru bez zmiany kodu. Ustaw w `Chamber` parametr `tableOnFile = true`, a `fileName` wskaż przez `Modelica.Utilities.Files.loadResource("modelica://FishRobot/Resources/Data/<plik>.csv")`. Plik ma mieć jedną linię nagłówka i kolumny `V [m³], p − p_ambient [Pa]`, a krzywa musi być rosnąca. Wzór: `FishRobot/Resources/Data/chamber_pV_placeholder.csv` i test `ChamberTableFromFile`.

## Ograniczenia

Model odpowiada na pytania typu „czy pompa i bateria wystarczą” i „gdzie ucieka energia”, a nie „jak dokładnie płynie woda”. Główne uproszczenia:

- **Ogon jako 1 DOF.** `Tail.TailEquivalent` to sztywna belka obracana o kąt θ ze sprężyną, tłumieniem i masą dodaną. Prawdziwy ogon z silikonu wygina się wzdłuż długości (kształt fali), czego ten model nie odda.
- **Ciąg z placeholderu.** `Propulsion.LighthillFin` to reaktywna teoria Lighthilla dla sztywnej płetwy z empirycznym współczynnikiem `C_T`. Nie ma w niej oderwania przepływu, śladu wirowego o skończonej długości ani wpływu kształtu płetwy. Liczby prędkości pokazują trendy, a nie wartości do projektowania.
- **Brak sprzężenia ruchów.** Ruch do przodu (`SurgeDynamics`), pion (`VerticalDynamics`) i obrót są niezależne. Machanie ogonem nie odchyla kadłuba (brak yaw i recoil), balast nie zmienia oporu ani trymu, a prędkość pływania nie daje siły nośnej.
- **Brak hydrodynamiki przestrzennej.** Opór kadłuba to `½·ρ·C_d·A·U²` ze stałym `C_d`, a masa dodana jest stała. Nie ma przepływu wokół ciała, fal, ściany basenu ani prądów.
- **Hydraulika o skupionych parametrach.** Woda jest nieściśliwa i ma stałą temperaturę. Komory mają statyczną krzywą p–V bez histerezy i lepkosprężystości silikonu. Przewód ma tarcie laminarne i turbulentne, ale przejście między nimi (Re 2000–4000) jest tylko interpolacją, a przepływ niestacjonarny (oscylujący) liczony jest charakterystyką ustaloną. Zawory nie mają dynamiki grzybka.
- **Elektryka uproszczona.** Bateria to źródło napięcia z rezystancją wewnętrzną, bez spadku napięcia w miarę rozładowania. Mostek H jest idealny (uśredniony PWM, bez strat przełączania). Silnik nie ma nasycenia magnetycznego ani temperatury uzwojenia.
- **Parametry niezidentyfikowane.** Wszystkie wartości oznaczone `PLACEHOLDER` w kodzie są szacunkami rzędu wielkości. Przy obecnych parametrach silnik jest np. mocno przewymiarowany względem pompy (scenariusz 1).

## Plan kalibracji

Parametry najlepiej identyfikować od źródła energii w stronę wody. Każdy krok korzysta z elementów zidentyfikowanych wcześniej, np. silnik z kroku 1 służy potem jako czujnik momentu (moment = `k·i`).

| Krok | Element | Pomiar na stole | Parametry |
|---|---|---|---|
| 1 | Bateria | napięcie jałowe i pod znanym obciążeniem, w kilku stanach naładowania | `U_nom`, `R_int`, `capacity_Wh` |
| 2 | Silnik DC | rezystancja uzwojenia (miernik, zablokowany wał); prędkość biegu jałowego przy kilku napięciach; wybieg po odłączeniu zasilania; odpowiedź prądu na skok napięcia przy zablokowanym wale | `R`, `k`, `b`, `J`, `L` |
| 3 | Pompa | przepływ (cylinder miarowy lub przepływomierz) przy kilku prędkościach i ciśnieniach (zawór dławiący na wyjściu); prąd silnika daje moment | `D_rev`, `k_leak`, `eta_m` |
| 4 | Przewody | spadek ciśnienia przy kilku przepływach (dwa czujniki ciśnienia); sprawdzić, przy jakim przepływie charakterystyka przestaje być liniowa | `l`, `d`, `zeta`, `roughness` (i czy przejście w turbulencję zgadza się z `Re_lam`, `Re_turb`) |
| 5 | Komory | quasi-statyczne napełnianie strzykawką z czujnikiem ciśnienia, ogon zablokowany; kilka cykli napełnij–opróżnij (histereza) | krzywa p–V (`table` lub plik CSV), `V_prefill` |
| 6 | Zawory przelewowe | ciśnienie otwarcia i przepływ ponad nim (pompa na zamknięty obwód) | `p_set`, `dp_open`, `V_flow_nominal` |
| 7 | Ogon (statycznie) | moment na zablokowanym ogonie (siłomierz na ramieniu) vs różnica ciśnień; kąt swobodnego ogona vs różnica ciśnień | `D_tail` (z momentu), `k` (z kąta) |
| 8 | Ogon (dynamicznie) | drgania własne po wychyleniu: w powietrzu (`J`, `c`), potem w wodzie (`J_added`, `c_h`) | `J`, `c`, `J_added`, `c_h` |
| 9 | Ciąg | ciąg na uwięzi (siłomierz) przy kilku częstotliwościach i amplitudach; najlepiej też przy przepływie w tunelu | `C_T`, `s_fin`, `L_tail` |
| 10 | Kadłub | holowanie ze stałą prędkością albo wybieg (spadek prędkości po wyłączeniu napędu) | `C_d·A`, `m_added_x` |
| 11 | Balast i pion | ważenie w wodzie przy kilku położeniach tłoka; wybieg w pionie po skoku pęcherza; zależność wyporu od głębokości | `V_b_neutral`, `V_air0`, `m_added_z`, `C_dz·A_z`, `lead`, `gear_ratio` |

Po każdym kroku warto powtórzyć odpowiedni test z `FishRobot.Tests` z nowymi parametrami i porównać przebieg z pomiarem. Kroki 1–8 dotyczą samego napędu ogona i można je wykonać na stole bez wody (oprócz kroku 8). Kroki 9–11 wymagają basenu.
