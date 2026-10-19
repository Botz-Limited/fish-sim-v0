#!/usr/bin/env bash
# Run independent cases of a sweep script as separate Julia processes.
#
#   scripts/run_parallel.sh [-j JOBS] [-t THREADS] SCRIPT CASE...
#
# Starts at most JOBS processes at a time (default 2), each `julia --project=. -t THREADS`
# (default 2) running `SCRIPT run CASE`; keep JOBS × THREADS ≤ the cores you may use.
# Logs: results/logs/<script>_<case>.log. Afterwards it runs `SCRIPT report` once.
# Run from WaterLily/. Exit status ≠ 0 if any case failed.
set -u
JOBS=2; THREADS=2
while getopts "j:t:" o; do
  case $o in j) JOBS=$OPTARG ;; t) THREADS=$OPTARG ;; *) exit 2 ;; esac
done
shift $((OPTIND - 1))
[ $# -ge 2 ] || { echo "usage: $0 [-j JOBS] [-t THREADS] SCRIPT CASE..." >&2; exit 2; }
SCRIPT=$1; shift
JULIA=${JULIA:-$HOME/.juliaup/bin/julia}
NAME=$(basename "$SCRIPT" .jl)
mkdir -p results/logs
export JULIA THREADS SCRIPT NAME
t0=$(date +%s)
printf '%s\n' "$@" | xargs -P "$JOBS" -I{} sh -c '
  log=results/logs/${NAME}_{}.log
  s=$(date +%s)
  if "$JULIA" --project=. -t "$THREADS" "$SCRIPT" run {} > "$log" 2>&1; then st=ok; else st=FAILED; fi
  echo "[run_parallel] {}: $st in $(( $(date +%s) - s )) s  (log $log)"
  [ "$st" = ok ]'
rc=$?
echo "[run_parallel] all cases finished in $(( $(date +%s) - t0 )) s (rc=$rc); report:"
"$JULIA" --project=. "$SCRIPT" report
exit $rc
