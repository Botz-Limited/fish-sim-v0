"""Tail mesh straight from the CAD model (cfg.geometry = "step", file cfg.step_file).

Usage:  python -m fishsofa.step_mesh --level coarse|medium|fine|test|all   (with bench_config())

What the STEP contains (Fish_Tail.step, 26.10.2026; STEP axes x along the tail, y up, z sideways):
  - 8 open tubes (the chambers, 4 per side, two sizes, ~3 mm wall), x 240–290 mm,
  - silicone body x 290–460 mm with an elliptical pocket in its front face (~4 mm deep),
  - caudal fin: 2 mm plate, x 420–500 mm, its front 40 mm in a slot of the body end,
  - ventral fin: 2 mm plate, partly inside the body underside.
What is added here, because the STEP does not have it:
  - tube end walls: the last END_WALL = 2 mm inside every tube at the back (the tube is glued
    to the body there; part of the tube end lies outside the body front face),
  - holder plate: a step_plate_thickness slab in front of the tubes (x < 240 mm). It closes the
    front ends of the tubes; all its nodes are the "base" (mount) nodes,
  - pocket plug: the pocket in the body front face is filled. In the real tail it holds the
    tube ends / glue; left open it would join the L and R tubes into one cavity.
The insides of the tubes (closed by the plate and the end walls) are the 8 chamber cavities;
the 4 of a side form ONE chamber (one supply line, equal pressure).

Why fTetWild and not a conforming OCC mesh: the STEP parts are not boolean-clean (neighbouring
tubes overlap by ~0.1 mm, the fin faces coincide with its slot in the body, the body skin has its
seam where the fin pierces it). OCC fragment/fuse dropped solids or crashed. Here every part is
only triangulated (gmsh, no booleans) and fTetWild meshes the union of the triangle soup
(robust to overlaps and coincident faces). The material of each tet is found afterwards from its
centroid: inside which part (generalized winding number), with priority plate > fins > tubes > body.

Material regions (tet_region, see config.region_young / region_density):
  0 body silicone, 2 tube, 3 stiff tail tip (body beyond step_tip_start), 4 fin plastic
  (caudal + ventral), 5 holder plate. Region 1 (spine) is not used here.

Output (meshes/step_<level>_<hash>/) has the same files as mesh_gen plus the tubes in
tail_meta.npz (axis end points and outer radii, for the hoop fibers). Coordinates in the SOFA
frame: X = −(x − x_root) (tail along −X, root at X = 0), Y = z (side, +Y = chamber L), Z = y (up).
"""
import argparse
import hashlib
import json
import os

import numpy as np

from fishsofa import PROJECT_DIR
from fishsofa.config import TailConfig, bench_config
from fishsofa.mesh_gen import (TailMesh, _write_obj, _write_vtk_legacy, boundary_faces, open_edges,
                               surface_volume, tet_volumes)

# Bump when a code change alters the meshing result (part of the hash -> meshes are regenerated).
GENERATOR_VERSION = 4
END_WALL = 0.002      # [m] closed back end of every tube
# fTetWild leaves a crack where two parts only touch along a coincident face (seen: tube front
# faces on the holder plate -> 2 of 8 chambers open to the water). Parts that must be joined
# therefore overlap by OVERLAP: the plate reaches into the tubes, body + fins are moved towards
# the tubes, the tube end walls reach into the tube wall and the body. Lengths change by 0.5 mm.
OVERLAP = 0.0005      # [m]
SURFACE_H = 0.0015    # [m] triangle size of the part surfaces handed to fTetWild

BODY, TUBE, TIP, FIN, PLATE = 0, 2, 3, 4, 5
REGION_NAMES = {BODY: "body silicone", TUBE: "tubes", TIP: "stiff tip", FIN: "fins (plastic)",
                PLATE: "holder plate"}


def _step_path(cfg: TailConfig) -> str:
    return cfg.step_file if os.path.isabs(cfg.step_file) else os.path.join(PROJECT_DIR, cfg.step_file)


def _to_sofa(p: np.ndarray, x_root: float) -> np.ndarray:
    """STEP (x tail, y up, z side) -> SOFA (X = −(x − x_root), Y = z, Z = y). det = +1 (no mirror)."""
    p = np.atleast_2d(p)
    return np.column_stack([-(p[:, 0] - x_root), p[:, 2], p[:, 1]])


# ----------------------------------------------------------------------------- parts (gmsh, no booleans between parts)

def _extent(gmsh, dim, tag):
    b = gmsh.model.occ.getBoundingBox(dim, tag)
    return np.array(b[3:]) - np.array(b[:3])


def _inner_curve(gmsh, face):
    """Of the (two) boundary curves of an annular plane face, the smaller one."""
    curves = [abs(c) for _, c in gmsh.model.getBoundary([(2, face)], oriented=False)]
    return min(curves, key=lambda c: np.linalg.norm(_extent(gmsh, 1, c)))


def _faces(gmsh, vol):
    """(plane faces, other faces) of a volume."""
    faces = [abs(f) for _, f in gmsh.model.getBoundary([(3, vol)], oriented=False)]
    planes = [f for f in faces if gmsh.model.getType(2, f) == "Plane"]
    return planes, [f for f in faces if f not in planes]


def _parts(gmsh, cfg: TailConfig):
    """Builds the parts in the OCC kernel. Returns ({region: [volume tags]}, tube data, x_root)."""
    occ = gmsh.model.occ
    gmsh.option.setString("Geometry.OCCTargetUnit", "M")
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)   # tight bounding boxes (B-spline faces)
    vols = [t for d, t in occ.importShapes(_step_path(cfg)) if d == 3]
    occ.synchronize()

    # Classify the solids: fins are the thin plates, the body the largest of the rest.
    thin = [v for v in vols if _extent(gmsh, 3, v).min() < 0.003]
    rest = [v for v in vols if v not in thin]
    body = max(rest, key=lambda v: occ.getMass(3, v))
    tubes = [v for v in rest if v != body]
    if len(thin) != 2 or len(tubes) != 8:
        raise RuntimeError(f"unexpected STEP content: {len(thin)} plates, {len(tubes)} tubes (expected 2, 8)")
    x_root = min(occ.getBoundingBox(3, v)[0] for v in tubes)

    # Tube end walls: a cylinder along x in the last END_WALL of every tube, radius = inner
    # radius at the back end + OVERLAP (reaches into the tube wall), and OVERLAP into the body.
    # (Earlier: lumen ∩ box, scaled up – the scaled B-spline faces broke the surface mesh.)
    # Tube axis + outer radius at both ends for the hoop fibers.
    end_walls, tube_data = [], []
    for v in tubes:
        planes, _ = _faces(gmsh, v)
        planes.sort(key=lambda f: occ.getBoundingBox(2, f)[0])
        ends = []
        for f in planes:
            c = max((abs(c) for _, c in gmsh.model.getBoundary([(2, f)], oriented=False)),
                    key=lambda c: np.linalg.norm(_extent(gmsh, 1, c)))
            b = np.array(occ.getBoundingBox(1, c))
            ends.append(((b[:3] + b[3:]) / 2, float(np.mean((b[3:] - b[:3])[1:]) / 2)))
        tube_data.append(ends)
        b = np.array(occ.getBoundingBox(1, _inner_curve(gmsh, planes[-1])))
        cy, cz = (b[1] + b[4]) / 2, (b[2] + b[5]) / 2
        r_in = float(np.mean((b[3:] - b[:3])[1:]) / 2)
        xb = b[0]
        end_walls.append(occ.addCylinder(xb - END_WALL, cy, cz, END_WALL + OVERLAP, 0, 0, r_in + OVERLAP))
    occ.synchronize()

    # Body + fins towards the tubes (OVERLAP), before the plug is built on the body faces
    # (translating the plug too would move the shared faces twice).
    occ.translate([(3, v) for v in [body] + thin], -OVERLAP, 0, 0)
    occ.synchronize()

    # Pocket plug: pocket wall + pocket bottom + cap on the inner curve of the front rim.
    planes, walls = _faces(gmsh, body)
    planes.sort(key=lambda f: occ.getBoundingBox(2, f)[0])
    rim, bottom = planes[0], planes[1]
    pocket_wall = min(walls, key=lambda f: np.linalg.norm(_extent(gmsh, 2, f)))
    cap = occ.addPlaneSurface([occ.addCurveLoop([_inner_curve(gmsh, rim)])])
    plug = occ.addVolume([occ.addSurfaceLoop([pocket_wall, bottom, cap])])

    # Holder plate in front of the tube ends (covers all tube front faces + 2 mm).
    occ.synchronize()
    b = np.array([occ.getBoundingBox(3, v) for v in tubes])
    lo, hi = b[:, :3].min(axis=0), b[:, 3:].max(axis=0)
    t = cfg.step_plate_thickness
    plate = occ.addBox(x_root - t, lo[1] - 0.002, lo[2] - 0.002, t + OVERLAP,
                       hi[1] - lo[1] + 0.004, hi[2] - lo[2] + 0.004)
    occ.synchronize()
    return {BODY: [body, plug], TUBE: tubes + end_walls, FIN: thin, PLATE: [plate]}, tube_data, x_root


def _triangles(gmsh, vol, pos) -> np.ndarray:
    """Surface triangles (node indices) of one volume, consistently oriented (see _orient)."""
    tris = []
    for _, f in gmsh.model.getBoundary([(3, vol)], oriented=False):
        _, _, en = gmsh.model.mesh.getElements(2, abs(f))
        tris.append(np.vectorize(pos.get)(np.asarray(en[0]).reshape(-1, 3)))
    return _orient(np.vstack(tris))


def _orient(tris: np.ndarray) -> np.ndarray:
    """Consistent orientation of a closed triangulated surface: neighbours across an edge must
    run it in opposite directions. gmsh orients each CAD face by its own parametrization, and
    the sign from getBoundary(oriented=True) did not fix that for these B-spline faces (part
    volumes came out wrong), so the orientation is propagated over the edges here. The global
    sign (outward) is set by the caller from the enclosed volume."""
    tris = tris.copy()
    edge_tris = {}
    for i, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edge_tris.setdefault((min(a, b), max(a, b)), []).append(i)
    done = np.zeros(len(tris), bool)
    for start in range(len(tris)):
        if done[start]:
            continue
        done[start] = True
        stack = [start]
        while stack:
            i = stack.pop()
            t = tris[i]
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                for j in edge_tris[(min(a, b), max(a, b))]:
                    if done[j]:
                        continue
                    u = tris[j]
                    # j must run the shared edge as b -> a; if it runs a -> b, flip it
                    if any(u[k] == a and u[(k + 1) % 3] == b for k in range(3)):
                        tris[j] = u[[0, 2, 1]]
                    done[j] = True
                    stack.append(j)
    return tris


def _soup(cfg: TailConfig):
    """Triangulated parts. Returns (points [m, STEP axes], {region: [tri arrays]}, tube data, x_root)."""
    import gmsh

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("tail_parts")
        parts, tube_data, x_root = _parts(gmsh, cfg)
        gmsh.option.setNumber("Mesh.MeshSizeMax", SURFACE_H)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)   # ≥ 12 elements per 2π on the tubes
        gmsh.model.mesh.generate(2)
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        pos = {int(t): i for i, t in enumerate(tags)}
        points = xyz.reshape(-1, 3)
        tris = {r: [] for r in parts}
        for r, vols in parts.items():
            for v in vols:
                t = _triangles(gmsh, v, pos)
                if surface_volume(points, t) < 0:      # guard: outward orientation
                    t = t[:, [0, 2, 1]]
                tris[r].append(t)
    finally:
        gmsh.finalize()
    return points, tris, tube_data, x_root


# ----------------------------------------------------------------------------- geometry helpers

def winding_number(points: np.ndarray, tris: np.ndarray, chunk: int = 128) -> np.ndarray:
    """Generalized winding number of a closed, outward-oriented triangulated surface tris (K, 3, 3)
    at points (N, 3): ≈ 1 inside, ≈ 0 outside. Van Oosterom–Strackee solid angles."""
    out = np.empty(len(points))
    for i in range(0, len(points), chunk):
        a, b, c = (tris[None, :, k, :] - points[i:i + chunk, None, :] for k in range(3))
        la, lb, lc = (np.linalg.norm(v, axis=2) for v in (a, b, c))
        det = np.einsum("pki,pki->pk", a, np.cross(b, c))
        div = (la * lb * lc + np.einsum("pki,pki->pk", a, b) * lc + np.einsum("pki,pki->pk", b, c) * la
               + np.einsum("pki,pki->pk", c, a) * lb)
        out[i:i + chunk] = 2 * np.arctan2(det, div).sum(axis=1) / (4 * np.pi)
    return out


def _inside(c: np.ndarray, points: np.ndarray, tris_list) -> np.ndarray:
    """Points c inside any of the closed parts (bounding-box prefilter, then winding number)."""
    hit = np.zeros(len(c), bool)
    for t in tris_list:
        p = points[t]
        lo, hi = p.reshape(-1, 3).min(axis=0) - 1e-6, p.reshape(-1, 3).max(axis=0) + 1e-6
        cand = np.flatnonzero(~hit & np.all((c >= lo) & (c <= hi), axis=1))
        if len(cand):
            hit[cand[winding_number(c[cand], p) > 0.5]] = True
    return hit


def _components(tris: np.ndarray) -> np.ndarray:
    """Edge-connected component label of every triangle."""
    parent = np.arange(len(tris))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    edges = np.sort(tris[:, [[0, 1], [1, 2], [2, 0]]].reshape(-1, 2), axis=1)
    owner = np.repeat(np.arange(len(tris)), 3)
    order = np.lexsort((edges[:, 1], edges[:, 0]))
    e, o = edges[order], owner[order]
    same = np.all(e[1:] == e[:-1], axis=1)
    for a, b in zip(o[:-1][same], o[1:][same]):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    return np.array([find(i) for i in range(len(tris))])


# ----------------------------------------------------------------------------- mesh -> TailMesh

def _ftetwild():
    """The compiled fTetWild wrapper of the pytetwild wheel, loaded without the package
    __init__ (that one imports pyvista/VTK, which this environment does not need)."""
    import importlib.machinery
    import importlib.util

    spec = importlib.util.find_spec("pytetwild")
    path = os.path.join(spec.submodule_search_locations[0], "PyfTetWildWrapper.abi3.so")
    loader = importlib.machinery.ExtensionFileLoader("pytetwild.PyfTetWildWrapper", path)
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(mod)
    return mod


def generate(cfg: TailConfig, level: str, root: str | None = None):
    """Returns (TailMesh, tubes) with tubes = {"axis": (8, 2, 3) [m], "radius": (8, 2) [m]} (SOFA frame)."""
    PyfTetWildWrapper = _ftetwild()
    edge, eps = cfg.step_mesh_levels[level]
    sp, tris, tube_data, x_root = _soup(cfg)
    # fTetWild takes ~10 min (coarse); its raw output is cached, so changes of the
    # post-processing below do not need a new run.
    cache = os.path.join(mesh_dir(cfg, level, root), "ftetwild_raw.npz")
    if os.path.exists(cache):
        d = np.load(cache)
        v, tets = d["v"], d["tets"]
    else:
        soup = np.vstack([t for ts in tris.values() for t in ts]).astype(np.uint32)
        empty3, empty4 = np.zeros((0, 3)), np.zeros((0, 4), np.int32)
        v, tets = PyfTetWildWrapper.tetrahedralize_mesh(
            sp, soup, True, False, 0.05, edge, eps, 10.0, False, 0, 80, 6, True, False, False,
            empty3, empty4, np.zeros(0))
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        np.savez(cache, v=v, tets=tets)
    tets = np.asarray(tets, np.int64)

    # Material from the tet centroid (STEP axes): plate > fins > tubes > body.
    c = v[tets].mean(axis=1)
    reg = np.full(len(tets), BODY, np.int8)
    todo = np.ones(len(tets), bool)
    for r in (PLATE, FIN, TUBE):
        idx = np.flatnonzero(todo)
        hit = idx[_inside(c[idx], sp, tris[r])]
        reg[hit] = r
        todo[hit] = False

    points = _to_sofa(v, x_root)
    neg = tet_volumes(points, tets) < 0
    tets[neg] = tets[neg][:, [1, 0, 2, 3]]
    # Stiff tip: body tets whose centroid lies beyond step_tip_start from the root.
    cs = points[tets].mean(axis=1)
    reg[(reg == BODY) & (cs[:, 0] < -cfg.step_tip_start)] = TIP

    # Surfaces: the boundary has 1 outer component and 8 closed cavities (the tube insides).
    faces = boundary_faces(tets)
    comp = _components(faces)
    labels, counts = np.unique(comp, return_counts=True)
    outer = labels[np.argmax(counts)]
    # Inner components: a chamber is one whose node centroid lies on a tube axis (within half the
    # tube radius), one per tube. The others are closed spaces between the round tubes (closed by
    # the plate in front and the body behind) and tiny gaps between the CAD parts: not pressurized,
    # not wetted -> dropped from the outer surface, only reported.
    axes = [(_to_sofa(t[0][0], x_root)[0], _to_sofa(t[1][0], x_root)[0], t[0][1]) for t in tube_data]

    def tube_of(f):
        if abs(surface_volume(points, f)) < 1e-7:     # < 0.1 ml: a gap between CAD parts
            return -1
        c = points[np.unique(f)].mean(axis=0)
        for k, (a, b, r) in enumerate(axes):
            ax = (b - a) / np.linalg.norm(b - a)
            w = c - a
            s = w @ ax
            if np.linalg.norm(w - s * ax) < 0.5 * r and 0 < s < np.linalg.norm(b - a):
                return k
        return -1

    inner = [faces[comp == k] for k in labels if k != outer]
    owner = [tube_of(f) for f in inner]
    cav = [f for f, k in zip(inner, owner) if k >= 0]
    voids = [f for f, k in zip(inner, owner) if k < 0]
    void_ml = [abs(surface_volume(points, f)) * 1e6 for f in voids]
    found = sorted(k for k in owner if k >= 0)
    if found != list(range(8)):
        raise RuntimeError(f"chambers found for tubes {found} (need each of 0..7 once): a chamber is open "
                           f"to the water or split; inner components [ml] "
                           f"{[round(abs(surface_volume(points, f)) * 1e6, 3) for f in inner]}")
    # Cavity faces from boundary_faces point out of the solid = into the cavity; SoftRobots wants
    # them out of the cavity, so the vertex order is reversed. Side from the centroid: Y > 0 -> L.
    side = [np.sign(points[f].reshape(-1, 3)[:, 1].mean()) for f in cav]
    tri_L = np.vstack([f[:, [0, 2, 1]] for f, s in zip(cav, side) if s > 0])
    tri_R = np.vstack([f[:, [0, 2, 1]] for f, s in zip(cav, side) if s < 0])
    tri_outer = faces[comp == outer]

    base = np.unique(tets[reg == PLATE])
    body_end = points[np.unique(tets[(reg == BODY) | (reg == TIP)]), 0].min()
    fin = np.flatnonzero(points[:, 0] < body_end - 1e-9)
    tubes = {"axis": np.array([[_to_sofa(e[0], x_root)[0] for e in t] for t in tube_data]),
             "radius": np.array([[e[1] for e in t] for t in tube_data])}
    # fTetWild optimizes for quality but does not report it: SICN-like proxy = 1 for all (not used).
    sicn = np.ones(len(tets))
    mesh = TailMesh(points, tets, tri_outer, tri_L, tri_R, base, fin, sicn, reg, level, edge, edge)
    tubes["voids_ml"] = np.array(void_ml)
    return mesh, tubes


# ----------------------------------------------------------------------------- report

def _quality(points, tets):
    """Radius ratio 3·r_in/r_circ (1 = regular tet) – a standard tet quality measure."""
    a, b, c, d = (points[tets[:, k]] for k in range(4))
    vol = np.abs(np.einsum("ij,ij->i", b - a, np.cross(c - a, d - a))) / 6
    area = sum(np.linalg.norm(np.cross(q - p, r - p), axis=1) / 2
               for p, q, r in ((a, b, c), (a, b, d), (a, c, d), (b, c, d)))
    r_in = 3 * vol / area
    # circumradius from the edge lengths: R = sqrt((aA+bB+cC)(aA+bB−cC)(aA−bB+cC)(−aA+bB+cC)) / (24 V)
    l = lambda p, q: np.linalg.norm(p - q, axis=1)
    p1, p2, p3 = l(a, b) * l(c, d), l(a, c) * l(b, d), l(a, d) * l(b, c)
    r_c = np.sqrt(np.maximum((p1 + p2 + p3) * (p1 + p2 - p3) * (p1 - p2 + p3) * (-p1 + p2 + p3), 0)) / (24 * vol)
    return 3 * r_in / r_c


def report(mesh: TailMesh, tubes: dict) -> str:
    vol = tet_volumes(mesh.points, mesh.tets)
    q = _quality(mesh.points, mesh.tets)
    lines = [f"[step {mesh.level}] fTetWild edge length {mesh.h_wall * 1e3:.1f} mm",
             f"  nodes {len(mesh.points)}, tets {len(mesh.tets)}, base (holder) nodes {len(mesh.base_nodes)}, "
             f"fin nodes {len(mesh.fin_nodes)}",
             f"  quality (radius ratio, 1 = regular): min {q.min():.3f}, 1st percentile {np.percentile(q, 1):.3f}, "
             f"tets with volume ≤ 0: {int((vol <= 0).sum())}",
             f"  length root -> fin tip {-mesh.points[:, 0].min() * 1e3:.1f} mm",
             f"  cavities L/R {surface_volume(mesh.points, mesh.tri_chamber_L) * 1e6:.2f} / "
             f"{surface_volume(mesh.points, mesh.tri_chamber_R) * 1e6:.2f} ml, open edges outer/L/R "
             f"{[open_edges(mesh.tri_outer), open_edges(mesh.tri_chamber_L), open_edges(mesh.tri_chamber_R)]}"]
    for r, name in REGION_NAMES.items():
        lines.append(f"  {name:15s} {vol[mesh.tet_region == r].sum() * 1e6:7.1f} cm³")
    lines.append(f"  tubes: outer radius front {np.round(tubes['radius'][:, 0] * 1e3, 1)} mm")
    lines.append(f"  closed voids between the tubes / CAD parts (not chambers): {np.round(tubes['voids_ml'], 3)} ml")
    return "\n".join(lines)


# ----------------------------------------------------------------------------- save / load

def _hash(cfg: TailConfig, level: str) -> str:
    with open(_step_path(cfg), "rb") as f:
        step = hashlib.sha1(f.read()).hexdigest()
    d = {"step": step, "level": list(cfg.step_mesh_levels[level]), "plate": cfg.step_plate_thickness,
         "tip": cfg.step_tip_start, "generator": GENERATOR_VERSION}
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:12]


def mesh_dir(cfg: TailConfig, level: str, root: str | None = None) -> str:
    base = root if root is not None else os.path.join(PROJECT_DIR, cfg.mesh_dir)
    return os.path.join(base, f"step_{level}_{_hash(cfg, level)}")


def save(mesh: TailMesh, tubes: dict, cfg: TailConfig, root: str | None = None) -> str:
    out = mesh_dir(cfg, mesh.level, root)
    os.makedirs(out, exist_ok=True)
    _write_vtk_legacy(os.path.join(out, "tail.vtk"), mesh.points, mesh.tets)
    _write_obj(os.path.join(out, "chamber_L.obj"), mesh.points, mesh.tri_chamber_L)
    _write_obj(os.path.join(out, "chamber_R.obj"), mesh.points, mesh.tri_chamber_R)
    _write_obj(os.path.join(out, "outer.obj"), mesh.points, mesh.tri_outer)
    np.savez(os.path.join(out, "tail_meta.npz"),
             points=mesh.points, tets=mesh.tets, tri_outer=mesh.tri_outer,
             tri_chamber_L=mesh.tri_chamber_L, tri_chamber_R=mesh.tri_chamber_R,
             base_nodes=mesh.base_nodes, fin_nodes=mesh.fin_nodes, sicn=mesh.sicn,
             tet_region=mesh.tet_region, level=mesh.level, h_wall=mesh.h_wall, h_far=mesh.h_far,
             tube_axis=tubes["axis"], tube_radius=tubes["radius"], voids_ml=tubes["voids_ml"], geometry_hash=_hash(cfg, mesh.level))
    with open(os.path.join(out, "report.txt"), "w") as f:
        f.write(report(mesh, tubes) + "\n")
    return out


def load(cfg: TailConfig, level: str, root: str | None = None) -> TailMesh:
    d = np.load(os.path.join(mesh_dir(cfg, level, root), "tail_meta.npz"))
    # Mount nodes: only the front face of the (rigid, E = young_fin) holder plate, X = +thickness.
    # Fixing / tying all plate nodes gives the same motion with ~3× more constraints.
    base = d["base_nodes"]
    base = base[d["points"][base, 0] > cfg.step_plate_thickness - 1e-6]
    return TailMesh(d["points"], d["tets"], d["tri_outer"], d["tri_chamber_L"], d["tri_chamber_R"],
                    base, d["fin_nodes"], d["sicn"], d["tet_region"], str(d["level"]),
                    float(d["h_wall"]), float(d["h_far"]))


def load_tubes(cfg: TailConfig, level: str, root: str | None = None) -> dict:
    d = np.load(os.path.join(mesh_dir(cfg, level, root), "tail_meta.npz"))
    return {"axis": d["tube_axis"], "radius": d["tube_radius"]}


def ensure(cfg: TailConfig, level: str, root: str | None = None) -> str:
    out = mesh_dir(cfg, level, root)
    meta = os.path.join(out, "tail_meta.npz")
    if os.path.exists(meta) and str(np.load(meta)["geometry_hash"]) == _hash(cfg, level):
        return out
    mesh, tubes = generate(cfg, level, root)
    return save(mesh, tubes, cfg, root)


def main():
    cfg = bench_config()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--level", default="coarse", choices=list(cfg.step_mesh_levels) + ["all"])
    args = ap.parse_args()
    for lv in (list(cfg.step_mesh_levels) if args.level == "all" else [args.level]):
        mesh, tubes = generate(cfg, lv)
        out = save(mesh, tubes, cfg)
        print(report(mesh, tubes))
        print(f"  -> {out}\n")


if __name__ == "__main__":
    main()
