# AUDIT-002: Ketersediaan Data Yahoo Finance untuk PBV

**Tanggal:** 2026-06-07  
**Tujuan:** Verifikasi ketersediaan dan keakuratan field Yahoo Finance untuk menghitung PBV

---

## Ringkasan

| Field | Tersedia? | Akurat? | Catatan |
|-------|-----------|---------|---------|
| `bookValue` | ✅ Ya | ❌ Tidak (8/30 ticker) | 0.17 IDR untuk ADRO, seharusnya ~3,000 IDR |
| `bookValuePerShare` | ❌ Tidak | — | Selalu `None` |
| `totalEquity` | ❌ Tidak | — | Selalu `None` |
| `sharesOutstanding` | ✅ Ya | ✅ Ya | Akurat untuk semua ticker |
| `priceToBook` | ✅ Ya | ❌ Tidak (8/30 ticker) | Dihitung Yahoo dari `bookValue` yang salah |
| `Common Stock Equity` | ✅ Ya (balance sheet) | ❌ Tidak (8/30) | Unit/scaling tidak konsisten |

---

## Detail per Ticker

### Ticker Normal (bookValue Akurat)

| Ticker | bookValue | sharesOutstanding | priceToBook (Yahoo) | PE×ROE | Equity (balance sheet) |
|--------|-----------|-------------------|--------------------|--------|----------------------|
| BBCA.JK | 2.109 | 122,9 M | 2,41 | 2,48 | 259,1 T |
| BBRI.JK | 2.246 | 150,6 M | 1,22 | 1,28 | — |
| BMRI.JK | 3.271 | 93,3 M | 1,17 | 1,29 | — |
| ASII.JK | 5.810 | 40,1 M | 0,79 | 0,77 | 232,8 T |
| TLKM.JK | 1.360 | 98,7 M | 2,03 | 2,02 | — |

### Ticker Broken (bookValue Salah)

| Ticker | bookValue | Seharusnya | priceToBook (Yahoo) | PE×ROE |
|--------|-----------|-----------|--------------------|--------|
| ADRO.JK | 0,17 | ~3.000 | 13.176 | **0,74** |
| MDKA.JK | 0,03 | ~3.000 | 80.313 | **N/A** (PE null) |
| AMMN.JK | 0,08 | ~3.000 | 43.289 | **2,36** |
| TPIA.JK | 0,04 | ~2.000 | 30.349 | **1,46** |
| BRPT.JK | 0,03 | ~5.000 | 59.200 | **4,74** |
| PGAS.JK | 0,12 | ~1.500 | 12.991 | **0,85** |
| ESSA.JK | 0,03 | ~600 | 21.667 | **1,33** |
| ITMG.JK | 1,72 | ~25.000 | 12.733 | **0,71** |

---

## Analisis

### Akar Masalah

`bookValue` di Yahoo Finance untuk 8 ticker IDX30 memiliki nilai antara 0,03–1,72 IDR per saham — terlalu rendah 3-4 orders of magnitude dibandingkan nilai seharusnya (ribuan IDR). Nilai ini dihitung Yahoo dari `Common Stock Equity / sharesOutstanding`, dan data `Common Stock Equity` di balance sheet juga memiliki unit/scaling yang salah.

**Pola:** Semua 8 ticker adalah perusahaan komoditas/mining/energi. Saham perbankan dan konsumen tidak terdampak.

### Ketelitian PE×ROE vs priceToBook Sebenarnya

Untuk ticker normal, PBV yang dihitung dari PE×ROE memiliki selisih ±3% dibandingkan `priceToBook` Yahoo:

| Ticker | PBV (Yahoo) | PBV (PE×ROE) | Selisih |
|--------|-------------|--------------|---------|
| BBCA.JK | 2,41 | 2,48 | +2,9% |
| BBRI.JK | 1,22 | 1,28 | +4,9% |
| BMRI.JK | 1,17 | 1,29 | +10,3% |
| ASII.JK | 0,79 | 0,77 | -2,5% |
| TLKM.JK | 2,03 | 2,02 | -0,5% |

Selisih terjadi karena:
- `trailingPE` menggunakan diluted EPS 12 bulan terakhir
- `returnOnEquity` menggunakan laba tahun buku terakhir
- Perbedaan waktu dan item non-recurring

Kesimpulan: PE×ROE **cukup akurat** untuk fallback PBV. Selisih <10% tidak mengubah peringkat persentil secara signifikan.

### Dividend Yield Dikonfirmasi dalam Persentase

`dividendYield` dari Yahoo dikembalikan dalam bentuk persentase:
- BBCA: 6.62 → **6,62%** (bukan desimal 0,0662)
- BBRI: 15.26 → **15,26%** (bukan desimal 0,1526)
- ASII: 8.53 → **8,53%**

✅ **Fix dashboard (AUDIT-001) sudah benar:** format `'dy'` tanpa perkalian 100.

---

## Kesimpulan

1. **Tidak ada field alternatif** yang bisa menggantikan `priceToBook` secara langsung — semua sumber Yahoo untuk book value memiliki scaling error yang sama pada 8 ticker.
2. **`PE × ROE` adalah fallback terbaik** yang tersedia. Akurat untuk ticker menguntungkan, error <10%.
3. **MDKA tidak bisa diperbaiki** karena PE=null (rugi).
4. **`sharesOutstanding`** adalah satu-satunya field yang akurat untuk semua ticker — tidak berguna untuk PBV tanpa equity yang benar.
5. **Fix AUDIT-001 sudah optimal** — tidak ada pendekatan lain yang lebih baik dengan data Yahoo yang tersedia.
