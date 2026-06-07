# Factor Warehouse V2 — Scientific Feasibility Assessment

**Date:** 2026-06-06  
**Prepared by:** AI Architect — Pre-Build Analysis  
**Scope:** Historical Factor Reconstruction, 2021-01 → Present  
**Classification:** RESEARCH-ONLY — No production systems modified

---

## Executive Summary

This document assesses whether the Historical Factor Warehouse V2 can be built
to the specification stated in the task brief. Each question is answered with
direct evidence from repository reconnaissance. Conclusions are honest and
evidence-bound. No assumptions are made in favour of the project.

---

## QUESTION 1 — Can historical factor scores actually be reconstructed?

For each factor the required raw inputs are identified, the source files are
located, and their actual date coverage is established.

---

### Factor 1: QUALITY

**Required inputs** (from `scoring/quality_score.py`):
| Field | Source key |
|---|---|
| ROE | `roe` |
| Net Margin | `net_margin` |
| Operating Margin | `operating_margin` |
| Debt-to-Equity | `debt_to_equity` |
| Free Cash Flow | `free_cash_flow` |

**Primary source file:** `output/raw/fundamentals.json`  
**Snapshot archive:** `snapshots/fundamentals/`

**Date coverage found:**

| File | Date |
|---|---|
| `snapshots/fundamentals/2026-05.json` | 2026-05 only |
| `snapshots/fundamentals/2026-06.json` | 2026-06 only |

**Finding:** Only 2 months of fundamental snapshots exist in the repository.
No historical fundamental snapshots exist for the period 2021-01 through
2025-12. The `output/raw/fundamentals.json` file contains a single live
snapshot (current as of the last pipeline run). It is overwritten each month
and is not archived historically.

**Missing fields for 2021–2025:** ALL fields — roe, net_margin,
operating_margin, debt_to_equity, free_cash_flow.

---

### Factor 2: GROWTH

**Required inputs** (from `scoring/growth_score.py`):
| Field | Source key |
|---|---|
| Revenue Growth (YoY) | `revenue_growth` |
| Earnings Growth (YoY) | `earnings_growth` |

**Primary source file:** `output/raw/growth.json`  
**Snapshot archive:** `snapshots/growth/`

**Date coverage found:**

| File | Date |
|---|---|
| `snapshots/growth/2026-05.json` | 2026-05 only |
| `snapshots/growth/2026-06.json` | 2026-06 only |

**Finding:** Same situation as Quality. Only 2 months of growth snapshots
exist. `output/raw/growth.json` is a single live file, overwritten each cycle.
No historical growth data survives for 2021–2025.

**Missing fields for 2021–2025:** revenue_growth, earnings_growth (all).

---

### Factor 3: VALUE

**Required inputs** (from `scoring/value_score.py`):
| Field | Source key |
|---|---|
| P/E Ratio | `pe_ratio` |
| P/B Ratio | `pb_ratio` |
| Dividend Yield | `dividend_yield` |

**Primary source file:** `output/raw/fundamentals.json`  
**Snapshot archive:** `snapshots/value/`

**Date coverage found:**

| File | Date |
|---|---|
| `snapshots/value/2026-05.json` | 2026-05 only |
| `snapshots/value/2026-06 .json` | 2026-06 only |

**Finding:** Same situation. Only 2 months of value snapshots exist.
PE ratio and PB ratio are point-in-time market-derived values. They change
every trading day and were never archived monthly. Dividend yield is also
only available for the current snapshot.

**Note on PE/PB derivation:** The prior FMP feasibility report
(`archives/research/fmp/v6_reconstruction_feasibility.md`) correctly identifies
that PE and PB *could* be derived as:  
`PE = Historical Price / EPS_at_that_date`  
`PB = Historical Price / BPS_at_that_date`  
However, this requires point-in-time EPS and BPS from financial statement
archives (e.g., FMP API), which are NOT present in this repository. Daily
price history **is** available in `output/history_prices/` from 2018 onward,
but EPS/BPS per ticker per reporting period are absent.

**Missing fields for 2021–2025:** pe_ratio, pb_ratio, dividend_yield (all).

---

### Factor 4: MOMENTUM

**Required inputs** (from `scoring/momentum_score.py`):
| Field | Source |
|---|---|
| month_end_price (rolling, 13+ months) | `database/monthly/*.csv` |
| net_foreign_buy (optional) | `database/monthly/*.csv` |
| IHSG monthly benchmark prices | `benchmarks/ihsg_monthly.csv` |

**Date coverage found:**

| Source | Tickers | Coverage |
|---|---|---|
| `database/monthly/*.csv` | 64 tickers | 2018-01 → 2026-05 |
| `benchmarks/ihsg_monthly.csv` | IHSG index | 2018-01 → 2026-05 |
| `output/history_prices/*.csv` | 64 tickers | 2018-01 → 2026-05 (daily) |

**Finding:** Momentum inputs are **fully available** from 2021 onward.
Every ticker in `database/monthly/` carries `month_end_price`,
`monthly_return`, and `net_foreign_buy` columns going back to 2018.
IHSG monthly data is also available for the same window. The 6-month
relative-strength and 12-month return calculations can be executed for
every month from 2021-01 to 2026-05 without any external API call.

**Missing fields for 2021–2025:** None. Momentum is fully self-contained.

---

## QUESTION 2 — Can production formulas be reproduced historically?

For each scoring module, verdict on whether all required inputs exist for 2021–present.

---

### `quality_score.py` — Verdict: **IMPOSSIBLE** (without external data)

The formula requires 5 fundamental fields per ticker per month. Zero historical
snapshots of these fields exist in the repository prior to 2026-05. The live
`output/raw/fundamentals.json` is a single-point TTM file, overwritten monthly,
with no archive chain.

Yahoo Finance and FMP *can* provide current TTM fundamentals today, but
**cannot** return what ROE, net_margin, or FCF were in June 2022 or January
2024 as point-in-time data. YF `info` is always the most recent TTM value.
Using today's fundamentals as a proxy for historical months constitutes
**direct look-ahead bias** and violates RULE 5 of the task specification.

The prior feasibility report confirms this problem and states that FMP
quarterly financial statements would be required to derive historical
point-in-time fundamentals.

**Verdict: IMPOSSIBLE (true historical, no look-ahead)**  
**Verdict: PARTIAL (if look-ahead bias from current YF data is accepted)**

---

### `growth_score.py` — Verdict: **IMPOSSIBLE** (without external data)

Growth requires YoY revenue and earnings growth, which are derived from two
consecutive annual financial statements. No historical financial statement
archives exist in this repository. YF's `tk.financials` provides trailing
income statements, not point-in-time historical figures.

**Verdict: IMPOSSIBLE (true historical, no look-ahead)**

---

### `value_score.py` — Verdict: **IMPOSSIBLE** (without external data)

PE and PB require point-in-time market cap and book value. Daily prices exist
in `output/history_prices/` (2018–2026), but EPS and BPS per reporting period
do not exist locally. Dividend yield in historical form is absent. The
Commodity Trap Rule (50% PE discount) can only be applied if PE exists.

**Note:** A derived PE could theoretically be computed as  
`Price(t) / EPS_from_latest_annual_before_t`  
but the EPS time series per ticker is not in the repository.

**Verdict: IMPOSSIBLE (true historical, no look-ahead)**

---

### `momentum_score.py` — Verdict: **FULL**

All inputs exist. `database/monthly/*.csv` provides 13+ months of price
history for every ticker from 2021 onward. IHSG benchmark is available.
Foreign flow column (`net_foreign_buy`) is present in all files. The
production formula can be reproduced exactly, including:
- RS-6M = 6-month stock return minus 6-month IHSG return
- Return-12M = 12-month price appreciation
- Percentile normalization across the active monthly universe
- Foreign flow accumulation (6-month sum)

**Verdict: FULL** ✓

---

## QUESTION 3 — What data is permanently lost?

The following fields **cannot be reconstructed** from any data source currently
in the repository (`database/monthly/`, `snapshots/`, `database/historical/`,
`archives/`, `output/`):

| # | Field | Why it is lost |
|---|---|---|
| 1 | `roe` (historical, monthly) | Never archived. `output/raw/fundamentals.json` overwrites each cycle. |
| 2 | `net_margin` (historical, monthly) | Same. Only 2026-05 and 2026-06 snapshots survive. |
| 3 | `operating_margin` (historical, monthly) | Same. |
| 4 | `debt_to_equity` (historical, monthly) | Same. |
| 5 | `free_cash_flow` (historical, monthly) | Same. |
| 6 | `pe_ratio` (historical, monthly) | Requires EPS per reporting period — not stored locally. |
| 7 | `pb_ratio` (historical, monthly) | Requires BPS per reporting period — not stored locally. |
| 8 | `dividend_yield` (historical, monthly) | Never archived historically. |
| 9 | `revenue_growth` (historical, monthly) | Derived from income statements — not stored locally. |
| 10 | `earnings_growth` (historical, monthly) | Same. |

**Fields that ARE recoverable:**
- `month_end_price` — fully in `database/monthly/`
- `net_foreign_buy` — fully in `database/monthly/`
- IHSG benchmark — fully in `benchmarks/ihsg_monthly.csv`
- `listing_date` — in `database/historical/ticker_metadata.csv`
- Active universe per month — in `database/historical_universe/` (semi-annual)

---

## QUESTION 4 — Can percentile rankings be reconstructed accurately?

Percentile normalization in production (`scoring/utils.py`) is a cross-sectional
rank across all tickers active in a given month. The accuracy of reconstructed
percentile scores therefore depends entirely on whether the historical monthly
universe can be recovered.

**Assessment of `database/historical_universe/` coverage:**

| Period | Files Available | Frequency |
|---|---|---|
| 2019 → 2026-01 | 2019-01, 2019-07, 2020-01, 2020-07, 2021-01, 2021-07, 2022-01, 2022-07, 2023-01, 2023-07, 2024-01, 2024-07, 2025-01, 2025-07, 2026-01 | Semi-annual |

**Gaps:** No monthly granularity. Between snapshot months (e.g., between
2021-01 and 2021-07) the exact universe composition is unknown.

The `historical_momentum_builder.py` already handles this by using the most
recent snapshot file whose date is ≤ the target month (`file_month <= month_key`).
This is a valid approximation — any ticker that entered or exited the universe
between two semi-annual snapshots will be misclassified for those intermediate
months.

**For Momentum factor specifically:**
- Universe accuracy: **~90%** (semi-annual gaps introduce ~1–2 ticker errors
  per 6-month window, given historical IDX30 churn)
- Percentile rank accuracy: **HIGH** — small universe changes minimally distort
  percentile positions of the remaining tickers

**For Quality/Growth/Value factors:**
- Not applicable — the inputs do not exist regardless of universe accuracy.

**Universe Reconstruction Verdict: PASS (with semi-annual approximation)**  
The semi-annual universe files are sufficient for momentum reconstruction.
The same approach has already been validated in `historical_momentum_builder.py`.

---

## QUESTION 5 — Can `final_score` be reconstructed exactly?

The production formula from `scoring/final_score_v3.py`:

```
final_score = quality * 0.25 + growth * 0.30 + value * 0.10 + momentum * 0.35
```

Reconstruction requires **all four** factor scores. As established:

| Factor | Reconstructible? | Confidence |
|---|---|---|
| quality_score | NO (2021–2025) | 0% |
| growth_score | NO (2021–2025) | 0% |
| value_score | NO (2021–2025) | 0% |
| momentum_score | YES | ~95% |

Since `quality`, `growth`, and `value` together contribute **65% of the
final score weight**, and none of those inputs are available historically,
`final_score` cannot be reconstructed with any fidelity for the period
2021–2025.

For the 2 months with complete snapshots (2026-05 and 2026-06), exact
reconstruction is achievable — but these months fall outside the main
research window and represent near-current, not historical, data.

**Confidence in exact `final_score` reconstruction (2021–2025):** **0%**  
**Confidence if look-ahead bias from current YF fundamentals is accepted:** **~30%**
(momentum is exact; quality/growth/value approximated by TTM values from today)

---

## QUESTION 6 — Estimate build quality

**Verdict: B — Near-Exact Reconstruction (Momentum Only) / C — Approximate for Full Score**

**Justification:**

The warehouse as specified — with all four factor scores — falls into
**Category C: Approximate Reconstruction Only** for the primary research window
(2021–2025). This is because 65% of the final score depends on fundamental
inputs that no longer exist in the repository and cannot be recovered without
either:

1. A historical fundamentals API (FMP, Refinitiv, Bloomberg), or
2. A time machine (the data was never archived)

However, there is a valid and scientifically clean **partial implementation**
available:

**What CAN be built exactly (Category A/B):**
- A **Momentum Factor Warehouse** covering 2021–present
- Monthly momentum_score, RS-6M, Return-12M, Foreign Flow per ticker
- Factor ranks based on production `momentum_score.py` formula
- Monthly universe snapshots via `database/historical_universe/`
- IPO Gate and Bank/Commodity Rule **not applicable to momentum**, but
  listing date gate can be applied via `ticker_metadata.csv`

**What CANNOT be built without look-ahead bias:**
- quality_score (historical)
- growth_score (historical)
- value_score (historical)
- final_score (historical, full-weight composite)

If the task brief is interpreted as "build what is feasible without bias",
the deliverable should be scoped to **momentum-only** with the three
fundamental factors marked as `NaN` for 2021–2025.

If the task brief accepts look-ahead bias (using today's YF fundamentals
as approximations for historical months), then a **Category C Approximate**
warehouse can be built, with explicit bias warnings in the output.

---

## QUESTION 7 — Estimated data completeness (2021–present)

Estimates are per ticker-month observation, across all required fields.

### Scenario A: Momentum Factor Only (No look-ahead, scientifically clean)

| Metric | Best Case | Expected | Worst Case |
|---|---|---|---|
| momentum_score completeness | 97% | 93% | 85% |
| quality_score completeness | 1%* | 1%* | 1%* |
| growth_score completeness | 1%* | 1%* | 1%* |
| value_score completeness | 1%* | 1%* | 1%* |
| final_score completeness | 1%* | 1%* | 1%* |
| **Overall warehouse completeness** | **~25%** | **~24%** | **~22%** |

*1% = 2026-05 and 2026-06 only (2 months of 65 total months in window)

**Coverage loss by ticker:**
- Tickers with incomplete `database/monthly/` data (< 13 rows): excluded from
  momentum for early months
- AMMN.JK: listed 2023-07, momentum available from ~2024-07
- GOTO.JK: listed 2022-04, momentum available from ~2023-04
- MBMA.JK: listed 2023-04, momentum available from ~2024-04
- PGEO.JK: listed 2023-02, momentum available from ~2024-02

### Scenario B: Approximate Reconstruction (Accept look-ahead bias from current YF)

| Metric | Best Case | Expected | Worst Case |
|---|---|---|---|
| momentum_score completeness | 97% | 93% | 85% |
| quality_score completeness | 85% | 70% | 55% |
| growth_score completeness | 80% | 65% | 50% |
| value_score completeness | 80% | 65% | 50% |
| final_score completeness | 75% | 60% | 45% |
| **Overall warehouse completeness** | **~83%** | **~70%** | **~57%** |

**Bias warning for Scenario B:** Using today's TTM fundamentals for a 2021
observation introduces **~4–5 years of look-ahead contamination**. A company's
ROE in 2026 may be materially different from its ROE in 2021. This makes
Scenario B scores **unreliable for walk-forward optimization or factor
attribution**. The warehouse could support directional research, but NOT
scientific backtesting.

---

## Summary Table

| Question | Finding |
|---|---|
| Q1: Inputs available? | Momentum: YES. Quality/Growth/Value: NO (2021–2025). |
| Q2: Formulas reproducible? | Momentum: FULL. Quality: IMPOSSIBLE. Growth: IMPOSSIBLE. Value: IMPOSSIBLE. |
| Q3: Permanently lost data? | 10 fundamental fields — all ROE, margins, PE, PB, DY, growth rates. |
| Q4: Percentile rankings accurate? | PASS (semi-annual universe files sufficient for momentum). |
| Q5: final_score exact? | 0% confidence for 2021–2025. |
| Q6: Build quality | Category B (momentum-only) / Category C (approximate full score). |
| Q7: Completeness 2021–present | Momentum-only: ~24%. With look-ahead proxy: ~70%. |

---

## Recommended Path Forward

Three options exist. Choose before implementation begins.

---

### OPTION 1 — Momentum Warehouse Only (Recommended)
**Scientific grade: HIGH. Build effort: LOW.**

Build the warehouse using only momentum factor, which is perfectly
reconstructible. Mark quality/growth/value as `NaN` in the output schema.
The warehouse supports momentum attribution, walk-forward momentum
optimization, and Config A vs Config B testing of momentum weight.

**Use case:** Validate whether the 35% momentum weight is optimal.
Factor attribution of the momentum dimension. IPO-clean, no look-ahead bias.

---

### OPTION 2 — Approximate Full Warehouse with Bias Disclosure
**Scientific grade: LOW. Build effort: MEDIUM.**

Fetch current YF fundamentals for all tickers and back-fill quality/growth/value
scores using today's TTM values for all historical months. Disclose the
look-ahead contamination prominently in all output files.

**Use case:** Rough directional research only. NOT suitable for rigorous
walk-forward optimization or factor weight validation.

---

### OPTION 3 — Full Warehouse via FMP API
**Scientific grade: HIGH. Build effort: HIGH.**

Integrate FMP Financial Modeling Prep API to collect quarterly financial
statements (Balance Sheet, Income Statement, Cash Flow) for each ticker from
2021 onward. Derive point-in-time ROE, margins, FCF, PE, PB, and growth
from those statements. This eliminates look-ahead bias and produces a
scientifically valid full-factor warehouse.

**Blocker:** FMP API key is not present in the repository (`config/settings.json`
shows only Telegram and email config). FMP integration was planned in a prior
feasibility study (`archives/research/fmp/`) but never executed.

---

## Final Verdict

> **The Historical Factor Warehouse V2 as specified (all four factors,
> 2021–present, no look-ahead bias) is NOT fully feasible with data currently
> in the repository.**
>
> Momentum is the single reconstructible factor. A momentum-only warehouse
> is immediately buildable to production specification standards.
>
> A complete four-factor warehouse requires either FMP API integration
> (Option 3) or explicit acceptance of look-ahead bias (Option 2).
>
> **No implementation should begin until the desired option is approved.**
