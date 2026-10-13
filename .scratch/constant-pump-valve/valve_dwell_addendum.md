**UPDATE (user decision): tail_freq_min = 1.5 Hz on ALL branches** (not 1.25 / not the per-branch rule below). At 1.25 Hz the valve still adds 1–2 extra switches per cycle and the per-cycle mean V_p jumps 0.1…5.1 ml for a 3 ml bias; from 1.5 Hz there are clean 2 switches/cycle. Sweeps: 1.5…2.5 Hz.

# Addendum to valve_model_spec.md — valve rate limit + frequency range (user decision 2026-10-13)

The real valve can switch at most ~5 times per second. Consequences (reference: MuJoCo on `main`,
see `MuJoCo/fishsim/controllers.py` TailRhythm and `MuJoCo/fishsim/config.py`):

1. New config params (all PLACEHOLDER-style comments like the others):
   - `valve_min_dwell = 0.2` [s] — minimum time between valve switches.
   - `tail_freq_min` [Hz] — lowest allowed tail frequency. MuJoCo: 1.25 Hz (just above
     f_track = Q_const/(2π·A_V) ≈ 1.19 Hz). Below f_track the relay must chatter many times per
     cycle to track V_ref, which the valve can't do and which excites tail modes.
     Per-branch: use max(1.25, round-up-to-0.25 of f_track for that branch), but never above tail_freq_max.
     If f_track ≥ tail_freq_max (e.g. SOFA f_track≈2.34, PyElastica ≈3.2 Hz), keep tail_freq_min = 1.25 and
     report that in this branch the low end still has >2 switches/cycle (dwell-limited) — do NOT change Q_const.
   - `tail_freq_max = 2.5` [Hz] = 1/(2·valve_min_dwell): 2 switches per cycle, each state ≥ 0.2 s.
2. Relay controller change (exact MuJoCo code):
   ```python
   self.t_switch = -np.inf            # in __init__ and reset()
   def _clamp(self, freq): return float(np.clip(freq, cfg.tail_freq_min, cfg.tail_freq_max))
   # __init__: self.freq = self._clamp(cfg.tail_freq if freq is None else freq)
   # set_freq: freq = self._clamp(freq) before the phase-continuity update
   def command(self, t, V_p):
       if t - self.t_switch < cfg.valve_min_dwell:
           return self.s
       e = self.v_ref(t)[0] - V_p
       s = self.s
       if e > δ: s = 1
       elif e < -δ: s = -1
       if s != self.s:
           self.s, self.t_switch = s, t
       return self.s
   ```
   (OpenModelica: equivalent in the relay block — e.g. a `pre(t_switch)` discrete var and a
   `when` guard `time - pre(t_switch) >= valve_min_dwell`; clamp the frequency parameter with an
   assert or min/max.)
3. Viewer/GUI frequency keys: limits come from config tail_freq_min / tail_freq_max.
4. Sweeps / scenarios: frequency ranges become tail_freq_min … tail_freq_max (step 0.25).
   Any scenario/test using f < 1.25 or > 2.5 Hz must move into the range (MuJoCo: h3 1 Hz → 1.25 Hz,
   offline fixtures 1 Hz → 1.25 Hz, sweep test [1.25, 1.5, 2.5]).
5. Tests to add (mirror MuJoCo tests/test_sanity.py):
   - `test_valve_holds_each_state_for_min_dwell`: for f in (f_min, 2.0, f_max) the min gap between
     switches ≥ valve_min_dwell − 1e-9.
   - `test_frequency_clamped_to_valve_range`: 0.5 → f_min, 3.0 → f_max, set_freq(10) → f_max,
     and f_max ≤ 1/(2·valve_min_dwell).
   - Remove/replace tests that expected tracking (many switches/cycle) at low frequency.
   - Expect: the relief valve may open during the start (first stroke held ≥ 0.2 s on a small V_ref).
     MuJoCo now checks all-time max ≤ 1.01·p_max and steady state (t > 3 s) < p_max.
6. MuJoCo results after the change (for comparison): offline V_p amplitude 1.5/2/2.5 Hz =
   9.3/6.7/5.4 ml (triangle Q/(4f) = 10/7.5/6 ml); 2 switches/cycle from 1.5 Hz up, 3.4 at 1.25 Hz;
   swim speed 1.25/1.5/2/2.5 Hz = 20.4/24.2/23.1/18.8 cm/s; steady max Δp 41 kPa.
