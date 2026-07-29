#!/usr/bin/env python3
"""Publish a JSON data file to scout-data's `main` via the GitHub Contents API —
the deterministic, guarded replacement for hand-running `base64` + `gh api`.

Why this exists: the routine's sandbox git is read-only, so we publish over the
Contents API, which wants the file content base64-encoded *exactly once*. On
2026-07-29 a hand-run publish base64-encoded `picking.json` twice, storing a
base64 blob as the file — which broke both `update_seasons.py` and the
dashboard's `fetchPicking`. This script removes that whole class of error:

  * it VALIDATES the file is real JSON first, so a malformed or already-encoded
    file is refused, never published; and
  * it does the base64 encode itself, exactly once.

Usage:
    python3 scripts/publish.py picking.json [aliases.json ...]
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys

REPO = "galniv/scout-data"


def _gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def publish(path: str) -> None:
    with open(path, "rb") as f:
        raw = f.read()

    # Guard: only ever publish valid JSON. This is what stops a base64 blob or a
    # truncated/garbled file from reaching `main` (the 2026-07-29 outage).
    try:
        json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"refusing to publish {path}: not valid JSON ({e})")

    content = base64.b64encode(raw).decode()  # encode ONCE
    sha = _gh(["api", f"repos/{REPO}/contents/{path}", "--jq", ".sha"]).stdout.strip()

    args = [
        "api", "-X", "PUT", f"repos/{REPO}/contents/{path}",
        "-f", f"message=Update {path}",
        "-f", f"content={content}",
        "-f", "branch=main",
    ]
    if sha:  # omitted only on the first-ever create
        args += ["-f", f"sha={sha}"]

    res = _gh(args)
    if res.returncode != 0:
        sys.exit(f"publish failed for {path}: {res.stderr.strip()}")
    commit = json.loads(res.stdout).get("commit", {}).get("sha", "?")
    print(f"published {path} → commit {commit[:8]}")


def main() -> int:
    for path in sys.argv[1:] or ["picking.json"]:
        publish(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
