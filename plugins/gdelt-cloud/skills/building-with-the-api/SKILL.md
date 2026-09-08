---
name: gdelt-cloud-building-with-the-api
description: Use this skill when writing CODE against GDELT Cloud rather than answering a one-off question — building an app, dashboard, monitor, scheduled job, notebook or ETL that calls /api/v2 repeatedly. It covers walking a result set to the end, telling a truncated page from a genuinely empty one, getting a time series when the endpoint you want will not give you one, caching and refresh cadence, and the failure modes that return HTTP 200. Pair it with gdelt-cloud-getting-started, which covers whether a single call is CORRECT; this one covers whether a BUILD is.
---

# Building an app on GDELT Cloud

`getting-started` tells you whether one call is correct. This tells you what changes when you make
the same call every hour, page through all of it, and put the result in front of someone.

**The theme is the same and it is worth restating: the dangerous failure is HTTP 200.** In a build,
it has a second form — a call that is correct today and wrong at scale, because you took one page
for the whole answer.

Before adding a polling job, check `gdelt-cloud-hosted-monitors`. One recurring Event/Story question
with hourly/daily cadence and email or signed-webhook delivery belongs in a Hosted Monitor; scheduled
checks consume no Query Units. Keep the client build when it needs multiple endpoints, private joins,
custom state/baselines, complete historical exports, or a different schedule.

## 1. Pagination: walk with the cursor, and trust only `next_cursor`

List endpoints are cursor-paged. `limit` is capped (100 on events, 100 on stories), so **any question
whose answer might exceed 100 rows needs a walk, not a bigger limit.**

```python
def walk(client, path, params, cap=5000):
    """Yield every row, not just the first page. `cap` is a deliberate ceiling — say what you
    dropped rather than looping forever on a window you misjudged."""
    cursor, seen = None, 0
    while True:
        page = client.get(path, params={**params, **({"cursor": cursor} if cursor else {})}).json()
        rows = page["data"]
        yield from rows
        seen += len(rows)
        cursor = page["pagination"]["next_cursor"]
        if cursor is None or seen >= cap:
            if cursor is not None:
                print(f"WARNING: stopped at {seen} rows with more available")
            return
```

**`next_cursor` is the truncation signal. Row count is not.**

```python
if len(rows) >= limit:   # WRONG — a full page can be the last page
if page["pagination"]["next_cursor"] is not None:   # RIGHT
```

The server fetches one row beyond your page to decide this, so `next_cursor is None` means *there
are no more rows*, not *probably none*. The count heuristic fails in both directions: a final page
that happens to be exactly `limit` long looks truncated, and a page shortened by de-duplication looks
final when it is not.

**Cursors are opaque.** Copy `pagination.next_cursor` verbatim. Do not parse it, add to it, or build
one by hand — on a snapshot read it encodes which snapshot you are walking, and a hand-made offset
silently restarts you against a different one.

**Want the denominator?** Pass `include_total=true` and read `pagination.estimated_total`. It is
opt-in because it costs a second scan, so ask for it on the first page and not on every one:

```python
first = client.get("/events", params={**params, "include_total": "true"}).json()
total = first["pagination"].get("estimated_total")   # None on a `search=` request — see §3
```

## 2. Empty, truncated, or filtered away — three different results

An empty `data` array has three causes and they need different responses. Distinguish them before
reporting "no activity":

| What you see | What it means | What to do |
|---|---|---|
| `data: []`, filters all echoed in `applied_filters` | Genuinely no coverage for that combination | Report zero coverage, never "no events happened" |
| `data: []`, a filter missing from `applied_filters` | The server did not apply it | Fix the parameter name — you are looking at an unfiltered answer that happened to be empty |
| `data: []`, something in `applied_filters.ignored` | The server did not recognise it | Same — a typo, or a parameter that does not exist on this endpoint |
| Full page, `next_cursor` non-null | Truncated | Walk it (§1) |

```python
def explain_empty(resp, sent):
    ap = resp["applied_filters"]
    missing = [k for k in sent if k not in ap and k not in ap.get("ignored", {})]
    if missing:
        raise ValueError(f"filters not applied: {missing} — this result is not what you asked for")
    if resp.get("note"):
        print(resp["note"])   # the server explains its own empty pages
```

Responses carry a `note` on an empty result saying what it means. Read it — it is cheaper than
guessing.

## 3. `search=` and `/summary` do not compose — bucket client-side

`/events/summary` **rejects** `search=` with a 400. This is deliberate: semantic retrieval ranks a
bounded candidate pool, and an aggregate over a pool is not an aggregate over the corpus. The
consequence for a build is real, so plan for it: **there is no server-side time series for a semantic
query.** Walk the list and bucket in your own code.

```python
from collections import Counter
rows = list(walk(c, "/events", {"search": "port congestion", "date_start": ..., "date_end": ...}))
series = Counter(r["event_date"] for r in rows)
```

Two things follow. `pagination.estimated_total` is `null` on a `search=` request for the same reason
— any number there would describe the candidate pool. And `search_score` is your precision lever:
semantic retrieval is deliberately broad, so threshold it rather than assuming every hit is relevant.

```python
strong = [r for r in rows if (r.get("search_score") or 0) >= 0.55]
```

`match_type` tells you which arm found the row: `semantic` (embedding distance, carries a
`search_score`) or `name` (literal match, `search_score` is `null` — a name hit has no computed
distance, and the API will not invent one). The key is absent entirely on non-search requests.

For a structured time series, use `/events/summary?group_by=date` with structured filters. It is one
call instead of a walk.

## 4. Identifiers, and the two fields that look alike

- An event card's key is **`id`**. `event_id` is the name of the PATH parameter
  (`/events/{event_id}/stories`), not a field on the card. `e["event_id"]` raises `KeyError`.
- `id` identifies a **coded story**, not a real-world incident. Group on `incident.uid` to count
  incidents, and pass `incident_resolution=llm,self` to restrict to the rows where that grouping was
  actually adjudicated — coverage is partial by design.
- `subcategory` is the **filter value** (`"EC04"`, or an ACLED sub-event type like
  `"Peaceful protest"`). `subcategory_label` is the human name (`"Trade Policy Action"`). Display the
  label; filter on the code. The same split applies to `group_by=subcategory` buckets: `key` is what
  you send back, `label` is what you show.

## 5. Caching and cadence

The pipeline is continuous. Articles are ingested, clustered and coded hourly; the snapshots the API
reads are rebuilt every 30 minutes. So:

- **Cache by window, and never cache today.** A closed historical window is stable and can be cached
  hard. Today's numbers are still moving.
- **End your window yesterday** for anything a user will compare day-over-day.
- **`meta.settled_at`** tells you when the snapshot behind the response was built — use it as your
  cache key rather than wall-clock time.
- **Poll on a schedule, not a loop.** Rate limits are per-minute and per-plan; a 429 with code
  `RATE_LIMITED` means back off and retry, and `QUOTA_EXCEEDED` means stop and tell the user. Same
  status, opposite responses — read `code`, and read `details.retry_after`.

## 6. What a call costs, and the one lever that matters

Every `/api/v2` call is **1 Query Unit whatever `limit` you pass**; an MCP tool call is 5. Discovery
calls are free. That single fact decides more about a plan's cost than anything else in this
document, because it inverts the intuition: `limit=25` is not cheaper than `limit=100`, it is
**four times more expensive** for the same rows.

- **Always page at `limit=100`.** Then walk the cursor as in section 1.
- **Prefer `/summary` to counting a list.** One bucketed call answers what a full walk would cost
  dozens of QU to answer.
- **Read `x-quota-cost` on the response**, and your position with
  `GET /api/v2/meta/query-units`.
- **Size before you build.** One thing kept current at hourly refresh costs roughly 750 QU a month,
  so a plan's QU divided by 750 is the number of things you can keep current. `QUOTA_EXCEEDED` is a
  sizing problem, not a retry problem — see section 5 for why it is not `RATE_LIMITED`.

## 7. What will change under you, and how to check it

Do not hardcode the notice period from this file — read it. `GET /api/v2/meta/endpoints` carries a
`stability_policy` block beside the endpoint inventory it governs, so an integration can assert its
own assumptions instead of trusting a web page:

```
stability_policy.breaking_change_notice_days   <days>
stability_policy.alias_compatibility_days      <days>
stability_policy.changes_without_notice        [ … ]
```

The two day counts are deliberately not written out here. This section previously printed them,
directly under the sentence telling you not to hardcode them — read the response, and the policy
in prose at `/reference/stability`.

The last one is the part that decides how you write your parser. A new endpoint, a new optional
parameter and **a new field in a response body** all ship without notice — so parse permissively; an
unrecognised field is not an error. So does widening what a parameter accepts, and adding a value to
an OPEN vocabulary. A **closed** enum gaining a value is announced. And corrected data is not a
breaking change: a score or count that was wrong is fixed as soon as it is known, which is why
section 2's advice to end a comparison window yesterday matters more than any version pin.

## 8. A checklist before you ship

- [ ] Every list read either walks to `next_cursor is None` or states the cap it stopped at
- [ ] No `len(rows) >= limit` truncation checks anywhere
- [ ] `applied_filters` is asserted, not assumed, for every filter that matters
- [ ] Empty results are reported as *no coverage*, never as *nothing happened*
- [ ] `null` metrics are rendered as gaps, never charted as `0`
- [ ] Windows are bounded and end yesterday if the number is compared over time
- [ ] Entity ids are resolved once and reused; no bare names crossing endpoints
- [ ] 429 handling branches on `code`, not on the status
- [ ] Response parsing tolerates unrecognised fields — new ones ship without notice (section 7)

## Creation receipts and Monitor checkpoints

`POST /api/v2/situations` accepts a Story or Event seed and requires `Idempotency-Key` for admitted
work. Persist the key before sending, reuse it with the same body after timeout, and retain the
returned canonical UID. Admitted work costs 5 QU; canonical reuse costs 0. Failed work releases
its quota reservation. Event ambiguity is a 409 requiring explicit supporting Story selection.
Do not infer successful completion from a connection drop or start another charged attempt.

Query Monitors persist filters plus original discovery provenance. Scheduled matching is a
half-open interval of newly committed publication evidence since the previous complete checkpoint,
not a rolling reporting-date window. First enablement starts without delivering preview history;
7/30-day previews are separate. Late arrivals retain their original occurrence/reporting dates.
Continue incomplete pagination within the original interval, deduplicate by stable identity, and
advance the checkpoint only after the whole interval has been processed.

## Build anything: first principles

The four sections below are the rules that hold across EVERY endpoint, so a build that the skills
above do not describe can still be derived correctly. Each one is a place a plausible HTTP 200 hides.

**Served, not raw.** Every read answers from settled serving tables, and the response says which
(`meta.row_source`, `meta.settled_at`, and on the activity journal `meta.coverage.window_complete`
plus `meta.exhaustive`). A `null` is *unmeasured* — an unknown `linked_event_count`, a withheld
source count, a country with no returned row — and is never a zero. Read the coverage block before
counting anything, and render a null as a gap.

**Three clocks.** A Story carries a *reporting* date (when coverage was assembled), an Event carries
an *occurrence* date (when the thing happened), and the publication journal carries *published*,
*recorded* and *source* dates (when a record entered our serving layer, versus what it says about
itself). Pick the clock explicitly — `time_basis=recorded` on `/api/v2/activity` for "what arrived
since my last check", occurrence dates on Events for "what happened that week" — and say which one a
number is measured on. A Situation's `origin` is the earliest member with material coverage, not the
true beginning.

**Resolve before you discover.** Every destination endpoint that takes `entity` wants the id that
`GET /api/v2/search?q=<name>&country_match=strict` returned, after you inspected the candidates
and chose one. Reuse that id across Events, Stories, Situations, activity and offices; never let a
bare name cross an endpoint boundary, and never take the first candidate by position.

**Budget in Query Units.** One read is 1 QU whatever `limit` you pass; admitted Situation creation
is 5 QU and reusing an existing one is 0; Monitor runs are 0. So count before you list (`/summary`
endpoints, `include_total=true` on the first page only), page at the maximum `limit`, and read
`GET /api/v2/meta/query-units` for your position rather than guessing it.

**Two paging shapes.** Events, Stories and the activity journal are keyset-paged: copy `next_cursor`
verbatim and keep every filter identical between pages. Situation member lists are offset-paged
under a `scope_version`: send the version from page one on every later page, and treat a `409` as
"the collection changed — restart at offset 0". `has_more` is measured on both; row count is not.

**Honest unknowns.** `applied_filters.ignored` names what the server did not apply; `caps` and
`truncated` say when an array is bounded; a withheld section is not an empty one; and every coverage
statement is dated. Carry those fields into whatever you build, or the build will claim more than
the API did.

## Four worked builds

Each is the minimal call list. `{braces}` in a path and `<angle brackets>` in a value are
placeholders filled from the previous step; `$GDELT_API_KEY` is the bearer token.

### 1. A query Monitor

Keep an executed activity request as a scheduled check, saved paused, then enabled on purpose.

```bash
# 1. resolve the subject and choose the candidate yourself
curl -G "https://gdeltcloud.com/api/v2/search" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "q=<name>" --data-urlencode "country_match=strict"

# 2. preview the standing question (1 QU, never delivers)
curl -X POST "https://gdeltcloud.com/api/v2/monitors/preview" -H "Authorization: Bearer $GDELT_API_KEY" \
  -H "Content-Type: application/json" -d '{
    "name": "Publication activity: <name>",
    "subject": { "type": "query", "endpoint": "/api/v2/activity",
                 "params": { "entity": "<entity_id>", "time_basis": "recorded" } },
    "trigger": { "type": "new_matches" },
    "schedule": { "cadence": "daily", "timezone": "UTC", "daily_hour": 8 },
    "delivery": { "email": true }
  }'

# 3. create it saved-but-paused; 4. enable it when the user says so
curl -X POST "https://gdeltcloud.com/api/v2/monitors" ... -d '{ ...same body..., "enabled": false }'
curl -X PATCH "https://gdeltcloud.com/api/v2/monitors/{id}" ... -d '{ "enabled": true }'
```

Read `evaluation.query_coverage` on the preview before promising anything: complete paging of the
observed journal can notify, but it is not exhaustive source intake.

### 2. A country brief

Four reads, one ISO-3 code, every number labelled with its clock.

```bash
curl -G "https://gdeltcloud.com/api/v2/countries/{iso3}" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "basis=reporting" --data-urlencode "date_start=<yyyy-mm-dd>" --data-urlencode "date_end=<yyyy-mm-dd>"
curl -G "https://gdeltcloud.com/api/v2/situations" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "country=<iso3>" --data-urlencode "date_start=<yyyy-mm-dd>" --data-urlencode "date_end=<yyyy-mm-dd>"
curl -G "https://gdeltcloud.com/api/v2/offices" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "country=<iso3>" --data-urlencode "as_of=<yyyy-mm-dd>"
curl -G "https://gdeltcloud.com/api/v2/facilities" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "country=<iso3>" --data-urlencode "granularity=site"
```

`basis=reporting` counts distinct served Events by occurrence date and location country; the default
`publication` basis keeps the journal clock. The Situations filter needs both date bounds (at most 30
days) and means *coded Event location*, not actor nationality. `as_of` on offices is valid time — who
held the office on that date by the publisher's dates. Facility totals are registry records; label
them as sites or units, never as construction.

### 3. A Situation tracker

Find the maintained Situation for an entity, then walk its Stories and Events independently.

```bash
curl -G "https://gdeltcloud.com/api/v2/situations" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "entity=<entity_id>" --data-urlencode "date_start=<yyyy-mm-dd>" --data-urlencode "date_end=<yyyy-mm-dd>"
curl -G "https://gdeltcloud.com/api/v2/situations/{situation_uid}" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "include=edges" --data-urlencode "limit=25"
```

```python
def walk_members(client, uid, kind, cap=2000):
    """kind is 'stories' or 'events'. Restart on 409: the collection changed under you."""
    while True:
        rows, offset, version = [], 0, None
        while True:
            params = {"limit": 100, "offset": offset, **({"scope_version": version} if version else {})}
            path = f"/api/v2/situations/{uid}/stories" if kind == "stories" else f"/api/v2/situations/{uid}/events"
            r = client.get(path, params=params)
            if r.status_code == 409:
                break                     # scope changed: discard rows and start again
            page = r.json()
            version = version or page["scope"]["version"]
            rows += page["data"]
            if not page["pagination"]["has_more"] or len(rows) >= cap:
                return rows, version
            offset += len(page["data"])
```

Save the whole response you used — `meta`, `applied_filters`, `caps`, the version — because the
service does not reconstruct earlier editions on demand. Read `meta.situation_source`: `curated` is
stored membership; `walked` is an exploratory neighbourhood and not a Situation.

### 4. An entity dossier

Resolve once, then read every surface with the same id.

```bash
curl -G "https://gdeltcloud.com/api/v2/search" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "q=<name>" --data-urlencode "country_match=strict"
curl "https://gdeltcloud.com/api/v2/entities/{entity_id}" -H "Authorization: Bearer $GDELT_API_KEY"
curl -G "https://gdeltcloud.com/api/v2/entities/{entity_id}/offices" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "as_of=<yyyy-mm-dd>"
curl -G "https://gdeltcloud.com/api/v2/activity" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "entity=<entity_id>" --data-urlencode "time_basis=recorded" \
  --data-urlencode "recorded_start=<iso-utc>" --data-urlencode "recorded_end=<iso-utc>"
curl -G "https://gdeltcloud.com/api/v2/stories" -H "Authorization: Bearer $GDELT_API_KEY" \
  --data-urlencode "entity=<entity_id>" --data-urlencode "date_start=<yyyy-mm-dd>" \
  --data-urlencode "date_end=<yyyy-mm-dd>" --data-urlencode "limit=100"
```

Offices, activity and Stories answer different questions — an office held, a record that arrived, a
cluster of coverage — so keep each in its own section with its own clock. A withheld offices section
is an entitlement, not evidence that the person holds none; an empty activity window with
`meta.coverage.window_complete=false` is an initialised journal, not a quiet entity.
