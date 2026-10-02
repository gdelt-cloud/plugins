# GDELT Cloud plugins

Point your coding agent at [GDELT Cloud](https://gdeltcloud.com) — a clean event database over the
world's news. Coded events in a CAMEO+ / ACLED-aligned taxonomy, deduplicated story clusters with
their source articles, entities resolved to one spine across news, SEC filings, sanctions lists and
asset registries, and the physical assets underneath.

Three jobs this is built for:

- **Software against the REST API** — `https://gdeltcloud.com/api/v2`, an API key, your language.
- **Agents on the MCP server** — the same data as tools, with progressive discovery.
- **Conversational use** in a chat client that can reach an MCP server (ChatGPT, Claude, Cowork).

The MCP servers give an agent the data. The skills give it the procedures for using the data
*correctly*, which is the harder half: almost every way of getting this API wrong returns `200`
with a plausible-looking answer rather than an error.

## Install

### Claude Code

```bash
/plugin marketplace add gdelt-cloud/plugins
/plugin install gdelt-cloud@gdelt-cloud
```

You will be asked for an API key on enable. Create an account at
[gdeltcloud.com/api-keys](https://gdeltcloud.com/api-keys). New accounts get a 7-day evaluation with
1,000 QU, REST API and MCP access, and up to three daily email Monitors; bulk downloads remain
paid-only. After the evaluation, Free keeps the UI, API Arena, saved Monitor settings and previews
with 50 QU a month; API, MCP and scheduled Monitor execution require active access. Eligible
existing personal workspaces can claim a one-time 500 QU grant valid for 7 days.

Verified Academic & Research accounts get permanent no-cost access with 5,000 QU a month, API and
MCP access, five daily Monitors, Monitor webhooks, bulk downloads, and every data surface; Briefs are
excluded.

Non-interactively:

```bash
claude plugin marketplace add gdelt-cloud/plugins
claude plugin install gdelt-cloud@gdelt-cloud --config gdelt_api_key=gdelt_sk_...
```

### Codex

```bash
codex plugin marketplace add gdelt-cloud/plugins
codex plugin add gdelt-cloud@gdelt-cloud
```

**Both commands.** `marketplace add` only registers the source — run `codex plugin list` after it
alone and the plugin reads `not installed`, which looks identical to a broken install. This README
used to show only the first line.

Then `export GDELT_API_KEY=gdelt_sk_...` — Codex reads the bearer token from the environment rather
than prompting, so export it in whatever shell profile Codex inherits before starting it.

### Just the docs, no account

If you only want your agent to read the API reference while it writes code:

```bash
/plugin install gdelt-cloud-docs@gdelt-cloud
```

No key, no signup. It wires the documentation MCP server only.

### Any other MCP client

Two servers, both Streamable HTTP:

| | URL | Auth |
|---|---|---|
| Data | `https://gdelt-cloud-mcp.fastmcp.app/mcp` | `Authorization: Bearer gdelt_sk_…`, or OAuth |
| Docs | `https://docs.gdeltcloud.com/mcp` | none |

These are JSON-RPC transports. A plain browser GET may return 405; verify a connection by MCP
initialization/discovery, not by treating a browser page as the protocol test.

The custom Manufact endpoint `https://mcp.gdeltcloud.com/mcp` is still launch-gated. The public
configs retain Horizon until TLS and client acceptance pass; do not switch just because the
new URL appears in migration documentation.

### By hand, without the plugin system

If the marketplace is unavailable or you want the skills in a project without installing a plugin,
wire it yourself. Three steps:

```bash
# 1. skills — plain directories, each holding a SKILL.md
git clone https://github.com/gdelt-cloud/plugins /tmp/gdelt-cloud-plugins
mkdir -p .claude/skills
cp -R /tmp/gdelt-cloud-plugins/plugins/gdelt-cloud/skills/* .claude/skills/
cp -R /tmp/gdelt-cloud-plugins/plugins/gdelt-cloud/workflows .claude/

# 2. key
export GDELT_API_KEY=gdelt_sk_...
```

3. a project `.mcp.json`:

```json
{
  "mcpServers": {
    "gdelt-cloud": {
      "type": "http",
      "url": "https://gdelt-cloud-mcp.fastmcp.app/mcp",
      "headers": { "Authorization": "Bearer ${GDELT_API_KEY}" }
    },
    "gdelt-cloud-docs": { "type": "http", "url": "https://docs.gdeltcloud.com/mcp" }
  }
}
```

**Use `${GDELT_API_KEY}`, not `${user_config.gdelt_api_key}`.** The `user_config` form is resolved by
the plugin system and by nothing else — in a hand-written `.mcp.json` it is passed through as a
literal string and the server answers with an authentication error that says nothing about the real
cause.

**Restart the session after adding an MCP server.** Servers are connected at startup; until you
restart, the tools are simply absent, which reads as a broken install.

## What you get

**`gdelt-cloud`** wires both MCP servers and ships eight workflow skills. The three larger skills
have short entrypoints and packaged references that load only when needed. It supports reads,
interactive results where the host supports them, and authorized workspace writes.

| Client task | Start here | What does not transfer automatically |
|---|---|---|
| ChatGPT / Claude web or desktop research | Remote data connector with OAuth; inspect live tools and read the server's task resource if needed | Installing a local coding plugin does not configure a separate web conversation |
| Codex / Claude Code builder | This marketplace plugin, then `building-with-the-api` | REST examples are not literal MCP arguments; inspect the live schema |
| No account / schema exploration | `gdelt-cloud-docs` | Documentation tools do not return authenticated data |

The registered/published web listing is a separate release surface. Server resource reads work
only when supported by the host or its `read_resource` compatibility tool. Do not claim local
skills are automatically installed by adding an MCP URL. Current [OpenAI skill import](https://developers.openai.com/plugins/build/mcp-server#import-skills-from-the-mcp-server)
uses a bounded submission-time snapshot; it is not a live sync of this repository.

### Try a bounded task

- “Show three events in Iran in the last seven days, with sources and coverage limitations.”
- “Resolve this company, then show which asset and filing sources can identify it.”
- “Preview a supplier Monitor; do not save or enable it yet.”
- “Build a paginated REST client that preserves missing-date and quota errors.”

Read [MCP workflows](plugins/gdelt-cloud/skills/getting-started/references/mcp-workflows.md)
for all 14 category routes, discovery, writes, errors and text-only fallback. `_tool_list` and
`_tool_get` reveal operations and schemas; `_tool_call` executes reads; `gdelt_cloud_tool_write`
executes authorized Monitor/Situation changes. The docs-only product exposes no data-server writes.
The same connected tool may be gated by account/workspace entitlement; visibility is not access.

The account actions are ordinary links: [Create account](https://gdeltcloud.com/signup) and
[View plans](https://gdeltcloud.com/pricing). No plugin performs signups or purchases for the user.

### Skills


| Skill | For |
|---|---|
| `getting-started` | The rules that decide whether a call is correct, identity resolution first, and what a Free account keeps after the evaluation. Short onboarding entrypoint with optional conventions and MCP reference. |
| `core-api` | Maps a plain-English ask onto the right endpoint — Events, Stories, Situations, Countries, activity, offices — and the minimal correct call |
| `building-with-the-api` | Writing CODE against it: paging to the end, truncated vs empty, caching, cadence — plus first principles and four worked builds |
| `hosted-monitors` | Resolve → preview → create → inspect: Event/Story Monitors and query Monitors over Events, Stories, Entities or Activity, signed webhooks, exact replay |
| `war-risk-underwriting` | Chokepoint and route monitors, political-violence exposure, marine war-risk briefs |
| `counterparty-exposure` | Company → hierarchy → assets → news → filings → government exposure |
| `supplier-disruption` | N suppliers × M sites, daily digest with an escalation threshold |
| `country-risk-series` | Atlas GPR and Posture as a frame you can join to returns |

**`gdelt-cloud-docs`** wires the documentation server and a focused `api-reference` skill. It needs no account and exposes no data-server connection.

## Why the skills exist

Almost every way of getting this API wrong returns `200` with a plausible-looking result rather than
an error. `bbox` axis order differs between the core and maritime families. A `/summary` endpoint
takes a smaller parameter set than its list sibling, and current descriptor-backed endpoints reject unknown parameters while some compatibility
surfaces report `applied_filters.ignored`. Six identifier spaces coexist and the wrong one
returns an empty result. Each skill front-loads the ones that matter for its workflow.

If you build without the skills, at least read
[docs.gdeltcloud.com/AGENTS.md](https://docs.gdeltcloud.com/AGENTS.md) — it is the same rules,
shorter.

## Working demos

Complete reference implementations, each a self-contained Python project — static HTML dashboards,
a Monitor webhook receiver, and end-to-end Monitor workflows:
<https://github.com/gdelt-cloud/demos>

## Links

The data plugin's 0.8.2 candidate includes canonical workflow bundle
`2026.10.02.3`, exported from the monorepo MCP package. Existing skill names route
to the packaged `workflows/` files. `python scripts/validate.py` checks their
SHA-256 manifest as well as client manifests and packaged references. Client
setup stays separate from shared workflows. Imported skills are snapshots; a
new release must be installed to receive updated guidance. Public MCP connection
defaults remain on Horizon until the Manufact launch gates pass.

- Docs — <https://docs.gdeltcloud.com>
- Page index for agents — <https://docs.gdeltcloud.com/llms.txt>
- API reference — <https://docs.gdeltcloud.com/api-reference>
- Setup — <https://gdeltcloud.com/build>

Issues and questions: <hello@gdeltcloud.com>

MIT licensed. The data carries its own per-dataset licences, published at
<https://docs.gdeltcloud.com/data/catalog>.

## Cursor

Cursor reads `.cursor-plugin/plugin.json` and a `.cursor-plugin/marketplace.json` at the repository
root. Its skills convention is the SAME as Claude Code's and Codex's — a `skills/` directory of
subdirectories each holding a `SKILL.md` — so the same skills are shared across the three clients
with no duplication. Only the manifests and the MCP config differ.

Two differences worth knowing: Cursor declares user-supplied values through a JSON Schema under
`variables` (Claude Code uses `userConfig`, Codex uses `bearer_token_env_var`), and it interpolates
them as `${GDELT_API_KEY}`. Installation is through the Cursor dashboard under **Plugins** rather
than a CLI command.

## Why the Claude manifests carry no `version`

Deliberate, and not an oversight to tidy up. The Codex manifests carry `version` because the Codex
spec requires it. Claude Code treats it as optional metadata, and a plugin with a pinned version can
be served from cache until that number changes — which means a docs or skill fix silently does not
reach anyone who already installed. Omitting it makes every install fetch the current contents.

If you add one, you own bumping it on every change, including one-line skill edits.
