"""Geometric measurements of the tail – one definition for tests, plots and export.

Tip angle (spec, section 5): angle of the chord from the center of the front wall (root)
to the centroid of the fin nodes, measured in the XY plane:
    θ_tip = atan2(Δy, −Δx)
The tail extends along −X, so for a straight tail Δx < 0, Δy = 0 and θ_tip = 0.
θ_tip > 0 = tail bent towards +Y (left, looking from the body towards the tail: to port).
"""
import numpy as np


def base_center(points0: np.ndarray, base_nodes: np.ndarray) -> np.ndarray:
    """Center of the front wall in the initial configuration (these nodes are fixed)."""
    return points0[base_nodes].mean(axis=0)


def fin_centroid(x: np.ndarray, fin_nodes: np.ndarray) -> np.ndarray:
    return x[fin_nodes].mean(axis=0)


def tip_angle(x: np.ndarray, base: np.ndarray, fin_nodes: np.ndarray) -> float:
    """θ_tip [rad] for the current node positions x."""
    d = fin_centroid(x, fin_nodes) - base
    return float(np.arctan2(d[1], -d[0]))


def tip_displacement(x: np.ndarray, x0: np.ndarray, fin_nodes: np.ndarray) -> np.ndarray:
    """Displacement of the fin centroid [m] relative to the initial configuration."""
    return fin_centroid(x, fin_nodes) - fin_centroid(x0, fin_nodes)
