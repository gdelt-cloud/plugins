# Plugin experience review — 2026-09-29

Reviewed both public products, the eight data-plugin workflow skills, three client manifests per
product, MCP connection files, and their relationship to the monorepo server's 14 categories.
Connection defaults stay on Horizon until the Manufact launch gates pass.

## Confirmed defects and repairs

| Finding | Effect | Repair/evidence |
|---|---|---|
| Onboarding, builder and Monitor entrypoints totalled 8,224 words | Simple tasks loaded extensive unrelated procedures | 1,330-word combined entrypoints, deeper references packaged and link-checked |
| Universal maximum-page advice | Oversized conversational results and unnecessary context use | Task-sized samples; larger pages only for requested export volume |
| Cursor example ignored incomplete coverage and overshot its cap | A cap of three emitted 100 rows; partial source data looked like an export | Reproduced original defect; six executable helper regressions cover bounds, receipts, gaps, loops and HTTP failures |
| Situation example could restart forever and silently truncate | Unbounded work / false completion | Explicit restart/request budgets and partial-result contract |
| REST-heavy skills lacked common MCP execution guidance | Wrong wrapper/argument translation and missing UI fallback | Shared 14-category routing, list/get/call, read/write and account/error guidance |
| Data plugin labeled only Read | Under-described existing workspace mutations | Read/Write/Interactive label; authorization remains per operation |
| Docs product had no workflow skill | Schema help depended on generic document search | Focused API-reference skill; no account or data-server dependency |
| “No API-key field” implied no data access | Misleading web/desktop onboarding | OAuth vs local secret configuration explained; connection inventory checked |

All nine skill entrypoints pass skill validation. Repository validation checks the three clients,
connection configuration, skill sets and packaged reference paths. The generic plugin-creator
validator incorrectly requires the shared `.mcp.json` filename for these per-client configs;
keep the intentionally separate files. Native Claude Code installation was not tested locally
(the CLI is unavailable). Codex CLI help confirms the documented installation commands; no
customer configuration was changed or credentials used for this review.

Against the current monorepo, 106 REST route references matched real routes. MCP sample arguments
were checked against real `_tool_get` schemas without external HTTP. That does not validate every
parameter in every REST recipe, live entitlement, response field or third-party data source.

## Skill-by-skill disposition

- getting-started: short connection/task router, access recovery and account links; detailed rules optional.
- core-api: precise trigger, task-sized reads, confirmed identifier spaces, link to MCP execution.
- building-with-the-api: receipt-preserving bounded paginator, partial coverage, bounded retries and revalidation.
- hosted-monitors: preview/authorization/save/enable/send separated; detailed payloads and replay remain available.
- counterparty-exposure: retained source-identity and unavailable-leg discipline; MCP route documented.
- country-risk-series: retained construction/vintage/coverage cautions; linked MCP workflow. Historical numerical
  observations remain dated examples, not a fresh validation of all index outputs.
- supplier-disruption: exact returned identity and positive completeness evidence, not “yesterday = complete”.
- war-risk-underwriting: retained separate bbox conventions, evidence and units; removed forced onboarding reload.
- docs/api-reference (new): precise contract retrieval and cited examples without live-data or account claims.

## Client boundaries and next work

Local marketplace plugins, remotely readable skills and a published web listing are distinct.
The server changes remove mandatory long-manual loading, fix array-valued examples and identity
routing, and preserve its retired-provider block. Tool names/categories, auth, metering, write
routing and entitlements are unchanged. Widgets remain optional; sources and caveats must work in text.

OpenAI now supports a draft Skills extension with at most five imported skills. The current server
provides MCP resources but does not implement that extension. A curated import adapter with digest,
path-safety, pagination and resource-read checks is follow-up work, not accomplished by adding an
MCP URL. See https://developers.openai.com/plugins/build/mcp-server#import-skills-from-the-mcp-server.

Other follow-ups: native install/update flows on all three coding clients; ChatGPT/Claude web
acceptance after the existing runner/TLS blockers; representative behavioral evals for retrieval,
identity ambiguity, partial coverage, schema help and preview-only monitoring; authored output schemas
for the remaining server operations. Context reduction is measured; latency/answer-quality gain is
not yet measured. Do not present this review as complete production acceptance or publication.

## Checks

Run `python3 scripts/validate.py` and `python3 -m unittest discover -s tests -v`.
For MCP example validation from the monorepo:

```bash
GDELT_PLUGIN_ROOT=/absolute/path/to/plugins-checkout uv run --project gdelt-cloud-mcp pytest -q gdelt-cloud-mcp/tests/test_skill_guidance.py
```

The cross-repo check is explicit: public-plugin CI cannot assume a private monorepo checkout exists.
