# Final Validation: Config B vs Config F

**Date:** 2026-06-06
**Period:** 202501-202511 (11 months)
**Universe:** IDX30 (29 tickers)
**Benchmark:** IHSG monthly return (excess-based Sharpe)
**Growth variant (Config F):** Earnings Only (100% earn_score percentile)

---

## Objective

Validate Config F (Q25 G10 V30 M35) against current Config B (Q25 G30 V10 M35)
under realistic transaction cost scenarios before promoting to production.

## Configurations

| Config | Quality | Growth | Value | Momentum | Growth Formula |
|--------|:-------:|:------:|:-----:|:--------:|---------------|
| Config B (current) | 25% | 30% | 10% | 35% | 50% rev_score + 50% earn_score |
| Config F (proposed) | 25% | 10% | 30% | 35% | 100% earn_score (Earnings Only) |

## Transaction Cost Scenarios

| Scenario | One-Way Cost | Round-Trip |
|----------|:-----------:|:-----------:|
| A - Low | 0.15% | 0.30% |
| B - Medium | 0.30% | 0.60% |
| C - High | 0.50% | 1.00% |

---

## Top 5 Results

| Config | Cost | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover | Total Ret |
|--------|:---:|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|:---------:|
| Config B | 0.00% | 50.85% | 0.9420 | 2.0895 | -4.18% | 63.64% | 21.55% | 26.61% | 18.18% | 45.77% |
| Config B | 0.15% | 50.37% | 0.9275 | 2.0413 | -4.24% | 63.64% | 21.22% | 26.60% | 18.18% | 45.35% |
| Config B | 0.30% | 49.90% | 0.9130 | 1.9937 | -4.30% | 63.64% | 20.90% | 26.59% | 18.18% | 44.93% |
| Config B | 0.50% | 49.27% | 0.8936 | 1.9313 | -4.38% | 63.64% | 20.46% | 26.58% | 18.18% | 44.37% |
| Config F | 0.00% | 47.78% | 0.9258 | 1.9110 | -7.98% | 63.64% | 20.13% | 29.01% | 23.64% | 43.05% |
| Config F | 0.15% | 47.19% | 0.9082 | 1.8515 | -8.04% | 63.64% | 19.70% | 28.95% | 23.64% | 42.52% |
| Config F | 0.30% | 46.60% | 0.8905 | 1.7930 | -8.10% | 63.64% | 19.28% | 28.89% | 23.64% | 42.00% |
| Config F | 0.50% | 45.82% | 0.8668 | 1.7168 | -8.18% | 63.64% | 18.71% | 28.81% | 23.64% | 41.31% |
| **IHSG** | - | 22.21% | - | - | - | - | - | - | - | - |

---

## Top 10 Results

| Config | Cost | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover | Total Ret |
|--------|:---:|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|:---------:|
| Config B | 0.00% | 28.96% | 0.4154 | 0.5733 | -5.42% | 63.64% | 4.08% | 18.75% | 19.09% | 26.26% |
| Config B | 0.15% | 28.53% | 0.3803 | 0.5184 | -5.47% | 63.64% | 3.74% | 18.72% | 19.09% | 25.87% |
| Config B | 0.30% | 28.10% | 0.3452 | 0.4648 | -5.51% | 63.64% | 3.39% | 18.70% | 19.09% | 25.49% |
| Config B | 0.50% | 27.54% | 0.2984 | 0.3954 | -5.57% | 63.64% | 2.93% | 18.67% | 19.09% | 24.98% |
| Config F | 0.00% | 37.43% | 1.0513 | 1.7979 | -5.32% | 72.73% | 11.33% | 22.64% | 12.73% | 33.83% |
| Config F | 0.15% | 37.12% | 1.0301 | 1.7392 | -5.37% | 72.73% | 11.10% | 22.63% | 12.73% | 33.56% |
| Config F | 0.30% | 36.82% | 1.0089 | 1.6820 | -5.41% | 72.73% | 10.87% | 22.62% | 12.73% | 33.29% |
| Config F | 0.50% | 36.42% | 0.9806 | 1.6077 | -5.47% | 72.73% | 10.56% | 22.61% | 12.73% | 32.93% |
| **IHSG** | - | 22.21% | - | - | - | - | - | - | - | - |

---

## Key Comparisons

### Top 5 - Config B vs Config F at 0.00% Cost

| Metric | Config B | Config F | Delta |
|--------|:--------:|:--------:|:-----:|
| CAGR | 50.85% | 47.78% | -3.07% |
| Sharpe | 0.9420 | 0.9258 | -0.0163 |
| Sortino | 2.0895 | 1.9110 | -0.1785 |
| Max DD | -4.18% | -7.98% | -3.80% |
| Win Rate | 63.64% | 63.64% | 0.00% |
| Alpha | 21.55% | 20.13% | -1.42% |
| Vol | 26.61% | 29.01% | 2.41% |
| Turnover | 18.18% | 23.64% | 5.45% |

### Top 5 - At 0.30% Cost (Decision Gate)

| Metric | Config B | Config F | Delta |
|--------|:--------:|:--------:|:-----:|
| CAGR | 49.90% | 46.60% | -3.30% |
| Sharpe | 0.9130 | 0.8905 | -0.0225 |
| Sortino | 1.9937 | 1.7930 | -0.2007 |
| Max DD | -4.30% | -8.10% | -3.80% |
| Win Rate | 63.64% | 63.64% | 0.00% |
| Alpha | 20.90% | 19.28% | -1.62% |
| Vol | 26.59% | 28.89% | 2.30% |
| Turnover | 18.18% | 23.64% | 5.45% |

### Alpha Erosion: Top 5

| Cost Scenario | Config B Alpha | Config F Alpha |
|:-------------:|:-------------:|:--------------:|
| 0.00% | 21.55% | 20.13% |
| 0.15% | 21.22% | 19.70% |
| 0.30% | 20.90% | 19.28% |
| 0.50% | 20.46% | 18.71% |

### Alpha Erosion: Top 10

| Cost Scenario | Config B Alpha | Config F Alpha |
|:-------------:|:-------------:|:--------------:|
| 0.00% | 4.08% | 11.33% |
| 0.15% | 3.74% | 11.10% |
| 0.30% | 3.39% | 10.87% |
| 0.50% | 2.93% | 10.56% |


## Decision Analysis

### Pass/Fail by Condition

**At 0.00% Cost**

| Condition | Top 5 | Top 10 |
|-----------|:-----:|:------:|
| Sharpe higher than Config B | NO | YES |
| CAGR higher than Config B | NO | YES |
| Alpha positive after cost | YES | YES |
| **Overall** | **FAIL** | **PASS** |

**At 0.15% Cost**

| Condition | Top 5 | Top 10 |
|-----------|:-----:|:------:|
| Sharpe higher than Config B | NO | YES |
| CAGR higher than Config B | NO | YES |
| Alpha positive after cost | YES | YES |
| **Overall** | **FAIL** | **PASS** |

**At 0.30% Cost**

| Condition | Top 5 | Top 10 |
|-----------|:-----:|:------:|
| Sharpe higher than Config B | NO | YES |
| CAGR higher than Config B | NO | YES |
| Alpha positive after cost | YES | YES |
| **Overall** | **FAIL** | **PASS** |

**At 0.50% Cost**

| Condition | Top 5 | Top 10 |
|-----------|:-----:|:------:|
| Sharpe higher than Config B | NO | YES |
| CAGR higher than Config B | NO | YES |
| Alpha positive after cost | YES | YES |
| **Overall** | **FAIL** | **PASS** |

## Final Verdict

**Status: RESEARCH ONLY**

Config F fails one or more validation gates.

### Recommendation

Keep Config F as **Research Only**. Do not promote to production.
Consider further tuning or alternative configurations for the next research cycle.

---

### Technical Note

Config F **passes Top 10** across all cost scenarios but **fails Top 5** across all cost scenarios.
Since the production system targets Top 10 portfolio construction, Config F may still be viable if the decision rule is applied per-portfolio-size rather than requiring both sizes to pass.

| Portfolio Size | Verdict |
|:--------------:|:-------:|
| Top 5 | FAIL (Config B still outperforms in concentrated portfolio) |
| Top 10 | PASS (Config F dominates in diversification) |
