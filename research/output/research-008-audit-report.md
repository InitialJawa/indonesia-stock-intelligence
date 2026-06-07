# RESEARCH-008 WAREHOUSE V4 AUDIT REPORT

**Generated:** 2026-06-07 14:15:14
**Warehouse:** `database/historical/warehouse_daily_v4.parquet`

---

## EXECUTIVE SUMMARY

🟢 **READY FOR RESEARCH-008**

### Key Metrics

| Metric | Value |
|--------|-------|
| **Dataset Shape** | 59,303 rows × 44 columns |
| **Date Range** | 2018-01-01 to 2026-05-29 |
| **Unique Tickers** | 30 |
| **Features Found** | 25 / 25 (100.0%) |
| **Critical Issues** | 0 |
| **High Priority Issues** | 0 |

---

## FEATURE MAPPING (FUZZY MATCHING)

**Method:** Candidates tested against actual columns using fuzzy matching

### Found Features

- ✓ **RS_20d** → `rs_20d` (score: 1.00)
- ✓ **RS_60d** → `rs_60d` (score: 1.00)
- ✓ **RS_120d** → `rs_120d` (score: 1.00)
- ✓ **RS_252d** → `rs_252d` (score: 1.00)
- ✓ **RS_CHANGE_20d** → `rs_change_20d` (score: 1.00)
- ✓ **RS_CHANGE_60d** → `rs_change_60d` (score: 1.00)
- ✓ **RECOVERY** → `recovery_from_60d_low` (score: 0.91)
- ✓ **DRAWDOWN** → `drawdown_252d` (score: 1.00)
- ✓ **DISTANCE_FROM_HIGH** → `distance_from_high_252d` (score: 1.00)
- ✓ **VOLATILITY_20d** → `volatility_20d` (score: 1.00)
- ... and 15 more

### Missing Features


---

## CRITICAL ISSUES

✓ No critical issues detected.

---

## LOOK-AHEAD BIAS ANALYSIS (COLUMN NAMES ONLY)

⚠️ **IMPORTANT:** This audit only scans column names for suspicious patterns.

It does NOT detect:
- Shifted/lagged calculations (e.g., `.shift(-20)`)
- Forward-looking windows (e.g., `rolling(window=60, center=True)`)
- Renamed columns hiding future data
- Feature engineering using future data

**Manual code review of feature construction is required.**

### Suspicious Columns Found (Name-Based)

4 columns flagged:

- `daily_return` (pattern: `y_`)
- `recovery_from_60d_low` (pattern: `y_`)
- `volatility_20d` (pattern: `y_`)
- `volatility_60d` (pattern: `y_`)
---

## DATA QUALITY

**Coverage Calculation:** Relative to longest ticker history (not adjusted for listing age)

### Ticker Coverage

- **Minimum Coverage:** 33.5%
- **Average Coverage:** 95.9%
- **Maximum Gap:** 12 days
- **Longest Ticker:** `AKRA.JK` (2062 records)

⚠️ **30 Tickers with Gaps > 10 Days:**

- `ADRO.JK`: 12 days
- `AKRA.JK`: 12 days
- `AMMN.JK`: 12 days
- `ANTM.JK`: 12 days
- `ASII.JK`: 12 days
- `BBCA.JK`: 12 days
- `BBNI.JK`: 12 days
- `BBRI.JK`: 12 days
- `BMRI.JK`: 12 days
- `BRPT.JK`: 12 days
- `CPIN.JK`: 12 days
- `ESSA.JK`: 12 days
- `EXCL.JK`: 12 days
- `GOTO.JK`: 12 days
- `HEAL.JK`: 12 days
- `ICBP.JK`: 12 days
- `INDF.JK`: 12 days
- `INTP.JK`: 12 days
- `ITMG.JK`: 12 days
- `KLBF.JK`: 12 days
- `MAPI.JK`: 12 days
- `MDKA.JK`: 12 days
- `MIKA.JK`: 12 days
- `PGAS.JK`: 12 days
- `PTBA.JK`: 12 days
- `SIDO.JK`: 12 days
- `SMGR.JK`: 12 days
- `TLKM.JK`: 12 days
- `TPIA.JK`: 12 days
- `UNTR.JK`: 12 days

---

## FORWARD RETURN VALIDATION

✓ No forward return columns in feature set (GOOD)

✓ Close price column found: `Close`

---

## FINAL VERDICT: RESEARCH-008 READINESS

# 🟢 READY FOR RESEARCH-008

All critical and high-priority issues resolved.
Dataset is suitable for daily winner autopsy analysis.

**Next Step:** Proceed to run RESEARCH-008.

---

## DETAILED ISSUE LOG

1. **[MEDIUM]** Data Continuity
   - **Issue:** 30 tickers have gaps > 10 days
   - **Impact:** Snapshot selection may fail
   - **Resolution:** Handle date gaps gracefully in research script

---

## AUDIT ARTIFACTS

Generated files in `research/output/`:

- `audit-columns.csv` - All columns with data types and null %
- `audit-ticker-coverage.csv` - Coverage per ticker
- `audit-feature-mapping.csv` - Expected vs actual features (fuzzy matched)
- `audit-issues.csv` - Detailed issue log
- `audit-summary.json` - Machine-readable summary
