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

Farms (all pick-your-own, within range):
- **Tougas Family Farm**, Northborough MA
  - Current status page (**start here — clean and reliable**):
    https://www.tougasfamilyfarm.com/whats-picking — lists exactly what's picking
    today. Homepage: https://www.tougasfamilyfarm.com/
- **Ward's Berry Farm**, Sharon MA — https://www.wardsberryfarm.com/ ·
  https://www.wardsberryfarm.com/pick-your-own · their Facebook
- **Lookout Farm** (Belkin Family Lookout Farm), South Natick MA —
  https://www.lookoutfarm.com/ · U-pick store https://www.lookoutfarmorchard.com/ · FB https://www.facebook.com/lookoutfarm/

## Rules

1. **Report ANY fruit currently open for PYO** at these farms — you are not
   limited to a preset list. Whatever the farm actually lists as picking now
   counts (strawberries, blueberries, cherries, raspberries, blackberries,
   currants, gooseberries, peaches, nectarines, plums, pears, apples, and even
   pick-your-own flowers like sunflowers if the farm features them).
2. **Read current status, don't assume.** Check each farm's dedicated "what's
   picking" / pick-your-own page first (these farms publish current status), plus
   a recent (~last 10 days) Facebook/Instagram post or an available U-pick product
   in their online store. Use both WebFetch and WebSearch; if one page is thin or
   JS-heavy, search for "<farm name> what's picking <current month>".
3. **Never guess from typical seasons.** Include a crop **only** when there's real
   current evidence it's open for PYO today. If a farm's season hasn't started, is
   between crops, or you truly can't confirm anything, include **nothing** for it
   — empty is correct and expected (e.g. Lookout is commonly closed right after
   strawberries end / before peaches begin). But do check thoroughly first — in
   season, these farms usually DO have something picking.
4. Prefer under-reporting to over-reporting. A wrong "it's ripe!" is worse than
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
- `crop`: lowercase, plural — whatever is actually picking (e.g. `strawberries`, `blueberries`, `cherries`, `raspberries`, `currants`, `peaches`, `apples`, `sunflowers`). Not restricted to a preset list.
- `orchard`: the farm's name, shown verbatim on the dashboard — `Tougas Family Farm`, `Ward's Berry Farm`, or `Lookout Farm`.
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
