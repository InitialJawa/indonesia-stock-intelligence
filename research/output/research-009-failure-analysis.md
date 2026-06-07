# RESEARCH-009: Failure Analysis — rs_change_60d
**Generated:** 2026-06-07 14:35:45

---

## Signal: rs_change_60d > 0

Total signals: 1884
True positives (rally follows): 396
False positives (no rally): 1488
Overall precision: 21.0%

---

## What Goes Wrong in False Positives?

### Characteristic Differences (FP vs TP)

| Feature | FP Mean | TP Mean | Difference |
|---------|---------|---------|------------|
| rs_change_60d | 0.1404 | 0.1472 | +0.0068 |
| volume_ratio | 1.1322 | 1.0987 | -0.0335 |
| momentum_slope | 0.0007 | 0.0008 | +0.0001 |
| recovery_from_60d_low | 0.2301 | 0.2440 | +0.0138 |
| drawdown_252d | -0.1675 | -0.2304 | -0.0630 |
| volatility_20d | 0.3583 | 0.4368 | +0.0785 |

### Binary Feature Prevalence

| Feature | FP %True | TP %True |
|---------|----------|----------|
| above_ma20 | 62% | 57% |
| above_ma50 | 67% | 62% |
| above_ma100 | 66% | 59% |
| above_ma200 | 62% | 48% |

### Regime Distribution

| Regime | FP Count | FP % | TP Count | TP % |
|--------|----------|------|----------|------|
| bear | 269 | 18% | 43 | 11% |
| bull | 118 | 8% | 85 | 21% |
| sideways | 1029 | 69% | 257 | 65% |
| unknown | 72 | 5% | 11 | 3% |

### Key Failure Patterns

- False positives have weaker recovery from lows (0.23 vs 0.24)

### Common FP Scenario

A typical false positive occurs when rs_change_60d turns positive but:

- Volume is low (mean volume_ratio = 1.13)
- Recovery from lows is weak (mean = 0.23)
- Price is often still below MA20 (38% of FP cases)
- The market regime may be unfavorable

---
*End of RESEARCH-009 Failure Analysis*
