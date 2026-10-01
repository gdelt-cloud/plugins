---
name: news-country-research
description: Answer news, Story, Event and country questions with structured evidence and explicit coverage.
---

# News Country Research

## Country research
Discover `gdelt_cloud` section `countries`. Use `get_countries` to identify available context and `get_country` for one country. Add `summarize_events` for counts/trends, or a bounded `search_events`/`search_stories` query for evidence. REST: `/api/v2/countries`, `/api/v2/countries/{iso3}`, `/api/v2/events/summary`, `/api/v2/events`, `/api/v2/stories`. Use the exact discovered date/filter names for each operation. Native macro series belong to `macro`; source-specific structural data must keep vintage, unit and attribution.

## News and narrative
Use Events for incidents and analytical aggregation, Stories for clustered narratives, article endpoints for reporting. Begin with the smallest scope implied by the question. A headline overview rarely needs every source or a cross-domain sweep. Fetch known records directly when their schema is already understood.

```python
gdelt_cloud_tool_call(tool_name="search_events", tool_arguments={"limit": 5})
gdelt_cloud_tool_call(tool_name="search_stories", tool_arguments={"limit": 5})
gdelt_cloud_tool_call(tool_name="get_countries", tool_arguments={})
```
These illustrate wrapper syntax; scope real requests to the user's geography, dates and question using discovered filters.

Present selected Events and Stories as linked GDELT Cloud records, with relevant returned metrics (magnitude, systemic importance, propagation potential and market sensitivity, plus evidence counts when useful; do not display coding confidence). Explain metric meaning without implying a calibrated probability of real-world impact. Add linked entities or facilities when a supported identity, ownership or geographic join helps answer the question; proximity alone is not impact. Use returned images when helpful (`include_images` where supported), up to three with attribution. Publisher links remain supporting reporting evidence. Report served/missing dates, applied filters and truncated lists. Aggregate totals cannot be reconstructed from the visible compact sample. Events are machine-coded, Stories cluster reporting, and source coverage is uneven; neither is an exhaustive census of reality. Category/subcategory and current metric definitions are authoritative, not raw CAMEO/Goldstein interpretation. Use `gdelt://codes/cameo-event` and `gdelt://codes/goldstein-scale` for the current interpretation.

Outside corroboration can supplement a material claim; it is never mandatory. Registry-only and schema-only questions usually need none. See getting started (`skill://getting-started/SKILL.md`) for hard web bounds and citations.

Rank a brief by the user's decisions and time horizon, not article volume alone. Story counts are coverage, not independent confirmations. Preserve language coverage and entity-match evidence; missing/unavailable enrichment remains unknown. Reconcile important amounts, currencies and dates against returned original reporting before trusting a translated title. A narrow primary-source corroboration can resolve a decision-changing conflict within the shared web bounds. A digest should separate distinct underlying developments even when several clusters repeat the same announcement; it is a selected brief, not an exhaustive census. Finish with the most useful action or missing input, and offer a reusable scope/identity/filter recipe when the user wants to repeat it.

## Quantified geography: country, region, or bounding box
Start with `summarize_events` grouped by category for an explicit date window. For events happening in a country/region, use `country_match="location"`; default country matching also includes actor origins and answers a different question. Use the discovered `region` enum or bbox format; never silently replace a box with nearby countries. Explain whether today's open UTC date is included. For a completed-week comparison prefer two adjacent closed seven-day windows, with identical filters and geographic semantics. Read coverage for both before computing change; partial windows cannot support a complete-period growth claim. Complete serving coverage is not exhaustive reporting of reality or proof that an open day has finished.

Use returned bucket `metrics`/`metric_stats`, including measurement counts where available; never average displayed samples into country totals. Magnitude is 0–10 and should be compared within a category. The other three metrics are 0–1 scores of reported conditions, not probabilities, forecasts or a country risk index. Missing CAMEO+ values on Conflict Events stay unknown/inapplicable; never substitute zero. Show category counts plus the four core metrics, then drill one important category by subcategory and fetch a few relevant Events with images/entity images. Preserve returned labels, codes and links; do not infer subcategory meaning from remembered raw CAMEO codes.

Identify named actors from returned Event/entity references and resolve only material ambiguities. Actor-country summary buckets describe origin, not a ranking of individual entities. Search existing Situations when persistent context adds value, and explain that a Situation may extend beyond the query geography/time window. Add facilities/structural data only for a supported relation; proximity and co-mention do not establish impact. Finish with the most useful next question, such as a narrower sector, geographic boundary or Monitor preview.

For a reproducible regional/bbox Monitor, prefer a query subject using the documented endpoint and supported query filters when that preserves the analyzed scope. Copy supported filters, not sample limit/cursor/fixed dates; execution owns its moving window. Do not promise aggregate threshold alerts: current Monitors detect new matching records, not changes in aggregate means. Preview only unless the user explicitly confirms creation.


A first pass normally needs one category summary per comparison scope, one focused subcategory drilldown and one evidence sample. Reuse each successful result and the first Monitor preview. Do not refetch identical summaries/Situations or shrink an already returned sample; use full response mode only when a specific missing field is needed. Report the result of a bounded Situation search as “no matches for this search,” not proof that no related Situation exists. Do not combine category averages into a global average unless the API provides each metric's non-null measurement count and all buckets; use the directly returned aggregate or keep the category comparison instead.
Country context links the same canonical Facilities inventory and separate natural-resource statistics. Follow returned evidence URLs or discover `resource_statistics` via the resources group for production/reserves, source year and units. Facility counts and registry-unit counts differ; country mineral reserves are not per-facility reserves. Owner/parent news context is a separate relationship from events located near a site. Retain unlinked identities, missing geography and partial publication coverage.
