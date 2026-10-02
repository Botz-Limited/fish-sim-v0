# fish-sim-v0 / SOFA – miękki hydrauliczny ogon (SOFA + SoftRobots)

Edukacyjne demo FEM ogona robota-ryby. Specyfikacja: [SPEC_fish_sofa_demo.md](SPEC_fish_sofa_demo.md). **To nie jest skalibrowany model** – wszystkie parametry to placeholdery.

Stan: **etap 0 (instalacja + sprawdzenie API) zakończony.** Kolejne etapy: patrz spec, sekcja 8.

## Instalacja (Linux, sprawdzone na Fedorze 44)

| Co | Wersja / źródło |
|---|---|
| SOFA | **v26.06.00**, oficjalna binarka `SOFA_v26.06.00_Linux_Python3.12.zip` z [github.com/sofa-framework/sofa/releases](https://github.com/sofa-framework/sofa/releases) |
| SoftRobots, SoftRobots.Inverse, STLIB, SofaPython3 | **w oficjalnej binarce** (nie trzeba kompilować ani używać DefrostSofaBundle) |
| Licencje | SOFA: LGPL 2.1+ (`LICENSE-LGPL.md`); SoftRobots: **LGPL v3** (`plugins/SoftRobots/LICENSE`) |
| Python | **3.12** w środowisku conda `fishsofa` (systemowy Python 3.14 nie pasuje do binarki) |

```bash
# 1. SOFA poza repo (~230 MB do pobrania, ~800 MB po rozpakowaniu)
mkdir -p ~/sofa && cd ~/sofa
curl -LO https://github.com/sofa-framework/sofa/releases/download/v26.06.00/SOFA_v26.06.00_Linux_Python3.12.zip
unzip SOFA_v26.06.00_Linux_Python3.12.zip          # -> ~/sofa/SOFA_v26.06.00_Linux

# 2. Python 3.12 + zależności
conda create -n fishsofa python=3.12 numpy scipy pybind11 matplotlib pytest
conda run -n fishsofa pip install gmsh meshio

# 3. W każdej nowej powłoce (bash lub zsh), z katalogu repo:
source SOFA/scripts/env.sh
python SOFA/scripts/check_sofa.py           # kod 0 = wszystko jest
```

Inna lokalizacja SOFA: `SOFA_ROOT=/inna/sciezka source SOFA/scripts/env.sh`.

**Co trzeba było zrobić na Fedorze:** nic z `dnf`. Binarka jest budowana na Ubuntu, ale `ldd` pokazał tylko jeden brak: `libpython3.12.so.1.0`. Bierzemy go z condy. `env.sh` tworzy katalog `~/sofa/fishsofa-pylib/` z jednym dowiązaniem do tej biblioteki i dodaje go do `LD_LIBRARY_PATH`. Celowo nie dodajemy całego `$CONDA_PREFIX/lib`, bo wtedy `libstdc++` z condy przesłoniłaby systemową, co grozi błędami sterowników OpenGL w GUI. Odpowiednik ubuntowego `libopengl0` (`libglvnd-opengl`) był już zainstalowany.

## Uruchamianie

```bash
source SOFA/scripts/env.sh
python SOFA/scripts/check_sofa.py           # etap 0: nazwy komponentów i pól w tej wersji SOFA
python SOFA/scripts/probe_volume_growth.py  # etap 0: jak działa SurfacePressureConstraint (~2.5 min)
# GUI z przykładem SoftRobots (komora ciśnieniowa vs objętościowa):
$SOFA_ROOT/bin/runSofa -l SofaPython3 $SOFA_ROOT/plugins/SoftRobots/share/sofa/examples/SoftRobots/component/constraint/SurfacePressureConstraint/PressureVsVolumeGrowthControl.py
# to samo bez okna (np. 50 kroków):
$SOFA_ROOT/bin/runSofa -g batch -n 50 -l SofaPython3 <scena.py>
```

## Ustalenia z etapu 0

### Nazwy komponentów w SOFA v26.06 (`check_sofa.py`)

| Rola | Używamy | Uwagi |
|---|---|---|
| solver ograniczeń | `BlockGaussSeidelConstraintSolver` | `GenericConstraintSolver` **już nie istnieje**; jest też `NNCGConstraintSolver` |
| mocowanie | `FixedProjectiveConstraint` | `FixedConstraint` jeszcze działa (stara nazwa) |
| korekcja ograniczeń | `LinearSolverConstraintCorrection` | jest też `GenericConstraintCorrection` |
| solver liniowy | `SparseLDLSolver`, `template="CompressedRowSparseMatrixMat3x3d"` | bloki 3×3 są szybsze dla węzłów 3D (sugestia SOFA) |
| pozostałe | `FreeMotionAnimationLoop`, `EulerImplicitSolver`, `StaticSolver`, `TetrahedronFEMForceField`, `MeshMatrixMass`, `UniformMass`, `BoxROI`, `ConstantForceField`, `MeshVTKLoader`, `MeshGmshLoader`, `MeshSTLLoader`, `MeshOBJLoader`, `BarycentricMapping`, `SurfacePressureConstraint` | wszystkie są |

Pluginy: w Pythonie `SofaRuntime.importPlugin("Sofa.Component")` (meta-plugin ze wszystkimi standardowymi komponentami) + `"SoftRobots"`. W scenach: `RequiredPlugin` z polem **`pluginName`**, bo pole `name` jest przestarzałe.

### Jak działa `SurfacePressureConstraint` (`probe_volume_growth.py`)

Scena: pusty „królik” z przykładów SoftRobots, bez grawitacji.

1. **`valueType="volumeGrowth"`: `value` to przyrost CAŁKOWITY względem objętości początkowej** (`initialCavityVolume`), a nie przyrost na krok. Przy stałym `value = 40` zmierzone `cavityVolume − V0` = 40.000 od 0.25 s do 1.5 s. Zgadza się to z kodem SoftRobots (`dfree = V − V_initial`). Wniosek dla `hydraulics.py`: co krok zadajemy wprost `ΔV_L = V_prefill + V_p`, bez różniczkowania.
2. **Znak:** dodatnie `value` powiększa wnękę i daje dodatnie ciśnienie (przy siatce komory z przykładu; dla naszej siatki sprawdzi to test znaku w etapie 1–2, a w razie potrzeby jest pole `flipNormal`).
3. **Pole `pressure` to p·dt, a nie p.** Ten sam stan ustalony przy dt = 0.001 i 0.002 daje surowe `pressure` 2.2912 i 4.5824 (stosunek 2.000), a `pressure/dt` = 2291.2 w obu przypadkach. Powód: solver ograniczeń liczy **impuls** siły w kroku (λ = p·dt), nie siłę.
4. **W trybie `valueType="pressure"` wejście `value` też jest w jednostkach p·dt.** Zadanie `value = p` (bez ·dt) dało ciśnienie 1000× za duże przy dt = 1 ms i FEM wybuchł (NaN), nawet z rampą. `value = p·dt` odtwarza ten sam przyrost objętości (9.993 przy zadanym 10) przy obu dt.

Konsekwencje dla następnych etapów:
- `hydraulics.py` (zawór na Δp) i wszystkie wykresy ciśnienia muszą dzielić `pressure` przez `dt`,
- test „ten sam p → ugięcie ~1/E” (spec, sekcja 10) musi zadawać `value = p·dt`,
- w obu trybach `value` zmienia się rampą: przykład SoftRobots zadaje `volumeGrowth = 40` skokiem w pierwszym kroku i działa tylko dzięki dużemu tłumieniu.

Wydajność dla orientacji: królik z przykładu (dt = 1 ms) liczy się ~25 ms na krok na tej maszynie, ok. 40× wolniej niż czas rzeczywisty. SOFA sugeruje `ParallelTetrahedronFEMForceField` (plugin MultiThreading, maszyna ma 12 wątków) – do sprawdzenia w etapie 1.

### GUI

`runSofa` startuje pod Waylandem bez dodatkowych zmiennych. Domyślne GUI to **ImGui** (plugin SofaImGui). Przykład `PressureVsVolumeGrowthControl` działa: po **Animate** oba króliki się nadmuchują (sprawdzone ręcznie). Przy pierwszym uruchomieniu w logu pojawia się `[ERROR] [ImGuiGUIEngine] Cannot set window position/size from settings`. To tylko brak zapisanych ustawień okna, nieszkodliwe. Tryb `-g batch` działa (50 kroków przykładu w 5.9 s).
