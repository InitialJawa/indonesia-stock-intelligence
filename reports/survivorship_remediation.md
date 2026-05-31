# Survivorship Bias Remediation Report

Laporan perbandingan kinerja backtest sebelum dan sesudah penerapan filter tanggal IPO/listing saham untuk mengeliminasi survivorship dan backfill bias.

## 1. Perubahan Programatik
- **Audit Listing**: Mengidentifikasi tanggal listing terawal dari 30 saham dalam database. Hasil disimpan di [ticker_metadata.csv](file:///c:/Users/Bedil Gaib/.gemini/antigravity/scratch/indonesia-stock-intelligence/database/historical/ticker_metadata.csv).
- **Prosedur Filtrasi**: Memodifikasi [historical_momentum_builder.py](file:///c:/Users/Bedil Gaib/.gemini/antigravity/scratch/indonesia-stock-intelligence/historical_momentum_builder.py) untuk secara eksplisit menolak ticker masuk ke dalam ranking bulanan jika `month_key < listing_date[:7]`.
- **Rerun Pipeline**: Menjalankan ulang rekonstruksi momentum, portofolio, dan perhitungan performa backtest.

## 2. Perbandingan Kinerja

Berikut adalah perbandingan metrik performa utama sebelum dan sesudah remediasi bias dilakukan:

| Parameter Kinerja | Sebelum Remediasi | Sesudah Remediasi | Perubahan (Delta) |
| :--- | :---: | :---: | :---: |
| **CAGR** | **19.07%** | **19.07%** | **0.00%** |
| **Annualized Return** | 21.46% | 21.46% | 0.00% |
| **Annualized Volatility** | 28.05% | 28.05% | 0.00% |
| **Sharpe Ratio** | 0.77 | 0.77 | 0.00 |
| **Max Drawdown** | 36.99% | 36.99% | 0.00% |
| **Win Rate (Monthly)** | 62.50% | 62.50% | 0.00% |
| **Beta vs IHSG** | 1.151 | 1.151 | 0.000 |
| **Annualized CAPM Alpha** | +21.04% | +21.04% | 0.00% |

## 3. Analisis Hasil
Kinerja portofolio sebelum dan sesudah remediasi adalah **identik (0.00% delta)**. Alasan teknis di balik temuan ini adalah:
1. **Tidak Ada Backfill Data**: File CSV asli di `database/monthly/` untuk saham IPO baru (seperti `AMMN.JK` per `2023-07` dan `GOTO.JK` per `2022-04`) memang tidak memiliki baris data harga atau return sama sekali sebelum tanggal listing resmi mereka.
2. **Skiping Otomatis**: Secara implisit, kode asli kami mengabaikan ticker jika data bulan tersebut tidak ada dalam file riwayat ticker. Dengan demikian, penambahan gate listing resmi secara eksplisit memformalkan validasi tanpa mengubah data aktual yang diproses.

## 4. Rekomendasi Lanjutan
Meskipun backfill bias IPO teratasi, **survivorship bias akibat modern-constituent selection** masih tersisa:
- Portofolio historis hanya memilih dari 30 saham IDX30 modern (tahun 2026).
- Untuk menghilangkan bias ini sepenuhnya, kita memerlukan basis data **konstituen IDX30 dinamis** yang mencatat komposisi indeks aktual di setiap titik waktu masa lalu.
