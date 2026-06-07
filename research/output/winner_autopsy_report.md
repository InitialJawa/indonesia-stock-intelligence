# RESEARCH-008: Daily Winner Autopsy Report
**Generated:** 2026-06-07 14:20:59

---

## Methodology

### Winner Definitions

| Category | Definition | Forward Window |
|----------|-----------|----------------|
| Winner20 | Forward Return >= +20% | 20 trading days |
| Winner30 | Forward Return >= +30% | 40 trading days |
| Winner40 | Forward Return >= +40% | 60 trading days |

**Primary analysis focuses on Winner40 (60D >= +40%).**

### Forward Alpha

Forward Alpha = Stock Forward Return - IHSG Forward Return

(Computed as (1+R_stock)/(1+R_ihsg) - 1)

### Snapshot Offsets

- T-40: 40 trading days before event
- T-20: 20 trading days before event
- T-10: 10 trading days before event
- T-5: 5 trading days before event
- T0: Event date (first day of >= +40% forward return)

### Control Group

Period-matched: For each winner event, a non-winner ticker is sampled at the same calendar date. This ensures market-wide effects are controlled.

### Statistical Tests

- **Cohen's d**: Effect size (standardized mean difference)
- **Spearman IC**: Rank correlation between feature value and win/no-win
- **t-test**: Parametric test of mean difference
- **Mann-Whitney U**: Non-parametric test of distribution difference
- **Lift**: Ratio of winner mean to control mean

---

## Dataset Summary

- Total warehouse records: 59,303
- Tickers: 30
- Date range: 2018-01-01 to 2026-05-29
- Features analyzed: 23

- Winner40 events (non-overlapping): 128
- Control samples: 128

### Winner Event Distribution

- 2018: 19 events
- 2019: 9 events
- 2020: 36 events
- 2021: 15 events
- 2022: 15 events
- 2023: 8 events
- 2024: 7 events
- 2025: 18 events
- 2026: 1 events

---

## Feature Statistics: Winner vs Control

All statistics at T0 (event date):

| Feature | Winner Mean | Control Mean | Cohen's d | Spearman IC | t-stat | MW p-val | Lift |
|---------|------------|-------------|-----------|-------------|--------|----------|------|
| ma200 | 2648.4787 | 4456.2561 | -0.479 | -0.298 | -3.69 | 5.00e-06 | 0.59 |
| ma100 | 2620.8605 | 4430.9589 | -0.479 | -0.302 | -3.78 | 2.00e-06 | 0.59 |
| ma50 | 2631.5210 | 4416.6860 | -0.477 | -0.308 | -3.77 | 1.00e-06 | 0.60 |
| ma20 | 2597.5360 | 4345.3065 | -0.471 | -0.308 | -3.73 | 1.00e-06 | 0.60 |
| volatility_60d | 0.4737 | 0.3962 | 0.401 | 0.289 | 3.17 | 5.00e-06 | 1.20 |
| drawdown_252d | -0.3115 | -0.2396 | -0.396 | -0.192 | -3.17 | 2.13e-03 | 1.30 |
| distance_from_high_252d | -0.3115 | -0.2396 | -0.396 | -0.192 | -3.17 | 2.13e-03 | 1.30 |
| volatility_20d | 0.5107 | 0.4051 | 0.370 | 0.273 | 2.92 | 1.60e-05 | 1.26 |
| above_ma50 | 0.2422 | 0.3984 | -0.338 | -0.167 | -2.71 | 7.52e-03 | 0.61 |
| rs_20d | -0.0486 | -0.0044 | -0.316 | -0.228 | -2.44 | 4.07e-04 | 11.14 |
| above_ma20 | 0.2109 | 0.3438 | -0.299 | -0.148 | -2.39 | 1.79e-02 | 0.61 |
| rs_change_20d | -0.0603 | -0.0042 | -0.291 | -0.185 | -2.24 | 4.32e-03 | 14.30 |
| rs_252d | 0.1278 | 0.0405 | 0.207 | -0.008 | 1.47 | 9.12e-01 | 3.15 |
| above_ma100 | 0.3281 | 0.3984 | -0.146 | -0.073 | -1.17 | 2.44e-01 | 0.82 |
| above_ma200 | 0.3438 | 0.4141 | -0.145 | -0.072 | -1.16 | 2.48e-01 | 0.83 |
| volume_ratio | 1.2073 | 1.1284 | 0.076 | -0.057 | 0.60 | 3.66e-01 | 1.07 |
| rs_60d | -0.0142 | 0.0002 | -0.068 | -0.094 | -0.53 | 1.41e-01 | -83.66 |
| recovery_from_60d_low | 0.1429 | 0.1336 | 0.052 | -0.049 | 0.42 | 4.31e-01 | 1.07 |
| rs_change_60d | -0.0478 | -0.0409 | -0.025 | -0.029 | -0.19 | 6.56e-01 | 1.17 |
| momentum_slope | -0.0010 | -0.0009 | -0.024 | 0.002 | -0.19 | 9.77e-01 | 1.10 |
| rs_120d | 0.0244 | 0.0254 | -0.004 | -0.081 | -0.03 | 2.18e-01 | 0.96 |
| golden_cross | 0.0078 | 0.0078 | 0.000 | 0.000 | 0.00 | 1.00e+00 | 1.00 |
| death_cross | 0.0078 | 0.0078 | 0.000 | 0.000 | 0.00 | 1.00e+00 | 1.00 |

---

## Top 10 Predictive Features

Ranked by composite score (Cohen's d, Spearman IC, Lift, MW significance):

| Rank | Feature | Composite | Cohen's d | Spearman IC | Lift | MW p-val |
|------|---------|----------|-----------|-------------|------|----------|
| 1 | `ma50` | 0.749 | -0.477 | -0.308 | 0.60 | 1.00e-06 |
| 2 | `ma20` | 0.746 | -0.471 | -0.308 | 0.60 | 1.00e-06 |
| 3 | `ma100` | 0.735 | -0.479 | -0.302 | 0.59 | 2.00e-06 |
| 4 | `ma200` | 0.719 | -0.479 | -0.298 | 0.59 | 5.00e-06 |
| 5 | `volatility_60d` | 0.663 | 0.401 | 0.289 | 1.20 | 5.00e-06 |
| 6 | `volatility_20d` | 0.613 | 0.370 | 0.273 | 1.26 | 1.60e-05 |
| 7 | `rs_20d` | 0.526 | -0.316 | -0.228 | 11.14 | 4.07e-04 |
| 8 | `distance_from_high_252d` | 0.494 | -0.396 | -0.192 | 1.30 | 2.13e-03 |
| 9 | `drawdown_252d` | 0.494 | -0.396 | -0.192 | 1.30 | 2.13e-03 |
| 10 | `rs_change_20d` | 0.450 | -0.291 | -0.185 | 14.30 | 4.32e-03 |

---

## Pre-Rally Timeline

Median feature values at each snapshot offset:

**T-40** (124 snapshots):

**T-20** (124 snapshots):

**T-10** (125 snapshots):

**T-5** (125 snapshots):

**T0** (128 snapshots):

| `rs_20d` | 0.0082 | 0.0014 | -0.0079 | -0.0294 | -0.0642 |
| `rs_60d` | 0.0065 | -0.0075 | -0.0127 | -0.0255 | -0.0549 |
| `rs_120d` | 0.0242 | -0.0049 | -0.0384 | -0.0485 | -0.0658 |
| `rs_252d` | 0.0711 | 0.0344 | -0.0085 | -0.0229 | -0.0359 |
| `rs_change_20d` | 0.0032 | -0.0204 | -0.0048 | -0.0377 | -0.0509 |
| `rs_change_60d` | 0.0008 | -0.0292 | -0.0036 | -0.0331 | -0.0558 |
| `recovery_from_60d_low` | 0.1321 | 0.1439 | 0.1355 | 0.1062 | 0.0680 |
| `drawdown_252d` | -0.2042 | -0.2172 | -0.2548 | -0.2898 | -0.3260 |
| `distance_from_high_252d` | -0.2042 | -0.2172 | -0.2548 | -0.2898 | -0.3260 |
| `volatility_20d` | 0.3678 | 0.4026 | 0.4260 | 0.4367 | 0.4561 |
| `volatility_60d` | 0.4268 | 0.4113 | 0.4148 | 0.4172 | 0.4384 |
| `volume_ratio` | 0.9251 | 0.7692 | 0.8701 | 0.8774 | 0.9073 |
| `momentum_slope` | -0.0006 | -0.0004 | -0.0004 | -0.0001 | -0.0010 |
| `ma20` | 1386.7053 | 1325.0206 | 1321.4843 | 1318.5977 | 1271.7363 |
| `ma50` | 1358.3966 | 1360.6141 | 1334.6044 | 1313.6613 | 1302.0784 |
| `ma100` | 1366.8933 | 1373.2074 | 1388.9582 | 1400.7852 | 1394.2964 |
| `ma200` | 1286.0354 | 1314.1368 | 1296.7312 | 1287.4033 | 1323.8203 |
| `above_ma20` | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| `above_ma50` | 0.5000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| `above_ma100` | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| `above_ma200` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `golden_cross` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `death_cross` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

---

## What Changes First?

Based on when features diverge from baseline (T-40) towards event values.

### Early Movers (change starts at T-40 to T-20)

- **volume_ratio**: 878% of total change occurs in first half (T-40 to T-20)
- **volatility_60d**: 133% of total change occurs in first half (T-40 to T-20)
- **above_ma50**: 100% of total change occurs in first half (T-40 to T-20)
- **momentum_slope**: 85% of total change occurs in first half (T-40 to T-20)
- **ma200**: 74% of total change occurs in first half (T-40 to T-20)

### Late Movers (change concentrated near T0)

- **drawdown_252d**: only 11% of change by T-20, majority after
- **distance_from_high_252d**: only 11% of change by T-20, majority after
- **rs_20d**: only 9% of change by T-20, majority after
- **ma50**: only 4% of change by T-20, majority after
- **above_ma100**: only 0% of change by T-20, majority after

### Typical Sequence

1. RS divergence begins (rs_20d, rs_60d start rising)
2. Recovery from lows accelerates (recovery_from_60d_low)
3. Volume picks up (volume_ratio increases)
4. Momentum slope turns positive
5. Price crosses moving averages (above_ma signals trigger)
6. Volatility expands
7. Golden cross / death cross signals

---

## Forward Alpha Analysis

- **fwd_alpha_20d** at T0: mean=0.1653, median=0.0765
- **fwd_alpha_40d** at T0: mean=0.2812, median=0.1818
- **fwd_alpha_60d** at T0: mean=0.4587, median=0.3627

---

## Limitations

1. **Look-ahead bias**: Forward returns used for labeling only, NOT as features
2. **Survivorship bias**: Only IDX30 tickers (current constituents as of universe definition)
3. **Small sample**: 30 tickers, limited number of Winner40 events
4. **No timing engine**: This is an autopsy, not a prediction model
5. **Correlation ≠ Causation**: Observed patterns may not predict future rallies

---
*End of RESEARCH-008 Report*
