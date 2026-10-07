"""Geometry of the hoop-fiber wrap: rings of points connected by springs.

The ring at cross-section x is the tail ellipse shrunk by fiber_inset (the points must lie
inside tetrahedra so that BarycentricMapping can "glue" them to the FEM).
Rings are placed every fiber_ring_spacing along the chambers (where the wall bulges).

Stiffness: the wrap is a membrane with hoop stiffness K = E_fiber·thickness [N/m]. A strip
of membrane of width w (= ring spacing) and length l (= ring segment) has
stiffness k = K·w/l – and that is what each spring gets.
"""
from dataclasses import dataclass

import numpy as np

from fishsofa.config import TailConfig


@dataclass
class Rings:
    points: np.ndarray     # (P, 3) [m]
    springs: np.ndarray    # (S, 2) point indices
    lengths: np.ndarray    # (S,) rest length [m]
    stiffness: np.ndarray  # (S,) [N/m]
    n_rings: int


def hoop_rings(cfg: TailConfig) -> Rings:
    x1, x2 = cfg.chamber_x_range
    n_r = max(2, int(round((x1 - x2) / cfg.fiber_ring_spacing)) + 1)
    xs = np.linspace(x1, x2, n_r)
    n = cfg.fiber_ring_points
    phi = np.linspace(0.0, 2 * np.pi, n, endpoint=False)
    pts, springs = [], []
    for r, x in enumerate(xs):
        s = cfg.scale_at(x)
        ry, rz = cfg.ry0 * s - cfg.fiber_inset, cfg.rz0 * s - cfg.fiber_inset
        pts.append(np.column_stack([np.full(n, x), ry * np.cos(phi), rz * np.sin(phi)]))
        i = r * n + np.arange(n)
        springs.append(np.column_stack([i, np.roll(i, -1)]))  # closed ring
    pts = np.vstack(pts)
    springs = np.vstack(springs)
    lengths = np.linalg.norm(pts[springs[:, 1]] - pts[springs[:, 0]], axis=1)
    stiffness = cfg.hoop_stiffness * cfg.fiber_ring_spacing / lengths
    return Rings(pts, springs, lengths, stiffness, n_r)
