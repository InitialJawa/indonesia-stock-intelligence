# PROJECT STATUS — 2026-06-07

## What Works Today

### Config B — PRODUCTION ✅
- Ranking engine: Q25/G30/V10/M35, percentile-normalized
- Portfolio: Top 5 equal weight, monthly rebalance
- Data: Yahoo Finance (single source)
- Pipeline: Monthly on 1st of month
- Backtest: 88 months (2019-2026), CAGR +0.82%, CAPM Alpha +4.47%

### Turnaround Watchlist — RESEARCH MONITORING ✅
- 5-stage filter: deep drawdown → far from high → high volatility → RS improving → confirmation
- Output: `turnaround_latest.csv`, `turnaround_summary.json`
- Dashboard Tab 02 visualizes all signals
- Paper trading only — not a production overlay
- RESEARCH-011 confirmed: useful as watchlist, not standalone strategy

### Exit Monitor V1.1 — ACTIVE ✅
- Rule-based state machine (A/B/C/D) for all 30 tickers
- Key rule: Market weakness != stock weakness — RS20 differentiates alpha failure from beta
- Output: `exit_watchlist_latest.csv`, `exit_summary.json`, `exit_entry_prices.json`
- Dashboard Tab 06 with color-coded exit states and rule legend
- Paper trading only — no automated execution

### Dashboard — ACTIVE ✅
- Single `dashboard/index.html`, 6 tabs
- Tab 01: Leaders (Config B ranking with color-coded tickers)
- Tab 02: Turnaround (Context/Transition matches with filter buttons)
- Tab 03: Daily Summary (signal diagnostics + top candidates)
- Tab 04: History (streak tracking for context/transition)
- Tab 05: Diagnostics (pipeline health, file ages)
- Tab 06: Exit Monitor (exit states with rule legend and hover tooltips)
- Side panel: company profiles, fundamentals (ROE, ROA, PER, PBV, EPS Growth, Revenue Growth, DER, Dividend Yield, Market Cap), signal alignment, simple interpretations
- Localized in Bahasa Indonesia

### Automation — STABLE ✅
- Daily pipeline (16:30 WIB): fetches data, computes turnaround/exits, generates dashboard, commits
- Monthly pipeline (1st): refreshes fundamentals, scores all factors, archives snapshots
- GitHub Actions: `daily_radar.yml`, `monthly_pipeline.yml`

## Key Numbers

| Metric | Config B | Turnaround Top 5 | IHSG |
|--------|:--------:|:-----------------:|:----:|
| CAGR | +0.82% | -0.17% | -0.87% |
| Sharpe | 0.17 | 0.13 | 0.02 |
| Max DD | 39.66% | 43.10% | 29.83% |
| CAPM Alpha | +4.47% | +3.05% | — |
| Hit Rate | 55.68% | 59.09% | 56.82% |
| Period | 2019-02 to 2026-05 | 2019-02 to 2026-05 | 2019-02 to 2026-05 |

## Not Working / Blocked

| System | Status | Reason |
|--------|--------|--------|
| Weight Optimization (V8.4) | BLOCKED | No Historical Factor Warehouse V2 |
| OOS Config Comparison | BLOCKED | All configs produce identical rankings (missing factor scores) |
| Gemini AI Narrative | QUOTA-LIMITED | Free tier 429 errors |
| Predictive Sell Signal | ABANDONED | Not viable — RESEARCH-S01 |
| Timing Overlay (R010) | ABANDONED | Degrades all metrics |
| Historical Factor Warehouse | NOT FEASIBLE | Yahoo data only from 2021-2022 |
