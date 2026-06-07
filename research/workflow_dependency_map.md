# Workflow Dependency Map

**Generated:** 2026-06-07

---

## Daily Risk Radar (daily_radar.yml)

```
GitHub Action (cron: 30 9 * * *)
    │
    ▼
data_fetcher.py ──yfinance──▶ dashboard/data.json  (inline scores)
    │
    ▼
dashboard.generate_dashboard ──▶ dashboard/index.html
    │                              dashboard/data.json (overwrites)
    │
    ▼
git commit: dashboard/data.json, dashboard/index.html,
            data_fetcher.py, dashboard/generate_dashboard.py
```

**Data sources:** Yahoo Finance API (live)

**Reads but does NOT update:**
- `output/scores/*.json` ← reads final_ranking_v3.json
- `output/raw/*.json` ← reads fundamentals.json, growth.json
- `config/sector_rules.json` ← reads bank/commodity mappings
- `output/daily_radar_status.json` ← reads radar narrative
- `database/historical/portfolio_warehouse.csv` ← reads latest portfolio

---

## ISI V4 Monthly Pipeline (monthly_pipeline.yml)

```
GitHub Action (cron: 0 2 1 * *)
    │
    ├─▶ Inject config/settings.json from GitHub Secrets
    │
    ▼
run_monthly_pipeline.py
    │
    ├── 1. collectors.fundamentals ──yfinance──▶ output/raw/fundamentals.json
    ├── 2. collectors.growth ──yfinance───────▶ output/raw/growth.json
    ├── 3. collectors.prices ──yfinance────────▶ output/raw/prices.json
    ├── 4. collectors.historical_foreign_flow ──(synthetic)──▶ database/historical_foreign_flow/*.csv
    ├── 5. backtesting.merge_foreign_flow ────────────────▶ database/monthly/*.csv (updated)
    │
    ├── 6. scoring.quality_score ────────────────────▶ output/scores/quality_ranking.json
    ├── 7. scoring.growth_score ─────────────────────▶ output/scores/growth_ranking.json
    ├── 8. scoring.value_score ──────────────────────▶ output/scores/value_ranking.json
    ├── 9. scoring.momentum_score ───────────────────▶ output/scores/momentum_ranking.json
    ├── 10. scoring.final_score_v3 ──────────────────▶ output/scores/final_ranking_v3.json
    │
    ├── 11. backtesting.archive_current_state ───────▶ archives/rankings/{YYYY-MM}.json
    ├── 12. backtesting.archive_fundamentals ────────▶ snapshots/fundamentals/{YYYY-MM}.json
    ├── 13. backtesting.archive_growth ──────────────▶ snapshots/growth/{YYYY-MM}.json
    ├── 14. backtesting.archive_factors ─────────────▶ snapshots/{quality,value,momentum,growth,final}/ + database/historical/factor_warehouse.csv
    ├── 15. backtesting.rebalance ───────────────────▶ archives/portfolios/{YYYY-MM}.json + database/historical/portfolio_warehouse.csv
    │
    └── 16. dashboard.generate_dashboard ───────────▶ dashboard/index.html + dashboard/data.json
                                                            │
                                                            ▼
                                              git commit: output/scores/ dashboard/index.html
                                                          database/ snapshots/ archives/
```

---

## Full Data Dependency Graph

```
OUTPUT/S CORES/ (Monthly only)
    quality_ranking.json ◄── quality_score.py ◄── fundamentals.json ◄── yfinance
    growth_ranking.json  ◄── growth_score.py  ◄── growth.json      ◄── yfinance
    value_ranking.json   ◄── value_score.py   ◄── fundamentals.json ◄── yfinance
    momentum_ranking.json ◄── momentum_score.py ◄── ihsg.csv + monthly/*.csv ◄── yfinance
    final_ranking_v3.json ◄── final_score_v3.py ◄── 4 factor JSONs + config/scoring_weights.json

ARCHIVES/ (Monthly only)
    rankings/{YYYY-MM}.json          ◄── archive_current_state ◄── final_ranking_v3.json
    portfolios/{YYYY-MM}.json       ◄── rebalance ◄── rankings/
    database/portfolio_warehouse.csv ◄── rebalance

DASHBOARD/ (Daily + Monthly)
    data.json  ◄── [daily: data_fetcher.py (yfinance)]
               ◄── [monthly: generate_dashboard.py (output/scores/*)]
    
    index.html ◄── generate_dashboard.py ◄── data.json + output/scores/* + sector_rules.json

DATABASE/ (Monthly)
    factor_warehouse.csv     ◄── archive_factors ◄── 4 factor JSONs + final_ranking_v3.json
    portfolio_warehouse.csv  ◄── rebalance
    monthly/{TICKER}.csv     ◄── merge_foreign_flow ◄── historical_foreign_flow/*.csv
```

---

## Key Architectural Observations

### 1. Two Parallel Score Paths (DIVERGENT)
```
DAILY PATH:   data_fetcher.py ──(inline scoring)──▶ dashboard/data.json
                         ↑                           ↓
                    (yfinance API)            (no output/scores/* write)

MONTHLY PATH: collectors ──▶ scoring modules ──▶ output/scores/* ──▶ dashboard/data.json
                                                         ↑
                                              (local file only, no API)
```
The daily path computes scores differently (no percentile normalization, simplified formulas) and never writes to `output/scores/*`. The monthly path uses normalized scores and writes all outputs.

### 2. Single Point of Truth Gap
There is **no single source of truth** for stock scores:
- The monthly pipeline produces canonical scores in `output/scores/*.json`
- The daily pipeline produces ephemeral scores in `dashboard/data.json`
- The dashboard HTML always shows `dashboard/data.json`, so the displayed scores depend on which pipeline ran last

### 3. No Back-Wiring
`data_fetcher.py` writes to `dashboard/data.json` but never to `output/scores/*.json`. This means:
- Daily runs update the visual dashboard but NOT the scoring database
- If the monthly pipeline fails, the dashboard falls back to daily scores with no record

### 4. Missing Turnaround Ranking
No turnaround ranking script exists. The dashboard has a "Sedang Anget" label derived from the action slug logic (momentum 55-85, quality > 45, value > 40), but there is no dedicated turnaround signal or ranking.

---

*End of Workflow Dependency Map*
