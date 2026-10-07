#!/usr/bin/env bash
# Etap 2: sam płyn, sztywny ogon. Test zbieżności siatki (3 gęstości) i wpływu
# granic domeny (domena 1.5x). Każdy wariant to kopia fluid-openfoam/.
#   ./run_all.sh          – wszystkie warianty po kolei (4 procesy MPI każdy)
set -e -u
cd "$(dirname "$0")"
run_variant() {  # nazwa, MESH_SCALE, MESH_DOMAIN
    local name=$1
    rm -rf "$name"
    cp -r fluid-openfoam "$name"
    (cd "$name" && ./clean.sh > /dev/null && MESH_SCALE=$2 MESH_DOMAIN=$3 ./run.sh -parallel > /dev/null 2>&1) \
        && echo "$name: OK ($(grep Duration "$name/$name.log" | sed 's/.*: *//'))" \
        || echo "$name: BŁĄD – patrz $name/$name.log"
}
run_variant mesh-coarse 0.7 1.0
run_variant mesh-medium 1.0 1.0
run_variant mesh-fine   1.4 1.0
run_variant domain-1.5x 1.0 1.5
python ../tools/postprocess.py e2 .
