# HANDOVER_AI — Indonesia Stock Intelligence (ISI)

**Purpose:** Agar AI baru (atau human) langsung paham proyek ini dari awal sampai akhir
tanpa membaca ribuan baris kode atau 5 master chronicle.

---

## 1. APA ITU ISI?

ISI adalah **sistem riset saham Indonesia** untuk indeks IDX30. Sistem ini:

- **Men-skor** 30 saham IDX30 setiap bulan menggunakan 4 faktor (Quality, Growth, Value, Momentum)
- **Memilih Top 5** dengan bobot sama, rebalance bulanan
- **Memantau** exit signal setiap hari (rule-based)
- **Mendeteksi** potensi turnaround (saham tertekan yang mulai pulih)
- **Menampilkan** semuanya di dashboard HTML

**Data source:** Yahoo Finance (single source — tidak ada provider lain)
**Bahasa:** Python
**Deployment:** GitHub Actions (daily 16:30 WIB + monthly 1st)

---

## 2. ARSITEKTUR CORE

### Scoring Engine

```
collectors/  →  output/raw/*.json  →  scoring/  →  output/scores/*.json  →  final_score_v3.py
```

Setiap collector mengambil data dari Yahoo, scoring mengubahnya jadi percentile (0-100),
dan `final_score_v3.py` menggabungkan dengan bobot dari `config/scoring_weights.json`.

### Factor Definitions (final)

| Faktor | Bobot Produksi | Input | IC |
|--------|---------------|-------|-----|
| Quality | 25% | ROE, Net Margin, Op Margin, DER, FCF | +0.028 |
| Growth | **10%** | Earnings growth ONLY (revenue excluded) | **-0.013** |
| Value | **30%** | PE, PB (PE×ROE fix), Dividend Yield | **+0.056** |
| Momentum | 35% | RS-6M, Return-12M | +0.036 |

### Portfolio Construction
- Top 5 berdasarkan composite score tertinggi
- Equal weight (20% each)
- Rebalance bulanan (setiap tanggal 1)
- Turnover rata-rata ~10-12% per bulan

### Exit Layer (daily)
4 level state machine: HEALTHY → EXIT WATCH → WEAKENING → EXIT RISK → EXIT.
Tidak digunakan sebagai sinyal jual otomatis (terbukti tidak efektif di RESEARCH-012).

---

## 3. PRODUCTION VS RESEARCH

### Production: Config F
| Quality | Growth | Value | Momentum |
|---------|--------|-------|----------|
| 25% | 10% | 30% | 35% |

**Alasan:** MaxDD lebih rendah (22% vs 27%), Sharpe lebih tinggi, lebih defensif saat krisis.

### Research Baseline: Config B
| Quality | Growth | Value | Momentum |
|---------|--------|-------|----------|
| 25% | 30% | 10% | 35% |

**Alasan:** CAGR lebih tinggi (13.22% vs 11.07% full period), menang di hampir semua periode kecuali 2026 crash.

### Investor Choice
- **Agresif → Config B** (CAGR 13.22%, MaxDD 27.53%)
- **Defensif → Config F** (CAGR 11.07%, MaxDD 22.00%)

Tidak ada yang secara mutlak superior — tergantung toleransi risiko.

---

## 4. SEJARAH RISET (YANG PALING PENTING)

### Phase 1: Discovery (R001-R011)
Membangun framework dari nol: faktor scoring, weight optimization (Config B),
turnaround detection, exit signals. Banyak yang gagal (timing overlay, predictive sell).

### Phase 2: Decision Layer (RESEARCH-012) — CLOSED FAILED
Mencoba menambahkan decision overlay di atas Config B (rank-drop sell, Turnaround replacement).
**Hasil:** Event-level improvement tidak bertahan di portfolio level. Config B murni tetap terbaik.

### Phase 3: Foundation Recovery (RESEARCH-013)

#### 013A — Baseline Reproducibility
Klaim lama "46.33% CAGR" dari GATE-001 ternyata pakai metodologi berbeda (daily warehouse,
survivorship bias). Di-rebuild dengan V3 warehouse: **17.45% CAGR** untuk Config B.

#### 013B — Config B vs Config F → ADR-005
Perbandingan pertama dengan data real. Config F dipilih untuk produksi karena risk-adjusted lebih baik.

#### 013C — Factor Attribution Audit
Menemukan bahwa **Growth IC negatif (-0.0673)** — tapi ini karena warehouse pakai 50/50
revenue+earnings blend, BUKAN earnings-only seperti yang didokumentasikan.

#### AUDIT-GROWTH-001/002 — Pipeline Drift Discovery
**Kritis:** `scoring/growth_score.py` pakai earnings-only, tapi `build_warehouse_v3.py`
diam-diam pakai 50/50 revenue+earnings. Semua backtest sebelum Juni 2026 pakai definisi
yang SALAH. Earnings-only punya IC **+0.0591** (positif), 50/50 blend punya IC **-0.0673** (negatif).
**Fix:** Earnings-only diadopsi universal. Revenue growth di-exclude (IC -0.3177).

#### 013D — Should Growth Weight Be 0%?
Hipotesis: Growth IC ≈ 0, jadi mungkin bisa dihapus.
**Hasil: DITOLAK.** Semua konfigurasi tanpa Growth (G=0%) mengalami penurunan CAGR drastis
(3-7% vs 20%+). Growth terbukti sebagai **diversifier** — memilih saham yang berbeda dari
Value/Momentum, mencegah top-5 overconcentration.

#### 013E — Period Sensitivity
Config B menang di semua periode kecuali 2026 crash. Config F melindungi saat krisis.
Kesimpulan: tidak ada winner universal.

### Phase 4: Data Quality (AUDIT-001/002)
- **PBV Yahoo salah** untuk 8 ticker komoditas (return 12-59x untuk yang seharusnya 0.7-4.7x)
  → Fix: PBV = PE × ROE
- **Dividend Yield rendering 100×** di dashboard → Fix
- **Warehouse stale** (berhenti di 2025-12 padahal data mentah sampai 2026-05)
  → Fix: END_YEAR 2025 → 2026

---

## 5. DATA WAREHOUSE

Ada 3 warehouse historical:

| File | Definisi Growth | Periode | Records | Ticker |
|------|----------------|---------|---------|--------|
| `warehouse_v3.csv` | 50/50 blend (RETIRED) | 2022-01 → 2026-05 | 1418 | 28 |
| `warehouse_v3_growth_fix.csv` | **Earnings-only (CURRENT)** | 2022-01 → 2026-05 | 1418 | 28 |
| `warehouse_v2_multiyear_pit.csv` | Legacy | 2022-01 → 2025-12 | 1389 | 29 |

**PIT coverage:** 67.7% dari data menggunakan annual financial statements (sisanya trailing metrics).
**Look-ahead bias:** Ada — semua data financial di-fetch sekali pakai Yahoo today data.
Ini limitasi yang diketahui dan tidak bisa diperbaiki tanpa data provider berbayar.

---

## 6. PROVEN FINDINGS (JANGAN DIUBAH TANPA BUKTI BARU)

1. **Value adalah faktor paling prediktif** di IDX30 (IC +0.0555, t=1.97)
2. **Growth bukan prediktor** (IC -0.0126, t=-0.44) tapi tetap harus dipertahankan sebagai diversifier
3. **Momentum adalah penggerak return utama** (standalone 24.05% CAGR)
4. **Revenue growth merusak** portfolio (IC -0.3177) — jangan pernah dipakai
5. **Top 5 optimal** — diminishing returns setelah 5 saham
6. **Timing overlay tidak bekerja** — RESEARCH-010, RESEARCH-012 sudah membuktikan
7. **EXIT bukan sinyal jual** — saham EXIT outperform saham Healthy di 90D (+2.16%)
8. **Turnaround sebagai watchlist** saja — negative CAGR sebagai standalone strategy
9. **Config F untuk produksi** (defensif), **Config B untuk agresif**
10. **PBV = PE × ROE** adalah formula paling reliable untuk data Yahoo

---

## 7. FILE STRUCTURE PENTING

```
ISI/
├── config/
│   └── scoring_weights.json      ← Bobot produksi (Config F)
├── scoring/
│   └── growth_score.py           ← Earnings-only (jangan diubah)
├── warehouse_historical/
│   ├── warehouse_v3.csv          ← 50/50 blend (jangan dipakai untuk riset baru)
│   └── warehouse_v3_growth_fix.csv ← Earnings-only (gunakan ini)
├── audits/
│   ├── AUDIT_GROWTH_001.md       ─┐
│   └── AUDIT_GROWTH_002_REPORT.md ┘ Pipeline drift documentation
├── reports/
│   ├── research_013*.md          ─┐ Semua laporan riset
│   └── research_013e.md           ┘
├── docs/
│   ├── chronicle/              ← SEMUA master chronicle + HANDOVER_AI (baca ini dulu)
│   └── ADR-005.md                ← Keputusan produksi Config F
└── research/
    ├── research_013*.py          ─┐ Script riset
    └── research_013e.py           ┘
```

---

## 8. OPEN QUESTIONS (PRIORITAS RENDAH)

1. **Survivorship Bias Audit** — Berapa besar inflasi CAGR karena static universe?
2. **Universe Bias** — Apakah hasil bertahan di LQ45 atau hanya IDX30?
3. **Bootstrap Significance** — Apakah perbedaan CAGR Config B vs F signifikan secara statistik?
4. **Regime Robustness** — Apakah hasil bertahan di regime pasar berbeda?
5. **Otomatisasi Warehouse** — END_YEAR masih hardcode, perlu `datetime.now().year`

**Status ISI saat ini:** Layak digunakan sebagai sistem pengambilan keputusan investasi.
Prioritas berikutnya adalah validasi robustness, bukan riset baru.

---

## 9. COMMON PITFALLS (BUAT AI BARU)

1. **Jangan pernah mengubah bobot** tanpa melalui ADR process
2. **Jangan pernah menggunakan warehouse_v3.csv** untuk riset baru — pakai `_growth_fix`
3. **Scoring code ≠ Warehouse code** — selalu verifikasi definisi faktor di kedua tempat
4. **Growth IC ≈ 0 bukan alasan untuk menghapus Growth** — lihat RESEARCH-013D
5. **Jangan tambah overlay** di atas Config B/F — sudah dibuktikan gagal di RESEARCH-012
6. **Unicode di print statements** break di Windows (cp1252) — hindari karakter non-ASCII
7. **END_YEAR** harus diupdate manual saat tahun berganti

---

*Generated: 2026-06-09*
*Source: MASTER_CHRONICLE_V4, V3, V4_PATCH, V2, V1*
*Next: Read `docs/chronicle/MASTER_CHRONICLE_V4.md` for full detail*
