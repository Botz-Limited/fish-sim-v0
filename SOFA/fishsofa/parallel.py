"""Wiele niezależnych symulacji naraz – po jednej na proces.

Jedna symulacja SOFA używa praktycznie jednego rdzenia: składanie macierzy FEM jest
sekwencyjne, a bloki rozkładu CHOLMOD są za małe, żeby BLAS zyskał na wątkach (README,
„Wydajność”). Kolejne kroki czasu zależą od poprzednich, więc jednej symulacji nie da się
podzielić. Za to punkty przeglądu (etapy 5–6) są niezależne: każdy liczymy w osobnym
procesie, kilka naraz.

Procesy startują metodą "spawn" (czysty interpreter), nie "fork": SOFA trzyma stan
globalny (fabryka komponentów, wczytane wtyczki), którego kopiowanie forkiem nie jest
bezpieczne. Jeden proces ≈ 0.5 GB RAM na siatce coarse.
"""
import multiprocessing as mp
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed


def default_workers(n_jobs: int) -> int:
    """Liczba procesów: tyle, ile zadań, ale zostawiamy 2 rdzenie dla systemu (GUI, IO).
    FISHSOFA_WORKERS nadpisuje limit (np. gdy liczy się coś jeszcze)."""
    limit = int(os.environ.get("FISHSOFA_WORKERS", 0)) or (os.cpu_count() or 2) - 2
    return max(1, min(n_jobs, limit))


def run_all(fn, jobs: dict, workers: int | None = None, label: str = "") -> dict:
    """Wywołuje fn(**kwargs) dla każdego jobs[klucz] = kwargs w osobnych procesach.

    Zwraca {klucz: wynik}. fn musi być funkcją z poziomu modułu (pickle).
    Postęp: jedna linia na zakończone zadanie.
    """
    workers = workers or default_workers(len(jobs))
    out, t0 = {}, time.perf_counter()
    print(f"{label}{len(jobs)} symulacji, {workers} naraz", flush=True)
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(fn, **kw): key for key, kw in jobs.items()}
        for i, fut in enumerate(as_completed(futs), 1):
            key = futs[fut]
            out[key] = fut.result()
            print(f"  [{i}/{len(jobs)}] {key} gotowe po {(time.perf_counter() - t0) / 60:.1f} min", flush=True)
    return out
