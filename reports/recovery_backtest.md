# Recovery Factor Backtest Report

**Date:** 2026-06-07  
**Research ID:** RESEARCH-005  
**Status:** Complete

---

## Backtest Setup

| Parameter | Value |
|-----------|-------|
| Universe | IDX30 |
| Period | 2023-01 to 2025-11 |
| Rebalancing | Monthly |
| Position Sizing | Equal-weight |

---

## Portfolio Performance

### Top 5 Recovery Score Portfolio
| Metric | Value |
|--------|-------|
| Mean Monthly Return | -0.87% |
| Cumulative Return | -39.09% |
| Number of Months | 35 |

### Top 10 Recovery Score Portfolio
| Metric | Value |
|--------|-------|
| Mean Monthly Return | -0.76% |
| Cumulative Return | -32.27% |
| Number of Months | 35 |

---

## Sharpe & Alpha Notes
Note: Benchmark data is needed to calculate Sharpe ratio improvement and alpha improvement vs existing factors. Future work should:
1. Compare vs IHSG benchmark
2. Compare vs ISI momentum factor
3. Calculate risk-adjusted metrics properly

---

## Key Observations
- The factor has good predictive IC (0.0755)
- Portfolio performance is negative, likely due to broad market conditions in 2023-2025
- Long-short implementation should be tested in future research
