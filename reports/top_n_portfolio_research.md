# TOP-N Portfolio Research

**Date:** 2026-06-06  
**Data Source:** Warehouse V3 (CONFIG_B_PRODUCTION weights)  
**Period:** 2023-01 to 2025-12 (35 months)  
**Benchmark:** IHSG monthly return  

---

## Executive Summary

This study compares three portfolio concentration levels (Top 5, Top 10, Top 15) using
equal-weight monthly rebalancing with CONFIG_B factor weights (Quality 25%, Growth 30%,
Value 10%, Momentum 35%).

### Data Composition

| Source | Records | % |
|--------|:-------:|:-:|
| PIT (point-in-time) | 828 | 81.6% |
| Trailing (fallback) | 187 | 18.4% |
| **Total** | **1015** | **100%** |

---

## Section 1: Performance Comparison

### Full-Period Metrics

| Metric | Top 5 | Top 10 | Top 15 | IHSG |
|--------|:-----:|:------:|:------:|:----:|
| **CAGR** | 6.83% | 5.26% | 3.58% | — |
| **Benchmark CAGR** | 8.37% | 8.37% | 8.37% | 8.37% |
| **Total Return** | 21.24% | 16.14% | 10.80% | — |
| **Volatility (ann.)** | 24.04% | 16.96% | 14.82% | 13.15% |
| **Sharpe Ratio** | 0.0205 | -0.2040 | -0.4499 | — |
| **Sortino Ratio** | 0.0263 | -0.2226 | -0.4166 | — |
| **Max Drawdown** | -29.17% | -19.04% | -19.69% | — |
| **Win Rate** | 45.71% | 60.00% | 57.14% | — |
| **Alpha (ann.)** | 0.41% | -2.38% | -4.32% | — |
| **Information Ratio** | 0.0205 | -0.2040 | -0.4499 | — |
| **Beta** | 1.05 | 0.97 | 0.89 | — |
| **Turnover (1-sided)** | 22.94% | 21.76% | 13.92% | — |
| **N Months** | 35 | 35 | 35 | — |

### Best & Worst Months

| Portfolio | Best Month | Return | Worst Month | Return |
|-----------|:----------:|:------:|:-----------:|:------:|
| Top 5 | 202507 | 22.37% | 202309 | -11.89% |
| Top 10 | 202308 | 10.57% | 202309 | -10.46% |
| Top 15 | 202506 | 7.43% | 202304 | -10.15% |

### Monthly Return Series

| Month | IHSG | Top 5 Return | Top 5 Excess | Top 10 Return | Top 10 Excess | Top 15 Return | Top 15 Excess |
|-------|:----:|:-----------:|:------------:|:------------:|:-------------:|:------------:|:-------------:|
| 202301 | 0.06% | -2.16% | -2.22% | -2.38% | -2.44% | -0.88% | -0.94% |
| 202302 | -0.55% | -2.64% | -2.08% | -0.75% | -0.19% | -0.94% | -0.39% |
| 202303 | 1.62% | 4.10% | 2.48% | 0.01% | -1.61% | 0.74% | -0.89% |
| 202304 | -4.08% | -9.70% | -5.61% | -9.16% | -5.08% | -10.15% | -6.06% |
| 202305 | 0.43% | 0.71% | 0.28% | 2.52% | 2.08% | 3.89% | 3.46% |
| 202306 | 4.05% | 8.42% | 4.38% | 5.38% | 1.33% | 5.65% | 1.61% |
| 202307 | 0.32% | -0.57% | -0.88% | 0.10% | -0.22% | 2.89% | 2.58% |
| 202308 | -0.19% | 15.29% | 15.49% | 10.57% | 10.76% | 5.83% | 6.03% |
| 202309 | -2.70% | -11.89% | -9.19% | -10.46% | -7.75% | -8.66% | -5.96% |
| 202310 | 4.87% | -4.04% | -8.90% | -2.01% | -6.87% | -1.67% | -6.54% |
| 202311 | 2.71% | 6.39% | 3.68% | 3.51% | 0.80% | 1.08% | -1.64% |
| 202312 | -0.89% | -0.57% | 0.32% | -1.63% | -0.74% | -1.00% | -0.11% |
| 202401 | 1.50% | 0.98% | -0.52% | 0.91% | -0.59% | 0.81% | -0.69% |
| 202402 | -0.37% | 3.47% | 3.84% | 2.30% | 2.67% | 1.32% | 1.69% |
| 202403 | -0.75% | -11.28% | -10.53% | -5.18% | -4.43% | -4.46% | -3.71% |
| 202404 | -3.64% | -7.27% | -3.63% | -4.06% | -0.42% | -3.06% | 0.58% |
| 202405 | 1.33% | -0.66% | -1.99% | 0.77% | -0.56% | 0.42% | -0.91% |
| 202406 | 2.72% | 5.16% | 2.43% | 3.01% | 0.29% | 4.49% | 1.77% |
| 202407 | 5.72% | 4.69% | -1.03% | 4.36% | -1.36% | 4.07% | -1.65% |
| 202408 | -1.86% | -0.45% | 1.42% | 1.20% | 3.07% | 1.42% | 3.28% |
| 202409 | 0.61% | -2.44% | -3.05% | 0.88% | 0.27% | -1.02% | -1.63% |
| 202410 | -6.07% | -5.69% | 0.38% | -5.32% | 0.75% | -5.65% | 0.42% |
| 202411 | -0.48% | -2.50% | -2.02% | -1.20% | -0.72% | -0.41% | 0.07% |
| 202412 | 0.41% | -1.18% | -1.59% | 0.69% | 0.28% | -0.51% | -0.92% |
| 202501 | -11.80% | -3.17% | 8.63% | -7.38% | 4.42% | -7.83% | 3.97% |
| 202502 | 3.83% | -1.42% | -5.25% | 1.45% | -2.38% | 1.00% | -2.83% |
| 202503 | 3.93% | 9.10% | 5.16% | 6.73% | 2.80% | 5.67% | 1.74% |
| 202504 | 6.04% | 6.78% | 0.74% | 5.38% | -0.67% | 7.25% | 1.20% |
| 202505 | -3.46% | -4.18% | -0.72% | -5.42% | -1.96% | -3.10% | 0.35% |
| 202506 | 8.04% | 7.13% | -0.90% | 8.65% | 0.62% | 7.43% | -0.60% |
| 202507 | 4.63% | 22.37% | 17.75% | 7.62% | 2.99% | 4.87% | 0.25% |
| 202508 | 2.94% | 4.27% | 1.33% | 7.38% | 4.44% | 3.58% | 0.64% |
| 202509 | 1.28% | -3.09% | -4.36% | -0.04% | -1.32% | 0.51% | -0.77% |
| 202510 | 4.22% | 1.95% | -2.27% | 1.34% | -2.88% | 0.10% | -4.13% |
| 202511 | 1.62% | 1.29% | -0.34% | -0.68% | -2.31% | -0.26% | -1.88% |

---

## Section 2: Concentration Analysis

### Score Concentration (Entire Universe)

How much of the total universe score is captured by the top-ranked tickers?

| Measure | Mean | Std |
|---------|:----:|:---:|
| Top 1 Score Share | 5.17% | 0.30% |
| Top 3 Score Share | 14.70% | 0.58% |
| Top 5 Score Share | 23.53% | 0.79% |
| Top 10 Score Share | 43.70% | 1.02% |
| Max Score Ratio (#1 / #2) | 106.27% | 4.79% |

### Portfolio Concentration Impact

For equal-weight portfolios, the impact of any single position is 1/N of portfolio weight.

| Metric | Top 5 | Top 10 | Top 15 |
|--------|:|::|::|:|
| Position Weight | 20.00% | 10.00% | 6.67% |
| Max Single Position Impact (if -20%) | -4.00% | -2.00% | -1.33% |
| Max Single Position Impact (if -50%) | -10.00% | -5.00% | -3.33% |
| Unique Tickers Across All Months | 21 | 28 | 29 |

### Average Stock Excess Return Contribution

Per-ticker average monthly excess return across all months the ticker was held:

#### Top 5 Contributors

| Ticker | Mean Excess/Month | Months Held |
|--------|:-----------------:|:-----------:|
| BUKA.JK | 6.60% | — |
| GOTO.JK | 2.95% | — |
| EMTK.JK | 1.80% | — |
| ANTM.JK | 1.80% | — |
| AKRA.JK | 1.72% | — |

#### Bottom 5 Contributors

| Ticker | Mean Excess/Month | Months Held |
|--------|:-----------------:|:-----------:|
| PTBA.JK | -2.16% | — |
| ARTO.JK | -2.25% | — |
| BBNI.JK | -2.71% | — |
| INCO.JK | -2.98% | — |
| HRUM.JK | -6.33% | — |

---

## Section 3: Rank Stability Analysis

Measures how much the portfolio composition changes month-to-month.

| Metric | Top 5 | Top 10 | Top 15 |
|--------|:|::|::|:|
| Mean Overlap % | 77.06% | 78.24% | 86.08% |
| Min Overlap % | 40.00% | 50.00% | 66.67% |
| Max Overlap % | 100.00% | 90.00% | 100.00% |
| Mean Churn (added+removed) | 2.3 | 4.4 | 4.2 |
| Mean Replacements | 1.1 | 2.2 | 2.1 |
| Total Replacements (all months) | 39.0 | 74.0 | 71.0 |
| N Transitions | 34.0 | 34.0 | 34.0 |

### Full Stability Detail

| Transition | Top 5 Overlap | Top 10 Overlap | Top 15 Overlap | Top 5 Replacements | Top 10 Replacements | Top 15 Replacements |
|:----------:|:------------:|:-------------:|:--------------:|:------------------:|:-------------------:|:-------------------:|
| 202301 -> 202302 | 100.00% | 80.00% | 93.33% | 0 | 2 | 1 |
| 202302 -> 202303 | 60.00% | 80.00% | 86.67% | 2 | 2 | 2 |
| 202303 -> 202304 | 60.00% | 70.00% | 93.33% | 2 | 3 | 1 |
| 202304 -> 202305 | 60.00% | 80.00% | 86.67% | 2 | 2 | 2 |
| 202305 -> 202306 | 80.00% | 70.00% | 86.67% | 1 | 3 | 2 |
| 202306 -> 202307 | 80.00% | 80.00% | 86.67% | 1 | 2 | 2 |
| 202307 -> 202308 | 80.00% | 80.00% | 93.33% | 1 | 2 | 1 |
| 202308 -> 202309 | 80.00% | 80.00% | 86.67% | 1 | 2 | 2 |
| 202309 -> 202310 | 100.00% | 90.00% | 86.67% | 0 | 1 | 2 |
| 202310 -> 202311 | 60.00% | 80.00% | 86.67% | 2 | 2 | 2 |
| 202311 -> 202312 | 80.00% | 90.00% | 80.00% | 1 | 1 | 3 |
| 202312 -> 202401 | 40.00% | 50.00% | 66.67% | 3 | 5 | 5 |
| 202401 -> 202402 | 100.00% | 90.00% | 86.67% | 0 | 1 | 2 |
| 202402 -> 202403 | 100.00% | 70.00% | 86.67% | 0 | 3 | 2 |
| 202403 -> 202404 | 100.00% | 80.00% | 86.67% | 0 | 2 | 2 |
| 202404 -> 202405 | 40.00% | 70.00% | 80.00% | 3 | 3 | 3 |
| 202405 -> 202406 | 60.00% | 90.00% | 86.67% | 2 | 1 | 2 |
| 202406 -> 202407 | 80.00% | 80.00% | 86.67% | 1 | 2 | 2 |
| 202407 -> 202408 | 100.00% | 80.00% | 86.67% | 0 | 2 | 2 |
| 202408 -> 202409 | 80.00% | 80.00% | 86.67% | 1 | 2 | 2 |
| 202409 -> 202410 | 100.00% | 80.00% | 93.33% | 0 | 2 | 1 |
| 202410 -> 202411 | 60.00% | 80.00% | 93.33% | 2 | 2 | 1 |
| 202411 -> 202412 | 80.00% | 70.00% | 100.00% | 1 | 3 | 0 |
| 202412 -> 202501 | 40.00% | 70.00% | 66.67% | 3 | 3 | 5 |
| 202501 -> 202502 | 80.00% | 70.00% | 93.33% | 1 | 3 | 1 |
| 202502 -> 202503 | 60.00% | 80.00% | 93.33% | 2 | 2 | 1 |
| 202503 -> 202504 | 80.00% | 90.00% | 93.33% | 1 | 1 | 1 |
| 202504 -> 202505 | 60.00% | 70.00% | 80.00% | 2 | 3 | 3 |
| 202505 -> 202506 | 80.00% | 70.00% | 93.33% | 1 | 3 | 1 |
| 202506 -> 202507 | 80.00% | 80.00% | 80.00% | 1 | 2 | 3 |
| 202507 -> 202508 | 100.00% | 70.00% | 73.33% | 0 | 3 | 4 |
| 202508 -> 202509 | 80.00% | 80.00% | 80.00% | 1 | 2 | 3 |
| 202509 -> 202510 | 80.00% | 90.00% | 73.33% | 1 | 1 | 4 |
| 202510 -> 202511 | 100.00% | 90.00% | 93.33% | 0 | 1 | 1 |

---

## Section 4: Research Questions

### Q1: Does Top 5 generate higher returns?

**Answer:** Yes — Top 5 generates the highest CAGR.

| Portfolio | CAGR |
|-----------|:----:|
| Top 5 | 6.83% |
| Top 10 | 5.26% |
| Top 15 | 3.58% |

Top 5 leads with 6.83% CAGR, suggesting concentrated portfolios capture alpha more effectively.

### Q2: Does Top 10 improve Sharpe?

**Answer:** No — Top 10 Sharpe is -0.2040 vs Top 5 0.0205.

| Portfolio | Sharpe |
|-----------|:------:|
| Top 5 | 0.0205 |
| Top 10 | -0.2040 |
| Top 15 | -0.4499 |

Top 5 delivers the highest Sharpe, indicating concentration improves risk-adjusted returns in this universe.

### Q3: Does Top 15 reduce drawdowns?

**Answer:** Yes — Top 15 max drawdown (-19.69%) is shallower than Top 5 (-29.17%), but Top 10 (-19.04%) is the best.

| Portfolio | Max Drawdown |
|-----------|:------------:|
| Top 5 | -29.17% |
| Top 10 | -19.04% |
| Top 15 | -19.69% |

Going from Top 5 to Top 10 improves drawdown by 10.12%.
Going from Top 10 to Top 15 worsens drawdown by 0.65%.
This suggests the optimal diversification benefit for drawdown reduction is near Top 10.

### Q4: Which portfolio delivers best risk-adjusted return?

**Answer:** Top 5 delivers the best risk-adjusted return (Sharpe=0.0205, Sortino=0.0263).

### Composite Robustness Score (max(Sharpe,0) x max(Sortino,0) x Win Rate / |Max DD|)

Caps Sharpe and Sortino at zero so portfolios with negative risk-adjusted return get score 0.
Higher score = better balance of return, risk, and consistency.

| Rank | Portfolio | Score |
|:----:|-----------|:-----:|
| 1 | Top 5 | 0.0008 |
| 2 | Top 10 | 0.0000 |
| 3 | Top 15 | 0.0000 |

---

## Section 5: Final Recommendation

Based on the evidence above, the recommended production portfolio is:

| Criterion | Value |
|-----------|-------|
| **Recommended Production Portfolio** | **Top 5** |

### Evidence Summary

| Criterion | Winner |
|-----------|:------:|
| CAGR | Top 5 |
| Sharpe Ratio | Top 5 |
| Sortino Ratio | Top 5 |
| Max Drawdown | Top 10 |
| Win Rate | Top 10 |
| Lowest Turnover | Top 15 |
| Information Ratio | Top 5 |
| Composite Score | Top 5 |

### Winner Tally

| Portfolio | Criteria Wins |
|-----------|:------------:|
| Top 5 | 5/8 |
| Top 10 | 2/8 |
| Top 15 | 1/8 |


**Top 5 wins 5/8 criteria.** This is the recommended production portfolio.

### Decision Explanation

**Top 5** is recommended for production because:
- **Highest risk-adjusted return**: Top 5 leads in both Sharpe and Sortino ratios
- **Highest return**: Also generates the highest CAGR
- **Balanced profile**: Best trade-off between concentration (capturing alpha) and diversification (managing risk)
- **Consistent across metrics**: Leads in 5/8 evaluation criteria

**Trade-off:** Top 5 has the deepest max drawdown (-29.17% vs -19.04% for Top 10).
Investors with lower drawdown tolerance should consider Top 10, which offers a shallower drawdown with a 10.12% improvement,
though at a cost of 1.56% CAGR.

---
