---
name: gdelt-cloud-core-api
description: Use this skill for ANY request that touches GDELT Cloud data — events, stories, summaries, entities, facilities, tone, or share of voice — whenever the user describes something they want to build, monitor, chart, count, or answer with it, and the request does not obviously belong to one of the narrower workflow skills. It maps a plain-English ask onto the right endpoint and the minimal correct call, so the first attempt returns real data instead of an empty 200.
---

# The Core API — which endpoint answers which question

Seven surfaces cover almost everything. Pick by the **shape of the question**, not by keyword.

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

## Always start here

```
GET /api/v2/search?q=<name>&universe=all
```

Almost every interesting question is about a *thing* — a company, a country, a port. Resolve it once,
keep the `e_…` id, reuse it everywhere. Filtering by a bare name across two endpoints gets you two
different entities and no error. This is the single most common way a first build goes silently wrong.

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

**Entities — who.** `search` resolves by name; the metrics are scoped to the window and to any
filter you pass, and `metrics_scope` in the response tells you which.

```
GET /api/v2/entities?search=Chevron&type=organization&days=30
```

**Facilities — the physical layer.** `has_geo=true` when you intend to map or bbox them.

```
GET /api/v2/facilities?country=Indonesia&type=mine&has_geo=true&limit=100
```

**Tone — how an entity is being talked about.** Needs a resolved id and a date window; `group_by`
gives you the series, `include_evidence` gives you the stories behind each point.

```
GET /api/v2/entities/e_12345/tone?days=30&group_by=date&include_evidence=true
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

## Five things that return 200 and are wrong

1. **A bare name instead of a resolved id** — different entity per endpoint.
2. **Mixed identifier spaces** — `e_…`, `wiki:…`, GEM ids, CIK, LEI are not interchangeable, and the
   accepted set differs by endpoint. The wrong one returns an empty result, not an error.
3. **`bbox` axis order** — latitude-first on events, stories, facilities, energy; longitude-first on
   maritime. Both orders are usually numerically valid, so a swap cannot error.
4. **Unbounded `geo_precision`** — precision `3` is a country centroid, which falls inside almost any
   box you draw. Pass `geo_precision_max=2` for site-level questions.
5. **Counting rows as incidents** — `event_id` identifies a coded *story*. Group on `incident.uid`
   and read `incident.resolution` before trusting it.

Read `applied_filters` on every response. It echoes what the server actually used; a filter missing
from it was not applied. That one habit catches all five.

## When you need a value list

Never hardcode one from an example. Ask the `gdelt-cloud-docs` MCP server, or read
`/reference/enums` — every vocabulary is published and labelled **closed** (fixed), **observed**
(what the corpus currently holds, never exhaustive) or **identifier** (discovered through a call).
