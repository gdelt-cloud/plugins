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

## 6. A checklist before you ship

- [ ] Every list read either walks to `next_cursor is None` or states the cap it stopped at
- [ ] No `len(rows) >= limit` truncation checks anywhere
- [ ] `applied_filters` is asserted, not assumed, for every filter that matters
- [ ] Empty results are reported as *no coverage*, never as *nothing happened*
- [ ] `null` metrics are rendered as gaps, never charted as `0`
- [ ] Windows are bounded and end yesterday if the number is compared over time
- [ ] Entity ids are resolved once and reused; no bare names crossing endpoints
- [ ] 429 handling branches on `code`, not on the status
