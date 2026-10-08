"""Loading config/*.json (JSON with // comments) – shared by the Python tools.

The C++ program reads the same files with the nlohmann::json library (ignore_comments option).
Python only has the standard json module, which does not know about comments, so we strip
them ourselves. Watch out for "//" inside strings (e.g. in paths) – those are left alone.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent      # the Stonefish/ directory


def strip_comments(text: str) -> str:
    """Removes // comments (to end of line), skipping those inside quotes."""
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
    """RFC 7396 (JSON merge-patch) – same as json::merge_patch in C++."""
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
    """config/default.json + optional overrides from the scenario file."""
    cfg = load_json(ROOT / "config" / "default.json")
    if scenario_json is not None:
        cfg = merge_patch(cfg, load_json(scenario_json))
    return cfg
