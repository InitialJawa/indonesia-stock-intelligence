# warehouse/archive_forward.py
"""Archive forward-looking factor data for the monthly pipeline.

This module is executed immediately after `scoring.final_score_v3`.
It collects raw inputs, factor scores, ranks, computes optional return
metrics, adds required metadata, and writes CSV snapshots to the
warehouse.
"""

import os
import json
import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration (adjusted per user request)
# ---------------------------------------------------------------------------
SOURCE = "YahooFinance"
WEIGHT_CONFIGURATION = "standard_weights_v1"  # explicit config identifier
FACTOR_FORMULA_VERSION = "v3"  # matches scoring.final_score_v3

# Project root (repository root)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Paths to source data (relative to project root)
RAW_FUNDERMENTS = PROJECT_ROOT / "output" / "raw" / "fundamentals.json"
RAW_GROWTH = PROJECT_ROOT / "output" / "raw" / "growth.json"
RAW_PRICES = PROJECT_ROOT / "output" / "raw" / "prices.json"

QUALITY_RANK = PROJECT_ROOT / "output" / "scores" / "quality_ranking.json"
GROWTH_RANK = PROJECT_ROOT / "output" / "scores" / "growth_ranking.json"
VALUE_RANK = PROJECT_ROOT / "output" / "scores" / "value_ranking.json"
MOMENTUM_RANK = PROJECT_ROOT / "output" / "scores" / "momentum_ranking.json"
FINAL_RANK = PROJECT_ROOT / "output" / "scores" / "final_ranking_v3.json"

# Destination directories
WAREHOUSE_ROOT = PROJECT_ROOT / "warehouse"
RAW_INPUTS_DIR = WAREHOUSE_ROOT / "raw_inputs"
MONTHLY_SNAP_DIR = WAREHOUSE_ROOT / "monthly_snapshots"
UNIVERSE_DIR = WAREHOUSE_ROOT / "universe"

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def setup_logging() -> logging.Logger:
    log_path = WAREHOUSE_ROOT / "archive_forward.log"
    logger = logging.getLogger("archive_forward")
    logger.setLevel(logging.INFO)
    # Ensure the directory for the log file exists
    os.makedirs(log_path.parent, exist_ok=True)
    handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_get(mapping: Dict, key: str, default: Any = None) -> Any:
    return mapping.get(key, default)


def compute_return(prices: Dict[str, Dict[str, float]], ticker: str, months: int) -> Optional[float]:
    """Compute simple price return over *months* months.

    `prices` is expected to be a dict of ticker -> {date_str: price}.
    Dates are ISO strings (YYYY-MM-DD). The function picks the most recent
    price and the price *months* ago. If the older price is missing, returns
    None.
    """
    ticker_data = prices.get(ticker)
    if not ticker_data:
        return None
    # Convert to DataFrame for easy sorting
    df = pd.Series(ticker_data).sort_index()
    if df.empty:
        return None
    latest_date = df.index[-1]
    latest_price = df.iloc[-1]
    # Compute target date by subtracting months (approx 30 days per month)
    try:
        latest_dt = datetime.datetime.strptime(latest_date, "%Y-%m-%d")
    except ValueError:
        return None
    target_dt = latest_dt - datetime.timedelta(days=30 * months)
    # Find the closest earlier date
    older_prices = df[df.index <= target_dt.strftime("%Y-%m-%d")]
    if older_prices.empty:
        return None
    older_price = older_prices.iloc[-1]
    try:
        return (latest_price / older_price) - 1.0
    except Exception:
        return None


def main() -> None:
    logger = setup_logging()
    collection_date = datetime.datetime.utcnow().isoformat()
    month_label = datetime.datetime.utcnow().strftime("%Y-%m")

    # Ensure destination directories exist
    for d in [RAW_INPUTS_DIR, MONTHLY_SNAP_DIR, UNIVERSE_DIR]:
        os.makedirs(d, exist_ok=True)

    try:
        fundamentals = load_json(RAW_FUNDERMENTS)
        growth = load_json(RAW_GROWTH)
        prices = load_json(RAW_PRICES)
        quality = load_json(QUALITY_RANK)
        growth_r = load_json(GROWTH_RANK)
        value = load_json(VALUE_RANK)
        momentum = load_json(MOMENTUM_RANK)
        final = load_json(FINAL_RANK)
        # Normalize ranking structures: they may be lists of dicts
        def normalize_ranking(data: Any) -> Dict[str, Dict]:
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {entry.get("ticker"): entry for entry in data if isinstance(entry, dict)}
            return {}
        quality = normalize_ranking(quality)
        growth_r = normalize_ranking(growth_r)
        value = normalize_ranking(value)
        momentum = normalize_ranking(momentum)
        final = normalize_ranking(final)
    except Exception as e:
        logger.error(f"Failed to load source JSON files: {e}")
        # Continue with whatever could be loaded – downstream will handle missing keys
        fundamentals = fundamentals if 'fundamentals' in locals() else {}
        growth = growth if 'growth' in locals() else {}
        prices = prices if 'prices' in locals() else {}
        quality = quality if 'quality' in locals() else {}
        growth_r = growth_r if 'growth_r' in locals() else {}
        value = value if 'value' in locals() else {}
        momentum = momentum if 'momentum' in locals() else {}
        final = final if 'final' in locals() else {}

    # -------------------------------------------------------------------
    # Build the snapshot rows
    # -------------------------------------------------------------------
    rows: List[Dict[str, Any]] = []
    for ticker in set(list(quality.keys()) + list(growth_r.keys()) + list(value.keys()) + list(momentum.keys()) + list(final.keys())):
        row: Dict[str, Any] = {"ticker": ticker}
        
        # Extract Scores
        row["quality_score"] = safe_get(quality.get(ticker, {}), "quality_score")
        row["growth_score"] = safe_get(growth_r.get(ticker, {}), "growth_score")
        row["value_score"] = safe_get(value.get(ticker, {}), "value_score")
        row["momentum_score"] = safe_get(momentum.get(ticker, {}), "momentum")
        row["final_score"] = safe_get(final.get(ticker, {}), "final_score")

        # Raw inputs – map to expected field names
        fund = fundamentals.get(ticker, {})
        row["ROE"] = safe_get(fund, "roe")
        row["DER"] = safe_get(fund, "der")
        row["Net Margin"] = safe_get(fund, "net_margin")
        row["Operating Margin"] = safe_get(fund, "operating_margin")
        row["FCF"] = safe_get(fund, "free_cash_flow")
        row["PE"] = safe_get(fund, "pe_ratio")
        row["PB"] = safe_get(fund, "pb_ratio")
        grow = growth.get(ticker, {})
        row["Revenue Growth"] = safe_get(grow, "revenue_growth")
        row["Net Income Growth"] = safe_get(grow, "earnings_growth")

        # Return metrics
        row["RS_6M"] = compute_return(prices, ticker, 6)
        row["Return_12M"] = compute_return(prices, ticker, 12)

        # Metadata
        row["collection_date"] = collection_date
        row["source"] = SOURCE
        row["weight_configuration"] = WEIGHT_CONFIGURATION
        row["universe_version"] = f"IDX30_{datetime.datetime.utcnow().strftime('%Y_%m')}"
        row["factor_formula_version"] = FACTOR_FORMULA_VERSION

        rows.append(row)

    # Compute Ranks
    snap_df = pd.DataFrame(rows)
    for col in ["quality_score", "growth_score", "value_score", "momentum_score", "final_score"]:
        if col in snap_df.columns:
            snap_df[col.replace("_score", "_rank")] = snap_df[col].rank(ascending=False)

    # -------------------------------------------------------------------
    # Write monthly snapshot CSV
    # -------------------------------------------------------------------
    try:
        snapshot_path = MONTHLY_SNAP_DIR / f"{month_label}.csv"
        snap_df.to_csv(snapshot_path, index=False)
        logger.info(f"Monthly snapshot written to {snapshot_path}")
    except Exception as e:
        logger.error(f"Failed to write monthly snapshot: {e}")

    # -------------------------------------------------------------------
    # Write universe CSV (ticker, sector, listing_date, collection_date, universe_version)
    # -------------------------------------------------------------------
    try:
        universe_rows: List[Dict[str, Any]] = []
        for ticker, fund in fundamentals.items():
            uni_row = {
                "ticker": ticker,
                "sector": safe_get(fund, "sector"),
                "listing_date": safe_get(fund, "listing_date"),
                "collection_date": collection_date,
                "universe_version": f"IDX30_{datetime.datetime.utcnow().strftime('%Y_%m')}",
            }
            universe_rows.append(uni_row)
        uni_df = pd.DataFrame(universe_rows)
        uni_path = UNIVERSE_DIR / f"{month_label}.csv"
        uni_df.to_csv(uni_path, index=False)
        logger.info(f"Universe snapshot written to {uni_path}")
    except Exception as e:
        logger.error(f"Failed to write universe snapshot: {e}")

    # -------------------------------------------------------------------
    # Archive raw input copies for reference
    # -------------------------------------------------------------------
    try:
        raw_copy_path = RAW_INPUTS_DIR / f"{month_label}.json"
        with open(raw_copy_path, "w", encoding="utf-8") as f:
            json.dump({"fundamentals": fundamentals, "growth": growth, "prices": prices}, f, ensure_ascii=False, indent=2)
        logger.info(f"Raw inputs archived to {raw_copy_path}")
    except Exception as e:
        logger.error(f"Failed to archive raw inputs: {e}")


if __name__ == "__main__":
    main()
