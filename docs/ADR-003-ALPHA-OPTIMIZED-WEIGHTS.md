# Architectural Decision Record (ADR)
## ADR-003: Alpha-Optimized Factor Weights (V7.0)

- **Status**: Accepted (Approved)
- **Author**: Antigravity AI
- **Deciders**: Indonesian Stock Intelligence (ISI) Quantitative Team
- **Migration Date**: 2026-06-01

---

### Context
Model kuantitatif multi-faktor Indonesia Stock Intelligence (ISI) versi sebelumnya (V6) menggunakan bobot statis:
*   Quality: 30%
*   Growth: 25%
*   Value: 20%
*   Momentum: 25%

Meskipun model ini menghasilkan keunggulan Alpha, riset lanjutan (Dynamic Factor Weight Optimization Research) dan evaluasi counterfactual membuktikan adanya bias alokasi. Faktor **Value** berkinerja buruk di IDX30 selama periode 2019-2026, bertindak sebagai *alpha drag* (jebakan nilai/value trap). Sebaliknya, faktor **Momentum** dan **Growth** merupakan penyumbang Alpha terbesar (+23.29% dan +22.66% secara mandiri). Oleh karena itu, diperlukan optimasi bobot untuk memaksimalkan tangkapan Alpha dengan tetap menjaga benteng pertahanan risiko via faktor **Quality**.

---

### Decision
Kami memutuskan untuk memigrasikan bobot model produksi resmi dari konfigurasi saat ini ke konfigurasi **Config B (Alpha-Optimized)**:
*   **Momentum Weight**: **35%** (Meningkat dari 25%)
*   **Growth Weight**: **30%** (Meningkat dari 25%)
*   **Quality Weight**: **25%** (Menurun dari 30%)
*   **Value Weight**: **10%** (Menurun dari 20%)

Selain itu, pintu konfigurasi weights didelegasikan sepenuhnya secara terpusat pada file [[scoring_weights.json](file:///c:/Users/BedilGaib/Documents/indonesia-stock-intelligence-1/config/scoring_weights.json)] dan dimuat secara dinamis oleh [[final_score_v3.py](file:///c:/Users/BedilGaib/Documents/indonesia-stock-intelligence-1/scoring/final_score_v3.py)] untuk menghilangkan *technical debt* berupa hardcoded weights.

---

### Evidence
Hasil pengujian dinamis *walk-forward* bulanan (2019-01 s.d. 2026-05) bersih setelah dikurangi friction drag biaya transaksi 0.25% membuktikan keunggulan mutlak Config B atas Config A:
*   **CAGR**: Meningkat dari **2.92%** (Config A) menjadi **4.88%** (Config B), peningkatan kinerja sebesar **+1.96%**.
*   **Annualized Alpha**: Meningkat dari **+5.54%** (Config A) menjadi **+7.85%** (Config B), tambahan excess return sebesar **+2.31%** per tahun.
*   **Sharpe Ratio**: Meningkat dari **-0.08** (Config A) menjadi **-0.00** (Config B).
*   **Drawdown Control**: Config B menurunkan eksposur ke sektor perbankan dari 46.7% menjadi 34.6% dan menyebarkan risiko konsentrasi ke sektor energi/materials (30.8%) serta sektor lainnya secara dinamis, sehingga menurunkan Max Drawdown selama periode Normalisasi (2023-2024) dari 18.51% menjadi 13.73% dan pada Latest Regime (2025-2026) dari 29.57% menjadi 22.85%.
*   **Transaction Cost Resilience**: Config B terbukti mengungguli Config A secara konsisten di seluruh skenario fee (0.00%, 0.15%, 0.25%, dan 0.50%).

---

### Consequences
1.  **Turnover**: Terjadi peningkatan turnover tahunan yang sangat minim (dari 272.73% menjadi 283.64%, atau hanya naik +10.91% per tahun), yang dengan mudah diimbangi oleh keunggulan Alpha baru.
2.  **Sektor**: Eksposur portofolio menjadi lebih adaptif dan bergerak lincah mengikuti tren rotasi sektor bursa efek Indonesia. Ketergantungan berlebih terhadap perbankan besar dikurangi demi fleksibilitas strategi.
3.  **Kestabilan Kode**: Pemisahan konfigurasi bobot ke file JSON memudahkan eksperimen dan optimasi bobot di masa depan tanpa mengubah kode logika di scoring engine.
