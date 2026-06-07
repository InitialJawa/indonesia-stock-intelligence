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

| Component | Status | Notes |
|-----------|--------|-------|
| Config B (Q25/G30/V10/M35) | PRODUCTION | Locked. Do not modify weights |
| Top 5 Portfolio | PRODUCTION | Equal weight, monthly rebalance |
| Daily Pipeline | PRODUCTION | GitHub Actions, runs 16:30 WIB |
| Dashboard | ACTIVE | Single dashboard, 6 tabs |
| Turnaround Watchlist | RESEARCH MONITORING | Paper trading only |
| Exit Monitor V1.1 | ACTIVE | Rule-based, Version C thresholds |

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

**Outputs:** `exit_watchlist_latest.csv`, `exit_summary.json`, `exit_entry_prices.json`

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

## 6. LESSONS LEARNED

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

## 7. CURRENT ARCHITECTURE

```
ISI/
├── Production Systems
│   ├── Config B Ranking          scoring/final_score_v3.py
│   ├── Turnaround Watchlist      generate_turnaround_watchlist.py
│   ├── Exit Monitor              generate_exit_watchlist.py
│   └── Dashboard                 generate_dashboard_v2.py -> dashboard/index.html
│
├── Data Pipeline
│   ├── Daily (16:30 WIB)         .github/workflows/daily_radar.yml
│   └── Monthly (1st)             .github/workflows/monthly_pipeline.yml
│
├── Core Data
│   ├── warehouse_daily_v4.parquet  Daily OHLCV + 44 indicators, 30 tickers, 2018-2026
│   ├── warehouse_historical/       Monthly factor scores (V3, 2022-2025)
│   ├── database/monthly/           Monthly prices for 64 tickers, 2018-2026
│   └── benchmarks/IHSG.csv         Daily IHSG benchmark
│
├── Dashboard (dashboard/index.html)
│   ├── Tab 01: Leaders            Config B ranking with color-coded alignment
│   ├── Tab 02: Turnaround         Context/Transition signals
│   ├── Tab 03: Daily Summary      Signal diagnostics + top candidates
│   ├── Tab 04: History            Streak tracking
│   ├── Tab 05: Diagnostics        Pipeline health
│   └── Tab 06: Exit Monitor       Rule-based exit states with legend
│
└── Research Archive
    └── research/                    Individual research projects (see RESEARCH_INDEX.md)
```

---

## 8. ACTIVE WORKFLOWS

| Workflow | Schedule | Actions | Outputs |
|----------|----------|---------|---------|
| `daily_radar.yml` | 16:30 WIB daily | Fetch prices, compute turnaround, compute exits, generate dashboard | dashboard/index.html, leaders/exit/turnaround CSVs |
| `monthly_pipeline.yml` | 1st of month | Fetch fundamentals, score all factors, rebalance portfolio, archive snapshots | output/raw/*.json, output/scores/*.json, warehouse/ |

---

## 9. OPEN QUESTIONS

1. **Config F vs Config B** — Config F (Q25/G10-earnings/V30/M35) shows higher CAGR in standalone tests. Should Config B be replaced? BLOCKED: requires Historical Factor Warehouse V2 for proper OOS validation.
2. **Exit Rule D threshold** — Current Version C uses (Close<MA100 AND RS20<0 AND RS_CHANGE_20D<0) OR DD>15%. Is OR DD>15% too aggressive? Under review.
3. **Turnaround satellite allocation** — RESEARCH-011 suggests 10-20% satellite. What is the optimal blend with Config B? Requires correlation analysis.
4. **Gemini AI narrative** — Daily radar narrative generates 429 errors on free tier. Worth upgrading to paid tier?
5. **Historical Factor Warehouse V2** — Full OOS weight optimization blocked. What is the minimal viable dataset?

---

## 10. FUTURE BACKLOG

- [ ] Build Historical Factor Warehouse V2 (2021-present factor scores)
- [ ] Re-run OOS weight validation with real factor data
- [ ] Config B vs Config F comparison on real historical data
- [ ] Turnaround-Config B blended portfolio correlation study
- [ ] Gemini AI narrative to paid tier (if quota critical)
- [ ] Exit Rule D threshold backtest (V1.1 vs alternatives)
- [ ] Automated daily exit watchlist execution (paper trading)
- [ ] Sector exposure monitoring for Config B portfolio
