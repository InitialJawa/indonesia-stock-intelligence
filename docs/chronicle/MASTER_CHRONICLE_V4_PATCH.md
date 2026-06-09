# MASTER_CHRONICLE_V3 → V4: Patch Instructions

**Generated:** 2026-06-09
**Source:** AUDIT-CRITICAL-001 + RESEARCH-013-P0 Foundation Recovery
**Purpose:** Correct all FALSE, OUTDATED, and UNVERIFIABLE claims before V4 publication.

---

## Claim Classification Key

| Class | Meaning | Action |
|-------|---------|--------|
| **VALID** | True and current | Keep as-is |
| **FALSE** | Contradicted by code/config/data | Rewrite or delete |
| **OUTDATED** | Was true when written, superseded by new findings | Update |
| **UNVERIFIABLE** | No supporting evidence exists | Remove or reclassify |
| **MISLEADING** | Technically true but contextually wrong | Clarify |

---

## PATCH 1: RESEARCH-013A Section (lines 3-8)

**Classification:** UNVERIFIABLE

**Problem:** Claimed `audits/baseline_reproducibility.py` produced CAGR diff 0.11%, Sharpe diff 0.70%, Alpha diff 0.14%. File never existed in any git commit. Numbers are circular self-reference.

**Action:** Replace entire section with corrected version:

```markdown
## RESEARCH-013A Baseline Reproducibility Audit

**Status:** REBUILT — 2026-06-09 (see `research/RESEARCH-013_P0_FOUNDATION_RECOVERY.md`)

Original RESEARCH-013A_VERIFICATION.md claimed unreproducible results — the
claimed script `audits/baseline_reproducibility.py` never existed in the repository.
All metrics were circular self-reference.

Re-executed from scratch using:
- **Engine:** `research/research_013a_baseline_reproducibility.py`
- **Data:** `warehouse_historical/warehouse_v3.csv` (2022-01 to 2025-12)
- **Weights:** Config B (Q25/G30/V10/M35)
- **Portfolio:** Top 5 equal-weight, monthly rebalance
- **Output:** `research/output/research_013a_reproducibility.csv`

**Config B Results (47 months, 2022-02 to 2025-12):**
- CAGR: 17.45%
- Sharpe: 0.74
- CAPM Alpha: 19.43%
- Max DD: 29.17%
- Win Rate: 53.19%
- Sortino: 0.89
- Benchmark (IHSG) CAGR: -0.60%
- Excess CAGR: 18.05%

**Verdict:** PASS — code executes correctly, Config B weights applied, metrics computed.
Previous 46.33% CAGR from GATE-001 used different methodology (daily warehouse data);
this reproduction uses monthly V3 factor scores and produces different numbers.

```
**References:** Delete `docs/RESEARCH-013A_VERIFICATION.md`

---

## PATCH 2: Project Overview — Production Config (lines 21, 28-29, 37)

**Classification:** FALSE (lines 21, 28-29, 37)

**Problem:** Chronicle claims Config B is production with Q25/G30/V10/M35 and "Locked. Do not modify weights." In reality:
- `config/scoring_weights.json` has **Config F** (Q25/G10/V30/M35) since June 7
- `final_score_v3.py` reads config at runtime → production uses Config F
- Config was changed silently without ADR, violating ADR-004

**Action:** Update line 21 and the component table:

Line 21 change:
```diff
- stocks using a multi-factor model (Config B) with supporting turnaround and exit monitoring layers.
+ stocks using a multi-factor model (currently Config F — see ADR-005 decision) with supporting turnaround and exit monitoring layers.
```

Lines 28-29 change:
```diff
- **Mode:** STABILIZATION — no production strategy changes, no Config B modifications,
- no new research without explicit approval. Focus: data integrity and documentation.
+ **Mode:** STABILIZATION — no production strategy changes without ADR approval.
+ Focus: data integrity and documentation.
```

Line 37 change (component table):
```diff
- | Config B (Q25/G30/V10/M35) | PRODUCTION | Locked. Do not modify weights |
+ | Config F (Q25/G10/V30/M35) | PRODUCTION | Weights in config/scoring_weights.json. See ADR-005 |
+ | Config B (Q25/G30/V10/M35) | RESEARCH | Validated by V3 walk-forward. Used by RESEARCH-012 GATE-001 |
```

---

## PATCH 3: Section 2.1 — Core Ranking Engine (lines 50-67)

**Classification:** FALSE (lines 52, 57-62, 66-67), OUTDATED (line 64-65)

**Problem:**
- Line 52: Weights listed are Config B, but production uses Config F
- Lines 57-62: "Key Backtest Results" (0.82% CAGR, 88 months) appear to be momentum-only survivorship data from the old survivorship reports, NOT Config B backtest results
- Lines 64-65: ADR-004 is correct but contradicted by actual config change
- Line 66: We WERE modified without Historical Factor Warehouse V2
- Line 67: GATE-001 numbers are for Config B, not current production

**Action:** Replace entire section:

```markdown
### 2.1 Core Ranking Engine

**Production Weights (config/scoring_weights.json):** Quality 25% | Growth 10% | Value 30% | Momentum 35%
**Research Baseline (Config B):** Quality 25% | Growth 30% | Value 10% | Momentum 35%
**Portfolio:** Top 5 equal weight, monthly rebalance
**Universe:** IDX30 (dynamic historical for backtests)
**Data:** Yahoo Finance (single source)

**Config B Backtest (V3 warehouse, 2022-02 to 2025-12, 47 months, monthly rebalance):**
- CAGR: 17.45%
- Sharpe: 0.74
- Max DD: 29.17%
- CAPM Alpha: 19.43%
- Win Rate: 53.19%

**IMPORTANT:** ADR-004 suspends all weight superiority claims. Current production
weights (Config F) run because they are what's on disk — not because Config F has
been proven superior. OOS weight comparison (RESEARCH-013-P0 Phase B) now functions
correctly. See `reports/oos_weight_comparison_v3.md` for full results.

**RESEARCH-012 (GATE-001) confirmed:** Config B Top 5 monthly rebalance produced
46.33% CAGR (2022-2025, daily warehouse methodology). Config B remains the most
thoroughly validated configuration, though not currently the production weights.
```

---

## PATCH 4: Section 8 — Architecture (line 354)

**Classification:** FALSE

**Problem:** Labels `final_score_v3.py` as "Config B composite (Q25/G30/V10/M35)" but it loads whatever weights are in `config/scoring_weights.json`, which is Config F.

**Action:**
```diff
- │   └── final_score_v3.py           Config B composite (Q25/G30/V10/M35)
+ │   └── final_score_v3.py           Weighted composite (reads config/scoring_weights.json)
```

---

## PATCH 5: Section 10 — Open Question 1 (line 442)

**Classification:** OUTDATED

**Problem:** "Config F vs Config B — Config F shows higher CAGR. BLOCKED: requires Historical Factor Warehouse V2." This question is now partially answerable with the fixed OOS framework + V3 warehouse.

**Action:**
```diff
- 1. **Config F vs Config B** — Config F (Q25/G10-earnings/V30/M35) shows higher CAGR in standalone tests. Should Config B be replaced? BLOCKED: requires Historical Factor Warehouse V2 for proper OOS validation.
+ 1. **Config F vs Config B** — Fixed OOS comparison (RESEARCH-013-P0) now functions. Full V3 comparison shows:
+    - Config F (FULL): 9.23% CAGR, 0.49 Sharpe, +11.33% Alpha
+    - Config B (FULL): 7.49% CAGR, 0.41 Sharpe, +9.34% Alpha
+    - Config C (FULL): 18.31% CAGR, 0.77 Sharpe, +19.68% Alpha (momentum-heavy)
+    Config F outperforms B on V3 data but Config C dominates both.
+    See `reports/oos_weight_comparison_v3.md`. Decision pending ADR-005.
```

---

## PATCH 6: Section 10 — Open Question 7 (line 448)

**Classification:** OUTDATED

**Problem:** "RESEARCH-013: Is 46.33% CAGR robust?" — P0 foundation work completed.

**Action:**
```diff
- 7. **RESEARCH-013: Config B Robustness Validation** — Is 46.33% CAGR (2022-2025) robust? Survivorship bias? Universe bias? Regime dependence? See next research priority.
+ 7. **RESEARCH-013: Config B Robustness Validation** — P0 Foundation Recovery complete (2026-06-09). Baseline reproducibility rebuilt. OOS weight comparison fixed. Next: survivorship, bootstrap, regime analysis, concentration audit.
```

---

## PATCH 7: Section 5 — Failed Findings (line 265)

**Classification:** OUTDATED

**Problem:** "Weight Optimization (V8.4): PARTIALLY COMPLETE — Cannot optimize — missing historical factor scores." Now fixable via V3 warehouse.

**Action:**
```diff
- | Weight Optimization (V8.4) | PARTIALLY COMPLETE | Cannot optimize — missing historical factor scores |
+ | Weight Optimization (V8.4) | REPAIRED (RESEARCH-013-P0) | Fixed .get(key,50) bug. V3 warehouse now provides real factor scores. See oos_weight_comparison_v3.py |
```

---

## PATCH 8: Section 11 — Backlog (lines 476-479)

**Classification:** OUTDATED/COMPLETED

**Problem:** Three backlog items were completed by RESEARCH-013-P0.

**Action:**
```diff
- - [ ] RESEARCH-013: Config B Robustness Validation ...
- - [ ] Re-run OOS weight validation with real factor data
- - [ ] Config B vs Config F comparison on real historical data
+ - [x] RESEARCH-013-P0: Foundation Recovery — OOS bug fix, baseline rebuild, config truth (2026-06-09)
+ - [x] Re-run OOS weight validation with real factor data (see oos_weight_comparison_v3.py)
+ - [x] Config B vs Config F comparison on real historical data (see oos_weight_comparison_v3.md)
```

---

## PATCH 9: Section 7 — Lesson 6 (line 325)

**Classification:** MISLEADING

**Problem:** "Survivorship Bias inflates everything — Static universe CAGRs inflated by 40%." This number (40%) is from momentum-only backtests, not Config B multi-factor tests. Config B survivorship bias magnitude is unknown.

**Action:**
```diff
- 6. **Survivorship Bias inflates everything** — Static universe CAGRs inflated by 40%. Use dynamic universe.
+ 6. **Survivorship Bias inflates everything** — Momentum-only static universe CAGRs inflated by ~18-40%. Config B survivorship bias magnitude UNKNOWN — no Config B survivorship test has been run. Use dynamic universe.
```

---

## PATCH 10: Section 2.1 — "strongest validated production strategy" (line 67)

**Classification:** MISLEADING

**Problem:** The 46.33% CAGR / "strongest validated" claim at end of §2.1 refers to Config B (GATE-001), but the surrounding text describes production which runs Config F.

**Action:** Already covered by PATCH 3 above.

---

## PATCH 11: Chronology / Date (line 12)

**Classification:** OUTDATED

**Action:**
```diff
- **Generated:** 2026-06-08
+ **Generated:** 2026-06-09
```

---

## Patches Summary

| # | Location | Classification | Severity |
|---|----------|---------------|----------|
| 1 | RESEARCH-013A intro (lines 3-8) | UNVERIFIABLE | HIGH |
| 2 | §1 line 21, 28-29, 37 | FALSE | CRITICAL |
| 3 | §2.1 lines 52, 57-67 | FALSE / OUTDATED | CRITICAL |
| 4 | §8 line 354 | FALSE | HIGH |
| 5 | §10 Q1 line 442 | OUTDATED | MEDIUM |
| 6 | §10 Q7 line 448 | OUTDATED | MEDIUM |
| 7 | §5 line 265 | OUTDATED | LOW |
| 8 | §11 lines 476-479 | OUTDATED | MEDIUM |
| 9 | §7 lesson 6 line 325 | MISLEADING | MEDIUM |
| 10 | §2.1 line 67 | MISLEADING | HIGH |
| 11 | Date line 12 | OUTDATED | LOW |

---

## Files to Create/Delete

| Action | File |
|--------|------|
| DELETE | `docs/RESEARCH-013A_VERIFICATION.md` (original — unverifiable, replace with rebuilt version) |
| UPDATE | `docs/MASTER_CHRONICLE_V3.md` → V4 (apply all patches above) |
| UPDATE | `research/RESEARCH-013_P0_FOUNDATION_RECOVERY.md` (filled with OOS + 013A results) |
