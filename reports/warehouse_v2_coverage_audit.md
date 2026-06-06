# Warehouse V2 Coverage Audit

**Date:** 2026-06-06  
**Source:** `warehouse_historical/warehouse_v2_multiyear_pit.csv` (1,389 ticker-months, 29 tickers, 48 months)

---

## Coverage Summary

| Year | Total | PIT | Trailing | PIT% | Trail% | Missing% | Value LA% | QG LA% |
|------|------:|----:|---------:|:----:|:------:|:--------:|:---------:|:------:|
| 2022 | 345 | 0 | 345 | 0.0% | 100.0% | 0.0% | 100.0% | 100.0% |
| 2023 | 348 | 204 | 144 | 58.6% | 41.4% | 0.0% | 41.4% | 0.0% |
| 2024 | 348 | 180 | 168 | 51.7% | 48.3% | 0.0% | 48.3% | 0.0% |
| 2025 | 348 | 197 | 151 | 56.6% | 43.4% | 0.0% | 43.4% | 0.0% |

**Overall PIT coverage:** 581/1389 = 41.8%  
**Overall trailing coverage:** 58.2%  
**Missing factors:** 0.0% across all years

---

## Year-by-Year Verdict

| Year | Verdict |
|------|---------|
| 2022 | **FAIL** — 100% trailing data. FY2021 unavailable from yfinance. All Quality, Growth, and Value scores use 2026 TTM data. Not suitable for factor-weight optimization. |
| 2023 | **MARGINAL** — Value: 58.6% PIT, 41.4% trailing (commodity tickers). Quality/Growth: 100% PIT. PIT valid for banks/consumer; commodity/mining trailing. |
| 2024 | **MARGINAL** — Value: 51.7% PIT, 48.3% trailing (commodity tickers). Quality/Growth: 100% PIT. Highest value trailing exposure. |
| 2025 | **MARGINAL** — Value: 56.6% PIT, 43.4% trailing. Quality/Growth: 100% PIT. Improvement trend over 2024. |

---

## Look-Ahead Bias Analysis

### Key Finding: Quality/Growth vs Value have DIFFERENT look-ahead exposure

| Year | QG Look-Ahead | Value Look-Ahead |
|------|:-------------:|:----------------:|
| 2022 | 100.0% (FY2021 unavailable) | 100.0% (all trailing) |
| 2023 | 0.0% (all PIT) | 41.4% (commodity trailing) |
| 2024 | 0.0% (all PIT) | 48.3% (commodity trailing) |
| 2025 | 0.0% (all PIT) | 43.4% (commodity trailing) |

**Quality and Growth scores for 2023-2025 are clean PIT** — no look-ahead bias.  
**Value scores have ~41-48% look-ahead in 2023-2025** due to commodity ticker trailing fallback.

### Practical Impact on Weighted Scores

Since Value has only **10% weight** in Config B and **20% in Config A**, the effective
look-ahead bias in the composite final_score is:

- **Config B (10% Value):** ~4-5% effective look-ahead (2023-2025)
- **Config A (20% Value):** ~8-10% effective look-ahead (2023-2025)
- **All configs (2022):** 100% look-ahead — do not use for inference

This is a meaningful but manageable bias. Most of the score (~90% for Config B)
comes from Quality, Growth, and Momentum — which have 0% look-ahead in 2023-2025.

---

## Data Source Breakdown by Ticker Category

| Category | Tickers | Typical Source | Reliability |
|----------|---------|---------------|-------------|
| Banks (5) | BBCA, BBRI, BMRI, BBNI, ARTO | PIT | HIGH |
| Consumer/Industrial (9) | ASII, CPIN, INDF, KLBF, UNTR, AMRT, AKRA, SMGR, TOWR | PIT | HIGH |
| Commodity/Mining (8) | ADRO, BRPT, ESSA, HRUM, INCO, ITMG, MEDC, PGAS | Trailing | LOW |
| Tech/Other (7) | BUKA, EMTK, GOTO, MDKA, PTBA, ANTM, TLKM | Mixed | MODERATE |
