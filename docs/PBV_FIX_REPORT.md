# Laporan Perbaikan PBV

**Tanggal:** 2026-06-07
**Tujuan:** Memperbaiki data PBV yang tidak wajar akibat Yahoo Finance `priceToBook` scaling error

---

## Akar Masalah

Yahoo Finance mengembalikan nilai `priceToBook` yang salah untuk saham komoditas dan pertambangan Indonesia. Nilai yang dikembalikan berkisar antara 12.731–59.200× untuk saham yang seharusnya memiliki PBV 0,7–4,7×.

Masalah ini terjadi secara sistemik: **7 dari 30 saham IDX30** (23%) terdampak. Pola saham yang terdampak adalah perusahaan komoditas/mining/energi.

Penyebab pasti di sisi Yahoo Finance tidak diketahui — kemungkinan unit/scaling error pada `bookValue` untuk emiten-emiten tersebut.

## Solusi

**Rumus:** `PBV = PE × ROE`

**Pembuktian matematis:**
```
PE = Price / EPS
ROE = EPS / Book Value per Share
PBV = Price / Book Value per Share = (Price / EPS) × (EPS / Book Value) = PE × ROE
```

**Implementasi** di `collectors/fundamentals.py`:
- Jika `pb_ratio > 100` AND `pe_ratio` ada AND `roe` ada → hitung `pb = pe * roe`
- Jika `pb_ratio < 0` (negatif) → terapkan formula yang sama

## File yang Diubah

| File | Perubahan |
|------|-----------|
| `collectors/fundamentals.py` | Tambah validasi PBV setelah pengumpulan data (baris 55-70) |
| `scripts/generate_dashboard_v2.py` | Tambah format `'dy'` untuk dividend yield (tidak dikali 100) |

## Jumlah Saham Terdampak

**PBV fix:** 7 saham

| Ticker | Sebelum | Sesudah | Sumber Fix |
|--------|---------|---------|------------|
| ADRO.JK | 13.176,47 | 0,74 | PE×ROE = 7,24×0,103 |
| AMMN.JK | 43.289,48 | 2,36 | PE×ROE = 22,52×0,105 |
| TPIA.JK | 30.348,84 | 1,46 | PE×ROE = 3,44×0,424 |
| BRPT.JK | 59.200,00 | 4,74 | PE×ROE = 13,61×0,348 |
| PGAS.JK | 12.991,45 | 0,85 | PE×ROE = 8,42×0,101 |
| ESSA.JK | 21.666,67 | 1,33 | PE×ROE = 10,97×0,121 |
| ITMG.JK | 12.732,56 | 0,71 | PE×ROE = 7,59×0,094 |

**Tidak bisa diperbaiki:** 1 saham
| Ticker | PBV (tetap salah) | Alasan |
|--------|-------------------|--------|
| MDKA.JK | 80.312,50 | PE = null (perusahaan rugi) |

## Perubahan Skor Sebelum/Sesudah

### Value Score

| Ticker | Sebelum | Sesudah | Delta |
|--------|---------|---------|-------|
| ADRO.JK | 46,21 | 62,07 | +15,86 |
| AMMN.JK | 6,38 | 9,48 | +3,10 |
| TPIA.JK | 43,10 | 54,48 | +11,38 |
| BRPT.JK | 8,10 | 9,48 | +1,38 |
| PGAS.JK | 29,65 | 52,07 | +22,42 |
| ESSA.JK | 14,48 | 26,90 | +12,42 |
| ITMG.JK | 39,66 | 57,24 | +17,58 |

### Final Score (Config B, Top 10)

| Peringkat | Ticker | Final Score | Perubahan Peringkat |
|-----------|--------|-------------|-------------------|
| 1 | ADRO.JK | 78,05 | Tetap (#1) |
| 2 | ESSA.JK | 76,22 | Naik dari #4 |
| 3 | PTBA.JK | 74,70 | Tetap (#3) |
| 4 | MAPI.JK | 66,20 | Turun dari #2 |
| 5 | BMRI.JK | 66,07 | Naik dari #7 |
| 6 | BBNI.JK | 63,37 | Naik dari #8 |
| 7 | BBRI.JK | 61,41 | Naik dari #10 |
| 8 | INDF.JK | 60,53 | Tetap (#8) |
| 9 | PGAS.JK | 58,34 | Naik dari #12 |
| 10 | ASII.JK | 57,90 | Naik dari #13 |

**Perubahan peringkat terjadi karena value score yang lebih akurat mengubah distribusi persentil, yang berdampak pada seluruh 30 saham.**

## Verifikasi Dashboard

- ✅ PBV panel fundamental menampilkan nilai wajar (0,24×–4,74×) untuk 29/30 saham
- ✅ MDKA masih menampilkan 80.312,50× (keterbatasan data)
- ✅ Dividend yield tidak lagi dikali 100 (fix terpisah ditemukan saat audit)
- ✅ Semua komponen dashboard (Leaders, Turnaround, Exit) berfungsi normal
- ✅ Ticker color coding berdasarkan alignment tetap akurat
