# RESEARCH-002 Experiment B: Weight Reallocation

**Date:** 2026-06-06  
**Period:** 2023-01 to 2025-12 (35 months)  
**Growth variant:** Earnings Only (for all configs)  
**Benchmark:** IHSG monthly return (excess-based Sharpe)

---

## Objective

Test whether reducing Growth weight and reallocating to Value and/or LowVol
improves portfolio performance.

## Configurations Tested

| Config | Quality | Growth (Earnings) | Value | Momentum | LowVol |
|--------|:-------:|:-----------------:|:-----:|:--------:|:------:|
| Config B (prod) | 25% | 30% | 10% | 35% | 0% |
| Config D | 25% | 15% | 25% | 35% | 0% |
| Config E | 25% | 15% | 20% | 30% | 10% |
| Config F | 25% | 10% | 30% | 35% | 0% |

## Top 5 Backtest Results

| Config | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |
|--------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|
| Config B (prod) | 13.46% | 0.3430 | 0.3604 | -30.48% | 48.57% | 6.91% | 25.76% | 22.86% |
| Config D | 11.73% | 0.2663 | 0.3317 | -20.76% | 60.00% | 4.51% | 21.97% | 26.29% |
| Config E | 13.36% | 0.4179 | 0.4391 | -12.42% | 65.71% | 5.41% | 18.96% | 17.14% |
| Config F | 15.13% | 0.4339 | 0.5541 | -14.05% | 57.14% | 7.60% | 22.32% | 22.29% |

## Top 10 Backtest Results

| Config | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |
|--------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|
| Config B (prod) | 7.14% | -0.0603 | -0.0641 | -18.45% | 54.29% | -0.68% | 16.53% | 19.43% |
| Config D | 13.99% | 0.4503 | 0.3966 | -13.08% | 62.86% | 5.78% | 17.69% | 16.86% |
| Config E | 10.96% | 0.2666 | 0.2691 | -15.75% | 62.86% | 2.96% | 17.15% | 14.29% |
| Config F | 13.93% | 0.4701 | 0.4611 | -14.01% | 65.71% | 5.98% | 19.09% | 13.14% |


## Key Findings

### Top 5: Best Config by Sharpe

**Config F** — Sharpe=0.4339, CAGR=15.13%, Alpha=7.60%

### Top 10: Best Config by Sharpe

**Config F** — Sharpe=0.4701, CAGR=13.93%, Alpha=5.98%

### Config Comparison (Top 5)

| Config | vs Config B (Sharpe diff) | vs Config B (CAGR diff) |
|--------|:-------------------------:|:-----------------------:|
| Config D | -0.0767 | -1.72% |
| Config E | 0.0749 | -0.09% |
| Config F | 0.0910 | 1.67% |


### Verdict

| Question | Answer |
|----------|--------|
| Should Growth weight be reduced? | **Yes** |
| Should Value be increased? | **Yes** |
| Is LowVol useful? | **Yes** |
| Best overall config | **Config F** |
