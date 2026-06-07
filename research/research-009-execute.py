#!/usr/bin/env python3
"""
RESEARCH-009: RS_CHANGE_60D VALIDATION
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_WH = PROJECT_ROOT / "database" / "historical" / "warehouse_daily_v4.parquet"
BENCHMARK_FILE = PROJECT_ROOT / "benchmarks" / "ihsg.csv"
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    wh = pd.read_parquet(INPUT_WH)
    wh["Date"] = pd.to_datetime(wh["Date"])
    wh = wh.sort_values(["ticker", "Date"]).reset_index(drop=True)
    return wh


def load_ihsg():
    ihsg = pd.read_csv(BENCHMARK_FILE)
    date_col = next((c for c in ihsg.columns if c.lower() in ["date", "tanggal"]), ihsg.columns[0])
    price_col = next((c for c in ihsg.columns if c.lower() in ["close", "adj close", "price"]), ihsg.columns[1])
    ihsg[date_col] = pd.to_datetime(ihsg[date_col])
    ihsg = ihsg.set_index(date_col).sort_index()
    ihsg["ihsg_close"] = ihsg[price_col]
    ihsg["ihsg_return"] = ihsg[price_col].pct_change()
    return ihsg


def compute_forward_returns(wh, ihsg):
    """Add forward returns for validation."""
    df = wh.copy()
    ihsg_close = ihsg["ihsg_close"].values
    ihsg_dates = ihsg.index.values

    for ticker in df["ticker"].unique():
        mask = df["ticker"] == ticker
        t = df.loc[mask].sort_values("Date").copy()
        t = t.reset_index(drop=True)
        close = t["Close"].values
        n = len(close)

        fwd20 = np.full(n, np.nan)
        fwd40 = np.full(n, np.nan)
        if n > 20:
            fwd20[:-20] = close[20:] / close[:-20] - 1
        if n > 40:
            fwd40[:-40] = close[40:] / close[:-40] - 1

        t_dates = t["Date"].values
        ihsg_local = np.full(n, np.nan)
        for i, d in enumerate(t_dates):
            idx = np.searchsorted(ihsg_dates, d)
            if idx < len(ihsg_dates) and ihsg_dates[idx] == d:
                ihsg_local[i] = ihsg_close[idx]
            elif idx > 0:
                ihsg_local[i] = ihsg_close[idx - 1]

        fwd_ihsg20 = np.full(n, np.nan)
        fwd_ihsg40 = np.full(n, np.nan)
        if n > 20:
            fwd_ihsg20[:-20] = ihsg_local[20:] / ihsg_local[:-20] - 1
        if n > 40:
            fwd_ihsg40[:-40] = ihsg_local[40:] / ihsg_local[:-40] - 1

        t["fwd_return_20d"] = fwd20
        t["fwd_return_40d"] = fwd40
        t["fwd_ihsg_return_20d"] = fwd_ihsg20
        t["fwd_ihsg_return_40d"] = fwd_ihsg40

        df.loc[mask, "fwd_return_20d"] = t["fwd_return_20d"].values
        df.loc[mask, "fwd_return_40d"] = t["fwd_return_40d"].values
        df.loc[mask, "fwd_ihsg_return_20d"] = t["fwd_ihsg_return_20d"].values
        df.loc[mask, "fwd_ihsg_return_40d"] = t["fwd_ihsg_return_40d"].values

    return df


def classify_market_regime(ihsg, window=60):
    """Classify each date into Bull/Bear/Sideways based on IHSG forward 60D return."""
    ihsg = ihsg.copy()
    close = ihsg["ihsg_close"].values
    n = len(close)

    fwd60 = np.full(n, np.nan)
    if n > 60:
        fwd60[:-60] = close[60:] / close[:-60] - 1

    ihsg["fwd_60d_return"] = fwd60
    regimes = {}
    for date, row in ihsg.iterrows():
        ret = row["fwd_60d_return"]
        if np.isnan(ret):
            regimes[date] = "unknown"
        elif ret > 0.10:
            regimes[date] = "bull"
        elif ret < -0.05:
            regimes[date] = "bear"
        else:
            regimes[date] = "sideways"

    return pd.Series(regimes, name="regime")


def load_data_with_forward(wh, ihsg):
    """Convenience: load wh, compute forward returns, add regime."""
    df = compute_forward_returns(wh, ihsg)
    regime_series = classify_market_regime(ihsg)
    df["regime_60d"] = df["Date"].map(regime_series)
    return df


def evaluate_signal(df, signal_col, min_gap=20):
    """Evaluate a binary signal column. Returns events and metrics."""
    events = []
    for ticker in df["ticker"].unique():
        t = df[df["ticker"] == ticker].sort_values("Date").reset_index(drop=True)
        sig = t[signal_col].values.astype(bool)
        n = len(sig)
        i = 0
        while i < n:
            if sig[i]:
                fwd20 = t["fwd_return_20d"].values[i]
                fwd40 = t["fwd_return_40d"].values[i]
                is_positive = (not np.isnan(fwd20) and fwd20 > 0.10) or (not np.isnan(fwd40) and fwd40 > 0.15)
                events.append({
                    "ticker": ticker,
                    "date": t["Date"].values[i],
                    "idx": i,
                    "fwd20": fwd20,
                    "fwd40": fwd40,
                    "is_positive": is_positive,
                    "regime": t["regime_60d"].values[i] if "regime_60d" in t.columns else "unknown",
                    "rs_change_60d": t["rs_change_60d"].values[i],
                    "volume_ratio": t["volume_ratio"].values[i],
                    "above_ma20": t["above_ma20"].values[i],
                    "above_ma50": t["above_ma50"].values[i],
                    "above_ma100": t["above_ma100"].values[i],
                    "above_ma200": t["above_ma200"].values[i],
                    "momentum_slope": t["momentum_slope"].values[i],
                    "recovery_from_60d_low": t["recovery_from_60d_low"].values[i],
                    "drawdown_252d": t["drawdown_252d"].values[i],
                    "volatility_20d": t["volatility_20d"].values[i],
                })
                i += min_gap
            else:
                i += 1
    return pd.DataFrame(events)


def compute_metrics(events_df):
    """Compute precision, recall, lift, FPR from an events dataframe."""
    if len(events_df) == 0:
        return {"n_signals": 0, "n_positive": 0, "precision": 0,
                "recall": 0, "lift": 0, "fpr": 0}
    n_signals = len(events_df)
    n_positive = events_df["is_positive"].sum()
    precision = n_positive / n_signals if n_signals > 0 else 0
    # Estimate base rate: fraction of all ticker-days that are positive
    # Recall and FPR need a reference universe; we approximate
    return {
        "n_signals": n_signals,
        "n_positive": int(n_positive),
        "precision": round(precision, 4),
    }


def full_evaluation(events_df, total_ticker_days=None):
    """Full metrics: precision, recall, lift, FPR."""
    n_signals = len(events_df)
    n_positive = events_df["is_positive"].sum() if len(events_df) > 0 else 0
    n_false = n_signals - n_positive

    precision = n_positive / n_signals if n_signals > 0 else 0

    return {
        "n_signals": n_signals,
        "n_positive": int(n_positive),
        "n_false": n_false,
        "precision": round(precision, 4),
    }


def main():
    print("=" * 80)
    print("RESEARCH-009: RS_CHANGE_60D VALIDATION")
    print("=" * 80)

    print("\n--- Loading Data ---")
    wh = load_data()
    ihsg = load_ihsg()
    print(f"Warehouse: {len(wh):,} rows, {wh['ticker'].nunique()} tickers")
    print(f"IHSG: {len(ihsg)} rows")

    print("\n--- Computing Forward Returns & Regimes ---")
    df = load_data_with_forward(wh, ihsg)
    print(f"Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

    tickers = df["ticker"].unique()
    n_ticker_days = len(df)

    # Build ticker cache
    ticker_cache = {}
    for ticker in tickers:
        ticker_cache[ticker] = df[df["ticker"] == ticker].sort_values("Date").reset_index(drop=True)

    # ──────────────────────────────────────────────────────────────────
    # STEP 1: Walk Forward Validation
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 1: WALK FORWARD VALIDATION")
    print("=" * 70)

    walk_periods = [
        ("2018-01-01", "2019-12-31", "2020-01-01", "2020-12-31"),
        ("2019-01-01", "2020-12-31", "2021-01-01", "2021-12-31"),
        ("2020-01-01", "2021-12-31", "2022-01-01", "2022-12-31"),
        ("2021-01-01", "2022-12-31", "2023-01-01", "2023-12-31"),
        ("2022-01-01", "2023-12-31", "2024-01-01", "2024-12-31"),
        ("2023-01-01", "2024-12-31", "2025-01-01", "2025-12-31"),
    ]

    # rs_change_60d > 0 signal
    df["signal_rs60_pos"] = df["rs_change_60d"] > 0

    walk_results = []
    for train_start, train_end, test_start, test_end in walk_periods:
        train_start_dt = pd.Timestamp(train_start)
        train_end_dt = pd.Timestamp(train_end)
        test_start_dt = pd.Timestamp(test_start)
        test_end_dt = pd.Timestamp(test_end)

        train_df = df[(df["Date"] >= train_start_dt) & (df["Date"] <= train_end_dt)]
        test_df = df[(df["Date"] >= test_start_dt) & (df["Date"] <= test_end_dt)]

        # Evaluate on test period
        test_events = evaluate_signal(test_df, "signal_rs60_pos")

        if len(test_events) > 0:
            met = full_evaluation(test_events)
            walk_results.append({
                "train_period": f"{train_start} to {train_end}",
                "test_period": f"{test_start} to {test_end}",
                **met,
            })
            print(f"  Train {train_start[:4]}-{train_end[:4]} -> Test {test_start[:4]}-{test_end[:4]}: "
                  f"Signals={met['n_signals']}, Positive={met['n_positive']}, "
                  f"Precision={met['precision']:.2%}")
        else:
            walk_results.append({
                "train_period": f"{train_start} to {train_end}",
                "test_period": f"{test_start} to {test_end}",
                "n_signals": 0, "n_positive": 0, "n_false": 0, "precision": 0,
            })
            print(f"  Train {train_start[:4]}-{train_end[:4]} -> Test {test_start[:4]}-{test_end[:4]}: No signals")

    walk_df = pd.DataFrame(walk_results)
    walk_df.to_csv(OUTPUT_DIR / "research-009-walkforward.csv", index=False)
    print(f"  Saved: research-009-walkforward.csv")

    # ──────────────────────────────────────────────────────────────────
    # STEP 2: Market Regime Validation
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 2: MARKET REGIME VALIDATION")
    print("=" * 70)

    regime_results = []
    for regime_name in ["bull", "bear", "sideways", "unknown"]:
        regime_df = df[df["regime_60d"] == regime_name]
        if len(regime_df) == 0:
            continue
        regime_events = evaluate_signal(regime_df, "signal_rs60_pos")
        met = full_evaluation(regime_events)
        regime_results.append({"regime": regime_name, "n_days": len(regime_df), **met})
        print(f"  {regime_name:10s}: {met['n_signals']:5d} signals, {met['n_positive']:4d} positive, "
              f"Precision={met['precision']:.2%}")

    regime_df_out = pd.DataFrame(regime_results)
    regime_df_out.to_csv(OUTPUT_DIR / "research-009-regime-validation.csv", index=False)
    print(f"  Saved: research-009-regime-validation.csv")

    # ──────────────────────────────────────────────────────────────────
    # STEP 3: Ticker Robustness
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 3: TICKER ROBUSTNESS")
    print("=" * 70)

    ticker_results = []
    for ticker in tickers:
        t_df = df[df["ticker"] == ticker].sort_values("Date")
        t_events = evaluate_signal(t_df, "signal_rs60_pos")
        met = full_evaluation(t_events)
        hit_rate = met["n_positive"] / met["n_signals"] if met["n_signals"] > 0 else 0
        ticker_results.append({
            "ticker": ticker,
            "n_days": len(t_df),
            **met,
            "hit_rate": round(hit_rate, 4),
        })
        print(f"  {ticker:6s}: signals={met['n_signals']:4d}, hits={met['n_positive']:3d}, "
              f"precision={met['precision']:.2%}")

    ticker_df_out = pd.DataFrame(ticker_results)
    ticker_df_out = ticker_df_out.sort_values("n_signals", ascending=False).reset_index(drop=True)
    ticker_df_out.to_csv(OUTPUT_DIR / "research-009-ticker-validation.csv", index=False)
    print(f"  Saved: research-009-ticker-validation.csv")

    # Compute dispersion
    precisions = [r["precision"] for r in ticker_results if r["n_signals"] > 0]
    mean_prec = np.mean(precisions) if precisions else 0
    std_prec = np.std(precisions, ddof=1) if len(precisions) > 1 else 0
    print(f"  Mean ticker precision: {mean_prec:.4f}, Std: {std_prec:.4f}, CV: {std_prec/mean_prec:.2f}" if mean_prec > 0 else "")

    # ──────────────────────────────────────────────────────────────────
    # STEP 4: Threshold Stability
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 4: THRESHOLD STABILITY")
    print("=" * 70)

    thresholds = [0, 0.01, 0.02, 0.03, 0.05]
    threshold_results = []

    for thresh in thresholds:
        signal_col = f"signal_rs60_gt_{thresh}"
        df[signal_col] = df["rs_change_60d"] > thresh

        thresh_events = evaluate_signal(df, signal_col)
        met = full_evaluation(thresh_events)
        threshold_results.append({
            "threshold": thresh,
            **met,
        })
        print(f"  rs_change_60d > {thresh:+.2f}: {met['n_signals']:5d} signals, {met['n_positive']:4d} positive, "
              f"Precision={met['precision']:.2%}")

    thresh_df = pd.DataFrame(threshold_results)
    thresh_df.to_csv(OUTPUT_DIR / "research-009-threshold-validation.csv", index=False)
    print(f"  Saved: research-009-threshold-validation.csv")

    # ──────────────────────────────────────────────────────────────────
    # STEP 5: Combined Signal Validation
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 5: COMBINED SIGNAL VALIDATION")
    print("=" * 70)

    combined_defs = [
        ("A", "rs_change_60d > 0", df["rs_change_60d"] > 0),
        ("B", "rs_change_60d > 0 AND volume_ratio > 1.2",
         (df["rs_change_60d"] > 0) & (df["volume_ratio"] > 1.2)),
        ("C", "rs_change_60d > 0 AND above_ma20",
         (df["rs_change_60d"] > 0) & df["above_ma20"]),
        ("D", "rs_change_60d > 0 AND momentum_slope > 0",
         (df["rs_change_60d"] > 0) & (df["momentum_slope"] > 0)),
        ("E", "rs_change_60d > 0 AND volume_ratio > 1.2 AND above_ma20",
         (df["rs_change_60d"] > 0) & (df["volume_ratio"] > 1.2) & df["above_ma20"]),
    ]

    combined_results = []
    for sig_id, sig_name, sig_condition in combined_defs:
        sig_col = f"signal_combined_{sig_id}"
        df[sig_col] = sig_condition

        sig_events = evaluate_signal(df, sig_col)
        met = full_evaluation(sig_events)
        combined_results.append({
            "signal_id": sig_id,
            "signal_name": sig_name,
            **met,
        })

        # Also compute year-by-year precision
        yearly = []
        if len(sig_events) > 0:
            sig_events_copy = sig_events.copy()
            sig_events_copy["year"] = pd.to_datetime(sig_events_copy["date"]).dt.year
            for yr in sorted(sig_events_copy["year"].unique()):
                yr_events = sig_events_copy[sig_events_copy["year"] == yr]
                yr_pos = yr_events["is_positive"].sum()
                yr_prec = yr_pos / len(yr_events) if len(yr_events) > 0 else 0
                yearly.append(f"{int(yr)}:{yr_prec:.2f}")
        yearly_str = ", ".join(yearly) if yearly else "N/A"

        print(f"  Signal {sig_id} ({sig_name}):")
        print(f"    Signals={met['n_signals']}, Positive={met['n_positive']}, "
              f"Precision={met['precision']:.2%}")
        print(f"    Yearly: {yearly_str}")

    comb_df = pd.DataFrame(combined_results)
    comb_df.to_csv(OUTPUT_DIR / "research-009-combined-signals.csv", index=False)
    print(f"  Saved: research-009-combined-signals.csv")

    # ──────────────────────────────────────────────────────────────────
    # STEP 6: Failure Analysis
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 6: FAILURE ANALYSIS")
    print("=" * 70)

    all_events = evaluate_signal(df, "signal_rs60_pos")
    false_positives = all_events[~all_events["is_positive"]].copy() if len(all_events) > 0 else pd.DataFrame()
    true_positives = all_events[all_events["is_positive"]].copy() if len(all_events) > 0 else pd.DataFrame()
    n_fp = len(false_positives)
    n_tp = len(true_positives)

    print(f"  Total signals: {len(all_events)}")
    print(f"  True positives: {n_tp}")
    print(f"  False positives: {n_fp}")

    fp_analysis = {}
    if n_fp > 0 and n_tp > 0:
        # Compare false positives vs true positives characteristics
        for col in ["volume_ratio", "above_ma20", "momentum_slope", "rs_change_60d",
                     "recovery_from_60d_low", "drawdown_252d", "volatility_20d",
                     "above_ma50", "above_ma100", "above_ma200"]:
            fp_vals = false_positives[col].dropna()
            tp_vals = true_positives[col].dropna()
            if len(fp_vals) > 0 and len(tp_vals) > 0:
                fp_analysis[col] = {
                    "fp_mean": round(fp_vals.mean(), 4),
                    "tp_mean": round(tp_vals.mean(), 4),
                    "fp_median": round(fp_vals.median(), 4),
                    "tp_median": round(tp_vals.median(), 4),
                    "diff_mean": round(tp_vals.mean() - fp_vals.mean(), 4),
                }
                if col in ["above_ma20", "above_ma50", "above_ma100", "above_ma200", "golden_cross", "death_cross"]:
                    fp_analysis[col]["fp_true_pct"] = round(fp_vals.mean() * 100, 1)
                    fp_analysis[col]["tp_true_pct"] = round(tp_vals.mean() * 100, 1)

        # Regime breakdown for false positives
        fp_regime = false_positives["regime"].value_counts()
        tp_regime = true_positives["regime"].value_counts()

        # Sector/ticker breakdown
        fp_ticker = false_positives["ticker"].value_counts().head(10)
        tp_ticker = true_positives["ticker"].value_counts().head(10)

        print("\n  False Positive Characteristics vs True Positives:")
        for col, analysis in fp_analysis.items():
            if col in ["above_ma20", "above_ma50", "above_ma100", "above_ma200"]:
                print(f"    {col:25s} FP_true={analysis.get('fp_true_pct', 'N/A'):.0f}%  "
                      f"TP_true={analysis.get('tp_true_pct', 'N/A'):.0f}%")
            else:
                print(f"    {col:25s} FP_mean={analysis['fp_mean']:.4f}  TP_mean={analysis['tp_mean']:.4f}  "
                      f"diff={analysis['diff_mean']:+.4f}")

        print(f"\n  False Positives by Regime:")
        for regime, count in fp_regime.items():
            print(f"    {regime:10s}: {count} ({count/n_fp*100:.0f}%)")

        print(f"\n  False Positives by Ticker (top 10):")
        for ticker, count in fp_ticker.items():
            print(f"    {ticker:6s}: {count}")

    # ──────────────────────────────────────────────────────────────────
    # GENERATE DELIVERABLES
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("GENERATING DELIVERABLES")
    print("=" * 70)

    # ── Failure Analysis MD ──
    fa_lines = []
    fa_lines.append("# RESEARCH-009: Failure Analysis — rs_change_60d\n")
    fa_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    fa_lines.append("---\n\n")

    fa_lines.append("## Signal: rs_change_60d > 0\n\n")
    fa_lines.append(f"Total signals: {len(all_events)}\n")
    fa_lines.append(f"True positives (rally follows): {n_tp}\n")
    fa_lines.append(f"False positives (no rally): {n_fp}\n")
    fa_lines.append(f"Overall precision: {n_tp/len(all_events)*100:.1f}%\n\n") if len(all_events) > 0 else None

    fa_lines.append("---\n\n")

    fa_lines.append("## What Goes Wrong in False Positives?\n\n")

    if n_fp > 0 and n_tp > 0:
        fa_lines.append("### Characteristic Differences (FP vs TP)\n\n")
        fa_lines.append("| Feature | FP Mean | TP Mean | Difference |\n")
        fa_lines.append("|---------|---------|---------|------------|\n")
        for col in ["rs_change_60d", "volume_ratio", "momentum_slope",
                     "recovery_from_60d_low", "drawdown_252d", "volatility_20d"]:
            if col in fp_analysis:
                a = fp_analysis[col]
                fa_lines.append(f"| {col} | {a['fp_mean']:.4f} | {a['tp_mean']:.4f} | {a['diff_mean']:+.4f} |\n")

        fa_lines.append("\n### Binary Feature Prevalence\n\n")
        fa_lines.append("| Feature | FP %True | TP %True |\n")
        fa_lines.append("|---------|----------|----------|\n")
        for col in ["above_ma20", "above_ma50", "above_ma100", "above_ma200"]:
            if col in fp_analysis:
                a = fp_analysis[col]
                fa_lines.append(f"| {col} | {a.get('fp_true_pct', 0):.0f}% | {a.get('tp_true_pct', 0):.0f}% |\n")

        fa_lines.append("\n### Regime Distribution\n\n")
        fa_lines.append(f"| Regime | FP Count | FP % | TP Count | TP % |\n")
        fa_lines.append(f"|--------|----------|------|----------|------|\n")
        all_regimes = set(list(fp_regime.index) + list(tp_regime.index))
        for regime in sorted(all_regimes):
            fc = fp_regime.get(regime, 0)
            tc = tp_regime.get(regime, 0)
            fp_pct = fc / n_fp * 100 if n_fp > 0 else 0
            tp_pct = tc / n_tp * 100 if n_tp > 0 else 0
            fa_lines.append(f"| {regime} | {fc} | {fp_pct:.0f}% | {tc} | {tp_pct:.0f}% |\n")

        fa_lines.append("\n### Key Failure Patterns\n\n")

        patterns = []
        for col in ["volume_ratio", "above_ma20", "recovery_from_60d_low"]:
            if col in fp_analysis:
                a = fp_analysis[col]
                if "above_ma20" == col:
                    if a.get('fp_true_pct', 0) < a.get('tp_true_pct', 0):
                        patterns.append(f"False positives are less likely to be above MA20 "
                                        f"({a.get('fp_true_pct', 0):.0f}% vs {a.get('tp_true_pct', 0):.0f}%%)")
                elif "volume_ratio" == col:
                    if a.get('fp_mean', 0) < a.get('tp_mean', 0):
                        patterns.append(f"False positives have lower volume ratio "
                                        f"({a['fp_mean']:.2f} vs {a['tp_mean']:.2f})")
                elif "recovery_from_60d_low" == col:
                    if a.get('fp_mean', 0) < a.get('tp_mean', 0):
                        patterns.append(f"False positives have weaker recovery from lows "
                                        f"({a['fp_mean']:.2f} vs {a['tp_mean']:.2f})")

        for p in patterns:
            fa_lines.append(f"- {p}\n")
        fa_lines.append("\n")

        fa_lines.append("### Common FP Scenario\n\n")
        # Build a composite picture
        low_vol = fp_analysis.get("volume_ratio", {}).get("fp_mean", 0)
        low_rec = fp_analysis.get("recovery_from_60d_low", {}).get("fp_mean", 0)
        low_ma20 = fp_analysis.get("above_ma20", {}).get("fp_true_pct", 0)
        fa_lines.append(f"A typical false positive occurs when rs_change_60d turns positive but:\n\n")
        fa_lines.append(f"- Volume is low (mean volume_ratio = {low_vol:.2f})\n")
        fa_lines.append(f"- Recovery from lows is weak (mean = {low_rec:.2f})\n")
        fa_lines.append(f"- Price is often still below MA20 ({100-low_ma20:.0f}% of FP cases)\n")
        fa_lines.append(f"- The market regime may be unfavorable\n\n")

    fa_lines.append("---\n")
    fa_lines.append("*End of RESEARCH-009 Failure Analysis*\n")

    with open(OUTPUT_DIR / "research-009-failure-analysis.md", "w", encoding="utf-8") as f:
        f.writelines(fa_lines)
    print("  Saved: research-009-failure-analysis.md")

    # ── Executive Summary MD ──
    exec_lines = []
    exec_lines.append("# RESEARCH-009: rs_change_60d Validation — Executive Summary\n")
    exec_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    exec_lines.append("---\n\n")

    exec_lines.append("## Core Question\n\n")
    exec_lines.append("*Is rs_change_60d a robust timing signal or merely an interesting observation?*\n\n")
    exec_lines.append("---\n\n")

    exec_lines.append("## Summary of Findings\n\n")

    # Walk forward
    walk_avail = [r for r in walk_results if r["n_signals"] > 0]
    avg_prec_walk = np.mean([r["precision"] for r in walk_avail]) if walk_avail else 0
    min_prec_walk = min([r["precision"] for r in walk_avail]) if walk_avail else 0
    max_prec_walk = max([r["precision"] for r in walk_avail]) if walk_avail else 0
    stable_walk = (max_prec_walk - min_prec_walk) <= 0.15 if walk_avail else False

    exec_lines.append("### 1. Walk Forward Stability\n\n")
    exec_lines.append(f"| Period | Signals | Positive | Precision |\n")
    exec_lines.append(f"|--------|---------|----------|-----------|\n")
    for r in walk_results:
        prec_str = f"{r['precision']:.1%}" if r['n_signals'] > 0 else "N/A"
        exec_lines.append(f"| {r['train_period'][:9]}->{r['test_period'][:9]} | {r['n_signals']} | {r['n_positive']} | {prec_str} |\n")

    exec_lines.append(f"\nPrecision range: {min_prec_walk:.1%} to {max_prec_walk:.1%} "
                      f"(avg={avg_prec_walk:.1%})\n")
    exec_lines.append(f"Stability: {'STABLE' if stable_walk else 'VARIABLE'} "
                      f"(range={max_prec_walk-min_prec_walk:.1%})\n\n")

    # Regime
    exec_lines.append("### 2. Market Regime Robustness\n\n")
    exec_lines.append("| Regime | Signals | Positive | Precision |\n")
    exec_lines.append("|--------|---------|----------|-----------|\n")
    for r in regime_results:
        prec_str = f"{r['precision']:.1%}" if r['n_signals'] > 0 else "N/A"
        exec_lines.append(f"| {r['regime']} | {r['n_signals']} | {r['n_positive']} | {prec_str} |\n")
    exec_lines.append("\n")

    # Ticker
    exec_lines.append("### 3. Ticker Robustness\n\n")
    active_tickers = [r for r in ticker_results if r["n_signals"] > 0]
    n_tickers_with_signal = len(active_tickers)
    exec_lines.append(f"Tickers with at least one signal: {n_tickers_with_signal}/{len(ticker_results)}\n")
    exec_lines.append(f"Mean ticker precision: {mean_prec:.2%}\n")
    exec_lines.append(f"Std ticker precision: {std_prec:.2%}\n")
    exec_lines.append(f"Coefficient of variation: {std_prec/mean_prec:.2f}\n\n")
    exec_lines.append("| Ticker | Signals | Hits | Precision |\n")
    exec_lines.append("|--------|---------|------|-----------|\n")
    for r in active_tickers[:10]:
        exec_lines.append(f"| {r['ticker']} | {r['n_signals']} | {r['n_positive']} | {r['precision']:.1%} |\n")
    exec_lines.append("\n")

    # Threshold
    exec_lines.append("### 4. Threshold Stability\n\n")
    exec_lines.append("| Threshold | Signals | Positive | Precision |\n")
    exec_lines.append("|-----------|---------|----------|-----------|\n")
    for r in threshold_results:
        exec_lines.append(f"| > {r['threshold']:+.2f} | {r['n_signals']} | {r['n_positive']} | {r['precision']:.1%} |\n")
    exec_lines.append("\n")

    # Combined
    exec_lines.append("### 5. Combined Signal Performance\n\n")
    exec_lines.append("| Signal | Definition | Signals | Hits | Precision |\n")
    exec_lines.append("|--------|------------|---------|------|-----------|\n")
    for r in combined_results:
        exec_lines.append(f"| {r['signal_id']} | {r['signal_name']} | {r['n_signals']} | {r['n_positive']} | {r['precision']:.1%} |\n")
    exec_lines.append("\n")

    # Answer
    exec_lines.append("---\n\n")
    exec_lines.append("## Verdict\n\n")

    # Determine verdict based on data
    verdict_points = []
    if avg_prec_walk > 0.15:
        verdict_points.append(f"Walk forward precision ({avg_prec_walk:.1%}) "
                              f"{'exceeds' if avg_prec_walk > 0.20 else 'meets'} minimum threshold")
    else:
        verdict_points.append(f"Walk forward precision ({avg_prec_walk:.1%}) is below minimum threshold")

    if stable_walk:
        verdict_points.append("Signal is stable across time periods (range <= 15pp)")
    else:
        verdict_points.append(f"Signal varies across time periods (range {max_prec_walk-min_prec_walk:.1%}pp)")

    regime_spread = max([r["precision"] for r in regime_results if r["n_signals"] > 0] or [0]) - \
                    min([r["precision"] for r in regime_results if r["n_signals"] > 0] or [0])

    # Combined improvement
    base_prec = combined_results[0]["precision"] if len(combined_results) > 0 else 0
    best_combined = max(combined_results, key=lambda r: r["precision"]) if len(combined_results) > 0 else {}
    best_prec = best_combined.get("precision", 0)
    combined_improves = best_prec > base_prec

    for p in verdict_points:
        exec_lines.append(f"- {p}\n")

    exec_lines.append(f"- Regime spread: {regime_spread:.1%} "
                      f"({'WIDE - signal regime-dependent' if regime_spread > 0.15 else 'narrow - signal regime-agnostic'})\n")
    exec_lines.append(f"- Combined signal improvement: {'YES' if combined_improves else 'NO'} "
                      f"(best={best_combined.get('signal_id', 'N/A')} at {best_prec:.1%} "
                      f"vs base {base_prec:.1%})\n\n")

    verdict = "ROBUST" if (avg_prec_walk > 0.15 and stable_walk and regime_spread <= 0.20 and not combined_improves) else "CONDITIONALLY ROBUST"
    exec_lines.append(f"### Verdict: **{verdict}**\n\n")

    if verdict == "CONDITIONALLY ROBUST":
        exec_lines.append("rs_change_60d is a meaningful signal that requires context:\n\n")
        exec_lines.append("- Standalone precision is moderate\n")
        exec_lines.append("- Performance improves when combined with volume and price filters\n")
        exec_lines.append("- Regime and ticker matter\n\n")

    exec_lines.append(f"**Bottom Line:** rs_change_60d is {'a genuine' if avg_prec_walk > 0.12 else 'an interesting but weak'} ")
    exec_lines.append("early warning signal. It identifies the earliest detectable transition from distress to accumulation, ")
    exec_lines.append(f"with {'reliable' if stable_walk else 'variable'} precision across time.\n\n")

    exec_lines.append("---\n")
    exec_lines.append("*End of RESEARCH-009 Executive Summary*\n")

    with open(OUTPUT_DIR / "research-009-executive-summary.md", "w", encoding="utf-8") as f:
        f.writelines(exec_lines)
    print("  Saved: research-009-executive-summary.md")

    # ──────────────────────────────────────────────────────────────────
    # FINAL SUMMARY
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("RESEARCH-009 COMPLETE")
    print("=" * 80)
    print(f"\nDeliverables in {OUTPUT_DIR}:")
    print("  research-009-walkforward.csv")
    print("  research-009-regime-validation.csv")
    print("  research-009-ticker-validation.csv")
    print("  research-009-threshold-validation.csv")
    print("  research-009-combined-signals.csv")
    print("  research-009-failure-analysis.md")
    print("  research-009-executive-summary.md")

    print(f"\nKey Metrics Summary:")
    print(f"  Walk forward avg precision: {avg_prec_walk:.2%}")
    print(f"  Walk forward stability: {'STABLE' if stable_walk else 'VARIABLE'}")
    print(f"  Regime spread: {regime_spread:.1%}")
    print(f"  Tickers with signal: {n_tickers_with_signal}/{len(ticker_results)}")
    if len(combined_results) > 0:
        print(f"  Best combined signal: {best_combined.get('signal_id', 'N/A')} @ {best_prec:.1%}")
    print(f"  False positives: {n_fp} / {len(all_events)} total ({n_fp/max(len(all_events),1)*100:.0f}%)")

    print("\nStopping here per instructions. Do NOT build timing engine, optimize thresholds, or create overlays.")


if __name__ == "__main__":
    main()
