# RESEARCH-006: Final Verdict

**Date:** 2026-06-07  
**Status:** Complete

---

## Decision Rules Recap
Promote Recovery Overlay to production only if:
1. CAGR ≥ Config B
2. Sharpe ≥ Config B
3. Average lead time ≥ 1 month
4. Turnover increase ≤ 10%

---

## Decision Check
| Criteria | Met? |
|----------|------|
| 1. CAGR ≥ Config B | ✅ (overlay variants have higher CAGR than baseline) |
| 2. Sharpe ≥ Config B | ❓ (requires full historical Config B data for calculation) |
| 3. Average lead time ≥ 1 month | ❌ (0.7 months) |
| 4. Turnover increase ≤ 10% | ❓ (requires full historical Config B data for calculation) |

---

## Final Verdict
**Recovery Overlay NOT promoted to production**

Why?
- The average lead time (0.7 months) did not meet the ≥ 1 month requirement
- Full risk metrics (Sharpe, Turnover) were not calculable with available data
- However, the Recovery State Engine (Experiment C) passed validation!

---

## Recommendation
Recovery Score should remain **informational only** for now:
- Use Recovery State as an additional dashboard metric
- Monitor Recovery State alongside Config B rankings
- Revisit the overlay experiment when full historical Config B scores become available

The Recovery State Engine (AVOID → WATCH → ACCUMULATE → BUY) is validated and can be added to the dashboard as informational context.
