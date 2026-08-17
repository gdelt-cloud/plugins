# GDELT Cloud plugins

Point your coding agent at [GDELT Cloud](https://gdeltcloud.com) — a clean event database over the
world's news. Coded events in a CAMEO+ / ACLED-aligned taxonomy, deduplicated story clusters with
their source articles, entities resolved to one spine across news, SEC filings, sanctions lists and
asset registries, and the physical assets underneath.

## Install

### Claude Code

```bash
/plugin marketplace add gdelt-cloud/plugins
/plugin install gdelt-cloud@gdelt-cloud
```

You will be asked for an API key on enable. Create one free at
[gdeltcloud.com/api-keys](https://gdeltcloud.com/api-keys) — **the free plan reads every dataset**;
paid plans buy volume and products, not access.

Non-interactively:

```bash
claude plugin marketplace add gdelt-cloud/plugins
claude plugin install gdelt-cloud@gdelt-cloud --config gdelt_api_key=gdelt_sk_...
```

### Codex

```bash
codex plugin marketplace add gdelt-cloud/plugins
```

Then `export GDELT_API_KEY=gdelt_sk_...` — Codex reads the bearer token from the environment rather
than prompting.

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

Both are JSON-RPC endpoints. Opening either in a browser returns `405` — that is expected.

### By hand, without the plugin system

If the marketplace is unavailable or you want the skills in a project without installing a plugin,
wire it yourself. Three steps:

```bash
# 1. skills — plain directories, each holding a SKILL.md
git clone https://github.com/gdelt-cloud/plugins /tmp/gdelt-cloud-plugins
mkdir -p .claude/skills && cp -R /tmp/gdelt-cloud-plugins/plugins/gdelt-cloud/skills/* .claude/skills/

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

**`gdelt-cloud`** wires both MCP servers and ships seven skills:

| Skill | For |
|---|---|
| `getting-started` | The ten rules that decide whether a call is correct. Read by the others. |
| `core-api` | Maps a plain-English ask onto the right endpoint and the minimal correct call |
| `building-with-the-api` | Writing CODE against it: paging to the end, truncated vs empty, caching, cadence |
| `war-risk-underwriting` | Chokepoint and route monitors, political-violence exposure, marine war-risk briefs |
| `counterparty-exposure` | Company → hierarchy → assets → news → filings → government exposure |
| `supplier-disruption` | N suppliers × M sites, daily digest with an escalation threshold |
| `country-risk-series` | Atlas GPR and Posture as a frame you can join to returns |

**`gdelt-cloud-docs`** wires the documentation server alone.

## Why the skills exist

Almost every way of getting this API wrong returns `200` with a plausible-looking result rather than
an error. `bbox` axis order differs between the core and maritime families. A `/summary` endpoint
takes a smaller parameter set than its list sibling, and an unknown parameter is echoed into
`applied_filters.ignored` rather than rejected. Six identifier spaces coexist and the wrong one
returns an empty result. Each skill front-loads the ones that matter for its workflow.

If you build without the skills, at least read
[docs.gdeltcloud.com/AGENTS.md](https://docs.gdeltcloud.com/AGENTS.md) — it is the same rules,
shorter.

## Working demos

Four complete reference implementations, each a self-contained Python project rendering a static
HTML dashboard: <https://github.com/gdelt-cloud/demos>

## Links

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
subdirectories each holding a `SKILL.md` — so all seven skills are shared across the three clients
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
