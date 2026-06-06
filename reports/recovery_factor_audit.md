# Recovery Factor Audit

**Date:** 2026-06-07  
**Research ID:** RESEARCH-005  
**Status:** Complete

---

## Factor Definition

### Input Variables
The Recovery Score combines 5 normalized market state variables:

| Variable | Source | Weight in Score | Rationale |
|----------|--------|-----------------|-----------|
| Recovery | Winner Autopsy (high for both horizons) | 30% | Recovery from recent 3-month lows |
| RS 3M | Winner Autopsy (very strong for 6M winners) | 30% | 3-month relative strength vs IHSG |
| RS 6M | Winner Autopsy (strong for 6M winners) | 20% | 6-month relative strength vs IHSG |
| RS Change | Winner Autopsy | 10% | Change in 6-month relative strength |
| Volatility (3M) | Winner Autopsy | 10% | 3-month rolling volatility |

### Normalization
All variables are normalized to z-scores **per month** before being combined into the Recovery Score.

### Final Score Calculation
```
Recovery Score = (0.30 × recovery_norm) 
               + (0.30 × rs_3m_norm) 
               + (0.20 × rs_6m_norm) 
               + (0.10 × rs_change_norm) 
               + (0.10 × volatility_3m_norm)
```
The final score is then ranked monthly and inverted (so 100 is best).

---

## Variable Validation

All variables are sourced from the existing data warehouse, no external data needed:
- Calculated from monthly price and return data
- No external APIs
- No look-ahead bias (using only data available at time t)

---

## Implementation Files
- `research/recovery_factor.py` - Core factor calculation and backtest script
- `research/output/recovery_factor_data.csv` - Scores for all tickers/months
