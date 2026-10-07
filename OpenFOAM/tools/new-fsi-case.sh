#!/usr/bin/env bash
# Creates a complete FSI case (fluid-openfoam + solid-calculix + precice-config.xml).
#
#   new-fsi-case.sh <directory> [options]
#     --u U          inflow speed [m/s]               (default 0.2)
#     --dt DT        time window = step of both solvers (default 0.005)
#     --t-end T      end time [s]                     (default 2)
#     --p0 P         chamber pressure amplitude [Pa], 0 = passive (default 0)
#     --freq F       actuation frequency [Hz]         (default 1)
#     --coupling C   implicit | explicit              (default implicit)
#     --write W      field write interval [s]         (default 0.1)
set -e -u
TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$1"; shift
U=0.2; DT=0.005; TEND=2; P0=0; FREQ=1; COUPLING=implicit; WRITE=0.1
while [ $# -gt 0 ]; do
    case "$1" in
        --u) U="$2" ;;
        --dt) DT="$2" ;;
        --t-end) TEND="$2" ;;
        --p0) P0="$2" ;;
        --freq) FREQ="$2" ;;
        --coupling) COUPLING="$2" ;;
        --write) WRITE="$2" ;;
        *) echo "unknown option $1"; exit 1 ;;
    esac
    shift 2
done

mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"

# --- preCICE ---
sed -e "s/@DT@/$DT/" -e "s/@T_END@/$TEND/" \
    "$TOOLS/precice-base/precice-config-$COUPLING.xml" > "$DEST/precice-config.xml"

# --- fluid ---
"$TOOLS/new-fluid-case.sh" "$DEST/fluid-openfoam" --fsi
P="$DEST/fluid-openfoam/system/caseParams"
sed -i -e "s/^U_IN .*/U_IN            $U;/" -e "s/^DELTA_T .*/DELTA_T         $DT;/" \
       -e "s/^END_TIME .*/END_TIME        $TEND;/" -e "s/^WRITE_INTERVAL .*/WRITE_INTERVAL  $WRITE;/" "$P"
cat > "$DEST/fluid-openfoam/run.sh" <<'EOF'
#!/usr/bin/env bash
# Participant "Fluid": mesh (gmsh) + pimpleFoam with the preCICE adapter.
#   ./run.sh -parallel   – MPI according to system/decomposeParDict (recommended)
set -e -u
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
TOOLS="$d/tools"
. "$TOOLS/log.sh"
exec > >(tee --append "$LOGFILE") 2>&1

"$TOOLS/fluid-mesh.sh"
"$TOOLS/run-openfoam.sh" "$@"

close_log
EOF
cat > "$DEST/fluid-openfoam/clean.sh" <<'EOF'
#!/usr/bin/env sh
set -e -u
cd "$(dirname "$0")"
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
. "$d/tools/cleaning-tools.sh"
clean_openfoam .
EOF

# --- solid ---
S="$DEST/solid-calculix"
mkdir -p "$S"
sed -e "s/@DT@/$DT/" -e "s/@T_END@/$TEND/" "$TOOLS/precice-base/fsi.inp" > "$S/fsi.inp"
cp "$TOOLS/precice-base/config.yml" "$S/"
cat > "$S/run.sh" <<EOF
#!/usr/bin/env bash
# Participant "Solid": tail mesh + actuation + CalculiX with the preCICE adapter.
set -e -u
d="\$(pwd)"; while [ ! -f "\$d/tools/make_geometry.py" ]; do d="\$(dirname "\$d")"; done
TOOLS="\$d/tools"
. "\$TOOLS/log.sh"
exec > >(tee --append "\$LOGFILE") 2>&1

python "\$TOOLS/make_geometry.py" solid .
python "\$TOOLS/make_actuation.py" . --p0 $P0 --freq $FREQ --t-end $TEND
ccx_preCICE -i fsi -precice-participant Solid

close_log
EOF
cat > "$S/clean.sh" <<'EOF'
#!/usr/bin/env sh
set -e -u
cd "$(dirname "$0")"
d="$(pwd)"; while [ ! -f "$d/tools/make_geometry.py" ]; do d="$(dirname "$d")"; done
. "$d/tools/cleaning-tools.sh"
rm -f tail.msh tail_sets.nam material.inc amplitude.inc dload.inc
clean_calculix .
EOF

# --- run both participants at once ---
cat > "$DEST/run.sh" <<'EOF'
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
EOF
cat > "$DEST/clean.sh" <<'EOF'
#!/usr/bin/env sh
cd "$(dirname "$0")"
rm -rf precice-run
./fluid-openfoam/clean.sh
./solid-calculix/clean.sh
EOF
chmod +x "$DEST"/run.sh "$DEST"/clean.sh "$DEST"/*/run.sh "$DEST"/*/clean.sh
cat > "$DEST/case.txt" <<EOF
Case parameters (new-fsi-case.sh):
  U_IN = $U m/s, DT = $DT s, T_END = $TEND s
  P0 = $P0 Pa, f = $FREQ Hz, coupling = $COUPLING
EOF
echo "created $DEST ($COUPLING, U=$U, dt=$DT, T=$TEND, P0=$P0, f=$FREQ)"
