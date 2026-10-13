# Handoff 2: constant pump + ±1 valve, session of 2026-10-13 (evening)

Continues `HANDOFF.md` (read it for the model; decisions 1-3 are now applied, see below).
User wants ADHD output mode (`/i-have-adhd:i-have-adhd`). **Commit is authorised once SOFA finishes** (see "Commit" below).

## Decisions applied (from HANDOFF.md)
1. Q_const ≈ 7.5·A_V on every branch: MuJoCo/Stonefish/PyElastica 60 ml/s, SOFA 100 ml/s (A_V 13 ml). f_track ≈ 1.2 Hz < tail_freq_min 1.5 Hz, so the valve switches exactly 2×/cycle (OpenModelica 2.7× at 1.5 Hz).
2. OpenModelica 2.7 switches/cycle + ReliefValveDemo redesign accepted.
3. OpenFOAM rerun goes to the original machine (not here).

## Branch state (all UNCOMMITTED, worktrees in `../fish-sim-v0-wt/<branch>`)
| Branch | State |
|---|---|
| main / MuJoCo | done. s1 23.1 cm/s, sweep 24.2/24.6/23.1/21.1/18.9 cm/s at 1.5…2.5 Hz |
| stonefish | done. s2 34.5 cm/s, sweep 31.6-34.4 cm/s, 2.0 switches/cycle |
| openmodelica | done. SwimForward 14.3 cm/s at 1.5 Hz, sweep 13.3-14.9 cm/s, 1.76-1.78 W |
| pyelastica | fixed this session: Q_const 60 ml/s, 23 tests pass, e4 37.0 cm/s, results regenerated, new `free_swim` video rendered |
| sofa | config + tests fixed (Q 100 ml/s, A_V 13 ml, 46 pass, 3 xfail left). **Stages 4→5→6 are running in the background** (`run_stage4 && run_stage5 && run_stage6`, ≈2 h total; stage 4 finished 18:50, stage 5 was running, stage 6 next). Check `pgrep -af run_stage` and `SOFA/results/` |
| openfoam | code done, results stale (FSI rerun impossible here). Untracked backup `OpenFOAM/results/old_sine/` (optionally delete). Runner `OpenFOAM/logs/run_sequential_valve.sh` |

## Left to do, in order
1. **Wait for SOFA stages 4-6** (`SOFA/results/s4_*`, `s5_*`, `s6_*`, `sofa_freq_sweep.png`).
2. **SOFA README** (`sofa` worktree, `SOFA/README.md`): still stale at ~lines 306, 332, 373, 418, 430 (A_V 17 ml, Q 250 ml/s, 2.34 Hz). Update to A_V 13 ml, Q 100 ml/s, f_track ≈ 1.2 Hz, and the new stage 4-6 numbers. Check `scripts/run_stage6.py` / `render_video.py` text too.
3. **Notion pages**: put the SOFA numbers in (tables, `s4 flapping in air`, `s5 water vs air`, `s6 sweeps`, sweep caption, remove the "earlier sine-pump model; rerun pending" notes in the SOFA section and the OpenFOAM stage-6 note stays until the rerun). Replace the SOFA sweep plot and the SOFA videos (see Notion below).
4. **Commit** (when SOFA is done): per worktree, see "Commit".
5. HTML docs (`docs/research_EN.html`, `docs/research_PL.html`) and PDFs were NOT updated this session (user decided "docs" = the Notion pages). Ask the user whether to port the changes to the HTML and rebuild PDFs (`docs/build_pdf.sh`). The numbers are in this file and in the Notion pages.

## Commit (authorised after SOFA finishes)
- One commit per branch/worktree: `main` (MuJoCo, repo root), `stonefish`, `openmodelica`, `pyelastica`, `sofa`, `openfoam` (worktrees `../fish-sim-v0-wt/<branch>`). Check `git status` in each first; do not commit venvs (`pyelastica/.venv` is gitignored).
- `openfoam`: stage 6 `git mv` is already staged; results are stale (old sine-pump CSVs restored from HEAD), mention that in the message; do not commit `OpenFOAM/results/old_sine/`.
- `.scratch/` in the main repo is untracked: do not commit it unless the user says so.
- Commit message ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Do not push.

## Notion pages (the "docs")
- EN: `3f7c306d-b18b-81fe-a765-e1a4bd84e937` (Robot Fish Simulator Survey (EN)), PL: `3f7c306d-b18b-8185-b334-d06e16e0c0be` (Przegląd symulatorów ryby-robota (PL)). Parent: `3f7c306d-b18b-81268716f0342700d745`.
- Text edits work with `notion-update-page` + `update_content` (exact `old_str`). Careful: LaTeX in Notion looks like `$`Q_\mathrm{max}`$`, not the HTML form; always grep the fetched text (saved by the fetch tool to a file) first.
- **Images/videos cannot be matched or deleted with `update_content`.** New media: `notion-create-file-upload` → `curl -X POST <upload_url> -H "authorization: Bearer <token>" -F file=@file` → insert `<image src="file-upload://ID"></image>` / `<video src="file-upload://ID"></video>` with `update_content` anchored on the caption text.
- Done this session (both pages): all pump/valve text + numbers for MuJoCo, Stonefish, PyElastica, OpenModelica, comparison table, energy figure and caption; new images: MuJoCo sweep (EN: English labels, PL: Polish), PyElastica free-swim plot, energy bar (EN/PL); new videos: MuJoCo, Stonefish, OpenModelica, PyElastica; new screenshots: MuJoCo GUI, Stonefish hydro + GUI, OpenModelica diagram + plot.
- **Old media: the user deletes them by hand. Do NOT rewrite whole pages** (user decision). Old+new pairs may still exist on the pages; just insert new media next to the caption as before and tell the user which old one to delete. Verify nothing else is Polish on the EN page: the `sofa_flapping.mp4` video has Polish labels, see below.
- Text still stale in Notion (found while reading, not yet fixed): PyElastica `e6 depth` row says "settles in 9.9 s, overshoot 23 cm" → should be **9.5 s, 22 cm**; OpenModelica Inputs "Control" row says "CPG amplitude 0.8, 1.5 Hz" → now V_ref amplitude 4 ml, 1.5-2.5 Hz, relay δ 1 ml, dwell 0.2 s. Same on the PL page.
- SOFA media still old (A_V 17 ml model): `sofa_freq_sweep.png`, `sofa_gui_replay.mp4`, `sofa_flapping.mp4` (**labels in Polish**, needs an English version for the EN page, Polish for PL), `sofa_gui.jpg` (still fine). OpenFOAM media stay as they are until the rerun.

## Recording (headless X on Wayland, XWayland :99)
Scripts were saved in `.scratch/constant-pump-valve/recording/` (paths inside point to the old scratchpad: adapt `S=`). Latest recorded media in `recording/latest_media/`.
- Start: `Xwayland :99 -fullscreen -output DP-2 -hidpi -noreset -nolisten tcp &` then `DISPLAY=:99 xrandr --output XWAYLAND0 --mode 2560x1440` (or 1920x1080 for OMEdit). Stop with `pkill -f '^Xwayland :99'`.
- `xact.py` needs `python-xlib` in a venv (`python3 -m venv xvenv && xvenv/bin/pip install python-xlib`); it fakes clicks/keys/resize on :99.
- MuJoCo: `mj_video.sh SECONDS OUT.mp4` (uses `mj_record.py`, args `<MuJoCo dir> SEC no 0.5 200`; with `ui` as 3rd arg for the GUI-panel screenshot). Run with `WAYLAND_DISPLAY=none-xx XDG_SESSION_TYPE=x11 DISPLAY=:99`.
- Stonefish: `sf_video2.sh` (`build/fish_gui config/s3_turn.json --window 2560x1440 --speed 0.5`, clicks the "Hydrodynamics" checkbox at 30 s and 40 s); screenshots are frames cut from the raw video.
- OpenModelica: `omedit.sh` (podman `docker.io/openmodelica/openmodelica:v1.27.1-gui`, needs MSL 4.1.0 installed into the container HOME once: `installPackage(Modelica, "4.1.0+maint.om", exactMatch=true)` with `omc`), then `om_video.sh` (Modeling tab → Simulate → plot `surge.U`). Window is 1280×720 at +0,0.
- SOFA GUI: old recipe in `sofa_gui.sh.OLD` (runSofa replay of `recordings/*.npz`, `FISHSOFA_SPEED=0.5`); needs the new stage-6 recording first. `flapping.mp4` comes from `SOFA/scripts/render_video.py` (Polish labels in the repo; make an EN copy for the EN page).
- PyElastica video: `../fish-sim-v0-wt/pyelastica/fish_elastica_demo/.venv`-less, use `../.venv/bin/python scripts/animate.py --fps 25 --speed 0.5 --out X.mp4 --size 2560x1440` (≈3 min), then `ffmpeg -c:v libx264 -preset slow -crf 27 -pix_fmt yuv420p -movflags +faststart`.
- Notion single upload limit 20 MiB: encode videos with crf 26-27 (MuJoCo/Stonefish ≈7 MB).

## Gotchas
- SOFA runs through conda env `fishsofa` + `source scripts/env.sh`. PyElastica tests: `../.venv/bin/python -m pytest` in its worktree (own venv).
- SOFA xfail left: first one-sided flap stroke (−16.5 ml) and the flapping-both-ways-from-the-start test; no gentler start rule.
- OpenModelica: 2.7 switches/cycle at 1.5 Hz is expected (loaded flow 33 < 37.7 ml/s needed).
- Memory index entry: `constant-pump-valve-model.md`.
