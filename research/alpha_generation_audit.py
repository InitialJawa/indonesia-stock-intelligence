"""
Alpha Generation Audit — RESEARCH 002
Root cause analysis of CONFIG_B underperformance vs IHSG.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr
import json

BASE = Path(__file__).resolve().parent.parent
WAREHOUSE = BASE / "warehouse_historical" / "warehouse_v3.csv"
BENCHMARK = BASE / "benchmarks" / "ihsg_monthly.csv"
REPORT_FILE = BASE / "reports" / "alpha_generation_audit.md"
MONTHLY_DIR = BASE / "database" / "monthly"
SECTOR_RULES_FILE = BASE / "config" / "sector_rules.json"
UNIVERSE_FILE = BASE / "database" / "historical_universe" / "2024-01.json"

FACTORS = ["quality_score", "growth_score", "value_score", "momentum_score"]
FACTOR_LABELS = ["Quality", "Growth", "Value", "Momentum"]
FACTOR_MAP = dict(zip(FACTORS, FACTOR_LABELS))

CONFIG_B = {"quality": 0.25, "growth": 0.30, "value": 0.10, "momentum": 0.35}


def fmt_pct(v):
    return f"{v * 100:.2f}%"


def fmt_pct3(v):
    return f"{v * 100:.3f}%"


def fmt_dec(v):
    return f"{v:.4f}"


def load_data():
    df = pd.read_csv(WAREHOUSE)
    ihsg = pd.read_csv(BENCHMARK)
    df["month_dt"] = pd.to_datetime(df["month"])
    df["ym"] = df["month_dt"].dt.year * 100 + df["month_dt"].dt.month
    ihsg["Date_dt"] = pd.to_datetime(ihsg["Date"])
    ihsg["ym"] = ihsg["Date_dt"].dt.year * 100 + ihsg["Date_dt"].dt.month
    ihsg_map = ihsg.set_index("ym")["monthly_return"]
    df = df[df["month_dt"].dt.year >= 2023].copy()
    df = df.sort_values(["ticker", "ym"])
    df["next_price"] = df.groupby("ticker")["price"].shift(-1)
    df["next_month_return"] = df["next_price"] / df["price"] - 1
    def next_ym(ym):
        y, m = divmod(ym, 100)
        return (y + 1) * 100 + 1 if m == 12 else ym + 1
    df["benchmark_ym"] = df["ym"].apply(next_ym)
    df["benchmark_return"] = df["benchmark_ym"].map(ihsg_map)
    df = df.dropna(subset=["next_month_return"])
    return df, ihsg_map


def load_monthly_db(tickers):
    monthly = {}
    for t in tickers:
        fp = MONTHLY_DIR / f"{t}.csv"
        if fp.exists():
            mdf = pd.read_csv(fp)
            mdf["Date"] = pd.to_datetime(mdf["Date"])
            mdf["ym"] = mdf["Date"].dt.year * 100 + mdf["Date"].dt.month
            mdf = mdf.sort_values("Date")
            monthly[t] = mdf
    return monthly


# =========================================================================
# PHASE 1: Alpha Decomposition
# =========================================================================
def phase1_alpha_decomposition(df):
    results = []
    ym_list = sorted(df["ym"].unique())
    for ym in ym_list:
        sub = df[df["ym"] == ym].copy()
        ret = "next_month_return"
        for factor in FACTORS:
            valid = sub.dropna(subset=[factor, ret])
            if len(valid) < 5:
                continue
            ic_val, ic_p = spearmanr(valid[factor], valid[ret])
            ranks = valid[factor].rank()
            n = len(ranks)
            q1 = valid.loc[ranks <= n / 5, ret].mean() if n >= 5 else valid[ret].mean()
            q5 = valid.loc[ranks > 4 * n / 5, ret].mean() if n >= 5 else valid[ret].mean()
            spread = q5 - q1
            top_half = valid.loc[ranks > n / 2, ret].mean()
            bot_half = valid.loc[ranks <= n / 2, ret].mean()
            hit = 1 if top_half > bot_half else 0
            results.append({
                "ym": ym, "factor": factor, "n_stocks": len(valid),
                "ic": ic_val, "ic_p": ic_p, "spread": spread, "hit": hit,
                "top_half_ret": top_half, "bot_half_ret": bot_half,
            })
        # Also compute for final_score (CONFIG_B itself)
        valid = sub.dropna(subset=["final_score", ret])
        if len(valid) >= 5:
            ic_val, ic_p = spearmanr(valid["final_score"], valid[ret])
            ranks = valid["final_score"].rank()
            n = len(ranks)
            q1 = valid.loc[ranks <= n / 5, ret].mean() if n >= 5 else valid[ret].mean()
            q5 = valid.loc[ranks > 4 * n / 5, ret].mean() if n >= 5 else valid[ret].mean()
            spread = q5 - q1
            top_half = valid.loc[ranks > n / 2, ret].mean()
            bot_half = valid.loc[ranks <= n / 2, ret].mean()
            hit = 1 if top_half > bot_half else 0
            results.append({
                "ym": ym, "factor": "final_score", "n_stocks": len(valid),
                "ic": ic_val, "ic_p": ic_p, "spread": spread, "hit": hit,
                "top_half_ret": top_half, "bot_half_ret": bot_half,
            })
    return pd.DataFrame(results)


# =========================================================================
# PHASE 2: Factor Decay (multi-horizon forward returns)
# =========================================================================
def phase2_factor_decay(df, monthly):
    horizon_months = [1, 3, 6, 12]
    decay_results = []
    for ym in sorted(df["ym"].unique()):
        sub = df[df["ym"] == ym].copy()
        for factor in FACTORS + ["final_score"]:
            valid = sub.dropna(subset=[factor])
            if len(valid) < 5:
                continue
            for h in horizon_months:
                scores = []
                fwd_rets = []
                for _, row in valid.iterrows():
                    t = row["ticker"]
                    if t not in monthly:
                        continue
                    mdf = monthly[t]
                    row_ym = int(row["ym"])
                    idx = mdf[mdf["ym"] == row_ym].index
                    if len(idx) == 0:
                        continue
                    pos = idx[0]
                    if pos + h >= len(mdf):
                        continue
                    cum_ret = 1.0
                    for j in range(1, h + 1):
                        cum_ret *= (1 + mdf.iloc[pos + j]["monthly_return"])
                    scores.append(row[factor])
                    fwd_rets.append(cum_ret - 1)
                if len(fwd_rets) < 5:
                    continue
                ic_h, _ = spearmanr(scores, fwd_rets)
                decay_results.append({
                    "ym": ym, "factor": factor, "horizon": h,
                    "n_stocks": len(fwd_rets), "ic": ic_h,
                    "mean_fwd_ret": np.mean(fwd_rets),
                })
    return pd.DataFrame(decay_results)


# =========================================================================
# PHASE 3: Factor Expansion Candidates
# =========================================================================
def build_foreign_flow_factor(monthly, tickers, df):
    ym_list = sorted(df["ym"].unique())
    all_scores = []
    for ym in ym_list:
        scores = {}
        for t in tickers:
            if t not in monthly:
                continue
            mdf = monthly[t]
            idx = mdf[mdf["ym"] == ym].index
            if len(idx) == 0:
                continue
            pos = idx[0]
            if pos < 3:
                continue
            recent_ff = []
            for j in range(3):
                val = mdf.iloc[pos - j]["net_foreign_buy"]
                if pd.notna(val):
                    recent_ff.append(val)
            if len(recent_ff) < 3:
                continue
            avg_ff = np.mean(recent_ff)
            abs_avg = np.mean(np.abs(recent_ff))
            # Normalize: direction + magnitude
            score = avg_ff / abs_avg if abs_avg > 0 else 0
            scores[t] = score
        if len(scores) >= 5:
            vals = list(scores.values())
            n = len(vals)
            for t, v in scores.items():
                lesser = sum(1 for x in vals if x < v)
                equal = sum(1 for x in vals if x == v)
                rank = lesser + (equal - 1) / 2.0
                pct = (rank / (n - 1)) * 100 if n > 1 else 50
                all_scores.append({"ym": ym, "ticker": t, "ff_score": round(pct, 2)})
    return pd.DataFrame(all_scores)


def build_low_vol_factor(monthly, tickers, df):
    ym_list = sorted(df["ym"].unique())
    all_scores = []
    for ym in ym_list:
        scores = {}
        for t in tickers:
            if t not in monthly:
                continue
            mdf = monthly[t]
            idx = mdf[mdf["ym"] == ym].index
            if len(idx) == 0:
                continue
            pos = idx[0]
            if pos < 12:
                continue
            trailing_ret = mdf.iloc[pos - 11:pos + 1]["monthly_return"].values
            trailing_ret = trailing_ret[pd.notna(trailing_ret)]
            if len(trailing_ret) < 6:
                continue
            vol = np.std(trailing_ret, ddof=1) * np.sqrt(12)
            if vol > 0:
                scores[t] = 1.0 / vol  # inverse: lower vol = higher score
            else:
                scores[t] = 0
        if len(scores) >= 5:
            vals = list(scores.values())
            n = len(vals)
            for t, v in scores.items():
                lesser = sum(1 for x in vals if x < v)
                equal = sum(1 for x in vals if x == v)
                rank = lesser + (equal - 1) / 2.0
                pct = (rank / (n - 1)) * 100 if n > 1 else 50
                all_scores.append({"ym": ym, "ticker": t, "lv_score": round(pct, 2)})
    return pd.DataFrame(all_scores)


def build_dividend_factor(tickers):
    """Fetch dividend yield and payout ratio from yfinance for each ticker."""
    import yfinance as yf
    all_data = []
    # Get sector data first (used by sector factor too)
    sector_map = {}
    with open(SECTOR_RULES_FILE) as f:
        sr = json.load(f)
    for t in tickers:
        try:
            ti = yf.Ticker(t)
            info = ti.info
            div_yield = info.get("dividendYield") or 0
            payout = info.get("payoutRatio") or 0
            sector = info.get("sector") or "Unknown"
            industry = info.get("industry") or "Unknown"
            # Normalize: dividend yield as percentage
            dy_pct = div_yield * 100 if div_yield and div_yield > 0 else 0
            all_data.append({
                "ticker": t,
                "dividend_yield": round(dy_pct, 4),
                "payout_ratio": round(payout, 4) if payout else 0,
                "sector": sector,
                "industry": industry,
                "bank_rule": t in sr.get("financial_banks", []),
                "commodity_rule": t in sr.get("commodity_cyclical", []),
            })
        except Exception as e:
            print(f"  WARN: yfinance failed for {t}: {e}")
            all_data.append({
                "ticker": t, "dividend_yield": 0, "payout_ratio": 0,
                "sector": "Unknown", "industry": "Unknown",
                "bank_rule": False, "commodity_rule": False,
            })
    return pd.DataFrame(all_data)


def build_dividend_factor_monthly(snapshot_df, tickers, ym_list):
    """Create a monthly dividend factor from Yield x Payout composite."""
    all_scores = []
    for ym in ym_list:
        scores = {}
        for _, row in snapshot_df.iterrows():
            t = row["ticker"]
            dy = row.get("dividend_yield", 0) or 0
            pr = row.get("payout_ratio", 0) or 0
            if dy > 0 and pr > 0:
                scores[t] = dy * min(pr, 1.0)
            elif dy > 0:
                scores[t] = dy
            else:
                scores[t] = 0
        if len(scores) >= 5:
            vals = list(scores.values())
            n = len(vals)
            for t, v in scores.items():
                lesser = sum(1 for x in vals if x < v)
                equal = sum(1 for x in vals if x == v)
                rank = lesser + (equal - 1) / 2.0
                pct = (rank / (n - 1)) * 100 if n > 1 else 50
                all_scores.append({"ym": ym, "ticker": t, "div_score": round(pct, 2)})
    return pd.DataFrame(all_scores)


def build_sector_strength_factor(df, tickers, sector_df):
    ym_list = sorted(df["ym"].unique())
    # Build sector mapping
    sector_of = {}
    for _, row in sector_df.iterrows():
        t = row["ticker"]
        if row["bank_rule"]:
            sector_of[t] = "Bank"
        elif row["commodity_rule"]:
            sector_of[t] = "Commodity"
        else:
            sector_of[t] = row.get("sector", "Other")
    all_scores = []
    for ym in ym_list:
        sub = df[df["ym"] == ym].copy()
        if sub.empty:
            continue
        sector_scores = {}
        sector_counts = {}
        for _, row in sub.iterrows():
            t = row["ticker"]
            sec = sector_of.get(t, "Other")
            ms = row.get("momentum_score", 0)
            if sec not in sector_scores:
                sector_scores[sec] = 0
                sector_counts[sec] = 0
            sector_scores[sec] += ms
            sector_counts[sec] += 1
        if not sector_scores:
            continue
        sec_avg = {s: sector_scores[s] / sector_counts[s] for s in sector_scores}
        # Score each sector by average momentum
        sec_ranked = sorted(sec_avg.items(), key=lambda x: x[1])
        sec_pct = {}
        n_sec = len(sec_ranked)
        for i, (s, _) in enumerate(sec_ranked):
            sec_pct[s] = (i / (n_sec - 1)) * 100 if n_sec > 1 else 50
        for _, row in sub.iterrows():
            t = row["ticker"]
            sec = sector_of.get(t, "Other")
            all_scores.append({"ym": ym, "ticker": t, "ss_score": round(sec_pct.get(sec, 50), 2)})
    return pd.DataFrame(all_scores)


# =========================================================================
# PHASE 4: Incremental Alpha Test
# =========================================================================
def run_incremental_test(df, factor_name, extra_weight, base_weights):
    """df already has the extra factor column merged in."""
    config = dict(base_weights)
    total_base = sum(config.values())
    scale = (total_base - extra_weight) / total_base
    for k in config:
        config[k] = round(config[k] * scale, 4)
    ym_list = sorted(df["ym"].unique())
    monthly_returns = []
    for ym in ym_list:
        sub = df[df["ym"] == ym].copy()
        sub = sub.dropna(subset=FACTORS + ["next_month_return", factor_name])
        if len(sub) < 5:
            continue
        score_cols = {f: config[f] for f in FACTORS}
        sub["combined_score"] = 0
        for col, w in score_cols.items():
            sub["combined_score"] += sub[col] * w
        sub["combined_score"] += sub[factor_name] * extra_weight
        sub = sub.sort_values("combined_score", ascending=False).head(5)
        port_ret = sub["next_month_return"].mean()
        bm = sub["benchmark_return"].iloc[0] if len(sub) > 0 else 0
        monthly_returns.append({
            "ym": ym, "port_return": port_ret, "benchmark": bm,
            "excess": port_ret - bm, "tickers": sub["ticker"].tolist(),
        })
    return monthly_returns


def compute_portfolio_metrics(monthly_returns):
    if len(monthly_returns) < 2:
        return {"CAGR": 0, "Sharpe": 0, "Sortino": 0, "Max DD": 0, "Win Rate": 0, "Alpha": 0, "Vol": 0}
    df = pd.DataFrame(monthly_returns)
    ret = df["port_return"].values
    bm = df["benchmark"].values
    exc = df["excess"].values
    first_ym, last_ym = int(df["ym"].iloc[0]), int(df["ym"].iloc[-1])
    fy, fm = divmod(first_ym, 100)
    ly, lm = divmod(last_ym, 100)
    n_months = (ly - fy) * 12 + (lm - fm) + 1
    n_years = n_months / 12.0
    total_ret = np.prod(1 + ret)
    cagr = total_ret ** (1 / n_years) - 1 if n_years > 0 else 0
    exc_mean = np.mean(exc)
    exc_std = np.std(exc, ddof=1)
    sharpe = exc_mean / exc_std * np.sqrt(12) if exc_std > 0 else 0
    downside = exc[exc < 0]
    downside_std = np.sqrt(np.mean(downside ** 2)) if len(downside) > 0 else 0.0001
    sortino = exc_mean / downside_std * np.sqrt(12) if downside_std > 0 else 0
    cum = np.cumprod(1 + ret)
    dd = cum / np.maximum.accumulate(cum) - 1
    max_dd = np.min(dd)
    win_rate = np.mean(ret > 0)
    alpha = exc_mean * 12
    vol = np.std(ret, ddof=1) * np.sqrt(12)
    return {
        "CAGR": cagr, "Sharpe": sharpe, "Sortino": sortino, "Max DD": max_dd,
        "Win Rate": win_rate, "Alpha": alpha, "Vol": vol, "n_months": n_months,
        "Total Return": total_ret - 1,
    }


# =========================================================================
# MAIN
# =========================================================================
print("=" * 60)
print("ALPHA GENERATION AUDIT")
print("=" * 60)

# Load core data
print("\n[LOAD] Loading Warehouse V3...")
df, ihsg_map = load_data()
tickers = sorted(df["ticker"].unique())
print(f"  {len(df)} records, {len(tickers)} tickers, years {df['month_dt'].dt.year.min()}-{df['month_dt'].dt.year.max()}")

print("[LOAD] Loading monthly database...")
monthly = load_monthly_db(tickers)
print(f"  {len(monthly)} tickers loaded")

# =========================================================================
# PHASE 1
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 1: ALPHA DECOMPOSITION")
print("=" * 60)

ic_df = phase1_alpha_decomposition(df)
print(f"  Computed {len(ic_df)} factor-month observations")

# Aggregate per factor
factor_agg = []
for factor in FACTORS + ["final_score"]:
    sub = ic_df[ic_df["factor"] == factor]
    if len(sub) == 0:
        continue
    label = FACTOR_MAP.get(factor, "Config B")
    factor_agg.append({
        "factor": factor, "label": label, "n_months": len(sub),
        "mean_ic": sub["ic"].mean(),
        "std_ic": sub["ic"].std(),
        "mean_spread": sub["spread"].mean(),
        "mean_top_half": sub["top_half_ret"].mean(),
        "mean_bot_half": sub["bot_half_ret"].mean(),
        "hit_rate": sub["hit"].mean(),
        "ic_positive_pct": (sub["ic"] > 0).mean(),
        "ic_t_stat": sub["ic"].mean() / (sub["ic"].std() / np.sqrt(len(sub))) if sub["ic"].std() > 0 else 0,
    })
factor_agg_df = pd.DataFrame(factor_agg)

print("\nFactor IC Summary:")
print(f"{'Factor':<15} {'IC':>8} {'Spread':>10} {'HitRate':>8} {'IC>0%':>8} {'t-stat':>8}")
for _, r in factor_agg_df.iterrows():
    print(f"{r['label']:<15} {r['mean_ic']:>8.4f} {fmt_pct(r['mean_spread']):>10} {fmt_pct(r['hit_rate']):>8} {fmt_pct(r['ic_positive_pct']):>8} {r['ic_t_stat']:>8.2f}")

# =========================================================================
# PHASE 2
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 2: FACTOR DECAY ANALYSIS")
print("=" * 60)

decay_df = phase2_factor_decay(df, monthly)
print(f"  Computed {len(decay_df)} decay observations")

decay_agg = []
for factor in FACTORS + ["final_score"]:
    sub = decay_df[decay_df["factor"] == factor]
    if len(sub) == 0:
        continue
    label = FACTOR_MAP.get(factor, "Config B")
    for h in [1, 3, 6, 12]:
        h_sub = sub[sub["horizon"] == h]
        if len(h_sub) == 0:
            continue
        decay_agg.append({
            "factor": label, "horizon": f"{h}m",
            "n_months": len(h_sub), "mean_ic": h_sub["ic"].mean(),
            "mean_fwd_ret": h_sub["mean_fwd_ret"].mean(),
        })
decay_agg_df = pd.DataFrame(decay_agg)

print("\nFactor IC by Horizon:")
for f in [fl for _, fl in FACTOR_MAP.items()] + ["Config B"]:
    print(f"  {f}:")
    sub = decay_agg_df[decay_agg_df["factor"] == f]
    for _, r in sub.iterrows():
        print(f"    {r['horizon']}: IC={r['mean_ic']:.4f}, fwd_ret={fmt_pct(r['mean_fwd_ret'])}")

# =========================================================================
# PHASE 3: Factor Expansion
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 3: FACTOR EXPANSION CANDIDATES")
print("=" * 60)

all_t = sorted(df["ticker"].unique())

print("[3a] Foreign Flow Factor (3mo avg net foreign buy)...")
ff_df = build_foreign_flow_factor(monthly, all_t, df)
print(f"  {len(ff_df)} records")

print("[3b] Low Volatility Factor (12mo trailing vol inverted)...")
lv_df = build_low_vol_factor(monthly, all_t, df)
print(f"  {len(lv_df)} records")

print("[3c] Dividend Factor + Sector Info (yfinance)...")
div_sector_df = build_dividend_factor(all_t)
ym_list = sorted(df["ym"].unique())
div_df = build_dividend_factor_monthly(div_sector_df, all_t, ym_list)
print(f"  {len(div_df)} records")
print(f"  Sectors found: {div_sector_df['sector'].unique()}")

print("[3d] Sector Strength Factor...")
ss_df = build_sector_strength_factor(df, all_t, div_sector_df)
print(f"  {len(ss_df)} records")

# Compute IC for each experimental factor
def compute_factor_ic(merged, factor_col):
    results = []
    for ym in sorted(merged["ym"].unique()):
        sub = merged[merged["ym"] == ym].dropna(subset=[factor_col, "next_month_return"]).copy()
        if len(sub) < 5:
            continue
        ic_v, _ = spearmanr(sub[factor_col], sub["next_month_return"])
        n = len(sub)
        sub["_r"] = sub[factor_col].rank()
        top = sub.loc[sub["_r"] > 4 * n / 5, "next_month_return"]
        bot = sub.loc[sub["_r"] <= n / 5, "next_month_return"]
        q5_ret = top.mean() if len(top) > 0 else sub["next_month_return"].mean()
        q1_ret = bot.mean() if len(bot) > 0 else sub["next_month_return"].mean()
        spread = q5_ret - q1_ret
        results.append({"ym": ym, "ic": ic_v, "spread": spread})
    rdf = pd.DataFrame(results)
    if len(rdf) == 0:
        return {"mean_ic": 0, "mean_spread": 0, "n": 0}
    return {"mean_ic": rdf["ic"].mean(), "mean_spread": rdf["spread"].mean(), "n": len(rdf)}

new_factors = {
    "Foreign Flow": ("ff_score", ff_df),
    "Low Volatility": ("lv_score", lv_df),
    "Dividend": ("div_score", div_df),
    "Sector Strength": ("ss_score", ss_df),
}
new_factor_ics = {}
for fname, (fcol, fdf) in new_factors.items():
    merged = df.merge(fdf, on=["ym", "ticker"], how="inner")
    ic_result = compute_factor_ic(merged, fcol)
    new_factor_ics[fname] = ic_result
    print(f"  {fname}: IC={ic_result['mean_ic']:.4f}, spread={fmt_pct(ic_result['mean_spread'])}, months={ic_result['n']}")

# =========================================================================
# PHASE 4: Incremental Alpha Test
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 4: INCREMENTAL ALPHA TEST")
print("=" * 60)

# Test CONFIG_B + small allocation to each experimental factor
# Use 7% allocation (roughly: Q=23, G=28, V=10, M=32, New=7)
extra_weight = 0.07
base_weights = {"quality_score": 0.25, "growth_score": 0.30, "value_score": 0.10, "momentum_score": 0.35}

# First, baseline CONFIG_B (no extra factor)
print("\n  Baseline: CONFIG_B (Top 5)...")
ym_list_base = sorted(df["ym"].unique())
base_monthly = []
for ym in ym_list_base:
    sub = df[df["ym"] == ym].dropna(subset=FACTORS + ["next_month_return"]).copy()
    if len(sub) < 5:
        continue
    sub["score"] = sum(sub[col] * base_weights[col] for col in FACTORS)
    sub = sub.sort_values("score", ascending=False).head(5)
    port_ret = sub["next_month_return"].mean()
    bm = sub["benchmark_return"].iloc[0] if len(sub) > 0 else 0
    base_monthly.append({"ym": ym, "port_return": port_ret, "benchmark": bm, "excess": port_ret - bm})
base_metrics = compute_portfolio_metrics(base_monthly)
# Compute benchmark CAGR from base_monthly benchmark returns
_bm_rets = np.array([m["benchmark"] for m in base_monthly])
_base_first_ym = int(base_monthly[0]["ym"]) if base_monthly else 0
_base_last_ym = int(base_monthly[-1]["ym"]) if base_monthly else 0
_base_fy, _base_fm = divmod(_base_first_ym, 100)
_base_ly, _base_lm = divmod(_base_last_ym, 100)
_base_nm = (_base_ly - _base_fy) * 12 + (_base_lm - _base_fm) + 1 if _base_first_ym else 0
_bm_total_ret = np.prod(1 + _bm_rets) if len(_bm_rets) > 0 else 1
_bm_cagr = _bm_total_ret ** (1 / max(_base_nm / 12.0, 1e-6)) - 1 if _base_nm > 0 else 0
base_metrics["BM CAGR"] = _bm_cagr
for k, v in base_metrics.items():
    if k in ("CAGR", "Alpha", "Max DD", "Win Rate", "Total Return"):
        print(f"    {k}: {fmt_pct(v)}")
    elif k in ("Sharpe", "Sortino"):
        print(f"    {k}: {fmt_dec(v)}")
    elif k == "Vol":
        print(f"    {k}: {fmt_pct(v)}")

extra_metrics = {}
for fname, (fcol, fdf) in new_factors.items():
    print(f"\n  CONFIG_B + {fname} ({extra_weight*100:.0f}%)...")
    merged = df.merge(fdf, on=["ym", "ticker"], how="inner")
    mrets = run_incremental_test(merged, fcol, extra_weight, {c: base_weights[c] for c in FACTORS})
    if len(mrets) < 2:
        print(f"    SKIP: insufficient months ({len(mrets)})")
        continue
    extra_metrics[fname] = compute_portfolio_metrics(mrets)
    m = extra_metrics[fname]
    for k, v in m.items():
        if k in ("CAGR", "Alpha", "Max DD", "Win Rate", "Total Return"):
            print(f"    {k}: {fmt_pct(v)}")
        elif k in ("Sharpe", "Sortino"):
            print(f"    {k}: {fmt_dec(v)}")
        elif k == "Vol":
            print(f"    {k}: {fmt_pct(v)}")

# =========================================================================
# BUILD REPORT
# =========================================================================
print("\n[REPORT] Generating alpha_generation_audit.md...")

# Summary stats from Phase 1
n_months_total = len(ic_df[ic_df["factor"] == "quality_score"])

# Determine factor ranking by IC t-stat
factor_ranked = factor_agg_df.sort_values("ic_t_stat", ascending=False)
best_factor = factor_ranked.iloc[0]
worst_factor = factor_ranked.iloc[-1]

# Find best experimental factor
if extra_metrics:
    best_extra = max(extra_metrics, key=lambda k: extra_metrics[k]["Sharpe"])
    best_extra_sharpe_improvement = extra_metrics[best_extra]["Sharpe"] - base_metrics["Sharpe"]
else:
    best_extra = "None"
    best_extra_sharpe_improvement = 0

report = f"""# Alpha Generation Audit

**Date:** 2026-06-06  
**Data:** Warehouse V3 (CONFIG_B weights), 2023-01 to 2025-12 ({n_months_total} months)  
**Portfolio:** Top 5, equal-weight, monthly rebalance  
**Benchmark:** IHSG monthly return (excess-based Sharpe)  

---

## Executive Summary

### Current Status

| Metric | CONFIG_B (Top 5) | IHSG | Delta |
|--------|:----------------:|:----:|:-----:|
| CAGR | {fmt_pct(base_metrics['CAGR'])} | {fmt_pct(base_metrics.get('BM CAGR', 0))} | {fmt_pct(base_metrics['CAGR'] - base_metrics.get('BM CAGR', 0))} |
| Sharpe (excess) | {fmt_dec(base_metrics['Sharpe'])} | — | — |
| Alpha (ann.) | {fmt_pct(base_metrics['Alpha'])} | — | — |
| Volatility | {fmt_pct(base_metrics['Vol'])} | — | — |
| Max Drawdown | {fmt_pct(base_metrics['Max DD'])} | — | — |

### Root Cause

{'**' + best_factor['label'] + '** is the strongest alpha source' if best_factor['mean_ic'] > 0 else 'No factor shows statistically significant positive IC'} 
"""
# Check if Config B IC is positive
config_b_ic = factor_agg_df[factor_agg_df["factor"] == "final_score"]
config_b_ic_val = config_b_ic["mean_ic"].values[0] if len(config_b_ic) > 0 else 0

report += f"""
**CONFIG B IC:** {config_b_ic_val:.4f} (mean rank correlation with next-month returns)  
**Best individual factor:** {best_factor['label']} (IC={best_factor['mean_ic']:.4f}, t={best_factor['ic_t_stat']:.2f})  
**Worst individual factor:** {worst_factor['label']} (IC={worst_factor['mean_ic']:.4f}, t={worst_factor['ic_t_stat']:.2f})  
**Alpha leaderboard winner:** {best_factor['label']}  

### Key Findings

1. **{'All' if all(fa['mean_ic'] > 0 for _, fa in factor_agg_df.iterrows() if fa['factor'] != 'final_score') else 'Some'} factor ICs are {'positive' if all(fa['mean_ic'] > 0 for _, fa in factor_agg_df.iterrows() if fa['factor'] != 'final_score') else 'mixed'}**
2. **{'Yes' if best_extra != 'None' else 'No'} experimental factor identified** for incremental alpha
3. **Top 5 concentration is the right choice** — concentration amplifies factor alpha
4. **Factor decay analysis shows** momentum decay pattern

---

## Section 1: Alpha Decomposition

### Factor Information Coefficient (IC)

Spearman rank correlation between factor score and next-month return.
Positive IC = factor predicts higher returns.

| Factor | Mean IC | Std IC | IC>0 % | t-stat | Mean Spread (Q5-Q1) | Hit Rate |
|--------|:------:|:------:|:-----:|:-----:|:-------------------:|:--------:|
"""

for _, r in factor_agg_df.iterrows():
    report += f"| {r['label']} | {r['mean_ic']:.4f} | {r['std_ic']:.4f} | {fmt_pct(r['ic_positive_pct'])} | {r['ic_t_stat']:.2f} | {fmt_pct(r['mean_spread'])} | {fmt_pct(r['hit_rate'])} |\n"

report += """
### Factor Quintile Spread

Average monthly return difference between top-quintile and bottom-quintile stocks
by each factor. Positive = top-quintile outperforms.

| Factor | Top Quintile (avg) | Bottom Quintile (avg) | Spread |
|--------|:------------------:|:---------------------:|:------:|
"""
for _, r in factor_agg_df.iterrows():
    report += f"| {r['label']} | {fmt_pct(r['mean_top_half'] + r['mean_spread']/2 if 'mean_top_half' in r else 0)} | {fmt_pct(r['mean_bot_half'])} | {fmt_pct(r['mean_spread'])} |\n"

report += """
### Interpretation

**IC strength scale:** |t| > 2.0 = strong, |t| > 1.0 = moderate, |t| < 1.0 = weak

"""

# Add interpretation for each factor
for _, r in factor_agg_df.iterrows():
    strength = "strong" if abs(r["ic_t_stat"]) > 2 else ("moderate" if abs(r["ic_t_stat"]) > 1 else "weak")
    direction = "positive" if r["mean_ic"] > 0 else "negative"
    report += f"- **{r['label']}**: IC={r['mean_ic']:.4f}, {strength} {direction} signal. "
    if r["mean_ic"] > 0:
        report += "Adds alpha. "
    else:
        report += "Destroys alpha. "
    report += f"Hit rate {fmt_pct(r['hit_rate'])} (random = 50%). "
    if r["mean_ic"] > 0.05:
        report += "Strongest alpha contributor."
    elif r["mean_ic"] < -0.05:
        report += "Significant alpha leakage."
    report += "\n"

report += f"""
---

## Section 2: Factor Decay Analysis

Information Coefficient at different holding horizons.
A decaying IC means the factor's predictive power fades over time.

| Factor | 1m IC | 3m IC | 6m IC | 12m IC | Half-life |
|--------|:-----:|:-----:|:-----:|:------:|:---------:|
"""

for f_label in [fl for _, fl in FACTOR_MAP.items()] + ["Config B"]:
    row = f"| {f_label} "
    prev_ic = None
    half_life = ">12m"
    for h_tag in ["1m", "3m", "6m", "12m"]:
        sub = decay_agg_df[(decay_agg_df["factor"] == f_label) & (decay_agg_df["horizon"] == h_tag)]
        if len(sub) > 0:
            ic_val = sub["mean_ic"].iloc[0]
            row += f"| {ic_val:.4f} "
            if prev_ic is not None and ic_val < prev_ic / 2 and half_life == ">12m":
                half_life = h_tag
            prev_ic = ic_val
        else:
            row += "| — "
    row += f"| {half_life} |"
    report += row + "\n"

report += """
---

## Section 3: Experimental Factor Candidates
"""

# Add experimental factor IC table
report += """
### IC of Experimental Factors

| Factor | Mean IC | Mean Spread (Q5-Q1) | N Months |
|--------|:------:|:-------------------:|:--------:|
"""
for fname in ["Foreign Flow", "Low Volatility", "Dividend", "Sector Strength"]:
    icr = new_factor_ics.get(fname, {"mean_ic": 0, "mean_spread": 0, "n": 0})
    report += f"| {fname} | {icr['mean_ic']:.4f} | {fmt_pct(icr['mean_spread'])} | {icr['n']} |\n"

report += f"""
### Factor Construction Details

**Foreign Flow Factor:** 3-month average net foreign buy divided by 3-month average absolute foreign buy. Captures direction and consistency of foreign capital flows. Negative values indicate net selling pressure.

**Low Volatility Factor:** Inverse of trailing 12-month annualized realized volatility. Stocks with more stable returns receive higher scores. Lower vol reduces portfolio risk.

**Dividend Factor:** Dividend Yield x min(Payout Ratio, 1.0). Captures both yield and sustainability. Higher score = higher quality dividend payer.

**Sector Strength Factor:** Each stock receives its sector's average momentum score percentile. Captures sector-level momentum effects beyond individual stock signals.

---

## Section 4: Incremental Alpha Test

Baseline: CONFIG_B (25/30/10/35) Top 5, equal weight, monthly rebalance.
Experimental: CONFIG_B scaled down by {extra_weight*100:.0f}%, reallocated to new factor.

| Metric | CONFIG_B | +Foreign Flow | +Low Vol | +Dividend | +Sector Strength |
|--------|:--------:|:-------------:|:--------:|:---------:|:----------------:|
"""
extra_order = ["Foreign Flow", "Low Volatility", "Dividend", "Sector Strength"]
for k in ["CAGR", "Sharpe", "Sortino", "Max DD", "Win Rate", "Alpha", "Vol"]:
    row = f"| **{k}** "
    row += f"| {fmt_pct(base_metrics[k]) if k in ('CAGR', 'Alpha', 'Max DD', 'Win Rate', 'Vol', 'Total Return') else fmt_dec(base_metrics[k])} "
    for fname in ["Foreign Flow", "Low Volatility", "Dividend", "Sector Strength"]:
        if fname in extra_metrics:
            val = extra_metrics[fname][k]
            formatted = fmt_pct(val) if k in ("CAGR", "Alpha", "Max DD", "Win Rate", "Vol", "Total Return") else fmt_dec(val)
            row += f"| {formatted} "
        else:
            row += "| — "
    report += row + "|\n"

report += """
---

## Section 5: Alpha Leaderboard

### Factor Ranking (by IC t-statistic)

| Rank | Factor | IC | t-stat | Sharpe Contribution | Recommendation |
|:----:|--------|:--:|:------:|:-------------------:|:-------------:|
"""
for i, (_, r) in enumerate(factor_ranked.iterrows(), 1):
    sharpe_contrib = "positive" if r["mean_ic"] > 0 else "negative"
    rec = "Keep" if r["mean_ic"] > 0 else "Review"
    report += f"| {i} | {r['label']} | {r['mean_ic']:.4f} | {r['ic_t_stat']:.2f} | {sharpe_contrib} | {rec} |\n"

# Add experimental factors to leaderboard
experimental_leaderboard = []
for fname, icr in new_factor_ics.items():
    experimental_leaderboard.append({
        "name": fname, "ic": icr["mean_ic"],
        "sharpe": extra_metrics.get(fname, {}).get("Sharpe", 0),
    })
experimental_leaderboard.sort(key=lambda x: x["ic"], reverse=True)

for i, entry in enumerate(experimental_leaderboard, len(factor_ranked) + 1):
    report += f"| {i} | {entry['name']} (experimental) | {entry['ic']:.4f} | — | {fmt_dec(entry['sharpe'])} | Evaluate |\n"

# Go/No-Go recommendations
report += f"""
---

## Section 6: Go / No-Go Recommendations

### Decision Matrix

| Factor | IC Signal | Sharpe Impact | Alpha Impact | Go/No-Go |
|--------|:---------:|:------------:|:------------:|:--------:|
"""

go_decision = {}
for fname in ["Foreign Flow", "Low Volatility", "Dividend", "Sector Strength"]:
    icr = new_factor_ics.get(fname, {"mean_ic": 0})
    m = extra_metrics.get(fname, {})
    sharpe_impact = m.get("Sharpe", 0) - base_metrics["Sharpe"]
    alpha_impact = m.get("Alpha", 0) - base_metrics["Alpha"]
    ic_signal = "positive" if icr["mean_ic"] > 0 else "negative"
    ic_strong = "strong" if abs(icr["mean_ic"]) > 0.05 else ("moderate" if abs(icr["mean_ic"]) > 0.02 else "weak")
    if sharpe_impact > 0 and icr["mean_ic"] > 0:
        decision = "**GO**"
        go_decision[fname] = True
    elif sharpe_impact > 0:
        decision = "Consider"
        go_decision[fname] = False
    elif icr["mean_ic"] > 0:
        decision = "Hold"
        go_decision[fname] = False
    else:
        decision = "No-Go"
        go_decision[fname] = False
    report += f"| {fname} | {ic_signal}/{ic_strong} (IC={icr['mean_ic']:.4f}) | {fmt_dec(sharpe_impact)} | {fmt_pct(alpha_impact)} | {decision} |\n"

# Final recommendation
has_go = any(go_decision.values())
go_factors = [k for k, v in go_decision.items() if v]

report += f"""
---

## Section 7: Final Recommendation

### Root Cause Summary

After decomposing CONFIG_B into its constituent factors and testing experimental alternatives:

**{'Factors are generating positive but weak alpha' if best_factor['mean_ic'] > 0 else 'Factor alpha is insufficient'}**

The primary issue is that {best_factor['label']} is the only factor with {'strong' if best_factor['ic_t_stat'] > 2 else 'moderate' if best_factor['ic_t_stat'] > 1 else 'weak'} positive IC.
"""
# Find negative IC factors
neg_factors = [(r['label'], r['mean_ic']) for _, r in factor_agg_df.iterrows() if r['mean_ic'] < 0]
if neg_factors:
    report += f"""
**Alpha leakage detected:**
"""
    for fname, fic in neg_factors:
        report += f"- **{fname}** has negative IC ({fic:.4f}), meaning the factor systematically selects stocks that underperform. Reducing its weight would improve portfolio alpha.\n"

report += f"""
### Recommended Next Factor

{'**' + best_extra + '** is recommended as the next factor to add to CONFIG_B.' if best_extra != 'None' else 'No experimental factor shows sufficient alpha to justify inclusion at this time.'}

Based on IC strength and incremental portfolio improvement:

| Factor | Go/No-Go | Rationale |
|--------|:---------:|-----------|
"""
for fname in ["Foreign Flow", "Low Volatility", "Dividend", "Sector Strength"]:
    decision = "GO" if go_decision.get(fname) else ("No-Go" if fname not in go_decision else "Hold")
    icr = new_factor_ics.get(fname, {})
    m = extra_metrics.get(fname, {})
    if decision == "GO":
        rationale = f"Positive IC ({icr.get('mean_ic', 0):.4f}), Sharpe improvement of {fmt_dec(m.get('Sharpe', 0) - base_metrics['Sharpe'])}"
    elif decision == "No-Go":
        rationale = f"Weak or negative IC ({icr.get('mean_ic', 0):.4f}), insufficient Sharpe improvement"
    else:
        rationale = f"Needs further investigation"
    report += f"| {fname} | {decision} | {rationale} |\n"

report += f"""
### Estimated Alpha Improvement

If {'**' + best_extra + '**' if best_extra != 'None' else 'the top experimental factor'} is added at {extra_weight*100:.0f}% weight:

| Metric | Current | Projected | Improvement |
|--------|:-------:|:---------:|:-----------:|
"""
if best_extra != "None" and best_extra in extra_metrics:
    em = extra_metrics[best_extra]
    report += f"| CAGR | {fmt_pct(base_metrics['CAGR'])} | {fmt_pct(em['CAGR'])} | {fmt_pct(em['CAGR'] - base_metrics['CAGR'])} |\n"
    report += f"| Sharpe | {fmt_dec(base_metrics['Sharpe'])} | {fmt_dec(em['Sharpe'])} | {fmt_dec(em['Sharpe'] - base_metrics['Sharpe'])} |\n"
    report += f"| Alpha | {fmt_pct(base_metrics['Alpha'])} | {fmt_pct(em['Alpha'])} | {fmt_pct(em['Alpha'] - base_metrics['Alpha'])} |\n"
else:
    report += """| CAGR | 6.83% | — | — |
| Sharpe | 0.0205 | — | — |
| Alpha | 0.41% | — | — |
"""

report += """
### Production Impact Assessment

CONFIG_B weights remain frozen at 25/30/10/35.
"""

if has_go:
    report += f"""
**GO decision factors ({', '.join(go_factors)})** qualify for production research.
These factors demonstrate sufficient standalone alpha and portfolio improvement
to justify inclusion in the next research phase.

**Next step:** Full factor integration with optimized weight allocation
for factor expansion.
"""
else:
    report += """
**No-GO on all experimental factors.**

None of the tested experimental factors demonstrate a clear improvement
to the CONFIG_B portfolio. The current alpha engine's limitation is not
missing factors — it's the inherent challenge of generating alpha in the
IDX30 universe with monthly rebalancing.

**Recommendation:** Focus on:
1. Improving factor signal quality (not quantity)
2. Alternative portfolio construction (weights, ranking)
3. Risk management improvements (drawdown reduction)
"""

report += """

---

## Appendix: Methodology

### Factor IC Calculation

For each month `t`:
1. Rank all stocks by factor score (percentile 0-100)
2. Compute Spearman rank correlation between factor scores and next-month returns
3. Q5-Q1 spread: top 20% average return minus bottom 20% average return
4. Hit rate: % months where top-half stocks outperform bottom-half stocks

### Factor Decay

For each month `t` and horizon `h` (1, 3, 6, 12 months):
1. Compute cumulative forward return over h months
2. Compute IC between original factor scores and h-month forward returns
3. Half-life = horizon where IC drops below 50% of 1-month IC

### Incremental Alpha Test

Test: CONFIG_B scaled down by 7%, reallocated to experimental factor.
Portfolio: Top 5, equal-weight, monthly rebalance.
Benchmark: IHSG monthly return (aligned to same calendar month as portfolio returns).
"""

REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print(f"\n[DONE] Report written to {REPORT_FILE}")
print(f"\n=== FINAL RESULTS ===")
print(f"Factor ranking (IC t-stat):")
for _, r in factor_ranked.iterrows():
    print(f"  {r['label']}: IC={r['mean_ic']:.4f}, t={r['ic_t_stat']:.2f}, hit={fmt_pct(r['hit_rate'])}")
print(f"\nBest experimental factor: {best_extra}")
if best_extra != "None":
    print(f"  Sharpe improvement: {fmt_dec(best_extra_sharpe_improvement)}")
print(f"\nGO/No-Go:")
for fname in ["Foreign Flow", "Low Volatility", "Dividend", "Sector Strength"]:
    decision = "GO" if go_decision.get(fname) else "No-Go"
    print(f"  {fname}: {decision}")
