"""Generacja siatki ogona: gmsh (połowa) -> odbicie lustrzane -> pliki dla SOFA.

Uruchomienie:  python -m fishsofa.mesh_gen --level coarse|medium|fine|test|all

Dlaczego połowa + odbicie: siatkowanie gmsh nie jest symetryczne, a test symetrii
(komora L vs R) ma sprawdzać kod hydrauliki, nie przypadek w rozmieszczeniu węzłów.
Siatkujemy połowę y ≥ 0 (jedna komora), a drugą połowę dostajemy przez odbicie
y -> −y. Węzły na płaszczyźnie y = 0 są wspólne dla obu połówek.

Co powstaje w meshes/<level>/:
  tail.vtk        – siatka objętościowa (czworościany) dla MeshVTKLoader,
  chamber_L.obj   – powierzchnia wnęki lewej komory (+Y) dla SurfacePressureConstraint,
  chamber_R.obj   – to samo dla prawej (−Y),
  outer.obj       – zewnętrzna powierzchnia ogona (siły wody, wizualizacja),
  tail_meta.npz   – te same dane jako tablice indeksów węzłów FEM + metadane.

Konwencje orientacji trójkątów (sprawdzane w testach):
  outer   – normalne NA ZEWNĄTRZ bryły (w wodę),
  chamber – normalne NA ZEWNĄTRZ WNĘKI, czyli w głąb silikonu. Tak jak w przykładach
            SoftRobots: wtedy dodatni przyrost objętości daje dodatnie ciśnienie
            (ustalone w etapie 0 na siatce królika).
"""
import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass

import numpy as np

from fishsofa import PROJECT_DIR
from fishsofa.config import TailConfig

# Wersja generatora: zmiana kodu, która zmienia wynik siatkowania, podbija numer,
# żeby ensure() wygenerował siatki od nowa (wchodzi do _geometry_hash).
GENERATOR_VERSION = 2

# Faces tetry (a,b,c,d) o dodatniej objętości, z normalnymi NA ZEWNĄTRZ tetry.
_TET_FACES = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]])


@dataclass
class TailMesh:
    points: np.ndarray       # (N, 3) [m]
    tets: np.ndarray         # (M, 4) indeksy węzłów, objętość każdej tetry > 0
    tri_outer: np.ndarray    # (K, 3) normalne na zewnątrz bryły
    tri_chamber_L: np.ndarray  # normalne na zewnątrz wnęki (konwencja SoftRobots)
    tri_chamber_R: np.ndarray
    base_nodes: np.ndarray   # węzły przedniej ściany x = 0 (mocowanie)
    fin_nodes: np.ndarray    # węzły płetwy za końcem korpusu (pomiar końcówki)
    sicn: np.ndarray         # jakość elementów gmsh (signed inverse condition number), połowa siatki
    level: str
    h_wall: float
    h_far: float


# ----------------------------------------------------------------------------- gmsh

def _build_half_geometry(gmsh, cfg: TailConfig):
    """Geometria połowy ogona (y ≥ 0) w jądrze OpenCASCADE. Zwraca dimtagi bryły."""
    occ = gmsh.model.occ
    L = cfg.tail_length

    def ellipse_loop(x, ry, rz):
        # Elipsa w płaszczyźnie YZ (normalna = oś X). gmsh wymaga, żeby pierwsza półoś
        # (wzdłuż xAxis) była większa, a u nas przekrój jest wyższy niż szerszy (rz > ry).
        c = occ.addEllipse(x, 0, 0, rz, ry, zAxis=[1, 0, 0], xAxis=[0, 0, 1])
        return occ.addCurveLoop([c])

    # Korpus: powierzchnia prostokreślna (makeRuled) między elipsą nasady i końca,
    # czyli liniowe zwężanie przekroju, tak jak taper w MuJoCo.
    s_end = cfg.scale_at(-L)
    body = occ.addThruSections([ellipse_loop(0.0, cfg.ry0, cfg.rz0),
                                ellipse_loop(-L, cfg.ry0 * s_end, cfg.rz0 * s_end)],
                               makeSolid=True, makeRuled=True)

    # Wnęka komory: ten sam kształt pomniejszony o grubość ścianki, przycięty do
    # zakresu x komory i do y ≥ septum/2 (połowa przegrody leży w tej połówce).
    x1, x2 = cfg.chamber_x_range
    w = cfg.wall_thickness
    s1, s2 = cfg.scale_at(x1), cfg.scale_at(x2)
    cavity = occ.addThruSections([ellipse_loop(x1, cfg.ry0 * s1 - w, cfg.rz0 * s1 - w),
                                  ellipse_loop(x2, cfg.ry0 * s2 - w, cfg.rz0 * s2 - w)],
                                 makeSolid=True, makeRuled=True)
    cavity, _ = occ.intersect(cavity, [(3, occ.addBox(-1, cfg.septum_thickness / 2, -1, 2, 1, 2))])

    # Płetwa: eliptyczny dysk w płaszczyźnie XZ wyciągnięty w Y na całą grubość.
    disk = occ.addDisk(cfg.fin_center_x, -cfg.fin_thickness / 2, 0, cfg.fin_semi_z, cfg.fin_semi_x,
                       zAxis=[0, 1, 0], xAxis=[0, 0, 1])
    fin = [e for e in occ.extrude([(2, disk)], 0, cfg.fin_thickness, 0) if e[0] == 3]

    solid, _ = occ.fuse(body, fin)
    solid, _ = occ.intersect(solid, [(3, occ.addBox(-1, 0, -1, 2, 1, 2))])  # połowa y ≥ 0
    solid, _ = occ.cut(solid, cavity)
    occ.synchronize()
    if len(solid) != 1:
        raise RuntimeError(f"oczekiwano jednej bryły, jest {len(solid)}")

    return solid


def _mesh_half(cfg: TailConfig, h_wall: float, h_far: float):
    """Siatkuje połowę ogona. Zwraca (punkty, tetry, SICN)."""
    import gmsh

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("tail_half")
        solid = _build_half_geometry(gmsh, cfg)

        # Rozmiar elementu: h_wall blisko powierzchni (cienkie ścianki komory, płetwa,
        # skóra ogona), rośnie do h_far w głębi bryły. Distance liczy odległość od
        # powierzchni, Threshold zamienia ją na rozmiar elementu.
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
        gmsh.option.setNumber("Mesh.Optimize", 1)  # poprawa najgorszych elementów
        gmsh.model.mesh.generate(3)

        tags, coords, _ = gmsh.model.mesh.getNodes()
        coords = coords.reshape(-1, 3)
        _, elem_tags, elem_nodes = gmsh.model.mesh.getElements(3)
        tet_tags = np.asarray(elem_tags[0])
        tet_nodes = np.asarray(elem_nodes[0]).reshape(-1, 4)
        sicn = np.asarray(gmsh.model.mesh.getElementQualities(tet_tags, "minSICN"))
    finally:
        gmsh.finalize()

    # Zwarta numeracja: tylko węzły używane przez tetry, indeksy od 0.
    used = np.unique(tet_nodes)
    tag_to_idx = {int(t): i for i, t in enumerate(used)}
    tag_pos = {int(t): i for i, t in enumerate(tags)}
    points = coords[[tag_pos[int(t)] for t in used]]
    tets = np.vectorize(tag_to_idx.get)(tet_nodes)
    return points, tets, sicn


# ----------------------------------------------------------------------------- geometria siatki (numpy)

def tet_volumes(points, tets):
    a, b, c, d = (points[tets[:, k]] for k in range(4))
    return np.einsum("ij,ij->i", b - a, np.cross(c - a, d - a)) / 6.0


def surface_volume(points, tris):
    """Objętość ze znakiem zamknięta przez powierzchnię (tw. Gaussa). > 0 = normalne na zewnątrz."""
    p0, p1, p2 = (points[tris[:, k]] for k in range(3))
    return float(np.einsum("ij,ij->i", p0, np.cross(p1, p2)).sum() / 6.0)


def boundary_faces(tets):
    """Ściany występujące w dokładnie jednej tetrze, z normalnymi na zewnątrz bryły."""
    faces = tets[:, _TET_FACES].reshape(-1, 3)
    key = np.sort(faces, axis=1)
    _, inv, counts = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    return faces[counts[inv.ravel()] == 1]


def _mirror(points, tets, tol=1e-9):
    """Odbicie y -> −y. Węzły z |y| < tol zostają wspólne."""
    n = len(points)
    on_plane = np.abs(points[:, 1]) < tol
    # Węzły tuż obok płaszczyzny, ale nie na niej, oznaczałyby błąd geometrii (szczelina).
    if np.any(points[:, 1] < -tol):
        raise RuntimeError("połowa siatki ma węzły z y < 0")
    off = np.flatnonzero(~on_plane)
    mirror_idx = np.arange(n)
    mirror_idx[off] = n + np.arange(len(off))
    mirrored_pts = points[off] * np.array([1.0, -1.0, 1.0])
    pts_full = np.vstack([points, mirrored_pts])
    pts_full[np.flatnonzero(on_plane), 1] = 0.0
    # Odbicie zmienia orientację tetry (objętość zmienia znak) – zamiana dwóch
    # wierzchołków przywraca dodatnią objętość.
    tets_m = mirror_idx[tets][:, [1, 0, 2, 3]]
    tets_full = np.vstack([tets, tets_m])
    return pts_full, tets_full


def _in_cavity(cfg: TailConfig, c: np.ndarray, side: int) -> np.ndarray:
    """Czy punkty c (środki trójkątów) leżą na wnęce komory po stronie side (+1 = L, −1 = R).

    Wnęka to przekrój eliptyczny (półosie ogona minus ścianka) dla x w zakresie komory
    i |y| ≥ septum/2. Sprawdzamy obrys powiększony o pół ścianki: łapie trójkąty wnęki,
    a odrzuca skórę ogona (odległą o całą ściankę) i płaszczyznę symetrii y = 0.
    Uwaga: wcześniejsza wersja szukała powierzchni wnęki po bounding boxach gmsh, ale
    OpenCASCADE podaje dla powierzchni B-spline zbyt luźne bboxy i część wnęki ginęła.
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

    # gmsh zwykle zwraca tetry o dodatniej objętości; na wszelki wypadek poprawiamy.
    neg = tet_volumes(points, tets) < 0
    tets[neg] = tets[neg][:, [1, 0, 2, 3]]

    points, tets = _mirror(points, tets)

    faces = boundary_faces(tets)
    centers = points[faces].mean(axis=1)
    in_L = _in_cavity(cfg, centers, +1)
    in_R = _in_cavity(cfg, centers, -1)
    # Ściany wnęki z boundary_faces mają normalne na zewnątrz bryły = W GŁĄB wnęki.
    # SoftRobots chce odwrotnie (na zewnątrz wnęki), więc odwracamy kolejność wierzchołków.
    tri_L = faces[in_L][:, [0, 2, 1]]
    tri_R = faces[in_R][:, [0, 2, 1]]
    tri_outer = faces[~(in_L | in_R)]

    L = cfg.tail_length
    base = np.flatnonzero(np.abs(points[:, 0]) < 1e-9)
    fin = np.flatnonzero(points[:, 0] < -L - 1e-9)
    return TailMesh(points, tets, tri_outer, tri_L, tri_R, base, fin, sicn, level, h_wall, h_far)


# ----------------------------------------------------------------------------- raport jakości

def _mean_edge(points, tets, mask):
    sel = tets[mask]
    if len(sel) == 0:
        return float("nan")
    e = [np.linalg.norm(points[sel[:, i]] - points[sel[:, j]], axis=1)
         for i, j in ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))]
    return float(np.mean(e))


def open_edges(tris) -> int:
    """Liczba krawędzi należących do jednego trójkąta (0 = powierzchnia zamknięta)."""
    e = np.sort(tris[:, [[0, 1], [1, 2], [2, 0]]].reshape(-1, 2), axis=1)
    _, counts = np.unique(e, axis=0, return_counts=True)
    return int((counts == 1).sum())


def quality_report(mesh: TailMesh, cfg: TailConfig) -> dict:
    vol = tet_volumes(mesh.points, mesh.tets)
    v_L = surface_volume(mesh.points, mesh.tri_chamber_L)
    v_R = surface_volume(mesh.points, mesh.tri_chamber_R)
    v_outer = surface_volume(mesh.points, mesh.tri_outer)
    v_solid = float(vol.sum())

    # Rozmiar elementu przy ściankach komory: średnia krawędź tetr dotykających wnęki.
    # Elementy na grubość ≈ grubość / średnia krawędź (przybliżenie, nie liczenie warstw).
    ch_nodes = np.union1d(np.unique(mesh.tri_chamber_L), np.unique(mesh.tri_chamber_R))
    h_ch = _mean_edge(mesh.points, mesh.tets, np.isin(mesh.tets, ch_nodes).any(axis=1))
    in_fin = np.isin(mesh.tets, mesh.fin_nodes).all(axis=1)
    h_fin = _mean_edge(mesh.points, mesh.tets, in_fin)

    # Symetria: każdy węzeł ma lustrzany odpowiednik (porównanie posortowanych współrzędnych).
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
        # Każda z trzech powierzchni musi być zamknięta (inaczej komora „przecieka”:
        # SurfacePressureConstraint liczyłby złą objętość). Zamknięta + objętość ze znakiem
        # > 0 = poprawna orientacja normalnych.
        "open_edges": [open_edges(mesh.tri_outer), open_edges(mesh.tri_chamber_L),
                       open_edges(mesh.tri_chamber_R)],
        "volume_outer_m3": v_outer,
        "mirror_symmetric": sym,
        "h_chamber_wall_mm": h_ch * 1e3,
        "elements_across_wall": cfg.wall_thickness / h_ch,
        "elements_across_septum": cfg.septum_thickness / h_ch,
        "h_fin_mm": h_fin * 1e3,
        "elements_across_fin": cfg.fin_thickness / h_fin,
    }


def format_report(r: dict) -> str:
    return "\n".join([
        f"[{r['level']}] h przy powierzchni = {r['h_wall_mm']:.1f} mm, h w głębi = {r['h_far_mm']:.1f} mm",
        f"  węzły: {r['n_nodes']}, czworościany: {r['n_tets']}, trójkąty: zewn. {r['n_tri_outer']}, "
        f"komory L/R {r['n_tri_chamber'][0]}/{r['n_tri_chamber'][1]}",
        f"  węzły nasady (mocowanie): {r['n_base_nodes']}, węzły płetwy: {r['n_fin_nodes']}",
        f"  min objętość tetry: {r['tet_volume_min_m3']:.3e} m³, tetry z objętością ≤ 0: {r['n_tets_nonpositive']}",
        f"  jakość SICN (1 = idealny czworościan): min {r['sicn_min']:.3f}, 1. percentyl {r['sicn_p1']:.3f}, "
        f"średnia {r['sicn_mean']:.3f}",
        f"  objętość silikonu: {r['volume_solid_m3'] * 1e6:.1f} ml, wnęki L/R: "
        f"{r['volume_chamber_L_m3'] * 1e6:.2f} / {r['volume_chamber_R_m3'] * 1e6:.2f} ml",
        f"  powierzchnie zamknięte (krawędzie otwarte zewn./L/R): {r['open_edges']}, "
        f"objętość w powierzchni zewn. {r['volume_outer_m3'] * 1e6:.1f} ml",
        f"  symetria lustrzana węzłów: {'TAK' if r['mirror_symmetric'] else 'NIE'}",
        f"  przy ściankach komory: średnia krawędź {r['h_chamber_wall_mm']:.2f} mm -> "
        f"~{r['elements_across_wall']:.1f} elem. na ściankę, ~{r['elements_across_septum']:.1f} na przegrodę",
        f"  płetwa: średnia krawędź {r['h_fin_mm']:.2f} mm -> ~{r['elements_across_fin']:.1f} elem. na grubość",
    ])


# ----------------------------------------------------------------------------- zapis / odczyt

def _geometry_hash(cfg: TailConfig, level: str) -> str:
    """Skrót parametrów wpływających na siatkę – zmiana configu wymusza regenerację."""
    keys = ["n_segments", "n_actuated", "segment_length", "ry0", "rz0", "taper_last", "fin_semi_x",
            "fin_semi_z", "fin_thickness", "fin_root_overlap", "chamber_x_start", "wall_thickness",
            "septum_thickness"]
    d = {k: asdict(cfg)[k] for k in keys}
    d["level"] = list(cfg.mesh_levels[level])
    d["generator"] = GENERATOR_VERSION
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:12]


def mesh_dir(cfg: TailConfig, level: str, root: str | None = None) -> str:
    base = root if root is not None else os.path.join(PROJECT_DIR, cfg.mesh_dir)
    return os.path.join(base, level)


def _write_obj(path, points, tris):
    """OBJ z indeksowanymi wierzchołkami (STL zapisuje każdy trójkąt osobno, bez wspólnych węzłów)."""
    used, local = np.unique(tris, return_inverse=True)
    local = local.reshape(-1, 3)
    with open(path, "w") as f:
        f.write("# fishsofa – wierzchołki = węzły FEM o indeksach z tail_meta.npz\n")
        for p in points[used]:
            f.write(f"v {p[0]:.9g} {p[1]:.9g} {p[2]:.9g}\n")
        for t in local + 1:
            f.write(f"f {t[0]} {t[1]} {t[2]}\n")


def _write_vtk_legacy(path, points, tets):
    """Klasyczny VTK 4.2 ASCII (UNSTRUCTURED_GRID).

    Nie używamy meshio: zapisuje VTK 5.1 (sekcje OFFSETS/CONNECTIVITY), którego
    MeshVTKLoader z SOFA v26.06 nie rozumie – kończy się to segfaultem przy wczytaniu.
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
             level=mesh.level, h_wall=mesh.h_wall, h_far=mesh.h_far,
             geometry_hash=_geometry_hash(cfg, mesh.level))
    with open(os.path.join(out, "report.txt"), "w") as f:
        f.write(format_report(quality_report(mesh, cfg)) + "\n")
    return out


def load(cfg: TailConfig, level: str, root: str | None = None) -> TailMesh:
    d = np.load(os.path.join(mesh_dir(cfg, level, root), "tail_meta.npz"))
    return TailMesh(d["points"], d["tets"], d["tri_outer"], d["tri_chamber_L"], d["tri_chamber_R"],
                    d["base_nodes"], d["fin_nodes"], d["sicn"], str(d["level"]),
                    float(d["h_wall"]), float(d["h_far"]))


def ensure(cfg: TailConfig, level: str, root: str | None = None) -> str:
    """Generuje siatkę, jeśli jej nie ma albo jeśli config geometrii się zmienił. Zwraca katalog."""
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
