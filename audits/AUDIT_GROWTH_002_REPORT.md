# AUDIT-GROWTH-002: Growth Definition Comparison

> Generated: 2026-06-09 18:28 WIB  
> Data: 2024-06 snapshot (29 IDX30 tickers) + yfinance + warehouse_v3 (47 months)  

---

## Critical Finding: Warehouse vs Standalone Definition Mismatch

| Component | Growth Formula | Source |
|-----------|---------------|--------|
| `scoring/growth_score.py` (standalone) | **Earnings only** (100% earnings percentile) | `scoring/growth_score.py:25` |
| `build_warehouse_v3.py` (production) | **50% Revenue + 50% Earnings percentile** | `build_warehouse_v3.py:507` |
| `research_013c_factor_attribution.py` | Uses warehouse scores (50/50 blend) | warehouse_v3.csv |

**Impact**: All RESEARCH-013C conclusions about "Growth having negative IC" were based on the **50/50 blend** (warehouse), NOT the standalone earnings-only definition. The two definitions produce materially different rankings.

## Growth Definition Comparison

| Definition | 1M IC | 3M IC | 6M IC | CAGR (Top5) | Top 5 Picks | Notes |
|-----------|-------|-------|-------|-------------|-------------|-------|
| earnings_growth | 0.0591 | 0.0813 | 0.0379 | 63.18% | BRPT.JK, ARTO.JK, GOTO.JK, INCO.JK, BMRI.JK | Current standalone definition |
| revenue_growth | -0.3177 | -0.1345 | -0.2670 | 26.27% | MDKA.JK, GOTO.JK, BUKA.JK, ARTO.JK, BBCA.JK |  |
| earnings+revenue | -0.1202 | -0.0182 | -0.1131 | 96.25% | GOTO.JK, ARTO.JK, BBCA.JK, BMRI.JK, AMRT.JK | Current warehouse definition |
| earnings_acceleration | -0.2089 | -0.0433 | -0.3946 | -17.23% | BRPT.JK, BUKA.JK, MDKA.JK, INCO.JK, ANTM.JK | yfinance annual data |
| 3Y earnings CAGR | 0.1354 | 0.0254 | 0.1869 | 122.97% | BRPT.JK, ARTO.JK, CPIN.JK, ANTM.JK, KLBF.JK |  |

## Snapshot Raw Data (2024-06)

| Ticker | Rev Growth | Ern Growth | Ern Score | Rev Score | Comb Score |
|--------|-----------|-----------|-----------|----------|------------|
| BBCA.JK | 12.25% | 19.40% | 78.5700 | 85.7100 | 82.1400 |
| BMRI.JK | 7.40% | 33.74% | 85.7100 | 71.4300 | 78.5700 |
| AMRT.JK | 10.34% | 19.21% | 75.0000 | 82.1400 | 78.5700 |
| UNTR.JK | 4.03% | -1.87% | 53.5700 | 50.0000 | 51.7850 |
| ADRO.JK | -73.64% | -34.16% | 28.5700 | 0.0000 | 14.2850 |
| BBNI.JK | -0.39% | 14.18% | 60.7100 | 32.1400 | 46.4250 |
| BBRI.JK | 8.24% | 17.45% | 71.4300 | 75.0000 | 73.2150 |
| PGAS.JK | 2.18% | -14.76% | 42.8600 | 42.8600 | 42.8600 |
| CPIN.JK | 8.35% | -20.82% | 32.1400 | 78.5700 | 55.3550 |
| INDF.JK | 0.79% | 28.12% | 82.1400 | 35.7100 | 58.9250 |
| INCO.JK | 4.48% | 36.89% | 89.2900 | 53.5700 | 71.4300 |
| AKRA.JK | -11.47% | 15.69% | 64.2900 | 10.7100 | 37.5000 |
| MEDC.JK | -2.72% | -37.71% | 25.0000 | 28.5700 | 26.7850 |
| ASII.JK | 5.04% | 16.91% | 67.8600 | 57.1400 | 62.5000 |
| PTBA.JK | -9.75% | -51.42% | 17.8600 | 17.8600 | 17.8600 |
| ... | ... | ... | ... | ... | ... |


## Warehouse Growth Score Multi-Month IC (2022-2025)

This is the IC of the **50/50 blend** (current warehouse definition) across all 47 months.

| Metric | Value |
|--------|-------|
| Mean IC (1M forward) | -0.0673 |
| IC > 0 | 20/47 |
| IC < 0 | 27/47 |
| IC Sharpe | -1.2436 |

## Analysis & Conclusions

### 1. Definition Comparison Results

From the snapshot comparison (June 2024, single-period):

- **Best 1M IC**: 3Y earnings CAGR (IC = 0.1354)
- **Worst 1M IC**: revenue_growth (IC = -0.3177)

### 2. The Real Problem: Definition Inconsistency

The most critical finding is **not** which definition is best, but that the codebase has TWO conflicting definitions:

1. **`scoring/growth_score.py`**: Earnings-only (100% earnings_growth percentile).
   The comment at line 24 states: `Menghilangkan Revenue Growth yang menghasilkan alpha negatif`.

2. **`build_warehouse_v3.py`**: 50% Revenue + 50% Earnings blend (line 507).
   This was introduced silently when the V3 warehouse was built. No corresponding update was made to
   the standalone scoring script, and the reason for including revenue growth again is undocumented.

This means:
- The standalone scoring pipeline produces **different growth scores** than the warehouse.
- All backtests (RESEARCH-013A, 013B, 013C) used the **warehouse definition** (50/50 blend).
- The RESEARCH-013C conclusion that "Growth has negative IC" applies to the **50/50 blend**, not earnings-only.
- The comment claiming revenue_growth has negative alpha may refer to a different time period or was
  never validated against the V3 data.

### 3. Why This Matters

If earnings-only growth has a different (potentially positive) IC, then the RESEARCH-013C conclusion
that "Growth has negative IC" becomes:

> **"The warehouse 50/50 growth blend has negative IC"**

This is a fundamentally different statement. The standalone earnings-only definition might have
positive IC, which would mean:
- Config B (G=30%) might not drag as much with earnings-only growth.
- The Config B vs Config F comparison might change.
- The recommendation to favor Config F might be less robust.

### 4. Recommendations

| # | Recommendation | Priority |
|---|---------------|----------|
| R1 | **Reconcile the two definitions** — either update `scoring/growth_score.py` to match warehouse (50/50 blend) or update warehouse to match standalone (earnings-only). Having two definitions is a bug. | **HIGH** |
| R2 | **Re-run RESEARCH-013C** with the earnings-only growth definition to determine which IC is actually positive/negative. | **HIGH** |
| R3 | **Document the reason** for including/excluding revenue growth. If revenue_growth was excluded for negative alpha, show the evidence. If it was re-included in V3, show the evidence. | MEDIUM |
| R4 | **Validate with longer data** — the single-month snapshot comparison is insufficient. Run the V3 warehouse builder with raw growth values captured, then compute IC for all 5 definitions across 47 months. | MEDIUM |

### 5. Root Cause

The root cause of this audit is not about factor selection but **pipeline drift**:

1. Original design (growth_score.py): earnings-only growth.
2. Warehouse V3 (build_warehouse_v3.py): 50/50 blend — introduced without updating the scoring script.
3. RESEARCH-013C tested the warehouse scores and concluded "Growth IC negative."
4. But this conclusion applies only to the 50/50 warehouse blend, not the original earnings-only definition.

**The question "Is earnings_growth the best definition?" cannot be answered until the codebase uses a single definition.**

---
*Report generated by `audits/audit_growth_002.py`*
