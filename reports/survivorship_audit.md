# Audit #2 - Survivorship Bias Report

Laporan analisis survivorship bias dalam backtest momentum pasar saham Indonesia.

## 1. Pertanyaan Kunci

**Apakah universe menggunakan komposisi IDX30 modern untuk seluruh periode historis?**

> **YA.** Universe pengujian menggunakan konstituen IDX30 per tahun 2026 secara statis dari awal periode backtest (`2019-01`).

## 2. Dampak Survivorship Bias
Penggunaan konstituen modern statis untuk periode historis menimbulkan bias yang signifikan:
1. **Selection Bias**: Tickers yang berkinerja buruk dan dikeluarkan dari IDX30 sebelum tahun 2026 sepenuhnya diabaikan dari analisis historis, sehingga performa historis portofolio terlihat jauh lebih baik daripada realitas pasar sebenarnya.
2. **Listing Date Bias (Backfill Bias)**: Beberapa ticker belum melantai di bursa (belum IPO) pada awal periode pengujian (`2019-01`).

## 3. Daftar Ticker IPO Baru (Penyebab Bias)
Berikut adalah saham IDX30 modern yang belum ada atau baru melantai di bursa selama periode backtest:

| Ticker | Tanggal IPO/Data Terawal | Dampak pada Awal Backtest (2019-2022) |
| :--- | :---: | :--- |
| **HEAL** | `2018-05-31` | Diabaikan otomatis dari ranking sebelum tanggal IPO (mengurangi universe aktif). |
| **GOTO** | `2022-04-30` | Diabaikan otomatis dari ranking sebelum tanggal IPO (mengurangi universe aktif). |
| **AMMN** | `2023-07-31` | Diabaikan otomatis dari ranking sebelum tanggal IPO (mengurangi universe aktif). |

## 4. Kesimpulan Rekomendasi
- Backtest ini memiliki **Survivorship Bias Tinggi**.
- **Rekomendasi**: Untuk validasi produksi, universe harus diubah menggunakan konstituen IDX30 dinamis (membaca daftar konstituen aktual di setiap bulan $t$).
