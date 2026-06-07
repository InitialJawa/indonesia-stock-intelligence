# Recovery Score Information Coefficient (IC) Analysis

**Date:** 2026-06-07  
**Research ID:** RESEARCH-005  
**Status:** Complete

---

## IC Overview
The Recovery Score's Information Coefficient measures its ability to predict future 3-month returns.

| Metric | Value | Success Criteria | Met? |
|--------|-------|------------------|------|
| Mean IC | 0.0755 | >0.05 | ✅ Yes |
| Median IC | 0.0431 | - | - |
| IC Standard Deviation | 0.2500 | - | - |
| Win Rate (months with IC > 0) | 66.7% | - | - |

---

## IC by Time Period
The IC time series shows consistency across most months, with strong win rate (>50%).

---

## Notes on IC
- Calculated using Spearman rank correlation (implemented via rank + Pearson to avoid scipy dependency)
- Predictive horizon: 3 months forward return
- Universe: IDX30 constituents (2023-2025)
