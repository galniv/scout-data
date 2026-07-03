# scout-data — Family Scout picking feed

This repo publishes one file, `picking.json`: the **current** pick-your-own (PYO)
fruit status for our farms, read by the home dashboard
([galniv/ha-dashboard](https://github.com/galniv/ha-dashboard), `src/scout/picking.ts`).
It's public on purpose (non-sensitive — just what fruit is ripe) so the dashboard
can fetch it without auth at
`https://raw.githubusercontent.com/galniv/scout-data/main/picking.json`.

A scheduled Claude routine updates it every morning. **This file is the routine's
instructions** — the routine prompt can just say *"Update picking.json following
CLAUDE.md."*

## The job (each run)

Determine which fruit is **actually available to pick right now** at each farm,
then write `picking.json` and push to `main`.

**Every run is a fresh check.** Do not reuse or lightly edit the existing
`picking.json` — rebuild it from what you read today, and set `generatedAt` to
the current time. Visit **all three** farms, and for each, read its **full**
"what's picking" list and capture **every** fruit on it — in season a farm often
has 3–6 fruits at once (e.g. Ward's can have strawberries, blueberries,
**gooseberries**, currants, and more the same week). Don't stop after the first
one or two; list them all.

Farms (all pick-your-own, within range):
- **Tougas Family Farm**, Northborough MA
  - Current status page (**start here — clean and reliable**):
    https://www.tougasfamilyfarm.com/whats-picking — lists exactly what's picking
    today. Homepage: https://www.tougasfamilyfarm.com/
- **Ward's Berry Farm**, Sharon MA — https://www.wardsberryfarm.com/ ·
  https://www.wardsberryfarm.com/pick-your-own · their Facebook
- **Lookout Farm** (Belkin Family Lookout Farm), South Natick MA —
  https://www.lookoutfarm.com/ · U-pick store https://www.lookoutfarmorchard.com/ · FB https://www.facebook.com/lookoutfarm/

## Tooling note (do this first)

Before using `WebFetch` or `WebSearch`, **load their schemas** — in this
environment they're deferred tools. Run `ToolSearch` with
`select:WebFetch,WebSearch` (or search `web fetch search`) once at the start,
then call them normally. If you skip this, the call fails with
`WebFetch failed … required parameter 'prompt' is missing`.

## Rules

1. **Report every FRUIT currently open for PYO** at each farm — list them all,
   not just one, and you are not limited to a preset list. Whatever fruit the
   farm actually lists as picking now counts (strawberries, blueberries,
   cherries, raspberries, blackberries, currants, **gooseberries**, elderberries,
   peaches, nectarines, plums, apricots, pears, apples, grapes, melons, etc.) —
   including fruit types not named here.
   **Fruit only.** Do NOT include flowers (sunflowers, tulips, "summer flowers"),
   vegetables, herbs, or non-fruit items — we only care about fruit picking.
2. **Read the actual pages with `WebFetch`** — each farm's "what's picking" /
   pick-your-own page is the real source (it lists the full set of fruits).
   **Do NOT use `WebSearch` for the fruit list** — search snippets are incomplete
   and miss fruits, which is worse than nothing.
   **On failure, stop — don't guess and don't clobber good data.** If `WebFetch`
   returns **403** (the farms sometimes rate-limit/bot-block) or otherwise fails
   so you can't read a farm's real page, then **do not** fall back to search, **do
   not** guess from typical seasons, and **do not** write `picking.json` — leave
   the previous good feed untouched, print a clear error naming the farm(s) and
   status code, and exit. A 403 is usually temporary; the next daily run will
   likely succeed. Only ever write `picking.json` from fruit you actually read off
   a page this run.
3. **Never guess from typical seasons.** Include a crop **only** when there's real
   current evidence it's open for PYO today. If a farm's season hasn't started, is
   between crops, or you truly can't confirm anything, include **nothing** for it
   — empty is correct and expected (e.g. Lookout is commonly closed right after
   strawberries end / before peaches begin). But do check thoroughly first — in
   season, these farms usually DO have something picking.
4. Prefer under-reporting to over-reporting. A wrong "it's ripe!" is worse than
   silence — the dashboard shows nothing when the feed is empty, which is fine.

## Output format (`picking.json`, repo root, exactly this shape)

One object **per fruit per farm** — so a farm with several fruits gets several
entries (the dashboard groups them by farm and lists all of them).

```json
{
  "generatedAt": "2026-07-15T07:03:00-04:00",
  "crops": [
    { "crop": "strawberries", "orchard": "Ward's Berry Farm", "status": "now picking", "url": "https://www.wardsberryfarm.com/pick-your-own" },
    { "crop": "gooseberries", "orchard": "Ward's Berry Farm", "status": "now picking", "url": "https://www.wardsberryfarm.com/pick-your-own" },
    { "crop": "blueberries", "orchard": "Tougas Family Farm", "status": "now picking", "url": "https://www.tougasfamilyfarm.com/whats-picking" },
    { "crop": "cherries", "orchard": "Tougas Family Farm", "status": "now picking", "url": "https://www.tougasfamilyfarm.com/whats-picking" }
  ]
}
```

- `generatedAt`: ISO 8601 with timezone offset (America/New_York).
- `crop`: lowercase, plural — whatever **fruit** is actually picking. Not restricted to a preset list; **no flowers/veg**.
- `orchard`: the farm's name, shown verbatim on the dashboard — `Tougas Family Farm`, `Ward's Berry Farm`, or `Lookout Farm`.
- `status`: a short human phrase you actually read — e.g. `now picking`, `just opened`, `peak`, `ending soon`.
- `url`: the page you confirmed it from.
- If nothing is confirmed at either farm: `{"generatedAt":"<now>","crops":[]}`.

## Finish — publish to `main` via the GitHub API (important)

The dashboard reads `picking.json` on `main`. In this cloud environment a plain
`git push` does **not** leave the sandbox (it stays on an ephemeral branch), so
you MUST commit to `main` through the GitHub API using the authenticated `gh`
CLI. Do exactly this:

```bash
SHA=$(gh api repos/galniv/scout-data/contents/picking.json --jq .sha 2>/dev/null)
B64=$(base64 < picking.json | tr -d '\n')
gh api -X PUT repos/galniv/scout-data/contents/picking.json \
  -f message="Update picking feed" \
  -f content="$B64" \
  ${SHA:+-f sha="$SHA"} \
  -f branch=main
```

Confirm the API response contains a new `commit`. Only if `gh` is unavailable or
returns 403, fall back to `git commit` + `git push origin HEAD:main`.

Keep the run short and cheap — a few fetches and this write, no extensive
exploration.
