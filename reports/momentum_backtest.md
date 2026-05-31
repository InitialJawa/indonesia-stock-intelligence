# Momentum Portfolio Backtest Report

Laporan kinerja portofolio momentum historis dibandingkan dengan tolok ukur IHSG.

## 1. Ringkasan Kinerja (Performance Summary)

| Parameter | Portofolio Momentum | Benchmark (IHSG) | Selisih (Excess) |
| :--- | :---: | :---: | :---: |
| **CAGR** | 19.07% | -0.87% | +19.94% |
| **Annualized Return** | 21.46% | 0.37% | +21.10% |
| **Volatility (Annualized)** | 28.05% | 15.53% | +12.53% |
| **Sharpe Ratio** | 0.77 | 0.02 | +0.74 |
| **Max Drawdown** | 36.99% | 29.83% | +7.16% |
| **Best Month** | 24.05% | 9.44% | - |
| **Worst Month** | -20.72% | -16.76% | - |
| **Win Rate (Monthly)** | 62.50% | 56.82% | - |

## 2. Parameter Alpha & Beta vs IHSG

- **Beta vs IHSG**: `1.151`
- **Annualized CAPM Alpha**: `+21.04%` (Bulanan: `+1.753%`)

## 3. Validasi Data & Integritas

- **Jumlah Bulan Portfolio Evaluasi**: `88` bulan (Holdings dari `2019-01` ke `2026-04`)
- **Jumlah Bulan Return Terkalkulasi**: `88` bulan (`2019-02` sampai `2026-05`)
- **Missing Return Check**: Lulus (0 missing return values)
- **Equity Curve Calculation**: Lulus (Terkalkulasi penuh sampai akhir)

## 4. Kesimpulan Akhir

Berdasarkan analisis perbandingan CAGR historis, Portofolio Momentum dinyatakan:

> [!IMPORTANT]
> **Mengalahkan IHSG**
