# Scientific Verdict: Warehouse V2 Factor Optimization

**Date:** 2026-06-06  
**Classification:** Final Assessment  
**Data:** Warehouse V2 multiyear PIT (2022-2025, 29 tickers, 1,389 records)

---

## Question 1: Is Config B actually superior to Config A?

| Metric | Config A | Config B | Config B Superior? |
|--------|:--------:|:--------:|:------------------:|
| CAGR | 20.43% | 23.25% | YES |
| Sharpe | 0.5488 | 0.6263 | YES |
| Max Drawdown | -20.76% | -22.18% | NO (higher risk) |
| Win Rate | 57.45% | 63.83% | YES |
| **Total Return** | 103.95% | 122.84% | — |
| **Months** | 47 | 47 | — |

**Verdict Q1:** Config B is superior to Config A
(YES — 3/4 metrics favor B).

Config B shows higher CAGR (+2.82pp)
and higher win rate (+6.38pp),
but comparable Sharpe ratio.

The evidence is broadly consistent with Config B's design intent (higher growth+momentum
exposure) but the margin over Config A is small.

---

## Question 2: Is the superiority statistically meaningful?

**Factors limiting statistical significance:**

1. **Small sample:** ~47 monthly observations (48-month window, minus
   months without forward returns). CAGR estimates have wide confidence intervals.

2. **Look-ahead bias in 2022:** All 12 months (25% of sample) use 2026 TTM data.
   This inflates apparent performance for both configs.

3. **Look-ahead bias in Value:** ~45% of 2023-2025 Value scores use trailing data.
   Since Value has only 10% (B) / 20% (A) weight, the effective bias is ~4-10%.

4. **Small universe:** 29 tickers limit diversification and increase sampling error.
   A single ticker's outlier return can materially shift portfolio metrics.

5. **Data source limitation:** 11/29 tickers (commodity/mining) have unreliable
   annual financial data from Yahoo Finance — fundamental data scale issue.

6. **No cross-validation:** Single train-test period (2022-2025) with no walk-forward
   or rolling validation to test parameter stability.

**Conclusion Q2:** The observed superiority is **indicative but not statistically
meaningful.** The combination of look-ahead bias, small sample, and single-source
data makes it impossible to reject the null hypothesis that Config A and Config B
have equal expected performance.

---

## Question 3: Is Warehouse V2 sufficient for factor optimization?

### Strengths

| Strength | Detail |
|----------|--------|
| Complete factor coverage | 100% populated across all 4 factors for all ticker-months |
| PIT for Quality/Growth (2023-2025) | 1,044 ticker-months with clean PIT fundamental data |
| Methodology consistency | Scoring formulas match production `scoring/utils.py` exactly |
| Sector rules applied | Bank DER exclusion, ROE boost; commodity PE halving |
| Temporal range | 48 months (2022-2025) covering commodity boom, rate hikes, recovery |

### Limitations

| Limitation | Detail | Severity |
|------------|--------|:--------:|
| Trailing data over 50% | 58.2% of Value scores use trailing (2026) PE/PB | HIGH |
| 2022 full look-ahead | All 345 ticker-months use 2026 TTM data | HIGH |
| Commodity data failure | 11/29 tickers (38%) have unreliable annual financials | HIGH |
| Dividend data omitted | 30% of Value score formula uses dividend yield — not populated | MEDIUM |
| Single data source | Yahoo Finance only — no cross-validation source | MEDIUM |
| Limited temporal span | 4 years is minimal for factor research (5-10+ ideal) | MEDIUM |
| FY2021 gap | No annual data for 2021 → 2022 forced to trailing fallback | MEDIUM |

### Verdict Q3

| Criterion | Score | Comment |
|-----------|:-----:|---------|
| Data Completeness | A | 100% populated, all factors computed |
| Point-in-Time Accuracy | D+ | 58% trailing (Value), 25% trailing (all factors in 2022) |
| Look-ahead Bias Control | D | 100% in 2022, ~45% Value in 2023-2025 |
| Universe Coverage | B+ | 29/30 IDX30 tickers (96.7%) |
| Temporal Coverage | C- | 4 years — marginal for factor research |
| Methodological Consistency | A | Scoring formulas, normalization, sector rules match production |
| Statistical Power | D | Small sample + pervasive look-ahead bias |

**Final:** Warehouse V2 is adequate for **exploratory research** but **insufficient
for definitive factor-weight optimization.** The ~58% trailing data rate,
100% look-ahead in 2022, and Yahoo-only single source limit scientific confidence.

---

## Question 4: What confidence level should be assigned?

### Rating Scale

| Rating | Definition |
|:------:|-----------|
| **A** | **Research Grade** — Clean PIT data, no look-ahead bias, verified source lineage |
| **B** | **Strong Exploratory** — Mostly valid with minor documented limitations |
| **C** | **Indicative Only** — Results suggestive but not conclusive |
| **D** | **Not Usable** — Data quality prevents any meaningful inference |

---

## FINAL RATING: C — Indicative Only

### Weighted Assessment

| Evidence | Weight | Assessment | Score |
|----------|:-----:|:----------:|:-----:|
| PIT Coverage (Value) | 20% | 41.8% PIT | D+ |
| Look-Ahead Bias | 25% | QG: 24.8% (2022 only), Value: 58.2% | D |
| Sample Size | 15% | 47 months, 29 tickers | C- |
| Methodology | 20% | Production-identical formulas, sector rules, normalization | A |
| Factor breadth | 10% | All 4 factors computed with zero missing data | A |
| Source diversity | 10% | Single source (Yahoo Finance) | C- |

**Key Score:** Methodology A (strength) x Data Quality C- (weakness) = **Overall C**

### Rationale

1. **Config B shows some evidence of superiority** over Config A (higher CAGR, win rate)
   but the margin is small and data quality limitations prevent a definitive conclusion.

2. **The Value factor is the weakest link** — 58.2% trailing data with 2026 look-ahead bias.
   Given Value's 10% weight in Config B and 20% in Config A, this primarily affects
   Config A's comparison more than Config B's absolute performance.

3. **Quality and Growth scores for 2023-2025 are clean PIT** — these are the most
   methodologically sound components of the warehouse and support factor research.

4. **2022 data must be excluded** from any rigorous optimization. Keeping it introduces
   pervasive look-ahead bias that invalidates statistical inference.

5. **Config B's apparent advantage may reflect momentum over-weighting during a
   commodity bull cycle (2022-2024)** rather than genuine factor alpha — cyclical
   backtest dependency is a known risk.

### Recommendation

- **DO** use Warehouse V2 for exploratory analysis and hypothesis generation
- **DO NOT** use Warehouse V2 results to justify production weight changes
- **DO** re-run optimization after fixing commodity ticker annual financials
- **DO** exclude 2022 data from all future analyses
- **PRIORITY:** Fix Yahoo parser for Indonesian GAAP financial statements
  (11 commodity/mining tickers) to achieve 80%+ PIT coverage

---

## Appendix: Methodology Notes

- **Scoring:** Percentile normalization identical to `scoring/utils.py`
- **Sector rules:** Banks (DER excluded, ROE boosted), commodities (PE halved)
- **Portfolio:** Equal-weight Top 5, rebalanced monthly
- **Return calculation:** `(next_month_price / current_price) - 1` from warehouse prices
- **Benchmark:** IHSG monthly return for excess return / Sharpe calculation
- **Sharpe:** Annualized (x sqrt(12)), 0% risk-free rate
- **Turnover:** `(entries + exits) / (2 * portfolio_size)` averaged across months
- **CAGR:** Geometric annualized return `(1 + total_return)^(1/n_years) - 1`
- **Max Drawdown:** Peak-to-trough decline in cumulative portfolio returns
