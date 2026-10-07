#!/usr/bin/env python3
"""Geometria 2D ogona ryby z komorami (gmsh) dla CalculiX i OpenFOAM.

Dwa tryby:

  solid  – siatka ciała stałego dla CalculiX: czworokąty 2D wyciągnięte
           o jedną warstwę w z (elementy C3D8; tutorial perpendicular-flap używa
           C3D8I, ale z NLGEOM i siłami węzłowymi C3D8I traciły zbieżność –
           patrz NOTES.md).
           Zapisuje tail.msh (węzły + elementy) i tail_sets.nam (zbiory/powierzchnie):
             Nfix      – węzły nasady (sklejone ze sztywną głową, utwierdzone)
             Nsurface  – węzły zewnętrznej powierzchni ogona (interfejs preCICE)
             Ntip      – węzeł środka końcówki (x = L, y = 0), do pomiaru ugięcia
             SchL/SchR – ścianki komory lewej/prawej (powierzchnie dla *DLOAD)

  fluid  – siatka płynu dla OpenFOAM (2D: jedna warstwa komórek w z).
           Zapisuje fluid.msh (format 2.2) do konwersji przez gmshToFoam.
           Patche: inlet, outlet, sides, frontAndBack, head (sztywna), tail (ruchoma).
           Komory są wewnątrz ciała stałego, więc płyn widzi tylko obrys ogona.

Użycie:
  python tools/make_geometry.py solid <katalog>
  python tools/make_geometry.py fluid <katalog> [--scale S] [--domain K]
     S – zagęszczenie siatki (2 = dwa razy mniejsze komórki),
     K – mnożnik rozmiaru domeny (test wpływu granic).
"""
import argparse
import sys
from pathlib import Path

import gmsh
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import params as P  # noqa: E402

# Kolejność ścian elementu C3D8 w CalculiX dla krawędzi i czworokąta podstawy:
# krawędź 1-2 -> S3, 2-3 -> S4, 3-4 -> S5, 4-1 -> S6
EDGE_TO_FACE = ("S3", "S4", "S5", "S6")


def tail_outline_points():
    """Punkty obrysu ogona (bez głowy), od dolnej nasady przeciwnie do zegara."""
    return [
        (0.0, -P.T_ROOT / 2),
        (P.L, -P.T_TIP / 2),
        (P.L, 0.0),            # środek końcówki – tu mierzymy ugięcie
        (P.L, P.T_TIP / 2),
        (0.0, P.T_ROOT / 2),
    ]


def chamber_cells(side):
    """Lista czworokątów cel komory; side = +1 (lewa, y > 0) albo -1 (prawa)."""
    y_in = P.W_MID / 2
    cell = (P.CH_X1 - P.CH_X0 - (P.N_CELLS - 1) * P.RIB) / P.N_CELLS
    cells = []
    for k in range(P.N_CELLS):
        xa = P.CH_X0 + k * (cell + P.RIB)
        xb = xa + cell
        ya = P.thickness(xa) / 2 - P.W_OUT
        yb = P.thickness(xb) / 2 - P.W_OUT
        pts = [(xa, y_in), (xb, y_in), (xb, yb), (xa, ya)]
        if side < 0:
            pts = [(x, -y) for x, y in reversed(pts)]
        cells.append(pts)
    return cells


def add_loop(pts, h):
    tags = [gmsh.model.geo.addPoint(x, y, 0.0, h) for x, y in pts]
    lines = [gmsh.model.geo.addLine(tags[i], tags[(i + 1) % len(tags)]) for i in range(len(tags))]
    return gmsh.model.geo.addCurveLoop(lines), lines


# ---------------------------------------------------------------------------
# Ciało stałe (CalculiX)
# ---------------------------------------------------------------------------
def build_solid(out):
    gmsh.model.add("tail_solid")
    h = P.SOLID_H
    outer, outer_lines = add_loop(tail_outline_points(), h)
    holes, chL_lines, chR_lines = [], [], []
    for side, lines_acc in ((+1, chL_lines), (-1, chR_lines)):
        for pts in chamber_cells(side):
            loop, lines = add_loop(pts, h)
            holes.append(loop)
            lines_acc += lines
    gmsh.model.geo.addPlaneSurface([outer] + holes)
    gmsh.model.geo.synchronize()

    gmsh.option.setNumber("Mesh.Algorithm", 8)               # Frontal-Delaunay dla czworokątów
    gmsh.option.setNumber("Mesh.RecombineAll", 1)
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 3)  # blossom, same czworokąty
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.model.mesh.generate(2)
    gmsh.model.mesh.optimize("Laplace2D")

    tags, coords, _ = gmsh.model.mesh.getNodes()
    xy = coords.reshape(-1, 3)[:, :2]
    renum = {int(t): i + 1 for i, t in enumerate(tags)}      # numeracja 1..N
    nn = len(tags)

    etypes, _, enodes = gmsh.model.mesh.getElements(dim=2)
    quads = np.array(enodes[list(etypes).index(3)], dtype=int).reshape(-1, 4)
    quads = np.vectorize(renum.get)(quads)
    # orientacja przeciwnie do zegara (dodatnia objętość C3D8)
    for q in quads:
        a = xy[q - 1]
        area = 0.5 * np.sum(a[:, 0] * np.roll(a[:, 1], -1) - np.roll(a[:, 0], -1) * a[:, 1])
        if area < 0:
            q[:] = q[::-1]

    def curve_edges(curves):
        edges = set()
        for c in curves:
            et, _, en = gmsh.model.mesh.getElements(dim=1, tag=c)
            for pair in np.array(en[0], dtype=int).reshape(-1, 2):
                edges.add(frozenset(renum[int(n)] for n in pair))
        return edges

    def curve_nodes(curves):
        nodes = set()
        for e in curve_edges(curves):
            nodes |= e
        return nodes

    root_line = outer_lines[-1]          # (0, T/2) -> (0, -T/2)
    surf_lines = outer_lines[:-1]
    n_fix = curve_nodes([root_line])
    n_surf = curve_nodes(surf_lines) - n_fix
    tip = [i + 1 for i, p in enumerate(xy) if np.allclose(p, (P.L, 0.0), atol=1e-9)]
    assert len(tip) == 1, "brak węzła w środku końcówki"

    def faces(curves):
        edges = curve_edges(curves)
        out_faces = []
        for e, q in enumerate(quads, start=1):
            for k in range(4):
                if frozenset((q[k], q[(k + 1) % 4])) in edges:
                    out_faces.append((e, EDGE_TO_FACE[k]))
        return out_faces

    sch_l, sch_r = faces(chL_lines), faces(chR_lines)

    out.mkdir(parents=True, exist_ok=True)
    with open(out / "tail.msh", "w") as f:
        f.write("** Siatka ogona (generowana przez tools/make_geometry.py – nie edytować)\n")
        f.write("** Jedna warstwa elementów C3D8 w z: model 2D (płaski stan odkształcenia,\n")
        f.write("** bo w flap.inp blokujemy przemieszczenie z wszystkich węzłów).\n")
        f.write("*NODE, NSET=Nall\n")
        for z, off in ((0.0, 0), (P.DEPTH, nn)):
            for i, (x, y) in enumerate(xy, start=1):
                f.write(f"{i + off}, {x:.9e}, {y:.9e}, {z:.9e}\n")
        f.write("*ELEMENT, TYPE=C3D8, ELSET=Eall\n")
        for e, q in enumerate(quads, start=1):
            ids = list(q) + [n + nn for n in q]
            f.write(f"{e}, " + ", ".join(map(str, ids)) + "\n")

    def write_nset(f, name, nodes):
        f.write(f"*NSET, NSET={name}\n")
        allnodes = sorted(nodes) + sorted(n + nn for n in nodes)
        for i in range(0, len(allnodes), 10):
            f.write(", ".join(map(str, allnodes[i:i + 10])) + ",\n")

    with open(out / "tail_sets.nam", "w") as f:
        f.write("** Zbiory węzłów i powierzchnie (generowane – nie edytować)\n")
        write_nset(f, "Nfix", n_fix)
        write_nset(f, "Nsurface", n_surf)
        write_nset(f, "Ntip", set(tip))
        for name, fl in (("SchL", sch_l), ("SchR", sch_r)):
            f.write(f"*SURFACE, NAME={name}, TYPE=ELEMENT\n")
            for e, s in fl:
                f.write(f"{e}, {s}\n")

    with open(out / "material.inc", "w") as f:
        f.write(f"""** Materiał ogona (generowany z tools/params.py – zmieniaj tam, nie tutaj)
** Liniowo sprężysty silikon; duże ugięcia obsługuje NLGEOM w kroku analizy.
*MATERIAL, NAME=SILICONE
*ELASTIC
** E [Pa], nu [-]   PLACEHOLDER – do identyfikacji z pomiarów
{P.E_SOLID:.6g}, {P.NU_SOLID:.6g}
*DENSITY
** rho [kg/m^3]     PLACEHOLDER – do identyfikacji z pomiarów
{P.RHO_SOLID:.6g}
*SOLID SECTION, ELSET=Eall, MATERIAL=SILICONE
""")

    print(f"solid: {nn} węzłów 2D, {len(quads)} elementów C3D8, "
          f"Nfix={len(n_fix)}, Nsurface={len(n_surf)}, ściany komór L/R={len(sch_l)}/{len(sch_r)}")


# ---------------------------------------------------------------------------
# Płyn (OpenFOAM)
# ---------------------------------------------------------------------------
def build_fluid(out, scale, domain):
    gmsh.model.add("fluid")
    geo = gmsh.model.geo
    s = scale
    h_tail = 1.5e-3 / s     # rozmiar komórki przy ogonie
    h_head = 3.0e-3 / s     # przy głowie
    h_wake = 4.0e-3 / s     # w śladzie wirowym
    h_far = 25e-3 / s       # daleko od ciała

    x_in = -P.HEAD_A - domain * P.UPSTREAM
    x_out = P.L + domain * P.DOWNSTREAM
    y_s = domain * P.SIDE

    # --- obrys ciała: głowa (2 łuki elipsy) + ogon (4 odcinki) ---
    c = geo.addPoint(0, 0, 0, h_head)
    p_nose = geo.addPoint(-P.HEAD_A, 0, 0, h_head)
    tail_pts = [geo.addPoint(x, y, 0, h_tail) for x, y in tail_outline_points()]
    p_bot, p_top = tail_pts[0], tail_pts[-1]
    head_curves = [geo.addEllipseArc(p_top, c, p_nose, p_nose),
                   geo.addEllipseArc(p_nose, c, p_nose, p_bot)]
    tail_curves = [geo.addLine(tail_pts[i], tail_pts[i + 1]) for i in range(len(tail_pts) - 1)]
    body = geo.addCurveLoop(head_curves + tail_curves)

    # --- prostokąt domeny ---
    b = [geo.addPoint(x_in, -y_s, 0, h_far), geo.addPoint(x_out, -y_s, 0, h_far),
         geo.addPoint(x_out, y_s, 0, h_far), geo.addPoint(x_in, y_s, 0, h_far)]
    bottom, outlet, top, inlet = (geo.addLine(b[i], b[(i + 1) % 4]) for i in range(4))
    box = geo.addCurveLoop([bottom, outlet, top, inlet])
    surf = geo.addPlaneSurface([box, body])
    geo.synchronize()

    # --- pola rozmiaru: blisko ciała drobno, ślad wirowy, daleko grubo ---
    f = gmsh.model.mesh.field
    dist = f.add("Distance")
    f.setNumbers(dist, "CurvesList", head_curves + tail_curves)
    f.setNumber(dist, "Sampling", 400)
    thr = f.add("Threshold")
    f.setNumber(thr, "InField", dist)
    f.setNumber(thr, "SizeMin", h_tail)
    f.setNumber(thr, "SizeMax", h_far)
    f.setNumber(thr, "DistMin", 0.01)
    f.setNumber(thr, "DistMax", 0.3)
    wake = f.add("Box")
    f.setNumber(wake, "VIn", h_wake)
    f.setNumber(wake, "VOut", h_far)
    f.setNumber(wake, "XMin", -P.HEAD_A - 0.02)
    f.setNumber(wake, "XMax", P.L + 0.6)
    f.setNumber(wake, "YMin", -0.08)
    f.setNumber(wake, "YMax", 0.08)
    f.setNumber(wake, "Thickness", 0.1)
    fmin = f.add("Min")
    f.setNumbers(fmin, "FieldsList", [thr, wake])
    f.setAsBackgroundMesh(fmin)

    # warstwa przyścienna (czworokąty) – rozdziela gradienty prędkości przy ścianie
    bl = f.add("BoundaryLayer")
    f.setNumbers(bl, "CurvesList", head_curves + tail_curves)
    f.setNumbers(bl, "PointsList", [p_nose] + tail_pts)
    f.setNumber(bl, "Size", 2.5e-4 / s)       # pierwsza komórka
    f.setNumber(bl, "Ratio", 1.2)
    f.setNumber(bl, "Thickness", 2.5e-3)
    f.setNumber(bl, "Quads", 1)
    # bez "wachlarza" w narożnikach końcówki: wachlarz tworzy bardzo małe komórki,
    # które wymuszały mały krok czasowy (Co ~1.4 przy dt = 2 ms)
    f.setAsBoundaryLayer(bl)

    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)          # Frontal-Delaunay (trójkąty)
    gmsh.option.setNumber("Mesh.RecombineAll", 1)       # trójkąty -> czworokąty
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)

    # --- wyciągnięcie o jedną warstwę w z (OpenFOAM liczy zawsze 3D) ---
    ext = geo.extrude([(2, surf)], 0, 0, P.DEPTH, numElements=[1], recombine=True)
    geo.synchronize()
    back, vol = ext[0][1], ext[1][1]
    # Ściany boczne po wyciągnięciu klasyfikujemy po położeniu (bounding box),
    # a nie po kolejności – gmsh nie gwarantuje kolejności krzywych pętli.
    groups = {"inlet": [], "outlet": [], "sides": [], "head": [], "tail": []}
    eps = 1e-6
    for dim, srf in ext[2:]:
        if dim != 2:
            continue
        x0, y0, _, x1, y1, _ = gmsh.model.getBoundingBox(2, srf)
        if x1 < x_in + eps:
            groups["inlet"].append(srf)
        elif x0 > x_out - eps:
            groups["outlet"].append(srf)
        elif min(abs(y0 + y_s), abs(y1 - y_s)) < eps:
            groups["sides"].append(srf)
        elif x1 < eps:                      # cała ściana w x <= 0 -> głowa
            groups["head"].append(srf)
        else:
            groups["tail"].append(srf)
    assert [len(groups[k]) for k in ("inlet", "outlet", "sides", "head", "tail")] == [1, 1, 2, 2, 4], groups
    pg = gmsh.model.addPhysicalGroup
    pg(2, [surf, back], name="frontAndBack")
    for name, tags in groups.items():
        pg(2, tags, name=name)
    pg(3, [vol], name="fluid")

    gmsh.model.mesh.generate(3)
    out.mkdir(parents=True, exist_ok=True)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write(str(out / "fluid.msh"))
    ncell = sum(len(t) for t in gmsh.model.mesh.getElements(dim=3)[1])
    print(f"fluid: scale={s}, domain={domain}, {ncell} komórek")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["solid", "fluid"])
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--domain", type=float, default=1.0)
    a = ap.parse_args()
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        if a.mode == "solid":
            build_solid(a.outdir)
        else:
            build_fluid(a.outdir, a.scale, a.domain)
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    main()
