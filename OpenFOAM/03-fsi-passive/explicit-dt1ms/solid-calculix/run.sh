#!/usr/bin/env bash
# Participant "Solid": tail mesh + actuation + CalculiX with the preCICE adapter.
set -e -u
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
TOOLS="$d/tools"
. "$TOOLS/log.sh"
exec > >(tee --append "$LOGFILE") 2>&1

python "$TOOLS/make_geometry.py" solid .
python "$TOOLS/make_actuation.py" . --p0 0 --freq 1 --t-end 0.1
ccx_preCICE -i fsi -precice-participant Solid

close_log
