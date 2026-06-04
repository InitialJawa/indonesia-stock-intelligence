import pandas as pd
import numpy as np

df = pd.read_csv("database/historical/momentum_monthly_returns.csv")
rets = df["portfolio_return"].values
ihsg = df["benchmark_return"].values

p_equity = (1 + rets).prod()
b_equity = (1 + ihsg).prod()

n = len(rets)
years = n / 12.0

p_cagr = p_equity ** (1/years) - 1
b_cagr = b_equity ** (1/years) - 1

print(f"Number of months: {n}")
print(f"Years: {years:.2f}")
print(f"Portfolio ending equity: {p_equity:.4f}")
print(f"Portfolio CAGR: {p_cagr*100:.4f}%")
print(f"IHSG ending equity: {b_equity:.4f}")
print(f"IHSG CAGR: {b_cagr*100:.4f}%")
