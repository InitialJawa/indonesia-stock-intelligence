# ROOT FILE CLASSIFICATION

**Date:** 2026-06-07
**Phase:** 2 — Root Directory Simplification

---

## A. Production Scripts

| File | Used By | Destination |
|------|---------|-------------|
| `data_fetcher.py` | `daily_radar.yml`, standalone | `scripts/` |
| `generate_dashboard_v2.py` | `daily_radar.yml`, `run_monthly_pipeline.py`, `run_daily_risk_radar.py` | `scripts/` |
| `generate_exit_watchlist.py` | `daily_radar.yml` | `scripts/` |
| `generate_turnaround_watchlist.py` | `daily_radar.yml` | `scripts/` |

## B. Research Tools

| File | Used By | Destination |
|------|---------|-------------|
| `generate_yahoo_coverage.py` | docs only | `research/tools/` |
| `historical_momentum_builder.py` | docs only | `research/tools/` |
| `historical_portfolio_builder.py` | docs only | `research/tools/` |
| `momentum_backtest_engine.py` | docs only | `research/tools/` |
| `momentum_backtest_audit.py` | docs only | `research/tools/` |
| `momentum_validation_analysis.py` | docs only | `research/tools/` |

## C. Historical Artifact (Orphaned)

| File | Classification | Destination |
|------|---------------|-------------|
| `audit_forward_snapshot.py` | H — zero references anywhere | `docs/archive/root_artifacts/` |

## D. Generated Output — CSVs (→ `data/current/`)

| File | Produced By | Consumed By |
|------|-------------|-------------|
| `leaders_latest.csv` | `generate_turnaround_watchlist.py` | `generate_dashboard_v2.py`, `generate_exit_watchlist.py` |
| `turnaround_latest.csv` | `generate_turnaround_watchlist.py` | `generate_dashboard_v2.py` |
| `exit_watchlist_latest.csv` | `generate_exit_watchlist.py` | `generate_dashboard_v2.py` |

## E. Generated Output — JSONs (→ `data/state/`)

| File | Produced By | Consumed By |
|------|-------------|-------------|
| `company_profiles.json` | manual / external | `generate_dashboard_v2.py` |
| `exit_summary.json` | `generate_exit_watchlist.py` | — |
| `exit_entry_prices.json` | `generate_exit_watchlist.py` | `generate_exit_watchlist.py` |
| `turnaround_summary.json` | `generate_turnaround_watchlist.py` | `generate_dashboard_v2.py` |

## F. Stays at Root

| File | Reason |
|------|--------|
| `README.md` | Project documentation |
| `requirements.txt` | Dependency manifest |
| `run_daily_risk_radar.py` | Daily pipeline entry point |
| `run_monthly_pipeline.py` | Monthly pipeline entry point |
| `.gitignore` | VCS config |
| `.nojekyll` | GitHub Pages config |
