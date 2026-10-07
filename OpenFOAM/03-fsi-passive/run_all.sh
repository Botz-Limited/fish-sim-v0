#!/usr/bin/env bash
# Stage 3: passive tail in a stream. First explicit coupling (expected to
# diverge – added-mass effect), then implicit with IQN-ILS.
cd "$(dirname "$0")"
for c in explicit implicit; do
    (cd $c && ./clean.sh > /dev/null 2>&1; s=$(date +%s); ./run.sh; echo "$c: $(( $(date +%s)-s )) s")
done
python ../tools/postprocess.py e3 .
