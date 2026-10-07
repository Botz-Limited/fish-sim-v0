#!/usr/bin/env bash
# Two queues in parallel (12 hardware threads, each FSI run uses 6):
#   A: stage 5            B: stage 4 (8 cycles) -> stage 6
# At the end: refresh plots and run check_results. Logs: logs/queue_A.log, queue_B.log
cd "$(dirname "$0")"
source ./env.sh > /dev/null 2>&1
mkdir -p logs
( echo "=== A start $(date +%T)"; ./05-fsi-inflow/run_all.sh; echo "=== A end $(date +%T)" ) > logs/queue_A.log 2>&1 &
( echo "=== B start $(date +%T)"; ./04-fsi-actuated/run_all.sh; ./06-freq-sweep/run_all.sh; echo "=== B end $(date +%T)" ) > logs/queue_B.log 2>&1 &
wait
python tools/postprocess.py e4 04-fsi-actuated > logs/final.log 2>&1
python tools/postprocess.py e5 05-fsi-inflow >> logs/final.log 2>&1
python tools/postprocess.py e6 06-freq-sweep >> logs/final.log 2>&1
python tools/check_results.py >> logs/final.log 2>&1
echo "=== all done $(date +%T)" >> logs/final.log
