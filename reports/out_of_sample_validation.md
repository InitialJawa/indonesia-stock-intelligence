# ISI Out-of-Sample Validation Report

> Generated: 2026-06-05 18:48 WIB  
> Framework: ISI V8.4 — Institutional OOS Validation

---

## 🏆 Verdict Akhir

> [!NOTE]
> **✅ PASS**  
> Performa stabil lintas periode. Tidak ada degradasi signifikan terdeteksi.  

---

## 📐 Data Split

| Periode | Range | Jumlah Bulan Return |
|:--------|:------|:--------------------|
| **TRAIN** | 2019-02 → 2023-12 | 59 |
| **VALIDATION** | 2024-01 → 2024-12 | 12 |
| **TEST** | 2025-01 → sekarang | 17 |

> [!IMPORTANT]
> Tidak ada parameter yang dipilih menggunakan data TEST.

---

## 📊 Performance Metrics Per Periode

| Metric | TRAIN | VALIDATION | TEST | Δ Train→Test |
|:-------|------:|----------:|-----:|------------:|
| **CAGR** | 0.53% | -5.18% | 6.35% | +5.82% |
| **Sharpe** | 0.15 | -0.21 | 0.35 | +0.20 |
| **Sortino** | 0.14 | -0.17 | 0.35 | +0.21 |
| **Max Drawdown** | 39.66% | 17.69% | 30.59% | -9.07% |
| **Win Rate** | 57.63% | 58.33% | 47.06% | -10.57% |
| **Alpha vs IHSG** | -0.15% | -2.06% | 23.58% | +23.72% |
| **Beta vs IHSG** | 1.36 | 0.81 | 1.29 | -0.07 |
| **Excess CAGR** | -1.68% | -2.53% | 16.05% | +17.73% |

| **Turnover (est.)** | 26.55% | 29.09% | 22.50% | — |

---

## ⚙️ Weight Configuration Optimization (TRAIN + VALIDATION Only)

> [!NOTE]
> Optimization dilakukan **hanya** pada data TRAIN + VALIDATION. Data TEST tidak disentuh.

| Konfigurasi | Quality | Growth | Value | Momentum | TRAIN Sharpe | VAL Sharpe | VAL CAGR |
|:------------|--------:|------:|------:|--------:|-----------:|----------:|--------:|
| **Config_A (Legacy Equal) ⭐** | 30% | 25% | 20% | 25% | 0.18 | -0.37 | -7.84% |
| **Config_B (Alpha Optimized)** | 25% | 30% | 10% | 35% | 0.18 | -0.37 | -7.84% |
| **Config_C (Momentum Heavy)** | 20% | 25% | 5% | 50% | 0.18 | -0.37 | -7.84% |
| **Config_D (Quality First)** | 40% | 25% | 10% | 25% | 0.18 | -0.37 | -7.84% |
| **Config_E (Balanced)** | 25% | 25% | 25% | 25% | 0.18 | -0.37 | -7.84% |

**Konfigurasi Produksi Aktif:** `{'quality': 0.25, 'growth': 0.3, 'value': 0.1, 'momentum': 0.35}`

---

## 🔍 Detail TRAIN

- **Periode**: `2019-02` → `2023-12`  
- **Jumlah Bulan**: `59`  
- **CAGR**: `0.53%`  
- **Ann. Return**: `4.16%`  
- **Volatility**: `27.06%`  
- **Sharpe**: `0.15`  
- **Sortino**: `0.14`  
- **Max Drawdown**: `39.66%`  
- **Win Rate**: `57.63%`  
- **CAPM Alpha vs IHSG**: `-0.15%`  
- **Beta vs IHSG**: `1.36`  
- **Benchmark CAGR (IHSG)**: `2.21%`  
- **Best Month**: `+25.21%`  
- **Worst Month**: `-21.16%`  

## 🔍 Detail VALIDATION

- **Periode**: `2024-01` → `2024-12`  
- **Jumlah Bulan**: `12`  
- **CAGR**: `-5.18%`  
- **Ann. Return**: `-3.83%`  
- **Volatility**: `17.90%`  
- **Sharpe**: `-0.21`  
- **Sortino**: `-0.17`  
- **Max Drawdown**: `17.69%`  
- **Win Rate**: `58.33%`  
- **CAPM Alpha vs IHSG**: `-2.06%`  
- **Beta vs IHSG**: `0.81`  
- **Benchmark CAGR (IHSG)**: `-2.65%`  
- **Best Month**: `+7.48%`  
- **Worst Month**: `-8.48%`  

## 🔍 Detail TEST (Evaluasi Final)

- **Periode**: `2025-01` → `2026-05`  
- **Jumlah Bulan**: `17`  
- **CAGR**: `6.35%`  
- **Ann. Return**: `13.82%`  
- **Volatility**: `39.34%`  
- **Sharpe**: `0.35`  
- **Sortino**: `0.35`  
- **Max Drawdown**: `30.59%`  
- **Win Rate**: `47.06%`  
- **CAPM Alpha vs IHSG**: `+23.58%`  
- **Beta vs IHSG**: `1.29`  
- **Benchmark CAGR (IHSG)**: `-9.70%`  
- **Best Month**: `+15.77%`  
- **Worst Month**: `-22.82%`  

---

## 📋 Aturan OOS Validation (Wajib Dipatuhi)

1. **Optimization hanya pada TRAIN** — bobot, parameter, threshold tidak boleh diubah berdasarkan data TEST.
2. **Seleksi konfigurasi via VALIDATION** — pilih konfigurasi dengan Sharpe tertinggi di periode VALIDATION.
3. **TEST adalah hakim final** — jalankan sekali, tanpa tuning ulang, tanpa cherry-picking.
4. **Semua riset faktor baru wajib melewati framework ini** sebelum boleh diintegrasikan ke production.
5. **Verdict FAIL = rollback** — jika TEST memberikan verdict FAIL, konfigurasi aktif harus di-rollback ke versi stabil sebelumnya.

---

*Report ini digenerate otomatis oleh `research/out_of_sample_validation.py` — ISI V8.4*
