# RESEARCH-004B Winner Autopsy

**Date:** 2026-06-07  
**Author:** Indonesia Stock Intelligence Research Team  
**Status:** Complete  
**Objective:** Identify common characteristics that appear BEFORE large stock advances.

---

## Executive Summary

This research analyzes characteristics of stocks before large advances (3M > 20%, 6M > 40%) in IDX30 universe for 2023-2025.

Key findings:
- Higher volatility is a leading indicator
- Higher recovery from lows is a strong predictor (especially for 6M winners)
- Relative strength (RS 3M/6M) shows predictive value for 6M winners

---

## Universe & Period

- **Universe:** IDX30 constituents
- **Period:** 2023-01-01 to 2025-12-31
- **Total Observations:** 2271 ticker-months

---

## Winner Definition

1. **3M Winner:** Forward 3-month return > 20% (217 events)
2. **6M Winner:** Forward 6-month return > 40% (79 events)

---

## Analysis & Findings

### Part 1: 3-Month Winners (>20% forward return)

| Variable | Winner Mean | Non-Winner Mean | Difference | Rank |
|----------|-------------|-----------------|------------|------|
| Volatility (3M) | 0.114 | 0.086 | +0.028 | 1 |
| Recovery | 0.093 | 0.074 | +0.019 | 2 |
| Drawdown | -0.251 | -0.172 | -0.079 | 3 |
| RS 3M | -0.014 | -0.002 | -0.012 | 4 |
| RS Change | -0.014 | -0.002 | -0.012 | 5 |
| RS 6M | -0.020 | -0.009 | -0.011 | 6 |

**Key Insight for 3M Winners:** 
- Winners tend to be more volatile and recovering from larger drawdowns (contrarian bounce effect)

---

### Part 2: 6-Month Winners (>40% forward return)

| Variable | Winner Mean | Non-Winner Mean | Difference | Rank |
|----------|-------------|-----------------|------------|------|
| RS 3M | 0.040 | -0.004 | +0.044 | 1 |
| Recovery | 0.110 | 0.075 | +0.035 | 2 |
| RS 6M | 0.023 | -0.011 | +0.034 | 3 |
| RS Change | 0.018 | -0.004 | +0.022 | 4 |
| Volatility (3M) | 0.113 | 0.088 | +0.025 | 5 |
| Drawdown | -0.215 | -0.178 | -0.037 | 6 |

**Key Insight for 6M Winners:**
- Relative strength is strongly positive! Winners show excess returns vs IHSG in both 3M and 6M lookback periods.
- Recovery from recent lows is pronounced.

---

## Predictive Power Ranking

### Top Predictors by Forward Horizon

| Horizon | Top Predictor | Rationale |
|---------|---------------|-----------|
| 3 Months | Volatility (3M) | Bounce candidates have higher recent volatility |
| 6 Months | RS 3M | Sustained relative strength vs index leads to longer-term outperformance |

### Summary of Predictive Variables

| Variable | Predictive for 3M? | Predictive for 6M? | Strength |
|----------|--------------------|--------------------|----------|
| RS 3M | ❌ | ✅ | High |
| RS 6M | ❌ | ✅ | High |
| RS Change | ❌ | ✅ | Medium |
| Recovery | ✅ | ✅ | High |
| Volatility 3M | ✅ | ✅ | Medium |
| Drawdown | ✅ | ✅ | Medium |

---

## Data Limitations

Note: Full historical factor scores (quality/value/growth/momentum from ISI scoring engine) are only available for 2026-05 and 2026-06. Future research should:
1. Backfill historical factor scores for 2023-2025
2. Test interactions between factor scores and market states
3. Add sector-level analysis

---

## Files Produced

- `research/winner_autopsy.py` - Analysis script
- `research/output/winner_autopsy_data.csv` - Labeled dataset
- `research/output/winner_analysis.csv` - Detailed comparison
