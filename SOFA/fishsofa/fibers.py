"""Geometria oplotu obwodowego: pierścienie punktów połączonych sprężynami.

Pierścień w przekroju x to elipsa ogona pomniejszona o fiber_inset (punkty muszą leżeć
wewnątrz czworościanów, żeby BarycentricMapping mógł je „przykleić” do FEM).
Pierścienie stoją co fiber_ring_spacing na długości komór (tam ścianka się wydyma).

Sztywność: oplot to membrana o sztywności obwodowej K = E_włókna·grubość [N/m]. Pasek
membrany o szerokości w (= odstęp pierścieni) i długości l (= odcinek pierścienia) ma
sztywność k = K·w/l – i taką dostaje każda sprężyna.
"""
from dataclasses import dataclass

import numpy as np

from fishsofa.config import TailConfig


@dataclass
class Rings:
    points: np.ndarray     # (P, 3) [m]
    springs: np.ndarray    # (S, 2) indeksy punktów
    lengths: np.ndarray    # (S,) długość spoczynkowa [m]
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
        springs.append(np.column_stack([i, np.roll(i, -1)]))  # zamknięty pierścień
    pts = np.vstack(pts)
    springs = np.vstack(springs)
    lengths = np.linalg.norm(pts[springs[:, 1]] - pts[springs[:, 0]], axis=1)
    stiffness = cfg.hoop_stiffness * cfg.fiber_ring_spacing / lengths
    return Rings(pts, springs, lengths, stiffness, n_r)
