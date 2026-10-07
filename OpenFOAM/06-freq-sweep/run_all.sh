#!/usr/bin/env bash
# Etap 6: przegląd częstotliwości (woda stojąca, P0 = 15 kPa). Punkt 1 Hz = etap 4.
cd "$(dirname "$0")"
for c in f0.5 f1.5 f2; do
    (cd $c && ./clean.sh > /dev/null 2>&1; s=$(date +%s); ./run.sh; echo "$c: $(( $(date +%s)-s )) s")
done
python ../tools/postprocess.py e6 .
