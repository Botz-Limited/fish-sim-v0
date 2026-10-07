# Environment for running SOFA from Python (pytest, scripts) and runSofa.
# Usage (from any directory):  source SOFA/scripts/env.sh
#
# What happens here and why:
# - FISHSOFA_HOME: directory outside the repo with the SOFA binary and the CHOLMOD plugin (default ~/sofa;
#   same as in scripts/setup.sh). SOFA_ROOT: directory of the unpacked SOFA binary
#   (~800 MB). Both can be overridden before `source`, e.g. SOFA_ROOT=/opt/sofa source ...
# - The SOFA binary has Python modules (Sofa, SofaRuntime, softrobots, stlib3)
#   in the plugin directories, not in Python's site-packages -> we add them to PYTHONPATH.
# - SofaPython3 modules are linked against libpython3.12.so.1.0. Fedora does not have it
#   (the system Python is 3.14); it is in the conda environment `fishsofa`. We do not add
#   the whole $CONDA_PREFIX/lib to LD_LIBRARY_PATH, because then libstdc++ from conda
#   would shadow the system one (risk of OpenGL driver errors in the GUI).
#   Instead, a separate directory with a single symlink to libpython.

: "${FISHSOFA_HOME:=$HOME/sofa}"
: "${SOFA_ROOT:=$FISHSOFA_HOME/SOFA_v26.06.00_Linux}"
: "${FISHSOFA_CONDA_ENV:=fishsofa}"
export SOFA_ROOT

if [ ! -x "$SOFA_ROOT/bin/runSofa" ]; then
    echo "env.sh: $SOFA_ROOT/bin/runSofa not found – set SOFA_ROOT (see SOFA/README.md)" >&2
    return 1 2>/dev/null || exit 1
fi

# Activate the conda environment with Python 3.12 (the version must match the SOFA binary).
if [ "${CONDA_DEFAULT_ENV:-}" != "$FISHSOFA_CONDA_ENV" ]; then
    eval "$(conda shell.bash hook 2>/dev/null || conda shell.zsh hook 2>/dev/null)"
    conda activate "$FISHSOFA_CONDA_ENV" || { echo "env.sh: conda environment $FISHSOFA_CONDA_ENV not found" >&2; return 1 2>/dev/null || exit 1; }
fi

# Directory with only libpython (see the comment at the top).
FISHSOFA_PYLIB="$SOFA_ROOT/../fishsofa-pylib"
mkdir -p "$FISHSOFA_PYLIB"
ln -sf "$CONDA_PREFIX/lib/libpython3.12.so.1.0" "$FISHSOFA_PYLIB/libpython3.12.so.1.0"
# BLAS/LAPACK for CHOLMOD: OpenBLAS from conda (environment.yml) instead of the system one.
# Supernodal CHOLMOD computes dense blocks in BLAS, so its quality determines the step time.
# On Arch the system libblas.so.3 is the reference (unoptimized) BLAS from netlib:
# 470 ms/step, with OpenBLAS 217 ms/step (coarse, flapping), identical result (README,
# "Performance"). We symlink only these libraries, for the same reason as libpython.
for _l in libblas.so.3 liblapack.so.3 libgfortran.so.5 libquadmath.so.0; do
    [ -e "$CONDA_PREFIX/lib/libopenblas.so.0" ] && [ -e "$CONDA_PREFIX/lib/$_l" ] \
        && ln -sf "$CONDA_PREFIX/lib/$_l" "$FISHSOFA_PYLIB/$_l"
done
unset _l
# One BLAS thread per process: CHOLMOD blocks are small (4 threads = same time), and sweeps
# (stage 6) run many simulations in parallel – more threads would only contend.
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
case ":${LD_LIBRARY_PATH:-}:" in
    *":$FISHSOFA_PYLIB:"*) ;;
    *) export LD_LIBRARY_PATH="$FISHSOFA_PYLIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" ;;
esac

# Python modules provided by SOFA plugins.
for _p in SofaPython3 SoftRobots STLIB; do
    _sp="$SOFA_ROOT/plugins/$_p/lib/python3/site-packages"
    case ":${PYTHONPATH:-}:" in
        *":$_sp:"*) ;;
        *) [ -d "$_sp" ] && export PYTHONPATH="$_sp${PYTHONPATH:+:$PYTHONPATH}" ;;
    esac
done
unset _p _sp

# SofaCHOLMOD plugin (solver "cholmod"), built separately for the v26.06 binary – the binary
# does not include it (README, "Installation"). SOFA also looks for plugins in SOFA_PLUGIN_PATH.
: "${FISHSOFA_CHOLMOD_LIB:=$FISHSOFA_HOME/SofaCHOLMOD_v26.06/lib}"
if [ -f "$FISHSOFA_CHOLMOD_LIB/libSofaCHOLMOD.so" ]; then
    export SOFA_PLUGIN_PATH="$FISHSOFA_CHOLMOD_LIB${SOFA_PLUGIN_PATH:+:$SOFA_PLUGIN_PATH}"
else
    echo "env.sh: SofaCHOLMOD plugin not found in $FISHSOFA_CHOLMOD_LIB – solver \"cholmod\" will not work" >&2
fi

# The SOFA/ project directory also on PYTHONPATH, so that `import fishsofa` works without installation.
_here="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/.." && pwd)"
case ":$PYTHONPATH:" in *":$_here:"*) ;; *) export PYTHONPATH="$_here:$PYTHONPATH" ;; esac
unset _here
