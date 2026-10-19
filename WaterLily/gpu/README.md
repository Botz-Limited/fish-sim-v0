# WaterLily.jl on the AMD GPU (ROCm) — setup and benchmark

**Result: it works.** WaterLily 1.9.2 runs on the Radeon RX 7700 XT (Navi 32, gfx1101)
through AMDGPU.jl, using Fedora's ROCm 7.1.1 packages. No sudo was needed. The one
workaround is a small `rocm-shim/` directory of symlinks, passed in through `ROCM_PATH`.

This is a separate Julia environment (`WaterLily/gpu/Project.toml`). It is independent of
the top-level `WaterLily/Project.toml`.

## Versions (tested 2026-10-19)

| Component | Version |
|---|---|
| OS | Fedora 44, kernel 7.2.10 |
| GPU | AMD Radeon RX 7700 XT, gfx1101, 12 GiB (an iGPU gfx1036 also appears as device 2; device 1 is the default) |
| Julia | 1.13.2 (juliaup `release`); no older Julia was needed |
| WaterLily.jl | 1.9.2 |
| AMDGPU.jl | 2.8.0 (2.9.1 exists, but the resolver held it back) |
| KernelAbstractions.jl | 0.9.45 |
| GPUCompiler.jl / LLVM.jl | 2.6.0 / 9.13.2 |
| Device libraries | ROCmDeviceLibs_jll 7.0.2 (Julia artifact) |
| HIP runtime | Fedora `rocm-hip-7.1.1-3.fc44` (HIP 7.1.52802), `rocm-runtime-7.1.1-6.fc44` |
| Linker | `/usr/lib64/rocm/llvm/bin/ld.lld` from Fedora `rocm-llvm-20-13.rocm7.1.1.fc44` |

## What fails out of the box, and why

Without extra settings, `AMDGPU.functional()` returns `false`. The first GPU call then fails
with `could not load symbol "hipDeviceGet"`.

The cause is how AMDGPU.jl looks for ROCm (`src/discovery/utils.jl`). It checks
`$ROCM_PATH`, then `/opt/rocm`, then `/usr`, and accepts a directory only if it contains
the **unversioned** file `libamdhip64.so`. Fedora's runtime package `rocm-hip` installs only
`/usr/lib64/libamdhip64.so.7`. The unversioned symlink comes with `rocm-hip-devel`, which is
not installed here. So AMDGPU.jl finds no HIP library at all.

## Setup (no sudo)

Run from `WaterLily/` (the parent directory of `gpu/`):

```bash
# 1. Julia environment (first run takes a few minutes to precompile)
julia --project=gpu -e 'using Pkg; Pkg.add([
    PackageSpec(name="WaterLily", version="1.9.2"), "AMDGPU", "StaticArrays"])'
# (or: julia --project=gpu -e 'using Pkg; Pkg.instantiate()' to use the committed Manifest)

# 2. ROCm shim: a fake ROCM_PATH whose lib/ holds the unversioned names (git-ignored,
#    rebuilt per machine by the script; it only creates symlinks into /usr/lib64)
gpu/setup_rocm_shim.sh
G=$PWD/gpu/rocm-shim

# 3. Check that it works
ROCM_PATH=$G julia --project=gpu -e 'using AMDGPU; AMDGPU.versioninfo(); @show AMDGPU.functional()'
```

`ld.lld` has to be under `lib/llvm/bin`, because AMDGPU.jl searches `<libdir>/llvm/bin`.
If the shim cannot find it, AMDGPU.jl falls back to its own `AMDGPU_LLVM_Backend_jll`
linker. The device bitcode always comes from the `ROCmDeviceLibs_jll` artifact. The Fedora
copy at `/usr/lib64/rocm/llvm/lib/clang/20/lib/amdgcn/bitcode` is not used.

The user must be in the `render` and `video` groups to access `/dev/kfd`. On this machine
they already are.

At load time AMDGPU.jl warns that rocBLAS, rocSOLVER, rocSPARSE, rocRAND, rocFFT and MIOpen
are unavailable. WaterLily does not use any of them, so the warnings can be ignored.

### Alternative with sudo (would remove the need for the shim; not tested)

```bash
sudo dnf install rocm-hip-devel
```

This provides `/usr/lib64/libamdhip64.so`, so AMDGPU.jl's built-in check of `/usr` should
succeed without setting `ROCM_PATH`.

## Using it in WaterLily

```julia
using AMDGPU, WaterLily        # loading AMDGPU activates WaterLilyAMDGPUExt
sim = Simulation(dims, uBC, L; body, ν, T=Float32, mem=ROCArray)
sim_step!(sim, t_end)
Array(sim.flow.p)              # copy fields back to the host for plotting or I/O
```

Use `Float32`. Consumer RDNA3 cards have very low FP64 throughput.

## Benchmark

`gpu/benchmark.jl` runs the standard WaterLily flow past a circle (2D) and past a sphere
(3D). Settings: Re = 250, radius = m/8, Float32, `AutoBody`. Each case gets 10 warm-up
steps and then 50 timed steps. Both modes are timed:

- `remeasure=false`: the body is fixed.
- `remeasure=true`: the body is re-measured every step. This is the cost a moving body,
  such as the fish, would pay.

```bash
julia --project=gpu -t 4 gpu/benchmark.jl cpu                              # CPU, 4 threads
ROCM_PATH=$PWD/gpu/rocm-shim julia --project=gpu -t 4 gpu/benchmark.jl gpu  # GPU
```

CPU: AMD Ryzen 5 7600 (6C/12T), limited to 4 Julia threads, with other jobs running on the
machine (load average about 4). Times are wall-clock per `sim_step!`.

| Case | Cells | Mode | CPU (4 threads) ms/step | GPU RX 7700 XT ms/step | Speedup |
|---|---|---|---:|---:|---:|
| 2D circle 1024×512 | 0.52 M | fixed body | 8.87 | 6.27 | 1.4× |
| 2D circle 1024×512 | 0.52 M | remeasure | 10.38 | 5.54 | 1.9× |
| 3D sphere 256×128×128 | 4.19 M | fixed body | 147.1 | 26.9 | **5.5×** |
| 3D sphere 256×128×128 | 4.19 M | remeasure | 174.1 | 31.0 | **5.6×** |

Throughput: the GPU reaches about 135–155 Mcell-steps/s in 3D. The 4-thread CPU reaches
about 24–28 Mcell-steps/s.

## Caveats

- **2D is too small to fill the GPU.** At about 0.5 M cells, the time per step is mostly
  kernel launch and synchronisation overhead. That is why the 2D speedup is only 1.4–1.9×.
  The GPU pays off for 3D or for much larger 2D grids.
- **The timed steps are early in the flow.** They follow the impulsive start, and the
  Poisson solver converged in about 1 iteration per step. Once the wake develops, the solver
  needs more iterations, so each step costs more on both backends. The relative speedup
  should stay similar or grow for the GPU, but this was not measured.
- **CPU numbers use 4 of 12 threads on a shared machine.** Using all cores would narrow the
  gap, perhaps to roughly 2.5–3× in 3D (an estimate, not measured).
- **The first GPU call compiles kernels.** This takes tens of seconds and is excluded from
  the timings.
- **Fields must be copied back for output.** Plotting and saving need data on the host:
  call `Array(...)` on the fields, or use the WriteVTK/JLD2 extensions, which handle it.
- **The shim depends on the Fedora package layout.** If an update renames `libamdhip64.so.7`
  (for example to `.so.8`), the symlinks must be recreated.

## Stage 7: 3D fish on the GPU

Script: `scripts/stage7_3d.jl` (helper module `scripts/lib_3d.jl`). Run from `WaterLily/`:

```bash
# 3D CFD on the GPU (gpu env). Default N=160; the reported run used N=224.
N=224 ROCM_PATH=$PWD/gpu/rocm-shim julia --project=gpu -t 1 scripts/stage7_3d.jl run
# Caudal fin variant (reported run used N=224, 66.5 min)
N=224 FIN=1 ROCM_PATH=$PWD/gpu/rocm-shim julia --project=gpu -t 1 scripts/stage7_3d.jl run
# 2D reference with the same valve and inflow (FishLily env, CPU, takes about 2 min)
julia --project=. -t 1 scripts/stage7_3d.jl ref2d
# Figures and results/stage7_summary.csv (FishLily env, uses Plots)
julia --project=. scripts/stage7_3d.jl plot
```

Environment variables: `N` (cells per body length), `T_END` (4.0 s), `F` (2.0 Hz),
`U_IN` (0.2 m/s), `FIN` (0/1), `T_AVG` (2.0 s, start of the averaging window),
`BACKEND` (`gpu`/`cpu`), `CASE`, `MAX_STEPS` (for quick tests).

How FishLily is loaded: it is **not** `Pkg.develop`ed into this env. FishLily's
dependencies (Plots, DataFrames, CSV, JLD2, ParametricBodies) would make the GPU
environment much heavier. `lib_3d.jl` therefore `include`s only `src/params.jl`, `units.jl`,
`valve.jl`, `geometry.jl` and `progress.jl` into a module `Fish3D`. These files need only
WaterLily, StaticArrays and Printf. The same file also loads in the FishLily env, which
the plot mode uses.

GPU safety: the body is an `AutoBody` built from two isbits callable structs. The valve
runs on the host. Before each step, `sim.body` is replaced by a new body whose map holds
the scalars `(t0, θ0, dθ/dt)`, a linear θ track over the step as in 2D. The body type does
not change, so no kernel is recompiled. A `WaterLily.bbox` method limits `measure!` and the
force integrals to a box around the fish.

Memory and speed on the RX 7700 XT for the 3D fish (moving body, forces every step):

| N (cells/L) | grid | cells | GPU memory | ms/step (first 80 steps) |
|---|---|---|---|---|
| 64  | 256×96×64   | 1.6 M  | 0.7 GiB | ≈ 65–150 (latency-bound) |
| 160 | 640×240×160 | 24.6 M | 3.4 GiB | 254 |
| 192 | 768×288×192 | 42.5 M | 5.6 GiB | 427 |
| 224 | 896×336×224 | 67.4 M | 8.5 GiB | 639 |

The fish runs at about 100 Mcell-steps/s. N=224 is the largest grid that fits in 12 GiB
with some headroom. Full run N=224, t = 0…4 s: 3248 steps, **36.3 min wall, 665 ms/step**
Caudal-fin variant (FIN=1, N=224): 5541 steps, 66.5 min, 716 ms/step. Δt is smaller because the
fin tip is faster (`results/stage7_summary.md`).
