"""Wspólna konfiguracja OpenModelica/OMPython dla skryptów projektu.

Ustawienia wydajności (zmierzone na RobotR3.FullRobot z MSL, 24 rdzenie):
- kompilacja kodu C równolegle na wszystkich rdzeniach (omc -n): 2.4 s vs 6.0 s na 1 rdzeniu,
- -O2 dla wygenerowanego kodu C: ok. 8% szybsza symulacja przy tym samym czasie kompilacji,
- -O3, -march=native, ccache: brak mierzalnego zysku, więc ich nie używamy.
Największą oszczędnością w przeglądach parametrów jest kompilacja RAZ
i zmiana parametrów przy uruchomieniu (override), a nie ponowne budowanie modelu.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = ROOT / "FishRobot"
RESULTS_DIR = ROOT / "results"
BUILD_DIR = ROOT / "build"

MSL_VERSION = "4.1.0"
NUM_PROCS = os.cpu_count() or 1

# Flagi kompilatora C dla kodu symulacji (omc dokleja je przez ${MODELICAUSERCFLAGS}).
os.environ.setdefault("MODELICAUSERCFLAGS", "-O2")

COMMAND_LINE_OPTIONS = [f"-n={NUM_PROCS}"]


def model_file():
    return PACKAGE_DIR / "package.mo"


def libraries():
    """Biblioteki do załadowania: MSL w ustalonej wersji + własny pakiet FishRobot.

    FishRobot podajemy jako bibliotekę (ścieżka *.mo -> loadFile w miejscu), a nie jako model_file:
    OMPython kopiuje model_file do katalogu roboczego, co psuje pakiet o strukturze katalogowej.
    """
    return [("Modelica", MSL_VERSION), model_file().as_posix()]


def make_system(model_name, work_dir=None, variable_filter=None, build=True):
    """Tworzy ModelicaSystemOMC (API OMPython 4.1; klasa ModelicaSystem jest przestarzała)."""
    from OMPython import ModelicaSystemOMC

    work_dir = Path(work_dir or BUILD_DIR / model_name)
    work_dir.mkdir(parents=True, exist_ok=True)
    mod = ModelicaSystemOMC(command_line_options=COMMAND_LINE_OPTIONS, work_directory=work_dir)
    mod.model(
        model_name=model_name,
        libraries=libraries(),
        variable_filter=variable_filter,
        build=build,
    )
    return mod
