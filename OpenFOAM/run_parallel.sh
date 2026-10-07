#!/usr/bin/env bash
# Dwie kolejki równolegle (12 wątków sprzętowych, każda FSI zajmuje 6):
#   A: etap 5            B: etap 4 (8 okresów) -> etap 6
# Na końcu odświeżenie wykresów i check_results. Logi: logs/queue_A.log, queue_B.log
cd "$(dirname "$0")"
source ./env.sh > /dev/null 2>&1
mkdir -p logs
( echo "=== A start $(date +%T)"; ./05-fsi-inflow/run_all.sh; echo "=== A koniec $(date +%T)" ) > logs/queue_A.log 2>&1 &
( echo "=== B start $(date +%T)"; ./04-fsi-actuated/run_all.sh; ./06-freq-sweep/run_all.sh; echo "=== B koniec $(date +%T)" ) > logs/queue_B.log 2>&1 &
wait
python tools/postprocess.py e4 04-fsi-actuated > logs/final.log 2>&1
python tools/postprocess.py e5 05-fsi-inflow >> logs/final.log 2>&1
python tools/postprocess.py e6 06-freq-sweep >> logs/final.log 2>&1
python tools/check_results.py >> logs/final.log 2>&1
echo "=== wszystko gotowe $(date +%T)" >> logs/final.log
