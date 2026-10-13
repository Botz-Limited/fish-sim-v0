#!/usr/bin/env bash
# Participant "Fluid": mesh (gmsh) + pimpleFoam with the preCICE adapter.
#   ./run.sh -parallel   – MPI according to system/decomposeParDict (recommended)
set -e -u
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
TOOLS="$d/tools"
. "$TOOLS/log.sh"
exec > >(tee --append "$LOGFILE") 2>&1

"$TOOLS/fluid-mesh.sh"
"$TOOLS/run-openfoam.sh" "$@"

close_log
