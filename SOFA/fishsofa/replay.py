"""Real-time playback of a recording (scripts/record.py) in the SOFA GUI.

A scene without physics: only visual models of the skin and chambers. Each GUI frame the
controller computes which recording frame matches the elapsed wall-clock time and swaps
in the vertex positions. So the playback speed does not depend on how fast the GUI draws:
1 s of recording lasts 1 s (or 1/speed s, e.g. speed = 0.25 is slow motion).
The recording plays in a loop.

Chambers are colored by the recorded pressure (blue = lowest in the rhythm phase,
red = highest); the skin is semi-transparent so they are visible.

Readouts (FISHSOFA_OVERLAY=1, the default): the skin is colored by the displacement
magnitude |u| with a legend, a text panel shows time, pump volume, pressures, tip angle and
displacement and the net water force, and arrows show the water force on each slice of the
tail. The recording stores only node positions and a log, so the slice forces are recomputed
here with the same drag model as the simulation (water.drag), from velocities obtained by
differentiating the recorded positions.
"""
import os
import time

import numpy as np
import Sofa.Core

from fishsofa import fields, hud, mesh_gen, water
from fishsofa.config import TailConfig

SKIN = [0.95, 0.70, 0.30, 0.35]


def _colormap(s: float) -> list:
    """0 -> blue, 1 -> red (via light gray), RGBA."""
    s = float(np.clip(s, 0.0, 1.0))
    lo, mid, hi = np.array([0.16, 0.47, 0.84]), np.array([0.85, 0.85, 0.85]), np.array([0.92, 0.25, 0.15])
    c = lo + (mid - lo) * s * 2 if s < 0.5 else mid + (hi - mid) * (s - 0.5) * 2
    return [*c.tolist(), 1.0]


def build(root, path: str, speed: float = 1.0, overlay: bool = True):
    rec = np.load(path)
    x0 = rec["x"][0].astype(float)
    root.addObject("RequiredPlugin", pluginName=["Sofa.Component.AnimationLoop", "Sofa.GL.Component.Rendering3D",
                                                 "Sofa.Component.Visual", "Sofa.Component.StateContainer",
                                                 "Sofa.Component.Mapping.Linear",
                                                 "Sofa.Component.Topology.Container.Constant"])
    root.addObject("DefaultAnimationLoop")
    root.addObject("VisualStyle", displayFlags="showVisualModels showForceFields")
    if overlay:
        # Plain dark background instead of the default logo pattern, so readouts stay legible.
        root.addObject("RequiredPlugin", pluginName=["Sofa.Component.Setting"])
        root.addObject("BackgroundSetting", color=[0.11, 0.13, 0.16, 1.0])
    root.dt = 1.0 / 60
    root.gravity = [0.0, 0.0, 0.0]
    models = {}
    surfaces = [("chamberL", "tri_chamber_L", _colormap(0.5)), ("chamberR", "tri_chamber_R", _colormap(0.5))]
    if not overlay:
        surfaces.insert(0, ("skin", "tri_outer", SKIN))
    for name, key, color in surfaces:
        tris = rec[key]
        used = np.unique(tris)          # only this surface's vertices (less data per frame)
        remap = np.full(len(x0), -1)
        remap[used] = np.arange(len(used))
        # Positions live in a MechanicalObject, and OglModel gets them via IdentityMapping.
        # Writing directly to OglModel.position does not refresh the on-screen geometry
        # (color does, shape does not); SOFA updates mappings every step.
        node = root.addChild(name)
        dofs = node.addObject("MechanicalObject", name="dofs", template="Vec3d", position=x0[used].tolist())
        ogl = node.addObject("OglModel", name="ogl", position=x0[used].tolist(),
                             triangles=remap[tris].tolist(), color=color)
        node.addObject("IdentityMapping", input="@dofs", output="@ogl")
        models[name] = (dofs, ogl, used)
    extras = None
    if overlay:
        extras = _add_overlay(root, rec, x0)
    root.addObject(ReplayController(name="replay", rec=rec, models=models, speed=speed, extras=extras))
    return root


def _add_overlay(root, rec, x0):
    """Colored skin (DataDisplay + OglColorMap legend), force arrows, text panel."""
    tris = rec["tri_outer"]
    used = np.unique(tris)
    remap = np.full(len(x0), -1)
    remap[used] = np.arange(len(used))
    sections = hud.Sections(rec["points0"].astype(float), used, n=8)
    node_f, slice_f = _water_forces(rec, sections)
    modes = _color_fields(rec, used, node_f)
    first = modes[0]
    root.addObject("RequiredPlugin", pluginName=hud.PLUGINS)
    node = root.addChild("skin")
    node.addObject("MeshTopology", name="topology", triangles=remap[tris].tolist())
    cmap = node.addObject("OglColorMap", name="cmap", colorScheme="Blue to Red", showLegend=True,
                          legendTitle=first["title"], min=0.0, max=first["max"], legendOffset=[70, 330],
                          legendSize=16)
    disp = node.addObject("DataDisplay", name="display", position=x0[used].tolist(),
                          pointData=np.zeros(len(used)).tolist(), userRange=[0.0, first["max"]],
                          transparency=0.55)
    arrows = hud.add_arrows(root, len(sections.groups))
    big = float(np.percentile(np.linalg.norm(slice_f, axis=2), 95))
    arrows[1].showArrowSize = 0.03 / max(big, 1e-9)       # 95th-percentile force -> 30 mm arrow
    panel = hud.Hud(root, 8, size=20)
    return dict(disp=disp, cmap=cmap, used=used, modes=modes, mode=-1, sections=sections, arrows=arrows,
                forces=slice_f, u=modes[0]["data"], hud=panel)


def _water_forces(rec, sections):
    """Water force on every node (F, N, 3) and summed per tail slice (F, K, 3) [N], recomputed
    with the simulation's drag model from velocities of the recorded positions (water only)."""
    t, X = rec["t"].astype(float), rec["x"].astype(float)
    if str(rec["env"]) != "water":
        return None, np.zeros((len(t), len(sections.groups), 3))
    cfg = TailConfig(environment="water")
    V = np.gradient(X, t, axis=0)
    node_f = np.array([water.drag(X[k], V[k], rec["tri_outer"], cfg.rho_water, cfg.drag_C_n,
                                  cfg.drag_C_t).node_forces for k in range(len(t))])
    return node_f, np.array([sections.forces(f) for f in node_f])


def _color_fields(rec, used, node_f) -> list:
    """Skin coloring modes, each a dict(name, title, data (F, n_used), max). The playback cycles
    through them once per loop: displacement, water load (water only), von Mises stress."""
    X = rec["x"].astype(float)
    u = np.linalg.norm(X[:, used] - X[0][None, used], axis=2) * 1e3                 # [mm]
    modes = [dict(name="displacement |u|", title="|u| [mm]", data=u)]
    if node_f is not None:
        area = fields.node_areas(X[0], rec["tri_outer"], X.shape[1])[used]
        load = np.linalg.norm(node_f[:, used], axis=2) / np.maximum(area, 1e-12)  # [Pa]
        modes.append(dict(name="water load on the skin", title="water load [Pa]", data=load, pct=97))
    stress = _stress_cached(rec, X)
    if stress is not None:
        # 95th percentile: the 20x stiffer spine carries the peak stress and would otherwise
        # leave the whole silicone dark blue; above the range the color saturates red.
        modes.append(dict(name="von Mises stress", title="von Mises [kPa]", data=stress[:, used] / 1e3, pct=95))
    for m in modes:
        m["max"] = float(max(np.percentile(m["data"], m.get("pct", 99.5)), 1e-9))
    return modes


def _stress_cached(rec, X):
    """Nodal von Mises stress (F, N) [Pa] for all frames; cached next to the recording because
    it needs one polar decomposition per tetrahedron and frame (a few seconds)."""
    src = str(rec.zip.filename) if hasattr(rec, "zip") and rec.zip is not None else None
    cache = src.replace(".npz", ".stress.npz") if src else None
    if cache and os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(src):
        return np.load(cache)["stress"]
    cfg = TailConfig(environment=str(rec["env"]))
    try:
        mesh = mesh_gen.load(cfg, str(rec["level"]))
    except OSError:
        mesh_gen.ensure(cfg, str(rec["level"]))
        mesh = mesh_gen.load(cfg, str(rec["level"]))
    if mesh.points.shape != X.shape[1:]:
        print("Replay: mesh does not match the recording - no stress coloring")
        return None
    young = np.where(mesh.tet_region == 1, cfg.young_modulus * cfg.spine_E_factor, cfg.young_modulus)
    x0 = X[0]
    Dm_inv = np.linalg.inv(fields.tet_shape(x0, mesh.tets))
    vol = np.abs(np.linalg.det(fields.tet_shape(x0, mesh.tets))) / 6.0
    stress = np.array([fields.to_nodes(fields.von_mises(x0, xk, mesh.tets, young, cfg.poisson_ratio, Dm_inv),
                                       mesh.tets, len(x0), vol) for xk in X], dtype=np.float32)
    if cache:
        np.savez_compressed(cache, stress=stress)
    return stress


class ReplayController(Sofa.Core.Controller):
    def __init__(self, *args, rec, models, speed, extras=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.t, self.x, self.models, self.speed = rec["t"], rec["x"], models, speed
        self.extras, self.env = extras, str(rec["env"])
        t_log = rec["log_t"]
        self.log = {k: np.interp(self.t, t_log, rec[f"log_{k}"]) for k in
                    ("theta", "p_L", "p_R", "V_p", "V_ref", "F_x", "F_y") if f"log_{k}" in rec}
        x0 = rec["x"][0]
        tip = np.where(x0[:, 0] < x0[:, 0].min() + 0.005)[0]      # nodes at the trailing edge
        self.tip_y = (rec["x"][:, tip, 1].mean(axis=1) - x0[tip, 1].mean()) * 1e3   # [mm]
        p_L, p_R, t_log = rec["log_p_L"], rec["log_p_R"], rec["log_t"]
        # Pressure at frame instants (the log has step dt, frames every 1/60 s).
        self.p = {"chamberL": np.interp(self.t, t_log, p_L), "chamberR": np.interp(self.t, t_log, p_R)}
        # Scale from the rhythm phase (after prefill): motion is driven by a ±6 kPa difference
        # on top of a ~53 kPa common pressure; a scale from 0 would hide it. During prefill the
        # color is out of scale.
        m = self.t > float(rec["prefill_time"]) + 0.2
        lo = min(self.p["chamberL"][m].min(), self.p["chamberR"][m].min())
        hi = max(self.p["chamberL"][m].max(), self.p["chamberR"][m].max())
        self.p_range = (lo, max(hi, lo + 1.0))
        self.start = None
        self.last = -1
        print(f"Replay: {rec['env']}, {len(self.t)} frames, {self.t[-1]:.2f} s of recording, speed ×{speed:g}")
        if extras:
            self._add_readouts(len(extras["sections"].groups))

    # Readouts as Data fields: double-click "replay" in the Scene Graph and the ImGui GUI shows
    # them live in its own (readable) font, grouped as below.
    READOUTS = (
        ("time_s", "Time", "recording time [s]"),
        ("pump_volume_ml", "Hydraulics", "V_p: volume moved R -> L [ml]"),
        ("pump_volume_ref_ml", "Hydraulics", "V_ref: commanded volume [ml]"),
        ("p_L_kPa", "Hydraulics", "pressure in chamber L [kPa]"),
        ("p_R_kPa", "Hydraulics", "pressure in chamber R [kPa]"),
        ("dp_kPa", "Hydraulics", "dp = p_L - p_R [kPa]"),
        ("tip_angle_deg", "Displacement", "tip angle [deg]"),
        ("tip_disp_y_mm", "Displacement", "lateral displacement of the trailing edge [mm]"),
        ("max_disp_mm", "Displacement", "largest node displacement |u| [mm]"),
        ("water_Fx_mN", "Forces on the tail", "net water force along x, + = thrust [mN]"),
        ("water_Fy_mN", "Forces on the tail", "net water force sideways [mN]"),
        ("water_F_mN", "Forces on the tail", "magnitude of the net water force [mN]"),
    )

    def _add_readouts(self, n_slices):
        for name, group, help_ in self.READOUTS:
            self.addData(name=name, type="double", value=0.0, help=help_, group=group)
        self.addData(name="slice_Fy_mN", type="vector<double>", value=[0.0] * n_slices,
                     help="sideways water force on each tail slice, root -> tip [mN]", group="Forces on the tail")
        self.addData(name="slice_Fx_mN", type="vector<double>", value=[0.0] * n_slices,
                     help="water force along x on each tail slice, root -> tip [mN]", group="Forces on the tail")

    def onAnimateBeginEvent(self, event):
        now = time.perf_counter()
        if self.start is None:
            self.start = now
        t_rec = ((now - self.start) * self.speed) % self.t[-1]
        k = int(np.searchsorted(self.t, t_rec))
        k = min(k, len(self.t) - 1)
        if k == self.last:
            return
        self.last = k
        x = self.x[k]
        lo, hi = self.p_range
        for name, (dofs, ogl, used) in self.models.items():
            dofs.position.value = x[used]
            if name in self.p:
                ogl.material.value = _material(_colormap((self.p[name][k] - lo) / (hi - lo)))
        if self.extras:
            self._update_overlay(k, x)

    def _update_overlay(self, k, x):
        e, lg = self.extras, self.log
        # SOFA Data setters want float64 (float32 arrays crash the binding for some types).
        xd = np.asarray(x, dtype=np.float64)
        loop = int((time.perf_counter() - self.start) * self.speed // self.t[-1])
        mi = loop % len(e["modes"])
        mode = e["modes"][mi]
        if mi != e["mode"]:                              # new loop: next coloring, new legend
            e["mode"] = mi
            e["cmap"].legendTitle.value = mode["title"]
            e["cmap"].max.value = mode["max"]
            e["disp"].userRange.value = [0.0, mode["max"]]
        e["disp"].position.value = xd[e["used"]]
        e["disp"].pointData.value = np.asarray(mode["data"][k], dtype=np.float64).tolist()
        dofs, ff = e["arrows"]
        dofs.position.value = e["sections"].points(xd)
        ff.forces.value = np.asarray(e["forces"][k], dtype=np.float64)
        dp = (lg["p_L"][k] - lg["p_R"][k]) / 1e3
        F = e["forces"][k] * 1e3                         # [mN] per slice, tip first (x grows to the root)
        vals = dict(time_s=self.t[k], pump_volume_ml=lg["V_p"][k] * 1e6, pump_volume_ref_ml=lg["V_ref"][k] * 1e6,
                    p_L_kPa=lg["p_L"][k] / 1e3, p_R_kPa=lg["p_R"][k] / 1e3, dp_kPa=dp,
                    tip_angle_deg=np.degrees(lg["theta"][k]), tip_disp_y_mm=self.tip_y[k],
                    max_disp_mm=e["u"][k].max(), water_Fx_mN=lg["F_x"][k] * 1e3, water_Fy_mN=lg["F_y"][k] * 1e3,
                    water_F_mN=np.hypot(lg["F_x"][k], lg["F_y"][k]) * 1e3)
        for name, v in vals.items():
            getattr(self, name).value = float(v)
        self.slice_Fy_mN.value = [float(v) for v in F[::-1, 1]]
        self.slice_Fx_mN.value = [float(v) for v in F[::-1, 0]]
        sl = " ".join(f"{v:+5.0f}" for v in F[::-1, 1])
        lines = [f"SOFA  soft tail (FEM) in {self.env}    replay x{self.speed:g}    t = {self.t[k]:4.2f} s"
                 "    (skin field changes every loop)",
                 "",
                 f"HYDRAULICS  V_p {vals['pump_volume_ml']:+5.1f} ml   p_L {vals['p_L_kPa']:4.1f} kPa"
                 f"   p_R {vals['p_R_kPa']:4.1f} kPa   dp {dp:+5.2f} kPa",
                 f"TAIL        tip angle {vals['tip_angle_deg']:+5.1f} deg   tip disp. y {self.tip_y[k]:+5.1f} mm"
                 f"   max |u| {vals['max_disp_mm']:4.1f} mm"]
        if self.env == "water":
            lines += [f"FORCES      water on tail: F_x {vals['water_Fx_mN']:+6.1f} mN (+ = thrust)"
                      f"   F_y {vals['water_Fy_mN']:+6.0f} mN   |F| {vals['water_F_mN']:5.0f} mN",
                      f"            F_y per slice, root -> tip [mN]: {sl}"]
        lines += ["", f"skin: {mode['name']}    chambers: pressure    "
                  + ("arrows: water force per slice" if self.env == "water" else "")]
        e["hud"].show(lines)


def _material(rgba) -> str:
    """OglModel material (SOFA format) with diffuse color rgba."""
    c = " ".join(f"{v:.3f}" for v in rgba)
    return f"Default Diffuse 1 {c} Ambient 1 {c} Specular 0 1 1 1 1 Emissive 0 0 0 0 0 Shininess 0 45"
