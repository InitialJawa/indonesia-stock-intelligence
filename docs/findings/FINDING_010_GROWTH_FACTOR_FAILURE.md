# ISI Finding #010: Growth Factor Failure — Alpha Leakage Source & Remediation

Laporan ini mendokumentasikan temuan riset kuantitatif terhadap faktor Growth pada model scoring ISI (Warehouse V3 / CONFIG_B). Growth merupakan sumber alpha leakage terbesar dengan bobot 30% pada Config B.

## 1. Research Question

- **Pertanyaan Riset**: Apakah faktor Growth (gabungan 50% Revenue Growth + 50% Earnings Growth) menghasilkan alpha positif atau negatif? Dapatkah diperbaiki?
- **Hipotesis**: Growth adalah faktor rusak (broken factor) yang justru menyeleksi saham underperform secara konsisten.

## 2. Root Cause Analysis

### 2.1 Faktor Decomposition

Growth didekomposisi menjadi dua komponen:

| Komponen | Formula | IC | t-stat | Signifikan? |
|----------|---------|:--:|:------:|:-----------:|
| Revenue Growth | YoY perubahan total revenue | -0.1036 | -3.05 | **Ya (negatif)** |
| Earnings Growth | YoY perubahan net income | -0.0409 | -1.14 | Tidak |
| 50/50 Blend | Rata-rata kedua komponen | -0.0846 | -2.66 | **Ya (negatif)** |

**Temuan Kunci**: Revenue Growth secara konsisten memilih saham yang underperform. Earnings Growth masih negatif namun tidak signifikan secara statistik.

### 2.2 Mengapa 50/50 Blend Lebih Buruk?

Kombinasi 50/50 justru lebih buruk dari Earnings saja karena Revenue Growth menarik IC ke bawah. Revenue Growth memiliki spread negatif lebih besar (-1.83% vs -0.13%).

## 3. Experiment Results

### Experiment A: Earnings Only

| Definisi | CAGR (Top 5) | Sharpe (Top 5) | IC | t-stat |
|----------|:-----------:|:--------------:|:--:|:------:|
| Current 50/50 (Config B) | 6.83% | 0.0205 | -0.0846 | -2.66 |
| Revenue Only | -2.72% | -0.4650 | -0.1063 | -3.05 |
| **Earnings Only** | **13.46%** | **0.3430** | **-0.0346** | **-0.95** |

Earnings-only menghilangkan alpha leakage signifikan (IC=-0.0346, t=-0.95 = tidak signifikan).

### Experiment B: Weight Reallocation (Earnings-Only Growth)

| Config | Quality | Growth | Value | Momentum | LowVol | CAGR | Sharpe | Max DD |
|--------|:-------:|:------:|:-----:|:--------:|:------:|:----:|:------:|:------:|
| Config B (prod) | 25% | 30% | 10% | 35% | — | 13.46% | 0.3430 | -30.48% |
| Config D | 25% | 15% | 25% | 35% | — | 11.73% | 0.2663 | -20.76% |
| Config E | 25% | 15% | 20% | 30% | 10% | 13.36% | 0.4179 | -12.42% |
| **Config F** | **25%** | **10%** | **30%** | **35%** | **—** | **15.13%** | **0.4339** | **-14.05%** |

**Config F (25/10/30/35)** memberikan hasil terbaik: CAGR 15.13%, Sharpe 0.4339, Max DD -14.05%.

### Experiment C: Growth Replacement

| Config | CAGR | Sharpe | Max DD |
|--------|:----:|:------:|:------:|
| Config B (prod) | 6.83% | 0.0205 | -29.17% |
| Replace w/ LowVol (25/0/20/35/20) | 9.53% | 0.1237 | -13.71% |
| Replace w/ Dividend (25/0/20/35/20) | 2.24% | -0.3515 | -16.90% |

LowVol lebih baik dari Config B namun tidak sebaik Config F. Dividend justru merusak performa.

## 4. Final Recommendation

### Verdict Matrix

| Pertanyaan | Jawaban | Evidence |
|-----------|---------|----------|
| Revenue Growth bermasalah? | **Ya** | IC=-0.1036, t=-3.05 — signifikan negatif |
| Earnings-only menghilangkan leakage? | **Sebagian** | IC=-0.0346 tidak signifikan, netral |
| Growth layak dipertahankan? | **Tidak (bobot 30% terlalu besar)** | Bobot optimum 10-15% |
| Growth weight harus turun? | **Ya, dari 30% ke 10-15%** | Config F (10%) unggul |
| Value harus dinaikkan? | **Ya, dari 10% ke 25-30%** | Value IC tertinggi (0.0805) |
| LowVol lebih berguna dari Growth? | **Ya** | Config E (dengan LowVol) Sharpe 0.4179 |
| Dividend lebih berguna dari Growth? | **Tidak** | Replacement Dividend Sharpe -0.3515 |

### Konfigurasi Terbaik (Final)

**TOP CHOICE: Config F** — Quality 25%, Growth (Earnings) 10%, Value 30%, Momentum 35%
- CAGR: 15.13% (vs 6.83% Config B)
- Sharpe: 0.4339 (vs 0.0205 Config B)
- Max DD: -14.05% (vs -29.17% Config B)

**ALTERNATIVE: Config E** — Quality 25%, Growth (Earnings) 15%, Value 20%, Momentum 30%, LowVol 10%
- Sharpe: 0.4179
- Max DD: -12.42% (terendah)

### Implementation Path

1. **Segera**: Switch Growth ke Earnings-only formula
2. **Jangka pendek**: Implementasi Config F (25/10/30/35) untuk Top 5
3. **Jangka menengah**: Evaluasi Config E dengan LowVol untuk Max DD lebih rendah
4. **Jangan implementasi**: Revenue Growth harus dihapus, Dividend replacement tidak direkomendasikan

## 5. Referensi

- `reports/research_growth_earnings_only.md` — Experiment A detail
- `reports/research_weight_reallocation.md` — Experiment B detail  
- `reports/research_growth_replacement.md` — Experiment C detail
- `reports/growth_factor_autopsy.md` — Growth decomposition analysis
- `reports/alpha_generation_audit.md` — Factor IC audit
