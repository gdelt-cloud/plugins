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

Events and Stories use cursor pagination; other families use offsets or versioned membership.
Use the exact contract. For cursor exports, use [the bounded helper](../scripts/cursor_pages.py)
and inspect every page's receipt. A terminal cursor only ends this result sequence. It does not
prove complete date coverage or exhaustive semantic recall. Keep filters fixed and copy opaque
cursors unchanged; stop and disclose a row/call budget or a non-advancing cursor.

The helper freezes the query and its first-page `limit`: the activity cursor binds `limit` too.
When the remaining row budget cannot fit that unchanged page size, it stops before another read.
Increase the budget or start a new walk with a smaller page size; never shrink a continuation's
`limit`. Save yielded receipts and an exception's `page` when attached. The helper is a bounded iterator, not
a durable checkpoint store or a general retry policy.

Supply a receipt validator for your endpoint's canonical semantic echoes. This Event example
expects the documented ISO-3 **array** for country, rather than comparing `"France"` to `["FRA"]`:

```python
from cursor_pages import cursor_pages
params = {"country": "FRA", "country_match": "location",
          "date_start": "2026-09-22", "date_end": "2026-09-28"}
def validate_scope(receipt):
    applied = receipt.get("applied_filters") or {}
    expected = {**params, "country": ["FRA"]}
    for key, value in expected.items():
        if applied.get(key) != value:
            raise ValueError(f"Missing or changed applied filter: {key}")
pages = list(cursor_pages(client, "/events", params, page_size=100, max_rows=1000,
                          validate_receipt=validate_scope))
```

Replace the example dates with the user's explicit scope. Apply the same discipline to every
material filter; each endpoint can canonicalize aliases differently. The helper rejects explicit
ignored filters, malformed/repeated cursors and contradictory pagination before yielding a page,
but it cannot infer an identity or geography match on your behalf.

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
| `data: []`, filters applied, positive complete-coverage evidence | No returned records in the measured scope | Report that scope, never "no events happened" |
| Missing/false completeness or withheld dates | Unknown/partial coverage | Disclose gaps; do not report a quiet interval |
| `data: []`, a filter missing from `applied_filters` | The server did not apply it | Fix the parameter name — you are looking at an unfiltered answer that happened to be empty |
| `400 UNKNOWN_PARAM` | A descriptor-backed endpoint rejected a spelling it does not support | Use `details.accepted_params` / `did_you_mean` and correct the request |
| `data: []`, something in `applied_filters.ignored` | A compatibility endpoint did not recognise it | Correct the typo or remove the unsupported parameter before interpreting the data |
| Full page, `next_cursor` non-null | Truncated | Walk it (§1) |

Filter echoes use canonical names and do not necessarily echo transport controls. Compare semantic
filters using documented aliases instead of treating every absent request key as ignored.
Read errors, coverage, truncation and any returned note before interpreting an empty page.

## 3. `search=` and `/summary` do not compose — bucket client-side

`/events/summary` **rejects** `search=` with a 400. This is deliberate: semantic retrieval ranks a
bounded candidate pool, and an aggregate over a pool is not an aggregate over the corpus. The
consequence for a build is real, so plan for it: **there is no server-side time series for a semantic
query.** Walk the bounded candidate list and bucket it in your own code, explicitly labeling it as retrieval coverage, not population counts.

```python
from collections import Counter
# Copy the packaged cursor_pages.py helper into your integration module first.
from cursor_pages import cursor_pages
pages = list(cursor_pages(c, "/events", {"search": "port congestion", "date_start": ..., "date_end": ...}))
rows = [row for page in pages for row in page["data"]]  # candidate-pool sample, not all events
series = Counter(r["event_date"] for r in rows)
```

Two things follow. `pagination.estimated_total` is `null` on a `search=` request for the same reason
— any number there would describe the candidate pool. `search_score` ranks semantic candidates
within a query; it is not a calibrated probability or a universal relevance cutoff. Preserve the
name-match arm and unscored candidates for separate review instead of silently treating null as zero:

```python
name_matches = [r for r in rows if r.get("match_type") == "name"]
ranked_semantic = sorted(
    [r for r in rows if r.get("match_type") == "semantic" and r.get("search_score") is not None],
    key=lambda r: r["search_score"], reverse=True)
needs_review = [r for r in rows if r not in name_matches and r not in ranked_semantic]
```

`match_type` tells you which arm found the row: `semantic` (embedding distance, carries a
`search_score`) or `name` (literal match, `search_score` is `null` — a name hit has no computed
distance, and the API will not invent one). The key is absent entirely on non-search requests.
Review returned summaries and underlying source evidence for decision-changing relevance. A
validated cutoff for one task is not automatically valid for another or a later retrieval version.

For a structured time series, use `/events/summary?group_by=date` with structured filters. It is one
call instead of a walk.

## 4. Identifiers, and the two fields that look alike

- An event card's key is **`id`**. `event_id` is the name of the PATH parameter
  (`/events/{event_id}/stories`), not a field on the card. `e["event_id"]` raises `KeyError`.
- `id` identifies an **Event record**, not a real-world incident. Group on `incident.uid` to count
  incidents, and pass `incident_resolution=llm,self` to restrict to the rows where that grouping was
  actually adjudicated — coverage is partial by design.
- `subcategory` is the **filter value** (`"EC04"`, or an ACLED sub-event type like
  `"Peaceful protest"`). `subcategory_label` is the human name (`"Trade Policy Action"`). Display the
  label; filter on the code. The same split applies to `group_by=subcategory` buckets: `key` is what
  you send back, `label` is what you show.

## 5. Caching and cadence

The pipeline is continuous. Articles are ingested, clustered and coded hourly; the snapshots the API
reads are rebuilt every 30 minutes. So:

- **Cache with revalidation.** Key by endpoint, normalized filters, access scope and version/freshness.
  Closed dates can still receive corrections or backfills; today generally needs a shorter TTL.
- **End your window yesterday** for anything a user will compare day-over-day.
- **Retain returned freshness/version evidence**, including `meta.settled_at` when present.
  It contributes to the scoped cache's version; it is not a replacement for endpoint, filters,
  account scope or scheduled revalidation.
- **Poll on a schedule, not a loop.** Rate limits are per-minute and per-plan; a 429 with code
  `RATE_LIMITED` means back off and retry, and `QUOTA_EXCEEDED` means stop and tell the user. Same
  status, opposite responses — read `code`, and read `details.retry_after`.

## 6. What a call costs, and the one lever that matters

Read current costs from `/api/v2/meta/query-units`, endpoint capabilities and `x-quota-cost`.
Different operations and transports can have different costs. Use larger supported pages for
exports, small samples for conversation, and summaries instead of counting a long list.
Budget calls per subject and refresh interval; stop on quota exhaustion rather than retrying.

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
- [ ] Complete empty results say *no returned records in the measured scope*; missing/partial
      coverage remains unknown, and neither result claims *nothing happened*
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

The principles below apply across endpoints, so a build that the skills
above do not describe can still be derived correctly. Each one is a place a plausible HTTP 200 hides.

**Served, not raw.** Event and Story reads use serving records; the activity feed uses its committed
publication journal, while registries retain their native source semantics. Read the available
receipts (`meta.row_source`, `meta.settled_at`, and on the activity journal
`meta.coverage.window_complete` plus `meta.exhaustive`), not warehouse SQL. A `null` is *unmeasured* — an unknown `linked_event_count`, a withheld
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

**Budget in Query Units.** Read current source multipliers, endpoint weights and measured usage
from `GET /api/v2/meta/query-units`; a response's `X-Quota-Cost` is an upper bound, not proof of
consumption. Prefer summaries for aggregates and supported larger pages for exports, while keeping
the cursor's page size fixed. Set a request and elapsed-time budget before collection. Pending usage
is unknown, not zero, and exhausted quota stops the job.

**Two paging shapes.** Events, Stories and the activity journal expose their own opaque cursor
forms: copy `next_cursor` verbatim and keep every filter and the page size identical between pages.
Do not infer their internal keyset/offset implementation. Situation member lists are offset-paged
under a `scope_version`: send the version from page one on every later page, and treat a `409` as
"the collection changed — restart at offset 0". `has_more` is measured on both; row count is not.

**Honest unknowns.** Strict descriptor-backed endpoints return `400 UNKNOWN_PARAM`; legacy
compatibility endpoints may instead use `applied_filters.ignored` to name what they did not apply. `caps` and
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

For each member list, keep a separate offset, scope version and response-receipt collection.
Check HTTP status before consuming rows. On a scope-change 409, discard that list's accumulated
rows and restart at offset zero; impose a small restart budget (for example two) and an overall
request budget. If the scope keeps changing, report an incomplete export instead of retrying
forever. Bound each page by the remaining row budget. When `has_more` remains true at that budget,
return an explicitly partial result or fail the export; never label the truncated rows complete.
Detect a non-advancing offset/empty page with `has_more=true`. Keep separate results for Stories
and Events: one list's completion or scope version does not establish the other's completion.

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
