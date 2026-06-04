import json
import pandas as pd
import numpy as np
import math
from pathlib import Path

MONTH_DIR = Path("database/monthly")
IHSG_FILE = Path("benchmarks/ihsg_monthly.csv")

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def run_backtest_for_portfolio(tickers, df_ihsg):
    merged = None
    for ticker in tickers:
        file = MONTH_DIR / f"{ticker}.csv"
        if not file.exists():
            continue
        df_stock = pd.read_csv(file)
        df_stock = df_stock[["Date", "monthly_return"]].rename(columns={"monthly_return": ticker})
        if merged is None:
            merged = df_stock
        else:
            merged = merged.merge(df_stock, on="Date", how="inner")
            
    if merged is None:
        return None
        
    merged["portfolio_return"] = merged[tickers].mean(axis=1)
    df_eval = merged[["Date", "portfolio_return"]].merge(df_ihsg, on="Date")
    df_eval = df_eval.dropna()
    return df_eval

def calculate_metrics(df_eval):
    p_returns = df_eval["portfolio_return"].values
    b_returns = df_eval["monthly_return"].values
    
    n = len(p_returns)
    years = n / 12.0
    
    p_cum = (1 + p_returns).prod()
    cagr = p_cum ** (1 / years) - 1
    
    ann_return = p_returns.mean() * 12.0
    vol = p_returns.std() * math.sqrt(12.0)
    
    # Sharpe
    sharpe = (cagr - 0.05) / vol if vol > 0 else 0.0
    
    # Sortino
    downside_returns = p_returns[p_returns < 0]
    downside_std = downside_returns.std() * math.sqrt(12.0) if len(downside_returns) > 0 else 0.0
    sortino = (cagr - 0.05) / downside_std if downside_std > 0 else 0.0
    
    # Max DD
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
    
    win_rate = sum(1 for r in p_returns if r > 0) / n
    
    return {
        "cagr": cagr,
        "ann_return": ann_return,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_dd": max_dd,
        "alpha": alpha_annualized,
        "vol": vol,
        "win_rate": win_rate
    }

def main():
    # Load IHSG
    df_ihsg = pd.read_csv(IHSG_FILE)
    df_ihsg = df_ihsg[["Date", "monthly_return"]]
    
    # Load rankings
    quality = load_json("output/scores/quality_ranking.json")
    growth = load_json("output/scores/growth_ranking.json")
    value = load_json("output/scores/value_ranking.json")
    momentum = load_json("output/scores/momentum_ranking.json")
    
    # Map to df
    df_q = pd.DataFrame(quality)[["ticker", "quality_score"]]
    df_g = pd.DataFrame(growth)[["ticker", "growth_score"]]
    df_v = pd.DataFrame(value)[["ticker", "value_score"]]
    df_m = pd.DataFrame(momentum)[["ticker", "momentum"]]
    
    df_all = df_q.merge(df_g, on="ticker").merge(df_v, on="ticker").merge(df_m, on="ticker")
    
    # Configs
    configs = {
        "A": {"m": 0.25, "g": 0.25, "q": 0.30, "v": 0.20},
        "B": {"m": 0.35, "g": 0.30, "q": 0.25, "v": 0.10},
        "C": {"m": 0.40, "g": 0.35, "q": 0.25, "v": 0.00},
        "D": {"m": 0.50, "g": 0.30, "q": 0.20, "v": 0.00},
        "E": {"m": 0.30, "g": 0.30, "q": 0.40, "v": 0.00}
    }
    
    portfolios_tickers = {}
    for code, weights in configs.items():
        score = (
            df_all["momentum"] * weights["m"] +
            df_all["growth_score"] * weights["g"] +
            df_all["quality_score"] * weights["q"] +
            df_all["value_score"] * weights["v"]
        )
        df_temp = df_all.copy()
        df_temp["score"] = score
        df_temp = df_temp.sort_values("score", ascending=False)
        tickers = df_temp["ticker"].head(5).tolist()
        portfolios_tickers[code] = tickers
        print(f"Config {code} Top 5: {', '.join([t.replace('.JK', '') for t in tickers])}")
        
    print("\n=== FASE 1: DYNAMIC WEIGHT COMPARISON TABLE (FULL PERIOD 2018-2026) ===")
    results = {}
    for code, tickers in portfolios_tickers.items():
        df_eval = run_backtest_for_portfolio(tickers, df_ihsg)
        metrics = calculate_metrics(df_eval)
        results[code] = df_eval
        print(f"Config {code}: CAGR={metrics['cagr']*100:.2f}%, Ann_Ret={metrics['ann_return']*100:.2f}%, Sharpe={metrics['sharpe']:.2f}, Sortino={metrics['sortino']:.2f}, MaxDD={metrics['max_dd']*100:.2f}%, Alpha={metrics['alpha']*100:+.2f}%, Vol={metrics['vol']*100:.2f}%, WinRate={metrics['win_rate']*100:.2f}%, Turnover=0.00%")
        
    print("\n=== FASE 2: ROBUSTNESS TEST (SUB-PERIOD ANALYSIS) ===")
    periods = {
        "2019-2020": ("2019-01-01", "2020-12-31"),
        "2021-2022": ("2021-01-01", "2022-12-31"),
        "2023-2024": ("2023-01-01", "2024-12-31"),
        "2025-2026": ("2025-01-01", "2026-06-30")
    }
    
    for p_name, (start_dt, end_dt) in periods.items():
        print(f"\nSub-Period: {p_name} ({start_dt} to {end_dt})")
        for code, df_eval in results.items():
            df_sub = df_eval[(df_eval["Date"] >= start_dt) & (df_eval["Date"] <= end_dt)]
            if df_sub.empty:
                print(f"  Config {code}: No data")
                continue
            metrics = calculate_metrics(df_sub)
            print(f"  Config {code}: CAGR={metrics['cagr']*100:.2f}%, Sharpe={metrics['sharpe']:.2f}, MaxDD={metrics['max_dd']*100:.2f}%, Alpha={metrics['alpha']*100:+.2f}%")

if __name__ == "__main__":
    main()
