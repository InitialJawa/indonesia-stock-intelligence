# BUG-006 Restore Inventory

Source: `a2c428a` (merge commit: `feature/insight-layer-v1` into `main`)
File: `dashboard/index.html`

All counts verified against the actual checkout of `a2c428a:dashboard/index.html` (989 lines).

---

## 1. CSS Blocks Count: **5 groups** (~106 unique declaration lines, ~164 total lines including responsive)

| Group | Declarations | Lines | Notes |
|-------|-------------|-------|-------|
| `.insight-*` (card, hdr, title, grid, row, lbl, val, badge, note) | 16 | 16 | Static analysis card styling |
| `.help-*` (modal, hdr, title, close, body, section, ul li) | 16 | 16 | Help modal popup |
| `.conc-*` (card, hdr, status, label, body, col, sub, list li) | 25 | 25 | Kesimpulan Hari Ini banner |
| `.tip` / `.tip:hover` | 2 | 2 | Interactive help trigger (cursor:pointer) |
| `.panel` positioning + `.panel-dragging` | 2 | 2 | translateX vs right; drag-to-close |
| **Subtotal (static)** | **61** | **61** | |
| `@media(max-width:600px)` responsive rules for insight/help/conc/panel/tip | — | ~48 | Mobile responsive |
| `@media(max-width:430px)` responsive rules | — | ~48 | Small mobile responsive |
| `@media(min-width:601px)` responsive rules | — | ~7 | Tablet responsive |
| **Total CSS** | **~61 declarations** | **~164 lines** | |

---

## 2. HTML Container Blocks Count: **8 elements** + **13 tip triggers**

| Container | Count | Purpose |
|-----------|-------|---------|
| `<div id="insight-leaders">` | 1 | Injection point for Leaders analysis card (Leaders tab) |
| `<div id="insight-top10">` | 1 | Injection point for Top 10 summary card (Leaders tab) |
| `<div id="insight-turnaround">` | 1 | Injection point for Turnaround breakdown card (Turnaround tab) |
| `<div id="insight-exit">` | 1 | Injection point for Exit analysis card (Exit Monitor tab) |
| `<div id="conclusion">` | 1 | Kesimpulan Hari Ini narrative banner (before tab-nav) |
| `<div class="help-modal" id="help">` (+ children) | 1 | Help modal overlay with hdr/close/body |
| `<div class="overlay" id="overlay">` | 1 | Background overlay (was passive, got `onclick="closePanel()"`) |
| `<span class="tip" onclick="showHelp(...)">?` | **13** | Help trigger buttons on section titles |
| **Total distinct containers** | **8** | |

---

## 3. HLP Object: **13 entries**

| Key | Help content topic |
|-----|-------------------|
| `leaders` | Config B Leaders scoring explanation |
| `turnaround` | Turnaround detection methodology |
| `diagnostics` | Pipeline health and data freshness |
| `exit` | Exit rule system (A/B/C/D levels) |
| `saham_tertekan` | Distressed stocks definition |
| `mulai_membaik` | Stocks starting to recover |
| `kandidat_turnaround` | Full turnaround candidates |
| `kekuatan_mulai_naik` | Relative strength improvement |
| `minat_beli_meningkat` | High volume buying interest |
| `di_atas_trend_pendek` | Price above MA20 |
| `pantul_dari_dasar` | Bounce from 60-day low |
| `rata_penurunan` | Average drawdown across IDX30 |
| `rata_gejolak` | Average volatility across IDX30 |

File location (a2c428a): lines ~340-373, ~18 lines total in object definition.

---

## 4. Kesimpulan IIFE Line Count: **78 lines**

```
Line 422: (function(){
Line 423-492: Computation (exit counts, signal diagnostics, portfolio exit, status classification, reasons array, focuses array)
Line 493-497: HTML generation (conc-card with status badge + Alasan + Fokus Hari Ini lists)
Line 498: document.getElementById('conclusion').innerHTML = h
Line 499: })();
```

**What it does:**
- Computes `exitCount`, `exitRiskCount`, `weakeningCount`, `exitWatchCount`, `healthyCount` from `EX`
- Identifies `top5` leaders, `portfolioExit` intersection
- Reads `SM.signal_diagnostics` (avgDD, avgVol, aboveMA20, rsPositive)
- Computes `rankDrops`, `bigDrops`
- Classifies status: `RISIKO MENINGKAT` / `REVIEW` / `TAHAN` / `TIDAK ADA AKSI`
- Builds `reasons` array (max 3) + `focuses` array (max 2)
- Renders `<div class="conc">` HTML into `#conclusion`

---

## 5. Insight Render IIFEs: **4 blocks** (98 lines total)

| Block | Lines | Container | Purpose |
|-------|-------|-----------|---------|
| **Leaders Analysis** | 21 (502-522) | `#insight-leaders` | Top5 vs Bottom5 score gap, strongest/weakest factors |
| **Top 10 Summary** | 23 (525-547) | `#insight-top10` | Average scores, sector distribution in top 10 |
| **Turnaround Analysis** | 23 (550-572) | `#insight-turnaround` | Full/context/transition/none counts, avg DD/recovery/vol |
| **Exit Analysis** | 31 (575-605) | `#insight-exit` | Exit state distribution, avg RS20, rule frequency |
| **Total** | **98** | **4 containers** | |

---

## 6. JS Functions: **3 new + 5 pre-existing**

### New (need to add to generator):
| Function | Lines | Purpose |
|----------|-------|---------|
| `function showHelp(k)` | ~9 | Opens help modal, reads `HLP[k]`, writes `#htitle`/`#hbody` |
| `function closeHelp()` | ~4 | Closes help modal |
| `const HLP = { ... }` | ~18 | 13 help content strings |

### Pre-existing in generator (no action needed):
| Function | Location (current generator) | Notes |
|----------|-----------------------------|-------|
| `function tickerData(t)` | Line 513 | Already present, unchanged |
| `function aiExplain(...)` | Line 521 | Already present, unchanged |
| `function renderFundamentals(fd)` | Line 556 | Already present, unchanged |
| `function renderAlignment(ld, td, ed)` | Line 625 | Already present, unchanged |
| `function closePanel()` | Line 692 | Already present, unchanged |
| `const PF = {...}` | Line 510 | Already present, unchanged |
| `const FD = {...}` | Line 511 | Already present, unchanged |

---

## Summary: Total Restoration Scope

| Category | Items | Lines |
|----------|-------|-------|
| CSS declarations | ~61 declarations | ~164 |
| HTML containers | 8 elements + 13 tip buttons | ~22 |
| HLP data object | 13 entries | ~18 |
| Kesimpulan IIFE | 1 block | 78 |
| Insight render IIFEs | 4 blocks | 98 |
| JS functions | 2 (showHelp, closeHelp) | ~13 |
| **Total** | | **~393 lines** |

All source code available at `a2c428a:dashboard/index.html`.
