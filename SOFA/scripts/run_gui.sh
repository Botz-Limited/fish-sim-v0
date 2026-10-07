#!/usr/bin/env bash
# SOFA GUI with the tail.  Usage:  SOFA/scripts/run_gui.sh [coarse|medium|fine|test] [flap|sag]
# flap (default): both chambers + pump, the tail flaps; sag: sag under its own weight (stage 1).
# After the window opens, press Animate.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh"
export FISHSOFA_LEVEL="${1:-coarse}"
export FISHSOFA_MODE="${2:-flap}"
exec "$SOFA_ROOT/bin/runSofa" -l SofaPython3 "$HERE/../fishsofa/scene.py"
