# FMP API Migration Audit Report
Audit Date: 2026-06-01
Target Symbol: BBRI.JK

Laporan ini menganalisis transisi dari endpoint legacy FMP (V3) yang tidak didukung untuk akun baru ke stable endpoints pengganti.

## Ringkasan Temuan

| Endpoint Test | URL Path | Status | Records | Historis? |
| :--- | :--- | :--- | :--- | :--- |
| Legacy Ratios (Path-based) | `https://financialmodelingprep.com/api/v3/ratios/BBRI.JK?limit=5&apikey=HIDDEN` | 403 | 0 | N/A |
| Legacy Financial Growth (Path-based) | `https://financialmodelingprep.com/api/v3/financial-growth/BBRI.JK?limit=5&apikey=HIDDEN` | 403 | 0 | N/A |
| Stable Ratios (Query Param) | `https://financialmodelingprep.com/stable/ratios?symbol=BBRI.JK&limit=5&apikey=HIDDEN` | 402 | 0 | N/A |
| Stable Ratios (Path-based) | `https://financialmodelingprep.com/stable/ratios/BBRI.JK?limit=5&apikey=HIDDEN` | 404 | 0 | N/A |
| Stable Ratios TTM (Query Param) | `https://financialmodelingprep.com/stable/ratios-ttm?symbol=BBRI.JK&apikey=HIDDEN` | 402 | 0 | N/A |
| Stable Ratios TTM (Path-based) | `https://financialmodelingprep.com/stable/ratios-ttm/BBRI.JK?apikey=HIDDEN` | 404 | 0 | N/A |
| Stable Financial Growth (Query Param) | `https://financialmodelingprep.com/stable/financial-growth?symbol=BBRI.JK&limit=5&apikey=HIDDEN` | 402 | 0 | N/A |
| Stable Financial Growth (Path-based) | `https://financialmodelingprep.com/stable/financial-growth/BBRI.JK?limit=5&apikey=HIDDEN` | 404 | 0 | N/A |

## Analisis Detail Per Endpoint

### Legacy Ratios (Path-based)
* **Request URL**: `https://financialmodelingprep.com/api/v3/ratios/BBRI.JK?limit=5&apikey=HIDDEN`
* **Status Code**: `403`
* **Error/Detail**: Endpoint legacy atau tidak valid. Respons:
```
{
  "Error Message": "Legacy Endpoint : Due to Legacy endpoints being no longer supported - This endpoint is only available for legacy users who have valid subscriptions prior August 31, 2025. Please visit our documentation page https://site.financialmodelingprep.com/developer/docs for our current APIs. "
}
```

---

### Legacy Financial Growth (Path-based)
* **Request URL**: `https://financialmodelingprep.com/api/v3/financial-growth/BBRI.JK?limit=5&apikey=HIDDEN`
* **Status Code**: `403`
* **Error/Detail**: Endpoint legacy atau tidak valid. Respons:
```
{
  "Error Message": "Legacy Endpoint : Due to Legacy endpoints being no longer supported - This endpoint is only available for legacy users who have valid subscriptions prior August 31, 2025. Please visit our documentation page https://site.financialmodelingprep.com/developer/docs for our current APIs. "
}
```

---

### Stable Ratios (Query Param)
* **Request URL**: `https://financialmodelingprep.com/stable/ratios?symbol=BBRI.JK&limit=5&apikey=HIDDEN`
* **Status Code**: `402`
* **Error/Detail**: Endpoint legacy atau tidak valid. Respons:
```
Premium Query Parameter: 'Special Endpoint : This value set for 'symbol' is not available under your current subscription please visit our subscription page to upgrade your plan at https://financialmodelingprep.com/
```

---

### Stable Ratios (Path-based)
* **Request URL**: `https://financialmodelingprep.com/stable/ratios/BBRI.JK?limit=5&apikey=HIDDEN`
* **Status Code**: `404`
* **Error/Detail**: Endpoint legacy atau tidak valid. Respons:
```
[]
```

---

### Stable Ratios TTM (Query Param)
* **Request URL**: `https://financialmodelingprep.com/stable/ratios-ttm?symbol=BBRI.JK&apikey=HIDDEN`
* **Status Code**: `402`
* **Error/Detail**: Endpoint legacy atau tidak valid. Respons:
```
Premium Query Parameter: 'Special Endpoint : This value set for 'symbol' is not available under your current subscription please visit our subscription page to upgrade your plan at https://financialmodelingprep.com/
```

---

### Stable Ratios TTM (Path-based)
* **Request URL**: `https://financialmodelingprep.com/stable/ratios-ttm/BBRI.JK?apikey=HIDDEN`
* **Status Code**: `404`
* **Error/Detail**: Endpoint legacy atau tidak valid. Respons:
```
[]
```

---

### Stable Financial Growth (Query Param)
* **Request URL**: `https://financialmodelingprep.com/stable/financial-growth?symbol=BBRI.JK&limit=5&apikey=HIDDEN`
* **Status Code**: `402`
* **Error/Detail**: Endpoint legacy atau tidak valid. Respons:
```
Premium Query Parameter: 'Special Endpoint : This value set for 'symbol' is not available under your current subscription please visit our subscription page to upgrade your plan at https://financialmodelingprep.com/
```

---

### Stable Financial Growth (Path-based)
* **Request URL**: `https://financialmodelingprep.com/stable/financial-growth/BBRI.JK?limit=5&apikey=HIDDEN`
* **Status Code**: `404`
* **Error/Detail**: Endpoint legacy atau tidak valid. Respons:
```
[]
```

---
