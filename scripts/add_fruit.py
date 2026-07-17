#!/usr/bin/env python3
"""Add a brand-new canonical fruit (optionally with variant spellings).

    python3 scripts/add_fruit.py figs fig
    python3 scripts/add_fruit.py quince

Canonical should be lowercase plural (e.g. "figs"). Deterministic: refuses if the
canonical — or any given variant — already exists elsewhere. Use this instead of
hand-editing aliases.json.
"""

from __future__ import annotations

import sys

from aliases_lib import build_reverse, canonical_of, load_aliases, normalize_name, save_aliases


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: add_fruit.py <canonical> [variant ...]", file=sys.stderr)
        return 2
    canonical = normalize_name(sys.argv[1])
    variants = [normalize_name(v) for v in sys.argv[2:]]
    aliases = load_aliases()
    reverse = build_reverse(aliases)

    if canonical in aliases:
        print(f"error: canonical '{canonical}' already exists", file=sys.stderr)
        return 1
    for name in [canonical, *variants]:
        clash = canonical_of(name, reverse)
        if clash is not None:
            print(f"error: '{name}' already maps to '{clash}'", file=sys.stderr)
            return 1

    aliases[canonical] = variants
    save_aliases(aliases)
    print(f"added fruit '{canonical}'" + (f" with variants {variants}" if variants else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
