"""Hydraulika komór. Etap 2: tylko jednostki ciśnienia (reszta w etapie 4).

Ustalone w etapie 0 (scripts/probe_volume_growth.py): SurfacePressureConstraint
w SOFA v26.06 podaje w polu `pressure` impuls z solvera ograniczeń λ = p·dt, a nie p.
W trybie valueType="pressure" wejście `value` też jest w jednostkach p·dt.
Wszystkie przeliczenia robimy TYLKO tutaj, żeby w reszcie kodu ciśnienie było w Pa.
"""
import numpy as np


def pressure_pa(spc, dt: float) -> float:
    """Ciśnienie w komorze [Pa] z pola `pressure` komponentu SurfacePressureConstraint."""
    return float(np.atleast_1d(spc.pressure.value)[0]) / dt


def pressure_input(p_pa: float, dt: float) -> float:
    """Wartość `value` dla valueType="pressure", odpowiadająca ciśnieniu p_pa [Pa]."""
    return p_pa * dt
