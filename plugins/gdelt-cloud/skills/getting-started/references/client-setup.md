# Client connection and access

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

## Access and account navigation

Create an account at https://gdeltcloud.com/auth/sign-up; compare plans at https://gdeltcloud.com/pricing.
Offer these links when the user wants access or a server error indicates it is needed. Do not
interrupt a successful research answer with an unrelated sales pitch. Account links use website navigation; in text-only clients provide normal clickable links. Reconnect after an access change
if the host still has a stale authorization session. Never sign up, subscribe or upgrade for them.

New accounts receive a 7-day evaluation with 1,000 QU. After evaluation, Free retains web/API Arena
use with 50 QU monthly and saved settings; programmatic access and scheduled execution need active
access. Eligible existing personal workspaces can claim a one-time 500 QU grant valid for 7 days.
Academic access has separate verification and entitlements. Read current account/endpoint
capabilities for a decision; plan-service errors are not permission to bypass a restriction.
