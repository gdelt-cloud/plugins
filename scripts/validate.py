#!/usr/bin/env python3
"""
Structural validation for this marketplace, run in CI and before every push.

`claude plugin validate` checks a plugin against Anthropic's schema. This checks the four
things that schema cannot see, each of which fails SILENTLY at runtime:

  1. A root `.mcp.json`. Claude Code and Codex BOTH auto-discover that filename, with
     incompatible schemas (`headers` + `${user_config.X}` vs `http_headers` +
     `bearer_token_env_var`, and Codex has no interpolation). Ship per-CLI files instead.
  2. A remote server declared without `"type": "http"`. Claude Code reads it as stdio,
     finds no command, and skips the server — no error, just no tools.
  3. A `${user_config.X}` used in a header but not marked `required: true`. When unset the
     placeholder passes through UNEXPANDED and the connection fails, rather than falling
     back to OAuth.
  4. `skills/` or `commands/` placed inside `.claude-plugin/` rather than at the plugin root.

Run: python3 scripts/validate.py
"""
import json, re, pathlib, sys

RESERVED = {"claude-code-marketplace","claude-code-plugins","claude-plugins-official",
 "claude-plugins-community","claude-community","anthropic-marketplace","anthropic-plugins",
 "agent-skills","anthropic-agent-skills","knowledge-work-plugins","life-sciences",
 "claude-for-legal","claude-for-financial-services","financial-services-plugins",
 "first-party-plugins","healthcare"}
KEBAB = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
ROOT = pathlib.Path(__file__).resolve().parent.parent
errs = []


def load(p):
    try:
        return json.loads((ROOT / p).read_text())
    except Exception as e:
        errs.append(f"{p}: {e}")
        return None


def main() -> int:
    mkt = load('.claude-plugin/marketplace.json')
    if mkt:
        for k in ('name', 'owner', 'plugins'):
            if k not in mkt:
                errs.append(f"marketplace.json missing required '{k}'")
        if mkt.get('name') in RESERVED:
            errs.append(f"marketplace name '{mkt['name']}' is reserved for Anthropic")
        if not KEBAB.match(mkt.get('name', '')):
            errs.append(f"marketplace name '{mkt.get('name')}' is not kebab-case")
        root = (mkt.get('metadata') or {}).get('pluginRoot', '.')
        for entry in mkt.get('plugins', []):
            for k in ('name', 'source'):
                if k not in entry:
                    errs.append(f"plugin entry missing '{k}': {entry}")
            if not KEBAB.match(entry.get('name', '')):
                errs.append(f"plugin name '{entry.get('name')}' is not kebab-case")
            if isinstance(entry.get('source'), str) and not (ROOT / root / entry['source']).is_dir():
                errs.append(f"source does not resolve: {root}/{entry['source']}")

    for d in sorted((ROOT / 'plugins').iterdir()):
        if not d.is_dir():
            continue
        rel = d.relative_to(ROOT)
        if (d / '.mcp.json').exists():
            errs.append(f"{rel}/.mcp.json — both CLIs auto-discover this name with incompatible "
                        f"schemas; use .mcp.claude.json and .mcp.codex.json")
        for bad in ('skills', 'commands', 'agents', 'hooks'):
            if (d / '.claude-plugin' / bad).exists():
                errs.append(f"{rel}/.claude-plugin/{bad} — must sit at the plugin root")

        man = load(rel / '.claude-plugin' / 'plugin.json')
        if not man:
            continue
        if 'name' not in man:
            errs.append(f"{rel}: plugin.json missing 'name'")
        mcp_rel = man.get('mcpServers')
        if mcp_rel:
            mcp = load(rel / mcp_rel)
            if mcp:
                servers = mcp.get('mcpServers', {})
                if not servers:
                    errs.append(f"{rel}/{mcp_rel}: no mcpServers declared")
                for name, cfg in servers.items():
                    if 'url' in cfg and cfg.get('type') != 'http':
                        errs.append(f"{rel} server '{name}': remote url without \"type\": \"http\" "
                                    f"— Claude Code reads it as stdio and skips it")
                declared = man.get('userConfig') or {}
                for u in set(re.findall(r'\$\{user_config\.([A-Za-z0-9_]+)\}', json.dumps(mcp))):
                    if u not in declared:
                        errs.append(f"{rel}: ${{user_config.{u}}} is not declared in userConfig")
                    elif not declared[u].get('required'):
                        errs.append(f"{rel}: userConfig '{u}' is interpolated into a header but is "
                                    f"not required:true — unset, it passes through unexpanded and "
                                    f"the connection fails instead of falling back to OAuth")
        for s in sorted((d / 'skills').iterdir()) if (d / 'skills').is_dir() else []:
            f = s / 'SKILL.md'
            if not f.exists():
                errs.append(f"{s.relative_to(ROOT)}: no SKILL.md")
                continue
            head = f.read_text()[:800]
            if not head.startswith('---'):
                errs.append(f"{f.relative_to(ROOT)}: no YAML frontmatter")
            elif 'description:' not in head.split('---')[1]:
                errs.append(f"{f.relative_to(ROOT)}: frontmatter carries no description, so the "
                            f"model has nothing to trigger on")

    cx = load('.agents/plugins/marketplace.json')
    if cx:
        for entry in cx.get('plugins', []):
            p = pathlib.Path(entry['source']['path'])
            if not (ROOT / p).is_dir():
                errs.append(f"codex source does not resolve: {p}")
            elif not (ROOT / p / '.codex-plugin' / 'plugin.json').exists():
                errs.append(f"{p}: no .codex-plugin/plugin.json")

    # ★ CURSOR IS THE THIRD CLIENT AND WAS INVISIBLE HERE. Adding `.cursor-plugin/` without adding
    # it to this loop left the validator reporting "0 errors" while never opening the new files —
    # a green that means "not checked", which is worse than a red. Same shape as the two above.
    cur = load('.cursor-plugin/marketplace.json')
    if cur:
        for entry in cur.get('plugins', []):
            p = pathlib.Path(entry['source'])
            if not (ROOT / p).is_dir():
                errs.append(f"cursor source does not resolve: {p}")
                continue
            man = load(p / '.cursor-plugin' / 'plugin.json')
            if not man:
                errs.append(f"{p}: no .cursor-plugin/plugin.json")
                continue
            if man.get('name') != entry['name']:
                errs.append(f"{p}: cursor manifest name {man.get('name')!r} != marketplace {entry['name']!r}")
            # `mcpServers` may be a path; when it is, the file has to exist or the servers are silent.
            mcp = man.get('mcpServers')
            if isinstance(mcp, str) and not (ROOT / p / mcp).exists():
                errs.append(f"{p}: cursor mcpServers points at {mcp}, which does not exist")
            # Skills are the same SKILL.md convention as the other two clients — so a manifest that
            # claims them while the directory is absent ships a plugin that triggers on nothing.
            sk = man.get('skills')
            if isinstance(sk, str) and not (ROOT / p / sk).is_dir():
                errs.append(f"{p}: cursor skills points at {sk}, which is not a directory")

    for e in errs:
        print(f"ERROR: {e}")
    print(f"\n{len(errs)} error(s)")
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
