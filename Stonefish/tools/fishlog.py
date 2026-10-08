"""Wczytywanie logów CSV z aplikacji konsolowej (linie '#' to komentarze)."""

import numpy as np


class Log(dict):
    """Słownik kolumna -> tablica numpy, plus dostęp atrybutem: log.t, log.x ..."""

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e


def read_log(path) -> Log:
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    header = lines[0].strip().split(",")
    data = np.loadtxt(lines[1:], delimiter=",", ndmin=2)
    return Log({h: data[:, i] for i, h in enumerate(header)})


def at(log, t):
    """Indeks próbki najbliższej czasowi t."""
    return int(np.argmin(np.abs(log["t"] - t)))
