#!/usr/bin/env bash
# Buduje wtyczkę SofaCHOLMOD (solver "cholmod") dla binarki SOFA v26.06.
# Użycie:  SOFA/scripts/build_cholmod_plugin.sh        (~1 min; potrzebne: cmake, ninja, g++,
#          nagłówki SuiteSparse/CHOLMOD i Eigen – scripts/setup.sh je sprawdza, patrz README)
#
# Po co: wtyczka jest tylko w SOFA master, a master ma błąd w połączeniu komory
# (SurfacePressureConstraint) ze sztywnymi włóknami (README, „Wydajność”). Źródła samej
# wtyczki są skopiowane do repo (third_party/SofaCHOLMOD, opis w VENDORED.md) i budowane
# na nagłówkach binarki v26.06 z dwiema poprawkami:
#  1. EigenSolverFactory.h z master (overlay/): wtyczka używa registerProxyType(), szablonu
#     dodanego po v26.06. To czysty dodatek w nagłówku (bez zmiany układu klasy), więc
#     wystarczy podać nowszy nagłówek przed nagłówkami binarki (-I), bez przebudowy SOFA.
#  2. cmake/FindCHOLMOD.cmake bez configu CMake z SuiteSparse: config z Fedory odwołuje się
#     do nieistniejących plików *_static.cmake, więc szukamy biblioteki ręcznie.
set -euo pipefail

: "${FISHSOFA_HOME:=$HOME/sofa}"
: "${SOFA_ROOT:=$FISHSOFA_HOME/SOFA_v26.06.00_Linux}"
: "${FISHSOFA_CHOLMOD_PREFIX:=$FISHSOFA_HOME/SofaCHOLMOD_v26.06}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../third_party/SofaCHOLMOD" && pwd)"
BUILD="${BUILD:-$FISHSOFA_HOME/build-cholmod-v2606}"

if [ ! -f "$SOFA_ROOT/lib/cmake/Sofa.Config/Sofa.ConfigConfig.cmake" ]; then
    echo "build_cholmod_plugin.sh: brak SOFA w $SOFA_ROOT (ustaw SOFA_ROOT albo uruchom scripts/setup.sh)" >&2
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
echo "OK: $FISHSOFA_CHOLMOD_PREFIX/lib/libSofaCHOLMOD.so (env.sh dodaje ten katalog do SOFA_PLUGIN_PATH)"
