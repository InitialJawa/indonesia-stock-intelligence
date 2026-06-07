# ROOT SIMPLIFICATION REPORT — PHASE 2

**Date:** 2026-06-07

---

## Files Moved

### → `scripts/` (Production)
| File | Size |
|------|------|
| `data_fetcher.py` | 4.7 KB |
| `generate_dashboard_v2.py` | 51.3 KB |
| `generate_exit_watchlist.py` | 12.1 KB |
| `generate_turnaround_watchlist.py` | 15.2 KB |

### → `research/tools/` (Research)
| File | Size |
|------|------|
| `generate_yahoo_coverage.py` | 4.0 KB |
| `historical_momentum_builder.py` | 5.7 KB |
| `historical_portfolio_builder.py` | 4.1 KB |
| `momentum_backtest_engine.py` | 12.7 KB |
| `momentum_backtest_audit.py` | 22.3 KB |
| `momentum_validation_analysis.py` | 15.1 KB |

### → `data/current/` (Generated CSV)
| File | Size |
|------|------|
| `leaders_latest.csv` | 1.3 KB |
| `turnaround_latest.csv` | 1.8 KB |
| `exit_watchlist_latest.csv` | 2.7 KB |

### → `data/state/` (Generated JSON)
| File | Size |
|------|------|
| `company_profiles.json` | 6.7 KB |
| `exit_summary.json` | 0.1 KB |
| `exit_entry_prices.json` | 1.1 KB |
| `turnaround_summary.json` | 5.0 KB |

### → `docs/archive/root_artifacts/` (Orphaned)
| File | Size |
|------|------|
| `audit_forward_snapshot.py` | 2.7 KB |

## Imports Updated

### Script path changes
| File | Old Reference | New Reference |
|------|---------------|---------------|
| `run_daily_risk_radar.py:340` | `python generate_dashboard_v2.py` | `python scripts/generate_dashboard_v2.py` |
| `run_monthly_pipeline.py` | `python generate_dashboard_v2.py` | `python scripts/generate_dashboard_v2.py` |
| `daily_radar.yml` (4 steps) | `python data_fetcher.py` etc. | `python scripts/...` |
| `daily_radar.yml` (git add) | `leaders_latest.csv` etc. | `data/current/` `data/state/` |
| `monthly_pipeline.yml` (git add) | `archives/` | `data/` (removed stale `archives/`) |

### CSV/JSON path changes in moved scripts
| Script | Old Path | New Path |
|--------|----------|----------|
| `scripts/generate_dashboard_v2.py` | `leaders_latest.csv` | `data/current/leaders_latest.csv` |
| `scripts/generate_dashboard_v2.py` | `turnaround_latest.csv` | `data/current/turnaround_latest.csv` |
| `scripts/generate_dashboard_v2.py` | `turnaround_summary.json` | `data/state/turnaround_summary.json` |
| `scripts/generate_dashboard_v2.py` | `exit_watchlist_latest.csv` | `data/current/exit_watchlist_latest.csv` |
| `scripts/generate_dashboard_v2.py` | `company_profiles.json` | `data/state/company_profiles.json` |
| `scripts/generate_exit_watchlist.py` | `leaders_latest.csv` | `data/current/leaders_latest.csv` |
| `scripts/generate_exit_watchlist.py` | `exit_watchlist_latest.csv` | `data/current/exit_watchlist_latest.csv` |
| `scripts/generate_exit_watchlist.py` | `exit_summary.json` | `data/state/exit_summary.json` |
| `scripts/generate_exit_watchlist.py` | `exit_entry_prices.json` | `data/state/exit_entry_prices.json` |
| `scripts/generate_turnaround_watchlist.py` | `leaders_latest.csv` | `data/current/leaders_latest.csv` |
| `scripts/generate_turnaround_watchlist.py` | `turnaround_latest.csv` | `data/current/turnaround_latest.csv` |
| `scripts/generate_turnaround_watchlist.py` | `turnaround_summary.json` | `data/state/turnaround_summary.json` |

### Removal of broken backtesting module references
- `run_monthly_pipeline.py`: Removed 6 `python -m backtesting.*` calls (archived in Phase 1)
- `run_monthly_pipeline.py`: Removed broken `merge_foreign_flow` call

## Dashboard Validation

✅ Dashboard generated successfully: `dashboard/index.html`
- 30 leaders loaded
- 30 turnaround records
- 30 exit watchlist records
- 30 company profiles
- 30 fundamental records
- Turnaround history archived

## Remaining Root Files (6)

```
.gitignore
.nojekyll
README.md
requirements.txt
run_daily_risk_radar.py
run_monthly_pipeline.py
```

## Success Criteria

| Criterion | Status |
|-----------|--------|
| Root < 10 operational files | ✅ (6 files) |
| No research utilities at root | ✅ |
| No generated CSVs at root | ✅ |
| No audit scripts at root | ✅ |
| No backtest engines at root | ✅ |
| Dashboard generation works | ✅ |
| Pipeline YAMLs valid (syntax) | ✅ |
| All moved scripts pass syntax check | ✅ |
| Monthly pipeline backtesting steps removed | ✅ (6 broken calls removed) |
