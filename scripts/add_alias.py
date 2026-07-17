#!/usr/bin/env python3
"""Add a variant spelling to an existing canonical fruit.

    python3 scripts/add_alias.py "highbush blueberry" blueberries

Deterministic: validates the canonical exists, de-dupes, keeps aliases.json
sorted. Use this (never hand-edit aliases.json) so a stray character can't break
the file. Exits non-zero with a clear message if the canonical is unknown (then
use add_fruit.py to create it first).
"""

from __future__ import annotations

import sys

from aliases_lib import build_reverse, canonical_of, load_aliases, normalize_name, save_aliases


def main() -> int:
    if len(sys.argv) != 3:
        print('usage: add_alias.py "<variant>" <canonical>', file=sys.stderr)
        return 2
    variant, canonical = sys.argv[1], sys.argv[2]
    aliases = load_aliases()

    if canonical not in aliases:
        print(f"error: canonical '{canonical}' does not exist; add it with add_fruit.py first", file=sys.stderr)
        return 1

    existing = canonical_of(variant, build_reverse(aliases))
    if existing == canonical:
        print(f"noop: '{variant}' already maps to '{canonical}'")
        return 0
    if existing is not None:
        print(f"error: '{variant}' already maps to '{existing}', not '{canonical}'", file=sys.stderr)
        return 1

    aliases[canonical].append(normalize_name(variant))
    save_aliases(aliases)
    print(f"added alias '{normalize_name(variant)}' -> '{canonical}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
