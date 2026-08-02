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
import os
import subprocess
import sys
import urllib.request
import urllib.error

REPO = "galniv/scout-data"
API_BASE = "https://api.github.com"


def _api_get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _api_put(url: str, token: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="PUT", headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def publish(path: str) -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        # Fall back to gh CLI if available and no token in env
        token = None

    with open(path, "rb") as f:
        raw = f.read()

    # Guard: only ever publish valid JSON. This is what stops a base64 blob or a
    # truncated/garbled file from reaching `main` (the 2026-07-29 outage).
    try:
        json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"refusing to publish {path}: not valid JSON ({e})")

    content = base64.b64encode(raw).decode()  # encode ONCE

    if token:
        url = f"{API_BASE}/repos/{REPO}/contents/{path}"
        try:
            existing = _api_get(url, token)
            sha = existing.get("sha", "")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                sha = ""
            else:
                sys.exit(f"publish failed fetching sha for {path}: {e}")

        payload = {
            "message": f"Update {path}",
            "content": content,
            "branch": "main",
        }
        if sha:
            payload["sha"] = sha

        try:
            result = _api_put(url, token, payload)
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            sys.exit(f"publish failed for {path}: {e} — {body}")
        commit = result.get("commit", {}).get("sha", "?")
        print(f"published {path} → commit {commit[:8]}")
    else:
        # gh CLI fallback
        gh_get = subprocess.run(
            ["gh", "api", f"repos/{REPO}/contents/{path}", "--jq", ".sha"],
            capture_output=True, text=True,
        )
        sha = gh_get.stdout.strip()
        args = [
            "api", "-X", "PUT", f"repos/{REPO}/contents/{path}",
            "-f", f"message=Update {path}",
            "-f", f"content={content}",
            "-f", "branch=main",
        ]
        if sha:
            args += ["-f", f"sha={sha}"]
        res = subprocess.run(["gh", *args], capture_output=True, text=True)
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
