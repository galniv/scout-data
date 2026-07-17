#!/usr/bin/env python3
"""Update seasons.json from the current picking.json. Deterministic; CI-run.

    seasons.json = { "<fruit>": { "<year>": { "start": "YYYY-MM-DD",
                                               "lastSeen": "YYYY-MM-DD" } } }

For each fruit in the feed: if there's no entry for this year, record start=today;
always bump lastSeen=today. There is no explicit "end" — the end of a past year's
season is simply that year's lastSeen. "today" is the date in picking.json's
`generatedAt` (home tz), so the record tracks the feed, not the CI clock.
Assumes picking.json crop names are already canonical (normalize_picking.py).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime

from aliases_lib import ROOT

PICKING = os.path.join(ROOT, "picking.json")
SEASONS = os.path.join(ROOT, "seasons.json")


def crops_in(data: dict) -> set[str]:
    out: set[str] = set()
    for farm in data.get("farms", []):
        for c in farm.get("crops", []):
            crop = (c.get("crop") or "").strip()
            if crop:
                out.add(crop)
    return out


def main() -> int:
    with open(PICKING) as f:
        picking = json.load(f)

    day = (picking.get("generatedAt") or "")[:10]  # YYYY-MM-DD from the ISO stamp
    try:
        year = str(datetime.strptime(day, "%Y-%m-%d").year)
    except ValueError:
        print(f"error: bad or missing generatedAt date '{day}'", file=sys.stderr)
        return 1

    crops = crops_in(picking)
    if not crops:
        print("no crops in feed; leaving seasons.json unchanged")
        return 0

    seasons: dict = {}
    if os.path.exists(SEASONS):
        with open(SEASONS) as f:
            seasons = json.load(f)

    for crop in crops:
        year_map = seasons.setdefault(crop, {})
        if year not in year_map:
            year_map[year] = {"start": day, "lastSeen": day}
        else:
            year_map[year]["lastSeen"] = day

    # Tidy + stable: fruits sorted, years sorted within each.
    ordered = {c: {yr: seasons[c][yr] for yr in sorted(seasons[c])} for c in sorted(seasons)}
    with open(SEASONS, "w") as f:
        json.dump(ordered, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"seasons.json updated for {day} ({len(crops)} crops)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
