"""Performance settings for PyElastica.

Measurements on this machine (Ryzen AI 5 PRO 340, 6 cores / 12 threads, 100-element rod,
PositionVerlet, cantilever + gravity + AnalyticalLinearDamper):
  - first run (JIT compilation of ~90 numba kernels): ~11.5 s,
    subsequent runs (numba cache on disk): ~0.13 s,
  - one step ~27 µs (50 elements: ~20 µs) -> ~38k steps/s per process.
    The step time is mostly Python overhead of the kernel calls, not arithmetic,
    so threads (BLAS/numba parallel) give nothing for a single rod.
  - scaling with processes: 1 -> 38k, 6 -> ~191k, 12 -> ~207k steps/s in total.
    Optimum = number of physical cores (SMT adds only +8%).

Conclusions for the demo code:
  1. Every simulation single-threaded (BLAS/OpenMP/numba = 1 thread), so that parallel
     processes do not fight over cores.
  2. Parameter sweeps (stage 5) and independent scenarios -> ProcessPoolExecutor
     with N_WORKERS processes.
  3. Custom forces (water.py, buoyancy.py, actuation.py): loops inside @njit(cache=True)
     functions, called once per step; no Python loops over elements.
  4. Callbacks save data rarely (step_skip), because every call costs time.
  5. Manual integration loop (stepper.step), without the tqdm progress bar of ea.integrate.
"""

import os

# Number of physical cores (os.cpu_count() returns SMT threads).
N_PHYSICAL_CORES = max(1, (os.cpu_count() or 2) // 2)
N_WORKERS = int(os.environ.get("FISHROD_WORKERS", N_PHYSICAL_CORES))

_SINGLE_THREAD = {
    "OPENBLAS_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMBA_NUM_THREADS": "1",
}
for _k, _v in _SINGLE_THREAD.items():
    os.environ.setdefault(_k, _v)

# Numba compiles for the detected CPU on its own (here Zen 5 with AVX-512). Do NOT set
# NUMBA_CPU_NAME="host": llvmlite 0.50 does not know this name and silently compiles
# for a generic CPU. The kernel cache is kept in the project directory.
os.environ.setdefault(
    "NUMBA_CACHE_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".numba_cache"),
)
