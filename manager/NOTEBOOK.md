# 📓 ISI Project Notebook — Catatan Si Manager

Ini buku catatan gue. Setiap ada perubahan, error, atau keputusan penting, gue catet di sini kronologisnya. Biar gak lupa dan AI lain bisa langsung paham.

---

## 2026-06-13

### 🆕 engine.mjs — Shared Backtest Engine
**Apa:** Ekstraksi shared pure-function engine (`runAlgo`, `runSingle`, `normalizeDay`) dari duplikasi kode di CLI + server + dashboard.
**File:** `engine.mjs`
**Kenapa:** Dulu tiap entry point punya copy-paste logic sendiri. Sekarang semua import dari satu source.
**Entry points:**
- `backtest_compare.mjs` (CLI) — import dari `engine.mjs`
- `dashboard/dashboard_v7/server.ts` — `POST /api/run-backtest` pake engine
- `dashboard/dashboard_v7/src/components/SimulationTab.tsx` — API-first, inline fallback

### 🆕 POST /api/run-backtest
**Apa:** Endpoint baru di server.ts yang nerima parameter backtest, generate data, jalanin engine, return results + journal logs.
**Body:** `{ mode, ticker, topN, crashPct, safeHaven, capital, configType, ... }`

### 🐛 Grafik Algo Flat (Strategi Rebalancer = 0)
**Apa:** Chart pake `"Strategi Rebalancer": 0` pas pake API result.
**Fix:** Engine sekarang collect `chartData[]` di loop (tiap 8 hari + hari terakhir) — pake portfolio value real.
**SimulationTab.tsx:** Map `engineResult.chartData` → `{ date, "Strategi Rebalancer", "Benchmark IHSG", "Benchmark Emas", ranks }`.

### 🐛 GOTO Pre-IPO (Error Kritis)
**Apa:** GOTO muncul di transaksi Jan 2021 padahal IPO April 2022. Data synthetic di milestones.json.
**Fix:** Filter GOTO dari `stockPrices`/`stockRanks` untuk tanggal sebelum `2022-04-11` di SEMUA data generation:
- `SimulationTab.tsx` — `generateBacktestData()` + inline fallback
- `server.ts` — GET `/api/backtest-data` + POST `/api/run-backtest`
- `backtest_compare.mjs` — CLI data generation

### 🐛 Crash Trigger VELOCITY -2%/5D (False Positive)
**Apa:** Jan 2020 IHSG turun kecil (~0.8%) tapi kena trigger VELOCITY karena sensitif.
**Fix:** Dihapus. Cuma HIGH-60D `-crashPct%` yang dipakai. Minimal 60 hari data sebelum bisa trigger.

### 🐛 Recovery 2,5 Tahun di Emas (2022→2025)
**Apa:** Crash Dec 2022 → baru recovery July 2025. Gak ada transaksi 2,5 tahun.
**Akar masalah:** `crashLow` dihitung pake rolling 60-day minimum. Noise jitter harian (±0.75%) bikin 60-day low selalu dekat harga sekarang, jadi threshold 3% gak pernah tercapai.
**Fix:** `crashLowPrice` disimpan **fixed** pas crash (`= day.ihsg`) dan diupdate cuma kalau IHSG turun lebih rendah (tracking true bottom). Recovery diukur dari bottom beneran, bukan rolling window.

### 🐛 Harga Emas Jan 2020 Overestimate
**Apa:** Milestone gold: 800.000 → historis Antam ~765.000.
**Fix:** `milestones.json` → gold `800000` → `765000`.

---

## 2026-06-11

### 🆕 Rank Change dari Warehouse (RK) — Deploy
**Apa:** Implementasi rank_change real dari warehouse backtest data (53 bulan, 2022-01 → 2026-05).
**Kenapa:** EX rank_change semua 0, gak berguna buat Rotation column.
**Apa aja:**
- `scripts/compute_rank_change.py` — baca warehouse CSV, compute rank change per ticker per month
- `rebuild_data_js.py` — auto-run compute_rank_change, embed `RK` variable ke data.js
- `dashboard/dashboard_v4.js` — merge RK + EX, display di Rotation column + widget
- `run_daily_risk_radar.py` — call rebuild setelah dashboard generation
- Daily snapshot `data/history/rank_snapshots/2026-06-11.json` (daily tracking)
- `dashboard/data/rk.json` + `dashboard/data/rank_history.json`
- 10 ticker marked NEW (gak ada di May warehouse): ESSA, MAPI, AKRA, EXCL, INTP, MIKA, SIDO, TPIA, AMMN, HEAL
- Commit: `633e6d9` → rebase `8f64b3d`, push ke `origin/main`

### 🆕 MANAGER.md + NOTEBOOK.md — Dibuat
**Apa:** File manager dan notebook untuk project oversight.
**Kenapa:** Biar gampang di-track sama AI lain kalo ada yang baru join.
**Detail:** MANAGER.md berisi full project context, NOTEBOOK.md buat catatan kronologis.

---

## 2026-06-10

### 🐛 Bottom Sheet - Overview Tab Hanya "Rank"
**Apa:** Overview tab di bottom sheet cuma nampilin rank number aja.
**Status:** Masih gitu, belum ada chart atau visual tambahan.

### 🐛 Bottom Sheet - Factors Tab Static Bars
**Apa:** Factors tab nampilin bar chart statis tanpa breakdown metric.
**Status:** Masih gitu, improvisasi nanti.

---

## 2026-06-09

### 🐛 Audit: Config F di Production Tanpa Dokumentasi
**Apa:** Audit nemuin kalo `config/scoring_weights.json` udah diubah dari Config B ke Config F diam-diam.
**Impact:** High. ADR-004 dilanggar, documentation gak sinkron sama reality.
**Dokumentasi:** `AUDIT_CRITICAL_001_PRODUCTION_REALITY.md`
**Status:** Masih open — production pake Config F, docs masih bilang Config B.

---

## 2026-06-07

### 🆕 Dashboard V4 — Terminal Style
**Apa:** Redesign total dashboard dari V3 ke V4.
**Fitur:**
- Dark terminal theme dengan grid layout
- 6 tabs: Market, Leaders, Recovery, Protection, Simulation, Diagnostics
- Bottom sheet per ticker (Overview + Factors)
- Cards/Table toggle view
- Conviction badges (Strong Buy / Buy / Hold / Avoid / Strong Sell)
- Drag-to-dismiss bottom sheet (mobile)
- Config switch (Config B vs F)
- Right intelligence panel
- Rotation widget & column

### 📄 Project Handover
**Apa:** Dokumentasi handover lengkap.
**File:** `docs/PROJECT_HANDOVER_2026-06-07.md`

---

## 2026-06-01

### 🔧 Monthly Pipeline Jalan
Pipeline bulanan Juni berhasil jalan via GitHub Actions. Collectors, scoring, dashboard regenerate.

---

## 2026-05-?? — 2026-01

### 🏗️ Research & Development Bertahap
- Momentum factor confirmed sebagai core factor (FINDING_001)
- Growth factor failure documented (FINDING_010): revenue growth IC negatif
- Weight optimization & comparison (Config B vs F)
- Warehouse V2 & V3 build (multi-year backtest data)
- Turnaround detection logic
- Exit state machine (4 rules)
- Foreign flow synthetic generator

---

## 2025-???

### 🚀 Project Dimulai
- Initial setup: collect → score → dashboard
- IDX30 universe selection
- Yahoo Finance integration
- ADR-001: Factor-based scoring approach
- ADR-002: Yahoo Finance exclusive data source
- V1, V2, V3 dashboard evolution
