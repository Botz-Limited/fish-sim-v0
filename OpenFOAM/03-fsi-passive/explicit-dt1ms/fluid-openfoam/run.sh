#!/usr/bin/env bash
# Uczestnik "Fluid": siatka (gmsh) + pimpleFoam z adapterem preCICE.
#   ./run.sh -parallel   – MPI wg system/decomposeParDict (zalecane)
set -e -u
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
TOOLS="$d/tools"
. "$TOOLS/log.sh"
exec > >(tee --append "$LOGFILE") 2>&1

"$TOOLS/fluid-mesh.sh"
"$TOOLS/run-openfoam.sh" "$@"

close_log
