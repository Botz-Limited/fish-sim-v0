"""Recording of tail flapping for real-time playback.

Usage:  source scripts/env.sh && python scripts/record.py            (~40 min, air + water at once)
        python scripts/record.py --env water --t-end 3              (single recording, shorter)

The SOFA simulation runs 100–800× slower than real time (README, "Performance"), so live in
the GUI the tail crawls. Instead we compute the run headless (like stages 4–5) and every
1/60 s of simulation time we save the positions of all nodes. Such a recording then plays
back in real time:
  - in the SOFA GUI:  scripts/run_gui.sh coarse replay recordings/water.npz
  - as a video:       python scripts/render_video.py  (results/flapping.mp4)

Recordings (~25 MB each) go to recordings/ and are not in the repo – this script regenerates them.
"""
import argparse
import os
import sys
from dataclasses import replace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fishsofa import PROJECT_DIR, headless, mesh_gen, parallel  # noqa: E402
from fishsofa.config import TailConfig  # noqa: E402

FPS = 60
# Time step as in stages 4–5: air 1 ms (numerical damping −5% at 2 ms), water 0.5 ms
# (explicit drag: max(c·dt/m) < 0.5 only at 0.5 ms).
DT = {"air": 0.001, "water": 0.0005}
LOG_KEYS = ("t", "theta", "p_L", "p_R", "V_ref", "V_p", "F_x", "F_y")


def record(env: str, level: str, t_end: float) -> dict:
    """A single recording (called in a separate process by parallel.run_all)."""
    cfg = replace(TailConfig(environment=env), dt=DT[env])
    r = headless.run_flapping(cfg, level, t_end, record_fps=FPS)
    log = {k: r.log[k] for k in LOG_KEYS if k in r.log}
    return {"frames": r.frames, "log": log, "ms_per_step": r.ms_per_step, "dt": cfg.dt}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", choices=("air", "water", "both"), default="both")
    ap.add_argument("--level", default="coarse")
    ap.add_argument("--t-end", type=float, default=4.5, help="simulation time [s] (prefill 1 s + ramp 1 s + rhythm)")
    a = ap.parse_args()
    envs = ("air", "water") if a.env == "both" else (a.env,)
    out_dir = os.path.join(PROJECT_DIR, "recordings")
    os.makedirs(out_dir, exist_ok=True)
    jobs = {env: dict(env=env, level=a.level, t_end=a.t_end) for env in envs}
    res = parallel.run_all(record, jobs, label="Recordings: ")
    cfg = TailConfig()
    mesh = mesh_gen.load(cfg, a.level)
    for env, r in res.items():
        path = os.path.join(out_dir, f"{env}.npz")
        log = {f"log_{k}": v for k, v in r["log"].items()}
        np.savez_compressed(path, t=r["frames"]["t"], x=r["frames"]["x"], points0=mesh.points.astype(np.float32),
                            tri_outer=mesh.tri_outer, tri_chamber_L=mesh.tri_chamber_L,
                            tri_chamber_R=mesh.tri_chamber_R, level=a.level, env=env, dt=r["dt"],
                            prefill_time=cfg.prefill_time, tail_freq=cfg.tail_freq, **log)
        print(f"{path}: {len(r['frames']['t'])} frames, {os.path.getsize(path) / 1e6:.0f} MB, "
              f"{r['ms_per_step']:.0f} ms/step")


if __name__ == "__main__":
    main()
