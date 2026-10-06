#!/usr/bin/env bash
# Instalacja pakietów systemowych (wymaga sudo).
# OpenModelica 1.27.1 (kanał "release") z oficjalnego repozytorium apt + narzędzia.
set -euo pipefail

CODENAME="$(. /etc/os-release && echo "$VERSION_CODENAME")"

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Klucz i repozytorium OpenModelica
curl -fsSL https://build.openmodelica.org/apt/openmodelica.asc \
  | sudo gpg --dearmor --yes -o /usr/share/keyrings/openmodelica-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/openmodelica-keyring.gpg] https://build.openmodelica.org/apt ${CODENAME} release" \
  | sudo tee /etc/apt/sources.list.d/openmodelica.list >/dev/null

sudo apt-get update
# omc ciągnie: clang, cmake, build-essential, lapack; omedit = GUI; omsimulator = FMI
sudo apt-get install -y --install-recommends openmodelica omedit omsimulator \
  git ccache python3-venv python3-pip python3-dev

echo
omc --version
