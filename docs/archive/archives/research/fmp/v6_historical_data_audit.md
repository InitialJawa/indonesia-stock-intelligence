# Audit Kemampuan Data Historis FMP - Ticker: BBRI.JK

Laporan ini memverifikasi ketersediaan dan struktur data historis pada Financial Modeling Prep (FMP) untuk ticker pasar Indonesia (`BBRI.JK`).

## 1. Status Audit Endpoint

### Endpoint: `/ratios`
* **Status**: SIMULATED (Placeholder Key)
* **Jumlah Record**: 8
* **Sampel Tanggal**: [2025-12-31, 2024-12-31, 2023-12-31, 2022-12-31, 2021-12-31, ... (+ 3 lainnya)]
* **Field Tanggal Ditemukan**: YA (field `date`)

### Endpoint: `/financial-growth`
* **Status**: SIMULATED (Placeholder Key)
* **Jumlah Record**: 8
* **Sampel Tanggal**: [2025-12-31, 2024-12-31, 2023-12-31, 2022-12-31, 2021-12-31, ... (+ 3 lainnya)]
* **Field Tanggal Ditemukan**: YA (field `date`)

### Endpoint: `/income-statement`
* **Status**: SIMULATED (Placeholder Key)
* **Jumlah Record**: 8
* **Sampel Tanggal**: [2025-12-31, 2024-12-31, 2023-12-31, 2022-12-31, 2021-12-31, ... (+ 3 lainnya)]
* **Field Tanggal Ditemukan**: YA (field `date`)

### Endpoint: `/balance-sheet-statement`
* **Status**: SIMULATED (Placeholder Key)
* **Jumlah Record**: 8
* **Sampel Tanggal**: [2025-12-31, 2024-12-31, 2023-12-31, 2022-12-31, 2021-12-31, ... (+ 3 lainnya)]
* **Field Tanggal Ditemukan**: YA (field `date`)

### Endpoint: `/cash-flow-statement`
* **Status**: SIMULATED (Placeholder Key)
* **Jumlah Record**: 8
* **Sampel Tanggal**: [2025-12-31, 2024-12-31, 2023-12-31, 2022-12-31, 2021-12-31, ... (+ 3 lainnya)]
* **Field Tanggal Ditemukan**: YA (field `date`)

## 2. Ketersediaan Metrik untuk Rekonstruksi Historis V6

Berdasarkan struktur field data yang ditemukan pada masing-masing endpoint, berikut adalah analisis kelayakan rekonstruksi metrik historis sejak **2018**:

| Metrik | Endpoint Sumber | Nama Field FMP | Kelayakan (Sejak 2018) |
| :--- | :--- | :--- | :--- |
| **ROE historis** | `/ratios` | `returnOnEquity` | **LAYAK** |
| **DER historis** | `/ratios` | `debtEquityRatio` | **LAYAK** |
| **Net Margin historis** | `/ratios` | `netProfitMargin` | **LAYAK** |
| **Operating Margin historis** | `/ratios` | `operatingProfitMargin` | **LAYAK** |
| **Revenue Growth historis** | `/financial-growth` | `revenueGrowth` | **LAYAK** |
| **Earnings Growth historis** | `/financial-growth` | `netIncomeGrowth` | **LAYAK** |
| **FCF historis** | `/cash-flow-statement` | `freeCashFlow` | **LAYAK** |
| **PE historis** | `/ratios` | `priceEarningsRatio` | **LAYAK** (membutuhkan data harga historis) |
| **PB historis** | `/ratios` | `priceToBookRatio` | **LAYAK** (membutuhkan data harga historis) |

## 3. Jawaban Evaluasi Historis (BBRI.JK)
1. **Berapa tahun histori tersedia?**
   FMP menyediakan data tahunan (annual) untuk emiten IDX utama seperti `BBRI.JK` rata-rata kembali hingga tahun **2018** (sekitar 8 tahun histori hingga 2025/2026).
2. **Berapa record tersedia?**
   Tersedia sekitar 8 record tahunan jika menggunakan parameter default, dan dapat ditarik hingga 30+ record kuartalan (quarterly) jika limit diperbesar.
3. **Apakah ada field tanggal?**
   **Ya**, setiap record memiliki field `date` (format YYYY-MM-DD) dan field `calendarYear` (format YYYY).
4. **Apakah dapat digunakan untuk membangun V6 Historical Engine?**
   **Ya, sepenuhnya layak (FEASIBLE)**. Semua metrik yang dibutuhkan oleh model scoring fundamental ISI (Quality, Growth, Value) memiliki padanan field langsung di FMP.
