"""Water drag on the outer surface of the tail – a simple local model (stage 5).

SOFA has no fluid model. Instead of CFD, each skin triangle gets a drag force that depends
only on its own velocity (a local drag model, cf. resistive force theory):
  - normal force      F_n = −½ ρ C_n A (v·n)|v·n| n    (quadratic pressure drag),
  - tangential force  F_t = −½ ρ C_t A |v_t| v_t       (skin friction, small),
where v = mean velocity of the triangle's 3 nodes, n = outward normal, A = area.
The triangle force is split equally among its 3 nodes.

Note on C_n: a closed solid has two sides. A plate (fin) moving perpendicular to itself
gets drag on BOTH sides (front: v·n > 0, back: v·n < 0, force in the same direction),
so the drag coefficient of the whole plate is 2·C_n. C_n = 1 gives C_d ≈ 2, typical
for a flat plate in cross-flow.

What this model does NOT include (README, "Limitations"): added mass (water accelerated
together with the tail), lift, vortices and the wake. Fish swimming is dominated by exactly
these reactive effects (Lighthill's theory), so the thrust from this model is only qualitative.

Everything here is pure numpy (no SOFA) – testable on synthetic data.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class DragResult:
    node_forces: np.ndarray   # (N, 3) [N] nodal forces
    total: np.ndarray         # (3,) [N] net water force on the tail
    power: float              # [W] drag power Σ F·v (always ≤ 0: drag removes energy)
    node_damping: np.ndarray  # (N,) [kg/s] local nodal damping coefficient c (for stability)


def triangle_geometry(x: np.ndarray, tris: np.ndarray):
    """Triangle areas [m²] and unit normals (orientation follows node order)."""
    a, b, c = x[tris[:, 0]], x[tris[:, 1]], x[tris[:, 2]]
    cr = np.cross(b - a, c - a)
    dbl = np.linalg.norm(cr, axis=1)
    n = cr / np.maximum(dbl, 1e-300)[:, None]
    return 0.5 * dbl, n


def triangle_forces(x: np.ndarray, v: np.ndarray, tris: np.ndarray, rho: float, C_n: float, C_t: float):
    """Drag force on each triangle (K, 3) plus auxiliary data: triangle velocity (K, 3),
    its normal component (K,) and area (K,)."""
    area, n = triangle_geometry(x, tris)
    vt = v[tris].mean(axis=1)                    # triangle velocity
    vn = np.einsum("ij,ij->i", vt, n)            # normal component (scalar)
    v_tan = vt - vn[:, None] * n                 # tangential component (vector)
    s_tan = np.linalg.norm(v_tan, axis=1)
    f = (-0.5 * rho * C_n * area * vn * np.abs(vn))[:, None] * n \
        - (0.5 * rho * C_t * area * s_tan)[:, None] * v_tan
    return f, vt, vn, area


def drag(x: np.ndarray, v: np.ndarray, tris: np.ndarray, rho: float, C_n: float, C_t: float) -> DragResult:
    """Water drag forces on skin nodes for positions x and velocities v (both (N, 3))."""
    f, vt, vn, area = triangle_forces(x, v, tris, rho, C_n, C_t)
    nodes = np.zeros_like(x)
    np.add.at(nodes, tris.ravel(), np.repeat(f / 3.0, 3, axis=0))
    # Derivative |dF_n/dv_n| = ρ C_n A |v_n|: the "damping" contributed by the explicit drag.
    # Each node gets 1/3 of each triangle's area (spec, section 7: c = ρ·C_n·A_node·|v_n|).
    c_tri = rho * C_n * area * np.abs(vn)
    damp = np.zeros(len(x))
    np.add.at(damp, tris.ravel(), np.repeat(c_tri / 3.0, 3))
    power = float(np.einsum("ij,ij->", f, vt))
    return DragResult(nodes, f.sum(axis=0), power, damp)


def stability_ratio(node_damping: np.ndarray, node_mass: np.ndarray, dt: float) -> float:
    """max(c·dt/m) over skin nodes.

    Drag is computed from the PREVIOUS step's velocity, i.e. explicitly. For a node with
    damping c, an explicit step multiplies the velocity by (1 − c·dt/m): at c·dt/m > 1 it
    flips sign (growing oscillation), and from ~0.5 on the result is noticeably distorted.
    The thin fin has light nodes and a large area, so this ratio is largest there
    (spec, section 7).
    """
    m = node_mass[node_damping > 0]
    return float((node_damping[node_damping > 0] * dt / m).max()) if len(m) else 0.0
