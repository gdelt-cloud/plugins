---
name: building-with-api
description: Build applications on GDELT Cloud REST and MCP, including company watches and Story feeds.
metadata:
  tool_exposure: named
---

# Building With Api

Use the API as the product contract. Discover exact filters and bounded responses, then implement through documented /api/v2 endpoints. Do not query warehouse SQL, copy raw CAMEO filters, or invent URL parameters. Read getting started (`skill://getting-started/SKILL.md`) for evidence and response modes.

The canonical REST origin is **https://gdeltcloud.com**: for example, `GET https://gdeltcloud.com/api/v2/activity`, with `Authorization: Bearer $GDELT_API_KEY`. Use that exact origin in runnable examples. The MCP connection URL is a different interface; do not infer an API subdomain from the product name.

## Company watch application
Resolve a company with `unified_entity_search`; inspect candidates rather than picking a similarly named company. Use returned IDs with Events/Stories or documented entity context. Use the advertised operation schema; optional parameter options can clarify unfamiliar choices. Add filings or asset records only if the task requires them. REST: `/api/v2/search`, `/api/v2/events`, `/api/v2/stories`; use the API's accepted entity ID space. A name mention alone is not an exposure relationship. Monitoring is an explicit optional next step, never silently created.

Choose by task scope and returned source availability, not name rank alone. A registry-only owner, registered legal entity and news-linked corporate Group are not interchangeable. For a Group news feed, select the matching Group candidate with available news/Event coverage; if the requested legal scope is ambiguous, clarify it. Explicit unavailable news is not a quiet-company finding; an absent source key may be entitlement-withheld. Keep source-reported asset ownership separate and do not merge identities just to obtain results.

For a daily watch, keep company relevance separate from arrival detection. Linked identity means a record refers to the company; it does not establish direct action or material impact. Preserve structured actor roles and their match basis. Where actors lack canonical IDs, a vetted exact name match remains provisional identity evidence. For a decision-changing claim, inspect returned original reporting and record the evidence for direct company involvement, incidental mention, or unresolved relevance. Do not promote an executive mention, high metric, or keyword match into company action. Unknown relevance stays reviewable.

## Ongoing recorded-time feed
Use `get_activity` / `GET /api/v2/activity` for what became available since the last successful run, including late arrivals, substantive updates and removals. Events/Stories date searches answer occurrence/reporting questions and cannot substitute for this arrival clock. The example below uses an observed NVIDIA identity; resolve and review the user's identity, and choose the actual interval before executing it.

```python
get_activity(
    entity="e_2af946de69c91484", kind="story", time_basis="recorded",
    recorded_start="2026-09-29T00:00:00Z",
    recorded_end="2026-09-30T00:00:00Z", limit=100, response_mode="full")
```

Persist a frozen half-open `[recorded_start, recorded_end)` interval before the first read. Bounds are UTC timestamps with at most three fractional digits, and span at most 31 days; reject unsupported precision without rounding and process longer catch-up in consecutive bounded intervals. Start from a completed checkpoint or a deliberately chosen initial history boundary. Retain the interval, identity, kind and **limit** unchanged on every continuation and retry; copy `next_cursor` verbatim. Validate material applied filters using the endpoint's canonical echoes. Budget requests, rows and elapsed time before collection, including hydration and retries. Empty progressing pages are not completion and can still consume the budget.

Represent that scope as a frozen request object and pass it to the transport on **every** read; configuration that never reaches the adapter does not constrain the API. Store a versioned request fingerprint with each pending cursor, covering resolved identity, time basis, paired bounds, kind and limit. Refuse to resume a cursor with changed scope. Give each requested kind its own pending cursor and completion evidence.

Read the discovered output schema before writing fixtures or a transport adapter. Activity rows are in `data`; source capabilities are in `meta.coverage.sources`, matched by source/kind, with `available` on each row. Event/Story journal source keys are `events`/`stories`; `source_dataset` is separate returned dataset attribution to preserve verbatim. Do not invent `activity` lists or `meta.capabilities[kind]`. Explicit URL query echoes in `applied_filters` are strings; numeric page size is in `pagination.limit`. Positive `meta.coverage.window_complete` is independent of pagination and can be true on a continuing page. Continue until an explicit terminal `pagination.next_cursor=null`; a missing cursor is not terminal. Preserve `evidence_url` exactly, including relative API references; hydrate detail for returned public record and publisher links. Validate an API-shaped offline receipt as well as failure fixtures before advertising live mode.

Retain full receipts for diagnosis, including refused pages. Validate pagination, material filter echoes, requested-source capabilities and positive coverage before committing records or moving the cursor. Commit accepted records, stable `change_id` deduplication and cursor state in one durable transaction. Derive exports from that store or make them idempotent; appending records before validating a page can duplicate them on retry. Incomplete pages may be retained as pending evidence, but cannot become completed checkpoints.

Keep an append-only change ledger keyed by `change_id` separate from the current Story/Event card keyed by `record_id`. Pages can present changes in descending order: an older change encountered later must not overwrite a newer card or resurrect a removal. Preserve change receipts and resolve current cards through detail hydration; do not claim a one-row-per-Story table with a replaceable unique change ID provides historical deduplication. Test multiple updates and removals for the same record across pages, including replay after a restart.

Apply this ordering guard **before every current-card write, including removals and hydration**. `previous` is the last applied journal change's `record_id`, `change_id` and `recorded_at`, stored with the current card; it is not the card's reporting date. Always retain older changes in the append-only ledger, but skip their current-state writes. Missing versions or conflicting same-time changes keep the page pending; do not invent an order from change-ID spelling. Stage the ledger, current card and cursor in the same transaction.

```python
from datetime import datetime, timezone


def should_apply_activity_change(change, previous=None):
    def stamp(value):
        if not isinstance(value, str) or not value:
            raise ValueError("Missing recorded version; keep page pending")
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("Recorded version requires an explicit timezone")
        return parsed.astimezone(timezone.utc)

    receipts = (change,) if previous is None else (change, previous)
    for receipt in receipts:
        if not isinstance(receipt, dict) or any(
            not isinstance(receipt.get(key), str) or not receipt[key]
            for key in ("record_id", "change_id")
        ):
            raise ValueError("Canonical record and change identities required")
    current_time = stamp(change.get("recorded_at"))
    if previous is None:
        return True
    if change["record_id"] != previous["record_id"]:
        raise ValueError("Compare versions of the same canonical record")
    previous_time = stamp(previous.get("recorded_at"))
    if change["change_id"] == previous["change_id"]:
        if current_time != previous_time:
            raise ValueError("Conflicting receipt for an existing change")
        return False
    if current_time == previous_time:
        raise ValueError("Ambiguous change order; keep page pending")
    return current_time > previous_time
```

A runnable resumable example must read its pending cursor from durable storage before its first request, check the saved request fingerprint, and resume the same frozen interval. Writing pending state while always restarting from `cursor=None` is not resumption. On completion, read the completed checkpoint to open the next contiguous interval. State the implemented limits clearly; prose about restart safety does not repair code that ignores stored state.

Resolve canonical publication identity before hydration; missing Story/Event anchors or unavailable enrichment needed by the application remain retryable on the same page. Hydration returns the current serving card, not an earlier historical edition; retain its receipt time. For an explicit `change=removed`, retain/apply a tombstone with its change identity and returned evidence; do not require current-detail hydration of a record the journal says was removed. Preserve previously observed evidence. A missing detail response alone never proves removal: added/updated members remain retryable on the same page. Keep publisher links beside returned GDELT Cloud record links. Advance the completed checkpoint only after terminal `next_cursor=null`, positive `meta.coverage.window_complete=true`, available capability for each requested source, processing of all required page members, and durable export/delivery. Missing/false coverage, a contradictory `has_more`, repeated cursor, unavailable record or budget stop retains pending work. Completing the observed journal does not prove exhaustive upstream intake or a quiet company; baseline inventories and unavailable history are excluded.

Completion belongs to that interval. An ongoing collector must explicitly open its next contiguous bounded interval after the previous one completes, resetting per-kind cursors and completion flags. Exercise malformed-pagination then valid retry, incomplete empty pages, interruption/resume, changed identity/window/limit and next-window transition in offline fixtures. Use the installed plugin's bounded cursor helper where its contract fits, or implement equivalent guards; the helper does not provide durable checkpoint storage.

Before accepting a page, use this completion receipt guard or equivalent. Its indexed cursor access is deliberate: `pagination.get("next_cursor")` silently turns a missing field into terminal null. Retain refused receipts as pending evidence. This guard does not replace scope/filter validation, row validation, hydration or durable storage.

```python
def validate_activity_page(receipt, kind, previous_cursor=None):
    if kind not in ("event", "story"):
        raise ValueError("Choose an event or story stream")
    if not isinstance(receipt, dict) or receipt.get("success") is not True:
        raise ValueError("Successful API receipt required")
    page = receipt.get("pagination")
    if not isinstance(page, dict) or not {"next_cursor", "has_more"} <= page.keys():
        raise ValueError("Missing pagination evidence; keep the checkpoint pending")
    next_cursor = page["next_cursor"]
    if next_cursor is not None and (not isinstance(next_cursor, str) or not next_cursor):
        raise ValueError("Invalid continuation token")
    if type(page["has_more"]) is not bool or page["has_more"] != (next_cursor is not None):
        raise ValueError("Contradictory pagination")
    if next_cursor is not None and next_cursor == previous_cursor:
        raise ValueError("Repeated cursor")
    meta = receipt.get("meta")
    coverage = meta.get("coverage") if isinstance(meta, dict) else None
    if not isinstance(coverage, dict) or coverage.get("window_complete") is not True:
        raise ValueError("Positive window coverage required before page acceptance")
    sources = coverage.get("sources")
    source = "events" if kind == "event" else "stories"
    if not isinstance(sources, list) or not any(
        isinstance(s, dict) and s.get("source") == source
        and s.get("kind") == kind and s.get("available") is True for s in sources
    ):
        raise ValueError("Requested journal source is unavailable or unreported")
    rows = receipt.get("data")
    if not isinstance(rows, list):
        raise ValueError("Activity data must be an array")
    return rows, next_cursor
```

Call `rows, next_cursor = validate_activity_page(receipt, kind, previous_cursor=cursor)` **before** any accepted-record write or cursor advancement. Then validate material filter echoes and every required member; process hydration/removals; commit accepted records and cursor in one durable transaction. Only after that transaction and required export/delivery succeed can explicit `next_cursor is None` complete the interval. Persist a seen-cursor set as needed to reject cycles across restarts. An empty page with a non-null continuation progresses; it does not complete.

## Story feed
Use `search_stories` for clustered narratives and `get_story_articles` for evidence. REST: `GET /api/v2/stories`, `GET /api/v2/stories/{story_id}/articles`. Preserve canonical IDs, pagination and returned public URLs. Follow server cursors and stop on the requested bound, repeated cursors, or error. Deduplicate canonical identity across pages. Do not generate a cursor or infer completion from an empty page when coverage is incomplete. Use full MCP mode to inspect bounded API receipts before implementing.

## Implementation discipline
Keep API keys server-side. Handle auth, plan gates, throttling and retryable coverage failures distinctly; do not log credentials. Cache by complete applied filters and account entitlement scope where relevant. Use UTC windows and disclose their exact dates. Background jobs must retain incomplete checkpoints for retry. A current date is still growing even if rows are available. Use recorded-time activity for ongoing ingestion when its published schema supports it; publication and occurrence clocks are different.

Use endpoint schemas/OpenAPI and the generated catalog for authoritative parameter names. Both MCP and REST honor the published API contract. Build the endpoint workflow first; the UI should render what it returns. No hidden data calls are needed to answer schema-only questions.

When translating a demonstrated result into REST, carry every material applied filter into the example, especially explicit start/end dates, country matching mode, entity identity and linked-Event constraints. Keep them fixed on subsequent cursor requests. A prose warning about dates does not repair an example that omits the date window and silently falls back to a different default.
