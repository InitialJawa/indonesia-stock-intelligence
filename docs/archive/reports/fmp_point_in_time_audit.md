# FMP Point-in-Time Validation Audit

**Date:** 2026-06-06  
**Prepared by:** AI Architect — Pre-Build Investigation  
**Scope:** FMP API temporal safety for Historical Factor Warehouse V2  
**Repository context:** `utils/data_provider.py`, `archives/research/fmp/`

---

## Purpose

This audit answers one question with scientific precision:

> **If we use FMP to backfill historical fundamental data for 2021–2025,
> does the resulting warehouse contain look-ahead bias?**

Every answer below is grounded in either repository evidence (file paths cited)
or live FMP API documentation retrieved 2026-06-06.

---

## QUESTION 1 — Does FMP expose `reportedDate`, `acceptedDate`, `fillingDate`?

### Finding: YES — on financial statement endpoints. NOT on ratios endpoint.

FMP exposes three distinct date fields on its financial statement endpoints
(`/income-statement`, `/balance-sheet-statement`, `/cash-flow-statement`):

| Field | What it represents | Available on |
|---|---|---|
| `date` | Fiscal period **end date** (e.g. 2022-12-31) | All statement + ratios endpoints |
| `fillingDate` | Date the company **submitted** the report to the regulator | Statement endpoints only |
| `acceptedDate` | Exact **timestamp** the regulator formally accepted the filing | Statement endpoints only |

**Source — FMP API documentation (retrieved 2026-06-06):**

> *"fillingDate: This is the date on which the company officially filed the
> report with the SEC. This indicates when the document was submitted and made
> available to the public record."*

> *"acceptedDate: This is the date and time when the SEC formally accepted the
> filing into its EDGAR database. It is often the most precise timestamp, as it
> frequently includes the specific time of acceptance (e.g., 2024-11-01 06:01:36)."*

### Critical gap: `/ratios` endpoint

The ISI project's FMP integration (`archives/research/fmp/fmp_audit_report.md`)
uses two endpoints:

```
https://financialmodelingprep.com/api/v3/ratios/{ticker}?limit=1&apikey=...
https://financialmodelingprep.com/api/v3/financial-growth/{ticker}?limit=1&apikey=...
```

**The `/ratios` endpoint returns only the `date` field (fiscal period end).**
It does NOT return `fillingDate` or `acceptedDate`.

This means: when you call `/ratios`, you receive the ratio value keyed to when
the fiscal period **ended** — not when the data became **public**. A July 2022
backtest that reads `/ratios?limit=1` for the 2021-12-31 period would be using
data that was filed weeks or months after December 31, 2021.

**Verdict for Q1:**

| Endpoint | `date` | `fillingDate` | `acceptedDate` |
|---|---|---|---|
| `/income-statement` | ✅ | ✅ | ✅ |
| `/balance-sheet-statement` | ✅ | ✅ | ✅ |
| `/cash-flow-statement` | ✅ | ✅ | ✅ |
| `/ratios` | ✅ | ❌ | ❌ |
| `/financial-growth` | ✅ | ❌ | ❌ |

**The two endpoints used by ISI's FMP integration do NOT expose filing dates.**

---

## QUESTION 2 — Can we determine exactly when a financial report became public?

### Verdict: CONDITIONAL PASS — on statement endpoints. FAIL on ratios endpoint.

**On `/income-statement`, `/balance-sheet-statement`, `/cash-flow-statement`:**

Yes. Each record contains both `fillingDate` and `acceptedDate`. The
`acceptedDate` is the most precise: it includes a timestamp down to the
second (e.g. `"2022-08-05 16:33:21"`). A correctly-built pipeline can use
`acceptedDate` to determine the exact moment a given set of financials became
public knowledge, then map any backtest date to only the filings whose
`acceptedDate` precedes it.

**On `/ratios` and `/financial-growth`:**

No. These endpoints return only the `date` field (fiscal period end). There
is no way to extract the filing date from these endpoints alone. A pipeline
using only `/ratios` cannot determine when ratios became available without
cross-referencing statement endpoints separately.

**Evidence from ISI repository:**

`archives/research/fmp/fmp_audit_report.md` documents that the ISI integration
uses `/ratios` and `/financial-growth` with `limit=1`. The `limit=1` parameter
returns the **most recent** record only — discarding all historical periods.
This design was built for live pipeline use, not historical reconstruction.

```
# From fmp_audit_report.md (line 21–23):
# Endpoint: /ratios/{ticker}?limit=1&apikey=...
# Endpoint: /financial-growth/{ticker}?limit=1&apikey=...
```

A historical warehouse using these endpoints as designed would retrieve today's
most recent ratio, not the ratio for any specific historical period.

**Verdict for Q2: CONDITIONAL PASS**  
Filing dates ARE available, but only via statement endpoints, not via the ratio
and growth endpoints currently used in ISI's FMP integration.

---

## QUESTION 3 — Could a July 2022 ranking accidentally see information from an August 2022 filing?

### Verdict: FAIL — Look-ahead contamination is structurally guaranteed under the current design.

This is the core look-ahead bias question. The answer is yes — and the
contamination pathway is documented clearly.

### How the contamination occurs

**Pathway A — Via `/ratios` endpoint (ISI current design)**

The `/ratios/{ticker}?limit=1` endpoint returns the most recent ratio
record available today. If called in 2026 to reconstruct a July 2022 score,
it returns ratios based on **2025 or 2026 fiscal year data** — not 2021 or
2022 data. This is a **4–5 year look-ahead**.

Even if `limit=N` is used to retrieve historical periods, the `date` field
on `/ratios` represents the **fiscal period end date** (e.g. 2021-12-31),
not the **public availability date**. A company with a December fiscal year
end typically files its annual report in February or March of the following
year. For Indonesia (IDX), the regulatory filing deadline for annual reports
under OJK rules is **120 days after fiscal year end** (April 30).

**Concrete example: BBCA.JK FY2021**

| Event | Date |
|---|---|
| Fiscal year ends | 2021-12-31 |
| FMP `date` field value | 2021-12-31 |
| Estimated filing/acceptance date | ~March–April 2022 |
| Earliest safe use in backtest | 2022-04 or later |

A July 2022 backtest using FMP `/ratios` keyed to `date = 2021-12-31` is safe —
but **only** if the builder correctly filters to `acceptedDate < 2022-07-01`.
The ratios endpoint does not expose this field, making correct filtering impossible
without also querying the statement endpoints.

**Pathway B — Via restated/adjusted data**

FMP documentation (retrieved 2026-06-06) confirms:

> *"Standard APIs (e.g., /ratios, /financial-statement): These endpoints
> typically provide standardized data. FMP often processes and updates these
> figures to account for restatements, audit adjustments, and reclassifications,
> ensuring that historical comparisons remain consistent for financial modeling."*

This means the `/ratios` endpoint for `date = 2021-12-31` **may reflect a
restated figure that was revised in 2023 or 2024**, not the figure investors
could read in April 2022. For Indonesian companies this risk is moderate —
PSAK restatements occur but are less frequent than US GAAP restatements.

**Pathway C — IDX-specific reporting lag uncertainty**

FMP's own documentation warns:

> *"The latency for international exchanges like the IDX may vary depending on
> the availability and processing of local regulatory disclosures."*

For Indonesian stocks, FMP ingests filings from IDX/OJK regulatory disclosures,
not SEC EDGAR. The `acceptedDate` field may not be available, or may reflect FMP's
internal ingestion timestamp rather than the actual public disclosure date.

**Verdict for Q3: FAIL**

A July 2022 ranking using FMP `/ratios` as currently designed in ISI **can and
will** see data that was not publicly available in July 2022. The contamination
has three pathways:
1. The endpoint returns no `fillingDate`, so the builder cannot filter by public availability date
2. Standard ratios may incorporate post-period restatements
3. IDX filing lag timing is unverified by FMP for non-SEC filings

---

## QUESTION 4 — Are historical ratios calculated from data available at that date, or recalculated using restated statements?

### Finding: Standard endpoints use restated/standardized data. As-Reported endpoints use original filings.

FMP offers two distinct data tiers:

| Tier | Endpoint example | Data nature |
|---|---|---|
| **Standard** | `/ratios`, `/income-statement` | Standardized, may incorporate restatements |
| **As-Reported** | `/financial-statement-full-as-reported` | Original filing data, no adjustments |

**Evidence from FMP documentation (retrieved 2026-06-06):**

> *"Standard APIs (e.g., /ratios): FMP often processes and updates these figures
> to account for restatements, audit adjustments, and reclassifications, ensuring
> that historical comparisons remain consistent."*

> *"As-Reported APIs: These endpoints are explicitly designed to provide data
> exactly as it appeared in the original filings. This raw, unadjusted data is
> intended for audits, compliance, or research where you need to see exactly what
> was disclosed at a specific point in time."*

**Critical implication for ISI V2:**

The ISI production scoring uses `/ratios` (standard tier). This means:

- ROE for `date = 2021-12-31` returned today **may reflect a 2023 restatement**
- Net margin for `date = 2022-12-31` may be the **corrected** figure, not the one investors saw in early 2023
- Ratios are not point-in-time safe by default

**To achieve point-in-time safety, ISI would need to:**
1. Use `/financial-statement-full-as-reported` endpoint (not the ISI's current approach)
2. Recalculate all ratios manually from as-reported line items
3. Map each calculation to `acceptedDate`, not `date`

**ISI repository evidence:**

`archives/research/fmp/fmp_audit_report.md` documents the ratios mapping:

```
# From fmp_audit_report.md:
# pe_ratio   → priceEarningsRatio     (from /ratios)
# roe        → returnOnEquity          (from /ratios)
# debt_to_equity → debtEquityRatio    (from /ratios)
# net_margin → netProfitMargin         (from /ratios)
```

**All four metrics come from the standard `/ratios` endpoint — standardized,
potentially restated, keyed to fiscal period end only.**

`archives/research/fmp/fmp_audit_report.md` (line 37) also confirms:

> *"free_cash_flow is never fetched from FMP because it is not implemented
> in `_fetch_from_fmp`."*

FCF — which contributes 20% of Quality Score for non-bank tickers — has no
FMP source at all. It would fall back to Yahoo Finance's `freeCashflow`, which
is always TTM (trailing twelve months, as of today).

**Verdict for Q4: PARTIAL**

- Standard `/ratios` endpoint: data keyed to fiscal period end, may incorporate restatements → **NOT point-in-time safe**
- As-Reported endpoint: data from original filing, original figures → **point-in-time safe** (with `acceptedDate` filtering)
- FCF: no FMP source, falls back to YF TTM → **never point-in-time safe**

---

## QUESTION 5 — Can point-in-time fundamental reconstruction be claimed?

### Verdict: C — Approximate Only

Evaluated against three precision tiers:

---

### Tier A — Exact Point-in-Time Reconstruction

**Requirements:**
- All fundamental inputs sourced from original filings (`as-reported` data)
- Each value gated by `acceptedDate < evaluation_date`
- No restated figures used
- FCF derived from original cash flow statements, not TTM API

**Can ISI V2 achieve this with FMP?**

Only if all of the following are implemented:
1. Switch from `/ratios` → `/financial-statement-full-as-reported`
2. Recalculate ROE, margins, DER, FCF, PE, PB from raw line items
3. Filter all records by `acceptedDate < month_end_price_date`
4. Handle IDX-specific `acceptedDate` uncertainty (OJK vs SEC filing pipeline)

**Assessment: NOT achievable with current ISI FMP integration design.**
Achievable only with significant engineering investment.

---

### Tier B — Near-Exact Point-in-Time Reconstruction

**Requirements:**
- Fiscal period end dates used (accepting the lag assumption)
- Reporting lag modelled explicitly (e.g., +120 days for IDX annual reports)
- Standard restated figures used, with assumption that restatements are rare
- FCF derived from statement endpoints (not TTM)

**Can ISI V2 achieve this?**

Yes, if the following assumptions are accepted and documented:
- Reporting lag is modelled as: fundamentals become available 120 days after fiscal year end
- Restatements are assumed to be non-material (acceptable for IDX large-caps)
- FCF sourced from `/cash-flow-statement` (not YF TTM)
- PE/PB computed as `historical_price / EPS_from_prior_annual`

**Assessment: Achievable with engineering effort. Requires explicit bias documentation.**

---

### Tier C — Approximate Reconstruction

**What it means:**
- Use current YF TTM fundamentals for all historical months
- No filing lag modelling
- Accept 4–5 year look-ahead contamination

**Assessment: Trivially achievable but scientifically invalid for backtesting.**

---

### Overall Verdict: **C — Approximate Only** (under current ISI FMP design)

**B — Near-Exact** is achievable, but requires:
- Switching to statement endpoints (not ratios endpoint)
- Implementing reporting lag logic
- Sourcing FCF from cash flow statements
- Documenting residual restatement risk

---

## Summary Scorecard

| Question | Finding | Verdict |
|---|---|---|
| Q1: Do FMP statement endpoints expose filing dates? | Yes — `fillingDate` and `acceptedDate` on statement endpoints. NOT on `/ratios`. | CONDITIONAL PASS |
| Q2: Can we determine when a report became public? | Yes via statement endpoints. No via ratios endpoint (current ISI design). | CONDITIONAL PASS |
| Q3: Could July 2022 ranking see August 2022 data? | Yes. Three contamination pathways confirmed. Current design provides no guard. | **FAIL** |
| Q4: Are ratios restated or as-reported? | Standard `/ratios` endpoint: restated/standardized. As-Reported endpoint: original. | PARTIAL |
| Q5: Can point-in-time reconstruction be claimed? | Not under current design. Possible with significant re-engineering. | **C — Approximate** |

---

## Engineering Requirements to Achieve Near-Exact (Tier B)

For the record, achieving Tier B requires the following changes to the ISI
data pipeline — none of which are currently implemented:

| Requirement | Effort | Status |
|---|---|---|
| Switch to `/income-statement` + `/balance-sheet-statement` + `/cash-flow-statement` | Medium | Not implemented |
| Recalculate ROE, margins, DER, FCF from raw line items | Medium | Not implemented |
| Model reporting lag: `available_date = max(fiscal_end + 90 days, acceptedDate)` | Low | Not implemented |
| Filter all records by `available_date < backtest_date` | Low | Not implemented |
| Compute PE = `price_at_date / EPS_last_annual_before_date` | High | Not implemented |
| Compute PB = `price_at_date / BPS_last_annual_before_date` | High | Not implemented |
| Verify IDX `acceptedDate` field accuracy vs OJK filing dates | High | Not verified |
| FMP API key active and configured in environment | Blocker | Not present in repo |

---

## Conclusion

FMP **does** expose the fields required for point-in-time reconstruction
(`fillingDate`, `acceptedDate`), but these fields are only available on
**statement endpoints**, not on the `/ratios` endpoint that ISI's current
integration uses.

The current ISI FMP design (`utils/data_provider.py`, `archives/research/fmp/`)
is built for live production scoring, not historical reconstruction. Using it
unchanged for the Factor Warehouse V2 would produce data with look-ahead
contamination on every fundamental metric.

**Point-in-time fundamental reconstruction via FMP is possible, but only
with a purpose-built collector that uses statement endpoints, implements
reporting lag logic, and recalculates ratios from raw as-reported line items.**

No such collector exists in the ISI repository today.
