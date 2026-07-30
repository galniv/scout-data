#!/usr/bin/env python3
"""Self-heal picking.json if the publishing routine double-base64-encoded it.

The picking feed is published by a model-driven cloud routine. Twice
(2026-07-29, 2026-07-30) it base64-encoded picking.json an extra time, storing a
base64 blob as the file — which breaks update_seasons.py *and* the dashboard.
CLAUDE.md and a guarded publish script weren't enough because the model doesn't
reliably invoke them. This runs first in the seasons workflow (deterministic CI
that can't be skipped) and fixes the file in place:

  * already valid JSON      -> no-op (the normal case)
  * base64-of-valid-JSON    -> decode in place (the double-encode bug)
  * anything else           -> fail loudly (don't write garbage over the feed)
"""
from __future__ import annotations

import base64
import binascii
import json
import sys

PATH = "picking.json"


def main() -> int:
    raw = open(PATH, "rb").read()

    try:
        json.loads(raw)
        return 0  # already valid JSON — nothing to do
    except json.JSONDecodeError:
        pass

    # Not JSON. The only tolerated failure mode is a double-base64 blob whose
    # decoded bytes are valid JSON; anything else is a real problem, fail loudly.
    try:
        decoded = base64.b64decode(raw.strip(), validate=True)
        json.loads(decoded)
    except (binascii.Error, ValueError, json.JSONDecodeError) as e:
        sys.exit(f"picking.json is neither valid JSON nor base64-of-JSON: {e}")

    open(PATH, "wb").write(decoded)
    print("repaired picking.json (was double-base64-encoded by the publish step)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
