#!/usr/bin/env bash
# Etap 1: tylko ciało stałe. Liczy rampę ciśnienia w komorze L i R (równolegle)
# i rysuje results/e1_tip_vs_pressure.png.
set -e -u
cd "$(dirname "$0")"
python ../tools/make_geometry.py solid .
export OMP_NUM_THREADS=3
ccx_preCICE -i tail_L > tail_L.log 2>&1 &
ccx_preCICE -i tail_R > tail_R.log 2>&1 &
wait
python ../tools/postprocess.py e1 .
