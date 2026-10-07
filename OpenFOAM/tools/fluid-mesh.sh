#!/usr/bin/env bash
# Generates the fluid mesh in the current OpenFOAM case directory:
#   gmsh (tools/make_geometry.py) -> gmshToFoam -> patch types -> checkMesh
# Environment variables:
#   MESH_SCALE  – refinement factor (default 1)
#   MESH_DOMAIN – domain size multiplier (default 1)
set -e -u
TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python "$TOOLS/make_geometry.py" fluid . --scale "${MESH_SCALE:-1}" --domain "${MESH_DOMAIN:-1}"
gmshToFoam fluid.msh > log.gmshToFoam 2>&1
rm -f fluid.msh

# gmshToFoam creates every patch as type "patch" – set the proper types
B=constant/polyMesh/boundary
foamDictionary -entry entry0/frontAndBack/type -set empty "$B" > /dev/null 2>&1
foamDictionary -entry entry0/head/type -set wall "$B" > /dev/null 2>&1
foamDictionary -entry entry0/tail/type -set wall "$B" > /dev/null 2>&1
foamDictionary -entry entry0/sides/type -set patch "$B" > /dev/null 2>&1

checkMesh -constant > log.checkMesh 2>&1 || true
grep -E "cells:|Max non-orthogonality|Max skewness|Mesh OK|Failed" log.checkMesh
