# RESEARCH-006: Recovery Overlay Validation — Consolidated Report

**Date:** 2026-06-07  
**Status:** Complete

---

## Executive Summary
This research validates whether adding a Recovery Score overlay to ISI's Config B improves early detection of rebound candidates without degrading portfolio performance.

---

## Objective
Tentukan apakah Recovery Score dapat meningkatkan kemampuan ISI mendeteksi kandidat rebound lebih awal tanpa merusak performa portfolio produksi.

---

## Current Production Setup
- **Portfolio**: Top 5
- **Config B**: Q25 / G30 / V10 / M35
- **No Production Changes**: All experiments are research-only

---

## Hypothesis
Recovery Factor tidak layak menjadi faktor utama, namun mungkin layak menjadi ranking overlay, timing overlay, atau early accumulation detector untuk saham yang mulai keluar dari fase weakness.

Target utama: Identifikasi BBCA, BBRI, TLKM, BMRI, ASII lebih awal dibanding ranking ISI standar.

---

## Experiment A — Score Overlay

### Setup
Test overlay variants combining ISI Config B score with Recovery Score:

| Variant | ISI Weight | Recovery Weight |
|---------|------------|-----------------|
| Baseline | 1.00 | 0.00 |
| Variant 1 | 0.95 | 0.05 |
| Variant 2 | 0.90 | 0.10 |
| Variant 3 | 0.85 | 0.15 |
| Variant 4 | 0.80 | 0.20 |

### Results (2023-2025)
| Score Name | Mean Monthly Return | Cumulative Return | CAGR |
|------------|---------------------|-------------------|------|
| Baseline (Synthetic Config B) | -0.57% | -18.9% | -7.2% |
| Overlay V1 (5% Recovery) | -0.55% | -18.5% | -7.1% |
| Overlay V2 (10% Recovery) | -0.52% | -17.8% | -6.8% |
| Overlay V3 (15% Recovery) | -0.49% | -17.1% | -6.5% |
| Overlay V4 (20% Recovery) | -0.45% | -16.2% | -6.1% |

### Notes
- Preliminary results show overlays slightly improve CAGR
- Full risk metrics (Sharpe, Sortino, Max DD, Turnover) need full historical Config B data
- Success Criteria Check: CAGR overlays ≥ Baseline ✅

---

## Experiment B — Rank Advancement Analysis

### Objective
Measure how many months earlier Recovery Overlay detects future top 5 stocks.

### Key Metrics
| Metric | Value |
|--------|-------|
| Number of tickers analyzed | 35 |
| Mean lead time | 0.7 months |
| Median lead time | 0 months |
| Max lead time | 3 months |

### Target Stock Observations
| Stock | Lead Time |
|-------|-----------|
| BBCA | -1 month |
| BBRI | +1 month |
| TLKM | +2 months |
| BMRI | 0 months |
| ASII | +1 month |

### Success Criteria Check
Average lead time ≥ 1 month ❌ (0.7 months)

---

## Experiment C — Recovery Confirmation Layer

### State Definition
Use Recovery Score percentiles to assign states (no ranking change):
| State | Recovery Percentile |
|-------|----------------------|
| AVOID | <40 |
| WATCH | 40-60 |
| ACCUMULATE | 60-80 |
| BUY | >80 |

### Performance by State
| State | 1M Mean | 3M Mean | 6M Mean | Count |
|-------|---------|---------|---------|-------|
| AVOID | -0.34% | -1.52% | -3.12% | 732 |
| WATCH | -0.18% | -1.19% | -2.45% | 456 |
| ACCUMULATE | 0.09% | -0.67% | -1.89% | 387 |
| BUY | 0.45% | 0.12% | -0.78% | 345 |

### Success Criteria Check
✅ BUY outperforms WATCH  
✅ WATCH outperforms AVOID

---

## Experiment D — BBCA Case Study

### Objective
Use BBCA as validation sample to see if Recovery detects accumulation phase earlier.

### Key Timeline (Selected Months)
| Month | ISI Rank | Recovery Rank | Overlay Rank | Recovery State |
|-------|----------|---------------|--------------|----------------|
| 2023-03 | 12 | 3 | 6 | BUY |
| 2023-07 | 15 | 5 | 9 | ACCUMULATE |
| 2024-01 | 8 | 4 | 6 | BUY |
| 2024-06 | 11 | 2 | 7 | BUY |
| 2025-04 | 7 | 3 | 5 | ACCUMULATE |

### Findings
Recovery consistently ranks BBCA in top 5 before synthetic ISI in several months. Largest lead in 2023-07: Recovery ranked 5th vs ISI 15th.

---

## Final Verdict

### Decision Rules Recap
Promote Recovery Overlay to production only if:
1. CAGR ≥ Config B
2. Sharpe ≥ Config B
3. Average lead time ≥ 1 month
4. Turnover increase ≤10%

### Check List
| Criteria | Met? |
|----------|------|
| 1. CAGR ≥ Config B | ✅ |
| 2. Sharpe ≥ Config B | ❓ (needs full Config B data) |
| 3. Average lead time ≥1 month | ❌ (0.7 months) |
| 4. Turnover ≤+10% | ❓ (needs full Config B data) |

### Final Decision
**Recovery Overlay NOT promoted to production**

However, the Recovery State Engine (Experiment C) passed validation and should remain **informational only** (added to dashboard as context).

### Recommendation
- Add Recovery State (AVOID/WATCH/ACCUMULATE/BUY) to ISI dashboard as informational layer
- Monitor Recovery metrics alongside Config B rankings
- Revisit when full historical Config B scores are available

---

## Files Produced
- `research/recovery_overlay_validation.py`
- `research/output/experiment_a_results.csv`
- `research/output/experiment_b_results.csv`
- `research/output/experiment_c_results.csv`
- `research/output/experiment_d_bbca.csv`
