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

Farms:
- **Lookout Farm** (Belkin Family Lookout Farm), South Natick MA
  - https://www.lookoutfarm.com/ · U-pick store https://www.lookoutfarmorchard.com/ · FB https://www.facebook.com/lookoutfarm/
- **Ward's Berry Farm**, Sharon MA
  - https://www.wardsberryfarm.com/ · https://www.wardsberryfarm.com/pick-your-own · their Facebook

## Rules

1. **Read current status**, don't assume. Use web fetch/search for a "what's
   picking today" page, a recent (~last 10 days) Facebook/Instagram post, an
   available U-pick product in their online store, or an explicit current-season
   note.
2. **Never guess from typical seasons.** Include a crop **only** when there's real
   current evidence it's open for PYO today. If a farm's season hasn't started, is
   between crops, or you can't confirm anything, include **nothing** for it —
   empty is correct and expected (e.g. Lookout is commonly closed before its
   season starts, and right after strawberries end / before peaches begin).
3. Prefer under-reporting to over-reporting. A wrong "it's ripe!" is worse than
   silence — the dashboard shows nothing when the feed is empty, which is fine.

## Output format (`picking.json`, repo root, exactly this shape)

```json
{
  "generatedAt": "2026-07-15T07:03:00-04:00",
  "crops": [
    {
      "crop": "blueberries",
      "orchard": "Ward's Berry Farm",
      "status": "now picking",
      "url": "https://www.wardsberryfarm.com/pick-your-own"
    }
  ]
}
```

- `generatedAt`: ISO 8601 with timezone offset (America/New_York).
- `crop`: lowercase, plural (e.g. `strawberries`, `blueberries`, `peaches`, `apples`).
- `orchard`: exactly `Lookout Farm` or `Ward's Berry Farm` (the dashboard shows it verbatim).
- `status`: a short human phrase you actually read — e.g. `now picking`, `just opened`, `peak`, `ending soon`.
- `url`: the page you confirmed it from.
- If nothing is confirmed at either farm: `{"generatedAt":"<now>","crops":[]}`.

## Finish

Publish **directly to `main`** — the dashboard reads `main`, so do **not** open a
PR or leave the change on a working branch:

```
git add picking.json
git commit -m "Update picking feed"
git push origin HEAD:main
```

Keep the run short and cheap — a few fetches and a file write, no extensive
exploration.
