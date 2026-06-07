# Fundamental Data Audit

**Date:** 2026-06-07  
**Universe:** IDX30 (30 tickers)  
**Source Pipeline:** Yahoo Finance → collectors/fundamentals.py → output/raw/fundamentals.json  
**Growth Source:** collectors/growth.py → output/raw/growth.json

---

## Metric Availability

| Metric | Available? | Source Column | Coverage | Notes |
|--------|-----------|--------------|----------|-------|
| **ROE** | Y | `roe` (raw) / `ROE` (warehouse) | 30/30 (100%) | Direct from Yahoo Finance `returnOnEquity` |
| **ROA** | **N** | — | 0/30 (0%) | **Not collected by any pipeline step** |
| **PER** | Y | `pe_ratio` (raw) / `PE` (warehouse) | 27/30 (90%) | 3 null (negative earnings: EXCL, GOTO, MDKA) |
| **PBV** | Y | `pb_ratio` (raw) / `PB` (warehouse) | 30/30 (100%) | Direct from Yahoo Finance `priceToBook` |
| **EPS Growth** | Y | `earnings_growth` (raw) / `Net Income Growth` (warehouse) | 25/30 (83%) | 5 null (no growth data from Yahoo) |
| **Revenue Growth** | Y | `revenue_growth` (raw) / `Revenue Growth` (warehouse) | 30/30 (100%) | 100% coverage |
| **Dividend Yield** | Y | `dividend_yield` (raw) | 26/30 (87%) | 4 null (non-dividend stocks) |
| **DER** | Y | `debt_to_equity` (raw) / `DER` (warehouse) | 26/30 (87%) | 4 null — all are **banks** (BBCA, BMRI, BBRI, BBNI). Banks carry deposits as liabilities so DER is meaningless for them. |
| **Market Cap** | **N** | — | 0/30 (0%) | **Not collected** (prices.py only fetches close + volume) |

---

## BMRI — Actual Values Found

| Source | File | Value |
|--------|------|-------|
| Raw fundamentals | `output/raw/fundamentals.json` | `roe: 0.2104`, `pe_ratio: 6.76`, `pb_ratio: 1.25`, `debt_to_equity: None`, `dividend_yield: 11.69` |
| Raw growth | `output/raw/growth.json` | `revenue_growth: 0.015`, `earnings_growth: 0.167` |
| Warehouse snapshot | `warehouse/monthly_snapshots/2026-06.csv` | Same values + scores: `quality: 77.59`, `growth: 45.69`, `value: 83.45`, `momentum: 52.06`, `final: 59.67` |

All values match between raw files and warehouse.

---

## Why ROA Shows "Tidak tersedia"

**Root cause:** The Yahoo Finance data provider (`utils/data_provider.py`) defines a `yf_metric_map` dictionary that maps internal metric names to Yahoo Finance API fields. **`returnOnAssets` was never added to this map.**

The map currently has 10 entries:

```
pe_ratio        → trailingPE
roe             → returnOnEquity
debt_to_equity  → debtToEquity
pb_ratio        → priceToBook
dividend_yield  → dividendYield
net_margin      → profitMargins
operating_margin→ operatingMargins
free_cash_flow  → freeCashflow
revenue_growth  → revenueGrowth
earnings_growth → earningsGrowth
```

`returnOnAssets` is missing. Yahoo Finance does provide this field for most stocks.

## Pipeline Changes Required for ROA

Do **not** implement yet. Changes needed when ready:

### 1. `utils/data_provider.py`
Add to `yf_metric_map`:
```python
"roa": "returnOnAssets",
```

### 2. `collectors/fundamentals.py`
Add to `process_single_ticker`:
```python
"roa": provider.get_fundamental_metric(ticker, "roa"),
```

### 3. `output/raw/fundamentals.json`
Will automatically include `"roa"` after next collector run.

### 4. `generate_dashboard_v2.py`
- No JS changes needed — `renderFundamentals` already calls `fmt('ROA', fd.roa, '%')` which will pick up the field once present
- Pipeline already passes the full `fundamentals` dict to the frontend

### 5. `scoring/quality_score.py` (optional)
If ROA should affect quality scoring, add percentile normalization for ROA alongside ROE.

---

## Pipeline Changes Required for Market Cap

Market cap is available via `yfinance.Ticker.info['marketCap']`, not through the current `get_fundamental_metric` pattern (which uses `info.get(field)`). Would need:

### Option A — Add to `yf_metric_map`
Yahoo Finance field name: `marketCap`. This should work through the existing `info.get()` pattern in `data_provider.py`.

### Option B — Add to `collectors/prices.py`
Currently only fetches `history()`. Could also fetch `stock.info.get('marketCap')`.

---

## Dashboard — Current State Integration

The dashboard already displays all available metrics through `renderFundamentals()`:

- **Working (with live data):** ROE, PER, PBV, DER, Dividend Yield, Revenue Growth, EPS Growth
- **Shows "Tidak tersedia":** ROA (not yet collected), Market Cap (not yet collected)

The `fmt()` helper function correctly handles `null`/`undefined` → "Tidak tersedia" per specification.

---

## Recommendations

1. **ROA** — Low effort (4 lines across 2 files). Yahoo Finance provides `returnOnAssets` for most IDX30 stocks. Expected coverage: ~90%.
2. **Market Cap** — Low effort. Add `marketCap` to `yf_metric_map`. Coverage: 100%.
3. **DER for banks** — Currently null for all 4 banks (BBCA, BMRI, BBRI, BBNI). This is correct behavior (DER is not meaningful for banks), but the interpretation label "Tidak tersedia" could be misleading. Consider setting DER to a special sentinel or displaying "N/A" for banks.
4. **ROA for banks** — ROA is a standard metric for banks and would be more useful than DER for bank analysis.
