# RESEARCH-007: Daily Warehouse V4 — Phase 1 Complete!

**Date**: 2026-06-07  
**Author**: ISI Research Team  
**Status**: ✅ Complete!

---

## Overview
Successfully built **WAREHOUSE DAILY V4** — the missing "Daily Timing Brain" for Indonesia Stock Intelligence!

---

## What We Built
### `warehouse_historical/build_warehouse_daily_v4.py`
This script:
1. **Downloads missing daily prices** (if needed)
2. **Loads IHSG benchmark** from existing `benchmarks/ihsg.csv`
3. **Calculates ALL required fields** (full list below)
4. **Writes final data** to:
   - `database/historical/warehouse_daily_v4.parquet`

---

## Final Data Spec
### Location
`database/historical/warehouse_daily_v4.parquet`

### Stats
| Metric | Value |
|--------|-------|
| Total records | 59,303 |
| Unique tickers | 30 (full IDX30) |
| Date range | 2018-01-01 → 2026-05-29 |
| Columns | 45 |

### All Fields Included
1. Date & Ticker
2. OHLCV
3. Returns: daily, 20d, 60d, 120d, 252d
4. Rolling highs/lows (20/60/120/252d)
5. Distance from 252d high, Drawdown from 252d high
6. Recovery from 60d low
7. 20d & 60d volatility (annualized)
8. Avg volume 20d & Volume Ratio
9. Relative Strength vs IHSG (20/60/120/252d)
10. RS Change (20d & 60d)
11. Momentum Slope (slope of 20d returns over 60d window)
12. MAs (20/50/100/200)
13. Above MA flags
14. Golden Cross / Death Cross

---

## Next Steps
Ready to move to:
- Phase 2: Daily Signal Research (RESEARCH-008)
- Phase 3: Daily Timing Engine
- Phase 4: HTML Integration Design

---

## Success!
✅ Phase 1 complete!
✅ Daily Warehouse V4 built and saved!
✅ All required fields included!
