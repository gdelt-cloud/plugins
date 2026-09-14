---
name: gdelt-cloud-core-api
description: Use this skill for ANY request that touches GDELT Cloud data — events, stories, summaries, entities, Situations (maintained collections of Stories and coded Events around one occurrence), country context and the Countries directory, publication activity, public office-holders, facilities, tone or share of voice — whenever the user describes something they want to build, monitor, chart, count or answer with it and it does not obviously belong to a narrower workflow skill. It maps a plain-English ask onto the right endpoint and the minimal correct call, including identity resolution before any destination call, so the first attempt returns real data instead of an empty 200.
---

# The Core API — which endpoint answers which question

These surfaces cover the common workflows. Pick by the **shape of the question**, not by keyword.

| The user is asking | Endpoint | Returns |
| --- | --- | --- |
| *What happened?* | `GET /api/v2/events` | Coded events: date, place, actors, taxonomy, metrics, fatalities |
| *How much / what shape?* | `GET /api/v2/events/summary` | Aggregated buckets — counts and metrics by date, country, category… |
| *What is the coverage saying?* | `GET /api/v2/stories` | Deduplicated news clusters with their source articles |
| *What are the themes?* | `GET /api/v2/stories/summary` | Story volume bucketed by date, country, category |
| *Which country and its context?* | `GET /api/v2/countries` and `/countries/{ISO3}` | Canonical country directory, reporting/publication activity and dated reference context |
| *Which developing thread?* | `GET /api/v2/situations` and `/situations/{uid}` | Maintained membership, dated evidence, graph samples and independent list totals |
| *Who is involved?* | `GET /api/v2/entities` | Resolved people, organizations, places with windowed metrics |
| *Where is the physical asset?* | `GET /api/v2/facilities` | Plants, mines, ports, pipelines, data centres — with coordinates |
| *How is X being talked about?* | `GET /api/v2/entities/{entity_id}/tone` | Sentiment for one entity over time, with evidence |
| *Who dominates the conversation?* | `GET /api/v2/share-of-voice` | One entity's share of a defined story population |

## One call, one Query Unit — page at 100

Standard reads cost 1 QU regardless of `limit`, so `limit=25` is four times the price of
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
   that has actually burned an evaluator. Entity matching is coverage through a linked Story: the
   entity appears in that Story, and the returned Events are carried by it. This does not establish
   that the entity acted in or was materially involved in the Event. Omit `entity_match` to inherit
   the API default, or explicitly pass its only supported value, `coverage`. Do not invent a
   material- or actor-attribution mode; the public contract does not offer one.
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
from it was not applied. That one habit catches all six and keeps coverage evidence labelled as
coverage rather than attribution.

## When you need a value list

Never hardcode one from an example. Ask the `gdelt-cloud-docs` MCP server, or read
`/reference/enums` — every vocabulary is published and labelled **closed** (fixed), **observed**
(what the corpus currently holds, never exhaustive) or **identifier** (discovered through a call).

### Candidate identity and country evidence

Start identity lookup with `/api/v2/search?q=…&country_match=strict` (MCP `unified_entity_search`). Inspect the candidates and select the intended identity; never silently select an ambiguous first result. Reuse the returned entity ID in the relevant endpoint’s `entity=` parameter. `/api/v2/entities` discovers entities appearing in reporting within a date/geography/category scope; its legacy name search remains compatible.

Strict country matching requires known source association. It does not equate office country, citizenship, headquarters or reporting location. Explicit `country_match=include_unknown` broadens to candidates without country evidence. Missing/failed coverage is unknown, not zero; withheld source keys are omitted. Facility candidates use `type=facility` and return `facility_id`, separate from owner identity and nearby Events.

## Countries, public officials and Situations

- `/api/v2/countries?directory=true&sort=name` enumerates the canonical ISO-3 registry, including
  quiet countries. Use `q`, `country`, `region`, `continent`, `limit` and `offset` for directory
  discovery; `sort=events` or `stories` is optional activity sorting. Country profiles and place
  entity records are different resources; never manufacture an entity ID from an ISO code.
- Country `basis=reporting` counts distinct Events by occurrence date and Stories by reporting
  date. The default `basis=publication` preserves additions/updates; `time_basis` chooses published
  or recorded time within that publication layer. Reporting has day precision, so do not request
  hourly reporting counts. Country counts can overlap and do not sum to a global distinct total.
- Country context exposes source availability. Keep economic units, observation periods and
  vintages distinct from reporting dates. Office valid-time queries use a separately labeled
  `as_of`; missing term dates do not establish a holder on that day.
- Resolve a person through `/search?type=person&holds_office=true`. Public official is an
  evidence-backed role, not an entity type. Reuse the person's canonical ID and existing entity
  URLs. Office identity belongs to `/offices`; holder history is `/offices/{id}/holders` and
  `/entities/{id}/offices`. Keep current, former/ended, unknown and unavailable distinct.
  Publisher rosters have measured but incomplete source/country and identity coverage. Office
  jurisdiction is not citizenship; an office badge is not a risk or screening assessment.
- Situation discovery accepts `entity`, `story_id` and `event_uid`. Entity and geographic/category
  filters need a reporting range of at most 30 days. `selected_scope` and `category_summaries`
  describe that range; `totals` describe lifetime membership. Recent ordering uses evidence dates
  and genuine first-observed timestamps, never settle freshness or lifetime article totals.
- Page `/situations/{uid}/stories`, `/events`, `/entities` and `/connections` independently, retaining
  dates and each list's `scope_version`. On scope-change 409, restart that list at offset 0.
  Connections carry membership decisions and provenance; graph samples never limit list totals.
  For a drawable detail graph, request `include=edges` (MCP `get_situation` takes
  `include=["edges"]`). Edges can reference Stories outside the current detail page; page
  member Stories before drawing those nodes and inspect graph caps. Connections explain
  membership decisions, whereas detail edges describe pairwise graph relationships.
  MCP Situation member-list tools currently take `story_id` for a Situation UID (not
  `situation_uid`) and a maximum page limit of 100. Read the current schema and page;
  do not invent aliases or request oversized pages.
- Public `/country/{ISO3}` and `/situations/{uid}` show immutable daily editions with cutoff and
  publication time. Signed-in `/view/country/{ISO3}` and `/view/situations/{uid}` are live.

**Creating a shared Situation is a write.** Inspect `create_situation`, then call
`gdelt_cloud_tool_write` with a Story or Event seed and one stable `idempotency_key`. Explain the
5 QU creation/expansion price before execution; paid subscribers and active trials qualify.
Existing canonical membership is reused for 0 QU. An ambiguous Event returns supporting Stories:
ask which Story to use instead of silently choosing one. Retain the same key and body across an
uncertain retry; never issue a new key merely because the first call timed out. The API reserves
and refunds quota; MCP does not add a separate read charge.

Expired Free accounts keep signed-in browsing with QU after the trial and optional extension;
programmatic REST/OAuth/MCP, Monitors and data exports require subscription. Preserve saved
configurations and surface the subscription indicator. Never claim the trusted UI exemption from
a customer request header or convert an access-service error into permission to proceed.
