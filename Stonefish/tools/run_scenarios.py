#!/usr/bin/env python3
"""Uruchamia wszystkie scenariusze aplikacją konsolową i rysuje wykresy.

    .venv/bin/python tools/run_scenarios.py            # wszystko (~2 min na 8 rdzeniach)
    .venv/bin/python tools/run_scenarios.py --only s4   # tylko przebiegi o nazwie zaczynającej się od "s4"
    .venv/bin/python tools/run_scenarios.py --plot-only # same wykresy z istniejących logów

Pełne logi (100 Hz, ~70 kolumn) trafiają do results/logs/ (poza gitem),
wykresy PNG i dane z wykresów (CSV) – do results/ (tools/plot_logs.py).
"""

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fishcfg import ROOT  # noqa: E402

CONSOLE = ROOT / "build" / "fish_console"
LOGS = ROOT / "results" / "logs"

# Przegląd częstotliwości (scenariusz 6): te same parametry, zmienia się tylko f.
SWEEP_FREQS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
TURN_BIASES_ML = [-3, -2, -1, 0, 1, 2, 3]


def runs():
    """(nazwa logu, plik konfiguracji, nadpisania --set)."""
    r = [
        ("s1_hover", "config/s1_hover.json", []),
        ("s1_righting", "config/s1_righting.json", []),
        ("s2_swim", "config/s2_swim.json", []),
        ("s2_swim_nolift", "config/s2_swim_nolift.json", []),
        ("s2_swim_libfriction", "config/s2_swim.json", ["hydro.skin_friction=library"]),
        ("s2_swim_libfriction_nolift", "config/s2_swim_nolift.json", ["hydro.skin_friction=library"]),
        ("s2_swim_locked", "config/s2_swim_locked.json", []),
        ("s4_depth", "config/s4_depth.json", []),
        ("s5_current", "config/s5_current.json", []),
        ("s5_current_heading", "config/s5_current_heading.json", []),
        ("t_internal", "config/t_internal.json", []),
    ]
    r += [(f"s3_turn_{b:+d}ml", "config/s3_turn.json", [f"rhythm.volume_bias={b}e-6"]) for b in TURN_BIASES_ML]
    # 60 s: przy niektórych częstotliwościach ryba rusza DO TYŁU, a potem zawraca (README, scen. 6)
    r += [(f"s6_sweep_{f:.2f}Hz", "config/s2_swim.json", [f"rhythm.freq={f}", "sim.duration=60"]) for f in SWEEP_FREQS]
    return r


def run_one(name, cfg, sets):
    cmd = [str(CONSOLE), cfg, "--out", str(LOGS / f"{name}.csv")]
    for s in sets:
        cmd += ["--set", s]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    last = (p.stdout.strip().splitlines() or [""])[-1]
    return name, p.returncode, last if p.returncode == 0 else p.stdout[-2000:] + p.stderr[-2000:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="prefiks nazwy przebiegu")
    ap.add_argument("--plot-only", action="store_true")
    ap.add_argument("-j", type=int, default=4, help="ile symulacji równolegle")
    a = ap.parse_args()
    if not a.plot_only:
        if not CONSOLE.exists():
            sys.exit(f"Brak {CONSOLE} – najpierw zbuduj projekt (README).")
        LOGS.mkdir(parents=True, exist_ok=True)
        todo = [r for r in runs() if not a.only or r[0].startswith(a.only)]
        failed = 0
        with ThreadPoolExecutor(a.j) as ex:
            for name, rc, msg in ex.map(lambda r: run_one(*r), todo):
                print(f"[{'OK' if rc == 0 else 'BŁĄD'}] {name}: {msg}")
                failed += rc != 0
        if failed:
            sys.exit(f"{failed} przebieg(ów) zakończyło się błędem")
    import plot_logs
    plot_logs.main()


if __name__ == "__main__":
    main()
