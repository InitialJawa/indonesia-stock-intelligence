#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
MARKET_STATE_DIR = BASE_DIR / "research" / "output"
INPUT_DIR = BASE_DIR / "database" / "historical"


ms_df = pd.read_csv(MARKET_STATE_DIR / "market_states_all.csv")
ms_df["Date"] = pd.to_datetime(ms_df["Date"])
ms_df["month"] = ms_df["Date"].dt.strftime("%Y-%m")
print("=== Market States sample ===")
print(ms_df[["Date", "month", "ticker"]].head())
print("\n")

fw_df = pd.read_csv(INPUT_DIR / "factor_warehouse.csv")
print("=== Factor Warehouse sample ===")
print(fw_df[["date", "ticker", "momentum_score"]].head())
print("\n")
print("=== Factor Warehouse unique dates ===")
print(fw_df["date"].unique())
print("\n")
print("=== Market States unique months ===")
print(ms_df["month"].unique()[:20])
print("\n")

print("=== Checking if any match ===")
fw_months = set(fw_df["date"].unique())
ms_months = set(ms_df["month"].unique())
print("Overlap months:", fw_months & ms_months)
