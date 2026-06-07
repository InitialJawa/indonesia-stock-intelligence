# Momentum Portfolio Backtest Report

Laporan kinerja portofolio momentum historis dibandingkan dengan tolok ukur IHSG.

## 1. Ringkasan Kinerja (Performance Summary)

| Parameter | Portofolio Momentum | Benchmark (IHSG) | Selisih (Excess) |
| :--- | :---: | :---: | :---: |
| **CAGR** | 0.82% | -0.87% | +1.69% |
| **Annualized Return** | 4.94% | 0.37% | +4.57% |
| **Volatility (Annualized)** | 28.56% | 15.53% | +13.03% |
| **Sharpe Ratio** | 0.17 | 0.02 | +0.15 |
| **Max Drawdown** | 39.66% | 29.83% | +9.83% |
| **Best Month** | 25.21% | 9.44% | - |
| **Worst Month** | -22.82% | -16.76% | - |
| **Win Rate (Monthly)** | 55.68% | 56.82% | - |

## 2. Parameter Alpha & Beta vs IHSG

- **Beta vs IHSG**: `1.285`
- **Annualized CAPM Alpha**: `+4.47%` (Bulanan: `+0.372%`)

## 3. Validasi Data & Integritas

- **Jumlah Bulan Portfolio Evaluasi**: `88` bulan (Holdings dari `2019-01` ke `2026-04`)
- **Jumlah Bulan Return Terkalkulasi**: `88` bulan (`2019-02` sampai `2026-05`)
- **Missing Return Check**: Lulus (0 missing return values)
- **Equity Curve Calculation**: Lulus (Terkalkulasi penuh sampai akhir)

## 4. Kesimpulan Akhir

Berdasarkan analisis perbandingan CAGR historis, Portofolio Momentum dinyatakan:

> [!IMPORTANT]
> **Mengalahkan IHSG**
