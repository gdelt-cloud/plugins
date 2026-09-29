# Using the MCP well

Start with the smallest workflow that answers the user. Inspect the tools actually connected
in this host. Tool names may have a client-added server prefix; the logical names below do not.

## Discover, inspect, execute

1. `<category>_tool_list()` lists operations and their `call_with` wrapper.
2. `<category>_tool_get(tool_name="...")` returns the exact input schema, defaults and enums.
3. `<category>_tool_call(tool_name="...", tool_arguments={...})` executes reads.

Underlying names such as `search_events` are not separate top-level tools. REST parameter
names and body nesting can differ from the MCP wrapper: use the schema just retrieved.
Reuse a schema already seen in the current session; refresh after a schema error or release.
Do not enumerate every category or load a long operating manual before a simple lookup.

Example, after inspecting `search_events`:

```python
gdelt_cloud_tool_call(tool_name="search_events", tool_arguments={
    "country": ["Iran"], "country_match": "location", "days": 7, "limit": 3
})
```

This is a sample, not a complete inventory. For a named company, discover
`unified_entity_search` first, inspect ambiguous candidates, and preserve its returned identifier
and source availability. Do not silently pick the top result or invent an `e_` identifier.

## Route by the question

| Question | Category / operations to discover |
|---|---|
| Events, news, counts, identities, Countries, activity, Situations | `gdelt_cloud` |
| Energy capacity, assets and ownership | `energy` |
| Unified physical sites / facilities | `facilities` |
| Company reports and financial facts | `filings` |
| Corporate LEIs and hierarchy | `gleif` |
| Awards and foreign-agent registrations | `gov` |
| Public offices and holder history | `offices` |
| Sanctions/list screening and exposure | `risk` |
| Vessel and port signals | `maritime` |
| Economic series and dated observations | `macro` |
| AI models, compute and hardware | `epoch` |
| Tone and share of voice | `media_intel` |
| Contract odds and rules | `prediction_market` |
| Web corroboration / source extraction | `web_research` |

List the category to check availability and plan requirements. Some REST capabilities (including
bulk-export workflows) have no MCP operation: use documented REST in a builder environment with
configured credentials, or explain the limitation. Never synthesize an unadvertised tool.

## Read the receipt before the answer

- Inspect `meta.coverage`, served/missing dates, completeness and source freshness. A missing
  `window_complete: true` does not establish complete coverage. Empty or withheld is not zero.
- Preserve pagination and truncation warnings. A sample or bounded semantic candidate pool is
  not the population; exhausting that pool does not prove exhaustive recall.
- Use each operation's pagination model (opaque cursor, offset, or versioned membership).
  Keep filters fixed. Stop at the user's budget and disclose unfinished pages.
- Keep null metrics null. Reservation counters are not delivered usage; pending usage is unknown.
- Link returned public record/source URLs. Entity-linked coverage is not proof of involvement.
  Do not invent URLs, quotes, citations or result counts.
- Widgets are optional. Summarize the useful data and caveats in text when UI does not render;
  never ask a CLI user to inspect an unavailable card. `gdelt-event` fences are Agent UI-specific.

## Writes and access errors

Use the descriptor's `call_with`. Monitor and Situation writes use `gdelt_cloud_tool_write`.
Preview is a read; saving, enabling and sending a test delivery are distinct actions. Obtain the
user's authorization for the actual scope/destination before a write; a skill is not permission.
Preserve documented idempotency keys across uncertain retries and inspect resulting state.
Do not promise idempotency for operations that do not support it.

401: reconnect OAuth or verify the configured key without exposing it. 403: explain workspace or
plan restrictions and offer https://gdeltcloud.com/pricing when relevant. 429: distinguish a
retryable rate limit from exhausted quota. A service error is not an empty result. Never switch
identities or transports to evade access controls. Docs-only research can continue without a key.
