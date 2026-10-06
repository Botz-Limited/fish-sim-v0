"""Eksport podukładu napędu ogona jako FMU 2.0 Co-Simulation -> results/fmu/TailDrive.fmu.

Eksportowany model: FishRobot.Subsystems.TailDriveFMU (bateria + mostek H + silnik + pompa + przewody
+ komory + zawory + ogon). Wejście: u. Wyjścia: theta, w_tail, tau_tail, p_L, p_R, i_motor.

Solver wewnątrz FMU: CVODE (flaga --fmiFlags=s:cvode). Domyślnie OpenModelica wkłada do FMU CS
jawną metodę Eulera z krokiem równym krokowi komunikacji. Przy sztywnej hydraulice (sztywne komory,
indukcyjność silnika) i kroku 2 ms taki FMU pada po ok. 0,1 s (sprawdzone: układ nieliniowy przestaje się
zbiegać). CVODE sam dobiera kroki wewnątrz każdego kroku komunikacji, a biblioteki sundials są pakowane do FMU.

Uwaga: FMU zawiera skompilowane binaria (binaries/linux64) i działa tylko na systemie zgodnym z tym,
na którym go zbudowano.

Uruchomienie:  .venv/bin/python scripts/export_fmu.py
"""

import shutil

import om_config as C

MODEL = "FishRobot.Subsystems.TailDriveFMU"
FMU_NAME = "TailDrive"
FMU_PATH = C.RESULTS_DIR / "fmu" / f"{FMU_NAME}.fmu"


def export():
    mod = C.make_system(MODEL, work_dir=C.BUILD_DIR / "fmu", build=False)
    if not mod.sendExpression('setCommandLineOptions("--fmiFlags=s:cvode")'):
        raise RuntimeError("omc nie przyjął flagi --fmiFlags=s:cvode")
    built = mod.convertMo2Fmu(version="2.0", fmuType="cs", fileNamePrefix=FMU_NAME)
    FMU_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(built.as_posix(), FMU_PATH)
    return FMU_PATH


def main():
    path = export()
    from fmpy import read_model_description

    md = read_model_description(str(path))
    io = [f"{v.name} ({v.causality})" for v in md.modelVariables if v.causality in ("input", "output")]
    print(f"FMU {md.fmiVersion} Co-Simulation: {path} ({path.stat().st_size / 1e6:.1f} MB)")
    print(f"  stany ciągłe: {md.numberOfContinuousStates}, solver: CVODE")
    print("  " + ", ".join(io))


if __name__ == "__main__":
    main()
