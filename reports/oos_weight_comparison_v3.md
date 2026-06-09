# OOS Weight Comparison V3 — Fixed

> Generated: 2026-06-09 17:59 WIB  
> Data: warehouse_historical/warehouse_v3.csv (2022-01 to 2025-12)  
> Bug fix: Replaced `.get(key,50)` snapshot fallback with real factor scores from V3 warehouse  

---

## Bug Fixed

Previous V8.4 framework read from `snapshots/momentum_history/*.json` which contain
only `return_12m` and `rank`. Factor score keys were absent → every `.get(key, 50)`
returned 50 → all configs scored **50.0** → identical Top 5 every month.

This version reads `warehouse_v3.csv` which has REAL `quality_score`, `growth_score`,
`value_score`, `momentum_score` per ticker per month for 2022-2025 (48 months).

## Differentiation Verified

- Confirmed: each weight config produces DIFFERENT Top-5 portfolios
- The `.get(key,50)` structural bug is fully resolved

## Data Split

| Period | Months |
|--------|-------|
| TRAIN (2022-04 → 2023-09) | 18 |
| VALIDATION (2023-10 → 2024-09) | 12 |
| TEST (2024-10 → 2025-12) | 15 |
| FULL | 45 |

## Performance by Config

| Config | Q | G | V | M | Period | CAGR | Sharpe | Alpha | WinRate | MaxDD |
|--------|---|---|---|---|--------|------|--------|-------|---------|-------|
| A (Legacy Equal) | 30% | 25% | 20% | 25% | TRAIN | 6.10% | 0.35 | +8.14% | 52.94% | 20.09% |
| A (Legacy Equal) |  |  |  |  | VALIDATION | 0.86% | 0.14 | +3.00% | 54.55% | 18.27% |
| A (Legacy Equal) |  |  |  |  | TEST | 24.48% | 0.91 | +21.98% | 50.00% | 17.93% |
| A (Legacy Equal) |  |  |  |  | FULL | 6.06% | 0.35 | +8.29% | 52.27% | 27.48% |
| | | | | |
| B (Alpha Optimized) | 25% | 30% | 10% | 35% | TRAIN | 14.06% | 0.61 | +13.90% | 58.82% | 16.27% |
| B (Alpha Optimized) |  |  |  |  | VALIDATION | -5.44% | -0.21 | -3.81% | 45.45% | 18.27% |
| B (Alpha Optimized) |  |  |  |  | TEST | 27.25% | 1.06 | +21.07% | 50.00% | 13.26% |
| B (Alpha Optimized) |  |  |  |  | FULL | 7.49% | 0.41 | +9.34% | 50.00% | 29.17% |
| | | | | |
| C (Momentum Heavy) | 20% | 25% | 5% | 50% | TRAIN | 17.46% | 0.72 | +13.93% | 64.71% | 16.27% |
| C (Momentum Heavy) |  |  |  |  | VALIDATION | 9.54% | 0.58 | +10.83% | 63.64% | 14.25% |
| C (Momentum Heavy) |  |  |  |  | TEST | 47.88% | 1.46 | +37.66% | 57.14% | 7.98% |
| C (Momentum Heavy) |  |  |  |  | FULL | 18.31% | 0.77 | +19.68% | 59.09% | 16.27% |
| | | | | |
| D (Quality First) | 40% | 25% | 10% | 25% | TRAIN | 3.87% | 0.27 | +3.53% | 47.06% | 22.16% |
| D (Quality First) |  |  |  |  | VALIDATION | 9.20% | 0.55 | +10.57% | 54.55% | 14.95% |
| D (Quality First) |  |  |  |  | TEST | 21.78% | 0.82 | +30.28% | 57.14% | 15.49% |
| D (Quality First) |  |  |  |  | FULL | 6.37% | 0.36 | +10.17% | 50.00% | 22.16% |
| | | | | |
| F (Earnings Growth) | 25% | 10% | 30% | 35% | TRAIN | 8.82% | 0.46 | +6.15% | 64.71% | 18.30% |
| F (Earnings Growth) |  |  |  |  | VALIDATION | 21.35% | 1.32 | +20.69% | 54.55% | 11.30% |
| F (Earnings Growth) |  |  |  |  | TEST | 12.79% | 0.57 | +11.71% | 57.14% | 15.01% |
| F (Earnings Growth) ⭐ |  |  |  |  | FULL | 9.23% | 0.49 | +11.33% | 56.82% | 18.30% |
| | | | | |

## Best Config

**F (Earnings Growth)** — selected by highest VALIDATION Sharpe (1.32)

## Top-5 Log (Sample)

### A (Legacy Equal)

| Month | Top 5 | Scores |
|-------|-------|--------|
| 2022-04 | ESSA.JK, ADRO.JK, BMRI.JK, BBRI.JK, BBNI.JK | [74.1, 69.0, 60.9, 59.4, 58.1] |
| 2022-05 | ESSA.JK, ADRO.JK, BMRI.JK, BBRI.JK, INCO.JK | [74.1, 68.6, 60.0, 59.0, 58.9] |
| 2022-06 | ESSA.JK, ADRO.JK, BMRI.JK, PTBA.JK, BBNI.JK | [71.9, 67.7, 60.5, 59.2, 58.6] |
| 2022-07 | ESSA.JK, ADRO.JK, BMRI.JK, BBRI.JK, PTBA.JK | [72.4, 67.2, 61.4, 59.9, 59.6] |
| 2022-08 | ESSA.JK, ADRO.JK, BMRI.JK, PTBA.JK, MEDC.JK | [73.7, 66.8, 60.0, 58.3, 57.6] |
| 2022-09 | ADRO.JK, ESSA.JK, BMRI.JK, MEDC.JK, PTBA.JK | [68.1, 63.4, 63.2, 59.8, 57.8] |

### B (Alpha Optimized)

| Month | Top 5 | Scores |
|-------|-------|--------|
| 2022-04 | ESSA.JK, ADRO.JK, INCO.JK, HRUM.JK, BMRI.JK | [82.2, 75.1, 63.3, 59.5, 59.0] |
| 2022-05 | ESSA.JK, ADRO.JK, INCO.JK, PTBA.JK, AKRA.JK | [82.2, 74.5, 65.1, 62.5, 60.5] |
| 2022-06 | ESSA.JK, ADRO.JK, PTBA.JK, AKRA.JK, AMRT.JK | [79.1, 73.2, 64.3, 61.8, 58.9] |
| 2022-07 | ESSA.JK, ADRO.JK, PTBA.JK, AKRA.JK, BMRI.JK | [79.7, 72.6, 65.0, 64.9, 59.6] |
| 2022-08 | ESSA.JK, ADRO.JK, MEDC.JK, PTBA.JK, AKRA.JK | [81.6, 72.0, 64.8, 63.1, 62.4] |
| 2022-09 | ADRO.JK, MEDC.JK, ESSA.JK, AKRA.JK, PTBA.JK | [73.8, 67.9, 67.2, 63.0, 62.5] |

### C (Momentum Heavy)

| Month | Top 5 | Scores |
|-------|-------|--------|
| 2022-04 | ESSA.JK, ADRO.JK, INCO.JK, HRUM.JK, ITMG.JK | [87.7, 80.6, 66.5, 65.7, 62.4] |
| 2022-05 | ESSA.JK, ADRO.JK, INCO.JK, PTBA.JK, AKRA.JK | [87.7, 79.7, 69.2, 68.2, 64.4] |
| 2022-06 | ESSA.JK, ADRO.JK, PTBA.JK, AKRA.JK, AMRT.JK | [83.3, 77.9, 70.9, 66.1, 66.1] |
| 2022-07 | ESSA.JK, ADRO.JK, PTBA.JK, AKRA.JK, ITMG.JK | [84.2, 77.1, 71.8, 70.6, 66.8] |
| 2022-08 | ESSA.JK, ADRO.JK, MEDC.JK, PTBA.JK, AKRA.JK | [86.8, 76.2, 69.9, 69.1, 67.0] |
| 2022-09 | ADRO.JK, MEDC.JK, PTBA.JK, AKRA.JK, ESSA.JK | [78.8, 74.4, 68.2, 67.9, 66.3] |

### D (Quality First)

| Month | Top 5 | Scores |
|-------|-------|--------|
| 2022-04 | ESSA.JK, ADRO.JK, BMRI.JK, BBRI.JK, INCO.JK | [77.7, 69.7, 63.0, 61.1, 58.4] |
| 2022-05 | ESSA.JK, ADRO.JK, BMRI.JK, BBRI.JK, INCO.JK | [77.7, 69.3, 62.1, 60.6, 59.8] |
| 2022-06 | ESSA.JK, ADRO.JK, BMRI.JK, PTBA.JK, BBRI.JK | [75.5, 68.4, 62.5, 61.0, 59.3] |
| 2022-07 | ESSA.JK, ADRO.JK, BMRI.JK, BBRI.JK, PTBA.JK | [75.9, 68.0, 63.4, 61.5, 61.4] |
| 2022-08 | ESSA.JK, ADRO.JK, BMRI.JK, PTBA.JK, AKRA.JK | [77.3, 67.5, 62.1, 60.1, 58.6] |
| 2022-09 | ADRO.JK, ESSA.JK, BMRI.JK, PTBA.JK, AKRA.JK | [68.8, 67.0, 65.2, 59.6, 59.1] |

### F (Earnings Growth)

| Month | Top 5 | Scores |
|-------|-------|--------|
| 2022-04 | ESSA.JK, ADRO.JK, BBNI.JK, BMRI.JK, ITMG.JK | [70.3, 69.1, 64.0, 63.7, 61.5] |
| 2022-05 | ESSA.JK, ADRO.JK, ITMG.JK, BBNI.JK, BMRI.JK | [70.3, 68.5, 62.8, 62.7, 62.4] |
| 2022-06 | ADRO.JK, ESSA.JK, BBNI.JK, ITMG.JK, BMRI.JK | [67.3, 67.2, 64.6, 63.4, 63.0] |
| 2022-07 | ESSA.JK, ADRO.JK, ITMG.JK, BMRI.JK, PTBA.JK | [67.8, 66.6, 64.7, 64.3, 62.4] |
| 2022-08 | ESSA.JK, ADRO.JK, BMRI.JK, ITMG.JK, PTBA.JK | [69.7, 66.0, 62.4, 61.5, 60.5] |
| 2022-09 | ADRO.JK, BMRI.JK, ITMG.JK, BBNI.JK, PTBA.JK | [67.9, 66.8, 62.8, 62.7, 59.9] |

---
*Report generated by `research/oos_weight_comparison_v3.py`*
