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

## Sites: box, then refine

```
GET /api/v2/events
  ?bbox=<lat_min,lon_min,lat_max,lon_max>
  &country_match=location
  &geo_precision_max=2
  &date_start=…&date_end=…
```

`bbox` on `/events` is **latitude first** and is applied as the enclosing box, not a true radius —
a deliberate superset. Refine with a haversine filter against each site's coordinates client-side.

`geo_precision_max=2` is the difference between an event at your plant and an event anywhere in that
country. Without it, every country-centroid event inside your box scores as on-site, and in
compact countries the centroid is inside every box you would draw.

## Suppliers: resolve, then watch

Resolve each supplier once with `GET /api/v2/search` and cache the spine `e_…` id — see the
`gdelt-cloud-counterparty-exposure` skill for the identifier-space rules, which apply here too. Then
per supplier: `/events?entity=`, `/stories?entity=`, and media tone if entitled.

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

There is no `total` on any list response — pagination is `{limit, cursor, next_cursor}`.
`/events/summary` DOES take `country_match`, `geo_precision_max` and `entity`, so it can give you
the count of the population your list describes — but confirm that by comparing `applied_filters`
on both responses rather than assuming it, and note it takes no `search`. Consequences you must
still build around:

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
