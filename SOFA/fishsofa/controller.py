"""Kontroler SOFA hydrauliki antagonistycznej (etap 4): pompa L↔R steruje objętościami komór.

W każdym kroku (onAnimateBeginEvent, czyli PRZED rozwiązaniem kroku):
  1. odczyt p_L, p_R z poprzedniego kroku (hydraulics.pressure_pa),
  2. krok modelu pompy (hydraulics.TailHydraulics) -> zadane ΔV_L, ΔV_R na koniec kroku,
  3. ustawienie `value` obu SurfacePressureConstraint (volumeGrowth),
  4. zapis wiersza logu.
Wiersz logu dotyczy stanu na początku kroku: pozycje, ciśnienia i zmierzone objętości
to wynik poprzedniego kroku (cavityVolume SOFA i tak liczy przed rozwiązaniem kroku).
"""
import numpy as np
import Sofa.Core

from fishsofa import geometry, hydraulics

LOG_KEYS = ("t", "V_ref", "V_p", "u", "Q", "Q_valve", "valve_open", "dV_L_cmd", "dV_R_cmd",
            "dV_L", "dV_R", "p_L", "p_R", "theta", "cs_iterations", "cs_error")


class FlapController(Sofa.Core.Controller):
    def __init__(self, *args, root, handles, cfg, **kwargs):
        super().__init__(*args, **kwargs)
        self.root, self.cfg = root, cfg
        self.spc_L, self.spc_R = handles["chambers"]["L"], handles["chambers"]["R"]
        self.dofs, self.mesh = handles["dofs"], handles["mesh"]
        self.cs = next((o for o in root.objects if "ConstraintSolver" in o.getClassName()), None)
        self.hyd = hydraulics.TailHydraulics(cfg)
        self.log = {k: [] for k in LOG_KEYS}
        self.base = None

    def onAnimateBeginEvent(self, event):
        dt = self.root.dt.value
        t = self.root.time.value
        x = np.array(self.dofs.position.value)
        if self.base is None:   # pierwszy krok: stan spoczynkowy
            self.base = geometry.base_center(x, self.mesh.base_nodes)
        p_L = hydraulics.pressure_pa(self.spc_L, dt)
        p_R = hydraulics.pressure_pa(self.spc_R, dt)
        s = self.hyd.step(t, p_L - p_R, dt)
        self.spc_L.value = [s.dV_L]
        self.spc_R.value = [s.dV_R]

        lg = self.log
        lg["t"].append(t)
        for k in ("V_ref", "V_p", "u", "Q", "Q_valve", "valve_open"):
            lg[k].append(getattr(s, k))
        lg["dV_L_cmd"].append(s.dV_L)
        lg["dV_R_cmd"].append(s.dV_R)
        lg["dV_L"].append(float(self.spc_L.cavityVolume.value) - float(self.spc_L.initialCavityVolume.value))
        lg["dV_R"].append(float(self.spc_R.cavityVolume.value) - float(self.spc_R.initialCavityVolume.value))
        lg["p_L"].append(p_L)
        lg["p_R"].append(p_R)
        lg["theta"].append(geometry.tip_angle(x, self.base, self.mesh.fin_nodes))
        lg["cs_iterations"].append(_data(self.cs, "currentIterations"))
        lg["cs_error"].append(_data(self.cs, "currentError"))


def _data(obj, name):
    """Pole komponentu albo NaN, gdy ta wersja SOFA go nie ma."""
    d = obj.findData(name) if obj is not None else None
    return float(d.value) if d is not None else float("nan")
