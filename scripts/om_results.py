"""Szybki odczyt wyników OpenModelica (*.mat, format v4) bez uruchamiania omc."""

import numpy as np
import scipy.io


def read_mat(path, names):
    """Zwraca {nazwa: tablica} dla zmiennych z pliku wyników OpenModelica.

    Format: macierz 'name' (nazwy), 'dataInfo' (gdzie leży zmienna: [blok, ±kolumna, ...]),
    'data_1' (parametry, stałe w czasie) i 'data_2' (przebiegi). Ujemny indeks = zmienna z minusem (alias).
    """
    m = scipy.io.loadmat(path, chars_as_strings=False)
    transposed = "".join(m["Aclass"][3]).strip() == "binTrans"
    raw = m["name"].T if transposed else m["name"]
    all_names = ["".join(row).rstrip("\x00 ") for row in raw]
    info = m["dataInfo"].T if transposed else m["dataInfo"]
    data = {1: m["data_1"], 2: m["data_2"]}
    if transposed:
        data = {k: v.T for k, v in data.items()}  # -> wiersze = chwile czasu, kolumny = zmienne
    time = data[2][:, 0]
    index = {n: i for i, n in enumerate(all_names)}
    out = {}
    for n in names:
        block, col = int(info[index[n]][0]), int(info[index[n]][1])
        block = 2 if block == 0 else block  # 'time' ma blok 0, leży w data_2
        values = np.sign(col) * data[block][:, abs(col) - 1]
        out[n] = np.full_like(time, values[0]) if block == 1 else values
    return out
