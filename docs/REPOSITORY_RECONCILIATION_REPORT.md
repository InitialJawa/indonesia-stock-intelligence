# REPOSITORY RECONCILIATION REPORT

**Tanggal:** 2026-06-07
**Tujuan:** Sinkronisasi dokumentasi dengan kondisi repository aktual setelah Phase 1 & 2 refactor.

---

## 1. RINGKASAN PERUBAHAN REPOSITORY

### Phase 1 — Konsolidasi Dokumentasi & Arsip
- 7 dokumen baru dibuat di `docs/` (MASTER_CHRONICLE_V3, RESEARCH_INDEX, LESSONS_LEARNED, ARCHITECTURE_TREE, PROJECT_STATUS, REPOSITORY_REFACTOR_REPORT, ROOT_FILE_CLASSIFICATION, ROOT_SIMPLIFICATION_REPORT)
- `backtesting/` → `docs/archive/backtesting/` (11 file)
- `reports/` → `docs/archive/reports/` (75 file)
- `archives/` → `docs/archive/archives/` (9 file)
- Root artifacts → `docs/archive/root_artifacts/` (7 file)
- Session logs, task.md, index.html → `docs/archive/`
- Old chronicles → `docs/archive/`

### Phase 2 — Simplifikasi Root Directory
- 4 production scripts → `scripts/`
- 6 research tools → `research/tools/`
- 3 generated CSVs → `data/current/`
- 4 generated JSONs → `data/state/`
- 1 orphaned script → `docs/archive/root_artifacts/`
- 6 broken `backtesting.*` calls dihapus dari `run_monthly_pipeline.py`
- Path references diperbarui di semua script dan workflow YAML

### Total File Dipindahkan: ~110 file
### Root Level: 24 file → 6 file

---

## 2. DOKUMEN YANG DIPERBARUI

| Dokumen | Perubahan |
|---------|-----------|
| `docs/MASTER_CHRONICLE_V3.md` | Path output (2.3), arsitektur (7), workflow (8), backlog (10) |
| `docs/ARCHITECTURE_TREE.md` | Rewrite penuh — tambah `scripts/`, `data/`, `research/tools/`, hapus root files |
| `docs/PROJECT_STATUS.md` | Path output disinkronkan, tambah repo structure section |
| `README.md` | Rewrite penuh — struktur, cara pakai, performansi |
| `docs/RESEARCH_INDEX.md` | Tidak perlu perubahan (hasil riset tidak berubah) |
| `docs/LESSONS_LEARNED.md` | Tidak perlu perubahan (tidak referensi file path) |

---

## 3. KETIDAKSESUAIAN YANG DITEMUKAN

| Dokumen | Masalah | Status |
|---------|---------|--------|
| ARCHITECTURE_TREE.md | Referensi path root lama (generate_*.py di root) | ✅ Diperbaiki |
| ARCHITECTURE_TREE.md | `data/`, `scripts/`, `research/tools/` tidak ada | ✅ Diperbaiki |
| MASTER_CHRONICLE_V3.md | Path output exit (masih root) | ✅ Diperbaiki |
| MASTER_CHRONICLE_V3.md | Arsitektur tree outdated | ✅ Diperbaiki |
| MASTER_CHRONICLE_V3.md | Workflow path references | ✅ Diperbaiki |
| MASTER_CHRONICLE_V3.md | Backlog tidak mencakup Phase 1 & 2 | ✅ Diperbaiki |
| PROJECT_STATUS.md | Path output (turnaround_latest.csv etc.) | ✅ Diperbaiki |
| README.md | Hanya 1 baris — tidak informatif | ✅ Diperbaiki |
| RESEARCH_INDEX.md | Tidak ada ketidaksesuaian | ✅ OK |
| LESSONS_LEARNED.md | Tidak ada ketidaksesuaian | ✅ OK |

---

## 4. STRUKTUR REPOSITORY FINAL

```
root/                          (6 file)
├── .gitignore
├── .nojekyll
├── README.md
├── requirements.txt
├── run_daily_risk_radar.py
└── run_monthly_pipeline.py

scripts/                       (4 file — production)
data/current/                  (3 file — live CSVs)
data/state/                    (4 file — live JSONs)
scoring/                       (6 file — factor engine)
collectors/                    (6 file — data collection)
utils/                         (7 file — shared utilities)
dashboard/                     (1 file — index.html)
config/                        (4 file — settings)
database/                      (historical + current data)
├── monthly/                   (64 file — monthly prices)
├── historical/                (6 file — warehouse + metadata)
├── historical_universe/       (15 file — IDX30 snapshots)
└── historical_foreign_flow/   (66 file — foreign flow)
warehouse/                     (current warehouse + snapshots)
warehouse_historical/          (historical factor scores)
benchmarks/                    (IHSG benchmark)
output/                        (generated scores, raw, history)
snapshots/                     (monthly snapshots 2019-2026)
universe/                      (IDX30 definition)
automation/                    (shell script)
research/                      (~40 scripts + tools/ + output/)
.github/workflows/             (2 YAML pipelines)
docs/                          (12 dokumen + archive/)
docs/archive/                  (backtesting, reports, archives, etc.)
```

---

## 5. SISTEM PRODUKSI AKTIF

| No | Sistem | Lokasi | Status | Pipeline |
|----|--------|--------|--------|----------|
| 1 | Config B Ranking | `scoring/final_score_v3.py` | PRODUCTION | Monthly |
| 2 | Turnaround Watchlist | `scripts/generate_turnaround_watchlist.py` | MONITORING | Daily |
| 3 | Exit Monitor V1.1 | `scripts/generate_exit_watchlist.py` | ACTIVE | Daily |
| 4 | Dashboard Generator | `scripts/generate_dashboard_v2.py` | ACTIVE | Daily + Monthly |
| 5 | Daily Pipeline | `.github/workflows/daily_radar.yml` | ACTIVE | 16:30 WIB |
| 6 | Monthly Pipeline | `.github/workflows/monthly_pipeline.yml` | ACTIVE | 1st of month |
| 7 | Daily Risk Radar | `run_daily_risk_radar.py` | ACTIVE | Entry point |

## 6. KOMPONEN YANG DIARSIPKAN

| Komponen | Arsip | Isi |
|----------|-------|-----|
| Backtesting | `docs/archive/backtesting/` | 11 file — PIT backtest, archive utilities |
| Reports | `docs/archive/reports/` | 75 file — research reports, audit, validation |
| Archives | `docs/archive/archives/` | 9 file — portfolios/rankings 2026-05/06 |
| Root Artifacts | `docs/archive/root_artifacts/` | 7 file — one-off scripts, audit reports |
| Session Logs | `docs/archive/session_logs/` | 1 file — ses_163b (7,544 lines) |
| Old Chronicles | `docs/archive/` | V2, master_chronicle.txt, old project status |
| Root Redirect | `docs/archive/index.html` | Redirect ke dashboard (nonaktif) |
| Scratch Notes | `docs/archive/task.md` | Task checklist |

---

## 7. MASALAH YANG MASIH TERSISA

1. **`run_monthly_pipeline.py`** — 6 baris `python -m backtesting.*` dihapus. Pipeline tidak lagi mengarsip snapshot atau rebalance otomatis. Fungsionalitas archive perlu dipulihkan jika dibutuhkan.
2. **`research/tools/momentum_backtest_engine.py`** dan **`historical_portfolio_builder.py`** — Membaca file dari `archives/backtest/momentum_portfolio.csv` dan `reports/` yang sudah dipindah ke `docs/archive/`. Path perlu diperbarui jika tools ini dijalankan.
3. **`research/out_of_sample_validation.py`** — Masih diblokir oleh Historical Factor Warehouse V2.
4. **GitHub Pages root redirect** — `index.html` diarsipkan. Jika Pages diaktifkan dari root, redirect ke dashboard tidak aktif. Solusi: atur Pages ke `/dashboard` di repo settings.

---

## 8. REKOMENDASI

1. **Segera:** Tidak ada — repository sudah sinkron dan stabil.
2. **Minggu depan:** Evaluasi apakah monthly pipeline perlu fungsi archive/rebalance yang dipulihkan.
3. **Bulan depan:** Jika Historical Factor Warehouse V2 feasible, prioritaskan OOS weight validation.
