# PROJECT HANDOVER — Indonesia Stock Intelligence

**Tanggal:** 2026-06-07  |  **Mode:** STABILIZATION  |  **Baca dulu:** `docs/MASTER_CHRONICLE_V3.md`

---

## Status Proyek

ISI adalah sistem riset saham Indonesia untuk indeks IDX30. Multi-factor ranking (Config B) dengan
turnaround watchlist dan exit monitor. Paper trading + dashboard monitoring. **Tidak ada ML,
tidak ada prediksi, tidak ada perubahan strategi produksi tanpa persetujuan eksplisit.**

## Sistem Produksi Aktif

| Sistem | Status | Keterangan |
|--------|--------|------------|
| Config B (Q25/G30/V10/M35) | PRODUCTION | Top 5 equal weight, monthly rebalance |
| Daily Pipeline | 16:30 WIB | GitHub Actions — harga, turnaround, exit, dashboard |
| Monthly Pipeline | 1st of month | GitHub Actions — fundamental, scoring, dashboard |
| Dashboard | 6 tabs | Leaders, Turnaround, Daily Summary, History, Diagnostics, Exit Monitor |
| Turnaround Watchlist | PAPER TRADING | 5-stage filter, watchlist only |
| Exit Monitor V1.1 | PAPER TRADING | Rule-based state machine (A/B/C/D) |
| Data Quality Rule PBV | ACTIVE | AUTO_VALIDATE — flag/fix/null extreme PBV |

## Temuan Penting

1. **Momentum is king** — RS-6M + Return12M = 19.07% CAGR standalone. Config B +0.82%.
2. **Timing overlay degrades** — R010 confirmed: all metrics worse with timing.
3. **Turnaround bukan strategi** — R011: negative CAGR (-0.17%). Watchlist only.
4. **Predictive sell impossible** — S01: losers look healthy at T0. Rule-based exits only.
5. **Data vendor tidak selalu benar** — AUDIT-001: PBV Yahoo salah untuk 8/30 IDX30.

## Audit yang Sudah Selesai

- **AUDIT-001 (KRITIS):** 8 ticker PBV salah (7 fixed via PE×ROE, 1 unfixable/MDKA).
  Dividend yield rendering 100× di dashboard diperbaiki (format `'dy'`).
- **AUDIT-002:** Verifikasi field Yahoo — bookValue/priceToBook salah, PE×ROE fallback
  terbaik (error <10%). sharesOutstanding akurat.

## Backlog Teknis

- Archive restoration — update `research/tools/` paths
- Dashboard cosmetic — AMMN revenue_growth cap, data quality flag display
- Automated exit watchlist paper trading execution
- Sector exposure monitoring

## Antrian Riset

- **Historical Factor Warehouse V2** — prerequisite for all weight/config research
- Config B vs Config F comparison
- Exit Rule D threshold backtest
- Turnaround-Config B correlation

## Risiko Terbuka

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| MDKA PBV = null | Value score MDKA terendah | Diterima — data limitation |
| AMMN revenue_growth 37937% | Tampilan dashboard misleading | Tidak pengaruh scoring |
| Yahoo data error pola komoditas | 8/30 ticker PBV bermasalah | Rule PBV menangani otomatis |
| Gemini AI free tier quota | 429 errors pada narrative | Belum critical |
| Historical data terbatas | Weight optimization terblokir | Partial V2 (2021+) mungkin feasible |

## Langkah Berikutnya

1. **Pertahankan STABILIZATION MODE** — no new features, no ranking changes
2. **Monitor data quality flags** di monthly pipeline
3. **Jika riset dilanjutkan:** bangun Historical Factor Warehouse V2 (minimal 2021+)
4. **Dokumentasi:** baca `MASTER_CHRONICLE_V3.md` sebelum perubahan kode apa pun
