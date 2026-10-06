"""Opór wody na powierzchni zewnętrznej ogona – prosty model lokalny (etap 5).

SOFA nie ma modelu płynu. Zamiast CFD każdy trójkąt skóry dostaje siłę oporu zależną
tylko od własnej prędkości (model „lokalnego oporu”, ang. resistive force theory):
  - siła normalna  F_n = −½ ρ C_n A (v·n)|v·n| n    (kwadratowy opór ciśnieniowy),
  - siła styczna   F_t = −½ ρ C_t A |v_t| v_t       (tarcie skóry, małe),
gdzie v = średnia prędkość 3 węzłów trójkąta, n = normalna zewnętrzna, A = pole.
Siłę trójkąta dzielimy po równo na jego 3 węzły.

Uwaga do C_n: zamknięta bryła ma dwie strony. Płytka (płetwa) poruszająca się prostopadle
do siebie dostaje opór z OBU stron (przednia: v·n > 0, tylna: v·n < 0, siła w tę samą
stronę), więc współczynnik oporu całej płytki to 2·C_n. C_n = 1 daje C_d ≈ 2, typowe
dla płaskiej płytki w przepływie poprzecznym.

Czego ten model NIE ma (README, „Ograniczenia”): masy dodanej (woda rozpędzana razem
z ogonem), siły nośnej, wirów i śladu. W pływaniu ryb dominują właśnie efekty
reaktywne (teoria Lighthilla), więc ciąg z tego modelu jest tylko jakościowy.

Wszystko tu to czyste funkcje numpy (bez SOFA) – testowalne na syntetycznych danych.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class DragResult:
    node_forces: np.ndarray   # (N, 3) [N] siły na węzły
    total: np.ndarray         # (3,) [N] wypadkowa siła wody na ogon
    power: float              # [W] moc sił oporu Σ F·v (zawsze ≤ 0: opór zabiera energię)
    node_damping: np.ndarray  # (N,) [kg/s] lokalny współczynnik tłumienia c węzła (do stabilności)


def triangle_geometry(x: np.ndarray, tris: np.ndarray):
    """Pola [m²] i jednostkowe normalne trójkątów (orientacja wg kolejności węzłów)."""
    a, b, c = x[tris[:, 0]], x[tris[:, 1]], x[tris[:, 2]]
    cr = np.cross(b - a, c - a)
    dbl = np.linalg.norm(cr, axis=1)
    n = cr / np.maximum(dbl, 1e-300)[:, None]
    return 0.5 * dbl, n


def triangle_forces(x: np.ndarray, v: np.ndarray, tris: np.ndarray, rho: float, C_n: float, C_t: float):
    """Siła oporu na każdy trójkąt (K, 3) oraz dane pomocnicze: prędkość trójkąta (K, 3),
    jego składowa normalna (K,) i pole (K,)."""
    area, n = triangle_geometry(x, tris)
    vt = v[tris].mean(axis=1)                    # prędkość trójkąta
    vn = np.einsum("ij,ij->i", vt, n)            # składowa normalna (skalar)
    v_tan = vt - vn[:, None] * n                 # składowa styczna (wektor)
    s_tan = np.linalg.norm(v_tan, axis=1)
    f = (-0.5 * rho * C_n * area * vn * np.abs(vn))[:, None] * n \
        - (0.5 * rho * C_t * area * s_tan)[:, None] * v_tan
    return f, vt, vn, area


def drag(x: np.ndarray, v: np.ndarray, tris: np.ndarray, rho: float, C_n: float, C_t: float) -> DragResult:
    """Siły oporu wody na węzły skóry dla pozycji x i prędkości v (obie (N, 3))."""
    f, vt, vn, area = triangle_forces(x, v, tris, rho, C_n, C_t)
    nodes = np.zeros_like(x)
    np.add.at(nodes, tris.ravel(), np.repeat(f / 3.0, 3, axis=0))
    # Pochodna |dF_n/dv_n| = ρ C_n A |v_n|: tyle „tłumienia” wnosi jawnie liczony opór.
    # Na węzeł 1/3 pola każdego trójkąta (spec, sekcja 7: c = ρ·C_n·A_węzła·|v_n|).
    c_tri = rho * C_n * area * np.abs(vn)
    damp = np.zeros(len(x))
    np.add.at(damp, tris.ravel(), np.repeat(c_tri / 3.0, 3))
    power = float(np.einsum("ij,ij->", f, vt))
    return DragResult(nodes, f.sum(axis=0), power, damp)


def stability_ratio(node_damping: np.ndarray, node_mass: np.ndarray, dt: float) -> float:
    """max(c·dt/m) po węzłach skóry.

    Opór liczymy z prędkości z POPRZEDNIEGO kroku, czyli jawnie. Dla węzła z tłumieniem c
    jawny krok mnoży prędkość przez (1 − c·dt/m): przy c·dt/m > 1 zmienia znak (drgania
    rosnące), już od ~0.5 wynik jest wyraźnie zafałszowany. Cienka płetwa ma lekkie węzły
    i dużą powierzchnię, więc tam ten stosunek jest największy (spec, sekcja 7).
    """
    m = node_mass[node_damping > 0]
    return float((node_damping[node_damping > 0] * dt / m).max()) if len(m) else 0.0
