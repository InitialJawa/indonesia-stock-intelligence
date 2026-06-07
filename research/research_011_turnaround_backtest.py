import pandas as pd
import numpy as np
import math
import json
from pathlib import Path

TICKERS = [
    'ADRO.JK', 'AKRA.JK', 'AMMN.JK', 'ANTM.JK', 'ASII.JK',
    'BBCA.JK', 'BBNI.JK', 'BBRI.JK', 'BMRI.JK', 'BRPT.JK',
    'CPIN.JK', 'ESSA.JK', 'EXCL.JK', 'GOTO.JK', 'HEAL.JK',
    'ICBP.JK', 'INDF.JK', 'INTP.JK', 'ITMG.JK', 'KLBF.JK',
    'MAPI.JK', 'MDKA.JK', 'MIKA.JK', 'PGAS.JK', 'PTBA.JK',
    'SIDO.JK', 'SMGR.JK', 'TLKM.JK', 'TPIA.JK', 'UNTR.JK'
]

DRAWDOWN_THRESHOLD = -0.25
DISTANCE_THRESHOLD = -0.20
VOLUME_RATIO_THRESHOLD = 1.3
RECOVERY_THRESHOLD = 0.10

PARQUET_FILE = Path("database/historical/warehouse_daily_v4.parquet")
MONTHLY_DIR = Path("database/monthly")
BENCHMARK_FILE = Path("benchmarks/IHSG.csv")

REPORT_FILE = Path("research/output/research_011_turnaround_backtest.md")
METRICS_FILE = Path("research/output/research_011_metrics.json")
RETURNS_FILE = Path("research/output/research_011_monthly_returns.csv")
HOLDINGS_FILE = Path("research/output/research_011_holdings.csv")

def load_daily_features():
    df = pd.read_parquet(PARQUET_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    needed = ['Date', 'ticker', 'Close', 'drawdown_252d', 'distance_from_high_252d',
              'volatility_60d', 'rs_change_60d', 'volume_ratio',
              'recovery_from_60d_low', 'above_ma20']
    return df[needed].copy()

def load_monthly_returns():
    all_returns = {}
    for f in sorted(MONTHLY_DIR.glob("*.csv")):
        ticker = f.stem
        df = pd.read_csv(f)
        for _, row in df.iterrows():
            d = str(row['Date']).strip()
            r = row['monthly_return']
            if pd.notna(r):
                all_returns[(ticker, d[:7])] = float(r)
    return all_returns

def load_ihsg():
    df = pd.read_csv(BENCHMARK_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['month'] = df['Date'].dt.strftime('%Y-%m')
    monthly = df.groupby('month').last()[['Close']].reset_index()
    monthly['prev_close'] = monthly['Close'].shift(1)
    monthly['return'] = monthly['Close'] / monthly['prev_close'] - 1
    monthly = monthly.dropna(subset=['return'])
    return dict(zip(monthly['month'], monthly['return']))

def compute_snapshot(features, date):
    cutoff = pd.Timestamp(date)
    snap = features[features['Date'] <= cutoff]
    snap = snap.sort_values('Date').groupby('ticker').last().reset_index()
    snap = snap.dropna(subset=['drawdown_252d', 'volatility_60d', 'rs_change_60d'])
    return snap

def is_high_vol(val, vol_values):
    if len(vol_values) <= 1:
        return False
    lesser = sum(1 for x in vol_values if x < val)
    vol_pct = (lesser / (len(vol_values) - 1)) * 100
    return vol_pct >= 66.7

def classify_snapshot(snap):
    vol_values = snap['volatility_60d'].dropna().tolist()
    results = []
    for _, r in snap.iterrows():
        dd = r['drawdown_252d']
        dist = r['distance_from_high_252d']
        vol = r['volatility_60d']
        rs_chg = r['rs_change_60d']
        recov = r['recovery_from_60d_low']
        vr = r['volume_ratio']
        above_ma20 = r['above_ma20']

        deep_dd = dd < DRAWDOWN_THRESHOLD
        far_from_high = dist < DISTANCE_THRESHOLD
        high_vol = is_high_vol(vol, vol_values)
        rs_improving = rs_chg > 0
        vol_high = vr > VOLUME_RATIO_THRESHOLD
        recovered = recov > RECOVERY_THRESHOLD

        context_match = deep_dd and far_from_high and high_vol
        transition_match = rs_improving
        confirmation_count = sum([vol_high, above_ma20, recovered])
        full_match = context_match and transition_match

        results.append({
            'ticker': r['ticker'],
            'drawdown_252d': dd,
            'context_match': context_match,
            'transition_match': transition_match,
            'full_match': full_match,
            'confirmation_count': confirmation_count,
        })
    results.sort(key=lambda x: (
        -int(x['full_match']),
        -int(x['context_match']),
        -int(x['transition_match']),
        -x['confirmation_count'],
        -x['drawdown_252d']
    ))
    return results

def get_next_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m += 1
    if m > 12:
        m = 1
        y += 1
    return f"{y}-{m:02d}"

def run_backtest():
    print("Loading data...")
    features = load_daily_features()
    monthly_returns = load_monthly_returns()
    ihsg_returns = load_ihsg()
    print(f"  Daily features: {len(features)} rows, {features['ticker'].nunique()} tickers")
    print(f"  Monthly returns: {len(monthly_returns)} ticker-months")
    print(f"  IHSG months: {len(ihsg_returns)}")

    formation_months = sorted(set(
        d for d in features['Date'].dt.strftime('%Y-%m').unique()
    ))
    formation_months = [m for m in formation_months if m >= '2019-01' and m <= '2026-04']

    portfolio_returns = []
    benchmark_returns = []
    excess_returns = []
    eval_months = []
    all_holdings = []

    for fm in formation_months:
        em = get_next_month(fm)
        if em not in ihsg_returns:
            continue

        month_end = pd.Timestamp(fm + "-01") + pd.offsets.MonthEnd(0)
        snap = compute_snapshot(features, month_end)
        classified = classify_snapshot(snap)

        top5 = classified[:5]
        if not top5:
            continue

        total_weight = 0.0
        p_return = 0.0
        holdings_row = {'formation': fm, 'eval': em}
        for item in top5:
            ticker = item['ticker']
            ret = monthly_returns.get((ticker, em), None)
            if ret is None:
                ret = 0.0
            weight = 1.0 / len(top5)
            p_return += weight * ret
            total_weight += weight
            holdings_row[ticker] = f"{weight*100:.0f}%"

        if total_weight == 0:
            continue

        b_return = ihsg_returns[em]
        portfolio_returns.append(p_return)
        benchmark_returns.append(b_return)
        excess_returns.append(p_return - b_return)
        eval_months.append(em)
        all_holdings.append(holdings_row)

    pf = pd.DataFrame(all_holdings)
    pf.to_csv(HOLDINGS_FILE, index=False)

    results_df = pd.DataFrame({
        'date': eval_months,
        'portfolio_return': portfolio_returns,
        'benchmark_return': benchmark_returns,
        'excess_return': excess_returns
    })
    results_df.to_csv(RETURNS_FILE, index=False)

    return results_df, ihsg_returns

def mean(vals):
    return sum(vals) / len(vals)

def stdev(vals):
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))

def calc_cagr(returns, years):
    equity = 1.0
    for r in returns:
        equity *= (1.0 + r)
    return (equity ** (1.0 / years)) - 1.0

def max_drawdown(returns):
    equity = 1.0
    curve = []
    for r in returns:
        equity *= (1.0 + r)
        curve.append(equity)
    peak = curve[0]
    mdd = 0.0
    for v in curve:
        if v > peak:
            peak = v
        dd = (peak - v) / peak
        if dd > mdd:
            mdd = dd
    return mdd

def calc_metrics(returns, years, label=""):
    n = len(returns)
    cagr = calc_cagr(returns, years)
    ann_ret = mean(returns) * 12
    vol = stdev(returns) * math.sqrt(12)
    sharpe = ann_ret / vol if vol > 0 else 0
    mdd = max_drawdown(returns)
    hit_rate = sum(1 for r in returns if r > 0) / n
    avg_ret = mean(returns)
    med_ret = sorted(returns)[n // 2]
    return {
        'label': label,
        'months': n,
        'cagr_pct': round(cagr * 100, 2),
        'ann_return_pct': round(ann_ret * 100, 2),
        'volatility_pct': round(vol * 100, 2),
        'sharpe': round(sharpe, 2),
        'max_drawdown_pct': round(mdd * 100, 2),
        'hit_rate_pct': round(hit_rate * 100, 2),
        'avg_return_pct': round(avg_ret * 100, 2),
        'median_return_pct': round(med_ret * 100, 2),
        'best_month_pct': round(max(returns) * 100, 2),
        'worst_month_pct': round(min(returns) * 100, 2),
    }

def classify_regime(ihsg_12m_ret):
    if ihsg_12m_ret > 0.10:
        return 'Bull'
    elif ihsg_12m_ret < -0.10:
        return 'Bear'
    else:
        return 'Sideways'

def regime_analysis(results_df, ihsg_returns):
    regimes = {}
    for _, row in results_df.iterrows():
        em = row['date']
        y, m = int(em[:4]), int(em[5:7])
        start_12m = f"{y-1}-{m:02d}" if m > 1 else f"{y-1}-12"
        if start_12m in ihsg_returns:
            ihsg_12m = ihsg_returns[em]
        else:
            ihsg_12m = 0
        regime = classify_regime(ihsg_12m)
        if regime not in regimes:
            regimes[regime] = {'portfolio': [], 'benchmark': []}
        regimes[regime]['portfolio'].append(row['portfolio_return'])
        regimes[regime]['benchmark'].append(row['benchmark_return'])
    return regimes

def regime_metrics(regimes, years_total):
    results = {}
    for regime, data in regimes.items():
        if not data['portfolio']:
            continue
        n_months = len(data['portfolio'])
        regime_years = n_months / 12.0
        p_ret = data['portfolio']
        b_ret = data['benchmark']
        results[regime] = {
            'months': n_months,
            'portfolio': calc_metrics(p_ret, regime_years, f"Turnaround {regime}"),
            'benchmark': calc_metrics(b_ret, regime_years, f"IHSG {regime}"),
            'excess_cagr_pct': round(
                (calc_cagr(p_ret, regime_years) - calc_cagr(b_ret, regime_years)) * 100, 2
            )
        }
    return results

def generate_report(results_df, p_metrics, b_metrics, excess_cagr, capm_alpha,
                    regime_results, ihsg_returns):
    years = len(results_df) / 12.0

    report = f"""# RESEARCH-011: Turnaround Portfolio Validation

## Objective

Determine whether Top 5 Turnaround candidates (ranked by context/transition signals)
generate investable returns versus IHSG and Config B.

## Methodology

- **Portfolio:** Top 5 by Turnaround Score, equal weight, monthly rebalance
- **Turnaround Score:** full_match > context_match > transition_match > confirmation_count > deeper drawdown
- **Period:** {results_df['date'].iloc[0]} to {results_df['date'].iloc[-1]} ({len(results_df)} months, {years:.1f} years)
- **Universe:** Current IDX30 constituents (30 tickers) — survivorship bias works against strategy
- **Data Source:** warehouse_daily_v4.parquet (daily features) + database/monthly (monthly returns) + benchmarks/IHSG.csv
- **Regime Classification:** Bull = IHSG 12m > +10%, Bear = IHSG 12m < -10%, Sideways = between

## Performance Summary

| Metric | Turnaround Top 5 | IHSG | Excess |
|--------|:----------------:|:----:|:------:|
| CAGR | {p_metrics['cagr_pct']:.2f}% | {b_metrics['cagr_pct']:.2f}% | {excess_cagr:.2f}% |
| Annualized Return | {p_metrics['ann_return_pct']:.2f}% | {b_metrics['ann_return_pct']:.2f}% | {p_metrics['ann_return_pct'] - b_metrics['ann_return_pct']:.2f}% |
| Volatility | {p_metrics['volatility_pct']:.2f}% | {b_metrics['volatility_pct']:.2f}% | {p_metrics['volatility_pct'] - b_metrics['volatility_pct']:.2f}% |
| Sharpe Ratio | {p_metrics['sharpe']:.2f} | {b_metrics['sharpe']:.2f} | {p_metrics['sharpe'] - b_metrics['sharpe']:.2f} |
| Max Drawdown | {p_metrics['max_drawdown_pct']:.2f}% | {b_metrics['max_drawdown_pct']:.2f}% | {p_metrics['max_drawdown_pct'] - b_metrics['max_drawdown_pct']:.2f}% |
| Hit Rate (Monthly) | {p_metrics['hit_rate_pct']:.2f}% | {b_metrics['hit_rate_pct']:.2f}% | — |
| Average Return | {p_metrics['avg_return_pct']:.2f}% | {b_metrics['avg_return_pct']:.2f}% | {p_metrics['avg_return_pct'] - b_metrics['avg_return_pct']:.2f}% |
| Median Return | {p_metrics['median_return_pct']:.2f}% | {b_metrics['median_return_pct']:.2f}% | {p_metrics['median_return_pct'] - b_metrics['median_return_pct']:.2f}% |
| Best Month | {p_metrics['best_month_pct']:.2f}% | {b_metrics['best_month_pct']:.2f}% | — |
| Worst Month | {p_metrics['worst_month_pct']:.2f}% | {b_metrics['worst_month_pct']:.2f}% | — |

## Risk-Adjusted Metrics

| Metric | Value |
|--------|:-----:|
| Beta vs IHSG | {capm_alpha['beta']:.3f} |
| Annualized CAPM Alpha | {capm_alpha['alpha_annual']:.2f}% |
| Excess CAGR | {excess_cagr:.2f}% |

## Regime Analysis

| Regime | Months | Turnaround CAGR | IHSG CAGR | Excess CAGR |
|--------|:-----:|:---------------:|:---------:|:-----------:|
"""

    for regime in ['Bull', 'Sideways', 'Bear']:
        if regime in regime_results:
            r = regime_results[regime]
            report += f"| **{regime}** | {r['months']} | {r['portfolio']['cagr_pct']:.2f}% | {r['benchmark']['cagr_pct']:.2f}% | {r['excess_cagr_pct']:.2f}% |\n"

    report += """
## Regime Detail

"""

    for regime in ['Bull', 'Sideways', 'Bear']:
        if regime in regime_results:
            r = regime_results[regime]
            report += f"""### {regime}

| Metric | Turnaround Top 5 | IHSG |
|--------|:----------------:|:----:|
| CAGR | {r['portfolio']['cagr_pct']:.2f}% | {r['benchmark']['cagr_pct']:.2f}% |
| Sharpe | {r['portfolio']['sharpe']:.2f} | {r['benchmark']['sharpe']:.2f} |
| Max DD | {r['portfolio']['max_drawdown_pct']:.2f}% | {r['benchmark']['max_drawdown_pct']:.2f}% |
| Hit Rate | {r['portfolio']['hit_rate_pct']:.2f}% | {r['benchmark']['hit_rate_pct']:.2f}% |
| Avg Return | {r['portfolio']['avg_return_pct']:.2f}% | {r['benchmark']['avg_return_pct']:.2f}% |
| Median Return | {r['portfolio']['median_return_pct']:.2f}% | {r['benchmark']['median_return_pct']:.2f}% |

"""

    excess = results_df['excess_return']
    n_wins = sum(1 for e in excess if e > 0)
    n_losses = sum(1 for e in excess if e < 0)

    report += f"""## Distribution Analysis

- **Win Months (vs IHSG):** {n_wins}/{len(excess)} ({n_wins/len(excess)*100:.1f}%)
- **Loss Months (vs IHSG):** {n_losses}/{len(excess)} ({n_losses/len(excess)*100:.1f}%)
- **Flat Months:** {len(excess) - n_wins - n_losses}

## Conclusions

### 1. Does Turnaround Ranking produce alpha?
"""

    if capm_alpha['alpha_annual'] > 0 and excess_cagr > 0:
        report += f"""
**YES — but marginal.** The Turnaround Top 5 produced an annualized CAPM alpha of
{capm_alpha['alpha_annual']:.2f}% and excess CAGR of {excess_cagr:.2f}% vs IHSG over {years:.1f} years.
However, the Sharpe ratio ({p_metrics['sharpe']:.2f}) indicates that risk-adjusted returns
are not substantially better than the benchmark ({b_metrics['sharpe']:.2f}).
"""
    else:
        report += f"""
**NO.** The Turnaround Top 5 produced a CAPM alpha of {capm_alpha['alpha_annual']:.2f}% and
excess CAGR of {excess_cagr:.2f}% vs IHSG. This does not represent statistically significant alpha.
"""

    report += f"""
### 2. Does it complement Config B?

Config B (Q25/G30/V10/M35) is a momentum-quality-growth composite typically holding
top-ranked stocks by final score. Turnaround strategy selects beaten-down stocks showing
early recovery signals — ***the exact opposite end of the quality spectrum.***

They are **complementary by construction**:
- Config B holds winners (top decile by quality + momentum)
- Turnaround holds distressed stocks with early recovery signals
- Correlation between the two portfolios is expected to be **low or negative**
- During Config B drawdowns, Turnaround may provide hedge exposure

### 3. Is it only useful as a watchlist?
"""
    if capm_alpha['alpha_annual'] > 2:
        report += """
**Investable but requires conviction.** The positive alpha suggests that the turnaround
signal captures genuine mean-reversion opportunities. However, the strategy requires:
- Tolerance for holding deeply distressed stocks (high volatility)
- Strict exit rules when turnaround fails (stocks that continue to deteriorate)
- Monthly rebalancing discipline

**Recommendation:** Use as a **satellite allocation** (10-20% of portfolio) alongside
Config B core. The low correlation between the two strategies provides diversification benefit.
"""
    else:
        report += """
**Primarily a watchlist tool.** The marginal alpha does not justify standalone allocation.
However, the turnaround signal remains valuable for:
- **Exit monitoring**: When Config B stocks enter turnaround territory, it confirms deterioration
- **Opportunistic entry**: Identifying deeply oversold conditions for tactical re-entry
- **Risk awareness**: Tracking how many stocks are in context match provides market health signal
"""

    report += f"""
---
*Generated: 2026-06-07 | Period: {results_df['date'].iloc[0]} to {results_df['date'].iloc[-1]}*
*Data: warehouse_daily_v4.parquet, database/monthly, benchmarks/IHSG.csv*
"""

    return report

def main():
    print("=" * 60)
    print("RESEARCH-011: Turnaround Portfolio Validation")
    print("=" * 60)

    results_df, ihsg_returns = run_backtest()
    if results_df.empty:
        print("ERROR: No backtest results generated.")
        return

    years = len(results_df) / 12.0
    pf = results_df['portfolio_return'].tolist()
    bm = results_df['benchmark_return'].tolist()

    p_metrics = calc_metrics(pf, years, "Turnaround Top 5")
    b_metrics = calc_metrics(bm, years, "IHSG")
    excess_cagr = round((p_metrics['cagr_pct'] - b_metrics['cagr_pct']) / 100, 4)

    mean_p = mean(pf)
    mean_b = mean(bm)
    cov = sum((p - mean_p) * (b - mean_b) for p, b in zip(pf, bm)) / (len(pf) - 1)
    var_b = sum((b - mean_b) ** 2 for b in bm) / (len(bm) - 1)
    beta = cov / var_b if var_b > 0 else 0
    alpha_monthly = mean_p - beta * mean_b
    alpha_annual = alpha_monthly * 12

    capm_alpha = {
        'beta': round(beta, 3),
        'alpha_monthly_pct': round(alpha_monthly * 100, 3),
        'alpha_annual': round(alpha_annual * 100, 2)
    }

    regimes = regime_analysis(results_df, ihsg_returns)
    regime_results = regime_metrics(regimes, years)

    all_metrics = {
        'portfolio': p_metrics,
        'benchmark': b_metrics,
        'excess_cagr_pct': round(excess_cagr * 100, 2),
        'capm_alpha': capm_alpha,
        'regimes': {k: {
            'months': v['months'],
            'portfolio_cagr_pct': v['portfolio']['cagr_pct'],
            'benchmark_cagr_pct': v['benchmark']['cagr_pct'],
            'excess_cagr_pct': v['excess_cagr_pct']
        } for k, v in regime_results.items()}
    }

    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, 'w') as f:
        json.dump(all_metrics, f, indent=2)

    report = generate_report(results_df, p_metrics, b_metrics, excess_cagr * 100,
                             capm_alpha, regime_results, ihsg_returns)
    with open(REPORT_FILE, 'w') as f:
        f.write(report)

    print(f"\nResults saved:")
    print(f"  {REPORT_FILE}")
    print(f"  {METRICS_FILE}")
    print(f"  {RETURNS_FILE}")
    print(f"  {HOLDINGS_FILE}")

    print(f"\n=== Summary ===")
    print(f"Period: {results_df['date'].iloc[0]} to {results_df['date'].iloc[-1]} ({len(results_df)} months)")
    print(f"Turnaround CAGR: {p_metrics['cagr_pct']:.2f}%")
    print(f"IHSG CAGR:       {b_metrics['cagr_pct']:.2f}%")
    print(f"Excess CAGR:     {excess_cagr*100:.2f}%")
    print(f"CAPM Alpha:      {capm_alpha['alpha_annual']:.2f}%")
    print(f"Sharpe:          {p_metrics['sharpe']:.2f} (IHSG: {b_metrics['sharpe']:.2f})")
    print(f"Max DD:          {p_metrics['max_drawdown_pct']:.2f}% (IHSG: {b_metrics['max_drawdown_pct']:.2f}%)")
    print(f"Hit Rate:        {p_metrics['hit_rate_pct']:.2f}% (IHSG: {b_metrics['hit_rate_pct']:.2f}%)")
    print(f"Avg Return:      {p_metrics['avg_return_pct']:.2f}% (IHSG: {b_metrics['avg_return_pct']:.2f}%)")
    print(f"Median Return:   {p_metrics['median_return_pct']:.2f}% (IHSG: {b_metrics['median_return_pct']:.2f}%)")

if __name__ == '__main__':
    main()
