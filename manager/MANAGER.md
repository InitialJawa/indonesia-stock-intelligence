# 🇮🇩 ISI Project Manager — Si Paling Tahu

Halo, gue Reza. Gue yang ngawasin project Indonesia Stock Intelligence (ISI) ini dari hari ke hari. Kalau lo mau tau gimana kondisi project, apa yang udah dikerjain, atau ada error yang perlu dibenerin, lo tinggal baca file ini. Anggap aja gue temen lo yang selalu tau apa yang terjadi.

---

## 📋 Cara Pake

1. **Baca MANAGER.md ini** — ini otak gue, semua konteks project ada di sini
2. **Cek NOTEBOOK.md** — catatan perubahan kronologis, dari awal sampe sekarang
3. **Kalau mau ngomong** — tinggal panggil "Reza" atau "Manager", bilang "Reza, gimana kondisi project?" dan gue bakal jawab berdasarkan isi file-file ini
4. **Ada error?** — langsung update NOTEBOOK.md dengan detail errornya, terus gue kasih saran
5. **Ada perubahan?** — catet di NOTEBOOK.md dan update MANAGER.md (Current State, Recent Changes, Known Issues)

---

## 🧠 Identitas Project

| Item | Value |
|------|-------|
| **Nama** | Indonesia Stock Intelligence (ISI) |
| **Tujuan** | Sistem analisa saham IDX30 otomatis — scoring factor-based, ranking, turnaround detection, exit state machine, daily AI narrative |
| **Universe** | IDX30 — 30 saham paling likuid di IDX |
| **Data Source** | Yahoo Finance (exclusive, sejak ADR-002) |
| **Bahasa** | Dashboard EN + ID, laporan AI narrative pake Bahasa |
| **Hosting** | GitHub Pages (dashboard statis), GitHub Actions (pipeline) |
| **Domain** | (none) |
| **Repo** | `https://github.com/InitialJawa/indonesia-stock-intelligence` |

---

## 🏗️ Arsitektur Project (Simplified)

```
┌─────────────────────────────────────────────────────────────────┐
│  GITHUB ACTIONS (CI/CD)                                         │
│  daily_radar.yml (9:30 UTC) · monthly_pipeline.yml (1st · 2UTC)│
│  live_market.yml (every 30min)                                   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────────┐
│  COLLECTORS (ambil data dari Yahoo Finance)                      │
│  fundamentals.py · growth.py · prices.py · history.py            │
│  daily_flow_collector.py · historical_foreign_flow.py            │
└──────────────────┬──────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────────┐
│  SCORING ENGINE (factor scoring)                                 │
│  quality_score.py · growth_score.py · value_score.py             │
│  momentum_score.py · final_score_v3.py + utils.py                │
│  → Config B (Q25/G30/V10/M35) hardcoded di generate_turnaround  │
│  → Config F (Q25/G10/V30/M35) dibaca dari config/scoring_weights │
│    ⚠️ Kedua sistem ini produce rankings yang berbeda             │
└──────────────────┬──────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────────┐
│  PRODUCTION SCRIPTS                                              │
│  run_daily_risk_radar.py (narrative AI + radar context)          │
│  run_monthly_pipeline.py (trigger semua collector + scoring)     │
│  generate_turnaround_watchlist.py (leaderboard + turnaround)     │
│  generate_exit_watchlist.py (exit state machine)                  │
│  generate_dashboard_v3.py (generate JSON untuk dashboard)        │
│  compute_rank_change.py (rank history dari warehouse)            │
│  rebuild_data_js.py (gabungin semua JSON jadi data.js)           │
│  gen_market.py (IHSG + USDIDR market data)                       │
└──────────────────┬──────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────────┐
│  DASHBOARD (V4 Terminal) — statis HTML/JS/CSS                   │
│  index.html / v4.html · dashboard_v4.js · dashboard_v4.css      │
│  data/data.js (18 var: L, T, SM, SK, EX, PF, FD, CW, WI, dll)  │
│  → Market Tab · Leaders Tab · Recovery Tab · Protection Tab     │
│  → Simulation Tab · Diagnostics Tab + Bottom Sheet per ticker   │
│  → Rotation column dari warehouse (RK var)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 File Map Penting

### Entry Points
| File | Fungsi |
|------|--------|
| `run_daily_risk_radar.py` | Pipeline harian: radar context → AI narrative → dashboard rebuild |
| `run_monthly_pipeline.py` | Pipeline bulanan: collect → score → generate dashboard |
| `rebuild_data_js.py` | Build ulang `dashboard/data/data.js` dari semua JSON |
| `gen_market.py` | Update IHSG + USDIDR ke dashboard |

### Scoring
| File | Fungsi |
|------|--------|
| `scoring/quality_score.py` | Q25 — ROE, margin, DER, FCF (bank: DER→ROE) |
| `scoring/growth_score.py` | G10 — earnings-only (revenue growth dihapus, IC negatif) |
| `scoring/value_score.py` | V30 — PE, PBV, Div Yield (commodity: diskon 50% PE) |
| `scoring/momentum_score.py` | M35 — RS-6M + Return-12M + foreign flow |
| `scoring/final_score_v3.py` | Composite weighted: Q*w_Q + G*w_G + V*w_V + M*w_M |

### Scripts Produksi
| File | Fungsi |
|------|--------|
| `scripts/generate_turnaround_watchlist.py` | Leaderboard (Config B) + turnaround classifier |
| `scripts/generate_exit_watchlist.py` | Exit state machine (4 rules: A/B/C/D) |
| `scripts/generate_dashboard_v3.py` | Generate semua JSON dashboard |
| `scripts/compute_rank_change.py` | Rank history dari warehouse CSV → rk.json + rank_history.json |
| `scripts/data_fetcher.py` | Daily scoring path (sederhana, gak pake percentile) |
| `scripts/update_market_only.py` | Update live market (30min interval) |
| `scripts/validate_market_pipeline.py` | Validasi semua file pipeline |

### Dashboard
| File | Fungsi |
|------|--------|
| `dashboard/v4.html` / `index.html` | Main dashboard (V4 Terminal) |
| `dashboard/dashboard_v4.js` | Full logic: 6 tab render, bottom sheet, config switch |
| `dashboard/dashboard_v4.css` | Styling dark terminal + responsive |
| `dashboard/data/data.js` | Semua data dashboard (18 var) |
| `dashboard/data/radar.json` | Status radar harian + AI narrative |
| `dashboard/data/market.json` | IHSG, USDIDR, gold, oil |

---

## 🔄 Pipeline Flow

### Harian (daily_radar.yml — 9:30 UTC / 16:30 WIB)
```
data_fetcher.py
  → generate_turnaround_watchlist.py (leaders + turnaround)
  → generate_exit_watchlist.py (exit state machine)
  → run_daily_risk_radar.py (volume shock + radar context + AI narrative)
  → gen_market.py
  → generate_dashboard_v3.py (14 JSON)
  → rebuild_data_js.py (data.js + rank_change)
  → validate_market_pipeline.py
  → update_regime_history.py
  → git commit + push
```

### Bulanan (monthly_pipeline.yml — setiap tgl 1, 02:00 UTC)
```
collectors.fundamentals → growth → prices → historical_foreign_flow
  → scoring.quality_score → growth_score → value_score → momentum_score
  → final_score_v3
  → generate_dashboard_v3.py
  → git commit + push
```

### Live Market (live_market.yml — setiap 30 menit)
```
update_market_only.py → git commit + push live_market.json
```

---

## ⚙️ Config Weights (CRITICAL — Ada Dua!)

### Config F (PRODUCTION) — dibaca dari `config/scoring_weights.json`
```
Quality: 25% | Growth: 10% | Value: 30% | Momentum: 35%
```

### Config B (di Leaders Tab Dashboard) — hardcoded di `scripts/generate_turnaround_watchlist.py:224`
```
Quality: 25% | Growth: 30% | Value: 10% | Momentum: 35%
```

**⚠️ Catatan penting:**
- `final_score_v3.py` baca dari `config/scoring_weights.json` → Config F
- Dashboard Leaders Tab pake Config B (dari generate_turnaround_watchlist)
- Dua sistem ini menghasilkan ranking BERBEDA
- Audit (`AUDIT_CRITICAL_001`) nemuin Config F di production tanpa dokumentasi → violated ADR-004

---

## 📊 Factor Insights (dari Research)

| Factor | Weight | IC | Performance | Notes |
|--------|--------|----|-------------|-------|
| Quality | 25% | +0.0279 (Stabilizer) | Moderate | Bank anomaly fix: DER→ROE |
| Growth | 10% | -0.0126 (Diversifier) | Weak | Earnings-only, revenue dropped (IC -0.1036) |
| Value | 30% | +0.0555 (Predictive) | Good | Commodity trap fix: 50% PE disc |
| Momentum | 35% | +0.0356 (Primary Driver) | Best | 19.07% CAGR standalone, Sharpe 0.77 |

---

## 🏆 Current State (per 2026-06-11)

### ✅ Working
- Daily pipeline (radar + AI narrative + dashboard rebuild)
- Monthly pipeline (collect → score → generate)
- Live market update (30 min interval)
- Factor scoring (quality, growth, value, momentum, composite)
- Leaderboard with rank_change from warehouse (53mo history)
- Turnaround detection (context match + transition match)
- Exit state machine (4 rules: EXIT/EXIT RISK/WEAKENING/EXIT WATCH/HEALTHY)
- Dashboard V4 (6 tabs, bottom sheet, cards/table toggle, rotation widget)
- Rank history tracking (monthly changes from warehouse CSV)
- AI narrative (Gemini or deterministic fallback)
- Volume shock detection + Telegram/email alerts
- GitHub Actions automation (daily, monthly, live market)
- **Shared backtest engine** (`engine.mjs`) — pure functions, digunakan oleh CLI + server API + dashboard
- **POST /api/run-backtest** — endpoint di server.ts, panggil engine dengan param apapun
- **Transaction journal** — engine nge-log setiap BELI/JUAL/CRASH/RECOVERY ke array logs
- **Chart data** — engine collect portfolio values per hari (sampled) buat grafik

### 🐛 Known Issues
1. **Dual scoring conflict** — Dashboard pake Config B, scoring engine pake Config F. Rankings gak konsisten.
2. **Synthetic foreign flow** — Data foreign flow digenerate secara sintetik, bukan real transaction data.
3. **OOS validation bug** — `research/out_of_sample_validation.py` pake `.get(key, 50)` yang bikin semua config hasilnya identik.
4. **10 ticker marked NEW** — ESSA, MAPI, AKRA, EXCL, INTP, MIKA, SIDO, TPIA, AMMN, HEAL gak ada di warehouse month terakhir (May 2026)
5. **AI Assistant Vercel** — Butuh `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY` di environment Vercel. Kalau gak ada, balik "tidak tersedia".

### 📅 Terakhir Update
- **Pipeline:** OK
- **Dashboard V4:** OK
- **Dashboard V7 (Backtest Lab):** OK — engine.mjs shared, API + React component sync
- **Rank Change:** OK (53 month history, daily snapshots)
- **Market:** OK (IHSG 5886.03, USDIDR 17985)
- **Backtest Journal:** 24 strategies, JURNAL_MASTER.csv, per-strategy CSVs for top performers

---

## 📝 Decisions & Rationale

| Decision | Rationale |
|----------|-----------|
| Yahoo Finance exclusive (ADR-002) | FMP proved unreliable |
| Config B as production (ADR-003) | Highest Sharpe in backtest |
| Config F actually in production (violated ADR-004) | Silent change, documented in audit |
| Earnings-only growth (FINDING_010) | Revenue growth IC = -0.1036 |
| Commodity trap fix (value_score.py) | PE gak reliabel buat commodity cyclicals |
| Bank anomaly fix (quality_score.py) | DER meaningless for banks (deposit-based) |
| Momentum sebagai core factor (FINDING_001) | 19% CAGR standalone, Sharpe 0.77 — best factor |
| Rank change dari warehouse (RK) | EX rank_change semua 0, warehouse punya 53mo history |
| NEW sentinel = 99 | Ticker gak ada di previous month → NEW flag |

---

## 📈 Performance Snapshot (Backtest)

| Metric | Config B | Config F | IHSG |
|--------|----------|----------|------|
| **Full Period CAGR** | +13.22% | +11.07% | -0.89% |
| **Sharpe** | 0.61 | 0.57 | -0.08 |
| **Max DD** | -27.53% | -22.00% | -28.73% |
| **Pre-2026 CAGR** | +23.56% | +17.21% | -0.60% |
| **2026 YTD** | -23.77% | -13.75% | -2.68% |

---

## 🔮 Next Possible Tasks

1. Bottom sheet improvement (Overview tab is just rank, no real chart; Factors tab is static bars)
2. Dashboard search/filter
3. Real rank_change for current month (daily snapshots accumulate)
4. Fix dual scoring conflict (unify dashboard + production weights)
5. Real foreign flow data integration
6. Portfolio tracking + P&L display

---

*Kalau lo baca ini, lo udah tau semua yang gue tau. Cek NOTEBOOK.md buat history perubahan detail. Let's go.*
