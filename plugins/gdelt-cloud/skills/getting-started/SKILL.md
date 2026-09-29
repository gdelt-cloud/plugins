---
name: gdelt-cloud-getting-started
description: Connect to GDELT Cloud, diagnose missing tools or access errors, and choose a first research or builder workflow. Covers Events, Stories, entities, Situations, Countries, publication activity and public offices. Use for onboarding; use the matching domain skill for an established workflow.
---

# Start with the user's task

For a quick answer, use the connected MCP tools. For an application, use REST and the
building-with-the-api skill. For recurring delivery, use hosted-monitors. Local plugin files
and a remote MCP connection are different installation paths; check which tools the host exposes.

## Connect and verify

- Data: `https://gdelt-cloud-mcp.fastmcp.app/mcp` during the launch transition. The planned
  `https://mcp.gdeltcloud.com/mcp` replacement is not an instruction to switch before verification.
- Documentation: `https://docs.gdeltcloud.com/mcp`, no account required. It provides reference
  material, not live customer data. Discover its current tools instead of guessing their names.
- ChatGPT and Claude web/desktop: use the host's remote MCP connection and OAuth flow where
  supported. A missing API-key field does not mean only documentation is available. Local
  marketplace skills do not automatically appear in a separate web conversation.
- Codex and Claude Code: use the plugin's client-specific configuration described in the README.
  Keep API keys in the host's secret configuration or environment, never in a prompt or source file.
- Check that `gdelt_cloud_tool_list` is available. If only documentation search appears, explain
  the missing data connection. Do not interpret missing tools or 401/403 as empty data.

## First successful MCP workflow

Read [MCP workflows](references/mcp-workflows.md) for category routing, exact wrapper calls,
coverage, UI fallback and authentication recovery. It is enough for a first bounded query.
Only load [detailed API conventions](references/details.md) for identity-space joins,
geography, bulk exports, access rules or a REST integration. Do not load every domain skill.

Use list → get → call for the selected category. Discovery is free; data queries may consume
Query Units. Resolve named counterparties before joining datasets, but a country-scoped count
does not need an extra person/company lookup. Use a small result limit for a conversational
sample; use summaries for counts and bounded pagination for an explicit export.

## Access and account navigation

Create an account at https://gdeltcloud.com/signup; compare plans at https://gdeltcloud.com/pricing.
Offer these links when the user wants access or a server error indicates it is needed. Do not
interrupt a successful research answer with an unrelated sales pitch. Widget buttons use host
navigation; in text-only clients provide normal clickable links. Reconnect after an access change
if the host still has a stale authorization session. Never sign up, subscribe or upgrade for them.

New accounts receive a 7-day evaluation with 1,000 QU. After evaluation, Free retains web/API Arena
use with 50 QU monthly and saved settings; programmatic access and scheduled execution need active
access. Eligible existing personal workspaces can claim a one-time 500 QU grant valid for 7 days.
Academic access has separate verification and entitlements. Read current account/endpoint
capabilities for a decision; plan-service errors are not permission to bypass a restriction.
