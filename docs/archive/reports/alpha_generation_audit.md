# Alpha Generation Audit

**Date:** 2026-06-06  
**Data:** Warehouse V3 (CONFIG_B weights), 2023-01 to 2025-12 (35 months)  
**Portfolio:** Top 5, equal-weight, monthly rebalance  
**Benchmark:** IHSG monthly return (excess-based Sharpe)  

---

## Executive Summary

### Current Status

| Metric | CONFIG_B (Top 5) | IHSG | Delta |
|--------|:----------------:|:----:|:-----:|
| CAGR | 6.83% | 8.37% | -1.54% |
| Sharpe (excess) | 0.0205 | — | — |
| Alpha (ann.) | 0.41% | — | — |
| Volatility | 24.04% | — | — |
| Max Drawdown | -29.17% | — | — |

### Root Cause

**Value** is the strongest alpha source 

**CONFIG B IC:** -0.0198 (mean rank correlation with next-month returns)  
**Best individual factor:** Value (IC=0.0805, t=2.33)  
**Worst individual factor:** Growth (IC=-0.0846, t=-2.66)  
**Alpha leaderboard winner:** Value  

### Key Findings

1. **Some factor ICs are mixed**
2. **Yes experimental factor identified** for incremental alpha
3. **Top 5 concentration is the right choice** — concentration amplifies factor alpha
4. **Factor decay analysis shows** momentum decay pattern

---

## Section 1: Alpha Decomposition

### Factor Information Coefficient (IC)

Spearman rank correlation between factor score and next-month return.
Positive IC = factor predicts higher returns.

| Factor | Mean IC | Std IC | IC>0 % | t-stat | Mean Spread (Q5-Q1) | Hit Rate |
|--------|:------:|:------:|:-----:|:-----:|:-------------------:|:--------:|
| Quality | 0.0357 | 0.2353 | 62.86% | 0.90 | 0.40% | 45.71% |
| Growth | -0.0846 | 0.1885 | 42.86% | -2.66 | -0.26% | 48.57% |
| Value | 0.0805 | 0.2044 | 68.57% | 2.33 | 1.07% | 57.14% |
| Momentum | 0.0061 | 0.2306 | 54.29% | 0.16 | -0.18% | 54.29% |
| Config B | -0.0198 | 0.2188 | 45.71% | -0.54 | -1.49% | 60.00% |

### Factor Quintile Spread

Average monthly return difference between top-quintile and bottom-quintile stocks
by each factor. Positive = top-quintile outperforms.

| Factor | Top Quintile (avg) | Bottom Quintile (avg) | Spread |
|--------|:------------------:|:---------------------:|:------:|
| Quality | 0.26% | 0.96% | 0.40% |
| Growth | 0.17% | 0.73% | -0.26% |
| Value | 1.26% | 0.25% | 1.07% |
| Momentum | 0.53% | 0.36% | -0.18% |
| Config B | -0.35% | 0.61% | -1.49% |

### Interpretation

**IC strength scale:** |t| > 2.0 = strong, |t| > 1.0 = moderate, |t| < 1.0 = weak

- **Quality**: IC=0.0357, weak positive signal. Adds alpha. Hit rate 45.71% (random = 50%). 
- **Growth**: IC=-0.0846, strong negative signal. Destroys alpha. Hit rate 48.57% (random = 50%). Significant alpha leakage.
- **Value**: IC=0.0805, strong positive signal. Adds alpha. Hit rate 57.14% (random = 50%). Strongest alpha contributor.
- **Momentum**: IC=0.0061, weak positive signal. Adds alpha. Hit rate 54.29% (random = 50%). 
- **Config B**: IC=-0.0198, weak negative signal. Destroys alpha. Hit rate 60.00% (random = 50%). 

---

## Section 2: Factor Decay Analysis

Information Coefficient at different holding horizons.
A decaying IC means the factor's predictive power fades over time.

| Factor | 1m IC | 3m IC | 6m IC | 12m IC | Half-life |
|--------|:-----:|:-----:|:-----:|:------:|:---------:|
| Quality | 0.0357 | -0.0049 | 0.0163 | 0.0037 | 3m |
| Growth | -0.0846 | -0.1028 | -0.1158 | -0.1464 | 3m |
| Value | 0.0805 | 0.1163 | 0.1553 | 0.2343 | >12m |
| Momentum | 0.0061 | -0.0011 | 0.0508 | 0.0107 | 3m |
| Config B | -0.0198 | -0.0281 | 0.0230 | 0.0016 | 3m |

---

## Section 3: Experimental Factor Candidates

### IC of Experimental Factors

| Factor | Mean IC | Mean Spread (Q5-Q1) | N Months |
|--------|:------:|:-------------------:|:--------:|
| Foreign Flow | -0.0742 | -2.40% | 35 |
| Low Volatility | 0.0713 | -0.81% | 35 |
| Dividend | 0.1245 | 0.57% | 35 |
| Sector Strength | 0.0500 | 1.03% | 35 |

### Factor Construction Details

**Foreign Flow Factor:** 3-month average net foreign buy divided by 3-month average absolute foreign buy. Captures direction and consistency of foreign capital flows. Negative values indicate net selling pressure.

**Low Volatility Factor:** Inverse of trailing 12-month annualized realized volatility. Stocks with more stable returns receive higher scores. Lower vol reduces portfolio risk.

**Dividend Factor:** Dividend Yield x min(Payout Ratio, 1.0). Captures both yield and sustainability. Higher score = higher quality dividend payer.

**Sector Strength Factor:** Each stock receives its sector's average momentum score percentile. Captures sector-level momentum effects beyond individual stock signals.

---

## Section 4: Incremental Alpha Test

Baseline: CONFIG_B (25/30/10/35) Top 5, equal weight, monthly rebalance.
Experimental: CONFIG_B scaled down by 7%, reallocated to new factor.

| Metric | CONFIG_B | +Foreign Flow | +Low Vol | +Dividend | +Sector Strength |
|--------|:--------:|:-------------:|:--------:|:---------:|:----------------:|
| **CAGR** | 6.83% | -2.08% | 13.81% | 10.61% | 3.27% |
| **Sharpe** | 0.0205 | -0.4032 | 0.3493 | 0.2151 | -0.1632 |
| **Sortino** | 0.0263 | -0.4178 | 0.4031 | 0.2391 | -0.1877 |
| **Max DD** | -29.17% | -29.71% | -19.61% | -24.85% | -26.83% |
| **Win Rate** | 45.71% | 51.43% | 57.14% | 54.29% | 48.57% |
| **Alpha** | 0.41% | -8.35% | 7.15% | 4.48% | -3.11% |
| **Vol** | 24.04% | 23.54% | 25.44% | 26.32% | 23.18% |

---

## Section 5: Alpha Leaderboard

### Factor Ranking (by IC t-statistic)

| Rank | Factor | IC | t-stat | Sharpe Contribution | Recommendation |
|:----:|--------|:--:|:------:|:-------------------:|:-------------:|
| 1 | Value | 0.0805 | 2.33 | positive | Keep |
| 2 | Quality | 0.0357 | 0.90 | positive | Keep |
| 3 | Momentum | 0.0061 | 0.16 | positive | Keep |
| 4 | Config B | -0.0198 | -0.54 | negative | Review |
| 5 | Growth | -0.0846 | -2.66 | negative | Review |
| 6 | Dividend (experimental) | 0.1245 | — | 0.2151 | Evaluate |
| 7 | Low Volatility (experimental) | 0.0713 | — | 0.3493 | Evaluate |
| 8 | Sector Strength (experimental) | 0.0500 | — | -0.1632 | Evaluate |
| 9 | Foreign Flow (experimental) | -0.0742 | — | -0.4032 | Evaluate |

---

## Section 6: Go / No-Go Recommendations

### Decision Matrix

| Factor | IC Signal | Sharpe Impact | Alpha Impact | Go/No-Go |
|--------|:---------:|:------------:|:------------:|:--------:|
| Foreign Flow | negative/strong (IC=-0.0742) | -0.4238 | -8.76% | No-Go |
| Low Volatility | positive/strong (IC=0.0713) | 0.3288 | 6.74% | **GO** |
| Dividend | positive/strong (IC=0.1245) | 0.1945 | 4.07% | **GO** |
| Sector Strength | positive/moderate (IC=0.0500) | -0.1838 | -3.52% | Hold |

---

## Section 7: Final Recommendation

### Root Cause Summary

After decomposing CONFIG_B into its constituent factors and testing experimental alternatives:

**Factors are generating positive but weak alpha**

The primary issue is that Value is the only factor with strong positive IC.

**Alpha leakage detected:**
- **Growth** has negative IC (-0.0846), meaning the factor systematically selects stocks that underperform. Reducing its weight would improve portfolio alpha.
- **Config B** has negative IC (-0.0198), meaning the factor systematically selects stocks that underperform. Reducing its weight would improve portfolio alpha.

### Recommended Next Factor

**Low Volatility** is recommended as the next factor to add to CONFIG_B.

Based on IC strength and incremental portfolio improvement:

| Factor | Go/No-Go | Rationale |
|--------|:---------:|-----------|
| Foreign Flow | Hold | Needs further investigation |
| Low Volatility | GO | Positive IC (0.0713), Sharpe improvement of 0.3288 |
| Dividend | GO | Positive IC (0.1245), Sharpe improvement of 0.1945 |
| Sector Strength | Hold | Needs further investigation |

### Estimated Alpha Improvement

If **Low Volatility** is added at 7% weight:

| Metric | Current | Projected | Improvement |
|--------|:-------:|:---------:|:-----------:|
| CAGR | 6.83% | 13.81% | 6.99% |
| Sharpe | 0.0205 | 0.3493 | 0.3288 |
| Alpha | 0.41% | 7.15% | 6.74% |

### Production Impact Assessment

CONFIG_B weights remain frozen at 25/30/10/35.

**GO decision factors (Low Volatility, Dividend)** qualify for production research.
These factors demonstrate sufficient standalone alpha and portfolio improvement
to justify inclusion in the next research phase.

**Next step:** Full factor integration with optimized weight allocation
for factor expansion.


---

## Appendix: Methodology

### Factor IC Calculation

For each month `t`:
1. Rank all stocks by factor score (percentile 0-100)
2. Compute Spearman rank correlation between factor scores and next-month returns
3. Q5-Q1 spread: top 20% average return minus bottom 20% average return
4. Hit rate: % months where top-half stocks outperform bottom-half stocks

### Factor Decay

For each month `t` and horizon `h` (1, 3, 6, 12 months):
1. Compute cumulative forward return over h months
2. Compute IC between original factor scores and h-month forward returns
3. Half-life = horizon where IC drops below 50% of 1-month IC

### Incremental Alpha Test

Test: CONFIG_B scaled down by 7%, reallocated to experimental factor.
Portfolio: Top 5, equal-weight, monthly rebalance.
Benchmark: IHSG monthly return (aligned to same calendar month as portfolio returns).
