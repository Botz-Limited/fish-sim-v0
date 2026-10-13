#!/usr/bin/env python3
"""Generates actuation files for CalculiX: pressure in chambers L/R.

Two waveforms (--waveform):

valve (default) – the real hardware: a constant-speed pump with a constant flow
    Q_const and directional valves with only two states, s = +1 (R -> L) or
    s = -1 (L -> R); there is no "closed" state. Same model as the other demos
    (MuJoCo/SOFA/Stonefish/PyElastica after the Q_max -> Q_const change):
        V_ref(t) = r(t) * A_V * sin(2*pi*f*t)          (pumped-volume reference)
        e = V_ref - V_p;  e > +delta -> s = +1;  e < -delta -> s = -1
                          (otherwise s unchanged; start s = +1)   relay + hysteresis
        the valve holds each state for at least valve_min_dwell (0.2 s: the
        real valve switches at most ~5 times/s), i.e. the relay is ignored
        until t - t_switch >= valve_min_dwell
        dQ/dt   = (s*Q_const - Q) / tau_valve          (valve switch + flow reversal)
        dV_p/dt = Q
        dp      = clip(V_p / C_h, -p_max, +p_max)      (relief valve)
        p_L = max(0, dp),  p_R = max(0, -dp)
    Volume -> pressure: this case PRESCRIBES pressure, so it has no
    volume/pressure relation of its own. We use the hydraulic-spring relation
    of the other demos, dp = (V_p - A_r*L)/C_h, with a RIGID-TAIL assumption
    (A_r*L = 0, the tail does not "make room"), i.e. a single lumped stiffness
    1/C_h. Default C_h = A_V / P0, so a perfectly tracked V_ref gives exactly
    the old peak pressure P0 – the old sine and the valve waveform are
    directly comparable. Below f_track = Q_const/(2*pi*A_V) the relay would
    track V_ref with a sawtooth (many valve switches per cycle) – the valve
    cannot do that, so frequencies are limited to
        [TAIL_FREQ_MIN, TAIL_FREQ_MAX] = [1.5, 2.5] Hz
    (user decision: TAIL_FREQ_MIN = 1.5 Hz on all demos – at 1.25 Hz, just
    above f_track ~ 1.19 Hz, the dwell-limited valve still adds 1-2 extra
    switches per cycle; TAIL_FREQ_MAX = 1/(2*valve_min_dwell): 2 switches per
    cycle, each state >= 0.2 s).
    In this range the valve switches only at the peaks (2 per cycle) and the
    pressure is a triangle with amplitude ~ Q_const/(4*f*C_h) (minus the
    tau_valve loss). A valve-waveform frequency outside the range is REJECTED
    with an error (no silent clamping: the case name/case.txt would lie).

sine – the old waveform, kept for comparison:
        p_L = P0 * r(t) * max(0,  sin 2*pi*f*t),  p_R = P0 * r(t) * max(0, -sin 2*pi*f*t)

r(t) = ramp 0 -> 1 over the first T_RAMP seconds (soft start). Chamber pressure
cannot be negative (underpressure would collapse the chambers), hence the split
of dp into p_L and p_R.

Writes:
    amplitude.inc – *AMPLITUDE definitions (model data, before *STEP)
    dload.inc     – *DLOAD on the chamber walls (step data, inside *STEP)
With P0 = 0 the files are empty (passive tail).

Usage:
    python tools/make_actuation.py <dir> --p0 PA --freq HZ --t-end S [--t-ramp S]
           [--waveform valve|sine] [--q-const M3/S] [--volume-amp M3]
           [--tau-valve S] [--hysteresis M3] [--min-dwell S] [--compliance M3/PA]
           [--p-max PA]
"""
import argparse
from pathlib import Path

import numpy as np

# --- Valve model (all PLACEHOLDER – to be identified from measurements) -------
# Values as in MuJoCo/fishsim/config.py (Q_max -> Q_const, tau_pump -> tau_valve).
# The 2D CalculiX model has no real chamber volume (1 m span), so A_V and
# Q_const only set the RATIO f_track = Q_const/(2*pi*A_V) ~ 1.19 Hz.
Q_CONST = 60e-6          # [m^3/s] constant pump flow (60 ml/s)           PLACEHOLDER
VOLUME_AMP = 8e-6        # [m^3] A_V, amplitude of V_ref (8 ml)          PLACEHOLDER
TAU_VALVE = 0.02         # [s] valve switching + flow reversal           PLACEHOLDER
HYSTERESIS = 1e-6        # [m^3] delta, relay hysteresis (1 ml)          PLACEHOLDER
P_MAX = 50e3             # [Pa] relief valve                             PLACEHOLDER
VALVE_MIN_DWELL = 0.2    # [s] min. time between valve switches (<= 5/s) PLACEHOLDER
# Allowed tail frequency range [Hz]. Min: 1.5 Hz (user decision, all demos;
# > f_track ~ 1.19 Hz, clean 2 switches/cycle). Max: 1/(2*VALVE_MIN_DWELL) = 2.5 Hz.
TAIL_FREQ_MIN = 1.5      # [Hz]                                          PLACEHOLDER
TAIL_FREQ_MAX = 2.5      # [Hz]                                          PLACEHOLDER
DT_SIM = 1e-4            # [s] integration step of the valve ODE
DT_OUT = 1e-3            # [s] sampling of the *AMPLITUDE table (FSI step 2.5 ms)


def ramp(t, t_ramp):
    return np.clip(t / t_ramp, 0.0, 1.0)


def sine_waveform(t, freq, t_ramp):
    """Old waveform: multipliers of P0 for chambers L and R."""
    s = np.sin(2 * np.pi * freq * t)
    r = ramp(t, t_ramp)
    return r * np.maximum(0.0, s), r * np.maximum(0.0, -s)


def check_freq(freq, f_min=TAIL_FREQ_MIN, f_max=TAIL_FREQ_MAX):
    """Raises ValueError if freq is outside the valve's frequency range."""
    if not (f_min - 1e-9 <= freq <= f_max + 1e-9):
        raise ValueError(
            f"tail frequency {freq:g} Hz is outside the valve range [{f_min:g}, {f_max:g}] Hz "
            f"(valve min. dwell {VALVE_MIN_DWELL:g} s -> at most 2 switches per cycle up to "
            f"{1 / (2 * VALVE_MIN_DWELL):g} Hz; below ~f_track the relay would chatter)")
    return freq


def valve_model(t_end, freq, t_ramp, q_const, volume_amp, tau_valve, delta,
                min_dwell=VALVE_MIN_DWELL, dt=DT_SIM):
    """Relay valve (min. dwell) + first-order flow. Returns t, V_ref, V_p, Q, s on the DT_SIM grid."""
    n = int(np.ceil(t_end / dt)) + 1
    t = np.arange(n) * dt
    v_ref = ramp(t, t_ramp) * volume_amp * np.sin(2 * np.pi * freq * t)
    v = np.zeros(n)
    q = np.zeros(n)
    s = np.ones(n)
    sk, qk, vk = 1.0, 0.0, 0.0           # start: s = +1, pump at rest
    a = np.exp(-dt / tau_valve)          # exact step of dQ/dt = (s*Q_const - Q)/tau
    # dwell counted in whole steps (t - t_switch >= min_dwell without round-off)
    n_dwell = int(np.ceil(min_dwell / dt - 1e-9))
    k_switch = -n_dwell                  # t_switch = -inf: the first switch is free
    for k in range(n):
        if k - k_switch >= n_dwell:
            e = v_ref[k] - vk
            s_new = sk
            if e > delta:
                s_new = 1.0
            elif e < -delta:
                s_new = -1.0
            if s_new != sk:
                sk, k_switch = s_new, k
        v[k], q[k], s[k] = vk, qk, sk
        q_new = sk * q_const + (qk - sk * q_const) * a
        vk += 0.5 * (qk + q_new) * dt
        qk = q_new
    return t, v_ref, v, q, s


def write_amplitude(path, t, curves, header):
    with open(path, "w") as f:
        f.write("** Actuation (generated by tools/make_actuation.py – do not edit)\n")
        for line in header:
            f.write(f"** {line}\n")
        for name, y in curves.items():
            # TIME=TOTAL TIME: time counted from the start of the analysis (not the step)
            f.write(f"*AMPLITUDE, NAME={name}, TIME=TOTAL TIME\n")
            for i in range(0, len(t), 4):
                f.write(", ".join(f"{tt:.6g}, {yy:.6g}" for tt, yy in zip(t[i:i + 4], y[i:i + 4])) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--p0", type=float, required=True,
                    help="reference pressure [Pa]: sine amplitude, or (valve) pressure at V_p = A_V")
    ap.add_argument("--freq", type=float, default=TAIL_FREQ_MIN,
                    help=f"frequency [Hz]; valve: {TAIL_FREQ_MIN:g}..{TAIL_FREQ_MAX:g}")
    ap.add_argument("--t-end", type=float, required=True, help="end time [s]")
    ap.add_argument("--t-ramp", type=float, default=None, help="ramp time [s] (default: 1 period)")
    ap.add_argument("--waveform", choices=["valve", "sine"], default="valve",
                    help="valve = constant pump + +-1 valves (default); sine = old waveform")
    ap.add_argument("--q-const", type=float, default=Q_CONST, help="pump flow Q_const [m^3/s]")
    ap.add_argument("--volume-amp", type=float, default=VOLUME_AMP, help="A_V of V_ref [m^3]")
    ap.add_argument("--tau-valve", type=float, default=TAU_VALVE, help="valve time constant [s]")
    ap.add_argument("--hysteresis", type=float, default=HYSTERESIS, help="relay hysteresis delta [m^3]")
    ap.add_argument("--min-dwell", type=float, default=VALVE_MIN_DWELL,
                    help="valve min. time between switches [s]")
    ap.add_argument("--compliance", type=float, default=None,
                    help="C_h [m^3/Pa], rigid tail (default: A_V / P0)")
    ap.add_argument("--p-max", type=float, default=P_MAX, help="relief valve [Pa]")
    ap.add_argument("--dt-out", type=float, default=DT_OUT, help="table sampling [s] (valve)")
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)
    amp, dl = a.outdir / "amplitude.inc", a.outdir / "dload.inc"

    # The valve frequency range applies to an actuated valve waveform only
    # (P0 = 0 is a passive tail; sine is the old waveform kept for comparison).
    if a.p0 != 0 and a.waveform == "valve":
        try:
            check_freq(a.freq)
        except ValueError as e:
            ap.error(str(e))

    if a.p0 == 0:
        amp.write_text("** Passive tail: no actuation\n")
        dl.write_text("** Passive tail: no chamber pressure\n")
        print("actuation: none (P0 = 0)")
        return

    t_ramp = a.t_ramp if a.t_ramp is not None else 1.0 / a.freq
    if a.waveform == "sine":
        # 64 points per period – CalculiX interpolates linearly between points
        t = np.linspace(0.0, a.t_end, int(np.ceil(a.t_end * a.freq * 64)) + 1)
        yl, yr = sine_waveform(t, a.freq, t_ramp)
        header = [f"waveform = sine (old), f = {a.freq} Hz, ramp {t_ramp} s; "
                  "values are a multiplier of P0 (0..1)"]
        info = ""
    else:
        c_h = a.compliance if a.compliance is not None else a.volume_amp / a.p0
        ts, v_ref, v, q, s = valve_model(a.t_end, a.freq, t_ramp, a.q_const,
                                         a.volume_amp, a.tau_valve, a.hysteresis, a.min_dwell)
        dp = np.clip(v / c_h, -a.p_max, a.p_max)
        # The table needs every corner of the sawtooth: sample at DT_OUT
        # (finer than the FSI step), CalculiX interpolates linearly in between.
        stride = max(1, int(round(a.dt_out / DT_SIM)))
        idx = np.arange(0, len(ts), stride)
        if idx[-1] != len(ts) - 1:
            idx = np.append(idx, len(ts) - 1)
        t = ts[idx]
        yl, yr = np.maximum(0.0, dp[idx]) / a.p0, np.maximum(0.0, -dp[idx]) / a.p0
        f_track = a.q_const / (2 * np.pi * a.volume_amp)
        # valve switches per tail cycle, counted after the ramp
        after = ts >= t_ramp
        n_sw = np.count_nonzero(np.diff(s[after]) != 0)
        cycles = (a.t_end - t_ramp) * a.freq
        sw = n_sw / cycles if cycles > 0 else float("nan")
        peak = np.max(np.abs(dp[after])) if after.any() else np.max(np.abs(dp))
        t_sw = ts[1:][np.diff(s) != 0]
        gap = np.min(np.diff(t_sw)) if len(t_sw) > 1 else float("nan")
        header = [
            f"waveform = valve (constant pump + +-1 valves), f = {a.freq} Hz, ramp {t_ramp} s",
            f"Q_const = {a.q_const:g} m3/s, A_V = {a.volume_amp:g} m3, tau_valve = {a.tau_valve:g} s, "
            f"delta = {a.hysteresis:g} m3, valve min. dwell = {a.min_dwell:g} s",
            f"dp = clip(V_p/C_h, +-{a.p_max:g}), rigid tail, C_h = {c_h:.4g} m3/Pa; "
            "values are a multiplier of P0 (may exceed 1)",
            f"f_track = Q_const/(2 pi A_V) = {f_track:.3g} Hz; "
            f"valve switches per cycle = {sw:.1f}; min. gap between switches = {gap:.4g} s; "
            f"peak |dp| = {peak:.4g} Pa",
        ]
        info = (f", f_track {f_track:.2f} Hz, {sw:.1f} switches/cycle, min. switch gap {gap:.3f} s, "
                f"peak |dp| {peak:.0f} Pa")

    write_amplitude(amp, t, {"AMP_L": yl, "AMP_R": yr}, header)
    with open(dl, "w") as f:
        f.write("** Chamber pressure: P0 * amplitude(t)\n")
        f.write(f"** P0 = {a.p0:g} Pa   PLACEHOLDER – to be identified from measurements\n")
        f.write("*DLOAD, AMPLITUDE=AMP_L\n")
        f.write(f"SchL, P, {a.p0:g}\n")
        f.write("*DLOAD, AMPLITUDE=AMP_R\n")
        f.write(f"SchR, P, {a.p0:g}\n")
    print(f"actuation ({a.waveform}): P0 = {a.p0:g} Pa, f = {a.freq} Hz, ramp {t_ramp} s{info}")


if __name__ == "__main__":
    main()
