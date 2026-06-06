# Historical Warehouse V2 — Multi-Year Reconstruction (2022-2025)

**Date:** 2026-06-06
**Status:** COMPLETE
**File:** `warehouse_historical/warehouse_v2_multiyear_pit.csv`

---

## 1. Scope

| Dimension | Value |
|-----------|-------|
| Universe | 29 IDX30 tickers (excl. UNVR.JK — no monthly data) |
| Period | January 2022 – December 2025 (48 months) |
| Records | 1,389 ticker-months |
| Factors | Quality (25%), Growth (30%), Value (10%), Momentum (35%) |

## 2. Data Sources

| Source | Ticker-Months | % of Total |
|--------|:------------:|:----------:|
| **PIT** (annual FY financials) | 581 | 41.8% |
| **Trailing** (Yahoo info fields) | 808 | 58.2% |

### PIT-Capable Tickers (18)

These tickers have reliable annual financial data from Yahoo:

| Ticker | Sector | PE Range (PIT) | Data Quality |
|--------|--------|:--------------:|:------------:|
| AKRA.JK | Commodity | 7.1 – 11.1 | Good |
| AMRT.JK | Consumer | 23.5 – 41.6 | Good |
| ANTM.JK | Mining | 8.7 – 20.8 | Good |
| ARTO.JK | Bank | 158 – 200 | *Borderline (low earnings)* |
| ASII.JK | Consumer | 4.4 – 7.5 | Good |
| BBCA.JK | Bank | 16.3 – 25.5 | Good |
| BBRI.JK | Bank | 7.2 – 13.2 | Good |
| BMRI.JK | Bank | 6.3 – 10.7 | Good |
| BUKA.JK | Tech | 9.7 – 13.5 | Good |
| CPIN.JK | Consumer | 18.1 – 36.3 | Good |
| EMTK.JK | Consumer | 5.2 – 52.0 | Moderate |
| INDF.JK | Consumer | 5.9 – 9.3 | Good |
| KLBF.JK | Consumer | 14.7 – 27.6 | Good |
| PTBA.JK | Commodity | 1.5 – 5.8 | Good |
| SMGR.JK | Cement | 9.7 – 26.8 | Good |
| TLKM.JK | Telecom | 9.6 – 17.0 | Good |
| TOWR.JK | Telecom | 8.5 – 17.4 | Good |
| UNTR.JK | Commodity | 2.6 – 5.1 | Good |

### Trailing-Only Tickers (11)

Yahoo annual financial data is **unreliable** for these tickers (Indonesian GAAP label mismatch):

| Ticker | Reason |
|--------|--------|
| ADRO.JK | Net Income scale error (shows 1.38B instead of ~18T IDR) |
| BBNI.JK | PIT PE = 0.11 (outside valid range 0.5-200) |
| BRPT.JK | Net Income scale error |
| ESSA.JK | Net Income scale error |
| GOTO.JK | No positive earnings (PE = 0) |
| HRUM.JK | Net Income scale error |
| INCO.JK | Net Income scale error |
| ITMG.JK | Net Income scale error |
| MDKA.JK | No positive earnings (PE = 0) |
| MEDC.JK | Net Income scale error |
| PGAS.JK | Net Income scale error |

## 3. Key Findings

### 3.1 PIT vs Trailing Comparison (2024-06)

Comparing the 18 PIT-capable tickers in June 2024:

| Metric | Value |
|--------|-------|
| Mean Value Score change (PIT - Trailing) | +0.74 points |
| Std Dev Value Score change | 14.29 points |
| Max Value Score change | +34.28 (EMTK) |
| Min Value Score change | -39.29 (TOWR) |
| Mean Final Score change | +0.07 points |
| Max Final Score change | +3.43 (EMTK) |
| Max rank change | 4 positions (TLMK +4, TOWR -4) |

### 3.2 Ranking Stability

| Shift | Tickers | % |
|:-----:|:-------:|:-:|
| No change | 16 | 55% |
| 1-3 ranks | 11 | 38% |
| >3 ranks | 2 | 7% |

### 3.3 Monthly Winners

| Year | Dominant Tickers |
|:----:|-----------------|
| 2022 | Commodity boom: ITMG, ESSA, ADRO, HRUM |
| 2023 | Bank recovery: BMRI, BBRI, PTBA, MEDC |
| 2024 | Bank dominance: BMRI, BBCA |
| 2025 | Consumer turnaround: ANTM, EMTK |

## 4. Scoring Weights

| Factor | Weight |
|--------|:------:|
| Quality | 0.25 |
| Growth | 0.30 |
| Value | 0.10 |
| Momentum | 0.35 |

### Sector Rules Applied

- **Banks** (BBCA, BBRI, BMRI, BBNI, ARTO): DER excluded, ROE weight boosted to 45%
- **Commodities** (ADRO, PTBA, ITMG, HRUM, UNTR, MEDC, PGAS, AKRA, ESSA): PE score halved (50% discount) via commodity trap rule

## 5. Data Quality Notes

1. **Label mismatch for ~10 commodity tickers**: Yahoo's annual Net Income is off by 6,000-180,000x for ADRO, BRPT, ESSA, HRUM, INCO, ITMG, MEDC, PGAS. The root cause is Yahoo's parser not correctly mapping Indonesian GAAP financial statement line items.

2. **PIT vs trailing PE direction unpredictable**: For tickers where both are available, the difference direction depends on earnings trajectory. Growing companies (BBCA) show trailing PE < PIT PE (trailing understates). Declining companies (TLKM) show trailing PE > PIT PE (trailing overstates).

3. **Dividend yield not included**: Value factor uses 40% PE + 30% PB + 30% dividend_yield, but dividend data was not available in this build. The dividend component is omitted (treated as 0), which slightly reduces Value factor accuracy.

4. **Quality/Growth from PIT annual data**: Growth scores use YoY changes from annual financial data (more PIT accurate than trailing). Quality uses ROE and net margins from annual data, but operating margin is approximated.

## 6. Limitations

| Limitation | Impact |
|------------|--------|
| 11 tickers use trailing PE/PB (2026 TTM data) | Look-ahead bias for those tickers' Value factor |
| Dividend yield omitted from Value | Slightly less accurate Value scores |
| Quality operating margin ≈ net margin (proxy) | Minor impact on Quality ranking |
| All FY use Dec 31 year-end (generalization) | Minor timing mismatch for non-Dec FY companies |
| `info.sharesOutstanding` is current (2026), not PIT | Minor drift from buybacks/splits |

## 7. Output

**File:** `warehouse_historical/warehouse_v2_multiyear_pit.csv`

**Columns:**

| Column | Description |
|--------|-------------|
| ticker | Stock ticker |
| month | Month (YYYY-MM-DD, first of month) |
| price | Month-end price (IDR) |
| pe | PE ratio used (PIT or trailing) |
| pb | PB ratio used (PIT or trailing) |
| data_source | "pit" or "trailing" |
| pit_pe | PIT PE (raw, before validation) |
| pit_pb | PIT PB (raw, before validation) |
| quality_score | 0-100 percentile normalized |
| growth_score | 0-100 percentile normalized |
| value_score | 0-100 (PE: 40%, PB: 30%, Div: 30%) |
| momentum_score | 0-100 (RS-6M: 50%, Ret-12M: 50%) |
| final_score | Weighted composite (Q:25%, G:30%, V:10%, M:35%) |
| fy_used | Fiscal year used for PIT calculation |

---

*Generated by Historical Warehouse V2.1 Multi-Year Reconstruction — 2026-06-06*
