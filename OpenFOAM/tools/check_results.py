#!/usr/bin/env python3
"""Automatyczne kryteria poprawności (SPEC, sekcja 7).

Uruchom z katalogu OpenFOAM/:   python tools/check_results.py
Każdy test: PASS / FAIL / SKIP (brak wyników). Niespełnione warunki muszą
być wyjaśnione w NOTES.md.
"""
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import postprocess as pp  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
results = []


def check(name, ok, detail):
    status = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
    results.append((status, name, detail))


def fsi_cases():
    """Wszystkie katalogi z przypadkiem FSI (mają precice-config.xml i oba uczestniki)."""
    for cfg in sorted(ROOT.glob("0[3-9]-*/**/precice-config.xml")):
        case = cfg.parent
        if (case / "fluid-openfoam").is_dir() and (case / "solid-calculix").is_dir():
            yield case


def fluid_log_health(case):
    """(ujemne objętości?, NaN?, zakończony?) z logu OpenFOAM."""
    log = case / "fluid-openfoam" / "fluid-openfoam.log"
    if not log.exists():
        return None
    t = log.read_text(errors="replace")
    negvol = bool(re.search(r"negative (cell )?volume|Negative volume|Mesh non-orthogonality.*FAIL", t, re.I))
    # "trapFpe: Floating point exception trapping enabled" to tylko informacja
    nan = bool(re.search(r"[=\s]-?nan\b", t, re.I)) or "Signal: Floating point exception" in t
    finished = "Finished on:" in t and "FOAM FATAL" not in t
    running = "Finished on:" not in t and "FOAM FATAL" not in t and "exit" not in t[-2000:]
    return negvol, nan, finished, running


# --- Etap 0 -----------------------------------------------------------------
try:
    err = pp.e0(ROOT / "00-reference-flap")
    check("E0: końcówka flapu vs referencja (< 5%)", err < 0.05, f"maks. błąd względny {err:.2%}")
except Exception as e:  # noqa: BLE001
    check("E0: końcówka flapu vs referencja (< 5%)", None, f"brak wyników ({e})")

# --- Etap 1 -----------------------------------------------------------------
try:
    asym, mono = pp.e1(ROOT / "01-solid-only")
    check("E1: symetria L/R (< 5%)", asym < 0.05, f"asymetria {asym:.2%}")
    check("E1: ugięcie monotoniczne vs ciśnienie", mono, "")
except Exception as e:  # noqa: BLE001
    check("E1: symetria / monotoniczność", None, f"brak wyników ({e})")

# --- Etap 2 -----------------------------------------------------------------
try:
    ch_mesh, ch_dom = pp.e2(ROOT / "02-fluid-only")
    check("E2: opór, dwie najgęstsze siatki (< 10%)", ch_mesh < 0.10, f"zmiana {ch_mesh:.2%}")
    check("E2: wpływ granic domeny (< 10%)", ch_dom < 0.10, f"zmiana przy domenie 1.5x {ch_dom:.2%}")
except Exception as e:  # noqa: BLE001
    check("E2: zbieżność siatki", None, f"brak wyników ({e})")

# --- Etap 3 -----------------------------------------------------------------
st3 = ROOT / "03-fsi-passive"
it = pp.read_iterations(st3 / "implicit")
if len(it):
    max_it = 50  # <max-iterations> w precice-config.xml
    n_max = int(np.sum(it[:, 1] >= max_it))
    check("E3: niejawne zbiega w ograniczonej liczbie iteracji",
          n_max == 0, f"średnio {it[:, 1].mean():.1f}, maks. {int(it[:, 1].max())}, okien z limitem: {n_max}")
else:
    check("E3: niejawne zbiega", None, "brak wyników")
ex = pp.read_watchpoint(st3 / "explicit")
im = pp.read_watchpoint(st3 / "implicit")
if len(ex) and len(im):
    diverged = len(ex) < len(im) or not np.all(np.isfinite(ex))
    check("E3: jawne pokazuje rozbieganie", diverged,
          f"jawne przerwane po {len(ex)} oknach (niejawne: {len(im)})")
else:
    check("E3: jawne pokazuje rozbieganie", None, "brak wyników")

# --- Każdy przypadek FSI ----------------------------------------------------
for case in fsi_cases():
    rel = case.relative_to(ROOT)
    if "explicit" in case.name:
        continue  # wariant celowo niestabilny
    h = fluid_log_health(case)
    if h is None:
        check(f"FSI {rel}: log OpenFOAM", None, "brak logu")
        continue
    negvol, nan, finished, running = h
    if running and not finished:
        check(f"FSI {rel}", None, "obliczenia w toku")
        continue
    check(f"FSI {rel}: brak ujemnych objętości", not negvol, "")
    check(f"FSI {rel}: brak NaN / FPE", not nan, "")
    check(f"FSI {rel}: obliczenia zakończone", finished, "")
    # jakość deformowanej siatki (checkMesh na każdym zapisie; wymaga env.sh)
    try:
        q = pp.meshq(case)
        check(f"FSI {rel}: siatka – nieortogonalność < 70°, objętości > 0",
              bool(np.nanmax(q[:, 1]) < 70 and np.nanmin(q[:, 3]) > 0),
              f"maks. {np.nanmax(q[:, 1]):.0f}°, skośność maks. {np.nanmax(q[:, 2]):.2f}"
              + (" (> 4 przy największym wychyleniu – NOTES.md)" if np.nanmax(q[:, 2]) > 4 else ""))
    except Exception as e:  # noqa: BLE001
        check(f"FSI {rel}: jakość siatki", None, f"checkMesh niedostępny ({e})")
    conv = case / "solid-calculix" / "precice-Solid-convergence.log"
    if conv.exists():
        c = np.atleast_2d(np.loadtxt(conv, skiprows=1))
        # ostatnia iteracja każdego okna: residua względne poniżej progu 1e-3
        last = np.array([c[c[:, 0] == w][-1, 2:] for w in np.unique(c[:, 0])])
        frac = float(np.mean(np.all(last < 1e-3, axis=1)))
        check(f"FSI {rel}: residua preCICE < 1e-3", frac > 0.999, f"{frac:.1%} okien zbieżnych")

# --- Etap 4 -----------------------------------------------------------------
try:
    wet, dry = pp.e4_amplitudes(ROOT / "04-fsi-actuated")
    check("E4: amplituda w wodzie < na sucho", wet < dry, f"woda {wet * 1e3:.1f} mm, sucho {dry * 1e3:.1f} mm")
except Exception as e:  # noqa: BLE001
    check("E4: amplituda w wodzie < na sucho", None, f"brak wyników ({e})")

# --- Raport -------------------------------------------------------------------
print("\n=== check_results ===")
for status, name, detail in results:
    print(f"[{status}] {name}" + (f" – {detail}" if detail else ""))
n_fail = sum(s == "FAIL" for s, _, _ in results)
print(f"\n{sum(s == 'PASS' for s, _, _ in results)} PASS, {n_fail} FAIL, "
      f"{sum(s == 'SKIP' for s, _, _ in results)} SKIP")
sys.exit(1 if n_fail else 0)
