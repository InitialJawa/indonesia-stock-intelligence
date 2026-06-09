# BUG-006 Insight Layer Regression — Diagnosis

## A. Last commit where Insight Layer existed

**`ba41195`** — `fix: remove PF reference from conclusion IIFE to avoid const TDZ ReferenceError`

This was the last commit on the `main` branch where `dashboard/index.html` contained the complete Insight Layer V1:
- Kesimpulan Hari Ini narrative banner (`<div id="conclusion">` + IIFE)
- Per-tab insight cards (`#insight-leaders`, `#insight-top10`, `#insight-turnaround`, `#insight-exit`)
- Help modal system (`.help-modal` HTML, `const HLP`, `showHelp/closeHelp`)
- All supporting CSS (`.insight-*`, `.conc-*`, `.help-*`, `.tip` popup trigger)

## B. First commit where Insight Layer disappeared

**`96f5307`** — `feat: daily turnaround watchlist + Dashboard V2 read-only`

This commit regenerated `dashboard/index.html` from `generate_dashboard_v2.py` (author: `github-actions[bot]`). The generator had **never contained** Insight Layer display code — the Insight Layer was only ever embedded directly into `dashboard/index.html` via merge PR `#1` (`a2c428a`, merging `e881e07` from `feature/insight-layer-v1`). Regeneration overwrote the handwritten HTML, wiping all Insight Layer elements.

## C. Exact lines removed

The diff `ba41195..96f5307` on `dashboard/index.html` shows ~686 lines deleted, ~268 added. The removed sections fall into 5 groups:

### C1. CSS (~120 lines)
| Pattern | Lines removed |
|---------|---------------|
| `.tip` behavior (cursor:pointer → cursor:help + interactive styling) | 1 |
| `.panel` positioning (translateX → right:-420px) + `.panel-dragging` | 3 |
| `.help-modal`, `.help-hdr`, `.help-title`, `.help-close`, `.help-body`, `.help-section`, `.help-section-title`, `.help-body ul li` | ~30 |
| `.conc`, `.conc-hdr`, `.conc-status.s-*`, `.conc-label`, `.conc-body`, `.conc-col`, `.conc-sub`, `.conc-list li` | ~20 |
| `@media(max-width:600px)` block (help/conc/insight responsive rules) | ~40 |
| `@media(max-width:430px)` block (help/conc/insight mobile rules) | ~20 |
| `@media(min-width:601px)` block | ~5 |
| `.insight-*` (`.insight-card`, `-hdr`, `-title`, `-grid`, `-row`, `-lbl`, `-val`, `-badge`, `-note`) | ~30 |

### C2. HTML elements (~15 lines)
| Element | Purpose |
|---------|---------|
| `<div id="insight-leaders">` | Insight card injection point on Leaders tab |
| `<div id="insight-top10">` | Top-10 insight card on Leaders tab |
| `<div id="insight-turnaround">` | Insight card injection point on Turnaround tab |
| `<div id="insight-exit">` | Insight card injection point on Exit Monitor tab |
| `<div id="conclusion">` | Kesimpulan Hari Ini narrative banner (above tabs) |
| `<span class="tip" onclick="showHelp(...)">?` on 15 section titles | Interactive help triggers |
| `<div class="help-modal" id="help">` + children | Help modal overlay |
| `<button class="help-close">` | Help modal close button |
| `<div class="overlay" id="overlay">` changed to `onclick="closePanel()"` | Overlay click behavior added (was passive) |

### C3. JS data object (1 large object)
| Removed | Lines |
|---------|-------|
| `const HLP = { leaders: '...', turnaround: '...', diagnostics: '...', exit: '...', saham_tertekan: '...', mulai_membaik: '...', kandidat_turnaround: '...', kekuatan_mulai_naik: '...', minat_beli_meningkat: '...', di_atas_trend_pendek: '...', pantul_dari_dasar: '...', rata_penurunan: '...', rata_gejolak: '...' }` | ~14 lines |
| Inline `const L`, `const T`, `const SM`, `const SK`, `const EX` (hardcoded data) | ~5 large JSON lines |

### C4. Kesimpulan Hari Ini IIFE (~100 lines)
The narrative analysis IIFE that:
1. Computes `exitCount`, `exitRiskCount`, `weakeningCount`, etc. from `EX`
2. Analyzes `avgDD`, `avgVol`, `aboveMA20`, `rsPositive` from `SM.signal_diagnostics`
3. Identifies `top5`, `top10`, `bot5` leaders and strongest/weakest factors
4. Classifies `status` (`TIDAK ADA AKSI`/`RISIKO MENINGKAT`/`REVIEW`/`TAHAN`) with color class
5. Builds 3 narrative sections: `Pimpinan Pasar`, `Kandidat Turnaround`, `Tekanan Pasar`
6. Generates focus list (max 3 items)
7. Renders `<div class="conc">` HTML with status badge + sections into `#conclusion`

### C5. Per-tab insight card rendering (~50 lines in ticker click handler)
Functions that render insight cards:
- `document.getElementById('insight-leaders').innerHTML = h` — shows top-5 comparison vs bottom-5
- `document.getElementById('insight-top10').innerHTML = h` — shows top-10 dispersion
- `document.getElementById('insight-turnaround').innerHTML = h` — shows turnaround match breakdown
- `document.getElementById('insight-exit').innerHTML = h` — shows exit state distribution
- `document.getElementById('conclusion').innerHTML = h` — renders Kesimpulan Hari Ini

## D. Dependency graph

```
ba41195 dashboard/index.html
├── CSS: .insight-*, .conc-*, .help-*, .tip (interactive)
├── HTML elements
│   ├── #conclusion (above tabs)
│   ├── #insight-leaders, #insight-top10 (Leaders tab)
│   ├── #insight-turnaround (Turnaround tab)
│   ├── #insight-exit (Exit tab)
│   ├── .tip (15× section-title help triggers)
│   └── #help modal + overlay
├── const HLP (13 help content objects)
├── Kesimpulan Hari Ini IIFE (~100 lines)
│   ├── Depends on: const L, const T, const SM, const SK, const EX
│   ├── Reads: signal_diagnostics, top_candidates, exit_state, rank
│   └── Writes: #conclusion.innerHTML
├── Per-tab insight rendering
│   ├── Depends on: const L, const T, const EX, aiExplain()
│   └── Writes: #insight-*, #conclusion
├── function showHelp(k)
│   ├── Reads: const HLP, const titles
│   └── Writes: #htitle, #hbody, #help.show
├── function closeHelp()
│   └── Writes: #help.show → false
└── function tickerData(t) (SURVIVED)
    ├── Reads: const L, const T, const PF, const FD
    ├── Calls: aiExplain(), renderFundamentals(), renderAlignment()
    └── Writes: #ptk, #pname, #pbody, #panel.show, #overlay.show
```

**Key insight**: The ticker click panel (`tickerData`, `aiExplain`, `renderFundamentals`, `renderAlignment`, `closePanel`, `const PF`, `const FD`, panel HTML) **survived** because it lives in `generate_dashboard_v2.py`'s template and gets regenerated every run. Only the **display-layer elements** (Kesimpulan Hari Ini, per-tab insight cards, help modal) were lost because they existed **exclusively** in `dashboard/index.html` as handwritten additions from the feature branch merge.

## E. Safe restoration plan

All lost code exists in the git history at `ba41195:dashboard/index.html`. Since the generator already contains the ticker panel functions, restoration only requires adding the **display-layer** components back into the generator template in `build_html()`:

### Step 1 — Add CSS blocks
- `.insight-*` classes (~30 lines)
- `.conc-*` classes (~20 lines)  
- `.help-*` classes (~30 lines)
- `.tip` interactive styling (change cursor:help → cursor:pointer)
- `.panel` positioning (restore translateX/transform behavior)
- Responsive `@media` blocks for help/conc/insight

### Step 2 — Add HTML container elements
- `<div id="conclusion">` above tab navigation
- `<div id="insight-leaders">` + `<div id="insight-top10">` in Leaders tab
- `<div id="insight-turnaround">` in Turnaround tab
- `<div id="insight-exit">` in Exit Monitor tab
- `<span class="tip" onclick="showHelp('...')">?` on section titles (Leaders, Turnaround, Diagnostics, Exit, and 9 Daily Summary cards)
- `<div class="help-modal" id="help">` + children + overlay wiring

### Step 3 — Add JS data and functions
- `const HLP` object (13 help texts) — inject via Jinja/Python template
- `function showHelp(k)` / `function closeHelp()`

### Step 4 — Add Kesimpulan Hari Ini IIFE
This is the largest piece (~100 lines). It can be parameterized using existing template vars (`const L`, `const T`, `const SM`, `const SK`, `const EX`).

### Step 5 — Add per-tab insight card rendering
- Inside the `tickerData`/click handler or as a standalone IIFE that runs on page load
- Renders summary cards from leader/turnaround/exit data into `#insight-*` containers

### Pre-existing (no action needed)
- `const PF`, `const FD` — already in generator
- `function tickerData`, `aiExplain`, `renderFundamentals`, `renderAlignment`, `closePanel` — already in generator
- Panel HTML (`<div class="panel" id="panel">` + children) — already in generator
- `.panel-*`, `.align-*`, `.fd-*`, `.interp-*` CSS — already in generator
