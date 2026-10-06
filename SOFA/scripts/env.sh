# Środowisko do uruchamiania SOFA z Pythona (pytest, skrypty) i runSofa.
# Użycie (z dowolnego katalogu):  source SOFA/scripts/env.sh
#
# Co tu się dzieje i dlaczego:
# - FISHSOFA_HOME: katalog poza repo z binarką SOFA i wtyczką CHOLMOD (domyślnie ~/sofa;
#   tak samo jak w scripts/setup.sh). SOFA_ROOT: katalog rozpakowanej binarki SOFA
#   (~800 MB). Oba można nadpisać przed `source`, np. SOFA_ROOT=/opt/sofa source ...
# - Binarka SOFA ma moduły Pythona (Sofa, SofaRuntime, softrobots, stlib3)
#   w katalogach pluginów, a nie w site-packages Pythona -> dopisujemy je do PYTHONPATH.
# - Moduły SofaPython3 są zlinkowane z libpython3.12.so.1.0. Fedora jej nie ma
#   (systemowy Python to 3.14), jest w środowisku conda `fishsofa`. Nie dodajemy
#   całego $CONDA_PREFIX/lib do LD_LIBRARY_PATH, bo wtedy libstdc++ z condy
#   przesłoniłaby systemową (ryzyko błędów sterowników OpenGL w GUI).
#   Zamiast tego osobny katalog z jednym dowiązaniem do libpython.

: "${FISHSOFA_HOME:=$HOME/sofa}"
: "${SOFA_ROOT:=$FISHSOFA_HOME/SOFA_v26.06.00_Linux}"
: "${FISHSOFA_CONDA_ENV:=fishsofa}"
export SOFA_ROOT

if [ ! -x "$SOFA_ROOT/bin/runSofa" ]; then
    echo "env.sh: brak $SOFA_ROOT/bin/runSofa – ustaw SOFA_ROOT (patrz SOFA/README.md)" >&2
    return 1 2>/dev/null || exit 1
fi

# Aktywacja środowiska conda z Pythonem 3.12 (wersja musi pasować do binarki SOFA).
if [ "${CONDA_DEFAULT_ENV:-}" != "$FISHSOFA_CONDA_ENV" ]; then
    eval "$(conda shell.bash hook 2>/dev/null || conda shell.zsh hook 2>/dev/null)"
    conda activate "$FISHSOFA_CONDA_ENV" || { echo "env.sh: brak środowiska conda $FISHSOFA_CONDA_ENV" >&2; return 1 2>/dev/null || exit 1; }
fi

# Katalog z samym libpython (patrz komentarz na górze).
FISHSOFA_PYLIB="$SOFA_ROOT/../fishsofa-pylib"
mkdir -p "$FISHSOFA_PYLIB"
ln -sf "$CONDA_PREFIX/lib/libpython3.12.so.1.0" "$FISHSOFA_PYLIB/libpython3.12.so.1.0"
# BLAS/LAPACK dla CHOLMOD: OpenBLAS z condy (environment.yml) zamiast systemowego.
# CHOLMOD supernodalny liczy gęste bloki w BLAS, więc jego jakość decyduje o czasie kroku.
# Na Archu systemowy libblas.so.3 to wzorcowy (nieoptymalizowany) BLAS z netlib:
# 470 ms/krok, z OpenBLAS 217 ms/krok (coarse, machanie), wynik identyczny (README,
# „Wydajność”). Dowiązujemy tylko te biblioteki, z tego samego powodu co libpython.
for _l in libblas.so.3 liblapack.so.3 libgfortran.so.5 libquadmath.so.0; do
    [ -e "$CONDA_PREFIX/lib/libopenblas.so.0" ] && [ -e "$CONDA_PREFIX/lib/$_l" ] \
        && ln -sf "$CONDA_PREFIX/lib/$_l" "$FISHSOFA_PYLIB/$_l"
done
unset _l
# Jeden wątek BLAS na proces: bloki CHOLMOD są małe (4 wątki = ten sam czas), a przeglądy
# (etap 6) uruchamiają wiele symulacji równolegle – więcej wątków tylko by się przepychało.
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
case ":${LD_LIBRARY_PATH:-}:" in
    *":$FISHSOFA_PYLIB:"*) ;;
    *) export LD_LIBRARY_PATH="$FISHSOFA_PYLIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" ;;
esac

# Moduły Pythona dostarczane przez pluginy SOFA.
for _p in SofaPython3 SoftRobots STLIB; do
    _sp="$SOFA_ROOT/plugins/$_p/lib/python3/site-packages"
    case ":${PYTHONPATH:-}:" in
        *":$_sp:"*) ;;
        *) [ -d "$_sp" ] && export PYTHONPATH="$_sp${PYTHONPATH:+:$PYTHONPATH}" ;;
    esac
done
unset _p _sp

# Wtyczka SofaCHOLMOD (solver "cholmod"), zbudowana osobno dla binarki v26.06 – binarka
# jej nie zawiera (README, „Instalacja”). SOFA szuka wtyczek też w SOFA_PLUGIN_PATH.
: "${FISHSOFA_CHOLMOD_LIB:=$FISHSOFA_HOME/SofaCHOLMOD_v26.06/lib}"
if [ -f "$FISHSOFA_CHOLMOD_LIB/libSofaCHOLMOD.so" ]; then
    export SOFA_PLUGIN_PATH="$FISHSOFA_CHOLMOD_LIB${SOFA_PLUGIN_PATH:+:$SOFA_PLUGIN_PATH}"
else
    echo "env.sh: brak wtyczki SofaCHOLMOD w $FISHSOFA_CHOLMOD_LIB – solver \"cholmod\" nie zadziała" >&2
fi

# Katalog projektu SOFA/ też na PYTHONPATH, żeby `import fishsofa` działało bez instalacji.
_here="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/.." && pwd)"
case ":$PYTHONPATH:" in *":$_here:"*) ;; *) export PYTHONPATH="$_here:$PYTHONPATH" ;; esac
unset _here
