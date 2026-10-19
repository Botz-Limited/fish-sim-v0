#!/usr/bin/env bash
# Build gpu/rocm-shim/: a fake ROCM_PATH whose lib/ holds the unversioned library names that
# AMDGPU.jl looks for. Fedora ships only libamdhip64.so.7 (the unversioned .so comes with
# rocm-hip-devel). Run once per machine, then: ROCM_PATH=$PWD/gpu/rocm-shim julia --project=gpu ...
set -euo pipefail

G="$(cd "$(dirname "$0")" && pwd)/rocm-shim"
LIB=${ROCM_LIBDIR:-/usr/lib64}

link() {  # link <target> <name>
    [ -e "$1" ] || { echo "missing: $1 (install the Fedora rocm-hip / rocm-runtime packages)" >&2; exit 1; }
    ln -sf "$1" "$2"
}

mkdir -p "$G/lib/llvm/bin"
link "$(ls "$LIB"/libamdhip64.so.* | sort -V | head -1)" "$G/lib/libamdhip64.so"
link "$LIB/libhsa-runtime64.so.1"                     "$G/lib/libhsa-runtime64.so.1"
# AMDGPU.jl searches <libdir>/llvm/bin for ld.lld; optional (falls back to its own JLL linker)
if [ -e "$LIB/rocm/llvm/bin/ld.lld" ]; then
    ln -sf "$LIB/rocm/llvm/bin/ld.lld" "$G/lib/llvm/bin/ld.lld"
fi

echo "ROCm shim ready: $G"
echo "check: ROCM_PATH=$G julia --project=gpu -e 'using AMDGPU; @show AMDGPU.functional()'"
