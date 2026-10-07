# Środowisko FSI: OpenFOAM v2606 + preCICE 3.4.1 + CalculiX 2.20 (adapter 2.20.2).
# Użycie:  source OpenFOAM/env.sh   (bash lub zsh)
export FSI_PREFIX="$HOME/opt/fsi"
export PATH="$FSI_PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$FSI_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="$FSI_PREFIX/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
export CPATH="$FSI_PREFIX/include${CPATH:+:$CPATH}"
export CMAKE_PREFIX_PATH="$FSI_PREFIX${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
export CCACHE_DIR="$HOME/.cache/ccache"

# OpenFOAM (etc/bashrc obsługuje bash i zsh)
source "$HOME/OpenFOAM/OpenFOAM-v2606/etc/bashrc"

# CalculiX: solver PARDISO (Intel MKL z pip, w venv) + OpenMP.
# 2 wątki dla ciała stałego; płyn dostaje 4 procesy MPI (decomposeParDict).
# Uwaga: SPOOLES z 4 wątkami dawał błędne wyniki (NOTES.md) – nie używać.
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
export MKL_NUM_THREADS="$OMP_NUM_THREADS"
export CCX_NPROC_EQUATION_SOLVER="$OMP_NUM_THREADS"
export CCX_NPROC_STIFFNESS="$OMP_NUM_THREADS"
export CCX_NPROC_RESULTS="$OMP_NUM_THREADS"

# Python (gmsh, meshio + systemowe numpy/matplotlib/pandas/scipy)
source "$FSI_PREFIX/venv/bin/activate"
