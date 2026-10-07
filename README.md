# fish-sim-v0 – miękka ryba jako pręt Cosserata (PyElastica)

Gałąź `pyelastica`: edukacyjne, **nieskalibrowane** demo robota-ryby w PyElastica.
Specyfikacja: [`SPEC_fish_pyelastica_demo.md`](SPEC_fish_pyelastica_demo.md), kod w [`fish_elastica_demo/`](fish_elastica_demo/).

Pozostałe dema są na osobnych gałęziach: `main` (MuJoCo), `openmodelica`, `sofa`, `openfoam`.

## Wersje

| Pakiet | Wersja |
|---|---|
| Python | 3.14 |
| PyElastica | 1.0.0 (`import elastica as ea`) |
| numba / llvmlite | 0.68.0 / 0.50.0 |
| numpy | 2.5.3 |

## Instalacja

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r fish_elastica_demo/requirements.txt
cd fish_elastica_demo && ../.venv/bin/python -m pytest
```

Pierwsze uruchomienie kompiluje kernele numby (~10 s), kolejne biorą je z cache (`fish_elastica_demo/.numba_cache/`).

## Wydajność

Ustawienia w [`fishrod/perf.py`](fish_elastica_demo/fishrod/perf.py) (ładowane przy `import fishrod`):
każda symulacja jednowątkowo, równoległość przez procesy (domyślnie liczba fizycznych rdzeni,
zmienna `FISHROD_WORKERS`). Pomiar na Ryzen AI 5 PRO 340, pręt 100 elementów: ~38k kroków/s
na proces, ~191k kroków/s na 6 procesach.
