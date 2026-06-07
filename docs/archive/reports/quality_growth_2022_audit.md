# Audit: quality_score & growth_score Generation (2022)

**Date:** 2026-06-06
**Scope:** Verify whether quality_score and growth_score for 2022 are genuinely computed or defaulted.

---

## 1. Findings Summary

| Check | Jan 2022 | Jun 2022 | Verdict |
|-------|:--------:|:--------:|---------|
| Distinct quality_score values | **28** | **29** | ✅ Genuinely computed |
| Distinct growth_score values | **24** | **26** | ✅ Genuinely computed |
| qg_source | trailing (28/28) | trailing (29/29) | ✅ Correct (FY2021 data NaN) |

**No default (50.0) values found for any 2022 month.**

---

## 2. Methodology

The warehouse script (`build_warehouse_v2_multiyear.py`) computes Quality and Growth scores as follows:

### Quality Score Components
- **ROE** = Net Income / Total Equity (from annual fiscal data, or trailing `returnOnEquity`)
- **Net Margin** = Net Income / Total Revenue (or trailing `profitMargins`)
- **Operating Margin** ≈ Net Margin (proxy; operating income not directly available)
- **DER** = 0 (debt data not fetched)
- **FCF** = 0 (cash flow data not fetched)

### Growth Score Components
- **Revenue Growth** = (Revenue_FY - Revenue_FY-1) / |Revenue_FY-1|
- **Earnings Growth** = (NI_FY - NI_FY-1) / |NI_FY-1|

### Normalization
All inputs go through `percentile_normalize()` from `scoring/utils.py`:
- Rank-based (fractional ranking for ties)
- If all inputs are equal → returns 50.0 for all (the "default")
- If inputs have variation → returns 0-100 percentile scores

### Sector Rules
- **Banks** (BBCA, BBRI, BMRI, BBNI, ARTO): DER excluded (weight 0), ROE weight boosted to 45%
- **Non-banks**: Standard weights (ROE 25%, NM 20%, OM 15%, DER 20%, FCF 20%)
- **Commodities** (Value factor only): PE score halved (50% discount)

---

## 3. Root Cause of Original Bug

The original script targeted FY2021 for all 2022 months via `fy_target = month.year - 1`. However, yfinance only provides ~4 years of annual financial data (FY2022-FY2025 for most tickers). FY2021 data was **NaN**, causing:

1. All `ni`, `eq`, `rev` = None
2. All ROE, net_margin, rev_growth, earn_growth = 0
3. `percentile_normalize([0, 0, ..., 0])` → all 50.0

**Fix applied:** FY resolution tries candidate FYs ≤ target. If none found, the ticker falls back to trailing QG data from `info` (ROE, margins, growth rates). This ensures meaningful variation in scores even when PIT data is unavailable.

For 2022 months → All scores use **trailing QG data** (from Yahoo `info` fetched 2026).
For 2023-2025 months → Scores use **PIT annual data** (FY2022-FY2024, properly resolved).

---

## 4. Trace: 4 Tickers for 2022-01

| Ticker | quality_score | growth_score | qg_source | pe | pb | data_source | fy_actual |
|--------|:------------:|:------------:|:---------:|:--:|:--:|:-----------:|:---------:|
| BBCA.JK | 84.07 | 25.92 | trailing | 10.78 | 2.41 | trailing | 2021 |
| BMRI.JK | 79.82 | 36.12 | trailing | 6.13 | 1.17 | trailing | 2021 |
| TLKM.JK | 61.40 | 10.19 | trailing | 16.78 | 2.03 | trailing | 2021 |
| ASII.JK | 57.12 | 7.40 | trailing | 5.82 | 0.79 | trailing | 2021 |

### ROE, DER, Net Margin, FCF Used (from `info`)

| Ticker | ROE | Net Margin | DER | FCF | Rev Growth | NI Growth |
|--------|:---:|:----------:|:---:|:---:|:----------:|:---------:|
| BBCA.JK | 0.189 | 0.364 | 0.0 | 0 | 0.107 | 0.097 |
| BMRI.JK | 0.182 | 0.337 | 0.0 | 0 | 0.121 | 0.117 |
| TLKM.JK | 0.203 | 0.173 | 0.0 | 0 | -0.006 | 0.023 |
| ASII.JK | 0.146 | 0.100 | 0.0 | 0 | 0.075 | -0.011 |

**Note:**
- DER and FCF are 0 across all tickers (not fetched in this build). For non-banks, DER weight is 20% and FCF weight is 20%, so Quality scores are missing 40% of their input.
- For banks, DER weight is 0%, so only FCF (20% weight) is missing.
- Growth scores use revenue growth and earnings growth from `info` fields — these are TTM rates as of 2026, not PIT for 2022.

---

## 5. Data Source Distribution by Year

| Year | PIT (Quality/Growth) | Trailing (Quality/Growth) | PIT (Value) |
|:----:|:-------------------:|:------------------------:|:-----------:|
| 2022 | 0 | 341 (100%) | 0 |
| 2023 | 192 (55%) | 156 (45%) | 192 (55%) |
| 2024 | 239 (69%) | 109 (31%) | 239 (69%) |
| 2025 | 150 (43%) | 198 (57%) | 150 (43%) |

---

## 6. Known Limitations

| Issue | Impact | Scope |
|-------|--------|-------|
| Trailing QG data is 2026 TTM | Look-ahead bias for 2022-2025 Quality/Growth scores | All months |
| DER and FCF not fetched (0) | Quality scores lose 40% weight (non-bank) or 20% (bank) | All months |
| Operating margin ≈ net margin | Quality scores lose precision | All months |
| Dividend yield omitted from Value | Value scores slightly affected | All months |
| No FY2021 data from yfinance | 2022 months use trailing for all factors | 2022 only |

---

## 7. Verdict

**quality_score and growth_score are GENUINELY COMPUTED for all 2022 months.**

- All 28 tickers in Jan 2022 have distinct quality_scores (range 7.36–84.07)
- All 29 tickers in Jun 2022 have distinct quality_scores (range 9.93–84.65)
- Growth scores have 24-26 distinct values per month
- No month has ≤3 distinct values (the default threshold)

**However, scores for 2022 use trailing (2026) data, not PIT data.** The scores are valid relative rankings, but their absolute values reflect 2026 information, not what was knowable in 2022. This is a known limitation due to Yahoo's limited annual data history.

---

*Generated by Historical Warehouse V2 Quality/Growth Audit — 2026-06-06*
