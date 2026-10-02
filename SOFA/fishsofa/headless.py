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


# ----------------------------------------------------------------------------- etap 2: quasi-statyka

@dataclass
class QuasiStaticCurve:
    dV_target: list = field(default_factory=list)  # [m³]
    dV: list = field(default_factory=list)         # zmierzony przyrost objętości wnęki [m³]
    p: list = field(default_factory=list)          # [Pa]
    tip_angle: list = field(default_factory=list)  # [rad]
    bulge: list = field(default_factory=list)      # wydymanie ścianki zewnętrznej [m]
    ke_ratio: list = field(default_factory=list)   # energia kinetyczna / praca ciśnienia
    v0: float = float("nan")                       # objętość wnęki w spoczynku [m³]
    wall_s: float = float("nan")


def _bulge_probe(mesh, cfg: TailConfig, side: int):
    """Węzły do pomiaru wydymania: najbardziej zewnętrzny węzeł skóry po stronie komory
    i węzeł najbliżej osi (y = z = 0), oba w przekroju w połowie długości komory."""
    x1, x2 = cfg.chamber_x_range
    xm = 0.5 * (x1 + x2)
    pts = mesh.points
    near = np.abs(pts[:, 0] - xm) < 0.6 * mesh.h_wall
    skin = np.zeros(len(pts), bool)
    skin[np.unique(mesh.tri_outer)] = True
    outer = np.flatnonzero(near & skin)
    outer = outer[np.argmax(side * pts[outer, 1])]
    cand = np.flatnonzero(near)
    center = cand[np.argmin(pts[cand, 1] ** 2 + pts[cand, 2] ** 2)]
    return outer, center


def quasi_static_sweep(cfg: TailConfig, level: str, dV_targets, side: str = "L",
                       mesh_root: str | None = None, dt: float = 0.05, ramp_steps: int = 4,
                       max_hold_steps: int = 60, ke_tol: float = 0.01,
                       p_stop: float | None = None, max_fraction: float | None = None) -> QuasiStaticCurve:
    """Krzywa ciśnienie–objętość–kąt dla jednej komory (druga odpowietrzona), quasi-statycznie.

    Metoda „pseudo-statyki”: niejawny Euler z dużym krokiem (dt = 50 ms). Bezwładność
    (M/dt²) jest wtedy mała wobec sztywności, więc każdy krok prawie od razu trafia
    w równowagę. Sprawdzone w planie etapu 2: stan końcowy taki sam jak przy wolnej
    rampie z dt = 2 ms (1950.4 Pa w obu), przy 5–25× mniejszym koszcie. Statyka
    (StaticSolver) odpada, bo nie działa z ograniczeniami Lagrange'a komory.

    Kryterium „quasi-statyczności” (spec, etap 2): po dojściu do każdego punktu trzymamy
    objętość, aż energia kinetyczna < ke_tol · praca ciśnienia ∫p dV (dla procesu
    quasi-statycznego praca ciśnienia ≈ zmagazynowana energia odkształcenia).
    Zawsze solver "ldl" – "warp" z komorą daje błędną równowagę (README).
    """
    from dataclasses import replace

    from fishsofa import hydraulics
    from fishsofa.scene import build_tail

    Sofa = _sofa()
    cfg = replace(cfg, dt=dt, linear_solver="ldl")
    other = "R" if side == "L" else "L"
    root = Sofa.Core.Node("root")
    h = build_tail(root, cfg, level, mesh_root, chambers={side: "volume", other: "vented"})
    Sofa.Simulation.init(root)
    spc, dofs, mesh, m = h["chambers"][side], h["dofs"], h["mesh"], h["masses"].node_mass
    x0 = np.array(dofs.position.value)
    base = geometry.base_center(x0, mesh.base_nodes)
    i_out, i_cen = _bulge_probe(mesh, cfg, +1 if side == "L" else -1)
    sgn = 1.0 if side == "L" else -1.0

    res = QuasiStaticCurve(v0=float(spc.initialCavityVolume.value))
    work, p_prev, dV_prev, target_prev = 0.0, 0.0, 0.0, 0.0
    t0 = time.perf_counter()
    for target in dV_targets:
        if max_fraction is not None and target > max_fraction * res.v0:
            break
        steps = 0
        while True:
            steps += 1
            frac = min(1.0, steps / ramp_steps)
            spc.value = [target_prev + frac * (target - target_prev)]
            Sofa.Simulation.animate(root, dt)
            x = np.array(dofs.position.value)
            v = np.array(dofs.velocity.value)
            dV = float(spc.cavityVolume.value) - res.v0
            p = hydraulics.pressure_pa(spc, dt)
            work += 0.5 * (p + p_prev) * (dV - dV_prev)   # ∫p dV (trapezy)
            p_prev, dV_prev = p, dV
            ke = 0.5 * float((m * (v ** 2).sum(axis=1)).sum())
            ratio = ke / work if work > 0 else float("inf")
            # steps > ramp_steps: co najmniej jeden krok trzymania, bo cavityVolume SOFA
            # liczy PRZED rozwiązaniem kroku (odczyt spóźnia się o jeden krok).
            if (steps > ramp_steps and ratio < ke_tol) or steps >= ramp_steps + max_hold_steps:
                break
        res.dV_target.append(target)
        res.dV.append(dV)
        res.p.append(p)
        res.tip_angle.append(geometry.tip_angle(x, base, mesh.fin_nodes))
        u = x - x0
        res.bulge.append(sgn * (u[i_out, 1] - u[i_cen, 1]))
        res.ke_ratio.append(ratio)
        target_prev = target
        if p_stop is not None and p > p_stop:
            break
    res.wall_s = time.perf_counter() - t0
    Sofa.Simulation.unload(root)
    return res
