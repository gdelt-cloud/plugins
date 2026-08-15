---
name: gdelt-cloud-country-risk-series
description: Use this skill to build a dated country or regional risk time series from GDELT Cloud that a quant can join to returns, prices or a portfolio — Atlas GPR and Posture readings, event-count and severity series, and the baseline discipline that makes a series comparable across places and weeks. Triggers on country risk scores, geopolitical risk indices, signal construction, backtesting, or "give me a number per country per day I can regress on".
---

# Country risk as a joinable time series

The output is a tidy frame: one row per (place, date), columns you can regress on, and a stated
construction. The failure mode is not a crash — it is a series that looks stationary and is not,
because the denominator moved underneath it.

Read `gdelt-cloud-getting-started` first.

## Two sources, and they answer different questions

**Atlas** is the published index family, computed from our own coded events and resolved entities:

```
GET /api/v2/intelligence/gpr        # geopolitical risk vs a place's OWN normal
GET /api/v2/intelligence/posture    # structural + dynamic condition
GET /api/v2/intelligence/coverage   # where the index can and cannot be read
```

**Your own rollup** from `/events/summary` gives you counts and severity in whatever grouping you
choose. Use Atlas when you want a normalized, baseline-aware reading; use the rollup when you want
something you fully control and can explain line by line.

## Call `coverage` first, and honour it

`GET /api/v2/intelligence/coverage` reports which countries are dense enough to serve a
country-level reading. It is scoped to the Atlas index — it is not a general statement about event
coverage. Countries below the floor should be **excluded from the panel, not read as low risk**. A
thin-coverage country scores quiet for the same reason a well-covered peaceful one does, and nothing
downstream can tell those apart.

Measured over a recent 107-day window, only a small minority of countries cleared the per-country
floor on most days. Treat a wide panel as a modelling choice you have to defend, not a default.

## The baseline rules that make a series comparable

1. **GPR is relative to a place's own normal.** A GPR of 60 in Norway and 60 in Yemen are not the
   same absolute danger; they are the same distance from their own baselines. Never rank countries
   by GPR as though it were an absolute scale.
2. **Fix the base window across the whole panel and state it.** A rolling baseline that moves with
   the series will flatten exactly the regime change you are trying to detect.
3. **`variant` and `construction` change what you are measuring.** The two GPR lenses and the
   own-coverage vs world-corpus constructions are different series, not settings. Pick one per panel
   and put it in the column name. Ask the `gdelt-cloud-docs` MCP for the current accepted values rather than
   hardcoding them — the 400 carries `details.accepted_values`.
4. **Never correlate two `*_share` columns.** They are compositional; a share series and another
   share series over the same denominator are mechanically related.
5. **Day of week is a real effect.** Weekend news volume is structurally lower and the abnormality
   band fires several times more often on Sundays. Either control for it or resample weekly.

## Windows and joins

Windows are capped at 30 days per call, so a long panel means paginating by window and concatenating.
Coded history begins **March 2026** — anything earlier returns near-empty, which will look like a
regime of perfect calm if you do not clip it.

Emit an explicit date index with no gaps, so a missing reading is `NaN` rather than an absent row.
`null` is not `0`: a day we could not read is not a day with no risk, and the difference is the
whole signal when you join to returns.

## A defensible frame

```python
# one row per (iso3, date); every column names its own construction
cols = [
    "gpr_<variant>_<construction>",   # Atlas reading, baseline-aware
    "event_count",                    # your rollup, same window, same filters
    "significance_sum",               # severity, NOT summed with other metrics
    "fatalities",                     # conflict family only; null where not published
    "coverage_ok",                    # from /intelligence/coverage — drop rows where False
]
```

Ship the frame with a README stating: the window, the variant and construction, the coverage floor
you applied, the countries you dropped and why, and the day-of-week treatment. A risk series without
those five lines is not reproducible, and the first question a risk committee asks is which one you
chose.

## Output

A CSV or Parquet frame plus a short HTML methodology page showing the series, the baseline, and the
excluded panel. Keep the API calls in a separate module from the transform so the frame can be
rebuilt without re-fetching.
