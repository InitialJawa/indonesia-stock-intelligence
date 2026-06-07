# MASTER_CHRONICLE_V2 — Indonesia Stock Intelligence

**Generated:** 2026-06-07  
**Previous:** `master_chronicle.txt` (BAB 1–22, Indonesian language, deprecated)  
**Purpose:** Single source of truth for future AI agents

---

## SECTION 1 — EXECUTIVE SUMMARY

### Status: PRODUCTION

| Component | Status | Notes |
|-----------|--------|-------|
| Config B (Q25/G30/V10/M35) | PRODUCTION | Proven via walk-forward 2019–2026 |
| Top 5 Portfolio | PRODUCTION | Equal weight, monthly rebalance |
| Daily Pipeline | PRODUCTION | GitHub Actions, runs 16:30 WIB |
| Dashboard | ACTIVE | Single dashboard, 6 tabs (Leaders, Turnaround, Summary, History, Diagnostics, Exit Monitor) |
| Dashboard Consolidation | COMPLETE | V1 retired, single dashboard at dashboard/index.html |
| Turnaround Watchlist | RESEARCH MONITORING | Paper trading only |
| Exit Monitor V1.1 | ACTIVE | Rule-based exit states, Version C thresholds |

### Production Configuration

```
Config B:  Quality 25% | Growth 30% | Value 10% | Momentum 35%
Portfolio: Top 5 equal weight, monthly rebalance
Universe:  IDX30 (dynamic historical for backtest)
Data:      Yahoo Finance (single source)
```

### Key Numbers (Config B Top 5, 2019–2026)

- CAGR: 17.45% (pre-cost) / 13.08% (clean 2023–2025)
- Sharpe: 0.54
- Max DD: -29.17% (2020 COVID)
- Alpha: +12.02% annual vs IHSG

---

## SECTION 2 — CURRENT ARCHITECTURE

```
ISI/
├── Production
│   ├── Config B (Q25/G30/V10/M35)
│   ├── Top 5 Equal Weight Portfolio
│   └── Monthly Rebalance Pipeline
│
├── Daily Pipeline (daily_radar.yml, 16:30 WIB)
│   ├── data_fetcher.py                -> fetches IDX30 daily prices
│   ├── generate_turnaround_watchlist.py
│   │   ├── leaders_latest.csv
│   │   └── turnaround_latest.csv + summary
│   ├── generate_exit_watchlist.py
│   │   ├── exit_watchlist_latest.csv
│   │   └── exit_summary.json
│   ├── generate_dashboard_v2.py        -> dashboard/index.html
│   └── (V1: dashboard.generate_dashboard.py — RETIRED)
│
├── Monthly Pipeline (monthly_pipeline.yml, 1st of month)
│   ├── collectors/*          -> Fetch fundamentals/growth/prices
│   ├── scoring/*             -> Quality/Growth/Value/Momentum/Final
│   ├── backtesting/*         -> Archive factors, rebalance portfolio
│   └── dashboard.*           -> Refresh dashboard
│
├── Dashboard (single, dashboard/index.html)
│   ├── Tab 01: Leaders       Config B ranking
│   ├── Tab 02: Turnaround    Context/Transition signals
│   ├── Tab 03: Daily Summary Signal diagnostics + top candidates
│   ├── Tab 04: History       Streak tracking
│   ├── Tab 05: Diagnostics   Pipeline health
│   └── Tab 06: Exit Monitor  Rule-based exit states
│
├── Core Data
│   ├── warehouse_daily_v4.parquet   45 cols, 30 tickers, 2018-2026
│   ├── factor_warehouse.csv         Monthly factor scores (V3)
│   ├── portfolio_warehouse.csv      Monthly portfolio holdings
│   └── ticker_metadata.csv          Listing dates for IPO gate
│
└── Research Archive
    ├── R001-R007: Factor definition and validation
    ├── R008: Weight optimization (Config B selection)
    ├── R008B: Rally initiation detection
    ├── R009: RS_CHANGE_60D validation
    ├── R009B: Context filter discovery
    ├── R010: Timing engine (paper trading)
    └── S01: Exit signal autopsy
```

---

## SECTION 3 — PROVEN FINDINGS

Research-supported results. Do NOT modify without new evidence.

### Factor Performance

| Factor | Standalone CAGR | IC | Role in Config B |
|--------|:-:|:-:|:-|
| Momentum (RS-6M + Return12M) | 19.07% | Strong | 35% - primary alpha driver |
| Growth (Earnings-only) | +22.66% (combined) | Positive | 30% - acceleration engine |
| Quality (ROE/Margins/FCF) | Moderate | Positive | 25% - drawdown stabilizer |
| Value (PE/PB/DY) | Negative | -0.04 | 10% - minimal exposure |

### Key Findings

✓ **Config B** is the best production configuration - wins 3/4 core metrics across all validation periods.

✓ **Future winners originate from distressed conditions** - deep drawdown + far from high + high volatility predicts turnaround candidates.

✓ **RS_CHANGE_60D is the earliest detectable transition signal** - base precision 21%, improves to 28% in high-volatility contexts.

✓ **Context matters more than threshold magnitude** - same RS_CHANGE_60D signal produces 43% precision on volatile stocks vs 4.5% on stable stocks.

✓ **Earnings-only growth outperforms revenue+earnings** - revenue growth has negative IC (-0.1036, t=-3.05), removing it improves CAGR 6.83% to 13.46%.

✓ **Top 5 is the optimal portfolio size** - maximum CAGR (17.45%), Sharpe per stock peaks at 5, diminishing returns begin immediately after.

✓ **Relative Strength (RS-6M) is a pure alpha generator** - independent signal, not redundant with price momentum.

### Exit Layer Findings

✓ **RS_20D is the strongest exit signal** - Cohen's d = 0.563, Spearman IC = 0.302. Losers show elevated RS at T0 (paradoxical strength before collapse).

✓ **Market weakness must be separated from stock weakness** - Close < MA100 alone captures beta during broad selloffs. Adding RS20 < 0 AND RS_CHANGE_20D < 0 isolates alpha failure.

✓ **Deterioration starts 20-40 days before collapse** - volatility_60d, above_ma20, above_ma100 change first. Drawdown and RS_20D change only 5 days before.

---

## SECTION 4 — FAILED IDEAS (DO NOT REPEAT)

### Recovery Overlay
**Result:** FAILED - not promoted
**Reason:** Mean lead time 0.7 months < 1 month threshold. Lead time insufficient for production use. Recovery State Engine kept as dashboard informational metric only.
**Files:** reports/research_006_consolidated.md

### Early Reversal Engine
**Result:** FAILED - not integrated
**Reason:** Top signals identified (RS 3M, Recovery, RS 6M, Vol 3M, RS Change) but IC target not achieved for standalone production signal. Deferred until live trade execution infrastructure exists.
**Files:** reports/research_007_consolidated.md

### Distress Engine as Config B Overlay
**Result:** FAILED - philosophical mismatch
**Reason:** Adding distress/turnaround filter to Config B degrades portfolio performance. Config B selects leaders; distress selects laggards. Mixing them produces mediocre results. Confirmed: Config B standalone is superior.
**Files:** reports/research_weight_reallocation.md

### Predictive Sell Signal
**Result:** WEAK EVIDENCE - not viable
**Reason:** RESEARCH-S01 confirmed: alpha loss occurs while stocks still appear healthy (strong RS, above MA20, elevated volume). Losers at T0 are indistinguishable from winners. Predictive sell signals cannot be built from existing features.
**Files:** research/output/s01_exit_signal_autopsy_report.md

### Foreign Flow Factor (Factor 005)
**Result:** FAILED - parked indefinitely
**Reason:** Synthetic proxy was volume-adjusted momentum, not real foreign transaction data. Scientific validity score: 10/100. CAGR dropped from 6.62% to 3.11% when included. Cannot be reinstated without real institutional flow data.
**Files:** reports/research_008_audit_report.md

### Min-Max Normalization
**Result:** FAILED - replaced permanently
**Reason:** Outlier Crisis: single extreme value compresses all other scores near zero. Replaced with Percentile Normalization in V4.
**Lesson:** Never use Min-Max for fundamental factor scoring.

### FMP Multi-Source Provider
**Result:** FAILED - decommissioned
**Reason:** FMP blocked IDX queries on free tier with 402/403. Fallback logic became dead code, increased maintenance burden. Replaced with pure YahooFinanceProvider in V6.1.
**Lesson:** Never maintain multi-source fallback for providers that don't work.

### Historical Factor Warehouse (Full 2019+)
**Result:** NOT FEASIBLE
**Reason:** Yahoo Finance only has annual data from 2021-2022 onward. Cannot reconstruct Quality/Growth/Value scores for 2019-2020. Partial V2 (2021+) under investigation but not yet built.
**Lesson:** Before building optimization frameworks, audit historical data availability first.

### Out-of-Sample Factor Weight Optimization (V8.4)
**Result:** PARTIALLY COMPLETE
**Reason:** Framework correctly evaluates performance but CANNOT optimize weights - historical snapshots contain only ticker/return_12m/rank, not factor scores. All configs produce identical rankings.
**Lesson:** Framework is valid for performance evaluation only. Weight optimization requires Historical Factor Warehouse V2.

---

## SECTION 5 — LESSONS LEARNED

### Lesson 1: Future Winner does not equal Current Leader
Stocks that produce the highest forward returns often look distressed at entry - deep drawdown, far from high, elevated volatility. Config B correctly identifies quality within this population.

### Lesson 2: RS Acceleration Appears Before Price Confirmation
RS_CHANGE_60D > 0 is the earliest detectable signal that a stock is transitioning from distress to accumulation. It precedes price recovery by 10-20 trading days.

### Lesson 3: Market Weakness does not equal Stock Weakness
During broad selloffs, Close < MA100 captures beta, not alpha. Always condition exit rules on relative strength (RS20) to differentiate market-driven drawdown from stock-specific deterioration.

### Lesson 4: Backtest Success does not equal Production Compatibility
Config B's superiority in backtest (2019-2025) was validated via walk-forward, but forward warehouse (2026) showed 53% null rates for fundamentals. Real-world data quality differs from backtest.

### Lesson 5: Data Quality Before Factor Research
The OOS validation framework (V8.4) was architecturally correct but produced zero useful weight optimization because historical factor scores were unavailable. Audit data before building research infrastructure.

### Lesson 6: Survivorship Bias Inflates Everything
Static universe backtest showed 41.28% CAGR for RS-6M. After dynamic historical universe correction: 1.21%. The +18.25% CAGR inflation from survivorship bias was eliminated by semi-annual historical snapshots.

### Lesson 7: Banks Are Not Normal Companies
DER > 500% is natural for banks (customer deposits = liabilities). Applying standard DER scoring eliminates all banks. Bank Rule: disable DER for banks, redirect weight to ROE.

### Lesson 8: Commodities at Cycle Peak Are Value Traps
Low PE at commodity cycle peak is false valuation signal. When cycle reverses, earnings collapse and price crashes. Commodity Trap Rule: 50% discount on PE score for cyclical commodity tickers.

---

## SECTION 6 — CURRENT DAILY OUTPUTS

| File | Schema | Generated By |
|------|--------|-------------|
| leaders_latest.csv | rank, ticker, quality, growth, value, momentum, final_score | generate_turnaround_watchlist.py |
| turnaround_latest.csv | rank, ticker, drawdown_252d, distance_from_high_252d, volatility_60d, rs_change_60d, volume_ratio, recovery_from_60d_low, context_match, transition_match | generate_turnaround_watchlist.py |
| turnaround_summary.json | date, universe_size, context/match counts, signal diagnostics, top_candidates | generate_turnaround_watchlist.py |
| exit_watchlist_latest.csv | Date, ticker, rank, rank_change, close, rs_20d, rs_change_20d, ma20, ma50, ma100, drawdown_from_entry, exit_state, triggered_rules | generate_exit_watchlist.py |
| exit_summary.json | date, universe_size, Healthy, Exit Watch, Weakening, Exit Risk, Exit | generate_exit_watchlist.py |
| exit_entry_prices.json | entry_price, entry_date, current_rank per ticker (top 10 tracked) | generate_exit_watchlist.py |
| dashboard/index.html | 6-tab dashboard (Leaders, Turnaround, Summary, History, Diagnostics, Exit Monitor) | generate_dashboard_v2.py |

### Exit Monitor Rule Hierarchy (V1.1)

```text
D: (Close < MA100 AND RS20 < 0 AND RS_CHANGE_20D < 0) OR DD > 15%  ->  EXIT
C: Close < MA50                                                       ->  EXIT RISK
B: RS20 < 0 AND RS_CHANGE_20D < 0                                     ->  WEAKENING
A: Rank > 10 (left Config B Top 10)                                   ->  EXIT WATCH
None                                                                  ->  HEALTHY
```

---

## SECTION 7 — CURRENT STATUS OF EACH SYSTEM

### Config B - PRODUCTION (locked)
- Portfolio: Top 5 equal weight
- Weights: Q25/G30/V10/M35
- Config file: config/scoring_weights.json
- Pipeline: Monthly (1st of month)
- **Do NOT modify weights without:**
  1. Historical Factor Warehouse V2
  2. Proper walk-forward OOS validation

### Turnaround Watchlist - RESEARCH MONITORING
- Identifies stocks transitioning from distress to accumulation
- Uses 5-stage filter: deep drawdown + far from high + high volatility + RS improvement + confirmation
- Output: turnaround_latest.csv
- **Paper trading only - not a production overlay**

### Exit Monitor V1.1 - RESEARCH MONITORING
- Rule-based exit states for all 30 tickers
- Version C thresholds: (Close < MA100 AND RS20<0 AND RS_CHG<0) OR DD > 15%
- Output: exit_watchlist_latest.csv
- **Paper trading only - no production portfolio changes**

### Dashboard - ACTIVE
- Path: dashboard/index.html
- 6 tabs, filterable tables, real-time data from daily pipeline
- Diagnostics tab shows pipeline health and file ages
- Dashboard Consolidation: Complete (V1 retired 2026-06-07)

### Daily Risk Radar - STABLE
- Volume shock detection for top 5 portfolio
- Gemini AI narrative (quota-limited on free tier)
- Output: output/daily_radar_status.json

### OOS Validation Framework - PARTIALLY COMPLETE
- Historical performance evaluation: COMPLETE
- Train/Validation/Test split: COMPLETE
- Factor weight optimization: BLOCKED (missing historical factor data)
- Config A vs B vs C scientific comparison: BLOCKED

---

## SECTION 8 — FUTURE AI INSTRUCTIONS

### Before Proposing Any New Factor:
1. Check Section 4 (Failed Ideas) - do not rebuild what already failed
2. Verify historical data availability - if no PIT data exists for 2019+, factor cannot be validated
3. Review RESEARCH-S01 - no predictive sell signal is viable from current features

### Before Modifying Config B:
1. Review Research-003 (reports/production_portfolio_definition.md)
2. Review Research-010 (reports/FINAL_WEIGHT_DECISION.md)
3. Config B superiority was validated via walk-forward but NOT via proper OOS weight optimization

### Do NOT Rebuild (Unless New Evidence):
- Recovery Overlay - lead time too short
- Early Reversal Engine - IC target not met
- Distress Overlay - philosophical mismatch with Config B
- Predictive Sell Signal - no viable features found
- Foreign Flow Factor - synthetic proxy, needs real data
- Min-Max Normalization - replaced by percentile
- FMP Integration - decommissioned permanently
- Dashboard V1 - retired, use generate_dashboard_v2.py

### Always Use:
- **Percentile Normalization** for all factor scoring - never Min-Max
- **Bank Rule** (DER disabled for financial banks)
- **Commodity Trap Rule** (50% PE discount for cyclical commodities)
- **Dynamic Universe** for backtests - never static
- **IPO Date Gate** - no ranking before listing date
- **BASE_DIR** via config_loader.py - never relative paths

---

## SECTION 9 — RESEARCH ARCHIVE INDEX

### R001-R007: Factor Definition and Validation
Factor research establishing Quality, Growth, Value, and Momentum scoring. Momentum validated as strongest standalone alpha generator (CAGR 19.07%). Growth originally included Revenue + Earnings; Revenue later removed due to negative IC.
- **Files:** reports/alpha_source_analysis.md, reports/v6_momentum_research_summary.md
- **Verdict:** Foundation - all factors accepted

### R008: Weight Optimization (Config B Selection)
Tested Configs A/B/C/D/E/F across Top 5/7/10/12/15 portfolios. Config B (Q25/G30/V10/M35) selected - wins 3/4 core metrics. Config B retained over Config F (earnings-only growth variant).
- **Files:** reports/FINAL_WEIGHT_DECISION.md, reports/config_a_vs_b_clean_validation.md
- **Verdict:** Config B is PRODUCTION

### R008B: Rally Initiation Detection
Discovered earliest detectable transition signals for future winners. Key findings: RS_CHANGE_60D > 0 is the strongest single predictor; context (volatility, sector, drawdown depth) dramatically affects signal quality.
- **Files:** reports/research-008b-executive-summary.md
- **Verdict:** Validated - used in Turnaround Watchlist

### R009: RS_CHANGE_60D Validation
Walk-forward precision analysis: base precision 21.4%, stable across windows. 37.7% precision in bull regimes. 1488 false positives vs 396 true positives - FP stocks show weaker recovery and lower volume.
- **Files:** reports/research-009-executive-summary.md, reports/research-009-failure-analysis.md
- **Verdict:** Validated but not standalone - context filter required

### R009B: Context Filter Discovery
Why same signal produces 43% precision on BRPT vs 4.5% on BBCA. Root cause: volatility context. High-volatility stocks: 28% precision (1.34x lift). Low-volatility stocks: 11.5% precision (0.55x).
- **Files:** research/output/research-009b-context-map.md
- **Verdict:** Context filtering is essential for signal quality

### R010: Timing Engine Paper Trading
5-stage timing layer on top of Config B. Deep drawdown -> far from high -> high volatility -> RS improvement -> confirmation. Paper trading only - no production integration.
- **Files:** research/output/research-010-report.md
- **Verdict:** Research monitoring - paper trading

### S01: Exit Signal Autopsy
Forensic analysis of 303 alpha loss events. Key finding: losers appear healthy at T0 (strong RS, above MA20, elevated volume). Predictive sell signals are weak. Shift to rule-based exit.
- **Files:** research/output/s01_exit_signal_autopsy_report.md
- **Verdict:** Predictive sell not viable -> Exit Layer V1 built

### Dashboard Consolidation
Retired Dashboard V1 (`dashboard/generate_dashboard.py`, `dashboard/data.json`) and nested artifacts. Single dashboard at `dashboard/index.html`. Workflow updated to use only `generate_dashboard_v2.py`.
- **Files:** generate_dashboard_v2.py, .github/workflows/daily_radar.yml
- **Verdict:** Complete - single dashboard, one workflow, no duplicated code
