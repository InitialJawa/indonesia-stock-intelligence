import json
import pandas as pd
import numpy as np
from pathlib import Path

# Paths
SCORES_DIR = Path("output/scores")
MOMENTUM_HIST_DIR = Path("snapshots/momentum_history")
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

def get_monthly_portfolios(quality, growth, value, weight_m, weight_g, weight_q, weight_v, is_mom_only=False):
    files = sorted(list(MOMENTUM_HIST_DIR.glob("*.json")))
    portfolios = {}
    for file in files:
        month_key = file.stem
        with open(file, "r") as f:
            momentum_list = json.load(f)
        if not momentum_list:
            continue
        momentum_list.sort(key=lambda x: x["return_12m"])
        n = len(momentum_list)
        scored_tickers = []
        for idx, item in enumerate(momentum_list):
            ticker = item["ticker"]
            m_score = ((idx + 1) / n) * 100.0
            if is_mom_only:
                final_score = m_score
            else:
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
        scored_tickers.sort(key=lambda x: x[1], reverse=True)
        top_5 = [x[0] for x in scored_tickers[:5]]
        portfolios[month_key] = top_5
    return portfolios

def run_backtest_details(portfolios, df_ihsg, fee_rate):
    months = sorted(list(portfolios.keys()))
    ticker_returns = {}
    for ticker_file in MONTH_DIR.glob("*.csv"):
        ticker = ticker_file.stem
        df = pd.read_csv(ticker_file)
        df["month_key"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m")
        ticker_returns[ticker] = df.set_index("month_key")["monthly_return"].to_dict()
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
        if i == 0:
            turnover_one_sided = 1.0
        else:
            prev_holdings = set(portfolios[months[i-1]])
            curr_holdings = set(holdings)
            turnover_one_sided = len(curr_holdings - prev_holdings) / 5.0
        drag = 2 * turnover_one_sided * fee_rate
        p_ret_adj = p_ret_raw - drag
        results.append(p_ret_adj)
    
    # Calculate ending capital
    capital = 100000000.0 # 100 million
    for r in results:
        capital *= (1.0 + r)
    return capital

def main():
    quality, growth, value = load_rankings()
    df_ihsg = pd.read_csv(IHSG_FILE)[["Date", "monthly_return"]]
    
    port_mom = get_monthly_portfolios(quality, growth, value, 0, 0, 0, 0, is_mom_only=True)
    port_a = get_monthly_portfolios(quality, growth, value, 0.25, 0.25, 0.30, 0.20)
    port_b = get_monthly_portfolios(quality, growth, value, 0.35, 0.30, 0.25, 0.10)
    
    # 0.25% fee
    cap_mom = run_backtest_details(port_mom, df_ihsg, 0.0025)
    cap_a = run_backtest_details(port_a, df_ihsg, 0.0025)
    cap_b = run_backtest_details(port_b, df_ihsg, 0.0025)
    
    # Raw (no fee)
    cap_mom_raw = run_backtest_details(port_mom, df_ihsg, 0.0)
    cap_a_raw = run_backtest_details(port_a, df_ihsg, 0.0)
    cap_b_raw = run_backtest_details(port_b, df_ihsg, 0.0)
    
    print("Ending Capital from Rp100,000,000 Starting Capital:")
    print(f"Momentum Only (Raw): Rp {cap_mom_raw:,.2f}")
    print(f"Momentum Only (Net): Rp {cap_mom:,.2f}")
    print(f"Config A (Raw): Rp {cap_a_raw:,.2f}")
    print(f"Config A (Net): Rp {cap_a:,.2f}")
    print(f"Config B (Raw): Rp {cap_b_raw:,.2f}")
    print(f"Config B (Net): Rp {cap_b:,.2f}")

if __name__ == "__main__":
    main()
