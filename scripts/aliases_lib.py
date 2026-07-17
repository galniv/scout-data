"""Shared helpers for the fruit-name normalization files.

aliases.json maps a canonical fruit name (lowercase plural, e.g. "blueberries")
to the list of variants that should collapse into it. Everything that writes
these files goes through here so the on-disk shape stays consistent (sorted,
2-space indent) and reads/writes are deterministic — never hand-edited.
"""

from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIASES_PATH = os.path.join(ROOT, "aliases.json")


def normalize_name(name: str) -> str:
    """Lowercase, trim, collapse inner whitespace — the comparison form."""
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def load_aliases(path: str = ALIASES_PATH) -> dict:
    with open(path) as f:
        return json.load(f)


def save_aliases(data: dict, path: str = ALIASES_PATH) -> None:
    """Write canonical keys sorted, each alias list sorted + de-duped."""
    clean = {k: sorted(set(normalize_name(a) for a in v)) for k, v in data.items()}
    ordered = {k: clean[k] for k in sorted(clean)}
    with open(path, "w") as f:
        json.dump(ordered, f, indent=2, ensure_ascii=False)
        f.write("\n")


def build_reverse(aliases: dict) -> dict:
    """{variant-or-canonical (normalized) -> canonical}."""
    rev: dict[str, str] = {}
    for canonical, variants in aliases.items():
        rev[normalize_name(canonical)] = canonical
        for v in variants:
            rev[normalize_name(v)] = canonical
    return rev


def canonical_of(name: str, reverse: dict) -> str | None:
    """Canonical for a raw crop name, or None if unknown (needs adding)."""
    return reverse.get(normalize_name(name))
