#!/usr/bin/env python3
"""Extracts the flap tip displacement from the preCICE reference results.

The reference results of the perpendicular-flap tutorial
(fluid-openfoam_solid-calculix) are VTU exports of the solid interface mesh
at every time window. The tutorial's watch point is Flap-Tip = (0, 1); we take
the mean of the nodes on the upper edge of the flap (y = max), which matches
the interpolation of the preCICE watch point.

Usage:
    python tools/extract_reference.py <dir_with_vtu> <output.csv>
"""
import re
import sys
from pathlib import Path

import numpy as np

WINDOW = 0.01  # time-window-size from the tutorial precice-config.xml [s]


def read_array(text, name):
    m = re.search(rf'Name="{name}"[^>]*>(.*?)</DataArray>', text, re.S)
    return np.array(m.group(1).split(), dtype=float).reshape(-1, 3)


def main(src, out):
    src = Path(src)
    files = sorted(src.glob("Solid-Mesh-Solid.dt*.vtu"),
                   key=lambda p: int(re.search(r"dt(\d+)", p.name).group(1)))
    rows = [(0.0, 0.0, 0.0)]
    for f in files:
        n = int(re.search(r"dt(\d+)", f.name).group(1))
        text = f.read_text()
        pos = read_array(text, "Position")
        disp = read_array(text, "Displacement")
        top = np.isclose(pos[:, 1], pos[:, 1].max())
        d = disp[top].mean(axis=0)
        rows.append((n * WINDOW, d[0], d[1]))
    np.savetxt(out, rows, delimiter=",", header="time,dx,dy", comments="", fmt="%.6g")
    print(f"{len(rows)} rows -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
