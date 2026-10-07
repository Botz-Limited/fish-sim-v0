#!/usr/bin/env bash
# Stage 4: pressure actuation (sine, f = 1 Hz, P0 = 15 kPa), still water.
# "dry" – the same tail without water (CalculiX alone), "water" – FSI.
cd "$(dirname "$0")"
(s=$(date +%s); ./dry/run.sh; echo "dry: $(( $(date +%s)-s )) s")
(cd water && ./clean.sh > /dev/null 2>&1; s=$(date +%s); ./run.sh; echo "water: $(( $(date +%s)-s )) s")
python ../tools/postprocess.py e4 .
