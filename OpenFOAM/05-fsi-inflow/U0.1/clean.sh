#!/usr/bin/env sh
cd "$(dirname "$0")"
rm -rf precice-run
./fluid-openfoam/clean.sh
./solid-calculix/clean.sh
