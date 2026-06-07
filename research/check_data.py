"""Quick check of warehouse data structure."""
import pandas as pd

print("=== warehouse_v3 columns ===")
df = pd.read_csv("warehouse_historical/warehouse_v3.csv", nrows=3)
print(list(df.columns))

print("\n=== warehouse_v3 tickers ===")
tickers = pd.read_csv("warehouse_historical/warehouse_v3.csv", usecols=["ticker"])["ticker"].unique()
print(f"Count: {len(tickers)}")
print(sorted(tickers))

print("\n=== warehouse_v3 date range ===")
dates = pd.read_csv("warehouse_historical/warehouse_v3.csv", usecols=["month"])
print(f"Min: {dates['month'].min()}")
print(f"Max: {dates['month'].max()}")
print(f"Unique months: {dates['month'].nunique()}")

print("\n=== warehouse_v3 sample final_scores ===")
samp = df[["ticker", "month", "final_score"]].head(10)
print(samp)

print("\n=== Check daily parquet (no nrows) ===")
df2 = pd.read_parquet("database/historical/warehouse_daily_v4.parquet")
print(f"Records: {len(df2):,}")
print(f"Columns: {list(df2.columns)}")
print(f"Date range: {df2['Date'].min()} to {df2['Date'].max()}")
print(f"Tickers: {sorted(df2['ticker'].unique())}")
