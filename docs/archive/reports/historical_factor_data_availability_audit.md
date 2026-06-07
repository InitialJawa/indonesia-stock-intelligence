# Historical Factor Data Availability Audit

**Scope:** Evaluation of factor data coverage from **2021-01** to the latest month (2026-06) using only repository assets.

---

## 1. Coverage Matrix

| Month   | Quality | Growth | Value | Momentum |
|---------|:------:|:------:|:-----:|:--------:|
| 2021‑01 | NO | NO | NO | NO |
| 2021‑02 | NO | NO | NO | NO |
| ...     | ... | ... | ... | ... |
| 2025‑12 | NO | NO | NO | NO |
| 2026‑05 | **YES** | **YES** | **YES** | **YES** |
| 2026‑06 | **YES** | **YES** | **YES** | **YES** |

*Only the two most recent months (2026‑05 and 2026‑06) contain any factor data. All earlier months lack snapshots.*

---

## 2. Coverage Percentages

- **Total months considered:** 66 (2021‑01 → 2026‑06 inclusive)
- **Months with data:** 2 (2026‑05, 2026‑06)

| Factor | Covered Months | Coverage % |
|--------|----------------|------------|
| Quality | 2 / 66 | **3.03 %** |
| Growth  | 2 / 66 | **3.03 %** |
| Value   | 2 / 66 | **3.03 %** |
| Momentum| 2 / 66 | **3.03 %** |

---

## 3. Source Mapping

| Input                | Source File (example) | Months Covered | Reliability |
|----------------------|-----------------------|----------------|-------------|
| **ROE**              | `snapshots/fundamentals/2026-05.json` (and 2026‑06) | 2026‑05, 2026‑06 | High (Yahoo Finance) – but many *null* values |
| **DER** (Debt‑to‑Equity) | Same as above | 2026‑05, 2026‑06 | High, but missing for many tickers |
| **Net Margin**       | Same as above | 2026‑05, 2026‑06 | High |
| **Operating Margin** | Same as above | 2026‑05, 2026‑06 | High |
| **FCF** (Free Cash Flow) | Same as above | 2026‑05, 2026‑06 | High, but sparse (many nulls) |
| **Revenue Growth**   | `snapshots/growth/2026-05.json` (and 2026‑06) | 2026‑05, 2026‑06 | High |
| **Net Income Growth**| Same as above | 2026‑05, 2026‑06 | High |
| **PE** (Price‑Earnings) | `snapshots/fundamentals/2026-05.json` | 2026‑05, 2026‑06 | High |
| **PB** (Price‑Book)   | Same as above | 2026‑05, 2026‑06 | High |
| **RS‑6M** (Relative Strength 6M) | `snapshots/momentum/2026-05.json` (and 2026‑06) | 2026‑05, 2026‑06 | High |
| **Return‑12M**        | Same as above | 2026‑05, 2026‑06 | High |

*Note:* The CSV `database/historical/factor_warehouse.csv` contains the derived quality/value/momentum/growth scores **only** for the two months shown above.

---

## 4. Missing Data Analysis

| Missing Field | Impact on Warehouse | Severity |
|---------------|---------------------|----------|
| **DER** (many `null`) | Prevents accurate Quality score; fallback constant used in legacy validation. | High |
| **FCF** (mostly `null`) | Same as above; reduces reliability of Quality factor. | High |
| **Growth scores** for many tickers (e.g., earnings_growth = 0 or missing) | Limits Growth factor construction. | Medium |
| **Value‑related fields** (PE/PB missing for a few tickers) | Affects Value factor but coverage still acceptable for most tickers. | Low |
| **Historical months (>2026‑06)** | Complete absence of any snapshots → impossible to build a time‑series Warehouse. | Critical |

---

## 5. Warehouse Feasibility

Given the evidence:
- **Momentum** data (momentum, return_6m, return_12m) is fully present for the two months.
- **Value** can be derived from PE/PB which are largely available for the same months.
- **Growth** and **Quality** suffer from missing DER/FCF and limited growth metrics.

**Feasibility options:**
- **A. Momentum Only** – Highest confidence (data present, no missing critical fields).
- **B. Momentum + Value** – Reasonable; value relies on PE/PB which are available.
- **C. Momentum + Growth** – Moderate; growth metrics exist but many earnings_growth values are zero or missing.
- **D. Full Four‑Factor** – Not feasible; Quality lacks essential DER/FCF for the majority of tickers.

**Recommendation:** **Option A – Momentum Only** as the most reliable partial Warehouse.

---

## 6. Final Recommendation

**GO WITH LIMITATIONS** – Build a **Momentum‑only** Historical Factor Warehouse covering the two months that have complete data. Expansion to Value is possible but would still be limited to 2026‑05/06; Quality and Growth cannot be reliably reconstructed without additional historical snapshots.

---

*Evidence links*
- Fundamentals snapshot: [fundamentals/2026-05.json](file:///c:/Users/Bedil%20Gaib/.gemini/antigravity/scratch/indonesia-stock-intelligence/snapshots/fundamentals/2026-05.json)
- Growth snapshot: [growth/2026-05.json](file:///c:/Users/Bedil%20Gaib/.gemini/antigravity/scratch/indonesia-stock-intelligence/snapshots/growth/2026-05.json)
- Momentum snapshot: [momentum/2026-05.json](file:///c:/Users/Bedil%20Gaib/.gemini/antigravity/scratch/indonesia-stock-intelligence/snapshots/momentum/2026-05.json)
- Factor warehouse CSV (derived scores): [database/historical/factor_warehouse.csv](file:///c:/Users/Bedil%20Gaib/.gemini/antigravity/scratch/indonesia-stock-intelligence/database/historical/factor_warehouse.csv)
