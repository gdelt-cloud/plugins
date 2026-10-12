---
name: situations-monitors
description: Explore or create Situations and preview or manage Monitors, with explicit state-change boundaries.
metadata:
  tool_exposure: named
---

# Situations Monitors

Situations organize persistent topics and linked evidence; Monitors save repeatable detection rules and delivery settings. Call the named Situation or Monitor operation directly; optional `get_data_catalog(domain="gdelt_cloud", section="situations")` or section `monitors` explains related operations when needed. Search existing Situations before considering creation; a user asking for a one-time answer does not authorize a saved object.

## Minimal workflow
Read `search_situations`/`get_situation` and linked Stories/Events for an existing topic. To propose monitoring, inspect `preview_monitor` and preview the user's actual filters with `preview_monitor`; preview creates nothing but is metered. Report evidence, coverage and estimated matches. Only an authorized save/update/delete or test delivery uses the corresponding named mutation. Do not send a test webhook as an implicit preview.

REST: `/api/v2/situations`, `/api/v2/situations/{story_id}` and linked evidence endpoints; `/api/v2/monitors/preview` for preview and documented `/api/v2/monitors` operations for persistence. Discover required configuration and supported destinations before presenting a concrete save. A company watch or supply-chain watch can stop after preview.

Incomplete coverage cannot establish a quiet interval or complete a scheduled checkpoint. Keep missing dates and retryable pages explicit. Never advance durable pagination from filtered absence alone. A Monitor is not an arbitrary agent that researches the whole web; describe its actual dataset, matching and delivery limits. Monitoring Brief delivery remains separately gated/paused where advertised. Do not imply it is enabled by a Monitor subscription.

Cite returned evidence and product links; distinguish saved configuration from preview results and delivered notifications. See getting started (`skill://getting-started/SKILL.md`) and building (`skill://building-with-api/SKILL.md`).

## Query Monitor: the same scope in MCP and REST

This draft watches new Transport Disruption Events occurring in France. The current taxonomy pair is Infrastructure / `IN02`; use optional taxonomy lookup if unfamiliar. It includes aviation and shipping as well as road and rail. Run Preview to inspect evidence and coverage; execute the creation example only after the user authorizes saving this scope and email delivery.

The named MCP Preview uses flattened arguments:

```python
preview_monitor(
    name="France transport disruptions", subject_type="query",
    query_endpoint="/api/v2/events",
    query_params={"country": "FRA", "country_match": "location",
                  "category": "INFRASTRUCTURE", "subcategory": "IN02"},
    cadence="daily", timezone="UTC", daily_hour=8, email=False, history_days=7)
```

Its exact REST equivalent is `POST /api/v2/monitors/preview` with this JSON body:

```json
{
  "name": "France transport disruptions",
  "subject": {
    "type": "query",
    "endpoint": "/api/v2/events",
    "params": {
      "country": "FRA",
      "country_match": "location",
      "category": "INFRASTRUCTURE",
      "subcategory": "IN02"
    }
  },
  "criteria": {},
  "trigger": {"type": "new_matches"},
  "schedule": {"cadence": "daily", "timezone": "UTC", "daily_hour": 8},
  "delivery": {"email": false},
  "history_days": 7
}
```

The name and schedule are draft settings during Preview; they do not create scheduled work. `history_days` is Preview-only (7 or 30), and `enabled` is not a Preview field. Delivery is retained configuration, never a send. Read returned `query_window` and coverage for the historical scope rather than assuming the scheduled interval describes that history.

After explicit confirmation, the corresponding MCP creation saves paused:

```python
create_monitor(
    name="France transport disruptions", subject_type="query",
    query_endpoint="/api/v2/events",
    query_params={"country": "FRA", "country_match": "location",
                  "category": "INFRASTRUCTURE", "subcategory": "IN02"},
    cadence="daily", timezone="UTC", daily_hour=8, email=True, enabled=False)
```

Its exact REST equivalent is `POST /api/v2/monitors` with this JSON body:

```json
{
  "name": "France transport disruptions",
  "subject": {
    "type": "query",
    "endpoint": "/api/v2/events",
    "params": {
      "country": "FRA",
      "country_match": "location",
      "category": "INFRASTRUCTURE",
      "subcategory": "IN02"
    }
  },
  "criteria": {},
  "trigger": {"type": "new_matches"},
  "schedule": {"cadence": "daily", "timezone": "UTC", "daily_hour": 8},
  "delivery": {"email": true},
  "enabled": false
}
```

MCP `subject_type`, `query_endpoint` and `query_params` become REST `subject.type`, `subject.endpoint` and `subject.params`. MCP cadence/timezone/hour become `schedule`; email/webhook become `delivery`. All query filters stay string-valued in `subject.params`; the endpoint selects the data, so do not add `criteria.data` or legacy criteria filters. An empty `criteria` is accepted; it can also be omitted for a query body. Fixed dates and pagination belong only in optional provenance `source_request` (MCP top-level; REST `subject.source_request`), never the standing `params`.

Create has no `history_days`; `enabled=false` stores the rule without scheduling. At least email or an entitled HTTPS webhook destination is required for creation. For webhook delivery, MCP `webhook_url` maps to REST `delivery.webhook_url`; Preview never contacts it. Confirm a positive creation receipt and returned Monitor identity before saying it was saved. First enablement starts at that time and does not deliver Preview history. Enabling scheduled checks and sending a test notification are separate authorized actions. Preserve returned record links for the Preview's selected evidence; missing history stays explicit rather than implying a quiet week.

After an authorized save, confirm the returned Monitor name, actual enabled/paused state, schedule/timezone, saved scope and configured delivery channels. A branded receipt can show these facts; it must not imply a Preview saved anything or a saved configuration delivered a notification. Keep one-time webhook signing secrets out of presentation components and screenshots. Offer to refine scope or inspect the first run only when useful.


## Interactive draft confirmation
When the user requests review before saving, open `gdelt_cloud_monitor_form` and stop before creation. A preview, an initial request to set up a watch, or a paused default does not replace that requested confirmation. If the host cannot render the form, present the readable draft and wait for conversational confirmation. Direct writes remain available for explicitly authorized builder automation and for a save the user has already confirmed.

For editable setup, use the advertised `preview_monitor` parameters, then call `gdelt_cloud_monitor_form` with those fields as direct arguments. The mini form is prepopulated from validated arguments and displays a small match/coverage receipt. A temporary execution failure can retain the editable draft while the tool honestly reports a failed preview and unavailable matches. Authentication, validation, plan and quota refusals do not open a fallback form. Do not automatically retry, change the user's scope or infer zero matches from unavailable results. Some clients may suppress an app on a failed tool result; explain the unsaved draft in text if no form renders. Ordinary `preview_monitor` stays in native chat without opening an app block. The user can adjust name, readable country/category/subcategory choices, daily time/timezone, the record type, geography and categories, with email or webhook delivery, then open Advanced filters for refinements or schedule settings for time/cadence, and preview again (1 QU for a successful execution) or explicitly confirm creation. Editing and Preview never save. Save defaults to paused; starting scheduled checks is a separate visible choice. The form calls the same authenticated named read/mutation operations and respects host approval and plan checks. It does not call REST directly. Private webhook destinations are omitted from component metadata and model-context updates. A user can enter an HTTPS destination in the form; an existing omitted destination must be re-entered or explicitly disabled. Preview never sends a webhook; actual save still requires server destination and entitlement validation. Do not request signing secrets in the form. If the host cannot run component tools, continue through normal conversational confirmation using the visible draft or the website. Never tell the user a control is available unless the client actually renders it.

For a watch of a named event type, inspect the current taxonomy and prefer its supported coded predicate when it answers the user's request. For example, transport disruptions occurring in France can use an Events query with Infrastructure → Transport Disruption and event-location matching, rather than inventing a broad semantic Events/Stories keyword sweep. Explain the selected records and geographic matching in readable language, and keep exact filter codes in advanced settings or a requested builder recipe. Broader reporting or actor-country coverage is a separate choice to offer when it serves the user's decision; do not silently broaden a location watch.

Semantic text in a query Monitor is bounded relevance retrieval: a successful historical Preview does not establish that it can be saved or scheduled. Use structured filters when they represent the requested scope. If text is needed, explain and obtain the user's explicit choice of `search_mode=lexical`, which matches a literal phrase in served text and can miss related wording. Never silently convert a multiword semantic request into a literal phrase or imply it is an OR over words. The form disables Save for a semantic text query and exposes Text matching for this choice. Transport Disruption includes aviation and shipping as well as road and rail; disclose that scope and offer human triage or a narrower supported predicate. No road/rail-only promise without an actual validated filter.

A successful creation requires the positive API receipt and returned Monitor identity. Disable duplicate submissions; an ambiguous timeout requires checking existing Monitors before another create attempt. Saving is not delivery, Preview history is not sent on first enablement, and a new-match Monitor is not an aggregate metric threshold alarm. Keep country/location/actor semantics and supported geographic filters consistent with the analysis being watched.


Compose only supported predicates. Separate metric minimum filters are combined by the API's documented logic; do not promise an arbitrary OR across magnitude/systemic/propagation/market thresholds or a taxonomy exception in one Monitor. If the desired rule cannot be expressed, explain the limitation, offer a simpler supported rule or explicitly separate Monitors, and preview the chosen shape. A recommendation is not a tested filter until the exact configuration has been validated.

For a query subject, keep caller pagination, limits and discovery dates in `source_request` where the schema supports them, not in `query_params`; the Monitor controls evaluation windows and pagination. After a source failure, report the unavailable preview; do not silently reinterpret its scope or claim zero matches.

Prefer connected Monitors for company or facility watches: subject_type=connected, target_type=entity or facility, resolved target_ids and related_scope=direct or connected. Select source_updates from returned choices. Entity defaults include filings and relationships; facility defaults include facility records, observations and relationships. Nearby Events require an explicit facility nearby_radius_km opt-in. API-selected item limits are account-dependent (at most 25); do not infer access from the schema maximum. For edits, pass the saved monitor_id to Preview to preserve authorized existing scope. Preview never establishes a completed checkpoint from partial coverage.

The Monitor form offers seven subject buttons: Company or person, Facility, Country or region, Place on a map, Event type, News topic and Situation. Events/Stories is a separate results choice; new drafts do not offer the deprecated combined lane. Subcategories sit below their parent categories and follow the selected Event/Story lane. Advanced filters stay collapsed. A different subject requests an agent-resolved replacement draft through the conversation; it never silently changes target IDs or saves. If the client cannot send that request, offer its copyable text. Do not ask a
customer to edit JSON, enter an internal identity or know an endpoint. Resolved targets, supported
query refinements and source provenance are retained when advanced settings stay closed. For a
different company/facility or data source, resolve the new scope conversationally rather than
silently replacing it. Metric minimums, when offered for an Events query, are conjunctive CAMEO+
filters; they do not create an aggregate-change alert. Explain any blocking matching choice in
plain language. Preview details may be collapsed, but unavailable or partial coverage stays visible.
