# V7 Alpha Optimization Data Lineage Audit

**Date:** 2026-06-06  
**Prepared by:** AI Architect  
**Classification:** Root Cause Analysis — No code changes  
**Subject:** V7.0 Alpha Optimized Weights — ADR-003, Chronicle Bab 16  
**Final Verdict:** See Section 5

---

## Background

The master chronicle (Bab 16) documents that V7 concluded:

> *"Momentum: Faktor dengan kontribusi Alpha terbesar (+23.29% secara mandiri).
> Growth: Faktor kedua terbaik (+22.66% secara mandiri)."*

And subsequently approved migrating production weights to Config B:
> *"Momentum 35%, Growth 30%, Quality 25%, Value 10%"*

This audit traces what data actually fed that conclusion.

---

## QUESTION 1 — What exact files were used?

### Source files reconstructed from code trace

V7's Alpha Optimization involved at minimum three distinct research components.
Each is traced separately.

---

### Component 1: Weight Configuration Comparison (OOS Validation)

**Script:** `research/out_of_sample_validation.py`  
**Data source read at runtime (line 43):**
```python
SNAPSHOT_DIR = BASE_DIR / "snapshots" / "momentum_history"
```

**Actual files loaded:**
```
snapshots/momentum_history/2019-01.json  through  2026-05.json
(89 files, each ~2,683–2,809 bytes)
```

**Structure of each file (verified via 2022-06.json and 2024-03.json):**
```json
[
    {"ticker": "ADRO.JK", "return_12m": 1.6678, "rank": 1},
    {"ticker": "PTBA.JK", "return_12m": 1.2436, "rank": 2},
    ...
]
```

**Fields NOT present:** `quality_score`, `growth_score`, `value_score`, `momentum_score`

**Pre-computed returns file (line 39):**
```python
RETURNS_FILE = BASE_DIR / "database" / "historical" / "momentum_monthly_returns.csv"
```
This file stores the actual live portfolio returns from the production system.
It is used for the headline TRAIN/VALIDATION/TEST metrics — not for re-ranking.

---

### Component 2: Counterfactual Factor Portfolio Simulation

**Chronicle Bab 16 states:**
> *"Analisis Alpha Attribution selesai dilakukan dengan mensimulasikan
> counterfactual factor portfolios."*
> *"Momentum: +23.29% secara mandiri. Growth: +22.66% secara mandiri."*

No dedicated script in the `research/` directory was found that simulates
counterfactual single-factor portfolios for Quality, Growth, Value, or Momentum
independently. The existing `research/compare_backtests.py` compares bias
remediation deltas (V6.2.2 vs V6.2.3), not factor portfolios.

**Possible source:** These numbers may have been computed by a temporary
script that was not preserved in the repository, or they may have been
analytically derived from `momentum_monthly_returns.csv` without a dedicated file.

**Actual factor-level input available for this analysis:**  
None in the historical window. The `database/historical/factor_warehouse.csv`
contains factor scores only for 2026-05 and 2026-06 (2 months).

---

### Component 3: RS-6M Backtest (Factor 006)

**Script:** `research/rs6m_backtest_engine.py`  
**Data sources used (confirmed from code):**

| File | Purpose | Valid? |
|---|---|---|
| `output/history_prices/*.csv` (64 tickers) | Daily prices for RS computation | ✅ Real data |
| `benchmarks/ihsg.csv` | IHSG daily prices for RS excess return | ✅ Real data |
| `database/historical/ticker_metadata.csv` | Listing dates for IPO gate | ✅ Real data |
| `database/historical/historical_universe/` | Active IDX30 per month | ✅ Real data |
| `database/historical/momentum_monthly_returns.csv` | Momentum baseline comparison | ✅ Real data |

**This component — Factor 006 RS-6M — is the only component of the V7 research
cluster that used genuinely independent real data.** Its CAGR 41.28% (before
survivorship bias remediation) and later corrected to 1.21% after remediation
are both derived from actual price history.

---

### Summary: Files Used in V7

| Component | Files Used | Factor Scores? |
|---|---|---|
| Weight config comparison (OOS) | `snapshots/momentum_history/*.json` | ❌ Absent — `return_12m` and `rank` only |
| Counterfactual factor portfolios | Unknown/undiscoverable | ❌ No historical factor scores exist |
| RS-6M backtest (Factor 006) | Daily prices, IHSG, metadata, universe | N/A (price-based, not factor-based) |
| Factor warehouse (any period) | `database/historical/factor_warehouse.csv` | ⚠️ 2026-05 and 2026-06 only (2 months) |

---

## QUESTION 2 — Were factor scores available?

**Answer: No — not for any historical period used in V7 optimization.**

### Evidence

**`database/historical/factor_warehouse.csv`** — the only file in the repository
that stores multi-factor scores — contains exactly **2 months** of data:

```
date,ticker,quality_score,value_score,momentum_score,growth_score,final_score
2026-05,SIDO.JK,82.3,49.31,53.33,1.73,48.32
2026-05,BBCA.JK,80.35,36.55,47.5,36.21,52.34
...
2026-06,SIDO.JK,82.3,49.31,31.33,1.73,36.99
...
```

These 2 months (2026-05 and 2026-06) are **post-V7**. They are current production
snapshots, not historical data. They did not exist when V7 was executed.

**`snapshots/fundamentals/`** — contains:
- `2026-05.json`
- `2026-06.json`
Only. No historical fundamental snapshots.

**`snapshots/growth/`** — contains:
- `2026-05.json`
- `2026-06.json`
Only.

**`snapshots/quality/`**, **`snapshots/value/`** — same pattern. All are
2026-only snapshots.

**`snapshots/momentum_history/`** — contains 89 files from 2019-01 to 2026-05,
but each file holds only `return_12m` and `rank`. No `quality_score`,
`growth_score`, `value_score`, or composite `momentum_score` percentile.

### Conclusion for Q2

At the time V7 was executed, zero historical factor scores existed for any
month in the 2019–2025 window. The four factor sub-scores (quality, growth,
value, momentum percentile) did not exist in any historical file.

---

## QUESTION 3 — Did V7 optimization use Real, Reconstructed, or Constant Fallback data?

### Weight Configuration Comparison: C — Constant Fallback

The OOS validation's `run_weighted_backtest()` function reads factor scores
via (lines 558–561):

```python
q  = item.get("quality_score",  item.get("quality",  50))
g  = item.get("growth_score",   item.get("growth",   50))
v  = item.get("value_score",    item.get("value",    50))
mo = item.get("momentum_score", item.get("momentum", 50))
```

Since all four keys are absent from `snapshots/momentum_history/*.json`:
- `q = 50` (constant)
- `g = 50` (constant)
- `v = 50` (constant)
- `mo = 50` (constant)

The computed score for every ticker, every month, every config:
```
_oos_score = w_q*50 + w_g*50 + w_v*50 + w_mo*50
           = 50 * (w_q + w_g + w_v + w_mo)
           = 50 * 1.0
           = 50.0
```

All configs produce identical portfolios. The OOS weight comparison table
in the report is not a product of real factor optimization. It is the output
of a constant-input scoring engine.

**This is Category C: Constant Fallback Values.**

### Counterfactual Alpha Attribution (+23.29% Momentum, +22.66% Growth): Unclear

The chronicle claims factor-by-factor alpha numbers were computed. However:

- No script in `research/` implements a single-factor counterfactual backtest
  using historical factor scores
- No historical factor data exists to run such a backtest against
- `research/rs6m_backtest_engine.py` is price-based (uses daily prices, not
  factor scores) and produces RS-6M alpha, not Quality/Growth/Value alpha

**Most probable explanation:** The counterfactual alpha numbers represent
simulated portfolios ranked by the production momentum score only (Top 5 by
return_12m) compared to IHSG — not by individual factor scores. This would
mean Momentum alpha (+23.29%) = the actual momentum backtest result, and
Growth/Quality/Value alphas were computed by some form of approximation that
has not been preserved in the codebase.

**Alternative explanation:** These numbers were analytically extrapolated from
the production momentum returns rather than independently simulated.

In either case: the claim that Growth independently contributes +22.66% alpha
cannot be verified from any file in the repository. There is no Growth-only
backtest engine and no historical growth scores to power one.

### RS-6M Analysis (Factor 006): A — Real Factor Data

The only component of V7's research cluster that used genuinely real,
independently computed data is the RS-6M backtest. This used:
- Daily stock prices (output/history_prices/)
- Daily IHSG prices
- Listing date gates
- Dynamic historical universe

The RS-6M integration result — that RS-6M is a valid, non-redundant alpha
signal — is data-valid. The 41.28% CAGR (pre-remediation) and 1.21% CAGR
(post-remediation) numbers are real. The survivorship bias remediation that
followed is also correctly executed.

---

## QUESTION 4 — Can V7 conclusions still be trusted?

V7 produced multiple distinct conclusions. Each must be evaluated separately.

---

### Conclusion 1: Config B outperforms Config A, C, D, E

**ADR-003 Evidence cited:**
> *"CAGR meningkat dari 2.92% (Config A) menjadi 4.88% (Config B)"*
> *"Alpha tahunan dari +5.54% ke +7.85%"*

**Data lineage:** The OOS weight comparison ran with all four factor scores
defaulting to 50. All five configs produced the same Top 5 portfolio each month.
The CAGR numbers cited in ADR-003 cannot be the output of the OOS optimization
loop because that loop produced identical metrics for all configs.

**Possible origin of these different CAGR numbers:** The numbers in ADR-003
(2.92% vs 4.88%) are different from the OOS report's identical Sharpe values.
This suggests these numbers came from a **separate run or analysis** — potentially
a script that is no longer in the repository, or a manual calculation.

However, if that separate run also lacked historical factor scores, it would
have the same problem. And since no historical factor scores exist in the
repository for any period before 2026-05, any separate run would also have
been operating on constant or proxy data.

**Verdict for Conclusion 1:**

| Claim | Verifiable? | Trust? |
|---|---|---|
| Config B CAGR = 4.88% (vs Config A 2.92%) | ❌ Source script not found | **UNVERIFIABLE** |
| Config B Sharpe improved | ❌ OOS loop produces identical values | **CONTRADICTED** |
| Config B outperforms A, C, D, E | ❌ Cannot be proven without factor data | **UNPROVEN** |

---

### Conclusion 2: Momentum contributes +23.29% alpha; Growth +22.66%

**Verification attempt:** No single-factor counterfactual backtest engine
exists in the repository. No historical Quality, Growth, or Value scores exist
to power one. The RS-6M engine is price-based (not factor-score-based).

**Assessment:** These numbers may represent the return of momentum-ranked
portfolios (real data) compared to IHSG, but attributing alpha independently
to Growth is impossible without a Growth-sorted historical portfolio.

**Verdict for Conclusion 2:**

| Claim | Trust? |
|---|---|
| Momentum alpha +23.29% (may reflect real momentum backtest) | PARTIALLY VALID — if derived from momentum_monthly_returns.csv |
| Growth alpha +22.66% (requires historical growth scores) | **UNVERIFIABLE** — no historical growth scores exist |
| Value as alpha drag | **UNVERIFIABLE** — no historical value scores exist |
| Quality as stabilizer | **UNVERIFIABLE** — no historical quality scores exist |

---

### Conclusion 3: RS-6M is a valid, independent signal

**Data lineage:** `research/rs6m_backtest_engine.py` — uses real daily prices,
IHSG, listing dates, and dynamic universe. Fully self-contained and verified.

**Verdict for Conclusion 3: VALID** — The finding that RS-6M is independent
from Return-12M momentum (Pearson r < 0.70) is methodologically sound and
based on real price data.

---

### Conclusion 4: Foreign Flow (Factor 005) is inconclusive

**Data lineage:** The foreign flow proxy was acknowledged to be a
Volume-Adjusted Momentum proxy, not real institutional flow data. The
backtest showed degradation (CAGR fell from 6.62% to 3.11%). The decision
to park Factor 005 is based on valid reasoning even if the underlying
backtest used proxy data.

**Verdict for Conclusion 4: VALID** — The conclusion is correct regardless
of data quality: proxy data ≠ real institutional data, so the factor is
correctly parked.

---

### Conclusion 5: Survivorship bias remediation

**Data lineage:** Real dynamic historical universe files (15 JSON files in
`database/historical_universe/`), ticker metadata with listing dates, and
real price history. The survivorship remediation work is fully real.

**Verdict for Conclusion 5: VALID** — CAGR correction from 19.07% to 1.21%
is a real measurement using real data.

---

## QUESTION 5 — Final Verdict

### Verdict by component:

| V7 Research Component | Data Used | Verdict |
|---|---|---|
| Config A vs B vs C vs D vs E weight comparison | Constant fallback (50) for all factor scores | **INVALID** |
| Config B CAGR 4.88% vs Config A 2.92% claim | Source not in repository; cannot verify | **UNVERIFIABLE** |
| Momentum alpha +23.29% | Likely real if from momentum_monthly_returns.csv | **PARTIALLY VALID** |
| Growth alpha +22.66% | No historical growth scores — unverifiable | **UNVERIFIABLE** |
| Quality as risk stabilizer | No historical quality scores | **UNVERIFIABLE** |
| Value as alpha drag | No historical value scores | **UNVERIFIABLE** |
| RS-6M Factor 006 validity | Real daily prices + IHSG | **VALID** |
| Foreign Flow Factor 005 inconclusive | Correctly reasoned even on proxy data | **VALID** |
| Survivorship bias remediation | Real dynamic universe + prices | **VALID** |
| Production weight migration to Config B | Based on invalid comparison | **INVALID BASIS** |

---

## Overall V7 Verdict: **PARTIALLY VALID**

Specifically:

**Valid components (can be retained):**
- Momentum is a real alpha signal in IDX30 (confirmed by real backtest)
- RS-6M is an independent alpha signal (confirmed by real price audit)
- Foreign Flow proxy is scientifically insufficient (correctly rejected)
- Survivorship bias was real and has been correctly remediated

**Invalid components (require re-investigation with Warehouse V2):**
- Config B weight configuration was never proven superior to Config A
- The TRAIN Sharpe comparison (0.18 for all five configs) is identical —
  mathematically proving no real ranking differentiation occurred
- Growth's independent alpha contribution (+22.66%) has no data support
- Quality's risk-stabilizer role has no historical quality score data
- Value's "alpha drag" characterization has no historical value score data

**Consequences for production:**

| Decision | Status |
|---|---|
| Production uses Config B weights (35% Momentum, 30% Growth, 25% Quality, 10% Value) | ❌ Adopted without valid proof of superiority |
| Config B was "APPROVED" in ADR-003 | ❌ ADR evidence is unverifiable/contradicted |
| Production weights should be reverted to Config A? | ⚠️ Neither Config is proven; Config A is at least the prior validated state |

---

## What Warehouse V2 Would Fix

| V7 Unresolved Question | Warehouse V2 Resolution |
|---|---|
| Does Config B actually outperform Config A? | Re-run `run_weighted_backtest()` with real 4-factor scores from 2021–present |
| Is Growth alpha truly +22.66%? | Simulate Growth-only Top 5 portfolio using historical growth_score |
| Is Value truly an alpha drag? | Simulate Value-only Top 5 portfolio using historical value_score |
| Is Quality a risk stabilizer? | Simulate Quality-only portfolio; measure Max Drawdown |
| Which weight config is optimal for IDX30? | Genuine multi-factor walk-forward optimization for first time |

---

## Appendix: Evidence Chain

| Claim | Source | Verified? |
|---|---|---|
| All 89 momentum snapshots contain only `return_12m` and `rank` | `snapshots/momentum_history/2022-06.json`, `2024-03.json` (verified directly) | ✅ |
| Backtester defaults all 4 factor scores to 50 | `out_of_sample_validation.py` lines 558–561 `.get(key, 50)` | ✅ |
| All five configs produce identical Sharpe in OOS report | `reports/out_of_sample_validation.md` — Table row values all 0.18/−0.37 | ✅ |
| Factor warehouse has only 2026-05 and 2026-06 data | `database/historical/factor_warehouse.csv` — 96 rows, dates 2026-05 and 2026-06 only | ✅ |
| No single-factor counterfactual backtest script exists | `research/` directory listing — 15 files; none implements factor-isolated backtest | ✅ |
| RS-6M backtest uses real price data | `research/rs6m_backtest_engine.py` — `output/history_prices/`, `benchmarks/ihsg.csv` | ✅ |
| Chronicle V7 status marked UNDER REVIEW | `master_chronicle.txt` lines 749–759 — "Framework optimisasi bobot tidak benar-benar melakukan historical factor re-ranking" | ✅ |
| ADR-003 cites Config B CAGR 4.88% vs Config A 2.92% | `docs/ADR-003-ALPHA-OPTIMIZED-WEIGHTS.md` line 35 | ✅ but source script not found |

**The Chronicle itself already acknowledges the problem at lines 749–759:**

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

This self-documented note in the Chronicle is accurate and fully consistent
with the findings of this audit.
