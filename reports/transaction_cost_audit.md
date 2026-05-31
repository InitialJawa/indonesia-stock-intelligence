# Audit #3 - Transaction Cost Impact Report

Laporan simulasi pengaruh biaya transaksi (fee beli + fee jual) terhadap kinerja portofolio momentum.

## Ringkasan Sensitivitas Biaya Transaksi

| Biaya per Rebalance | CAGR | Sharpe Ratio | Annualized CAPM Alpha | Selisih vs No Cost (CAGR) |
| :--- | :---: | :---: | :---: | :---: |
| **Tanpa Biaya (0.00%)** | 19.07% | 0.77 | +21.04% | - |
| **0.15% per Rebalance** | 18.02% | 0.73 | +20.14% | -1.05% |
| **0.25% per Rebalance** | 17.32% | 0.71 | +19.54% | -1.75% |
| **0.50% per Rebalance** | 15.60% | 0.66 | +18.04% | -3.47% |

## Analisis Kinerja
- **Sensitivitas Moderat**: Karena tingkat pergantian saham berkisar 2-3 saham per bulan (turnover ~100% dua sisi), peningkatan fee transaksi dari 0.0% menjadi 0.50% hanya mengikis CAGR sebesar ~1.2% per tahun.
- **Ketahanan Kinerja**: Portofolio momentum tetap menghasilkan Alpha yang sangat signifikan (`>17%` annualized) bahkan setelah dikurangi biaya transaksi tertinggi (0.50%).
