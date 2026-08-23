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
GET /api/v2/search?q=<company name>&universe=all
```

Returns candidates across every universe — news, Wikipedia, SEC/EDGAR, Global Energy Monitor,
sanctions lists, China development finance — deduplicated to one row per real-world entity, keyed on
the canonical spine `e_…` id, with a per-source breakdown.

Keep the whole row, not just the id. It carries the `identifiers` map, which is how you cross into
the other id spaces. **Ask the `gdelt-cloud-docs` MCP for the exact key names before you index into it** — they
are not guessable, and a `KeyError` is better than a silent miss.

Then assert once, loudly, and stop if it fails:

```python
resolved = search["data"][0]
# `spine_id` is the registry id, and it is the one that must be present — it is null when the
# candidate exists only in news, EDGAR, GLEIF or an asset registry and has not been bridged.
# `entity_id` falls back to the source candidate's own id in that case, so asserting it starts
# with "e_" aborts on resolutions that are perfectly good for the news legs below.
assert resolved.get("spine_id"), resolved
```

## The fan-out, and what each leg actually accepts

| Leg | Call | Identifier it wants |
|---|---|---|
| Corporate hierarchy | `GET /api/v2/entities/{entity_id}/hierarchy` | name, `e_…`, `wiki:…`, a wikipedia URL, or a bare 20-char LEI |
| News coverage | `GET /api/v2/events?entity=…` and `GET /api/v2/stories?entity=…` | `e_…`, `wiki:…`, or a name |
| Media tone | `GET /api/v2/entities/{entity_id}/tone` | **requires an explicit date window** |
| Share of voice | `GET /api/v2/share-of-voice?entity=…&category=…` | an id in `entity` / `entity_id` / `entities`, **plus a denominator** — see below |
| Physical assets | `GET /api/v2/facilities?entity=…` / `GET /api/v2/energy/assets?entity=…` | `e_…` or a name |
| SEC filings | `GET /api/v2/filings?cik=…` or `?search=<company name>` | CIK, ticker, or a company-name search |
| Federal awards | `GET /api/v2/gov/awards?entity=…` or `?recipient=<name>` | `e_…`, `wiki:…`, `cik:…` on `entity`; `recipient` takes a plain name |
| Foreign influence | `GET /api/v2/gov/fara?entity=…` | **`e_…` only** |
| Sanctions / screening exposure | `GET /api/v2/exposure?entity=…` or `?entity_search=<name>` | ids on `entity`; `entity_search` takes a plain name |
| LEI record | `GET /api/v2/gleif/entities/{lei}` | LEI |

**Share of voice needs a denominator, and without one it 400s.** A share is meaningless without
saying what it is a share *of*, so the numerator alone is refused with `DENOMINATOR_REQUIRED` —
which names the eight filters that qualify in `details.allowed_filters`. Pick one:

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

## Output

One HTML page per company plus a portfolio index, or a JSON artifact your own pipeline consumes.
Whichever you build, put the resolved ids in the output — the next run should reuse them rather than
re-resolving, and a human should be able to check that you monitored the right company.
