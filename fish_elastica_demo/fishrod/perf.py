"""Ustawienia wydajności dla PyElastica.

Pomiary na tej maszynie (Ryzen AI 5 PRO 340, 6 rdzeni / 12 wątków, pręt 100 elementów,
PositionVerlet, wspornik + grawitacja + AnalyticalLinearDamper):
  - pierwsze uruchomienie (kompilacja JIT ~90 kerneli numby): ~11.5 s,
    kolejne (cache numby na dysku): ~0.13 s,
  - jeden krok ~27 µs (50 elementów: ~20 µs) -> ~38k kroków/s na proces.
    Czas kroku to głównie narzut Pythona na wywołania kerneli, nie arytmetyka,
    dlatego wątki (BLAS/numba parallel) nic nie dają dla pojedynczego pręta.
  - skalowanie procesami: 1 -> 38k, 6 -> ~191k, 12 -> ~207k kroków/s łącznie.
    Optimum = liczba fizycznych rdzeni (SMT daje tylko +8%).

Wnioski dla kodu demo:
  1. Każda symulacja jednowątkowo (BLAS/OpenMP/numba = 1 wątek), żeby procesy
     równoległe nie walczyły o rdzenie.
  2. Przeglądy parametrów (etap 5) i niezależne scenariusze -> ProcessPoolExecutor
     z N_WORKERS procesami.
  3. Własne siły (water.py, buoyancy.py, actuation.py): pętle w funkcjach @njit(cache=True),
     wywoływane raz na krok; żadnych pętli Pythona po elementach.
  4. Callbacki zapisujące dane rzadko (step_skip), bo każde wywołanie kosztuje.
  5. Pętla integracji ręczna (stepper.step), bez paska tqdm z ea.integrate.
"""

import os

# Liczba fizycznych rdzeni (os.cpu_count() zwraca wątki SMT).
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

# Kompilacja pod konkretny procesor (AVX-512 na Zen 5) - domyślne w numbie,
# ustawiamy jawnie, żeby było widać. Cache trzymamy w katalogu projektu.
os.environ.setdefault("NUMBA_CPU_NAME", "host")
os.environ.setdefault(
    "NUMBA_CACHE_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".numba_cache"),
)
