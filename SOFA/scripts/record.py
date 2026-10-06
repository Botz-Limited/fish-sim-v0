"""Nagranie machania ogona do odtwarzania w czasie rzeczywistym.

Uruchomienie:  source scripts/env.sh && python scripts/record.py            (~40 min, air + water naraz)
               python scripts/record.py --env water --t-end 3              (jedno nagranie, krócej)

Symulacja SOFA liczy się 100–800× wolniej niż czas rzeczywisty (README, „Wydajność”), więc
na żywo ogon w GUI pełznie. Zamiast tego liczymy przebieg bez GUI (jak etapy 4–5) i co
1/60 s czasu symulacji zapisujemy pozycje wszystkich węzłów. Takie nagranie odtwarza się
już w czasie rzeczywistym:
  - w GUI SOFA:  scripts/run_gui.sh coarse replay recordings/water.npz
  - jako wideo:  python scripts/render_video.py  (results/flapping.mp4)

Nagrania (~25 MB każde) trafiają do recordings/ i nie są w repo – da się je odtworzyć tym skryptem.
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
# Krok jak w etapach 4–5: powietrze 1 ms (tłumienie numeryczne −5% przy 2 ms), woda
# 0.5 ms (jawny opór: max(c·dt/m) < 0.5 dopiero przy 0.5 ms).
DT = {"air": 0.001, "water": 0.0005}
LOG_KEYS = ("t", "theta", "p_L", "p_R", "V_ref", "V_p", "F_x", "F_y")


def record(env: str, level: str, t_end: float) -> dict:
    """Jedno nagranie (wywoływane w osobnym procesie przez parallel.run_all)."""
    cfg = replace(TailConfig(environment=env), dt=DT[env])
    r = headless.run_flapping(cfg, level, t_end, record_fps=FPS)
    log = {k: r.log[k] for k in LOG_KEYS if k in r.log}
    return {"frames": r.frames, "log": log, "ms_per_step": r.ms_per_step, "dt": cfg.dt}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", choices=("air", "water", "both"), default="both")
    ap.add_argument("--level", default="coarse")
    ap.add_argument("--t-end", type=float, default=4.5, help="czas symulacji [s] (prefill 1 s + rampa 1 s + rytm)")
    a = ap.parse_args()
    envs = ("air", "water") if a.env == "both" else (a.env,)
    out_dir = os.path.join(PROJECT_DIR, "recordings")
    os.makedirs(out_dir, exist_ok=True)
    jobs = {env: dict(env=env, level=a.level, t_end=a.t_end) for env in envs}
    res = parallel.run_all(record, jobs, label="Nagrania: ")
    cfg = TailConfig()
    mesh = mesh_gen.load(cfg, a.level)
    for env, r in res.items():
        path = os.path.join(out_dir, f"{env}.npz")
        log = {f"log_{k}": v for k, v in r["log"].items()}
        np.savez_compressed(path, t=r["frames"]["t"], x=r["frames"]["x"], points0=mesh.points.astype(np.float32),
                            tri_outer=mesh.tri_outer, tri_chamber_L=mesh.tri_chamber_L,
                            tri_chamber_R=mesh.tri_chamber_R, level=a.level, env=env, dt=r["dt"],
                            prefill_time=cfg.prefill_time, tail_freq=cfg.tail_freq, **log)
        print(f"{path}: {len(r['frames']['t'])} klatek, {os.path.getsize(path) / 1e6:.0f} MB, "
              f"{r['ms_per_step']:.0f} ms/krok")


if __name__ == "__main__":
    main()
