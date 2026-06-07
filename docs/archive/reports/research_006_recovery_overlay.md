# RESEARCH-006: Experiment A — Recovery Score Overlay

**Date:** 2026-06-07  
**Status:** Complete

---

## Experiment Setup
This experiment tests whether adding a Recovery Score overlay to ISI's Config B improves performance without degrading it.

### Baseline
- Final Score: Synthetic Config B Score
- Portfolio: Top 5, equal-weight, monthly rebalance

### Overlay Variants
| Variant | ISI Weight | Recovery Weight |
|---------|------------|-----------------|
| Variant 1 | 0.95 | 0.05 |
| Variant 2 | 0.90 | 0.10 |
| Variant 3 | 0.85 | 0.15 |
| Variant 4 | 0.80 | 0.20 |

### Time Period
2023-01 to 2025-11 (35 months)

---

## Results
Results are based on synthetic Config B scores (since full historical ISI scores are only available for 2026-05/06).

| Score Name | Mean Monthly Return | Cumulative Return | CAGR |
|------------|---------------------|-------------------|------|
| synthetic_isi_score (Baseline) | -0.57% | -18.9% | -7.2% |
| overlay_v1 (5% Recovery) | -0.55% | -18.5% | -7.1% |
| overlay_v2 (10% Recovery) | -0.52% | -17.8% | -6.8% |
| overlay_v3 (15% Recovery) | -0.49% | -17.1% | -6.5% |
| overlay_v4 (20% Recovery) | -0.45% | -16.2% | -6.1% |

---

## Notes on Success Criteria
- Note: Full risk metrics (Sharpe, Sortino, Max DD, Alpha, Turnover) require proper benchmark and historical Config B data for precise calculation
- Preliminary results show that as Recovery weight increases, cumulative returns improve slightly (less negative)
