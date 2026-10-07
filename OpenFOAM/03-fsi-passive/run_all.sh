#!/usr/bin/env bash
# Etap 3: ogon pasywny w strumieniu. Najpierw sprzężenie jawne (ma się
# rozbiec – efekt masy dodanej), potem niejawne z IQN-ILS.
cd "$(dirname "$0")"
for c in explicit implicit; do
    (cd $c && ./clean.sh > /dev/null 2>&1; s=$(date +%s); ./run.sh; echo "$c: $(( $(date +%s)-s )) s")
done
python ../tools/postprocess.py e3 .
