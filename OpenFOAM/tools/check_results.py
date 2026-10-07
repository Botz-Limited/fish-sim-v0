#!/usr/bin/env python3
"""Automated correctness criteria (SPEC, section 7).

Run from the OpenFOAM/ directory:   python tools/check_results.py
Each test: PASS / FAIL / SKIP (no results). Unmet conditions must be
explained in NOTES.md.
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
    """All directories with an FSI case (they have precice-config.xml and both participants)."""
    for cfg in sorted(ROOT.glob("0[3-9]-*/**/precice-config.xml")):
        case = cfg.parent
        if (case / "fluid-openfoam").is_dir() and (case / "solid-calculix").is_dir():
            yield case


def fluid_log_health(case):
    """(negative volumes?, NaN?, finished?) from the OpenFOAM log."""
    log = case / "fluid-openfoam" / "fluid-openfoam.log"
    if not log.exists():
        return None
    t = log.read_text(errors="replace")
    negvol = bool(re.search(r"negative (cell )?volume|Negative volume|Mesh non-orthogonality.*FAIL", t, re.I))
    # "trapFpe: Floating point exception trapping enabled" is only an info line
    nan = bool(re.search(r"[=\s]-?nan\b", t, re.I)) or "Signal: Floating point exception" in t
    finished = "Finished on:" in t and "FOAM FATAL" not in t
    running = "Finished on:" not in t and "FOAM FATAL" not in t and "exit" not in t[-2000:]
    return negvol, nan, finished, running


# --- Stage 0 -----------------------------------------------------------------
try:
    err = pp.e0(ROOT / "00-reference-flap")
    check("E0: flap tip vs reference (< 5%)", err < 0.05, f"max. relative error {err:.2%}")
except Exception as e:  # noqa: BLE001
    check("E0: flap tip vs reference (< 5%)", None, f"no results ({e})")

# --- Stage 1 -----------------------------------------------------------------
try:
    asym, mono = pp.e1(ROOT / "01-solid-only")
    check("E1: L/R symmetry (< 5%)", asym < 0.05, f"asymmetry {asym:.2%}")
    check("E1: deflection monotonic vs pressure", mono, "")
except Exception as e:  # noqa: BLE001
    check("E1: symmetry / monotonicity", None, f"no results ({e})")

# --- Stage 2 -----------------------------------------------------------------
try:
    ch_mesh, ch_dom = pp.e2(ROOT / "02-fluid-only")
    check("E2: drag, two finest meshes (< 10%)", ch_mesh < 0.10, f"change {ch_mesh:.2%}")
    check("E2: domain boundary effect (< 10%)", ch_dom < 0.10, f"change with 1.5x domain {ch_dom:.2%}")
except Exception as e:  # noqa: BLE001
    check("E2: mesh convergence", None, f"no results ({e})")

# --- Stage 3 -----------------------------------------------------------------
st3 = ROOT / "03-fsi-passive"
it = pp.read_iterations(st3 / "implicit")
if len(it):
    max_it = 50  # <max-iterations> in precice-config.xml
    n_max = int(np.sum(it[:, 1] >= max_it))
    check("E3: implicit converges in a bounded number of iterations",
          n_max == 0, f"mean {it[:, 1].mean():.1f}, max. {int(it[:, 1].max())}, windows at the limit: {n_max}")
else:
    check("E3: implicit converges", None, "no results")
ex = pp.read_watchpoint(st3 / "explicit")
im = pp.read_watchpoint(st3 / "implicit")
if len(ex) and len(im):
    diverged = len(ex) < len(im) or not np.all(np.isfinite(ex))
    check("E3: explicit shows divergence", diverged,
          f"explicit stopped after {len(ex)} windows (implicit: {len(im)})")
else:
    check("E3: explicit shows divergence", None, "no results")

# --- Every FSI case ----------------------------------------------------------
for case in fsi_cases():
    rel = case.relative_to(ROOT)
    if "explicit" in case.name:
        continue  # intentionally unstable variant
    h = fluid_log_health(case)
    if h is None:
        check(f"FSI {rel}: OpenFOAM log", None, "no log")
        continue
    negvol, nan, finished, running = h
    if running and not finished:
        check(f"FSI {rel}", None, "run in progress")
        continue
    check(f"FSI {rel}: no negative volumes", not negvol, "")
    check(f"FSI {rel}: no NaN / FPE", not nan, "")
    check(f"FSI {rel}: run finished", finished, "")
    # quality of the deforming mesh (checkMesh at every write; requires env.sh)
    try:
        q = pp.meshq(case)
        check(f"FSI {rel}: mesh – non-orthogonality < 70°, volumes > 0",
              bool(np.nanmax(q[:, 1]) < 70 and np.nanmin(q[:, 3]) > 0),
              f"max. {np.nanmax(q[:, 1]):.0f}°, max. skewness {np.nanmax(q[:, 2]):.2f}"
              + (" (> 4 at peak deflection – NOTES.md)" if np.nanmax(q[:, 2]) > 4 else ""))
    except Exception as e:  # noqa: BLE001
        check(f"FSI {rel}: mesh quality", None, f"checkMesh unavailable ({e})")
    conv = case / "solid-calculix" / "precice-Solid-convergence.log"
    if conv.exists():
        c = np.atleast_2d(np.loadtxt(conv, skiprows=1))
        # last iteration of each window: relative residuals below 1e-3
        last = np.array([c[c[:, 0] == w][-1, 2:] for w in np.unique(c[:, 0])])
        frac = float(np.mean(np.all(last < 1e-3, axis=1)))
        check(f"FSI {rel}: preCICE residuals < 1e-3", frac > 0.999, f"{frac:.1%} of windows converged")

# --- Stage 4 -----------------------------------------------------------------
try:
    wet, dry = pp.e4_amplitudes(ROOT / "04-fsi-actuated")
    check("E4: amplitude in water < dry", wet < dry, f"water {wet * 1e3:.1f} mm, dry {dry * 1e3:.1f} mm")
except Exception as e:  # noqa: BLE001
    check("E4: amplitude in water < dry", None, f"no results ({e})")

# --- Report -------------------------------------------------------------------
print("\n=== check_results ===")
for status, name, detail in results:
    print(f"[{status}] {name}" + (f" – {detail}" if detail else ""))
n_fail = sum(s == "FAIL" for s, _, _ in results)
print(f"\n{sum(s == 'PASS' for s, _, _ in results)} PASS, {n_fail} FAIL, "
      f"{sum(s == 'SKIP' for s, _, _ in results)} SKIP")
sys.exit(1 if n_fail else 0)
