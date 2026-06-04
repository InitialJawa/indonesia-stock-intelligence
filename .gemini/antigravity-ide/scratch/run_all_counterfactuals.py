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

def run_static_backtest(tickers, df_ihsg):
    # Load returns for each ticker
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
    
    # Merge with IHSG
    df_eval = merged[["Date", "portfolio_return"]].merge(df_ihsg, on="Date")
    df_eval = df_eval.dropna()
    
    p_returns = df_eval["portfolio_return"].values
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
        "alpha": alpha_annualized,
        "beta": beta
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
    final = load_json("output/scores/final_ranking_v3.json")
    
    # A. Momentum only (without FF)
    # We rank based on return_12m or return_6m+return_12m average.
    # Let's see: in momentum_ranking.json, the momentum score is:
    # return_6m * 0.35 + return_12m * 0.35 + score_ff * 0.30
    # Let's calculate purely: (score_6m + score_12m) / 2 or return_12m. Let's do (return_6m + return_12m) / 2
    # Wait, let's look at the current momentum ranking JSON. We can reconstruct pure price momentum.
    # Let's rank by return_12m:
    momentum_sorted = sorted(momentum, key=lambda x: x["return_12m"], reverse=True)
    tickers_mom_only = [x["ticker"] for x in momentum_sorted[:5]]
    
    # B. Quality only
    tickers_qual = [x["ticker"] for x in quality[:5]]
    
    # C. Value only
    tickers_val = [x["ticker"] for x in value[:5]]
    
    # D. Growth only
    tickers_growth = [x["ticker"] for x in growth[:5]]
    
    # E. Momentum + Foreign Flow (which is the momentum score in the json since it contains the FF rule)
    tickers_mom_ff = [x["ticker"] for x in momentum[:5]]
    
    # F. Quality + Growth + Value
    # Merge quality, growth, value scores
    df_q = pd.DataFrame(quality)[["ticker", "quality_score"]]
    df_g = pd.DataFrame(growth)[["ticker", "growth_score"]]
    df_v = pd.DataFrame(value)[["ticker", "value_score"]]
    df_fund = df_q.merge(df_g, on="ticker").merge(df_v, on="ticker")
    df_fund["fund_score"] = df_fund["quality_score"] * 0.30 + df_fund["growth_score"] * 0.25 + df_fund["value_score"] * 0.20
    df_fund = df_fund.sort_values("fund_score", ascending=False)
    tickers_fund = df_fund["ticker"].head(5).tolist()
    
    # G. Full Model
    tickers_full = [x["ticker"] for x in final[:5]]
    
    models = {
        "A. Momentum only": tickers_mom_only,
        "B. Quality only": tickers_qual,
        "C. Value only": tickers_val,
        "D. Growth only": tickers_growth,
        "E. Momentum + Foreign Flow": tickers_mom_ff,
        "F. Quality + Growth + Value": tickers_fund,
        "G. Full Model": tickers_full
    }
    
    print("Model,Top 5 Tickers,CAGR,Sharpe,Max DD,Alpha,Turnover")
    for name, tickers in models.items():
        metrics = run_static_backtest(tickers, df_ihsg)
        tickers_str = "/".join([t.replace(".JK", "") for t in tickers])
        print(f"{name},{tickers_str},{metrics['cagr']*100:.2f}%,{metrics['sharpe']:.2f},{metrics['max_dd']*100:.2f}%,{metrics['alpha']*100:+.2f}%,0.00%")

if __name__ == "__main__":
    main()
