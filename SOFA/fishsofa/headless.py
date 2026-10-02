"""Uruchamianie sceny z Pythona, bez GUI (testy, skrypty scenariuszy).

Wymaga `source scripts/env.sh` (moduły Sofa z binarki SOFA na PYTHONPATH).
"""
import time
from dataclasses import dataclass, field

import numpy as np

from fishsofa import geometry
from fishsofa.config import TailConfig

_PLUGINS_LOADED = False


def _sofa():
    """Import SOFA dopiero przy pierwszym użyciu – reszta pakietu działa bez SOFA."""
    global _PLUGINS_LOADED
    import Sofa
    import Sofa.Core
    import Sofa.Simulation
    import SofaRuntime
    if not _PLUGINS_LOADED:
        SofaRuntime.importPlugin("Sofa.Component")
        _PLUGINS_LOADED = True
    return Sofa


@dataclass
class RunLog:
    t: list = field(default_factory=list)          # [s]
    tip: list = field(default_factory=list)        # przemieszczenie centroidu płetwy [m] (3,)
    max_disp: list = field(default_factory=list)   # max |u| po węzłach [m]
    tip_angle: list = field(default_factory=list)  # [rad]
    ms_per_step: float = float("nan")
    init_s: float = float("nan")
    has_nan: bool = False
    x_final: np.ndarray | None = None


def run(cfg: TailConfig, level: str, n_steps: int, mesh_root: str | None = None,
        log_every: int = 1, solver: str = "dynamic") -> RunLog:
    Sofa = _sofa()
    from fishsofa.scene import build_tail

    root = Sofa.Core.Node("root")
    t0 = time.perf_counter()
    h = build_tail(root, cfg, level, mesh_root, solver=solver)
    Sofa.Simulation.init(root)
    log = RunLog(init_s=time.perf_counter() - t0)

    mesh, dofs = h["mesh"], h["dofs"]
    x0 = np.array(dofs.position.value)
    base = geometry.base_center(x0, mesh.base_nodes)
    t1 = time.perf_counter()
    for i in range(1, n_steps + 1):
        Sofa.Simulation.animate(root, root.dt.value)
        if i % log_every == 0 or i == n_steps:
            x = np.array(dofs.position.value)
            if not np.all(np.isfinite(x)):
                log.has_nan = True
                break
            log.t.append(i * root.dt.value)
            log.tip.append(geometry.tip_displacement(x, x0, mesh.fin_nodes))
            log.max_disp.append(float(np.linalg.norm(x - x0, axis=1).max()))
            log.tip_angle.append(geometry.tip_angle(x, base, mesh.fin_nodes))
    log.ms_per_step = 1e3 * (time.perf_counter() - t1) / max(1, i)
    log.x_final = np.array(dofs.position.value)
    Sofa.Simulation.unload(root)
    return log


def static_sag(cfg: TailConfig, level: str, mesh_root: str | None = None, n_steps: int = 1) -> RunLog:
    """Ugięcie statyczne pod ciężarem: jeden krok StaticSolver (Newton) = stan równowagi."""
    return run(cfg, level, n_steps, mesh_root, solver="static")
