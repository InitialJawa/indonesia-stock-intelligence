import pandas as pd
import numpy as np
import math
from pathlib import Path

MONTH_DIR = Path("database/monthly")
IHSG_FILE = Path("benchmarks/ihsg_monthly.csv")

# Portfolios
portfolio_a = ["ADRO.JK", "BBRI.JK", "BMRI.JK", "ESSA.JK", "MAPI.JK"] # Current
portfolio_b = ["ADRO.JK", "ESSA.JK", "MAPI.JK", "BBRI.JK", "PTBA.JK"] # Candidate

def load_returns(tickers):
    merged = None
    for ticker in tickers:
        file = MONTH_DIR / f"{ticker}.csv"
        if not file.exists():
            continue
        df = pd.read_csv(file)
        df = df[["Date", "monthly_return"]].rename(columns={"monthly_return": ticker})
        if merged is None:
            merged = df
        else:
            merged = merged.merge(df, on="Date", how="inner")
    merged["portfolio_return"] = merged[tickers].mean(axis=1)
    return merged[["Date", "portfolio_return"]]

def run_backtest_with_costs(df_port, df_ihsg, turnover_one_sided, cost_rate):
    df_eval = df_port.merge(df_ihsg, on="Date").dropna()
    # Apply transaction cost drag
    # Drag = 2 * turnover_one_sided * cost_rate
    drag = 2 * turnover_one_sided * cost_rate
    df_eval["portfolio_return_adj"] = df_eval["portfolio_return"] - drag
    
    p_returns = df_eval["portfolio_return_adj"].values
    b_returns = df_eval["monthly_return"].values
    
    n = len(p_returns)
    years = n / 12.0
    
    p_cum = (1 + p_returns).prod()
    cagr = p_cum ** (1 / years) - 1
    
    vol = p_returns.std() * math.sqrt(12.0)
    sharpe = (cagr - 0.05) / vol if vol > 0 else 0.0
    
    p_equity = (1 + p_returns).cumprod()
    peaks = np.maximum.accumulate(p_equity)
    dds = (peaks - p_equity) / peaks
    max_dd = dds.max()
    
    # CAPM Alpha
    mean_p = p_returns.mean()
    mean_b = b_returns.mean()
    cov_pb = np.cov(p_returns, b_returns)[0, 1]
    var_b = np.var(b_returns, ddof=1)
    beta = cov_pb / var_b if var_b > 0 else 0.0
    alpha_monthly = mean_p - beta * mean_b
    alpha_annualized = alpha_monthly * 12.0
    
    return {
        "cagr": cagr,
        "sharpe": sharpe,
        "max_dd": max_dd,
        "alpha": alpha_annualized
    }

def main():
    df_ihsg = pd.read_csv(IHSG_FILE)[["Date", "monthly_return"]]
    df_a = load_returns(portfolio_a)
    df_b = load_returns(portfolio_b)
    
    # Turnover assumptions:
    # Config A: stable, Quality 30, Value 20 -> monthly one-sided turnover ~10% (rebalance 1 stock every 10 months)
    # Config B: Growth 30, Momentum 35 -> monthly one-sided turnover ~15% (rebalance 1 stock every 6.7 months)
    turnover_a = 0.10
    turnover_b = 0.15
    
    scenarios = [0.0015, 0.0025, 0.0050] # 0.15%, 0.25%, 0.50%
    
    print("=== TRANSACTION COST IMPACT ANALYSIS ===")
    print("Model,Fee,CAGR,Sharpe,Alpha,Max DD")
    for name, df_port, to in [("Config A", df_a, turnover_a), ("Config B", df_b, turnover_b)]:
        # Raw (no cost)
        raw = run_backtest_with_costs(df_port, df_ihsg, to, 0.0)
        print(f"{name},0.00%,{raw['cagr']*100:.2f}%,{raw['sharpe']:.2f},{raw['alpha']*100:+.2f}%,{raw['max_dd']*100:.2f}%")
        for fee in scenarios:
            res = run_backtest_with_costs(df_port, df_ihsg, to, fee)
            print(f"{name},{fee*100:.2f}%,{res['cagr']*100:.2f}%,{res['sharpe']:.2f},{res['alpha']*100:+.2f}%,{res['max_dd']*100:.2f}%")
            
    print("\n=== STRESS TEST REGIME ANALYSIS ===")
    regimes = {
        "COVID CRASH": ("2020-01-01", "2020-12-31"),
        "COMMODITY BOOM": ("2021-01-01", "2022-12-31"),
        "NORMALIZATION": ("2023-01-01", "2024-12-31"),
        "LATEST REGIME": ("2025-01-01", "2026-05-31")
    }
    
    for name, df_port, to in [("Config A", df_a, turnover_a), ("Config B", df_b, turnover_b)]:
        print(f"\n{name}:")
        for r_name, (start_dt, end_dt) in regimes.items():
            # Apply 0.25% fee scenario
            df_eval = df_port.merge(df_ihsg, on="Date").dropna()
            df_sub = df_eval[(df_eval["Date"] >= start_dt) & (df_eval["Date"] <= end_dt)].copy()
            drag = 2 * to * 0.0025
            df_sub["portfolio_return_adj"] = df_sub["portfolio_return"] - drag
            
            p_returns = df_sub["portfolio_return_adj"].values
            b_returns = df_sub["monthly_return"].values
            
            p_cum = (1 + p_returns).prod() - 1.0
            b_cum = (1 + b_returns).prod() - 1.0
            
            # Alpha
            mean_p = p_returns.mean()
            mean_b = b_returns.mean()
            cov_pb = np.cov(p_returns, b_returns)[0, 1]
            var_b = np.var(b_returns, ddof=1)
            beta = cov_pb / var_b if var_b > 0 else 0.0
            alpha = (mean_p - beta * mean_b) * 12.0
            
            # Max DD
            p_equity = (1 + p_returns).cumprod()
            peaks = np.maximum.accumulate(p_equity)
            dds = (peaks - p_equity) / peaks
            max_dd = dds.max()
            
            win_rate = sum(1 for r in p_returns if r > 0) / len(p_returns)
            print(f"  {r_name}: Return={p_cum*100:.2f}%, Alpha={alpha*100:+.2f}%, MaxDD={max_dd*100:.2f}%, WinRate={win_rate*100:.2f}%")

if __name__ == "__main__":
    main()
