"""Environment check: PyElastica version and performance settings."""
import os

import elastica as ea
import numba
from elastica.version import VERSION


def test_pyelastica_version():
    assert VERSION == "1.0.0"


def test_single_thread_per_process():
    assert os.environ["OPENBLAS_NUM_THREADS"] == "1"
    assert numba.config.NUMBA_NUM_THREADS == 1


def test_rod_steps():
    import numpy as np

    class Sim(ea.BaseSystemCollection, ea.Constraints):
        pass

    sim = Sim()
    rod = ea.CosseratRod.straight_rod(
        20, np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0]),
        0.4, 0.02, 1050.0, youngs_modulus=1e6, shear_modulus=1e6 / 3,
    )
    sim.append(rod)
    sim.finalize()
    stepper = ea.PositionVerlet()
    t = np.float64(0.0)
    for _ in range(100):
        t = stepper.step(sim, t, 1e-5)
    assert np.all(np.isfinite(rod.position_collection))
