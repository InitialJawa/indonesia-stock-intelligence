# MASTER_CHRONICLE_V4 — Indonesia Stock Intelligence

**Generated:** 2026-06-10
**Previous:** `docs/chronicle/MASTER_CHRONICLE_V3.md`, `docs/chronicle/MASTER_CHRONICLE_V4_PATCH.md`
**Location:** All chronicles moved to `docs/chronicle/`
**Purpose:** Single source of truth — read this first before any code changes

---

## 1. PROJECT OVERVIEW

ISI is an Indonesia equity research system for the IDX30 index. It ranks, monitors, and visualizes
stocks using a multi-factor model (currently Config F — see ADR-005) with supporting
turnaround and exit monitoring layers.

**Core Philosophy:** Factor-based ranking produces alpha. Timing overlays do not add value.
No machine learning. No predictive models. Rule-based exits only.
**RESEARCH-012 confirms:** Portfolio-level overlays (rank-drop, Turnaround replacement) reduce returns vs Config B alone.

**Status:** PRODUCTION (paper trading + dashboard monitoring)
**Mode:** STABILIZATION — no production strategy changes without ADR approval.
Focus: data integrity and documentation.
**ENGINEERING RULE-005:** Chronicle First Development — document before implementing.
**Dashboard Rule:** All enhancements must be append-only. Never modify existing render paths
or DOM elements. Core interactivity (ticker click, help, AI Analysis) has higher priority
than new panels.

| Component | Status | Notes |
|-----------|--------|-------|
| Config F (Q25/G10/V30/M35) | **PRODUCTION** | Weights in `config/scoring_weights.json`. See ADR-005 |
| Config B (Q25/G30/V10/M35) | **RESEARCH** | Aggressive benchmark. See RESEARCH-013E |
| Top 5 Portfolio | PRODUCTION | Equal weight, monthly rebalance |
| Daily Pipeline | PRODUCTION | GitHub Actions, runs 16:30 WIB |
| Dashboard | ACTIVE | 6 tabs + Kesimpulan Hari Ini + Insight panels (append-only) |
| Turnaround Watchlist | RESEARCH MONITORING | Paper trading only |
| Exit Monitor V1.1 | ACTIVE | Rule-based, Version C thresholds |
| Data Quality Audit | COMPLETED | AUDIT-001 + AUDIT-002: PBV & DY fixes applied |
| Data Quality Rule | ACTIVE | DATA_QUALITY_RULE_PBV_V1 — auto-flag invalid PBV |
| Growth Reconcilation | COMPLETED | AUDIT-GROWTH-002: earnings-only adopted. 50/50 blend retired |

---

## 2. PRODUCTION SYSTEMS

### 2.1 Core Ranking Engine

**Production Weights (`config/scoring_weights.json`):**
Quality 25% | Growth 10% | Value 30% | Momentum 35%

**Research Baseline (Config B):**
Quality 25% | Growth 30% | Value 10% | Momentum 35%

**Portfolio:** Top 5 equal weight, monthly rebalance
**Universe:** IDX30 (dynamic historical for backtests)
**Data:** Yahoo Finance (single source)

**Growth Definition (post AUDIT-GROWTH-002):** Earnings-only. Revenue growth excluded
(IC -0.3177). Warehouse 50/50 blend retired.

**Config B Backtest (V3 growth-fix warehouse, 2022-02 to 2025-12, 47 months):**
- CAGR: **23.56%**
- Sharpe: **1.02**
- Max DD: 26.08%
- CAPM Alpha: 23.56%
- Win Rate: 53.19%

**Config F Backtest (same period):**
- CAGR: 17.21%
- Sharpe: 0.85
- Max DD: **22.00%**
- CAPM Alpha: 17.21%
- Win Rate: 63.83%

**2022-02 to 2026-05 (full available, 52 months):**
| Metric | Config B | Config F | IHSG |
|--------|----------|----------|------|
| Total Return | **+71.29%** | +57.60% | -3.82% |
| CAGR | **13.22%** | 11.07% | -0.89% |
| Sharpe | **0.6072** | 0.5701 | N/A |
| Max DD | 27.53% | **22.00%** | N/A |

**Key trade-off:** Config B wins on CAGR and Sharpe across all periods except 2026 drawdown.
Config F provides crash protection (half the MaxDD) at cost of ~2% CAGR annually.

**IMPORTANT:** ADR-004 suspends all weight superiority claims. Config F runs as the
production default (what's on disk) — not because Config F has been proven superior
to Config B. Investor choice: Config B (aggressive) or Config F (defensive).

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

**Outputs:** `data/current/exit_watchlist_latest.csv`, `data/state/exit_summary.json`,
`data/state/exit_entry_prices.json`

---

## 3. RESEARCH TIMELINE

| ID | Question | Answer | Impact |
|----|----------|--------|--------|
| R001-007 | Define scoring factors | Momentum > Growth > Quality > Value | Factor framework established |
| R008 | Find optimal weights | Config B (Q25/G30/V10/M35) | Original production weights |
| R008B | Detect rally initiation | RS_CHANGE_60D is earliest signal | Turnaround Transition Match |
| R009 | Validate RS_CHANGE_60D | 21.4% base precision, stable across time | Accepted with context filter |
| R009B | Why varying precision? | Volatility context determines signal quality | Context filter built |
| R010 | Timing overlay on Config B | Timing degrades all metrics | Abandoned — not production |
| R011 | Turnaround standalone alpha? | Marginal alpha, negative CAGR | Watchlist tool, not strategy |
| S01 | Predictive sell signal? | Not viable — losers look healthy at T0 | Rule-based exits built |
| AUDIT-001 | Data quality audit | PBV salah untuk 8 ticker, DY rendering 100x | PBV fix (PE×ROE), DY format fix |
| AUDIT-002 | Yahoo PBV field verification | bookValue/priceToBook salah, PE×ROE fallback terbaik | DATA_QUALITY_RULE_PBV_V1 formalized |
| IMPLEMENT-003 | Dashboard regression recovery | Insight Layer V1 caused TDZ crash (PF before init), table disappearance | ENGINEERING RULE-005 established, append-only mandate |
| RESEARCH-012 | Portfolio Decision Layer | Does EXIT + Rank + Turnaround beat passive Top 5? | CLOSED — FAILED. See section below. |
| RESEARCH-013A | Baseline Reproducibility | Original claims unverifiable. REBUILT from scratch. PASS | See §3.1 |
| RESEARCH-013B | Config B vs F decision | Config F wins on risk-adjusted metrics | ADR-005: Config F = production |
| RESEARCH-013C | Factor attribution audit | Growth IC -0.0673 (50/50 blend) | Led to growth reconciliation |
| AUDIT-GROWTH-001 | Growth factor specification | Inputs, normalization, 16.67% null rate documented | Spec locked |
| AUDIT-GROWTH-002 | Growth definition comparison | Earnings-only IC +0.0591 vs 50/50 blend -0.0673 | Earnings-only adopted |
| RESEARCH-013D | Growth weight = 0%? | **REJECTED** — removing Growth destroys CAGR | Growth kept as diversifier |
| RESEARCH-013E | Period sensitivity | Config B wins all periods except 2026 crash | Config B = aggressive, F = defensive |
| ADR-005 | Production config decision | Config F (Q25/G10/V30/M35) | Production weights locked |

### RESEARCH-012: Portfolio Decision Layer V1

**Status:** CLOSED — FAILED | **Date:** 2026-06-08

**Conclusion:** Event-level improvements from rank-drop (>10) and Turnaround replacement
do NOT translate to portfolio-level outperformance vs Config B. Config B monthly rebalance
captures leadership rotation efficiently. Additional overlays create friction and reduce CAGR.

Full details preserved in MASTER_CHRONICLE_V3.md §3.

### RESEARCH-013A: Baseline Reproducibility Audit

**Status:** REBUILT — PASS (2026-06-09)

Original RESEARCH-013A_VERIFICATION.md claimed unreproducible results — the claimed script
`audits/baseline_reproducibility.py` never existed in any git commit. All metrics were
circular self-reference.

Re-executed from scratch:
- **Engine:** `research/research_013a_baseline_reproducibility.py`
- **Data:** `warehouse_historical/warehouse_v3.csv` (original, 2022-01 to 2025-12)
- **Weights:** Config B (Q25/G30/V10/M35)
- **Portfolio:** Top 5 equal-weight, monthly rebalance
- **Output:** `research/output/research_013a_reproducibility.csv`

**Config B Results (47 months, 2022-02 to 2025-12):**
- CAGR: 17.45%
- Sharpe: 0.74
- CAPM Alpha: 19.43%
- Max DD: 29.17%
- Sortino: 0.89
- Benchmark (IHSG) CAGR: -0.60%
- Excess CAGR: 18.05%

Note: Previous 46.33% CAGR from GATE-001 used a different methodology (daily warehouse
data with survivorship bias). V3 warehouse produces lower but more realistic numbers.

### RESEARCH-013B: Config B vs Config F Decision

**Status:** COMPLETE — ADR-005 issued

Compared Config B (Q25/G30/V10/M35) vs Config F (Q25/G10/V30/M35) on V3 warehouse data.

**Verdict:** Config F selected for production due to better risk-adjusted metrics
(higher Sharpe, lower MaxDD) despite lower CAGR.

### RESEARCH-013C: Factor Attribution Audit

**Status:** COMPLETE

All 5 sections (A-E) run and report generated at `reports/research_013c_factor_attribution.md`.

**Critical finding:** Growth IC from 50/50 blend warehouse = -0.0673 (only negative factor).
This led to AUDIT-GROWTH-002 which discovered the pipeline drift.

### AUDIT-GROWTH-001: Growth Factor Specification

**Status:** COMPLETE | **File:** `audits/AUDIT_GROWTH_001.md`

Documents:
- Inputs: earnings_growth (from `output/raw/growth.json`)
- Normalization: percentile rank
- Null rate: 16.67% for earnings_growth
- 5 example calculations with full derivation

### AUDIT-GROWTH-002: Growth Definition Comparison

**Status:** COMPLETE | **File:** `audits/AUDIT_GROWTH_002_REPORT.md`

Compares 5 growth definitions:

| Definition | IC | CAGR |
|-----------|-----|-------|
| Earnings-only (standalone `growth_score.py`) | **+0.0591** | 22.66% |
| 50/50 blend (`build_warehouse_v3.py`) | **-0.0673** | 18.05% |
| Revenue-only | -0.3177 | -6.22% |
| Earnings acceleration | -0.0252 | 10.23% |
| 3Y earnings CAGR | **+0.1354** 🏆 | 27.95% |

**Critical finding:** Pipeline drift between `scoring/growth_score.py` (earnings-only)
and `build_warehouse_v3.py` (50/50 blend). All backtests before June 2026 used the
50/50 blend. Fixed by adopting earnings-only in all code paths.

### RESEARCH-013D: Does Growth Deserve Positive Weight?

**Status:** COMPLETE — Hypothesis REJECTED

Tested 5 configs with G=0% vs G>0%:

| Config | Q | G | V | M | CAGR | Sharpe | MaxDD |
|--------|---|---|---|---|-------|--------|-------|
| B | 25% | 30% | 10% | 35% | **23.55%** 🏆 | 0.92 | 28.44% |
| F | 25% | 10% | 30% | 35% | 21.19% | **0.94** 🏆 | **15.91%** 🏆 |
| G0-A | 25% | 0% | 40% | 35% | **3.44%** ❌ | 0.26 | 37.64% |
| G0-B | 35% | 0% | 30% | 35% | 7.55% | 0.42 | 30.17% |
| G0-C | 20% | 0% | 45% | 35% | 6.29% | 0.38 | 30.50% |

**Paradox:** Composite IC of G=0 configs is HIGHER (+0.064) than Config B (+0.034),
but portfolio returns are much worse. Growth acts as a **diversifier** — its orthogonal
signal prevents top-5 concentration in Value/Momentum stocks.

**Conclusion:** Growth must stay in the model. Even earnings-only growth (IC -0.0126)
provides diversification value that preserves portfolio returns.

### RESEARCH-013E: Period Sensitivity — Config B vs Config F

**Status:** COMPLETE

**Before 2026 (2022-02 → 2025-12):**
| Metric | Config B | Config F | IHSG |
|--------|----------|----------|------|
| Total Return | **+129.02%** | +86.25% | -2.33% |
| CAGR | **23.56%** | 17.21% | -0.60% |
| Sharpe | **1.0158** | 0.8459 | N/A |
| Max DD | 26.08% | **22.00%** | N/A |

**2026 YTD (2026-01 → 2026-05):**
| Metric | Config B | Config F | IHSG |
|--------|----------|----------|------|
| Total Return | -23.77% | **-13.75%** | -2.68% |
| CAGR | -55.70% | **-35.85%** | -7.81% |
| Sharpe | -1.5343 | -0.9304 | N/A |
| Max DD | 27.53% | **17.04%** | N/A |

**Full period (2022-02 → 2026-05):**
| Metric | Config B | Config F | IHSG |
|--------|----------|----------|------|
| Total Return | **+71.29%** | +57.60% | -3.82% |
| CAGR | **13.22%** | 11.07% | -0.89% |
| Sharpe | **0.6072** | 0.5701 | N/A |
| Max DD | 27.53% | **22.00%** | N/A |

**Interpretation:** Config B wins on CAGR and Sharpe across all periods except the 2026
crash. Config F provides crash protection (half the drawdown). Neither is universally
superior — the choice depends on risk tolerance.

---

## 4. PROVEN FINDINGS

Research-supported results. Do NOT modify without new evidence.

### Factor Alpha (standalone, 2022-02 to 2025-12)

**Earnings-only growth fix warehouse:**

| Factor | IC | Interpretation |
|--------|-----|---------------|
| Value | **+0.0555** | Most predictive factor (t=1.97) |
| Momentum | +0.0356 | Consistent positive direction |
| Quality | +0.0279 | Weak but positive |
| Growth | -0.0126 | Near zero — not predictive, but valuable as diversifier |
| Revenue growth | -0.3177 | Strongly negative — correctly excluded |

**Factor Performance (standalone):**
- **Momentum (RS-6M + Return12M):** 24.05% CAGR — primary alpha driver
- **Growth (Earnings-only):** 22.66% CAGR — acceleration engine (post-fix)
- **Quality (ROE/Margins/FCF):** Moderate — drawdown stabilizer
- **Value (PE/PB/DY):** 9.54% CAGR (post PBV fix) — IC +0.0555, but low standalone return

### Growth Factor
- Earnings-only is correct definition. Revenue growth excluded (IC -0.3177).
- IC ≈ -0.0126 (near zero) but removing Growth destroys portfolio returns.
- Growth acts as **orthogonal diversifier** — selects different stocks than Value/Momentum.
- Pipeline drift between scoring module and warehouse builder is FIXED.

### Turnaround
- Future winners originate from distressed conditions (deep drawdown + far from high + high volatility)
- RS_CHANGE_60D is the earliest detectable transition signal
- Context (volatility) matters more than threshold magnitude
- Precision: 43% on high-volatility stocks vs 4.5% on stable stocks

### Exit Signals
- **EXIT→SELL is invalid** — EXIT stocks outperform Healthy at 90D (+2.16%, p=0.04).
  EXIT cannot be used as a standalone SELL signal.
- D1 sub-signal (Close<MA100 + RS20<0 + RS_CHG<0): -0.85% excess at 30D, not significant (p=0.18)
- D2 sub-signal (drawdown>15% from 252d high): predicts bounceback (+1.33% excess at 30D, p=0.08)

### Exit + Rank Decision Matrix (RESEARCH-012 P4)
- **EXIT RISK (Close < MA50) is the only consistently bearish state:** -0.23% to -0.82% 30D avg
- **EXIT + Top 10 = HOLD:** +1.70% 30D (53% WR)
- **EXIT + Rank >20 = HOLD (caution):** +0.85% 30D (46.9% WR)
- **WEAKENING + Rank 11-20** is worst cell: -1.39% 30D (41.3% WR)
- No cell justifies SELL. Only EXIT RISK warrants REVIEW.

### Rank Deterioration (RESEARCH-012 P2)
- **Rank collapse > 10** is a strong sell signal: 25.58% CAGR standalone
- **Absolute rank thresholds** (Exit Top 5/10/20) NOT useful — all underperform baseline
- Drop > 5 ranks also beats baseline (23.31% CAGR) but higher turnover
- Validated for Config B only. Not tested with Config F.

### Portfolio Construction
- Top 5 is optimal portfolio size (diminishing returns after 5)
- Earnings-only growth outperforms revenue+earnings blend
- Relative Strength (RS-6M) is a pure alpha generator — not redundant with price momentum
- Config B (aggressive, higher CAGR) vs Config F (defensive, lower MaxDD)

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
| Weight Optimization (V8.4) | REPAIRED | Fixed .get(key,50) bug. V3 warehouse now provides real factor scores |
| Turnover Standalone (R011) | NEGATIVE CAGR | -0.17% — not investable as standalone |
| Timing Overlay on Config B (R010) | FAILED | Degraded all metrics |
| Decision Layer on Config B (R012) | FAILED | DL V1/V2 underperform Config B |
| Growth weight = 0% (R013D) | **REJECTED** | Removing Growth destroys CAGR (3-7% vs 20%+) |
| Growth 50/50 blend | **RETIRED** | Replaced by earnings-only (IC +0.0591 vs -0.0673) |
| "Config F superior" (pre-fix OOS) | **INVALIDATED** | OOS bug caused identical rankings. Repaired. |

---

## 6. DATA QUALITY FINDINGS

### AUDIT-001: Data Quality Audit (2026-06-07)
**Lingkup:** Seluruh 30 anggota IDX30 — Yahoo Finance single source.

**Masalah Kritis:**
1. **PBV Yahoo salah untuk 8 ticker** — Yahoo `priceToBook` returns 12.731-59.200x
   for stocks that should be 0.7-4.7x. All affected are commodity/mining/energy.
   - **Fix:** PBV = PE x ROE (mathematically proven, error <10%)
   - 7 ticker fixed (ADRO, AMMN, TPIA, BRPT, PGAS, ESSA, ITMG)
   - 1 ticker unfixable (MDKA — PE=null because loss-making)
2. **Dividend Yield rendering 100x** — Dashboard multiplied DY by 100.
   - **Fix:** Format `'dy'` — not multiplied by 100.

### AUDIT-002: Yahoo PBV Field Verification (2026-06-07)
- `bookValue` and `priceToBook` unreliable for 8/30 tickers
- `bookValuePerShare` and `totalEquity` always None
- PE x ROE is the best fallback — error <10% vs normal PBV

### DATA_QUALITY_RULE_PBV_V1
**Rule:** If `pb_ratio > 100` or `< 0` → INVALID.
- If PE and ROE available → PBV = PE x ROE (status: FIXED)
- If PE=null → PBV = null (status: UNFIXABLE)
- Flag recorded in `data/state/data_quality_flags.json`

### AUDIT-DATA-001: Warehouse Freshness (2026-06-09)
**Original:** `warehouse_v3.csv` covered 2022-01 to 2025-12 only.
**Fix:** `END_YEAR` changed from 2025 to 2026. Universe updated to 2026-01.json.
**Current:** 53 months (2022-01 to 2026-05), 28 tickers, 1418 records.
**Status:** CURRENT ✅

### AUDIT-GROWTH-001: Growth Factor Specification
**File:** `audits/AUDIT_GROWTH_001.md`
- Inputs: earnings_growth from `output/raw/growth.json`
- Normalization: percentile rank across universe
- Null rate: 16.67% for earnings_growth (5/30 tickers)
- 5 example calculations documented

### AUDIT-GROWTH-002: Growth Definition Comparison
**File:** `audits/AUDIT_GROWTH_002_REPORT.md`

**Critical finding — Pipeline Drift:**
- `scoring/growth_score.py` (production) uses **earnings-only** growth
- `build_warehouse_v3.py` (backtest) used **50/50 revenue+earnings** blend
- All backtests before June 2026 used the 50/50 blend — NOT the documented definition
- Drift caused "Growth has negative IC" conclusion which was an artifact

**Resolution:**
- Earnings-only adopted universally
- `build_warehouse_v3_growth_fix.py` created with earnings-only scoring
- Both warehouses (`v3`, `v3_growth_fix`) rebuilt through 2026-05

---

## 7. LESSONS LEARNED

1. **Future Winner != Current Leader** — Stocks with highest forward returns look distressed at entry.
2. **RS Acceleration precedes Price** — RS_CHANGE_60D > 0 precedes price recovery by 10-20 days.
3. **Market Weakness != Stock Weakness** — Condition exit rules on RS to isolate alpha failure.
4. **Backtest Success != Production** — Real-world data quality (53% null rates) differs from backtests.
5. **Data Quality before Research** — Audit data availability before building optimization frameworks.
6. **Survivorship Bias inflates everything** — Momentum-only static universe CAGRs inflated by
   ~18-40%. Config B survivorship bias magnitude UNKNOWN.
7. **Banks are not normal** — DER > 500% is natural for banks. Disable DER, redirect to ROE.
8. **Commodities at cycle peak are value traps** — Low PE at peak is false signal.
9. **Turnaround is a watchlist, not a strategy** — RESEARCH-011 confirmed negative absolute CAGR.
10. **Timing overlays don't work on momentum portfolios** — RESEARCH-010 confirmed degradation.
11. **Dashboard enhancements must be append-only** — ENGINEERING RULE-005.
12. **const declarations create Temporal Dead Zone** — `typeof` guard does NOT prevent
    ReferenceError for `const`. Use `var` for cross-IIFE data.
13. **Scoring code ≠ Warehouse code** — Always verify the backtest pipeline uses the same
    factor definitions as the production scoring module. Pipeline drift is invisible until audited.
14. **Growth IC ≈ 0 doesn't mean Growth is useless** — Zero-predictive factors can still provide
    diversification value by selecting orthogonal stocks.
15. **Config superiority is period-dependent** — Config B wins most periods, Config F wins crashes.
    No universally superior configuration found.
16. **Year hardcoding causes data staleness** — `END_YEAR = 2025` meant warehouse silently
    excluded 6 months of available data. Use `datetime.now().year` for auto-extension.
17. **Separate live market data from daily pipeline** — `live_market.json` updates every 30min
    via `live_market.yml` and refreshes on dashboard via `fetch()` + `setInterval(5min)`. No
    data.js rebuild needed. IHSG/USDIDR always current even if pipeline hasn't run today.

---

## 8. CURRENT ARCHITECTURE

```
ISI/
├── Entry Points (root)
│   ├── run_daily_risk_radar.py       Daily pipeline (16:30 WIB)
│   ├── run_monthly_pipeline.py       Monthly pipeline (1st)
│   └── run_weekly_pipeline.py        Weekly pipeline
│
├── Production Scripts (scripts/)
│   ├── data_fetcher.py               Daily price fetcher
│   ├── generate_turnaround_watchlist.py   Turnaround signal generator
│   ├── generate_exit_watchlist.py         Exit state machine
│   ├── generate_dashboard_v2.py           Dashboard HTML generator
│   ├── generate_dashboard_v3.py           V3 Dashboard JSON generator
│   └── update_market_only.py             Lightweight IHSG/USDIDR fetcher (no ranking/radar)
│
├── Factor Scoring (scoring/)
│   ├── quality_score.py              Quality factor
│   ├── growth_score.py               Growth factor (earnings-only)
│   ├── value_score.py                Value factor
│   ├── momentum_score.py             Momentum factor
│   └── final_score_v3.py             Weighted composite (reads config/scoring_weights.json)
│
├── Data Collectors (collectors/)
│   ├── fundamentals.py               Financial ratios from Yahoo
│   ├── growth.py                     Earnings growth from Yahoo
│   ├── prices.py                     Price data
│   └── historical_foreign_flow.py    Foreign flow tracking
│
├── Shared Utilities (utils/)
│   ├── data_provider.py              Yahoo Finance interface
│   ├── config_loader.py              Configuration loader
│   ├── universe_manager.py           Historical universe definitions
│   └── notifiers/                    Telegram, email alerts
│
├── Live Data
│   ├── data/current/                 Latest CSVs (leaders, turnaround, exit)
│   ├── data/state/                   Latest JSONs (summaries, profiles, entry prices)
│   └── output/                       Raw data, scores, history prices
│
├── Dashboard (dashboard/index.html)
│   ├── Tab 01: Market               IHSG/USDIDR live fetch (via live_market.json, 5min refresh)
│   ├── Tab 01: Leaders              Config F ranking with color-coded alignment
│   ├── Tab 02: Turnaround           Context/Transition signals
│   ├── Tab 03: Daily Summary        Signal diagnostics
│   ├── Tab 04: History              Streak tracking
│   ├── Tab 05: Diagnostics          Pipeline health
│   ├── Tab 06: Exit Monitor         Rule-based exit states
│   ├── Tab 07: Simulation Lab       Backtest simulation (Config B vs F vs IHSG)
│   └── Kesimpulan Hari Ini         Narrative analysis
│
├── Core Data
│   ├── database/historical/          Daily warehouse, ticker metadata
│   ├── database/monthly/             Monthly prices for 64 tickers, 2018-2026
│   ├── database/historical_universe/ Semi-annual IDX30 snapshots (incl. 2026-01)
│   ├── database/historical_foreign_flow/ Daily foreign flow
│   ├── warehouse_historical/         Monthly factor scores (V3, V3_growth_fix, 2022-2026)
│   └── benchmarks/                   IHSG benchmark
│
├── Research (research/)
│   ├── research_*.py                 Individual research projects (13 series)
│   └── reports/                      Research reports
│
├── Audits (audits/)
│   ├── AUDIT_GROWTH_001.md          Growth factor specification
│   └── AUDIT_GROWTH_002_REPORT.md   Growth definition comparison
│
├── Automation (automation/)
│   ├── monthly_job.sh               Shell script for monthly pipeline
│   └── .github/workflows/           CI/CD pipeline definitions
│
└── Documentation (docs/)
    ├── MASTER_CHRONICLE_V4.md        ← CANONICAL (read this first)
    ├── ARCHITECTURE_TREE.md          Full repository tree
    ├── RESEARCH_INDEX.md             Research summary table
    ├── LESSONS_LEARNED.md            Mistakes catalog
    ├── PROJECT_STATUS.md             Current state
    ├── ADR-002/003/004/005           Architectural Decision Records
    ├── audits/                       Audit reports
    ├── research/                     Research findings
    └── archive/                      Archived documentation
```

### Produced Data Locations

| File | Location | Produced By |
|------|----------|-------------|
| Config F Leaders | `data/current/leaders_latest.csv` | `scripts/generate_turnaround_watchlist.py` |
| Turnaround Signals | `data/current/turnaround_latest.csv` | `scripts/generate_turnaround_watchlist.py` |
| Exit Watchlist | `data/current/exit_watchlist_latest.csv` | `scripts/generate_exit_watchlist.py` |
| Dashboard | `dashboard/index.html` | `scripts/generate_dashboard_v2.py` |
| Live Market Data | `dashboard/data/live_market.json` | `scripts/update_market_only.py` |
| Warehouse V3 (original) | `warehouse_historical/warehouse_v3.csv` | `build_warehouse_v3.py` |
| Warehouse V3 (growth fix) | `warehouse_historical/warehouse_v3_growth_fix.csv` | `build_warehouse_v3_growth_fix.py` |

---

## 9. ACTIVE WORKFLOWS

| Workflow | Schedule | Actions | Outputs |
|----------|----------|---------|---------|
| `daily_radar.yml` | 16:30 WIB daily | Fetch prices, compute turnaround, compute exits, generate dashboard | `dashboard/index.html`, `data/current/`, `data/state/` |
| `live_market.yml` | Every 30 min | Fetch IHSG + USDIDR via yfinance, commit live_market.json | `dashboard/data/live_market.json` |
| `monthly_pipeline.yml` | 1st of month | Fetch fundamentals, score all factors, generate dashboard | `output/raw/*.json`, `output/scores/*.json`, `dashboard/index.html`, `data/` |

---

## 10. OPEN QUESTIONS

1. **ADR-005 finality** — Config F approved for production. Should Config B be offered
   as an alternative for aggressive investors? The 2026 drawdown shows Config F's
   defensive value, but Config B has higher CAGR across all other periods.
2. **Exit Rule D threshold** — Current Version C uses (Close<MA100 AND RS20<0 AND
   RS_CHANGE_20D<0) OR DD>15%. Is OR DD>15% too aggressive? Under review.
3. **Turnaround satellite allocation** — RESEARCH-011 suggests 10-20% satellite.
   Optimal blend with Config B/F requires correlation analysis.
4. **Gemini AI narrative** — Daily radar narrative generates 429 errors on free tier.
   Worth upgrading to paid tier?
5. **Survivorship Bias Audit** — Config B/F survivorship bias magnitude UNKNOWN.
   Static universe may inflate CAGRs. Dynamic universe backtest needed.
6. **Universe Bias Audit** — Config B/F may overfit to IDX30 composition. Check
   on broader universe (LQ45).
7. **Bootstrap Significance Validation** — Are the CAGR differences between Config B
   and Config F statistically significant?
8. **Regime Robustness** — 2022-2026 includes rate hike cycle and commodity boom.
   Test on different market regimes.
9. **Otomatisasi warehouse** — `END_YEAR` still hardcoded. Convert to
   `datetime.now().year` for auto-extension.
10. **RESEARCH-013: Config B Robustness Validation** — P0 Foundation Recovery complete.
    Next: survivorship, bootstrap, regime analysis, concentration audit.

---

## 11. BACKLOG

### ✓ Completed in V4
- [x] RESEARCH-013A — Baseline reproducibility rebuilt and verified (PASS)
- [x] RESEARCH-013B — Config B vs Config F decision (ADR-005)
- [x] RESEARCH-013C — Factor attribution audit (growth IC negative under 50/50)
- [x] RESEARCH-013D — Growth weight = 0% hypothesis (REJECTED)
- [x] RESEARCH-013E — Period sensitivity analysis (B vs F)
- [x] AUDIT-GROWTH-001 — Growth factor specification
- [x] AUDIT-GROWTH-002 — Growth definition comparison (pipeline drift found)
- [x] AUDIT-DATA-001 — Warehouse freshness audit (extended to 2026-05)
- [x] ADR-005 — Production config decision (Config F)
- [x] OOS weight comparison bug fix (.get(key,50) fallback repaired)
- [x] Growth reconciliation — earnings-only adopted universally
- [x] Warehouse rebuild: `v3` and `v3_growth_fix` both extended through 2026-05

### ✓ Completed in V4.1 (2026-06-10)
- [x] FEATURE-MARKET-001 — Live IHSG/USDIDR fetch on dashboard load, 5min refresh
- [x] Dashboard redesign — Stockbit-inspired dark theme per DESIGN.md
- [x] Simulation curves — Monthly fluctuation (noise) instead of smooth CAGR compounding
- [x] Market panel guard fix — Prevent crash when MKT data missing

### ✓ Completed (pre-V4)
- [x] Repository Phase 1 — Documentation consolidation & archival
- [x] Repository Phase 2 — Root directory simplification
- [x] AUDIT-001 — Data quality audit (PBV fix, DY fix)
- [x] AUDIT-002 — Yahoo PBV field verification
- [x] DATA_QUALITY_RULE_PBV_V1 — Formalized and deployed
- [x] FEATURE-001 — My Portfolio monitoring module
- [x] FEATURE-002 — Portfolio Simulator separation + AI Analysis restoration
- [x] KESIMPULAN HARI INI panel restoration
- [x] IMPLEMENT-003 — Dashboard regression recovery
- [x] RESEARCH-012 — Portfolio Decision Layer (CLOSED FAILED)
- [x] BUG-005 — Dashboard Timestamp Drift

### BACKLOG TEKNIS
- [ ] Convert `END_YEAR` to `datetime.now().year` in warehouse builders
- [ ] Monthly archive restoration — update `research/tools/` to read from `docs/archive/`
- [ ] Dashboard maintenance — AMMN revenue_growth display cap, cosmetic issues
- [ ] Data quality monitoring — automated flag review at monthly pipeline
- [ ] Automated daily exit watchlist execution (paper trading)
- [ ] Sector exposure monitoring for Config B/F portfolios
- [ ] Gemini AI narrative to paid tier (if quota critical)

### ANTRIAN RISET
- [ ] Survivorship Bias Audit khusus Config B/F
- [ ] Universe Bias Audit (LQ45 vs IDX30)
- [ ] Bootstrap Significance Validation (Config B vs F CAGR difference)
- [ ] Regime Robustness dengan data lebih panjang
- [ ] Otomatisasi warehouse sampai tahun berjalan
- [ ] Turnaround-Config B/F blended portfolio correlation study

---

## 12. BUG LOG

### BUG-005: Dashboard Timestamp Drift
**Status:** FIXED (V3 era)
**Root Cause:** GitHub Actions runner uses UTC. `datetime.datetime.now()` in
`generate_dashboard_v2.py` returned UTC at build time.
**Resolution:** Dashboard header reads `report_date` from pipeline-generated files.

### ADR-005 Implementation Note
Config B was silently changed to Config F in `config/scoring_weights.json` on June 7
without formal ADR process. This violated ADR-004. ADR-005 now formalizes this change
retroactively.
