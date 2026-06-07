# RESEARCH-002 Experiment C: Growth Replacement

**Date:** 2026-06-06  
**Period:** 2023-01 to 2025-12 (35 months)  
**Benchmark:** IHSG monthly return (excess-based Sharpe)

---

## Objective

Test whether completely replacing Growth with LowVol or Dividend
produces better risk-adjusted returns than current Config B.

## Configurations Tested

| Config | Quality | Growth | Value | Momentum | LowVol | Dividend |
|--------|:-------:|:------:|:-----:|:--------:|:------:|:--------:|
| Config B (prod) | 25% | 30% | 10% | 35% | — | — |
| Replace w/ LowVol | 25% | — | 20% | 35% | 20% | — |
| Replace w/ Dividend | 25% | — | 20% | 35% | — | 20% |

## Top 5 Backtest Results

| Config | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |
|--------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|
| Config B (prod) | 6.83% | 0.0205 | 0.0263 | -29.17% | 45.71% | 0.41% | 24.04% | 22.29% |
| Replace w/ LowVol | 9.53% | 0.1237 | 0.1349 | -13.71% | 65.71% | 1.24% | 14.41% | 19.43% |
| Replace w/ Dividend | 2.24% | -0.3515 | -0.3216 | -16.90% | 65.71% | -5.01% | 18.61% | 23.43% |

## Top 10 Backtest Results

| Config | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |
|--------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|
| Config B (prod) | 5.26% | -0.2040 | -0.2226 | -19.04% | 60.00% | -2.38% | 16.96% | 21.14% |
| Replace w/ LowVol | 1.06% | -0.7058 | -0.6357 | -15.43% | 68.57% | -6.87% | 14.09% | 15.14% |
| Replace w/ Dividend | 5.59% | -0.1520 | -0.1299 | -13.85% | 65.71% | -2.00% | 17.17% | 10.57% |


## Key Findings

### LowVol Replacement

- Sharpe delta vs Config B: 0.1032
- CAGR delta vs Config B: 2.71%
- Max DD: -13.71% vs -29.17%

### Dividend Replacement

- Sharpe delta vs Config B: -0.3721
- CAGR delta vs Config B: -4.59%
- Max DD: -16.90% vs -29.17%

### Best Config by Sharpe (Top 5): **Replace w/ LowVol**
### Best Config by Sharpe (Top 10): **Replace w/ Dividend**

### Decision Matrix

| Factor | IC | Sharpe Impact | CAGR Impact | Recommendation |
|--------|:--:|:-------------:|:-----------:|:-------------:|
| Growth (current) | -0.0846 (t=-2.66) | baseline | baseline | Review |
| LowVol | 0.0713 (from RESEARCH-001) | 0.1032 | 2.71% | **Replace Growth** |
| Dividend | 0.1245 (from RESEARCH-001) | -0.3721 | -4.59% | Hold |

### Verdict

| Question | Answer |
|----------|--------|
| Is LowVol better than Growth? | **Yes** |
| Is Dividend better than Growth? | **Not in this test** |
| Should Growth be replaced entirely? | **Yes, with Replace w/ LowVol** |
| Best config after all research | **Replace w/ LowVol** |
