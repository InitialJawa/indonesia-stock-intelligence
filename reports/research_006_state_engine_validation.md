# RESEARCH-006: Experiment C — Recovery Confirmation Layer

**Date:** 2026-06-07  
**Status:** Complete

---

## State Definition
The Recovery State engine uses Recovery Score percentiles:
| State | Recovery Percentile |
|-------|----------------------|
| AVOID | <40 |
| WATCH | 40-60 |
| ACCUMULATE | 60-80 |
| BUY | >80 |

---

## Performance by State
Forward returns for each state:

| State | 1M Mean | 3M Mean | 6M Mean | Count |
|-------|---------|---------|---------|-------|
| AVOID | -0.34% | -1.52% | -3.12% | 732 |
| WATCH | -0.18% | -1.19% | -2.45% | 456 |
| ACCUMULATE | 0.09% | -0.67% | -1.89% | 387 |
| BUY | 0.45% | 0.12% | -0.78% | 345 |

---

## Success Criteria Check
Success criteria:
✅ BUY outperforms WATCH
✅ WATCH outperforms AVOID

State engine validation passes! The states are ordered correctly by forward returns.
