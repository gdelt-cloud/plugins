---
name: building-with-api
description: Build applications on GDELT Cloud REST and MCP, including company watches and Story feeds.
---

# Building With Api

Use the API as the product contract. Discover exact filters and bounded responses, then implement through documented /api/v2 endpoints. Do not query warehouse SQL, copy raw CAMEO filters, or invent URL parameters. Read getting started (`skill://getting-started/SKILL.md`) for evidence and response modes.

## Company watch application
Resolve a company with `gdelt_cloud_tool_call` operation `unified_entity_search`; inspect candidates rather than picking a similarly named company. Use returned IDs with Events/Stories or documented entity context. Fetch the exact operation schema first. Add filings or asset records only if the task requires them. REST: `/api/v2/search`, `/api/v2/events`, `/api/v2/stories`; use the API's accepted entity ID space. A name mention alone is not an exposure relationship. Monitoring is an explicit optional next step, never silently created.

For a daily watch, keep company relevance separate from arrival detection. Linked identity means a record refers to the company; it does not establish direct action or material impact. Preserve structured actor roles and their match basis. Where actors lack canonical IDs, a vetted exact name match remains provisional identity evidence. For a decision-changing claim, inspect returned original reporting and record the evidence for direct company involvement, incidental mention, or unresolved relevance. Do not promote an executive mention, high metric, or keyword match into company action. Unknown relevance stays reviewable.

## Ongoing recorded-time feed
Use `get_activity` / `GET /api/v2/activity` for what became available since the last successful run, including late arrivals, substantive updates and removals. Events/Stories date searches answer occurrence/reporting questions and cannot substitute for this arrival clock. The example below uses an observed NVIDIA identity; resolve and review the user's identity, and choose the actual interval before executing it.

```python
gdelt_cloud_tool_call(
    tool_name="get_activity", response_mode="full",
    tool_arguments={"entity": "e_2af946de69c91484", "kind": "story", "time_basis": "recorded",
                    "recorded_start": "2026-09-29T00:00:00Z",
                    "recorded_end": "2026-09-30T00:00:00Z", "limit": 100})
```

Persist a frozen half-open `[recorded_start, recorded_end)` interval before the first read. Bounds are UTC timestamps with at most three fractional digits, and span at most 31 days; reject unsupported precision without rounding and process longer catch-up in consecutive bounded intervals. Start from a completed checkpoint or a deliberately chosen initial history boundary. Retain the interval, identity, kind and **limit** unchanged on every continuation and retry; copy `next_cursor` verbatim. Validate material applied filters using the endpoint's canonical echoes. Budget requests, rows and elapsed time before collection, including hydration and retries. Empty progressing pages are not completion and can still consume the budget.

Represent that scope as a frozen request object and pass it to the transport on **every** read; configuration that never reaches the adapter does not constrain the API. Store a versioned request fingerprint with each pending cursor, covering resolved identity, time basis, paired bounds, kind and limit. Refuse to resume a cursor with changed scope. Give each requested kind its own pending cursor and completion evidence.

Retain full receipts for diagnosis, including refused pages. Validate pagination, material filter echoes, requested-source capabilities and positive coverage before committing records or moving the cursor. Commit accepted records, stable `change_id` deduplication and cursor state in one durable transaction. Derive exports from that store or make them idempotent; appending records before validating a page can duplicate them on retry. Incomplete pages may be retained as pending evidence, but cannot become completed checkpoints.

Resolve canonical publication identity before hydration; missing Story/Event anchors or unavailable enrichment needed by the application remain retryable on the same page. Hydration returns the current serving card, not an earlier historical edition; retain its receipt time. Keep removals explicit and publisher links beside the returned GDELT Cloud record links. Advance the completed checkpoint only after terminal `next_cursor=null`, positive `meta.coverage.window_complete=true`, available capability for each requested source, processing of all required page members, and durable export/delivery. Missing/false coverage, a contradictory `has_more`, repeated cursor, unavailable record or budget stop retains pending work. Completing the observed journal does not prove exhaustive upstream intake or a quiet company; baseline inventories and unavailable history are excluded.

Completion belongs to that interval. An ongoing collector must explicitly open its next contiguous bounded interval after the previous one completes, resetting per-kind cursors and completion flags. Exercise malformed-pagination then valid retry, incomplete empty pages, interruption/resume, changed identity/window/limit and next-window transition in offline fixtures. Use the installed plugin's bounded cursor helper where its contract fits, or implement equivalent guards; the helper does not provide durable checkpoint storage.

## Story feed
Use `search_stories` for clustered narratives and `get_story_articles` for evidence. REST: `GET /api/v2/stories`, `GET /api/v2/stories/{story_id}/articles`. Preserve canonical IDs, pagination and returned public URLs. Follow server cursors and stop on the requested bound, repeated cursors, or error. Deduplicate canonical identity across pages. Do not generate a cursor or infer completion from an empty page when coverage is incomplete. Use full MCP mode to inspect bounded API receipts before implementing.

## Implementation discipline
Keep API keys server-side. Handle auth, plan gates, throttling and retryable coverage failures distinctly; do not log credentials. Cache by complete applied filters and account entitlement scope where relevant. Use UTC windows and disclose their exact dates. Background jobs must retain incomplete checkpoints for retry. A current date is still growing even if rows are available. Use recorded-time activity for ongoing ingestion when its published schema supports it; publication and occurrence clocks are different.

Use endpoint schemas/OpenAPI and the generated catalog for authoritative parameter names. Both MCP and REST go through the shared serving contract. Build the endpoint workflow first; the UI should render what it returns. No hidden data calls are needed to answer schema-only questions.

When translating a demonstrated result into REST, carry every material applied filter into the example, especially explicit start/end dates, country matching mode, entity identity and linked-Event constraints. Keep them fixed on subsequent cursor requests. A prose warning about dates does not repair an example that omits the date window and silently falls back to a different default.
