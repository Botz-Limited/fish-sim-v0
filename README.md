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
| 10 | Kalibracja: stanowiska `FishRobot.Calibration` i `calibrate.py` dla kroków 2–11 planu kalibracji | gotowe, sprawdzone na pomiarach syntetycznych |

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
.venv/bin/python scripts/calibrate.py motor     # identyfikacja silnika DC (pomiar syntetyczny) -> results/calibration/
.venv/bin/python scripts/calibrate.py motor --data pomiar.csv --U 6 --t-step 0.01   # to samo na prawdziwym pomiarze
.venv/bin/python scripts/calibrate.py pump      # identyfikacja pompy (wymaga wyniku kroku motor)
.venv/bin/python scripts/calibrate.py pipe [--data punkty.csv --l 0.2]   # identyfikacja przewodu z Δp(Q)
.venv/bin/python scripts/calibrate.py chamber [--data cykle.csv --V-rest 5e-6]   # krzywa p–V komory -> CSV dla Chamber
.venv/bin/python scripts/calibrate.py valve [--data punkty.csv]   # zawór przelewowy z Q(Δp), z histerezą grzybka
.venv/bin/python scripts/calibrate.py tail-static [--data punkty.csv --k small]   # D_tail i k ogona
.venv/bin/python scripts/calibrate.py tail-dynamic [--data-air a.csv --data-water w.csv]   # J, c, J_added, c_h
.venv/bin/python scripts/calibrate.py thrust [--data punkty.csv --noise-abs 1e-4 --noise-rel 0.05]   # C_T płetwy
.venv/bin/python scripts/calibrate.py hull [--data-tow h.csv --data-coast w.csv --A 0.005 --m 1.0]   # C_d, m_added_x
.venv/bin/python scripts/calibrate.py ballast [--data-turns t.csv --data-depth d.csv --data-vertical v.csv]   # balast i pion
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

### Identyfikacja silnika (krok 2): `calibrate.py motor`

Na stole wystarczy jeden rozruch: skok napięcia z zasilacza na silnik z wolnym wałem, zapis prądu i prędkości. Model stanowiska to `FishRobot.Calibration.MotorStep`. Każdy z pięciu parametrów kształtuje inną część przebiegu, więc wszystkie da się wyznaczyć naraz:

- `R` – szczyt prądu (wirnik jeszcze stoi),
- `L` – narastanie prądu do szczytu,
- `k` – prędkość ustalona,
- `b` – prąd ustalony,
- `J` – czas rozpędzania.

`calibrate.py` kompiluje model raz i dopasowuje parametry metodą najmniejszych kwadratów (`scipy.optimize.least_squares`). Każde wywołanie to uruchomienie gotowego pliku wykonywalnego z `-override`, a kolumny jakobianu liczą się równolegle. Parametry są dopasowywane w skali logarytmicznej, bo wszystkie są dodatnie i różnią się o 6 rzędów wielkości. Plik pomiaru to CSV z nagłówkiem i kolumnami `time [s], i [A], w [rad/s]`. Wynik zawiera gotowy modyfikator do wklejenia w model, niepewność 1σ każdego parametru i macierz korelacji (`results/calibration/motor_step_fit.{txt,png}`).

Bez `--data` skrypt sprawdza samą procedurę. Tworzy „pomiar” z modelu o znanych parametrach (inne niż placeholdery o 25–100%), dodaje szum czujników (0,03 A i 2 rad/s) i dopasowuje, startując od placeholderów. Całość zajmuje ok. 1,5 s. Wszystkie parametry wracają z błędem poniżej 1,5σ. W 20 powtórzeniach z innym szumem rozrzut wyników zgadza się z podawaną niepewnością, a średni błąd jest bliski zera:

| Parametr | Niepewność 1σ | Rozrzut w 20 powtórzeniach |
|---|---|---|
| `R` | 0,09% | 0,09% |
| `L` | 1,0% | 0,9% |
| `k` | 0,03% | 0,03% |
| `J` | 0,11% | 0,10% |
| `b` | 1,2% | 1,4% |

**Lekcja: wagi sygnałów decydują o niepewności.** Prąd i prędkość mają różne jednostki i różny szum, więc reszty trzeba podzielić przez szum każdego czujnika. Szumu zwykle nie znamy, dlatego skrypt po pierwszym dopasowaniu szacuje go z reszt każdego sygnału osobno i dopasowuje jeszcze raz. Pierwsza wersja ważyła sygnały przez 1% zakresu. Prąd był wtedy względnie dwa razy bardziej zaszumiony niż prędkość, a wspólna wariancja reszt to ukrywała. Niepewność `b`, wyznaczanego głównie z prądu ustalonego, wychodziła przez to za mała: 1,0% przy rzeczywistym rozrzucie 1,6%.

Macierz korelacji pokazuje, czego eksperyment nie rozróżnia dobrze. `k` i `b` są skorelowane (−0,84), bo oba ustalają punkt pracy w stanie ustalonym, a `R` i `J` (−0,77), bo razem dają mechaniczną stałą czasową `J·R/k²`. Niepewność `b` i `L` jest największa: prąd ustalony to tylko ok. 0,08 A, a narastanie prądu trwa ok. 0,5 ms, czyli kilka próbek przy 5 kHz. Na prawdziwym stole pomaga dłuższy zapis stanu ustalonego (uśrednianie prądu) i szybsze próbkowanie prądu. Krok zapisuje parametry silnika z kowariancją do `results/calibration/motor_params.json`, z którego korzysta krok 3.

### Identyfikacja pompy (krok 3): `calibrate.py pump`

Silnik z kroku 2 kręci pompą, która tłoczy wodę ze zbiornika przez zawór dławiący z powrotem do zbiornika (`FishRobot.Calibration.PumpBench`). Punkt pracy ustawia się napięciem zasilacza i nastawą zaworu, a w każdym punkcie, po ustaleniu prędkości, mierzy się `U, i, w, Δp, Q`. Plik pomiaru to CSV z tymi kolumnami (jednostki SI). Równania pompy są liniowe w szukanych parametrach, więc zamiast dopasowywać symulację wystarcza regresja liniowa:

- `Q = D·ω − k_leak·Δp` daje `D_rev = 2π·D` i `k_leak`,
- `k·i − b·ω = D·Δp/η_m` daje `η_m`. Lewa strona to moment na wale policzony z prądu, czyli silnik działa jako czujnik momentu.

Model stanowiska służy tu tylko do wygenerowania pomiaru syntetycznego: 3 napięcia × 5 nastaw zaworu, „prawdziwy” silnik z kroku 2 i pompa różna od placeholderów, plus szum uśrednionych wartości. Wynik (`results/calibration/pump_fit.{txt,png}`):

| Parametr | Niepewność 1σ | Rozrzut w 2000 powtórzeniach | Średni błąd |
|---|---|---|---|
| `D_rev` | 0,14% | 0,14% | 0,00% |
| `k_leak` | 4,1% | 4,0% | −0,1% |
| `eta_m` | 0,77% | 0,65% | −0,33% |

**Lekcja: błąd czujnika nie uśrednia się.** `eta_m` ma stały błąd −0,33%, także bez żadnego szumu. Bierze się z parametrów silnika z kroku 2 (`b` wyszło tam o 1,2% za małe), a ten sam błąd momentu jest w każdym punkcie pracy. Więcej punktów zmniejsza tylko część niepewności pochodzącą z rozrzutu (0,63%), a część od silnika (0,36%) zostaje. Dlatego skrypt podaje obie części osobno i uwzględnia korelację `k` i `b` z kroku 2. Tarcie silnika `b·ω` to od 15% (przy najwyższym Δp) do ponad 80% (zawór otwarty) momentu z prądu, więc dokładne `b` jest tu ważniejsze, niż sugerowałby sam krok 2. Druga pułapka: tarcie lepkie pompy (proporcjonalne do ω) byłoby nie do odróżnienia od `b` silnika, bo w tym stanowisku zawsze występują razem. Jeśli prawdziwa pompa takie tarcie ma, pokaże się jako stały moment przy `Δp ≈ 0` na prawym wykresie.

Najmniej dokładny jest przeciek (ok. 4%): przy 85 kPa to tylko 2,5 ml/s wobec ok. 30 ml/s wyparcia, a szum przepływomierza to 0,1 ml/s. Pomaga więcej punktów przy wysokim Δp i niskiej prędkości, gdzie przeciek stanowi większą część przepływu.

### Identyfikacja przewodu (krok 4): `calibrate.py pipe`

Pompa przetłacza wodę przez badany przewód, a w kilkunastu punktach pracy mierzy się przepływ i spadek ciśnienia czujnikiem różnicowym (`FishRobot.Calibration.PipeBench`). Plik pomiaru to CSV z kolumnami `Q [m³/s], dp [Pa]`. Długość mierzy się linijką (`--l`), a dopasowujemy średnicę hydrauliczną `d`, straty miejscowe `zeta` i chropowatość `roughness`. Charakterystyka jest nieliniowa i przechodzi z laminarnej w turbulentną, więc tu znowu dopasowujemy symulację. Model nie ma inertancji, więc rampa przepływu w czasie służy tylko do przejścia po punktach pracy. Szum czujnika ciśnienia jest względny (procent odczytu), a Δp zmienia się o 3 rzędy wielkości, dlatego reszty liczone są jako `ln(Δp_sym/Δp_pomiar)`.

Pomiar syntetyczny: 20 punktów od 1 do 40 ml/s (Re ok. 350–14 000), szum 1% odczytu. „Prawdziwy” przewód ma średnicę 3,6 mm zamiast nominalnych 4 mm, `zeta = 2,5` i gładką ściankę (5 µm). Wyniki z 200 powtórzeń (`results/calibration/pipe_fit.{txt,png}`):

| Parametr | Niepewność 1σ | Rozrzut | Średni błąd |
|---|---|---|---|
| `d` | 0,23% | 0,24% | 0,0% |
| `zeta` | 2,2% | 2,3% | 0,1% |
| `roughness` | 29% | 32% | −7% |

**Lekcja: nie każdy parametr da się wyznaczyć z danego eksperymentu.** Średnicę wyznacza głównie zakres laminarny, bo opór rośnie tam jak `1/d⁴`: 0,23% niepewności `d` to ok. 1% oporu. Dla tego węża placeholder 4 mm dawał prawie 2 razy za mały opór. Chropowatość ma niepewność 29%, bo przy Re poniżej ok. 15 000 gładki wąż zachowuje się prawie jak idealnie gładka rura i ścianka ledwo wpływa na tarcie. Taki parametr lepiej przyjąć z tablic, niż dopasowywać. Sprawdzenie: przy chropowatości z tablic 1,5 µm, czyli 3 razy za małej, `d` przesuwa się o 0,25%, a `zeta` o 3,4%, czyli o 1–1,6σ. Średnica i `zeta` są silnie skorelowane (0,96), bo obie podnoszą opór w całym zakresie. Gdyby `d` zmierzyć osobno (np. objętością wody w odcinku węża), niepewność `zeta` by spadła.

Model przejścia laminarny–turbulentny (interpolacja między `Re_lam` a `Re_turb`) jest tu założeniem, a nie wynikiem. W pomiarze syntetycznym zgadza się z „rzeczywistością” z definicji. Na prawdziwym pomiarze błędne progi przejścia pokażą się jako garb reszt w szarym pasie na wykresie.

### Krzywa p–V komory (krok 5): `calibrate.py chamber`

Strzykawka (najlepiej pompa strzykawkowa) powoli wtłacza i wyciąga wodę z komory przy zablokowanym ogonie, a czujnik ciśnienia stoi przy komorze. Kilka cykli od lekkiego podciśnienia do ciśnienia otwarcia zaworu. Plik pomiaru to CSV w kolejności czasu z kolumnami `dV [m³]` (objętość ze strzykawki względem spoczynku) i `p [Pa]` (nadciśnienie). Wynikiem nie są parametry, tylko cała krzywa: `results/calibration/chamber_pV.csv` w formacie dla `Chamber(tableOnFile = true, fileName = ...)`. Objętość w spoczynku (`--V-rest`) nie wynika z tego pomiaru, trzeba ją wziąć z CAD albo z ważenia. W modelu liczy się zresztą tylko jej położenie względem `V_prefill`, czyli to, ile wody dolano ponad spoczynek przy zamykaniu obwodu.

Przetwarzanie:

1. Podział na suwy między zawróceniami strzykawki i odrzucenie pierwszego cyklu. Silikon przy pierwszym rozciągnięciu jest sztywniejszy (efekt Mullinsa).
2. W 15 węzłach lokalna regresja liniowa osobno dla gałęzi napełniania i opróżniania, uśredniona po cyklach.
3. Krzywa szkieletowa = średnia obu gałęzi. Skrypt sprawdza, czy jest rosnąca, bo innej `Chamber` nie przyjmie.
4. Pole pętli histerezy `∮ p dV` z surowych danych, czyli energia tracona w każdym cyklu.
5. Kontrola w Modelice: `FishRobot.Calibration.ChamberBench` z wyznaczonym plikiem (`fileName` przez `-override`) przechodzi przez cały zakres.

Pomiar syntetyczny: „prawdziwa” komora jest na początku bardziej miękka od placeholdera, a potem mocniej sztywnieje. Ma histerezę o półszerokości `300 Pa + 6%·|p|`, pierwsze napełnienie o 15% sztywniejsze i szum (150 Pa, 0,01 ml). Cztery cykle od −3 do +10 ml. Wyniki (`results/calibration/chamber_fit.{txt,png}`):

- krzywa w węzłach różni się od prawdziwej krzywej szkieletowej o najwyżej 0,17% zakresu ciśnień, a po interpolacji w `Chamber` o 0,53%,
- bez odrzucenia pierwszego cyklu: 1,7%,
- pętla histerezy: 25 mJ na cykl przy pełnym suwie.

**Lekcja: czubki pętli nie leżą na krzywej szkieletowej.** W punkcie zawrócenia strzykawki obie gałęzie się spotykają, bo histereza potrzebuje trochę objętości, żeby się „przełączyć”. Węzły na samych końcach suwu dawały błąd 4,8% zakresu. Dlatego tabela kończy się 1 ml przed punktami zawrócenia (`--margin`), a dalej `Chamber` przedłuża krzywą liniowo, czyli przy rosnącej sztywności zaniża ciśnienie. Suw strzykawki trzeba więc zaplanować z zapasem ponad zakres pracy komory w robocie.

**Czy brak histerezy w modelu ma znaczenie?** W scenariuszu `EnergyBudget` komory pracują między 6 a 10 ml, czyli 1–5 ml ponad spoczynek, przy 2–12 kPa. Syntetyczna komora traci w takim cyklu ok. 3,9 mJ. Dla dwóch komór przy 1 Hz to ok. 8 mW, czyli ok. 0,4% mocy napędu ogona (1,8 W). To więcej niż straty ogona w bilansie (0,1%), ale mniej niż przewody i łożyska. Prawdziwy silikon może mieć szerszą pętlę, więc tę liczbę trzeba policzyć ponownie z pomiaru. Jeśli wyjdzie istotna, `Chamber` trzeba rozszerzyć o tłumienie lepkosprężyste.

### Zawór przelewowy (krok 6): `calibrate.py valve`

Pompa z kroku 3 tłoczy wodę przez zawór do zbiornika. Przepływ zwiększa się małymi krokami, a potem zmniejsza, i w każdym punkcie mierzy się przepływ i różnicę ciśnień na zaworze (`FishRobot.Calibration.ValveBench`). Plik pomiaru to CSV z kolumnami `dp [Pa], Q [m³/s], up` (1 przy rosnącym przepływie, 0 przy malejącym). Dopasowujemy `p_set`, `V_flow_nominal` i `dp_smooth` osobno dla obu gałęzi i wspólnie.

**`dp_open` nie jest dopasowywane.** W modelu przewodność otwartego zaworu to `V_flow_nominal/dp_open`, więc pomiar wyznacza tylko ten iloraz. Dwa razy większe oba parametry dają identyczną charakterystykę, a jakobian ma wtedy dwie proporcjonalne kolumny. `dp_open` zostaje punktem odniesienia (5 kPa).

Pomiar syntetyczny: zawór ze słabszą sprężyną (`p_set` = 46 kPa zamiast 50), z większą przewodnością, łagodniejszym otwarciem i histerezą grzybka 2 kPa (otwiera się przy 47 kPa, zamyka przy 45 kPa). 15 punktów w każdą stronę, szum przepływomierza 0,05 ml/s i czujnika 100 Pa. Wyniki (`results/calibration/valve_fit.{txt,png}`):

| | `p_set` | Niepewność |
|---|---|---|
| gałąź otwierania | 46,97 kPa | ±0,10 kPa |
| gałąź zamykania | 45,08 kPa | ±0,11 kPa |
| wspólnie | 46,06 kPa | ±0,72 kPa |

Histereza wyznaczona z różnicy gałęzi: 1,89 kPa przy prawdziwych 2 kPa.

**Lekcja: reszty pokazują, czego model nie umie.** Przy wspólnym dopasowaniu reszty układają się w dwa pasma przeciwnego znaku (dolny panel wykresu). Szum oszacowany z reszt wychodzi 1,9 ml/s, czyli prawie 40 razy więcej niż szum przepływomierza. To nie szum, tylko histereza, której model z jednym `p_set` nie ma. Niepewność wspólnego `p_set` (±0,72 kPa) jest przez to 7 razy większa niż każdej gałęzi z osobna, ale to uczciwa miara: tyle wynosi rozjazd modelu z zaworem. Przy histerezie 2 kPa (4% `p_set`) jedno `p_set` ze środka wystarcza do bilansu energii. Jeśli zawór ma ograniczać ciśnienie w komorach z zapasem, liczy się gałąź otwierania. `dp_smooth` jest wyznaczane słabo (±51%), bo zależy tylko od kilku punktów przy samym otwarciu. Wpływa jednak tylko na kształt kolanka charakterystyki. Jego „ogon” poniżej `p_set` działa w modelu jak dodatkowy przeciek (ok. 0,2 ml/s przy 35 kPa), więc osobno mierzony przeciek zamkniętego zaworu (`G_leak`, np. zbieranie kropel przez kilka minut) ma sens tylko wtedy, gdy jest większy.

### Ogon statycznie (krok 7): `calibrate.py tail-static`

Dwa pomiary przy różnicy ciśnień zadanej strzykawkami i mierzonej czujnikiem różnicowym:

- **ogon zablokowany**, siłomierz na ramieniu: `τ = D_tail·Δp`, prosta przez zero daje `D_tail`,
- **ogon swobodny**, kąt z kamery lub enkodera: `k·θ = D_tail·Δp`, nachylenie daje `D_tail/k`, a z `D_tail` wynika `k`.

Plik pomiaru to CSV z kolumnami `dp_blocked, tau, dp_free, theta` (SI). Skrypt sprawdza też, czy kąt jest liniowy w Δp: dopasowuje dodatkowo człon `Δp³` i podaje jego statystykę t. Model ma stałe `k`, a prawdziwy silikon zwykle sztywnieje przy dużych kątach.

### Ogon dynamicznie (krok 8): `calibrate.py tail-dynamic`

Ogon wychylony i puszczony z bezruchu, komory otwarte do zbiornika, więc hydraulika nie dokłada sztywności ani tłumienia (`FishRobot.Calibration.TailDecay`). Najpierw w powietrzu, gdzie dopasowujemy `J` i `c`, potem w wodzie, gdzie dopasowujemy `J_added`, `c` i `c_h` przy `J` z powietrza. Wychylenie początkowe dopasowujemy jako parametr pomocniczy. Pliki pomiaru to CSV z kolumnami `time, theta`.

**Z drgań swobodnych nie da się wyznaczyć bezwładności bez sztywności.** Równanie podzielone przez `J` zawiera tylko `k/J`, `c/J` i `c_h/J`, więc dwa razy większe wszystkie parametry dają ten sam przebieg θ(t). Dlatego `k` pochodzi z kroku 7, a jego błąd przenosi się 1:1 na wszystkie parametry dynamiczne. Skrypt podaje osobno niepewność z dopasowania i całkowitą (z `k` i, dla `J_added`, z `J` z powietrza). W wodzie tłumienie liniowe `c` i kwadratowe `c_h` są skorelowane (−0,75). Rozróżnia je tylko zależność zaniku od amplitudy, więc `c` wychodzi z niepewnością ok. 7%. Pomogłyby dodatkowe drgania z małego wychylenia, gdzie dominuje `c`.

Pomiar syntetyczny: ogon z `D_tail` = 1,6e-5 m³/rad, sztywnością 2,6 N·m/rad przy małych kątach, rosnącą z kątem (`k·(1 + 0,6·θ²)`), i dynamiką liniową z tą sztywnością. 17 punktów statycznych do ±40 kPa (±14°), drgania próbkowane 500 Hz z szumem 0,17°. Wyniki (`results/calibration/tail_*`):

| `--k` | `k` do kroku 8 | `J`: błąd | `J`: niepewność całkowita |
|---|---|---|---|
| `line` (prosta w całym zakresie) | 2,657 (+2,2%) | +2,2% | ±0,72% |
| `small` (małe kąty, z członem Δp³) | 2,546 (−2,1%) | −2,1% | ±1,30% |

**Lekcja: niezgodność modelu daje błąd, którego nie widać w σ.** Prosta w całym zakresie ma obciążenie: w 500 powtórzeniach średnio +2,3% przy rozrzucie tylko 0,6%. Jej σ jest małe, ale fałszywe, bo błąd `J` jest 3 razy większy od podanej niepewności. Sztywność przy małych kątach nie ma obciążenia (średnio 2,605 przy prawdziwych 2,6), ale ma większy rozrzut (1,5%). Tu błąd mieści się w σ. Który wariant wybrać, zależy od zakresu pracy: przy 1 Hz ogon macha o ok. 8°, a przy zaworze otwartym o ok. 31°. Ogólna zasada: jeśli test nieliniowości alarmuje, `k` trzeba mierzyć w zakresie kątów, w którym ogon naprawdę pracuje. Jeśli zakres jest duży, `TailEquivalent` potrzebuje nieliniowej sprężyny. Nieliniowości prawie nie widać na wykresie reszt, a test ją wykrywa (t = −3,5).

### Ciąg płetwy (krok 9): `calibrate.py thrust`

Ryba przymocowana do siłomierza, w basenie (`U = 0`, na uwięzi) i w miarę możliwości w tunelu wodnym przy kilku prędkościach przepływu. W każdym punkcie mierzy się średni ciąg i amplitudę kąta ogona. W tunelu siłomierz widzi ciąg minus opór kadłuba, więc przy każdej prędkości trzeba też zmierzyć siłę przy nieruchomym ogonie (tara) i ją odjąć. Plik pomiaru to CSV z kolumnami `Theta [rad], f [Hz], U [m/s], T [N]`.

Średni ciąg dla zadanego sinusa kąta liczy `FishRobot.Calibration.ThrustBench` (`C_T = 1`). Ciąg jest liniowy w `C_T`, więc `C_T` wyznacza regresja przez zero. `s_fin` występuje w modelu tylko w iloczynie `C_T·s_fin²`, dlatego `s_fin` i `L_tail` mierzy się linijką. Skrypt sprawdza też postać modelu: dopasowuje osobno człon statyczny i karę za prędkość (`T = a·T(0) − b·(T(0) − T(U))`). W teorii Lighthilla `b/a = 1`.

**Wagi z modelu szumu czujnika.** Szum siłomierza ma część stałą (`--noise-abs`, tu 0,1 mN) i względną (`--noise-rel`, tu 5%). Przy połowie amplitudy ciąg to ok. 0,3 mN, więc dominuje część stała, a przy pełnej amplitudzie (ok. 3 mN) względna. W 2000 powtórzeniach zwykła regresja zaniżała niepewność `C_T` z uwięzi (σ 2,95% przy rozrzucie 3,86%). Regresja ważona tylko szumem względnym była jeszcze gorsza (rozrzut 5,1%). Dopiero wagi z pełnego modelu szumu dają σ zgodne z rozrzutem (3,64% i 3,64%).

Pomiar syntetyczny: płetwa z `C_T = 0,6` i karą za prędkość 1,5 razy większą niż w teorii (np. przez oderwanie przepływu). Amplitudy jak w przeglądzie częstotliwości (pompa ogranicza θ·f), pełna i połowa komendy, 4 częstotliwości × 4 prędkości (0–10 cm/s), razem 32 punkty. Wyniki z 2000 powtórzeń (`results/calibration/thrust_fit.{txt,png}`):

| Estymator | Średnio | Rozrzut | σ |
|---|---|---|---|
| `C_T`, wszystkie punkty | 0,584 (−2,6%) | 2,0% | 2,3% |
| `C_T`, tylko na uwięzi | 0,600 (0,0%) | 3,6% | 3,6% |
| kara za prędkość `b/a` | 1,50 | 0,12 | 0,14 |

**Lekcja: model o złej postaci daje obciążony parametr, ale nie zawsze ma to znaczenie.** `C_T` ze wszystkich punktów jest obciążone, bo model źle opisuje spadek ciągu z prędkością. `C_T` z samej uwięzi tego problemu nie ma, ale ma większy rozrzut. Skrypt wpisuje do modelu `C_T` z uwięzi, bo robot pływa wolno: przy 1 Hz krawędź spływu porusza się z prędkością ok. 63 cm/s, a robot płynie 6 cm/s. Kara za prędkość to tam ok. 1% ciągu, a jej błąd o 50% zmienia ciąg o ok. 0,5%. Ma ona znaczenie dopiero dla prędkości maksymalnej: ciąg znika przy `L·ω/√1,5` ≈ 51 cm/s zamiast 63 cm/s. Test postaci wykrywa `b/a = 1,5` (powyżej 3σ) tylko w 74% powtórzeń. Rozstrzygają go nieliczne punkty o dużym `U²/(L·ω)²`, czyli przy małej częstotliwości i dużej prędkości przepływu (prawy wykres), a nie liczba punktów.

### Kadłub (krok 10): `calibrate.py hull`

Dwa pomiary w basenie, oba z nieruchomym ogonem:

- **holowanie** ze stałą prędkością, siłomierz na wózku: `F = ½·ρ·C_d·A·U²`. Pole `A` mierzy się linijką (wyznaczalny jest tylko iloczyn `C_d·A`), a `C_d` wynika z regresji ważonej modelem szumu siłomierza. Plik: `U [m/s], F [N]`.
- **wybieg** po puszczeniu z wózka, położenie z kamery nad basenem (`FishRobot.Calibration.CoastDown`). Plik: `time [s], x [m]`, z `x = 0` w chwili puszczenia.

**Wybieg zależy tylko od `k_d/M`**, gdzie `k_d = ½·ρ·C_d·A`, a `M = m + m_added_x`. Dlatego `C_d` pochodzi z holowania, `m` z wagi (`--m`), a wybieg daje masę całkowitą `M` i dopiero z niej masę dodaną `m_added_x = M − m`. Prędkość początkową dopasowujemy jako parametr pomocniczy.

Pomiar syntetyczny: `C_d = 0,4`, `A = 50 cm²`, `m = 1 kg`, `m_added_x = 0,08 kg`. Holowanie przy 10 prędkościach 2–20 cm/s (szum 0,1 mN + 3%), wybieg z 15 cm/s przez 20 s, kamera 30 kl./s z szumem 2 mm (`results/calibration/hull_fit.{txt,png}`):

- `C_d` = 0,402 ± 0,9%,
- masa całkowita z wybiegu: niepewność z samego dopasowania tylko 0,09%,
- `m_added_x` = 0,084 ± 0,010 kg (12%), z czego 0,0097 kg pochodzi z `C_d`, a po 0,001 kg z dopasowania i z ważenia.

W 200 powtórzeniach rozrzut `m_added_x` to 0,015 kg (ok. 18%), przy średnim σ 0,014 kg i bez obciążenia.

**Lekcja: mała różnica dużych liczb.** Masa dodana to tylko 8% masy całkowitej, więc każdy procent błędu `M` daje ok. 13% błędu `m_added_x`. Kamera wyznacza `k_d/M` bardzo dokładnie, ale błąd `C_d` z holowania przechodzi w `M` 1:1 i zjada całą precyzję. Żeby poprawić `m_added_x`, trzeba lepiej zmierzyć opór (więcej punktów holowania przy prędkościach z wybiegu, 5–15 cm/s), a nie dłużej filmować wybieg. Dla samego pływania to małe zmartwienie: `m_added_x` wpływa tylko na czas rozpędzania, a prędkość ustalona zależy wyłącznie od `C_d·A`, który jest wyznaczony z dokładnością 1%.

### Balast i pion (krok 11): `calibrate.py ballast`

Trzy pomiary w basenie:

1. **Ważenie pod wodą przy kilku położeniach tłoka** (licznik obrotów silnika strzykawki, 0 = pęcherz pusty). Ciężar pozorny `W = ρ·g·(V_b_neutral − A_tłoka·posuw·n)` jest liniowy w liczbie obrotów `n`. Wyraz wolny to `ρ·g·V_b_neutral`, niezależnie od geometrii tłoka. Nachylenie daje posuw tłoka na obrót silnika, czyli `lead/gear_ratio` (tylko ten iloraz), przy średnicy tłoka z suwmiarki. Plik: `turns, W [N]`.
2. **Ważenie na kilku głębokościach** przy stałym tłoku: `W = W0 + ρ·g·V_air0·(1 − p_atm/(p_atm + ρ·g·h))`, regresja liniowa w `W0` i `V_air0`. Plik: `depth [m], W [N]`.
3. **Wynurzanie po skoku pęcherza** z pływalności neutralnej (`FishRobot.Calibration.VerticalStep`), położenie z czujnika ciśnienia w kadłubie. Siła `ρ·g·dV` jest znana, więc prędkość graniczna wyznacza opór `C_dz`, a czas rozpędzania masę `m + m_added_z`. Plik: `time [s], z [m]`, skok w `t = 2 s`.

Pomiar syntetyczny (waga pod wodą 1 mN, czujnik głębokości 3 mm) (`results/calibration/ballast_fit.{txt,png}`):

| Parametr | Wynik | Niepewność | Błąd |
|---|---|---|---|
| `V_b_neutral` | 7,29 ml | ±0,06 ml | +1,3% |
| posuw tłoka | 33,1 µm/obr | ±0,8% | +1,3% |
| `V_air0` | 15,2 ml | ±0,7 ml | +1,2% |
| `m_added_z` | 0,595 kg | ±1,6% | −0,8% |
| `C_dz` | 1,304 | ±1,1% | +0,3% |

**Lekcja 1: znana siła daje masę dodaną.** W kroku 10 wybieg wyznaczał tylko `k_d/M`, a masa dodana wynikała z różnicy dużych liczb z niepewnością 18%. Tu wymuszenie `ρ·g·dV` jest znane z położenia tłoka, więc jeden przebieg wyznacza i opór, i masę, a `m_added_z` wychodzi z niepewnością 1,6%. Masa dodana w pionie (60% masy ryby) jest też dużo większa niż wzdłuż osi (8%), więc łatwiej ją zmierzyć.

**Lekcja 2: model może pasować idealnie i być zły.** Kieszeń powietrza w kadłubie (15 ml) rozpręża się przy wynurzaniu. Na 0,5 m drogi z 1,5 m to ok. 0,7 ml dodatkowego wyporu, prawie tyle co sam skok pęcherza (1 ml). Dopasowanie modelu bez ściśliwości daje `C_dz` = 1,01 (prawdziwe 1,3) i `m_added_z` = 0,71 kg (prawdziwe 0,6), a reszty mają 3,0 mm, czyli dokładnie szum czujnika. Rosnący wypór „chowa się” w oporze i masie, więc reszty niczego nie zdradzają. Dlatego `VerticalStep` ma włączoną ściśliwość, `V_air0` pochodzi z pomiaru 2, a jego niepewność jest doliczana do niepewności `C_dz` i `m_added_z` (przez ponowne dopasowanie przy `V_air0 + σ`).

### Podsumowanie kalibracji

Każdy krok ma model stanowiska w `FishRobot.Calibration` (albo regresję, gdy zależności są liniowe), pomiar syntetyczny ze znanymi parametrami i sprawdzenie, czy podawana niepewność zgadza się z rozrzutem w powtórzeniach. Przy prawdziwych pomiarach wystarczy podać pliki CSV (`--data...`). Lekcje powtarzające się w wielu krokach:

- **Nie każdy parametr da się wyznaczyć z danego pomiaru.** Często widać tylko iloraz albo iloczyn: `C_T·s_fin²`, `C_d·A`, `V_flow_nominal/dp_open`, `k/J`, `k_d/M`, `lead/gear_ratio`. Brakujący czynnik trzeba zmierzyć inaczej (linijka, waga, osobny pomiar statyczny), a jego błąd przenosi się na wynik.
- **Wagi sygnałów i punktów muszą wynikać z modelu szumu czujników.** Inaczej podawana niepewność jest za mała (silnik, ciąg).
- **Błąd czujnika zidentyfikowanego wcześniej nie uśrednia się.** Silnik jako czujnik momentu dla pompy, `k` ogona dla dynamiki, `C_d` dla masy dodanej, `V_air0` dla oporu w pionie.
- **Niezgodność modelu z rzeczywistością daje błąd, którego nie ma w σ.** Czasem widać ją w resztach (histereza zaworu, przejście laminarne w przewodzie), czasem tylko w teście postaci (nieliniowa sztywność ogona, ciąg w funkcji prędkości), a czasem wcale (ściśliwość przy wynurzaniu). Dlatego pomiar syntetyczny z „rzeczywistością” bogatszą niż model to dobry sposób, żeby przed wyjazdem na basen sprawdzić, czy plan pomiarów w ogóle pozwoli wyznaczyć parametry.
