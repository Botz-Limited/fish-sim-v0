#!/usr/bin/env bash
# Stage 2: fluid only, rigid tail. Mesh convergence test (3 densities) and the
# effect of domain boundaries (1.5x domain). Each variant is a copy of fluid-openfoam/.
#   ./run_all.sh          – all variants one after another (4 MPI ranks each)
set -e -u
cd "$(dirname "$0")"
run_variant() {  # nazwa, MESH_SCALE, MESH_DOMAIN
    local name=$1
    rm -rf "$name"
    cp -r fluid-openfoam "$name"
    (cd "$name" && ./clean.sh > /dev/null && MESH_SCALE=$2 MESH_DOMAIN=$3 ./run.sh -parallel > /dev/null 2>&1) \
        && echo "$name: OK ($(grep Duration "$name/$name.log" | sed 's/.*: *//'))" \
        || echo "$name: ERROR – see $name/$name.log"
}
run_variant mesh-coarse 0.7 1.0
run_variant mesh-medium 1.0 1.0
run_variant mesh-fine   1.4 1.0
run_variant domain-1.5x 1.0 1.5
python ../tools/postprocess.py e2 .
