"""Szybkie wielokrotne uruchamianie skompilowanego modelu (przeglądy parametrów).

Model kompilujemy raz (om_config.make_system), potem odpalamy gotowy plik wykonywalny
równolegle z różnymi parametrami. Bez ponownej kompilacji i bez sesji omc na każde uruchomienie.

Uwaga (OpenModelica 1.27.1): -override zmienia parametry modelu, ale NIE ustawienia eksperymentu
(stopTime, tolerance, stepSize) – te podmieniamy w kopii pliku <model>_init.xml i podajemy przez -f.
"""

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import om_config as C
from om_results import read_mat


def compile_model(model):
    """Kompiluje model i zwraca katalog z plikiem wykonywalnym."""
    mod = C.make_system(model)
    return Path(mod.getWorkDirectory())


def run(work_dir, model, tag, params=None, experiment=None, names=()):
    """Jedno uruchomienie: params -> -override, experiment -> atrybuty DefaultExperiment w _init.xml."""
    work_dir = Path(work_dir)
    xml = (work_dir / f"{model}_init.xml").read_text()
    for key, value in (experiment or {}).items():
        xml, n = re.subn(rf'(\b{key}\s*=\s*")[^"]*(")', rf"\g<1>{value}\g<2>", xml, count=1)
        if n != 1:
            raise KeyError(f"brak atrybutu {key} w _init.xml")
    xml_path = work_dir / f"run_{tag}_init.xml"
    res_path = work_dir / f"run_{tag}_res.mat"
    xml_path.write_text(xml)
    cmd = [str(work_dir / model), f"-f={xml_path.name}", f"-r={res_path.name}", "-lv=-LOG_SUCCESS"]
    if params:
        cmd.append("-override=" + ",".join(f"{k}={v}" for k, v in params.items()))
    proc = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"symulacja {tag} nie powiodła się:\n{proc.stdout[-2000:]}")
    return read_mat(res_path, names)


def run_many(work_dir, model, cases, names, workers=C.NUM_PROCS):
    """cases: lista (tag, params, experiment). Uruchamia równolegle, zwraca wyniki w tej samej kolejności."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run, work_dir, model, tag, p, e, names) for tag, p, e in cases]
        return [f.result() for f in futures]
