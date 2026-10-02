"""Pomiary geometryczne ogona – jedna definicja dla testów, wykresów i eksportu.

Kąt końcówki (spec, sekcja 5): kąt cięciwy od środka przedniej ściany (nasady)
do centroidu węzłów płetwy, mierzony w płaszczyźnie XY:
    θ_tip = atan2(Δy, −Δx)
Ogon wychodzi w −X, więc dla prostego ogona Δx < 0, Δy = 0 i θ_tip = 0.
θ_tip > 0 = ogon wygięty w +Y (w lewo, patrząc od kadłuba w stronę ogona: na lewą burtę).
"""
import numpy as np


def base_center(points0: np.ndarray, base_nodes: np.ndarray) -> np.ndarray:
    """Środek przedniej ściany w konfiguracji początkowej (te węzły są unieruchomione)."""
    return points0[base_nodes].mean(axis=0)


def fin_centroid(x: np.ndarray, fin_nodes: np.ndarray) -> np.ndarray:
    return x[fin_nodes].mean(axis=0)


def tip_angle(x: np.ndarray, base: np.ndarray, fin_nodes: np.ndarray) -> float:
    """θ_tip [rad] dla aktualnych pozycji węzłów x."""
    d = fin_centroid(x, fin_nodes) - base
    return float(np.arctan2(d[1], -d[0]))


def tip_displacement(x: np.ndarray, x0: np.ndarray, fin_nodes: np.ndarray) -> np.ndarray:
    """Przemieszczenie centroidu płetwy [m] względem konfiguracji początkowej."""
    return fin_centroid(x, fin_nodes) - fin_centroid(x0, fin_nodes)
