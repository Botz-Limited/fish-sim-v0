#!/usr/bin/env bash
# Instalacja bez sudo: środowisko Python (.venv) + Modelica Standard Library 4.1.0.
# Uruchom po setup/install_system.sh, z katalogu głównego repo.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

tmp="$(mktemp -d)"
cat > "$tmp/msl.mos" <<'EOS'
updatePackageIndex(); getErrorString();
installPackage(Modelica, "4.1.0+maint.om", exactMatch=true); getErrorString();
loadModel(Modelica, {"4.1.0"}); getErrorString();
getVersion(Modelica);
EOS
omc "$tmp/msl.mos"
rm -rf "$tmp"
