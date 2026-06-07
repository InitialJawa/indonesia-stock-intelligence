# Growth Factor Autopsy

**Date:** 2026-06-06  
**Data:** Warehouse V3, 2023-01 to 2025-12 (36 months)  
**Portfolio:** Top 5, equal-weight, monthly rebalance (CONFIG_B framework)  
**Benchmark:** IHSG monthly return (excess-based Sharpe)

---

## Executive Summary

### Current Growth Factor Formula

```
growth_score = percentile_normalize(rev_growth) x 0.50 + percentile_normalize(earn_growth) x 0.50
```

### Root Cause

**Revenue Growth** has negative IC (-0.1036, t=-3.05)  
**Earnings Growth** has negative IC (-0.0409, t=-1.14)

### Decision

| Factor | Go/No-Go |
|--------|:--------:|
| Keep current (50R/50E) | No-Go |
| Revenue Only | No-Go |
| Earnings Only | **Mitigate** |
| Best alternative | **B: Earnings Only** |

---

## Section 1: Raw Growth Component Statistics

### Revenue Growth Distribution (across all month-tickers)

| Metric | Value |
|--------|:-----:|
| Mean | 0.0996 |
| Median | 0.0630 |
| Std | 0.3221 |
| Min | -0.7364 |
| Max | 2.3220 |
| % Negative | 26.44% |
| % Extreme (>+/-100%) | 1.15% |

### Earnings Growth Distribution (across all month-tickers)

| Metric | Value |
|--------|:-----:|
| Mean | 0.4168 |
| Median | 0.0370 |
| Std | 2.0772 |
| Min | -1.6993 |
| Max | 13.8471 |
| % Negative | 40.23% |
| % Extreme (>+/-100%) | 16.09% |

---

## Section 2: Component IC Analysis

### Individual Component IC

| Component | Mean IC | Std IC | t-stat | IC>0% | Spread | Hit Rate |
|-----------|:------:|:------:|:-----:|:----:|:-----:|:--------:|
| A: Revenue Only | -0.1036 | 0.2037 | -3.05 | 30.56% | -1.46% | 33.33% |
| B: Earnings Only | -0.0409 | 0.2150 | -1.14 | 38.89% | -0.68% | 44.44% |

### Quintile Spread Detail

| Component | Top Quintile | Bottom Quintile | Spread |
|-----------|:----------:|:--------------:|:------:|
| A: Revenue Only | 0.70% | 2.16% | -1.46% |
| B: Earnings Only | 0.54% | 1.22% | -0.68% |

### Interpretation

- **Revenue Growth alone**: Negative IC (-0.1036), t=-3.05. Hit rate 33.33%.
- **Earnings Growth alone**: Negative IC (-0.0409), t=-1.14. Hit rate 44.44%.

### Interaction Effect
The 50/50 equal-weight blend produces IC=-0.0857, t=-2.77.
If Revenue and Earnings had complementary signals (one working when the other fails),
the blend IC would exceed both individual ICs. This is **not** the case here.

---

## Section 3: Alternative Definitions Comparison

### IC Comparison (all alternatives)

| Definition | Mean IC | t-stat | Spread | Hit Rate | Rank |
|-----------|:------:|:-----:|:-----:|:--------:|:----:|
| B: Earnings Only | -0.0409 | -1.14 | -0.68% | 44.44% | 1 |
| F: Earn Capped +/-100% | -0.0409 | -1.14 | -0.68% | 44.44% | 2 |
| D: 30R/70E | -0.0711 | -2.10 | -1.20% | 41.67% | 3 |
| Original (50R/50E) | -0.0857 | -2.77 | -0.30% | 41.67% | 4 |
| A: Revenue Only | -0.1036 | -3.05 | -1.46% | 33.33% | 5 |
| E: Rev Capped +/-100% | -0.1036 | -3.05 | -1.46% | 33.33% | 6 |
| C: 70R/30E | -0.1057 | -3.35 | -1.22% | 36.11% | 7 |

### Portfolio Backtest Results (Top 5, CONFIG_B framework)

| Definition | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol |
|-----------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|
| Original (50R/50E) | 9.56% | 0.1397 | 0.1501 | -29.17% | 47.22% | 3.27% | 24.10% |
| A: Revenue Only | 0.93% | -0.2058 | -0.2004 | -33.68% | 44.44% | -4.95% | 24.01% |
| B: Earnings Only | 11.12% | 0.1949 | 0.2172 | -30.48% | 47.22% | 5.09% | 25.65% |
| C: 70R/30E | 3.51% | -0.1137 | -0.1164 | -29.57% | 47.22% | -2.63% | 23.09% |
| D: 30R/70E | 7.96% | 0.0870 | 0.0948 | -28.88% | 44.44% | 2.38% | 26.51% |
| E: Rev Capped +/-100% | 0.93% | -0.2058 | -0.2004 | -33.68% | 44.44% | -4.95% | 24.01% |
| F: Earn Capped +/-100% | 11.12% | 0.1949 | 0.2172 | -30.48% | 47.22% | 5.09% | 25.65% |
| **IHSG (benchmark)** | 8.07% | — | — | — | — | — | — |

---

## Section 4: Alternative Definitions (Detail)

### Formula Definitions

| Label | Formula | Rationale |
|-------|---------|-----------|
| Original (50R/50E) | 50% rev_score + 50% earn_score | Current production formula |
| A: Revenue Only | 100% rev_score | Remove earnings noise |
| B: Earnings Only | 100% earn_score | Remove revenue noise |
| C: 70R/30E | 70% rev_score + 30% earn_score | Revenue-dominant |
| D: 30R/70E | 30% rev_score + 70% earn_score | Earnings-dominant |
| E: Rev Capped +/-100% | percentile(rev_growth.clip(-1,1)) | Winsorize extreme revenue |
| F: Earn Capped +/-100% | percentile(earn_growth.clip(-1,1)) | Winsorize extreme earnings |

### Key Observations

**Best by Sharpe:** B: Earnings Only (Sharpe=0.1949, CAGR=11.12%)

**Worst by Sharpe:** E: Rev Capped +/-100% (Sharpe=-0.2058, CAGR=0.93%)

**Revenue vs Earnings delta:** IC difference = -0.0627 (Earnings outperforms Revenue as a factor; Earnings is the less harmful component)

**Capping effect on Revenue:** IC changes from -0.1036 (uncapped) to -0.1036 (capped at +/-100%), delta = +0.0000

**Capping effect on Earnings:** IC changes from -0.0409 (uncapped) to -0.0409 (capped at +/-100%), delta = +0.0000

**Revenue-dominant blend (70R/30E):** IC=-0.1057

**Earnings-dominant blend (30R/70E):** IC=-0.0711


---

## Section 5: Recommendation

### Decision Options

| Option | Action | Rationale |
|--------|--------|-----------|
| Repair | Adjust growth formula weights | Revenue dominates (-0.1036 vs -0.0409). Best alternative (B: Earnings Only) achieves IC=-0.0409 |
| Reduce weight | Decrease growth allocation in CONFIG_B | Current 30% weight amplifies negative alpha |
| Replace | Substitute Growth with experimental factor | Low Volatility (IC=0.0713) or Dividend (IC=0.1245) show positive IC |

### Recommended Path

**Recommendation: Reduce + Replace path** — No alternative formula yields positive alpha.
Best alternative (B: Earnings Only) still shows negative IC (IC=-0.0409)
but is the least harmful (backtest CAGR=11.12%, Sharpe=0.1949).

**Immediate action:** Switch to Earnings-only formula to minimize alpha leakage.

**Medium-term:** Reduce Growth weight from 30% to 15% and allocate freed weight to
Value (currently 10%) and Low Volatility.

**Long-term:** Replace Growth entirely with a positive-alpha factor
(Low Volatility IC=0.0713 or Dividend IC=0.1245 from RESEARCH 001).


---

## Appendix: Methodology

### Factor IC Calculation

For each month `t`:
1. Rank all stocks by growth score (percentile 0-100)
2. Compute Spearman rank correlation between scores and next-month returns
3. Q5-Q1 spread: top 20% average return minus bottom 20% average return
4. Hit rate: % months where top-half stocks outperform bottom-half stocks

### Growth Component Calculation

**Revenue Growth:** YoY change in total revenue from fiscal data.
Fallback: Yahoo Finance trailing `revenueGrowth` metric.

**Earnings Growth:** YoY change in net income from fiscal data.
Fallback: Yahoo Finance trailing `earningsGrowth` metric.

### Raw Growth Data Source

For each month-ticker in the warehouse, `fy_actual` determines which
fiscal years are compared. Point-in-time fiscal data is fetched from
yfinance (annual income statements). When PIT data is unavailable,
Yahoo trailing growth rates are used as a fallback.

### Alternative Definitions

- **A (Revenue Only):** Same percentile-normalization applied to revenue growth only
- **B (Earnings Only):** Same percentile-normalization applied to earnings growth only
- **C (70R/30E):** Weighted blend favoring revenue
- **D (30R/70E):** Weighted blend favoring earnings
- **E (Rev Capped +/-100%):** Revenue growth winsorized at +/-100% before normalization
- **F (Earn Capped +/-100%):** Earnings growth winsorized at +/-100% before normalization

### Portfolio Backtest

Top 5, equal-weight, monthly rebalance.
CONFIG_B weights: Quality=25%, Growth=30%, Value=10%, Momentum=35%.
Only the Growth factor is replaced with each alternative definition.
Benchmark: IHSG monthly return (same calendar month as portfolio returns).
