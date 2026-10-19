# WaterLily.jl CPU vs AMD GPU (ROCm) benchmark.
#
# Usage (from the WaterLily/ directory):
#   CPU:  julia --project=gpu -t 4 gpu/benchmark.jl cpu
#   GPU:  ROCM_PATH=$PWD/gpu/rocm-shim julia --project=gpu -t 4 gpu/benchmark.jl gpu
#
# Optional 2nd argument: number of timed steps (default 50).
# Cases: 2D circle 1024x512 and 3D sphere 256x128x128, Float32, Re=250.
# Each case is timed twice: fixed body (remeasure=false) and moving-body cost
# (remeasure=true, the SDF/body is re-measured every step as for a swimming fish).

using WaterLily, StaticArrays, Printf

const BACKEND = length(ARGS) >= 1 ? lowercase(ARGS[1]) : "cpu"
const NSTEPS = length(ARGS) >= 2 ? parse(Int, ARGS[2]) : 50

if BACKEND == "gpu"
    using AMDGPU
    AMDGPU.functional() || error("AMDGPU not functional (did you set ROCM_PATH=gpu/rocm-shim?)")
    const MEM = ROCArray
    sync() = AMDGPU.synchronize()
    devname = string(AMDGPU.device())
else
    const MEM = Array
    sync() = nothing
    devname = "CPU, $(Threads.nthreads()) Julia threads"
end

function circle(n, m; Re=250, U=1, mem=Array, T=Float32)
    R, c = m / 8, m / 2 - 1
    sdf(x, t) = √sum(abs2, x .- c) - R
    Simulation((n, m), (U, 0), R; ν=U * R / Re, body=AutoBody(sdf), mem, T)
end

function sphere(n, m; Re=250, U=1, mem=Array, T=Float32)
    R, c = m / 8, m / 2 - 1
    sdf(x, t) = √sum(abs2, x .- c) - R
    Simulation((n, m, m), (U, 0, 0), R; ν=U * R / Re, body=AutoBody(sdf), mem, T)
end

function bench(make, label; nwarm=10, nsteps=NSTEPS)
    sim = make()
    ncells = prod(size(sim.flow.p) .- 2)
    results = Dict{Bool,Float64}()
    for remeasure in (false, true)
        for _ in 1:nwarm
            sim_step!(sim; remeasure)
        end
        sync()
        GC.gc()
        t0 = time_ns()
        for _ in 1:nsteps
            sim_step!(sim; remeasure)
        end
        sync()
        dt = (time_ns() - t0) / 1e9 / nsteps
        results[remeasure] = dt
        @printf("%-22s remeasure=%-5s %9.2f ms/step  %7.1f Mcell-steps/s  (Δt=%.3f, last pois iters=%d)\n",
                label, remeasure, 1e3dt, ncells / dt / 1e6, sim.flow.Δt[end], sim.pois.n[end])
        flush(stdout)
    end
    return results
end

println("WaterLily ", pkgversion(WaterLily), " | Julia ", VERSION, " | backend: ", devname)
bench(() -> circle(1024, 512; mem=MEM), "2D circle 1024x512")
bench(() -> sphere(256, 128; mem=MEM), "3D sphere 256x128x128")
