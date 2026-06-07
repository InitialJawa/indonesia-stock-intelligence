# Indonesia Stock Intelligence (ISI)

Sistem riset dan monitoring saham IDX30 berbasis multi-faktor.

## Struktur Repository

```
root/                           # Entry points + config
├── run_daily_risk_radar.py     Jalankan daily pipeline
├── run_monthly_pipeline.py     Jalankan monthly pipeline
├── requirements.txt            Dependensi Python
├── .github/workflows/          CI/CD otomatis
│
scripts/                        # Production scripts
├── data_fetcher.py             Fetch harga harian
├── generate_turnaround_watchlist.py  Ranking + turnaround
├── generate_exit_watchlist.py  Exit state machine
└── generate_dashboard_v2.py    Generator dashboard HTML
│
scoring/                        # Factor scoring engine
collectors/                     # Data collectors (Yahoo Finance)
utils/                          # Shared utilities
│
dashboard/index.html            # Dashboard output (6 tabs)
data/current/                   # Live CSVs (leaders, turnaround, exit)
data/state/                     # Live JSONs (summary, profiles)
database/                       # Historical data warehouse
research/                       # Research scripts + tools
docs/                           # Dokumentasi
```

## Cara Menjalankan

```bash
# Daily pipeline (fetch harga + turnaround + exit + dashboard)
python run_daily_risk_radar.py

# Monthly pipeline (fetch fundamentals + score + dashboard)
python run_monthly_pipeline.py

# Individual scripts
python scripts/generate_dashboard_v2.py
python scripts/generate_turnaround_watchlist.py
python scripts/generate_exit_watchlist.py
```

## Sistem Produksi

| Komponen | Status | Lokasi |
|----------|--------|--------|
| Config B (Q25/G30/V10/M35) | PRODUCTION | `scoring/final_score_v3.py` |
| Daily Pipeline | ACTIVE | `.github/workflows/daily_radar.yml` |
| Monthly Pipeline | ACTIVE | `.github/workflows/monthly_pipeline.yml` |
| Dashboard | ACTIVE | `dashboard/index.html` |
| Turnaround Watchlist | MONITORING | `scripts/generate_turnaround_watchlist.py` |
| Exit Monitor V1.1 | ACTIVE | `scripts/generate_exit_watchlist.py` |

## Performansi (88 bulan, 2019-2026)

| Metric | Config B | Turnaround Top 5 |
|--------|:--------:|:-----------------:|
| CAGR | +0.82% | -0.17% |
| Sharpe | 0.17 | 0.13 |
| CAPM Alpha | +4.47% | +3.05% |

## Dokumentasi Lengkap

Baca `docs/MASTER_CHRONICLE_V3.md` untuk pemahaman menyeluruh.
