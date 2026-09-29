---
name: gdelt-cloud-hosted-monitors
description: Preview, create, pause or inspect a hosted GDELT Cloud Monitor and its delivery or replay. Supports Event/Story questions and query Monitors over Events, Stories, Entities or activity. Explains watching Situation evidence, Country publications and office changes. Use for recurring monitoring, not a one-off answer or an analytical Brief.
---

# Preview, authorize, save, inspect

Hosted Monitors evaluate one supported question on an hourly/daily schedule. They are shared
workspace state. A request to investigate a topic is not a request to create a Monitor or send
email/webhooks. A Monitoring Brief is a separate product.

Read [MCP workflows](../getting-started/references/mcp-workflows.md) for connection, discovery,
coverage and error handling. Read [Monitor specifications and replay](references/details.md)
when preparing a Monitor: it contains the subject/criteria shapes, checkpoint semantics,
webhook handling and exact replay requirements.

1. Resolve named subjects with `unified_entity_search`; preserve ambiguity and returned IDs.
2. Inspect `preview_monitor`, prepare one supported specification and execute it through
   `gdelt_cloud_tool_call`. Preview consumes its documented Query Units but does not save or send.
3. Inspect the preview's actual matches, coverage, dates and execution receipts. Partial history
   cannot establish a quiet interval. Explain the intended scope, cadence and destination.
4. After authorization, inspect `create_monitor` and use its `call_with` wrapper:
   `gdelt_cloud_tool_write`. To save a draft, explicitly pass `enabled=false`; do not depend on
   defaults. Enabling, configuring delivery and sending a test webhook are separate actions.
5. Read back the saved Monitor and later run state. Preserve one-time webhook secrets in the
   user's secret store; never put them in chat, code examples or logs.

The schema's `tool_arguments` are flattened MCP arguments, not necessarily the REST request
body. The read wrapper rejects mutations. Read/write annotations do not replace authorization.
Do not create another Monitor after an ambiguous timeout without checking whether it was saved.

Query scheduling tracks newly committed qualifying publications and late arrivals. Preserve
source-request provenance; do not silently change semantic matching to lexical. Situations,
Countries and offices are not direct subjects: monitor their supported Event/Story/activity
inputs and explain that scope. Do not promise a Situation-change subscription.

Inspect `get_monitor_run_matches` for a run's recorded matches and its own pagination contract.
Follow returned replay requests when needed. Retain types, IDs, completeness and exact windows.
An empty successful page, a failed read and an incomplete run are different states.

Offer https://gdeltcloud.com/pricing for a genuine access/slot restriction; do not upgrade or
change plans. Preserve saved configuration after access expiry. Use custom client logic only
for requirements outside hosted Monitors, not to bypass an entitlement.
