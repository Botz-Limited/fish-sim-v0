#!/usr/bin/env bash
# Etap 2: sam płyn, sztywny ogon (siatka nieruchoma).
#   ./run.sh            – szeregowo
#   ./run.sh -parallel  – MPI wg system/decomposeParDict
set -e -u
. ../../tools/log.sh
exec > >(tee --append "$LOGFILE") 2>&1

../../tools/fluid-mesh.sh
../../tools/run-openfoam.sh "$@"

close_log
