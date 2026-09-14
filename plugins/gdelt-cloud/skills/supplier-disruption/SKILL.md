---
name: gdelt-cloud-supplier-disruption
description: Use this skill to build a supplier, site or supply-chain disruption watchboard on GDELT Cloud — detecting unrest, strikes, port closures, regulatory action and sanctions near a set of physical sites or against a set of supplier companies, ranking by severity, and emitting a daily digest with an escalation threshold. Triggers on supply-chain risk, supplier monitoring, plant or mine disruption, logistics and port disruption, and commodity sourcing-country monitoring.
---

# Supplier and site disruption watchboard

N suppliers × M sites, run daily, with a threshold that pages someone. The two things that make this
hard are geography precision and knowing when a day is complete.

Read `gdelt-cloud-getting-started` first. Rules 5, 6 and 8 are what keep this from crying wolf.

## The taxonomy is split across domains you would not guess

Supply-chain relevant codes do not live in one place:

- supply-chain shock sits under the **corporate** domain
- infrastructure disruption sits under **infrastructure**
- **strikes and labour action sit under the demographic domain**, not under protest

`subcategory` requires its parent `category`, so filtering the obvious way misses siblings. Ask the
docs MCP for the domain code pages (`/reference/codes-domains`) and assemble your own list of
(category, subcategory) pairs once, at the top of the file, with a comment saying why each is in it.
Do not hardcode the list from memory — it is published and it changes.

## Sites: use the native exact-radius filter

```
GET /api/v2/events
  ?near=<latitude,longitude>
  &radius_km=<kilometres>
  &country_match=location
  &geo_precision_max=2
  &date_start=…&date_end=…
```

`near` is **latitude first** and `/events` applies an exact great-circle distance fence after a
bounding-box candidate prune. Use `bbox=<lat_min,lon_min,lat_max,lon_max>` only when the site scope
really is rectangular; do not reimplement proximity with a client-side haversine filter.

`geo_precision_max=2` is the difference between an event at your plant and an event anywhere in that
country. Without it, every country-centroid event inside your box scores as on-site, and in
compact countries the centroid is inside every box you would draw.

## Suppliers: resolve, then watch

Resolve each supplier once with
`GET /api/v2/search?q=<name>&type=organization&limit=10`, present ambiguous candidates, and cache the
selected terminal `e_…` id — see the `gdelt-cloud-counterparty-exposure` skill for the
identifier-space rules, which apply here too. Then per supplier: `/events?entity=`,
`/stories?entity=`, and media tone if entitled.

**Treat entity-scoped Events as coverage, not supplier attribution.** The supplier appears in a
linked Story; this does not establish that it acted in or was materially affected by the Event.
Omit `entity_match` to inherit the API default, or pass the only supported value, `coverage`.
Inspect the linked Story and source evidence before escalating a row. The Event surface already
serves the adjudicated incident view; preserve `incident.uid` as the deduplication key when merging
pages or combining several supplier queries.

For a supplier set that shares one question, cadence, delivery route, and response process, prefer
a Hosted entity Monitor with up to 25 confirmed ids and `match: coverage`; use
`gdelt-cloud-hosted-monitors` for resolve → preview → create → replay. The Monitor is an intake
signal, not proof that a supplier was materially affected. Keep this client watchboard when you
need N suppliers × M sites, private dependency data, sanctions diffs, tone, a day-of-week baseline,
or one combined escalation score: those are composite operations a single Monitor does not express.

For "was a supplier newly sanctioned this week", note that three different questions exist and they
disagree:

- `GET /api/v2/screening/match` — name matching against screening lists, as of a date
- `GET /api/v2/lists/entries?active_on=…` — the point-in-time membership question
- `GET /api/v2/lists/changes` — the diff feed

`/lists/changes` has **no entity filter**, so supplier-specific change detection means walking the
feed and matching client-side. Prefer diffing `screening/match` between two `as_of` dates as the
primary signal and use the change feed as a cross-check. Screening output is a **risk signal, not a
compliance control** — say so in the output, every time.

## Counting, and why you cannot

A list response does not carry a total by default — pagination is `{limit, cursor, next_cursor}`.
Two ways to get one, and they answer slightly different questions:

- **`include_total=true` on `/events`** adds `pagination.estimated_total`. Opt-in because it is a
  second scan of the same window, so ask on the first page and not on every one. It is `null` on a
  `search=` request, and it is not available on every list endpoint — check the parameter list for
  the one you are calling.
- **`/events/summary`** takes `country_match`, `geo_precision_max` and `entity`, so it can count
  the population your list describes — but it takes no `search`, so confirm the two agree by
  comparing `applied_filters` on both responses rather than assuming it.

Where neither is available to you, the consequences you must build around:

- Report "at least N" and whether you stopped early, never a bare count.
- An escalation threshold above one page size can never fire unless you paginate to exhaustion.
- Never present a summary count and a filtered list side by side as if they reconcile.

## Freshness

Coded history begins March 2026 and today is still filling. A digest that runs at 06:00 against a
partially-settled day produces a false all-clear. Bound the digest to **complete** days — run over
`date_end = yesterday` — and put the window in the output so a reader can see what was and was not
covered.

## Ranking and the threshold

Rank by `significance` — the only metric meant to compare events across domains. Keep the other
rubric metrics as separate columns; their published noise floors are at `/metrics/limits` and summing
them produces a number with no defined meaning.

For the threshold, compare against a trailing baseline with a day-of-week control. Weekend news
volume is structurally lower, so an absolute daily threshold fires on Mondays and sleeps on Sundays.

## Output

A daily HTML digest: an escalation banner when the threshold trips, per-site and per-supplier rows
sorted by severity, the events with their source articles, tone deltas where entitled, and a footer
naming the window, the sites that returned nothing, and any leg skipped for entitlement. The hosted
reference implementations are <https://gdeltcloud.com/demos/bauxite-supply-chain-monitor> and
<https://gdeltcloud.com/demos/apac-risk-workbench>.

**Search in the supplier's own press.** A disruption at a Japanese, Korean or German plant is reported locally first and often only. Pass `languages=ja,ko,de` and write the semantic `search` string in that language — an English query over a non-English event returns thin, off-topic results that read as "no disruption" and are not.
