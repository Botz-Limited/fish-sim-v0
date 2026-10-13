# Handoff: constant pump + ±1 valve migration (2026-10-13)

Plan: `~/.claude/plans/pompa-ma-sta-e-obroty-fancy-clover.md`
Specs given to branch agents (copied here): `valve_model_spec.md`, `valve_dwell_addendum.md` (UPDATE line at top wins).
User wants ADHD output mode (`/i-have-adhd:i-have-adhd`). Commit only when asked. Work in parallel where possible.

## Model (decided)

- Constant-speed pump `Q_const`. Directional valves have only two states, s = ±1 (no closed state). Flow: dQ/dt = (s·Q_const − Q)/τ_valve.
- Hysteresis relay on e = V_ref − V_p with δ = 1 ml, plus a minimum dwell `valve_min_dwell = 0.2` s (the valve switches at most ~5 times/s).
- τ_valve = 0.02 s. Q_const = old Q_max **for now** (see open decision 1). All values are PLACEHOLDER.
- `tail_freq_min = 1.5` Hz (the user raised it from 1.25: extra switches made the turn jerky). `tail_freq_max = 2.5` Hz = 1/(2·dwell). Frequency is clamped to this range; sweeps run 1.5…2.5 Hz in 0.25 steps.
- OpenModelica keeps full electrics, with 2× 3/2 valves.

## Branch status (ALL UNCOMMITTED)

Worktrees: `../fish-sim-v0-wt/<branch>`. Python venv: `fish-sim-v0/.venv` (run from `MuJoCo/` with `PYTHONPATH=$PWD`).

| Branch | State | Tests | Notes |
|---|---|---|---|
| main / MuJoCo | done | 44 passed | reference; s1 23.1 cm/s; sweep 24.2/24.6/23.1/21.1/18.9 cm/s at 1.5…2.5 Hz; 2 switches/cycle |
| stonefish | done | pass | 2.00 switches/cycle, 32–34 cm/s, Δp ≤ 20 kPa; GUI screenshot is stale; s4 noise is unseeded |
| openmodelica | done, needs OK | 23 models pass | 2.7 switches/cycle at 1.5 Hz (loaded flow 33 < 37.7 ml/s needed); ReliefValveDemo redesigned (A_V 4 ml, bias 14 ml, Δp 52 kPa) |
| pyelastica | ported, **broken physics** | 23 pass | Q 160 ml/s × 0.2 s = 32 ml = 4·A_V, so the valve is a fixed 2.5 Hz square wave; speed 54–58 cm/s flat; stage 4 turns 120° |
| sofa | ported, **broken physics** | 46 pass, 4 xfail | Q 250 ml/s × 0.2 s = 50 ml > 2·A_V (34); \|V_p\| 24–27 ml steady, 43.7 ml at start > V_prefill 20 ml; long stage 4–6 runs (~2 h) not run; flapping test loosened to lagged correlation |
| openfoam | code done, results stale | 5/5 | cases moved to 1.5/1.75/2/2.5 Hz (stage 6 `git mv` staged); FSI rerun impossible here (no gmsh/preCICE/CalculiX/OpenFOAM v2606); old CSVs restored from HEAD; untracked backup `OpenFOAM/results/old_sine/`; runner `OpenFOAM/logs/run_sequential_valve.sh` |

## Open decisions (asked, not answered)

1. **Pump flow rule.** Recommended: Q_const ≈ 7.5·A_V on every branch (MuJoCo ratio 60/8), so the valve switches twice per cycle across 1.5–2.5 Hz → PyElastica 60 ml/s, SOFA ~130 ml/s. This changes the earlier "Q_const = old Q_max" rule. Alternatives: per-branch fixes (PyElastica open-loop square wave; SOFA smaller A_V / higher prefill, which buckling limits to ~22 ml); or accept and document.
   - SOFA risk: even at 130 ml/s the start-up stroke may reach ~26 ml (estimate). It may need a gentler start rule for the relay (it currently starts at s=+1 and flips after ~16 ms, then holds 0.2 s).
2. **OpenModelica:** accept 2.7 switches/cycle at 1.5 Hz, and the ReliefValveDemo redesign (recommend yes to both).
3. **OpenFOAM rerun location:** A build toolchain here (needs sudo, Arch script on Fedora) / B podman v2512 image / C original machine (recommended; commit the openfoam branch first).

## Remaining work after decisions

1. Apply decision 1 on pyelastica and sofa; rerun their tests and scenarios (SOFA stages 4–6 ≈ 2 h: `source scripts/env.sh && python scripts/run_stage{4,5,6}.py`).
2. Fix up OpenModelica if decision 2 is no.
3. Rerun OpenFOAM stages 4–6 (~4 h) wherever decision 3 says.
4. Update docs `research_PL/EN.html`, rebuild PDFs, fact-check.
5. Commit each branch (only when the user asks; attribution `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`). Optionally delete `OpenFOAM/results/old_sine/`.
