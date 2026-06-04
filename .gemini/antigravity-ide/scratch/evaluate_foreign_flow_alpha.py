# file: scratch/evaluate_foreign_flow_alpha.py

import json
import pandas as pd
import numpy as np
import math
from pathlib import Path

# Paths
SCORES_DIR = Path("output/scores")
UNIV_DIR = Path("database/historical_universe")
MONTH_DIR = Path("database/monthly")
IHSG_FILE = Path("benchmarks/ihsg_monthly.csv")

def load_rankings():
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

def calculate_percentile(series):
    if series.empty:
        return series
    if series.nunique() == 1:
        return pd.Series([100.0] * len(series), index=series.index)
    return series.rank(pct=True) * 100.0

def load_monthly_data():
    ticker_data = {}
    for file in MONTH_DIR.glob("*.csv"):
        ticker = file.stem
        df = pd.read_csv(file)
        df["month_key"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m")
        df = df.set_index("month_key").sort_index()
        ticker_data[ticker] = df
    return ticker_data

def reconstruct_portfolios(quality, growth, value, ticker_data, use_ff=True):
    univ_files = sorted(list(UNIV_DIR.glob("*.json")))
    
    # Generate month keys from 2019-01 to 2026-05
    months = []
    for year in range(2019, 2027):
        end_month = 5 if year == 2026 else 12
        for month in range(1, end_month + 1):
            months.append(f"{year}-{month:02d}")
            
    portfolios = {}
    
    for month_key in months:
        # Load universe for this month
        active_universe = None
        for file in univ_files:
            file_month = file.stem
            if file_month <= month_key:
                active_universe = file
            else:
                break
                
        if active_universe is None:
            continue
            
        with open(active_universe, "r") as f:
            universe_tickers = json.load(f)
            
        rows = []
        for ticker in universe_tickers:
            if ticker not in ticker_data:
                continue
            df = ticker_data[ticker]
            
            # Find the position of month_key
            if month_key not in df.index:
                continue
                
            idx = df.index.get_loc(month_key)
            if idx < 12:
                # Not enough history for 12m return
                continue
                
            p_t = df.iloc[idx]["month_end_price"]
            p_6m = df.iloc[idx - 6]["month_end_price"]
            p_12m = df.iloc[idx - 12]["month_end_price"]
            
            if pd.isna(p_t) or pd.isna(p_6m) or pd.isna(p_12m) or p_6m == 0 or p_12m == 0:
                continue
                
            ret_6m = (p_t / p_6m) - 1.0
            ret_12m = (p_t / p_12m) - 1.0
            
            # 6-month foreign flow accumulation
            ff_6m = 0.0
            if "net_foreign_buy" in df.columns:
                ff_6m = df["net_foreign_buy"].iloc[idx-6:idx+1].sum()
                
            rows.append({
                "ticker": ticker,
                "ret_6m": ret_6m,
                "ret_12m": ret_12m,
                "ff_6m": ff_6m
            })
            
        if not rows:
            continue
            
        df_scored = pd.DataFrame(rows)
        df_scored["score_6m"] = calculate_percentile(df_scored["ret_6m"])
        df_scored["score_12m"] = calculate_percentile(df_scored["ret_12m"])
        df_scored["score_ff"] = calculate_percentile(df_scored["ff_6m"])
        
        # Calculate momentum score
        if use_ff:
            df_scored["momentum"] = (
                df_scored["score_6m"] * 0.35 +
                df_scored["score_12m"] * 0.35 +
                df_scored["score_ff"] * 0.30
            )
        else:
            df_scored["momentum"] = (
                df_scored["score_6m"] * 0.50 +
                df_scored["score_12m"] * 0.50
            )
            
        # Calculate final multi-factor score for Config B
        # Config B: M 35% / G 30% / Q 25% / V 10%
        final_rows = []
        for _, r in df_scored.iterrows():
            tk = r["ticker"]
            m_score = r["momentum"]
            q_score = quality.get(tk, 50.0)
            g_score = growth.get(tk, 50.0)
            v_score = value.get(tk, 50.0)
            
            final_score = (
                m_score * 0.35 +
                g_score * 0.30 +
                q_score * 0.25 +
                v_score * 0.10
            )
            final_rows.append((tk, final_score))
            
        final_rows.sort(key=lambda x: x[1], reverse=True)
        top_5 = [x[0] for x in final_rows[:5]]
        portfolios[month_key] = top_5
        
    return portfolios

def run_backtest_with_fees(portfolios, df_ihsg, ticker_returns, fee_rate=0.0025):
    months = sorted(list(portfolios.keys()))
    results = []
    
    for i in range(len(months) - 1):
        formation_month = months[i]
        evaluation_month = months[i+1]
        
        holdings = portfolios[formation_month]
        
        rets = []
        for ticker in holdings:
            ret = ticker_returns.get(ticker, {}).get(evaluation_month, np.nan)
            if not pd.isna(ret):
                rets.append(ret)
                
        if not rets:
            continue
            
        p_ret_raw = np.mean(rets)
        
        # Calculate turnover
        if i == 0:
            turnover_one_sided = 1.0
        else:
            prev_holdings = set(portfolios[months[i-1]])
            curr_holdings = set(holdings)
            turnover_one_sided = len(curr_holdings - prev_holdings) / 5.0
            
        drag = 2 * turnover_one_sided * fee_rate
        p_ret_adj = p_ret_raw - drag
        
        results.append({
            "Date": evaluation_month,
            "portfolio_return": p_ret_adj,
            "turnover": turnover_one_sided
        })
        
    df_eval = pd.DataFrame(results)
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
    
    mean_p = p_returns.mean()
    mean_b = b_returns.mean()
    cov_pb = np.cov(p_returns, b_returns)[0, 1]
    var_b = np.var(b_returns, ddof=1)
    beta = cov_pb / var_b if var_b > 0 else 0.0
    alpha = (mean_p - beta * mean_b) * 12.0
    
    avg_monthly_turnover = df_final["turnover"].mean()
    
    return {
        "cagr": cagr,
        "sharpe": sharpe,
        "max_dd": max_dd,
        "alpha": alpha,
        "turnover": avg_monthly_turnover
    }

def main():
    print("=== FASE 5: EVALUASI KONTRIBUSI ALPHA BANDAR ASING (FOREIGN FLOW) ===")
    quality, growth, value = load_rankings()
    ticker_data = load_monthly_data()
    df_ihsg = pd.read_csv(IHSG_FILE)[["Date", "monthly_return"]]
    
    # Load ticker returns dict for fast lookups
    ticker_returns = {}
    for ticker, df in ticker_data.items():
        ticker_returns[ticker] = df["monthly_return"].to_dict()
        
    print("\nRekonstruksi Portofolio Config B Tanpa Foreign Flow...")
    port_no_ff = reconstruct_portfolios(quality, growth, value, ticker_data, use_ff=False)
    metrics_no_ff = run_backtest_with_fees(port_no_ff, df_ihsg, ticker_returns, fee_rate=0.0025)
    
    print("Rekonstruksi Portofolio Config B Dengan Foreign Flow (Bandar Asing)...")
    port_with_ff = reconstruct_portfolios(quality, growth, value, ticker_data, use_ff=True)
    metrics_with_ff = run_backtest_with_fees(port_with_ff, df_ihsg, ticker_returns, fee_rate=0.0025)
    
    print("\n=== HASIL PERBANDINGAN PORTFOLIO (FEE 0.25%) ===")
    print("| Parameter Kinerja | Config B (Tanpa FF) | Config B (Dengan FF) | Perubahan (Delta) |")
    print("| :--- | :---: | :---: | :---: |")
    print(f"| **CAGR** | {metrics_no_ff['cagr']*100:.4f}% | {metrics_with_ff['cagr']*100:.4f}% | **{(metrics_with_ff['cagr'] - metrics_no_ff['cagr'])*100:+.4f}%** |")
    print(f"| **Sharpe Ratio** | {metrics_no_ff['sharpe']:.4f} | {metrics_with_ff['sharpe']:.4f} | **{(metrics_with_ff['sharpe'] - metrics_no_ff['sharpe']):+.4f}** |")
    print(f"| **CAPM Alpha** | {metrics_no_ff['alpha']*100:+.4f}% | {metrics_with_ff['alpha']*100:+.4f}% | **{(metrics_with_ff['alpha'] - metrics_no_ff['alpha'])*100:+.4f}%** |")
    print(f"| **Max Drawdown** | {metrics_no_ff['max_dd']*100:.4f}% | {metrics_with_ff['max_dd']*100:.4f}% | {(metrics_with_ff['max_dd'] - metrics_no_ff['max_dd'])*100:+.4f}% |")
    print(f"| **Rata-rata Turnover Bulanan** | {metrics_no_ff['turnover']*100:.4f}% | {metrics_with_ff['turnover']*100:.4f}% | {(metrics_with_ff['turnover'] - metrics_no_ff['turnover'])*100:+.4f}% |")

if __name__ == "__main__":
    main()
