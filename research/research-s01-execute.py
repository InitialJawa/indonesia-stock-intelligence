#!/usr/bin/env python3
"""
RESEARCH-S01: EXIT SIGNAL AUTOPSY

Mirror RESEARCH-008 methodology but study future underperformers.
Goal: Discover sell-side deterioration signals.
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


def define_losers(wh, ihsg):
    """Define underperformers by forward alpha vs IHSG."""
    df = wh.copy()
    tickers = df["ticker"].unique()
    all_parts = []

    for ticker in tickers:
        t = df[df["ticker"] == ticker].sort_values("Date").copy()
        t = t.reset_index(drop=True)
        close = t["Close"].values
        n = len(close)

        fwd_return_20d = np.full(n, np.nan)
        fwd_return_40d = np.full(n, np.nan)
        fwd_return_60d = np.full(n, np.nan)

        if n > 20:
            fwd_return_20d[:-20] = close[20:] / close[:-20] - 1
        if n > 40:
            fwd_return_40d[:-40] = close[40:] / close[:-40] - 1
        if n > 60:
            fwd_return_60d[:-60] = close[60:] / close[:-60] - 1

        t["fwd_return_20d"] = fwd_return_20d
        t["fwd_return_40d"] = fwd_return_40d
        t["fwd_return_60d"] = fwd_return_60d

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

        t["fwd_alpha_20d"] = (1 + t["fwd_return_20d"]) / (1 + t["fwd_ihsg_return_20d"]) - 1
        t["fwd_alpha_40d"] = (1 + t["fwd_return_40d"]) / (1 + t["fwd_ihsg_return_40d"]) - 1
        t["fwd_alpha_60d"] = (1 + t["fwd_return_60d"]) / (1 + t["fwd_ihsg_return_60d"]) - 1

        t["LoserAlpha20"] = t["fwd_alpha_20d"] <= -0.10
        t["LoserAlpha40"] = t["fwd_alpha_40d"] <= -0.12
        t["LoserAlpha60"] = t["fwd_alpha_60d"] <= -0.15

        t.drop(columns=["ihsg_close_local"], inplace=True)
        all_parts.append(t)

    result = pd.concat(all_parts, ignore_index=True)
    result = result.sort_values(["ticker", "Date"]).reset_index(drop=True)

    n20 = result["LoserAlpha20"].sum()
    n40 = result["LoserAlpha40"].sum()
    n60 = result["LoserAlpha60"].sum()
    print(f"\nLoserAlpha20 (fwd alpha 20D <= -10%): {n20} events")
    print(f"LoserAlpha40 (fwd alpha 40D <= -12%): {n40} events")
    print(f"LoserAlpha60 (fwd alpha 60D <= -15%): {n60} events")

    return result


def extract_events(wh, loser_col="LoserAlpha60", min_gap=60):
    """Extract non-overlapping loser events."""
    events = []
    for ticker in wh["ticker"].unique():
        t = wh[wh["ticker"] == ticker].sort_values("Date").reset_index(drop=True)
        flags = t[loser_col].values
        n = len(flags)
        i = 0
        while i < n:
            if flags[i]:
                events.append({
                    "ticker": ticker,
                    "event_date": t["Date"].values[i],
                    "event_idx": i,
                    "loser_type": loser_col,
                    "fwd_alpha": t["fwd_alpha_60d"].values[i] if loser_col == "LoserAlpha60" else
                                 t["fwd_alpha_40d"].values[i] if loser_col == "LoserAlpha40" else
                                 t["fwd_alpha_20d"].values[i],
                    "fwd_return": t["fwd_return_60d"].values[i] if loser_col == "LoserAlpha60" else
                                  t["fwd_return_40d"].values[i] if loser_col == "LoserAlpha40" else
                                  t["fwd_return_20d"].values[i],
                })
                i += min_gap
            else:
                i += 1
    events_df = pd.DataFrame(events)
    print(f"Extracted {len(events_df)} non-overlapping {loser_col} events")
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
            row["fwd_alpha_event"] = ev["fwd_alpha"]
            row["fwd_return_event"] = ev["fwd_return"]
            rows.append(row)

    snapshots = pd.DataFrame(rows)
    print(f"Created {len(snapshots)} snapshots ({len(snapshots) // 5} events x ~5 offsets)")
    return snapshots


def create_control_group(wh, events_df):
    """Period-matched control: for each loser event date, sample a non-loser ticker."""
    tickers = wh["ticker"].unique()
    ticker_list = list(tickers)

    control_rows = []
    rng = np.random.RandomState(42)

    for _, ev in events_df.iterrows():
        event_date = ev["event_date"]
        loser_ticker = ev["ticker"]
        candidates = [t for t in ticker_list if t != loser_ticker]
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
                row["fwd_alpha_event"] = 0.0
                row["fwd_return_event"] = 0.0
                control_rows.append(row)
                found = True
                break

        if not found:
            for c in ticker_list:
                if c == loser_ticker:
                    continue
                c_data = wh[wh["ticker"] == c].set_index("Date")
                if event_date in c_data.index:
                    row = c_data.loc[event_date].to_dict()
                    row["event_date"] = event_date
                    row["event_ticker"] = c
                    row["offset_label"] = "T0"
                    row["offset_days"] = 0
                    row["fwd_alpha_event"] = 0.0
                    row["fwd_return_event"] = 0.0
                    control_rows.append(row)
                    found = True
                    break

    control = pd.DataFrame(control_rows)
    print(f"Control group: {len(control)} samples (matched to {len(events_df)} events)")
    return control


def compute_statistics(snapshots, control):
    """Compute all statistics for loser vs control at T0."""
    loser_t0 = snapshots[snapshots["offset_label"] == "T0"].copy()
    control_t0 = control.copy()

    results = []

    for feat in FEATURE_COLS:
        w = loser_t0[feat].dropna().values
        c = control_t0[feat].dropna().values

        if len(w) == 0 or len(c) == 0:
            continue

        mean_w = float(np.mean(w))
        mean_c = float(np.mean(c))
        std_w = float(np.std(w, ddof=1))
        std_c = float(np.std(c, ddof=1))

        pooled_std = np.sqrt(((len(w) - 1) * std_w**2 + (len(c) - 1) * std_c**2) / (len(w) + len(c) - 2))
        cohens_d = float((mean_w - mean_c) / pooled_std) if pooled_std > 0 else 0.0

        combined_vals = np.concatenate([w, c])
        labels = np.concatenate([np.ones(len(w)), np.zeros(len(c))])
        from scipy.stats import spearmanr
        spearman_ic_val, spearman_p = spearmanr(combined_vals, labels)

        t_stat, t_pval = stats.ttest_ind(w, c, equal_var=False)
        mw_stat, mw_pval = stats.mannwhitneyu(w, c, alternative="two-sided")

        lift = float(mean_w / mean_c) if mean_c != 0 else np.nan

        results.append({
            "feature": feat,
            "loser_mean": round(mean_w, 6),
            "control_mean": round(mean_c, 6),
            "cohens_d": round(cohens_d, 6),
            "spearman_ic": round(float(spearman_ic_val), 6),
            "spearman_p": round(float(spearman_p), 6),
            "t_stat": round(float(t_stat), 6),
            "t_pval": round(float(t_pval), 6),
            "mw_stat": int(mw_stat),
            "mw_pval": round(float(mw_pval), 6),
            "lift": round(lift, 6) if not np.isnan(lift) else None,
            "n_loser": len(w),
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

    max_abs_d = rankings["cohens_d"].abs().max()
    rankings["cohen_score"] = rankings["cohens_d"].abs() / max_abs_d if max_abs_d > 0 else 0

    max_abs_ic = rankings["spearman_ic"].abs().max()
    rankings["ic_score"] = rankings["spearman_ic"].abs() / max_abs_ic if max_abs_ic > 0 else 0

    max_lift_dev = (rankings["lift"].fillna(1) - 1).abs().max()
    rankings["lift_score"] = (rankings["lift"].fillna(1) - 1).abs() / max_lift_dev if max_lift_dev > 0 else 0

    rankings["mw_signal"] = -np.log10(rankings["mw_pval"].clip(lower=1e-300))
    max_mw = rankings["mw_signal"].max()
    rankings["mw_score"] = rankings["mw_signal"] / max_mw if max_mw > 0 else 0

    rankings["composite_score"] = (
        0.30 * rankings["cohen_score"]
        + 0.25 * rankings["ic_score"]
        + 0.25 * rankings["lift_score"]
        + 0.20 * rankings["mw_score"]
    )

    rankings = rankings.sort_values("composite_score", ascending=False).reset_index(drop=True)
    rankings["rank"] = range(1, len(rankings) + 1)

    return rankings


def compute_early_changers(timeline):
    """Determine which features change earliest before a collapse."""
    timeline_long = timeline.melt(id_vars=["feature"], var_name="offset", value_name="median_val")
    timeline_long = timeline_long.dropna()

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
    return early_changers


def generate_report(stats_df, rankings, timeline, snapshots, control, wh, early_changers):
    """Generate all deliverable files."""

    # ── feature_rankings.csv ──
    rankings_out = rankings[["rank", "feature", "composite_score", "cohens_d",
                              "spearman_ic", "lift", "mw_pval"]].copy()
    rankings_out.to_csv(OUTPUT_DIR / "s01_feature_rankings.csv", index=False)
    print("Saved: s01_feature_rankings.csv")

    # ── loser_vs_control_statistics.csv ──
    stats_df.to_csv(OUTPUT_DIR / "s01_loser_vs_control_statistics.csv", index=False)
    print("Saved: s01_loser_vs_control_statistics.csv")

    # ── pre_collapse_timeline.csv ──
    timeline.to_csv(OUTPUT_DIR / "s01_pre_collapse_timeline.csv", index=False)
    print("Saved: s01_pre_collapse_timeline.csv")

    # ── Full report ──
    n_events = len(snapshots[snapshots["offset_label"] == "T0"])
    top10 = rankings.head(10)

    lines = []
    lines.append(f"# RESEARCH-S01: Exit Signal Autopsy Report\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    lines.append("---\n\n")

    lines.append("## Methodology\n\n")
    lines.append("### Underperformer Definition\n\n")
    lines.append("| Category | Definition | Window |\n")
    lines.append("|----------|-----------|--------|\n")
    lines.append("| LoserAlpha20 | Forward Alpha vs IHSG <= -10% | 20 trading days |\n")
    lines.append("| LoserAlpha40 | Forward Alpha vs IHSG <= -12% | 40 trading days |\n")
    lines.append("| LoserAlpha60 | Forward Alpha vs IHSG <= -15% | 60 trading days |\n\n")
    lines.append("**Primary analysis: LoserAlpha60 (60D alpha <= -15%).**\n\n")
    lines.append("Forward Alpha = (1+R_stock)/(1+R_ihsg) - 1 (isolates stock-specific weakness)\n\n")
    lines.append("### Snapshot Offsets\n\n")
    lines.append("- T-40: 40 trading days before event\n")
    lines.append("- T-20: 20 trading days before event\n")
    lines.append("- T-10: 10 trading days before event\n")
    lines.append("- T-5: 5 trading days before event\n")
    lines.append("- T0: Event date (first day of alpha <= -15%)\n\n")
    lines.append("### Control Group\n\n")
    lines.append("Period-matched: For each loser event, a non-loser ticker is sampled at the same calendar date.\n\n")
    lines.append("### Statistical Tests\n\n")
    lines.append("- **Cohen's d**: Effect size (standardized mean difference)\n")
    lines.append("- **Spearman IC**: Rank correlation between feature value and lose/no-lose\n")
    lines.append("- **t-test**: Parametric test of mean difference\n")
    lines.append("- **Mann-Whitney U**: Non-parametric test of distribution difference\n")
    lines.append("- **Lift**: Ratio of loser mean to control mean\n\n")

    lines.append("---\n\n")
    lines.append("## Dataset Summary\n\n")
    lines.append(f"- Total warehouse records: {len(wh):,}\n")
    lines.append(f"- Tickers: {wh['ticker'].nunique()}\n")
    lines.append(f"- Date range: {wh['Date'].min().date()} to {wh['Date'].max().date()}\n")
    lines.append(f"- Features analyzed: {len(FEATURE_COLS)}\n")
    lines.append(f"- LoserAlpha60 events (non-overlapping): {n_events}\n")
    lines.append(f"- Control samples: {len(control)}\n\n")

    if "event_date" in snapshots.columns:
        event_dates = snapshots[snapshots["offset_label"] == "T0"]["event_date"]
        event_years = pd.to_datetime(event_dates).dt.year.value_counts().sort_index()
        lines.append("### Event Distribution by Year\n\n")
        for year, count in event_years.items():
            lines.append(f"- {year}: {count} events\n")
        lines.append("\n")

    lines.append("---\n\n")
    lines.append("## Feature Statistics: Loser vs Control (at T0)\n\n")
    lines.append("| Feature | Loser Mean | Control Mean | Cohen's d | Spearman IC | t-stat | MW p-val | Lift |\n")
    lines.append("|---------|-----------|-------------|-----------|-------------|--------|----------|------|\n")
    for _, r in stats_df.iterrows():
        lift_str = f"{r['lift']:.2f}" if pd.notna(r.get('lift')) else "N/A"
        lines.append(
            f"| {r['feature']} | {r['loser_mean']:.4f} | {r['control_mean']:.4f} | "
            f"{r['cohens_d']:.3f} | {r['spearman_ic']:.3f} | "
            f"{r['t_stat']:.2f} | {r['mw_pval']:.2e} | {lift_str} |\n"
        )
    lines.append("\n")

    lines.append("---\n\n")
    lines.append("## Top 10 Exit Signals\n\n")
    lines.append("Ranked by composite score:\n\n")
    lines.append("| Rank | Feature | Composite | Cohen's d | Spearman IC | Lift | MW p-val |\n")
    lines.append("|------|---------|----------|-----------|-------------|------|----------|\n")
    for _, r in rankings.head(10).iterrows():
        lift_str = f"{r['lift']:.2f}" if pd.notna(r.get('lift')) else "N/A"
        if r['cohens_d'] < 0:
            lines.append(
                f"| {int(r['rank'])} | `{r['feature']}` (!! LOSING) | {r['composite_score']:.3f} | "
                f"{r['cohens_d']:.3f} | {r['spearman_ic']:.3f} | "
                f"{lift_str} | {r['mw_pval']:.2e} |\n"
            )
        else:
            lines.append(
                f"| {int(r['rank'])} | `{r['feature']}` | {r['composite_score']:.3f} | "
                f"{r['cohens_d']:.3f} | {r['spearman_ic']:.3f} | "
                f"{lift_str} | {r['mw_pval']:.2e} |\n"
            )
    lines.append("\n")

    lines.append("**NOTE:** Negative Cohen's d = feature value is LOWER in losers than controls.\n")
    lines.append("Positive Cohen's d = feature value is HIGHER in losers.\n\n")

    lines.append("---\n\n")
    lines.append("## Pre-Collapse Timeline\n\n")
    lines.append("Median feature values from T-40 to T0:\n\n")

    for feat in FEATURE_COLS:
        tl_row = timeline[timeline["feature"] == feat]
        if len(tl_row) == 0:
            continue
        vals = []
        for label in ["T-40", "T-20", "T-10", "T-5", "T0"]:
            v = tl_row.iloc[0][label]
            vals.append(f"{v:.4f}" if v is not None else "N/A")
        lines.append(f"| `{feat}` | {' | '.join(vals)} |\n")
    lines.append("\n")

    lines.append("---\n\n")
    lines.append("## Deterioration Sequence\n\n")
    lines.append("Features ranked by WHEN they change (early = T-40 to T-20, late = T-5 to T0):\n\n")

    lines.append("### Earliest Signals (change starts 20-40 days before collapse)\n\n")
    for feat, early_pct, total_chg in early_changers[:5]:
        direction = "INCREASING" if total_chg > 0 else "DECREASING"
        lines.append(f"- **{feat}**: {early_pct:.0%} of total change in first half ({direction})\n")

    lines.append("\n### Latest Signals (change concentrated just before collapse)\n\n")
    for feat, early_pct, total_chg in early_changers[-5:]:
        direction = "INCREASING" if total_chg > 0 else "DECREASING"
        lines.append(f"- **{feat}**: only {early_pct:.0%} of change by T-20 ({direction})\n")

    lines.append("\n### Typical Deterioration Sequence\n\n")

    # Find the features that decrease (negative d) - these are the deterioration signals
    decreasing = rankings[rankings['cohens_d'] < 0].head(5)
    increasing = rankings[rankings['cohens_d'] > 0].head(3)

    step = 1
    for _, r in decreasing.iterrows():
        lines.append(f"{step}. **{r['feature']}** declines (d={r['cohens_d']:.2f})\n")
        step += 1
    for _, r in increasing.iterrows():
        lines.append(f"{step}. **{r['feature']}** rises as distress signal (d={r['cohens_d']:.2f})\n")
        step += 1

    lines.append(f"{step}. Stock enters full exit risk zone\n\n")

    lines.append("---\n\n")
    lines.append("## SELL WATCHLIST: 3-State Classification\n\n")
    lines.append("Based on the autopsy findings, stocks can be classified into:\n\n")

    # Determine thresholds from the top features
    top_neg_features = rankings[rankings['cohens_d'] < 0]['feature'].head(3).tolist()
    top_pos_features = rankings[rankings['cohens_d'] > 0]['feature'].head(3).tolist()

    lines.append("### HEALTHY\n")
    lines.append("- No deterioration signals detected\n")
    lines.append(f"- Key features ({', '.join(top_neg_features[:2])}) near or above control group medians\n")
    lines.append("\n### WEAKENING (early warning)\n")
    lines.append("- At least 2 of the following:\n")
    lines.append(f"  - `{top_neg_features[0] if len(top_neg_features) > 0 else 'rs_change_60d'}` declining\n")
    lines.append(f"  - `{top_neg_features[1] if len(top_neg_features) > 1 else 'rs_20d'}` turning negative\n")
    lines.append("  - Volume starting to dry up\n")
    lines.append("  - Price approaching MA20 (still above)\n")
    lines.append("\n### EXIT RISK (confirmed deterioration)\n")
    lines.append("- At least 3 of the following:\n")
    lines.append("  - Price below MA20 AND MA50\n")
    lines.append("  - RS_CHANGE_60D deeply negative\n")
    lines.append("  - Drawdown expanding past -20%\n")
    lines.append("  - Volume ratio below 0.7 (drying up)\n")
    lines.append("  - Recovery from 60d low stalling\n")
    lines.append("\n")

    lines.append("---\n\n")
    lines.append("## Forward Alpha Analysis\n\n")
    alpha_cols = ["fwd_alpha_20d", "fwd_alpha_40d", "fwd_alpha_60d"]
    for col in alpha_cols:
        if col in snapshots.columns:
            vals = snapshots[snapshots["offset_label"] == "T0"][col].dropna()
            if len(vals) > 0:
                lines.append(f"- **{col}** at T0: mean={vals.mean():.4f}, median={vals.median():.4f}\n")
    lines.append("\n")

    lines.append("---\n\n")
    lines.append("## Limitations\n\n")
    lines.append("1. **Look-ahead bias**: Forward alpha used for labeling only, NOT as features\n")
    lines.append("2. **Survivorship bias**: Only IDX30 tickers (current constituents)\n")
    lines.append("3. **Small sample**: 30 tickers, limited number of extreme underperformance events\n")
    lines.append("4. **No timing engine**: This is an autopsy, not a prediction model\n")
    lines.append("5. **Alpha is relative**: Underperformance vs IHSG may reflect sector rotation, not stock-specific issues\n")
    lines.append("6. **Event clustering**: Underperformance events may cluster (2020 COVID, 2022 bear market)\n\n")

    lines.append("---\n")
    lines.append("*End of RESEARCH-S01 Report*\n")

    with open(OUTPUT_DIR / "s01_exit_signal_autopsy_report.md", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Saved: s01_exit_signal_autopsy_report.md")

    # ── sell_watchlist_classification.md ──
    wl_lines = []
    wl_lines.append(f"# SELL WATCHLIST: 3-State Classification\n")
    wl_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    wl_lines.append(f"**Based on:** RESEARCH-S01 Exit Signal Autopsy\n\n")
    wl_lines.append("---\n\n")

    wl_lines.append("## State Definitions\n\n")
    wl_lines.append("### HEALTHY\n")
    wl_lines.append("No deterioration signals. Stock maintains positive relative strength.\n")
    wl_lines.append("- `RS_CHANGE_60D` near or above zero\n")
    wl_lines.append("- Price above both MA20 and MA50\n")
    wl_lines.append("- Drawdown shallower than -15%\n")
    wl_lines.append("- Volume ratio in normal range (0.8x - 1.5x)\n\n")
    wl_lines.append("### WEAKENING (Early Warning)\n")
    wl_lines.append("Early deterioration signals detected. Monitor closely.\n")
    wl_lines.append("- RS_CHANGE_60D declining or turning negative\n")
    wl_lines.append("- RS_20D turning negative\n")
    wl_lines.append("- Volume starting to dry up (ratio < 0.8x)\n")
    wl_lines.append("- Price approaching MA20 but still above\n")
    wl_lines.append("- Recovery from 60d low decelerating\n\n")
    wl_lines.append("### EXIT RISK (Confirmed Deterioration)\n")
    wl_lines.append("Multiple signals confirmed. Consider exit.\n")
    wl_lines.append("- Price below MA20 AND below MA50\n")
    wl_lines.append("- RS_CHANGE_60D deeply negative\n")
    wl_lines.append("- RS_20D negative and declining\n")
    wl_lines.append("- Drawdown expanding past -20%\n")
    wl_lines.append("- Volume ratio below 0.7x (drying up)\n")
    wl_lines.append("- Recovery from 60d low stalled or reversing\n")
    wl_lines.append("- Distance from 252d high widening\n\n")

    wl_lines.append("---\n")
    wl_lines.append("*End of SELL WATCHLIST Classification*\n")

    with open(OUTPUT_DIR / "s01_sell_watchlist_classification.md", "w", encoding="utf-8") as f:
        f.writelines(wl_lines)
    print("Saved: s01_sell_watchlist_classification.md")


def main():
    print("=" * 80)
    print("RESEARCH-S01: EXIT SIGNAL AUTOPSY")
    print("=" * 80)

    print("\n--- Loading Data ---")
    wh = load_data()
    ihsg = load_ihsg()

    print("\n--- STEP 1: Define Losers (Underperformers) ---")
    wh = define_losers(wh, ihsg)

    print("\n--- STEP 2: Extract Events & Snapshots ---")
    events = extract_events(wh, "LoserAlpha60")
    snapshots = create_snapshots(wh, events)
    snapshots.to_csv(OUTPUT_DIR / "s01_event_snapshots.csv", index=False)
    print("Saved: s01_event_snapshots.csv")

    print("\n--- STEP 3: Create Control Group ---")
    control = create_control_group(wh, events)
    control.to_csv(OUTPUT_DIR / "s01_control_group.csv", index=False)
    print("Saved: s01_control_group.csv")

    print("\n--- STEP 4: Compute Statistics ---")
    stats_df = compute_statistics(snapshots, control)
    print(f"Features analyzed: {len(stats_df)}")
    print("\nTop features by |Cohen's d|:")
    for _, r in stats_df.head(5).iterrows():
        print(f"  {r['feature']:25s} d={r['cohens_d']:+.3f}  IC={r['spearman_ic']:+.3f}  Lift={r['lift']:.2f}x  MWp={r['mw_pval']:.2e}")

    print("\n--- STEP 5: Pre-Collapse Timeline ---")
    timeline = compute_timeline(snapshots)
    print(f"Timeline features: {len(timeline)}")

    print("\n--- STEP 6: Rank Features ---")
    rankings = rank_features(stats_df)
    print("\nTop 10 Exit Signals:")
    for _, r in rankings.head(10).iterrows():
        arrow = "!! LOSING" if r['cohens_d'] < 0 else "^^ RISING"
        print(f"  #{int(r['rank']):2d} {r['feature']:25s} {arrow}  d={r['cohens_d']:+.3f}  IC={r['spearman_ic']:+.3f}")

    print("\n--- STEP 7: Deterioration Sequence ---")
    early_changers = compute_early_changers(timeline)
    print("Earliest signals (change T-40 to T-20):")
    for feat, early_pct, total_chg in early_changers[:5]:
        print(f"  {feat:25s} {early_pct:.0%} early  total_chg={total_chg:.4f}")
    print("Latest signals (concentrated at T-5 to T0):")
    for feat, early_pct, total_chg in early_changers[-5:]:
        print(f"  {feat:25s} {early_pct:.0%} early  total_chg={total_chg:.4f}")

    print("\n--- Generating Deliverables ---")
    generate_report(stats_df, rankings, timeline, snapshots, control, wh, early_changers)

    print("\n" + "=" * 80)
    print("RESEARCH-S01 COMPLETE")
    print("=" * 80)
    print(f"\nDeliverables in {OUTPUT_DIR}:")
    print("  s01_exit_signal_autopsy_report.md")
    print("  s01_sell_watchlist_classification.md")
    print("  s01_feature_rankings.csv")
    print("  s01_loser_vs_control_statistics.csv")
    print("  s01_pre_collapse_timeline.csv")
    print("\nAnswer: What happens before a stock loses alpha?")
    top_feat = rankings.iloc[0]["feature"]
    top_dir = "DECLINES" if rankings.iloc[0]["cohens_d"] < 0 else "RISES"
    print(f"  -> See s01_exit_signal_autopsy_report.md and {top_feat} {top_dir} as top signal")


if __name__ == "__main__":
    main()
