"""Debug metrics computation."""
import pandas as pd
import numpy as np

# Recreate the backtest return generation (minimal)
wh = pd.read_csv("warehouse_historical/warehouse_v3.csv", usecols=["ticker","month","final_score","price"])
wh["month"] = pd.to_datetime(wh["month"])

import glob
prices = {}
for fp in glob.glob("database/monthly/*.csv"):
    ticker = fp.split("\\")[-1].replace(".csv","")
    df = pd.read_csv(fp)
    df["Date"] = pd.to_datetime(df["Date"])
    prices[ticker] = df

price_map = {}
for ticker, df in prices.items():
    for _, row in df.iterrows():
        price_map[(ticker, row["Date"])] = row["month_end_price"]

# Build returns dataset
all_returns = []
for _, row in wh.iterrows():
    me = row["month"] + pd.offsets.MonthEnd(0)
    nme = me + pd.offsets.MonthEnd(1)
    cp = price_map.get((row["ticker"], me))
    np_ = price_map.get((row["ticker"], nme))
    if cp and np_ and cp > 0 and np_ > 0:
        all_returns.append({
            "month": row["month"], "ticker": row["ticker"],
            "final_score": row["final_score"],
            "monthly_return": (np_ / cp) - 1
        })

data = pd.DataFrame(all_returns)

# Backtest baseline: Top 5 each month
portfolio_returns = []
for month, group in data.groupby("month"):
    ranked = group.sort_values("final_score", ascending=False)
    top5 = ranked.head(5)
    port_return = top5["monthly_return"].mean()
    portfolio_returns.append({"month": month, "portfolio_return": port_return})

pr = pd.DataFrame(portfolio_returns).set_index("month")["portfolio_return"]
print("=== Portfolio returns (first 5) ===")
print(pr.head())
print(f"  Mean: {pr.mean()*100:.2f}%")
print(f"  Std: {pr.std()*100:.2f}%")
print(f"  Total months: {len(pr)}")

# Load IHSG
ihsg = pd.read_csv("benchmarks/ihsg_monthly.csv")
ihsg["Date"] = pd.to_datetime(ihsg["Date"])
ihsg = ihsg.set_index("Date")["monthly_return"]
print("\n=== IHSG returns (first 5) ===")
print(ihsg.head())

# Check alignment
pr_index = pr.index.to_period("M").to_timestamp()
ihsg_index = ihsg.index.to_period("M").to_timestamp()
common = pr_index.intersection(ihsg_index)
print(f"\n=== Alignment ===")
print(f"PR index (first 3): {pr_index[:3].values}")
print(f"IHSG index (first 3): {ihsg_index[:3].values}")
print(f"Common months: {len(common)}")
if len(common) > 0:
    print(f"First common: {common[0]}")
    print(f"Last common: {common[-1]}")

# Now compute CAGR manually
pr_aligned = pr.copy()
pr_aligned.index = pr_aligned.index.to_period("M").to_timestamp()
ir = ihsg.copy()
ir.index = ir.index.to_period("M").to_timestamp()
common = pr_aligned.index.intersection(ir.index)
pr_aligned = pr_aligned.loc[common]
ir = ir.loc[common]

print(f"\n=== After alignment ===")
print(f"PR months: {len(pr_aligned)}")
print(f"PR first 5:")
print(pr_aligned.head())
total_ret = (1 + pr_aligned).prod() - 1
n_years = len(pr_aligned) / 12
cagr = ((1 + total_ret) ** (1 / n_years) - 1) * 100
print(f"Total return: {total_ret*100:.2f}%")
print(f"N years: {n_years:.1f}")
print(f"CAGR: {cagr:.2f}%")
