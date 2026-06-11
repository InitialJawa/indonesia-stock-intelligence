import csv
import json
import datetime
from pathlib import Path
from collections import defaultdict

WAREHOUSE = Path("warehouse_historical/warehouse_v3_growth_fix.csv")
LEADERS = Path("data/current/leaders_latest.csv")
OUTPUT = Path("dashboard/data/rk.json")
OUTPUT_FULL = Path("dashboard/data/rank_history.json")

def read_csv(path):
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))

def compute_rank_change():
    wh_rows = read_csv(WAREHOUSE)
    ld_rows = read_csv(LEADERS)

    # 1) Monthly rankings from warehouse (final_score desc)
    months = defaultdict(list)
    for r in wh_rows:
        month = r["month"]
        ticker = r["ticker"]
        try:
            score = float(r["final_score"])
        except (ValueError, TypeError):
            score = 0
        months[month].append((ticker, score))

    # Sort months chronologically
    sorted_months = sorted(months.keys())

    # Rank per ticker per month
    rank_map = {}  # month -> {ticker: rank}
    for m in sorted_months:
        items = sorted(months[m], key=lambda x: -x[1])
        rank_map[m] = {t[0]: i + 1 for i, t in enumerate(items)}

    # 2) Full history: per ticker, list of (month, rank) sorted chronologically
    ticker_history = defaultdict(list)
    for m in sorted_months:
        for ticker, rank in rank_map[m].items():
            ticker_history[ticker].append({"month": m[:7], "rank": rank})

    # 3) Month-over-month rank_change for full history
    #    rank_change = rank[prev] - rank[cur]  (positive = UP)
    monthly_changes = {}  # month -> {ticker: change}
    for i in range(1, len(sorted_months)):
        cur_m = sorted_months[i][:7]
        prev_m = sorted_months[i-1]
        cur_ranks_m = rank_map[sorted_months[i]]
        prev_ranks_m = rank_map[prev_m]
        changes = {}
        all_tickers = set(cur_ranks_m.keys()) | set(prev_ranks_m.keys())
        for t in all_tickers:
            cur_r = cur_ranks_m.get(t)
            prev_r = prev_ranks_m.get(t)
            if cur_r is not None and prev_r is not None:
                changes[t] = prev_r - cur_r
            elif cur_r is not None:
                changes[t] = 99  # NEW entry
            elif prev_r is not None:
                changes[t] = -99  # DROPPED OUT
        monthly_changes[cur_m] = changes

    # 4) Latest month from warehouse
    latest_wh_month = sorted_months[-1]

    # 5) Current ranking from leaders_latest.csv
    current_ranks = {}
    for r in ld_rows:
        try:
            t = r["ticker"]
            rank = int(r["rank"])
            current_ranks[t] = rank
        except (ValueError, KeyError):
            continue

    # 6) Compute rank_change: current L rank vs last warehouse month rank
    rk = {}
    for ticker, cur_rank in current_ranks.items():
        prev_ranks = rank_map.get(latest_wh_month, {})
        prev_rank = prev_ranks.get(ticker)
        if prev_rank is not None:
            change = prev_rank - cur_rank
        else:
            change = 99
        rk[ticker] = change

    # 7) Save current rank_change map
    with open(OUTPUT, "w") as f:
        json.dump(rk, f, separators=(",", ":"))
    print(f"[+] Saved rank_change map ({len(rk)} tickers) to {OUTPUT}")

    # 8) Save full rank history + monthly changes
    full = {
        "months": [m[:7] for m in sorted_months],
        "tickers": {t: h for t, h in sorted(ticker_history.items())},
        "monthly_changes": monthly_changes
    }
    with open(OUTPUT_FULL, "w") as f:
        json.dump(full, f, separators=(",", ":"))
    print(f"[+] Saved full rank history + monthly changes to {OUTPUT_FULL}")
    print(f"    Months: {len(sorted_months)}, Tickers: {len(ticker_history)}, Change periods: {len(monthly_changes)}")

    # Print change summary
    up = sum(1 for v in rk.values() if 0 < v < 99)
    down = sum(1 for v in rk.values() if v < 0)
    new = sum(1 for v in rk.values() if v == 99)
    unch = sum(1 for v in rk.values() if v == 0)
    print(f"    UP: {up}, DOWN: {down}, NEW: {new}, UNCHANGED: {unch}")

    # Save a daily snapshot of current rankings for future comparisons
    snap_dir = Path("data/history/rank_snapshots")
    snap_dir.mkdir(parents=True, exist_ok=True)
    today = sorted_months[-1][:7]  # Use latest warehouse month as ref
    today_str = datetime.date.today().isoformat()
    snapshot = {"date": today_str, "ref_month": today, "rankings": current_ranks}
    with open(snap_dir / f"{today_str}.json", "w") as f:
        json.dump(snapshot, f, separators=(",", ":"))

if __name__ == "__main__":
    compute_rank_change()
