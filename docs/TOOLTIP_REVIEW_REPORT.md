# TOOLTIP REVIEW REPORT — Dashboard V2

**Tanggal:** 2026-06-07
**Lingkup:** Seluruh tooltip pada `dashboard/index.html` — 6 tabs
**Tujuan:** Bahasa Indonesia, praktis, konsisten, tanpa referensi riset internal

---

## Ringkasan

| Tab | Tooltip Ditemukan | Perlu Perbaikan | Status |
|-----|------------------|-----------------|--------|
| Leaders (t0) | 0 | 0 | ✅ Tidak ada tooltip |
| Turnaround (t1) | 0 | 0 | ✅ Tidak ada tooltip |
| Daily Summary (t2) | 9 `.tip` elements | 9 | ❌ Semua diperbaiki |
| History (t3) | 1 deskripsi teks | 0 | ✅ Hanya teks penjelas |
| Exit Monitor (t5) | 1 `title` + 1 legend | 2 | ❌ Diperbaiki |
| Diagnostics (t4) | 0 | 0 | ✅ Tidak ada tooltip |
| Side Panel | 0 | 0 | ❌ Tidak ada tooltip (tapi aiExplain masih Inggris) |

---

## Tooltip Daily Summary

### 1. SAHAM TERTEKAN

**Masalah:** Bahasa Inggris, ada Research Source, teknis.

**SEBELUM:**
```
What does this mean?
Stock is still under heavy pressure.

How is it calculated?
Price is far below previous highs
and volatility remains elevated.

Research Source:
Research-009B
```

**SESUDAH:**
```
Saham yang masih berada dalam tekanan besar.

Harga saat ini jauh di bawah harga tertinggi sebelumnya dan pergerakannya masih sangat fluktuatif.

Ini penting karena saham yang tertekan berpotensi menjadi kandidat pemulihan — tetapi belum waktunya untuk dibeli. Tunggu hingga ada tanda-tanda kekuatan mulai muncul.
```

**Alasan:** Bahasa Indonesia, 3 kalimat, tanpa istilah teknis, langsung ke interpretasi praktis.

---

### 2. MULAI MEMBAIK

**Masalah:** Bahasa Inggris, ada Research Source, tidak menjawab "mengapa penting".

**SEBELUM:**
```
What does this mean?
Stock is starting to recover.

How is it calculated?
Current strength is better than it was
during the previous two months.

Research Source:
Research-008B / Research-009B
```

**SESUDAH:**
```
Saham yang kekuatan relatifnya mulai meningkat dibanding dua bulan sebelumnya.

Menunjukkan bahwa minat pasar terhadap saham ini perlahan kembali — bisa menjadi sinyal awal pemulihan.

Semakin banyak saham dalam kategori ini, semakin besar kemungkinan pasar sedang memasuki fase pemulihan secara luas.
```

**Alasan:** Bahasa Indonesia, menjelaskan arti, pentingnya, dan cara membaca konteks pasar.

---

### 3. KANDIDAT TURNAROUND

**Masalah:** Bahasa Inggris, istilah "Context Match"/"Transition Match" tidak dijelaskan.

**SEBELUM:**
```
What does this mean?
Distressed stocks that are beginning
to show signs of recovery.

How is it calculated?
Stock meets BOTH conditions:
1. Under heavy pressure (Context Match)
2. Improving relative strength (Transition Match)

Research Source:
Research-008B / Research-009B
```

**SESUDAH:**
```
Saham yang sebelumnya mengalami tekanan besar dan mulai menunjukkan tanda-tanda pemulihan.

Kandidat ini memenuhi dua syarat:
• Masih dalam kondisi tertekan
• Kekuatan relatif mulai membaik

Ini bukan sinyal beli otomatis, tetapi radar untuk memantau peluang pemulihan lebih awal.
```

**Alasan:** Bahasa Indonesia, langsung pakai istilah yang mudah dipahami, dengan peringatan bahwa ini bukan sinyal beli.

---

### 4. KEKUATAN MULAI NAIK

**Masalah:** Bahasa Inggris, istilah "RS_CHANGE_60D" tidak dijelaskan.

**SEBELUM:**
```
What does this mean?
Stocks starting to outperform the market.

How is it calculated?
RS_CHANGE_60D > 0
Relative strength improved over 60 days.

Research Source:
Research-009
```

**SESUDAH:**
```
Jumlah saham yang mulai mengungguli pergerakan pasar secara relatif.

Digunakan untuk mendeteksi perubahan momentum lebih awal. Jika jumlahnya meningkat, artinya semakin banyak saham yang pulih — ini bisa menjadi indikasi awal penguatan pasar secara luas.

Angka yang tinggi menandakan pemulihan yang meluas.
```

**Alasan:** Bahasa Indonesia, istilah teknis dihilangkan, fokus ke interpretasi praktis.

---

### 5. MINAT BELI MENINGKAT

**Masalah:** Bahasa Inggris, ada Research Source.

**SEBELUM:**
```
What does this mean?
Trading activity is increasing.

How is it calculated?
Current volume is at least
30% higher than normal.

Research Source:
Research-008B
```

**SESUDAH:**
```
Volume perdagangan saham ini berada di atas kondisi normal (minimal 30% lebih tinggi).

Ini menunjukkan meningkatnya perhatian investor — bisa menjadi konfirmasi bahwa pergerakan harga didukung oleh minat beli yang nyata.

Waspada jika volume tinggi diikuti harga turun — itu bisa menandakan distribusi (penjualan besar-besaran).
```

**Alasan:** Bahasa Indonesia, tambahan interpretasi tentang volume tinggi vs harga turun.

---

### 6. DI ATAS TREND PENDEK

**Masalah:** Bahasa Inggris, ada Research Source.

**SEBELUM:**
```
What does this mean?
Price has moved above
its short-term trend.

How is it calculated?
Current price is above
its average price over
the last 20 trading days.

Research Source:
Research-009B
```

**SESUDAH:**
```
Harga saham saat ini berada di atas rata-rata 20 hari terakhir.

Ini menandakan tren jangka pendek yang positif. Saham yang konsisten di atas MA20 biasanya menunjukkan momentum naik yang sehat.

Namun, ini hanya indikator jangka pendek — kombinasikan dengan indikator lain untuk keputusan yang lebih kuat.
```

**Alasan:** Bahasa Indonesia, istilah MA20 dijelaskan sebagai rata-rata, dengan peringatan bahwa ini hanya indikator jangka pendek.

---

### 7. PANTUL DARI DASAR

**Masalah:** Bahasa Inggris, ada Research Source.

**SEBELUM:**
```
What does this mean?
Stock has rebounded from
a recent low.

How is it calculated?
Price is more than 10%
above the lowest point
of the last 60 trading days.

Research Source:
Research-008B
```

**SESUDAH:**
```
Saham yang telah naik lebih dari 10% dari titik terendah 60 hari terakhir.

Ini menunjukkan adanya usaha pemulihan setelah fase penurunan. Semakin banyak saham yang memantul, semakin besar kemungkinan pasar memasuki fase pemulihan.

Gunakan indikator ini bersama konfirmasi lain seperti peningkatan volume atau perbaikan kekuatan relatif.
```

**Alasan:** Bahasa Indonesia, menjelaskan pentingnya konteks market-wide, dengan saran penggunaan bersama indikator lain.

---

### 8. RATA-RATA PENURUNAN

**Masalah:** Istilah teknis "Mean Drawdown_252D" tidak dijelaskan dalam bahasa awam.

**SEBELUM:**
```
Rata-rata penurunan semua saham dari harga tertinggi masing-masing.

(Perhitungan:
Mean Drawdown_252D
— seluruh universe IDX30)
```

**SESUDAH:**
```
Rata-rata penurunan semua saham IDX30 dari harga tertinggi masing-masing dalam satu tahun terakhir.

Semakin negatif angkanya, semakin banyak saham yang sedang berada dalam tekanan. Ini adalah indikator kesehatan pasar secara keseluruhan.

Jika angkanya di atas -15%, pasar relatif sehat. Jika di bawah -30%, pasar sedang dalam tekanan luas.
```

**Alasan:** Istilah "Mean Drawdown_252D" dihilangkan, ditambah interpretasi praktis (kapan sehat, kapan tekanan).

---

### 9. RATA-RATA GEJOLAK

**Masalah:** Istilah teknis "Mean Volatility_60D" tidak dijelaskan dalam bahasa awam.

**SEBELUM:**
```
Intensitas pergerakan harga rata-rata — semakin tinggi semakin berisiko.

(Perhitungan:
Mean Volatility_60D
— seluruh universe IDX30)
```

**SESUDAH:**
```
Rata-rata intensitas pergerakan harga semua saham IDX30 dalam 60 hari terakhir.

Semakin tinggi nilainya, semakin besar ketidakpastian di pasar. Ini penting untuk mengatur ekspektasi risiko — di pasar yang bergejolak, pergerakan harga harian bisa lebih ekstrem dari biasanya.

Nilai di atas 4% menandakan volatilitas tinggi. Di bawah 2% menandakan pasar yang tenang.
```

**Alasan:** Istilah "Mean Volatility_60D" dihilangkan, ditambah ambang praktis untuk interpretasi.

---

## Tooltip Exit Monitor

### 10. Triggered Rules (title attribute)

**Masalah:** Hanya peraturan (A/B/C/D) tanpa penjelasan.

**SEBELUM:**
```
A: Peringkat Turun
B: Momentum Melemah
C: Trend MA50 Rusak
D: Pelemahan Terkonfirmasi
```

**SESUDAH:**
```
A: Peringkat turun di luar 10 besar — sinyal awal
B: Momentum jangka pendek melemah — kewaspadaan
C: Harga di bawah MA50 — tren rusak
D: Pelemahan terkonfirmasi — keluar
```

**Alasan:** Ditambah level kewaspadaan di setiap aturan.

---

## aiExplain Function (Side Panel)

### 11. KANDIDAT TURNAROUND — teks bahasa Inggris

**Masalah:** "Deep drawdown", "Far from previous high", "Improving RS60", "Elevated volume", "Stock remains high risk but shows early signs of accumulation."

**SEBELUM:**
```
Deep drawdown
Far from previous high
Improving RS60
Elevated volume
Stock remains high risk but shows early signs of accumulation.
```

**SESUDAH:**
```
Penurunan dalam
Jauh dari harga tertinggi
Kekuatan relatif membaik
Volume meningkat
Saham masih berisiko tinggi tetapi menunjukkan tanda awal akumulasi.
```

### 12. SINYAL EXIT AKTIF — teks bahasa Inggris

**Masalah:** "Stock shows sustained weakness across multiple indicators."

**SEBELUM:**
```
Stock shows sustained weakness across multiple indicators.
```

**SESUDAH:**
```
Saham menunjukkan kelemahan yang berkelanjutan di beberapa indikator.
```

### 13. PORTOFOLIO AKTIF — teks bahasa Inggris

**Masalah:** "Top 5 in Config B ranking"

**SEBELUM:**
```
Top 5 in Config B ranking
```

**SESUDAH:**
```
Peringkat 5 besar dalam sistem Config B
```

---

## Daftar Tooltip yang Masih Perlu Ditinjau

Tidak ada — semua tooltip yang ada sudah diperbaiki. Tooltip baru untuk fundamental snapshot (ROE, ROA, PER, PBV, EPS Growth, dll.) bisa ditambahkan di iterasi berikutnya, tetapi di luar lingkup tugas ini.

## File yang Diubah

- `dashboard/index.html` — 9 tooltip title attributes, 3 aiExplain strings, 1 exit monitor title

## Prinsip yang Diterapkan

1. **Bahasa Indonesia** — konsisten di seluruh dashboard
2. **Tanpa referensi riset** — tidak ada Research-XXX di tooltip pengguna
3. **3-5 kalimat** — padat, langsung ke inti
4. **Apa → Mengapa → Cara baca** — setiap tooltip menjawab ketiganya
5. **Interpretasi praktis** — bukan teori, tapi "kalau angka X artinya Y"
