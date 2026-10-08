"""Wczytywanie config/*.json (JSON z komentarzami //) – wspólne dla narzędzi Pythona.

Program C++ czyta te same pliki biblioteką nlohmann::json (opcja ignore_comments).
Python ma tylko standardowy moduł json, który komentarzy nie zna, więc usuwamy je
sami. Uwaga na "//" wewnątrz napisów (np. w ścieżkach) – tych nie ruszamy.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent      # katalog Stonefish/


def strip_comments(text: str) -> str:
    """Usuwa komentarze // (do końca linii), pomijając te w cudzysłowach."""
    out = []
    for line in text.splitlines():
        in_str = False
        esc = False
        cut = len(line)
        for i, ch in enumerate(line):
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
            elif ch == '"':
                in_str = not in_str
            elif ch == "/" and not in_str and line[i:i + 2] == "//":
                cut = i
                break
        out.append(line[:cut])
    return "\n".join(out)


def load_json(path) -> dict:
    return json.loads(strip_comments(Path(path).read_text(encoding="utf-8")))


def merge_patch(base: dict, patch: dict) -> dict:
    """RFC 7396 (JSON merge-patch) – tak samo jak json::merge_patch w C++."""
    out = dict(base)
    for k, v in patch.items():
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge_patch(out[k], v)
        else:
            out[k] = v
    return out


def load_config(scenario_json=None) -> dict:
    """config/default.json + opcjonalnie nadpisania z pliku scenariusza."""
    cfg = load_json(ROOT / "config" / "default.json")
    if scenario_json is not None:
        cfg = merge_patch(cfg, load_json(scenario_json))
    return cfg
