# Factor 006 (Relative Strength 6M / RS-6M) Standalone Backtest Report

Laporan kinerja portofolio Relative Strength 6 bulan historis dibandingkan dengan Momentum (Config B) dan tolok ukur IHSG.

## 1. Ringkasan Kinerja (Performance Summary)

| Parameter | Portofolio RS-6M | Portofolio Momentum | Benchmark (IHSG) | Selisih RS-6M vs IHSG |
| :--- | :---: | :---: | :---: | :---: |
| **CAGR** | 1.21% | 0.82% | -0.87% | +2.08% |
| **Annualized Return** | 6.12% | 4.94% | 0.37% | +5.75% |
| **Volatility (Annualized)** | 31.13% | 28.56% | 15.53% | +15.60% |
| **Sharpe Ratio** | 0.20 | 0.17 | 0.02 | +0.17 |
| **Max Drawdown** | 57.27% | 39.66% | 29.83% | +27.43% |
| **Best Month** | 32.02% | 25.21% | 9.44% | - |
| **Worst Month** | -32.61% | -22.82% | -16.76% | - |
| **Win Rate (Monthly)** | 50.00% | 55.68% | 56.82% | - |

## 2. Parameter Alpha & Beta vs IHSG

| Parameter | Portofolio RS-6M | Portofolio Momentum |
| :--- | :---: | :---: |
| **Beta vs IHSG** | `1.393` | `1.285` |
| **Annualized CAPM Alpha** | `+5.60%` | `+4.47%` |
| **Monthly CAPM Alpha** | `+0.467%` | `+0.372%` |

## 3. Kinerja Kalender Tahunan (Yearly Breakdown)

| Tahun | Portofolio RS-6M | Portofolio Momentum | Benchmark (IHSG) | Selisih RS-6M vs IHSG |
| :---: | :---: | :---: | :---: | :---: |
| **2019** | 3.38% | 0.30% | -3.57% | +6.96% |
| **2020** | -11.16% | -10.51% | -5.09% | -6.07% |
| **2021** | 15.85% | 3.46% | 10.08% | +5.77% |
| **2022** | 27.19% | 15.06% | 4.09% | +23.10% |
| **2023** | -12.77% | -3.94% | 6.16% | -18.93% |
| **2024** | -5.01% | -5.18% | -2.65% | -2.36% |
| **2025** | 43.69% | 39.17% | 22.13% | +21.55% |
| **2026** | -32.21% | -21.59% | -29.14% | -3.07% |

## 4. Validasi Data & Integritas

- **Jumlah Bulan Portfolio Evaluasi**: `88` bulan (Holdings dari `2019-01` ke `2026-04`)
- **Jumlah Bulan Return Terkalkulasi**: `88` (`2019-02` sampai `2026-05`)
- **IPO Listing date gate check**: Lulus (Seluruh ticker diverifikasi listing sebelum lookback start untuk mencegah backfill bias)
- **Equity Curve Calculation**: Lulus (Terkalkulasi penuh sampai akhir)

## 5. Kesimpulan Akhir

Berdasarkan analisis perbandingan CAGR historis, Portofolio RS-6M dinyatakan:

> [!IMPORTANT]
> **Mengalahkan IHSG**
