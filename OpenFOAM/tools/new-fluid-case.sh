#!/usr/bin/env bash
# Tworzy katalog przypadku OpenFOAM na bazie tools/fluid-base.
#   new-fluid-case.sh <katalog> [--fsi]
# Bez --fsi: siatka nieruchoma (etap 2, sztywny ogon).
# Z --fsi:  ruchoma siatka + adapter preCICE (etapy 3–5).
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
