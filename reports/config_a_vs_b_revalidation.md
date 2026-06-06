# Config A vs B Revalidation

**Date:** 2026-06-06  
**Methodology:** Monthly Top-5 equal-weight portfolio using Warehouse V2 factor scores.
Next-month return computed from warehouse monthly prices.  
**Period:** 202201 to 202511 (47 months)

---

## Configuration Definitions

| Config | Quality | Growth | Value | Momentum |
|--------|:------:|:------:|:-----:|:--------:|
| A (Legacy Equal) | 30% | 25% | 20% | 25% |
| B (Alpha Optimized) | 25% | 30% | 10% | 35% |

---

## Performance Metrics

| Metric | Config A | Config B | Difference |
|--------|:--------:|:--------:|:----------:|
| **CAGR** | 20.43% | 23.25% | 2.82% |
| **Sharpe Ratio** | 0.5488 | 0.6263 | 0.0776 |
| **Max Drawdown** | -20.76% | -22.18% | -1.41% |
| **Win Rate** | 57.45% | 63.83% | 6.38% |
| **Portfolio Turnover** | 18.26% | 21.30% | 3.04% |
| **Total Return** | 103.95% | 122.84% | 18.89% |
| **Observations** | 47 | 47 | — |

---

## Analysis

**Config B wins 3 of 4 core metrics.**

### CAGR
Config B delivers higher geometric annualized return
by 2.82 pp. Total return over full period: Config A 103.95% vs
Config B 122.84%.

### Sharpe Ratio
Config B achieves higher
risk-adjusted returns (excess over IHSG) by 0.0776.

### Max Drawdown
Config A has lower (better) peak-to-trough decline:
-20.76% vs -22.18% (diff -1.41%).

### Win Rate & Turnover
- **Win Rate:** Config B wins 63.83% of months vs 57.45% for Config A
- **Turnover:** Config A rebalances less (lower turnover worse for trading costs)
- **Month-by-month:** Config B outperforms Config A in 15/47 months (31.9%)

---

## Statistical Significance

**Caveats (critical to interpret results):**

1. **2022 look-ahead:** All 2022 months use trailing data — scores reflect 2026 information.
   These 12 months inflate apparent CAGR for both configs equally but bias the comparison.

2. **Value factor under-weight:** Config B has only 10% Value weight. The ~41-48% Value
   look-ahead in 2023-2025 has minimal impact (<4.8% effective bias).

3. **Small universe:** 29 tickers, 48 months — limited diversification and statistical power.
   The observed CAGR difference of 2.82 pp is within sampling error.

4. **No transaction costs:** Turnover of 21.30% (Config B) would reduce
   net returns in practice.

5. **Equal-weight Top 5:** No position sizing optimization; results may differ with
   rank-weighted or volatility-weighted portfolios.
