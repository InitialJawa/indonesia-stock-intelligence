import pandas as pd
df = pd.read_csv("database/historical/momentum_monthly_returns.csv")
df["year"] = df["date"].str[:4]
for yr, group in df.groupby("year"):
    ret = (1 + group["portfolio_return"]).prod() - 1
    ihsg = (1 + group["benchmark_return"]).prod() - 1
    print(f"Year {yr}: Portfolio={ret*100:.2f}%, IHSG={ihsg*100:.2f}%")
