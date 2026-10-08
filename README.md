# fish-sim-v0 – soft fish as a Cosserat rod (PyElastica)

Branch `pyelastica`: an educational, **uncalibrated** robotic-fish demo in PyElastica. The body and tail are one soft Cosserat rod, driven by internal hydraulic chambers through the rod's rest curvature. It swims in a custom high-Reynolds-number water model (quadratic drag + Lighthill reactive force), with buoyancy, a ballast bladder and a depth PID.

- Specification: [`SPEC_fish_pyelastica_demo.md`](SPEC_fish_pyelastica_demo.md)
- Code, results and full documentation: [`fish_elastica_demo/README.md`](fish_elastica_demo/README.md)

The other demos live on separate branches: `main` (MuJoCo), `sofa`, `stonefish`, `openfoam`, `openmodelica`.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r fish_elastica_demo/requirements.txt
cd fish_elastica_demo
../.venv/bin/python -m pytest                  # 19 tests
../.venv/bin/python scripts/run_scenarios.py   # figures + CSV in results/
../.venv/bin/python scripts/animate.py         # results/free_swim.gif
```

PyElastica 1.0.0, Python 3.14. Each simulation runs single-threaded; independent runs are spread over the physical cores (`FISHROD_WORKERS`).
