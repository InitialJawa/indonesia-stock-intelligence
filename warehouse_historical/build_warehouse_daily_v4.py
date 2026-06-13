#!/usr/bin/env python3
"""
Build Warehouse Daily V4 — ISI's "Daily Timing Brain" foundation!
Generates warehouse_daily_v4.parquet with all required fields!
"""

import json
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
import yfinance as yf

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(PROJECT_ROOT))
from utils.config_loader import load_universe

DAILY_PRICES_DIR = PROJECT_ROOT / "output" / "history_prices"
BENCHMARK_FILE = PROJECT_ROOT / "benchmarks" / "ihsg.csv"
OUTPUT_DIR = PROJECT_ROOT / "database" / "historical"
OUTPUT_PATH = OUTPUT_DIR / "warehouse_daily_v4.parquet"

START_DATE = "2022-01-01"


def load_universe():
    return [t for t in load_universe("IDX80") if t != "UNVR.JK"]


def download_missing_prices(tickers):
    """Download any missing daily prices (uses existing first, adds new if missing)."""
    DAILY_PRICES_DIR.mkdir(parents=True, exist_ok=True)
    for ticker in tickers:
        fp = DAILY_PRICES_DIR / f"{ticker}.csv"
        if not fp.exists():
            print(f"Downloading {ticker} daily prices...")
            try:
                data = yf.download(ticker, start=START_DATE, auto_adjust=True, progress=False)
                if data.empty:
                    print(f"Skip {ticker} — no data")
                    continue
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                data = data.reset_index()
                data.to_csv(fp, index=False)
                print(f"Saved {ticker} to {fp}")
            except Exception as e:
                print(f"{ticker} failed: {e}")


def load_benchmark():
    """Load IHSG daily prices from benchmarks/ihsg.csv!"""
    ihsg_df = pd.read_csv(BENCHMARK_FILE)
    date_col = next((c for c in ihsg_df.columns if c.lower() in ["date", "tanggal"]), ihsg_df.columns[0])
    price_col = next((c for c in ihsg_df.columns if c.lower() in ["close", "adj close", "price"]), ihsg_df.columns[1])
    ihsg_df[date_col] = pd.to_datetime(ihsg_df[date_col])
    return ihsg_df.set_index(date_col).sort_index()[price_col].rename("ihsg_close").astype(float)


def process_ticker_daily(ticker, ihsg_series):
    """Process one ticker and compute all fields."""
    fp = DAILY_PRICES_DIR / f"{ticker}.csv"
    if not fp.exists():
        return None
    df = pd.read_csv(fp)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    df["ticker"] = ticker

    # Compute basic OHLCV returns
    df["daily_return"] = df["Close"].pct_change()
    for days in [20, 60, 120, 252]:
        df[f"{days}d_return"] = df["Close"].pct_change(days)

    # Rolling highs & lows
    for days in [20, 60, 120, 252]:
        df[f"{days}d_high"] = df["High"].rolling(days, min_periods=1).max()
        df[f"{days}d_low"] = df["Low"].rolling(days, min_periods=1).min()

    # Distance from 252d high & drawdown
    df["distance_from_high_252d"] = (df["Close"] / df["252d_high"]) - 1
    df["drawdown_252d"] = (df["Close"] / df["252d_high"]) - 1  # same as distance_from_high for drawdown from high

    # Recovery from 60d low
    df["recovery_from_60d_low"] = (df["Close"] / df["60d_low"]) - 1

    # Volatility (20d and 60d)
    for days in [20, 60]:
        df[f"volatility_{days}d"] = df["daily_return"].rolling(days, min_periods=days//2).std() * np.sqrt(252)  # annualized!

    # Volume metrics
    df["avg_volume_20d"] = df["Volume"].rolling(20, min_periods=10).mean()
    df["volume_ratio"] = df["Volume"] / df["avg_volume_20d"]

    # Relative Strength vs IHSG (20/60/120/252d)
    # First merge IHSG close
    df = df.join(ihsg_series, how="left")
    for days in [20, 60, 120, 252]:
        df[f"rs_{days}d"] = (
            (df["Close"].pct_change(days)) - (df["ihsg_close"].pct_change(days))
        )

    # RS Change (change in RS20/60 over 20/60 days)
    df["rs_change_20d"] = df["rs_20d"] - df["rs_20d"].shift(20)
    df["rs_change_60d"] = df["rs_60d"] - df["rs_60d"].shift(60)

    # Momentum slope: slope of 20d returns over last 60 days
    def calc_slope(arr):
        # arr is numpy array when raw=True!
        non_nan = arr[~np.isnan(arr)]
        if len(non_nan) < 20:
            return np.nan
        x = np.arange(len(non_nan))
        slope, intercept = np.polyfit(x, non_nan, 1)
        return slope
    df["momentum_slope"] = (
        df["20d_return"]
        .rolling(window=60, min_periods=30)
        .apply(calc_slope, raw=True)
    )

    # Moving Averages
    for ma in [20, 50, 100, 200]:
        df[f"ma{ma}"] = df["Close"].rolling(ma, min_periods=ma//2).mean()
        df[f"above_ma{ma}"] = df["Close"] > df[f"ma{ma}"]

    # Golden Cross / Death Cross
    df["golden_cross"] = (
        (df["ma50"] > df["ma200"]) & (df["ma50"].shift(1) <= df["ma200"].shift(1))
    )
    df["death_cross"] = (
        (df["ma50"] < df["ma200"]) & (df["ma50"].shift(1) >= df["ma200"].shift(1))
    )

    return df.reset_index()


def main():
    print("="*80)
    print("BUILDING WAREHOUSE DAILY V4 — Daily Timing Brain")
    print("="*80)
    tickers = load_universe()
    print(f"Universe: {len(tickers)} IDX30 tickers")
    download_missing_prices(tickers)

    print("\nLoading benchmark (IHSG)...")
    ihsg = load_benchmark()
    all_records = []

    for i, ticker in enumerate(tickers, 1):
        print(f"Processing [{i}/{len(tickers)}] {ticker}...")
        ticker_df = process_ticker_daily(ticker, ihsg)
        if ticker_df is not None:
            all_records.append(ticker_df)

    if not all_records:
        print("Error: No data!")
        return

    final_df = pd.concat(all_records, ignore_index=True)
    final_df = final_df.sort_values(["Date", "ticker"]).reset_index(drop=True)
    # Select final columns (only those that exist!)
    final_columns = [
        "Date", "ticker",
        "Open", "High", "Low", "Close", "Volume",
        "daily_return",
        "20d_return", "60d_return", "120d_return", "252d_return",
        "20d_high", "60d_high", "120d_high", "252d_high",
        "20d_low", "60d_low", "120d_low", "252d_low",
        "distance_from_high_252d",
        "drawdown_252d",
        "recovery_from_60d_low",
        "volatility_20d", "volatility_60d",
        "avg_volume_20d", "volume_ratio",
        "rs_20d", "rs_60d", "rs_120d", "rs_252d",
        "rs_change_20d", "rs_change_60d",
        "momentum_slope",
        "ma20", "ma50", "ma100", "ma200",
        "above_ma20", "above_ma50", "above_ma100", "above_ma200",
        "golden_cross", "death_cross"
    ]
    # Keep only columns that are actually present!
    final_df = final_df[[col for col in final_columns if col in final_df.columns]]

    print(f"\nWriting to {OUTPUT_PATH}...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(OUTPUT_PATH, index=False)

    print("\n" + "="*80)
    print("WAREHOUSE DAILY V4 COMPLETE")
    print("="*80)
    print(f"Total records: {len(final_df)}")
    print(f"Unique tickers: {final_df['ticker'].nunique()}")
    print(f"Date range: {final_df['Date'].min().date()} to {final_df['Date'].max().date()}")
    print(f"Columns: {list(final_df.columns)}")


if __name__ == "__main__":
    main()
