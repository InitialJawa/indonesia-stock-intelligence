# RESEARCH-008B: Rally Initiation Detection — Executive Summary
**Generated:** 2026-06-07 14:31:58

---

## Core Question

*What is the earliest detectable sign that a future winner is transitioning from distress into accumulation?*

---

## Key Findings

### 1. Best Rally Start Signal: Candidate D

**Momentum Slope Negative->Positive**

- Validated events: 171
- Precision: 23.85%
- Recall: 18.13%
- Lift vs random: 15.00x
- False Positive Rate: 0.9207%
- Avg forward 20D return: 14.36%
- Avg forward 40D return: 22.82%

### 2. Signal Stability Comparison

| Candidate | Precision | Recall | Lift | FPR | Validated Events |
|-----------|-----------|--------|------|-----|-----------------|
| A (MA20 Cross After 20D Below) | 23.62% | 10.92% | 14.86x | 0.5615% | 103 |
| B (RS20 Negative->Positive) | 20.16% | 31.92% | 12.68x | 2.0100% | 301 |
| C (Volume >1.3 + Above MA20) | 21.35% | 39.02% | 13.42x | 2.2866% | 368 |
| D (Momentum Slope Negative->Positive) | 23.85% | 18.13% | 15.00x | 0.9207% | 171 |

### 3. Earliest Detectable Sign

**rs_change_60d** — 57% of its total change occurs between T-40 and T-20, before the rally start.

Other early-changing features:

- `rs_change_60d`: 57% change at T-40→T-20
- `rs_120d`: 42% change at T-40→T-20
- `rs_252d`: 40% change at T-40→T-20
- `distance_from_high_252d`: 40% change at T-40→T-20
- `drawdown_252d`: 40% change at T-40→T-20

### 4. Transition Sequence

Based on when features peak in rate of change:

**T-40 to T-20**: `rs_change_60d`, `rs_120d`, `rs_252d`, `distance_from_high_252d`, `drawdown_252d`, `volatility_60d`

**T-10 to T-5**: `volatility_20d`

**T-5 to T0**: `rs_60d`, `rs_20d`, `momentum_slope`, `volume_ratio`, `recovery_from_60d_low`, `rs_change_20d`, `above_ma20`, `above_ma50`

### 5. Accumulation State Profile

The most common condition set at T-5 (just before rally start):

- drawdown_gt_20pct: 62.4% of events
- recovery_gt_10pct: 52.2% of events
- volatility_above_median: 49.6% of events
- rs_change_20d_improving: 44.9% of events
- above_ma20: 44.1% of events
- rs_change_60d_improving: 41.9% of events
- drawdown_gt_30pct: 41.8% of events
- above_ma50: 38.6% of events

The most common condition set at T0 (rally start):

- above_ma20: 87.8% of events
- recovery_gt_10pct: 71.9% of events
- rs_20d_positive: 70.4% of events
- volume_ratio_high: 63.5% of events
- rs_change_20d_improving: 61.2% of events
- drawdown_gt_20pct: 57.7% of events
- above_ma50: 55.7% of events
- momentum_slope_positive: 51.4% of events

### 6. Total Validated Events

- Total validated rally start events: 943
- Unique tickers with events: 30
- Date range: 2018-01-01 to 2026-05-29

---

## Answer to Research Question

*What is the earliest detectable sign that a future winner is transitioning from distress into accumulation?*

The earliest detectable sign is a change in **`rs_change_60d`**, which begins shifting 57% of its total movement between T-40 and T-20 before the rally start.

This is followed by:

2. `rs_120d` begins changing
3. `rs_252d` begins changing
4. `distance_from_high_252d` begins changing

The last changes occur in:

- `above_ma20` (concentrated at T-5 to T0)
- `above_ma50` (concentrated at T-5 to T0)
- `volume_ratio` (concentrated at T-5 to T0)
- `rs_change_20d` (concentrated at T-5 to T0)
- `recovery_from_60d_low` (concentrated at T-5 to T0)

---

*End of RESEARCH-008B Executive Summary*
