# NOTES – dziennik diagnoz

Co się rozbiegło / nie działało, dlaczego i jak naprawione. Najnowsze na dole.

## Etap 1 – jedna długa komora "balonuje" (2026-10-06)

**Objaw.** Pierwsza wersja: jedna komora 100 mm × ~4–11 mm z każdej strony.
Rampa ciśnienia w komorze L: przy ~0.5 kPa końcówka przesunęła się o −20 mm
w osi x (skrócenie!) i +11 mm w y (zgięcie *w stronę* komory pod ciśnieniem),
potem `*ERROR: increment size smaller than minimum`.

**Diagnoza.** Ścianka zewnętrzna (3 mm) między końcami komory to belka o
rozpiętości 100 mm obciążona ciśnieniem. Ugięcie belki utwierdzonej:
w = p·l⁴ / (384·E·I), I = t³/12 (na metr głębokości).
Dla p = 500 Pa, l = 0.1 m, E = 3e5 Pa, t = 3 mm: w ≈ 0.19 m – ścianka wybrzusza
się jak membrana. Wybrzuszona ścianka ściąga końce komory (efekt mięśnia
McKibbena), więc strona pod ciśnieniem się *skraca*. W 3D prawdziwe aktuatory
temu zapobiegają żebrami (PneuNet) albo oplotem z włókien (demo SOFA).

**Naprawa.** Komora podzielona żebrami na cele (`N_CELLS`, `RIB` w
`tools/params.py`). Rozpiętość ścianki spada ze 100 mm do ~8.6 mm, czyli
ugięcie ∝ l⁴ spada ~18 000 razy. Cele są połączone kanałem poza płaszczyzną
przekroju (to samo ciśnienie).

## Etap 1 – zapadanie ścianki środkowej (2026-10-06)

**Objaw.** 6 cel po 15 mm, ścianka środkowa 2 mm: zgięcie już we właściwą
stronę, ale utrata zbieżności przy ~16 kPa, ugięcie końcówki tylko 11 mm.

**Diagnoza.** Ta sama formuła dla ścianki środkowej (t = 2 mm, l = 15 mm,
p = 16 kPa) daje w ≈ 10 mm – więcej niż wysokość sąsiedniej komory. Ścianka
zapada się do pustej komory po drugiej stronie, a model nie ma kontaktu.

**Naprawa.** 10 cel po 8.65 mm, żebra 1.5 mm, ścianka środkowa 3 mm
(w ≈ 0.35 mm). Wynik: odpowiedź prawie liniowa ~1.2 mm/kPa, 24 mm (16% L)
przy 20 kPa. Zbieżność traci się dopiero powyżej ~21 kPa, dlatego zakres
roboczy to 0–20 kPa (`P_MAX`).

## Etap 1 – zbieżność siatki ciała stałego (2026-10-06)

Ugięcie końcówki przy 20 kPa (komora L) dla rozmiaru elementu h:
h = 0.5 mm: 24.31 mm (8152 el.), 0.75 mm: 24.20 mm (3596 el.), 1.0 mm: 24.29 mm (2559 el.).
Rozrzut < 0.5%, więc przyjęto h = 1.0 mm – CalculiX jest najdroższą częścią
każdej iteracji sprzężenia, a mniej elementów = krótsze obliczenia FSI.

## Etap 0 – FPE w preCICE przy Eigen 5 (2026-10-06)

**Objaw.** Referencyjny perpendicular-flap padał po 1. kroku: `Floating point
exception` w procesach OpenFOAM, stos: `Eigen::internal::triSolveKernelLxK` <-
`RadialBasisFctSolver<CompactPolynomialC6>::solveConsistent` (mapowanie RBF).

**Diagnoza.** Arch dostarcza Eigen 5.0.1, a preCICE 3.4 wybiera Eigen 5, jeśli
jest dostępny. Nowy, wektoryzowany kernel rozwiązywania układu trójkątnego w
Eigen 5 podnosi flagę wyjątku zmiennoprzecinkowego, a OpenFOAM domyślnie
pułapkuje takie wyjątki (FOAM_SIGFPE) i przerywa obliczenia.

**Naprawa.** preCICE przebudowany z Eigen 3.4.0 (to wersja używana w
oficjalnych pakietach .deb preCICE). Pułapka FPE w OpenFOAM zostaje włączona,
bo przydaje się przy rozbieganiu sprzężenia (NaN zatrzymuje obliczenia od
razu). Alternatywa (gorsza): `export FOAM_SIGFPE=false`.

Po naprawie: perpendicular-flap zgodny z referencją tutorialu (maks. błąd
względny przemieszczenia końcówki 0.83%, średnio 2.01 iteracji sprzężenia na
okno vs 2.012 w referencji). Czas: 34 s (płyn 4 procesy MPI, CalculiX 2 wątki).

## Wydajność CalculiX – PARDISO zamiast SPOOLES (2026-10-06)

CalculiX to najdroższa część każdej iteracji sprzężenia (płyn ~20 ms/krok na
4 procesach, ciało stałe ~3–4 iteracje Newtona na przyrost). Test: 20
przyrostów dynamicznych, NLGEOM, 2559 el. C3D8I, czas na iterację Newtona:

| wątki | SPOOLES | PARDISO (MKL) |
|---|---|---|
| 1 | 158 ms | 123 ms |
| 2 | 130 ms | 81 ms |
| 4 | 121 ms (**błędny wynik!**) | 69 ms |

SPOOLES w wersji wielowątkowej z 4 wątkami dał inne (błędne) ugięcie
końcówki (−3.4 mm zamiast −7.9 mm) i zbiegał w innej liczbie iteracji –
znany problem SPOOLES MT. PARDISO daje identyczne wyniki dla 1/2/4 wątków.
Iteracyjne solvery CalculiX były ~15–20x wolniejsze.

Decyzja: `ccx_preCICE` budowany z PARDISO (MKL z `pip install mkl-devel` do
venv – bez sudo), 2 wątki. Stara wersja zostaje jako `ccx_preCICE_spooles`.

## Etap 3 – CalculiX rozbiega się już w 2. oknie FSI (2026-10-06)

**Objaw.** Pierwszy test FSI (ogon pasywny, U = 0.2 m/s): okno 1 zbiega
(23 iteracje sprzężenia), w oknie 2 CalculiX nie zbiega w pętli Newtona
("largest correction to disp 7.8e-2"), potem `corrupted double-linked list`.

**Diagnoza.** Eksport VTU z preCICE pokazał, że siły na interfejsie są
fizyczne (−1.4 N/m w oknie 1, −51 N/m w oknie 2 – skok to efekt masy dodanej:
przesunięcie ściany o 2e-5 m w jednym kroku daje duże ciśnienie). Test bez
preCICE: to samo obciążenie (−51 N/m jako siły węzłowe na Nsurface) w kroku
dynamicznym z NLGEOM również się rozbiega. Macierz testów:

| wariant | wynik |
|---|---|
| C3D8I + NLGEOM (oryginał) | rozbieżność |
| C3D8I bez NLGEOM | zbieżność |
| C3D8I + NLGEOM, siła 10x mniejsza | zbieżność, ale wolna |
| C3D8 + NLGEOM | zbieżność |
| SPOOLES zamiast PARDISO / ALPHA = −0.1 | rozbieżność (to nie solver) |

Winne są elementy z modami niezgodnymi (C3D8I – w CalculiX rozwinięte w
dodatkowe węzły bez masy) w połączeniu z NLGEOM i siłami węzłowymi; największe
poprawki pojawiały się właśnie w tych dodatkowych węzłach.

**Naprawa.** Elementy C3D8 (pełne całkowanie). Sprawdzenie blokady ścinania
na etapie 1 (20 kPa): C3D8I 24.28 mm, C3D8 24.14 mm (−0.6%), C3D8R 24.63 mm.
Różnica pomijalna, a C3D8 jest ~2x szybszy.

## Etap 3/4 – rozbieganie CalculiX w dłuższych przebiegach (2026-10-06)

**Objaw.** Etap 3 niejawny padał w oknie 44 (t = 0.11 s): w jednej iteracji
sprzężenia siła na interfejsie skacze ~1000x, Newton w CalculiX nie zbiega
(rezydua 77 kN w jednym węźle), potem `corrupted double-linked list`.

**Diagnoza.**
1. Testy akceleracji na krótkim przebiegu (0.2 s): IQN-ILS jak w tutorialu
   (QR2 1e-2, relaksacja 0.5) – pad w oknie 66; IQN-IMVJ – pad w oknie 58.
   Zmiana akceleracji nie pomaga.
2. Kluczowy test: etap 4 "na sucho" (sam CalculiX, bez wody i bez preCICE)
   też się rozbiegł przy t = 1.58 s – liczba iteracji Newtona skakała 4/9/4/9.
   Problem jest więc w dynamice samego ciała stałego: schemat Newmarka bez
   tłumienia (ALPHA = 0) + NLGEOM + bardzo miękki materiał – mody osiowe
   (~30 Hz, okres ~12 kroków) nie są tłumione i "rozhuśtują" iteracje.

**Naprawa.** `*DYNAMIC, ALPHA=-0.2` (schemat HHT). Krótki test FSI: 79/79
okien bez błędów; "na sucho": pełne 4 s (wcześniej pad przy 1.58 s).
Tłumienie numeryczne HHT ∝ (ω·Δt)³: dla 1 Hz i Δt = 2.5 ms praktycznie zerowe,
więc nie zmienia odpowiedzi w paśmie aktuacji. Prawdziwy silikon i tak ma
tłumienie materiałowe, którego model nie zawiera.

## Etap 3 – wynik: jawne vs niejawne (2026-10-06)

- **Niejawne** (parallel-implicit + IQN-ILS): 1200 okien (3 s) w 592 s,
  średnio 4.7 iteracji sprzężenia na okno, maks. 17 (tylko na starcie, zanim
  IQN zbierze historię). Ogon drga w śladzie wirowym, amplituda rośnie do ~0.15 mm.
- **Jawne** (serial-explicit): siła w węźle końcówki zmienia znak i rośnie
  ×13 na okno (Δt = 2.5 ms); po 2 oknach CalculiX się rozbiega.
- **Jawne z Δt = 1 ms: ×40 na okno** – mniejszy krok czasowy pogarsza sprawę.
  To klasyczny wynik dla niestabilności masy dodanej (Causin, Gerbeau, Nobile
  2005, CMAME 194): przy gęstości ciała ~ gęstości płynu schemat jawny jest
  niestabilny dla każdego Δt, a czynnik wzmocnienia rośnie, gdy Δt maleje.

## Etap 4 – pułapka w postprocessingu: siły z każdej iteracji (2026-10-06)

**Objaw.** Wykres siły Fx ogona: oscylacje ±300 N/m z częstotliwością
~20–25 Hz w paczkach co pół okresu, „ciąg” 5.4 N/m – 40x więcej niż opór
całego ciała przy 0.2 m/s z etapu 2.

**Diagnoza.** Widmo dawało nieskończone częstotliwości (dzielenie przez Δt = 0):
w `postProcessing/forces*/0/force.dat` każda chwila występuje kilka razy.
Przy sprzężeniu niejawnym adapter cofa OpenFOAM do punktu kontrolnego i krok
jest liczony ponownie w każdej iteracji sprzężenia – a funkcja `forces`
zapisuje wiersz za każdym razem, także dla niezbieżnych iteracji.

**Naprawa.** `read_forces()` zostawia ostatni wiersz dla każdej chwili
(= wartość zbieżna). Po poprawce: siła ±3.7 N/m, bez oscylacji 20 Hz.
Druga poprawka: ciąg liczony z siły na **całe** ciało (głowa + ogon) – sam
ogon nie jest powierzchnią zamkniętą, więc jego Fx zależy od poziomu
odniesienia ciśnienia.

## Etap 4 – w wodzie amplituda WIĘKSZA niż na sucho (2026-10-06)

Przy f = 1 Hz, P0 = 15 kPa: na sucho 20.7 mm, w wodzie 26.5 mm, opóźnienie
fazy w wodzie 62° (na sucho ~0°). Spec zakładał „woda tłumi”, ale to zależy
od częstotliwości względem rezonansu:
- na sucho f₁ = 3.39 Hz (CalculiX, `*FREQUENCY`), więc 1 Hz to praca
  quasi-statyczna (wzmocnienie ~1.1),
- masa dodana obniża częstotliwość własną; szacunek 2D (masa dodana ~6x masy
  ogona): f₁,woda ≈ 3.39/√7 ≈ 1.3 Hz – napęd 1 Hz jest blisko rezonansu w wodzie,
  więc amplituda rośnie, a faza przesuwa się w stronę 90°.
Woda jednocześnie tłumi (energia odpływa w ślad wirowy) i „opóźnia” ruch –
widać to w fazie. Przegląd częstotliwości (etap 6) pokazuje przebieg.

Średni ciąg w wodzie stojącej jest mały i po 3 okresach jeszcze się nie
ustalił (średnie po okresach: −12.6, −467.5, −91.9, +78.4 mN/m – duży ciąg
od wiru startowego, potem zanik). Dlatego etap 4 i 6 liczone ponownie na
8 okresach.

## Etap 4 – jakość deformowanej siatki płynu (2026-10-06)

`python tools/postprocess.py meshq 04-fsi-actuated/water` (checkMesh na każdym
zapisie): przy największym wychyleniu (kąt końcówki 13.5°, ugięcie 26.5 mm =
18% L, t ≈ 1.9 s) maks. nieortogonalność 63° (próg checkMesh 70°), maks.
skośność 4.1 (próg 4), min. objętość komórki spada z 3.1e-7 do 1.7e-7 m³ –
ujemnych objętości brak. To praktyczna granica deformacji siatki metodą
Laplace'a dla tej geometrii: większe amplitudy (wyższe P0 albo bliżej
rezonansu) wymagają przesiatkowania albo siatek overset.

## Etap 5 – napęd daje opór netto; równowaga dopiero przy U ≈ 0.02 m/s (2026-10-07)

Średnie Fx całego ciała (okresy od t = 2 s, ± błąd standardowy średniej z okresów):
U = 0 (etap 4): −87 ± 99, U = 0.05: +100 ± 32, U = 0.1: +292 ± 14,
U = 0.2: +416 ± 18 mN/m. Dla porównania sztywne ciało przy 0.2 m/s: +132 mN/m.

- Machanie **zwiększa** opór ~3x (przy 0.2 m/s): część ciśnieniowa 338 vs 86
  mN/m, tarcie 66 vs 44 mN/m (cieńsza warstwa przyścienna przy ruchu bocznym –
  efekt Bone'a–Lighthilla).
- Siła boczna ma odchylenie std. 8–13 N/m, czyli ~30x więcej niż średnia siła
  wzdłużna: ogon głównie „przepycha” wodę na boki.
- Równowaga (średnie Fx = 0) z interpolacji: U ≈ 0.023 m/s, St ≈ 2.4 – daleko
  poza zakresem ryb 0.2–0.4. Niepewność duża: w wodzie stojącej rozrzut
  średnich z okresów wynosi ±230 mN/m.

**Interpretacja (hipoteza, nie do końca sprawdzona).** Aktuator z dwiema
jednolitymi komorami zgina ogon jak wspornik: cały ogon wychyla się w jednej
fazie (fala stojąca), końcówka jest tępa (10 mm), a sztywna głowa jest
nieruchoma. Ryby wytwarzają ciąg falą biegnącą wzdłuż ciała i ostrą, giętką
płetwą ogonową z odpowiednią fazą wychylenia i kąta natarcia. Kierunki do
sprawdzenia w modelu: komory sterowane z przesunięciem fazy wzdłuż długości
(fala biegnąca), cieńsza/ostra końcówka albo osobna giętka płetwa ogonowa,
wyższa częstotliwość. Ograniczenia modelu (2D, laminarnie) też mogą zawyżać
opór.

Wizualizacja: przy U = 0.2 m/s ślad to pojedynczy rząd wirów blisko osi; przy
U = 0.05 m/s (St ≈ 1.1) ślad jest asymetryczny i odchylony w dół – typowe dla
bardzo dużych St.

Poprawka po drodze: `pv_snapshots.py` kolorował moduł wektora wirowości (same
dodatnie wartości) – trzeba jawnie ustawić `VectorMode = "Component"`.

## Etap 6 – rezonans w wodzie ~1 Hz (2026-10-07)

Amplituda końcówki (średnia z połówek rozpiętości w 2 ostatnich okresach):
0.5 Hz: 20.7 mm, 1 Hz: 28.3 mm, 1.5 Hz: 14.8 mm, 2 Hz: 3.1 mm. Maksimum przy
1 Hz – rezonans w wodzie jest niżej niż szacowane wcześniej 1.3 Hz, czyli
masa dodana w 2D to ~10x masa ogona ((3.39/1)² − 1), nie ~6x.
Średni ciąg (okresy od t = 2/f): 0 ± 5, 87 ± 99, −142 ± 61, −23 ± 32 mN/m –
istotny jest tylko opór przy 1.5 Hz.

Uwaga do definicji: amplituda liczona wcześniej jako połowa rozpiętości w
jednym ostatnim okresie (etap 4: 25.8 mm), teraz średnia z 2 ostatnich okresów
(28.3 mm) – ta sama definicja dla wody i „na sucho” i we wszystkich etapach.
