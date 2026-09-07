---
name: gdelt-cloud-core-api
description: Use this skill for ANY request that touches GDELT Cloud data — events, stories, summaries, entities, facilities, tone, or share of voice — whenever the user describes something they want to build, monitor, chart, count, or answer with it, and the request does not obviously belong to one of the narrower workflow skills. It maps a plain-English ask onto the right endpoint and the minimal correct call, so the first attempt returns real data instead of an empty 200.
---

# The Core API — which endpoint answers which question

Eight surfaces cover almost everything. Pick by the **shape of the question**, not by keyword.

| The user is asking | Endpoint | Returns |
| --- | --- | --- |
| *What happened?* | `GET /api/v2/events` | Coded events: date, place, actors, taxonomy, metrics, fatalities |
| *How much / what shape?* | `GET /api/v2/events/summary` | Aggregated buckets — counts and metrics by date, country, category… |
| *What is the coverage saying?* | `GET /api/v2/stories` | Deduplicated news clusters with their source articles |
| *What are the themes?* | `GET /api/v2/stories/summary` | Story volume bucketed by date, country, category |
| *Who is involved?* | `GET /api/v2/entities` | Resolved people, organizations, places with windowed metrics |
| *Where is the physical asset?* | `GET /api/v2/facilities` | Plants, mines, ports, pipelines, data centres — with coordinates |
| *How is X being talked about?* | `GET /api/v2/entities/{entity_id}/tone` | Sentiment for one entity over time, with evidence |
| *Who dominates the conversation?* | `GET /api/v2/share-of-voice` | One entity's share of a defined story population |

## One call, one Query Unit — page at 100

Every call below costs 1 QU regardless of `limit`, so `limit=25` is four times the price of
`limit=100` for the same data. Page at 100, and reach for a `/summary` endpoint before you count a
list by walking it.

## Always start here

```
GET /api/v2/search?q=<name>&type=<person|organization|place|facility>&country_match=strict&limit=10
```

Use this lexical candidate resolver (MCP `unified_entity_search`) for a company, person, place or
facility. Its compact filters are `type`, `country`, and `holds_office`; use `country_match=strict`
for known source country association. Inspect ambiguity and select the intended identity before
reusing its returned ID in a destination endpoint that supports that identifier space. Entity IDs
may be `e_…`, `wiki:…` or `llm:…`; facility candidates keep `facility_id`, separate from their owners.
Unlinked source records have no entity ID. Missing or withheld evidence never establishes zero.

## The minimal correct call for each

**Events — what happened.** Bound the window; it is capped at 30 days.

```
GET /api/v2/events?country=Nigeria&country_match=location&days=7&sort=significance&limit=50
```

`country_match=location` means *happened there*. Without it you also get events elsewhere involving
a Nigerian actor — often what you want for exposure, rarely what you want for a site watchboard.

**Events summary — count before you list.** Takes almost every list filter (`days`, `date`, `entity`,
`country_match`, `geo_precision_max`), but no `search`, `sort` or `cursor`.

```
GET /api/v2/events/summary?country=Nigeria&days=30&group_by=category
```

**Stories — the coverage behind the events.**

```
GET /api/v2/stories?story_category=CONFLICT&days=7&limit=25
GET /api/v2/stories/{story_id}/articles          # the actual sources
```

`story_category` takes either spelling — `CONFLICT` or `conflict_security`, `CORPORATE` or
`cameoplus_corporate`. Both resolve to the same filter.

**Entity candidates — select the identity.** Use the lexical resolver below. `/api/v2/entities`
separately discovers entities appearing in reporting within a date/geography/category scope;
its `metrics_scope` describes those reporting metrics.

```
GET /api/v2/search?q=Chevron&type=organization&country_match=strict
```

**Facilities — the physical layer.** `granularity=site` (default) returns physical sites;
`granularity=unit` returns registry units. `has_geo=true` is useful for a map, but omitting unknown
coordinates changes the inventory you can count. Country context `/api/v2/countries/{iso3}`
reports site `facility_count` and separate `unit_count` by type. Publication activity counts added
facility registry records, not newly built sites.

```
GET /api/v2/facilities?country=Indonesia&type=coal_mine&granularity=site&has_geo=true&limit=100
```

**Tone — how an entity is being talked about.** Needs a resolved id and a date window. The series
comes back in `rows` without asking for anything; `include_evidence` adds the stories behind each
point, and `language_breakdown` is always present if you want the per-language split. `group_by` on
this endpoint accepts only `language` — any other value is taken and ignored, so do not reach for
`group_by=date` here.

```
GET /api/v2/entities/e_12345/tone?days=30&include_evidence=true
```

**Share of voice — dominance within a population.** The denominator is the population you define; a
share is meaningless without knowing what it is a share *of*.

```
GET /api/v2/share-of-voice?entity_id=e_12345&category=CORPORATE&days=30
```

`category` is validated — a value outside the vocabulary returns `400 INVALID_ENUM` with the
accepted list attached, not a confident `0%`.

## Composing them — the pattern that answers most real questions

1. **Resolve** the thing (`/search`) → keep the `e_…` id.
2. **Size** the period (`/events/summary` or `/stories/summary`) → find where the volume is.
3. **Drill** into the buckets that carried it (`/events`, `/stories`).
4. **Attach** context: `/entities/{id}/tone` for sentiment, `/share-of-voice` for prominence,
   `/facilities` for the physical assets in the same geography.
5. **Cite** it: every event links to its stories, every story to its articles. Never present a number
   without the path back to the coverage behind it.

If the user wants the same single Event/Story question checked hourly or daily, switch to the
`gdelt-cloud-hosted-monitors` skill instead of writing a polling loop. Keep custom code for joins,
private state, nonstandard schedules, multi-endpoint dashboards, and historical baselines.

## Six things that return 200 and are wrong

1. **Reading `entity=` on `/events` as "events this entity did"** — it is not, and this is the one
   that has actually burned an evaluator. `entity_match` defaults to `material` (the entity is a
   party to the event), but where material attribution has not been built the server SUBSTITUTES
   `coverage` — story co-occurrence — and still answers 200. It tells you, in
   `applied_filters.coverage_fallback_applied` and `applied_filters.entity_match_note`: *"These rows
   are events in stories the entity appears in, not events the entity is a party to."* Most such
   rows will not name your entity anywhere in their own payload, and some of them are still right.
   Read the flag before you put the rows in front of anyone. The accepted values are `material`,
   `actor` and `coverage`; naming either of the first two **explicitly** returns
   `503 ENTITY_ATTRIBUTION_UNAVAILABLE` today rather than a substitution you did not ask for, which
   is the honest answer and the one to build against. Passing `entity_match=coverage` yourself
   returns the same rows as the default with `coverage_fallback_applied: false`, because you asked
   for co-occurrence instead of being handed it.
2. **A bare name instead of a resolved id** — different entity per endpoint.
3. **Mixed identifier spaces** — `e_…`, `wiki:…`, GEM ids, CIK, LEI are not interchangeable, and the
   accepted set differs by endpoint. The wrong one returns an empty result, not an error.
4. **`bbox` axis order** — latitude-first on events, stories, facilities, energy; longitude-first on
   maritime. Both orders are usually numerically valid, so a swap cannot error.
5. **Unbounded `geo_precision`** — precision `3` is a country centroid, which falls inside almost any
   box you draw. Pass `geo_precision_max=2` for site-level questions.
6. **Dropping incident identity while merging queries** — the Event surface serves the adjudicated
   incident view, but the same incident can still be returned by several entity/site queries. Merge
   on `incident.uid`, read `incident.resolution` before trusting it, and pass
   `incident_resolution=llm,self` to keep only groupings that were adjudicated.

Read `applied_filters` on every response. It echoes what the server actually used; a filter missing
from it was not applied. That one habit catches all six — and it is the only way to see the
`entity_match` substitution in (1) at all.

## When you need a value list

Never hardcode one from an example. Ask the `gdelt-cloud-docs` MCP server, or read
`/reference/enums` — every vocabulary is published and labelled **closed** (fixed), **observed**
(what the corpus currently holds, never exhaustive) or **identifier** (discovered through a call).

### Candidate identity and country evidence

Start identity lookup with `/api/v2/search?q=…&country_match=strict` (MCP `unified_entity_search`). Inspect the candidates and select the intended identity; never silently select an ambiguous first result. Reuse the returned entity ID in the relevant endpoint’s `entity=` parameter. `/api/v2/entities` discovers entities appearing in reporting within a date/geography/category scope; its legacy name search remains compatible.

Strict country matching requires known source association. It does not equate office country, citizenship, headquarters or reporting location. Explicit `country_match=include_unknown` broadens to candidates without country evidence. Missing/failed coverage is unknown, not zero; withheld source keys are omitted. Facility candidates use `type=facility` and return `facility_id`, separate from owner identity and nearby Events.
