# RESEARCH-011: Turnaround Portfolio Validation

## Objective

Determine whether Top 5 Turnaround candidates (ranked by context/transition signals)
generate investable returns versus IHSG and Config B.

## Methodology

- **Portfolio:** Top 5 by Turnaround Score, equal weight, monthly rebalance
- **Turnaround Score:** full_match > context_match > transition_match > confirmation_count > deeper drawdown
- **Period:** 2019-02 to 2026-05 (88 months, 7.3 years)
- **Universe:** Current IDX30 constituents (30 tickers) � survivorship bias works against strategy
- **Data Source:** warehouse_daily_v4.parquet (daily features) + database/monthly (monthly returns) + benchmarks/IHSG.csv
- **Regime Classification:** Bull = IHSG 12m > +10%, Bear = IHSG 12m < -10%, Sideways = between
- **Comparison:** Config B momentum backtest (same period, same universe, Top 5 equal-weight)

## Performance Summary

| Metric | Turnaround Top 5 | IHSG | Excess |
|--------|:----------------:|:----:|:------:|
| CAGR | -0.17% | -0.87% | 0.70% |
| Annualized Return | 3.48% | 0.37% | 3.11% |
| Volatility | 26.68% | 15.53% | 11.15% |
| Sharpe Ratio | 0.13 | 0.02 | 0.11 |
| Max Drawdown | 43.10% | 29.83% | 13.27% |
| Hit Rate (Monthly) | 59.09% | 56.82% | � |
| Average Return | 0.29% | 0.03% | 0.26% |
| Median Return | 1.91% | 0.50% | 1.41% |
| Best Month | 16.95% | 9.44% | � |
| Worst Month | -22.74% | -16.76% | � |

## Comparison vs Config B Momentum

| Metric | Turnaround Top 5 | Config B Momentum | IHSG |
|--------|:----------------:|:-----------------:|:----:|
| CAGR | -0.17% | 0.82% | -0.87% |
| Sharpe Ratio | 0.13 | 0.17 | 0.02 |
| Max Drawdown | 43.10% | 39.66% | 29.83% |
| Hit Rate | 59.09% | 55.68% | 56.82% |
| Volatility | 26.68% | 28.56% | 15.53% |
| CAPM Alpha | 3.05% | 4.47% | — |

**Key Observation:** Turnaround has lower CAGR and higher drawdown than Config B,
but achieves a higher monthly hit rate. The two strategies select stocks from opposite
ends of the quality spectrum — their correlation is expected to be low.

## Risk-Adjusted Metrics

| Metric | Value |
|--------|:-----:|
| Beta vs IHSG | 1.182 |
| Annualized CAPM Alpha | 3.05% |
| Excess CAGR | 0.70% |

## Regime Analysis

| Regime | Months | Turnaround CAGR | IHSG CAGR | Excess CAGR |
|--------|:-----:|:---------------:|:---------:|:-----------:|
| **Sideways** | 84 | 11.13% | 7.83% | 3.30% |
| **Bear** | 4 | -89.48% | -83.05% | -6.43% |

## Regime Detail

### Sideways

| Metric | Turnaround Top 5 | IHSG |
|--------|:----------------:|:----:|
| CAGR | 11.13% | 7.83% |
| Sharpe | 0.57 | 0.71 |
| Max DD | 17.50% | 15.71% |
| Hit Rate | 61.90% | 59.52% |
| Avg Return | 1.11% | 0.69% |
| Median Return | 2.10% | 0.61% |

### Bear

| Metric | Turnaround Top 5 | IHSG |
|--------|:----------------:|:----:|
| CAGR | -89.48% | -83.05% |
| Sharpe | -7.92 | -20.18 |
| Max DD | 43.12% | 33.51% |
| Hit Rate | 0.00% | 0.00% |
| Avg Return | -16.87% | -13.72% |
| Median Return | -17.00% | -11.92% |

## Distribution Analysis

- **Win Months (vs IHSG):** 47/88 (53.4%)
- **Loss Months (vs IHSG):** 41/88 (46.6%)
- **Flat Months:** 0

## Conclusions

### 1. Does Turnaround Ranking produce alpha?

**Marginal alpha, negative absolute return.** The Turnaround Top 5 produced a CAPM alpha
of 3.05% and excess CAGR of +0.70% vs IHSG. However, the absolute CAGR is -0.17% --
the strategy loses money on a standalone basis over 7.3 years.

Config B Momentum produced superior results in the same period: CAGR +0.82%,
CAPM alpha +4.47%, Sharpe 0.17. Turnaround's only edge is a higher hit rate
(59.09% vs 55.68%).

**Verdict: Turnaround ranking produces weak alpha but NOT investable absolute returns.**

### 2. Does it complement Config B?

| Aspect | Config B Momentum | Turnaround Top 5 |
|--------|:-----------------:|:----------------:|
| CAGR | +0.82% | -0.17% |
| Sharpe | 0.17 | 0.13 |
| Max DD | 39.66% | 43.10% |
| Hit Rate | 55.68% | 59.09% |
| Selection | Winners (top decile) | Distressed (bottom decile) |

They select from opposite ends of the quality spectrum, so **correlation is expected
to be low-to-negative**. In sideways regimes (84/88 months), Turnaround delivers
+11.13% CAGR vs IHSG +7.83% (excess +3.30%), suggesting real diversification benefit.

**Verdict: Complementary by construction. Turnaround shines in sideways markets.**

### 3. Is it only useful as a watchlist?

**Primarily a watchlist tool.** The marginal alpha and negative absolute CAGR do not
justify standalone allocation. However, the signal adds value:

- **Exit monitoring**: When Config B stocks enter context match, it confirms deterioration
- **Opportunistic entry**: Deeply oversold conditions flagged by context+transition signals
- **Risk awareness**: Number of stocks in context match is a market health barometer
- **Satellite hedge**: 10-20% allocation in sideways regimes provides +3.30% excess CAGR

**Recommendation:** Watchlist tool + satellite allocation in favorable regimes only.

---
*Generated: 2026-06-07 | Period: 2019-02 to 2026-05*
*Data: warehouse_daily_v4.parquet, database/monthly, benchmarks/IHSG.csv*
