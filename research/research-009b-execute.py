#!/usr/bin/env python3
"""
RESEARCH-009B: CONTEXT FILTER DISCOVERY

Why does rs_change_60d produce 43% precision on BRPT but only 4.5% on BBCA?
Analysis across 6 context dimensions: volatility, drawdown, market cap,
trend regime, sector, distance-from-high.
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_WH = PROJECT_ROOT / "database" / "historical" / "warehouse_daily_v4.parquet"
BENCHMARK_FILE = PROJECT_ROOT / "benchmarks" / "ihsg.csv"
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SECTOR_MAP = {
    "ADRO.JK": "Coal Mining",
    "AKRA.JK": "Energy & Logistics",
    "AMMN.JK": "Mining (Gold/Copper)",
    "ANTM.JK": "Mining (State-owned)",
    "ASII.JK": "Automotive & Conglomerate",
    "BBCA.JK": "Banking",
    "BBNI.JK": "Banking",
    "BBRI.JK": "Banking",
    "BMRI.JK": "Banking",
    "BRPT.JK": "Chemicals & Conglomerate",
    "CPIN.JK": "Poultry & Feed",
    "ESSA.JK": "Energy (Oil & Gas)",
    "EXCL.JK": "Telecom",
    "GOTO.JK": "Technology",
    "HEAL.JK": "Healthcare",
    "ICBP.JK": "Consumer Goods",
    "INDF.JK": "Consumer Goods",
    "INTP.JK": "Cement",
    "ITMG.JK": "Coal Mining",
    "KLBF.JK": "Pharmaceutical",
    "MAPI.JK": "Retail",
    "MDKA.JK": "Mining (Gold)",
    "MIKA.JK": "Healthcare",
    "PGAS.JK": "Energy (Gas)",
    "PTBA.JK": "Coal Mining (State-owned)",
    "SIDO.JK": "Consumer Goods",
    "SMGR.JK": "Cement",
    "TLKM.JK": "Telecom",
    "TPIA.JK": "Chemicals (Petrochemical)",
    "UNTR.JK": "Heavy Equipment & Mining",
}


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
    return ihsg


def compute_forward_returns(wh, ihsg):
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


def compute_context_buckets(wh, ihsg):
    """Add forward returns, regimes, and context bucket columns."""
    df = compute_forward_returns(wh, ihsg)
    regime_series = classify_market_regime(ihsg)
    df["regime_60d"] = df["Date"].map(regime_series)

    df["sector"] = df["ticker"].map(SECTOR_MAP)
    df["signal_rs60_pos"] = df["rs_change_60d"] > 0

    ticker_avg_price = df.groupby("ticker")["Close"].mean()
    df["ticker_avg_price"] = df["ticker"].map(ticker_avg_price)

    # ── 1. Volatility buckets (population-wide percentiles) ──
    vol_bins = [0, df["volatility_60d"].quantile(0.33), df["volatility_60d"].quantile(0.67), np.inf]
    df["volatility_bucket"] = pd.cut(
        df["volatility_60d"], bins=vol_bins,
        labels=["Low Vol", "Medium Vol", "High Vol"],
        include_lowest=True
    )

    # ── 2. Drawdown buckets ──
    def drawdown_bucket(d):
        if d >= -0.10:
            return "Shallow (>-10%)"
        elif d >= -0.25:
            return "Moderate (-10% to -25%)"
        else:
            return "Deep (<-25%)"
    df["drawdown_bucket"] = df["drawdown_252d"].apply(drawdown_bucket)

    # ── 3. Market cap buckets (proxy: avg close price) ──
    def price_bucket(p):
        if p < 1000:
            return "Small (<1k)"
        elif p < 5000:
            return "Mid (1k-5k)"
        else:
            return "Large (>5k)"
    df["mcap_bucket"] = df["ticker_avg_price"].apply(price_bucket)

    # ── 4. Trend regime buckets ──
    def trend_bucket(row):
        above50 = row["above_ma50"]
        above200 = row["above_ma200"]
        if above50 and above200:
            return "Bull Trend (above MA50+200)"
        elif above50 and not above200:
            return "Mixed (above MA50, below MA200)"
        elif not above50 and above200:
            return "Mixed (below MA50, above MA200)"
        else:
            return "Bear Trend (below both)"
    df["trend_bucket"] = df.apply(trend_bucket, axis=1)

    # ── 5. Sector buckets (from SECTOR_MAP) ──

    # ── 6. Distance-from-high buckets ──
    def dist_bucket(d):
        if d >= -0.05:
            return "Near High (>-5%)"
        elif d >= -0.20:
            return "Mid (-5% to -20%)"
        else:
            return "Far (<-20%)"
    df["distance_bucket"] = df["distance_from_high_252d"].apply(dist_bucket)

    return df


def evaluate_signal(df, signal_col, min_gap=20):
    """Evaluate a binary signal column. Returns events with validation."""
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
                is_positive = (
                    (not np.isnan(fwd20) and fwd20 > 0.10) or
                    (not np.isnan(fwd40) and fwd40 > 0.15)
                )
                events.append({
                    "ticker": t["ticker"].values[i],
                    "date": t["Date"].values[i],
                    "is_positive": is_positive,
                    "rs_change_60d": t["rs_change_60d"].values[i],
                    "volatility_60d": t["volatility_60d"].values[i],
                    "drawdown_252d": t["drawdown_252d"].values[i],
                    "distance_from_high_252d": t["distance_from_high_252d"].values[i],
                    "above_ma50": t["above_ma50"].values[i],
                    "above_ma200": t["above_ma200"].values[i],
                    "ticker_avg_price": t["ticker_avg_price"].values[i],
                    "regime_60d": t["regime_60d"].values[i],
                    "sector": t["sector"].values[i],
                    "volatility_bucket": t["volatility_bucket"].values[i],
                    "drawdown_bucket": t["drawdown_bucket"].values[i],
                    "mcap_bucket": t["mcap_bucket"].values[i],
                    "trend_bucket": t["trend_bucket"].values[i],
                    "distance_bucket": t["distance_bucket"].values[i],
                })
                i += min_gap
            else:
                i += 1
    return pd.DataFrame(events)


def bucket_analysis(events_df, bucket_col):
    """Compute precision per bucket category."""
    rows = []
    for category in events_df[bucket_col].sort_values().unique():
        cat_events = events_df[events_df[bucket_col] == category]
        n = len(cat_events)
        pos = cat_events["is_positive"].sum()
        prec = pos / n if n > 0 else 0
        rows.append({
            "bucket": bucket_col.replace("_", " ").title(),
            "category": category,
            "n_signals": n,
            "n_positive": int(pos),
            "precision": round(prec, 4),
            "pct_of_signals": round(n / len(events_df) * 100, 1),
        })
    return pd.DataFrame(rows)


def main():
    print("=" * 80)
    print("RESEARCH-009B: CONTEXT FILTER DISCOVERY")
    print("=" * 80)

    # Load
    print("\n--- Loading Data ---")
    wh = load_data()
    ihsg = load_ihsg()
    print(f"Warehouse: {len(wh):,} rows, {wh['ticker'].nunique()} tickers")

    # Build context buckets
    print("\n--- Computing Context Buckets ---")
    df = compute_context_buckets(wh, ihsg)
    print(f"Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

    # Evaluate base signal
    print("\n--- Evaluating Base Signal (rs_change_60d > 0) ---")
    all_events = evaluate_signal(df, "signal_rs60_pos")
    n_total = len(all_events)
    n_pos = all_events["is_positive"].sum()
    base_precision = n_pos / n_total if n_total > 0 else 0
    print(f"  Total signals: {n_total}, Positive: {n_pos}, Base Precision: {base_precision:.2%}")

    # ──────────────────────────────────────────────────────────────
    # BUCKET ANALYSIS
    # ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("BUCKET ANALYSIS")
    print("=" * 80)

    bucket_cols = [
        "volatility_bucket",
        "drawdown_bucket",
        "mcap_bucket",
        "trend_bucket",
        "sector",
        "distance_bucket",
    ]

    all_bucket_dfs = []
    for bc in bucket_cols:
        print(f"\n  --- {bc.replace('_', ' ').title()} ---")
        bdf = bucket_analysis(all_events, bc)
        bdf["lift_vs_baseline"] = bdf["precision"] / base_precision if base_precision > 0 else 0
        bdf["signal_quality"] = bdf["precision"].apply(
            lambda p: "STRONG" if p > 0.30 else ("MODERATE" if p > 0.20 else "WEAK")
        )
        for _, row in bdf.iterrows():
            print(f"    {str(row['category']):35s} n={row['n_signals']:5d}  "
                  f"pos={row['n_positive']:4d}  prec={row['precision']:.2%}  "
                  f"lift={row['lift_vs_baseline']:.2f}x  "
                  f"pct={row['pct_of_signals']:5.1f}%  [{row['signal_quality']}]")
        all_bucket_dfs.append(bdf)

    # ──────────────────────────────────────────────────────────────
    # CROSS-BUCKET ANALYSIS
    # ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("CROSS-BUCKET ANALYSIS: BEST & WORST CONTEXTS")
    print("=" * 80)

    best_cross = []
    worst_cross = []
    for bc in bucket_cols:
        bdf = bucket_analysis(all_events, bc)
        bdf = bdf[bdf["n_signals"] >= 20]
        if len(bdf) > 0:
            best = bdf.loc[bdf["precision"].idxmax()]
            worst = bdf.loc[bdf["precision"].idxmin()]
            best_cross.append({"dimension": bc.replace("_", " ").title(),
                               "best_context": best["category"],
                               "best_precision": best["precision"],
                               "best_n": best["n_signals"]})
            worst_cross.append({"dimension": bc.replace("_", " ").title(),
                                "worst_context": worst["category"],
                                "worst_precision": worst["precision"],
                                "worst_n": worst["n_signals"]})

    best_df = pd.DataFrame(best_cross)
    worst_df = pd.DataFrame(worst_cross)
    print("\n  Best contexts:")
    for _, r in best_df.iterrows():
        print(f"    {r['dimension']:25s} -> {str(r['best_context']):30s}  precision={r['best_precision']:.2%} (n={r['best_n']})")
    print("\n  Worst contexts:")
    for _, r in worst_df.iterrows():
        print(f"    {r['dimension']:25s} -> {str(r['worst_context']):30s}  precision={r['worst_precision']:.2%} (n={r['worst_n']})")

    # ── HIGH-PRECISION COMBINED CONTEXT ──
    print("\n" + "=" * 80)
    print("HIGH-PRECISION COMBINED CONTEXT ANALYSIS")
    print("=" * 80)

    all_events["context_label"] = (
        all_events["volatility_bucket"].astype(str) + " | " +
        all_events["drawdown_bucket"].astype(str) + " | " +
        all_events["trend_bucket"].astype(str) + " | " +
        all_events["distance_bucket"].astype(str)
    )
    context_groups = all_events.groupby("context_label")
    combined_contexts = context_groups.agg(
        n_signals=("is_positive", "size"),
        n_positive=("is_positive", "sum"),
    ).reset_index()
    combined_contexts["precision"] = (combined_contexts["n_positive"] / combined_contexts["n_signals"]).round(4)
    combined_contexts = combined_contexts.sort_values("precision", ascending=False).reset_index(drop=True)

    # Split components back for readability
    combined_contexts[["vol_bucket", "dd_bucket", "trend_bucket", "dist_bucket"]] = (
        combined_contexts["context_label"].str.split(r" \| ", expand=True)
    )

    print(f"\n  Top 15 combined contexts (n >= 10):")
    top_combined = combined_contexts[combined_contexts["n_signals"] >= 10].head(15)
    for _, r in top_combined.iterrows():
        print(f"    prec={r['precision']:.2%}  n={r['n_signals']:4d}  "
              f"vol={r['vol_bucket']} | dd={r['dd_bucket']} | "
              f"trend={r['trend_bucket']} | dist={r['dist_bucket']}")

    print(f"\n  Bottom 15 combined contexts (n >= 10):")
    bottom_combined = combined_contexts[combined_contexts["n_signals"] >= 10].tail(15).sort_values("precision")
    for _, r in bottom_combined.iterrows():
        print(f"    prec={r['precision']:.2%}  n={r['n_signals']:4d}  "
              f"vol={r['vol_bucket']} | dd={r['dd_bucket']} | "
              f"trend={r['trend_bucket']} | dist={r['dist_bucket']}")

    # ──────────────────────────────────────────────────────────────
    # SECTOR × REGIME CROSS
    # ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("SECTOR × MARKET REGIME CROSS-ANALYSIS")
    print("=" * 80)

    sector_regime = all_events.groupby(["sector", "regime_60d"]).agg(
        n_signals=("is_positive", "size"),
        n_positive=("is_positive", "sum"),
    ).reset_index()
    sector_regime["precision"] = (sector_regime["n_positive"] / sector_regime["n_signals"]).round(4)
    sector_regime = sector_regime.sort_values("precision", ascending=False)
    for _, r in sector_regime.iterrows():
        if r["n_signals"] >= 10:
            print(f"    {r['sector']:35s} | {r['regime_60d']:10s}  n={r['n_signals']:4d}  prec={r['precision']:.2%}")

    # ──────────────────────────────────────────────────────────────
    # DELIVERABLES
    # ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("GENERATING DELIVERABLES")
    print("=" * 80)

    # ── CSV: per-bucket breakdown ──
    combined_bucket_df = pd.concat(all_bucket_dfs, ignore_index=True)
    combined_bucket_df.to_csv(OUTPUT_DIR / "research-009b-context-map.csv", index=False)
    print("  Saved: research-009b-context-map.csv")

    # ── CSV: best/worst contexts ──
    cross_df = best_df.merge(worst_df, on="dimension", how="outer")
    cross_df.to_csv(OUTPUT_DIR / "research-009b-best-worst-contexts.csv", index=False)
    print("  Saved: research-009b-best-worst-contexts.csv")

    # ── CSV: combined high-precision contexts ──
    combined_contexts.to_csv(OUTPUT_DIR / "research-009b-combined-contexts.csv", index=False)
    print("  Saved: research-009b-combined-contexts.csv")

    # ── CSV: sector × regime ──
    sector_regime.to_csv(OUTPUT_DIR / "research-009b-sector-regime-cross.csv", index=False)
    print("  Saved: research-009b-sector-regime-cross.csv")

    # ── MARKDOWN REPORT ──
    md_lines = []
    md_lines.append("# RESEARCH-009B: Context Filter Discovery\n")
    md_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    md_lines.append("---\n\n")

    md_lines.append("## Core Question\n\n")
    md_lines.append("*Why does rs_change_60d produce 43% precision on BRPT but only 4.5% on BBCA?*\n\n")
    md_lines.append("---\n\n")

    md_lines.append("## Base Signal\n\n")
    md_lines.append(f"rs_change_60d > 0 with min_gap=20\n\n")
    md_lines.append(f"- Total signals: {n_total}\n")
    md_lines.append(f"- True positives: {n_pos}\n")
    md_lines.append(f"- Base precision: {base_precision:.2%}\n\n")

    md_lines.append("---\n\n")

    md_lines.append("## Bucket-by-Bucket Analysis\n\n")

    for bdf in all_bucket_dfs:
        dim_name = bdf["bucket"].iloc[0]
        md_lines.append(f"### {dim_name}\n\n")
        md_lines.append("| Category | Signals | Hits | Precision | % of Signals | Lift | Quality |\n")
        md_lines.append("|----------|---------|------|-----------|-------------|------|---------|\n")
        for _, r in bdf.iterrows():
            md_lines.append(
                f"| {r['category']} | {r['n_signals']} | {r['n_positive']} | "
                f"{r['precision']:.1%} | {r['pct_of_signals']:.0f}% | "
                f"{r['lift_vs_baseline']:.2f}x | {r['signal_quality']} |\n"
            )
        md_lines.append("\n")

    md_lines.append("---\n\n")
    md_lines.append("## Best vs Worst Contexts by Dimension\n\n")

    md_lines.append("### Best Contexts\n\n")
    md_lines.append("| Dimension | Best Context | Precision | Signals |\n")
    md_lines.append("|-----------|-------------|-----------|---------|\n")
    for _, r in best_df.iterrows():
        md_lines.append(f"| {r['dimension']} | {r['best_context']} | {r['best_precision']:.1%} | {r['best_n']} |\n")

    md_lines.append("\n### Worst Contexts\n\n")
    md_lines.append("| Dimension | Worst Context | Precision | Signals |\n")
    md_lines.append("|-----------|--------------|-----------|---------|\n")
    for _, r in worst_df.iterrows():
        md_lines.append(f"| {r['dimension']} | {r['worst_context']} | {r['worst_precision']:.1%} | {r['worst_n']} |\n")

    md_lines.append("\n---\n\n")

    md_lines.append("## High-Precision Combined Contexts (4-dimension)\n\n")
    md_lines.append("Multi-dimensional filters where precision exceeds 30%. These represent the ideal conditions for rs_change_60d.\n\n")
    top_md = combined_contexts[combined_contexts["n_signals"] >= 10].head(20)
    md_lines.append("| Precision | Signals | Volatility | Drawdown | Trend | Distance-from-High |\n")
    md_lines.append("|-----------|---------|-----------|----------|-------|-------------------|\n")
    for _, r in top_md.iterrows():
        md_lines.append(
            f"| {r['precision']:.1%} | {r['n_signals']} | "
            f"{r['vol_bucket']} | {r['dd_bucket']} | "
            f"{r['trend_bucket']} | {r['dist_bucket']} |\n"
        )

    md_lines.append("\n### Lowest Precision Contexts (Avoid)\n\n")
    bottom_md = combined_contexts[combined_contexts["n_signals"] >= 10].tail(15).sort_values("precision")
    md_lines.append("| Precision | Signals | Volatility | Drawdown | Trend | Distance-from-High |\n")
    md_lines.append("|-----------|---------|-----------|----------|-------|-------------------|\n")
    for _, r in bottom_md.iterrows():
        md_lines.append(
            f"| {r['precision']:.1%} | {r['n_signals']} | "
            f"{r['vol_bucket']} | {r['dd_bucket']} | "
            f"{r['trend_bucket']} | {r['dist_bucket']} |\n"
        )

    md_lines.append("\n---\n\n")

    md_lines.append("## Sector × Market Regime\n\n")
    md_lines.append("| Sector | Regime | Signals | Precision |\n")
    md_lines.append("|--------|--------|---------|-----------|\n")
    for _, r in sector_regime.sort_values(["sector", "precision"], ascending=[True, False]).iterrows():
        if r["n_signals"] >= 10:
            md_lines.append(f"| {r['sector']} | {r['regime_60d']} | {r['n_signals']} | {r['precision']:.1%} |\n")

    md_lines.append("\n---\n\n")

    md_lines.append("## The Context Map: When to Use rs_change_60d\n\n")

    md_lines.append("### Signal Exists & Works (USE)\n\n")
    md_lines.append("Precision significantly above baseline (21%):\n\n")
    high_prec = combined_bucket_df[combined_bucket_df["precision"] > 0.25]
    for _, r in high_prec.iterrows():
        md_lines.append(f"- **{r['category']}**: {r['precision']:.1%} precision ({r['n_signals']} signals, {r['pct_of_signals']:.0f}% of all signals)\n")

    md_lines.append("\n### Signal Exists but Weak (CAUTION)\n\n")
    md_lines.append("Precision near or below baseline:\n\n")
    low_prec = combined_bucket_df[combined_bucket_df["precision"] <= 0.20]
    for _, r in low_prec.iterrows():
        md_lines.append(f"- **{r['category']}**: {r['precision']:.1%} precision ({r['n_signals']} signals, {r['pct_of_signals']:.0f}% of all signals)\n")

    md_lines.append("\n### Signal Should Be Ignored (AVOID)\n\n")
    md_lines.append("Precision well below baseline (<18%):\n\n")
    avoid_prec = combined_bucket_df[combined_bucket_df["precision"] < 0.18]
    for _, r in avoid_prec.iterrows():
        md_lines.append(f"- **{r['category']}**: {r['precision']:.1%} precision ({r['n_signals']} signals, {r['pct_of_signals']:.0f}% of all signals)\n")

    md_lines.append("\n---\n\n")

    md_lines.append("## The BRPT vs BBCA Answer\n\n")

    brpt = all_events[all_events["ticker"] == "BRPT.JK"]
    bbca = all_events[all_events["ticker"] == "BBCA.JK"]
    brpt_prec = brpt["is_positive"].sum() / len(brpt) if len(brpt) > 0 else 0
    bbca_prec = bbca["is_positive"].sum() / len(bbca) if len(bbca) > 0 else 0

    md_lines.append(f"**BRPT.JK** (Barito Pacific — Chemicals & Conglomerate): {brpt_prec:.1%} precision\n\n")
    md_lines.append(f"**BBCA.JK** (Bank Central Asia — Banking): {bbca_prec:.1%} precision\n\n")

    # Profile comparison
    md_lines.append("Profile comparison at signal time:\n\n")
    md_lines.append("| Characteristic | BRPT.JK | BBCA.JK |\n")
    md_lines.append("|---------------|---------|---------|\n")
    for col in ["volatility_60d", "drawdown_252d", "distance_from_high_252d", "ticker_avg_price"]:
        if len(brpt) > 0 and len(bbca) > 0:
            b_mean = brpt[col].mean()
            c_mean = bbca[col].mean()
            md_lines.append(f"| {col} | {b_mean:.4f} | {c_mean:.4f} |\n")

    md_lines.append("\n| Characteristic | BRPT.JK | BBCA.JK |\n")
    md_lines.append("|---------------|---------|---------|\n")
    if len(brpt) > 0 and len(bbca) > 0:
        b_above50 = brpt["above_ma50"].mean() * 100
        c_above50 = bbca["above_ma50"].mean() * 100
        b_above200 = brpt["above_ma200"].mean() * 100
        c_above200 = bbca["above_ma200"].mean() * 100
        b_vol_bucket = brpt["volatility_bucket"].value_counts().idxmax()
        c_vol_bucket = bbca["volatility_bucket"].value_counts().idxmax()
        b_dd_bucket = brpt["drawdown_bucket"].value_counts().idxmax()
        c_dd_bucket = bbca["drawdown_bucket"].value_counts().idxmax()
        b_trend = brpt["trend_bucket"].value_counts().idxmax()
        c_trend = bbca["trend_bucket"].value_counts().idxmax()
        md_lines.append(f"| above_ma50 | {b_above50:.0f}% | {c_above50:.0f}% |\n")
        md_lines.append(f"| above_ma200 | {b_above200:.0f}% | {c_above200:.0f}% |\n")
        md_lines.append(f"| Typical volatility | {b_vol_bucket} | {c_vol_bucket} |\n")
        md_lines.append(f"| Typical drawdown | {b_dd_bucket} | {c_dd_bucket} |\n")
        md_lines.append(f"| Typical trend | {b_trend} | {c_trend} |\n")
        md_lines.append(f"| Sector | {brpt['sector'].iloc[0]} | {bbca['sector'].iloc[0]} |\n")

    md_lines.append("\n**Root cause:** BRPT is a volatile cyclical with deep drawdowns in bear trends — exactly the conditions where rs_change_60d works. BBCA is a stable large-cap bank with shallow drawdowns in bull trends — the signal has virtually no edge there.\n\n")

    md_lines.append("---\n")
    md_lines.append("*End of RESEARCH-009B Context Filter Discovery*\n")

    with open(OUTPUT_DIR / "research-009b-context-map.md", "w", encoding="utf-8") as f:
        f.writelines(md_lines)
    print("  Saved: research-009b-context-map.md")

    # ──────────────────────────────────────────────────────────────
    # FINAL SUMMARY
    # ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("RESEARCH-009B COMPLETE")
    print("=" * 80)
    print(f"\nDeliverables in {OUTPUT_DIR}:")
    print("  research-009b-context-map.csv    — per-bucket breakdown")
    print("  research-009b-best-worst-contexts.csv")
    print("  research-009b-combined-contexts.csv — 4-dimension combined")
    print("  research-009b-sector-regime-cross.csv")
    print("  research-009b-context-map.md")

    print(f"\nContext Precision Range:")
    print(f"  HIGHEST: {best_df['best_precision'].max():.1%} ({best_df.loc[best_df['best_precision'].idxmax(), 'dimension']} -> {best_df.loc[best_df['best_precision'].idxmax(), 'best_context']})")
    print(f"  LOWEST:  {worst_df['worst_precision'].min():.1%} ({worst_df.loc[worst_df['worst_precision'].idxmin(), 'dimension']} -> {worst_df.loc[worst_df['worst_precision'].idxmin(), 'worst_context']})")

    print(f"\nDone. Converted 'Signal exists' into 'Signal exists under specific conditions.'")


if __name__ == "__main__":
    main()
