"""
Historical Warehouse V2 — Multi-Year Reconstruction (2022-2025)
PIT Value Factor with validated fallback for unreliable financial data.

Usage: python warehouse_historical/build_warehouse_v2_multiyear.py
"""

import json
import os
import sys
import warnings
from pathlib import Path

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scoring.utils import percentile_normalize

# ── Config ──────────────────────────────────────────────────────────
UNIVERSE_FILE = PROJECT_ROOT / "database" / "historical_universe" / "2024-01.json"
MONTHLY_DIR = PROJECT_ROOT / "database" / "monthly"
SECTOR_RULES_FILE = PROJECT_ROOT / "config" / "sector_rules.json"
WEIGHTS_FILE = PROJECT_ROOT / "config" / "scoring_weights.json"
OUTPUT_DIR = PROJECT_ROOT / "warehouse_historical"

START_YEAR, END_YEAR = 2022, 2025
PE_VALID_MIN, PE_VALID_MAX = 0.5, 200.0

# ── Helpers ─────────────────────────────────────────────────────────
def load_json(path):
    with open(path) as f:
        return json.load(f)

def load_monthly(ticker):
    fp = MONTHLY_DIR / f"{ticker}.csv"
    if not fp.exists():
        return None
    df = pd.read_csv(fp)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")
    return df

def get_pit_financial(ticker):
    """Fetch annual financial data and trailing info from yfinance.
    Returns dict with:
      - fiscal_data: {fy_year: {net_income, total_equity, total_revenue, shares}}
      - trailing: {pe, pb, eps}
      - valid: bool (whether annual data passes sanity check)
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info
        fs = t.financials
        bs = t.balance_sheet
    except Exception as e:
        print(f"  WARN: yfinance failed for {ticker}: {e}")
        return None

    if fs is None or bs is None:
        print(f"  WARN: No financials for {ticker}")
        return None

    shares_out = info.get("sharesOutstanding")
    trailing_pe = info.get("trailingPE") or 0
    trailing_pb = info.get("priceToBook") or 0
    trailing_eps = info.get("trailingEps") or 0

    # Trailing Quality/Growth fields for fallback
    trailing_roe = info.get("returnOnEquity") or 0
    trailing_net_margin = info.get("profitMargins") or 0
    trailing_op_margin = info.get("operatingMargins") or 0
    trailing_der = info.get("debtToEquity") or 0
    trailing_fcf = info.get("freeCashflow") or 0
    trailing_rev_growth = info.get("revenueGrowth") or 0
    trailing_earn_growth = info.get("earningsGrowth") or 0

    trailing_qg = {
        "roe": trailing_roe,
        "net_margin": trailing_net_margin,
        "op_margin": trailing_op_margin,
        "der": trailing_der,
        "fcf": trailing_fcf,
        "rev_growth": trailing_rev_growth,
        "earn_growth": trailing_earn_growth,
    }

    # Collect fiscal year data
    fiscal_data = {}
    for col_idx in range(len(fs.columns)):
        fy = fs.columns[col_idx]
        fy_year = fy.year

        net_income = None
        for label in ["Net Income", "Net Income Common Stockholders",
                       "Net Income From Continuing And Discontinued Operation"]:
            if label in fs.index:
                val = fs.loc[label].iloc[col_idx]
                if val == val and val is not None:  # not NaN
                    net_income = val
                    break

        total_revenue = None
        for label in ["Total Revenue", "Operating Revenue"]:
            if label in fs.index:
                val = fs.loc[label].iloc[col_idx]
                if val == val and val is not None:
                    total_revenue = val
                    break

        total_equity = None
        if bs is not None and col_idx < len(bs.columns):
            for label in ["Stockholders Equity", "Total Equity Gross Minority Interest",
                           "Common Stock Equity"]:
                if label in bs.index:
                    val = bs.loc[label].iloc[col_idx]
                    if val == val and val is not None:
                        total_equity = val
                        break

        shares = None
        if bs is not None and col_idx < len(bs.columns):
            if "Ordinary Shares Number" in bs.index:
                val = bs.loc["Ordinary Shares Number"].iloc[col_idx]
                if val == val and val is not None:
                    shares = val

        fiscal_data[fy_year] = {
            "net_income": net_income,
            "total_revenue": total_revenue,
            "total_equity": total_equity,
            "shares": shares or shares_out,
        }

    # Determine if annual data is reliable
    is_valid = True
    if "Diluted EPS" in fs.index and shares_out:
        for col_idx in range(min(3, len(fs.columns))):
            eps = fs.loc["Diluted EPS"].iloc[col_idx]
            if eps and eps == eps and eps > 0:
                implied_pe = 1000 / eps
                if implied_pe > 1000:
                    is_valid = False
                    break

    if not is_valid:
        print(f"  NOTE: {ticker} annual data unreliable (Diluted EPS too small)")

    # Build sorted list of available FY years (those with non-NaN NI)
    available_fy = sorted(
        [y for y, d in fiscal_data.items()
         if d["net_income"] is not None and d["net_income"] == d["net_income"]],
        reverse=True
    )

    return {
        "fiscal_data": fiscal_data,
        "trailing": {"pe": trailing_pe, "pb": trailing_pb, "eps": trailing_eps},
        "trailing_qg": trailing_qg,
        "valid": is_valid,
        "shares_out": shares_out,
        "available_fy": available_fy,
    }

def get_fy_for_month(month_date):
    """For a given month, return the most recent complete fiscal year."""
    return month_date.year - 1  # all have Dec 31 FY

# ── Main ─────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    weights = load_json(WEIGHTS_FILE)
    w_q = weights["quality"]
    w_g = weights["growth"]
    w_v = weights["value"]
    w_m = weights["momentum"]

    sector_rules = load_json(SECTOR_RULES_FILE)
    banks = set(sector_rules.get("financial_banks", []))
    commodities = set(sector_rules.get("commodity_cyclical", []))

    universe = [t for t in load_json(UNIVERSE_FILE) if t != "UNVR.JK"]

    # ── 1. Fetch financial data for all tickers ──────────────
    print("=" * 60)
    print("FETCHING FINANCIAL DATA")
    print("=" * 60)
    fin_data = {}
    for i, ticker in enumerate(universe, 1):
        print(f"[{i}/{len(universe)}] {ticker}...", end=" ")
        sys.stdout.flush()
        fd = get_pit_financial(ticker)
        fin_data[ticker] = fd
        if fd:
            status = "VALID" if fd["valid"] else "UNRELIABLE"
            print(f"{status}")
        else:
            print("FAILED")

    # ── 2. Generate all month-ticker combinations ────────────
    print("\n" + "=" * 60)
    print("BUILDING WAREHOUSE (2022-2025)")
    print("=" * 60)

    all_months = pd.date_range(f"{START_YEAR}-01-01", f"{END_YEAR}-12-01", freq="MS")

    records = []

    for month in all_months:
        month_prefix = month.strftime("%Y-%m")
        month_str = month.strftime("%Y-%m-%d")
        fy_target = get_fy_for_month(month)

        # Collect data for all tickers this month
        month_data = {}

        for ticker in universe:
            monthly_df = load_monthly(ticker)
            if monthly_df is None:
                continue
            # Find row matching this month (month-end dates like "2024-06-30")
            match = monthly_df[monthly_df.index.strftime("%Y-%m") == month_prefix]
            if match.empty:
                continue
            price = match.iloc[0]["month_end_price"]
            if pd.isna(price) or price <= 0:
                continue

            fd = fin_data.get(ticker)
            if fd is None:
                continue

            # ── Resolve FY data ─────────────────────────────────────
            # Find the nearest available FY at or before target
            fiscal = {}
            ni = None
            eq = None
            rev = None
            shares = fd.get("shares_out")
            fy_actual = fy_target
            fy_found = False

            if fd.get("available_fy"):
                for fy_candidate in sorted(fd["available_fy"], reverse=True):
                    if fy_candidate <= fy_target:
                        fiscal = fd["fiscal_data"].get(fy_candidate, {})
                        ni = fiscal.get("net_income")
                        eq = fiscal.get("total_equity")
                        rev = fiscal.get("total_revenue")
                        fy_actual = fy_candidate
                        if ni and ni == ni:
                            fy_found = True
                            break

            shares_src = fd.get("shares_out") or fiscal.get("shares")

            # ── PIT PE/PB ───────────────────────────────────────────
            pit_pe = None
            pit_pb = None
            data_source = "trailing"
            shares_src = fd.get("shares_out") or fiscal.get("shares")

            if fy_found and fd["valid"] and ni and shares_src and shares_src > 0 and ni == ni:
                eps = ni / shares_src
                pit_pe = price / eps if eps > 0 else 0
                if eq and eq == eq and eq > 0:
                    pit_pb = price / (eq / shares_src) if shares_src > 0 else 0
                if pit_pe and PE_VALID_MIN <= pit_pe <= PE_VALID_MAX:
                    pe_used = pit_pe
                    pb_used = pit_pb
                    data_source = "pit"
                else:
                    pe_used = fd["trailing"]["pe"]
                    pb_used = fd["trailing"]["pb"]
            else:
                pe_used = fd["trailing"]["pe"]
                pb_used = fd["trailing"]["pb"]

            month_data[ticker] = {
                "price": float(price),
                "pe": float(pe_used or 0),
                "pb": float(pb_used or 0),
                "data_source": data_source,
                "pit_pe": float(pit_pe or 0),
                "pit_pb": float(pit_pb or 0),
                "ni": ni if fy_found else None,
                "eq": eq if fy_found else None,
                "rev": rev if fy_found else None,
                "shares_src": shares_src,
                "fy_actual": fy_actual,
            }

        if not month_data:
            continue

        # ── 3. Compute Value scores ─────────────────────────
        tickers_list = list(month_data.keys())
        pe_vals = [month_data[t]["pe"] for t in tickers_list]
        pb_vals = [month_data[t]["pb"] for t in tickers_list]
        # Dividend yield omitted (not available in this build)
        div_vals = [0] * len(tickers_list)

        pe_scores_raw = percentile_normalize(pe_vals)
        pb_scores_raw = percentile_normalize(pb_vals)
        div_scores_raw = percentile_normalize(div_vals)

        # Invert: lower PE/PB → higher score
        pe_scores = [100 - s for s in pe_scores_raw]
        pb_scores = [100 - s for s in pb_scores_raw]

        value_scores = {}
        for i, t in enumerate(tickers_list):
            is_commodity = t in commodities
            final_pe = pe_scores[i] * (0.5 if is_commodity else 1.0)
            vs = final_pe * 0.40 + pb_scores[i] * 0.30 + div_scores_raw[i] * 0.30
            value_scores[t] = round(vs, 2)

        # ── 4. Compute Quality scores ───────────────────────
        roe_vals, nm_vals, om_vals, der_vals, fcf_vals = [], [], [], [], []
        qg_source_vals = []  # track source: "pit" or "trailing"
        tick_is_bank = [t in banks for t in tickers_list]

        for t in tickers_list:
            fd = fin_data.get(t)
            md = month_data.get(t, {})
            ni = md.get("ni")
            eq = md.get("eq")
            rev = md.get("rev")
            tqg = fd.get("trailing_qg", {}) if isinstance(fd, dict) else {}

            if ni and eq and eq > 0 and ni == ni and eq == eq and rev and rev > 0 and rev == rev:
                roe = ni / eq
                net_margin = ni / rev
                der = 0
                fcf = 0
                qg_source_vals.append("pit")
            elif tqg:
                roe = tqg.get("roe", 0)
                net_margin = tqg.get("net_margin", 0)
                der = tqg.get("der", 0)
                fcf = tqg.get("fcf", 0)
                qg_source_vals.append("trailing")
            else:
                roe, net_margin, der, fcf = 0, 0, 0, 0
                qg_source_vals.append("trailing")

            roe_vals.append(roe if isinstance(roe, (int, float)) else 0)
            nm_vals.append(net_margin if isinstance(net_margin, (int, float)) else 0)
            om_vals.append(net_margin if isinstance(net_margin, (int, float)) else 0)
            der_vals.append(der if isinstance(der, (int, float)) else 0)
            fcf_vals.append(fcf if isinstance(fcf, (int, float)) else 0)

        # Normalize
        roe_scores = percentile_normalize(roe_vals)
        nm_scores = percentile_normalize(nm_vals)
        om_scores = percentile_normalize(om_vals)
        fcf_scores = percentile_normalize(fcf_vals)

        # D/E only for non-bank
        der_non_bank = [der_vals[i] for i, b in enumerate(tick_is_bank) if not b]
        der_scores_non_bank = percentile_normalize(der_non_bank)
        der_score_map = {}
        nb_idx = 0
        for i, t in enumerate(tickers_list):
            if not tick_is_bank[i]:
                der_score_map[t] = der_scores_non_bank[nb_idx]
                nb_idx += 1
            else:
                der_score_map[t] = 0

        quality_scores = {}
        for i, t in enumerate(tickers_list):
            is_bank = tick_is_bank[i]
            if is_bank:
                w_roe, w_nm, w_om, w_der, w_fcf = 0.45, 0.20, 0.15, 0.0, 0.20
                debt_s = 0
            else:
                w_roe, w_nm, w_om, w_der, w_fcf = 0.25, 0.20, 0.15, 0.20, 0.20
                debt_s = 100 - der_score_map.get(t, 0)

            qs = (roe_scores[i] * w_roe + nm_scores[i] * w_nm +
                  om_scores[i] * w_om + debt_s * w_der + fcf_scores[i] * w_fcf)
            quality_scores[t] = round(qs, 2)

        # ── 5. Compute Growth scores ────────────────────────
        rev_growth_vals, earn_growth_vals = [], []
        for t in tickers_list:
            fd = fin_data.get(t)
            tqg = fd.get("trailing_qg", {}) if isinstance(fd, dict) else {}

            # Try PIT: use fiscal_data[fy_actual] vs fiscal_data[fy_actual-1]
            if fd and isinstance(fd, dict):
                fiscal_data = fd.get("fiscal_data", {})
                fy_actual = month_data.get(t, {}).get("fy_actual", fy_target)
                cur_f = fiscal_data.get(fy_actual, {}) if isinstance(fiscal_data, dict) else {}
                prv_f = fiscal_data.get(fy_actual - 1, {}) if isinstance(fiscal_data, dict) else {}
                cur_r = cur_f.get("total_revenue") if isinstance(cur_f, dict) else None
                prv_r = prv_f.get("total_revenue") if isinstance(prv_f, dict) else None
                cur_n = cur_f.get("net_income") if isinstance(cur_f, dict) else None
                prv_n = prv_f.get("net_income") if isinstance(prv_f, dict) else None

                rev_g = ((cur_r - prv_r) / abs(prv_r)
                        if (cur_r and prv_r and prv_r > 0
                            and cur_r == cur_r and prv_r == prv_r) else None)
                earn_g = ((cur_n - prv_n) / abs(prv_n)
                         if (cur_n and prv_n and prv_n > 0
                             and cur_n == cur_n and prv_n == prv_n) else None)
            else:
                rev_g, earn_g = None, None

            if rev_g is not None and earn_g is not None:
                rev_growth_vals.append(rev_g)
                earn_growth_vals.append(earn_g)
            elif tqg:
                rev_growth_vals.append(tqg.get("rev_growth", 0))
                earn_growth_vals.append(tqg.get("earn_growth", 0))
            else:
                rev_growth_vals.append(0)
                earn_growth_vals.append(0)

        rev_scores = percentile_normalize(rev_growth_vals)
        earn_scores = percentile_normalize(earn_growth_vals)

        growth_scores = {}
        for i, t in enumerate(tickers_list):
            gs = rev_scores[i] * 0.50 + earn_scores[i] * 0.50
            growth_scores[t] = round(gs, 2)

        # ── 6. Compute Momentum scores ──────────────────────
        rs_vals = []
        ret12_vals = []
        for t in tickers_list:
            monthly_df = load_monthly(t)
            if monthly_df is None:
                rs_vals.append(0)
                ret12_vals.append(0)
                continue
            try:
                match = monthly_df[monthly_df.index.strftime("%Y-%m") == month_prefix]
                if match.empty:
                    rs_vals.append(0)
                    ret12_vals.append(0)
                    continue
                idx = monthly_df.index.get_loc(match.index[0])
                if idx >= 6:
                    p0 = monthly_df.iloc[idx]["month_end_price"]
                    p6 = monthly_df.iloc[idx - 6]["month_end_price"]
                    rs = (p0 / p6 - 1) if p6 > 0 else 0
                else:
                    rs = 0
                if idx >= 12:
                    p12 = monthly_df.iloc[idx - 12]["month_end_price"]
                    ret12 = (p0 / p12 - 1) if p12 > 0 else 0
                else:
                    ret12 = 0
            except Exception:
                rs, ret12 = 0, 0
            rs_vals.append(rs)
            ret12_vals.append(ret12)

        rs_scores = percentile_normalize(rs_vals)
        ret12_scores = percentile_normalize(ret12_vals)

        momentum_scores = {}
        for i, t in enumerate(tickers_list):
            ms = rs_scores[i] * 0.50 + ret12_scores[i] * 0.50
            momentum_scores[t] = round(ms, 2)

        # ── 7. Compute Final scores ─────────────────────────
        for t in tickers_list:
            q = quality_scores.get(t, 0)
            g = growth_scores.get(t, 0)
            v = value_scores.get(t, 0)
            m = momentum_scores.get(t, 0)
            fs = q * w_q + g * w_g + v * w_v + m * w_m

            md = month_data[t]
            qg_src = qg_source_vals[tickers_list.index(t)] if t in tickers_list else "trailing"
            records.append({
                "ticker": t,
                "month": month_str,
                "price": md["price"],
                "pe": md["pe"],
                "pb": md["pb"],
                "data_source": md["data_source"],
                "pit_pe": md["pit_pe"],
                "pit_pb": md["pit_pb"],
                "quality_score": q,
                "growth_score": g,
                "value_score": v,
                "momentum_score": m,
                "final_score": round(fs, 2),
                "fy_used": fy_target,
                "fy_actual": md.get("fy_actual", fy_target),
                "qg_source": qg_src,
            })

        # Progress
        count_t = len(tickers_list)
        print(f"  {month_str}: {count_t} tickers processed")

    # ── 8. Save to CSV ──────────────────────────────────────
    if not records:
        print("No records generated!")
        return

    df = pd.DataFrame(records)
    df = df.sort_values(["month", "ticker"]).reset_index(drop=True)
    out_path = OUTPUT_DIR / "warehouse_v2_multiyear_pit.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")
    print(f"Total records: {len(df)}")
    print(f"Date range: {df['month'].min()} to {df['month'].max()}")
    print(f"Unique tickers: {df['ticker'].nunique()}")

    # ── Summary ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("DATA SOURCE SUMMARY")
    print("=" * 60)
    source_counts = df["data_source"].value_counts()
    for src, cnt in source_counts.items():
        print(f"  {src}: {cnt} ({cnt/len(df)*100:.1f}%)")

    pit_tickers = df[df["data_source"] == "pit"]["ticker"].unique()
    trail_tickers = df[df["data_source"] == "trailing"]["ticker"].unique()
    print(f"\nPIT tickers: {sorted(pit_tickers)}")
    print(f"Trailing tickers: {sorted(trail_tickers)}")

    # ── Monthly ticker coverage ─────────────────────────────
    print("\n" + "=" * 60)
    print("MONTHLY COVERAGE")
    print("=" * 60)
    monthly_counts = df.groupby("month")["ticker"].count()
    for m, c in monthly_counts.items():
        print(f"  {m}: {c} tickers")

if __name__ == "__main__":
    main()
