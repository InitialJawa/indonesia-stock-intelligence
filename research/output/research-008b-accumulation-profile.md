# RESEARCH-008B: Accumulation State Profile
**Generated:** 2026-06-07 14:31:58

---

## Definition

The accumulation state is the set of conditions most commonly observed immediately before a validated rally start event (T-5 through T0).

Validated events are rally start signals (from 4 candidate definitions) that pass forward return validation (fwd 20D > +10% OR fwd 40D > +15%).

## Candidate Definitions

| Candidate | Signal | Validation |
|-----------|--------|------------|
| A | Price crosses above MA20 after >= 20 days below | fwd20>+10% or fwd40>+15% |
| B | RS20 changes from negative to positive | same |
| C | Volume Ratio > 1.3 AND price above MA20 | same |
| D | Momentum Slope changes from negative to positive | same |

---

## Condition Prevalence at Each Offset

Values represent the percentage of events where each condition is true at each snapshot offset:

| Condition | T-40 | T-20 | T-10 | T-5 | T0 |
|-----------|------|------|------|-----|----|
| rs_20d_positive                          | 43.8% | 41.1% | 37.0% | 36.4% | 70.4% |
| rs_change_20d_improving                  | 47.3% | 48.0% | 42.7% | 44.9% | 61.2% |
| rs_change_60d_improving                  | 46.6% | 38.1% | 38.9% | 41.9% | 43.8% |
| above_ma20                               | 43.9% | 39.1% | 39.1% | 44.1% | 87.8% |
| above_ma50                               | 43.8% | 39.1% | 35.7% | 38.6% | 55.7% |
| above_ma100                              | 44.8% | 41.3% | 38.6% | 38.6% | 48.9% |
| above_ma200                              | 43.3% | 39.1% | 37.5% | 38.5% | 44.4% |
| volume_ratio_high                        | 30.4% | 29.5% | 24.5% | 24.2% | 63.5% |
| volume_ratio_very_high                   | 19.3% | 18.5% | 14.2% | 15.0% | 47.0% |
| golden_cross                             | 0.1% | 0.2% | 0.1% | 0.2% | 0.5% |
| death_cross                              | 0.9% | 0.1% | 0.9% | 0.2% | 0.3% |
| momentum_slope_positive                  | 42.9% | 41.1% | 38.0% | 33.3% | 51.4% |
| drawdown_gt_20pct                        | 56.0% | 60.7% | 64.1% | 62.4% | 57.7% |
| drawdown_gt_30pct                        | 32.6% | 39.6% | 42.4% | 41.8% | 34.4% |
| drawdown_lt_10pct                        | 18.0% | 16.0% | 16.2% | 16.9% | 22.0% |
| recovery_gt_10pct                        | 54.1% | 52.5% | 49.5% | 52.2% | 71.9% |
| recovery_gt_20pct                        | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| volatility_above_median                  | 48.5% | 49.9% | 52.5% | 49.6% | 49.4% |

## Median Feature Values at Each Offset

| Feature | T-40 | T-20 | T-10 | T-5 | T0 |
|---------|------|------|------|-----|----|
| rs_20d                    | -0.0107 | -0.0200 | -0.0336 | -0.0298 | 0.0133 |
| rs_60d                    | -0.0215 | -0.0420 | -0.0478 | -0.0419 | -0.0139 |
| rs_120d                   | -0.0189 | -0.0482 | -0.0574 | -0.0555 | -0.0263 |
| rs_252d                   | 0.0161 | -0.0181 | -0.0386 | -0.0320 | -0.0081 |
| rs_change_20d             | -0.0079 | -0.0077 | -0.0206 | -0.0165 | 0.0322 |
| rs_change_60d             | -0.0148 | -0.0524 | -0.0515 | -0.0448 | -0.0244 |
| recovery_from_60d_low     | 0.1104 | 0.1090 | 0.0978 | 0.1062 | 0.1614 |
| drawdown_252d             | -0.2240 | -0.2515 | -0.2598 | -0.2655 | -0.2383 |
| distance_from_high_252d   | -0.2240 | -0.2515 | -0.2598 | -0.2655 | -0.2383 |
| volatility_20d            | 0.3865 | 0.3923 | 0.4014 | 0.3921 | 0.3916 |
| volatility_60d            | 0.3990 | 0.4040 | 0.4069 | 0.4091 | 0.4120 |
| volume_ratio              | 0.9136 | 0.8816 | 0.8489 | 0.8517 | 1.4533 |
| momentum_slope            | -0.0004 | -0.0005 | -0.0008 | -0.0008 | 0.0000 |
| above_ma20                | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| above_ma50                | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| above_ma100               | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| above_ma200               | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| golden_cross              | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| death_cross               | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Discovered Accumulation State

### Most Common Conditions at T0 (Rally Start)

- **above_ma20**: 87.8%
- **recovery_gt_10pct**: 71.9%
- **rs_20d_positive**: 70.4%
- **volume_ratio_high**: 63.5%
- **rs_change_20d_improving**: 61.2%
- **drawdown_gt_20pct**: 57.7%
- **above_ma50**: 55.7%
- **momentum_slope_positive**: 51.4%
- **volatility_above_median**: 49.4%
- **above_ma100**: 48.9%

### Most Common Conditions at T-5 (5 Days Before)

- **drawdown_gt_20pct**: 62.4%
- **recovery_gt_10pct**: 52.2%
- **volatility_above_median**: 49.6%
- **rs_change_20d_improving**: 44.9%
- **above_ma20**: 44.1%
- **rs_change_60d_improving**: 41.9%
- **drawdown_gt_30pct**: 41.8%
- **above_ma50**: 38.6%
- **above_ma100**: 38.6%
- **above_ma200**: 38.5%

### Most Common Conditions at T-20 (20 Days Before)

- **drawdown_gt_20pct**: 60.7%
- **recovery_gt_10pct**: 52.5%
- **volatility_above_median**: 49.9%
- **rs_change_20d_improving**: 48.0%
- **above_ma100**: 41.3%
- **rs_20d_positive**: 41.1%
- **momentum_slope_positive**: 41.1%
- **drawdown_gt_30pct**: 39.6%
- **above_ma50**: 39.1%
- **above_ma20**: 39.1%

## Transition Sequence (Data-Driven)

Features ranked by when their strongest change occurs:

### Early Movers (largest change at T-40 to T-20)

- **rs_change_60d**: 57% of change happens T-40 to T-20
- **rs_120d**: 42% of change happens T-40 to T-20
- **rs_252d**: 40% of change happens T-40 to T-20
- **distance_from_high_252d**: 40% of change happens T-40 to T-20
- **drawdown_252d**: 40% of change happens T-40 to T-20

### Late Movers (largest change at T-5 to T0)

- **above_ma20**: 100% of change happens T-5 to T0
- **above_ma50**: 100% of change happens T-5 to T0
- **volume_ratio**: 90% of change happens T-5 to T0
- **rs_change_20d**: 74% of change happens T-5 to T0
- **recovery_from_60d_low**: 73% of change happens T-5 to T0

### Proposed Transition Sequence

**T-40 to T-20**: `rs_change_60d`, `rs_120d`, `rs_252d`, `distance_from_high_252d`, `drawdown_252d`, `volatility_60d`

**T-10 to T-5**: `volatility_20d`

**T-5 to T0**: `rs_60d`, `rs_20d`, `momentum_slope`, `volume_ratio`, `recovery_from_60d_low`, `rs_change_20d`, `above_ma20`, `above_ma50`

---

*End of RESEARCH-008B Accumulation Profile*
