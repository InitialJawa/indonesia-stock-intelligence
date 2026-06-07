# RESEARCH-002 Experiment A: Earnings Only Growth

**Date:** 2026-06-06  
**Period:** 2023-01 to 2025-12 (35 months)  
**Universe:** IDX30 (29 tickers)  
**Benchmark:** IHSG monthly return (excess-based Sharpe)

---

## Objective

Test whether switching Growth from 50/50 (Revenue + Earnings) to Earnings-only
improves factor quality and portfolio performance.

## Growth Formula Comparison

| Component | Formula | IC | t-stat | Hit Rate | Quintile Spread |
|-----------|---------|:--:|:------:|:--------:|:---------------:|
| Current 50/50 Growth | 50% rev_score + 50% earn_score | -0.0846 | -2.66 | 42.86% | -0.26% |
| Revenue Only | 100% rev_score | -0.1063 | -3.05 | 31.43% | -1.83% |
| Earnings Only | 100% earn_score | -0.0346 | -0.95 | 45.71% | -0.13% |

## Top 5 Backtest Results

| Definition | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |
|-----------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|
| Current 50/50 Growth | 6.83% | 0.0205 | 0.0263 | -29.17% | 45.71% | 0.41% | 24.04% | 22.29% |
| Revenue Only | -2.72% | -0.4650 | -0.5317 | -33.68% | 42.86% | -9.08% | 23.42% | 26.29% |
| Earnings Only | 13.46% | 0.3430 | 0.3604 | -30.48% | 48.57% | 6.91% | 25.76% | 22.86% |
| **IHSG** | 8.37% | — | — | — | — | — | — | — |

## Top 10 Backtest Results

| Definition | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |
|-----------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|
| Current 50/50 Growth | 5.26% | -0.2040 | -0.2226 | -19.04% | 60.00% | -2.38% | 16.96% | 21.14% |
| Revenue Only | 4.02% | -0.2992 | -0.2440 | -17.17% | 65.71% | -3.60% | 16.72% | 20.29% |
| Earnings Only | 7.14% | -0.0603 | -0.0641 | -18.45% | 54.29% | -0.68% | 16.53% | 19.43% |
| **IHSG** | 8.37% | — | — | — | — | — | — | — |

## Key Findings

### Earnings Only IC Improvement

- Revenue Only IC = -0.1063 (t=-3.05) — strongest negative alpha
- Earnings Only IC = -0.0346 (t=-0.95) — weakest negative alpha
- Current 50/50 IC = -0.0846 (t=-2.66)

Switching to Earnings-only raises IC from -0.0846 to -0.0346,
an improvement of +0.0500.

### Does it Eliminate Alpha Leakage?

**No.** Earnings-only IC is still negative (-0.0346).
The t-stat (-0.95) is not statistically significant at 95% confidence (|t| < 2.0),
meaning Earnings-only is effectively **neutral** rather than harmful.

### Top 5 Performance Impact

Switching to Earnings Only:
- CAGR: 6.83% -> 13.46%
- Sharpe: 0.0205 -> 0.3430
- Max DD: -29.17% -> -30.48%

### Top 10 Performance Impact

Earnings Only:
- CAGR: 7.14%
- Sharpe: -0.0603

### Verdict

| Question | Answer |
|----------|--------|
| Is Earnings-only better than 50/50? | **Yes** — less negative IC |
| Does it fix alpha leakage? | **Partially** — neutral rather than harmful |
| Should we switch to Earnings-only? | **Yes, as an immediate fix** |
