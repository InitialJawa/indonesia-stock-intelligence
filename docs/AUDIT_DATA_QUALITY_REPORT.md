# AUDIT-001: Laporan Kualitas Data

**Tanggal:** 2026-06-07
**Lingkup:** Seluruh anggota IDX30 (30 saham)
**Sumber Data:** Yahoo Finance (via `utils/data_provider.py`)

---

## Ringkasan Temuan

Data fundamental IDX30 mengandung **2 masalah kritis**, **1 masalah sedang**, dan **1 masalah minor**.
Perbaikan telah dilakukan untuk masalah kritis PBV (7 saham diperbaiki), sedangkan MDKA masih belum bisa diperbaiki karena data PE tidak tersedia.

---

## Masalah Kritis

### KR-01: PBV tidak wajar akibat data Yahoo Finance

| Ticker | Yahoo PBV | Seharusnya (PE×ROE) | Sumber |
|--------|-----------|---------------------|--------|
| ADRO.JK | 13.176,47 | 0,74 | `priceToBook` scaling error |
| AMMN.JK | 43.289,48 | 2,36 | `priceToBook` scaling error |
| TPIA.JK | 30.348,84 | 1,46 | `priceToBook` scaling error |
| BRPT.JK | 59.200,00 | 4,74 | `priceToBook` scaling error |
| PGAS.JK | 12.991,45 | 0,85 | `priceToBook` scaling error |
| ESSA.JK | 21.666,67 | 1,33 | `priceToBook` scaling error |
| ITMG.JK | 12.732,56 | 0,71 | `priceToBook` scaling error |

**Akar masalah:** Yahoo Finance mengembalikan `priceToBook` dalam unit/skala yang salah untuk saham-saham komoditas dan pertambangan Indonesia. Nilai yang benar dihitung dari `pe_ratio × returnOnEquity` (PBV = PE × ROE, terbukti secara matematis).

**Dampak terhadap scoring:** Value score untuk 7 saham ini sangat rendah (mendekati 0) karena percentil PBV yang terbalik. Setelah diperbaiki, value score naik secara signifikan (contoh: ADRO dari 46,21 menjadi 62,07).

**Dampak terhadap dashboard:** Panel saham menampilkan PBV hingga puluhan ribu — membingungkan dan tidak informatif.

**Perbaikan:** ✅ `collectors/fundamentals.py` — validasi PBV > 100, hitung ulang dari PE×ROE.

**Sisa masalah:** MDKA.JK (PBV=80.312,50) tidak bisa diperbaiki karena PE = null (rugi). PBV tetap tidak valid.

### KR-02: Dividend Yield ditampilkan 100x lipat di dashboard

**Akar masalah:** Yahoo Finance mengembalikan `dividendYield` dalam bentuk persentase (contoh: 6,62 = 6,62%), sedangkan fungsi `fmt()` di dashboard selalu mengalikan dengan 100 untuk format `%`. Akibatnya dividend yield di panel fundamental menampilkan BBCA sebagai 662%, BBRI sebagai 1.526%.

**Dampak terhadap dashboard:** Angka dividend yield sangat misleading. Pengguna melihat BBCA dengan yield 662%.

**Perbaikan:** ❌ Belum diperbaiki. Perlu penanganan khusus di fungsi `renderFundamentals()` — tidak gunakan `f*100` untuk dividend_yield.

---

## Masalah Sedang

### SR-01: Revenue Growth AMMN tidak realistis

| Ticker | Revenue Growth | Keterangan |
|--------|---------------|------------|
| AMMN.JK | 37.937% (379,373×) | Kemungkinan data error Yahoo Finance |

**Akar masalah:** Yahoo Finance membandingkan revenue AMMN periode terbaru dengan periode saat perusahaan belum memiliki revenue signifikan (fase pre-IPO/restrukturisasi).

**Dampak terhadap scoring:** ✅ Tidak ada. Growth score menggunakan earnings-only growth (sesuai FINDING_010), bukan revenue growth.

**Dampak terhadap dashboard:** ❌ Revenue Growth di panel fundamental menampilkan 37.937% — nilai yang tidak realistis.

**Perbaikan:** ❌ Belum diperbaiki. Revenue growth tidak mempengaruhi scoring, hanya tampilan dashboard.

---

## Masalah Minor

### MR-01: PBV MDKA tetap tidak valid

| Ticker | Yahoo PBV | Masalah |
|--------|-----------|---------|
| MDKA.JK | 80.312,50 | PE=null (rugi), tidak bisa dihitung dengan PE×ROE |

**Akar masalah:** MDKA memiliki trailing PE negatif (rugi), sehingga Yahoo mengembalikan `trailingPE=null`. Tanpa PE, formula PBV=PE×ROE tidak bisa diterapkan.

**Dampak terhadap scoring:** Value score MDKA sangat rendah (40,17) — kemungkinan terlalu rendah karena PBV fiktif. Namun, MDKA sudah berada di peringkat bawah (value score 40,17 dari 100), sehingga dampaknya terhadap final ranking minimal.

**Perbaikan:** ❌ Belum ada. MDKA tetap menggunakan PBV Yahoo yang salah.

---

## Daftar Saham Bermasalah

| Ticker | Field | Nilai Saat Ini | Nilai Seharusnya | Penyebab | Status |
|--------|-------|----------------|-------------------|----------|--------|
| ADRO.JK | pb_ratio | 0,74 | 0,74 | Yahoo scaling error | ✅ Fix |
| AMMN.JK | pb_ratio | 2,36 | 2,36 | Yahoo scaling error | ✅ Fix |
| TPIA.JK | pb_ratio | 1,46 | 1,46 | Yahoo scaling error | ✅ Fix |
| BRPT.JK | pb_ratio | 4,74 | 4,74 | Yahoo scaling error | ✅ Fix |
| PGAS.JK | pb_ratio | 0,85 | 0,85 | Yahoo scaling error | ✅ Fix |
| ESSA.JK | pb_ratio | 1,33 | 1,33 | Yahoo scaling error | ✅ Fix |
| ITMG.JK | pb_ratio | 0,71 | 0,71 | Yahoo scaling error | ✅ Fix |
| MDKA.JK | pb_ratio | 80.312,50 | Tidak diketahui | PE null, tidak bisa fix | ❌ |
| BBCA.JK | dividend_yield | 6,62% | 6,62% | Dashboard rendering salah | ❌ |
| BBRI.JK | dividend_yield | 15,26% | 15,26% | Dashboard rendering salah | ❌ |
| AMMN.JK | revenue_growth | 37.937% | Tidak diketahui | Yahoo data error | ❌ |

---

## Dampak Terhadap Scoring

### Value Score (Sebelum → Sesudah Fix PBV)

| Ticker | Value Score Sebelum | Value Score Sesudah | Delta |
|--------|-------------------|-------------------|-------|
| ADRO.JK | 46,21 | 62,07 | **+15,86** |
| ITMG.JK | 39,66 | 57,24 | **+17,58** |
| TPIA.JK | 43,10 | 54,48 | **+11,38** |
| PGAS.JK | 29,65 | 52,07 | **+22,42** |
| BRPT.JK | 8,10 | 9,48 | **+1,38** |
| ESSA.JK | 14,48 | 26,90 | **+12,42** |
| AMMN.JK | 6,38 | 9,48 | **+3,10** |

### Final Score (Sesudah Fix)

| Rank | Ticker | Final Score | Perubahan dari Sebelum |
|------|--------|-------------|----------------------|
| 1 | ADRO.JK | 78,05 | Tidak signifikan (Value weight hanya 10%) |
| 2 | ESSA.JK | 76,22 | Naik (value score +12,42) |
| 3 | PTBA.JK | 74,70 | Stabil |

**Kesimpulan:** Meskipun value score berubah signifikan, dampak terhadap final ranking Config B minimal karena value weight hanya 10%. Tidak ada perubahan material pada Top 5.

---

## Dampak Terhadap Dashboard

1. **Panel Fundamental** — PBV sekarang menampilkan nilai wajar (0,7×–4,7×) untuk semua saham kecuali MDKA.
2. **Dividend Yield** — Masih menampilkan angka 100× lipat. Perlu perbaikan rendering.
3. **Revenue Growth AMMN** — Menampilkan 37.937% di panel fundamental.

---

## Rekomendasi Perbaikan

### Prioritas Tinggi
1. ✅ **PBV validation** — Selesai. Ditambahkan di `collectors/fundamentals.py:54-70`.

### Prioritas Sedang
2. ❌ **Dashboard dividend yield** — Tambahkan format khusus untuk `dividend_yield` di `renderFundamentals()`. Jangan kalikan dengan 100. File: `scripts/generate_dashboard_v2.py`.

### Prioritas Rendah
3. ❌ **Revenue growth AMMN** — Tidak mempengaruhi scoring. Bisa diabaikan atau di-filter dengan threshold maksimum (misal: cap di 1000%).
4. ❌ **MDKA PBV** — Tidak bisa diperbaiki tanpa sumber data alternatif. Diterima sebagai risiko data.
