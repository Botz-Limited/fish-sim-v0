"""SOFA controller for the antagonistic hydraulics (stage 4): the L↔R pump drives chamber volumes.

Every step (onAnimateBeginEvent, i.e. BEFORE the step is solved):
  1. read p_L, p_R from the previous step (hydraulics.pressure_pa),
  2. step the pump model (hydraulics.TailHydraulics) -> prescribed ΔV_L, ΔV_R at step end,
  3. set `value` of both SurfacePressureConstraints (volumeGrowth),
  4. write a log row.
A log row describes the state at the start of the step: positions, pressures and measured
volumes are the previous step's result (SOFA computes cavityVolume before solving anyway).
"""
import numpy as np
import Sofa.Core

from fishsofa import geometry, hud, hydraulics, water

LOG_KEYS = ("t", "V_ref", "V_p", "u", "Q", "Q_valve", "valve_open", "dV_L_cmd", "dV_R_cmd",
            "dV_L", "dV_R", "p_L", "p_R", "theta", "cs_iterations", "cs_error")


class FlapController(Sofa.Core.Controller):
    def __init__(self, *args, root, handles, cfg, readouts=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.root, self.cfg = root, cfg
        self.water = handles.get("water")
        self.hud = self.arrows = None
        if readouts:
            self._add_readouts(handles)
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
        if self.base is None:   # first step: rest state
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
        if self.hud is not None:
            self._show(t, s, p_L, p_R, x)

    def _add_readouts(self, handles):
        """Text panel and water-force arrows in the GUI (scene.py, FISHSOFA_OVERLAY=1)."""
        self.hud = hud.Hud(self.root, 6, size=20)
        if self.water is not None:
            mesh = handles["mesh"]
            self.sections = hud.Sections(mesh.points, np.unique(mesh.tri_outer), n=8)
            self.arrows = hud.add_arrows(self.root, len(self.sections.groups))
            self.arrows[1].showArrowSize = 0.1          # [m/N]: 0.3 N on a slice -> 30 mm arrow

    def _show(self, t, s, p_L, p_R, x):
        x0 = self.mesh.points
        theta = self.log["theta"][-1]
        tip = geometry.tip_displacement(x, x0, self.mesh.fin_nodes) * 1e3
        u_max = float(np.linalg.norm(x - x0, axis=1).max() * 1e3)
        lines = [f"SOFA  soft tail (FEM) in {self.cfg.environment}    live simulation    t = {t:5.3f} s",
                 f"HYDRAULICS  V_p {s.V_p * 1e6:+5.1f} ml (ref {s.V_ref * 1e6:+5.1f})   p_L {p_L / 1e3:4.1f} kPa"
                 f"   p_R {p_R / 1e3:4.1f} kPa   dp {(p_L - p_R) / 1e3:+5.2f} kPa",
                 f"TAIL        tip angle {np.degrees(theta):+5.1f} deg   tip disp. y {tip[1]:+5.1f} mm"
                 f"   max |u| {u_max:4.1f} mm"]
        if self.water is not None and self.water.last is not None:
            d = self.water.last
            F = self.sections.forces(d.node_forces)
            self.arrows[0].position.value = self.sections.points(x)
            self.arrows[1].forces.value = F
            lines += [f"FORCES      water on tail: F_x {d.total[0] * 1e3:+6.1f} mN (+ = thrust)"
                      f"   F_y {d.total[1] * 1e3:+6.0f} mN   drag power {d.power * 1e3:+6.1f} mW",
                      "            F_y per slice, root -> tip [mN]: "
                      + " ".join(f"{v:+5.0f}" for v in F[::-1, 1] * 1e3),
                      "arrows: water force per slice"]
        self.hud.show(lines)


WATER_LOG_KEYS = ("t", "F_x", "F_y", "F_z", "drag_power", "stability")


class WaterDragController(Sofa.Core.Controller):
    """Water drag (stage 5): every step computes drag forces from node velocities and
    writes them into the ConstantForceField "water" on the tail skin.

    Computed at the start of the step from positions and velocities at the end of the
    previous step, i.e. EXPLICITLY: the force is constant within the solved step. Simple,
    but it limits the time step (water.stability_ratio, spec section 7) – the ratio
    c·dt/m is logged every step.

    Log: F = net water force ON THE TAIL [N] (F_x > 0 pushes the tail, and through the
    fixation the whole fish, forward = thrust), drag power [W], max(c·dt/m).
    """

    def __init__(self, *args, root, handles, force_field, cfg, **kwargs):
        super().__init__(*args, **kwargs)
        self.root, self.cfg, self.ff = root, cfg, force_field
        self.dofs, mesh = handles["dofs"], handles["mesh"]
        self.tris = mesh.tri_outer
        self.skin = np.unique(mesh.tri_outer)
        self.node_mass = handles["masses"].node_mass
        self.log = {k: [] for k in WATER_LOG_KEYS}
        self.last = None            # last DragResult (for the GUI readouts)

    def onAnimateBeginEvent(self, event):
        x = np.array(self.dofs.position.value)
        v = np.array(self.dofs.velocity.value)
        d = water.drag(x, v, self.tris, self.cfg.rho_water, self.cfg.drag_C_n, self.cfg.drag_C_t)
        self.ff.forces.value = d.node_forces[self.skin]
        self.last = d
        lg = self.log
        lg["t"].append(self.root.time.value)
        lg["F_x"].append(float(d.total[0]))
        lg["F_y"].append(float(d.total[1]))
        lg["F_z"].append(float(d.total[2]))
        lg["drag_power"].append(d.power)
        lg["stability"].append(water.stability_ratio(d.node_damping, self.node_mass, self.root.dt.value))


def _data(obj, name):
    """Component data field, or NaN if this SOFA version does not have it."""
    d = obj.findData(name) if obj is not None else None
    return float(d.value) if d is not None else float("nan")
