#!/usr/bin/env sh
set -e -u
cd "$(dirname "$0")"
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
. "$d/tools/cleaning-tools.sh"
clean_openfoam .
