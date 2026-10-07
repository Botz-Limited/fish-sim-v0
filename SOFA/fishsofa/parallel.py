"""Many independent simulations at once – one per process.

A single SOFA simulation uses practically one core: FEM matrix assembly is sequential,
and CHOLMOD's factorization blocks are too small for BLAS to gain from threads (README,
"Performance"). Each time step depends on the previous one, so a single simulation cannot
be split. Sweep points (stages 5–6), however, are independent: each runs in its own
process, several at a time.

Processes start with the "spawn" method (clean interpreter), not "fork": SOFA keeps global
state (component factory, loaded plugins) that is not safe to copy via fork.
One process ≈ 0.5 GB RAM on the coarse mesh.
"""
import multiprocessing as mp
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed


def default_workers(n_jobs: int) -> int:
    """Number of processes: as many as jobs, but 2 cores are left for the system (GUI, IO).
    FISHSOFA_WORKERS overrides the limit (e.g. when something else is also running)."""
    limit = int(os.environ.get("FISHSOFA_WORKERS", 0)) or (os.cpu_count() or 2) - 2
    return max(1, min(n_jobs, limit))


def run_all(fn, jobs: dict, workers: int | None = None, label: str = "") -> dict:
    """Calls fn(**kwargs) for each jobs[key] = kwargs in separate processes.

    Returns {key: result}. fn must be a module-level function (pickle).
    Progress: one line per finished job.
    """
    workers = workers or default_workers(len(jobs))
    out, t0 = {}, time.perf_counter()
    print(f"{label}{len(jobs)} simulations, {workers} at a time", flush=True)
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(fn, **kw): key for key, kw in jobs.items()}
        for i, fut in enumerate(as_completed(futs), 1):
            key = futs[fut]
            out[key] = fut.result()
            print(f"  [{i}/{len(jobs)}] {key} done after {(time.perf_counter() - t0) / 60:.1f} min", flush=True)
    return out
