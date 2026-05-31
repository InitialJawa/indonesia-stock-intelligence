# ADR-002-DATA-SOURCE: DATA SOURCE DECISION

**Status**: Accepted  
**Tanggal**: 2026-06-01  
**Primary Data Source**: Yahoo Finance  

## Context / Masalah
Sebelumnya, sistem Indonesia Stock Intelligence (ISI) menggunakan arsitektur hybrid yang menggabungkan Financial Modeling Prep (FMP) sebagai sumber data primer (melalui endpoint `/ratios` dan `/financial-growth`) dengan Yahoo Finance sebagai cadangan (fallback).

Namun, selama proses audit konektivitas FMP terbaru (V5.6.1), ditemukan bahwa FMP telah mendepresiasi endpoint legacy dan membatasi akses rasio keuangan pasar Indonesia (IDX) untuk pengguna baru terdaftar. Akses ke endpoint stable terbaru (seperti `/stable/ratios` dan `/stable/ratios-ttm`) diblokir dengan status `402 Payment Required` atau `403 Forbidden` di bawah paket gratis.

## Rationale / Alasan
Mempertahankan integrasi FMP dalam kondisi ini meningkatkan kompleksitas kode, utang teknis (technical debt), dan beban pemeliharaan (maintenance burden) tanpa memberikan nilai tambah karena semua permintaan akhirnya mengalami kegagalan dan jatuh kembali ke Yahoo Finance.

Yahoo Finance terpilih sebagai satu-satunya sumber data resmi karena:
1. **Gratis**: Tidak memerlukan kunci API berbayar atau langganan bulanan.
2. **Stabil**: Terbukti mampu mengembalikan seluruh metrik fundamental penting pasar Indonesia secara andal.
3. **Terintegrasi**: Sudah memiliki modul fallback dan cache yang matang dalam sistem.
4. **Mendukung Kebutuhan**: Mampu memenuhi kebutuhan rasio dan data pertumbuhan fundamental untuk scoring saat ini.

## Decision / Keputusan
Seluruh pipeline ISI (koleksi data, skoring, rebalancing, dan dashboard) akan diubah untuk menggunakan **Yahoo Finance secara eksklusif** sebagai satu-satunya sumber data resmi. Semua dependensi, fungsi pembungkus, cache, dan variabel lingkungan terkait FMP dihapus sepenuhnya dari kode produksi.

Keputusan ini berlaku sampai ada kebutuhan bisnis yang terbukti membutuhkan provider data berbayar lain yang lebih superior.
