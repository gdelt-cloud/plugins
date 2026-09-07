---
name: gdelt-cloud-counterparty-exposure
description: Use this skill to build a counterparty, portfolio-company or issuer exposure monitor on GDELT Cloud — resolving a company to a stable id, then fanning out to its corporate hierarchy, physical assets, news coverage, SEC filings, government awards and foreign-influence links. Triggers on requests about portfolio company risk, issuer monitoring, KYC-adjacent research, ultimate-parent resolution, or "what is our exposure to this company".
---

# Counterparty and asset exposure

This is the hardest workflow in the API because it crosses identifier spaces. It is also the one
where a mistake is invisible: the wrong id returns an empty `200`, and an empty result reads as
"no exposure" when it means "we asked the wrong question".

Read `gdelt-cloud-getting-started` first. Rule 2 is the whole game here.

## Resolve once, and record what you resolved

```
GET /api/v2/search?q=<company name>&type=organization&country_match=strict&limit=10
```

The lexical resolver returns candidates across the source universes available to the request.
Use `q`, optional `type`, `country`, `holds_office`, and `limit`; recommended examples send
`country_match=strict`. Match explanations and country evidence help distinguish namesakes.
Country association is not automatically headquarters, citizenship or reporting location.

Keep the whole selected row, including `identifiers` and source availability. Ask the
`gdelt-cloud-docs` MCP for the identifier keys and accepted ID spaces of each destination endpoint.
A missing key is unavailable evidence; do not manufacture a source ID or conclude zero exposure.

Inspect candidates and make an explicit selection:

```python
for candidate in search["data"]:
    print(candidate.get("entity_id"), candidate.get("name"),
          candidate.get("match_reason"), candidate.get("country_evidence"))
selected_entity_id = input("Paste the entity_id of the intended candidate: ").strip()
selected = [candidate for candidate in search["data"]
            if candidate.get("entity_id") == selected_entity_id and selected_entity_id]
if len(selected) != 1:
    raise ValueError("Select exactly one returned entity candidate; keep ambiguity visible")
(resolved,) = selected
entity_id = resolved["entity_id"]
```

Preserve `e_…`, `wiki:…` and `llm:…` identifiers exactly. Check each fan-out endpoint's accepted
spaces; a source-specific leg may be unavailable for the selected identity. Facility candidates
carry `facility_id` instead, and unlinked source records have no resolved entity ID.

## The fan-out, and what each leg actually accepts

| Leg | Call | Identifier it wants |
|---|---|---|
| Corporate hierarchy | `GET /api/v2/entities/{entity_id}/hierarchy` | use the selected terminal `e_…` id |
| News coverage | `GET /api/v2/events?entity=…&entity_match=…` and `GET /api/v2/stories?entity=…` | use the selected returned entity ID accepted by reporting — **and read `entity_match`**, see below |
| Media tone | `GET /api/v2/entities/{entity_id}/tone` | **requires an explicit date window** |
| Share of voice | `GET /api/v2/share-of-voice?entity=…&category=…` | an id in `entity` / `entity_id` / `entities`, **plus a denominator** — see below |
| Physical assets | `GET /api/v2/facilities?entity=…` / `GET /api/v2/energy/assets?entity=…` | use the terminal `e_…`; keep source-specific GEM ids separate |
| SEC filings | `GET /api/v2/filings?cik=…` or `?search=<company name>` | CIK, ticker, or a company-name search |
| Federal awards | `GET /api/v2/gov/awards?entity=…` or `?recipient=<name>` | prefer terminal `e_…` on `entity`; `recipient` is the explicit fuzzy-name path |
| Foreign influence | `GET /api/v2/gov/fara?entity=…` | **`e_…` only** |
| Sanctions / screening exposure | `GET /api/v2/exposure?entity=…` or `?entity_search=<name>` | ids on `entity`; `entity_search` takes a plain name |
| LEI record | `GET /api/v2/gleif/entities/{lei}` | LEI |

Reuse the selected identity on every leg that supports its ID space. A leg requiring terminal
`e_…`, CIK, LEI or GEM owner evidence must use a confirmed identifier from that candidate or report
the leg unavailable. Never replace a selected news identity with an unrelated spine candidate just
to satisfy a downstream filter.

**Share of voice needs a denominator, and without one it 400s.** A share is meaningless without
saying what it is a share *of*, so the numerator alone is refused with `DENOMINATOR_REQUIRED` —
which names the eight filters that qualify in `details.allowed_filters`. Pick one:

### `entity=` on `/events` is not "events this counterparty did"

`entity_match` defaults to `material` — the counterparty is a party to the event — but where
material attribution has not been built the server substitutes `coverage`, meaning any event in a
story that merely mentions them, and still answers 200. Check two fields on every response:

```
applied_filters.coverage_fallback_applied   true  -> these are co-occurrence rows
applied_filters.entity_match_note                 -> the server says so in words
```

A coverage row is not automatically wrong — a consortium-membership story is a real link — but it
is not attribution, and a diligence memo must not present it as one. The accepted values are
`material`, `actor` and `coverage`. Naming `material` or `actor` explicitly returns
`503 ENTITY_ATTRIBUTION_UNAVAILABLE` today rather than substituting, which is what you want in a
pipeline: a refusal you can branch on beats rows you have to audit. Naming `coverage` yourself
returns the same rows as the default with `coverage_fallback_applied: false` — same data, but now
it is your decision. When combining several counterparties, merge returned Events on
`incident.uid`; duplicate suppression is part of the served incident view and is not a request
switch.

```
GET /api/v2/share-of-voice?entity=e_12345&category=cameoplus_crime&days=30
```

`entity`, `entity_id` and `entities` are all accepted here; `entities` is the canonical spelling and
the only one that takes more than one id.

Two traps worth naming explicitly:

- **`/energy/assets` has an `owner_entity_id` that is a GEM entity id, not a spine id** — while
  `/facilities` uses the same spelling for a spine alias. Feeding a GEM id into `/events?entity=`
  returns an empty 200. Resolve GEM owners through `GET /api/v2/energy/owners` and keep the two id
  spaces in separate variables with different names.
- **Filings is reached by CIK.** Either read it out of the resolved `identifiers` map, or call
  `GET /api/v2/filings/resolve`. If you use the resolver, cross-check its `entity_id` against the
  one you already hold and abort on disagreement rather than silently monitoring two companies.

## Plan gating

Several of these legs are entitlement-gated (`can_use_gov`, `can_use_filings`, `can_use_exposure`,
`can_use_gleif`, `can_use_tone`). The gating flag is published per operation in the endpoint index.
Write the job so a `403 PLAN_REQUIRED` degrades that leg and reports it, rather than failing the
whole digest — and surface which legs were skipped, because a digest missing its filings leg looks
identical to a company with no filings.

## Assembling the digest

Per company, per week:

1. Identity block — resolved name, spine id, ultimate parent, LEI and CIK where known, and an
   explicit list of the id spaces you could **not** resolve.
2. Coverage — event and story counts over the window, top events by `significance`, with article
   links.
3. Tone and share of voice, if entitled, with the denominator stated.
4. Structural — assets with capacity and geography, filings by form type, award and FARA counts.
5. A "what we could not see" section. This is not boilerplate: owner resolution across the asset
   directory is partial and the API publishes its own coverage rate. A digest that silently omits
   what it could not join is the failure mode this whole workflow exists to avoid.

For recurring intake, a Hosted entity Monitor can notify on broad new Story coverage for the
confirmed counterparty ids. Use `gdelt-cloud-hosted-monitors` to preview and create it, and label the
signal as coverage rather than material involvement. The hierarchy, filings, government, asset,
tone, share-of-voice, and screening fan-out remains a client workflow after a trigger; one Hosted
Monitor cannot represent that composite diligence question.

## Output

One HTML page per company plus a portfolio index, or a JSON artifact your own pipeline consumes.
Whichever you build, put the resolved ids in the output — the next run should reuse them rather than
re-resolving, and a human should be able to check that you monitored the right company.
