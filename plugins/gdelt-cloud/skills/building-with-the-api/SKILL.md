---
name: gdelt-cloud-building-with-the-api
description: Build or repair a GDELT Cloud REST/MCP integration, dashboard, notebook or data pipeline. Covers verified schemas, bounded pagination, partial coverage, retries, caches and repeatable tests. Use for code and exports, not a one-off research answer.
---

# Build against the real contract

Choose REST for application code (`https://gdeltcloud.com/api/v2`) and MCP for agent tool use.
Read [MCP workflows](../getting-started/references/mcp-workflows.md) when using tools; do not
translate REST examples into guessed MCP argument names. Query the docs MCP/OpenAPI and endpoint
metadata for the exact operation. Do not fetch data merely to generate a client or explain a schema.

## Preserve evidence and bound work

- Use the endpoint's cursor, offset or versioned pagination contract. Do not apply one generic
  cursor loop to all endpoints. Keep filters fixed and detect a non-advancing cursor.
- A terminal cursor means the returned sequence ended; complete coverage also requires positive
  coverage evidence. Semantic retrieval can exhaust a bounded pool without exhausting the corpus.
- For an export, choose a supported page size and explicit row/call budget. For a chat sample,
  3–10 rows are often enough. Larger pages reduce requests only when you need those rows.
- Keep each response receipt: pagination, applied filters, source dates, missing dates, version
  and truncation. Unknown totals and usage remain null. Never zero-fill withheld dates.
- Check HTTP status before parsing success data. Correct schema errors; stop on auth/plan/quota
  denial; honor rate-limit retry hints with bounded retries. Do not blindly retry mutations.
- Cache by endpoint, normalized filters, access scope and data version/freshness. Closed dates
  can still be corrected or backfilled; use revalidation rather than an eternal historical cache.
- Read current costs/capabilities from metadata and response receipts. Not every operation has
  the same price, and a request budget is separate from a context/token budget.

For a cursor-based Events/Stories export, [cursor_pages.py](scripts/cursor_pages.py) is a small
reference helper that retains receipts, rejects incomplete coverage and detects cursor loops.
It expects an already authenticated client and does not read secrets or perform network calls
on import. Set endpoint-specific policy explicitly; it is not a universal API paginator.

## References to load when needed

- [Detailed integration recipes](references/details.md): semantic retrieval, stability,
  country briefs, Situation membership/versioning, entity dossiers and query Monitors.
- [Core API](../core-api/SKILL.md): select an endpoint for a product question.
- [Hosted Monitors](../hosted-monitors/SKILL.md): one supported recurring question with delivery;
  keep client code for private joins, custom schedules or composite state.

Test a representative response, partial/empty coverage, a terminal page, a repeated cursor,
a quota/plan error and a schema error. Verify returned IDs and filter meaning, not just status 200.
Keep test output free of credentials and private customer records.
