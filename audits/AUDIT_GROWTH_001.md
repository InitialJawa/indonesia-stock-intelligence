# AUDIT-GROWTH-001: Growth Factor Specification

> Date: 2026-06-09
> Files: `collectors/growth.py`, `scoring/growth_score.py`, `scoring/utils.py`, `utils/data_provider.py`
> Data: `output/raw/growth.json`, `output/scores/growth_ranking.json`

---

## 1. Inputs Used by Growth Factor

| Input | Collected | Scored | Source |
|-------|-----------|--------|--------|
| `earnings_growth` | Yes | **Yes** (sole input) | Yahoo Finance `earningsGrowth` |
| `revenue_growth` | Yes | **No** (excluded per `# EARNINGS-ONLY GROWTH: Menghilangkan Revenue Growth yang menghasilkan alpha negatif`) | Yahoo Finance `revenueGrowth` |

**Design decision**: Revenue growth was explicitly removed from scoring after producing negative alpha. The comment at `scoring/growth_score.py:24` states this. However, revenue_growth is still collected and stored in the output for reference.

### 1.1 Null Handling

When Yahoo returns `null` for either metric, the collector stores `null` (from `_fetch_from_yfinance` → `.get()` returns `None` → stored as JSON `null`).

In the scorer (`growth_score.py:16-21`), `info.get("earnings_growth") or 0` replaces `null` with `0`. This means:

- **5 tickers** (MDKA, AMMN, TPIA, GOTO, EXCL) have `earnings_growth: null`
- These 5 tickers are treated as having **zero earnings growth**
- Score = percentile rank among 30 values where 5 are tied at 0 → score = **34.48** (rank 18-22/30)

**Impact**: Null → 0 → mid-ranked score. This is misleading for tickers where Yahoo simply doesn't report the metric (AMMN, TPIA, EXCL have massive revenue growth but missing earnings growth). In production warehouse_v3, only MDKA.JK and GOTO.JK from the null set actually appear.

---

## 2. Final Score Formula

```
growth_score = percentile_normalize(earnings_values)
```

Where `percentile_normalize` is defined in `scoring/utils.py:22-45`:

```python
for v in values:
    lesser = count(x in values where x < v)
    equal = count(x in values where x == v)
    rank = lesser + (equal - 1) / 2.0          # fractional ranking for ties
    score = (rank / (n - 1)) * 100             # 0..100 scale
```

| Property | Value |
|----------|-------|
| Scale | 0.00 — 100.00 |
| Type | Rank-based (percentile) |
| Outlier resistance | **High** (rank-based, not sensitive to extreme values) |
| Tie handling | Fractional ranking (average of tied positions) |
| Edge case: all values equal | Returns 50.0 for all |
| Edge case: single value | Returns 50.0 |

### 2.1 Previous Formula (Legacy, Retained for Compatibility)

`min_max_normalize` in `scoring/utils.py:3-20`:

```python
score = ((v - min_v) / (max_v - min_v)) * 100
```

This was the original formula but was abandoned because **AMMN.JK has `revenue_growth = 379.373`** (37937%), which creates extreme distortion. The single outlier would compress all other scores near zero. Percentile normalization was introduced to fix this.

---

## 3. Yahoo Finance Fields Used

| Metric | Yahoo Field | Map Location | Notes |
|--------|-------------|-------------|-------|
| `revenue_growth` | `revenueGrowth` | `data_provider.py:27` | Collected but excluded from final score |
| `earnings_growth` | `earningsGrowth` | `data_provider.py:28` | Input to final score |

Both are fetched via `yfinance` library → `Ticker.info` dictionary.

### 3.1 Raw Values (Latest Snapshot)

| Field | Range | Outliers |
|-------|-------|----------|
| `revenue_growth` | -0.188 to 379.373 | AMMN (379.37 = 37937%), TPIA (2.864 = 286%), BRPT (2.322 = 232%) |
| `earnings_growth` | -0.794 to 4.610 | BRPT (4.61 = 461%), ESSA (1.31 = 131%), PTBA (1.047 = 105%) |

The `revenue_growth` outlier problem (AMMN: 379.37) is the reason percentile normalization replaced min-max, and the reason revenue_growth was excluded from scoring entirely.

---

## 4. Null Percentage

| Field | Total | Null | Null % | Imputation |
|-------|-------|------|--------|------------|
| `revenue_growth` | 30 | 0 | **0.00%** | N/A |
| `earnings_growth` | 30 | **5** | **16.67%** | `null → 0` |

**Null tickers** (earnings_growth):
- MDKA.JK, AMMN.JK, TPIA.JK, GOTO.JK, EXCL.JK

**Impact on warehouse production**: Only MDKA.JK and GOTO.JK appear in warehouse_v3 (29 tickers). AMMN, TPIA, EXCL are in idx30 universe but not in warehouse → their null data does not affect backtesting results.

### 4.1 Null Risk Assessment

| Risk | Severity | Explanation |
|------|----------|-------------|
| Null → 0 = mid-rank score | **Medium** | 5 tickers tied at 0 get score 34.48 (positions 18-22/30). These are not genuine zero-growth companies — Yahoo simply lacks the data. |
| Distorted rank of adjacent tickers | **Low** | The 5-way tie at 0 affects the fractional ranking of negative-earnings tickers (their `equal` count includes the 5 null → 0 values). This slightly compresses the lower tail. |
| Null tickers outside warehouse | **Low** | AMMN, TPIA, EXCL are not in warehouse_v3 → no backtest impact. |

---

## 5. Example Calculation (5 Tickers)

### Raw Inputs

| Ticker | `revenue_growth` | `earnings_growth` (𝑦) |
|--------|----------------:|---------------------:|
| BRPT.JK | 2.322 | 4.610 |
| CPIN.JK | 0.127 | 0.677 |
| BBCA.JK | 0.025 | 0.037 |
| MDKA.JK | 0.063 | **null → 0** |
| UNTR.JK | -0.167 | -0.794 |

### Step-by-Step (`percentile_normalize`)

n = 30 total tickers, denominator = n - 1 = 29.

```
For BRPT.JK (y = 4.610):
  lesser = 29   (all 29 other values are < 4.610)
  equal  = 1
  rank   = 29 + (1-1)/2 = 29.0
  score  = (29.0 / 29) × 100 = 100.00

For CPIN.JK (y = 0.677):
  lesser = 24   (24 values < 0.677)
  equal  = 1
  rank   = 24 + (1-1)/2 = 24.0
  score  = (24.0 / 29) × 100 = 82.76

For BBCA.JK (y = 0.037):
  lesser = 13   (13 values < 0.037)
  equal  = 1
  rank   = 13 + (1-1)/2 = 13.0
  score  = (13.0 / 29) × 100 = 44.83

For MDKA.JK (null → y = 0):    (4 other tickers also null → 0)
  lesser = 8    (8 negative values: TLKM, ASII, HEAL, KLBF, ICBP, SIDO, ITMG, UNTR)
  equal  = 5    (5 null → 0: MDKA, AMMN, TPIA, GOTO, EXCL)
  rank   = 8 + (5-1)/2 = 8 + 2 = 10.0
  score  = (10.0 / 29) × 100 = 34.48

For UNTR.JK (y = -0.794):
  lesser = 0    (lowest value)
  equal  = 1
  rank   = 0 + (1-1)/2 = 0.0
  score  = (0.0 / 29) × 100 = 0.00
```

### Final Scores

| Rank | Ticker | Growth Score | Earnings Growth |
|------|--------|:-----------:|:---------------:|
| 1 | BRPT.JK | **100.00** | 4.610 |
| 6 | CPIN.JK | **82.76** | 0.677 |
| 15 | BBCA.JK | **44.83** | 0.037 |
| 18-22 | MDKA.JK | **34.48** | 0 (null) |
| 30 | UNTR.JK | **0.00** | -0.794 |

---

## Findings Summary

| # | Finding | Severity | Recommendation |
|---|---------|----------|---------------|
| F1 | `earnings_growth` has **16.67% null rate** (5/30 tickers) | Medium | For tickers with null earnings but known revenue growth, consider falling back to revenue_growth instead of defaulting to 0. At minimum, flag them as "data unavailable" rather than assigning a mid-rank score. |
| F2 | `revenue_growth` is **collected but excluded** from scoring | Info | Design decision documented in code. Consider removing it from the collector entirely if it's never used, or keep as a fallback for null earnings_growth (F1). |
| F3 | **Outlier AMMN.JK** (revenue_growth = 379.37) forced the migration to percentile normalization | Info | Handled correctly — percentile normalization is the right approach. |
| F4 | **Universe mismatch**: idx30 has 30 tickers, warehouse has 29. AMMN, TPIA, EXCL in idx30 but not warehouse | Low | Should be audited separately. These tickers' missing data doesn't affect backtests but could affect production recommendations. |
| F5 | **Edge case**: all-null scenario would score all tickers at 50.0 (undifferentiated) | Low | `percentile_normalize` handles this via the `max(values) == min(values)` gate at line 30. |

---

*Report generated by `audits/AUDIT_GROWTH_001.md`*
