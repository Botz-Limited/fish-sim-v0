#!/usr/bin/env bash
# Etap 5: napęd (f = 1 Hz, P0 = 15 kPa) + napływ U = 0.05 / 0.1 / 0.2 m/s.
cd "$(dirname "$0")"
for c in U0.05 U0.1 U0.2; do
    (cd $c && ./clean.sh > /dev/null 2>&1; s=$(date +%s); ./run.sh; echo "$c: $(( $(date +%s)-s )) s")
done
python ../tools/postprocess.py e5 .
