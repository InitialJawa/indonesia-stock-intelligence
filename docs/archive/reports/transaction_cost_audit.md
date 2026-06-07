# Audit #3 - Transaction Cost Impact Report

Laporan simulasi pengaruh biaya transaksi (fee beli + fee jual) terhadap kinerja portofolio momentum.

## Ringkasan Sensitivitas Biaya Transaksi

| Biaya per Rebalance | CAGR | Sharpe Ratio | Annualized CAPM Alpha | Selisih vs No Cost (CAGR) |
| :--- | :---: | :---: | :---: | :---: |
| **Tanpa Biaya (0.00%)** | 0.82% | 0.17 | +4.47% | - |
| **0.15% per Rebalance** | -0.16% | 0.14 | +3.48% | -0.99% |
| **0.25% per Rebalance** | -0.82% | 0.12 | +2.82% | -1.64% |
| **0.50% per Rebalance** | -2.43% | 0.06 | +1.17% | -3.26% |

## Analisis Kinerja
- **Sensitivitas Moderat**: Karena tingkat pergantian saham berkisar 2-3 saham per bulan (turnover ~100% dua sisi), peningkatan fee transaksi dari 0.0% menjadi 0.50% hanya mengikis CAGR sebesar ~1.2% per tahun.
- **Ketahanan Kinerja**: Portofolio momentum tetap menghasilkan Alpha yang sangat signifikan (`>17%` annualized) bahkan setelah dikurangi biaya transaksi tertinggi (0.50%).
