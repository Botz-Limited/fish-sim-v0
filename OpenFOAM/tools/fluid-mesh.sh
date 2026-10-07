#!/usr/bin/env bash
# Generuje siatkę płynu w bieżącym katalogu przypadku OpenFOAM:
#   gmsh (tools/make_geometry.py) -> gmshToFoam -> typy patchy -> checkMesh
# Zmienne środowiskowe:
#   MESH_SCALE  – zagęszczenie (domyślnie 1)
#   MESH_DOMAIN – mnożnik rozmiaru domeny (domyślnie 1)
set -e -u
TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python "$TOOLS/make_geometry.py" fluid . --scale "${MESH_SCALE:-1}" --domain "${MESH_DOMAIN:-1}"
gmshToFoam fluid.msh > log.gmshToFoam 2>&1
rm -f fluid.msh

# gmshToFoam tworzy wszystkie patche jako "patch" – ustawiamy właściwe typy
B=constant/polyMesh/boundary
foamDictionary -entry entry0/frontAndBack/type -set empty "$B" > /dev/null 2>&1
foamDictionary -entry entry0/head/type -set wall "$B" > /dev/null 2>&1
foamDictionary -entry entry0/tail/type -set wall "$B" > /dev/null 2>&1
foamDictionary -entry entry0/sides/type -set patch "$B" > /dev/null 2>&1

checkMesh -constant > log.checkMesh 2>&1 || true
grep -E "cells:|Max non-orthogonality|Max skewness|Mesh OK|Failed" log.checkMesh
