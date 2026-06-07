# LESSONS LEARNED

## Assumption: Winners already have strong RS.
**Reality:** Winners emerge from distress — deep drawdown, far from high, elevated volatility.
**Source:** RESEARCH-008B, RESEARCH-009B
**Impact:** Turnaround Watchlist uses Context Match to detect this transition.

## Assumption: Timing overlay improves Config B.
**Reality:** Timing overlay degraded all metrics (CAGR 0.81% to -0.53%, Sharpe -0.15 to -0.18).
**Source:** RESEARCH-010
**Impact:** Timing overlay abandoned. Config B standalone is superior.

## Assumption: Turnaround can be a standalone portfolio.
**Reality:** Negative CAGR (-0.17%) over 7.3 years. Marginal alpha but not investable.
**Source:** RESEARCH-011
**Impact:** Turnaround is a watchlist/satellite tool, not a strategy.

## Assumption: Adding distress/turnaround filter improves Config B.
**Reality:** Philosophical mismatch — Config B selects leaders, distress selects laggards.
**Source:** RESEARCH-010 report
**Impact:** Distress overlay abandoned. Config B standalone confirmed superior.

## Assumption: Predictive sell signals can be built from existing features.
**Reality:** Losers at T0 are indistinguishable from winners — strong RS, above MA20, elevated volume.
**Source:** RESEARCH-S01
**Impact:** Shifted to rule-based exit state machine (Exit Layer V1.1).

## Assumption: Revenue Growth adds value to the Growth factor.
**Reality:** Revenue Growth has negative IC (-0.1036, t=-3.05). Earnings-only growth is superior (+13.46% vs +6.83% CAGR).
**Source:** FINDING_010_GROWTH_FACTOR_FAILURE.md
**Impact:** Growth factor formula should use earnings-only. Config B still uses 50/50 blend — blocked by Historical Factor Warehouse requirement.

## Assumption: Min-Max normalization produces valid factor scores.
**Reality:** A single extreme value compresses all other scores near zero (Outlier Crisis).
**Source:** V4 architecture migration
**Impact:** Replaced with Percentile Normalization permanently.

## Assumption: FMP is a reliable backup data source.
**Reality:** FMP blocked IDX queries on free tier (402/403). Fallback logic became dead code.
**Source:** ADR-002-DATA-SOURCE.md
**Impact:** Yahoo Finance is the exclusive data source.

## Assumption: Static universe is fine for backtesting.
**Reality:** Static universe CAGR (41.28%) vs dynamic universe CAGR (1.21%) — 40% inflation from survivorship bias.
**Source:** RESEARCH-006 comparison
**Impact:** All backtests must use dynamic historical universe + IPO date gate.

## Assumption: Factor weight optimization is straightforward.
**Reality:** Historical factor scores don't exist for 2019-2020. Yahoo only has data from 2021-2022. Optimization framework (V8.4) used constant inputs (score=50 for all tickers), making all configs identical.
**Source:** ADR-004-SUSPEND-WEIGHT-OPTIMIZATION.md
**Impact:** Config B runs by default. No weight changes without Historical Factor Warehouse V2.

## Assumption: Banks can be scored like normal companies.
**Reality:** DER > 500% is normal for banks (customer deposits = liabilities). Standard DER scoring eliminates all banks.
**Source:** Production scoring
**Impact:** Bank Rule: disable DER for banks, redirect weight to ROE.

## Assumption: Low PE at commodity cycle peak is undervaluation.
**Reality:** When the cycle reverses, earnings collapse and price crashes. Low PE is a false signal.
**Source:** Production scoring
**Impact:** Commodity Trap Rule: 50% discount on PE score for cyclical commodity tickers.

## Assumption: Recovery has enough lead time for production use.
**Reality:** Mean lead time 0.7 months < 1 month threshold. Not usable as a standalone signal.
**Source:** RESEARCH-006
**Impact:** Recovery State Engine kept as dashboard informational metric only.

## Assumption: Historical Factor Warehouse building is feasible.
**Reality:** Yahoo Finance only has annual data from 2021-2022 onward. Cannot reconstruct Quality/Growth/Value scores for 2019-2020.
**Source:** Warehouse V2 investigation
**Impact:** Full 2019+ warehouse not feasible. Partial V2 (2021+) under investigation.

## Assumption: Foreign flow data can be proxied.
**Reality:** Synthetic proxy was volume-adjusted momentum, not real foreign transaction data. Validity score: 10/100. Dropped CAGR from 6.62% to 3.11%.
**Source:** RESEARCH-008 audit
**Impact:** Foreign flow factor parked indefinitely. Needs real institutional flow data.
