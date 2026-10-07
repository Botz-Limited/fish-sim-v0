#!/usr/bin/env bash
# Stage 4, "dry" variant: the same actuation as in ../water, without water.
set -e -u
cd "$(dirname "$0")"
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
python "$d/tools/make_geometry.py" solid .
python "$d/tools/make_actuation.py" . --p0 15000 --freq 1 --t-end 8
OMP_NUM_THREADS=2 ccx_preCICE -i dry > dry.log 2>&1
