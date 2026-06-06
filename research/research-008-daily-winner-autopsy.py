
#!/usr/bin/env python3
"""
RESEARCH-008: Daily Winner Autopsy
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats  # For Mann-Whitney U

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_WH = PROJECT_ROOT / "database" / "historical" / "warehouse_daily_v4.parquet"
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BENCHMARK_FILE = PROJECT_ROOT / "benchmarks" / "ihsg.csv"


def load_benchmark_returns():
    """Load IHSG data and compute daily returns"""
    ihsg_df = pd.read_csv(BENCHMARK_FILE)
    date_col = next((c for c in ihsg_df.columns if c.lower() in ["date", "tanggal"]), ihsg_df.columns[0])
    price_col = next((c for c in ihsg_df.columns if c.lower() in ["close", "adj close", "price"]), ihsg_df.columns[1])
    ihsg_df[date_col] = pd.to_datetime(ihsg_df[date_col])
    ihsg_df = ihsg_df.set_index(date_col).sort_index()
    ihsg_df["ihsg_daily_return"] = ihsg_df[price_col].pct_change()
    return ihsg_df[["ihsg_daily_return"]].rename_axis("Date")


def load_daily_warehouse():
    df = pd.read_parquet(INPUT_WH)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["ticker", "Date"]).reset_index(drop=True)
    return df


def define_winners(df, ihsg_returns):
    """
    Define winner categories:
    Winner20: Fwd20D ≥ 20%
    Winner30: Fwd40D ≥ 30%
    Winner40: Fwd60D ≥40%
    Also calculate Forward Alpha vs IHSG
    """
    df = df.copy()

    # Calculate forward returns first
    for ticker in df["ticker"].unique():
        mask = df["ticker"] == ticker
        ticker_data = df.loc[mask].sort_values("Date").set_index("Date")

        # Forward returns
        for days, col in [(20, "fwd_return_20d"), (40, "fwd_return_40d"), (60, "fwd_return_60d")]:
            ticker_data[col] = ticker_data["Close"].pct_change(days).shift(-days)

        # Forward IHSG returns
        for days, col in [(20, "fwd_ihsg_return_20d"), (40, "fwd_ihsg_return_40d"), (60, "fwd_ihsg_return_60d")]:
            # Merge IHSG returns
            merged = ticker_data.join(ihsg_returns, how="left")
            ticker_data[col] = merged["ihsg_daily_return"].rolling(window=days, min_periods=days).apply(
                lambda x: (1 + x).prod() - 1, raw=True
            ).shift(-days)

        # Calculate forward alpha: (1+stock_return)/(1+ihsg_return) - 1
        for days in [20,40,60]:
            ticker_data[f"fwd_alpha_{days}d"] = (
                (1 + ticker_data[f"fwd_return_{days}d"]) /
                (1 + ticker_data[f"fwd_ihsg_return_{days}d"]) - 1
            )

        # Define winner flags
        ticker_data["Winner20"] = ticker_data["fwd_return_20d"] >= 0.20
        ticker_data["Winner30"] = ticker_data["fwd_return_40d"] >= 0.30
        ticker_data["Winner40"] = ticker_data["fwd_return_60d"] >= 0.40

        # Write back to df
        df.loc[mask, ["fwd_return_20d", "fwd_return_40d", "fwd_return_60d",
                      "fwd_ihsg_return_20d", "fwd_ihsg_return_40d", "fwd_ihsg_return_60d",
                      "fwd_alpha_20d", "fwd_alpha_40d", "fwd_alpha_60d",
                      "Winner20", "Winner30", "Winner40"]] = ticker_data.reset_index(drop=False)[
            ["fwd_return_20d", "fwd_return_40d", "fwd_return_60d",
             "fwd_ihsg_return_20d", "fwd_ihsg_return_40d", "fwd_ihsg_return_60d",
             "fwd_alpha_20d", "fwd_alpha_40d", "fwd_alpha_60d",
             "Winner20", "Winner30", "Winner40"]
        ].values

    return df


def create_event_snapshots(df):
    """
    For each Winner40 event (main focus), get snapshots at:
    T-40, T-20, T-10, T-5, T0
    """
    events = df[(df["Winner40"] == True)].copy()
    print(f"Found {len(events)} Winner40 events (T0 date)")

    snapshots = []
    for idx, event in events.iterrows():
        event_date = event["Date"]
        ticker = event["ticker"]
        ticker_data = df[df["ticker"] == ticker].set_index("Date").sort_index()

        for offset, label in [(-40, "T-40"), (-20, "T-20"), (-10, "T-10"), (-5, "T-5"), (0, "T0")]:
            try:
                # Find nearest date (not necessarily exactly offset days)
                target_date = event_date + pd.Timedelta(days=offset)
                nearest_idx = ticker_data.index.get_indexer([target_date], method="pad")[0]
                if nearest_idx >=0:
                    nearest_date = ticker_data.index[nearest_idx]
                    snapshot = ticker_data.loc[nearest_date].copy()
                    snapshot["event_date"] = event_date
                    snapshot["offset_label"] = label
                    snapshot["offset_days"] = offset
                    snapshots.append(snapshot)
            except Exception as e:
                continue

    snapshot_df = pd.DataFrame(snapshots)
    print(f"Created {len(snapshot_df)} total snapshots")
    return snapshot_df


def create_control_group(df, num_winners):
    """Create random control group of non-winner events"""
    non_winners = df[
        (~df["Winner20"]) &
        (~df["Winner30"]) &
        (~df["Winner40"])
    ].copy()

    # Random sample (1:1 ratio with winners)
    np.random.seed(42)
    control = non_winners.sample(n=min(len(non_winners), num_winners), replace=False)
    return control


def main():
    print("="*80)
    print("RESEARCH-008: DAILY WINNER AUTOPSY")
    print("="*80)

    print("\nStep 1: Load data & define winners")
    ihsg_rets = load_benchmark_returns()
    daily_df = load_daily_warehouse()
    daily_df = define_winners(daily_df, ihsg_rets)
    # Save intermediate winners data
    daily_df.to_parquet(OUTPUT_DIR / "research-008-winners-marked.parquet", index=False)

    print("\nStep 2: Create event snapshots")
    snapshot_df = create_event_snapshots(daily_df)
    snapshot_df.to_csv(OUTPUT_DIR / "research-008-event-snapshots.csv", index=False)

    print("\nStep 3: Create control group")
    num_winner_events = len(daily_df[daily_df["Winner40"] == True])
    control_df = create_control_group(daily_df, num_winner_events)
    control_df.to_csv(OUTPUT_DIR / "research-008-control-group.csv", index=False)

    # Step4: Basic stats (prepare data for analysis)
    feature_cols = [
        "rs_20d", "rs_60d", "rs_120d", "rs_252d",
        "rs_change_20d", "rs_change_60d",
        "drawdown_252d", "distance_from_high_252d",
        "recovery_from_60d_low",
        "volatility_20d", "volatility_60d",
        "volume_ratio", "momentum_slope",
        "above_ma20", "above_ma50", "above_ma100", "above_ma200",
        "golden_cross", "death_cross"
    ]

    # Keep only T0 snapshots for winner/control comparison at trigger date
    winner_t0 = snapshot_df[snapshot_df["offset_label"] == "T0"][feature_cols].dropna()
    control_t0 = control_df[feature_cols].dropna()

    print(f"\nWinner T0 samples: {len(winner_t0)}")
    print(f"Control T0 samples: {len(control_t0)}")

    # Step4: Compute feature statistics
    stats_list = []
    for feat in feature_cols:
        winner_vals = winner_t0[feat]
        control_vals = control_t0[feat]

        # Compute means, medians
        mean_win = winner_vals.mean()
        mean_ctrl = control_vals.mean()
        median_win = winner_vals.median()
        median_ctrl = control_vals.median()

        # Effect size (Cohen's d approximation)
        cohens_d = (mean_win - mean_ctrl) / np.sqrt((winner_vals.std()**2 + control_vals.std()**2)/2)

        # Information coefficient (Spearman)
        combined = pd.concat([pd.Series(winner_vals, index=range(len(winner_vals))),
                               pd.Series(control_vals, index=range(len(winner_vals), len(winner_vals)+len(control_vals)))])
        combined_label = pd.Series([1]*len(winner_vals) + [0]*len(control_vals))
        spearman_ic = combined.corr(combined_label, method="spearman")

        # t-test
        t_stat, t_pval = stats.ttest_ind(winner_vals, control_vals, nan_policy="omit")

        # Mann-Whitney U test
        mw_stat, mw_pval = stats.mannwhitneyu(winner_vals, control_vals, alternative="two-sided")

        # Lift
        # For continuous features, use (mean_win / mean_ctrl) if positive
        if mean_ctrl >0:
            lift = mean_win / mean_ctrl
        else:
            lift = np.nan

        stats_list.append({
            "feature": feat,
            "winner_mean": mean_win,
            "control_mean": mean_ctrl,
            "winner_median": median_win,
            "control_median": median_ctrl,
            "cohens_d": cohens_d,
            "spearman_ic": spearman_ic,
            "t_stat": t_stat,
            "t_pval": t_pval,
            "mw_stat": mw_stat,
            "mw_pval": mw_pval,
            "lift": lift
        })

    stats_df = pd.DataFrame(stats_list)
    # Rank by absolute cohen's d
    stats_df = stats_df.sort_values("cohens_d", key=abs, ascending=False).reset_index(drop=True)
    stats_df.to_csv(OUTPUT_DIR / "research-008-winner-vs-control-stats.csv", index=False)
    print("\nSaved winner vs control statistics")

    # Step5: Pre-rally timeline
    timeline_stats = []
    for feat in feature_cols:
        feat_timeline = {"feature": feat}
        for label in ["T-40", "T-20", "T-10", "T-5", "T0"]:
            label_slice = snapshot_df[snapshot_df["offset_label"] == label]
            feat_timeline[label] = label_slice[feat].median()
        timeline_stats.append(feat_timeline)
    timeline_df = pd.DataFrame(timeline_stats)
    timeline_df.to_csv(OUTPUT_DIR / "research-008-pre-rally-timeline.csv", index=False)
    print("Saved pre-rally timeline")

    # Save final deliverables to reports/
    print("\nStep 6: Done all steps! Deliverables saved to research/output/")


if __name__ == "__main__":
    main()
