# Laporan Kelayakan Rekonstruksi Historis V6 (2018-2026)

Laporan ini disusun oleh AI Architect untuk memvalidasi kelayakan pembangunan **V6 Historical Reconstruction Engine & Walk Forward Backtest** sejak tahun **2018** menggunakan data FMP dan Yahoo Finance.

---

## A. Kesimpulan Kelayakan (Feasibility Study)
**FEASIBLE (SANGAT LAYAK)**

Proyek rekonstruksi data fundamental historis IDX30 dari tahun 2018 hingga 2026 sepenuhnya layak untuk dilaksanakan. FMP menyediakan data laporan keuangan terstandardisasi untuk emiten Bursa Efek Indonesia (IDX) dengan history yang cukup panjang (sejak 2018) dan pemetaan metrik yang presisi.

---

## B. Data yang Tersedia
Melalui endpoint FMP dan Yahoo Finance, kita memiliki akses ke data berikut untuk kebutuhan rekonstruksi:
1. **Laporan Keuangan Tahunan & Kuartalan (FMP)**:
   * Neraca (Balance Sheet): Aset, Liabilitas, Ekuitas pemegang saham (untuk DER).
   * Laba Rugi (Income Statement): Pendapatan (Revenue), Laba Operasional, Laba Bersih (untuk Margins & Growth).
   * Arus Kas (Cash Flow): Arus kas operasi, Capital Expenditure (untuk FCF).
2. **Rasio Keuangan Terhitung (FMP)**:
   * ROE, Net Margin, Operating Margin, DER, PE Ratio, dan PB Ratio yang sudah dihitung per tanggal pelaporan keuangan (ttm).
3. **Data Harga Historis & Volume Harian (YFinance / FMP)**:
   * Harga penutupan harian dan volume transaksi saham IDX30 sejak 2018 (untuk menghitung return momentum 6M/12M dan volume shock).

---

## C. Data yang Tidak Tersedia / Terbatas
Terdapat beberapa batasan data yang perlu diwaspadai:
1. **Rasio PE dan PB Historis Harian/Bulanan**:
   * FMP menyediakan rasio PE dan PB hanya pada tanggal rilis laporan keuangan. Untuk mendapatkan PE dan PB historis bulanan secara dinamis (misal pada setiap tanggal rebalancing bulanan), kita harus menghitungnya secara manual menggunakan:
     `PE = Harga Saham pada Tanggal Rebalance / Laba per Saham (EPS) terakhir`
     `PB = Harga Saham pada Tanggal Rebalance / Nilai Buku per Saham (BPS) terakhir`
   * Solusi: Data ini bisa dihitung (derived) di memori menggunakan data harga historis harian dari Yahoo Finance digabungkan dengan EPS/BPS historis dari FMP.
2. **Foreign Flow Historis Bulanan (Historis Bandar Asing)**:
   * FMP tidak menyediakan data akumulasi net buy asing (Foreign Flow) untuk pasar Indonesia secara mendalam.
   * Solusi: Kita dapat memanfaatkan API/sumber lokal atau tetap menggunakan data net buy asing historis dari Yahoo Finance (jika tersedia kolom volume/net flow) atau membatasi pengujian tanpa faktor asing pada backtest masa lalu yang terlalu jauh, atau mengambil arsip yang sudah ada di database lokal.

---

## D. Estimasi Effort Pembangunan
Berikut adalah rincian estimasi pengerjaan modul V6:

| Modul | Deskripsi Pekerjaan | Estimasi Waktu | Bobot Kesulitan |
| :--- | :--- | :--- | :--- |
| **Historical Collector** | Membuat skrip pengumpul data historis laporan keuangan tahunan/kuartalan IDX30 sejak 2018 dari FMP dan menyimpannya ke basis data lokal (`database/historical/raw_fundamentals.json`). | 2 Hari | Sedang |
| **Historical Factor Builder** | Mengintegrasikan parser untuk menghitung faktor Quality, Growth, dan Value bulanan secara historis (Point-in-Time) untuk menghindari look-ahead bias. | 3 Hari | Tinggi |
| **Historical Ranking Builder** | Membuat modul penskoran persentil berjalan (rolling percentile) dari bulan ke bulan sejak 2018 untuk melacak evolusi peringkat. | 2 Hari | Sedang |
| **Walk Forward Backtest** | Membangun mesin simulasi transaksi bulanan yang mengeksekusi rebalancing portofolio, menghitung biaya transaksi, dan membandingkan return portofolio V6 terhadap benchmark IHSG. | 3 Hari | Tinggi |

**Total Estimasi Effort: 10 Hari Kerja**

---

## E. Rekomendasi Langkah Berikutnya
1. **Integrasikan FMP Key**: Daftarkan kunci API FMP yang valid ke environment variable produksi (`FMP_API_KEY`) di GitHub Secrets.
2. **Kembangkan Historical Collector**: Prioritaskan pembuatan collector laporan keuangan tahunan/kuartalan terlebih dahulu untuk mengisi `database/historical/` dengan data sejak 2018.
3. **Validasi Perhitungan PE/PB Point-in-Time**: Pastikan algoritma penggabungan harga saham historis bulanan dengan data laporan keuangan terakhir tidak mengalami kebocoran data masa depan (look-ahead bias).
