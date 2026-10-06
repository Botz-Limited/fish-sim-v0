#!/usr/bin/env bash
# Odtwarzanie nagrania machania w GUI SOFA, w czasie rzeczywistym (w pętli).
# Użycie:  SOFA/scripts/run_replay.sh [nagranie.npz] [tempo]
#   nagranie: domyślnie recordings/water.npz (tworzy je scripts/record.py)
#   tempo:    1 = czas rzeczywisty (domyślnie), 0.25 = 4× zwolnione
# Animacja startuje sama (-a). Kolor komór = ciśnienie (niebieski niskie, czerwony wysokie).
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh"
export FISHSOFA_MODE=replay
export FISHSOFA_RECORDING="$(realpath "${1:-$HERE/../recordings/water.npz}")"
export FISHSOFA_SPEED="${2:-1}"
[ -f "$FISHSOFA_RECORDING" ] || { echo "brak $FISHSOFA_RECORDING – najpierw: python scripts/record.py" >&2; exit 1; }
exec "$SOFA_ROOT/bin/runSofa" -a -l SofaPython3 "$HERE/../fishsofa/scene.py"
