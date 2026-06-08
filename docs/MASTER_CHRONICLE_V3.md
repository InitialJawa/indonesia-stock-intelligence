# MASTER_CHRONICLE_V3 — Indonesia Stock Intelligence

## RESEARCH-013A Baseline Reproducibility Audit (PASS)
- **Result:** Config B baseline successfully reproduced from raw inputs.
- **CAGR difference:** 0.11%
- **Sharpe difference:** 0.70%
- **Alpha difference:** 0.14%
- **Conclusion:** Baseline metrics are reproducible and suitable for further robustness audits.



**Generated:** 2026-06-08
**Previous:** `docs/archive/MASTER_CHRONICLE_V2.md`, `docs/archive/master_chronicle.txt`
**Purpose:** Single source of truth — read this first before any code changes

---

## 1. PROJECT OVERVIEW

ISI is an Indonesia equity research system for the IDX30 index. It ranks, monitors, and visualizes
stocks using a multi-factor model (Config B) with supporting turnaround and exit monitoring layers.

**Core Philosophy:** Factor-based ranking produces alpha. Timing overlays do not add value.
No machine learning. No predictive models. Rule-based exits only.
**RESEARCH-012 confirms:** Portfolio-level overlays (rank-drop, Turnaround replacement) reduce returns vs Config B alone.

**Status:** PRODUCTION (paper trading + dashboard monitoring)
**Mode:** STABILIZATION — no production strategy changes, no Config B modifications,
no new research without explicit approval. Focus: data integrity and documentation.
**ENGINEERING RULE-005:** Chronicle First Development — document before implementing.
**Dashboard Rule:** All enhancements must be append-only. Never modify existing render paths
or DOM elements. Core interactivity (ticker click, help, AI Analysis) has higher priority
than new panels.

| Component | Status | Notes |
|-----------|--------|-------|
| Config B (Q25/G30/V10/M35) | PRODUCTION | Locked. Do not modify weights |
| Top 5 Portfolio | PRODUCTION | Equal weight, monthly rebalance |
| Daily Pipeline | PRODUCTION | GitHub Actions, runs 16:30 WIB |
| Dashboard | ACTIVE | 6 tabs + Kesimpulan Hari Ini + Insight panels (append-only) |
| Turnaround Watchlist | RESEARCH MONITORING | Paper trading only |
| Exit Monitor V1.1 | ACTIVE | Rule-based, Version C thresholds |
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
**RESEARCH-012 (GATE-001) confirmed:** Config B Top 5 monthly rebalance (46.33% CAGR, 2022-2025) is the strongest validated production strategy. No overlay tested improved on it.

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
| IMPLEMENT-003 | Dashboard regression recovery | Insight Layer V1 caused TDZ crash (PF before init), table disappearance | ENGINEERING RULE-005 established, append-only mandate |
| RESEARCH-012 | Portfolio Decision Layer | Does EXIT + Rank + Turnaround beat passive Top 5? | CLOSED — FAILED. Event-level gains don't translate to portfolio level. Config B remains sole engine. |
| RESEARCH-012A | EXIT Sell Hypothesis | Does EXIT state justify automatic selling? | REJECTED — EXIT stocks outperform Healthy at 90D (+2.16%, p=0.04) |
| RESEARCH-012B | Rank Deterioration Validation | Can rank deterioration justify selling? | COMPLETE — Drop > 10 validated: 25.58% CAGR, 16.61% Alpha. Promoted to P3 |
| RESEARCH-012D | Decision Layer Production Gate Review | Does integrated Decision Layer beat Config B? | FAILED. V1: 34.92% CAGR vs Config B 46.33%. V2: 22.74%. Event-level edge does not survive integration. |

### RESEARCH-012: Portfolio Decision Layer V1

**Status:** CLOSED — FAILED | **Date:** 2026-06-08

**Conclusion:** Event-level improvements from rank-drop (>10) and Turnaround replacement do NOT translate to portfolio-level outperformance vs Config B. Config B monthly rebalance captures leadership rotation efficiently. Additional overlays create friction and reduce CAGR.

**Phase 1 — Exit Validation** ✅ COMPLETED 2026-06-08
Question: Do EXIT stocks underperform after the signal?
Method: Reconstruct historical EXIT signals from warehouse_daily_v4 (2022-2026, 30 IDX30 tickers) using Rule D (Close<MA100 + RS20<0 + RS_CHG<0 / drawdown>15%). Event-based: first-entry only (832 EXIT, 446 HEALTHY events). Forward returns 30/60/90D.
Result: **NOT CONFIRMED** — EXIT stocks do NOT underperform. 30D: +0.53% excess vs Healthy (p=0.39). 90D: +2.16% excess — significantly *outperform* (p=0.04). Sub-signal D1 (technical breakdown) only: -0.13% avg, -0.85% excess vs Healthy (p=0.18, NS). D2 (drawdown>15%): +2.05% avg, predicts bounceback.
Gate: NOT passed — EXIT is NOT a candidate SELL signal standalone. Decision matrix (Phase 4) required to combine EXIT with Rank for useful signals.

**Phase 2 — Rank Deterioration Test** ✅ COMPLETED 2026-06-08
Question: Does leaving Top N or rank collapse justify selling?
Method: Monthly backtest 2022-01 to 2025-12, Config B universe (21-29 tickers). Compare: Exit Top 5/10/20 thresholds vs Drop >5/10/15 ranks vs Baseline (monthly Top 5 rebalance).
Result: **CONFIRMED — Rank collapse exceeds baseline.** Drop > 10 ranks: 25.58% CAGR (vs 19.45% baseline), 0.76 Sharpe (vs 0.58), 16.61% Alpha (vs 10.95%), MaxDD -20.2% (vs -29.2%), turnover 4.6% (vs 20.4%). Exit thresholds ALL underperform (Exit Top 5: 16.65% CAGR). Drop > 5: 23.31% CAGR, also beats baseline. Drop > 15: 13.62%, underperforms.
Decision rule: **SELL when rank drops by > 10 from entry rank** — replace with highest-ranked unheld stock.
Gate: **PASSED** — Drop > 5 and Drop > 10 materially improve CAGR (+3.86% and +6.13% respectively) vs Baseline.

**Phase 3 — Replacement Test** ✅ COMPLETED 2026-06-08
Question: Is replacing weak holdings better than holding them?
Method: For each rank-drop >10 event, compare HOLD (keep deteriorated stock) vs REPLACE (sell + buy highest-ranked eligible). Portfolio-level and event-level analysis. 2022-2025 Config B universe.
Result: **PASSED — Replacement consistently outperforms hold.** Portfolio: REPLACE 24.21% CAGR (+4.76% vs HOLD), 0.68 Sharpe (+0.11), 15.40% Alpha (+4.45%), MaxDD -20.7% (vs -29.2%). Event-level (10 events): 6M win rate 70%, avg excess +10.07%. Replaced stocks had negative 1M returns (-1.66%), confirming rank drop >10 is genuine deterioration. Replacements bounced back: +1.91% (1M), +14.60% (3M), +16.00% (6M).
Gate: **PASSED** — replacement consistently outperforms hold across all metrics.

**Phase 4 — Exit + Rank Decision Matrix** ✅ COMPLETED 2026-06-08
Build empirical decision matrix from every EXIT state × Rank bucket combination (30D forward returns). Daily warehouse 2022-2026, 31k classified records across 12 cells.
Result: **Matrix created. Hypothesized rules (EXIT→SELL, EXIT→TRIM) invalidated by data.**
Key findings:
  - EXIT RISK (Close < MA50) is the ONLY consistently negative state: -0.23% (Top 10), -0.82% (Rank 11-20), -0.48% (Rank >20) 30D avg
  - EXIT + Top 10: +1.70% 30D (HOLD, NOT REVIEW) — confirms Phase 1
  - EXIT + Rank >20: +0.85% 30D (HOLD caution, NOT SELL)
  - WEAKENING + Rank 11-20: -1.39% 30D (worst cell, 41.3% WR)
Derived rules:
  - HOLD: HEALTHY Top 10, EXIT WATCH any, WEAKENING Top 10/>20, EXIT Top 10
  - REVIEW: EXIT RISK any rank, WEAKENING Rank 11-20
  - No TRIM/SELL cells found — no combination produces sufficiently negative returns
Decision Layer implication: EXIT alone cannot justify TRIM or SELL. Only EXIT RISK (technical breakdown below MA50) warrants REVIEW.

**Phase 5 — Turnaround Promotion Test** ✅ COMPLETED 2026-06-08
Question: When should Turnaround candidates replace existing holdings?
Method: For each month (2022-2025) where Top 5 holding is in EXIT state AND Full Match Turnaround candidate exists, compare: HOLD (keep weak stock) vs REPLACE (buy Turnaround). 78 events identified.
Result: **PASSED — Turnaround replacement creates measurable improvement.** 1M: REPLACE +5.31% vs HOLD -1.65% (diff +6.95%, 68.5% WR). 3M: diff +6.81% (50.7% WR). 6M: diff +8.40% (49.3% WR). Avg diff across horizons: +7.39%. Strongest edge is short-term (1M).
Interpretation: Turnaround works best as immediate replacement upon EXIT signal in a holding. Edge decays over time (6M WR ~50%). Best used tactically.
Gate: **PASSED** — measurable improvement confirmed. Avg win rate 56.2% across horizons.

**Production Gate — GATE-001** ❌ FAILED 2026-06-08
Integrated backtest (53 months, 2022-2025, daily+warehouse data):
| Strategy | CAGR | Sharpe | MaxDD | Alpha |
|----------|------|--------|-------|-------|
| Config B Top 5 | **46.33%** | 1.43 | -18.3% | 49.03% |
| DL V1 (rank drop + Turnaround) | 34.92% | 1.07 | -17.7% | 36.16% |
| DL V2 (rank drop only) | 22.74% | 0.70 | -18.0% | 25.16% |
**Verdict: FAILED** — No Decision Layer variant beats Config B. Event-level gains do not survive portfolio integration.
**Decision Layer V1 rejected.** Config B remains sole production engine. Exit Layer stays monitoring-only. Turnaround stays watchlist-only.
**RESEARCH-012 closed.** Do not re-open unless new evidence emerges.

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

### Exit Signals
- **EXIT→SELL is invalid** — EXIT stocks outperform Healthy at 90D (+2.16%, p=0.04). EXIT cannot be used as a standalone SELL signal.
- D1 sub-signal (Close<MA100 + RS20<0 + RS_CHG<0): -0.85% excess at 30D, not significant (p=0.18)
- D2 sub-signal (drawdown>15% from 252d high): predicts bounceback (+1.33% excess at 30D, p=0.08)

### Exit + Rank Decision Matrix (RESEARCH-012 P4)
- **EXIT RISK (Close < MA50) is the only consistently bearish state**: -0.23% to -0.82% 30D avg across rank buckets
- **EXIT + Top 10 = HOLD**: +1.70% 30D (53% WR) — EXIT is NOT a sell signal even in context
- **EXIT + Rank >20 = HOLD (caution)**: +0.85% 30D (46.9% WR) — not negative enough for SELL
- **WEAKENING + Rank 11-20** is worst cell: -1.39% 30D (41.3% WR)
- Hypothesized rules (EXIT→SELL, EXIT→TRIM) all invalidated by data
- Decision layer signal: only EXIT RISK warrants REVIEW; no cell justifies SELL

### Turnaround Promotion (RESEARCH-012 P5)
- **Turnaround replacement beats holding**: 1M diff +6.95% (68.5% WR), avg across horizons +7.39%
- Strongest edge is short-term (1M): weak stocks continue declining (-1.65%) while Turnaround bounces (+5.31%)
- Edge decays over time: 6M win rate 49.3% — best used as immediate tactical replacement
- 78 events across 2022-2025: actionable when EXIT state holding + Full Match Turnaround coexist

### Production Gate — Decision Layer V1 Assessment
**GATE-001 RESULT: FAILED** — Decision Layer V1 rejected.
- Event-level improvements (P2 rank-drop, P3 replacement, P5 Turnaround overlay) do NOT translate to portfolio-level outperformance
- Config B monthly rebalance captures leadership rotation more efficiently than any decision overlay
- Additional overlays create friction: turnover, timing lag, inappropriate replacements reduce CAGR
- Config B remains sole production engine. Exit Layer monitoring-only. Turnaround watchlist-only.
- **RESEARCH-012 closed.** Do not re-open without new evidence.

### Proven Research Conclusions (RESEARCH-012)
- **EXIT is not a sell signal** — EXIT stocks outperform Healthy at 90D (+2.16%, p=0.04)
- **Rank deterioration identifies weakening stocks** — Drop > 10 from entry rank is a valid sell signal (25.58% CAGR standalone)
- **Replacement improves individual events** — Event-level: +4.76% CAGR, +10.07% avg excess, 70% WR at 6M
- **Turnaround replacement improves individual events** — 1M diff +6.95%, 68.5% WR
- **Portfolio-level overlays reduce returns vs Config B** — Integrated Decision Layer fails to beat Config B
- **Config B is the strongest validated production strategy** — 46.33% CAGR (2022-2025), 1.43 Sharpe, 49.03% Alpha

### Rank Deterioration (RESEARCH-012 P2)
- **Rank collapse > 10** is a strong sell signal: 25.58% CAGR (vs 19.45% baseline), 0.76 Sharpe, 16.61% Alpha, -20.2% MaxDD, 4.6% turnover
- **Absolute rank thresholds** (Exit Top 5/10/20) are NOT useful sell signals — all underperform baseline
- **"Loss of leadership"** is the signal, not current rank: stock falling >10 positions from entry rank represents meaningful deterioration
- Drop > 5 ranks also beats baseline (23.31% CAGR) but higher turnover (8.3%)
- Drop > 15 ranks underperforms (13.62% CAGR) — too loose, catches false positives

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
| Decision Layer on Config B (R012) | FAILED | Integrated DL (V1/V2) underperforms Config B — event-level gains do not survive portfolio integration |

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
11. **Dashboard enhancements must be append-only** — Insight Layer V1 introduced TDZ crash (PF before init) and table disappearance by modifying render order. All future dashboard work must: (a) insert new DOM elements only, never modify existing ones, (b) place new JS IIFEs after all data constants, (c) preserve core interactivity (ticker click, help, panel) as highest priority.
12. **const declarations create Temporal Dead Zone** — `typeof` guard does NOT prevent ReferenceError for `const`. Variables in TDZ throw on ANY reference. Place all consumers after declarations or use `var` for cross-IIFE data.

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
│   ├── Tab 01: Leaders            Config B ranking with color-coded alignment + Insight panels
│   ├── Tab 02: Turnaround         Context/Transition signals + Turnaround analysis
│   ├── Tab 03: Daily Summary      Signal diagnostics + top candidates
│   ├── Tab 04: History            Streak tracking
│   ├── Tab 05: Diagnostics        Pipeline health
│   ├── Tab 06: Exit Monitor       Rule-based exit states with legend + Exit analysis
│   └── Kesimpulan Hari Ini       Narrative analysis (Leaders, Turnaround, Exit) above tabs
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
| Portfolio Simulator | `data/state/portfolio_simulator.json` | Manual entry |
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
6. **RESEARCH-012: Portfolio Decision Layer** — CLOSED. Integrated Decision Layer FAILS to outperform Config B. Event-level gains do not survive portfolio integration.
7. **RESEARCH-013: Config B Robustness Validation** — Is 46.33% CAGR (2022-2025) robust? Survivorship bias? Universe bias? Regime dependence? See next research priority.

---

## 11. BACKLOG

### ✓ Completed
- [x] Repository Phase 1 — Documentation consolidation & archival
- [x] Repository Phase 2 — Root directory simplification
- [x] AUDIT-001 — Data quality audit (PBV fix, DY fix)
- [x] AUDIT-002 — Yahoo PBV field verification
- [x] DATA_QUALITY_RULE_PBV_V1 — Formalized and deployed
- [x] FEATURE-001 — My Portfolio monitoring module (06 · My Portfolio tab)
- [x] FEATURE-002 — Portfolio Simulator separation + AI Analysis restoration
- [x] KESIMPULAN HARI INI panel restoration (regression from FEATURE-001)
- [x] IMPLEMENT-003 — Dashboard regression recovery (Insight Layer V1 TDZ crash, append-only mandate, ENGINEERING RULE-005)
- [x] RESEARCH-012: Portfolio Decision Layer — CLOSED FAILED (event-level gains do not survive portfolio integration)

### BACKLOG TEKNIS
- [ ] Monthly archive restoration — update `research/tools/` to read from `docs/archive/`
- [ ] Dashboard maintenance — AMMN revenue_growth display cap, cosmetic issues
- [ ] Data quality monitoring — automated flag review at monthly pipeline
- [ ] Automated daily exit watchlist execution (paper trading)
- [ ] Sector exposure monitoring for Config B portfolio
- [ ] Gemini AI narrative to paid tier (if quota critical)

### ANTRIAN RISET
- [ ] RESEARCH-013: Config B Robustness Validation — Is 46.33% CAGR robust? Check: survivorship bias, universe bias, concentration, regime dependence
- [ ] Build Historical Factor Warehouse V2 (2021-present factor scores)
- [ ] Re-run OOS weight validation with real factor data
- [ ] Config B vs Config F comparison on real historical data
- [ ] Turnaround-Config B blended portfolio correlation study
- [ ] RESEARCH-012: Portfolio Decision Layer -- CLOSED -- FAILED (see section 3)
