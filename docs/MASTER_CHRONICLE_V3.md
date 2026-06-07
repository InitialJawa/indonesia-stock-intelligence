# MASTER_CHRONICLE_V3 — Indonesia Stock Intelligence

**Generated:** 2026-06-07
**Previous:** `docs/archive/MASTER_CHRONICLE_V2.md`, `docs/archive/master_chronicle.txt`
**Purpose:** Single source of truth — read this first before any code changes

---

## 1. PROJECT OVERVIEW

ISI is an Indonesia equity research system for the IDX30 index. It ranks, monitors, and visualizes
stocks using a multi-factor model (Config B) with supporting turnaround and exit monitoring layers.

**Core Philosophy:** Factor-based ranking produces alpha. Timing overlays do not add value.
No machine learning. No predictive models. Rule-based exits only.

**Status:** PRODUCTION (paper trading + dashboard monitoring)
**Mode:** STABILIZATION — no production strategy changes, no Config B modifications,
no new research without explicit approval. Focus: data integrity and documentation.

| Component | Status | Notes |
|-----------|--------|-------|
| Config B (Q25/G30/V10/M35) | PRODUCTION | Locked. Do not modify weights |
| Top 5 Portfolio | PRODUCTION | Equal weight, monthly rebalance |
| Daily Pipeline | PRODUCTION | GitHub Actions, runs 16:30 WIB |
| Dashboard | ACTIVE | Single dashboard, 5 tabs |
| Turnaround Watchlist | RESEARCH MONITORING | Paper trading only |
| Exit Monitor V1.1 | ACTIVE | Rule-based, Version C thresholds |
| AUDIT-003 | COMPLETED | Exit Layer distribution validated — Rule C 97% sensitive in bear market |

### 2.6 Exit Monitor — Sensitivity Note

**AUDIT-003 finding (2026-06-07):** Current distribution: 30% EXIT, 67% EXIT RISK, 3% HEALTHY. Rule C (Close<MA50) triggers on 97% of IDX30 because avg drawdown is -36.9% and 0/30 stocks are above MA20. State WEAKENING and EXIT WATCH are currently dead states — no stock triggers Rule A or B alone without also triggering Rule C. This is driven by broad market weakness, not threshold error, but it means the 5-level state machine collapses to 3 levels during bear markets. Exit Layer is most useful for discriminating within top 10 Config B (3 EXIT, 6 EXIT RISK, 1 HEALTHY).
| Data Quality Audit | COMPLETED | AUDIT-001 + AUDIT-002: PBV & DY fixes applied |
| Data Quality Rule | ACTIVE | DATA_QUALITY_RULE_PBV_V1 — auto-flag invalid PBV |

---

## 2. PRODUCTION SYSTEMS

### 2.1 Config B — Core Ranking Engine

**Weights:** Quality 25% | Growth 30% | Value 10% | Momentum 35%
**Portfolio:** Top 5 equal weight, monthly rebalance
**Universe:** IDX30 (dynamic historical for backtests)
**Data:** Yahoo Finance (single source)

**Key Backtest Results (2019-02 to 2026-05, 88 months):**
- CAGR: 0.82%
- Sharpe: 0.17
- Max DD: 39.66%
- CAPM Alpha: 4.47%
- Win Rate: 55.68%

**IMPORTANT:** ADR-004 (docs/ADR-004-SUSPEND-WEIGHT-OPTIMIZATION.md) suspends all
weight superiority claims. Config B runs because reverting is equally unsupported.
Do NOT modify weights without Historical Factor Warehouse V2.

### 2.2 Turnaround Watchlist

Identifies stocks transitioning from distress to accumulation using a 5-stage filter:

1. **Context Match (RESEARCH-009B):** Drawdown < -25% AND Distance from high < -20% AND Volatility top 33%
2. **Transition Match (RESEARCH-008B):** RS_CHANGE_60D > 0
3. **Confirmation (optional):** Volume > 1.3x normal, Above MA20, Recovery > 10%
4. **Full Match:** Context + Transition confirmed
5. **Ranking:** Full > Context > Transition > Confirmation count > Deeper drawdown

**Status:** Paper trading only — not a production overlay.
**RESEARCH-011 finding:** Negative absolute CAGR (-0.17%). Useful as watchlist / satellite
allocation (10-20%), not standalone strategy.

### 2.3 Exit Layer V1.1

Rule-based exit state machine for all 30 tickers. Evaluated daily.

**Rule Hierarchy (top wins):**
```
D: (Close < MA100 AND RS20 < 0 AND RS_CHANGE_20D < 0) OR DD > 15%  ->  EXIT
C: Close < MA50                                                       ->  EXIT RISK
B: RS20 < 0 AND RS_CHANGE_20D < 0                                     ->  WEAKENING
A: Rank > 10                                                          ->  EXIT WATCH
None                                                                  ->  HEALTHY
```

**Key principle (RESEARCH-S01 + RESEARCH-011):** Market weakness must be separated from
stock weakness. Close < MA100 captures beta during selloffs. Adding RS20 AND RS_CHANGE_20D
isolates alpha failure.

**Outputs:** `data/current/exit_watchlist_latest.csv`, `data/state/exit_summary.json`, `data/state/exit_entry_prices.json`

---

## 3. RESEARCH TIMELINE

| ID | Question | Answer | Impact |
|----|----------|--------|--------|
| R001-007 | Define scoring factors | Momentum > Growth > Quality > Value | Factor framework established |
| R008 | Find optimal weights | Config B (Q25/G30/V10/M35) | Production weights set |
| R008B | Detect rally initiation | RS_CHANGE_60D is earliest signal | Turnaround Transition Match |
| R009 | Validate RS_CHANGE_60D | 21.4% base precision, stable across time | Accepted with context filter |
| R009B | Why varying precision? | Volatility context determines signal quality | Context filter built |
| R010 | Timing overlay on Config B | Timing degrades all metrics | Abandoned — not production |
| R011 | Turnaround standalone alpha? | Marginal alpha, negative CAGR | Watchlist tool, not strategy |
| S01 | Predictive sell signal? | Not viable — losers look healthy at T0 | Rule-based exits built |
| AUDIT-001 | Data quality audit | PBV salah untuk 8 ticker, DY rendering 100x | PBV fix (PE×ROE), DY format fix |
| AUDIT-002 | Yahoo PBV field verification | bookValue/priceToBook salah, PE×ROE fallback terbaik | DATA_QUALITY_RULE_PBV_V1 formalized |

---

## 4. PROVEN FINDINGS

Research-supported results. Do NOT modify without new evidence.

### Factor Alpha (standalone)
- **Momentum (RS-6M + Return12M):** 19.07% CAGR — primary alpha driver
- **Growth (Earnings-only):** +22.66% CAGR — acceleration engine
- **Quality (ROE/Margins/FCF):** Moderate — drawdown stabilizer
- **Value (PE/PB/DY):** Negative IC (-0.04) — minimal exposure

### Turnaround
- Future winners originate from distressed conditions (deep drawdown + far from high + high volatility)
- RS_CHANGE_60D is the earliest detectable transition signal
- Context (volatility) matters more than threshold magnitude
- Precision: 43% on high-volatility stocks vs 4.5% on stable stocks

### Portfolio Construction
- Top 5 is optimal portfolio size (diminishing returns after 5)
- Earnings-only growth outperforms revenue+earnings blend
- Relative Strength (RS-6M) is a pure alpha generator — not redundant with price momentum

### Exit Layer
- RS_20D is strongest exit signal (Cohen's d = 0.563)
- Market weakness != stock weakness — use RS20 to differentiate
- Deterioration starts 20-40 days before collapse

---

## 5. DISPROVEN / FAILED FINDINGS

| Idea | Status | Reason |
|------|--------|--------|
| Recovery Overlay (R006) | FAILED | Lead time 0.7mo < 1mo threshold |
| Early Reversal Engine (R007) | FAILED | IC target not met |
| Distress Overlay on Config B | FAILED | Philosophical mismatch — degrades performance |
| Predictive Sell Signal (S01) | WEAK EVIDENCE | Losers indistinguishable from winners at T0 |
| Foreign Flow Factor | FAILED | Synthetic proxy invalid (validity 10/100) |
| Min-Max Normalization | FAILED | Outlier crisis — replaced by percentile |
| FMP Multi-Source | FAILED | Blocked by FMP free tier |
| Full Historical Factor Warehouse | NOT FEASIBLE | Yahoo data only from 2021-2022 |
| Weight Optimization (V8.4) | PARTIALLY COMPLETE | Cannot optimize — missing historical factor scores |
| Turnover Standalone (R011) | NEGATIVE CAGR | -0.17% — not investable as standalone |
| Timing Overlay on Config B (R010) | FAILED | Degraded all metrics |

---

## 6. DATA QUALITY FINDINGS

### AUDIT-001: Data Quality Audit (2026-06-07)
**Lingkup:** Seluruh 30 anggota IDX30 — Yahoo Finance single source.

**Masalah Kritis:**

1. **PBV Yahoo salah untuk 8 ticker** — Yahoo `priceToBook` mengembalikan nilai
   12.731–59.200× untuk saham yang seharusnya 0,7–4,7×. Semua terdampak adalah
   perusahaan komoditas/mining/energi.
   - **Fix:** PBV = PE × ROE (terbukti matematis, error <10%)
   - **7 ticker diperbaiki** (ADRO, AMMN, TPIA, BRPT, PGAS, ESSA, ITMG)
   - **1 ticker unfixable** (MDKA — PE=null karena rugi)

2. **Dividend Yield rendering 100×** — Dashboard mengalikan DY dengan 100,
   menampilkan BBCA 662% (seharusnya 6,62%).
   - **Fix:** Format `'dy'` — tidak dikali 100. Yahoo return DY sebagai persen.

**Masalah Sedang:**
- **AMMN revenue_growth = 37.937%** — data error Yahoo (seharusnya ~minor).
  Tidak pengaruh scoring (earnings-only growth), hanya tampilan dashboard.

**Dampak Scoring:** Value score 7 ticker naik signifikan (+1,38 s.d. +22,42).
Final ranking Config B tidak berubah material (value weight hanya 10%).

### AUDIT-002: Verifikasi Field Yahoo untuk PBV (2026-06-07)
**Kesimpulan:**
- `bookValue` dan `priceToBook` dari Yahoo tidak reliable untuk 8/30 ticker
- `bookValuePerShare` dan `totalEquity` selalu `None`
- `sharesOutstanding` akurat untuk semua ticker
- PE×ROE adalah fallback terbaik — error <10% vs PBV normal

**Pola:** Hanya saham komoditas/mining/energi yang terdampak (8 ticker).
Perbankan, konsumen, dan infrastruktur normal.

### DATA_QUALITY_RULE_PBV_V1
**Rule:** Jika `pb_ratio > 100` atau `< 0` → INVALID.
- Jika PE dan ROE tersedia → PBV = PE × ROE (status: FIXED)
- Jika PE=null → PBV = null (status: UNFIXABLE)
- Flag dicatat di `data/state/data_quality_flags.json`
- Never use extreme PBV in scoring

**Null PBV handling:** Null → sentinel 1e10 → worst percentile after inversion → score 0.

---

## 7. LESSONS LEARNED

1. **Future Winner != Current Leader** — Stocks with highest forward returns look distressed at entry.
2. **RS Acceleration precedes Price** — RS_CHANGE_60D > 0 precedes price recovery by 10-20 days.
3. **Market Weakness != Stock Weakness** — Condition exit rules on RS to isolate alpha failure.
4. **Backtest Success != Production** — Real-world data quality (53% null rates) differs from backtests.
5. **Data Quality before Research** — Audit data availability before building optimization frameworks.
6. **Survivorship Bias inflates everything** — Static universe CAGRs inflated by 40%. Use dynamic universe.
7. **Banks are not normal** — DER > 500% is natural for banks. Disable DER, redirect to ROE.
8. **Commodities at cycle peak are value traps** — Low PE at peak is false signal.
9. **Turnaround is a watchlist, not a strategy** — RESEARCH-011 confirmed negative absolute CAGR.
10. **Timing overlays don't work on momentum portfolios** — RESEARCH-010 confirmed degradation.

---

## 8. CURRENT ARCHITECTURE

```
ISI/
├── Entry Points (root)
│   ├── run_daily_risk_radar.py     Daily pipeline (16:30 WIB)
│   └── run_monthly_pipeline.py     Monthly pipeline (1st)
│
├── Production Scripts (scripts/)
│   ├── data_fetcher.py             Daily price fetcher
│   ├── generate_turnaround_watchlist.py   Turnaround signal generator
│   ├── generate_exit_watchlist.py         Exit state machine
│   └── generate_dashboard_v2.py           Dashboard HTML generator
│
├── Factor Scoring (scoring/)
│   ├── quality_score.py            Quality factor
│   ├── growth_score.py             Growth factor
│   ├── value_score.py              Value factor
│   ├── momentum_score.py           Momentum factor
│   └── final_score_v3.py           Config B composite (Q25/G30/V10/M35)
│
├── Data Collectors (collectors/)
│   ├── fundamentals.py             Financial ratios from Yahoo
│   ├── growth.py                   Revenue/Earnings growth
│   └── prices.py                   Price data
│
├── Shared Utilities (utils/)
│   ├── data_provider.py            Yahoo Finance interface
│   ├── config_loader.py            Configuration loader
│   ├── universe_manager.py         Historical universe definitions
│   ├── telegram_notifier.py        Telegram alerts
│   └── email_notifier.py           Email alerts
│
├── Live Data
│   ├── data/current/               Latest CSVs (leaders, turnaround, exit)
│   ├── data/state/                 Latest JSONs (summaries, profiles, entry prices)
│   └── output/                     Raw data, scores, history prices
│
├── Dashboard (dashboard/index.html)
│   ├── Tab 01: Leaders            Config B ranking with color-coded alignment
│   ├── Tab 02: Turnaround         Context/Transition signals
│   ├── Tab 03: Daily Summary      Signal diagnostics + top candidates
│   ├── Tab 04: History            Streak tracking
│   └── Tab 05: Exit Monitor       Status EXIT saham + Pipeline Diagnostics
│
├── Core Data
│   ├── database/historical/        Daily warehouse, ticker metadata, backtest curves
│   ├── database/monthly/           Monthly prices for 64 tickers, 2018-2026
│   ├── database/historical_universe/  Semi-annual IDX30 snapshots
│   ├── database/historical_foreign_flow/  Daily foreign flow (64 tickers)
│   ├── warehouse_historical/       Monthly factor scores (V3, 2022-2025)
│   └── benchmarks/                 IHSG benchmark
│
├── Research (research/)
│   ├── research/                   Individual research projects (40+ scripts)
│   ├── research/tools/             Backtest engines & historical builders
│   └── research/output/            Research output files
│
├── Automation (automation/)
│   ├── monthly_job.sh              Shell script for monthly pipeline
│   └── .github/workflows/          CI/CD pipeline definitions
│
├── Documentation (docs/)
│   ├── MASTER_CHRONICLE_V3.md      ← CANONICAL (read this first)
│   ├── ARCHITECTURE_TREE.md        Full repository tree
│   ├── RESEARCH_INDEX.md           Research summary table
│   ├── LESSONS_LEARNED.md          Mistakes catalog
│   ├── PROJECT_STATUS.md           Current state
│   ├── AUDIT_DATA_QUALITY_REPORT.md  AUDIT-001 full report
│   ├── AUDIT-002_KETERSEDIAAN_DATA_YAHOO_PBV.md  AUDIT-002 full report
│   ├── PBV_FIX_REPORT.md           PBV fix details (7 fixed, 1 unfixable)
│   ├── REPOSITORY_REFACTOR_REPORT.md  Phase 1+2 report
│   ├── ADR-002/003/004             Architectural Decision Records
│   ├── findings/                   Key research findings
│   └── archive/                    Phase 1 & 2 archived directories
```

### Produced Data Locations

| File | Location | Produced By |
|------|----------|-------------|
| Config B Leaders | `data/current/leaders_latest.csv` | `scripts/generate_turnaround_watchlist.py` |
| Turnaround Signals | `data/current/turnaround_latest.csv` | `scripts/generate_turnaround_watchlist.py` |
| Exit Watchlist | `data/current/exit_watchlist_latest.csv` | `scripts/generate_exit_watchlist.py` |
| Turnaround Summary | `data/state/turnaround_summary.json` | `scripts/generate_turnaround_watchlist.py` |
| Exit Summary | `data/state/exit_summary.json` | `scripts/generate_exit_watchlist.py` |
| Entry Prices | `data/state/exit_entry_prices.json` | `scripts/generate_exit_watchlist.py` |
| Company Profiles | `data/state/company_profiles.json` | Manual / external |
| Data Quality Flags | `data/state/data_quality_flags.json` | `collectors/fundamentals.py` |
| Dashboard | `dashboard/index.html` | `scripts/generate_dashboard_v2.py` |

---

## 9. ACTIVE WORKFLOWS

| Workflow | Schedule | Actions | Outputs |
|----------|----------|---------|---------|
| `daily_radar.yml` | 16:30 WIB daily | Fetch prices, compute turnaround, compute exits, generate dashboard | `dashboard/index.html`, `data/current/`, `data/state/` |
| `monthly_pipeline.yml` | 1st of month | Fetch fundamentals, score all factors, generate dashboard | `output/raw/*.json`, `output/scores/*.json`, `dashboard/index.html`, `data/` |

---

## 10. OPEN QUESTIONS

1. **Config F vs Config B** — Config F (Q25/G10-earnings/V30/M35) shows higher CAGR in standalone tests. Should Config B be replaced? BLOCKED: requires Historical Factor Warehouse V2 for proper OOS validation.
2. **Exit Rule D threshold** — Current Version C uses (Close<MA100 AND RS20<0 AND RS_CHANGE_20D<0) OR DD>15%. Is OR DD>15% too aggressive? Under review.
3. **Turnaround satellite allocation** — RESEARCH-011 suggests 10-20% satellite. What is the optimal blend with Config B? Requires correlation analysis.
4. **Gemini AI narrative** — Daily radar narrative generates 429 errors on free tier. Worth upgrading to paid tier?
5. **Historical Factor Warehouse V2** — Full OOS weight optimization blocked. What is the minimal viable dataset?

---

## 11. BACKLOG

### ✓ Completed
- [x] Repository Phase 1 — Documentation consolidation & archival
- [x] Repository Phase 2 — Root directory simplification
- [x] AUDIT-001 — Data quality audit (PBV fix, DY fix)
- [x] AUDIT-002 — Yahoo PBV field verification
- [x] DATA_QUALITY_RULE_PBV_V1 — Formalized and deployed
- [x] AUDIT-003 — Exit Layer distribution validation (2026-06-07) — found Rule C drives 97% classification; WEAKENING/EXIT WATCH dead states in bear market

### BACKLOG TEKNIS
- [ ] Monthly archive restoration — update `research/tools/` to read from `docs/archive/`
- [ ] Dashboard maintenance — AMMN revenue_growth display cap, cosmetic issues
- [ ] Data quality monitoring — automated flag review at monthly pipeline
- [ ] Automated daily exit watchlist execution (paper trading)
- [ ] Sector exposure monitoring for Config B portfolio
- [ ] Gemini AI narrative to paid tier (if quota critical)

### ANTRIAN RISET
- [ ] Build Historical Factor Warehouse V2 (2021-present factor scores)
- [ ] Re-run OOS weight validation with real factor data
- [ ] Config B vs Config F comparison on real historical data
- [ ] Turnaround-Config B blended portfolio correlation study
- [ ] Exit Rule D threshold backtest (V1.1 vs alternatives)
