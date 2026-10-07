"""Animation of the free-swimming fish (top view) -> results/free_swim.gif.

    python scripts/animate.py             # from the saved stage 4 frames (or computes them)
    python scripts/animate.py --fps 25

The camera follows the fish (window around the center of mass); the dotted line is the nose path.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import fishrod  # noqa: E402,F401
import numpy as np  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402
from plotting import SERIES, THEORY, plt  # noqa: E402

RESULTS = ROOT / "results"
FRAMES = RESULTS / "e4_free_swim_frames.npz"


def load_frames():
    if not FRAMES.exists():
        from fishrod import scenarios as S
        from fishrod.config import default_config
        print("No saved frames – computing free swimming (stage 4)...")
        r = S.free_swim(default_config(), "drag+reactive", verbose=True)
        RESULTS.mkdir(exist_ok=True)
        np.savez_compressed(FRAMES, frames=r["frames"], t=r["frame_t"], length=r["length"])
    d = np.load(FRAMES)
    return d["frames"], d["t"], float(d["length"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--out", default=str(RESULTS / "free_swim.gif"))
    args = ap.parse_args()
    frames, t, L = load_frames()
    step = max(1, int(round(1.0 / (args.fps * (t[1] - t[0])))))
    idx = np.arange(0, len(frames), step)
    nose = frames[:, :2, 0]

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    trail, = ax.plot([], [], ":", color=THEORY, lw=1)
    body, = ax.plot([], [], color=SERIES[2], lw=3, solid_capstyle="round")
    head, = ax.plot([], [], "o", color=SERIES[2], ms=6)
    txt = ax.text(0.02, 0.95, "", transform=ax.transAxes, va="top", fontsize=9)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title("Soft fish (Cosserat rod), top view")
    w = 1.2 * L

    def draw(k):
        p = frames[k]
        c = p[:2].mean(axis=1)
        ax.set_xlim(c[0] - w, c[0] + w)
        ax.set_ylim(c[1] - 0.6 * w, c[1] + 0.6 * w)
        body.set_data(p[0], p[1])
        head.set_data([p[0, 0]], [p[1, 0]])
        trail.set_data(nose[:k + 1, 0], nose[:k + 1, 1])
        txt.set_text(f"t = {t[k]:4.1f} s   distance = {np.linalg.norm(nose[k] - nose[0]):.2f} m")
        return body, head, trail, txt

    anim = FuncAnimation(fig, draw, frames=idx, blit=False)
    anim.save(args.out, writer=PillowWriter(fps=args.fps), dpi=90)
    print(f"Saved {args.out} ({len(idx)} frames, {args.fps} fps)")


if __name__ == "__main__":
    main()
