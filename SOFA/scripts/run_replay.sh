#!/usr/bin/env bash
# Replay of a flapping recording in the SOFA GUI, in real time (looped).
# Usage:  SOFA/scripts/run_replay.sh [recording.npz] [speed]
#   recording: default recordings/water.npz (created by scripts/record.py)
#   speed:     1 = real time (default), 0.25 = 4× slower
# The animation starts by itself (-a). Chamber color = pressure (blue low, red high).
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/env.sh"
export FISHSOFA_MODE=replay
export FISHSOFA_RECORDING="$(realpath "${1:-$HERE/../recordings/water.npz}")"
export FISHSOFA_SPEED="${2:-1}"
[ -f "$FISHSOFA_RECORDING" ] || { echo "$FISHSOFA_RECORDING not found – first run: python scripts/record.py" >&2; exit 1; }
exec "$SOFA_ROOT/bin/runSofa" -a -l SofaPython3 "$HERE/../fishsofa/scene.py"
