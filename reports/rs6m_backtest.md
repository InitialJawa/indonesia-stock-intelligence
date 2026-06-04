# Factor 006 (Relative Strength 6M / RS-6M) Standalone Backtest Report

Laporan kinerja portofolio Relative Strength 6 bulan historis dibandingkan dengan Momentum (Config B) dan tolok ukur IHSG.

## 1. Ringkasan Kinerja (Performance Summary)

| Parameter | Portofolio RS-6M | Portofolio Momentum | Benchmark (IHSG) | Selisih RS-6M vs IHSG |
| :--- | :---: | :---: | :---: | :---: |
| **CAGR** | 41.28% | 0.82% | -0.87% | +42.15% |
| **Annualized Return** | 42.22% | 4.94% | 0.37% | +41.85% |
| **Volatility (Annualized)** | 39.14% | 28.56% | 15.53% | +23.61% |
| **Sharpe Ratio** | 1.08 | 0.17 | 0.02 | +1.06 |
| **Max Drawdown** | 37.87% | 39.66% | 29.83% | +8.03% |
| **Best Month** | 36.63% | 25.21% | 9.44% | - |
| **Worst Month** | -24.05% | -22.82% | -16.76% | - |
| **Win Rate (Monthly)** | 62.50% | 55.68% | 56.82% | - |

## 2. Parameter Alpha & Beta vs IHSG

| Parameter | Portofolio RS-6M | Portofolio Momentum |
| :--- | :---: | :---: |
| **Beta vs IHSG** | `1.433` | `1.285` |
| **Annualized CAPM Alpha** | `+41.70%` | `+4.47%` |
| **Monthly CAPM Alpha** | `+3.475%` | `+0.372%` |

## 3. Kinerja Kalender Tahunan (Yearly Breakdown)

| Tahun | Portofolio RS-6M | Portofolio Momentum | Benchmark (IHSG) | Selisih RS-6M vs IHSG |
| :---: | :---: | :---: | :---: | :---: |
| **2019** | 64.79% | 0.30% | -3.57% | +68.36% |
| **2020** | 97.91% | -10.51% | -5.09% | +103.00% |
| **2021** | 143.23% | 3.46% | 10.08% | +133.16% |
| **2022** | 64.74% | 15.06% | 4.09% | +60.65% |
| **2023** | -4.49% | -3.94% | 6.16% | -10.66% |
| **2024** | 23.99% | -5.18% | -2.65% | +26.64% |
| **2025** | 31.05% | 39.17% | 22.13% | +8.92% |
| **2026** | -37.85% | -21.59% | -29.14% | -8.71% |

## 4. Validasi Data & Integritas

- **Jumlah Bulan Portfolio Evaluasi**: `88` bulan (Holdings dari `2019-01` ke `2026-04`)
- **Jumlah Bulan Return Terkalkulasi**: `88` (`2019-02` sampai `2026-05`)
- **IPO Listing date gate check**: Lulus (Seluruh ticker diverifikasi listing sebelum lookback start untuk mencegah backfill bias)
- **Equity Curve Calculation**: Lulus (Terkalkulasi penuh sampai akhir)

## 5. Kesimpulan Akhir

Berdasarkan analisis perbandingan CAGR historis, Portofolio RS-6M dinyatakan:

> [!IMPORTANT]
> **Mengalahkan IHSG**
