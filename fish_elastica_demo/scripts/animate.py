"""Animation of the free-swimming fish (top view) with live readouts -> results/free_swim.gif.

    python scripts/animate.py                                   # GIF from the saved stage 4 frames
    python scripts/animate.py --out results/free_swim.mp4 --size 2560x1440   # video (needs ffmpeg)
    python scripts/animate.py --fps 25 --speed 0.5              # 2x slow motion

The camera follows the fish (window around the center of mass); the dotted line is the nose path.
Readouts (right panel and arrows), from the stage 4 run with the "drag+reactive" water model:
- swimming speed U (center-of-mass velocity along the nose direction), distance;
- hydraulics: pressure difference between the chambers dp and the bending angle of the chamber zone;
- water forces in the fish frame (fwd + = forward, side + = left), split into quadratic drag on
  the whole body, drag on the rear half (tail), and the Lighthill reactive force at the tail tip;
- arrows: drag per body slice (green) and the reactive force at the tip (magenta).
Old frame files (without forces) still animate, without the readouts: rerun stage 4 or delete
results/e4_free_swim_frames.npz to recompute.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import fishrod  # noqa: E402,F401
import numpy as np  # noqa: E402
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter  # noqa: E402
from plotting import INK, MUTED, SERIES, THEORY, plt  # noqa: E402

RESULTS = ROOT / "results"
FRAMES = RESULTS / "e4_free_swim_frames.npz"
READOUTS = ("drag", "reactive", "dp", "theta", "U")
N_SLICES = 8
DRAG_RGB, REACT_RGB = SERIES[5], "#d0109a"


def load_frames() -> dict:
    if not FRAMES.exists():
        from fishrod import scenarios as S
        from fishrod.config import default_config
        print("No saved frames – computing free swimming (stage 4)...")
        r = S.free_swim(default_config(), "drag+reactive", verbose=True)
        RESULTS.mkdir(exist_ok=True)
        np.savez_compressed(FRAMES, frames=r["frames"], t=r["frame_t"], length=r["length"],
                            **{k: r["frame_" + k] for k in READOUTS})
    d = dict(np.load(FRAMES))
    d["length"] = float(d["length"])
    return d


def fish_axes(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Unit vectors in the XY plane: forward (nose direction from the stiff head) and left."""
    e = p[:2, 0] - p[:2, 3]
    e /= np.linalg.norm(e)
    return e, np.array([-e[1], e[0]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--speed", type=float, default=1.0, help="pace relative to real time (0.5 = 2x slower)")
    ap.add_argument("--out", default=str(RESULTS / "free_swim.gif"))
    ap.add_argument("--size", default="", help="video size in pixels, e.g. 2560x1440")
    args = ap.parse_args()
    d = load_frames()
    frames, t, L = d["frames"], d["t"], d["length"]
    has_forces = all(k in d for k in READOUTS)
    step = max(1, int(round(args.speed / (args.fps * (t[1] - t[0])))))
    idx = np.arange(0, len(frames), step)
    nose = frames[:, :2, 0]

    if args.size:
        W, H = (int(v) for v in args.size.split("x"))
        dpi = H / 7.2
        fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi)
        plt.rcParams["savefig.bbox"] = None       # fixed frame size for the video encoder
    else:
        fig = plt.figure(figsize=(9.6, 4.8))
        dpi = 64                                  # GIF: keep the file small (~4 MB)
    ax = fig.add_axes([0.05, 0.09, 0.56, 0.84])
    trail, = ax.plot([], [], ":", color=THEORY, lw=1)
    body, = ax.plot([], [], color=SERIES[2], lw=4, solid_capstyle="round")
    head, = ax.plot([], [], "o", color=SERIES[2], ms=7)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title("Soft fish (Cosserat rod), top view")
    w = 1.2 * L
    panel = fig.text(0.64, 0.93, "", va="top", ha="left", family="monospace", fontsize=11, color=INK,
                     bbox=dict(boxstyle="round,pad=0.6", fc="#f4f3ef", ec=MUTED))

    if has_forces:
        drag, reac = d["drag"], d["reactive"]
        n = drag.shape[2]
        slices = np.array_split(np.arange(n), N_SLICES)
        rear = np.arange(n // 2, n)
        # arrow scale: 95th percentile of the slice drag after the start-up -> 0.25 L
        late = t > 0.2 * t[-1]
        sl = np.stack([drag[:, :2, s].sum(axis=2) for s in slices], axis=2)[late]
        ref = float(np.percentile(np.linalg.norm(sl, axis=1), 95)) or 1.0
        k = 0.25 * L / ref
        # the reactive force is ~10x larger than the drag of one slice: its own scale, 95th pct -> 0.3 L
        ref_r = float(np.percentile(np.linalg.norm(reac[late][:, :2].sum(axis=2), axis=1), 95)) or 1.0
        k_r = 0.3 * L / ref_r
        q_drag = ax.quiver(np.zeros(N_SLICES), np.zeros(N_SLICES), np.zeros(N_SLICES), np.zeros(N_SLICES),
                           color=DRAG_RGB, angles="xy", scale_units="xy", scale=1, width=0.004, zorder=3)
        q_reac = ax.quiver([0], [0], [0], [0], color=REACT_RGB, angles="xy", scale_units="xy", scale=1,
                           width=0.006, zorder=4)
        ax.text(0.02, 0.02, f"arrows (water force): green = drag per body slice, 0.25 L = {1e3 * ref:.0f} mN\n"
                f"magenta = reactive force at the tail tip, 0.3 L = {1e3 * ref_r:.0f} mN",
                transform=ax.transAxes, fontsize=9, color=MUTED)

    def readout(kf: int, e: np.ndarray, lft: np.ndarray) -> str:
        p = frames[kf]
        dist = np.linalg.norm(nose[kf] - nose[0])
        lines = [f"t = {t[kf]:5.2f} s     replay x{args.speed:g}",
                 f"distance       {dist:6.2f} m"]
        if not has_forces:
            return "\n".join(lines)
        def fs(F):
            return f"{1e3 * (F[:2] @ e):+7.1f} {1e3 * (F[:2] @ lft):+7.1f}"
        D = drag[kf].sum(axis=1)
        Dt = drag[kf][:, rear].sum(axis=1)
        R = reac[kf].sum(axis=1)
        v = p[:2, -1] - p[:2, -4]                   # last tail segment, pointing backward
        tip = np.degrees(np.arctan2(v @ lft, -(v @ e)))
        lines += [f"speed U        {100 * d['U'][kf]:+6.1f} cm/s",
                  "",
                  "HYDRAULICS",
                  f"dp (L - R)     {d['dp'][kf] / 1e3:+6.1f} kPa",
                  f"bend angle     {np.degrees(d['theta'][kf]):+6.1f} deg",
                  f"tip angle      {tip:+6.1f} deg",
                  "",
                  "WATER FORCES [mN]   fwd    side",
                  f"drag, body    {fs(D)}",
                  f"drag, tail    {fs(Dt)}",
                  f"reactive, tip {fs(R)}",
                  f"total         {fs(D + R)}",
                  "fwd + = forward (thrust)",
                  "side + = left"]
        return "\n".join(lines)

    def draw(kf):
        p = frames[kf]
        c = p[:2].mean(axis=1)
        ax.set_xlim(c[0] - w, c[0] + w)
        ax.set_ylim(c[1] - 0.75 * w, c[1] + 0.75 * w)
        body.set_data(p[0], p[1])
        head.set_data([p[0, 0]], [p[1, 0]])
        trail.set_data(nose[:kf + 1, 0], nose[:kf + 1, 1])
        e, lft = fish_axes(p)
        panel.set_text(readout(kf, e, lft))
        if has_forces:
            base = np.array([p[:2, s].mean(axis=1) for s in slices])
            vec = k * np.array([drag[kf][:2, s].sum(axis=1) for s in slices])
            q_drag.set_offsets(base)
            q_drag.set_UVC(vec[:, 0], vec[:, 1])
            q_reac.set_offsets(p[:2, -1:].T)
            r = k_r * reac[kf][:2].sum(axis=1)
            q_reac.set_UVC([r[0]], [r[1]])
        return body, head, trail, panel

    anim = FuncAnimation(fig, draw, frames=idx, blit=False)
    writer = FFMpegWriter(fps=args.fps, codec="libx264", extra_args=["-pix_fmt", "yuv420p", "-crf", "20"]) \
        if args.out.endswith(".mp4") else PillowWriter(fps=args.fps)
    anim.save(args.out, writer=writer, dpi=dpi)
    print(f"Saved {args.out} ({len(idx)} frames, {args.fps} fps, x{args.speed:g})")


if __name__ == "__main__":
    main()
