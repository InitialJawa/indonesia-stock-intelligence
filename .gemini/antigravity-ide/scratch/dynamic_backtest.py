import os
import json
import pandas as pd
import numpy as np
import math
from pathlib import Path

# Paths
SCORES_DIR = Path("output/scores")
MOMENTUM_HIST_DIR = Path("snapshots/momentum_history")
MONTH_DIR = Path("database/monthly")
IHSG_FILE = Path("benchmarks/ihsg_monthly.csv")

def load_rankings():
    # Load static rankings
    q_file = SCORES_DIR / "quality_ranking.json"
    g_file = SCORES_DIR / "growth_ranking.json"
    v_file = SCORES_DIR / "value_ranking.json"
    
    quality = {}
    if q_file.exists():
        with open(q_file, "r") as f:
            for item in json.load(f):
                quality[item["ticker"]] = item["quality_score"]
                
    growth = {}
    if g_file.exists():
        with open(g_file, "r") as f:
            for item in json.load(f):
                growth[item["ticker"]] = item["growth_score"]
                
    value = {}
    if v_file.exists():
        with open(v_file, "r") as f:
            for item in json.load(f):
                value[item["ticker"]] = item["value_score"]
                
    return quality, growth, value

def get_monthly_portfolios(quality, growth, value, weight_m, weight_g, weight_q, weight_v):
    # Retrieve all monthly momentum history files
    files = sorted(list(MOMENTUM_HIST_DIR.glob("*.json")))
    portfolios = {} # month_key -> list of tickers
    
    for file in files:
        month_key = file.stem # e.g. '2019-01'
        with open(file, "r") as f:
            momentum_list = json.load(f)
            
        if not momentum_list:
            continue
            
        # Re-sort by return_12m to compute standard percentile rank
        # Sort ascending so higher return has higher rank
        momentum_list.sort(key=lambda x: x["return_12m"])
        n = len(momentum_list)
        
        scored_tickers = []
        for idx, item in enumerate(momentum_list):
            ticker = item["ticker"]
            # Percentile rank (0-100)
            m_score = ((idx + 1) / n) * 100.0
            
            q_score = quality.get(ticker, 50.0)
            g_score = growth.get(ticker, 50.0)
            v_score = value.get(ticker, 50.0)
            
            final_score = (
                m_score * weight_m +
                g_score * weight_g +
                q_score * weight_q +
                v_score * weight_v
            )
            
            scored_tickers.append((ticker, final_score))
            
        # Sort descending by final score and select top 5
        scored_tickers.sort(key=lambda x: x[1], reverse=True)
        top_5 = [x[0] for x in scored_tickers[:5]]
        portfolios[month_key] = top_5
        
    return portfolios

def calculate_turnover(portfolios):
    months = sorted(list(portfolios.keys()))
    turnovers = [] # list of (month, one_sided_turnover_pct)
    
    for i in range(1, len(months)):
        prev_m = months[i-1]
        curr_m = months[i]
        
        prev_p = set(portfolios[prev_m])
        curr_p = set(portfolios[curr_m])
        
        # One-sided turnover: proportion of new holdings
        changed = len(curr_p - prev_p)
        turnovers.append((curr_m, changed / 5.0))
        
    df_to = pd.DataFrame(turnovers, columns=["month", "turnover"])
    df_to["year"] = df_to["month"].str[:4]
    
    # Calculate stats
    avg_monthly = df_to["turnover"].mean()
    avg_annual = avg_monthly * 12.0
    max_to = df_to["turnover"].max()
    median_to = df_to["turnover"].median()
    avg_changed = avg_monthly * 5.0
    
    # Distribution by year
    yearly_dist = df_to.groupby("year")["turnover"].mean() * 12.0
    
    return {
        "avg_monthly": avg_monthly,
        "avg_annual": avg_annual,
        "max_to": max_to,
        "median_to": median_to,
        "avg_changed": avg_changed,
        "yearly_dist": yearly_dist.to_dict(),
        "df": df_to
    }

def run_dynamic_backtest(portfolios, df_ihsg, fee_rate):
    months = sorted(list(portfolios.keys()))
    
    # Load all ticker returns
    ticker_returns = {}
    for ticker_file in MONTH_DIR.glob("*.csv"):
        ticker = ticker_file.stem
        df = pd.read_csv(ticker_file)
        df["month_key"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m")
        ticker_returns[ticker] = df.set_index("month_key")["monthly_return"].to_dict()
        
    results = []
    
    # Run month-by-month
    for i in range(len(months) - 1):
        formation_month = months[i]
        evaluation_month = months[i+1] # Walk-forward: held in month T+1
        
        holdings = portfolios[formation_month]
        
        # Calculate returns
        rets = []
        for ticker in holdings:
            ret = ticker_returns.get(ticker, {}).get(evaluation_month, np.nan)
            if not pd.isna(ret):
                rets.append(ret)
                
        if not rets:
            continue
            
        p_ret_raw = np.mean(rets)
        
        # Apply turnover fee drag
        # Turnover at month T+1 is determined by change from portfolio T-1 to T,
        # but for simplicity, we apply transaction cost based on rebalance changes.
        if i == 0:
            turnover_one_sided = 1.0 # Initial setup cost
        else:
            prev_holdings = set(portfolios[months[i-1]])
            curr_holdings = set(holdings)
            turnover_one_sided = len(curr_holdings - prev_holdings) / 5.0
            
        # Friction drag = 2 * turnover_one_sided * fee_rate
        drag = 2 * turnover_one_sided * fee_rate
        p_ret_adj = p_ret_raw - drag
        
        results.append({
            "Date": evaluation_month,
            "portfolio_return": p_ret_adj,
            "turnover": turnover_one_sided
        })
        
    df_eval = pd.DataFrame(results)
    
    # Merge with IHSG
    df_ihsg_clean = df_ihsg.copy()
    df_ihsg_clean["Date"] = pd.to_datetime(df_ihsg_clean["Date"]).dt.strftime("%Y-%m")
    
    df_final = df_eval.merge(df_ihsg_clean, on="Date", how="inner").dropna()
    
    # Calculate performance metrics
    p_returns = df_final["portfolio_return"].values
    b_returns = df_final["monthly_return"].values
    
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
    
    # Win rate
    win_rate = sum(1 for r in p_returns if r > 0) / len(p_returns)
    
    return {
        "cagr": cagr,
        "sharpe": sharpe,
        "max_dd": max_dd,
        "alpha": alpha_annualized,
        "win_rate": win_rate,
        "returns": df_final
    }

def main():
    # Load data
    quality, growth, value = load_rankings()
    df_ihsg = pd.read_csv(IHSG_FILE)[["Date", "monthly_return"]]
    
    # Config A: Current (25/25/30/20)
    port_a = get_monthly_portfolios(quality, growth, value, 0.25, 0.25, 0.30, 0.20)
    
    # Config B: Candidate (35/30/25/10)
    port_b = get_monthly_portfolios(quality, growth, value, 0.35, 0.30, 0.25, 0.10)
    
    # 1. Turnover Audit
    to_a = calculate_turnover(port_a)
    to_b = calculate_turnover(port_b)
    
    print("=== FASE 1: TURNOVER AUDIT ===")
    print(f"Config A (Current):")
    print(f"  Average Annual Turnover: {to_a['avg_annual']*100:.2f}%")
    print(f"  Average Monthly Turnover: {to_a['avg_monthly']*100:.2f}%")
    print(f"  Maximum Turnover: {to_a['max_to']*100:.2f}%")
    print(f"  Median Turnover: {to_a['median_to']*100:.2f}%")
    print(f"  Avg Changed Stocks: {to_a['avg_changed']:.2f}")
    print("  Yearly Turnover Distribution:")
    for yr, val in to_a["yearly_dist"].items():
        print(f"    {yr}: {val*100:.2f}%")
        
    print(f"\nConfig B (Candidate):")
    print(f"  Average Annual Turnover: {to_b['avg_annual']*100:.2f}%")
    print(f"  Average Monthly Turnover: {to_b['avg_monthly']*100:.2f}%")
    print(f"  Maximum Turnover: {to_b['max_to']*100:.2f}%")
    print(f"  Median Turnover: {to_b['median_to']*100:.2f}%")
    print(f"  Avg Changed Stocks: {to_b['avg_changed']:.2f}")
    print("  Yearly Turnover Distribution:")
    for yr, val in to_b["yearly_dist"].items():
        print(f"    {yr}: {val*100:.2f}%")
        
    # 2. Transaction Cost Analysis
    scenarios = [0.0, 0.0015, 0.0025, 0.0050]
    print("\n=== FASE 2: TRANSACTION COST ANALYSIS ===")
    print("Config,Fee,CAGR,Sharpe,Alpha,MaxDD")
    
    results_a = {}
    results_b = {}
    
    for fee in scenarios:
        res_a = run_dynamic_backtest(port_a, df_ihsg, fee)
        results_a[fee] = res_a
        print(f"Config A,{fee*100:.2f}%,{res_a['cagr']*100:.2f}%,{res_a['sharpe']:.2f},{res_a['alpha']*100:+.2f}%,{res_a['max_dd']*100:.2f}%")
        
    for fee in scenarios:
        res_b = run_dynamic_backtest(port_b, df_ihsg, fee)
        results_b[fee] = res_b
        print(f"Config B,{fee*100:.2f}%,{res_b['cagr']*100:.2f}%,{res_b['sharpe']:.2f},{res_b['alpha']*100:+.2f}%,{res_b['max_dd']*100:.2f}%")
        
    # 3. Stress Test (using 0.25% fee rate)
    print("\n=== FASE 3: STRESS TEST REGIME ANALYSIS (FEE 0.25%) ===")
    regimes = {
        "COVID CRASH": ("2020-01", "2020-12"),
        "COMMODITY BOOM": ("2021-01", "2022-12"),
        "NORMALIZATION": ("2023-01", "2024-12"),
        "LATEST REGIME": ("2025-01", "2026-05")
    }
    
    for name, res_dict in [("Config A", results_a[0.0025]), ("Config B", results_b[0.0025])]:
        print(f"{name}:")
        df_eval = res_dict["returns"]
        for r_name, (start_dt, end_dt) in regimes.items():
            df_sub = df_eval[(df_eval["Date"] >= start_dt) & (df_eval["Date"] <= end_dt)].copy()
            if df_sub.empty:
                print(f"  {r_name}: No data")
                continue
                
            p_returns = df_sub["portfolio_return"].values
            b_returns = df_sub["monthly_return"].values
            
            p_cum = (1 + p_returns).prod() - 1.0
            
            # CAPM Alpha
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

    # 4. Holding Stability Audit
    # Let's count tickers frequency and see the final holdings comparison
    print("\n=== FASE 4: HOLDING STABILITY AUDIT ===")
    
    # Collect all tickers that appeared in the portfolios
    tickers_a_all = []
    for t_list in port_a.values():
        tickers_a_all.extend(t_list)
    tickers_b_all = []
    for t_list in port_b.values():
        tickers_b_all.extend(t_list)
        
    counts_a = pd.Series(tickers_a_all).value_counts()
    counts_b = pd.Series(tickers_b_all).value_counts()
    
    print("\nTop 20 Ticker Paling Sering Muncul (Config A):")
    for tick, cnt in counts_a.head(20).items():
        print(f"  {tick}: {cnt} kali")
        
    print("\nTop 20 Ticker Paling Sering Muncul (Config B):")
    for tick, cnt in counts_b.head(20).items():
        print(f"  {tick}: {cnt} kali")

if __name__ == "__main__":
    main()
