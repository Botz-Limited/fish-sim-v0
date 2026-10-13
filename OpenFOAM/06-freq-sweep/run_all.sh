#!/usr/bin/env bash
# Stage 6: frequency sweep (still water, P0 = 15 kPa). The 1.5 Hz point = stage 4.
# Valve range 1.5..2.5 Hz (make_actuation.py): 1.5 (stage 4), 1.75, 2, 2.5 Hz.
cd "$(dirname "$0")"
for c in f1.75 f2 f2.5; do
    (cd $c && ./clean.sh > /dev/null 2>&1; s=$(date +%s); ./run.sh; echo "$c: $(( $(date +%s)-s )) s")
done
python ../tools/postprocess.py e6 .
