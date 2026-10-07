#!/usr/bin/env bash
# Etap 4, wariant "na sucho": ta sama aktuacja co w ../water, bez wody.
set -e -u
cd "$(dirname "$0")"
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
python "$d/tools/make_geometry.py" solid .
python "$d/tools/make_actuation.py" . --p0 15000 --freq 1 --t-end 8
OMP_NUM_THREADS=2 ccx_preCICE -i dry > dry.log 2>&1
