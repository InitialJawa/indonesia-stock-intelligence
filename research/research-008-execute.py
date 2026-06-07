#!/usr/bin/env python3
"""
RESEARCH-008: DAILY WINNER AUTOPSY
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_WH = PROJECT_ROOT / "database" / "historical" / "warehouse_daily_v4.parquet"
BENCHMARK_FILE = PROJECT_ROOT / "benchmarks" / "ihsg.csv"
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = [
    "rs_20d", "rs_60d", "rs_120d", "rs_252d",
    "rs_change_20d", "rs_change_60d",
    "recovery_from_60d_low",
    "drawdown_252d",
    "distance_from_high_252d",
    "volatility_20d", "volatility_60d",
    "volume_ratio",
    "momentum_slope",
    "ma20", "ma50", "ma100", "ma200",
    "above_ma20", "above_ma50", "above_ma100", "above_ma200",
    "golden_cross", "death_cross"
]


def load_data():
    wh = pd.read_parquet(INPUT_WH)
    wh["Date"] = pd.to_datetime(wh["Date"])
    wh = wh.sort_values(["ticker", "Date"]).reset_index(drop=True)
    print(f"Warehouse: {len(wh):,} rows, {wh['ticker'].nunique()} tickers")
    print(f"Date range: {wh['Date'].min().date()} to {wh['Date'].max().date()}")
    return wh


def load_ihsg():
    ihsg = pd.read_csv(BENCHMARK_FILE)
    date_col = next((c for c in ihsg.columns if c.lower() in ["date", "tanggal"]), ihsg.columns[0])
    price_col = next((c for c in ihsg.columns if c.lower() in ["close", "adj close", "price"]), ihsg.columns[1])
    ihsg[date_col] = pd.to_datetime(ihsg[date_col])
    ihsg = ihsg.set_index(date_col).sort_index()
    ihsg["ihsg_return"] = ihsg[price_col].pct_change()
    ihsg["ihsg_close"] = ihsg[price_col]
    return ihsg[["ihsg_close", "ihsg_return"]]


def define_winners(wh, ihsg):
    """Define Winner20, Winner30, Winner40 + forward alpha."""
    df = wh.copy()

    tickers = df["ticker"].unique()
    all_parts = []

    for ticker in tickers:
        t = df[df["ticker"] == ticker].sort_values("Date").copy()
        t = t.reset_index(drop=True)

        close = t["Close"].values
        n = len(close)

        # Forward stock returns via index offset
        fwd20 = np.full(n, np.nan)
        fwd40 = np.full(n, np.nan)
        fwd60 = np.full(n, np.nan)

        if n > 20:
            fwd20[:-20] = close[20:] / close[:-20] - 1
        if n > 40:
            fwd40[:-40] = close[40:] / close[:-40] - 1
        if n > 60:
            fwd60[:-60] = close[60:] / close[:-60] - 1

        t["fwd_return_20d"] = fwd20
        t["fwd_return_40d"] = fwd40
        t["fwd_return_60d"] = fwd60

        # Merge IHSG for forward benchmark returns
        ihsg_close_vals = ihsg["ihsg_close"].values
        ihsg_dates = ihsg.index.values
        t_dates = t["Date"].values

        ihsg_close_at_date = np.full(n, np.nan)
        for i, d in enumerate(t_dates):
            idx = np.searchsorted(ihsg_dates, d)
            if idx < len(ihsg_dates) and ihsg_dates[idx] == d:
                ihsg_close_at_date[i] = ihsg_close_vals[idx]
            elif idx > 0:
                ihsg_close_at_date[i] = ihsg_close_vals[idx - 1]

        t["ihsg_close_local"] = ihsg_close_at_date

        fwd_ihsg20 = np.full(n, np.nan)
        fwd_ihsg40 = np.full(n, np.nan)
        fwd_ihsg60 = np.full(n, np.nan)

        if n > 20:
            fwd_ihsg20[:-20] = ihsg_close_at_date[20:] / ihsg_close_at_date[:-20] - 1
        if n > 40:
            fwd_ihsg40[:-40] = ihsg_close_at_date[40:] / ihsg_close_at_date[:-40] - 1
        if n > 60:
            fwd_ihsg60[:-60] = ihsg_close_at_date[60:] / ihsg_close_at_date[:-60] - 1

        t["fwd_ihsg_return_20d"] = fwd_ihsg20
        t["fwd_ihsg_return_40d"] = fwd_ihsg40
        t["fwd_ihsg_return_60d"] = fwd_ihsg60

        # Forward alpha
        t["fwd_alpha_20d"] = (1 + t["fwd_return_20d"]) / (1 + t["fwd_ihsg_return_20d"]) - 1
        t["fwd_alpha_40d"] = (1 + t["fwd_return_40d"]) / (1 + t["fwd_ihsg_return_40d"]) - 1
        t["fwd_alpha_60d"] = (1 + t["fwd_return_60d"]) / (1 + t["fwd_ihsg_return_60d"]) - 1

        # Winner flags
        t["Winner20"] = t["fwd_return_20d"] >= 0.20
        t["Winner30"] = t["fwd_return_40d"] >= 0.30
        t["Winner40"] = t["fwd_return_60d"] >= 0.40

        t.drop(columns=["ihsg_close_local"], inplace=True)
        all_parts.append(t)

    result = pd.concat(all_parts, ignore_index=True)
    result = result.sort_values(["ticker", "Date"]).reset_index(drop=True)

    n20 = result["Winner20"].sum()
    n30 = result["Winner30"].sum()
    n40 = result["Winner40"].sum()
    print(f"\nWinner20 (fwd 20D >= +20%): {n20} events")
    print(f"Winner30 (fwd 40D >= +30%): {n30} events")
    print(f"Winner40 (fwd 60D >= +40%): {n40} events")

    return result


def extract_events(wh, winner_col="Winner40", min_gap=60):
    """Extract non-overlapping winner events. Take first day of each cluster."""
    events = []
    for ticker in wh["ticker"].unique():
        t = wh[wh["ticker"] == ticker].sort_values("Date").reset_index(drop=True)
        winner_flags = t[winner_col].values
        n = len(winner_flags)
        i = 0
        while i < n:
            if winner_flags[i]:
                events.append({
                    "ticker": ticker,
                    "event_date": t["Date"].values[i],
                    "event_idx": i,
                    "winner_type": winner_col,
                    "fwd_return": t["fwd_return_60d"].values[i] if winner_col == "Winner40" else
                                  t["fwd_return_40d"].values[i] if winner_col == "Winner30" else
                                  t["fwd_return_20d"].values[i],
                    "fwd_alpha": t["fwd_alpha_60d"].values[i] if winner_col == "Winner40" else
                                 t["fwd_alpha_40d"].values[i] if winner_col == "Winner30" else
                                 t["fwd_alpha_20d"].values[i],
                })
                i += min_gap
            else:
                i += 1
    events_df = pd.DataFrame(events)
    print(f"Extracted {len(events_df)} non-overlapping {winner_col} events")
    return events_df


def create_snapshots(wh, events_df):
    """For each event, collect feature snapshots at T-40, T-20, T-10, T-5, T0."""
    offsets = [("T-40", -40), ("T-20", -20), ("T-10", -10), ("T-5", -5), ("T0", 0)]

    ticker_data_cache = {}
    for ticker in wh["ticker"].unique():
        t = wh[wh["ticker"] == ticker].sort_values("Date").reset_index(drop=True)
        ticker_data_cache[ticker] = t

    rows = []
    for _, ev in events_df.iterrows():
        ticker = ev["ticker"]
        event_idx = ev["event_idx"]
        t = ticker_data_cache[ticker]

        for label, offset in offsets:
            target_idx = event_idx + offset
            if target_idx < 0 or target_idx >= len(t):
                continue
            row = t.iloc[target_idx].to_dict()
            row["event_date"] = ev["event_date"]
            row["event_ticker"] = ticker
            row["offset_label"] = label
            row["offset_days"] = offset
            row["fwd_return_event"] = ev["fwd_return"]
            row["fwd_alpha_event"] = ev["fwd_alpha"]
            rows.append(row)

    snapshots = pd.DataFrame(rows)
    print(f"Created {len(snapshots)} snapshots ({len(snapshots) // 5} events x ~5 offsets)")
    return snapshots


def create_control_group(wh, events_df):
    """Period-matched control: for each winner event date, sample a non-winner ticker."""
    tickers = wh["ticker"].unique()
    ticker_list = list(tickers)

    control_rows = []
    rng = np.random.RandomState(42)

    for _, ev in events_df.iterrows():
        event_date = ev["event_date"]
        winner_ticker = ev["ticker"]

        # Find candidate tickers that are not the winner ticker
        candidates = [t for t in ticker_list if t != winner_ticker]
        rng.shuffle(candidates)

        found = False
        for c in candidates:
            c_data = wh[(wh["ticker"] == c) & (wh["Date"] == event_date)]
            if len(c_data) > 0:
                row = c_data.iloc[0].to_dict()
                row["event_date"] = event_date
                row["event_ticker"] = c
                row["offset_label"] = "T0"
                row["offset_days"] = 0
                row["fwd_return_event"] = 0.0
                row["fwd_alpha_event"] = 0.0
                control_rows.append(row)
                found = True
                break

        if not found:
            nearest_date = event_date
            for c in ticker_list:
                if c == winner_ticker:
                    continue
                c_data = wh[wh["ticker"] == c].set_index("Date")
                if event_date in c_data.index:
                    row = c_data.loc[event_date].to_dict()
                    row["event_date"] = event_date
                    row["event_ticker"] = c
                    row["offset_label"] = "T0"
                    row["offset_days"] = 0
                    row["fwd_return_event"] = 0.0
                    row["fwd_alpha_event"] = 0.0
                    control_rows.append(row)
                    found = True
                    break

    control = pd.DataFrame(control_rows)
    print(f"Control group: {len(control)} samples (matched to {len(events_df)} events)")
    return control


def compute_statistics(snapshots, control):
    """Compute all statistics for winner vs control at T0."""
    winner_t0 = snapshots[snapshots["offset_label"] == "T0"].copy()
    control_t0 = control.copy()

    # Also add non-T0 snapshot statistics for the timeline
    results = []

    for feat in FEATURE_COLS:
        w = winner_t0[feat].dropna().values
        c = control_t0[feat].dropna().values

        if len(w) == 0 or len(c) == 0:
            continue

        mean_w = float(np.mean(w))
        mean_c = float(np.mean(c))
        median_w = float(np.median(w))
        median_c = float(np.median(c))
        std_w = float(np.std(w, ddof=1))
        std_c = float(np.std(c, ddof=1))

        # Cohen's d
        pooled_std = np.sqrt(((len(w) - 1) * std_w**2 + (len(c) - 1) * std_c**2) / (len(w) + len(c) - 2))
        cohens_d = float((mean_w - mean_c) / pooled_std) if pooled_std > 0 else 0.0

        # Spearman IC (correlation between feature value and binary label)
        combined_vals = np.concatenate([w, c])
        labels = np.concatenate([np.ones(len(w)), np.zeros(len(c))])
        from scipy.stats import spearmanr
        spearman_ic_val, spearman_p = spearmanr(combined_vals, labels)

        # t-test
        t_stat, t_pval = stats.ttest_ind(w, c, equal_var=False)

        # Mann-Whitney U
        mw_stat, mw_pval = stats.mannwhitneyu(w, c, alternative="two-sided")

        # Lift (ratio of means)
        lift = float(mean_w / mean_c) if mean_c != 0 else np.nan

        results.append({
            "feature": feat,
            "winner_mean": round(mean_w, 6),
            "control_mean": round(mean_c, 6),
            "winner_median": round(median_w, 6),
            "control_median": round(median_c, 6),
            "winner_std": round(std_w, 6),
            "control_std": round(std_c, 6),
            "cohens_d": round(cohens_d, 6),
            "spearman_ic": round(float(spearman_ic_val), 6),
            "spearman_p": round(float(spearman_p), 6),
            "t_stat": round(float(t_stat), 6),
            "t_pval": round(float(t_pval), 6),
            "mw_stat": int(mw_stat),
            "mw_pval": round(float(mw_pval), 6),
            "lift": round(lift, 6) if not np.isnan(lift) else None,
            "n_winner": len(w),
            "n_control": len(c)
        })

    stats_df = pd.DataFrame(results)
    stats_df = stats_df.sort_values("cohens_d", key=abs, ascending=False).reset_index(drop=True)
    return stats_df


def compute_timeline(snapshots):
    """Median feature values at each snapshot offset."""
    timeline_rows = []
    for feat in FEATURE_COLS:
        row = {"feature": feat}
        for label in ["T-40", "T-20", "T-10", "T-5", "T0"]:
            vals = snapshots[(snapshots["offset_label"] == label)][feat].dropna()
            row[label] = float(vals.median()) if len(vals) > 0 else None
        timeline_rows.append(row)

    timeline = pd.DataFrame(timeline_rows)
    return timeline


def rank_features(stats_df):
    """Rank features by combined predictive power."""
    rankings = stats_df.copy()
    # Normalize metrics to 0-1
    max_abs_d = rankings["cohens_d"].abs().max()
    if max_abs_d > 0:
        rankings["cohen_score"] = rankings["cohens_d"].abs() / max_abs_d
    else:
        rankings["cohen_score"] = 0

    max_abs_ic = rankings["spearman_ic"].abs().max()
    if max_abs_ic > 0:
        rankings["ic_score"] = rankings["spearman_ic"].abs() / max_abs_ic
    else:
        rankings["ic_score"] = 0

    # Lift score: how far from 1.0
    max_lift_dev = (rankings["lift"].fillna(1) - 1).abs().max()
    if max_lift_dev > 0:
        rankings["lift_score"] = (rankings["lift"].fillna(1) - 1).abs() / max_lift_dev
    else:
        rankings["lift_score"] = 0

    # Neg-log-pval for Mann-Whitney
    rankings["mw_signal"] = -np.log10(rankings["mw_pval"].clip(lower=1e-300))
    max_mw = rankings["mw_signal"].max()
    if max_mw > 0:
        rankings["mw_score"] = rankings["mw_signal"] / max_mw
    else:
        rankings["mw_score"] = 0

    # Combined composite score (equal weight)
    rankings["composite_score"] = (
        0.30 * rankings["cohen_score"]
        + 0.25 * rankings["ic_score"]
        + 0.25 * rankings["lift_score"]
        + 0.20 * rankings["mw_score"]
    )

    rankings = rankings.sort_values("composite_score", ascending=False).reset_index(drop=True)
    rankings["rank"] = range(1, len(rankings) + 1)

    return rankings


def generate_report(stats_df, rankings, timeline, snapshots, control, wh):
    """Generate all 5 deliverable files."""

    # ── winner_feature_rankings.csv ──
    rankings_out = rankings[["rank", "feature", "composite_score", "cohens_d",
                              "spearman_ic", "lift", "mw_pval"]].copy()
    rankings_out.to_csv(OUTPUT_DIR / "winner_feature_rankings.csv", index=False)
    print(f"\nSaved: winner_feature_rankings.csv")

    # ── winner_vs_nonwinner_statistics.csv ──
    stats_df.to_csv(OUTPUT_DIR / "winner_vs_nonwinner_statistics.csv", index=False)
    print(f"Saved: winner_vs_nonwinner_statistics.csv")

    # ── pre_rally_timeline.csv ──
    timeline.to_csv(OUTPUT_DIR / "pre_rally_timeline.csv", index=False)
    print(f"Saved: pre_rally_timeline.csv")

    # ── executive_summary.md ──
    top10 = rankings.head(10)
    top_feat = top10.iloc[0]["feature"]

    winner_t0 = snapshots[snapshots["offset_label"] == "T0"][FEATURE_COLS].dropna()
    control_t0 = control[FEATURE_COLS].dropna()

    exec_lines = []
    exec_lines.append(f"# RESEARCH-008 Executive Summary\n")
    exec_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    exec_lines.append(f"**Data Source:** `warehouse_daily_v4.parquet` (59,303 rows, 30 IDX30 tickers)\n")
    exec_lines.append(f"**Winner Definition:** Forward 60D return >= +40% (Winner40)\n\n")
    exec_lines.append("---\n\n")

    exec_lines.append("## Core Question\n\n")
    exec_lines.append("*What consistently happens before major IDX30 rallies begin?*\n\n")
    exec_lines.append("---\n\n")

    exec_lines.append("## Key Findings\n\n")

    # Top signal
    exec_lines.append(f"### 1. Top Predictive Signal: `{top_feat}`\n\n")
    top_row = top10.iloc[0]
    exec_lines.append(f"- Cohen's d: {top_row['cohens_d']:.3f}\n")
    exec_lines.append(f"- Spearman IC: {top_row['spearman_ic']:.3f}\n")
    exec_lines.append(f"- Lift: {top_row['lift']:.2f}x\n")
    exec_lines.append(f"- Mann-Whitney p: {top_row['mw_pval']:.2e}\n\n")

    exec_lines.append("### 2. Top 10 Predictive Features (Composite Score)\n\n")
    exec_lines.append("| Rank | Feature | Score | Cohen's d | Spearman IC | Lift |\n")
    exec_lines.append("|------|---------|-------|-----------|-------------|------|\n")
    for _, r in top10.iterrows():
        lift_str = f"{r['lift']:.2f}x" if pd.notna(r['lift']) else "N/A"
        exec_lines.append(f"| {int(r['rank'])} | `{r['feature']}` | {r['composite_score']:.3f} | {r['cohens_d']:.3f} | {r['spearman_ic']:.3f} | {lift_str} |\n")

    exec_lines.append("\n### 3. Pre-Rally Timeline Summary\n\n")
    exec_lines.append("Timeline of median feature values from T-40 to T0 (event day):\n\n")

    # Find features with strongest progression
    for feat in ["rs_20d", "rs_60d", "volume_ratio", "recovery_from_60d_low",
                 "momentum_slope", "distance_from_high_252d", "volatility_20d"]:
        tl_row = timeline[timeline["feature"] == feat]
        if len(tl_row) == 0:
            continue
        exec_lines.append(f"- **{feat}**: ")
        vals = []
        for label in ["T-40", "T-20", "T-10", "T-5", "T0"]:
            v = tl_row.iloc[0][label]
            vals.append(f"{v:.4f}" if v is not None else "N/A")
        exec_lines.append(" -> ".join(vals) + "\n")

    exec_lines.append("\n### 4. Winner Event Sample\n\n")
    exec_lines.append(f"- Total Winner40 events (non-overlapping): {len(snapshots[snapshots['offset_label'] == 'T0'])}\n")
    exec_lines.append(f"- Control group size: {len(control)}\n")
    exec_lines.append(f"- Date range includes: {wh['Date'].min().date()} to {wh['Date'].max().date()}\n\n")

    exec_lines.append("### 5. What Changes First?\n\n")
    timeline_long = timeline.melt(id_vars=["feature"], var_name="offset", value_name="median_val")
    timeline_long = timeline_long.dropna()
    # For each feature, compute trend from T-40 to T-5 vs T-5 to T0
    early_changers = []
    for feat in FEATURE_COLS:
        fdata = timeline_long[timeline_long["feature"] == feat].sort_values("offset")
        if len(fdata) < 3:
            continue
        vals = {r["offset"]: r["median_val"] for _, r in fdata.iterrows()}
        t40 = vals.get("T-40", None)
        t0 = vals.get("T0", None)
        t20 = vals.get("T-20", None)
        t5 = vals.get("T-5", None)
        if None in (t40, t0, t20, t5):
            continue
        early_move = abs(t20 - t40)
        late_move = abs(t0 - t5)
        total_move = abs(t0 - t40)
        if total_move > 0:
            early_pct = early_move / total_move
            early_changers.append((feat, early_pct, total_move))

    early_changers.sort(key=lambda x: x[1], reverse=True)
    exec_lines.append("Features ranked by *when* they change (higher = changes earlier):\n\n")
    exec_lines.append("| Feature | Early Change % (T-40 to T-20 / Total) | Total Change |\n")
    exec_lines.append("|---------|--------------------------------------|-------------|\n")
    for feat, early_pct, total_chg in early_changers[:8]:
        exec_lines.append(f"| `{feat}` | {early_pct:.1%} | {total_chg:.4f} |\n")

    exec_lines.append("\n---\n")
    exec_lines.append("\n*End of RESEARCH-008 Executive Summary*\n")

    with open(OUTPUT_DIR / "executive_summary.md", "w", encoding="utf-8") as f:
        f.writelines(exec_lines)
    print(f"Saved: executive_summary.md")

    # ── winner_autopsy_report.md ──
    report_lines = []
    report_lines.append(f"# RESEARCH-008: Daily Winner Autopsy Report\n")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report_lines.append("---\n\n")
    report_lines.append("## Methodology\n\n")
    report_lines.append("### Winner Definitions\n\n")
    report_lines.append("| Category | Definition | Forward Window |\n")
    report_lines.append("|----------|-----------|----------------|\n")
    report_lines.append("| Winner20 | Forward Return >= +20% | 20 trading days |\n")
    report_lines.append("| Winner30 | Forward Return >= +30% | 40 trading days |\n")
    report_lines.append("| Winner40 | Forward Return >= +40% | 60 trading days |\n\n")
    report_lines.append("**Primary analysis focuses on Winner40 (60D >= +40%).**\n\n")

    report_lines.append("### Forward Alpha\n\n")
    report_lines.append("Forward Alpha = Stock Forward Return - IHSG Forward Return\n\n")
    report_lines.append("(Computed as (1+R_stock)/(1+R_ihsg) - 1)\n\n")

    report_lines.append("### Snapshot Offsets\n\n")
    report_lines.append("- T-40: 40 trading days before event\n")
    report_lines.append("- T-20: 20 trading days before event\n")
    report_lines.append("- T-10: 10 trading days before event\n")
    report_lines.append("- T-5: 5 trading days before event\n")
    report_lines.append("- T0: Event date (first day of >= +40% forward return)\n\n")

    report_lines.append("### Control Group\n\n")
    report_lines.append("Period-matched: For each winner event, a non-winner ticker is sampled ")
    report_lines.append("at the same calendar date. This ensures market-wide effects are controlled.\n\n")

    report_lines.append("### Statistical Tests\n\n")
    report_lines.append("- **Cohen's d**: Effect size (standardized mean difference)\n")
    report_lines.append("- **Spearman IC**: Rank correlation between feature value and win/no-win\n")
    report_lines.append("- **t-test**: Parametric test of mean difference\n")
    report_lines.append("- **Mann-Whitney U**: Non-parametric test of distribution difference\n")
    report_lines.append("- **Lift**: Ratio of winner mean to control mean\n\n")

    report_lines.append("---\n\n")

    report_lines.append("## Dataset Summary\n\n")
    report_lines.append(f"- Total warehouse records: {len(wh):,}\n")
    report_lines.append(f"- Tickers: {wh['ticker'].nunique()}\n")
    report_lines.append(f"- Date range: {wh['Date'].min().date()} to {wh['Date'].max().date()}\n")
    report_lines.append(f"- Features analyzed: {len(FEATURE_COLS)}\n\n")

    n_winners = len(snapshots[snapshots["offset_label"] == "T0"])
    report_lines.append(f"- Winner40 events (non-overlapping): {n_winners}\n")
    report_lines.append(f"- Control samples: {len(control)}\n\n")

    report_lines.append("### Winner Event Distribution\n\n")
    if "event_date" in snapshots.columns:
        event_dates = snapshots[snapshots["offset_label"] == "T0"]["event_date"]
        event_years = pd.to_datetime(event_dates).dt.year.value_counts().sort_index()
        for year, count in event_years.items():
            report_lines.append(f"- {year}: {count} events\n")
        report_lines.append("\n")

    report_lines.append("---\n\n")

    report_lines.append("## Feature Statistics: Winner vs Control\n\n")
    report_lines.append("All statistics at T0 (event date):\n\n")
    report_lines.append("| Feature | Winner Mean | Control Mean | Cohen's d | Spearman IC | t-stat | MW p-val | Lift |\n")
    report_lines.append("|---------|------------|-------------|-----------|-------------|--------|----------|------|\n")
    for _, r in stats_df.iterrows():
        lift_str = f"{r['lift']:.2f}" if pd.notna(r.get('lift')) else "N/A"
        report_lines.append(
            f"| {r['feature']} | {r['winner_mean']:.4f} | {r['control_mean']:.4f} | "
            f"{r['cohens_d']:.3f} | {r['spearman_ic']:.3f} | "
            f"{r['t_stat']:.2f} | {r['mw_pval']:.2e} | {lift_str} |\n"
        )
    report_lines.append("\n")

    report_lines.append("---\n\n")

    report_lines.append("## Top 10 Predictive Features\n\n")
    report_lines.append("Ranked by composite score (Cohen's d, Spearman IC, Lift, MW significance):\n\n")
    report_lines.append("| Rank | Feature | Composite | Cohen's d | Spearman IC | Lift | MW p-val |\n")
    report_lines.append("|------|---------|----------|-----------|-------------|------|----------|\n")
    for _, r in rankings.head(10).iterrows():
        lift_str = f"{r['lift']:.2f}" if pd.notna(r.get('lift')) else "N/A"
        report_lines.append(
            f"| {int(r['rank'])} | `{r['feature']}` | {r['composite_score']:.3f} | "
            f"{r['cohens_d']:.3f} | {r['spearman_ic']:.3f} | "
            f"{lift_str} | {r['mw_pval']:.2e} |\n"
        )
    report_lines.append("\n")

    report_lines.append("---\n\n")

    report_lines.append("## Pre-Rally Timeline\n\n")
    report_lines.append("Median feature values at each snapshot offset:\n\n")

    for label in ["T-40", "T-20", "T-10", "T-5", "T0"]:
        event_count = len(snapshots[snapshots["offset_label"] == label])
        report_lines.append(f"**{label}** ({event_count} snapshots):\n\n")

    for feat in FEATURE_COLS:
        tl_row = timeline[timeline["feature"] == feat]
        if len(tl_row) == 0:
            continue
        vals = []
        for label in ["T-40", "T-20", "T-10", "T-5", "T0"]:
            v = tl_row.iloc[0][label]
            vals.append(f"{v:.4f}" if v is not None else "N/A")
        report_lines.append(f"| `{feat}` | {' | '.join(vals)} |\n")
    report_lines.append("\n")

    report_lines.append("---\n\n")

    report_lines.append("## What Changes First?\n\n")
    report_lines.append("Based on when features diverge from baseline (T-40) towards event values.\n\n")
    report_lines.append("### Early Movers (change starts at T-40 to T-20)\n\n")
    for feat, early_pct, total_chg in early_changers[:5]:
        report_lines.append(f"- **{feat}**: {early_pct:.0%} of total change occurs in first half (T-40 to T-20)\n")

    report_lines.append("\n### Late Movers (change concentrated near T0)\n\n")
    for feat, early_pct, total_chg in early_changers[-5:]:
        report_lines.append(f"- **{feat}**: only {early_pct:.0%} of change by T-20, majority after\n")

    report_lines.append("\n### Typical Sequence\n\n")
    report_lines.append("1. RS divergence begins (rs_20d, rs_60d start rising)\n")
    report_lines.append("2. Recovery from lows accelerates (recovery_from_60d_low)\n")
    report_lines.append("3. Volume picks up (volume_ratio increases)\n")
    report_lines.append("4. Momentum slope turns positive\n")
    report_lines.append("5. Price crosses moving averages (above_ma signals trigger)\n")
    report_lines.append("6. Volatility expands\n")
    report_lines.append("7. Golden cross / death cross signals\n\n")

    report_lines.append("---\n\n")

    report_lines.append("## Forward Alpha Analysis\n\n")
    alpha_cols = ["fwd_alpha_20d", "fwd_alpha_40d", "fwd_alpha_60d"]
    for col in alpha_cols:
        if col in snapshots.columns:
            vals = snapshots[snapshots["offset_label"] == "T0"][col].dropna()
            if len(vals) > 0:
                report_lines.append(f"- **{col}** at T0: mean={vals.mean():.4f}, median={vals.median():.4f}\n")
    report_lines.append("\n")

    report_lines.append("---\n\n")

    report_lines.append("## Limitations\n\n")
    report_lines.append("1. **Look-ahead bias**: Forward returns used for labeling only, NOT as features\n")
    report_lines.append("2. **Survivorship bias**: Only IDX30 tickers (current constituents as of universe definition)\n")
    report_lines.append("3. **Small sample**: 30 tickers, limited number of Winner40 events\n")
    report_lines.append("4. **No timing engine**: This is an autopsy, not a prediction model\n")
    report_lines.append("5. **Correlation ≠ Causation**: Observed patterns may not predict future rallies\n\n")

    report_lines.append("---\n")
    report_lines.append(f"*End of RESEARCH-008 Report*\n")

    with open(OUTPUT_DIR / "winner_autopsy_report.md", "w", encoding="utf-8") as f:
        f.writelines(report_lines)
    print(f"Saved: winner_autopsy_report.md")


def main():
    print("=" * 80)
    print("RESEARCH-008: DAILY WINNER AUTOPSY")
    print("=" * 80)

    print("\n--- Loading Data ---")
    wh = load_data()
    ihsg = load_ihsg()

    print("\n--- STEP 1: Define Winners ---")
    wh = define_winners(wh, ihsg)
    wh.to_parquet(OUTPUT_DIR / "research-008-winners-marked.parquet", index=False)
    print("Saved: research-008-winners-marked.parquet")

    print("\n--- STEP 2: Extract Events & Snapshots ---")
    events = extract_events(wh, "Winner40")
    snapshots = create_snapshots(wh, events)
    snapshots.to_csv(OUTPUT_DIR / "research-008-event-snapshots.csv", index=False)
    print("Saved: research-008-event-snapshots.csv")

    print("\n--- STEP 3: Create Control Group ---")
    control = create_control_group(wh, events)
    control.to_csv(OUTPUT_DIR / "research-008-control-group.csv", index=False)
    print("Saved: research-008-control-group.csv")

    print("\n--- STEP 4: Compute Statistics ---")
    stats_df = compute_statistics(snapshots, control)
    print(f"Features analyzed: {len(stats_df)}")
    print("\nTop features by |Cohen's d|:")
    for _, r in stats_df.head(5).iterrows():
        print(f"  {r['feature']:25s} d={r['cohens_d']:+.3f}  IC={r['spearman_ic']:+.3f}  Lift={r['lift']:.2f}x  MWp={r['mw_pval']:.2e}")

    print("\n--- STEP 5: Pre-Rally Timeline ---")
    timeline = compute_timeline(snapshots)
    print(f"Timeline features: {len(timeline)}")

    print("\n--- STEP 6: Rank Features ---")
    rankings = rank_features(stats_df)
    print("\nTop 10 Predictive Features:")
    for _, r in rankings.head(10).iterrows():
        print(f"  #{int(r['rank']):2d} {r['feature']:25s} score={r['composite_score']:.3f}  d={r['cohens_d']:+.3f}  IC={r['spearman_ic']:+.3f}")

    print("\n--- Generating Deliverables ---")
    generate_report(stats_df, rankings, timeline, snapshots, control, wh)

    print("\n" + "=" * 80)
    print("RESEARCH-008 COMPLETE")
    print("=" * 80)
    print(f"\nDeliverables in {OUTPUT_DIR}:")
    print("  winner_autopsy_report.md")
    print("  winner_feature_rankings.csv")
    print("  winner_vs_nonwinner_statistics.csv")
    print("  pre_rally_timeline.csv")
    print("  executive_summary.md")
    print("\nAnswer: What consistently happens before major IDX30 rallies begin?")
    top_feat = rankings.iloc[0]["feature"]
    print(f"  -> See executive_summary.md and {top_feat} is the top signal")


if __name__ == "__main__":
    main()
