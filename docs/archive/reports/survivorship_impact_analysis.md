# Survivorship Bias Impact Analysis

Laporan ini membandingkan kinerja strategi momentum **sebelum** dan **sesudah** remediasi *survivorship bias* melalui rekonstruksi semesta IDX30 historis yang benar.

---

## 1. Metodologi Perbandingan

| Parameter | V6.2.2 (Lama) | V6.2.3 (Baru) |
| :--- | :--- | :--- |
| **Semesta Ticker** | Modern IDX30 2026 (statis) | Historical IDX30 dinamis (2019–2026) |
| **Jumlah Ticker Unik** | 30 tickers | 64 tickers (termasuk delisted) |
| **Filter Listing Date** | Ya (basic) | Ya (extended metadata) |
| **Bias Universe** | **HIGH (Survivorship Bias)** | **MITIGATED** |

---

## 2. Perbandingan Kinerja Utama

| Parameter Kinerja | V6.2.2 (Lama) | V6.2.3 (Baru) | Delta |
| :--- | :---: | :---: | :---: |
| **CAGR** | 19.07% | 0.82% | **-18.25%** |
| **Annualized Return** | 21.46% | 4.94% | -16.52% |
| **Annualized Volatility** | 28.05% | 28.56% | +0.51% |
| **Sharpe Ratio** | 0.77 | 0.17 | **-0.60** |
| **Max Drawdown** | 36.99% | 39.66% | +2.67% |
| **Win Rate (Bulanan)** | 62.50% | 55.68% | -6.82% |
| **Beta vs IHSG** | 1.151 | 1.285 | +0.134 |
| **CAPM Alpha (Ann.)** | +21.04% | +4.47% | **-16.57%** |

---

> [!CAUTION]
> **Quantified Survivorship Bias:** Penggunaan semesta modern statis (2026) secara artifisial **melebih-lebihkan CAGR sebesar 18.25%** (19.07% vs 0.82%). Sharpe Ratio tergelembung dari **0.77** menjadi **0.17** secara riil.

---

## 3. Kinerja Tahunan Baru (V6.2.3)

| Tahun | Portfolio Return | IHSG Return | Excess Return |
| :---: | :---: | :---: | :---: |
| **2019** | 0.30% | -3.57% | +3.87% |
| **2020** | -10.51% | -5.09% | -5.43% |
| **2021** | 3.46% | 10.08% | -6.61% |
| **2022** | 15.06% | 4.09% | +10.97% |
| **2023** | -3.94% | 6.16% | -10.10% |
| **2024** | -5.18% | -2.65% | -2.53% |
| **2025** | 39.17% | 22.13% | +17.03% |
| **2026** | -21.59% | -29.14% | +7.55% |

---

## 4. Kesimpulan: Status FINDING_001

Berdasarkan rekonstruksi semesta IDX30 historis yang benar:

- **CAGR Portofolio Momentum (baru):** `0.82%`
- **CAGR IHSG (benchmark):** `-0.87%`
- **Selisih (Excess CAGR):** `+1.69%`

> [!IMPORTANT]
> ### FINDING_001: Momentum IDX30 Mengalahkan IHSG
> Status: **VALID (TERKONFIRMASI, namun dengan alpha yang jauh lebih rendah)**
>
> Portofolio momentum **masih** mengalahkan IHSG bahkan setelah semesta historis diterapkan. Namun, alpha yang sebelumnya tampak sangat besar (`+21.04% CAPM alpha`) ternyata digelembungkan secara artifisial oleh *survivorship bias*. Alpha yang **sesungguhnya** adalah jauh lebih rendah, yaitu `+4.47%`.

---

## 5. Rekomendasi Lanjutan

1. **Strategi Portofolio Lebih Luas**: Pertimbangkan menambah jumlah saham dari 5 menjadi 10 untuk mengurangi volatilitas idiosinkratik yang lebih tinggi dalam semesta yang lebih beragam.
2. **Kombinasi Faktor**: Momentum murni menunjukkan volatilitas tinggi. Mengkombinasikan dengan filter kualitas (ROE, profitabilitas) dapat meningkatkan Sharpe.
3. **Benchmark Dinamis**: Pertimbangkan menggunakan LQ45 atau IDX Growth sebagai benchmark alternatif untuk representasi yang lebih akurat.
