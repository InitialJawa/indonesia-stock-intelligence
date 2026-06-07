# REPOSITORY ARCHITECTURE TREE

**Terakhir diperbarui:** 2026-06-07 (setelah Phase 2 refactor)

Legend: [P] = PRODUCTION | [R] = RESEARCH | [A] = ARCHIVE | [C] = CONFIG

```
indonesia-stock-intelligence/
│
├── [P] .github/workflows/
│   ├── [P] daily_radar.yml              Daily pipeline (16:30 WIB)
│   └── [P] monthly_pipeline.yml         Monthly pipeline (1st of month)
│
├── [P] run_daily_risk_radar.py          Entry point — daily pipeline
├── [P] run_monthly_pipeline.py          Entry point — monthly pipeline
├── [C] .gitignore
├── [C] .nojekyll
├── [C] README.md
├── [C] requirements.txt
│
├── [P] scripts/                          Production scripts
│   ├── [P] data_fetcher.py              Daily price fetcher
│   ├── [P] generate_dashboard_v2.py     Dashboard HTML generator
│   ├── [P] generate_exit_watchlist.py   Exit state machine
│   └── [P] generate_turnaround_watchlist.py  Turnaround signal generator
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
│   ├── [P] fundamentals.py              Financial ratios from Yahoo
│   ├── [P] growth.py                    Revenue/Earnings growth
│   ├── [P] prices.py                    Price data
│   ├── [P] daily_flow_collector.py      Volume shock detection
│   ├── [P] historical_foreign_flow.py   Foreign flow data
│   └── [P] history.py                   Historical data collector
│
├── [P] utils/
│   ├── [P] data_provider.py             Yahoo Finance interface + yf_metric_map
│   ├── [P] config_loader.py             Configuration loader
│   ├── [P] universe_manager.py          Historical universe definitions
│   ├── [P] telegram_notifier.py         Telegram alert sender
│   ├── [P] email_notifier.py            Email alert sender
│   ├── [P] data_validator.py            Data quality validation
│   └── [P] logger.py                    Logging utility
│
├── [P] dashboard/
│   └── [P] index.html                   Single 6-tab dashboard
│
├── [P] data/                             Live generated data
│   ├── [P] current/                     Latest CSVs
│   │   ├── [P] leaders_latest.csv       Config B ranking
│   │   ├── [P] turnaround_latest.csv    Turnaround signals
│   │   └── [P] exit_watchlist_latest.csv  Exit states
│   └── [P] state/                       Latest JSONs
│       ├── [P] turnaround_summary.json   Turnaround summary
│       ├── [P] exit_summary.json         Exit summary
│       ├── [P] exit_entry_prices.json    Entry prices for exit monitor
│       ├── [P] company_profiles.json     Company descriptions
│       └── [P] data_quality_flags.json   DATA_QUALITY_RULE_PBV_V1 flags
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
│   │   └── [P] turnaround_history.csv       Turnaround history archive
│   ├── [P] historical_universe/         Semi-annual IDX30 snapshots
│   └── [P] historical_foreign_flow/     Daily foreign flow (64 tickers)
│
├── [P] warehouse/
│   ├── [P] monthly_snapshots/           Latest monthly snapshot
│   ├── [P] universe/                    Current universe definition
│   ├── [P] raw_inputs/                  Raw input data
│   ├── [R] archive_forward.py           Forward archive builder
│   └── [P] audit_results.json           Warehouse audit
│
├── [P] warehouse_historical/
│   ├── [P] warehouse_v3.csv             Factor scores 2022-2025
│   ├── [P] warehouse_v2_multiyear_pit.csv
│   ├── [R] build_warehouse_daily_v4.py
│   ├── [R] build_warehouse_v2_multiyear.py
│   └── [R] build_warehouse_v3.py
│
├── [P] benchmarks/
│   ├── [P] ihsg.csv                     Daily IHSG benchmark
│   └── [P] ihsg_monthly.csv
│
├── [P] output/
│   ├── [P] raw/                         Latest fundamentals/growth/prices
│   ├── [P] scores/                      Latest factor rankings
│   ├── [P] history_prices/              Daily OHLCV (65 tickers)
│   ├── [P] history/                     Radar history snapshots
│   ├── [P] charts/                      Generated charts
│   ├── [P] daily_radar_status.json      Daily radar status
│   └── [P] radar_history.json           Radar FIFO history
│
├── [C] config/
│   ├── [C] scoring_weights.json         Config B weights
│   ├── [C] sector_rules.json            Commodity/dividend rules
│   ├── [C] settings.json                Telegram/email credentials
│   └── [C] universe.json                Universe config
│
├── [C] universe/
│   └── [C] idx30.json                   IDX30 ticker list
│
├── [P] snapshots/
│   ├── [P] final/                       Monthly final score snapshots
│   ├── [P] fundamentals/                Monthly fundamental snapshots
│   ├── [P] growth/                      Monthly growth snapshots
│   ├── [P] momentum/                    Monthly momentum snapshots
│   ├── [P] quality/                     Monthly quality snapshots
│   ├── [P] value/                       Monthly value snapshots
│   ├── [P] rankings/                    Monthly ranking snapshots
│   └── [P] momentum_history/           78 monthly momentum snapshots (2019-2026)
│
├── [P] automation/
│   └── [P] monthly_job.sh              Shell script for monthly pipeline
│
├── [R] research/
│   ├── [R] research-008b-execute.py
│   ├── [R] research-009-execute.py
│   ├── [R] research-009b-execute.py
│   ├── [R] research-010-execute.py
│   ├── [R] research-010-report-final.py
│   ├── [R] research-s01-execute.py
│   ├── [R] research_011_turnaround_backtest.py
│   ├── [R] research-008-daily-winner-autopsy.py
│   ├── [R] research-008-execute.py
│   ├── [R] recovery_factor.py
│   ├── [R] early_reversal_engine.py
│   ├── [R] winner_autopsy.py
│   ├── [R] out_of_sample_validation.py  V8.4 framework (BLOCKED)
│   ├── [R] rs6m_backtest_engine.py      RS-6M standalone backtest
│   ├── [R] market_state_engine.py
│   ├── [R] build_factor_warehouse_v2.py
│   ├── [R] growth_factor_autopsy.py
│   ├── [R] recovery_overlay_validation.py
│   ├── [R] top_n_portfolio_research.py
│   ├── [R] + 20 more research scripts
│   ├── [R] tools/                       Research tools dari root
│   │   ├── [R] generate_yahoo_coverage.py
│   │   ├── [R] historical_momentum_builder.py
│   │   ├── [R] historical_portfolio_builder.py
│   │   ├── [R] momentum_backtest_engine.py
│   │   ├── [R] momentum_backtest_audit.py
│   │   └── [R] momentum_validation_analysis.py
│   └── [R] output/                      Research output files (70+)
│
├── [P] docs/
│   ├── [P] MASTER_CHRONICLE_V3.md       ← CANONICAL (read this first)
│   ├── [P] ARCHITECTURE_TREE.md         This file
│   ├── [P] RESEARCH_INDEX.md            Research summary table
│   ├── [P] LESSONS_LEARNED.md           Mistakes catalog
│   ├── [P] PROJECT_STATUS.md            Current state
│   ├── [P] AUDIT_DATA_QUALITY_REPORT.md AUDIT-001 full report
│   ├── [P] AUDIT-002_KETERSEDIAAN_DATA_YAHOO_PBV.md AUDIT-002 full report
│   ├── [P] PBV_FIX_REPORT.md            PBV fix details
│   ├── [P] REPOSITORY_REFACTOR_REPORT.md
│   ├── [P] ROOT_FILE_CLASSIFICATION.md  Phase 2 classification
│   ├── [P] ROOT_SIMPLIFICATION_REPORT.md Phase 2 report
│   ├── [P] ADR-002-DATA-SOURCE.md
│   ├── [P] ADR-003-ALPHA-OPTIMIZED-WEIGHTS.md
│   ├── [P] ADR-004-SUSPEND-WEIGHT-OPTIMIZATION.md
│   ├── [P] findings/
│   │   ├── [P] FINDING_001_MOMENTUM_ALPHA.md
│   │   └── [P] FINDING_010_GROWTH_FACTOR_FAILURE.md
│   └── [A] archive/                     Phase 1 & 2 archived components
│       ├── [A] backtesting/             Duplicate backtest code
│       ├── [A] reports/                 75+ research reports
│       ├── [A] archives/                Historical portfolios/rankings
│       ├── [A] root_artifacts/          One-off root scripts
│       ├── [A] session_logs/            Developer session logs
│       ├── [A] index.html               Root redirect (inactive)
│       ├── [A] task.md                  Scratch notes
│       ├── [A] master_chronicle.txt     Deprecated BAB 1-22
│       └── [A] MASTER_CHRONICLE_V2.md   Superseded by V3
```

## CATATAN

- `warehouse_historical/` dan `database/historical/` menyimpan tipe data berbeda — keduanya dipertahankan
- `research/out_of_sample_validation.py` — masih di `research/`, diblokir oleh Historical Factor Warehouse V2
- Root level hanya berisi 6 file operasional (target tercapai ✅)
- AUDIT-001 + AUDIT-002 selesai — data quality rule PBV aktif di `collectors/fundamentals.py`
- Mode status: STABILIZATION (no new features, no ranking changes, no research without approval)
