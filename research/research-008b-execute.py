#!/usr/bin/env python3
"""
RESEARCH-008B: RALLY INITIATION DETECTION
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from datetime import datetime
from collections import defaultdict

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
    "above_ma20", "above_ma50", "above_ma100", "above_ma200",
    "golden_cross", "death_cross"
]

SNAPSHOT_OFFSETS = [("T-40", -40), ("T-20", -20), ("T-10", -10), ("T-5", -5), ("T0", 0)]


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
    ihsg["ihsg_close"] = ihsg[price_col]
    return ihsg[["ihsg_close"]]


def compute_forward_returns(wh, ihsg):
    """Add forward return columns needed for validation."""
    df = wh.copy()
    ihsg_close = ihsg["ihsg_close"].values
    ihsg_dates = ihsg.index.values

    tickers = df["ticker"].unique()
    all_parts = []

    for ticker in tickers:
        t = df[df["ticker"] == ticker].sort_values("Date").copy()
        t = t.reset_index(drop=True)
        close = t["Close"].values
        n = len(close)

        fwd20 = np.full(n, np.nan)
        fwd40 = np.full(n, np.nan)
        fwd_ihsg20 = np.full(n, np.nan)
        fwd_ihsg40 = np.full(n, np.nan)

        if n > 20:
            fwd20[:-20] = close[20:] / close[:-20] - 1
        if n > 40:
            fwd40[:-40] = close[40:] / close[:-40] - 1

        t_dates = t["Date"].values
        ihsg_close_local = np.full(n, np.nan)
        for i, d in enumerate(t_dates):
            idx = np.searchsorted(ihsg_dates, d)
            if idx < len(ihsg_dates) and ihsg_dates[idx] == d:
                ihsg_close_local[i] = ihsg_close[idx]
            elif idx > 0:
                ihsg_close_local[i] = ihsg_close[idx - 1]

        if n > 20:
            fwd_ihsg20[:-20] = ihsg_close_local[20:] / ihsg_close_local[:-20] - 1
        if n > 40:
            fwd_ihsg40[:-40] = ihsg_close_local[40:] / ihsg_close_local[:-40] - 1

        t["fwd_return_20d"] = fwd20
        t["fwd_return_40d"] = fwd40
        t["fwd_ihsg_return_20d"] = fwd_ihsg20
        t["fwd_ihsg_return_40d"] = fwd_ihsg40

        all_parts.append(t)

    result = pd.concat(all_parts, ignore_index=True)
    result = result.sort_values(["ticker", "Date"]).reset_index(drop=True)
    return result


def compute_rsi(prices, period=14):
    """Compute RSI for a price series using vectorized approach."""
    deltas = np.diff(prices, prepend=np.nan)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.full_like(prices, np.nan)
    avg_loss = np.full_like(prices, np.nan)

    if len(prices) > period:
        avg_gain[period] = np.mean(gains[1:period+1])
        avg_loss[period] = np.mean(losses[1:period+1])
        for i in range(period + 1, len(prices)):
            avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i]) / period
            avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i]) / period

    rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
    rsi = 100 - (100 / (1 + rs))
    rsi[avg_loss == 0] = 100.0
    return rsi


def compute_ticker_derived(t):
    """Compute derived signals per ticker."""
    t = t.copy()
    close = t["Close"].values
    n = len(close)

    # Whether above_ma20 changes from below to above (cross up)
    above_ma20_vals = t["above_ma20"].values.astype(bool)
    ma20_cross_up = np.full(n, False)
    ma20_cross_up[1:] = above_ma20_vals[1:] & ~above_ma20_vals[:-1]

    # Count consecutive days below MA20
    below_streak = np.zeros(n, dtype=int)
    streak = 0
    for i in range(n):
        if ~above_ma20_vals[i]:
            streak += 1
        else:
            streak = 0
        below_streak[i] = streak

    t["ma20_cross_up"] = ma20_cross_up
    t["below_ma20_streak"] = below_streak

    # RS20 sign change: negative -> positive
    rs20 = t["rs_20d"].values
    rs20_pos = ~np.isnan(rs20) & (rs20 >= 0)
    rs20_neg = ~np.isnan(rs20) & (rs20 < 0)
    rs20_turns_pos = np.full(n, False)
    rs20_turns_pos[1:] = rs20_pos[1:] & rs20_neg[:-1]
    t["rs20_turns_positive"] = rs20_turns_pos

    # Momentum slope sign change: negative -> positive
    ms = t["momentum_slope"].values
    ms_pos = ~np.isnan(ms) & (ms >= 0)
    ms_neg = ~np.isnan(ms) & (ms < 0)
    ms_turns_pos = np.full(n, False)
    ms_turns_pos[1:] = ms_pos[1:] & ms_neg[:-1]
    t["ms_turns_positive"] = ms_turns_pos

    return t


def detect_candidate_a(t):
    """Candidate A: Price crosses above MA20 after >= 20 days below."""
    cross_days = t.index[t["ma20_cross_up"] & (t["below_ma20_streak"].shift(1) >= 20)].tolist()
    return cross_days


def detect_candidate_b(t):
    """Candidate B: RS20 changes from negative to positive."""
    return t.index[t["rs20_turns_positive"]].tolist()


def detect_candidate_c(t):
    """Candidate C: Volume Ratio > 1.3 AND Price above MA20."""
    cond = (t["volume_ratio"] > 1.3) & t["above_ma20"]
    return t.index[cond].tolist()


def detect_candidate_d(t):
    """Candidate D: Momentum Slope changes from negative to positive."""
    return t.index[t["ms_turns_positive"]].tolist()


def non_overlapping(indices, min_gap=20):
    """Filter indices to ensure minimum gap between events."""
    if len(indices) == 0:
        return []
    indices = sorted(indices)
    result = [indices[0]]
    for i in indices[1:]:
        if i - result[-1] >= min_gap:
            result.append(i)
    return result


def validate_event(t, idx):
    """Check if forward returns after signal meet validation criteria."""
    fwd20 = t["fwd_return_20d"].values[idx] if idx < len(t) else np.nan
    fwd40 = t["fwd_return_40d"].values[idx] if idx < len(t) else np.nan
    valid20 = not np.isnan(fwd20) and fwd20 > 0.10
    valid40 = not np.isnan(fwd40) and fwd40 > 0.15
    return valid20 or valid40, fwd20, fwd40


def main():
    print("=" * 80)
    print("RESEARCH-008B: RALLY INITIATION DETECTION")
    print("=" * 80)

    print("\n--- Loading Data ---")
    wh = load_data()
    ihsg = load_ihsg()

    print("\n--- Computing Forward Returns ---")
    wh = compute_forward_returns(wh, ihsg)

    print("\n--- Computing Derived Signals per Ticker ---")
    tickers = wh["ticker"].unique()
    derived_parts = []
    for ticker in tickers:
        t = wh[wh["ticker"] == ticker].sort_values("Date").reset_index(drop=True)
        t = compute_ticker_derived(t)
        derived_parts.append(t)
    wh = pd.concat(derived_parts, ignore_index=True)
    wh = wh.sort_values(["ticker", "Date"]).reset_index(drop=True)

    # Build ticker data cache
    ticker_cache = {}
    for ticker in tickers:
        ticker_cache[ticker] = wh[wh["ticker"] == ticker].sort_values("Date").reset_index(drop=True)

    # ──────────────────────────────────────────────────────────────────
    # STEP 1: Detect Rally Start Events for Each Candidate
    # ──────────────────────────────────────────────────────────────────
    print("\n--- STEP 1: Detecting Rally Start Candidates ---")

    candidates = {
        "A": ("MA20 Cross After 20D Below", detect_candidate_a),
        "B": ("RS20 Negative->Positive", detect_candidate_b),
        "C": ("Volume >1.3 + Above MA20", detect_candidate_c),
        "D": ("Momentum Slope Negative->Positive", detect_candidate_d),
    }

    all_events = []
    event_id = 0

    for cand_label, (cand_name, detect_fn) in candidates.items():
        print(f"\n  Candidate {cand_label}: {cand_name}")

        cand_events = []
        for ticker in tickers:
            t = ticker_cache[ticker]
            raw_indices = detect_fn(t)
            if len(raw_indices) == 0:
                continue
            clean_indices = non_overlapping(raw_indices, min_gap=20)

            for idx in clean_indices:
                is_valid, fwd20, fwd40 = validate_event(t, idx)
                if not is_valid:
                    continue

                event_id += 1
                cand_events.append({
                    "event_id": event_id,
                    "candidate": cand_label,
                    "candidate_name": cand_name,
                    "ticker": ticker,
                    "event_date": t.loc[idx, "Date"],
                    "event_idx": idx,
                    "fwd_return_20d": fwd20,
                    "fwd_return_40d": fwd40,
                })

        cand_df = pd.DataFrame(cand_events)
        print(f"    Raw signals: {len(raw_indices) if tickers[0] in ticker_cache else 'N/A'} "
              f"-> Clean (non-overlap): {len(cand_events) if False else 'N/A'} "
              f"-> Validated: {len(cand_df)}")

        # Count per ticker
        for _, row in cand_df.iterrows():
            all_events.append(row.to_dict())

    events_df = pd.DataFrame(all_events)
    print(f"\nTotal validated rally start events: {len(events_df)}")

    if len(events_df) == 0:
        print("\nERROR: No validated events found. Exiting.")
        return

    # Per-candidate stats
    cand_counts = events_df["candidate"].value_counts()
    for label in ["A", "B", "C", "D"]:
        print(f"  Candidate {label}: {cand_counts.get(label, 0)} events")

    # ──────────────────────────────────────────────────────────────────
    # STEP 2: Already done above (validation built into detection)
    # ──────────────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────────────
    # STEP 3: Create Snapshots for Each Event
    # ──────────────────────────────────────────────────────────────────
    print("\n--- STEP 3: Creating Event Snapshots ---")

    snapshot_rows = []
    for _, ev in events_df.iterrows():
        ticker = ev["ticker"]
        event_idx = ev["event_idx"]
        t = ticker_cache[ticker]

        for label, offset in SNAPSHOT_OFFSETS:
            target_idx = event_idx + offset
            if target_idx < 0 or target_idx >= len(t):
                continue
            row = t.iloc[target_idx].to_dict()
            row["event_id"] = ev["event_id"]
            row["candidate"] = ev["candidate"]
            row["candidate_name"] = ev["candidate_name"]
            row["event_ticker"] = ticker
            row["event_date"] = ev["event_date"]
            row["offset_label"] = label
            row["offset_days"] = offset
            row["fwd_return_20d_event"] = ev["fwd_return_20d"]
            row["fwd_return_40d_event"] = ev["fwd_return_40d"]
            snapshot_rows.append(row)

    snapshots = pd.DataFrame(snapshot_rows)
    n_unique_events = snapshots["event_id"].nunique()
    print(f"Created {len(snapshots)} snapshots ({n_unique_events} events x ~5 offsets)")

    snapshots.to_csv(OUTPUT_DIR / "research-008b-rally-start-events.csv", index=False)
    print(f"Saved: research-008b-rally-start-events.csv")

    # ──────────────────────────────────────────────────────────────────
    # STEP 4: Transition Analysis
    # ──────────────────────────────────────────────────────────────────
    print("\n--- STEP 4: Transition Analysis ---")

    timeline_rows = []
    for feat in FEATURE_COLS:
        row = {"feature": feat}
        for label, _ in SNAPSHOT_OFFSETS:
            vals = snapshots[(snapshots["offset_label"] == label)][feat].dropna()
            row[label] = float(vals.median()) if len(vals) > 0 else None
        timeline_rows.append(row)
    timeline_df = pd.DataFrame(timeline_rows)

    transition_analysis = []
    for feat in FEATURE_COLS:
        tl = timeline_df[timeline_df["feature"] == feat]
        if len(tl) == 0:
            continue
        t40 = tl.iloc[0]["T-40"]
        t20 = tl.iloc[0]["T-20"]
        t10 = tl.iloc[0]["T-10"]
        t5 = tl.iloc[0]["T-5"]
        t0 = tl.iloc[0]["T0"]
        if any(v is None for v in [t40, t20, t10, t5, t0]):
            continue

        change_40_20 = abs(t20 - t40)
        change_20_10 = abs(t10 - t20)
        change_10_5 = abs(t5 - t10)
        change_5_0 = abs(t0 - t5)
        total_change = change_40_20 + change_20_10 + change_10_5 + change_5_0

        if total_change == 0:
            continue

        pct_40_20 = change_40_20 / total_change
        pct_20_10 = change_20_10 / total_change
        pct_10_5 = change_10_5 / total_change
        pct_5_0 = change_5_0 / total_change

        transition_analysis.append({
            "feature": feat,
            "change_T40_T20": round(change_40_20, 6),
            "change_T20_T10": round(change_20_10, 6),
            "change_T10_T5": round(change_10_5, 6),
            "change_T5_T0": round(change_5_0, 6),
            "pct_T40_T20": round(pct_40_20, 4),
            "pct_T20_T10": round(pct_20_10, 4),
            "pct_T10_T5": round(pct_10_5, 4),
            "pct_T5_T0": round(pct_5_0, 4),
            "median_T40": round(t40, 6),
            "median_T20": round(t20, 6),
            "median_T10": round(t10, 6),
            "median_T5": round(t5, 6),
            "median_T0": round(t0, 6),
        })

    transition_df = pd.DataFrame(transition_analysis)

    # Rank features by which segment has largest share of change
    feature_sequences = {}
    for feat in FEATURE_COLS:
        tr = transition_df[transition_df["feature"] == feat]
        if len(tr) == 0:
            continue
        segments = [
            ("T-40 to T-20", tr.iloc[0]["pct_T40_T20"]),
            ("T-20 to T-10", tr.iloc[0]["pct_T20_T10"]),
            ("T-10 to T-5", tr.iloc[0]["pct_T10_T5"]),
            ("T-5 to T0", tr.iloc[0]["pct_T5_T0"]),
        ]
        segments.sort(key=lambda x: x[1], reverse=True)
        feature_sequences[feat] = segments

    transition_df = transition_df.sort_values("pct_T40_T20", ascending=False).reset_index(drop=True)
    transition_df.to_csv(OUTPUT_DIR / "research-008b-transition-analysis.csv", index=False)
    print(f"Saved: research-008b-transition-analysis.csv")

    print("\n  Features ranked by EARLY change (T-40 to T-20 proportion):")
    for _, r in transition_df.head(8).iterrows():
        print(f"    {r['feature']:25s}  T40-T20: {r['pct_T40_T20']:.1%}  "
              f"T20-T10: {r['pct_T20_T10']:.1%}  T10-T5: {r['pct_T10_T5']:.1%}  "
              f"T5-T0: {r['pct_T5_T0']:.1%}")

    print("\n  Features ranked by LATE change (T-5 to T0 proportion):")
    transition_late = transition_df.sort_values("pct_T5_T0", ascending=False).reset_index(drop=True)
    for _, r in transition_late.head(8).iterrows():
        print(f"    {r['feature']:25s}  T5-T0: {r['pct_T5_T0']:.1%}  "
              f"T10-T5: {r['pct_T10_T5']:.1%}  T20-T10: {r['pct_T20_T10']:.1%}  "
              f"T40-T20: {r['pct_T40_T20']:.1%}")

    # ──────────────────────────────────────────────────────────────────
    # STEP 5: Signal Stability
    # ──────────────────────────────────────────────────────────────────
    print("\n--- STEP 5: Signal Stability ---")

    # For each candidate, compute how well it predicts validated rallies
    total_ticker_days = 0
    for ticker in tickers:
        total_ticker_days += len(ticker_cache[ticker])

    signal_stability = []
    for cand_label in ["A", "B", "C", "D"]:
        cand_name = candidates[cand_label][0]
        cand_events_sub = events_df[events_df["candidate"] == cand_label]
        n_validated = len(cand_events_sub)

        # Occurrence: how many raw signals exist (before validation)
        n_raw_total = 0
        for ticker in tickers:
            t = ticker_cache[ticker]
            if cand_label == "A":
                raw = detect_candidate_a(t)
            elif cand_label == "B":
                raw = detect_candidate_b(t)
            elif cand_label == "C":
                raw = detect_candidate_c(t)
            elif cand_label == "D":
                raw = detect_candidate_d(t)
            n_raw_total += len(raw)

        # Occurrence % = raw signals per ticker-year
        n_years = (wh["Date"].max() - wh["Date"].min()).days / 365.25
        occurrence_pct = (n_raw_total / len(tickers)) / n_years * 100  # avg signals per ticker per year

        # Precision = validated / raw (among non-overlapping)
        n_raw_clean = 0
        for ticker in tickers:
            t = ticker_cache[ticker]
            if cand_label == "A":
                raw = detect_candidate_a(t)
            elif cand_label == "B":
                raw = detect_candidate_b(t)
            elif cand_label == "C":
                raw = detect_candidate_c(t)
            elif cand_label == "D":
                raw = detect_candidate_d(t)
            clean = non_overlapping(raw, min_gap=20)
            n_raw_clean += len(clean)

        precision = n_validated / n_raw_clean if n_raw_clean > 0 else 0

        # Recall: of all validated events (across all candidates), what fraction does this candidate catch?
        recall = n_validated / len(events_df) if len(events_df) > 0 else 0

        # False Positive Rate: (raw_clean - validated) / total_ticker_days
        false_positives = n_raw_clean - n_validated
        fpr = false_positives / total_ticker_days if total_ticker_days > 0 else 0

        # Expected rate if random
        base_rate = len(events_df) / total_ticker_days if total_ticker_days > 0 else 0
        actual_rate = n_validated / n_raw_clean if n_raw_clean > 0 else 0
        lift = actual_rate / base_rate if base_rate > 0 else 0

        signal_stability.append({
            "candidate": cand_label,
            "candidate_name": cand_name,
            "n_raw_signals": n_raw_total,
            "n_raw_non_overlap": n_raw_clean,
            "n_validated": n_validated,
            "occurrence_per_ticker_year": round(occurrence_pct, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "false_positive_rate": round(fpr, 6),
            "lift": round(lift, 4),
            "avg_fwd_20d": round(events_df[events_df["candidate"] == cand_label]["fwd_return_20d"].mean(), 4) if n_validated > 0 else None,
            "avg_fwd_40d": round(events_df[events_df["candidate"] == cand_label]["fwd_return_40d"].mean(), 4) if n_validated > 0 else None,
        })

    stability_df = pd.DataFrame(signal_stability)
    stability_df.to_csv(OUTPUT_DIR / "research-008b-signal-stability.csv", index=False)
    print(f"Saved: research-008b-signal-stability.csv")

    print("\n  Signal Stability Summary:")
    for _, r in stability_df.iterrows():
        print(f"    Cand {r['candidate']} ({r['candidate_name']}):")
        print(f"      Precision={r['precision']:.2%}  Recall={r['recall']:.2%}  "
              f"Lift={r['lift']:.2f}x  FPR={r['false_positive_rate']:.4%}")
        print(f"      Occurrence={r['occurrence_per_ticker_year']:.1f}/ticker-yr  "
              f"Validated={r['n_validated']}")

    # ──────────────────────────────────────────────────────────────────
    # STEP 6: Accumulation State Profile
    # ──────────────────────────────────────────────────────────────────
    print("\n--- STEP 6: Discover Accumulation State ---")

    # Look at T-20 to T0 values for all features across all validated events
    t0_snapshots = snapshots[snapshots["offset_label"] == "T0"]
    t20_snapshots = snapshots[snapshots["offset_label"] == "T-20"]
    t40_snapshots = snapshots[snapshots["offset_label"] == "T-40"]

    print("\n  Feature State at T0 (Rally Start):")
    for feat in FEATURE_COLS:
        vals = t0_snapshots[feat].dropna()
        if len(vals) == 0:
            continue
        is_bool = vals.dtype == bool or vals.dtype == np.bool_
        if is_bool:
            pct_true = vals.mean() * 100
            print(f"    {feat:30s}  %True={pct_true:.1f}%")
        else:
            p25 = vals.quantile(0.25)
            p50 = vals.median()
            p75 = vals.quantile(0.75)
            n_below_0 = (vals < 0).sum()
            pct_below = n_below_0 / len(vals) * 100
            print(f"    {feat:30s} median={p50:.4f}  [Q1={p25:.4f}, Q3={p75:.4f}]  %neg={pct_below:.0f}%")
            print(f"    {'':30s} mean={vals.mean():.4f}")

    # Build accumulation profile: find common conditions at T-20 through T0
    profile_feats = [
        ("rs_20d", "rs_20d_positive", lambda x: x > 0),
        ("rs_change_20d", "rs_change_20d_improving", lambda x: x > 0),
        ("rs_change_60d", "rs_change_60d_improving", lambda x: x > 0),
        ("above_ma20", "above_ma20", lambda x: x == True),
        ("above_ma50", "above_ma50", lambda x: x == True),
        ("above_ma100", "above_ma100", lambda x: x == True),
        ("above_ma200", "above_ma200", lambda x: x == True),
        ("volume_ratio", "volume_ratio_high", lambda x: x > 1.2),
        ("volume_ratio", "volume_ratio_very_high", lambda x: x > 1.5),
        ("golden_cross", "golden_cross", lambda x: x == True),
        ("death_cross", "death_cross", lambda x: x == True),
        ("momentum_slope", "momentum_slope_positive", lambda x: x > 0),
        ("drawdown_252d", "drawdown_gt_20pct", lambda x: x < -0.20),
        ("drawdown_252d", "drawdown_gt_30pct", lambda x: x < -0.30),
        ("drawdown_252d", "drawdown_lt_10pct", lambda x: x > -0.10),
        ("recovery_from_60d_low", "recovery_gt_10pct", lambda x: x > 0.10),
        ("recovery_from_60d_low", "recovery_gt_20pct", lambda x: x > 0.20),
        ("volatility_20d", "volatility_above_median", lambda x: x > x.median()),
    ]

    # Also compute the profile by looking at transition states
    print("\n  Accumulation State Profile (prevalence at each offset):")
    profile_rows = []
    for col, label, condition_fn in profile_feats:
        if col not in snapshots.columns:
            continue
        profile_row = {"condition": label, "feature": col}
        for label_name, _ in SNAPSHOT_OFFSETS:
            vals = snapshots[(snapshots["offset_label"] == label_name)][col].dropna()
            if len(vals) == 0:
                profile_row[label_name] = None
            else:
                try:
                    if col in ["above_ma20", "above_ma50", "above_ma100", "above_ma200",
                                "golden_cross", "death_cross"]:
                        true_pct = vals.mean() * 100
                        profile_row[label_name] = round(true_pct, 1)
                    elif "volatility_above_median" == label:
                        median_val = snapshots[col].median()
                        cond_true = (vals > median_val).mean() * 100
                        profile_row[label_name] = round(cond_true, 1)
                    elif "improving" in label:
                        cond_true = (vals > 0).mean() * 100
                        profile_row[label_name] = round(cond_true, 1)
                    elif "positive" in label:
                        cond_true = (vals > 0).mean() * 100
                        profile_row[label_name] = round(cond_true, 1)
                    elif "high" in label:
                        if "very" in label:
                            cond_true = (vals > 1.5).mean() * 100
                        else:
                            cond_true = (vals > 1.2).mean() * 100
                        profile_row[label_name] = round(cond_true, 1)
                    elif "gt_20pct" in label:
                        cond_true = (vals < -0.20).mean() * 100
                        profile_row[label_name] = round(cond_true, 1)
                    elif "gt_30pct" in label:
                        cond_true = (vals < -0.30).mean() * 100
                        profile_row[label_name] = round(cond_true, 1)
                    elif "lt_10pct" in label:
                        cond_true = (vals > -0.10).mean() * 100
                        profile_row[label_name] = round(cond_true, 1)
                    elif "gt_10pct" in label:
                        cond_true = (vals > 0.10).mean() * 100
                        profile_row[label_name] = round(cond_true, 1)
                    elif "gt_20pct" in label:
                        cond_true = (vals > 0.20).mean() * 100
                        profile_row[label_name] = round(cond_true, 1)
                    else:
                        profile_row[label_name] = round(float(vals.median()), 4)
                except Exception:
                    profile_row[label_name] = None
        profile_rows.append(profile_row)

    profile_df = pd.DataFrame(profile_rows)

    # Build accumulation profile markdown
    print("\n  Most common conditions at T-5 and T0:")
    for _, r in profile_df.iterrows():
        t5 = r.get("T-5", None)
        t0 = r.get("T0", None)
        change = ""
        if t5 is not None and t0 is not None:
            change = f" (change: {t0 - t5:+.1f}pp)" if isinstance(t5, (int, float)) else ""
        print(f"    {r['condition']:40s}  T-5={t5}  T0={t0}{change}")

    # ──────────────────────────────────────────────────────────────────
    # GENERATE DELIVERABLES
    # ──────────────────────────────────────────────────────────────────
    print("\n--- Generating Deliverables ---")

    # Already saved:
    #   research-008b-rally-start-events.csv
    #   research-008b-transition-analysis.csv
    #   research-008b-signal-stability.csv
    #
    # Remaining:
    #   research-008b-accumulation-profile.md
    #   research-008b-executive-summary.md

    # ── Accumulation Profile MD ──
    acc_lines = []
    acc_lines.append("# RESEARCH-008B: Accumulation State Profile\n")
    acc_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    acc_lines.append("---\n\n")

    acc_lines.append("## Definition\n\n")
    acc_lines.append("The accumulation state is the set of conditions most commonly observed ")
    acc_lines.append("immediately before a validated rally start event (T-5 through T0).\n\n")
    acc_lines.append("Validated events are rally start signals (from 4 candidate definitions) ")
    acc_lines.append("that pass forward return validation (fwd 20D > +10% OR fwd 40D > +15%).\n\n")

    acc_lines.append("## Candidate Definitions\n\n")
    acc_lines.append("| Candidate | Signal | Validation |\n")
    acc_lines.append("|-----------|--------|------------|\n")
    acc_lines.append("| A | Price crosses above MA20 after >= 20 days below | fwd20>+10% or fwd40>+15% |\n")
    acc_lines.append("| B | RS20 changes from negative to positive | same |\n")
    acc_lines.append("| C | Volume Ratio > 1.3 AND price above MA20 | same |\n")
    acc_lines.append("| D | Momentum Slope changes from negative to positive | same |\n\n")

    acc_lines.append("---\n\n")

    acc_lines.append("## Condition Prevalence at Each Offset\n\n")
    acc_lines.append("Values represent the percentage of events where each condition is true ")
    acc_lines.append("at each snapshot offset:\n\n")
    acc_lines.append("| Condition | T-40 | T-20 | T-10 | T-5 | T0 |\n")
    acc_lines.append("|-----------|------|------|------|-----|----|\n")
    for _, r in profile_df.iterrows():
        vals = []
        for label, _ in SNAPSHOT_OFFSETS:
            v = r.get(label, None)
            vals.append(f"{v:.1f}%" if v is not None else "N/A")
        acc_lines.append(f"| {r['condition']:40s} | {' | '.join(vals)} |\n")

    acc_lines.append("\n## Median Feature Values at Each Offset\n\n")
    acc_lines.append("| Feature | T-40 | T-20 | T-10 | T-5 | T0 |\n")
    acc_lines.append("|---------|------|------|------|-----|----|\n")
    for _, r in timeline_df.iterrows():
        vals = []
        for label, _ in SNAPSHOT_OFFSETS:
            v = r.get(label, None)
            vals.append(f"{v:.4f}" if v is not None else "N/A")
        acc_lines.append(f"| {r['feature']:25s} | {' | '.join(vals)} |\n")

    acc_lines.append("\n## Discovered Accumulation State\n\n")

    # Find the most prevalent condition at each offset leading to T0
    t0_conds = profile_df[["condition", "T0"]].dropna().sort_values("T0", ascending=False)
    t5_conds = profile_df[["condition", "T-5"]].dropna().sort_values("T-5", ascending=False)
    t20_conds = profile_df[["condition", "T-20"]].dropna().sort_values("T-20", ascending=False)

    acc_lines.append("### Most Common Conditions at T0 (Rally Start)\n\n")
    for _, r in t0_conds.head(10).iterrows():
        acc_lines.append(f"- **{r['condition']}**: {r['T0']:.1f}%\n")
    acc_lines.append("\n")

    acc_lines.append("### Most Common Conditions at T-5 (5 Days Before)\n\n")
    for _, r in t5_conds.head(10).iterrows():
        acc_lines.append(f"- **{r['condition']}**: {r['T-5']:.1f}%\n")
    acc_lines.append("\n")

    acc_lines.append("### Most Common Conditions at T-20 (20 Days Before)\n\n")
    for _, r in t20_conds.head(10).iterrows():
        acc_lines.append(f"- **{r['condition']}**: {r['T-20']:.1f}%\n")
    acc_lines.append("\n")

    acc_lines.append("## Transition Sequence (Data-Driven)\n\n")
    acc_lines.append("Features ranked by when their strongest change occurs:\n\n")

    early_feats = transition_df.head(5)
    acc_lines.append("### Early Movers (largest change at T-40 to T-20)\n\n")
    for _, r in early_feats.iterrows():
        acc_lines.append(f"- **{r['feature']}**: {r['pct_T40_T20']:.0%} of change happens T-40 to T-20\n")
    acc_lines.append("\n")

    late_feats = transition_df.sort_values("pct_T5_T0", ascending=False).head(5)
    acc_lines.append("### Late Movers (largest change at T-5 to T0)\n\n")
    for _, r in late_feats.iterrows():
        acc_lines.append(f"- **{r['feature']}**: {r['pct_T5_T0']:.0%} of change happens T-5 to T0\n")
    acc_lines.append("\n")

    acc_lines.append("### Proposed Transition Sequence\n\n")
    # Build data-driven sequence based on when each feature's peak change occurs
    sequence_map = {"T-40 to T-20": [], "T-20 to T-10": [], "T-10 to T-5": [], "T-5 to T0": []}
    for _, r in transition_df.iterrows():
        segments = [
            ("T-40 to T-20", r["pct_T40_T20"]),
            ("T-20 to T-10", r["pct_T20_T10"]),
            ("T-10 to T-5", r["pct_T10_T5"]),
            ("T-5 to T0", r["pct_T5_T0"]),
        ]
        peak_segment = max(segments, key=lambda x: x[1])
        if peak_segment[1] > 0.25:  # At least 25% of change in this segment
            sequence_map[peak_segment[0]].append(r["feature"])

    for seg_name in ["T-40 to T-20", "T-20 to T-10", "T-10 to T-5", "T-5 to T0"]:
        feats = sequence_map[seg_name]
        if feats:
            acc_lines.append(f"**{seg_name}**: {', '.join(f'`{f}`' for f in feats)}\n\n")

    acc_lines.append("---\n\n")
    acc_lines.append("*End of RESEARCH-008B Accumulation Profile*\n")

    with open(OUTPUT_DIR / "research-008b-accumulation-profile.md", "w", encoding="utf-8") as f:
        f.writelines(acc_lines)
    print("Saved: research-008b-accumulation-profile.md")

    # ── Executive Summary MD ──
    exec_lines = []
    exec_lines.append("# RESEARCH-008B: Rally Initiation Detection — Executive Summary\n")
    exec_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    exec_lines.append("---\n\n")

    exec_lines.append("## Core Question\n\n")
    exec_lines.append("*What is the earliest detectable sign that a future winner is transitioning ")
    exec_lines.append("from distress into accumulation?*\n\n")
    exec_lines.append("---\n\n")

    exec_lines.append("## Key Findings\n\n")

    # Best candidate
    best_candidate = stability_df.sort_values("lift", ascending=False).iloc[0]
    exec_lines.append(f"### 1. Best Rally Start Signal: Candidate {best_candidate['candidate']}\n\n")
    exec_lines.append(f"**{best_candidate['candidate_name']}**\n\n")
    exec_lines.append(f"- Validated events: {best_candidate['n_validated']}\n")
    exec_lines.append(f"- Precision: {best_candidate['precision']:.2%}\n")
    exec_lines.append(f"- Recall: {best_candidate['recall']:.2%}\n")
    exec_lines.append(f"- Lift vs random: {best_candidate['lift']:.2f}x\n")
    exec_lines.append(f"- False Positive Rate: {best_candidate['false_positive_rate']:.4%}\n")
    exec_lines.append(f"- Avg forward 20D return: {best_candidate['avg_fwd_20d']:.2%}\n")
    exec_lines.append(f"- Avg forward 40D return: {best_candidate['avg_fwd_40d']:.2%}\n\n")

    exec_lines.append("### 2. Signal Stability Comparison\n\n")
    exec_lines.append("| Candidate | Precision | Recall | Lift | FPR | Validated Events |\n")
    exec_lines.append("|-----------|-----------|--------|------|-----|-----------------|\n")
    for _, r in stability_df.iterrows():
        exec_lines.append(f"| {r['candidate']} ({r['candidate_name']}) | "
                          f"{r['precision']:.2%} | {r['recall']:.2%} | "
                          f"{r['lift']:.2f}x | {r['false_positive_rate']:.4%} | "
                          f"{r['n_validated']} |\n")

    exec_lines.append("\n### 3. Earliest Detectable Sign\n\n")

    # Find what changes first
    early_df = transition_df[transition_df["pct_T40_T20"] > transition_df["pct_T5_T0"]]
    if len(early_df) > 0:
        earliest = early_df.sort_values("pct_T40_T20", ascending=False).iloc[0]
        exec_lines.append(f"**{earliest['feature']}** — {earliest['pct_T40_T20']:.0%} of its total change ")
        exec_lines.append(f"occurs between T-40 and T-20, before the rally start.\n\n")

        exec_lines.append("Other early-changing features:\n\n")
        for _, r in early_df.head(5).iterrows():
            exec_lines.append(f"- `{r['feature']}`: {r['pct_T40_T20']:.0%} change at T-40→T-20\n")
    exec_lines.append("\n")

    exec_lines.append("### 4. Transition Sequence\n\n")
    exec_lines.append("Based on when features peak in rate of change:\n\n")

    for seg_name in ["T-40 to T-20", "T-20 to T-10", "T-10 to T-5", "T-5 to T0"]:
        feats = sequence_map[seg_name]
        if feats:
            exec_lines.append(f"**{seg_name}**: {', '.join(f'`{f}`' for f in feats)}\n\n")

    exec_lines.append("### 5. Accumulation State Profile\n\n")
    exec_lines.append("The most common condition set at T-5 (just before rally start):\n\n")
    for _, r in t5_conds.head(8).iterrows():
        exec_lines.append(f"- {r['condition']}: {r['T-5']:.1f}% of events\n")
    exec_lines.append("\n")

    exec_lines.append("The most common condition set at T0 (rally start):\n\n")
    for _, r in t0_conds.head(8).iterrows():
        exec_lines.append(f"- {r['condition']}: {r['T0']:.1f}% of events\n")
    exec_lines.append("\n")

    exec_lines.append("### 6. Total Validated Events\n\n")
    exec_lines.append(f"- Total validated rally start events: {len(events_df)}\n")
    exec_lines.append(f"- Unique tickers with events: {events_df['ticker'].nunique()}\n")
    exec_lines.append(f"- Date range: {wh['Date'].min().date()} to {wh['Date'].max().date()}\n\n")

    exec_lines.append("---\n\n")

    exec_lines.append("## Answer to Research Question\n\n")
    exec_lines.append("*What is the earliest detectable sign that a future winner is transitioning ")
    exec_lines.append("from distress into accumulation?*\n\n")

    # Craft the answer based on data
    if len(early_df) > 0:
        earliest_feat = early_df.sort_values("pct_T40_T20", ascending=False).iloc[0]
        exec_lines.append(f"The earliest detectable sign is a change in **`{earliest_feat['feature']}`**, ")
        exec_lines.append(f"which begins shifting {earliest_feat['pct_T40_T20']:.0%} of its total movement ")
        exec_lines.append(f"between T-40 and T-20 before the rally start.\n\n")

        exec_lines.append("This is followed by:\n\n")
        count = 0
        for _, r in early_df.sort_values("pct_T40_T20", ascending=False).iterrows():
            if r["feature"] == earliest_feat["feature"]:
                continue
            if count >= 3:
                break
            exec_lines.append(f"{count+2}. `{r['feature']}` begins changing\n")
            count += 1

        exec_lines.append(f"\nThe last changes occur in:\n\n")
        for _, r in late_feats.iterrows():
            exec_lines.append(f"- `{r['feature']}` (concentrated at T-5 to T0)\n")

    exec_lines.append("\n---\n\n")
    exec_lines.append("*End of RESEARCH-008B Executive Summary*\n")

    with open(OUTPUT_DIR / "research-008b-executive-summary.md", "w", encoding="utf-8") as f:
        f.writelines(exec_lines)
    print("Saved: research-008b-executive-summary.md")

    # ──────────────────────────────────────────────────────────────────
    # FINAL SUMMARY
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("RESEARCH-008B COMPLETE")
    print("=" * 80)
    print(f"\nDeliverables in {OUTPUT_DIR}:")
    print("  research-008b-rally-start-events.csv")
    print("  research-008b-transition-analysis.csv")
    print("  research-008b-signal-stability.csv")
    print("  research-008b-accumulation-profile.md")
    print("  research-008b-executive-summary.md")

    print(f"\nTotal validated events: {len(events_df)}")
    print(f"Best candidate: {stability_df.sort_values('lift', ascending=False).iloc[0]['candidate_name']}")
    if len(early_df) > 0:
        print(f"Earliest sign: {early_df.sort_values('pct_T40_T20', ascending=False).iloc[0]['feature']}")

    print("\nStopping here per instructions. Do NOT build timing engine, optimize thresholds, or create overlays.")


if __name__ == "__main__":
    main()
