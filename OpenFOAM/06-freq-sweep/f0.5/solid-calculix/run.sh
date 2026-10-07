#!/usr/bin/env bash
# Uczestnik "Solid": siatka ogona + aktuacja + CalculiX z adapterem preCICE.
set -e -u
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
TOOLS="$d/tools"
. "$TOOLS/log.sh"
exec > >(tee --append "$LOGFILE") 2>&1

python "$TOOLS/make_geometry.py" solid .
python "$TOOLS/make_actuation.py" . --p0 15000 --freq 0.5 --t-end 16
ccx_preCICE -i fsi -precice-participant Solid

close_log
