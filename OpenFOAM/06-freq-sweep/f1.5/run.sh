#!/usr/bin/env bash
# Uruchamia oba solvery równocześnie (płyn na MPI, ciało stałe na OpenMP).
# Jeśli jeden uczestnik padnie (np. rozbieżność), drugi czekałby w nieskończoność
# na dane przez gniazdo – dlatego po 15 s zatrzymujemy go (cała grupa procesów).
cd "$(dirname "$0")"
rm -rf precice-run
set -m   # każdy uczestnik we własnej grupie procesów (łatwo zabić z mpirun)
(cd fluid-openfoam && ./run.sh -parallel > /dev/null 2>&1) & PF=$!
(cd solid-calculix && ./run.sh > /dev/null 2>&1) & PS=$!
wait -n $PF $PS
for i in $(seq 15); do
    { kill -0 $PF 2>/dev/null || kill -0 $PS 2>/dev/null; } || break
    sleep 1
done
kill -TERM -$PF -$PS 2>/dev/null
wait $PF; EF=$?
wait $PS; ES=$?
echo "fluid exit=$EF, solid exit=$ES (logi: fluid-openfoam/fluid-openfoam.log, solid-calculix/solid-calculix.log)"
exit $(( EF | ES ))
