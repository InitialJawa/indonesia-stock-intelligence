# ISI Dashboard — Design System
> Inspired by Stockbit's visual language: dark navy surfaces, dense data tables, green/red sentiment colors, clean sans-serif typography.

---

## 1. Brand Identity

- **Product**: Indonesia Stock Intelligence (ISI)
- **Tone**: Professional, data-dense, analytical — seperti terminal trading, bukan halaman marketing
- **Paradigm**: Dark-first. Semua komponen dirancang untuk dark background, light mode adalah opsional

---

## 2. Color Palette

### Background Layers (Dark)
```
--bg-base:       #0D1117   /* halaman utama — paling gelap */
--bg-surface:    #161B22   /* card, panel, sidebar */
--bg-elevated:   #1C2128   /* modal, dropdown, tooltip */
--bg-border:     #21262D   /* garis pemisah antar section */
```

### Text
```
--text-primary:    #E6EDF3   /* heading, nilai utama */
--text-secondary:  #8B949E   /* label, subtitle, placeholder */
--text-muted:      #484F58   /* disabled, hint */
```

### Accent — Green (bullish, positif, aktif)
```
--green-strong:  #3FB950   /* nilai naik, badge aktif, CTA utama */
--green-muted:   #1A3A26   /* background badge positif */
--green-border:  #238636   /* border badge positif */
```

### Accent — Red (bearish, negatif, exit)
```
--red-strong:    #F85149   /* nilai turun, sinyal exit, Risk OFF */
--red-muted:     #3D1C1C   /* background badge negatif */
--red-border:    #DA3633   /* border badge negatif */
```

### Accent — Amber (netral, defensif, peringatan)
```
--amber-strong:  #D29922   /* regime transisi, Defensif */
--amber-muted:   #2D2110   /* background badge amber */
--amber-border:  #9E6A03   /* border badge amber */
```

### Accent — Blue (informasi, link, highlight aktif)
```
--blue-strong:   #388BFD   /* tab aktif, link, sorotan */
--blue-muted:    #0D2044   /* background info */
--blue-border:   #1F6FEB   /* border info */
```

---

## 3. Typography

```
Font: 'Inter', 'Segoe UI', system-ui, sans-serif

/* Hierarchy */
--text-xl:   22px / weight 600   /* nilai metrik besar (CAGR, Score) */
--text-lg:   16px / weight 500   /* heading section, tab aktif */
--text-md:   14px / weight 400   /* body, isi tabel */
--text-sm:   12px / weight 400   /* label, caption, badge */
--text-xs:   11px / weight 400   /* footer, timestamp, hint */

/* Angka finansial: selalu gunakan font-variant-numeric: tabular-nums */
/* agar kolom tabel angka rata */
```

---

## 4. Spacing & Layout

```
/* Base unit: 4px */
--space-1:   4px
--space-2:   8px
--space-3:   12px
--space-4:   16px
--space-6:   24px
--space-8:   32px

/* Border radius */
--radius-sm:  4px    /* badge, tag kecil */
--radius-md:  6px    /* tombol, input */
--radius-lg:  8px    /* card, panel */

/* Border */
--border-default: 1px solid #21262D
--border-focus:   1px solid #388BFD
```

---

## 5. Components

### 5.1 Status Badge
Digunakan untuk: Risk ON/OFF, regime pasar, status sinyal.

```
Struktur: background muted + border tipis + teks strong (warna sama)
Padding: 2px 8px
Font: 11px, weight 500
Border-radius: var(--radius-sm)

Contoh:
Risk OFF → bg: --red-muted,   border: --red-border,   text: --red-strong
Risk ON  → bg: --green-muted, border: --green-border, text: --green-strong
Defensif → bg: --amber-muted, border: --amber-border, text: --amber-strong
```

### 5.2 Metric Card
Digunakan untuk: CAGR, Alokasi Modal, Score Gap, Alpha.

```
Background: --bg-surface
Border: --border-default
Border-radius: var(--radius-lg)
Padding: 12px 16px

Label: 12px, --text-secondary, margin-bottom 4px
Value: 22px, weight 600, --text-primary
Delta (opsional): 12px, warna sesuai positif/negatif

JANGAN: border tebal, background solid berwarna, shadow dekoratif
```

### 5.3 Data Table
Digunakan untuk: Leaders, Exit Monitor, History, Turnaround.

```
Header:
  background: --bg-elevated
  font: 11px uppercase, --text-secondary, letter-spacing 0.05em
  padding: 8px 12px
  border-bottom: --border-default

Row:
  font: 14px, --text-primary
  padding: 10px 12px
  border-bottom: 1px solid --bg-border
  hover background: --bg-elevated

Angka naik:  warna --green-strong
Angka turun: warna --red-strong
Angka netral: warna --text-secondary

font-variant-numeric: tabular-nums  ← WAJIB untuk semua kolom angka
```

### 5.4 Tab Navigation
Digunakan untuk: Market / Leaders / Turnaround / History / Exit / dst.

```
Container: background --bg-surface, border-bottom --border-default

Tab aktif:
  color: --text-primary
  border-bottom: 2px solid --blue-strong
  font-weight: 500

Tab inaktif:
  color: --text-secondary
  border-bottom: 2px solid transparent
  hover color: --text-primary

Font: 14px
Padding: 10px 16px
Transition: border-color 150ms ease
```

### 5.5 Button
```
Primary (CTA):
  background: --green-strong
  color: #0D1117
  border: none
  font: 13px weight 500
  padding: 6px 16px
  border-radius: var(--radius-md)
  hover: brightness 110%

Secondary:
  background: transparent
  color: --text-primary
  border: --border-default
  hover background: --bg-elevated

Destructive / Exit:
  background: transparent
  color: --red-strong
  border: 1px solid --red-border
```

### 5.6 Chart / Equity Curve
```
Background: --bg-surface
Grid lines: --bg-border (tipis, jangan mengganggu)
Line ISI:  #3FB950 (green)
Line IHSG: #8B949E (abu-abu)
Area fill: gradient transparan dari warna line ke bg-surface
Tooltip: background --bg-elevated, border --border-default
```

### 5.7 Section Header
```
Font: 14px, weight 500, --text-primary
Border-bottom: --border-default, margin-bottom 12px
Icon (opsional): 16px, --text-secondary, margin-right 8px
Keterangan/subtitle: 12px, --text-secondary
```

---

## 6. States & Feedback

```
Positif / Bullish:  --green-strong  (#3FB950)
Negatif / Bearish:  --red-strong    (#F85149)
Netral / Sideways:  --text-secondary (#8B949E)
Peringatan:         --amber-strong  (#D29922)
Informasi:          --blue-strong   (#388BFD)

Exit State:
  EXIT      → --red-strong + red badge
  EXIT RISK → --amber-strong + amber badge
  HEALTHY   → --green-strong + green badge
  WEAKENING → --text-secondary + gray badge
```

---

## 7. Anti-patterns (JANGAN dilakukan)

- ❌ Jangan pakai background putih/terang untuk card utama
- ❌ Jangan pakai warna solid penuh (bukan muted) untuk badge — terlihat seperti lampu
- ❌ Jangan pakai border-radius > 8px untuk komponen data (terlihat mobile app, bukan terminal)
- ❌ Jangan campur banyak warna berbeda dalam satu tabel
- ❌ Jangan pakai font-weight 700+ — terlalu berat untuk data dense
- ❌ Jangan pakai shadow dekoratif — flat saja
- ❌ Angka finansial tanpa tabular-nums akan terlihat tidak rata di tabel

---

## 8. Referensi Visual
Stockbit.com — dark navy, data-dense, green/red sentiment, clean typography, minimal dekorasi.