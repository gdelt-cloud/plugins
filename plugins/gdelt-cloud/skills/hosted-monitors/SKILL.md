---
name: gdelt-cloud-hosted-monitors
description: Use this skill when a user wants GDELT Cloud to run a recurring hosted Monitor, alert on new Event or Story matches, manage a Monitor through REST or MCP, receive signed webhooks, or inspect and replay Monitor runs. It covers the supported resolve → preview → create → inspect → replay workflow. Do not use it for a one-off query, a Monitoring Brief, a historical risk index, or composite logic that requires several API calls and custom state.
---

# Hosted Monitors

Hosted Monitors run one structured Event/Story question on an hourly or daily schedule. They are
organization-shared, scheduled checks consume no Query Units, and accepted on-demand Previews cost
1 Query Unit. A Monitor reports **new coverage in its schedule window**; it is not a sentiment,
risk-score, anomaly, or material-involvement claim.

Use a Hosted Monitor when one canonical question can be expressed by its subject plus criteria. Use
client polling when the job needs several endpoints, a custom baseline, joins to private data,
arbitrary state, or a schedule other than hourly/daily. A Monitoring Brief is a generated analytic
memo and is a separate product.

## Supported workflow

### 1. Resolve named entities before drafting

For a person, organization, or place, call the public resolver:

```http
GET /api/v2/search?q=ASML&type=organization&limit=10
```

The canonical public call accepts only `q`, optional `type`, and `limit`. It returns ranked
candidates whose `entity_id` is a terminal spine `e_…` id. Present ambiguous candidates with their
name, type, country, match reason, sources, and identifiers; do not choose a weak match silently.
Store the selected terminal ids and pass them unchanged to the Monitor.

The MCP server uses progressive discovery. Inspect the underlying schema, then call it:

```text
gdelt_cloud_tool_get(tool_name="unified_entity_search")
gdelt_cloud_tool_call(
  tool_name="unified_entity_search",
  tool_arguments={"q":"ASML", "type":"organization", "limit":10}
)
```

Do not choose the underlying `search_entities` tool for this workflow: that is the news-entity
surface, while `unified_entity_search` is the cross-source resolver of record.

### 2. Draft one supported question

Choose exactly one subject:

- `entity`: 1–25 confirmed terminal `e_…` ids; public v1 supports `match: "coverage"` only.
- `facility`: one canonical `f_…` or `s_…` facility id plus a radius.
- `place`: latitude, longitude, and radius.
- `geography`: countries, region, or continent; `admin1` requires exactly one country.
- `topic`: semantic text belongs in `criteria.search`, not on the subject.

Entity coverage means a resolved entity appears in the Story coverage. A linked Event does **not**
prove that entity acted in or was materially affected by the Event. Investigate after a trigger
before making that claim.

Criteria select `events`, `stories`, or `events_and_stories`. Keep taxonomy values in their family:

```json
{
  "family_filters": {
    "cameoplus": { "domains": ["ECONOMIC"], "subcategories": [] },
    "conflict": { "categories": ["Protests"], "subcategories": [] },
    "story": { "categories": ["cameoplus_economic"] }
  }
}
```

CAMEO+ and Conflict filters require Event data; Story filters require Story data. Ask the docs MCP
for current accepted values instead of inventing a category. `criteria.search` is semantic content
matching and may refine any subject. Omit `criteria.search` entirely for broad structured-subject
coverage with no semantic refinement; do not send an empty string. Geography belongs either to a
geography subject or to criteria for another subject, never both. Duplicate event rows are not a
public Monitor option; the service evaluates its adjudicated incident view automatically.

Public v1 supports only `trigger: {"type":"new_matches"}`. Do not request `volume_spike`, entity
`material`, or entity `actor`; those are deferred compatibility values, not public write options.

### 3. Preview before consuming a slot

REST:

```http
POST /api/v2/monitors/preview
```

MCP: inspect `preview_monitor` with `gdelt_cloud_tool_get`, then execute it through
`gdelt_cloud_tool_call`. Its arguments are the flattened form published by that tool schema; do not
guess from the REST JSON body.

**Two execution wrappers, and picking the wrong one fails the call.** `gdelt_cloud_tool_call` is
read-only; every tool that creates, updates, pauses, deletes or *sends* something runs through
`gdelt_cloud_tool_write` instead. Passing a mutating tool to `gdelt_cloud_tool_call` is refused —
it is not a soft warning. `preview_monitor` is deliberately a READ: it costs a Query Unit but
creates nothing, so it belongs on `gdelt_cloud_tool_call`. Each entry in `gdelt_cloud_tool_list`
names its own wrapper in `call_with`; read that rather than inferring from the verb.

Preview and create accept the same Monitor specification. Read the returned rows, not only the
status and count. Confirm that geography, taxonomy, semantic topic, and entity coverage match what
the user meant. Compare a meaningful negative or mirror control when a silently ignored filter
would produce a plausible result. A successful Preview costs 1 Query Unit, creates no Monitor, and
sends no external delivery for an API-key caller. In the signed-in web Builder, every Preview also
performs a real, signed `monitor.test` round-trip to a two-minute first-party receiver and shows the
actual request and response transcript. That demonstration is free, creates no saved Monitor or
run, and does not prove that a user's eventual external endpoint works. The API-key REST response
envelope is `{ "success": true, "preview": { ... } }`; do not invent top-level preview fields.

Example REST body:

```json
{
  "name": "Critical supplier disruption",
  "description": "New disruption coverage for the procurement response team.",
  "subject": {
    "type": "entity",
    "entity_ids": ["e_0123456789abcdef"],
    "match": "coverage"
  },
  "criteria": {
    "data": "events_and_stories",
    "search": "factory outage, production disruption, logistics interruption",
    "countries": [],
    "family_filters": {
      "cameoplus": { "domains": ["ECONOMIC"], "subcategories": [] },
      "story": { "categories": ["cameoplus_economic", "cameoplus_infrastructure"] }
    },
    "fatalities_only": false
  },
  "trigger": { "type": "new_matches" },
  "schedule": { "cadence": "hourly", "timezone": "UTC", "daily_hour": 8 },
  "delivery": { "email": false, "webhook_url": "${WEBHOOK_URL}" }
}
```

### 4. Create and retain operation-only secrets

REST: `POST /api/v2/monitors`. MCP: inspect `create_monitor` with `gdelt_cloud_tool_get`, then
pass that underlying tool name and its published arguments to **`gdelt_cloud_tool_write`** —
creation changes state, so `gdelt_cloud_tool_call` refuses it.

Creation requires an organization owner/admin and is subject to the plan's Monitor count, cadence,
and webhook entitlement. The response returns the stored canonical Monitor. If webhook delivery is
first configured, `webhook_signing_secret` is returned **once**. Store it immediately; list/get
responses correctly never reveal it.

REST webhook configuration is a flat delivery field, not a nested webhook object:

```json
{ "delivery": { "email": false, "webhook_url": "https://risk.example/webhooks/gdelt" } }
```

Create and PATCH return
`{ "success": true, "monitor": { ... }, "webhook_signing_secret": "..." | null }`. The stored
Monitor uses the response shape below; request bodies use `delivery.webhook_url`, while stored
state exposes the destination as `delivery.webhook.endpoint`:

```json
{
  "delivery": {
    "email": false,
    "webhook": {
      "configured": true,
      "endpoint": "https://risk.example/webhooks/gdelt",
      "consecutive_failures": 0,
      "last_success_at": null,
      "last_failure_at": null
    }
  }
}
```

PATCH `delivery.webhook_url` to `null` to remove webhook delivery. Set
`rotate_webhook_secret: true` to invalidate the old signing secret and receive a replacement once;
changing unrelated fields does not rotate it. Never log the secret or put it in a URL, source file,
or example as a real value.

The underlying MCP management tools split across the two wrappers. Reads —
`list_monitors`, `get_monitor`, `list_monitor_runs`, `get_monitor_run` — run through
`gdelt_cloud_tool_call`. Writes — `set_monitor_enabled`, `configure_monitor_delivery`,
`test_monitor_delivery` (it sends a real signed webhook to an external destination),
`update_monitor`, `run_monitor_now` and `delete_monitor` — run through `gdelt_cloud_tool_write`.
Discover each with `gdelt_cloud_tool_get`, which names the correct wrapper in `call_with`. Confirm the stored subject,
criteria, cadence, enabled state, and delivery health after mutation. Delete only when the user
explicitly asks; pausing is the reversible choice.

REST equivalents:

```text
GET    /api/v2/monitors
GET    /api/v2/monitors/{id}
PATCH  /api/v2/monitors/{id}
DELETE /api/v2/monitors/{id}
POST   /api/v2/monitors/{id}/test-delivery
```

### 5. Inspect runs and replay complete results

Use the underlying MCP tools `list_monitor_runs`, then `get_monitor_run`, through the same
progressive get/call wrappers. REST equivalents:

```text
GET /api/v2/monitors/{id}/runs
GET /api/v2/monitors/{id}/runs/{run_id}
```

The detailed run adds:

- `summary.total_matches`: complete new-match count for the immutable schedule window.
- `summary.included_matches`: representative matches retained inline, at most ten.
- `summary.truncated`: whether more matches exist.
- `matches`: tagged Event/Story cards; Event wrappers identify CAMEO+ vs Conflict.
- `replay_requests`: canonical Core API calls for retrieving the complete result.

Execute every replay request when `truncated` is true or completeness matters. Mixed-data Monitors
return separate Event and Story requests. Multi-entity Monitors return one request per entity and
endpoint; union results by `(kind, id)` so a Story mentioning two tracked entities is not counted
twice. Walk `pagination.next_cursor` until it is null.

Use each returned `replay_requests` method, URL, and `exact_window_filter` verbatim. Never reconstruct
query parameter names or synthesize a replay URL from memory. The REST run-detail envelope is
`{ "success": true, "monitor": { ... }, "run": { ... } }`; `summary`, `matches`, and
`replay_requests` are inside `run`.

Replay calls are ordinary QU-backed API retrieval. Their date parameters safely cover the run, and
`exact_window_filter` gives the timestamp field plus the half-open `[start, end)` boundary. Apply
that exact boundary to replayed rows before reconciling them with the run.

## Signed webhook handling

Production destinations must be public HTTPS. Localhost HTTP is only for an explicitly enabled
local-development receiver. Verify the signature over the raw request bytes before parsing JSON:

```text
HMAC_SHA256(secret, X-GDELT-Timestamp + "." + raw_body)
```

Compare it to `X-GDELT-Signature` (`v1=<hex>`) in constant time, enforce a short timestamp replay
window, verify the header event id equals the body `id`, and persist `X-GDELT-Event-Id` with the
application side effect. Retries keep the event id and body stable while timestamp, signature, and
`X-GDELT-Delivery-Attempt` change. A `monitor.test` event has no run or matches; a
`monitor.triggered` event carries the run window, trigger counts, and representative matches.

## Final honesty checks

- A quiet run and a broken Monitor are different: inspect last-checked state and saved runs.
- Coverage is evidence intake, not materiality, causality, sentiment, or risk scoring.
- `total_matches` is not the number of inline cards; inspect `included_matches` and `truncated`.
- A replay is complete only after every request, cursor, exact-window filter, and cross-request
  deduplication is handled.
- Scheduled execution costs 0 QU; Preview costs 1 QU; replay and follow-up API calls use their
  normal Query Units.
