import pandas as pd
df = pd.read_csv("database/historical/momentum_equity_curve.csv")
print("First 5 lines:")
print(df.head())
print("\nLast 5 lines:")
print(df.tail())
print(f"\nFinal cumulative return in file: {df['cumulative_return'].iloc[-1]*100:.2f}%")
