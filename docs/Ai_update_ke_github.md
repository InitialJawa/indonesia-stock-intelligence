# AI OPERATING MANUAL

## Bahasa

Semua laporan dan dokumentasi menggunakan Bahasa Indonesia.

## Sebelum Edit Kode

WAJIB baca file berikut secara berurutan:

1. `docs/MASTER_CHRONICLE_V3.md` — kanonik, baca dulu sebelum kode
2. `docs/PROJECT_HANDOVER_2026-06-07.md` — onboarding cepat
3. File relevan lainnya

## Setelah Perubahan

Wajib:

1. Commit + push ke `origin/main`
2. Update MASTER_CHRONICLE (jika ada perubahan arsitektur/database/scoring)
3. Update RESEARCH_INDEX (jika ada temuan riset baru)
4. Update LESSONS_LEARNED (jika ada pelajaran baru)
5. Update ARCHITECTURE_TREE (jika ada perubahan struktur kode)
6. Update README (jika ada perubahan alur/cara pakai)
7. Buat laporan perubahan

## STABILIZATION MODE

V3 FREEZE aktif. Artinya:

- Tidak ada fitur baru (kecuali dashboard UX)
- Tidak ada perubahan Config B
- Tidak ada perubahan scoring/ranking/pipeline
- Tidak ada riset baru tanpa persetujuan eksplisit
- Yang BOLEH: perbaikan UX, dokumentasi, bugfix, monitoring

## Mobile UX — Pendekatan

Dashboard menggunakan 3 breakpoint CSS (tanpa JS):

| Breakpoint | Target |
|------------|--------|
| ≤600px | Tablet kecil / phablet |
| ≤430px | HP sempit (360-430px) |
| 601-1024px | Tablet landscape |

Tabel di HP: kolom non-esensial disembunyikan via CSS `nth-child`.
Panel samping: full-width di HP, 400px di desktop.
Tab-nav: sticky di HP, normal di desktop.
Touch target: icon `?` 28×28px (HP), 16×16px (desktop).
Transisi panel: `transform` (bukan `right`) agar smooth di semua ukuran layar.

## Panel KESIMPULAN HARI INI

Selalu muncul di atas tab navigasi. Tidak perlu data tambahan — dihitung
client-side dari data arrays L, T, EX, SM yang sudah ada.

Logika status (client-side JS):
- RISIKO MENINGKAT: ≥3 EXIT
- REVIEW: ≥1 EXIT atau ≥2 EXIT RISK
- TAHAN: turnaround ≥3 atau drawdown pasar dalam
- TIDAK ADA AKSI: tidak ada sinyal

## Help System

Semua tooltip menggunakan click-modal (bukan hover).
`HLP` object di JS berisi semua konten bantuan.
Format: Apa Artinya? / Mengapa Penting? / Cara Membaca? — bullet points.
Tidak ada istilah internal (Research-XXX, Context Match, dll) di teks pengguna.

## Prioritas

Repository aktual adalah sumber kebenaran.

Jika dokumentasi berbeda dengan kode:
ikuti kondisi repository.

## Larangan

Jangan membuat riset baru tanpa instruksi eksplisit.

Jangan mengubah kesimpulan riset yang sudah tervalidasi.

Jangan memberikan rekomendasi beli/jual di dashboard.
