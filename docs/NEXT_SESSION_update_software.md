# Next session: update outdated software and re-test

Source: `docs/research_EN-fact-check-2026-10-09.md` (fact-check of `research_EN.html`, 53 claims).
Already fixed (2026-10-09): OpenModelica licence line in EN + PL HTML.
Goal: bring tested versions up to date, re-run demos, then update the reports.

## Order of work (stop after each, commit per step)

### 1. MuJoCo 3.14.0 -> 3.15.0 (OUTDATED, ~15 min)
1. `pip install -U mujoco` in the MuJoCo env (branch `main`, dir `MuJoCo/`).
2. Re-run the demo and the live-GUI viewer; compare readouts with the old numbers.
3. If results hold, change "MuJoCo 3.14.0" to "3.15.0" in `research_EN.html:321` and `research_PL.html:321`. If not, report the diff and keep 3.14.0 with a note "3.15.0 released 5 Oct 2026, not tested".

### 2. CalculiX 2.20 vs 2.23 (NUANCED, ~10 min check)
1. Branch `openfoam`. The preCICE CalculiX adapter (v2.20.2) is built on CalculiX 2.20, so do NOT upgrade CalculiX alone.
2. Check https://github.com/precice/calculix-adapter/releases for a 2.23-based adapter.
3. If none: keep 2.20 and add to EN/PL line 688 "(2.23 exists; the preCICE adapter targets 2.20)".

### 3. PyElastica on Python 3.14 (NUANCED, ~10 min)
1. Branch `pyelastica`. PyElastica 1.0.0 declares Python 3.10-3.13 only.
2. Re-run the demo on Python 3.13 (numba 0.68 supports it). If it passes, switch the "tested" line (EN/PL line 505) to Python 3.13; otherwise annotate "3.14, not officially supported".

### 4. SOFA claims (UNCONFIRMED, ~20 min)
1. Branch `sofa`. List plugins loaded in the v26.06.00 binary; confirm SoftRobots is bundled, or reword to "SoftRobots plugin loaded".
2. Find the primary source for "model order reduction up to ~50x" (cite the MOR paper) or drop the number.
3. Link the real issue for the "v26.12-dev bug", or remove the sentence.
4. Check if v26.12 is released; if yes, retry it.

### 5. Wording fixes, no re-test (NUANCED)
- Stonefish added mass: "an automatically fitted sphere, cylinder or ellipsoid (ellipsoid in this demo)" - verify the demo's choice first.
- Stonefish "waves (GPU only)": docs say GPU FFT waves, body interaction "under development"; reword.
- MuJoCo added mass: say "per the source (`engine_passive.c`), only the gyroscopic part is applied; docs differ".
- MuJoCo flex bodies: mark as "observed", docs are silent.
- Strouhal glossary: "St ~0.2-0.4 (0.25-0.35 for most fish)", cite Taylor et al. 2003 and Triantafyllou et al. 1993.

### 6. Finish
1. Apply all edits to BOTH `research_EN.html` and `research_PL.html`.
2. `bash docs/build_pdf.sh` to rebuild the PDFs.
3. Update the verdicts in the fact-check file, then commit.

## Notes
- Each tool lives on its own branch (see root README). Switch branches before editing a demo.
- Repo-internal demo numbers (timesteps, mesh counts) were not fact-checked; they need re-running, not sourcing.
