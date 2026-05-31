# Audit Penggunaan FMP (Financial Modeling Prep) pada ISI V5

Laporan ini memverifikasi bagaimana `MultiSourceProvider` dalam file `utils/data_provider.py` beroperasi terkait integrasi data FMP (Financial Modeling Prep) dan fallback Yahoo Finance (YFinance).

## 1. Apakah FMP benar-benar digunakan?
**Ya, jika environment variable `FMP_API_KEY` dikonfigurasi.**
Jika kunci tersebut tersedia di sistem (`self.fmp_api_key` tidak None), `MultiSourceProvider` akan selalu mencoba mengambil metrik dari FMP terlebih dahulu melalui metode `_fetch_from_fmp()`. Namun, jika kunci tersebut kosong atau tidak disetel, sistem secara otomatis menerbitkan log:
`[INFO] FMP_API_KEY tidak ditemukan. Fallback murni ke YFinance.`
dan langsung mengarahkan semua kueri ke Yahoo Finance.

## 2. Kapan fallback ke Yahoo Finance terjadi?
Fallback ke Yahoo Finance (`_fetch_from_yfinance()`) terjadi dalam kondisi berikut:
1. **FMP_API_KEY tidak disetel** pada environment sistem.
2. **Kueri metrik yang tidak didukung oleh FMP** (seperti `free_cash_flow` yang tidak terdaftar di dalam `ratios_map` maupun `growth_map` FMP milik `MultiSourceProvider`).
3. **Terjadi error atau limit kuota tercapai** pada request FMP (ditangkap oleh blok `try...except` di `get_fundamental_metric` yang secara senyap/silently meneruskan eksekusi ke YFinance).
4. **Data yang dikembalikan FMP bernilai `None`** atau kosong untuk ticker tertentu.

## 3. Endpoint FMP apa saja yang digunakan?
Terdapat 2 endpoint API FMP v3 yang dipanggil oleh provider:
1. **Ratios Endpoint**: 
   `https://financialmodelingprep.com/api/v3/ratios/{ticker}?limit=1&apikey={self.fmp_api_key}`
2. **Financial Growth Endpoint**: 
   `https://financialmodelingprep.com/api/v3/financial-growth/{ticker}?limit=1&apikey={self.fmp_api_key}`

## 4. Metrik apa saja yang berasal dari FMP?
Jika FMP aktif, metrik berikut diambil dari FMP:
* `pe_ratio` (dipetakan ke `priceEarningsRatio`)
* `roe` (dipetakan ke `returnOnEquity`)
* `debt_to_equity` (dipetakan ke `debtEquityRatio`)
* `pb_ratio` (dipetakan ke `priceToBookRatio`)
* `dividend_yield` (dipetakan ke `dividendYield`)
* `net_margin` (dipetakan ke `netProfitMargin`)
* `operating_margin` (dipetakan ke `operatingProfitMargin`)
* `revenue_growth` (dipetakan ke `revenueGrowth`)
* `earnings_growth` (dipetakan ke `netIncomeGrowth`)

*Catatan: Metrik `free_cash_flow` **tidak pernah** diambil dari FMP karena tidak diimplementasikan di `_fetch_from_fmp`.*

## 5. Metrik apa saja yang berasal dari Yahoo Finance?
Semua metrik memiliki pemetaan ke Yahoo Finance (`stock.info`) sebagai fallback:
* `pe_ratio` (dipetakan ke `trailingPE`)
* `roe` (dipetakan ke `returnOnEquity`)
* `debt_to_equity` (dipetakan ke `debtToEquity` / 100)
* `pb_ratio` (dipetakan ke `priceToBook`)
* `dividend_yield` (dipetakan ke `dividendYield`)
* `net_margin` (dipetakan ke `profitMargins`)
* `operating_margin` (dipetakan ke `operatingMargins`)
* `free_cash_flow` (dipetakan ke `freeCashflow` — **selalu YFinance**)
* `revenue_growth` (dipetakan ke `revenueGrowth`)
* `earnings_growth` (dipetakan ke `earningsGrowth`)
