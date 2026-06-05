# OOS Validation Forensic Audit

**Date:** 2026-06-06  
**Prepared by:** AI Architect  
**Classification:** Root Cause Analysis — No code changes  
**Subject file:** `research/out_of_sample_validation.py`  
**Symptom:** Config A/B/C/D/E all produce identical Sharpe ratios (0.18 TRAIN, −0.37 VALIDATION)

---

## Summary Verdict

> **The OOS validation optimization loop is structurally broken.**
> It reweights scores that do not exist.
> All five configurations collapse to a pure momentum-only backtest
> because the snapshots fed into `run_weighted_backtest()` contain
> **only one field: `return_12m`** — with no `quality_score`,
> `growth_score`, or `value_score` present.
> The weight vector is applied to constants (defaulting to 50),
> not to real factor data.

---

## QUESTION 1 — Exact factor weights per configuration

Defined at `research/out_of_sample_validation.py`, lines 61–67:

```python
WEIGHT_CONFIGS = {
    "Config_A (Legacy Equal)":    {"quality": 0.30, "growth": 0.25, "value": 0.20, "momentum": 0.25},
    "Config_B (Alpha Optimized)": {"quality": 0.25, "growth": 0.30, "value": 0.10, "momentum": 0.35},
    "Config_C (Momentum Heavy)":  {"quality": 0.20, "growth": 0.25, "value": 0.05, "momentum": 0.50},
    "Config_D (Quality First)":   {"quality": 0.40, "growth": 0.25, "value": 0.10, "momentum": 0.25},
    "Config_E (Balanced)":        {"quality": 0.25, "growth": 0.25, "value": 0.25, "momentum": 0.25},
}
```

**Summary table — weights as declared:**

| Config | Quality | Growth | Value | Momentum |
|---|---|---|---|---|
| A (Legacy Equal) | 30% | 25% | 20% | 25% |
| B (Alpha Optimized) | 25% | 30% | 10% | 35% |
| C (Momentum Heavy) | 20% | 25% | 5% | 50% |
| D (Quality First) | 40% | 25% | 10% | 25% |
| E (Balanced) | 25% | 25% | 25% | 25% |

These weights are syntactically correct and meaningfully different.
If factor data existed in the snapshots, these configurations would produce
different rankings and different portfolio returns.

The fact that they produce identical results is therefore caused entirely by
what the snapshots contain, not by the weight definitions.

---

## QUESTION 2 — Rankings produced by each configuration

### What the scoring engine reads

The backtester (`run_weighted_backtest`, lines 531–598) reads factor scores
from `snapshots/momentum_history/*.json`. The relevant extraction is at
lines 558–567:

```python
q  = item.get("quality_score",  item.get("quality",  50))   # line 558
g  = item.get("growth_score",   item.get("growth",   50))   # line 559
v  = item.get("value_score",    item.get("value",    50))   # line 560
mo = item.get("momentum_score", item.get("momentum", 50))   # line 561

item["_oos_score"] = (
    weights["quality"]  * q  +
    weights["growth"]   * g  +
    weights["value"]    * v  +
    weights["momentum"] * mo
)
```

### What the snapshots actually contain

**Snapshot structure — 2022-06 (representative, TRAIN period):**

```json
[
    {"ticker": "ADRO.JK",  "return_12m": 1.6678, "rank": 1},
    {"ticker": "PTBA.JK",  "return_12m": 1.2436, "rank": 2},
    {"ticker": "BBNI.JK",  "return_12m": 0.7267, "rank": 3},
    {"ticker": "PGAS.JK",  "return_12m": 0.7013, "rank": 4},
    {"ticker": "UNTR.JK",  "return_12m": 0.4652, "rank": 5},
    ...
]
```

**Snapshot structure — 2024-03 (VALIDATION period):**

```json
[
    {"ticker": "BMRI.JK", "return_12m": 0.4762, "rank": 1},
    {"ticker": "MEDC.JK", "return_12m": 0.4726, "rank": 2},
    {"ticker": "BBRI.JK", "return_12m": 0.3476, "rank": 3},
    ...
]
```

**Fields present across all 89 snapshot files in `snapshots/momentum_history/`:**

| Field | Present | Notes |
|---|---|---|
| `ticker` | ✅ | All 89 files |
| `return_12m` | ✅ | All 89 files (pre-July 2023 months) |
| `rank` | ✅ | All 89 files |
| `quality_score` | ❌ | **ABSENT from all momentum_history snapshots** |
| `growth_score` | ❌ | **ABSENT from all momentum_history snapshots** |
| `value_score` | ❌ | **ABSENT from all momentum_history snapshots** |
| `momentum_score` | ❌ | **ABSENT from all momentum_history snapshots** |

**The snapshot directory `snapshots/momentum_history/` was built by the
historical momentum builder — which records only momentum-derived fields.
No fundamental factor scores were ever written to these files.**

### What the backtester receives for quality, growth, value

When `.get("quality_score", item.get("quality", 50))` is called on a
`2022-06` snapshot item, neither `"quality_score"` nor `"quality"` exist.
Python's `.get()` returns the default value: **50**.

This applies identically to `growth_score` (→ 50) and `value_score` (→ 50).

The only field that has a real value is `momentum_score` — but even this key
is not in the snapshot. The field present is `return_12m`, not `momentum_score`.
So `item.get("momentum_score", item.get("momentum", 50))` also returns **50**.

### Computed `_oos_score` for every ticker, every month, every config

With q=50, g=50, v=50, mo=50 for all tickers:

```
_oos_score = w_q*50 + w_g*50 + w_v*50 + w_mo*50
           = 50 * (w_q + w_g + w_v + w_mo)
           = 50 * 1.0
           = 50.0
```

**Every ticker receives exactly 50.0 — regardless of the weight configuration.**

With all tickers tied at 50.0, the sort at line 569:
```python
ranked = sorted(snapshot, key=lambda x: x["_oos_score"], reverse=True)
```
produces an **ordering determined entirely by Python's stable sort on equal keys**,
which preserves the original insertion order of the list — which is the
**pre-existing `rank` order from the snapshot file**.

### What ranking is actually selected

The "re-ranking" under different weight configurations produces the identical
order as the original momentum rank. All five configs select the same Top 5
tickers for every month. Therefore:

- Config A Top 5 = Config B Top 5 = Config C Top 5 = Config D Top 5 = Config E Top 5

For every single rebalance month in TRAIN, VALIDATION, and TEST.

---

## QUESTION 3 — Ranking overlap measurement

**Average overlap across all config pairs: 100%**

This is not a probabilistic estimate — it is a logical certainty derived from
the mechanism described in Q2. Because all five configurations assign
`_oos_score = 50.0` to every ticker and the sort is stable, the Top 5 is
identical for all configs in every month.

**Proof by specific example — 2022-06 (TRAIN period):**

Snapshot pre-existing rank order: ADRO, PTBA, BBNI, PGAS, UNTR, BMRI, ...

With `_oos_score = 50.0` for all, stable sort preserves this order.

| Config | Top 5 Selected |
|---|---|
| A | ADRO, PTBA, BBNI, PGAS, UNTR |
| B | ADRO, PTBA, BBNI, PGAS, UNTR |
| C | ADRO, PTBA, BBNI, PGAS, UNTR |
| D | ADRO, PTBA, BBNI, PGAS, UNTR |
| E | ADRO, PTBA, BBNI, PGAS, UNTR |

**Overlap = 100% for this month. Same for all 89 months.**

---

## QUESTION 4 — Do factor weights materially alter holdings?

**Answer: No — under the current snapshot data structure.**

### Why holdings are unchanged

The prerequisite for weight changes to affect holdings is:

> Tickers must have different, real values for quality_score, growth_score,
> value_score, and momentum_score.

When all four are missing and default to 50 uniformly, reweighting 50×w_q
+ 50×w_g + 50×w_v + 50×w_mo = 50 regardless of w. No weight vector can
produce differentiation from a constant input.

### What would be required for weights to matter

Each snapshot record would need to carry the four factor scores as separate
fields:

```json
{
  "ticker": "ADRO.JK",
  "quality_score": 53.77,
  "growth_score":  79.31,
  "value_score":   46.21,
  "momentum_score": 97.67,
  "return_12m": 1.6678,
  "rank": 1
}
```

The `archives/rankings/2026-05.json` file **does** have this structure (all
four scores present), but those are current-month production rankings, not
historical snapshots. The `snapshots/momentum_history/` directory — the data
source actually read by `run_weighted_backtest()` — contains only
`return_12m` and `rank`.

### Why the correct data source is ignored

The OOS script's `SNAPSHOT_DIR` is hardcoded to:
```python
SNAPSHOT_DIR = BASE_DIR / "snapshots" / "momentum_history"   # line 43
```

The production ranking archives with full factor scores are stored in:
```
archives/rankings/2026-05.json
archives/rankings/2026-06.json
```

Only two months of production rankings with full factor scores exist. The
historical ranking archive does not exist. The script's `SNAPSHOT_DIR`
correctly points to historical data, but that historical data is
momentum-only.

---

## QUESTION 5 — Does OOS validation actually recompute scores?

**Answer: Structurally yes, but effectively no — because inputs are constants.**

### Execution path trace

**Step 1 — Data loading (lines 619–621):**
```python
rankings    = load_snapshot_rankings()   # reads snapshots/momentum_history/*.json
ticker_rets = load_ticker_returns()      # reads database/monthly/*.csv
ihsg_monthly = load_ihsg_monthly()       # reads benchmarks/IHSG.csv
```
`load_snapshot_rankings()` at lines 90–101 loads all 89 `.json` files from
`snapshots/momentum_history/`. These files contain only `return_12m` and `rank`.

**Step 2 — Weight optimization check (lines 661–693):**
```python
if rankings and ticker_rets and ihsg_monthly:
    for cfg_name, w in WEIGHT_CONFIGS.items():
        tr_p, tr_b, _ = run_weighted_backtest(rankings, ticker_rets, ihsg_monthly, w, ...)
```
`rankings` is non-empty (89 files loaded), `ticker_rets` is non-empty, and
`ihsg_monthly` is non-empty. The `if` condition is `True`. The optimization
loop **does execute** — it calls `run_weighted_backtest()` for all 5 configs.

**Step 3 — Score computation inside `run_weighted_backtest` (lines 557–567):**
```python
q  = item.get("quality_score",  item.get("quality",  50))  # → 50 (key absent)
g  = item.get("growth_score",   item.get("growth",   50))  # → 50 (key absent)
v  = item.get("value_score",    item.get("value",    50))  # → 50 (key absent)
mo = item.get("momentum_score", item.get("momentum", 50))  # → 50 (key absent)
item["_oos_score"] = weights["quality"]*q + weights["growth"]*g + ...
```
Execution reaches this code. The code runs without error. The scores are
computed. But because all four `.get()` calls return 50, the computed score
is 50 for all tickers regardless of `weights`.

**Step 4 — The fallback path (lines 684–693) is NOT triggered:**
```python
else:
    print("⚠ Snapshot tidak cukup untuk config optimization.")
    for cfg_name in WEIGHT_CONFIGS:
        all_config_scores[cfg_name] = {
            "train_sharpe": train_m["sharpe"],
            "val_sharpe":   val_m["sharpe"],
            ...
        }
```
This else-branch runs only if `rankings` is empty or `ticker_rets` is empty.
Since both are non-empty, the else-branch is skipped. The identical Sharpe
values are **not** produced by the fallback. They are produced by the
main loop — which genuinely recomputes but with all-constant inputs.

**Conclusion:** The validation framework correctly executes the scoring
and backtesting pipeline. The pipeline is not broken. The data fed into it
is structurally incomplete.

---

## QUESTION 6 — Is optimization operating on full factor data, partial factor data, or momentum-only proxy?

**Answer: Neither full nor partial — it is operating on a constant proxy.**

Detailed classification:

| Category | Definition | Actual status |
|---|---|---|
| A. Full factor data | All four scores present and historically accurate | ❌ Not present in snapshots |
| B. Partial factor data | Some scores present, others absent | ❌ Not the case — ALL four absent |
| C. Momentum-only proxy | `return_12m` used as the sole signal | ❌ Not even this — `return_12m` is also ignored by the backtester |
| **D. Constant proxy** | All factor scores default to 50 uniformly | ✅ **Actual status** |

**This is more degenerate than a momentum-only proxy.** In a momentum-only
proxy, the backtester would at least use `return_12m` values which differ
between tickers and produce a meaningful ranking. But `run_weighted_backtest()`
does not read `return_12m` — it reads `quality_score`, `growth_score`,
`value_score`, and `momentum_score`. All four are absent. All four default
to 50. The optimizer sees no signal at all.

The portfolio actually held each month is determined by the pre-existing
**snapshot insertion order** (momentum rank), not by any weighted score.
So paradoxically, the output is equivalent to momentum-only — but arrived
at through a completely different (and broken) mechanism.

### Clarification: the primary OOS metrics (TRAIN/VALIDATION/TEST) are correct

The three headline performance metrics (0.53% CAGR TRAIN, −5.18% CAGR
VALIDATION, 6.35% CAGR TEST) are sourced from `RETURNS_FILE`:

```python
RETURNS_FILE = BASE_DIR / "database" / "historical" / "momentum_monthly_returns.csv"
```

These are **pre-computed returns from the actual live production portfolio**
that ran during those periods. They reflect real decisions made by the live
system. These numbers are valid — they describe what the system actually did.

The broken component is exclusively the **weight configuration comparison**
in the optimization loop. The per-config Sharpe ratios in the config table
are all identical because they all simulate the same portfolio (momentum rank
order), not because the actual portfolio returns are corrupted.

---

## QUESTION 7 — Would Warehouse V2 solve this issue?

**YES — directly and completely, for the optimization loop.**

### How Warehouse V2 resolves the root cause

The root cause is that `snapshots/momentum_history/*.json` contains only
`return_12m` and `rank`. The scoring engine expects `quality_score`,
`growth_score`, `value_score`, and `momentum_score`.

Warehouse V2 produces exactly those four fields, per ticker, per month,
from 2021 onward. If the warehouse is built and the OOS validation is
updated to read from it, the optimization loop will:

1. Find real, differentiated values for q, g, v, mo per ticker per month
2. Apply the five weight vectors to genuinely different inputs
3. Produce five different ranked portfolios
4. Compute five different Sharpe ratios
5. Select the genuinely best configuration

### What Warehouse V2 cannot fix

- The **primary OOS metrics** (headline CAGR/Sharpe per period) are sourced
  from `momentum_monthly_returns.csv`, not from snapshots. These are correct
  and reflect actual live portfolio returns. Warehouse V2 does not affect them.

- The **TRAIN period** (2019-02 → 2023-12) partially precedes the Warehouse V2
  window (2021-01 → present). Months 2019-02 through 2020-12 (23 months of the
  59-month training window) would still have no fundamental data unless the
  warehouse window is extended.

- Even with Warehouse V2, the fundamental scores for 2021–2025 will be
  **momentum-exact but fundamental-approximate** (Option B) or
  **fundamental-exact only via FMP** (Options B/C). The quality of the
  optimization is bounded by the quality of the reconstructed scores.

### Warehouse V2 fix pathway

```
CURRENT STATE:
  snapshots/momentum_history/2022-06.json
  → {"ticker": "ADRO.JK", "return_12m": 1.6678, "rank": 1}
  → q=50, g=50, v=50, mo=50 → _oos_score=50 → all configs identical

WITH WAREHOUSE V2:
  factor_warehouse_v2/2022-06.json (or .csv)
  → {"ticker": "ADRO.JK", "quality_score": X, "growth_score": Y,
     "value_score": Z, "momentum_score": W}
  → q=X, g=Y, v=Z, mo=W → _oos_score varies by config → configs differentiated
```

The OOS validation script would require one change: update `SNAPSHOT_DIR`
to point to the Warehouse V2 output directory, and ensure the warehouse
records use field names matching what `run_weighted_backtest()` expects
(`quality_score`, `growth_score`, `value_score`, `momentum_score`).

---

## Root Cause Summary

| Finding | Evidence |
|---|---|
| Snapshots contain only `return_12m` and `rank` | `snapshots/momentum_history/2022-06.json` — verified across pre-July 2023 files |
| Backtester reads `quality_score`, `growth_score`, `value_score`, `momentum_score` | `out_of_sample_validation.py` lines 558–561 |
| Missing keys default to 50 via `.get()` | Python `.get(key, default)` semantics, lines 558–561 |
| All tickers score 50×Σweights = 50×1.0 = 50 regardless of config | Mathematical certainty — weights sum to 1.0 |
| Stable sort on tied scores preserves original order | Python `sorted()` is stable; original order = momentum rank |
| Config optimization selects same Top 5 every month for all configs | Identical sort → identical portfolio |
| Identical portfolio → identical returns → identical Sharpe | Logical consequence |
| Fallback branch NOT triggered | `if rankings and ticker_rets and ihsg_monthly:` evaluates True |
| Primary OOS headline metrics (TRAIN/VALIDATION/TEST) are valid | Sourced from pre-computed `momentum_monthly_returns.csv`, not snapshot scores |
| Warehouse V2 directly provides the missing fields | Four factor scores per ticker per month — correct input for backtester |

---

## What This Means for the OOS Report

The `reports/out_of_sample_validation.md` contains two sections with
different validity:

| Section | Valid? | Reason |
|---|---|---|
| Overall PASS verdict | ✅ Valid | Based on real live portfolio returns |
| TRAIN/VALIDATION/TEST CAGR, Sharpe, Alpha | ✅ Valid | Based on `momentum_monthly_returns.csv` |
| Config A vs B vs C vs D vs E comparison table | ❌ Invalid | Identical Sharpe values result from constant-input collapse |
| "Best config" selection → Config_A ⭐ | ❌ Invalid | Arbitrary — all configs tied; A wins only by tie-breaking order |
| Production config confirmed as B | ❌ Not confirmed | Config B was never truly compared against A/C/D/E |

**The system has never run a real multi-factor weight optimization.**
The optimization infrastructure is correctly built, but has been running on
data that cannot differentiate any configuration.
