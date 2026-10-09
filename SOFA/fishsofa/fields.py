"""Fields for coloring the tail in the GUI: stress from node positions, load per skin area.

Pure numpy (no SOFA), so it can be tested and used on recordings, which store only node
positions. The stress follows the same corotational linear model as the FEM
(TetrahedronFEMForceField, method="large"): per tetrahedron the deformation gradient F is
split into a rotation R and a stretch (polar decomposition), the small strain is taken in
the rotated frame, ε = sym(RᵀF) − I, and Hooke's law gives σ = λ·tr(ε)·I + 2μ·ε.
Hoop fibers (springs) are not part of this stress: it is the stress in the silicone only.
"""
import numpy as np


def tet_shape(points: np.ndarray, tets: np.ndarray) -> np.ndarray:
    """Edge matrices D = [x1−x0, x2−x0, x3−x0] as columns, (M, 3, 3)."""
    p = points[tets]
    return np.stack([p[:, 1] - p[:, 0], p[:, 2] - p[:, 0], p[:, 3] - p[:, 0]], axis=2)


def von_mises(x0: np.ndarray, x: np.ndarray, tets: np.ndarray, young: np.ndarray, nu: float,
              Dm_inv: np.ndarray | None = None) -> np.ndarray:
    """Von Mises stress per tetrahedron [Pa] for rest positions x0 and current positions x."""
    if Dm_inv is None:
        Dm_inv = np.linalg.inv(tet_shape(x0, tets))
    F = tet_shape(x, tets) @ Dm_inv
    U, _, Vt = np.linalg.svd(F)
    R = U @ Vt
    flip = np.linalg.det(R) < 0                      # keep a proper rotation (no reflection)
    if np.any(flip):
        U[flip, :, 2] *= -1
        R[flip] = U[flip] @ Vt[flip]
    S = np.transpose(R, (0, 2, 1)) @ F
    eps = 0.5 * (S + np.transpose(S, (0, 2, 1))) - np.eye(3)
    lam = young * nu / ((1 + nu) * (1 - 2 * nu))
    mu = young / (2 * (1 + nu))
    tr = np.trace(eps, axis1=1, axis2=2)
    sig = 2 * mu[:, None, None] * eps + (lam * tr)[:, None, None] * np.eye(3)
    dev = sig - (np.trace(sig, axis1=1, axis2=2) / 3)[:, None, None] * np.eye(3)
    return np.sqrt(1.5 * np.einsum("kij,kij->k", dev, dev))


def to_nodes(values: np.ndarray, tets: np.ndarray, n_nodes: int, weights: np.ndarray) -> np.ndarray:
    """Weighted average of per-tet values at the nodes (weights: tet volumes)."""
    acc = np.zeros(n_nodes)
    w = np.zeros(n_nodes)
    np.add.at(acc, tets.ravel(), np.repeat(values * weights, 4))
    np.add.at(w, tets.ravel(), np.repeat(weights, 4))
    return acc / np.maximum(w, 1e-300)


def node_areas(points: np.ndarray, tris: np.ndarray, n_nodes: int) -> np.ndarray:
    """Surface area attributed to each node (1/3 of each adjacent triangle) [m²]."""
    a, b, c = points[tris[:, 0]], points[tris[:, 1]], points[tris[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    out = np.zeros(n_nodes)
    np.add.at(out, tris.ravel(), np.repeat(area / 3.0, 3))
    return out
