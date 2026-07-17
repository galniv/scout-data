# scout-data — Family Scout picking feed

This repo publishes one file, `picking.json`: the **current** pick-your-own (PYO)
fruit status for our regular farms **plus a few nearby farms that have fruit
picking right now**. It's read by the home dashboard
([galniv/ha-dashboard](https://github.com/galniv/ha-dashboard), `src/scout/picking.ts`),
public on purpose (non-sensitive — just what fruit is ripe) so the dashboard can
fetch it without auth at
`https://raw.githubusercontent.com/galniv/scout-data/main/picking.json`.

A scheduled Claude routine updates it. **This file is the routine's instructions**
— the routine prompt can just say *"Update picking.json following CLAUDE.md."*

## Each run

Do a **fresh** read (don't reuse the old file), set `generatedAt` to now, then
write `picking.json` (farm-centric, see Output) and commit to `main`. Two parts:

1. **Home farms** — read our three regular farms' current status (always included).
2. **Discovery** — find a few nearby farms that have fruit picking **right now**.

## 1. Home farms (always include)

Always in the feed, even if farther than the discovery radius. Fetch each via the
Jina reader (see "How to fetch"):

- **Tougas Family Farm** (Northborough) — https://www.tougasfamilyfarm.com/whats-picking (daily "what's picking today" page)
- **Ward's Berry Farm** (Sharon) — https://www.wardsberryfarm.com/pick-your-own ("Today's Conditions" list: each fruit + a rating like Good/Excellent)
- **Lookout Farm** / Belkin Family Lookout Farm (South Natick) — https://www.lookoutfarm.com/

Mark these `"home": true`.

## 2. Discover nearby farms — fruit available NOW (read carefully)

Home base is **Needham, MA**. Find a few *additional* PYO farms within about a
**25-minute drive** of Needham that are **open and picking right now**.

Method, and this part matters:

1. From the home farms you just read, note which fruits are **currently being
   picked** (in early/mid summer that's often strawberries, blueberries,
   raspberries, cherries, currants, gooseberries).
2. Search for OTHER nearby farms **currently open** for **those specific
   in-season fruits** — search per fruit, e.g. `pick your own blueberries near
   Needham MA open now <month> <year>`, `raspberry picking near Needham MA
   <month> <year>`. Use `WebSearch` to find candidates.
3. For each candidate, **confirm it is actually picking that fruit right now** —
   read its "what's picking" / PYO page through the Jina reader, or a very recent
   (~last 10 days) social post.

**Never include a farm based on typical season — only current, confirmed
availability.** In particular: there are **many apple orchards** around here, but
apples are a **fall** crop, so do **not** list an apple farm unless apples are
genuinely being picked *today*. The same rule applies to every fruit: if you
can't confirm it's open this week, leave it out.

Keep discovery **small and bounded** — a handful of confirmed farms is plenty (the
dashboard only shows the nearest few per fruit anyway). For each discovered farm,
estimate `driveMinutes` from Needham (rough is fine) and mark `"home": false`. If
you can't confirm any nearby farms, that's fine — just publish the home farms.

## How to fetch — use the Jina reader, NOT WebFetch

The farm sites **block direct fetches** from this environment (HTTP 403 —
datacenter-IP / bot protection), and some are JS/image-heavy. **Never fetch a farm
URL directly** — always go through the **Jina reader proxy**, which loads the page
from its own servers (bypassing the 403) and renders JS/images to clean markdown.
Prefix the farm URL with `https://r.jina.ai/`, e.g.
`https://r.jina.ai/https://www.tougasfamilyfarm.com/whats-picking`.

Fetch each reader URL — use whichever works in this environment:

1. **`curl` in Bash** (preferred — full raw text):
   `curl -s --max-time 90 "https://r.jina.ai/https://www.tougasfamilyfarm.com/whats-picking"`
2. **If Bash has no network / curl fails**, use **`WebFetch` on the same reader
   URL** (first load it: run `ToolSearch` with `select:WebFetch`, then
   `WebFetch(url="https://r.jina.ai/<farm-url>", prompt="List every fruit currently available for pick-your-own and its condition/status.")`).

Use the reader for the home farm pages **and** to confirm discovered farms. Use
`WebSearch` to *find* candidate farms, then confirm each via its page through the
reader. If a reader call fails or is empty, retry once and print the URL + what
happened.

## What to record (fruit only)

For each farm (home and discovered), list **every FRUIT** currently open for PYO.
**Fruit only** — never flowers (sunflowers, tulips, "flowers"), vegetables, or
herbs. Any fruit type (gooseberries, currants, etc.), not a preset list. Only fruit
with **real current evidence** on the page — never guess from typical seasons.

## Normalize crop names (required)

Crop names must be **canonical** and consistent across runs — that's what lets the
automatic season tracking (`seasons.json`) stay consistent for free. Canonical
names and their accepted variants live in **`aliases.json`** (canonical →
variants). Don't eyeball it — use the scripts:

1. After writing `picking.json`, run **`python3 scripts/normalize_picking.py`**.
   It rewrites known crop names to their canonical form in place.
2. If it exits non-zero it lists **UNKNOWN** crops (no alias entry yet). For each,
   decide: a spelling/variant of a fruit already in `aliases.json`, or a genuinely
   new fruit?
   - Variant of an existing canonical → `python3 scripts/add_alias.py "<crop as read>" <canonical>` (e.g. `add_alias.py "highbush blueberry" blueberries`).
   - A new fruit → `python3 scripts/add_fruit.py <canonical> ["<variant>" ...]` (canonical = lowercase plural, e.g. `add_fruit.py figs fig`).
   Then re-run `normalize_picking.py`. Repeat until it exits 0.
3. **Never hand-edit `aliases.json`** — always go through the scripts (they
   validate, de-dupe, and keep it sorted, so a stray character can't break it).

If `aliases.json` changed this run, publish it alongside `picking.json` (see Publish).

## Output — `picking.json` (repo root), farm-centric

```json
{
  "generatedAt": "2026-07-05T07:05:00-04:00",
  "farms": [
    {
      "name": "Ward's Berry Farm",
      "url": "https://www.wardsberryfarm.com/pick-your-own",
      "home": true,
      "driveMinutes": 20,
      "crops": [
        { "crop": "blueberries", "status": "good" },
        { "crop": "gooseberries", "status": "good" }
      ]
    },
    {
      "name": "Example Berry Farm",
      "url": "https://www.example.com/pick-your-own",
      "home": false,
      "driveMinutes": 18,
      "crops": [ { "crop": "blueberries", "status": "now picking" } ]
    }
  ]
}
```

- `generatedAt`: ISO 8601 with `-04:00` offset, set to **now**.
- `name`: the farm's name (shown verbatim on the dashboard).
- `url`: the farm's "what's picking" / PYO page (the tap-through link).
- `home`: `true` for our three farms, `false` for discovered ones.
- `driveMinutes`: estimated drive time from Needham, MA (integer; rough is fine).
- `crops`: fruit only; `crop` = lowercase plural **and canonical** (run through
  `normalize_picking.py` — see "Normalize crop names"); `status` = a short phrase
  you read (`now picking`, `good`, `excellent`, `ending soon`).

This farm-centric shape is the **only** shape — there's no legacy/crop-centric
fallback anymore.

Include a farm only if it has ≥1 confirmed fruit. **If all fetches fail**, do NOT
overwrite `picking.json` — leave the last good feed in place and report the error.

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

If `aliases.json` changed this run (you added a variant or a new fruit), publish
it the same way — a second `gh api -X PUT …/contents/aliases.json` with its own
`sha`.

### `seasons.json` is automatic — never touch it

`seasons.json` (per fruit, the `start`/`lastSeen` date each year) is maintained
**deterministically by a GitHub Action** that runs whenever `picking.json` is
pushed (`.github/workflows/seasons.yml` → `scripts/update_seasons.py`). The
routine must **never** write, edit, or publish `seasons.json` — it maintains
itself from the canonical `picking.json`.
