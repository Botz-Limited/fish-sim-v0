#!/usr/bin/env bash
# =============================================================================
# FSI environment installation: OpenFOAM v2606 + preCICE 3.4.1 + CalculiX 2.20
# (adapter 2.20.2, PARDISO from Intel MKL) + OpenFOAM adapter 1.4.0.
# Arch Linux / EndeavourOS. Everything except system packages is installed
# in the home directory (no sudo): ~/opt/fsi, ~/OpenFOAM.
#
# Time on a Ryzen AI 5 PRO 340 (6 cores / 12 threads): ~1.5 h (mostly OpenFOAM).
#
#   ./setup.sh            – everything in order (skips steps already done)
#
# Before running (once, needs your password):
#   sudo pacman -S --needed openmpi scotch gcc-fortran arpack ccache git-lfs \
#        paraview python-matplotlib python-pandas python-scipy
# =============================================================================
set -e -o pipefail
NJ=$(nproc --all)
SRC=$HOME/opt/src
PREFIX=$HOME/opt/fsi
FOAM=$HOME/OpenFOAM/OpenFOAM-v2606
mkdir -p "$SRC" "$PREFIX/bin"
cd "$SRC"

step() { echo; echo "=== $* ==="; }

for p in openmpi scotch gcc-fortran arpack ccache paraview python-matplotlib; do
    pacman -Q $p > /dev/null 2>&1 || { echo "Missing package $p – first run the sudo pacman command from the header."; exit 1; }
done

# -----------------------------------------------------------------------------
step "1/7 Sources"
[ -f OpenFOAM-v2606.tgz ] || curl -sSLO https://dl.openfoam.com/source/v2606/OpenFOAM-v2606.tgz
echo "35cbe9bc512fe087e4a472b1cb610063  OpenFOAM-v2606.tgz" | md5sum -c
[ -f precice-3.4.1.tar.gz ] || curl -sSL -o precice-3.4.1.tar.gz https://github.com/precice/precice/archive/v3.4.1.tar.gz
[ -f openfoam-adapter-1.4.0.tar.gz ] || curl -sSL -o openfoam-adapter-1.4.0.tar.gz \
    https://github.com/precice/openfoam-adapter/releases/download/v1.4.0/openfoam-adapter-1.4.0-OpenFOAMv1812-v2606-newer.tar.gz
[ -f calculix-adapter-2.20.2.tar.gz ] || curl -sSL -o calculix-adapter-2.20.2.tar.gz https://github.com/precice/calculix-adapter/archive/v2.20.2.tar.gz
[ -f ccx_2.20.src.tar.bz2 ] || curl -sSLO http://www.dhondt.de/ccx_2.20.src.tar.bz2
[ -f spooles.2.2.tgz ] || curl -sSLO https://www.netlib.org/linalg/spooles/spooles.2.2.tgz
[ -f eigen-3.4.0.tar.gz ] || curl -sSL -o eigen-3.4.0.tar.gz https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz
[ -d tutorials ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q https://github.com/precice/tutorials.git

# -----------------------------------------------------------------------------
step "2/7 Python (venv: gmsh, meshio, MKL for PARDISO)"
[ -d "$PREFIX/venv" ] || python3 -m venv --system-site-packages "$PREFIX/venv"
"$PREFIX/venv/bin/pip" install -q gmsh meshio mkl-devel
M=$PREFIX/venv/lib
mkdir -p "$PREFIX/mkl"
for l in mkl_rt mkl_core mkl_gnu_thread mkl_intel_lp64; do ln -sf "$M/lib$l.so.3" "$PREFIX/mkl/lib$l.so"; done

# -----------------------------------------------------------------------------
step "3/7 preCICE 3.4.1 (Release, -march=native, Eigen 3.4)"
if [ ! -f "$PREFIX/lib/libprecice.so" ]; then
    # Eigen 5 from Arch causes an FPE in RBF mapping under the OpenFOAM trap (NOTES.md)
    tar xzf eigen-3.4.0.tar.gz
    cmake -S eigen-3.4.0 -B eigen-build -DCMAKE_INSTALL_PREFIX="$PREFIX/eigen-3.4" -DBUILD_TESTING=OFF > /dev/null
    cmake --install eigen-build > /dev/null
    tar xzf precice-3.4.1.tar.gz
    cmake -S precice-3.4.1 -B precice-build -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CXX_FLAGS="-march=native" -DCMAKE_C_FLAGS="-march=native" \
        -DCMAKE_INSTALL_PREFIX="$PREFIX" -DBUILD_SHARED_LIBS=ON -DBUILD_TESTING=OFF \
        -DEigen3_DIR="$PREFIX/eigen-3.4/share/eigen3/cmake" -DCMAKE_IGNORE_PATH=/usr/share/eigen3/cmake \
        -DPRECICE_FEATURE_MPI_COMMUNICATION=ON -DPRECICE_FEATURE_PETSC_MAPPING=OFF \
        -DPRECICE_FEATURE_PYTHON_ACTIONS=OFF -DPRECICE_FEATURE_GINKGO_MAPPING=OFF \
        -DPRECICE_BINDINGS_C=ON -DPRECICE_BINDINGS_FORTRAN=OFF -DPRECICE_BUILD_TOOLS=ON \
        -DCMAKE_CXX_COMPILER_LAUNCHER=ccache -Wno-dev > precice-cmake.log
    cmake --build precice-build -j "$NJ" > precice-build.log
    cmake --install precice-build > /dev/null
fi

# -----------------------------------------------------------------------------
step "4/7 SPOOLES 2.2 + CalculiX 2.20 + adapter 2.20.2 (PARDISO/MKL, OpenMP)"
if [ ! -f "$PREFIX/bin/ccx_preCICE" ]; then
    mkdir -p "$PREFIX/spooles" && tar xzf spooles.2.2.tgz -C "$PREFIX/spooles"
    ( cd "$PREFIX/spooles"
      sed -i 's|^  CC = /usr/lang-4.0/bin/cc|  CC = gcc|; s|^  OPTLEVEL = -O$|  OPTLEVEL = -O3 -march=native -std=gnu89 -fcommon -w|' Make.inc
      make lib > build.log 2>&1
      (cd MT/src && make -f makeGlobalLib >> ../../build.log 2>&1) )
    mkdir -p ccx && tar xjf ccx_2.20.src.tar.bz2 -C ccx
    rm -rf calculix-adapter-2.20.2 && tar xzf calculix-adapter-2.20.2.tar.gz
    ( cd calculix-adapter-2.20.2
      sed -i -e 's|^CFLAGS  = -Wall -O3 -fopenmp|CFLAGS  = -std=gnu11 -w -O3 -march=native -fopenmp|' \
             -e 's|^FFLAGS = -Wall -O3 -fopenmp|FFLAGS = -w -O3 -march=native -fopenmp|' \
             -e 's|-fopenmp -Wall -O3 -o|-fopenmp -O3 -march=native -o|' \
             -e '/^CFLAGS += -DARCH/s/-DSPOOLES /-DSPOOLES -DPARDISO /' Makefile
      PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig" make -j "$NJ" CCX="$SRC/ccx/CalculiX/ccx_2.20/src" \
          SPOOLES_INCLUDE="-I$PREFIX/spooles -I$PREFIX/venv/include" \
          SPOOLES_LIBS="$PREFIX/spooles/spooles.a -L$PREFIX/mkl -Wl,-rpath,$M -lmkl_gnu_thread -lmkl_core -lmkl_intel_lp64 -lgomp" \
          > build.log 2>&1
      cp bin/ccx_preCICE "$PREFIX/bin/" )
fi

# -----------------------------------------------------------------------------
step "5/7 OpenFOAM v2606 (-O3 -march=native, ccache) – approx. 1.5 h"
if [ ! -x "$FOAM/platforms/linux64GccDPInt32Opt/bin/pimpleFoam" ]; then
    mkdir -p "$HOME/OpenFOAM" && [ -d "$FOAM" ] || tar xzf OpenFOAM-v2606.tgz -C "$HOME/OpenFOAM"
    cat > "$FOAM/etc/prefs.sh" <<'EOF'
export WM_COMPILER_TYPE=system
export WM_MPLIB=SYSTEMOPENMPI
export WM_COMPILE_CONTROL="+ccache"
export FOAM_EXTRA_CFLAGS="-march=native"
export FOAM_EXTRA_CXXFLAGS="-march=native"
EOF
    "$FOAM/bin/tools/foamConfigurePaths" -adios adios-none -boost boost-system -cgal cgal-none \
        -fftw fftw-system -kahip kahip-none -metis metis-none -scotch scotch-system > /dev/null
    sed -i 's/^ParaView_VERSION=.*/ParaView_VERSION=none/' "$FOAM/etc/config.sh/paraview"
    # two passes: in parallel mode some applications link before their libraries exist
    bash -c "set +e; source $FOAM/etc/bashrc; cd $FOAM; ./Allwmake -j $NJ -s -q -l > /dev/null 2>&1; ./Allwmake -j $NJ -s -l > /dev/null 2>&1"
fi

# -----------------------------------------------------------------------------
step "6/7 OpenFOAM-preCICE adapter 1.4.0"
mkdir -p openfoam-adapter && tar xzf openfoam-adapter-1.4.0.tar.gz -C openfoam-adapter --strip-components=1
bash -c "source $FOAM/etc/bashrc; export PKG_CONFIG_PATH=$PREFIX/lib/pkgconfig CPATH=$PREFIX/include LD_LIBRARY_PATH=$PREFIX/lib:\$LD_LIBRARY_PATH; cd openfoam-adapter && ./Allwmake > build.log 2>&1 && tail -1 build.log"

# -----------------------------------------------------------------------------
step "7/7 Test"
source "$(dirname "$0")/env.sh" > /dev/null 2>&1 || source "$(cd "$(dirname "$0")" && pwd)/env.sh"
precice-version | cut -d';' -f1
which pimpleFoam ccx_preCICE
echo "Done. Next: source OpenFOAM/env.sh  and  (cd OpenFOAM/00-reference-flap; ...)"
