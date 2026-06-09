# AUDIT-CRITICAL-001: PRODUCTION REALITY AUDIT

**Date:** 2026-06-09
**Scope:** MASTER_CHRONICLE_V3 claims vs actual production code
**Severity:** CRITICAL
**Status:** COMPLETED

---

## Executive Summary

This audit compares **what the system claims** (per MASTER_CHRONICLE_V3.md) against **what the system actually does** (per code, config files, git history, and research artifacts). It covers 5 sequential investigations.

**Bottom Line:** The chronicle is a work of fiction in 3 out of 5 critical claims. Production does NOT run Config B, the OOS framework has never performed a valid weight comparison, the sole evidence for RESEARCH-013A is circular and unverifiable, and zero survivorship reports tested the actual production strategy.

---

## Step 1 — Weight Call Stack: Config B vs Config F

### Claim (Chronicle §2.1)
> "Config B (Q25/G30/V10/M35) — PRODUCTION — Locked. Do not modify weights."

### Reality

| Component | Quality | Growth | Value | Momentum | Config |
|-----------|---------|--------|-------|----------|--------|
| `config/scoring_weights.json` | **0.25** | **0.10** | **0.30** | **0.35** | **F** |
| `scoring/final_score_v3.py` (reads config) | **0.25** | **0.10** | **0.30** | **0.35** | **F** |
| `scoring/final_score_v3.py` (fallback) | 0.25 | 0.30 | 0.10 | 0.35 | B |
| `scripts/generate_turnaround_watchlist.py:224` (hardcoded) | **0.25** | **0.30** | **0.10** | **0.35** | **B** |
| Dashboard title (cosmetic, line 325) | Q25 | G30 | V10 | M35 | B |

**Finding CRIT-001:** The production monthly pipeline (`final_score_v3.py`) reads `config/scoring_weights.json` at runtime and uses **Config F** (Q25/G10/V30/M35). The chronicle claims Config B (Q25/G30/V10/M35) is production. The Growth and Value weights are **swapped**.

**Finding CRIT-002:** Git history shows `config/scoring_weights.json` was set to Config B on 2026-06-01 (commit `996bc05`), then silently changed to Config F on 2026-06-07 (commit `c635b1f` — "BAB 22: Update Config to Config F"). This change occurred **after** ADR-004 (2026-06-06) which explicitly stated "Production continues operating on the current Config B weights" and "No production weight change without exit criteria."

**Finding CRIT-003:** The daily dashboard leaderboard (`generate_turnaround_watchlist.py`) hardcodes Config B weights. This means:
- Monthly scoring → Config F (different rankings)
- Daily dashboard → Config B (different rankings)
- The two systems produce **different scores** for the same tickers

**Finding CRIT-004:** Chronicle §8 (Architecture) labels `final_score_v3.py` as "Config B composite (Q25/G30/V10/M35)" — but the file loads whatever weights are in `config/scoring_weights.json`, which is Config F.

**Verdict:** ❌ CHRONICLE FALSE — Production runs Config F, not Config B. Config change violated ADR-004.

---

## Step 2 — OOS Validation Forensic

### Claim (ADR-003, cited in Chronicle)
> "Config B outperforms Config A: CAGR 4.88% vs 2.92%. Alpha +2.31%."

### Reality

The OOS framework in `research/out_of_sample_validation.py:558-561` reads scores from `snapshots/momentum_history/*.json` which contain **only** `{"ticker": "...", "return_12m": ..., "rank": ...}`. None of the four factor score keys exist:

```python
q  = item.get("quality_score",  item.get("quality",  50))   # → 50
g  = item.get("growth_score",   item.get("growth",   50))   # → 50
v  = item.get("value_score",    item.get("value",    50))   # → 50
mo = item.get("momentum_score", item.get("momentum", 50))   # → 50
```

Every ticker scores `50 × (w_q + w_g + w_v + w_mo) = 50.0`. Python's stable sort preserves original insertion order (momentum rank). **All five configs (A/B/C/D/E) select identical Top 5 every month.**

The headline TRAIN/VALIDATION/TEST Sharpe ratios (0.18 / −0.37 / 0.02) come from real `momentum_monthly_returns.csv` data — but the Config A/B/C/D/E comparison table is entirely fabricated by the constant fallback.

**Finding CRIT-005:** The OOS framework has **never performed a real multi-factor weight comparison**. Config B's claimed superiority over Config A (CAGR 4.88% vs 2.92%) is unproven by the framework that supposedly produced it.

**Finding CRIT-006:** Later V3 warehouse tests (2026-06-06, `FINAL_WEIGHT_DECISION.md`) independently validated Config B (11/12 windows, p=0.0002 vs A). This **vindicates Config B post-hoc** but does not fix the broken OOS framework.

**Verdict:** ❌ OOS FRAMEWORK BROKEN — But Config B is independently vindicated by later V3 tests.

---

## Step 3 — RESEARCH-013A Evidence Audit

### Claim (Chronicle §3, RESEARCH-013A_VERIFICATION.md)
> "CAGR diff 0.11%, Sharpe diff 0.70%, Alpha diff 0.14% — PASS. Baseline is reproducible."

### Evidence Artifacts Searched

| Artifact | Found? | Location |
|----------|--------|----------|
| `audits/baseline_reproducibility.py` | **NO** | File never existed in any git commit |
| CSV output with "reproducib" or "research_013" | **NO** | No matching files anywhere in repo |
| Log/notebook/cache with CAGR/Sharpe/Alpha diffs | **NO** | Numbers appear only in circular self-referencing docs |
| Git history for `audits/baseline_reproducibility.py` | **NO** | Zero commits matching this path |
| Independent source for numbers 0.11, 0.70, 0.14 | **NO** | Only in RESEARCH-013A_VERIFICATION.md and MASTER_CHRONICLE_V3 (which cites it) |

**Finding CRIT-007:** The verification document claims execution via `python -m audits.baseline_reproducibility` referencing absolute paths on the author's machine. But this file **has never existed in the repository** — not on disk, not in git history (all branches). No CSV output, log file, or notebook contains these numbers.

**Finding CRIT-008:** The "baseline" it claims to reproduce (46.33% CAGR, 1.43 Sharpe, 49.03% Alpha) comes from GATE-001 in RESEARCH-012, which used Config B weights. But the production config file was changed to Config F on June 7 — so even if RESEARCH-013A were valid, it verified Config B numbers that are no longer the production weights.

**Verdict:** ❌ UNVERIFIABLE — The claimed verification script never existed. The numbers are circular self-reference. RESEARCH-013A should be reclassified as UNCONFIRMED.

---

## Step 4 — Survivorship Report Relevance Audit

### Claim (Chronicle §7 point 6)
> "Survivorship Bias inflates everything — Static universe CAGRs inflated by 40%. Use dynamic universe."

### Reality

The chronicle correctly acknowledges survivorship bias but the claimed "18-40% inflation" numbers are from **momentum-only** backtests, not Config B multi-factor tests.

| Report | Strategy | Universe | Config B? | Applicable? |
|--------|----------|----------|-----------|-------------|
| survivorship_audit.md | Momentum RS-6M Top 5 | Static→Dynamic IDX30 | NO | Partial — infrastructure only |
| survivorship_remediation.md | Momentum (IPO gate fix) | IDX30 | NO | Partial — IPO filtering method |
| survivorship_impact_analysis.md | Momentum V6.2.2→V6.2.3 | Static→Dynamic | NO | Momentum-specific CAGR inflation |
| survivorship_remediation_plan.md | RS-6M standalone | Dynamic IDX30 | NO | Infrastructure yes, metrics no |
| universe_change_analysis.md | None (universe diff) | Dynamic IDX30 | NO | Methodology-neutral |
| v7_data_lineage_audit.md | **Config B directly** | Dynamic IDX30 | **YES** | Found Config B superiority UNPROVEN |

**Finding CRIT-009:** Zero survivorship reports tested the actual Config B strategy. All bias numbers (18.25% CAGR inflation, 41.28%→1.21%) are momentum-specific. The multi-factor Config B would likely have different survivorship magnitude, but no Config B survivorship test has ever been run.

**Finding CRIT-010:** The only report that directly touches Config B (`v7_data_lineage_audit.md`) concluded that Config B superiority is UNPROVEN due to the constant-50 bug (same Finding CRIT-005).

**Verdict:** ⚠️ CHRONICLE PARTIALLY TRUE — Bias is acknowledged, but all cited numbers are momentum-only. Config B survivorship bias magnitude is UNKNOWN.

---

## Step 5 — Chronicle Integrity Audit

### Claim-by-Claim Comparison

| Chronicle Claim | Location | Reality | Verdict |
|----------------|----------|---------|---------|
| "Config B (Q25/G30/V10/M35) PRODUCTION — Locked" | §1 line 37 | Config F (Q25/G10/V30/M35) since June 7 | ❌ FALSE |
| "Config B weights: Q25/G30/V10/M35" | §2.1 line 52 | Config file has Q25/G10/V30/M35 | ❌ FALSE |
| "Final_score_v3.py = Config B composite" | §8 line 354 | Reads config → Config F at runtime | ❌ FALSE |
| "CAGR 46.33%, Sharpe 1.43, Alpha 49.03%" | §3 line 174 | From RESEARCH-012 GATE-001, Config B | ❌ NOT PRODUCTION |
| "Key Backtest Results CAGR 0.82% (88mo)" | §2.1 line 58 | Momentum-only survivorship data, not Config B | ❌ MISLEADING |
| "RESEARCH-013A PASS" | §3 line 3 | Script never existed; numbers circular | ❌ UNVERIFIABLE |
| "Survivorship bias inflates everything" | §7 line 325 | Correct sentiment, but all numbers momentum-only | ⚠️ PARTIAL |
| "No production strategy changes" | §1 line 28 | Config was changed June 7 without ADR | ❌ VIOLATED |
| "ADR-004 suspends weight superiority claims" | §2.1 line 64 | Correct — but ignores that Config itself changed | ❌ INCONSISTENT |
| "Config F vs Config B — OPEN QUESTION" | §10 line 442 | Acknowledged as open — but already deployed! | ❌ CONTRADICTED |

### Timeline of Config Change (Git Evidence)

```
2026-06-01  ADR-003 approved. Config B weights deployed. (996bc05)
2026-06-06  ADR-004 accepted. "Config B remains production. No changes."
2026-06-07  Silent config change to Config F. (c635b1f)
2026-06-08  MASTER_CHRONICLE_V3 generated — still claims Config B.
```

### Gap Analysis

| Gap | Impact | Severity |
|-----|--------|----------|
| Production weights ≠ documented weights | Portfolio scores differ. Any backtest using Config B weights does NOT reflect production. | **CRITICAL** |
| Config change violated ADR-004 | ADR-004 exit criteria (Historical Factor Warehouse V2, re-validation) not met. Improper governance. | **HIGH** |
| Daily dashboard uses different weights than monthly pipeline | Dashboard leaders use Config B; monthly scoring uses Config F. Two different rankings coexist. | **HIGH** |
| RESEARCH-013A unverifiable | Robustness baseline claim has zero supporting evidence. | **HIGH** |
| Survivorship bias magnitude unknown for Config B | Cannot quantify how much of 46.33% CAGR is survivorship-inflated. | **MEDIUM** |
| Chronicle claims Config B locked but it was changed | Documentation integrity failure. | **HIGH** |

**Verdict:** ❌ CHRONICLE INTEGRITY FAILED — 5 of 9 key claims are false or misleading.

---

## Consolidated Verdict

| Investigation | Result | Confidence |
|---------------|--------|------------|
| Step 1: Weight call stack | Config F in production, not Config B. Dashboard uses Config B. Two different weight systems. | **HIGH** (code + git) |
| Step 2: OOS validation | Framework structurally broken (.get(key,50)). Config B vindicated post-hoc by V3 data. | **HIGH** (code) |
| Step 3: RESEARCH-013A | Unverifiable. Script never existed. Numbers are circular. | **HIGH** (git) |
| Step 4: Survivorship reports | Zero tested Config B. All bias numbers are momentum-only. | **HIGH** (file analysis) |
| Step 5: Chronicle integrity | 5/9 claims false. Config change violated ADR-004. | **HIGH** (code + git) |

## Immediate Action Items

1. **Decide: Config B or Config F?** The current state is an accidental hybrid. Choose one set of weights and make both the config file and the chronicle consistent. Update `generate_turnaround_watchlist.py` to read from config instead of hardcoding.

2. **Open ADR-005** documenting the weight decision, whether to revert to Config B or formalize Config F as production.

3. **Delete RESEARCH-013A_VERIFICATION.md** or reclassify as UNVERIFIABLE/UNCONFIRMED. The script never existed.

4. **Update MASTER_CHRONICLE_V3.md** to reflect actual production weights. Correct or remove all false claims identified in Step 5.

5. **Run a Config B survivorship test** if Config B is chosen. Otherwise, run a Config F survivorship test. The current bias estimates are all from momentum-only backtests.

6. **Fix `generate_turnaround_watchlist.py`** to read weights from `config/scoring_weights.json` instead of hardcoding, so the dashboard always matches the pipeline.

7. **Fix or deprecate `research/out_of_sample_validation.py`** — its .get(key,50) bug renders the weight comparison section inert.
