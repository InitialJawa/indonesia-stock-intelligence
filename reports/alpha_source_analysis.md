# Alpha Source Analysis by Market Regime

Analisis sumber alpha portofolio momentum pada berbagai kondisi pasar (Market Regimes).

## 1. Definisi Market Regime
- **Bull Market Month**: Bulan di mana IHSG return $> +1.0\%$
- **Bear Market Month**: Bulan di mana IHSG return $< -1.0\%$
- **Sideways Market Month**: Bulan di mana IHSG return antara $-1.0\%$ dan $+1.0\%$

## 2. Kinerja Berdasarkan Regime

| Market Regime | Jumlah Bulan | Rata-rata Return Portfolio | Rata-rata Return IHSG | Rata-rata Excess Return |
| :--- | :---: | :---: | :---: | :---: |
| **Bull Market** | 35 | 5.60% | 3.76% | +1.84% |
| **Bear Market** | 26 | -4.07% | -5.02% | +0.95% |
| **Sideways Market** | 27 | 2.49% | 0.06% | +2.43% |

## 3. Kesimpulan Regresi Regime
- **Bull Market Capture**: Momentum berhasil menangkap tren bull market dengan sangat baik, mengungguli IHSG secara signifikan ketika pasar sedang naik.
- **Bear Market Protection**: Ketika IHSG turun tajam, portofolio momentum ikut turun tetapi dengan excess return positif yang menandakan ketahanan relatif yang baik dibanding pasar keseluruhan.
- **Sideways Outperformance**: Pada pasar datar, momentum tetap mencatatkan excess return positif yang konsisten.
