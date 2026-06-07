# RESEARCH-008 Executive Summary
**Generated:** 2026-06-07 14:20:59
**Data Source:** `warehouse_daily_v4.parquet` (59,303 rows, 30 IDX30 tickers)
**Winner Definition:** Forward 60D return >= +40% (Winner40)

---

## Core Question

*What consistently happens before major IDX30 rallies begin?*

---

## Key Findings

### 1. Top Predictive Signal: `ma50`

- Cohen's d: -0.477
- Spearman IC: -0.308
- Lift: 0.60x
- Mann-Whitney p: 1.00e-06

### 2. Top 10 Predictive Features (Composite Score)

| Rank | Feature | Score | Cohen's d | Spearman IC | Lift |
|------|---------|-------|-----------|-------------|------|
| 1 | `ma50` | 0.749 | -0.477 | -0.308 | 0.60x |
| 2 | `ma20` | 0.746 | -0.471 | -0.308 | 0.60x |
| 3 | `ma100` | 0.735 | -0.479 | -0.302 | 0.59x |
| 4 | `ma200` | 0.719 | -0.479 | -0.298 | 0.59x |
| 5 | `volatility_60d` | 0.663 | 0.401 | 0.289 | 1.20x |
| 6 | `volatility_20d` | 0.613 | 0.370 | 0.273 | 1.26x |
| 7 | `rs_20d` | 0.526 | -0.316 | -0.228 | 11.14x |
| 8 | `distance_from_high_252d` | 0.494 | -0.396 | -0.192 | 1.30x |
| 9 | `drawdown_252d` | 0.494 | -0.396 | -0.192 | 1.30x |
| 10 | `rs_change_20d` | 0.450 | -0.291 | -0.185 | 14.30x |

### 3. Pre-Rally Timeline Summary

Timeline of median feature values from T-40 to T0 (event day):

- **rs_20d**: 0.0082 -> 0.0014 -> -0.0079 -> -0.0294 -> -0.0642
- **rs_60d**: 0.0065 -> -0.0075 -> -0.0127 -> -0.0255 -> -0.0549
- **volume_ratio**: 0.9251 -> 0.7692 -> 0.8701 -> 0.8774 -> 0.9073
- **recovery_from_60d_low**: 0.1321 -> 0.1439 -> 0.1355 -> 0.1062 -> 0.0680
- **momentum_slope**: -0.0006 -> -0.0004 -> -0.0004 -> -0.0001 -> -0.0010
- **distance_from_high_252d**: -0.2042 -> -0.2172 -> -0.2548 -> -0.2898 -> -0.3260
- **volatility_20d**: 0.3678 -> 0.4026 -> 0.4260 -> 0.4367 -> 0.4561

### 4. Winner Event Sample

- Total Winner40 events (non-overlapping): 128
- Control group size: 128
- Date range includes: 2018-01-01 to 2026-05-29

### 5. What Changes First?

Features ranked by *when* they change (higher = changes earlier):

| Feature | Early Change % (T-40 to T-20 / Total) | Total Change |
|---------|--------------------------------------|-------------|
| `volume_ratio` | 877.9% | 0.0178 |
| `volatility_60d` | 133.1% | 0.0116 |
| `above_ma50` | 100.0% | 0.5000 |
| `momentum_slope` | 84.8% | 0.0003 |
| `ma200` | 74.4% | 37.7849 |
| `ma20` | 53.7% | 114.9690 |
| `rs_change_60d` | 53.0% | 0.0567 |
| `rs_change_20d` | 43.6% | 0.0540 |

---

*End of RESEARCH-008 Executive Summary*
