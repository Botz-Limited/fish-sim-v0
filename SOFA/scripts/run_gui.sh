#!/usr/bin/env bash
# GUI SOFA z ogonem.  Użycie:  SOFA/scripts/run_gui.sh [coarse|medium|fine|test] [flap|sag]
# flap (domyślnie): obie komory + pompa, ogon macha; sag: ugięcie pod ciężarem (etap 1).
# Po otwarciu okna naciśnij Animate.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh"
export FISHSOFA_LEVEL="${1:-coarse}"
export FISHSOFA_MODE="${2:-flap}"
exec "$SOFA_ROOT/bin/runSofa" -l SofaPython3 "$HERE/../fishsofa/scene.py"
