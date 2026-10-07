#!/usr/bin/env bash
# Creates an OpenFOAM case directory from tools/fluid-base.
#   new-fluid-case.sh <directory> [--fsi]
# Without --fsi: static mesh (stage 2, rigid tail).
# With --fsi:   moving mesh + preCICE adapter (stages 3–6).
set -e -u
TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$1"; MODE="${2:-}"
mkdir -p "$DEST"
cp -r "$TOOLS/fluid-base/." "$DEST/"
cd "$DEST"
if [ "$MODE" = "--fsi" ]; then
    mv system/preciceDict.fsi system/preciceDict
    mv system/preciceFunctionObject.fsi system/preciceFunctionObject
else
    rm -f system/*.fsi constant/dynamicMeshDict 0/pointDisplacement
fi
