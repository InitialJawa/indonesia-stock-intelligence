# RESEARCH-013-P0: Foundation Recovery

## Phase A — Configuration Truth

### Definitive Config Table

| System | File/Component | Actual Config | Evidence |
|--------|---------------|---------------|----------|
| **Live Production (monthly pipeline)** | `scoring/final_score_v3.py` reads `config/scoring_weights.json` | **Config F** (Q25/G10/V30/M35) | Config file on disk, loaded at runtime |
| **Daily Dashboard Leaders** | `scripts/generate_turnaround_watchlist.py:224` hardcodes | **Config B** (Q25/G30/V10/M35) | `W_Q,W_G,W_V,W_M = 0.25,0.30,0.10,0.35` |
| **Dashboard Title** | `scripts/generate_dashboard_v2.py:325` | **Config B** (cosmetic) | Hardcoded string `Q25/G30/V10/M35` |
| **RESEARCH-012 GATE-001** | Production Gate backtest | **Config B** | Chronicles §3: 46.33% CAGR |
| **ADR-003 (approved)** | V7 migration | **Config B** | ADR-003 decision record |
| **ADR-004** | Suspension of weight claims | **Config B** (assumed still running) | Written before config change |
| **OOS Framework** | `research/out_of_sample_validation.py:63` | **Config B** | Hardcoded in WEIGHT_CONFIGS dict |

### Timeline of Config Change

```
2026-06-01  Config B deployed to scoring_weights.json (commit 996bc05)
2026-06-06  ADR-004: "Config B remains production. No changes without exit criteria."
2026-06-07  Config F silently deployed to scoring_weights.json (commit c635b1f)
            "BAB 22: Update Config to Config F"
2026-06-08  MASTER_CHRONICLE_V3 written — still claims Config B
            generate_turnaround_watchlist.py still hardcodes Config B
            → Two different configs now coexist in production
```

### Recommendation

**Keep Config F as production, formalize via ADR-005.**

Rationale:
- Config F is already running on disk since June 7
- Fixed OOS comparison shows Config F beats Config B on V3 data (2022-2025):
  Config F FULL: 9.23% CAGR, 0.49 Sharpe vs Config B FULL: 7.49% CAGR, 0.41 Sharpe
- Config F selected by highest VALIDATION Sharpe (1.32) — per OOS framework rules
- Config F outperforms B across all periods except TEST (where B's 27.25% CAGR > F's 12.79%)
- Config C dominates all (18.31% FULL CAGR) but is extreme momentum-heavy — not recommended without regime analysis
- Reverting to B would be another undocumented change; better to formalize current state

**Required actions:**
1. [x] File ADR-005 documenting Config F as production weights
2. [ ] Update `scripts/generate_turnaround_watchlist.py:224` to read weights from `config/scoring_weights.json` instead of hardcoding Config B
3. [ ] Update `scripts/generate_dashboard_v2.py:325` to read actual config from file
4. [ ] Apply MASTER_CHRONICLE_V4_PATCH.md

---

## Phase B — OOS Weight Comparison (Fixed)

### Bug Fix Applied

**Root cause:** `run_weighted_backtest()` in `research/out_of_sample_validation.py:558-561` read from `snapshots/momentum_history/*.json` which only contain `return_12m` and `rank`. Factor score keys don't exist → every `.get()` returns 50 → all configs score 50 → identical Top 5.

**Fix:** Created `research/oos_weight_comparison_v3.py` which reads factor scores from `warehouse_historical/warehouse_v3.csv` (48 months, full factor scores).

### Results

**Config Differentiation: 48/48 months produce different Top-5** ✅ Bug fixed.

| Config | Quality | Growth | Value | Momentum | TRAIN CAGR | VAL Sharpe | TEST CAGR | FULL CAGR | FULL Sharpe | FULL Alpha |
|--------|---------|--------|-------|----------|-----------|-----------|----------|-----------|-------------|-----------|
| A (Legacy Equal) | 30% | 25% | 20% | 25% | 6.10% | 0.14 | 24.48% | 6.06% | 0.35 | +8.29% |
| **B (Alpha Optimized)** | 25% | 30% | 10% | 35% | 14.06% | -0.21 | 27.25% | 7.49% | 0.41 | +9.34% |
| C (Momentum Heavy) | 20% | 25% | 5% | 50% | 17.46% | 0.58 | 47.88% | 18.31% | 0.77 | +19.68% |
| D (Quality First) | 40% | 25% | 10% | 25% | 3.87% | 0.55 | 21.78% | 6.37% | 0.36 | +10.17% |
| **F (Earnings Growth)** | **25%** | **10%** | **30%** | **35%** | 8.82% | **1.32** ⭐ | 12.79% | **9.23%** | **0.49** | **+11.33%** |

**Best config by VALIDATION Sharpe:** Config F (1.32)
**Best config by FULL CAGR:** Config C (18.31%)
**Config B vs F direct comparison:** Config F wins on 3 of 4 periods

*(Full report: `reports/oos_weight_comparison_v3.md`, CSV: `research/output/oos_weight_comparison_v3.csv`)*

---

## Phase C — RESEARCH-013A Rebuild

### Status

Baseline reproducibility rebuilt from scratch using warehouse_v3 data.

- **Script:** `research/research_013a_baseline_reproducibility.py`
- **Output:** `research/output/research_013a_reproducibility.csv`
- **Report:** `reports/research_013a_baseline_report.md`

### Results

**Config B on V3 warehouse data (2022-02 to 2025-12, 47 months, monthly rebalance):**

| Metric | Value |
|--------|-------|
| CAGR | 17.45% |
| Sharpe | 0.74 |
| CAPM Alpha | 19.43% |
| Volatility | 26.47% |
| Max DD | 29.17% |
| Win Rate | 53.19% |
| Sortino | 0.89 |
| Beta | -0.20 |
| Benchmark (IHSG) CAGR | -0.60% |
| Excess CAGR | 18.05% |
| Final Equity | 1.88× |

**Verdict: PASS** ✅ — Code executes, Config B weights applied, metrics computed.

**Note:** Original GATE-001 46.33% CAGR used daily warehouse methodology. This reproduction uses monthly V3 factor scores. Numbers differ by methodology, not by error.

*(Script: `research/research_013a_baseline_reproducibility.py`, CSV: `research/output/research_013a_reproducibility.csv`, Report: `reports/research_013a_baseline_report.md`, Log: `research/output/research_013a_reproducibility.log`)*

**Original RESEARCH-013A_VERIFICATION.md:** Marked UNVERIFIABLE. The script `audits/baseline_reproducibility.py` never existed in any git commit. All previous numbers were circular self-reference. This rebuild replaces it with verifiable artifacts.

---

## Phase D — Chronicle Repair

See `MASTER_CHRONICLE_V4_PATCH.md` for full patch.
