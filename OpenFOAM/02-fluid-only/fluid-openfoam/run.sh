#!/usr/bin/env bash
# Stage 2: fluid only, rigid tail (static mesh).
#   ./run.sh            – serial
#   ./run.sh -parallel  – MPI according to system/decomposeParDict
set -e -u
. ../../tools/log.sh
exec > >(tee --append "$LOGFILE") 2>&1

../../tools/fluid-mesh.sh
../../tools/run-openfoam.sh "$@"

close_log
