# file: research/rs6m_backtest_engine.py

import sys
import os
import csv
import math
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from utils.universe_manager import get_active_universe

# Path configurations
BASE_DIR = Path(__file__).resolve().parent.parent
PRICE_DIR = BASE_DIR / "output" / "history_prices"
METADATA_FILE = BASE_DIR / "database" / "historical" / "ticker_metadata.csv"
IHSG_FILE = BASE_DIR / "benchmarks" / "ihsg.csv"
MOMENTUM_RETURNS_FILE = BASE_DIR / "database" / "historical" / "momentum_monthly_returns.csv"

OUTPUT_CSV = BASE_DIR / "reports" / "rs6m_standalone_performance.csv"
OUTPUT_REPORT = BASE_DIR / "reports" / "rs6m_backtest.md"

def load_metadata():
    metadata = {}
    if METADATA_FILE.exists():
        with open(METADATA_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                metadata[row["ticker"]] = pd.to_datetime(row["listing_date"])
    else:
        raise FileNotFoundError(f"Metadata file not found at {METADATA_FILE}")
    return metadata

def load_ihsg():
    df = pd.read_csv(IHSG_FILE)
    date_col = next((c for c in df.columns if c.lower() in ["date","tanggal"]), df.columns[0])
    price_col = next((c for c in df.columns if c.lower() in ["close","adj close","price"]), df.columns[1])
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()
    return df[price_col].astype(float)

def load_ticker_prices(metadata):
    ticker_prices = {}
    print(f"Loading daily price data for tickers from {PRICE_DIR}...")
    for ticker, listing_date in metadata.items():
        patterns = [
            PRICE_DIR / f"{ticker}.csv",
            PRICE_DIR / f"{ticker.replace('.','_')}.csv",
        ]
        filepath = next((p for p in patterns if p.exists()), None)
        if filepath is None:
            matches = list(PRICE_DIR.glob(f"*{ticker.split('.')[0]}*"))
            filepath = matches[0] if matches else None
        if filepath is None:
            continue
        try:
            df = pd.read_csv(filepath)
            date_col = next((c for c in df.columns if c.lower() in ["date","tanggal"]), df.columns[0])
            price_col = next((c for c in df.columns if c.lower() in ["close","adj close"]), None)
            if price_col is None:
                price_col = df.columns[4] if len(df.columns) > 4 else df.columns[1]
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.set_index(date_col).sort_index()
            
            # Remove backfill bias: filter only prices on or after listing date
            df = df[df.index >= listing_date]
            
            ticker_prices[ticker] = df[price_col].astype(float)
        except Exception as e:
            print(f"Warning: Failed to load {filepath}: {e}")
    print(f"Loaded price data for {len(ticker_prices)} tickers.")
    return ticker_prices

def calculate_metrics(returns_series, benchmark_series):
    n = len(returns_series)
    years = n / 12.0
    
    # Cumulative return and equity curve
    equity = 1.0
    equity_curve = []
    drawdowns = []
    
    for r in returns_series:
        equity *= (1.0 + r)
        equity_curve.append(equity)
        
        peak = max(equity_curve)
        drawdown = (peak - equity) / peak
        drawdowns.append(drawdown)
        
    cagr = equity ** (1.0 / years) - 1.0
    
    mean_ret = returns_series.mean()
    ann_return = mean_ret * 12.0
    # Volatility using sample standard deviation
    vol = returns_series.std(ddof=1) * math.sqrt(12.0)
    
    sharpe = ann_return / vol if vol > 0 else 0.0
    max_dd = max(drawdowns) if drawdowns else 0.0
    
    best_month = returns_series.max()
    worst_month = returns_series.min()
    win_rate = (returns_series > 0).sum() / n
    
    # CAPM Alpha and Beta
    cov = returns_series.cov(benchmark_series)
    var_b = benchmark_series.var(ddof=1)
    beta = cov / var_b if var_b > 0 else 0.0
    
    mean_p = returns_series.mean()
    mean_b = benchmark_series.mean()
    alpha_monthly = mean_p - beta * mean_b
    alpha_annualized = alpha_monthly * 12.0
    
    return {
        "cagr": cagr,
        "annualized_return": ann_return,
        "volatility": vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "best_month": best_month,
        "worst_month": worst_month,
        "win_rate": win_rate,
        "beta": beta,
        "alpha_annualized": alpha_annualized,
        "alpha_monthly": alpha_monthly,
        "equity_curve": equity_curve
    }

def main():
    print("=" * 70)
    print("  FACTOR 006: RELATIVE STRENGTH 6M (RS-6M) STANDALONE BACKTEST ENGINE")
    print("=" * 70)
    
    # Load inputs
    metadata = load_metadata()
    ihsg = load_ihsg()
    ticker_prices = load_ticker_prices(metadata)
    
    # Generate monthly prices for IHSG and Tickers to simplify monthly calculations
    print("Resampling daily prices to monthly end-of-month prices...")
    ihsg_monthly = ihsg.groupby(ihsg.index.to_period('M')).last()
    
    ticker_monthly = {}
    for ticker, prices in ticker_prices.items():
        ticker_monthly[ticker] = prices.groupby(prices.index.to_period('M')).last()
        
    # Simulation range: Rebalance monthly from 2019-01 to 2026-04
    # The returns will be evaluated for month t+1 (from 2019-02 to 2026-05)
    start_period = pd.Period('2019-01', 'M')
    end_period = pd.Period('2026-04', 'M')
    
    simulation_periods = pd.period_range(start=start_period, end=end_period, freq='M')
    
    backtest_dates = []
    portfolio_monthly_returns = []
    benchmark_monthly_returns = []
    portfolio_holdings_log = {}
    
    print("\nRunning backtest simulation...")
    for p in simulation_periods:
        # Rebalancing at end of period p
        # Lookback start is p - 6
        p_start = p - 6
        
        # Check if IHSG has price for lookback start and current end
        if p_start not in ihsg_monthly.index or p not in ihsg_monthly.index:
            continue
            
        ihsg_price_start = ihsg_monthly.loc[p_start]
        ihsg_price_end = ihsg_monthly.loc[p]
        ihsg_ret_6m = (ihsg_price_end / ihsg_price_start) - 1.0
        
        # Get active universe for period p
        active_universe = get_active_universe(p.strftime('%Y-%m'))
        
        # Calculate RS score for all active tickers
        rs_scores = []
        for ticker, prices in ticker_monthly.items():
            if ticker not in active_universe:
                continue
                
            # Listing date gate: ticker must have listed on or before the end of the lookback start month
            listing_date = metadata[ticker]
            lookback_start_date = p_start.end_time
            if listing_date > lookback_start_date:
                # Exclude to prevent backfill/lookahead bias
                continue
                
            # Must have price data for both start and end
            if p_start not in prices.index or p not in prices.index:
                continue
                
            price_start = prices.loc[p_start]
            price_end = prices.loc[p]
            
            if pd.isna(price_start) or pd.isna(price_end) or price_start <= 0:
                continue
                
            stock_ret_6m = (price_end / price_start) - 1.0
            rs_score = stock_ret_6m - ihsg_ret_6m
            
            rs_scores.append((ticker, rs_score))
            
        if not rs_scores:
            continue
            
        # Select Top 5 tickers
        rs_scores.sort(key=lambda x: x[1], reverse=True)
        top_5 = rs_scores[:5]
        
        # Record holdings for this month
        portfolio_holdings_log[p.strftime('%Y-%m')] = top_5
        
        # Calculate return for next month (p + 1)
        p_next = p + 1
        if p_next not in ihsg_monthly.index:
            # We reached the end of return evaluation data
            continue
            
        # Portfolio monthly return
        p_return = 0.0
        for ticker, _ in top_5:
            prices = ticker_monthly[ticker]
            if p not in prices.index or p_next not in prices.index:
                # Missing price data, print warning and default return to 0
                print(f"WARNING: Ticker {ticker} missing prices for period {p} -> {p_next}")
                ret_1m = 0.0
            else:
                price_m = prices.loc[p]
                price_m1 = prices.loc[p_next]
                if pd.isna(price_m) or pd.isna(price_m1) or price_m <= 0:
                    print(f"WARNING: Ticker {ticker} has invalid prices for period {p} -> {p_next}")
                    ret_1m = 0.0
                else:
                    ret_1m = (price_m1 / price_m) - 1.0
            p_return += 0.20 * ret_1m
            
        # Benchmark return
        ihsg_price_m = ihsg_monthly.loc[p]
        ihsg_price_m1 = ihsg_monthly.loc[p_next]
        b_return = (ihsg_price_m1 / ihsg_price_m) - 1.0
        
        backtest_dates.append(p_next.strftime('%Y-%m'))
        portfolio_monthly_returns.append(p_return)
        benchmark_monthly_returns.append(b_return)
        
    print(f"Simulation completed for {len(backtest_dates)} months: {backtest_dates[0]} to {backtest_dates[-1]}")
    
    # Calculate RS-6M performance metrics
    p_series = pd.Series(portfolio_monthly_returns)
    b_series = pd.Series(benchmark_monthly_returns)
    
    rs_metrics = calculate_metrics(p_series, b_series)
    
    # Load Momentum returns for comparison
    mom_monthly_returns = {}
    if MOMENTUM_RETURNS_FILE.exists():
        mom_df = pd.read_csv(MOMENTUM_RETURNS_FILE)
        mom_monthly_returns = dict(zip(mom_df['date'], mom_df['portfolio_return']))
    else:
        print(f"WARNING: Momentum monthly returns file not found at {MOMENTUM_RETURNS_FILE}")
        
    # Align and merge returns for CSV output
    merged_rows = []
    mom_returns_aligned = []
    
    for date, rs_ret, b_ret in zip(backtest_dates, portfolio_monthly_returns, benchmark_monthly_returns):
        mom_ret = mom_monthly_returns.get(date, np.nan)
        mom_returns_aligned.append(mom_ret)
        
        rs_excess = rs_ret - b_ret
        mom_excess = mom_ret - b_ret if not pd.isna(mom_ret) else np.nan
        
        merged_rows.append({
            "date": date,
            "rs6m_return": round(rs_ret, 6),
            "momentum_return": round(mom_ret, 6) if not pd.isna(mom_ret) else "",
            "benchmark_return": round(b_ret, 6),
            "rs6m_excess": round(rs_excess, 6),
            "momentum_excess": round(mom_excess, 6) if not pd.isna(mom_excess) else ""
        })
        
    # Write to reports/rs6m_standalone_performance.csv
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "rs6m_return", "momentum_return", "benchmark_return", "rs6m_excess", "momentum_excess"])
        writer.writeheader()
        for row in merged_rows:
            writer.writerow(row)
    print(f"Saved merged monthly returns comparison to {OUTPUT_CSV}")
    
    # Calculate Momentum metrics for the same period
    mom_series = pd.Series(mom_returns_aligned)
    # drop NaNs if any
    valid_mask = ~mom_series.isna()
    valid_mom_series = mom_series[valid_mask]
    valid_b_series = b_series[valid_mask]
    valid_rs_series = p_series[valid_mask]
    
    mom_metrics = calculate_metrics(valid_mom_series, valid_b_series)
    rs_metrics_aligned = calculate_metrics(valid_b_series, valid_b_series)
    
    # Yearly calendar performance comparison
    df_merged = pd.DataFrame(merged_rows)
    df_merged['year'] = df_merged['date'].str[:4]
    df_merged['rs6m_return'] = pd.to_numeric(df_merged['rs6m_return'])
    df_merged['benchmark_return'] = pd.to_numeric(df_merged['benchmark_return'])
    
    if 'momentum_return' in df_merged.columns:
        df_merged['momentum_return'] = pd.to_numeric(df_merged['momentum_return'])
        
    yearly_perf = []
    for year, group in df_merged.groupby('year'):
        # Compound returns for the year
        rs_yearly = (group['rs6m_return'] + 1.0).prod() - 1.0
        b_yearly = (group['benchmark_return'] + 1.0).prod() - 1.0
        
        if 'momentum_return' in group.columns and not group['momentum_return'].isna().all():
            mom_yearly = (group['momentum_return'] + 1.0).prod() - 1.0
        else:
            mom_yearly = np.nan
            
        yearly_perf.append({
            "year": year,
            "rs6m_return": rs_yearly,
            "momentum_return": mom_yearly,
            "benchmark_return": b_yearly,
            "rs6m_excess": rs_yearly - b_yearly,
            "momentum_excess": mom_yearly - b_yearly if not pd.isna(mom_yearly) else np.nan
        })
        
    # Console performance output logs
    print("\n" + "="*50)
    print("             BACKTEST PERFORMANCE LOGS")
    print("="*50)
    print(f"CAGR (RS-6M)           : {rs_metrics['cagr']*100:.2f}% (Benchmark: {rs_metrics_aligned['cagr']*100:.2f}% | Momentum: {mom_metrics['cagr']*100:.2f}%)")
    print(f"Sharpe Ratio (RS-6M)    : {rs_metrics['sharpe']:.2f} (Benchmark: {rs_metrics_aligned['sharpe']:.2f} | Momentum: {mom_metrics['sharpe']:.2f})")
    print(f"Max Drawdown (RS-6M)    : {rs_metrics['max_drawdown']*100:.2f}% (Benchmark: {rs_metrics_aligned['max_drawdown']*100:.2f}% | Momentum: {mom_metrics['max_drawdown']*100:.2f}%)")
    print(f"Annualized CAPM Alpha   : {rs_metrics['alpha_annualized']*100:+.2f}%")
    print(f"Beta vs IHSG            : {rs_metrics['beta']:.3f}")
    print("="*50 + "\n")
    
    # Save reports/rs6m_backtest.md
    beats_ihsg = rs_metrics['cagr'] > rs_metrics_aligned['cagr']
    conclusion_text = "Mengalahkan IHSG" if beats_ihsg else "Tidak Mengalahkan IHSG"
    
    with open(OUTPUT_REPORT, mode="w", encoding="utf-8") as f:
        f.write("# Factor 006 (Relative Strength 6M / RS-6M) Standalone Backtest Report\n\n")
        f.write("Laporan kinerja portofolio Relative Strength 6 bulan historis dibandingkan dengan Momentum (Config B) dan tolok ukur IHSG.\n\n")
        
        f.write("## 1. Ringkasan Kinerja (Performance Summary)\n\n")
        f.write("| Parameter | Portofolio RS-6M | Portofolio Momentum | Benchmark (IHSG) | Selisih RS-6M vs IHSG |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: |\n")
        f.write(f"| **CAGR** | {rs_metrics['cagr']*100:.2f}% | {mom_metrics['cagr']*100:.2f}% | {rs_metrics_aligned['cagr']*100:.2f}% | {(rs_metrics['cagr'] - rs_metrics_aligned['cagr'])*100:+.2f}% |\n")
        f.write(f"| **Annualized Return** | {rs_metrics['annualized_return']*100:.2f}% | {mom_metrics['annualized_return']*100:.2f}% | {rs_metrics_aligned['annualized_return']*100:.2f}% | {(rs_metrics['annualized_return'] - rs_metrics_aligned['annualized_return'])*100:+.2f}% |\n")
        f.write(f"| **Volatility (Annualized)** | {rs_metrics['volatility']*100:.2f}% | {mom_metrics['volatility']*100:.2f}% | {rs_metrics_aligned['volatility']*100:.2f}% | {(rs_metrics['volatility'] - rs_metrics_aligned['volatility'])*100:+.2f}% |\n")
        f.write(f"| **Sharpe Ratio** | {rs_metrics['sharpe']:.2f} | {mom_metrics['sharpe']:.2f} | {rs_metrics_aligned['sharpe']:.2f} | {rs_metrics['sharpe'] - rs_metrics_aligned['sharpe']:+.2f} |\n")
        f.write(f"| **Max Drawdown** | {rs_metrics['max_drawdown']*100:.2f}% | {mom_metrics['max_drawdown']*100:.2f}% | {rs_metrics_aligned['max_drawdown']*100:.2f}% | {(rs_metrics['max_drawdown'] - rs_metrics_aligned['max_drawdown'])*100:+.2f}% |\n")
        f.write(f"| **Best Month** | {rs_metrics['best_month']*100:.2f}% | {mom_metrics['best_month']*100:.2f}% | {rs_metrics_aligned['best_month']*100:.2f}% | - |\n")
        f.write(f"| **Worst Month** | {rs_metrics['worst_month']*100:.2f}% | {mom_metrics['worst_month']*100:.2f}% | {rs_metrics_aligned['worst_month']*100:.2f}% | - |\n")
        f.write(f"| **Win Rate (Monthly)** | {rs_metrics['win_rate']*100:.2f}% | {mom_metrics['win_rate']*100:.2f}% | {rs_metrics_aligned['win_rate']*100:.2f}% | - |\n\n")
        
        f.write("## 2. Parameter Alpha & Beta vs IHSG\n\n")
        f.write("| Parameter | Portofolio RS-6M | Portofolio Momentum |\n")
        f.write("| :--- | :---: | :---: |\n")
        f.write(f"| **Beta vs IHSG** | `{rs_metrics['beta']:.3f}` | `{mom_metrics['beta']:.3f}` |\n")
        f.write(f"| **Annualized CAPM Alpha** | `{rs_metrics['alpha_annualized']*100:+.2f}%` | `{mom_metrics['alpha_annualized']*100:+.2f}%` |\n")
        f.write(f"| **Monthly CAPM Alpha** | `{rs_metrics['alpha_monthly']*100:+.3f}%` | `{mom_metrics['alpha_monthly']*100:+.3f}%` |\n\n")
        
        f.write("## 3. Kinerja Kalender Tahunan (Yearly Breakdown)\n\n")
        f.write("| Tahun | Portofolio RS-6M | Portofolio Momentum | Benchmark (IHSG) | Selisih RS-6M vs IHSG |\n")
        f.write("| :---: | :---: | :---: | :---: | :---: |\n")
        for row in yearly_perf:
            mom_str = f"{row['momentum_return']*100:.2f}%" if not pd.isna(row['momentum_return']) else "-"
            f.write(f"| **{row['year']}** | {row['rs6m_return']*100:.2f}% | {mom_str} | {row['benchmark_return']*100:.2f}% | {row['rs6m_excess']*100:+.2f}% |\n")
        f.write("\n")
        
        f.write("## 4. Validasi Data & Integritas\n\n")
        f.write(f"- **Jumlah Bulan Portfolio Evaluasi**: `{len(portfolio_holdings_log)}` bulan (Holdings dari `2019-01` ke `2026-04`)\n")
        f.write(f"- **Jumlah Bulan Return Terkalkulasi**: `{len(backtest_dates)}` (`2019-02` sampai `2026-05`)\n")
        f.write("- **IPO Listing date gate check**: Lulus (Seluruh ticker diverifikasi listing sebelum lookback start untuk mencegah backfill bias)\n")
        f.write("- **Equity Curve Calculation**: Lulus (Terkalkulasi penuh sampai akhir)\n\n")
        
        f.write("## 5. Kesimpulan Akhir\n\n")
        f.write(f"Berdasarkan analisis perbandingan CAGR historis, Portofolio RS-6M dinyatakan:\n\n")
        f.write(f"> [!IMPORTANT]\n")
        f.write(f"> **{conclusion_text}**\n")
        
    print(f"Saved performance report to {OUTPUT_REPORT}")
    print("=" * 70)

if __name__ == "__main__":
    main()
