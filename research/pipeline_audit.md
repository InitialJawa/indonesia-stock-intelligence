# Pipeline Audit

**Generated:** 2026-06-07

---

## Workflow 1: Daily Risk Radar & Dashboard Sync

### 1. Trigger Schedule
- **Cron:** `30 9 * * *` (daily at 09:30 UTC = 16:30 WIB)
- **Manual:** `workflow_dispatch` enabled

### 2. Inputs
| Input | Source | Description |
|-------|--------|-------------|
| Repo code | `actions/checkout@v4` | Full repository |
| Python packages | pip install | `yfinance`, `pandas`, `requests`, `requirements.txt` |
| API data | Yahoo Finance | Live stock fundamentals, prices (via `data_fetcher.py`) |
| Score files | `output/scores/*.json` | Ranking JSONs from monthly pipeline (read-only by dashboard) |
| Radar status | `output/daily_radar_status.json` | AI narrative from daily radar script |
| Sector rules | `config/sector_rules.json` | Bank/commodity mappings |

### 3. Scripts Executed
| Order | Script | What It Does |
|-------|--------|-------------|
| 1 | `python data_fetcher.py` | Fetches fundamentals + momentum from Yahoo Finance for all 30 IDX30 tickers. Computes inline quality/growth/value/momentum scores. Writes `dashboard/data.json`. |
| 2 | `python -m dashboard.generate_dashboard` | Reads `output/scores/*.json` + `dashboard/data.json` + `config/sector_rules.json`. Generates `dashboard/index.html` and overwrites `dashboard/data.json`. |

### 4. Files Generated
| File | By | Format | Contents |
|------|----|--------|----------|
| `dashboard/data.json` | `data_fetcher.py` (1st) then `generate_dashboard.py` (overwrites) | JSON | 30 stock entries with scores, fundamentals, signals, weights |
| `dashboard/index.html` | `generate_dashboard.py` | HTML | Full quant dashboard with ranking table, portfolio grid, modal |

### 5. Dashboard Files Updated
- `dashboard/data.json` — **Updated** (fully regenerated)
- `dashboard/index.html` — **Updated** (fully regenerated)

### 6. Current Failures
| Failure | Impact | Root Cause |
|---------|--------|------------|
| `generate_dashboard.py` reads `output/scores/final_ranking_v3.json` but this file is **only updated monthly** | Dashboard shows stale ranks between monthly runs | Daily workflow does NOT run the scoring pipeline — only `data_fetcher.py` |
| `data_fetcher.py` computes its OWN scores (inline, different formula) and overwrites `dashboard/data.json` | Score values differ between daily and monthly runs | Two parallel scoring paths with different algorithms |
| `data_fetcher.py` does NOT compute percentile-normalized scores | Scores are absolute values, not comparable across tickers | Simplified scoring in `data_fetcher.py` lacks `scoring/utils.py` normalization |
| `data_fetcher.py` does NOT write to `output/scores/*.json` | Daily rankings never persist to the scoring archive | Missing integration step |
| `dashboard/data.json` is staged in git commit but `generate_dashboard.py` already overwrote it | Atomicity concern — daily data.json is committed, may conflict with monthly version | Race condition between daily and monthly runs |

### 7. Current Limitations
- **No persistency:** Daily scores are ephemeral — they update the dashboard but never feed back into the monthly scoring pipeline.
- **Score inconsistency:** Daily and monthly scores use different formulas, so the dashboard's "Score" column means different things depending on when it was last run.
- **No validation:** `data_fetcher.py` has no error handling for Yahoo Finance API failures. A single failed ticker kills the entire run.
- **No notifications:** Pipeline failures are silent — no Telegram/email alerts despite the infrastructure existing in `utils/`.

---

## Workflow 2: ISI V4 Monthly Pipeline

### 1. Trigger Schedule
- **Cron:** `0 2 1 * *` (1st of each month at 02:00 UTC = 09:00 WIB)
- **Manual:** `workflow_dispatch` enabled

### 2. Inputs
| Input | Source | Description |
|-------|--------|-------------|
| Repo code | `actions/checkout@v4` | Full repository |
| Python packages | pip install | `pandas`, `yfinance`, `requests` (NO `requirements.txt`) |
| Credentials | GitHub Secrets | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SENDER_EMAIL`, `SENDER_PASSWORD` |
| API data | Yahoo Finance | Fundamentals, growth, prices (via collector modules) |
| Benchmark | `benchmarks/ihsg.csv` | IHSG daily close for RS-6M calculation |
| Monthly prices | `database/monthly/*.csv` | Per-ticker monthly CSVs with return data |
| Sector rules | `config/sector_rules.json` | Bank/commodity special rules |
| Weights | `config/scoring_weights.json` | Factor weights (Config F: Q25/G10/V30/M35) |
| Universe | `universe/idx30.json` | 30 IDX30 tickers |

### 3. Scripts Executed (via `run_monthly_pipeline.py`)

| Order | Script | Type | What It Does |
|-------|--------|------|-------------|
| 1 | `collectors.fundamentals` | API | Fetches ROE, margins, DER, FCF, PE, PB, DivYield from yfinance. Writes `output/raw/fundamentals.json`. |
| 2 | `collectors.growth` | API | Fetches revenue_growth, earnings_growth from yfinance. Writes `output/raw/growth.json`. |
| 3 | `collectors.prices` | API | Fetches last 5 days Close + Volume from yfinance. Writes `output/raw/prices.json`. |
| 4 | `collectors.historical_foreign_flow` | Synthetic | Generates fake foreign flow data. Writes `database/historical_foreign_flow/*.csv`. |
| 5 | `backtesting.merge_foreign_flow` | Local | Merges foreign flow into monthly CSVs. Updates `database/monthly/*.csv`. |
| 6 | `scoring.quality_score` | Local | Computes quality scores. Writes `output/scores/quality_ranking.json`. |
| 7 | `scoring.growth_score` | Local | Computes growth scores. Writes `output/scores/growth_ranking.json`. |
| 8 | `scoring.value_score` | Local | Computes value scores. Writes `output/scores/value_ranking.json`. |
| 9 | `scoring.momentum_score` | Local | Computes momentum scores. Writes `output/scores/momentum_ranking.json`. |
| 10 | `scoring.final_score_v3` | Local | Combines 4 factors with Config F weights. Writes `output/scores/final_ranking_v3.json`. |
| 11 | `backtesting.archive_current_state` | Local | Copies final ranking to `archives/rankings/{YYYY-MM}.json`. |
| 12 | `backtesting.archive_fundamentals` | Local | Copies raw fundamentals to `snapshots/fundamentals/{YYYY-MM}.json`. |
| 13 | `backtesting.archive_growth` | Local | Copies raw growth to `snapshots/growth/{YYYY-MM}.json`. |
| 14 | `backtesting.archive_factors` | Local | Archives all factor scores to `snapshots/` and appends to `database/historical/factor_warehouse.csv`. |
| 15 | `backtesting.rebalance` | Local | Selects Top 5 by final_score, writes `archives/portfolios/{YYYY-MM}.json` + `database/historical/portfolio_warehouse.csv`. |
| 16 | `dashboard.generate_dashboard` | Local | Generates `dashboard/index.html` + `dashboard/data.json`. |

### 4. Files Generated

| Category | Files | Format |
|----------|-------|--------|
| Raw data | `output/raw/fundamentals.json`, `output/raw/growth.json`, `output/raw/prices.json` | JSON |
| Factor scores | `output/scores/quality_ranking.json`, `output/scores/growth_ranking.json`, `output/scores/value_ranking.json`, `output/scores/momentum_ranking.json`, `output/scores/final_ranking_v3.json` | JSON |
| Archives | `archives/rankings/{YYYY-MM}.json`, `archives/portfolios/{YYYY-MM}.json` | JSON |
| Snapshots | `snapshots/fundamentals/{YYYY-MM}.json`, `snapshots/growth/{YYYY-MM}.json`, `snapshots/quality/{YYYY-MM}.json`, `snapshots/value/{YYYY-MM}.json`, `snapshots/momentum/{YYYY-MM}.json`, `snapshots/growth/{YYYY-MM}.json`, `snapshots/final/{YYYY-MM}.json` | JSON |
| Warehouse | `database/historical/factor_warehouse.csv`, `database/historical/portfolio_warehouse.csv` | CSV |
| Dashboard | `dashboard/index.html`, `dashboard/data.json` | HTML, JSON |

### 5. Dashboard Files Updated
- `dashboard/index.html` — **Updated** (regenerated with fresh factor scores)
- `dashboard/data.json` — **Updated** (regenerated with fresh factor scores)

### 6. Current Failures
| Failure | Impact | Root Cause |
|---------|--------|------------|
| `collectors.historical_foreign_flow.py` generates SYNTHETIC data | Foreign flow metrics in dashboard are meaningless | No real foreign flow API connected; random generation seeded by ticker hash |
| `pandas==3.0.3` in requirements.txt but NOT installed (pipeline explicitly uses `pip install pandas yfinance requests`, bypassing `requirements.txt`) | Potential version mismatch between local and CI environments | Workflow doesn't install `requirements.txt` |
| `collectors.prices` output not used by dashboard | Unnecessary API call — `generate_dashboard.py` fetches its OWN prices via yfinance | Missing integration |
| `warehouse/archive_forward.py` not in pipeline | Monthly snapshots don't go to warehouse directory | Script exists but was never wired into `run_monthly_pipeline.py` |
| No error handling in `run_monthly_pipeline.py` | Any single step failure kills the entire pipeline | `subprocess.run` with no retry/fallback |
| `utils/telegram_notifier.py` and `utils/email_notifier.py` exist but are never called | Pipeline failures are silent | Notification modules not wired into any workflow step |

### 7. Current Limitations
- **Monthly cadence only:** Rankings update once per month. No intra-month updates (the daily workflow runs but produces different scores).
- **No historical regeneration:** The pipeline runs forward only — there's no mechanism to regenerate historical scores when formulas change. The `ADR-004` audit found that historical factor scores don't exist, making true Config B backtesting impossible.
- **Synthetic foreign flow:** Real foreign flow data would require a paid IDX data feed. Current synthetic data has zero predictive value.
- **No sector rotation / position sizing:** Portfolio is equal-weight Top 5 with no sector constraints. A sector concentration (e.g., all banks) is possible.
- **No market regime filter:** Portfolio runs the same whether IHSG is in bull, bear, or sideways market.

---

*End of Pipeline Audit*
