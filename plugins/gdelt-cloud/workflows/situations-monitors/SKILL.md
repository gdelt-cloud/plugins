---
name: situations-monitors
description: Explore or create Situations and preview or manage Monitors, with explicit state-change boundaries.
---

# Situations Monitors

Situations organize persistent topics and linked evidence; Monitors save repeatable detection rules and delivery settings. Use `gdelt_cloud_tool_list(section="situations")` or section `monitors`, then inspect exact operations. Search existing Situations before considering creation; a user asking for a one-time answer does not authorize a saved object.

## Minimal workflow
Read `search_situations`/`get_situation` and linked Stories/Events for an existing topic. To propose monitoring, inspect `preview_monitor` and preview the user's actual filters through `gdelt_cloud_tool_call`; preview creates nothing but is metered. Report evidence, coverage and estimated matches. Only an authorized save/update/delete or test delivery uses `gdelt_cloud_tool_write`. Do not send a test webhook as an implicit preview.

REST: `/api/v2/situations`, `/api/v2/situations/{story_id}` and linked evidence endpoints; `/api/v2/monitors/preview` for preview and documented `/api/v2/monitors` operations for persistence. Discover required configuration and supported destinations before presenting a concrete save. A company watch or supply-chain watch can stop after preview.

Incomplete coverage cannot establish a quiet interval or complete a scheduled checkpoint. Keep missing dates and retryable pages explicit. Never advance durable pagination from filtered absence alone. A Monitor is not an arbitrary agent that researches the whole web; describe its actual dataset, matching and delivery limits. Monitoring Brief delivery remains separately gated/paused where advertised. Do not imply it is enabled by a Monitor subscription.

Cite returned evidence and product links; distinguish saved configuration from preview results and delivered notifications. See getting started (`skill://getting-started/SKILL.md`) and building (`skill://building-with-api/SKILL.md`).

After an authorized save, confirm the returned Monitor name, actual enabled/paused state, schedule/timezone, saved scope and configured delivery channels. A branded receipt can show these facts; it must not imply a Preview saved anything or a saved configuration delivered a notification. Keep one-time webhook signing secrets out of presentation components and screenshots. Offer to refine scope or inspect the first run only when useful.


## Interactive draft confirmation
For editable setup, discover the `preview_monitor` schema, then call `gdelt_cloud_monitor_form` with those arguments nested in `tool_arguments`. The mini form is prepopulated from validated arguments and displays a small match/coverage receipt. A temporary execution failure can retain the editable draft while the tool honestly reports a failed preview and unavailable matches. Authentication, validation, plan and quota refusals do not open a fallback form. Do not automatically retry, change the user's scope or infer zero matches from unavailable results. Some clients may suppress an app on a failed tool result; explain the unsaved draft in text if no form renders. Ordinary `preview_monitor` through the read wrapper stays in native chat without opening an app block. The user can adjust name, readable country/category/subcategory choices, daily time/timezone, exact target/advanced filters and email or webhook delivery, then preview again (1 QU for a successful execution) or explicitly confirm creation. Editing and Preview never save. Save defaults to paused; starting scheduled checks is a separate visible choice. The form calls the same authenticated read/write wrappers and respects host approval and plan checks. It does not call REST directly. Private webhook destinations are omitted from component metadata and model-context updates. A user can enter an HTTPS destination in the form; an existing omitted destination must be re-entered or explicitly disabled. Preview never sends a webhook; actual save still requires server destination and entitlement validation. Do not request signing secrets in the form. If the host cannot run component tools, continue through normal conversational confirmation using the visible draft or the website. Never tell the user a control is available unless the client actually renders it.

For a watch of a named event type, inspect the current taxonomy and prefer its supported coded predicate when it answers the user's request. For example, transport disruptions occurring in France can use an Events query with Infrastructure → Transport Disruption and event-location matching, rather than inventing a broad semantic Events/Stories keyword sweep. Explain the selected records and geographic matching in readable language, and keep exact filter codes in advanced settings or a requested builder recipe. Broader reporting or actor-country coverage is a separate choice to offer when it serves the user's decision; do not silently broaden a location watch.

A successful creation requires the positive API receipt and returned Monitor identity. Disable duplicate submissions; an ambiguous timeout requires checking existing Monitors before another create attempt. Saving is not delivery, Preview history is not sent on first enablement, and a new-match Monitor is not an aggregate metric threshold alarm. Keep country/location/actor semantics and supported geographic filters consistent with the analysis being watched.


Compose only supported predicates. Separate metric minimum filters are combined by the API's documented logic; do not promise an arbitrary OR across magnitude/systemic/propagation/market thresholds or a taxonomy exception in one Monitor. If the desired rule cannot be expressed, explain the limitation, offer a simpler supported rule or explicitly separate Monitors, and preview the chosen shape. A recommendation is not a tested filter until the exact configuration has been validated.

For a query subject, keep caller pagination, limits and discovery dates in `source_request` where the schema supports them, not in `query_params`; the Monitor controls evaluation windows and pagination. After a source failure, report the unavailable preview; do not silently reinterpret its scope or claim zero matches.
