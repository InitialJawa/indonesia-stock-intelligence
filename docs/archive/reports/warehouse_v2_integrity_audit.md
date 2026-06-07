# Warehouse V2 Integrity Audit

**Date:** 2026-06-06  
**Scope:** 2023-01 through 2025-12 (36 months, 29 tickers, 1044 ticker-months)  
**Objective:** Determine PIT vs trailing data coverage per factor, per month.

---

## 1. Per-Factor PIT/Trailing Classification

| Factor | Data Source | PIT = Annual Financials | Trailing = 2026 TTM `info` | Notes |
|--------|------------|------------------------|---------------------------|-------|
| **Quality** | `qg_source` (ROE, profit margins) | FY financials matched to month | `info.returnOnEquity`, `profitMargins` | QG is 100% PIT in 2023-2025 |
| **Growth** | `qg_source` (revenue growth, earnings growth) | FY financials matched to month | `info.revenueGrowth`, `earningsGrowth` | QG is 100% PIT in 2023-2025 |
| **Value PE** | `data_source` (P/E ratio) | `pit_pe` from annual Net Income + shares | `pe` from `info.trailingPE` | Mixed — see breakdown below |
| **Value PB** | `data_source` (P/B ratio) | `pit_pb` from annual Total Equity + shares | `pb` from `info.priceToBook` | Same source as Value PE |
| **Momentum** | Price-only (12-month return) | Always clean (price history) | Never uses fundamental data | 100% PIT |

---

## 2. Overall Summary

| Metric | Count | Percentage |
|--------|:----:|:----------:|
| Total ticker-months (2023-2025) | 1044 | 100% |
| Quality/Growth PIT (2023-2025) | 1044 | 100.0% |
| Value PIT | 581 | 55.7% |
| Value Trailing | 463 | 44.3% |
| Momentum clean | 1044 | 100.0% |

### Key Finding

**Quality, Growth, and Momentum are 100% clean PIT in 2023-2025.**  
Only **Value** has trailing fallback — affecting 463/1044 ticker-months (44.3%).

Since Value has only **10% weight in Config B** or **20% in Config A**, the effective
PIT percentage of the composite weighted score is:

- **Config B (Q25 G30 V10 M35):** 95.6% PIT overall
- **Config A (Q30 G25 V20 M25):** 91.1% PIT overall

This means **95.6% of Config B's final score** uses clean
PIT data (only the Value component may use trailing).

---

## 3. Monthly Coverage Matrix

| Month | Tickers | Quality PIT | Growth PIT | Value PIT | Value Trailing | Momentum PIT |
|-------|:-------:|:-----------:|:----------:|:---------:|:--------------:|:------------:|
| 202301 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202302 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202303 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202304 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202305 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202306 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202307 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202308 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202309 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202310 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202311 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202312 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202401 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202402 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202403 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202404 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202405 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202406 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202407 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202408 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202409 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202410 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202411 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202412 | 29 | 100% | 100% | 52% | 48% | 100% |
| 202501 | 29 | 100% | 100% | 55% | 45% | 100% |
| 202502 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202503 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202504 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202505 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202506 | 29 | 100% | 100% | 59% | 41% | 100% |
| 202507 | 29 | 100% | 100% | 55% | 45% | 100% |
| 202508 | 29 | 100% | 100% | 55% | 45% | 100% |
| 202509 | 29 | 100% | 100% | 55% | 45% | 100% |
| 202510 | 29 | 100% | 100% | 55% | 45% | 100% |
| 202511 | 29 | 100% | 100% | 55% | 45% | 100% |
| 202512 | 29 | 100% | 100% | 55% | 45% | 100% |


---

## 4. Year Rollup

| Year | Quality PIT | Growth PIT | Value PIT | Value Trailing | Momentum PIT |
|------|:-----------:|:----------:|:---------:|:--------------:|:------------:|
| 2023 (348 ticker-months) | 100% | 100% | 59% | 41% | 100% |
| 2024 (348 ticker-months) | 100% | 100% | 52% | 48% | 100% |
| 2025 (348 ticker-months) | 100% | 100% | 57% | 43% | 100% |


---

## 5. Effective PIT Weight by Month (Composite Score)

| Month | Config B Effective PIT% | Config A Effective PIT% |
|-------|:----------------------:|:----------------------:|
| 202301 | 95.9% | 91.7% |
| 202302 | 95.9% | 91.7% |
| 202303 | 95.9% | 91.7% |
| 202304 | 95.9% | 91.7% |
| 202305 | 95.9% | 91.7% |
| 202306 | 95.9% | 91.7% |
| 202307 | 95.9% | 91.7% |
| 202308 | 95.9% | 91.7% |
| 202309 | 95.9% | 91.7% |
| 202310 | 95.9% | 91.7% |
| 202311 | 95.9% | 91.7% |
| 202312 | 95.9% | 91.7% |
| 202401 | 95.2% | 90.3% |
| 202402 | 95.2% | 90.3% |
| 202403 | 95.2% | 90.3% |
| 202404 | 95.2% | 90.3% |
| 202405 | 95.2% | 90.3% |
| 202406 | 95.2% | 90.3% |
| 202407 | 95.2% | 90.3% |
| 202408 | 95.2% | 90.3% |
| 202409 | 95.2% | 90.3% |
| 202410 | 95.2% | 90.3% |
| 202411 | 95.2% | 90.3% |
| 202412 | 95.2% | 90.3% |
| 202501 | 95.5% | 91.0% |
| 202502 | 95.9% | 91.7% |
| 202503 | 95.9% | 91.7% |
| 202504 | 95.9% | 91.7% |
| 202505 | 95.9% | 91.7% |
| 202506 | 95.9% | 91.7% |
| 202507 | 95.5% | 91.0% |
| 202508 | 95.5% | 91.0% |
| 202509 | 95.5% | 91.0% |
| 202510 | 95.5% | 91.0% |
| 202511 | 95.5% | 91.0% |
| 202512 | 95.5% | 91.0% |


---

## 6. Ticker-Level Trailing Fallback Analysis

### A. Tickers Always Using Trailing Value (every month, 2023-2025)

Tickers: ADRO.JK, BBNI.JK, BRPT.JK, ESSA.JK, GOTO.JK, HRUM.JK, INCO.JK, ITMG.JK, MDKA.JK, MEDC.JK, PGAS.JK

  - ADRO.JK: Commodity — Yahoo annual financials in wrong scale/units (~6000x error). PE/PB from annuals unusable.
  - BBNI.JK: Bank — PIT PE=0.11 (Net Income annual data incorrectly parsed). Falls outside valid 0.5-200 range.
  - BRPT.JK: Commodity — Yahoo annual financials in wrong scale/units.
  - ESSA.JK: Commodity — Yahoo annual financials in wrong scale/units.
  - GOTO.JK: Tech — No positive earnings (PE=0). PIT always invalid.
  - HRUM.JK: Commodity — Yahoo annual financials in wrong scale/units.
  - INCO.JK: Commodity — Yahoo annual financials in wrong scale/units.
  - ITMG.JK: Commodity — Yahoo annual financials in wrong scale/units.
  - MDKA.JK: Mining — No positive earnings (PE=0). PIT always invalid.
  - MEDC.JK: Commodity — Yahoo annual financials in wrong scale/units.
  - PGAS.JK: Commodity — Yahoo annual financials in wrong scale/units.

### B. Tickers Switching Between PIT and Trailing

  - **ARTO.JK**: PIT in 5 months (202502, 202503, 202504, 202505, 202506), trailing in 31 months (202301, 202302, 202303, 202304, 202305, 202306, 202307, 202308, 202309, 202310, 202311, 202312, 202401, 202402, 202403, 202404, 202405, 202406, 202407, 202408, 202409, 202410, 202411, 202412, 202501, 202507, 202508, 202509, 202510, 202511, 202512)
    Root cause: Bank — PIT PE=158-200 borderline but technically valid. PIT used in some months, trailing when PE outside valid range.

  - **BUKA.JK**: PIT in 12 months (202301, 202302, 202303, 202304, 202305, 202306, 202307, 202308, 202309, 202310, 202311, 202312), trailing in 24 months (202401, 202402, 202403, 202404, 202405, 202406, 202407, 202408, 202409, 202410, 202411, 202412, 202501, 202502, 202503, 202504, 202505, 202506, 202507, 202508, 202509, 202510, 202511, 202512)
    Root cause: Tech — PIT PE may be invalid (negative earnings or extreme values). Trailing fallback when PE outside 0.5-200.

  - **EMTK.JK**: PIT in 24 months (202301, 202302, 202303, 202304, 202305, 202306, 202307, 202308, 202309, 202310, 202311, 202312, 202501, 202502, 202503, 202504, 202505, 202506, 202507, 202508, 202509, 202510, 202511, 202512), trailing in 12 months (202401, 202402, 202403, 202404, 202405, 202406, 202407, 202408, 202409, 202410, 202411, 202412)
    Root cause: Media/Tech — PIT PE may be invalid or extreme. Trailing fallback when PE outside 0.5-200.



### C. Tickers Always PIT (never trailing, 2023-2025)

Tickers: AKRA.JK, AMRT.JK, ANTM.JK, ASII.JK, BBCA.JK, BBRI.JK, BMRI.JK, CPIN.JK, INDF.JK, KLBF.JK, PTBA.JK, SMGR.JK, TLKM.JK, TOWR.JK, UNTR.JK

These 15 tickers have 100% clean PIT for ALL factors in ALL months.

---

## 7. Integrity Assessment

### Strengths

1. **Quality and Growth are 100% PIT in 2023-2025** — no look-ahead bias in these factors.
   This covers 55% of Config B's weighted score (25% Quality + 30% Growth).

2. **Momentum is 100% clean** — price-based, never uses fundamental data.
   This covers 35% of Config B's weighted score.

3. **Combined: 90% of Config B score is PIT** on typical months, **100% PIT on
   the 15 fully-clean tickers** (15/29 = 52% of universe).

4. **No fully-trailing months exist** in 2023-2025 (0 ticker-months with both
   QG and Value trailing).

5. **Sector rules are correctly applied** — bank DER exclusion, commodity PE halving
   in percentile normalization.

### Weaknesses

1. **Value factor is ~44% trailing** — affects
   44% of ticker-months. The Value score uses 2026 TTM
   PE/PB for these months, introducing look-ahead bias.

2. **11/29 tickers (38%) have fundamentally broken annual financial data**
   from Yahoo Finance — primarily commodity/mining. This is a data source limitation,
   not a Warehouse V2 bug.

3. **Dividend yield (30% of Value formula) is omitted** — currently factored as 0,
   which depresses Value scores somewhat. This affects all tickers equally.

4. **3 tickers switch between PIT and trailing inconsistently** — ARTO (PE 158-200
   borderline), BUKA (PIT in 2023 only), EMTK (trailing in 2024 only). The PIT/trailing
   boundary depends on PE range validation (0.5-200), creating artificial discontinuity.
   11 other tickers are consistently trailing (commodity data failure, zero earnings).

### Verdict

| Criterion | Score | Basis |
|-----------|:-----:|-------|
| Quality PIT | **A** | 100% PIT in 2023-2025 |
| Growth PIT | **A** | 100% PIT in 2023-2025 |
| Value PIT | **C-** | 56% PIT — main weakness |
| Momentum PIT | **A+** | 100% clean (price-only) |
| Config B effective PIT | **B+** | 95.6% of weighted score is PIT |
| Config A effective PIT | **B-** | 91.1% of weighted score is PIT |
| Universe coverage | **B** | 29/30 IDX30 tickers (96.7%) |
| Temporal coverage | **B** | 36 months — adequate for exploratory research |

### Conclusion

**Warehouse V2 is CLEAN ENOUGH for factor research on Quality, Growth, and Momentum**
(90% of Config B score). The Value factor's 44% trailing rate
is a known limitation that primarily affects:

- Value-only analysis (not recommended with current data)
- Configs with high Value weight (Config A: 20% Value → 91.1% effective PIT)
- Commodity/mining ticker research (11/29 tickers have unreliable Value data)

**For factor-weight optimization (Quality vs Growth vs Momentum), the warehouse is
methodologically sound.** Value weight optimization should be deferred until
commodity ticker annual financials can be fixed.

**Recommended confidence level: B- (Strong Exploratory)** for multi-factor research.
Upgrade to A- once Value reaches 80%+ PIT coverage.
