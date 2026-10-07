#!/usr/bin/env sh
set -e -u
cd "$(dirname "$0")"
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
. "$d/tools/cleaning-tools.sh"
rm -f tail.msh tail_sets.nam material.inc amplitude.inc dload.inc
clean_calculix .
