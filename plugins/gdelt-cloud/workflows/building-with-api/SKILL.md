---
name: building-with-api
description: Build applications on GDELT Cloud REST and MCP, including company watches and Story feeds.
---

# Building With Api

Use the API as the product contract. Discover exact filters and bounded responses, then implement through documented /api/v2 endpoints. Do not query warehouse SQL, copy raw CAMEO filters, or invent URL parameters. Read getting started (`skill://getting-started/SKILL.md`) for evidence and response modes.

## Company watch application
Resolve a company with `gdelt_cloud_tool_call` operation `unified_entity_search`; inspect candidates rather than picking a similarly named company. Use returned IDs with Events/Stories or documented entity context. Fetch the exact operation schema first. Add filings or asset records only if the task requires them. REST: `/api/v2/search`, `/api/v2/events`, `/api/v2/stories`; use the API's accepted entity ID space. A name mention alone is not an exposure relationship. Monitoring is an explicit optional next step, never silently created.

## Story feed
Use `search_stories` for clustered narratives and `get_story_articles` for evidence. REST: `GET /api/v2/stories`, `GET /api/v2/stories/{story_id}/articles`. Preserve canonical IDs, pagination and returned public URLs. Follow server cursors and stop on the requested bound, repeated cursors, or error. Deduplicate canonical identity across pages. Do not generate a cursor or infer completion from an empty page when coverage is incomplete. Use full MCP mode to inspect bounded API receipts before implementing.

## Implementation discipline
Keep API keys server-side. Handle auth, plan gates, throttling and retryable coverage failures distinctly; do not log credentials. Cache by complete applied filters and account entitlement scope where relevant. Use UTC windows and disclose their exact dates. Background jobs must retain incomplete checkpoints for retry. A current date is still growing even if rows are available. Use recorded-time activity for ongoing ingestion when its published schema supports it; publication and occurrence clocks are different.

Use endpoint schemas/OpenAPI and the generated catalog for authoritative parameter names. Both MCP and REST go through the shared serving contract. Build the endpoint workflow first; the UI should render what it returns. No hidden data calls are needed to answer schema-only questions.

When translating a demonstrated result into REST, carry every material applied filter into the example, especially explicit start/end dates, country matching mode, entity identity and linked-Event constraints. Keep them fixed on subsequent cursor requests. A prose warning about dates does not repair an example that omits the date window and silently falls back to a different default.
