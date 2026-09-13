---
name: gdelt-cloud-getting-started
description: Use this skill whenever the user mentions GDELT Cloud at all — before the first API call in a project, and whenever they describe anything they want to build, monitor, chart, count or answer using events, stories, summaries, entities, Situations, country context and the Countries directory, publication activity, public office-holders, facilities, tone or share of voice. It carries the orientation and the conventions that decide whether a call is correct, because almost every filter that is wrong in an interesting way returns HTTP 200 with the wrong data rather than an error. Pair it with gdelt-cloud-core-api, which maps the ask onto an endpoint, including the trial and what a Free account keeps after it.
---

# Building on GDELT Cloud — read this before your first call

**Who this is for.** Three jobs, and none of them is clicking around a web app:

1. **Building software against the REST API** — `https://gdeltcloud.com/api/v2`, an API key, and
   whatever language you are in. Most of what follows is about getting these calls *right*.
2. **Building an agent on the MCP server** — the same data as tools, with progressive discovery so
   a large surface does not eat your context. See `gdelt-cloud-building-with-the-api`.
3. **Answering questions conversationally** in a chat client that can reach an MCP server
   (ChatGPT, Claude, Cowork). The same rules apply; you just call the tools instead of writing
   the requests. Note that some chat clients' connector UIs have no field for an API key, so that
   path may reach only the unauthenticated docs server — check what you are actually connected to
   before concluding a dataset is empty.

GDELT Cloud is a clean event database over the world's news. It is **not** raw GDELT — we ingest
the public GDELT article stream as one input and never their coded output. Events are coded here,
from clustered news stories, into a CAMEO+ / ACLED-aligned taxonomy; entities are resolved to one
identity spine across news, SEC filings, sanctions lists and asset registries; and every number
traces back to the articles behind it.

## Orient yourself first — six nouns and one spine

Everything in the API is built from six nouns, and they compose in one direction:

**Article → Story → Event**, with **Entity**, **Facility** and **Metric** hanging off them.

- **Article** — one news item from one publisher. Evidence, not a claim.
- **Story** — a cluster of articles covering the same development. Deduplicated by embedding
  retrieval plus an LLM that adjudicates every candidate pair.
- **Event** — one discrete coded thing that happened or was said, with a date, a place, actors and
  metrics. One Story can yield several Events. This is the claim we stand behind.
- **Entity** — a resolved person, organization or place, stable across sources.
- **Facility** — a physical asset: plant, mine, port, pipeline, data centre.
- **Metric** — a number scored onto an Event by a published rubric.

**Two surfaces.** The **Core API** is events, stories and entities — the coded news layer described
above. The **Open Feeds** are independent public datasets loaded on the same identity spine so you
can join them to the news: SEC filings, US federal awards and FARA, sanctions and debarment
screening lists, energy and heavy-industry asset registries, vessel positions, FRED macro series,
AI compute. The join key is the entity id, which is why rule 1 below matters more than any other.

**Freshness.** The pipeline is continuous, not a nightly batch: articles are ingested, clustered and
coded **hourly**, and the daily snapshots the API reads are rebuilt **every 30 minutes**. Today's
numbers are still moving — end a window yesterday if you need day-over-day stability. Every
`/api/v2/events` response carries `meta.settled_at`, so you never have to guess how fresh a number
is. Cadence per layer: `/concepts#how-fresh-is-it`.

**Where the values live.** Never hardcode a value list from an example. Every vocabulary the API
validates against is published at `/reference/enums`, and each is labelled **closed** (fixed — safe
to switch on), **observed** (what the corpus currently holds — never exhaustive) or **identifier**
(discovered through a call, never enumerated). Treating an observed list as closed is the most
common way to build a filter that silently misses data. The map of which reference page answers
which question is at `/reference/index`.

**The whole risk in this API is the confident wrong answer.** Almost every filter that is wrong in
an interesting way returns `200` with a plausible-looking result set. Twelve rules below prevent that.
Follow them and your first build will be correct; skip them and it will look correct.

## Setup

```
Base URL   https://gdeltcloud.com/api/v2
Auth       Authorization: Bearer gdelt_sk_...
Keys       https://gdeltcloud.com/api-keys   (programmatic access during evaluation or on paid/Academic plans)
```

New accounts get a 7-day evaluation with 1,000 QU, REST API and MCP access, and up to three daily
email Monitors. Bulk downloads remain paid-only. After the evaluation, Free keeps the web app and
API Arena with 50 QU a month plus one daily email Monitor; API keys, OAuth, MCP, Monitor webhooks
and bulk downloads require a paid plan. Eligible existing personal workspaces can claim a one-time
500 QU grant valid for 7 days.

Verified Academic & Research accounts get permanent no-cost access with 5,000 QU a month, API and
MCP access, five daily Monitors, Monitor webhooks, bulk downloads, and every data surface; Briefs are
excluded.

Two MCP servers are wired by this plugin. `gdelt-cloud` is the data; `gdelt-cloud-docs` is the
documentation. When you need a parameter, a value list, or a response shape, **ask `gdelt-cloud-docs`
rather than guessing** — its `query_docs_filesystem_gdelt_cloud` tool can slice the OpenAPI spec
directly, which is far cheaper and more exact than a prose search:

```
jq '.paths."/api/v2/events".get.parameters[] | {name, description}' openapi-v2.json
```

## The twelve rules

**1. Resolve an entity once, then reuse the id.**
`GET /api/v2/search?q=<name>&type=<person|organization|place|facility>&country_match=strict&limit=10`
returns lexical identity candidates (MCP `unified_entity_search`). Refine with `country`, `type`,
and `holds_office=true` for people with published office evidence. Strict country matching uses
known source association; `country_match=include_unknown` explicitly broadens it.
Inspect match explanations and country evidence, then select the intended candidate. Preserve its
returned `entity_id` (`e_…`, `wiki:…` or `llm:…`) for endpoints that accept that identifier space.
Facilities retain a separate `facility_id`; unlinked source records have no entity ID to reuse.
Never select a candidate just because it ranks first or resolve the same bare name separately
on several endpoints.

**Use the destination endpoint's documented identifier parameter.** `entity` is the recommended
spelling on the reporting and record endpoints that declare it. Some aggregate contracts use a
plural canonical parameter: `/share-of-voice` declares `entities`, with singular compatibility
aliases. Read `/reference/parameters#identifier-parameters` and `applied_filters` rather than
assuming a parameter or a multi-ID format transfers unchanged to another endpoint.

**2. Identifier spaces are not interchangeable, and the wrong one returns an empty 200.**
A spine `e_…` id, a news `wiki:…` id, a GEM entity id, a CIK, an LEI and a SAM.gov UEI are
different things, and the set each endpoint accepts differs by endpoint. `/gov/fara` takes `e_…`
alone. `/gov/awards` also takes `cik:` and rejects bare names. `/exposure` also takes `llm:`.
`/energy/assets` has an `owner_entity_id` that is a **GEM** id, while `/facilities` uses that same
spelling for a spine alias. Check the identifier table in
`/reference/parameters#identifier-parameters` before chaining two endpoints.

Reuse the exact selected identifier for each endpoint that documents support for its space.
A returned terminal `e_…` is useful across many sources, but never invent one for a `wiki:…` or
`llm:…` candidate. A source-specific leg may require a CIK, GEM owner ID or LEI; use its documented
identifier from the candidate evidence, or mark that leg unavailable.

**3. A `/summary` endpoint is close to its list sibling, but not identical.**
Count before you list. `/events/summary` takes most of the list's filters — `days`, `date`,
`date_start`/`date_end`, `entity`, `country_match`, `geo_precision_max` — and not the list-only
concerns `search`, `sort` and `cursor`. An unknown parameter lands in `applied_filters.ignored`
rather than 400ing, so a summary and a list CAN describe different populations while both return
200. Compare `applied_filters` on both, and read the exact per-endpoint parameter set from
`/reference/endpoints` or the OpenAPI spec through the docs MCP. Do not memorise a count: the two
lists move independently, which is the whole reason this rule exists.

**4. `bbox` axis order differs by family.**
Events, stories, facilities and energy take **latitude first** (`lat_min,lon_min,lat_max,lon_max`).
The maritime endpoints take **longitude first** (`min_lon,min_lat,max_lon,max_lat`). For most real
boxes both orders are numerically valid, so a swap cannot error — it silently queries a different
part of the planet.

**5. "In a country" and "connected to a country" are different questions.**
`country=` defaults to the wide sense, which includes events elsewhere involving an actor from that
country. For events that actually happened there, pass `country_match=location`.

**6. Bound `geo_precision` when you mean "at this place".**
A precision of `3` is a country or region centroid. Inside a bounding box drawn around a site, every
country-centroid event in that country will match. For Singapore, Bahrain or Taiwan the centroid is
inside essentially any box you would draw. Pass `geo_precision_max=2` for site-level questions.

**7. `null` is not `0`.**
A null means we did not measure it, and charting it as zero fabricates data. This applies to every
metric and to `fatalities`, which only the conflict family publishes.

**8. Read `applied_filters` on every response.**
It echoes what the server actually used, under canonical names. A filter you passed that is missing
from it was not applied. This is the fastest way to catch rules 2, 3 and 5 going wrong.

**9. Bound every query by date, and know where history starts.**
Windows are capped on most endpoints, and consistently coded history begins in **March 2026** —
earlier dates return a near-empty result that reads like a bug and is not. Both the cap and the
start move as coverage is backfilled: the caps are per-endpoint at `/reference/endpoints`, and the
earliest date a surface can answer for is at `/metrics/limits`. If you want the corpus as files
rather than pages of JSON, see "Bulk downloads" below.

**10. `count()` over events is not an incident count — read `incident`.**
An event's `id` identifies a CODED STORY. One real-world incident covered by two story clusters is
coded twice, so counting rows over-counts incidents and summing `fatalities` double-counts the dead.
Every event card carries an `incident` block: group or count on `incident.uid` instead of `id`.
Adjudication is partial by design — a minority of events on any given day, because only events
that were CANDIDATES for a duplicate are ever compared — so pass `incident_resolution=llm,self`
when you need the subset where `incident.uid` is a trustworthy grouping key. Do not plan around a
fixed share; count `incident_resolution` yourself over your own window if the ratio matters.
**Always read `incident.resolution` before trusting it** — `llm` means a judge confirmed a duplicate
and `uid` names the survivor; `self` means a judge looked and found none; `unadjudicated` means
nothing ever compared this event to anything and `uid` is a fallback, not a verdict. `unadjudicated`
is the honest majority: only events that were candidates for a duplicate are ever adjudicated.
Nothing is deleted either way — the duplicate keeps its own id and stays retrievable.

**11. A call costs the same whatever `limit` you pass — so always page at the maximum.**
A `/api/v2` call is charged per CALL, not per row, so `limit=25` is not cheaper than `limit=100`:
it is four times more expensive for the same data. An MCP tool call costs more than a REST call.
Ask `GET /api/v2/meta/query-units` for the current rates and your own burn rather than assuming
either number, and read the `x-quota-cost` header to see what a call actually cost. Size a build
as (plan QU) ÷ (calls per subject per month) — a subject refreshed hourly is ~730 calls — and
treat `QUOTA_EXCEEDED` as a sizing problem, not a retry problem.

**12. Search in the language the story was written in.**
Non-English coverage is one of the strongest things here — Spanish, Arabic, Chinese, Portuguese and
more — and an English query will not find it. Two separate levers: `languages=` filters by the
source language of the coverage (`languages=it,de`), and the semantic `search` string should itself
be written in the language of the press you are searching. Asking for Italian regulatory news in
English returns thin, off-topic results that look like a coverage gap and are not; the same window
asked in Italian returns the national press. If a topic looks absent, try it in its own language
before concluding anything.

## Bulk downloads — when you want the corpus, not a page of it

Paging `/events` in 30-day windows to build a local frame is the wrong tool for a backfill, and it
is the expensive one: every page is a charged call. The same coded events are published as files.

```
GET /api/v2/bulk/files                     # the manifest: dataset, period, format, rows, sha256
GET /api/v2/bulk/files/{file_id}/url       # a short-lived signed download URL
```

One file per calendar month plus a rolling full-history file, in Parquet and gzipped CSV with
identical rows and column names. Prefer Parquet: a null stays a null and an array stays a list.
In CSV an empty field IS a null and array columns are JSON — parse them with a JSON reader, not by
splitting on a delimiter. Every file publishes a `sha256`, a byte size and a row count; check the
digest before loading. Full column reference: `/data/bulk-events-schema`.

Two things to know before you plan around it. **It is gated** — bulk export is included on the
Intelligence, Enterprise and Academic plans, and a key without it gets a `403`, not an empty list.
And **it is early**: history is not fully backfilled and completeness varies by period, which is
why every manifest row carries a per-month settled-day count. Read that count rather than assuming
a month is whole.

## The shape of a first build

```python
import os, httpx

BASE = "https://gdeltcloud.com/api/v2"
H = {"Authorization": f"Bearer {os.environ['GDELT_API_KEY']}"}

with httpx.Client(timeout=60, headers=H) as c:
    # 1. Shape of the period — where is the volume?
    summary = c.get(f"{BASE}/events/summary", params={
        "country": "Nigeria",
        "date_start": "2026-07-15",
        "date_end": "2026-08-13",
        "group_by": "category",
    }).json()

    # 2. Drill into the buckets that carried volume. NOTE the extra filters
    #    that only exist on the list endpoint.
    events = c.get(f"{BASE}/events", params={
        "country": "Nigeria",
        "country_match": "location",
        "category": summary["data"][0]["key"],
        "date_start": "2026-07-15",
        "date_end": "2026-08-13",
        "sort": "significance",
        "limit": 50,
    }).json()

    assert "country_match" in events["applied_filters"], events["applied_filters"]

    # 3. Every event carries its evidence.
    #    The card's key is `id`. `event_id` is the PATH-parameter name in the docs, not a field —
    #    reading e["event_id"] raises KeyError.
    for e in events["data"][:5]:
        stories = c.get(f"{BASE}/events/{e['id']}/stories").json()
        print(e["event_date"], e["category"], e["title"], "→", len(stories["data"]), "stories")
```

## Errors

Read the `code`, not just the status. `RATE_LIMITED` and `QUOTA_EXCEEDED` are both `429` and call for
opposite responses — back off and retry versus stop and tell the user. The full code list is at
`/reference/errors`.

## When you are stuck

Ask the `gdelt-cloud-docs` MCP server. If the docs are wrong or missing something, its `submit_feedback`
tool reaches a human. Do not guess a parameter name — the server rejects unknown filters into
`applied_filters.ignored`, and a guess becomes a silent wrong answer rather than an error.

## Explore and access

Explore starts with Stories and also offers Events, Entities, Facilities and a searchable Countries
directory. Atlas Today defaults to distinct coded Event activity for the current UTC day. Use
reporting/publication labels and keep macro observation years and office as-of dates intact.
Public officials are person entities distinguished by published office evidence, not a separate
kind of person page. Countries and Situations have public frozen daily editions and live signed-in
views. Open linked evidence in new tabs while retaining the selected dates and time basis.

A new account starts a 7-day evaluation with 1,000 QU and every dataset over the API and MCP, with
one optional 7-day extension on request. Afterwards the Free plan continues in the web app with
50 QU a month, including Atlas, but customer REST keys, OAuth/MCP, Monitor execution and exports
pause until you subscribe. Keys and Monitor settings remain saved. Every Free account can claim a
one-time 500 QU grant, valid 7 days from activation, announced by email — so a key that answers
`403 PROGRAMMATIC_ACCESS_DENIED` after the evaluation is a plan state, not a broken key.
Paid subscribers and active trials can create shared Situations for 5 QU; canonical reuse costs
0 QU and retries reuse the original idempotency key. See the core API skill before this write.
