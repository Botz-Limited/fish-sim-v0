#!/usr/bin/env bash
# Builds the SofaCHOLMOD plugin (solver "cholmod") for the SOFA v26.06 binary.
# Usage:  SOFA/scripts/build_cholmod_plugin.sh         (~1 min; requires: cmake, ninja, g++,
#          SuiteSparse/CHOLMOD and Eigen headers – scripts/setup.sh checks them, see README)
#
# Why: the plugin exists only in SOFA master, and master has a bug in combining a chamber
# (SurfacePressureConstraint) with stiff fibers (README, "Performance"). The sources of the plugin
# itself are copied into the repo (third_party/SofaCHOLMOD, described in VENDORED.md) and built
# against the v26.06 binary headers with two fixes:
#  1. EigenSolverFactory.h from master (overlay/): the plugin uses registerProxyType(), a template
#     added after v26.06. It is a pure header addition (no change to the class layout), so
#     it is enough to put the newer header before the binary's headers (-I), without rebuilding SOFA.
#  2. cmake/FindCHOLMOD.cmake without the SuiteSparse CMake config: the Fedora config refers
#     to nonexistent *_static.cmake files, so we search for the library manually.
set -euo pipefail

: "${FISHSOFA_HOME:=$HOME/sofa}"
: "${SOFA_ROOT:=$FISHSOFA_HOME/SOFA_v26.06.00_Linux}"
: "${FISHSOFA_CHOLMOD_PREFIX:=$FISHSOFA_HOME/SofaCHOLMOD_v26.06}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../third_party/SofaCHOLMOD" && pwd)"
BUILD="${BUILD:-$FISHSOFA_HOME/build-cholmod-v2606}"

if [ ! -f "$SOFA_ROOT/lib/cmake/Sofa.Config/Sofa.ConfigConfig.cmake" ]; then
    echo "build_cholmod_plugin.sh: SOFA not found in $SOFA_ROOT (set SOFA_ROOT or run scripts/setup.sh)" >&2
    exit 1
fi

cmake -G Ninja -S "$SRC" -B "$BUILD" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$SOFA_ROOT/lib/cmake;$SOFA_ROOT" \
    -DCMAKE_MODULE_PATH="$SRC/cmake" \
    -DCMAKE_CXX_FLAGS="-I$SRC/overlay" \
    -DCMAKE_INSTALL_PREFIX="$FISHSOFA_CHOLMOD_PREFIX" \
    -DCMAKE_INSTALL_RPATH="$SOFA_ROOT/lib" \
    -DSOFA_FLOATING_POINT_TYPE=double \
    -DSOFACHOLMOD_BUILD_TESTS=OFF
cmake --build "$BUILD"
cmake --install "$BUILD"
echo "OK: $FISHSOFA_CHOLMOD_PREFIX/lib/libSofaCHOLMOD.so (env.sh adds this directory to SOFA_PLUGIN_PATH)"
