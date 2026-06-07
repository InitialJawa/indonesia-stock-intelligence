# IDX30 Rally Autopsy — Master Research Report
**Generated:** 2026-06-07
**Data Source:** `warehouse_daily_v4.parquet` (59,303 rows, 30 IDX30 tickers, 2018–2026)

---

## Table of Contents

1. [RESEARCH-008: Daily Winner Autopsy](#research-008-daily-winner-autopsy)
2. [RESEARCH-008B: Rally Initiation Detection](#research-008b-rally-initiation-detection)
3. [RESEARCH-009: rs_change_60d Validation](#research-009-rs_change_60d-validation)
4. [Synthesis: The Complete Picture](#synthesis-the-complete-picture)

---

# RESEARCH-008: Daily Winner Autopsy

## Core Question

*What consistently happens before major IDX30 rallies begin?*

## Methodology

### Winner Definitions

| Category | Definition | Forward Window |
|----------|-----------|----------------|
| Winner20 | Forward Return >= +20% | 20 trading days |
| Winner30 | Forward Return >= +30% | 40 trading days |
| Winner40 | Forward Return >= +40% | 60 trading days |

**Primary analysis focuses on Winner40 (60D >= +40%).** 128 non-overlapping events extracted.

### Statistical Tests

- **Cohen's d**: Effect size (standardized mean difference)
- **Spearman IC**: Rank correlation between feature value and win/no-win
- **Mann-Whitney U**: Non-parametric test of distribution difference
- **Lift**: Ratio of winner mean to control mean

## Key Finding: Winners Are Distressed, Not Strong

Future winners are typically in **deeper drawdown**, **below moving averages**, with **higher volatility** and **weak short-term RS**. This contradicts the original hypothesis that winners emerge from strong RS and recovery profiles.

## Top 10 Predictive Features

| Rank | Feature | Score | Cohen's d | IC | Lift | p-value |
|------|---------|-------|-----------|-----|------|---------|
| 1 | `ma50` | 0.749 | -0.477 | -0.308 | 0.60x | 1e-06 |
| 2 | `ma20` | 0.746 | -0.471 | -0.308 | 0.60x | 1e-06 |
| 3 | `ma100` | 0.735 | -0.479 | -0.302 | 0.59x | 2e-06 |
| 4 | `ma200` | 0.719 | -0.479 | -0.298 | 0.59x | 5e-06 |
| 5 | `volatility_60d` | 0.663 | +0.401 | +0.289 | 1.20x | 5e-06 |
| 6 | `volatility_20d` | 0.613 | +0.370 | +0.273 | 1.26x | 1.6e-05 |
| 7 | `rs_20d` | 0.526 | -0.316 | -0.228 | 11.14x | 4e-04 |
| 8 | `distance_from_high_252d` | 0.494 | -0.396 | -0.192 | 1.30x | 2e-03 |
| 9 | `drawdown_252d` | 0.494 | -0.396 | -0.192 | 1.30x | 2e-03 |
| 10 | `rs_change_20d` | 0.450 | -0.291 | -0.185 | 14.30x | 4e-03 |

## Pre-Rally Timeline (T-40 to T0)

Median feature values at each offset:

| Feature | T-40 | T-20 | T-10 | T-5 | T0 |
|---------|------|------|------|-----|----|
| rs_20d | 0.0082 | 0.0014 | -0.0079 | -0.0294 | -0.0642 |
| rs_60d | 0.0065 | -0.0075 | -0.0127 | -0.0255 | -0.0549 |
| rs_change_60d | 0.0008 | -0.0292 | -0.0036 | -0.0331 | -0.0558 |
| recovery_from_60d_low | 0.1321 | 0.1439 | 0.1355 | 0.1062 | 0.0680 |
| drawdown_252d | -0.2042 | -0.2172 | -0.2548 | -0.2898 | -0.3260 |
| volatility_20d | 0.3678 | 0.4026 | 0.4260 | 0.4367 | 0.4561 |
| volume_ratio | 0.9251 | 0.7692 | 0.8701 | 0.8774 | 0.9073 |
| momentum_slope | -0.0006 | -0.0004 | -0.0004 | -0.0001 | -0.0010 |

**Observation:** Features consistently *deteriorate* from T-40 through T0. The rally inflection point occurs **after** T0, not before.

## What Changes First (008)

| Feature | Early Change % (T-40→T-20 / Total) |
|---------|--------------------------------------|
| volume_ratio | 878%* |
| volatility_60d | 133%* |
| above_ma50 | 100% |
| momentum_slope | 85% |
| rs_change_60d | 53% |

*\*Values >100% indicate non-monotonic movement (oscillation)*

---

# RESEARCH-008B: Rally Initiation Detection

## Core Question

*What is the earliest detectable sign that a future winner is transitioning from distress into accumulation?*

## Methodology

Four candidate rally start signals, each validated by forward return criteria:

| Candidate | Signal | Validation |
|-----------|--------|------------|
| A | Price crosses above MA20 after >= 20 days below | fwd20>+10% or fwd40>+15% |
| B | RS20 changes from negative to positive | same |
| C | Volume Ratio > 1.3 AND price above MA20 | same |
| D | Momentum Slope changes from negative to positive | same |

**943 validated rally start events** across all candidates.

## Signal Stability Comparison

| Candidate | Precision | Recall | Lift | FPR | Validated |
|-----------|-----------|--------|------|-----|-----------|
| A (MA20 Cross) | 23.62% | 10.92% | 14.86x | 0.56% | 103 |
| B (RS20 → Positive) | 20.16% | 31.92% | 12.68x | 2.01% | 301 |
| C (Volume >1.3 + MA20) | 21.35% | 39.02% | 13.42x | 2.29% | 368 |
| D (Momentum Slope → Positive) | **23.85%** | 18.13% | **15.00x** | **0.92%** | 171 |

**Best standalone signal: Candidate D** (Momentum Slope turning positive) — highest precision and lift, lowest FPR.

## Transition Sequence (Data-Determined)

### T-40 to T-20 — The Earliest Movers
`rs_change_60d` (57%), `rs_120d` (42%), `rs_252d` (40%), `distance_from_high_252d` (40%), `drawdown_252d` (40%), `volatility_60d` (39%)

### T-20 to T-10
Volatility builds further

### T-10 to T-5
`volatility_20d`

### T-5 to T0 — The Confirmation Cluster
`rs_60d` (47%), `rs_20d` (62%), `momentum_slope` (61%), `volume_ratio` (90%), `recovery_from_60d_low` (73%), `rs_change_20d` (74%), `above_ma20` (100%), `above_ma50` (100%)

## Accumulation State Profile

### At T-5 (5 days before rally start)
| Condition | Prevalence |
|-----------|-----------|
| Drawdown > 20% | 62.4% |
| Recovery > 10% from 60d low | 52.2% |
| Volatility above median | 49.6% |
| rs_change_20d improving | 44.9% |
| Above MA20 | 44.1% |
| rs_change_60d improving | 41.9% |
| Drawdown > 30% | 41.8% |

### At T0 (rally start)
| Condition | Prevalence |
|-----------|-----------|
| Above MA20 | 87.8% |
| Recovery > 10% from 60d low | 71.9% |
| RS20 positive | 70.4% |
| Volume Ratio > 1.2 | 63.5% |
| rs_change_20d improving | 61.2% |
| Drawdown > 20% | 57.7% |
| Above MA50 | 55.7% |
| Momentum slope positive | 51.4% |

### The Accumulation State (Composite)

```
Drawdown > 20%
Recovery_from_60d_low rising but still < 20%
RS20 improving from negative
Volume ratio increasing (>1.2 imminent)
Momentum slope turning positive
Below MA50 (typically)
```

---

# RESEARCH-009: rs_change_60d Validation

## Core Question

*Is rs_change_60d a robust timing signal or merely an interesting observation?*

## Walk Forward Stability

| Train → Test | Signals | Positive | Precision |
|-------------|---------|----------|-----------|
| 2018-2019 → 2020 | 236 | 65 | 27.5% |
| 2019-2020 → 2021 | 250 | 55 | 22.0% |
| 2020-2021 → 2022 | 241 | 50 | 20.8% |
| 2021-2022 → 2023 | 211 | 34 | 16.1% |
| 2022-2023 → 2024 | 260 | 44 | 16.9% |
| 2023-2024 → 2025 | 245 | 62 | 25.3% |

**Range: 16.1%–27.5% | Avg: 21.4% | STABLE (range 11.4pp)**

## Market Regime Dependence

| Regime | Signals | Positive | Precision |
|--------|---------|----------|-----------|
| **Bull** | 231 | 87 | **37.7%** |
| Bear | 341 | 47 | 13.8% |
| Sideways | 1311 | 266 | 20.3% |

**Signal works best in bull markets.** Bear market precision is weak.

## Ticker Dispersion

| Ticker | Precision | Ticker | Precision |
|--------|-----------|--------|-----------|
| BRPT.JK | **42.9%** | BBCA.JK | **4.5%** |
| MDKA.JK | **38.8%** | ICBP.JK | **3.0%** |
| TPIA.JK | 37.1% | INDF.JK | 8.6% |
| ESSA.JK | 36.4% | BMRI.JK | 12.5% |
| ANTM.JK | 31.8% | ASII.JK | 13.2% |

**CV = 0.46** — signal is ticker-dependent. Works best on volatile, cyclical names. Weak on stable large caps.

## Threshold Stability

| Threshold | Precision |
|-----------|-----------|
| > 0.00 | 21.02% |
| > 0.01 | 21.20% |
| > 0.02 | 20.65% |
| > 0.03 | 20.71% |
| > 0.05 | 20.93% |

**Virtually flat** — signal is qualitative, not quantitative. Threshold doesn't matter.

## Combined Signal Performance

| Signal | Definition | Precision |
|--------|------------|-----------|
| A | rs_change_60d > 0 (base) | 21.0% |
| B | + volume_ratio > 1.2 | 20.1% |
| C | + above_ma20 | 19.5% |
| D | + momentum_slope > 0 | **21.4%** |
| E | + volume_ratio > 1.2 AND above_ma20 | 19.6% |

**No meaningful improvement from combining.** Signal D (add momentum > 0) is marginally best.

## Failure Analysis

### False Positive Profile

False positives tend to occur when:
- **69% in sideways regimes**
- Volume ratio close to 1.0 (no conviction)
- Recovery from lows is weak
- Low volatility stocks (BBCA, ICBP, INDF)

True positives tend to have:
- **Deeper drawdown** (-0.23 vs -0.17) — more room to rally
- **Higher volatility** (0.44 vs 0.36) — more explosive moves
- **Lower above_ma200** (48% vs 62%) — truly distressed, not just drifting

### Verdict: CONDITIONALLY ROBUST

rs_change_60d is a **genuine early warning signal** that:
- Is stable across time (walk forward range 11.4pp)
- Is threshold-agnostic (precision flat across 5 thresholds)
- Works best in bull markets (37.7%) and on volatile names (BRPT 42.9%)
- Fails in bear markets (13.8%) and on stable large caps (BBCA 4.5%)
- Does NOT benefit materially from combination with other signals

---

# Synthesis: The Complete Picture

## The Narrative

The data tells a consistent story across all three research phases:

### Phase 1 (008): Future winners are distressed
Stocks that rally +40% in 60 days are beaten down — deep drawdown, below MAs, high volatility, weak RS. Not momentum leaders.

### Phase 2 (008B): The transition starts with RS change
The earliest detectable sign is `rs_change_60d` improving (57% of change by T-20). Volume, price cross, and momentum confirmation all cluster at T-5 to T0 — they confirm late.

### Phase 3 (009): The signal is real but context-dependent
rs_change_60d is stable through time and threshold-agnostic, but its precision varies by regime (37.7% bull vs 13.8% bear) and ticker (42.9% BRPT vs 4.5% BBCA).

## The Accumulation Sequence

```
T-40         rs_change_60d improves          ← EARLIEST DETECTABLE SIGN
             rs_120d, rs_252d begin rising
             Drawdown widens further
             
T-20         Volatility builds
             
T-10         Short-term RS improves
             Momentum slope turns positive
             
T-5          Price crosses above MA20
             Volume surges (>1.3x)
             Recovery from lows accelerates
             
T0           Above MA50
             RS20 positive
             Full accumulation state confirmed
```

## What rs_change_60d Measures

rs_change_60d = change in 60-day relative strength over 60 days. It captures whether a stock's performance relative to IHSG is *accelerating or decelerating* over a 3-month horizon.

When it turns positive, it means the stock's relative performance has stopped deteriorating and begun improving — even if absolute RS is still negative. This is the first green shoot.

## Practical Takeaways

1. **Don't wait for price confirmation.** By the time price crosses MA20 with volume, 90% of the move in those features has already happened in the last 5 days.

2. **Context matters.** The same rs_change_60d signal means different things in bull (38% precision) vs bear (14% precision) markets.

3. **Ticker selection is critical.** The signal is 10x more reliable on BRPT (43%) than BBCA (4%). It's a cyclical/reversal signal, not a compounder signal.

4. **Threshold doesn't matter.** rs_change_60d > 0 is as good as > 0.05. The presence of the inflection matters, not its magnitude.

5. **Don't stack signals.** Adding volume, MA, or momentum filters doesn't improve precision meaningfully. The signal is already in rs_change_60d.

---

## Limitations

1. **Look-ahead bias**: Forward returns used for labeling only, NOT as features
2. **Survivorship bias**: Only current IDX30 constituents
3. **Small universe**: 30 tickers limits generalization
4. **No timing engine**: This is an autopsy, not a prediction model
5. **Correlation ≠ Causation**: Observed patterns may not predict future rallies

---

*End of IDX30 Rally Autopsy Master Report*
