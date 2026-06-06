# Architectural Decision Record (ADR)
## ADR-004: Suspension of Factor Weight Optimization Research

- **Status:** ACCEPTED
- **Author:** Antigravity AI
- **Deciders:** Indonesia Stock Intelligence (ISI) Quantitative Team
- **Date:** 2026-06-06
- **Supersedes:** ADR-003 (Alpha-Optimized Factor Weights — V7.0), partially
- **Blocking:** All factor-weight superiority claims pending Historical Factor Warehouse V2

---

## Context

Three sequential forensic audits completed on 2026-06-06 have established the
following findings with direct code-level evidence:

### Finding 1 — Historical factor scores do not exist

`snapshots/momentum_history/*.json` (89 files, 2019-01 → 2026-05) contains
only two fields per ticker per month:

```json
{"ticker": "ADRO.JK", "return_12m": 1.6678, "rank": 1}
```

The fields `quality_score`, `growth_score`, `value_score`, and `momentum_score`
are absent from every file in this directory.

`database/historical/factor_warehouse.csv` contains factor scores for exactly
two months: 2026-05 and 2026-06. No historical factor scores exist for any
period in the research window (2019–2025).

**Source:** `reports/oos_validation_forensic_audit.md`, `reports/v7_data_lineage_audit.md`

---

### Finding 2 — OOS optimization compared constant scores, not real factor data

`research/out_of_sample_validation.py` (lines 558–567) extracts factor scores
via:

```python
q  = item.get("quality_score",  item.get("quality",  50))
g  = item.get("growth_score",   item.get("growth",   50))
v  = item.get("value_score",    item.get("value",    50))
mo = item.get("momentum_score", item.get("momentum", 50))
item["_oos_score"] = weights["quality"]*q + weights["growth"]*g + \
                     weights["value"]*v + weights["momentum"]*mo
```

Because all four keys are absent from the snapshot files, every `.get()` call
returns the default value of **50**. The computed score collapses to:

```
_oos_score = 50 × (w_quality + w_growth + w_value + w_momentum)
           = 50 × 1.0
           = 50.0  (identical for every ticker, every month, every config)
```

Python's stable sort on tied scores preserves the original snapshot insertion
order (momentum rank). All five configurations select the same Top 5 portfolio
in every rebalance month.

**Source:** `reports/oos_validation_forensic_audit.md` — Q1 through Q6

---

### Finding 3 — Config A/B/C/D/E were never scientifically differentiated

The OOS validation report (`reports/out_of_sample_validation.md`) shows:

| Config | Quality | Growth | Value | Momentum | TRAIN Sharpe | VAL Sharpe |
|---|---|---|---|---|---|---|
| Config_A | 30% | 25% | 20% | 25% | 0.18 | −0.37 |
| Config_B | 25% | 30% | 10% | 35% | 0.18 | −0.37 |
| Config_C | 20% | 25% | 5% | 50% | 0.18 | −0.37 |
| Config_D | 40% | 25% | 10% | 25% | 0.18 | −0.37 |
| Config_E | 25% | 25% | 25% | 25% | 0.18 | −0.37 |

Sharpe ratios are identical across all five configurations. This is a
mathematical certainty — not statistical noise — resulting from the
constant-input mechanism described in Finding 2.

**Source:** `reports/out_of_sample_validation.md` Weight Configuration table

---

### Finding 4 — Chronicle V7 self-documents the problem

`master_chronicle.txt` (lines 749–759) explicitly states:

```
STATUS: UNDER REVIEW

Reason:
Framework optimisasi bobot tidak benar-benar melakukan
historical factor re-ranking karena snapshots historis
tidak mengandung factor-level scores.

Result:
Config B superiority remains unproven.
Current production weights may remain unchanged until
Historical Factor Warehouse V2 exists.
```

ADR-003 was accepted before this finding was documented. ADR-004 formalizes
the suspension and defines exit criteria.

---

## Decision

**All factor-weight superiority claims are hereby suspended and reclassified
as UNPROVEN pending the completion of Historical Factor Warehouse V2.**

The suspension applies to the following specific claims made in ADR-003
and Chronicle Bab 16:

| Claim | Previous Status | New Status |
|---|---|---|
| Config B CAGR 4.88% > Config A 2.92% | APPROVED | **UNPROVEN — source unverifiable** |
| Config B Sharpe > Config A, C, D, E | APPROVED | **CONTRADICTED — all configs identical** |
| Momentum contributes +23.29% alpha independently | Accepted | **PARTIALLY VALID — momentum backtest is real; attribution method unverified** |
| Growth contributes +22.66% alpha independently | Accepted | **UNVERIFIABLE — no historical growth scores exist** |
| Quality functions as a risk stabilizer | Accepted | **UNVERIFIABLE — no historical quality scores exist** |
| Value functions as an alpha drag | Accepted | **UNVERIFIABLE — no historical value scores exist** |
| Production migration to Config B is scientifically justified | APPROVED | **SUSPENDED — justification basis is invalid** |

---

## Rationale

A weight optimization framework requires three conditions to produce valid
scientific output:

1. **Historical factor scores must exist** for each ticker for each evaluation month.
2. **Re-ranking must occur** using the candidate weight vector applied to those scores.
3. **Portfolio returns must differ** between configurations to enable comparison.

None of these three conditions were met during V7 optimization:

1. ❌ Historical factor scores did not exist (Finding 1)
2. ❌ Re-ranking produced constant output (Finding 2)
3. ❌ All configs produced identical portfolios and identical Sharpe ratios (Finding 3)

The CAGR and alpha numbers cited in ADR-003 (Config B: 4.88%, Config A: 2.92%)
were produced by a source not preserved in the current codebase. They cannot
be attributed to a verified factor-level optimization run. Their origin is
unresolvable without the original execution context.

---

## What Remains Valid

Not all V7 research is invalidated. The following conclusions are grounded in
real data and remain accepted:

| Finding | Data Source | Status |
|---|---|---|
| Momentum factor generates positive alpha vs IHSG | `database/historical/momentum_monthly_returns.csv` (real live portfolio returns) | ✅ VALID |
| RS-6M (Factor 006) is an independent, non-redundant signal | `research/rs6m_backtest_engine.py` — real daily prices + IHSG | ✅ VALID |
| Foreign Flow proxy (Factor 005) is scientifically insufficient | Acknowledged proxy design — correctly parked | ✅ VALID |
| Survivorship bias inflated original CAGR by ~18pp | Dynamic universe remediation — real data | ✅ VALID |
| Headline OOS TRAIN/VALIDATION/TEST metrics | Sourced from real live portfolio `momentum_monthly_returns.csv` | ✅ VALID |

---

## Consequence

### Operational (what does NOT change)

Production continues operating on the current Config B weights
(Momentum 35%, Growth 30%, Quality 25%, Value 10%).

Rationale for continuance: Config B has not been proven *worse* than Config A —
it has been proven *incomparable*. Reverting to Config A would be equally
unsupported. The current production system generates real trades; disrupting
it without proven justification introduces operational risk.

**The production system is permitted to continue.**

### Research (what DOES change)

The following research claims are suspended and must not be cited as evidence
in future decisions until exit criteria are met:

- Config B is superior to Config A
- Weight configuration X produces Y% alpha attribution for factor Z
- Any claim derived from the ADR-003 optimization comparison table

The following documents are marked as dependent on suspended claims:

| Document | Affected Claims | Action Required |
|---|---|---|
| `docs/ADR-003-ALPHA-OPTIMIZED-WEIGHTS.md` | All evidence table entries | Mark as PENDING RE-VALIDATION |
| `master_chronicle.txt` Bab 16 | Config B findings, alpha attribution | Already marked UNDER REVIEW — retain that status |
| `reports/out_of_sample_validation.md` | Weight config comparison table | Valid for headline metrics; invalid for config comparison |

### No New Weight Changes Until Exit Criteria Are Met

No production weight change — in either direction — may be justified by
the V7 research cluster. Any future weight change requires a fresh optimization
run on Warehouse V2 data passing all exit criteria below.

---

## Exit Criteria

This ADR is resolved and claims may be reinstated when **all** of the following
are satisfied:

| # | Criterion | Owner | Current Status |
|---|---|---|---|
| 1 | Historical Factor Warehouse V2 is built, covering 2021-01 → present, for all 4 factors (quality, growth, value, momentum) per ticker per month | Engineering | ❌ Not started |
| 2 | Warehouse V2 data passes an independent point-in-time audit (no look-ahead contamination) | Research | ❌ Not started |
| 3 | `run_weighted_backtest()` is re-executed using Warehouse V2 as its snapshot source | Engineering | ❌ Not started |
| 4 | Config A/B/C/D/E produce **different** Sharpe ratios — confirming factor data differentiation is working | QA | ❌ Not started |
| 5 | The winning config is selected by highest VALIDATION Sharpe (not TRAIN) per the OOS framework rules | Research | ❌ Not started |
| 6 | A new ADR (ADR-005) is filed documenting the verified weight configuration | Architecture | ❌ Not started |

---

## Related Records

| ADR | Title | Relationship |
|---|---|---|
| ADR-002 | Data Source Standardization (YFinance) | Unaffected — data source decision is independent |
| ADR-003 | Alpha-Optimized Factor Weights (V7.0) | **Partially suspended** — Config B adoption basis is suspended; RS-6M and momentum findings remain |

## Related Reports

| Report | Role in This ADR |
|---|---|
| `reports/oos_validation_forensic_audit.md` | Primary evidence — Findings 1, 2, 3 |
| `reports/v7_data_lineage_audit.md` | Supporting evidence — full data lineage trace |
| `reports/historical_factor_v2_architecture_study.md` | Exit path — Option B architecture |
| `reports/fmp_point_in_time_audit.md` | Pre-condition for Warehouse V2 — FMP data integrity |
| `reports/factor_warehouse_v2_feasibility.md` | Pre-condition for Warehouse V2 — reconstruction feasibility |
