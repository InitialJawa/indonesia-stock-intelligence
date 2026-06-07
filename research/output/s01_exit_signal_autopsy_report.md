# RESEARCH-S01: Exit Signal Autopsy Report
**Generated:** 2026-06-07 15:11:20

---

## Methodology

### Underperformer Definition

| Category | Definition | Window |
|----------|-----------|--------|
| LoserAlpha20 | Forward Alpha vs IHSG <= -10% | 20 trading days |
| LoserAlpha40 | Forward Alpha vs IHSG <= -12% | 40 trading days |
| LoserAlpha60 | Forward Alpha vs IHSG <= -15% | 60 trading days |

**Primary analysis: LoserAlpha60 (60D alpha <= -15%).**

Forward Alpha = (1+R_stock)/(1+R_ihsg) - 1 (isolates stock-specific weakness)

### Snapshot Offsets

- T-40: 40 trading days before event
- T-20: 20 trading days before event
- T-10: 10 trading days before event
- T-5: 5 trading days before event
- T0: Event date (first day of alpha <= -15%)

### Control Group

Period-matched: For each loser event, a non-loser ticker is sampled at the same calendar date.

### Statistical Tests

- **Cohen's d**: Effect size (standardized mean difference)
- **Spearman IC**: Rank correlation between feature value and lose/no-lose
- **t-test**: Parametric test of mean difference
- **Mann-Whitney U**: Non-parametric test of distribution difference
- **Lift**: Ratio of loser mean to control mean

---

## Dataset Summary

- Total warehouse records: 59,303
- Tickers: 30
- Date range: 2018-01-01 to 2026-05-29
- Features analyzed: 23
- LoserAlpha60 events (non-overlapping): 303
- Control samples: 303

### Event Distribution by Year

- 2018: 33 events
- 2019: 43 events
- 2020: 38 events
- 2021: 36 events
- 2022: 25 events
- 2023: 41 events
- 2024: 39 events
- 2025: 47 events
- 2026: 1 events

---

## Feature Statistics: Loser vs Control (at T0)

| Feature | Loser Mean | Control Mean | Cohen's d | Spearman IC | t-stat | MW p-val | Lift |
|---------|-----------|-------------|-----------|-------------|--------|----------|------|
| rs_20d | 0.0774 | -0.0035 | 0.563 | 0.302 | 6.78 | 0.00e+00 | -22.27 |
| above_ma20 | 0.7459 | 0.4851 | 0.555 | 0.268 | 6.84 | 0.00e+00 | 1.54 |
| rs_change_20d | 0.0799 | -0.0140 | 0.499 | 0.255 | 5.95 | 0.00e+00 | -5.69 |
| volume_ratio | 1.3991 | 1.0394 | 0.420 | 0.216 | 5.13 | 0.00e+00 | 1.35 |
| above_ma50 | 0.6700 | 0.4851 | 0.380 | 0.187 | 4.68 | 4.00e-06 | 1.38 |
| volatility_20d | 0.4219 | 0.3551 | 0.363 | 0.191 | 4.44 | 3.00e-06 | 1.19 |
| rs_60d | 0.0789 | 0.0086 | 0.319 | 0.121 | 3.81 | 3.81e-03 | 9.20 |
| rs_252d | 0.2097 | 0.0596 | 0.296 | 0.081 | 3.35 | 6.40e-02 | 3.52 |
| above_ma100 | 0.6370 | 0.5116 | 0.255 | 0.127 | 3.14 | 1.81e-03 | 1.25 |
| rs_120d | 0.1303 | 0.0356 | 0.248 | 0.115 | 2.90 | 6.74e-03 | 3.66 |
| rs_change_60d | 0.0393 | -0.0254 | 0.197 | 0.107 | 2.30 | 1.27e-02 | -1.55 |
| recovery_from_60d_low | 0.2758 | 0.1941 | 0.193 | 0.236 | 2.38 | 0.00e+00 | 1.42 |
| momentum_slope | 0.0003 | -0.0003 | 0.175 | 0.086 | 2.12 | 3.80e-02 | -0.86 |
| above_ma200 | 0.6040 | 0.5182 | 0.173 | 0.086 | 2.13 | 3.35e-02 | 1.17 |
| death_cross | 0.0066 | 0.0000 | 0.115 | 0.058 | 1.42 | 1.58e-01 | N/A |
| ma50 | 3756.6558 | 4190.2756 | -0.097 | -0.047 | -1.19 | 2.54e-01 | 0.90 |
| ma20 | 3785.7714 | 4201.1983 | -0.093 | -0.045 | -1.13 | 2.72e-01 | 0.90 |
| drawdown_252d | -0.1751 | -0.1871 | 0.083 | 0.050 | 1.02 | 2.21e-01 | 0.94 |
| distance_from_high_252d | -0.1751 | -0.1871 | 0.083 | 0.050 | 1.02 | 2.21e-01 | 0.94 |
| ma100 | 3790.7474 | 4148.1530 | -0.081 | -0.035 | -0.98 | 3.97e-01 | 0.91 |
| ma200 | 3759.6235 | 4083.5085 | -0.075 | -0.035 | -0.89 | 4.07e-01 | 0.92 |
| volatility_60d | 0.4262 | 0.4807 | -0.042 | 0.170 | -0.51 | 3.60e-05 | 0.89 |
| golden_cross | 0.0033 | 0.0033 | 0.000 | 0.000 | 0.00 | 1.00e+00 | 1.00 |

---

## Top 10 Exit Signals

Ranked by composite score:

| Rank | Feature | Composite | Cohen's d | Spearman IC | Lift | MW p-val |
|------|---------|----------|-----------|-------------|------|----------|
| 1 | `rs_20d` | 1.000 | 0.563 | 0.302 | -22.27 | 0.00e+00 |
| 2 | `rs_change_20d` | 0.749 | 0.499 | 0.255 | -5.69 | 0.00e+00 |
| 3 | `above_ma20` | 0.724 | 0.555 | 0.268 | 1.54 | 0.00e+00 |
| 4 | `volume_ratio` | 0.607 | 0.420 | 0.216 | 1.35 | 0.00e+00 |
| 5 | `recovery_from_60d_low` | 0.503 | 0.193 | 0.236 | 1.42 | 0.00e+00 |
| 6 | `above_ma50` | 0.365 | 0.380 | 0.187 | 1.38 | 4.00e-06 |
| 7 | `rs_60d` | 0.360 | 0.319 | 0.121 | 9.20 | 3.81e-03 |
| 8 | `volatility_20d` | 0.358 | 0.363 | 0.191 | 1.19 | 3.00e-06 |
| 9 | `rs_120d` | 0.258 | 0.248 | 0.115 | 3.66 | 6.74e-03 |
| 10 | `rs_252d` | 0.253 | 0.296 | 0.081 | 3.52 | 6.40e-02 |

**NOTE:** Negative Cohen's d = feature value is LOWER in losers than controls.
Positive Cohen's d = feature value is HIGHER in losers.

---

## Pre-Collapse Timeline

Median feature values from T-40 to T0:

| `rs_20d` | -0.0078 | -0.0054 | 0.0060 | 0.0106 | 0.0519 |
| `rs_60d` | -0.0028 | -0.0057 | -0.0019 | 0.0130 | 0.0458 |
| `rs_120d` | -0.0142 | -0.0016 | 0.0091 | 0.0120 | 0.0551 |
| `rs_252d` | 0.0280 | 0.0111 | 0.0049 | 0.0182 | 0.0449 |
| `rs_change_20d` | -0.0011 | -0.0114 | 0.0112 | 0.0129 | 0.0480 |
| `rs_change_60d` | -0.0082 | 0.0010 | -0.0187 | -0.0114 | 0.0520 |
| `recovery_from_60d_low` | 0.1412 | 0.1430 | 0.1446 | 0.1524 | 0.2038 |
| `drawdown_252d` | -0.1981 | -0.1958 | -0.1941 | -0.1783 | -0.1470 |
| `distance_from_high_252d` | -0.1981 | -0.1958 | -0.1941 | -0.1783 | -0.1470 |
| `volatility_20d` | 0.3604 | 0.3585 | 0.3511 | 0.3556 | 0.3859 |
| `volatility_60d` | 0.3854 | 0.3805 | 0.3803 | 0.3838 | 0.3897 |
| `volume_ratio` | 0.8846 | 0.9481 | 0.8882 | 0.8582 | 1.1256 |
| `momentum_slope` | -0.0003 | -0.0000 | -0.0002 | 0.0000 | 0.0002 |
| `ma20` | 2171.8640 | 2141.0905 | 2134.9605 | 2101.6496 | 2131.7227 |
| `ma50` | 2180.4986 | 2132.2877 | 2158.6353 | 2173.3867 | 2128.7171 |
| `ma100` | 2148.3812 | 2147.1505 | 2127.3255 | 2140.2342 | 2130.2774 |
| `ma200` | 2141.0809 | 2130.5650 | 2149.1145 | 2163.0140 | 2171.6578 |
| `above_ma20` | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| `above_ma50` | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| `above_ma100` | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| `above_ma200` | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| `golden_cross` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `death_cross` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

---

## Deterioration Sequence

Features ranked by WHEN they change (early = T-40 to T-20, late = T-5 to T0):

### Earliest Signals (change starts 20-40 days before collapse)

- **volatility_60d**: 115% of total change in first half (INCREASING)
- **above_ma20**: 100% of total change in first half (INCREASING)
- **above_ma100**: 100% of total change in first half (INCREASING)
- **rs_252d**: 99% of total change in first half (INCREASING)
- **ma50**: 93% of total change in first half (INCREASING)

### Latest Signals (change concentrated just before collapse)

- **drawdown_252d**: only 5% of change by T-20 (INCREASING)
- **distance_from_high_252d**: only 5% of change by T-20 (INCREASING)
- **rs_20d**: only 4% of change by T-20 (INCREASING)
- **recovery_from_60d_low**: only 3% of change by T-20 (INCREASING)
- **above_ma200**: only 0% of change by T-20 (INCREASING)

### Typical Deterioration Sequence

1. **volatility_60d** declines (d=-0.04)
2. **ma50** declines (d=-0.10)
3. **ma20** declines (d=-0.09)
4. **ma100** declines (d=-0.08)
5. **ma200** declines (d=-0.07)
6. **rs_20d** rises as distress signal (d=0.56)
7. **rs_change_20d** rises as distress signal (d=0.50)
8. **above_ma20** rises as distress signal (d=0.56)
9. Stock enters full exit risk zone

---

## SELL WATCHLIST: 3-State Classification

Based on the autopsy findings, stocks can be classified into:

### HEALTHY
- No deterioration signals detected
- Key features (volatility_60d, ma50) near or above control group medians

### WEAKENING (early warning)
- At least 2 of the following:
  - `volatility_60d` declining
  - `ma50` turning negative
  - Volume starting to dry up
  - Price approaching MA20 (still above)

### EXIT RISK (confirmed deterioration)
- At least 3 of the following:
  - Price below MA20 AND MA50
  - RS_CHANGE_60D deeply negative
  - Drawdown expanding past -20%
  - Volume ratio below 0.7 (drying up)
  - Recovery from 60d low stalling

---

## Forward Alpha Analysis

- **fwd_alpha_20d** at T0: mean=-0.0452, median=-0.0434
- **fwd_alpha_40d** at T0: mean=-0.0819, median=-0.0795
- **fwd_alpha_60d** at T0: mean=-0.1775, median=-0.1652

---

## Limitations

1. **Look-ahead bias**: Forward alpha used for labeling only, NOT as features
2. **Survivorship bias**: Only IDX30 tickers (current constituents)
3. **Small sample**: 30 tickers, limited number of extreme underperformance events
4. **No timing engine**: This is an autopsy, not a prediction model
5. **Alpha is relative**: Underperformance vs IHSG may reflect sector rotation, not stock-specific issues
6. **Event clustering**: Underperformance events may cluster (2020 COVID, 2022 bear market)

---
*End of RESEARCH-S01 Report*
