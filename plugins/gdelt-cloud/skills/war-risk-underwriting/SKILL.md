---
name: gdelt-cloud-war-risk-underwriting
description: Use this skill to build a war-risk, marine or political-violence exposure monitor on GDELT Cloud — chokepoint and route watchboards, war-risk underwriting briefs, per-region threat indices, hull and cargo exposure by littoral country. Triggers on requests about the Strait of Hormuz, the Red Sea, Bab-el-Mandeb, the Black Sea, the Niger Delta, or any "how dangerous is this route / region right now" question for an insurance, shipping or energy desk.
---

# War-risk and political-violence exposure monitor

The customer here is an underwriter or a marine analyst pricing a route, or a security team briefing
on a region. They need coded incidents with severity, geography they can trust to site level, the
articles behind each incident, and a rolling index they can defend to a committee.

Read the `gdelt-cloud-getting-started` skill first — the nine rules there decide whether this is
correct. Two of them are load-bearing for maritime work in particular:

- **`bbox` on `/events` is latitude first; `bbox` on every `/maritime/*` endpoint is longitude
  first.** A chokepoint box sent to the wrong family lands somewhere else entirely, at 200.
- **A country-centroid event is not an event at the strait.** Pass `geo_precision_max=2`.

## Build it in this order

### 1. Define the theatre as both a box and a country set

Chokepoints are small and cross borders, so do both and reconcile:

```python
HORMUZ = {"bbox": "24,54,28,58", "countries": ["Iran", "Oman", "United Arab Emirates", "Qatar"]}
```

`/events` treats `bbox` as the enclosing bounding box rather than a true distance filter — a
deliberate superset. Filter to your real polygon client-side if precision matters.

### 2. Shape the period before you list

```
GET /api/v2/events/summary?bbox=…&date_start=…&date_end=…&group_by=date
GET /api/v2/events/summary?bbox=…&date_start=…&date_end=…&group_by=subcategory
```

`/events/summary` takes `country_match`, `geo_precision_max` and `entity`, so it CAN be reconciled
against your filtered list — but only if you send the same filters to both and verify that by
diffing `applied_filters` on the two responses. It takes no `search`, so a semantic-search list has
no summary twin. Where the two cannot be made to agree, say so in the output rather than presenting
them side by side as though they did.

### 3. Pull the incidents

```
GET /api/v2/events
  ?bbox=24,54,28,58
  &country_match=location
  &geo_precision_max=2
  &date_start=…&date_end=…
  &sort=significance
  &limit=100
```

Ask the `gdelt-cloud-docs` MCP for the conflict categories rather than hardcoding them — the taxonomy is published
at `/reference/codes-conflict` and each code carries what it covers and what it explicitly does not.
The one most people miss on a maritime brief: interception and interdiction — a drone shot down, a
missile intercepted, a cache seized — is its own code, and it is most of the volume in a contested
strait.

**Fatalities:** gate with `has_fatalities=true`, then threshold the `fatalities` field client-side.
Range filters on it are rejected with `400 UNSUPPORTED_FILTER`, and fatalities are a conflict-family
observable — the CAMEO+ family serves `null`, which is not zero.

### 4. Attach the evidence

Every event links to the story it was coded from, and every story to its source articles:

```
GET /api/v2/events/{event_id}/stories
GET /api/v2/stories/{story_id}/articles
```

An underwriting brief that cannot show its sources is not an underwriting brief. Put the article
URLs in the output.

### 5. Energy and port exposure

```
GET /api/v2/facilities?bbox=…&class=…      # unified physical-asset directory
GET /api/v2/energy/assets?bbox=…           # GEM energy infrastructure with capacity
GET /api/v2/maritime/ports?bbox=…          # NOTE: longitude-first bbox
```

Owner resolution is partial by design and the API tells you so — roughly half of facility rows carry
a spine-resolved owner, and port rows carry essentially none. When you cannot bridge an asset to its
owner, say "not resolved", never "no exposure".

### 6. The index

Build it from what you pulled, and state the construction on the page. A defensible shape:

- incidents per day, weighted by `significance` (the only metric meant to compare across domains)
- a separate lethality series from `fatalities`, never summed into the same number
- a 7-day trailing mean against a fixed base window, so a quiet week is visibly quiet

**Do not sum the rubric metrics.** `magnitude`, `systemic_importance`, `propagation_potential` and
`market_sensitivity` are separate scales with published noise floors at `/metrics/limits`; adding
them produces a number with no defined meaning. And do not alert on a single day's reading without a
day-of-week control — weekend news volume is structurally lower, so a Sunday spike is usually the
calendar.

## Output

A single static HTML brief: executive summary, KPI tiles, a dated incident timeline, a map of the
theatre, the incident table with source links, and an explicit "what this does not cover" note
naming the coverage window and the owner-resolution gap. The hosted reference implementation is
<https://gdeltcloud.com/demos/strait-of-hormuz-underwriting-brief>.
