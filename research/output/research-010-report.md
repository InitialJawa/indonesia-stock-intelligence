# RESEARCH-010: Timing Engine Paper Trading
**Generated:** 2026-06-07 14:46:06

---

## Objective

Determine whether a 5-stage timing layer adds value on top of the existing ranking engine (Config B).

**Do NOT integrate into production. Do NOT alter Config B.**

---

## Engine Structure

| Stage | Filter | Criteria |
|-------|--------|----------|
| 1 | Deep Drawdown | `drawdown_252d < -25%` |
| 2 | Far From High | `distance_from_high_252d < -20%` |
| 3 | High Volatility | `volatility_60d > 67th pctile` |
| 4 | RS_CHANGE_60D | `rs_change_60d > 0` (gate) |
| 5 | Confirmation Layer | Volume > 1.2, Above MA20, Momentum > 0 |

### State Mapping

| State | Core Score | Confirmations | Weight |
|-------|-----------|---------------|--------|
| AVOID | any | rs_change <= 0 | 0% |
| WATCH | >= 1 core | any | 25% (reduced to 10% if no core) |
| ACCUMULATE | >= 2 core | >= 1 conf | 50% of normal |
| BUY | >= 2 core | >= 2 conf | 100% (full 20%) |
| HOLD | (carryover from prior period) | | maintained |

---

## Backtest Results

Period: 2019-02 to 2026-06 (89 months)
Portfolio: Top 5 by momentum score, equal weight baseline

### Performance Metrics

| Metric | Baseline | +Timing | IHSG |
|--------|----------|---------|------|
| CAGR | 0.81% | -0.53% | 0.43% |
| Volatility (ann.) | 28.39% | 31.45% | - |
| Sharpe Ratio | -0.15 | -0.18 | - |
| Sortino Ratio | -0.21 | -0.25 | - |
| Max Drawdown | -39.66% | -54.85% | - |
| Alpha | 1.10% | -0.66% | - |
| Beta | 1.29 | 1.13 | - |
| Hit Rate | 55.06% | 47.19% | - |
| Avg Monthly Turnover | 25.45% | 54.64% | - |

### State Distribution

| State | Count | % |
|-------|-------|---|
| AVOID | 272 | 61.1% |
| WATCH | 157 | 35.3% |
| ACCUMULATE | 8 | 1.8% |
| BUY | 8 | 1.8% |
| Cash (avg) | - | 88.8% |

### Regime Breakdown

| Regime | Months | Baseline Avg | Timed Avg | BM Avg | Diff |
|--------|--------|-------------|-----------|--------|------|
| bull | 7 | +9.37% | +9.54% | +4.40% | +0.17% |
| bear | 5 | -1.07% | -3.11% | -2.52% | -2.04% |
| sideways | 50 | +0.23% | +0.11% | +0.45% | -0.12% |
| unknown | 27 | -1.32% | -0.89% | -1.07% | +0.43% |

### Monthly Improvement Breakdown

- Timing helped in **39** of 89 months (43.8%)
- Timing hurt in **49** of 89 months (55.1%)

---

## Drawdown Analysis

| Measure | Baseline | +Timing |
|---------|----------|---------|
| Max Drawdown | -39.66% | -54.85% |
| Worst Month (Baseline) | 2020-05 (-39.66%) | -35.66% |
| Recovery (worst DD to 0) | - | - |

---

## Verdict

- ❌ Sharpe degraded: -0.15 → -0.18
- ❌ Max Drawdown increased: -39.66% → -54.85%
- ❌ CAGR destroyed: 0.81% → -0.53%

**Conclusion: Timing engine does NOT add value in its current form.**

## Root Cause: Engine Misalignment

The timing engine and the ranking engine operate on **fundamentally opposite premises**:

| Dimension | Timing Engine Expects | Momentum Ranking Selects |
|-----------|---------------------|------------------------|
| Drawdown | Deep (< -25%) | Shallow (avg -10% to -15%) |
| Distance from High | Far (< -20%) | Near high (> -5%) |
| RS Change 60D | Positive (improving) | Often negative (peaked momentum) |
| Profile | Distressed, reversing | Strong, trending up |

**Evidence from the failure:**
- **61.1%** of stock-months are AVOID (rs_change_60d negative for momentum winners)
- Only **1.8%** ever reach BUY state
- **88.8%** average cash — engine keeps the portfolio mostly uninvested
- When BUY does fire (e.g., BRPT.JK with dd=-57%, vol=1.26, rs_chg=+0.62), it adds +26% outperformance in one month (2026-05)

**Diagnostic sample — momentum portfolio stocks at formation dates:**

```
Formation 2024-01:
  BMRI.JK: dd=-0.8%  (Stage 1 FAILS — not distressed)
  BBRI.JK: dd=-3.4%  (Stage 1 FAILS)
  BRPT.JK: dd=-45.6% (Stage 1 PASS) rs_chg=-0.38 (Stage 4 FAILS)

Formation 2022-06:
  ADRO.JK: dd=-22.9%  (Stage 1 borderline) rs_chg=-0.26 (Stage 4 FAILS)
```

The timing engine was calibrated on the reversal setup discovered in RESEARCH-008/008B/009 (future winners emerge from deep distress). But it is being applied to a **momentum portfolio** that selects already-strong stocks. This is the fundamental mismatch.

### What Would Work

The timing engine's 5-stage design is appropriate for:
- A **value** or **contrarian** ranking engine that naturally selects distressed stocks
- A **mean-reversion** strategy
- A **recovery** overlay (as explored in RESEARCH-006)

For a momentum-ranking portfolio, the timing engine needs to be redesigned as a **momentum-sustain** filter:
- Stage 1: RS trend positive (not improving from negative, but maintaining positive)
- Stage 2: Above MA50/MA200 (confirmation of uptrend)
- Stage 3: Manageable volatility (avoid blow-off tops)
- Stage 4: Volume confirmation (sustained interest)
- Stage 5: Sector/market regime alignment

This is outside the scope of the current research. The current prototype demonstrates that the distressed-to-accumulation timing logic does NOT port directly to a momentum-ranking portfolio.

---
*End of RESEARCH-010 Timing Engine Paper Trading*
