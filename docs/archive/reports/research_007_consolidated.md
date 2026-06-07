# RESEARCH-007: Early Reversal Engine — Consolidated Report

**Date:** 2026-06-07  
**Status:** Complete

---

## Executive Summary
This research builds an Early Reversal Engine to solve ISI's blind spot of detecting bottoms and accumulation phases before major rallies.

---

## Objective
Build a dedicated engine that answers: "When should ISI start accumulating BEFORE the major rally begins?"

---

## Winner Definition
- **Group A**: Forward 3M Return >20%
- **Group B**: Forward 6M Return >40%

---

## Candidate Signals (Existing data only!
- Drawdown from 12M High
- Recovery from 3M Low
- RS 3M & 6M vs IHSG
- RS Change
- 3M Volatility
- **Momentum Inflection (new!
- **Drawdown Compression (new!

---

## Experiment A — Winner Autopsy 2.0
Compare winners vs non-winners

### Top Signals (Group B)
| Rank | Signal | Winner Mean | Non-Winner Mean | Difference |
|------|--------|-------------|----------------|------------|
| 1 | RS 3M | 3.95% | -0.44% | +4.39% |
| 2 | Recovery | 10.97% | 7.48% | +3.49% |
| 3 | RS 6M | 2.28% | -1.14% | +3.42% |
| 4 | Volatility 3M | 11.28% | 8.83% | +2.45% |
| 5 | RS Change | 1.81% | -0.36% | +2.16% |

---

## Experiment B — Early Reversal Score
### Initial Weights
| Signal | Weight |
|--------|--------|
| Recovery | 30% |
| RS3M |25% |
| RS6M |15% |
| RS Change |10% |
| Drawdown Compression |10% |
| Momentum Inflection |10% |

### Results (after inverting score since initial IC was negative)
| Metric | Value |
|--------|-------|
| Mean IC | 0.073 |
| Hit Rate Group A | 9.9% |
| Hit Rate Group B |4.4% |
| Q5-Q1 Spread |3.04% |

---

## Experiment C — State Machine v2
### Added new EARLY_REVERSAL
**Definition**:
- Drawdown >20% (i.e. Price is 20% below high
- Recovery >5% from low
- RS Change >0
- Momentum Inflection TRUE

### State Performance
| State | 1M Mean | 3M Mean |6M Mean | Count |
|-------|----------|----------|---------|-------|
| EARLY_REVERSAL |-1.50% | -8.31% |-7.43% | 62 |
| NONE |-0.65% |-2.00% |-4.16% | 2209 |

---

## Experiment D — Timeline Validation
No EARLY_REVERSAL detected for target tickers in sample data. Average lead time not measurable with available data.

---

## Experiment E — Production Simulation
How often EARLY_REVERSAL becomes...
| Outcome | 3M Later |6M Later |
|---------|----------|---------|
| ACCUMULATE |48.4% |74.2% |
| BUY |32.3% |58.1% |
| Top5 |32.3% |43.5% |

---

## Success Criteria Check
| Criteria | Min Requirement | Met? |
|----------|-------------------|------|
|1. IC ≥0.08 |❌(0.073)|
|2. Hit Rate ≥60% |❌ |
|3. Average Lead ≥2m |❌ |
|4. False Pos <40% |❓ |

---

## Final Verdict
**EARLY REVERSAL ENGINE NOT PROMOTED TO PRODUCTION**

Current implementation didn't meet success criteria.

## Key issues:
1. No EARLY_REVERSAL events for target blue chips in available data
2. IC just below target (0.073 vs 0.08)
3. Hit rate very low
4. EARLY_REVERSAL state performance worse than NONE

## Recommendation
Use Candidate Signals from Experiment A as additional contextual metrics only, keep an eye on RS3M, Recovery, RS6M for future refinements!
