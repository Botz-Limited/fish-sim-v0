#!/usr/bin/env python3
"""Wyciąga przemieszczenie końcówki flapu z wyników referencyjnych preCICE.

Wyniki referencyjne tutorialu perpendicular-flap (fluid-openfoam_solid-calculix)
to eksport VTU siatki interfejsu ciała stałego w każdym oknie czasowym.
Punkt obserwacji w tutorialu to Flap-Tip = (0, 1); bierzemy średnią z węzłów
leżących na górnej krawędzi flapu (y = max), co odpowiada interpolacji
watch-pointu preCICE.

Użycie:
    python tools/extract_reference.py <katalog_z_vtu> <wyjście.csv>
"""
import re
import sys
from pathlib import Path

import numpy as np

WINDOW = 0.01  # time-window-size z precice-config.xml tutorialu [s]


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
    print(f"{len(rows)} wierszy -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
