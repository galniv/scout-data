# scout-data — Family Scout picking feed

This repo publishes one file, `picking.json`: the **current** pick-your-own (PYO)
fruit status for our farms, read by the home dashboard
([galniv/ha-dashboard](https://github.com/galniv/ha-dashboard), `src/scout/picking.ts`).
It's public on purpose (non-sensitive — just what fruit is ripe) so the dashboard
can fetch it without auth at
`https://raw.githubusercontent.com/galniv/scout-data/main/picking.json`.

A scheduled Claude routine updates it. **This file is the routine's instructions**
— the routine prompt can just say *"Update picking.json following CLAUDE.md."*

## Each run

Read the **current** pick-your-own status of three MA farms and write
`picking.json`, then commit it to `main`. Do a **fresh** read every run (don't
reuse the old file), and set `generatedAt` to the current time.

Farms + their current-status pages:
- **Tougas Family Farm** (Northborough) — https://www.tougasfamilyfarm.com/whats-picking (a daily "what's picking today" page)
- **Ward's Berry Farm** (Sharon) — https://www.wardsberryfarm.com/pick-your-own (has a "Today's Conditions" list: each fruit with a rating like Good/Excellent + price)
- **Lookout Farm** / Belkin Family Lookout Farm (South Natick) — https://www.lookoutfarm.com/

## How to fetch — use the Jina reader, NOT WebFetch

The farm sites **block direct fetches** from this environment (they return HTTP
403 — datacenter-IP / bot protection), and some are JS/image-heavy. So do **not**
use `WebFetch` on the farm URLs. Instead fetch each page through the **Jina reader
proxy**, which loads the page server-side (rendering JS/images) and returns clean
markdown. Use `curl` in Bash, prefixing the farm URL with `https://r.jina.ai/`:

```bash
curl -s --max-time 90 "https://r.jina.ai/https://www.tougasfamilyfarm.com/whats-picking"
curl -s --max-time 90 "https://r.jina.ai/https://www.wardsberryfarm.com/pick-your-own"
curl -s --max-time 90 "https://r.jina.ai/https://www.lookoutfarm.com/"
```

This returns the readable page text (e.g. Ward's "Today's Conditions" with each
fruit + condition, Tougas's picking list). Read it and extract the fruit. If a
reader call fails or comes back empty, retry it once; you may also try a
`WebSearch` for "<farm> what's picking <month year>" as a supplement, but the
reader output is the primary source.

## What to record

- For each farm, list **every FRUIT** shown as currently available / picking today
  (on Ward's, that's the fruits in "Today's Conditions"; on Tougas, the "picking
  today" list). List them all, not just the first one or two.
- **Fruit only.** Never include flowers (sunflowers, tulips, "flowers"),
  vegetables, or herbs.
- Any fruit type — not a preset list. Include gooseberries, currants,
  elderberries, etc. if the page shows them.
- Only include fruit with **real current evidence** on the page. If a farm's page
  shows nothing pickable right now, include nothing for it. **Never** guess from
  typical seasons.

## Output — `picking.json` (repo root)

One object **per fruit per farm** (a farm with several fruits gets several rows):

```json
{
  "generatedAt": "2026-07-04T07:05:00-04:00",
  "crops": [
    { "crop": "blueberries", "orchard": "Ward's Berry Farm", "status": "good", "url": "https://www.wardsberryfarm.com/pick-your-own" },
    { "crop": "gooseberries", "orchard": "Ward's Berry Farm", "status": "good", "url": "https://www.wardsberryfarm.com/pick-your-own" },
    { "crop": "cherries", "orchard": "Tougas Family Farm", "status": "now picking", "url": "https://www.tougasfamilyfarm.com/whats-picking" }
  ]
}
```

- `generatedAt`: ISO 8601 with `-04:00` offset, set to **now**.
- `crop`: lowercase, plural fruit name. Not a preset list; **no flowers/veg**.
- `orchard`: exactly `Tougas Family Farm`, `Ward's Berry Farm`, or `Lookout Farm`.
- `status`: a short phrase you actually read — e.g. `now picking`, `good`,
  `excellent`, `ending soon`.
- `url`: the farm page.

**If every farm fetch fails**, do NOT overwrite `picking.json` — leave the last
good feed in place and report the error. Only ever write fruit you actually read
this run.

## Publish to `main`

The sandbox's own git is read-only, so commit via the GitHub Contents API with the
authenticated `gh` CLI:

```bash
SHA=$(gh api repos/galniv/scout-data/contents/picking.json --jq .sha 2>/dev/null)
B64=$(base64 < picking.json | tr -d '\n')
gh api -X PUT repos/galniv/scout-data/contents/picking.json \
  -f message="Update picking feed" \
  -f content="$B64" \
  ${SHA:+-f sha="$SHA"} \
  -f branch=main
```

Confirm the response contains a new `commit`.
