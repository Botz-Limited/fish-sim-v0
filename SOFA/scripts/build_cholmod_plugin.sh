#!/usr/bin/env bash
# Buduje wtyczkę SofaCHOLMOD (solver "cholmod") dla binarki SOFA v26.06.
# Użycie:  SOFA/scripts/build_cholmod_plugin.sh        (~3 min; potrzebne: cmake, ninja, g++,
#          suitesparse-devel, eigen3-devel – na Fedorze `sudo dnf install ...`, patrz README)
#
# Po co: wtyczka jest tylko w SOFA master, a master ma błąd w połączeniu komory
# (SurfacePressureConstraint) ze sztywnymi włóknami (README, „Wydajność”). Bierzemy więc
# źródła samej wtyczki z master i budujemy je na nagłówkach v26.06. Dwie poprawki:
#  1. EigenSolverFactory.h z master: wtyczka używa registerProxyType(), szablonu dodanego
#     po v26.06. To czysty dodatek w nagłówku (bez zmiany układu klasy), więc wystarczy
#     podać nowszy nagłówek przed nagłówkami binarki (-I), bez przebudowy SOFA.
#  2. FindCHOLMOD.cmake: config CMake z SuiteSparse Fedory odwołuje się do nieistniejących
#     plików *_static.cmake, więc pomijamy go i szukamy biblioteki ręcznie.
set -euo pipefail

: "${SOFA_ROOT:=$HOME/sofa/SOFA_v26.06.00_Linux}"
: "${FISHSOFA_CHOLMOD_PREFIX:=$HOME/sofa/SofaCHOLMOD_v26.06}"
# Commit SOFA master, z którego wzięto wtyczkę (sprawdzony z v26.06).
SOFA_REF="${SOFA_REF:-6c3e21f204ab78cdaedd94d8cf412e4f2e002f1e}"
WORK="${WORK:-$HOME/sofa/build-cholmod-v2606}"

mkdir -p "$WORK" && cd "$WORK"
if [ ! -d src/.git ]; then
    git init -q src
    git -C src remote add origin https://github.com/sofa-framework/sofa.git
    git -C src sparse-checkout set applications/plugins/SofaCHOLMOD cmake/Modules \
        Sofa/Component/LinearSolver/Direct/src/sofa/component/linearsolver/direct
fi
git -C src fetch -q --depth 1 origin "$SOFA_REF"
git -C src checkout -q FETCH_HEAD

# Poprawka 1: nakładka z nowszym nagłówkiem.
OV="$WORK/overlay/sofa/component/linearsolver/direct"
mkdir -p "$OV"
cp src/Sofa/Component/LinearSolver/Direct/src/sofa/component/linearsolver/direct/EigenSolverFactory.h "$OV/"

# Poprawka 2: FindCHOLMOD.cmake bez configu SuiteSparse.
mkdir -p cmake
python3 - "$WORK/src/cmake/Modules/FindCHOLMOD.cmake" "$WORK/cmake/FindCHOLMOD.cmake" <<'EOF'
import sys
s = open(sys.argv[1]).read()
a = s.index("find_package(SuiteSparse CONFIG QUIET COMPONENTS CHOLMOD)")
b = s.index("# Fallback: manual search")
open(sys.argv[2], "w").write(s[:a] + s[b:])
EOF

cmake -G Ninja -S src/applications/plugins/SofaCHOLMOD -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$SOFA_ROOT/lib/cmake;$SOFA_ROOT" \
    -DCMAKE_MODULE_PATH="$WORK/cmake" \
    -DCMAKE_CXX_FLAGS="-I$WORK/overlay" \
    -DCMAKE_INSTALL_PREFIX="$FISHSOFA_CHOLMOD_PREFIX" \
    -DCMAKE_INSTALL_RPATH="$SOFA_ROOT/lib" \
    -DSOFA_FLOATING_POINT_TYPE=double \
    -DSOFACHOLMOD_BUILD_TESTS=OFF
cmake --build build
cmake --install build
echo "OK: $FISHSOFA_CHOLMOD_PREFIX/lib/libSofaCHOLMOD.so (env.sh dodaje ten katalog do SOFA_PLUGIN_PATH)"
