# fish-sim-v0 / OpenFOAM – FSI miękkiego ogona w wodzie (OpenFOAM + preCICE + CalculiX)

Edukacyjne demo **sprzężenia płyn–ciało stałe** (FSI) dla miękkiego,
hydraulicznie napędzanego ogona ryby. Specyfikacja:
[SPEC_fish_fsi_openfoam_precice_calculix.md](SPEC_fish_fsi_openfoam_precice_calculix.md).
**To nie jest skalibrowany model** – wszystkie parametry fizyczne to
placeholdery (`tools/params.py`, komentarze `PLACEHOLDER` w plikach).

Co pokazuje, czego nie potrafią MuJoCo ani SOFA:
- prawdziwy przepływ wody (Navier–Stokes, OpenFOAM) wokół odkształcającego się ogona,
- dwukierunkowe sprzężenie: woda odkształca ogon, ogon zmienia przepływ (preCICE),
- ślad wirowy i ciąg/opór liczony z ciśnienia i naprężeń na powierzchni,
- efekt **masy dodanej** i to, dlaczego sprzężenie silikon–woda wymaga schematu niejawnego.

Stan: **etapy 0–6 zakończone** (7.10.2026); `tools/check_results.py`: 47 PASS,
1 FAIL (E4 – amplituda w wodzie większa niż na sucho, bo napęd 1 Hz trafia w
rezonans w wodzie; wyjaśnienie w NOTES.md). Etap 7 (3D) nieuruchamiany – wymaga
potwierdzenia czasu obliczeń.

Dziennik problemów i ich diagnoz: [NOTES.md](NOTES.md). Dokładne wersje: [versions.txt](versions.txt).

---

## 1. Instalacja (Arch Linux / EndeavourOS)

```bash
# raz, wymaga hasła (~1 GB, głównie ParaView):
sudo pacman -S --needed openmpi scotch gcc-fortran arpack ccache git-lfs \
     paraview python-matplotlib python-pandas python-scipy
OpenFOAM/setup.sh            # reszta bez sudo, ~1.5 h (głównie kompilacja OpenFOAM)
source OpenFOAM/env.sh       # w każdej nowej powłoce (bash lub zsh)
```

`setup.sh` pomija kroki już zrobione. Instaluje do `~/opt/fsi` (preCICE,
CalculiX, Python venv) i `~/OpenFOAM/OpenFOAM-v2606`.

| Składnik | Wersja | Uwagi |
|---|---|---|
| preCICE | **3.4.1** | ze źródeł, Release, `-O3 -march=native`, **Eigen 3.4.0** (z Eigen 5 z Arch – FPE, patrz NOTES) |
| OpenFOAM | **v2606** (openfoam.com) | ze źródeł, `-O3 -march=native`, ccache, systemowy OpenMPI 5 |
| Adapter OpenFOAM | **1.4.0** | wydanie „v1812–v2606-newer” |
| CalculiX + adapter | **2.20** + **2.20.2** | adapter 2.20.2 wymaga ccx 2.20; solver **PARDISO** (Intel MKL z pip) |
| Tutoriale preCICE | `develop` @ `e3188113` | ostatnie wydanie (v202404.0) jest z 2024 r., starsze niż adapter 1.4 |

Skąd ten zestaw: zgodny z preCICE v3 – najnowszy preCICE, adapter OpenFOAM
deklarujący wsparcie OpenFOAM do v2606, adapter CalculiX dla preCICE v3.
Ostatnia oficjalna „preCICE Distribution” (v2404.0) zawiera starsze wersje
(preCICE 3.1.1, adapter OF 1.3.0) – nowsze wydania zachowują zgodność z v3.

**Wydajność (Ryzen AI 5 PRO 340, 6 rdzeni / 12 wątków, 27 GB RAM):**
- płyn: 4 procesy MPI (`decomposeParDict`, scotch), ~20 ms/krok przy ~21 tys. komórek,
- ciało stałe: CalculiX z PARDISO na 2 wątkach – **1.6x szybciej niż SPOOLES**,
  a SPOOLES z 4 wątkami dawał wręcz błędne wyniki (NOTES.md),
- typowo ~0.6–1 s na okno czasowe FSI (5–6 iteracji sprzężenia).

---

## 2. Struktura

```
OpenFOAM/
  README.md  NOTES.md  versions.txt  setup.sh  env.sh  run_parallel.sh
  00-reference-flap/      oficjalny tutorial perpendicular-flap (OpenFOAM + CalculiX), bez zmian
  01-solid-only/          CalculiX sam: ogon z komorami, rampa ciśnienia, bez wody
  02-fluid-only/          OpenFOAM sam: sztywny ogon w napływie, zbieżność siatki, granice domeny
  03-fsi-passive/         FSI: ogon pasywny w strumieniu; explicit/ vs implicit/
  04-fsi-actuated/        FSI: napęd ciśnieniem w komorach, woda stojąca; water/ vs dry/
  05-fsi-inflow/          FSI: napęd + napływ U = 0.05 / 0.1 / 0.2 m/s
  06-freq-sweep/          FSI: f = 0.5 / 1.5 / 2 Hz (1 Hz = etap 4)
  tools/
    params.py             WSZYSTKIE parametry fizyczne i geometryczne (placeholdery)
    make_geometry.py      gmsh: geometria 2D ogona z komorami -> CalculiX i OpenFOAM
    make_actuation.py     przebieg ciśnienia w komorach (*AMPLITUDE/*DLOAD)
    fluid-base/           szablon przypadku OpenFOAM (komentarze po polsku)
    precice-base/         szablony precice-config (implicit/explicit), fsi.inp, config.yml
    new-fsi-case.sh       tworzy przypadek FSI z szablonów (parametry: U, dt, T, P0, f, schemat)
    postprocess.py        siły, kąt końcówki, wykresy -> results/
    pv_snapshots.py       pvbatch: zrzuty pola wirowości -> results/
    check_results.py      automatyczne kryteria poprawności (SPEC, sekcja 7)
  results/                PNG + CSV
```

Każdy przypadek FSI ma układ jak tutoriale preCICE: `fluid-openfoam/run.sh`,
`solid-calculix/run.sh` (można je uruchomić w dwóch terminalach) oraz
`run.sh` piętro wyżej, który uruchamia oba naraz.

---

## 3. Model fizyczny

```
           y
           ^        głowa (sztywna, nieruchoma)       ogon (silikon, CalculiX)
           |        ________________________________________________
 napływ U  |      /                    |  [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]  komora L (10 cel)   \
 -------> -+-----(                     |================================== ścianka środkowa   |  -> ślad wirowy
           |      \____________________|  [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]  komora R            /
           |    x = -0.06              x = 0 (nasada)                                x = L = 0.15
```

- **2D** (przekrój ogona w widoku z góry). Model ma grubość 1 m w z, więc
  **wszystkie siły są w N/m** (na metr rozpiętości) – jak w tutorialu.
- Ogon: 0.15 m, grubość 0.03 → 0.01 m. Dwie komory (L/R) podzielone żebrami na
  10 cel (styl PneuNet) – jedna długa komora „balonowała” zamiast zginać ogon
  (NOTES.md, etap 1).
- Woda: ρ = 1000 kg/m³, ν = 1e-6 m²/s.
- Silikon: E = 3e5 Pa, ν = 0.45, ρ = 1070 kg/m³, liniowo sprężysty, analiza
  **NLGEOM** (duże ugięcia). Elementy C3D8, jedna warstwa w z, przemieszczenie
  z zablokowane (płaski stan odkształcenia).
- Aktuacja: ciśnienie na ściankach cel (`*DLOAD` + `*AMPLITUDE`):
  p_L = P0·r(t)·max(0, sin 2πft), p_R = P0·r(t)·max(0, −sin 2πft), rampa r(t)
  przez pierwszy okres.

### Uproszczenia, które trzeba rozumieć

**Przepływ laminarny przy turbulentnym Re.** Dla U = 0.2 m/s i długości ciała
0.21 m: Re = U·L/ν ≈ 4·10⁴, realnie przepływ przejściowy/turbulentny. Demo
liczy laminarnie (`pimpleFoam`, `simulationType laminar`). W 2D laminarny
przepływ przy takim Re daje regularną ścieżkę wirów, ale opór tarcia i
oderwania warstwy przyściennej są obarczone błędem. Wariant „poprawny
laminarnie” = obniżyć Re (np. ν = 1e-4 → Re ≈ 400) kosztem realizmu.

**Ciśnienie zamiast objętości.** Wymuszamy ciśnienie w komorach. Pompa
hydrauliczna (wyporowa) wymusza raczej *objętość* – przy ciśnieniu zadanym
ogon może „uciekać” od obciążenia wody, a przy objętości zadanej ciśnienie
rośnie, gdy woda stawia opór. To przybliżenie; SOFA (demo obok) wymusza objętość.

---

## 4. Kluczowe zagadnienia numeryczne

1. **Masa dodana → sprzężenie niejawne.** Gęstość silikonu ≈ gęstość wody.
   Ogon, przyspieszając, musi przyspieszyć też wodę wokół siebie – w 2D ta
   „masa dodana” jest kilka razy większa od masy ogona. Przy sprzężeniu jawnym
   (jedna wymiana danych na krok) błąd siły jest w każdym kroku mnożony przez
   czynnik ~ m_dodana/m_ciała > 1, więc rośnie wykładniczo – **niezależnie od
   kroku czasowego**. Etap 3 to pokazuje. Rozwiązanie: `parallel-implicit` z
   akceleracją **IQN-ILS** (quasi-Newton na interfejsie).
2. **Ruch siatki.** `dynamicMotionSolverFvMesh` + `displacementLaplacian` z
   dyfuzyjnością `quadratic inverseDistance (tail head)`: komórki przy ciele
   poruszają się prawie sztywno, deformację przejmują duże komórki dalej.
   Amplituda końcówki ograniczona do ~15% L. Większe amplitudy wymagają
   przesiatkowania albo siatek overset – poza zakresem demo.
3. **Mapowanie** (`precice-config.xml`): RBF (compact-polynomial C6, promień
   5 mm), siły `conservative` (zachowana suma = zachowany ciąg), przemieszczenia
   `consistent`. CalculiX przekazuje tylko węzły (bez połączeń), więc RBF.
   preCICE 3.4 automatycznie wybiera wariant „partition-of-unity”.
4. **Krok czasowy.** Ten sam w obu solverach: okno preCICE = `DELTA_T`
   (`system/caseParams`) = przyrost `*DYNAMIC` w `fsi.inp` = 2.5 ms. Maks. liczba
   Couranta ~0.85 (przy U = 0.2 m/s), przy narożnikach końcówki.
5. **Tłumienie numeryczne w CalculiX** (`*DYNAMIC, ALPHA=-0.2`, schemat HHT).
   Bez niego nietłumione mody osiowe miękkiego ogona rozbiegały Newtona – nawet
   bez wody. Tłumienie HHT ∝ (ω·Δt)³ – w paśmie 0.5–2 Hz pomijalne.

---

## 5. Uruchamianie i czasy (ta maszyna)

```bash
source OpenFOAM/env.sh
cd OpenFOAM
python tools/check_results.py      # sprawdza wszystkie kryteria i odświeża wykresy
```

| Etap | Polecenie | Czas |
|---|---|---|
| 0 | `cd 00-reference-flap/fluid-openfoam && ./run.sh -parallel` + w drugim terminalu `cd 00-reference-flap/solid-calculix && ./run.sh`; potem `python tools/postprocess.py e0 00-reference-flap` | 34 s |
| 1 | `01-solid-only/run.sh` | ~10 s |
| 2 | `02-fluid-only/run_all.sh` (4 warianty) | 7 min |
| 3 | `03-fsi-passive/run_all.sh` | 10 min (jawne 20 s, niejawne 592 s) |
| 4 | `04-fsi-actuated/run_all.sh` | 16 min dla 4 s; wersja 8 s: 80 min (równolegle z etapem 5) |
| 5 | `05-fsi-inflow/run_all.sh` | 30 min na prędkość osobno; 2 h równolegle z etapem 4 |
| 6 | `06-freq-sweep/run_all.sh` | f = 0.5 Hz (16 s): 102 min, 1.5 Hz: 22 min, 2 Hz: 16 min |
| 4–6 | `setsid nohup ./run_parallel.sh &` (dwie kolejki równolegle, logi w `logs/`) | 3 h 47 min |

Zrzuty wirowości: `pvbatch tools/pv_snapshots.py 05-fsi-inflow/U0.1 e5_vorticity_U0.1 4`.
Ręcznie w ParaView: otwórz `<przypadek>/fluid-openfoam/fluid-openfoam.foam`
(wbudowany czytnik), pole `vorticity`, składowa Z, skala np. ±20 1/s.

Nowy przypadek (np. inna prędkość):
`tools/new-fsi-case.sh moj-przypadek --u 0.15 --p0 15000 --freq 1 --t-end 5 && moj-przypadek/run.sh`.

---

## 6. Wyniki – co pokazuje każdy wykres

Wszystkie siły na metr rozpiętości (model 2D). Parametry = placeholdery,
więc liczby służą do porównań, nie jako przewidywania.

### Etap 0 – referencja `e0_flap_tip.png`
Przemieszczenie końcówki elastycznego flapu w kanale (oficjalny tutorial
preCICE) w porównaniu z wynikami referencyjnymi tutorialu. Maks. błąd
względny **0.83%**, średnio 2.01 iteracji sprzężenia na okno (referencja 2.012):
instalacja działa tak jak u autorów preCICE.

### Etap 1 – sam ogon `e1_tip_vs_pressure.png`
Ugięcie i kąt końcówki przy rosnącym ciśnieniu w komorze L lub R (na sucho,
quasi-statycznie, NLGEOM). Odpowiedź prawie liniowa, ~1.2 mm/kPa: przy 20 kPa
**24 mm (16% L) i 9°**. Asymetria L/R 0.36%. Zbieżność siatki ciała stałego
(0.5/0.75/1.0 mm) – różnica < 0.5%. Zanim to zadziałało, trzeba było podzielić
komorę na cele (NOTES.md, etap 1).

### Etap 2 – sam płyn `e2_mesh_convergence.png`, `e2_vorticity_fine_0.png`
Sztywne ciało w napływie 0.2 m/s: opór w czasie, zbieżność siatki i rozkład
ciśnienia. Opór średni **0.13 N/m** (~2/3 ciśnieniowy, ~1/3 tarcie); zmiana
między siatką średnią i gęstą 1.0%, domena 1.5x zmienia wynik o 3.8%.
Cp = 1 w punkcie stagnacji na nosie. Zrzut wirowości: klasyczna ścieżka
wirów Kármána za tępą końcówką – ślad „oporowy”.

### Etap 3 – jawne vs niejawne `e3_explicit_vs_implicit.png`
Ogon pasywny w strumieniu. Niejawne (IQN-ILS): 3 s bez problemów, średnio
**4.7 iteracji sprzężenia** na okno, ogon drga w śladzie wirowym (~0.15 mm).
Jawne: siła w węźle końcówki zmienia znak i rośnie **×13 na okno** – po 2
oknach koniec. Z **Δt = 1 ms jest gorzej: ×40 na okno**. To efekt masy
dodanej: przy gęstości silikonu ≈ gęstości wody jawne sprzężenie jest
niestabilne dla każdego kroku czasowego (Causin, Gerbeau, Nobile 2005).

### Etap 4 – napęd w wodzie stojącej `e4_tip_angle_water_vs_dry.png`, `e4_thrust_cycle.png`
Kąt końcówki przy sinusie ciśnienia (P0 = 15 kPa, f = 1 Hz) w wodzie i na
sucho. **W wodzie amplituda jest większa** (28.3 vs 20.0 mm) i opóźniona
o ~71°. Woda dodaje masę i obniża częstotliwość własną ogona z 3.39 Hz (na
sucho) do okolic 1 Hz (etap 6), więc napęd 1 Hz trafia w rezonans w wodzie.
Siła wzdłużna oscyluje ±4 N/m, a średni ciąg wynosi **87 ± 99 mN/m** – nie
odróżnia się od zera. Jakość deformowanej siatki: `meshq_04-fsi-actuated_water.png`
(przy największym wychyleniu nieortogonalność 63°, skośność 4.1 – granica metody).

### Etap 5 – napęd + napływ `e5_force_vs_inflow.png`, `e5_vorticity_U0.05_0.png`, `e5_vorticity_U0.2_0.png`
Średnia siła X na całe ciało vs prędkość napływu (U = 0 to etap 4).
**Ogon daje opór netto**: +100, +292, +416 mN/m przy 0.05 / 0.1 / 0.2 m/s;
przy 0.2 m/s to ~3x więcej niż ciało sztywne. Równowaga (średnie Fx = 0)
wychodzi dopiero przy **U ≈ 0.02 m/s, czyli St ≈ 2.4** – daleko poza zakresem
ryb **St ≈ 0.2–0.4** (Taylor, Nudds, Thomas 2003, *Nature* 425:707–711;
Triantafyllou, Triantafyllou, Grosenbaugh 1993, *J. Fluids Struct.* 7:205–224).
Wniosek dla projektu: aktuator z dwiema jednolitymi komorami zgina ogon „w
jednej fazie” (fala stojąca) i ma tępą końcówkę – w tym modelu przepycha wodę
głównie na boki (siła boczna ±8–13 N/m) zamiast do tyłu. Kierunki do
sprawdzenia: fala biegnąca (komory z przesunięciem fazy wzdłuż ogona), ostra/
giętka płetwa ogonowa (NOTES.md, etap 5).

### Etap 6 – przegląd częstotliwości `e6_freq_sweep.png`
Amplituda i średni ciąg vs częstotliwość (woda stojąca, P0 = 15 kPa).
Amplituda: 20.7 / **28.3** / 14.8 / 3.1 mm przy 0.5 / 1 / 1.5 / 2 Hz –
**rezonans w wodzie ~1 Hz**, powyżej odpowiedź szybko maleje (dominuje masa
wody). Ciąg: 0 ± 5, 87 ± 99, −142 ± 61, −23 ± 32 mN/m – tylko przy 1.5 Hz
wynik jest istotny i jest to opór. Lekcja: częstotliwość pracy trzeba dobierać
względem rezonansu *w wodzie*, który dla miękkiego ogona leży ~3x niżej niż na
sucho.

### Zrzuty pola wirowości
`pvbatch tools/pv_snapshots.py <przypadek> <nazwa> [N]` – czerwony = wir
przeciwnie do zegara, niebieski = zgodnie. W ParaView ręcznie: otwórz
`fluid-openfoam/fluid-openfoam.foam`, pole `vorticity`, składowa Z, skala ±20 1/s.

---

## 7. Ograniczenia modelu

- **2D zamiast 3D** – brak efektów końcówek płetwy (wiry brzegowe), siły na
  metr rozpiętości; w 3D ciąg na jednostkę rozpiętości będzie mniejszy.
- **Przepływ laminarny** przy realnie przejściowym/turbulentnym Re (sekcja 3).
- **Głowa nieruchoma** – brak swobodnego pływania, odrzutu i kołysania głowy;
  „prędkość równowagi” z etapu 5 to tylko szacunek dla ryby na uwięzi.
- **Wymuszenie ciśnieniem**, a nie objętością (sekcja 3).
- **Materiał liniowo sprężysty** (z NLGEOM); silikon przy dużych odkształceniach
  jest hipersprężysty, bez tłumienia materiałowego.
- **Ograniczona amplituda** przez deformację siatki płynu (~15% L).
- **Komory 2D** – cele połączone w 3D kanałem; w przekroju ich nie widać.
- **Niezidentyfikowane parametry** – każda liczba to placeholder.

## 8. Jak to wykorzystać w projekcie

- **Porównania względne**, nie absolutne: wpływ geometrii płetwy (zwężenie,
  długość, liczba cel), sztywności (E), częstotliwości – na ciąg i amplitudę.
  Zmieniasz `tools/params.py`, generujesz przypadek `new-fsi-case.sh`, porównujesz.
- **Walidacja modeli MuJoCo/SOFA**: amplituda na sucho (etap 1/4 dry) i w wodzie
  (etap 4) oraz uśredniony ciąg (etapy 4–6) jako punkt odniesienia dla prostszych
  modeli oporu/masy dodanej.
- **Plan pomiaru na uwięzi w wannie**: głowa zamocowana na czujniku siły
  (tensometr 1-osiowy), napęd z zadanym ciśnieniem i częstotliwością, kamera z
  góry (kąt końcówki). Mierzyć: średnią siłę X w wodzie stojącej (porównanie z
  etapem 4/6), amplitudę końcówki na sucho i w wodzie, przy przepływie (kanał
  lub holowanie) – prędkość, przy której średnia siła ≈ 0 (etap 5). Z pomiarów
  zidentyfikować E, tłumienie i zastąpić placeholdery.
