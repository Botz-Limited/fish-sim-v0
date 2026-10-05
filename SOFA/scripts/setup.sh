#!/usr/bin/env bash
# Instalacja demo SOFA od zera na nowym komputerze (Linux x86_64; sprawdzone: Fedora 44).
#
# Użycie (z dowolnego katalogu):
#   SOFA/scripts/setup.sh                  # sprawdza zależności systemowe i instaluje resztę
#   SOFA/scripts/setup.sh --install-deps   # to samo, ale brakujące pakiety systemowe instaluje (sudo)
#   SOFA/scripts/setup.sh --no-tests       # bez końcowego pytest (~80 s)
#
# Co robi (każdy krok pomija, jeśli jest już zrobiony):
#   1. zależności systemowe: kompilator, cmake, ninja, SuiteSparse/CHOLMOD, Eigen, biblioteki
#      OpenGL/X11 dla gmsh i GUI SOFA – wypisuje komendę dnf/apt, jeśli czegoś brakuje,
#   2. binarka SOFA v26.06.00 (z SoftRobots, STLIB, SofaPython3) -> $FISHSOFA_HOME (~/sofa),
#      z kontrolą sumy SHA-256,
#   3. środowisko conda `fishsofa` z SOFA/environment.yml (Python 3.12 + przypięte pakiety),
#   4. wtyczka SofaCHOLMOD z third_party/ (scripts/build_cholmod_plugin.sh),
#   5. kontrola: check_sofa.py (nazwy komponentów) i pytest.
# Potem w każdej nowej powłoce:  source SOFA/scripts/env.sh
#
# Wymagane wcześniej: conda (np. Miniforge: https://github.com/conda-forge/miniforge).
set -euo pipefail

INSTALL_DEPS=0
RUN_TESTS=1
for a in "$@"; do
    case "$a" in
        --install-deps) INSTALL_DEPS=1 ;;
        --no-tests) RUN_TESTS=0 ;;
        *) echo "nieznana opcja: $a" >&2; exit 2 ;;
    esac
done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(cd "$HERE/.." && pwd)"
export FISHSOFA_HOME="${FISHSOFA_HOME:-$HOME/sofa}"
export FISHSOFA_CONDA_ENV="${FISHSOFA_CONDA_ENV:-fishsofa}"
SOFA_VERSION=v26.06.00
SOFA_ZIP="SOFA_${SOFA_VERSION}_Linux_Python3.12.zip"
SOFA_URL="https://github.com/sofa-framework/sofa/releases/download/${SOFA_VERSION}/${SOFA_ZIP}"
SOFA_SHA256=2a5c80dd012a433c36bae11ed06df701eb447387b6d2657410b2ef76ff2e32be
export SOFA_ROOT="${SOFA_ROOT:-$FISHSOFA_HOME/SOFA_${SOFA_VERSION}_Linux}"

step() { printf '\n== %s\n' "$*"; }

# --------------------------------------------------------------------------- 1. system
step "1/5 zależności systemowe"
. /etc/os-release 2>/dev/null || true
case " ${ID:-} ${ID_LIKE:-} " in
    *" fedora "*|*" rhel "*)
        PKG="sudo dnf install -y"
        PKGS="curl unzip git cmake ninja-build gcc-c++ suitesparse-devel eigen3-devel flexiblas-devel \
mesa-libGLU libglvnd-opengl libXcursor libXft libXinerama" ;;
    *" debian "*|*" ubuntu "*)
        PKG="sudo apt-get install -y"
        PKGS="curl unzip git cmake ninja-build g++ libsuitesparse-dev libeigen3-dev libopenblas-dev \
libglu1-mesa libopengl0 libxcursor1 libxft2 libxinerama1" ;;
    *)
        PKG=""
        PKGS="(nieznana dystrybucja: zainstaluj odpowiedniki pakietów z listy dla Fedory/Ubuntu w tym skrypcie)" ;;
esac

missing=()
for c in curl unzip git cmake ninja g++; do command -v "$c" >/dev/null || missing+=("polecenie $c"); done
[ -f /usr/include/suitesparse/cholmod.h ] || [ -f /usr/include/cholmod.h ] || missing+=("nagłówek cholmod.h (SuiteSparse)")
[ -f /usr/include/eigen3/Eigen/Core ] || missing+=("Eigen 3 (/usr/include/eigen3)")
for l in libGLU.so.1 libOpenGL.so.0 libXcursor.so.1 libXft.so.2 libXinerama.so.1; do
    ldconfig -p 2>/dev/null | grep -q "$l" || missing+=("biblioteka $l")
done
if [ ${#missing[@]} -gt 0 ]; then
    printf 'Brakuje: %s\n' "${missing[@]}"
    if [ "$INSTALL_DEPS" = 1 ] && [ -n "$PKG" ]; then
        # shellcheck disable=SC2086
        $PKG $PKGS
    else
        echo "Zainstaluj (albo uruchom ten skrypt z --install-deps):"
        echo "  $PKG $PKGS"
        exit 1
    fi
else
    echo "OK"
fi
command -v conda >/dev/null || { echo "Brak condy. Zainstaluj np. Miniforge: https://github.com/conda-forge/miniforge" >&2; exit 1; }

# --------------------------------------------------------------------------- 2. SOFA
step "2/5 SOFA ${SOFA_VERSION} -> $SOFA_ROOT"
if [ -x "$SOFA_ROOT/bin/runSofa" ]; then
    echo "już jest"
else
    mkdir -p "$FISHSOFA_HOME"
    zip="$FISHSOFA_HOME/$SOFA_ZIP"
    [ -f "$zip" ] || curl -fL --retry 3 -o "$zip" "$SOFA_URL"     # ~230 MB
    echo "$SOFA_SHA256  $zip" | sha256sum -c -
    unzip -q -o "$zip" -d "$(dirname "$SOFA_ROOT")"                # ~800 MB
    [ -x "$SOFA_ROOT/bin/runSofa" ] || { echo "po rozpakowaniu brak $SOFA_ROOT/bin/runSofa" >&2; exit 1; }
    rm -f "$zip"
fi

# --------------------------------------------------------------------------- 3. conda
step "3/5 środowisko conda $FISHSOFA_CONDA_ENV"
eval "$(conda shell.bash hook)"
if conda env list | awk '{print $1}' | grep -qx "$FISHSOFA_CONDA_ENV"; then
    conda env update -n "$FISHSOFA_CONDA_ENV" -f "$PROJECT/environment.yml"
else
    conda env create -y -n "$FISHSOFA_CONDA_ENV" -f "$PROJECT/environment.yml"
fi

# --------------------------------------------------------------------------- 4. CHOLMOD
step "4/5 wtyczka SofaCHOLMOD"
if [ -f "$FISHSOFA_HOME/SofaCHOLMOD_v26.06/lib/libSofaCHOLMOD.so" ]; then
    echo "już jest"
else
    "$HERE/build_cholmod_plugin.sh"
fi

# --------------------------------------------------------------------------- 5. kontrola
step "5/5 kontrola"
# shellcheck disable=SC1091
source "$HERE/env.sh"
python "$HERE/check_sofa.py" > "$FISHSOFA_HOME/check_sofa.log" 2>&1 \
    || { echo "check_sofa.py nie przeszedł – log: $FISHSOFA_HOME/check_sofa.log" >&2; exit 1; }
echo "check_sofa.py: OK"
if [ "$RUN_TESTS" = 1 ]; then
    (cd "$PROJECT" && python -m pytest -q tests 2>&1 | grep -E "passed|failed|error")
fi
echo
echo "Gotowe. W nowej powłoce:  source $HERE/env.sh"
echo "GUI (ogon macha):          $HERE/run_gui.sh"
