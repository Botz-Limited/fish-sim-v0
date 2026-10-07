#!/usr/bin/env bash
# Etap 4: napęd ciśnieniem (sinus, f = 1 Hz, P0 = 15 kPa), woda stojąca.
# "dry" – ten sam ogon bez wody (sam CalculiX), "water" – FSI.
cd "$(dirname "$0")"
(s=$(date +%s); ./dry/run.sh; echo "dry: $(( $(date +%s)-s )) s")
(cd water && ./clean.sh > /dev/null 2>&1; s=$(date +%s); ./run.sh; echo "water: $(( $(date +%s)-s )) s")
python ../tools/postprocess.py e4 .
