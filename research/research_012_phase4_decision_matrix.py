"""
RESEARCH-012 Phase 4 — Exit + Rank Decision Matrix
====================================================
Build empirical decision matrix from every EXIT state x Rank combination.
Backtest forward returns for each cell. Derive decision rules.

Matrix rows: EXIT states (HEALTHY, EXIT WATCH, WEAKENING, EXIT RISK, EXIT)
Matrix cols: Rank buckets (Top 10, Rank 11-20, Rank >20)

Output: Forward return for each cell, decision rules table.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DAILY_PATH = PROJECT_ROOT / "database" / "historical" / "warehouse_daily_v4.parquet"
WH_PATH = PROJECT_ROOT / "warehouse_historical" / "warehouse_v3.csv"
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TICKERS_IDX30 = [
    'ADRO.JK','AKRA.JK','AMMN.JK','ANTM.JK','ASII.JK',
    'BBCA.JK','BBNI.JK','BBRI.JK','BMRI.JK','BRPT.JK',
    'CPIN.JK','ESSA.JK','EXCL.JK','GOTO.JK','HEAL.JK',
    'ICBP.JK','INDF.JK','INTP.JK','ITMG.JK','KLBF.JK',
    'MAPI.JK','MDKA.JK','MIKA.JK','PGAS.JK','PTBA.JK',
    'SIDO.JK','SMGR.JK','TLKM.JK','TPIA.JK','UNTR.JK',
]

STATE_ORDER = ["HEALTHY", "EXIT WATCH", "WEAKENING", "EXIT RISK", "EXIT"]


def load_data():
    print("Loading warehouse daily v4...")
    cols = ["Date","ticker","Close","rs_20d","rs_change_20d","ma50","ma100","drawdown_252d"]
    daily = pd.read_parquet(DAILY_PATH, columns=cols)
    daily["Date"] = pd.to_datetime(daily["Date"])
    daily = daily[daily["ticker"].isin(TICKERS_IDX30)].sort_values(["ticker","Date"])
    print(f"  Daily: {len(daily):,} records ({daily['Date'].min().date()} to {daily['Date'].max().date()})")

    print("Loading warehouse v3 for Config B ranks...")
    wh = pd.read_csv(WH_PATH, usecols=["ticker","month","final_score"])
    wh["month"] = pd.to_datetime(wh["month"])
    wh = wh[wh["ticker"].isin(TICKERS_IDX30)].copy()
    wh["rank"] = wh.groupby("month")["final_score"].rank(ascending=False, method="min").astype(int)
    print(f"  Warehouse: {len(wh)} records, {wh['month'].nunique()} months, {wh['ticker'].nunique()} tickers")
    return daily, wh


def compute_exit_states(daily_df, rank_df):
    """Compute EXIT state + rank for every ticker-day."""
    print("\nComputing EXIT states and ranks...")
    df = daily_df.copy()
    df["date_dt"] = df["Date"].dt.normalize()

    # Merge rank (forward-fill monthly)
    r = rank_df.rename(columns={"month": "date_dt"})
    df = df.merge(r, on=["ticker","date_dt"], how="left")
    df["rank"] = df.groupby("ticker")["rank"].ffill().fillna(99).astype(int)

    # Filter to 2022+ (when rank data is available)
    df = df[df["date_dt"] >= "2022-01-01"].copy()

    # Rank buckets
    df["rank_bucket"] = pd.cut(df["rank"], bins=[0, 10, 20, 999],
                               labels=["Top 10", "Rank 11-20", "Rank >20"],
                               right=True)

    # Compute exit state for each row
    def exit_state(row):
        close = row["Close"]
        rs20 = row["rs_20d"]
        rsc = row["rs_change_20d"]
        ma50 = row["ma50"]
        ma100 = row["ma100"]
        rank = row["rank"]
        dd = row.get("drawdown_252d", np.nan)

        if pd.isna(close) or pd.isna(rs20):
            return "UNKNOWN"

        rule_a = rank > 10
        rule_b = (not pd.isna(rs20) and rs20 < 0 and not pd.isna(rsc) and rsc < 0)
        rule_c = (not pd.isna(ma50) and close < ma50)
        rule_d1 = (not pd.isna(ma100) and close < ma100 and not pd.isna(rs20) and rs20 < 0 and not pd.isna(rsc) and rsc < 0)
        rule_d2 = (not pd.isna(dd) and dd < -0.15)

        if rule_d1 or rule_d2:
            return "EXIT"
        elif rule_c:
            return "EXIT RISK"
        elif rule_b:
            return "WEAKENING"
        elif rule_a:
            return "EXIT WATCH"
        else:
            return "HEALTHY"

    df["exit_state"] = df.apply(exit_state, axis=1)
    df = df[df["exit_state"] != "UNKNOWN"]
    print(f"  {len(df):,} classified records")
    print("\n  State x Rank Bucket distribution:")
    crosstab = pd.crosstab(df["exit_state"], df["rank_bucket"],
                           margins=True, margins_name="Total")
    print(crosstab.to_string())
    return df


def compute_forward_returns_matrix(df, daily_pivot):
    """For each (exit_state, rank_bucket), compute avg forward returns."""
    print("\nComputing forward returns per cell...")
    horizons = [(21, "30D"), (42, "60D"), (63, "90D")]

    results = []
    for (state, bucket), group in df.groupby(["exit_state", "rank_bucket"]):
        cell = {"exit_state": state, "rank_bucket": bucket, "count": len(group)}

        # Sample for performance (up to 2000 per cell)
        if len(group) > 2000:
            group = group.sample(n=2000, random_state=42)

        for h_days, h_label in horizons:
            fwd_returns = []
            for _, row in group.iterrows():
                ticker = row["ticker"]
                dt = row["date_dt"]
                if ticker not in daily_pivot.columns:
                    continue
                ps = daily_pivot[ticker]
                try:
                    loc = ps.index.get_loc(dt)
                except KeyError:
                    continue
                px = ps.iloc[loc]
                if pd.isna(px) or px <= 0:
                    continue
                tloc = loc + h_days
                if tloc >= len(ps):
                    continue
                fpx = ps.iloc[tloc]
                if pd.isna(fpx) or fpx <= 0:
                    continue
                fwd_returns.append((fpx / px) - 1)

            if len(fwd_returns) > 0:
                arr = np.array(fwd_returns)
                cell[f"{h_label}_avg"] = arr.mean()
                cell[f"{h_label}_med"] = np.median(arr)
                cell[f"{h_label}_wr"] = (arr > 0).mean()
                cell[f"{h_label}_n"] = len(arr)
            else:
                cell[f"{h_label}_avg"] = np.nan
                cell[f"{h_label}_med"] = np.nan
                cell[f"{h_label}_wr"] = np.nan
                cell[f"{h_label}_n"] = 0

        results.append(cell)

    matrix = pd.DataFrame(results)
    return matrix


def build_decision_rules(matrix, baseline):
    """Derive decision rules from matrix performance vs baseline."""
    print("\n" + "=" * 80)
    print("DECISION MATRIX — 30D Forward Returns")
    print("=" * 80)

    # Pivot for human-readable table
    pivot = matrix.pivot_table(
        index="exit_state", columns="rank_bucket",
        values="30D_avg", aggfunc="first"
    )
    pivot_count = matrix.pivot_table(
        index="exit_state", columns="rank_bucket",
        values="30D_n", aggfunc="first"
    )

    print(f"\n  30D Average Return (%)")
    print(f"  {'State':<15} {'Top 10':<12} {'Rank 11-20':<12} {'Rank >20':<12}")
    print(f"  {'-'*51}")
    for state in STATE_ORDER:
        if state in pivot.index:
            row = pivot.loc[state]
            print(f"  {state:<15} {row.get('Top 10', np.nan)*100:<12.2f}% "
                  f"{row.get('Rank 11-20', np.nan)*100:<12.2f}% "
                  f"{row.get('Rank >20', np.nan)*100:<12.2f}%")

    print(f"\n  30D Win Rate (%)")
    wr_pivot = matrix.pivot_table(
        index="exit_state", columns="rank_bucket",
        values="30D_wr", aggfunc="first"
    )
    print(f"  {'State':<15} {'Top 10':<12} {'Rank 11-20':<12} {'Rank >20':<12}")
    print(f"  {'-'*51}")
    for state in STATE_ORDER:
        if state in wr_pivot.index:
            row = wr_pivot.loc[state]
            print(f"  {state:<15} {row.get('Top 10', np.nan)*100:<12.1f}% "
                  f"{row.get('Rank 11-20', np.nan)*100:<12.1f}% "
                  f"{row.get('Rank >20', np.nan)*100:<12.1f}%")

    # Also show 90D
    print(f"\n  90D Average Return (%)")
    pivot90 = matrix.pivot_table(
        index="exit_state", columns="rank_bucket",
        values="90D_avg", aggfunc="first"
    )
    print(f"  {'State':<15} {'Top 10':<12} {'Rank 11-20':<12} {'Rank >20':<12}")
    print(f"  {'-'*51}")
    for state in STATE_ORDER:
        if state in pivot90.index:
            row = pivot90.loc[state]
            print(f"  {state:<15} {row.get('Top 10', np.nan)*100:<12.2f}% "
                  f"{row.get('Rank 11-20', np.nan)*100:<12.2f}% "
                  f"{row.get('Rank >20', np.nan)*100:<12.2f}%")

    # Derive rules
    print("\n" + "=" * 80)
    print("DERIVED DECISION RULES (30D)")
    print("=" * 80)
    print()
    print("Rules based on forward return vs overall average:")
    print(f"  Overall market avg 30D: {baseline:.2f}%")
    print(f"  Threshold: >{baseline:.2f}% = FAVORABLE, <{baseline:.2f}% = UNFAVORABLE")
    print()

    rules = []
    for state in STATE_ORDER:
        for bucket in ["Top 10", "Rank 11-20", "Rank >20"]:
            try:
                val = matrix[(matrix["exit_state"] == state) &
                             (matrix["rank_bucket"] == bucket)]["30D_avg"].values[0]
                if pd.isna(val):
                    continue
                wr = matrix[(matrix["exit_state"] == state) &
                            (matrix["rank_bucket"] == bucket)]["30D_wr"].values[0]
                n = matrix[(matrix["exit_state"] == state) &
                           (matrix["rank_bucket"] == bucket)]["30D_n"].values[0]
            except (IndexError, KeyError):
                continue

            if val > baseline and wr > 0.50:
                action = "HOLD"
            elif val > 0 and wr > 0.50:
                action = "HOLD (weak)"
            elif val > 0:
                action = "HOLD (caution)"
            elif val > -0.02:
                action = "REVIEW"
            elif val > -0.05:
                action = "TRIM"
            else:
                action = "SELL"

            rules.append({
                "exit_state": state,
                "rank_bucket": bucket,
                "30D_avg": f"{val*100:.2f}%",
                "win_rate": f"{wr*100:.1f}%",
                "n": n,
                "decision": action,
            })

    rules_df = pd.DataFrame(rules)
    print(f"  {'State':<15} {'Rank':<12} {'30D Return':<12} {'Win Rate':<10} {'Decision':<12}")
    print(f"  {'-'*61}")
    for _, row in rules_df.iterrows():
        print(f"  {row['exit_state']:<15} {row['rank_bucket']:<12} "
              f"{row['30D_avg']:<12} {row['win_rate']:<10} {row['decision']:<12}")

    return rules_df


def main():
    print("=" * 80)
    print("RESEARCH-012 Phase 4: Exit + Rank Decision Matrix")
    print("=" * 80)

    daily_df, rank_df = load_data()

    # Build price lookup for forward returns
    daily_pivot = daily_df.pivot_table(
        index="Date", columns="ticker", values="Close"
    ).sort_index()
    print(f"\nPrice matrix: {daily_pivot.shape[0]} days x {daily_pivot.shape[1]} tickers")

    # Compute EXIT states
    classified = compute_exit_states(daily_df, rank_df)

    # Compute matrix
    matrix = compute_forward_returns_matrix(classified, daily_pivot)
    matrix.to_csv(OUTPUT_DIR / "research_012_phase4_matrix.csv", index=False)
    print(f"\nMatrix saved: {OUTPUT_DIR / 'research_012_phase4_matrix.csv'}")

    # Overall baseline
    all_30d = matrix["30D_avg"].dropna()
    baseline = all_30d.mean()

    # Build decision rules
    rules_df = build_decision_rules(matrix, baseline)
    rules_df.to_csv(OUTPUT_DIR / "research_012_phase4_rules.csv", index=False)
    print(f"\nRules saved: {OUTPUT_DIR / 'research_012_phase4_rules.csv'}")

    print("\n" + "=" * 80)
    print("PHASE 4 SUMMARY")
    print("=" * 80)
    print(f"Decision matrix created with {len(matrix)} cells")
    print(f"Decision rules derived for {len(rules_df)} state-rank combinations")
    print("Phase 4 complete.")


if __name__ == "__main__":
    main()
