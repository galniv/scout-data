#!/usr/bin/env python3
"""Rewrite picking.json crop names to their canonical form (from aliases.json).

Known crops are canonicalized in place. Any crop with no alias entry is left
untouched and reported, and the script exits non-zero — the caller (the routine)
adds it via add_alias.py / add_fruit.py and re-runs. This keeps picking.json (and
therefore seasons.json) consistently canonical.
"""

from __future__ import annotations

import json
import os
import sys

from aliases_lib import ROOT, build_reverse, canonical_of, load_aliases

PICKING = os.path.join(ROOT, "picking.json")


def main() -> int:
    reverse = build_reverse(load_aliases())
    with open(PICKING) as f:
        data = json.load(f)

    unknown: set[str] = set()
    for farm in data.get("farms", []):
        for c in farm.get("crops", []):
            raw = c.get("crop", "")
            canon = canonical_of(raw, reverse)
            if canon is None:
                unknown.add((raw or "").strip().lower())
            else:
                c["crop"] = canon

    with open(PICKING, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if unknown:
        print("UNKNOWN crops — add with add_alias.py / add_fruit.py, then re-run:", file=sys.stderr)
        for u in sorted(unknown):
            print(f"  {u}", file=sys.stderr)
        return 1
    print("picking.json normalized; all crops canonical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
