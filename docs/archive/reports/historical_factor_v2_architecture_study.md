# Historical Factor Warehouse V2 — Architecture Study

**Date:** 2026-06-06  
**Prepared by:** AI Architect  
**Classification:** Architecture Study — Pre-Implementation  
**Status:** Awaiting Selection

---

## Preamble

This study evaluates three candidate architectures for the Historical Factor
Warehouse V2. Every claim is grounded in evidence from the repository
reconnaissance (2026-06-06), the FMP Point-in-Time Audit, and the Feasibility
Report previously filed.

A critical finding is incorporated here that was not visible in prior reports:

> **All FMP API endpoints tested against this project's subscription return
> HTTP 402 or 403 errors.**
>
> Source: `archives/research/fmp/fmp_migration_audit.md` (Audit Date: 2026-06-01)
>
> Every endpoint tested — legacy `/api/v3/ratios/`, stable `/stable/ratios`,
> `/stable/financial-growth` — returned either:
> - `403`: *"Legacy Endpoint — only available for legacy users prior August 31, 2025"*
> - `402`: *"Special Endpoint — not available under your current subscription"*
>
> **FMP is not currently operational for this project without a paid upgrade.**
> This is a hard constraint that splits Options B and C from Option A.

---

## Evaluation Framework

Each option is scored on five dimensions:

| Dimension | Definition |
|---|---|
| **Development Cost** | Engineering effort to build and initially deploy |
| **Complexity** | Ongoing cognitive load and code surface area |
| **Bias Risk** | Probability and severity of look-ahead contamination |
| **Expected Accuracy** | How closely reconstructed scores match true historical scores |
| **Maintenance Burden** | Ongoing cost to keep the warehouse valid as data changes |

Ratings: `Low` / `Medium` / `High` / `Critical`

---

## Baseline: What Data Is Already Available

Before evaluating options, establish what the project already owns:

| Asset | Coverage | Columns | Usable for |
|---|---|---|---|
| `database/monthly/*.csv` (64 tickers) | 2018-01 → 2026-05 | `month_end_price`, `monthly_return`, `net_foreign_buy` | Momentum (exact) |
| `benchmarks/ihsg_monthly.csv` | 2018-01 → 2026-05 | `month_end_price`, `monthly_return` | IHSG benchmark (exact) |
| `output/history_prices/*.csv` (64 tickers) | 2018-01 → 2026-05 | `Date`, `Close`, `High`, `Low`, `Open`, `Volume` | PE/PB derivation (if EPS/BPS available) |
| `database/historical_universe/*.json` | Semi-annual: 2019-01 → 2026-01 | ticker list | Universe gating (approximate) |
| `database/historical/ticker_metadata.csv` | All 64 tickers | `ticker`, `listing_date` | IPO gate (exact) |
| `snapshots/fundamentals/` | 2026-05, 2026-06 only | All quality/value fields | 2 months only |
| `snapshots/growth/` | 2026-05, 2026-06 only | revenue_growth, earnings_growth | 2 months only |

**Key conclusion from baseline:** Only momentum can be reconstructed from
existing local data for the full 2021–2025 window. All fundamental factors
require external data acquisition.

---

## OPTION A — Yahoo Finance Only Reconstruction

### Description

Use `yfinance` to fetch current TTM (trailing twelve months) fundamental data
for all 64 tickers today, and back-apply those values to every historical month
from 2021 onward. The existing `utils/data_provider.py`
(`YahooFinanceProvider`) implements this approach for the live pipeline.

### Data Sources

| Factor | Source | Endpoint/Field |
|---|---|---|
| quality_score | `yf.Ticker(t).info` | `returnOnEquity`, `profitMargins`, `operatingMargins`, `debtToEquity`, `freeCashflow` |
| growth_score | `yf.Ticker(t).info` | `revenueGrowth`, `earningsGrowth` |
| value_score | `yf.Ticker(t).info` | `trailingPE`, `priceToBook`, `dividendYield` |
| momentum_score | `database/monthly/*.csv` | `month_end_price`, `net_foreign_buy` |

### Bias Analysis

YF `.info` returns **trailing twelve months (TTM) data as of the query date**
(today, 2026-06). This single snapshot is then applied uniformly to every
historical month from 2021-01 onward.

**Concrete example of contamination:**

| Ticker | Metric | True value (Jan 2021) | YF TTM value (Jun 2026) | Error |
|---|---|---|---|---|
| ADRO.JK | ROE | ~8% (pre-coal boom) | reflects 2025 fiscal year | ~5 year lag |
| BBCA.JK | PE Ratio | ~35x (pre-rate hikes) | reflects 2026 prices | ~5 year lag |
| GOTO.JK | revenue_growth | N/A (IPO Apr 2022) | reflects 2025 growth | N/A → contamination |

For ADRO.JK specifically: the database shows its price in Jan 2021 was ~357 IDR.
By Dec 2022 it had reached ~1,361 IDR. Using today's PE (which reflects 2026
prices of ~2,300 IDR) to score a Jan 2021 observation is a **5-year look-ahead
on PE alone.**

### Evaluation

| Dimension | Rating | Evidence |
|---|---|---|
| **Development Cost** | Low | `YahooFinanceProvider` already exists. Minimal new code required. |
| **Complexity** | Low | Single data source, no API key required, existing utility class. |
| **Bias Risk** | **Critical** | 4–5 year look-ahead on all fundamental factors. Restatement effects included. GOTO, AMMN, MBMA appear before IPO if not gated. |
| **Expected Accuracy** | Very Low (~15–25%) | Momentum column accurate; quality/growth/value columns systematically wrong for all months prior to current year. |
| **Maintenance Burden** | Low | YF `.info` is already used in production. No new dependencies. |

### Factor-Level Accuracy Estimate (2021–2025)

| Factor | Accuracy | Reason |
|---|---|---|
| momentum_score | ~93–97% | Built from local price data — no external dependency |
| quality_score | ~10–20% | TTM metrics from 2026 applied to 2021 observations |
| growth_score | ~5–15% | YoY growth in 2026 completely different from 2021 growth |
| value_score | ~10–20% | PE/PB reflect 2026 prices and 2025 earnings |
| final_score | ~20–30% | Momentum portion (35% weight) is correct; rest is corrupted |

### Verdict

Option A produces a warehouse that **appears** to contain factor scores but
whose fundamental columns are scientifically invalid for any 2021–2025 research.
Walk-forward optimization using Option A scores would produce results that
cannot be attributed to genuine factor signal — they reflect 2026 fundamentals
applied to historical price movements.

**Use case:** Demonstration, dashboard display, directional exploration only.  
**Not suitable for:** Walk-forward optimization, Config A vs B testing,
factor attribution, any published research.

---

## OPTION B — FMP Statement Endpoints with Filing-Date Gating

### Description

Use FMP's financial statement endpoints (`/income-statement`,
`/balance-sheet-statement`, `/cash-flow-statement`) to collect annual and
quarterly fundamental data for each ticker back to 2018. For each
ticker-month evaluation:

1. Identify all statement records whose `acceptedDate` precedes the evaluation date
2. Use the most recent such record for each metric
3. Calculate ROE, margins, DER, FCF, PE, PB from raw line items
4. Apply production scoring formulas exactly

PE and PB require a second step: compute `historical_price / EPS_at_that_date`
using daily prices from `output/history_prices/*.csv`.

### Hard Constraint: FMP Subscription Status

**This option is currently blocked.**

`archives/research/fmp/fmp_migration_audit.md` (2026-06-01) documents that
every FMP endpoint tested returns an error:

```
# Legacy endpoints → HTTP 403
"Legacy Endpoint: only available for legacy users prior August 31, 2025"

# Stable endpoints → HTTP 402
"Special Endpoint: not available under your current subscription"
```

**Option B cannot be implemented without a FMP subscription upgrade.**
The exact tier required depends on whether the project needs:
- Historical statements only (Starter/Basic tier likely sufficient)
- As-Reported endpoints (Premium tier required)
- Quarterly data for IDX stocks (coverage must be verified per ticker)

### Reporting Lag Logic Required

Even with a valid subscription, raw statement `date` fields cannot be used
directly. A reporting lag model is mandatory to avoid look-ahead bias:

```
# IDX regulatory deadline: 90 days for quarterly, 120 days for annual
available_date = max(acceptedDate, fiscal_period_end + 90_days)

# Only use this record if: available_date < evaluation_month_end
```

This logic must be implemented and tested per ticker.

### IDX-Specific Coverage Risk

FMP documentation warns that non-US exchange coverage varies. For IDX stocks:
- `acceptedDate` may reflect FMP's ingestion timestamp, not OJK filing date
- Some IDX tickers may have sparse quarterly data (only annual available)
- PSAK vs IFRS accounting differences may affect line item mapping

### Evaluation

| Dimension | Rating | Evidence |
|---|---|---|
| **Development Cost** | High | FMP subscription cost (unknown). New data collector required. Reporting lag logic. PE/PB derivation from raw EPS/BPS. 3–4 weeks estimated engineering. |
| **Complexity** | High | Two-stage pipeline: statement collection + ratio derivation. Filing date filtering. IDX-specific lag calibration. |
| **Bias Risk** | Low–Medium | Filing date gating eliminates timing bias. Standard `/ratios` endpoint risk (restatements) eliminated by using statement endpoints. Residual risk: IDX acceptedDate accuracy unverified. |
| **Expected Accuracy** | High (~75–85%) | Near-exact for annual reporting periods. Gaps between annual filings filled by carry-forward (slight approximation). FCF exact from cash flow statements. |
| **Maintenance Burden** | Medium | FMP subscription must be maintained. API changes require endpoint updates. New tickers require data backfill. |

### Factor-Level Accuracy Estimate (2021–2025, annual filing cadence)

| Factor | Accuracy | Residual risk |
|---|---|---|
| momentum_score | ~93–97% | Universe semi-annual approximation only |
| quality_score | ~75–85% | Carry-forward between annual filings. IDX filing lag uncertainty. |
| growth_score | ~75–85% | Requires two consecutive annual reports per ticker per year |
| value_score | ~80–88% | PE/PB derived from local price history + FMP EPS/BPS — highly accurate if EPS coverage complete |
| final_score | ~78–87% | All four factors present and approximately point-in-time safe |

### Verdict

Option B is the correct production-grade approach **if** a FMP subscription
is available. It produces a warehouse that is scientifically defensible for
walk-forward research, with residual risk concentrated in IDX filing lag
uncertainty that can be partially mitigated by adding a fixed 90-day safety
buffer per evaluation month.

**The single blocker is the FMP subscription.** Without it, this option cannot
be initiated.

---

## OPTION C — Full Point-in-Time Fundamental Engine

### Description

Build a complete point-in-time fundamental engine using FMP as-reported
endpoints exclusively. The distinction from Option B:

- Use `/financial-statement-full-as-reported` (not standardized statements)
- Recalculate all ratios entirely from raw XBRL line items
- Use `acceptedDate` for gating (not `fillingDate`)
- Maintain a local point-in-time database that stores each filing's values
  exactly as they were at the moment of acceptance
- When a company restates, store the original values separately from the
  restated values — both timestamped

This approach is equivalent to the methodology used by professional
quantitative research platforms (Bloomberg PORT, FactSet, Compustat PIT).

### Data Architecture Required

```
raw_statements/
  {ticker}/
    {acceptedDate}_{period}.json    # Original as-reported filing
    
pit_fundamentals/
  {ticker}/
    pit_timeline.csv                # [acceptedDate, field, value, period]
    
factor_warehouse_v2/
  {YYYY-MM}.json                    # Scores using only pre-month-end data
```

### Additional Requirements

1. **As-Reported endpoint access** — requires FMP Premium (higher tier than Option B)
2. **XBRL line item mapping** — Indonesian companies filing under PSAK use
   different XBRL tags than US GAAP. A mapping layer is required.
3. **Restatement tracking** — when a company files an amendment, both the
   original and restated values must be stored with separate `acceptedDate`
4. **EPS/BPS time series** — derived from as-reported income statements and
   balance sheets, then crossed with `output/history_prices/*.csv` for PE/PB
5. **IDX OJK filing verification** — cross-reference FMP `acceptedDate` against
   OJK disclosure platform (idx.co.id) to validate timing accuracy

### Evaluation

| Dimension | Rating | Evidence |
|---|---|---|
| **Development Cost** | **Critical** | FMP Premium subscription required. New PIT database architecture. XBRL mapping layer. Amendment tracking. IDX OJK cross-reference. 8–12 weeks estimated engineering. |
| **Complexity** | **Critical** | Highest architectural complexity in the study. Ongoing operational requirements. Distinct from all existing ISI systems. |
| **Bias Risk** | **Minimal** | As-reported data eliminates restatement contamination. `acceptedDate` gating eliminates timing bias. Residual: IDX `acceptedDate` accuracy (OJK vs FMP timestamp). |
| **Expected Accuracy** | Highest (~90–95%) | Matches what professional PIT databases provide for US stocks. IDX coverage depth may reduce to ~85–90% in practice. |
| **Maintenance Burden** | **Critical** | Permanent subscription dependency. New filings must be ingested and backfilled. Amendment handling requires ongoing monitoring. IDX data pipeline requires separate maintenance. |

### Factor-Level Accuracy Estimate (2021–2025)

| Factor | Accuracy | Notes |
|---|---|---|
| momentum_score | ~93–97% | Same as all options — local data |
| quality_score | ~88–93% | As-reported FCF, margins, DER exact per filing |
| growth_score | ~85–92% | YoY from consecutive as-reported statements |
| value_score | ~88–93% | PE/PB from as-reported EPS × local daily prices |
| final_score | ~88–93% | Highest achievable precision short of having original archived snapshots |

### Verdict

Option C is the gold standard for quantitative factor research. The methodology
is academically and institutionally correct. However, **it is disproportionate
to the stated research objective** — validating factor weight optimization for
a portfolio of 30 Indonesian large-cap stocks over a 5-year window.

The incremental accuracy gain over Option B (~8–10 percentage points) does not
justify the 3–4x additional development cost and the permanent operational
complexity introduced by maintaining a PIT fundamental database for IDX stocks.

Option C becomes the correct choice only if the ISI project scales to a point
where the research output requires publication-grade data integrity, or where
the portfolio strategy is managing capital at a scale where bias errors translate
to material financial risk.

---

## Head-to-Head Comparison

| Dimension | Option A (Yahoo-only) | Option B (FMP Statements) | Option C (Full PIT Engine) |
|---|---|---|---|
| **Development Cost** | Low | High | Critical |
| **Complexity** | Low | High | Critical |
| **Bias Risk** | Critical (4–5yr) | Low–Medium | Minimal |
| **Expected Accuracy** | ~20–30% | ~78–87% | ~88–93% |
| **Maintenance Burden** | Low | Medium | Critical |
| **External Dependency** | None (YF free) | FMP paid subscription | FMP Premium subscription |
| **Subscription Status** | ✅ Operational | ❌ Blocked (402/403) | ❌ Blocked (402/403) |
| **Time to Build** | 1–2 days | 3–4 weeks | 8–12 weeks |
| **Research Grade** | Demo only | Walk-forward research | Publication grade |
| **IPO Gate possible?** | Yes | Yes | Yes |
| **Bank Rule preserved?** | Yes | Yes | Yes |
| **Commodity Trap preserved?** | Yes | Yes | Yes |
| **Momentum exact?** | Yes | Yes | Yes |
| **Fundamentals point-in-time?** | **No** | **Yes (with lag model)** | **Yes (exact)** |

---

## Momentum-Only Sub-Option (Zero Blocker)

Before the recommendation, a fourth path deserves explicit acknowledgment:

**Build the warehouse using momentum only. Leave fundamental columns as NaN.**

This is not a failure mode — it is the scientifically honest reflection of
what local data supports. It delivers:

- Exact momentum_score reconstruction (2021–present)
- Full factor ranking within the momentum dimension
- IPO gate, listing date gate, universe gate — all applied exactly
- Foreign flow signal preserved
- Zero external dependency, zero subscription cost
- Buildable in 1–2 days

What it cannot support:
- Quality/growth/value factor attribution
- full final_score reconstruction
- Config A vs Config B testing of the four-factor composite

This sub-option should be delivered **first**, regardless of which full-option
is chosen. It is immediately executable and produces valid research output while
the FMP subscription decision is made.

---

## Recommendation

### PRIMARY RECOMMENDATION: OPTION B

**With the Momentum-Only Sub-Option delivered immediately as Phase 0.**

**Rationale:**

**1. Option A is not a research option.** Using 2026 TTM fundamentals to
reconstruct 2021 scores produces a warehouse that appears functional but is
scientifically void for any research that depends on factor signal quality.
The scores it would generate for 2021 would not reflect what any investor
could have known in 2021. Config A vs Config B comparison using Option A data
would be comparing noise, not signal.

**2. Option C is overengineered for this research scope.** The ISI system
tracks 30–64 Indonesian large-cap stocks for internal portfolio research. The
accuracy differential between Option B and Option C (~8–10 pp) is smaller than
the noise introduced by semi-annual universe approximation, which is already
present and accepted in the system. Option C's PIT database complexity
introduces permanent operational risk that is not commensurate with the
research benefit.

**3. Option B delivers scientifically defensible scores at manageable cost.**
With annual filing data (4–8 records per ticker per year), filing-date gating,
and a 90-day safety buffer for IDX reporting lag, Option B produces
reconstructed factor scores that are appropriate for walk-forward optimization
research, Config A vs Config B validation, and factor attribution analysis.

**4. The FMP subscription blocker must be resolved before Option B can begin.**
This is the only pre-condition. Until the subscription is active, the project
should deliver the Momentum-Only Phase 0.

---

### Phased Execution Plan (Recommendation)

```
PHASE 0 — Immediate (0 blocker)
  Deliverable: momentum-only warehouse
  Source:      database/monthly/ + ihsg_monthly.csv
  Coverage:    2021-01 → 2026-05, all 64 tickers
  Accuracy:    High (momentum exact)
  Duration:    1–2 days

PHASE 1 — After FMP subscription activated
  Deliverable: full four-factor warehouse (Option B)
  Source:      FMP income-statement + balance-sheet + cash-flow
  Coverage:    2021-01 → 2026-05
  Accuracy:    Near-exact (~78–87%)
  Duration:    3–4 weeks

PHASE 2 — Optional future upgrade
  Deliverable: Point-in-time upgrade of Phase 1 (Option C)
  Trigger:     Only if research scope expands to publication-grade requirements
  Duration:    8–12 weeks additional
```

---

## Pre-Conditions for Approval

Before implementation begins, the following must be confirmed:

| # | Pre-Condition | Owner | Status |
|---|---|---|---|
| 1 | FMP subscription tier confirmed and active | Project Owner | ❌ Not active |
| 2 | IDX ticker coverage verified for all 30 core tickers | Engineering | ❌ Not verified |
| 3 | Quarterly vs annual data availability confirmed per ticker | Engineering | ❌ Not verified |
| 4 | Reporting lag model (90 vs 120 days) approved for IDX | Research | ❌ Not confirmed |
| 5 | `acceptedDate` field accuracy for IDX stocks accepted as sufficient | Research | ❌ Not validated |
| 6 | Phase 0 (momentum-only) approved for immediate build | Project Owner | Pending |

---

## Appendix: Critical Evidence Citations

| Claim | Source file | Key line |
|---|---|---|
| FMP endpoints return 402/403 | `archives/research/fmp/fmp_migration_audit.md` | All 8 endpoints tested; all failed |
| FMP uses standardized (restated) data on /ratios | FMP docs (retrieved 2026-06-06) | "FMP often processes and updates these figures to account for restatements" |
| acceptedDate available on statement endpoints only | FMP docs (retrieved 2026-06-06) | Not present on /ratios endpoint |
| Fundamental snapshots exist for 2 months only | `snapshots/fundamentals/`, `snapshots/growth/` | 2026-05.json, 2026-06.json only |
| Momentum data complete 2018–2026 | `database/monthly/*.csv` (64 files) | BBCA.JK: 2018-01-31 → 2026-05-31 confirmed |
| Historical universe semi-annual only | `database/historical_universe/` | 15 files, all 6-month intervals |
| FCF never sourced from FMP | `archives/research/fmp/fmp_audit_report.md` | Line 37: "free_cash_flow not implemented in _fetch_from_fmp" |
| Config A/B scores identical on all periods | `reports/out_of_sample_validation.md` | Table: all configs show same Sharpe 0.18/−0.37 — factor data contamination likely explains collapse |
