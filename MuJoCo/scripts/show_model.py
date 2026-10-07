"""Etap 1: model statyczny – raport mas/objętości/pływalności i podgląd.

  .venv/bin/python scripts/show_model.py            # tylko raport
  .venv/bin/python scripts/show_model.py --viewer   # + okno viewera (ryba nieruchoma)
  .venv/bin/python scripts/show_model.py --render results/s0_model.png   # + zrzut offscreen
  .venv/bin/python scripts/show_model.py --xml fish.xml                  # + zapis MJCF

W etapie 1 nie ma jeszcze wyporu, więc viewer NIE krokuje fizyki (inaczej ryba
by tonęła) – tylko wywołuje mj_forward, żeby pokazać geometrię.
"""

import argparse
import time

import mujoco
import mujoco.viewer
import numpy as np

from fishsim.config import FishConfig
from fishsim.model_builder import build_mjcf, build_model, describe


def render_png(model, data, path):
    """Zrzut z kamery śledzącej + widok z góry, sklejone obok siebie."""
    import matplotlib.pyplot as plt

    with mujoco.Renderer(model, 480, 640) as r:
        r.update_scene(data, camera="track")
        side = r.render().copy()
        cam = mujoco.MjvCamera()
        cam.lookat[:] = data.xipos[model.body("hull").id] + np.array([-0.1, 0, 0])
        cam.distance, cam.azimuth, cam.elevation = 0.8, 90.0, -89.0
        r.update_scene(data, camera=cam)
        top = r.render().copy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, img, title in ((axes[0], side, "kamera śledząca (bok)"), (axes[1], top, "widok z góry")):
        ax.imshow(img)
        ax.set_title(title)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    print(f"zapisano {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--viewer", action="store_true")
    ap.add_argument("--render", metavar="PNG")
    ap.add_argument("--xml", metavar="PATH")
    args = ap.parse_args()

    cfg = FishConfig()
    model, info = build_model(cfg)
    data = mujoco.MjData(model)
    print(describe(model, data, cfg, info))

    if args.xml:
        with open(args.xml, "w") as f:
            f.write(build_mjcf(cfg, info))
        print(f"zapisano {args.xml}")
    if args.render:
        render_png(model, data, args.render)
    if args.viewer:
        with mujoco.viewer.launch_passive(model, data) as v:
            while v.is_running():
                mujoco.mj_forward(model, data)
                v.sync()
                time.sleep(0.02)


if __name__ == "__main__":
    main()
