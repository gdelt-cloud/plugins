---
name: gdelt-cloud-getting-started
description: Use this skill whenever you are about to call the GDELT Cloud API for the first time in a project, or when the user asks to build anything on GDELT Cloud events, stories or entities. It carries the conventions that decide whether a call is correct — identifier spaces, geographic filters, date windows, the summary/list gap — because getting these wrong returns HTTP 200 with the wrong data rather than an error.
---

# Building on GDELT Cloud — read this before your first call

GDELT Cloud is a clean event database over the world's news. It is not raw GDELT: events are
coded in-house from clustered news stories into a CAMEO+ / ACLED-aligned taxonomy, entities are
resolved to one spine across news, filings, sanctions lists and asset registries, and every number
is traceable to the articles behind it.

**The whole risk in this API is the confident wrong answer.** Almost every filter that is wrong in
an interesting way returns `200` with a plausible-looking result set. Nine rules below prevent that.
Follow them and your first build will be correct; skip them and it will look correct.

## Setup

```
Base URL   https://gdeltcloud.com/api/v2
Auth       Authorization: Bearer gdelt_sk_...
Keys       https://gdeltcloud.com/api-keys   (free plan reads every dataset)
```

Two MCP servers are wired by this plugin. `gdelt-cloud` is the data; `gdelt-docs` is the
documentation. When you need a parameter, a value list, or a response shape, **ask `gdelt-docs`
rather than guessing** — its `query_docs_filesystem_gdelt_cloud` tool can slice the OpenAPI spec
directly, which is far cheaper and more exact than a prose search:

```
jq '.paths."/api/v2/events".get.parameters[] | {name, description}' openapi-v2.json
```

## The nine rules

**1. Resolve an entity once, then reuse the id.**
`GET /api/v2/search?q=<name>&universe=all` is the resolver the rest of the API assumes you called.
It returns candidates; you pick one and keep its spine `e_…` id. Never filter by a bare company or
person name across more than one endpoint — you will get a different entity on each.

**2. Identifier spaces are not interchangeable, and the wrong one returns an empty 200.**
A spine `e_…` id, a news `wiki:…` id, a GEM entity id, a CIK, an LEI and a SAM.gov UEI are
different things, and the set each endpoint accepts differs by endpoint. `/gov/fara` takes `e_…`
alone. `/gov/awards` also takes `cik:` and rejects bare names. `/exposure` also takes `llm:`.
`/energy/assets` has an `owner_entity_id` that is a **GEM** id, while `/facilities` uses that same
spelling for a spine alias. Check the identifier table in
`/reference/parameters#identifier-parameters` before chaining two endpoints.

**3. A `/summary` endpoint is not a rollup of its list sibling.**
Count before you list — but `/events/summary` accepts neither `days` nor `date`, and also drops
`entity`, `country_match`, `geo_precision_*`, `near`, `search`, `sort` and `cursor`. It takes
`date_start` / `date_end`. An unknown parameter lands in `applied_filters.ignored` rather than
400ing, so a summary and a list can describe different populations while both return 200. The full
per-endpoint gap is at `/reference/endpoints#summary-endpoints-take-fewer-parameters`.

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
Windows are capped (30 days on most endpoints) and consistently coded history begins **March 2026**.
Earlier dates return a near-empty result that reads like a bug and is not.

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
    for e in events["data"][:5]:
        stories = c.get(f"{BASE}/events/{e['event_id']}/stories").json()
        print(e["event_date"], e["category"], e["title"], "→", len(stories["data"]), "stories")
```

## Errors

Read the `code`, not just the status. `RATE_LIMITED` and `QUOTA_EXCEEDED` are both `429` and call for
opposite responses — back off and retry versus stop and tell the user. The full code list is at
`/reference/errors`.

## When you are stuck

Ask the `gdelt-docs` MCP server. If the docs are wrong or missing something, its `submit_feedback`
tool reaches a human. Do not guess a parameter name — the server rejects unknown filters into
`applied_filters.ignored`, and a guess becomes a silent wrong answer rather than an error.
