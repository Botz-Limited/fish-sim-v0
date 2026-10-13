#!/usr/bin/env bash
# Runs both solvers at the same time (fluid on MPI, solid on OpenMP).
# If one participant dies (e.g. divergence), the other would wait forever for
# data on the socket – so after 15 s we stop it (the whole process group).
cd "$(dirname "$0")"
rm -rf precice-run
set -m   # each participant in its own process group (easy to kill together with mpirun)
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
echo "fluid exit=$EF, solid exit=$ES (logs: fluid-openfoam/fluid-openfoam.log, solid-calculix/solid-calculix.log)"
exit $(( EF | ES ))
