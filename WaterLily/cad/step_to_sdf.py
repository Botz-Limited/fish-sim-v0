"""Signed distance field of the CAD tail (Fish_Tail.step) for the WaterLily bench stage (stage 8).

Usage (from WaterLily/, Python env with gmsh + numpy + scipy, e.g. the SOFA `fishsofa` env):
    python cad/step_to_sdf.py            # -> cad/tail_sdf.bin + cad/tail_sdf.json (~30 MB, git-ignored)

Same CAD model and the same added parts as the SOFA bench setup (SOFA/fishsofa/step_mesh.py on the
sofa branch). STEP axes: x along the tail, y up, z sideways. Content:
  - 8 tubes (the chambers, 4 per side), x 240–290 mm. The CFD sees only the outside of the tail, so
    every tube is FILLED (its lumen is chamber water that moves with the tail),
  - silicone body x 290–460 mm with a ~4 mm pocket in its front face (filled, as the SOFA plug),
  - caudal fin (2 mm plate, x 420–500 mm) and ventral fin (2 mm plate),
  - holder plate added here as in SOFA: PLATE_T in front of the tubes, closing their front ends.
The holder ring / bracket of the stand are NOT in the STEP and not modelled.

Method (no boolean operations, the STEP parts overlap and touch, see the SOFA notes):
  1. gmsh triangulates the surface of every part,
  2. each part is voxelized on a H = 0.5 mm grid by ray parity along x,
  3. tubes and body: every yz slice is hole-filled (lumen, pocket); union; 3D hole fill,
  4. signed Euclidean distance transform (scipy), ± H/2 correction to the voxel boundary,
  5. sampled every 2nd voxel -> 1 mm grid, stored as Float32.
Two fields are stored: `rest` (body + tubes + plate) and `fin` (the two 2 mm plates). The CFD
takes min(rest, fin − pad): with cells ≥ 1 mm a 2 mm plate is only 1–2 cells thick and leaks
through the immersed boundary, so stage 8 can thicken the fins by `pad` (documented there).

Output frame (WaterLily body frame, meters): x = STEP x − x_root along the tail (root = front
ends of the tubes, x_root = 240 mm), y = STEP z (sideways), z = STEP y (up). Negative inside.
Binary layout: Float32, Fortran order (x fastest), first `rest` then `fin`, dims in the JSON.
"""
import json
import os
import sys

import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
STEP = os.path.join(HERE, "Fish_Tail.step")
H = 0.0005            # [m] voxel size of the inside test
STRIDE = 2            # stored grid = every STRIDE-th voxel (1 mm)
MARGIN = 0.010        # [m] around the bounding box (SDF band seen by the CFD)
PLATE_T = 0.003       # [m] holder plate in front of the tubes (as SOFA step_plate_thickness)
SURFACE_H = 0.001     # [m] triangle size of the part surfaces


def _extent(gmsh, dim, tag):
    b = gmsh.model.occ.getBoundingBox(dim, tag)
    return np.array(b[3:]) - np.array(b[:3])


def parts():
    """{name: [(points (P,3), tris (K,3))]} in STEP axes [m], and x_root."""
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setString("Geometry.OCCTargetUnit", "M")
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)
        occ = gmsh.model.occ
        vols = [t for d, t in occ.importShapes(STEP) if d == 3]
        occ.synchronize()
        thin = [v for v in vols if _extent(gmsh, 3, v).min() < 0.003]
        rest = [v for v in vols if v not in thin]
        body = max(rest, key=lambda v: occ.getMass(3, v))
        tubes = [v for v in rest if v != body]
        if len(thin) != 2 or len(tubes) != 8:
            raise RuntimeError(f"unexpected STEP content: {len(thin)} plates, {len(tubes)} tubes (expected 2, 8)")
        x_root = min(occ.getBoundingBox(3, v)[0] for v in tubes)
        b = np.array([occ.getBoundingBox(3, v) for v in tubes])
        lo, hi = b[:, :3].min(axis=0), b[:, 3:].max(axis=0)
        plate = occ.addBox(x_root - PLATE_T, lo[1] - 0.002, lo[2] - 0.002, PLATE_T,
                           hi[1] - lo[1] + 0.004, hi[2] - lo[2] + 0.004)
        occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMax", SURFACE_H)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
        gmsh.model.mesh.generate(2)
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        pos = np.zeros(int(tags.max()) + 1, np.int64)
        pos[tags.astype(np.int64)] = np.arange(len(tags))
        pts = xyz.reshape(-1, 3)

        def tris(v):
            out = []
            for _, f in gmsh.model.getBoundary([(3, v)], oriented=False):
                _, _, en = gmsh.model.mesh.getElements(2, abs(f))
                out.append(pos[np.asarray(en[0], np.int64)].reshape(-1, 3))
            return np.vstack(out)

        groups = {"body": [body], "tube": tubes, "fin": thin, "plate": [plate]}
        return {k: [tris(v) for v in vs] for k, vs in groups.items()}, pts, x_root
    finally:
        gmsh.finalize()


def voxelize(pts, tris, xs, ys, zs):
    """Inside mask of one closed triangulated surface on the grid xs×ys×zs (ray parity along +x).
    The grid is offset from the CAD coordinates by an irrational fraction of H, so rays do not
    run exactly through mesh vertices or edges."""
    nx, ny, nz = len(xs), len(ys), len(zs)
    a, b, c = pts[tris[:, 0]], pts[tris[:, 1]], pts[tris[:, 2]]
    # candidate (triangle, column) pairs from the yz bounding box of every triangle
    ylo = np.searchsorted(ys, np.minimum(np.minimum(a[:, 1], b[:, 1]), c[:, 1]))
    yhi = np.searchsorted(ys, np.maximum(np.maximum(a[:, 1], b[:, 1]), c[:, 1]))
    zlo = np.searchsorted(zs, np.minimum(np.minimum(a[:, 2], b[:, 2]), c[:, 2]))
    zhi = np.searchsorted(zs, np.maximum(np.maximum(a[:, 2], b[:, 2]), c[:, 2]))
    ny_t, nz_t = yhi - ylo, zhi - zlo
    cnt = ny_t * nz_t
    keep = cnt > 0
    t_idx = np.repeat(np.flatnonzero(keep), cnt[keep])
    off = np.arange(len(t_idx)) - np.repeat(np.cumsum(cnt[keep]) - cnt[keep], cnt[keep])
    j = ylo[t_idx] + off % ny_t[t_idx]
    k = zlo[t_idx] + off // ny_t[t_idx]
    py, pz = ys[j], zs[k]
    # 2D barycentric test in the yz plane, then the x of the hit
    A, B, C = a[t_idx], b[t_idx], c[t_idx]
    d = (B[:, 1] - A[:, 1]) * (C[:, 2] - A[:, 2]) - (C[:, 1] - A[:, 1]) * (B[:, 2] - A[:, 2])
    ok = np.abs(d) > 1e-18
    l1 = ((B[:, 1] - py) * (C[:, 2] - pz) - (C[:, 1] - py) * (B[:, 2] - pz)) / np.where(ok, d, 1)
    l2 = ((C[:, 1] - py) * (A[:, 2] - pz) - (A[:, 1] - py) * (C[:, 2] - pz)) / np.where(ok, d, 1)
    l3 = 1 - l1 - l2
    hit = ok & (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
    xh = (l1 * A[:, 0] + l2 * B[:, 0] + l3 * C[:, 0])[hit]
    i = np.searchsorted(xs, xh)                 # first voxel centre beyond the crossing
    flips = np.zeros((nx + 1, ny, nz), np.int32)
    np.add.at(flips, (i, j[hit], k[hit]), 1)
    return (np.cumsum(flips, axis=0)[:nx] % 2).astype(bool)


def fill_slices(mask):
    """Hole fill of every yz slice (tube lumen, body pocket)."""
    out = mask.copy()
    for i in range(mask.shape[0]):
        if mask[i].any():
            out[i] = ndimage.binary_fill_holes(mask[i])
    return out


def sdf(mask):
    """Signed distance [m] on the voxel grid, negative inside, ± H/2 to the voxel boundary."""
    dout = ndimage.distance_transform_edt(~mask) * H
    din = ndimage.distance_transform_edt(mask) * H
    return np.where(mask, -(din - H / 2), dout - H / 2).astype(np.float32)


def main():
    groups, pts, x_root = parts()
    lo, hi = pts.min(axis=0) - MARGIN, pts.max(axis=0) + MARGIN
    phase = H * (np.sqrt(2) - 1) / 3            # irrational grid offset (see voxelize)
    xs, ys, zs = (np.arange(lo[a], hi[a], H) + phase for a in range(3))
    print(f"grid {len(xs)}×{len(ys)}×{len(zs)} at {H * 1e3:.1f} mm, x_root = {x_root * 1e3:.1f} mm", flush=True)
    masks, vol = {}, {}
    for name, ts in groups.items():
        m = np.zeros((len(xs), len(ys), len(zs)), bool)
        for t in ts:
            mv = voxelize(pts, t, xs, ys, zs)
            m |= fill_slices(mv) if name in ("tube", "body") else mv
        masks[name] = m
        vol[name] = float(m.sum() * H**3)
        print(f"  {name:5s}: {vol[name] * 1e6:7.1f} ml (filled)", flush=True)
    rest = ndimage.binary_fill_holes(masks["body"] | masks["tube"] | masks["plate"])
    fin = masks["fin"] & ~rest
    print(f"  union : {rest.sum() * H**3 * 1e6:7.1f} ml + fins outside the body {fin.sum() * H**3 * 1e6:.1f} ml")
    s = slice(None, None, STRIDE)
    # STEP (x, y up, z side) -> body frame (x, y = z side, z = y up): swap the last two axes
    d_rest = np.ascontiguousarray(sdf(rest)[s, s, s].transpose(0, 2, 1))
    d_fin = np.ascontiguousarray(sdf(masks["fin"])[s, s, s].transpose(0, 2, 1))
    x0 = (xs[0] - x_root, zs[0], ys[0])          # body-frame coordinates of voxel (1,1,1)
    meta = {"dims": list(d_rest.shape), "h": H * STRIDE, "origin": [float(v) for v in x0],
            "x_root_step": float(x_root), "plate_t": PLATE_T, "fields": ["rest", "fin"],
            "volumes_ml": {k: v * 1e6 for k, v in vol.items()},
            "union_ml": float(rest.sum() * H**3 * 1e6), "step": os.path.basename(STEP),
            "layout": "Float32, Fortran order (x fastest), rest then fin; body frame x tail, y side, z up [m]"}
    with open(os.path.join(HERE, "tail_sdf.bin"), "wb") as f:
        # Fortran order: write the C-order transpose of (x, y, z) -> bytes run x fastest
        f.write(np.asfortranarray(d_rest).tobytes(order="F"))
        f.write(np.asfortranarray(d_fin).tobytes(order="F"))
    with open(os.path.join(HERE, "tail_sdf.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("written", os.path.join(HERE, "tail_sdf.bin"), meta["dims"])


if __name__ == "__main__":
    sys.exit(main())
