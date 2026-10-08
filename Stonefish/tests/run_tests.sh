#!/usr/bin/env bash
# Testy demo (SPEC §9). Uruchomienie z katalogu Stonefish/:
#     tests/run_tests.sh [katalog_build]        (domyślnie build/)
# 1) testy jednostkowe (hydraulika, TailDriver, siła nośna, regulatory),
# 2) każdy scenariusz ładuje się bez błędów parsera,
# 3) krótkie przebiegi aplikacji konsolowej + asercje na logach (tests/check_logs.py).
# Logi idą do katalogu tymczasowego – results/ zostaje nietknięte.
set -u
cd "$(dirname "$0")/.."
BUILD="${1:-build}"
CONSOLE="$BUILD/fish_console"
PY="${PYTHON:-.venv/bin/python}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail=0

echo "== 1. Testy jednostkowe"
"$BUILD/unit_tests" || fail=1

echo "== 2. Scenariusze ładują się bez błędów parsera"
for cfg in config/s*.json config/t_*.json; do
    out="$("$CONSOLE" "$cfg" --duration 0.05 --out "$TMP/load.csv" 2>&1)"
    rc=$?
    if [ $rc -ne 0 ] || grep -qE '\[ERROR\]|BŁĄD' <<<"$out"; then
        echo "  [FAIL] $cfg"; grep -E '\[ERROR\]|BŁĄD' <<<"$out" | head -5; fail=1
    else
        echo "  [ OK ] $cfg"
    fi
done

echo "== 3. Przebiegi konsolowe"
run() { # nazwa, konfiguracja, opcje...
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

echo "== 4. Asercje na logach"
"$PY" tests/check_logs.py "$TMP" || fail=1

if [ $fail -eq 0 ]; then echo "== WSZYSTKIE TESTY PRZESZŁY"; else echo "== SĄ BŁĘDY"; fi
exit $fail
