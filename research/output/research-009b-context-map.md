# RESEARCH-009B: Context Filter Discovery
**Generated:** 2026-06-07 14:40:37

---

## Core Question

*Why does rs_change_60d produce 43% precision on BRPT but only 4.5% on BBCA?*

---

## Base Signal

rs_change_60d > 0 with min_gap=20

- Total signals: 1884
- True positives: 396
- Base precision: 21.02%

---

## Bucket-by-Bucket Analysis

### Volatility Bucket

| Category | Signals | Hits | Precision | % of Signals | Lift | Quality |
|----------|---------|------|-----------|-------------|------|---------|
| High Vol | 650 | 183 | 28.1% | 34% | 1.34x | MODERATE |
| Low Vol | 592 | 68 | 11.5% | 31% | 0.55x | WEAK |
| Medium Vol | 642 | 145 | 22.6% | 34% | 1.07x | MODERATE |

### Drawdown Bucket

| Category | Signals | Hits | Precision | % of Signals | Lift | Quality |
|----------|---------|------|-----------|-------------|------|---------|
| Deep (<-25%) | 524 | 179 | 34.2% | 28% | 1.63x | STRONG |
| Moderate (-10% to -25%) | 738 | 129 | 17.5% | 39% | 0.83x | WEAK |
| Shallow (>-10%) | 622 | 88 | 14.1% | 33% | 0.67x | WEAK |

### Mcap Bucket

| Category | Signals | Hits | Precision | % of Signals | Lift | Quality |
|----------|---------|------|-----------|-------------|------|---------|
| Large (>5k) | 545 | 73 | 13.4% | 29% | 0.64x | WEAK |
| Mid (1k-5k) | 1041 | 244 | 23.4% | 55% | 1.12x | MODERATE |
| Small (<1k) | 298 | 79 | 26.5% | 16% | 1.26x | MODERATE |

### Trend Bucket

| Category | Signals | Hits | Precision | % of Signals | Lift | Quality |
|----------|---------|------|-----------|-------------|------|---------|
| Bear Trend (below both) | 464 | 113 | 24.3% | 25% | 1.16x | MODERATE |
| Bull Trend (above MA50+200) | 930 | 154 | 16.6% | 49% | 0.79x | WEAK |
| Mixed (above MA50, below MA200) | 307 | 92 | 30.0% | 16% | 1.43x | MODERATE |
| Mixed (below MA50, above MA200) | 183 | 37 | 20.2% | 10% | 0.96x | MODERATE |

### Sector

| Category | Signals | Hits | Precision | % of Signals | Lift | Quality |
|----------|---------|------|-----------|-------------|------|---------|
| Automotive & Conglomerate | 68 | 9 | 13.2% | 4% | 0.63x | WEAK |
| Banking | 258 | 29 | 11.2% | 14% | 0.53x | WEAK |
| Cement | 129 | 20 | 15.5% | 7% | 0.74x | WEAK |
| Chemicals & Conglomerate | 63 | 27 | 42.9% | 3% | 2.04x | STRONG |
| Chemicals (Petrochemical) | 62 | 23 | 37.1% | 3% | 1.77x | STRONG |
| Coal Mining | 136 | 32 | 23.5% | 7% | 1.12x | MODERATE |
| Coal Mining (State-owned) | 69 | 17 | 24.6% | 4% | 1.17x | MODERATE |
| Consumer Goods | 203 | 20 | 9.8% | 11% | 0.47x | WEAK |
| Energy & Logistics | 69 | 18 | 26.1% | 4% | 1.24x | MODERATE |
| Energy (Gas) | 64 | 18 | 28.1% | 3% | 1.34x | MODERATE |
| Energy (Oil & Gas) | 66 | 24 | 36.4% | 4% | 1.73x | STRONG |
| Healthcare | 129 | 25 | 19.4% | 7% | 0.92x | WEAK |
| Heavy Equipment & Mining | 65 | 14 | 21.5% | 4% | 1.02x | MODERATE |
| Mining (Gold) | 67 | 26 | 38.8% | 4% | 1.85x | STRONG |
| Mining (Gold/Copper) | 17 | 5 | 29.4% | 1% | 1.40x | MODERATE |
| Mining (State-owned) | 66 | 21 | 31.8% | 4% | 1.51x | STRONG |
| Pharmaceutical | 62 | 14 | 22.6% | 3% | 1.07x | MODERATE |
| Poultry & Feed | 62 | 10 | 16.1% | 3% | 0.77x | WEAK |
| Retail | 66 | 16 | 24.2% | 4% | 1.15x | MODERATE |
| Technology | 29 | 6 | 20.7% | 2% | 0.98x | MODERATE |
| Telecom | 134 | 22 | 16.4% | 7% | 0.78x | WEAK |

### Distance Bucket

| Category | Signals | Hits | Precision | % of Signals | Lift | Quality |
|----------|---------|------|-----------|-------------|------|---------|
| Far (<-20%) | 725 | 223 | 30.8% | 38% | 1.46x | STRONG |
| Mid (-5% to -20%) | 820 | 119 | 14.5% | 44% | 0.69x | WEAK |
| Near High (>-5%) | 339 | 54 | 15.9% | 18% | 0.76x | WEAK |

---

## Best vs Worst Contexts by Dimension

### Best Contexts

| Dimension | Best Context | Precision | Signals |
|-----------|-------------|-----------|---------|
| Volatility Bucket | High Vol | 28.1% | 650 |
| Drawdown Bucket | Deep (<-25%) | 34.2% | 524 |
| Mcap Bucket | Small (<1k) | 26.5% | 298 |
| Trend Bucket | Mixed (above MA50, below MA200) | 30.0% | 307 |
| Sector | Chemicals & Conglomerate | 42.9% | 63 |
| Distance Bucket | Far (<-20%) | 30.8% | 725 |

### Worst Contexts

| Dimension | Worst Context | Precision | Signals |
|-----------|--------------|-----------|---------|
| Volatility Bucket | Low Vol | 11.5% | 592 |
| Drawdown Bucket | Shallow (>-10%) | 14.1% | 622 |
| Mcap Bucket | Large (>5k) | 13.4% | 545 |
| Trend Bucket | Bull Trend (above MA50+200) | 16.6% | 930 |
| Sector | Consumer Goods | 9.8% | 203 |
| Distance Bucket | Mid (-5% to -20%) | 14.5% | 820 |

---

## High-Precision Combined Contexts (4-dimension)

Multi-dimensional filters where precision exceeds 30%. These represent the ideal conditions for rs_change_60d.

| Precision | Signals | Volatility | Drawdown | Trend | Distance-from-High |
|-----------|---------|-----------|----------|-------|-------------------|
| 50.0% | 12 | High Vol | Deep (<-25%) | Mixed (below MA50, above MA200) | Far (<-20%) |
| 42.9% | 14 | High Vol | Moderate (-10% to -25%) | Mixed (below MA50, above MA200) | Far (<-20%) |
| 39.0% | 41 | Medium Vol | Deep (<-25%) | Mixed (above MA50, below MA200) | Far (<-20%) |
| 36.7% | 120 | High Vol | Deep (<-25%) | Bear Trend (below both) | Far (<-20%) |
| 35.8% | 123 | High Vol | Deep (<-25%) | Mixed (above MA50, below MA200) | Far (<-20%) |
| 35.0% | 20 | High Vol | Moderate (-10% to -25%) | Mixed (above MA50, below MA200) | Far (<-20%) |
| 31.6% | 19 | Low Vol | Moderate (-10% to -25%) | Mixed (above MA50, below MA200) | Far (<-20%) |
| 30.8% | 26 | Medium Vol | Moderate (-10% to -25%) | Mixed (above MA50, below MA200) | Far (<-20%) |
| 30.8% | 39 | High Vol | Moderate (-10% to -25%) | Mixed (below MA50, above MA200) | Mid (-5% to -20%) |
| 30.7% | 127 | Medium Vol | Deep (<-25%) | Bear Trend (below both) | Far (<-20%) |
| 30.6% | 36 | High Vol | Deep (<-25%) | Bull Trend (above MA50+200) | Far (<-20%) |
| 27.3% | 22 | Medium Vol | Moderate (-10% to -25%) | Bear Trend (below both) | Far (<-20%) |
| 25.8% | 97 | Medium Vol | Shallow (>-10%) | Bull Trend (above MA50+200) | Near High (>-5%) |
| 25.4% | 63 | High Vol | Shallow (>-10%) | Bull Trend (above MA50+200) | Mid (-5% to -20%) |
| 21.9% | 64 | High Vol | Shallow (>-10%) | Bull Trend (above MA50+200) | Near High (>-5%) |
| 20.9% | 43 | Low Vol | Deep (<-25%) | Bear Trend (below both) | Far (<-20%) |
| 20.0% | 10 | Low Vol | Deep (<-25%) | Mixed (above MA50, below MA200) | Far (<-20%) |
| 19.2% | 26 | Low Vol | Moderate (-10% to -25%) | Mixed (below MA50, above MA200) | Mid (-5% to -20%) |
| 17.9% | 95 | High Vol | Moderate (-10% to -25%) | Bull Trend (above MA50+200) | Mid (-5% to -20%) |
| 17.6% | 17 | Medium Vol | Moderate (-10% to -25%) | Bull Trend (above MA50+200) | Far (<-20%) |

### Lowest Precision Contexts (Avoid)

| Precision | Signals | Volatility | Drawdown | Trend | Distance-from-High |
|-----------|---------|-----------|----------|-------|-------------------|
| 0.0% | 18 | High Vol | Moderate (-10% to -25%) | Bear Trend (below both) | Far (<-20%) |
| 2.4% | 41 | Low Vol | Shallow (>-10%) | Mixed (below MA50, above MA200) | Mid (-5% to -20%) |
| 7.4% | 27 | Low Vol | Moderate (-10% to -25%) | Bear Trend (below both) | Far (<-20%) |
| 7.5% | 80 | Low Vol | Shallow (>-10%) | Bull Trend (above MA50+200) | Mid (-5% to -20%) |
| 8.1% | 173 | Low Vol | Shallow (>-10%) | Bull Trend (above MA50+200) | Near High (>-5%) |
| 8.6% | 58 | Low Vol | Moderate (-10% to -25%) | Bear Trend (below both) | Mid (-5% to -20%) |
| 9.1% | 11 | High Vol | Moderate (-10% to -25%) | Mixed (above MA50, below MA200) | Mid (-5% to -20%) |
| 9.5% | 63 | Low Vol | Moderate (-10% to -25%) | Bull Trend (above MA50+200) | Mid (-5% to -20%) |
| 11.4% | 88 | Medium Vol | Shallow (>-10%) | Bull Trend (above MA50+200) | Mid (-5% to -20%) |
| 12.5% | 32 | Low Vol | Moderate (-10% to -25%) | Mixed (above MA50, below MA200) | Mid (-5% to -20%) |
| 14.3% | 28 | High Vol | Moderate (-10% to -25%) | Bull Trend (above MA50+200) | Far (<-20%) |
| 14.6% | 41 | Medium Vol | Moderate (-10% to -25%) | Bear Trend (below both) | Mid (-5% to -20%) |
| 16.7% | 24 | Medium Vol | Moderate (-10% to -25%) | Mixed (above MA50, below MA200) | Mid (-5% to -20%) |
| 16.8% | 107 | Medium Vol | Moderate (-10% to -25%) | Bull Trend (above MA50+200) | Mid (-5% to -20%) |
| 17.1% | 35 | Medium Vol | Moderate (-10% to -25%) | Mixed (below MA50, above MA200) | Mid (-5% to -20%) |

---

## Sector × Market Regime

| Sector | Regime | Signals | Precision |
|--------|--------|---------|-----------|
| Automotive & Conglomerate | sideways | 48 | 12.5% |
| Automotive & Conglomerate | bear | 11 | 0.0% |
| Banking | bull | 27 | 44.4% |
| Banking | sideways | 176 | 9.1% |
| Banking | bear | 42 | 2.4% |
| Banking | unknown | 13 | 0.0% |
| Cement | bull | 17 | 47.1% |
| Cement | sideways | 88 | 12.5% |
| Cement | bear | 20 | 5.0% |
| Chemicals & Conglomerate | sideways | 44 | 38.6% |
| Chemicals (Petrochemical) | sideways | 42 | 38.1% |
| Chemicals (Petrochemical) | bear | 10 | 10.0% |
| Coal Mining | bull | 15 | 40.0% |
| Coal Mining | bear | 26 | 26.9% |
| Coal Mining | sideways | 89 | 20.2% |
| Coal Mining (State-owned) | bear | 12 | 33.3% |
| Coal Mining (State-owned) | sideways | 48 | 25.0% |
| Consumer Goods | bear | 33 | 12.1% |
| Consumer Goods | sideways | 134 | 10.4% |
| Consumer Goods | bull | 25 | 8.0% |
| Consumer Goods | unknown | 11 | 0.0% |
| Energy & Logistics | sideways | 49 | 30.6% |
| Energy & Logistics | bear | 12 | 0.0% |
| Energy (Gas) | sideways | 47 | 27.7% |
| Energy (Oil & Gas) | sideways | 48 | 37.5% |
| Energy (Oil & Gas) | bear | 10 | 20.0% |
| Healthcare | bull | 17 | 35.3% |
| Healthcare | bear | 17 | 23.5% |
| Healthcare | sideways | 89 | 16.9% |
| Heavy Equipment & Mining | sideways | 43 | 25.6% |
| Heavy Equipment & Mining | bear | 12 | 0.0% |
| Mining (Gold) | sideways | 46 | 39.1% |
| Mining (Gold) | bear | 13 | 23.1% |
| Mining (State-owned) | sideways | 44 | 27.3% |
| Mining (State-owned) | bear | 13 | 23.1% |
| Pharmaceutical | sideways | 44 | 18.2% |
| Poultry & Feed | sideways | 45 | 15.6% |
| Retail | sideways | 45 | 22.2% |
| Retail | bear | 12 | 16.7% |
| Technology | sideways | 17 | 17.6% |
| Telecom | bull | 13 | 53.8% |
| Telecom | sideways | 93 | 15.0% |
| Telecom | bear | 24 | 4.2% |

---

## The Context Map: When to Use rs_change_60d

### Signal Exists & Works (USE)

Precision significantly above baseline (21%):

- **High Vol**: 28.1% precision (650 signals, 34% of all signals)
- **Deep (<-25%)**: 34.2% precision (524 signals, 28% of all signals)
- **Small (<1k)**: 26.5% precision (298 signals, 16% of all signals)
- **Mixed (above MA50, below MA200)**: 30.0% precision (307 signals, 16% of all signals)
- **Chemicals & Conglomerate**: 42.9% precision (63 signals, 3% of all signals)
- **Chemicals (Petrochemical)**: 37.1% precision (62 signals, 3% of all signals)
- **Energy & Logistics**: 26.1% precision (69 signals, 4% of all signals)
- **Energy (Gas)**: 28.1% precision (64 signals, 3% of all signals)
- **Energy (Oil & Gas)**: 36.4% precision (66 signals, 4% of all signals)
- **Mining (Gold)**: 38.8% precision (67 signals, 4% of all signals)
- **Mining (Gold/Copper)**: 29.4% precision (17 signals, 1% of all signals)
- **Mining (State-owned)**: 31.8% precision (66 signals, 4% of all signals)
- **Far (<-20%)**: 30.8% precision (725 signals, 38% of all signals)

### Signal Exists but Weak (CAUTION)

Precision near or below baseline:

- **Low Vol**: 11.5% precision (592 signals, 31% of all signals)
- **Moderate (-10% to -25%)**: 17.5% precision (738 signals, 39% of all signals)
- **Shallow (>-10%)**: 14.1% precision (622 signals, 33% of all signals)
- **Large (>5k)**: 13.4% precision (545 signals, 29% of all signals)
- **Bull Trend (above MA50+200)**: 16.6% precision (930 signals, 49% of all signals)
- **Automotive & Conglomerate**: 13.2% precision (68 signals, 4% of all signals)
- **Banking**: 11.2% precision (258 signals, 14% of all signals)
- **Cement**: 15.5% precision (129 signals, 7% of all signals)
- **Consumer Goods**: 9.8% precision (203 signals, 11% of all signals)
- **Healthcare**: 19.4% precision (129 signals, 7% of all signals)
- **Poultry & Feed**: 16.1% precision (62 signals, 3% of all signals)
- **Telecom**: 16.4% precision (134 signals, 7% of all signals)
- **Mid (-5% to -20%)**: 14.5% precision (820 signals, 44% of all signals)
- **Near High (>-5%)**: 15.9% precision (339 signals, 18% of all signals)

### Signal Should Be Ignored (AVOID)

Precision well below baseline (<18%):

- **Low Vol**: 11.5% precision (592 signals, 31% of all signals)
- **Moderate (-10% to -25%)**: 17.5% precision (738 signals, 39% of all signals)
- **Shallow (>-10%)**: 14.1% precision (622 signals, 33% of all signals)
- **Large (>5k)**: 13.4% precision (545 signals, 29% of all signals)
- **Bull Trend (above MA50+200)**: 16.6% precision (930 signals, 49% of all signals)
- **Automotive & Conglomerate**: 13.2% precision (68 signals, 4% of all signals)
- **Banking**: 11.2% precision (258 signals, 14% of all signals)
- **Cement**: 15.5% precision (129 signals, 7% of all signals)
- **Consumer Goods**: 9.8% precision (203 signals, 11% of all signals)
- **Poultry & Feed**: 16.1% precision (62 signals, 3% of all signals)
- **Telecom**: 16.4% precision (134 signals, 7% of all signals)
- **Mid (-5% to -20%)**: 14.5% precision (820 signals, 44% of all signals)
- **Near High (>-5%)**: 15.9% precision (339 signals, 18% of all signals)

---

## The BRPT vs BBCA Answer

**BRPT.JK** (Barito Pacific — Chemicals & Conglomerate): 42.9% precision

**BBCA.JK** (Bank Central Asia — Banking): 4.5% precision

Profile comparison at signal time:

| Characteristic | BRPT.JK | BBCA.JK |
|---------------|---------|---------|
| volatility_60d | 0.5593 | 0.2381 |
| drawdown_252d | -0.2563 | -0.0876 |
| distance_from_high_252d | -0.2563 | -0.0876 |
| ticker_avg_price | 1049.5687 | 6408.1996 |

| Characteristic | BRPT.JK | BBCA.JK |
|---------------|---------|---------|
| above_ma50 | 62% | 72% |
| above_ma200 | 49% | 73% |
| Typical volatility | High Vol | Low Vol |
| Typical drawdown | Deep (<-25%) | Shallow (>-10%) |
| Typical trend | Bull Trend (above MA50+200) | Bull Trend (above MA50+200) |
| Sector | Chemicals & Conglomerate | Banking |

**Root cause:** BRPT is a volatile cyclical with deep drawdowns in bear trends — exactly the conditions where rs_change_60d works. BBCA is a stable large-cap bank with shallow drawdowns in bull trends — the signal has virtually no edge there.

---
*End of RESEARCH-009B Context Filter Discovery*
