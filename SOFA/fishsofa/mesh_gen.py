"""Tail mesh generation: gmsh (half) -> mirror reflection -> files for SOFA.

Usage:  python -m fishsofa.mesh_gen --level coarse|medium|fine|test|all

Why half + mirror: gmsh meshing is not symmetric, and the symmetry test
(chamber L vs R) should check the hydraulics code, not an accident of node placement.
We mesh the half y ≥ 0 (one chamber) and obtain the other half by reflecting
y -> −y. Nodes on the plane y = 0 are shared by both halves.

What is produced in meshes/<level>/:
  tail.vtk        – volume mesh (tetrahedra) for MeshVTKLoader,
  chamber_L.obj   – cavity surface of the left chamber (+Y) for SurfacePressureConstraint,
  chamber_R.obj   – same for the right one (−Y),
  outer.obj       – outer surface of the tail (water forces, visualization),
  tail_meta.npz   – the same data as FEM node index arrays + metadata.

Triangle orientation conventions (checked in tests):
  outer   – normals pointing OUT of the solid (into the water),
  chamber – normals pointing OUT OF THE CAVITY, i.e. into the silicone. As in the SoftRobots
            examples: then a positive volume increase gives a positive pressure
            (established in stage 0 on the bunny mesh).
"""
import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass

import numpy as np

from fishsofa import PROJECT_DIR
from fishsofa.config import TailConfig

# Generator version: a code change that alters the meshing result bumps this number
# so that ensure() regenerates the meshes (it is part of _geometry_hash).
GENERATOR_VERSION = 4

# Faces of a positive-volume tet (a,b,c,d), with normals pointing OUT of the tet.
_TET_FACES = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]])


@dataclass
class TailMesh:
    points: np.ndarray       # (N, 3) [m]
    tets: np.ndarray         # (M, 4) node indices, every tet volume > 0
    tri_outer: np.ndarray    # (K, 3) normals pointing out of the solid
    tri_chamber_L: np.ndarray  # normals pointing out of the cavity (SoftRobots convention)
    tri_chamber_R: np.ndarray
    base_nodes: np.ndarray   # nodes of the front wall x = 0 (mount)
    fin_nodes: np.ndarray    # fin nodes beyond the body end (tip measurement)
    sicn: np.ndarray         # gmsh element quality (signed inverse condition number), half mesh
    tet_region: np.ndarray   # (M,) 0 = silicone, 1 = septum / spine (center |y| ≤ septum/2, within the body)
    level: str
    h_wall: float
    h_far: float


# ----------------------------------------------------------------------------- gmsh

def _build_half_geometry(gmsh, cfg: TailConfig):
    """Geometry of the tail half (y ≥ 0) in the OpenCASCADE kernel. Returns the solid's dimtags."""
    occ = gmsh.model.occ
    L = cfg.tail_length

    def ellipse_loop(x, ry, rz):
        # Ellipse in the YZ plane (normal = X axis). gmsh requires the first semi-axis
        # (along xAxis) to be the larger one, and our cross-section is taller than wide (rz > ry).
        c = occ.addEllipse(x, 0, 0, rz, ry, zAxis=[1, 0, 0], xAxis=[0, 0, 1])
        return occ.addCurveLoop([c])

    # Body: ruled surface (makeRuled) between the root ellipse and the end ellipse,
    # i.e. a linear taper of the cross-section, as with taper in MuJoCo.
    s_end = cfg.scale_at(-L)
    body = occ.addThruSections([ellipse_loop(0.0, cfg.ry0, cfg.rz0),
                                ellipse_loop(-L, cfg.ry0 * s_end, cfg.rz0 * s_end)],
                               makeSolid=True, makeRuled=True)

    # Chamber cavity: the same shape shrunk by the wall thickness, clipped to the
    # chamber x range and to y ≥ septum/2 (half of the septum lies in this half).
    x1, x2 = cfg.chamber_x_range
    w = cfg.wall_thickness
    s1, s2 = cfg.scale_at(x1), cfg.scale_at(x2)
    cavity = occ.addThruSections([ellipse_loop(x1, cfg.ry0 * s1 - w, cfg.rz0 * s1 - w),
                                  ellipse_loop(x2, cfg.ry0 * s2 - w, cfg.rz0 * s2 - w)],
                                 makeSolid=True, makeRuled=True)
    cavity, _ = occ.intersect(cavity, [(3, occ.addBox(-1, cfg.septum_thickness / 2, -1, 2, 1, 2))])

    # Fin: elliptical disk in the XZ plane extruded along Y over the full thickness.
    disk = occ.addDisk(cfg.fin_center_x, -cfg.fin_thickness / 2, 0, cfg.fin_semi_z, cfg.fin_semi_x,
                       zAxis=[0, 1, 0], xAxis=[0, 0, 1])
    fin = [e for e in occ.extrude([(2, disk)], 0, cfg.fin_thickness, 0) if e[0] == 3]

    solid, _ = occ.fuse(body, fin)
    solid, _ = occ.intersect(solid, [(3, occ.addBox(-1, 0, -1, 2, 1, 2))])  # half y ≥ 0
    solid, _ = occ.cut(solid, cavity)
    occ.synchronize()
    if len(solid) != 1:
        raise RuntimeError(f"expected one solid, got {len(solid)}")

    return solid


def _mesh_half(cfg: TailConfig, h_wall: float, h_far: float):
    """Meshes the tail half. Returns (points, tets, SICN)."""
    import gmsh

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("tail_half")
        solid = _build_half_geometry(gmsh, cfg)

        # Element size: h_wall near surfaces (thin chamber walls, fin,
        # tail skin), growing to h_far deep inside the solid. Distance computes the distance
        # from the surfaces, Threshold maps it to an element size.
        surfaces = [t for _, t in gmsh.model.getBoundary(solid, oriented=False)]
        fld = gmsh.model.mesh.field
        dist = fld.add("Distance")
        fld.setNumbers(dist, "SurfacesList", surfaces)
        fld.setNumber(dist, "Sampling", 40)
        thr = fld.add("Threshold")
        fld.setNumber(thr, "InField", dist)
        fld.setNumber(thr, "SizeMin", h_wall)
        fld.setNumber(thr, "SizeMax", h_far)
        fld.setNumber(thr, "DistMin", 0.5 * cfg.wall_thickness)
        fld.setNumber(thr, "DistMax", 3.0 * cfg.wall_thickness)
        fld.setAsBackgroundMesh(thr)
        for opt in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints",
                    "Mesh.MeshSizeFromCurvature"):
            gmsh.option.setNumber(opt, 0)
        gmsh.option.setNumber("Mesh.Optimize", 1)  # improve the worst elements
        gmsh.model.mesh.generate(3)

        tags, coords, _ = gmsh.model.mesh.getNodes()
        coords = coords.reshape(-1, 3)
        _, elem_tags, elem_nodes = gmsh.model.mesh.getElements(3)
        tet_tags = np.asarray(elem_tags[0])
        tet_nodes = np.asarray(elem_nodes[0]).reshape(-1, 4)
        sicn = np.asarray(gmsh.model.mesh.getElementQualities(tet_tags, "minSICN"))
    finally:
        gmsh.finalize()

    # Compact numbering: only nodes used by tets, indices from 0.
    used = np.unique(tet_nodes)
    tag_to_idx = {int(t): i for i, t in enumerate(used)}
    tag_pos = {int(t): i for i, t in enumerate(tags)}
    points = coords[[tag_pos[int(t)] for t in used]]
    tets = np.vectorize(tag_to_idx.get)(tet_nodes)
    return points, tets, sicn


# ----------------------------------------------------------------------------- mesh geometry (numpy)

def tet_volumes(points, tets):
    a, b, c, d = (points[tets[:, k]] for k in range(4))
    return np.einsum("ij,ij->i", b - a, np.cross(c - a, d - a)) / 6.0


def surface_volume(points, tris):
    """Signed volume enclosed by a surface (Gauss theorem). > 0 = outward normals."""
    p0, p1, p2 = (points[tris[:, k]] for k in range(3))
    return float(np.einsum("ij,ij->i", p0, np.cross(p1, p2)).sum() / 6.0)


def boundary_faces(tets):
    """Faces belonging to exactly one tet, with normals pointing out of the solid."""
    faces = tets[:, _TET_FACES].reshape(-1, 3)
    key = np.sort(faces, axis=1)
    _, inv, counts = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    return faces[counts[inv.ravel()] == 1]


def _mirror(points, tets, tol=1e-9):
    """Reflection y -> −y. Nodes with |y| < tol stay shared."""
    n = len(points)
    on_plane = np.abs(points[:, 1]) < tol
    # Nodes just next to the plane but not on it would indicate a geometry error (a gap).
    if np.any(points[:, 1] < -tol):
        raise RuntimeError("half mesh has nodes with y < 0")
    off = np.flatnonzero(~on_plane)
    mirror_idx = np.arange(n)
    mirror_idx[off] = n + np.arange(len(off))
    mirrored_pts = points[off] * np.array([1.0, -1.0, 1.0])
    pts_full = np.vstack([points, mirrored_pts])
    pts_full[np.flatnonzero(on_plane), 1] = 0.0
    # Reflection flips the tet orientation (the volume changes sign) – swapping two
    # vertices restores a positive volume.
    tets_m = mirror_idx[tets][:, [1, 0, 2, 3]]
    tets_full = np.vstack([tets, tets_m])
    return pts_full, tets_full


def _in_cavity(cfg: TailConfig, c: np.ndarray, side: int) -> np.ndarray:
    """Whether points c (triangle centers) lie on the chamber cavity on side side (+1 = L, −1 = R).

    The cavity is an elliptical cross-section (tail semi-axes minus the wall) for x within the
    chamber range and |y| ≥ septum/2. We test an outline enlarged by half a wall: it catches the
    cavity triangles and rejects the tail skin (a full wall away) and the symmetry plane y = 0.
    Note: an earlier version located the cavity surfaces via gmsh bounding boxes, but
    OpenCASCADE reports overly loose bboxes for B-spline surfaces and part of the cavity was lost.
    """
    x1, x2 = cfg.chamber_x_range
    w, tol = cfg.wall_thickness, 1e-6
    s = np.array([cfg.scale_at(x) for x in c[:, 0]])
    ry = cfg.ry0 * s - w + w / 2
    rz = cfg.rz0 * s - w + w / 2
    y = side * c[:, 1]
    return ((c[:, 0] <= x1 + w / 2) & (c[:, 0] >= x2 - w / 2) & (y >= cfg.septum_thickness / 2 - tol)
            & ((y / ry) ** 2 + (c[:, 2] / rz) ** 2 <= 1.0))


def generate(cfg: TailConfig, level: str) -> TailMesh:
    h_wall, h_far = cfg.mesh_levels[level]
    points, tets, sicn = _mesh_half(cfg, h_wall, h_far)

    # gmsh usually returns positive-volume tets; we fix them just in case.
    neg = tet_volumes(points, tets) < 0
    tets[neg] = tets[neg][:, [1, 0, 2, 3]]

    points, tets = _mirror(points, tets)

    faces = boundary_faces(tets)
    centers = points[faces].mean(axis=1)
    in_L = _in_cavity(cfg, centers, +1)
    in_R = _in_cavity(cfg, centers, -1)
    # Cavity faces from boundary_faces have normals pointing out of the solid = INTO the cavity.
    # SoftRobots wants the opposite (out of the cavity), so we reverse the vertex order.
    tri_L = faces[in_L][:, [0, 2, 1]]
    tri_R = faces[in_R][:, [0, 2, 1]]
    tri_outer = faces[~(in_L | in_R)]

    L = cfg.tail_length
    base = np.flatnonzero(np.abs(points[:, 0]) < 1e-9)
    fin = np.flatnonzero(points[:, 0] < -L - 1e-9)
    region = _tet_regions(cfg, points, tets)
    return TailMesh(points, tets, tri_outer, tri_L, tri_R, base, fin, sicn, region, level, h_wall, h_far)


def _tet_regions(cfg: TailConfig, points, tets):
    """Material region of each tet: 1 = septum/spine, 0 = rest of the silicone.

    Criterion on the tet center: |y| ≤ septum/2 and x within the body (−L ≤ x ≤ 0). With a mesh
    of ~1 element across the septum this is an approximation (the report gives the region volume).
    """
    c = points[tets].mean(axis=1)
    return ((np.abs(c[:, 1]) <= cfg.septum_thickness / 2) & (c[:, 0] >= -cfg.tail_length)).astype(np.int8)



# ----------------------------------------------------------------------------- quality report

def _mean_edge(points, tets, mask):
    sel = tets[mask]
    if len(sel) == 0:
        return float("nan")
    e = [np.linalg.norm(points[sel[:, i]] - points[sel[:, j]], axis=1)
         for i, j in ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))]
    return float(np.mean(e))


def open_edges(tris) -> int:
    """Number of edges belonging to a single triangle (0 = closed surface)."""
    e = np.sort(tris[:, [[0, 1], [1, 2], [2, 0]]].reshape(-1, 2), axis=1)
    _, counts = np.unique(e, axis=0, return_counts=True)
    return int((counts == 1).sum())


def quality_report(mesh: TailMesh, cfg: TailConfig) -> dict:
    vol = tet_volumes(mesh.points, mesh.tets)
    v_L = surface_volume(mesh.points, mesh.tri_chamber_L)
    v_R = surface_volume(mesh.points, mesh.tri_chamber_R)
    v_outer = surface_volume(mesh.points, mesh.tri_outer)
    v_solid = float(vol.sum())

    # Element size at the chamber walls: mean edge of the tets touching the cavity.
    # Elements across thickness ≈ thickness / mean edge (an approximation, not a layer count).
    ch_nodes = np.union1d(np.unique(mesh.tri_chamber_L), np.unique(mesh.tri_chamber_R))
    h_ch = _mean_edge(mesh.points, mesh.tets, np.isin(mesh.tets, ch_nodes).any(axis=1))
    in_fin = np.isin(mesh.tets, mesh.fin_nodes).all(axis=1)
    h_fin = _mean_edge(mesh.points, mesh.tets, in_fin)

    # Symmetry: every node has a mirror counterpart (comparison of sorted coordinates).
    p = np.round(mesh.points / 1e-9).astype(np.int64)
    pm = p * np.array([1, -1, 1])
    sym = bool(np.array_equal(np.unique(p, axis=0), np.unique(pm, axis=0)))

    return {
        "level": mesh.level,
        "h_wall_mm": mesh.h_wall * 1e3, "h_far_mm": mesh.h_far * 1e3,
        "n_nodes": int(len(mesh.points)), "n_tets": int(len(mesh.tets)),
        "n_tri_outer": int(len(mesh.tri_outer)),
        "n_tri_chamber": [int(len(mesh.tri_chamber_L)), int(len(mesh.tri_chamber_R))],
        "n_base_nodes": int(len(mesh.base_nodes)), "n_fin_nodes": int(len(mesh.fin_nodes)),
        "tet_volume_min_m3": float(vol.min()), "n_tets_nonpositive": int((vol <= 0).sum()),
        "sicn_min": float(mesh.sicn.min()), "sicn_p1": float(np.percentile(mesh.sicn, 1)),
        "sicn_mean": float(mesh.sicn.mean()),
        "volume_solid_m3": v_solid, "volume_chamber_L_m3": v_L, "volume_chamber_R_m3": v_R,
        # Each of the three surfaces must be closed (otherwise the chamber "leaks":
        # SurfacePressureConstraint would compute a wrong volume). Closed + signed volume
        # > 0 = correct normal orientation.
        "open_edges": [open_edges(mesh.tri_outer), open_edges(mesh.tri_chamber_L),
                       open_edges(mesh.tri_chamber_R)],
        "volume_outer_m3": v_outer,
        "mirror_symmetric": sym,
        "h_chamber_wall_mm": h_ch * 1e3,
        "elements_across_wall": cfg.wall_thickness / h_ch,
        "elements_across_septum": cfg.septum_thickness / h_ch,
        "h_fin_mm": h_fin * 1e3,
        "volume_spine_m3": float(vol[mesh.tet_region == 1].sum()),
        "volume_spine_nominal_m3": _spine_nominal_volume(cfg),
        "elements_across_fin": cfg.fin_thickness / h_fin,
    }


def format_report(r: dict) -> str:
    return "\n".join([
        f"[{r['level']}] h near surface = {r['h_wall_mm']:.1f} mm, h in the interior = {r['h_far_mm']:.1f} mm",
        f"  nodes: {r['n_nodes']}, tetrahedra: {r['n_tets']}, triangles: outer {r['n_tri_outer']}, "
        f"chambers L/R {r['n_tri_chamber'][0]}/{r['n_tri_chamber'][1]}",
        f"  root nodes (mount): {r['n_base_nodes']}, fin nodes: {r['n_fin_nodes']}",
        f"  min tet volume: {r['tet_volume_min_m3']:.3e} m³, tets with volume ≤ 0: {r['n_tets_nonpositive']}",
        f"  SICN quality (1 = ideal tetrahedron): min {r['sicn_min']:.3f}, 1st percentile {r['sicn_p1']:.3f}, "
        f"mean {r['sicn_mean']:.3f}",
        f"  silicone volume: {r['volume_solid_m3'] * 1e6:.1f} ml, cavities L/R: "
        f"{r['volume_chamber_L_m3'] * 1e6:.2f} / {r['volume_chamber_R_m3'] * 1e6:.2f} ml",
        f"  closed surfaces (open edges outer/L/R): {r['open_edges']}, "
        f"volume inside outer surface {r['volume_outer_m3'] * 1e6:.1f} ml",
        f"  node mirror symmetry: {'YES' if r['mirror_symmetric'] else 'NO'}",
        f"  at chamber walls: mean edge {r['h_chamber_wall_mm']:.2f} mm -> "
        f"~{r['elements_across_wall']:.1f} elem. across wall, ~{r['elements_across_septum']:.1f} across septum",
        f"  fin: mean edge {r['h_fin_mm']:.2f} mm -> ~{r['elements_across_fin']:.1f} elem. across thickness",
        f"  septum/spine region: {r['volume_spine_m3'] * 1e6:.1f} ml "
        f"(nominal {r['volume_spine_nominal_m3'] * 1e6:.1f} ml)",
    ])


def _spine_nominal_volume(cfg: TailConfig) -> float:
    """Volume of the slab |y| ≤ septum/2 within the body: ∫ cross-section width in Z dx."""
    xs = np.linspace(-cfg.tail_length, 0.0, 401)
    rz = np.array([cfg.rz0 * cfg.scale_at(x) for x in xs])
    return float(np.trapezoid(2 * rz * cfg.septum_thickness, xs))


# ----------------------------------------------------------------------------- save / load

def _geometry_hash(cfg: TailConfig, level: str) -> str:
    """Hash of the parameters that affect the mesh – a config change forces regeneration."""
    keys = ["n_segments", "n_actuated", "segment_length", "ry0", "rz0", "taper_last", "fin_semi_x",
            "fin_semi_z", "fin_thickness", "fin_root_overlap", "chamber_x_start", "wall_thickness",
            "septum_thickness"]
    d = {k: asdict(cfg)[k] for k in keys}
    d["level"] = list(cfg.mesh_levels[level])
    d["generator"] = GENERATOR_VERSION
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:12]


def mesh_dir(cfg: TailConfig, level: str, root: str | None = None) -> str:
    """meshes/<level>_<geometry hash>: geometry variants (e.g. a thicker wall) get
    separate directories and do not overwrite each other's meshes."""
    base = root if root is not None else os.path.join(PROJECT_DIR, cfg.mesh_dir)
    return os.path.join(base, f"{level}_{_geometry_hash(cfg, level)}")


def _write_obj(path, points, tris):
    """OBJ with indexed vertices (STL stores each triangle separately, without shared nodes)."""
    used, local = np.unique(tris, return_inverse=True)
    local = local.reshape(-1, 3)
    with open(path, "w") as f:
        f.write("# fishsofa – vertices = FEM nodes with indices from tail_meta.npz\n")
        for p in points[used]:
            f.write(f"v {p[0]:.9g} {p[1]:.9g} {p[2]:.9g}\n")
        for t in local + 1:
            f.write(f"f {t[0]} {t[1]} {t[2]}\n")


def _write_vtk_legacy(path, points, tets):
    """Classic legacy VTK 4.2 ASCII (UNSTRUCTURED_GRID).

    We do not use meshio: it writes VTK 5.1 (OFFSETS/CONNECTIVITY sections), which
    MeshVTKLoader in SOFA v26.06 does not understand – loading ends in a segfault.
    """
    with open(path, "w") as f:
        f.write("# vtk DataFile Version 4.2\nfishsofa tail\nASCII\nDATASET UNSTRUCTURED_GRID\n")
        f.write(f"POINTS {len(points)} double\n")
        np.savetxt(f, points, fmt="%.9g")
        f.write(f"CELLS {len(tets)} {5 * len(tets)}\n")
        np.savetxt(f, np.hstack([np.full((len(tets), 1), 4), tets]), fmt="%d")
        f.write(f"CELL_TYPES {len(tets)}\n")
        np.savetxt(f, np.full(len(tets), 10), fmt="%d")  # 10 = VTK_TETRA


def save(mesh: TailMesh, cfg: TailConfig, root: str | None = None) -> str:
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
             tet_region=mesh.tet_region,
             level=mesh.level, h_wall=mesh.h_wall, h_far=mesh.h_far,
             geometry_hash=_geometry_hash(cfg, mesh.level))
    with open(os.path.join(out, "report.txt"), "w") as f:
        f.write(format_report(quality_report(mesh, cfg)) + "\n")
    return out


def load(cfg: TailConfig, level: str, root: str | None = None) -> TailMesh:
    d = np.load(os.path.join(mesh_dir(cfg, level, root), "tail_meta.npz"))
    return TailMesh(d["points"], d["tets"], d["tri_outer"], d["tri_chamber_L"], d["tri_chamber_R"],
                    d["base_nodes"], d["fin_nodes"], d["sicn"], d["tet_region"], str(d["level"]),
                    float(d["h_wall"]), float(d["h_far"]))


def ensure(cfg: TailConfig, level: str, root: str | None = None) -> str:
    """Generates the mesh if it is missing or if the geometry config changed. Returns the directory."""
    out = mesh_dir(cfg, level, root)
    meta = os.path.join(out, "tail_meta.npz")
    if os.path.exists(meta):
        if str(np.load(meta)["geometry_hash"]) == _geometry_hash(cfg, level):
            return out
    return save(generate(cfg, level), cfg, root)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cfg = TailConfig()
    ap.add_argument("--level", default="coarse", choices=list(cfg.mesh_levels) + ["all"])
    args = ap.parse_args()
    levels = list(cfg.mesh_levels) if args.level == "all" else [args.level]
    for lv in levels:
        mesh = generate(cfg, lv)
        out = save(mesh, cfg)
        print(format_report(quality_report(mesh, cfg)))
        print(f"  -> {out}\n")


if __name__ == "__main__":
    main()
