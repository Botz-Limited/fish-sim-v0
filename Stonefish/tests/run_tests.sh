#!/usr/bin/env bash
# Demo tests (SPEC §9). Run from the Stonefish/ directory:
#     tests/run_tests.sh [build_dir]        (default build/)
# 1) unit tests (hydraulics, TailDriver, lift, controllers),
# 2) every scenario loads without parser errors,
# 3) short console app runs + assertions on the logs (tests/check_logs.py).
# Logs go to a temporary directory – results/ stays untouched.
set -u
cd "$(dirname "$0")/.."
BUILD="${1:-build}"
CONSOLE="$BUILD/fish_console"
PY="${PYTHON:-.venv/bin/python}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail=0

echo "== 1. Unit tests"
"$BUILD/unit_tests" || fail=1

echo "== 2. Scenarios load without parser errors"
for cfg in config/s*.json config/t_*.json; do
    out="$("$CONSOLE" "$cfg" --duration 0.05 --out "$TMP/load.csv" 2>&1)"
    rc=$?
    if [ $rc -ne 0 ] || grep -qE '\[ERROR\]|^ERROR' <<<"$out"; then
        echo "  [FAIL] $cfg"; grep -E '\[ERROR\]|^ERROR' <<<"$out" | head -5; fail=1
    else
        echo "  [ OK ] $cfg"
    fi
done

echo "== 3. Console runs"
run() { # name, config, options...
    local name=$1 cfg=$2; shift 2
    if "$CONSOLE" "$cfg" --out "$TMP/$name.csv" "$@" >"$TMP/$name.txt" 2>&1; then
        echo "  [ OK ] $name: $(tail -1 "$TMP/$name.txt" | cut -c1-60)"
    else
        echo "  [FAIL] $name"; tail -5 "$TMP/$name.txt"; fail=1
    fi
}
run s1_hover config/s1_hover.json &
run s1_righting config/s1_righting.json &
run s2_swim config/s2_swim.json &
run s2_swim_locked config/s2_swim_locked.json &
run s4_depth config/s4_depth.json &
run t_internal config/t_internal.json &
wait

echo "== 4. Log assertions"
"$PY" tests/check_logs.py "$TMP" || fail=1

if [ $fail -eq 0 ]; then echo "== ALL TESTS PASSED"; else echo "== THERE ARE FAILURES"; fi
exit $fail
