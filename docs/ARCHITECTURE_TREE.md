# REPOSITORY ARCHITECTURE TREE

Legend: [P] = PRODUCTION | [R] = RESEARCH | [A] = ARCHIVE | [O] = OBSOLETE | [?] = REVIEW

```
indonesia-stock-intelligence/
│
├── [P] .github/workflows/
│   ├── [P] daily_radar.yml              Daily pipeline (16:30 WIB)
│   └── [P] monthly_pipeline.yml         Monthly pipeline (1st of month)
│
├── [P] scoring/                          Factor scoring engine
│   ├── [P] quality_score.py
│   ├── [P] growth_score.py
│   ├── [P] value_score.py
│   ├── [P] momentum_score.py
│   ├── [P] final_score_v3.py            Config B composite
│   └── [P] utils.py                     Percentile normalization
│
├── [P] collectors/                       Data collection
│   ├── [P] fundamentals.py               Financial ratios from Yahoo
│   ├── [P] growth.py                     Revenue/Earnings growth
│   └── [P] prices.py                     Price data
│
├── [P] utils/
│   ├── [P] data_provider.py             Yahoo Finance interface + yf_metric_map
│   ├── [P] config_loader.py             Configuration loader
│   └── [P] universe_manager.py          Historical universe definitions
│
├── [P] generate_turnaround_watchlist.py  Turnaround signal generator
├── [P] generate_exit_watchlist.py       Exit state machine
├── [P] generate_dashboard_v2.py         Dashboard HTML generator
├── [P] data_fetcher.py                  Daily price fetcher
│
├── [R] generate_yahoo_coverage.py       Coverage checker
│
├── [P] dashboard/
│   └── [P] index.html                   Single 6-tab dashboard
│
├── [P] database/
│   ├── [P] monthly/                     Monthly prices (64 tickers, 2018-2026)
│   ├── [P] historical/
│   │   ├── [P] warehouse_daily_v4.parquet  Core daily data (30 tickers)
│   │   ├── [P] ticker_metadata.csv
│   │   ├── [P] momentum_monthly_returns.csv
│   │   ├── [P] momentum_equity_curve.csv
│   │   ├── [?] factor_warehouse.csv         Only 2 months of data
│   │   ├── [?] portfolio_warehouse.csv      Only 2 months of data
│   │   └── [?] turnaround_history.csv       Only 1 day of data
│   ├── [P] historical_universe/         Semi-annual IDX30 snapshots
│   └── [P] historical_foreign_flow/     Daily foreign flow (64 tickers)
│
├── [P] warehouse/
│   ├── [P] monthly_snapshots/
│   └── [P] universe/
│
├── [P] warehouse_historical/
│   ├── [P] warehouse_v3.csv             Factor scores 2022-2025
│   └── [P] warehouse_v2_multiyear_pit.csv
│
├── [P] benchmarks/
│   ├── [P] IHSG.csv                     Daily benchmark
│   └── [P] ihsg_monthly.csv
│
├── [P] output/
│   ├── [P] raw/                         Latest fundamentals/growth/prices
│   ├── [P] scores/                      Latest factor rankings
│   └── [P] history_prices/              Daily OHLCV (65 tickers)
│
├── [P] config/
│   ├── [?] scoring_weights.json         Config B weights (hardcoded override in code)
│   └── [P] tickers.json
│
├── [P] leaders_latest.csv               Latest Config B ranking
├── [P] turnaround_latest.csv            Latest turnaround signals
├── [P] turnaround_summary.json          Latest turnaround summary
├── [P] exit_watchlist_latest.csv        Latest exit states
├── [P] exit_summary.json                Latest exit summary
├── [P] exit_entry_prices.json           Entry prices for monitoring
│
├── [R] research/
│   ├── [R] research-008b-execute.py
│   ├── [R] research-009-execute.py
│   ├── [R] research-009b-execute.py
│   ├── [R] research-010-execute.py
│   ├── [R] research-010-report-final.py
│   ├── [R] research-011_turnaround_backtest.py  NEW
│   ├── [R] research-s01-execute.py
│   ├── [R] recovery_factor.py
│   ├── [R] early_reversal_engine.py
│   ├── [R] winner_autopsy.py
│   ├── [R] out_of_sample_validation.py  V8.4 framework
│   ├── [R] rs6m_backtest_engine.py      RS-6M standalone backtest
│   ├── [R] market_state_engine.py
│   ├── [R] build_factor_warehouse_v2.py
│   ├── [R] output/                      64 research output files
│   └── [R] ... (30+ research files)
│
├── [R] momentum_backtest_engine.py      Config B backtest engine
├── [R] historical_momentum_builder.py   Historical momentum reconstruction
├── [R] historical_portfolio_builder.py  Historical portfolio reconstruction
│
├── [A] docs/archive/                    Archived files
│   ├── [A] MASTER_CHRONICLE_V2.md       Superseded by V3
│   ├── [A] master_chronicle.txt         DEPRECATED BAB 1-22
│   ├── [A] PROJECT_STATUS_2026_06_07.md
│   ├── [A] backtesting/                 Duplicate of research/
│   ├── [A] reports/                     Superseded by docs/ + research/output/
│   ├── [A] archives/                    Superseded by database/historical/ + output/scores/
│   ├── [A] root_artifacts/              One-off research scripts at root
│   ├── [A] session_logs/                Developer session logs
│   ├── [A] index.html                   Root redirect → dashboard/index.html
│   └── [A] task.md                      Scratch notes
│
├── [P] docs/
│   ├── [P] MASTER_CHRONICLE_V3.md       ← CANONICAL (read this first)
│   ├── [P] RESEARCH_INDEX.md            Research summary
│   ├── [P] LESSONS_LEARNED.md           Mistakes catalog
│   ├── [P] ARCHITECTURE_TREE.md         This file
│   ├── [P] PROJECT_STATUS.md            Current state
│   ├── [P] REPOSITORY_REFACTOR_REPORT.md
│   ├── [P] ADR-002-DATA-SOURCE.md       Architectural Decision Record
│   ├── [P] ADR-003-ALPHA-OPTIMIZED-WEIGHTS.md
│   └── [P] ADR-004-SUSPEND-WEIGHT-OPTIMIZATION.md
│
├── [P] docs/findings/
│   ├── [P] FINDING_001_MOMENTUM_ALPHA.md
│   └── [P] FINDING_010_GROWTH_FACTOR_FAILURE.md
│
├── [P] .nojekyll                         For GitHub Pages (keep — required)
├── [P] .gitignore
├── [P] requirements.txt
├── [P] README.md
```

## CLEANUP COMPLETE

All 7 items from the refactor backlog are now archived under `docs/archive/`:
- `backtesting/` → `docs/archive/backtesting/`
- `reports/` → `docs/archive/reports/`
- `archives/` → `docs/archive/archives/`
- Root `compute_*.py`, `test_*.py`, `model_audit_report.md`, `root_cause_report.md`, `fundamental_audit.md` → `docs/archive/root_artifacts/`
- `session-ses_163b.md` → `docs/archive/session_logs/`
- `task.md` → `docs/archive/task.md`
- `index.html` → `docs/archive/index.html`

## STILL DUPLICATE / REDUNDANT

- `warehouse_historical/` and `database/historical/` both store historical data (different data types — keep both)
