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

## What you get

**`gdelt-cloud`** wires both MCP servers and ships five skills:

| Skill | For |
|---|---|
| `getting-started` | The nine rules that decide whether a call is correct. Read by the others. |
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
