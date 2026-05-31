# file: scoring/quality_score.py

import json
import os
from scoring.utils import percentile_normalize

def main():
    # 1. Load Sector Rules untuk deteksi Anomali
    try:
        with open("config/sector_rules.json") as f:
            sector_rules = json.load(f)
            banks = sector_rules.get("financial_banks", [])
    except FileNotFoundError:
        banks = []

    with open("output/raw/fundamentals.json") as f:
        data = json.load(f)

    tickers = list(data.keys())

    roe_values = []
    net_margin_values = []
    op_margin_values = []
    fcf_values = []
    
    # Memisahkan pool data DER agar DPK bank tidak merusak kurva persentil saham normal
    debt_values_non_bank = []
    ticker_is_bank = []

    for ticker, info in data.items():
        is_bank = ticker in banks
        ticker_is_bank.append(is_bank)

        roe_values.append(info.get("roe") or 0)
        net_margin_values.append(info.get("net_margin") or 0)
        op_margin_values.append(info.get("operating_margin") or 0)
        
        fcf = info.get("free_cash_flow")
        fcf_values.append(fcf if fcf is not None else 0)

        debt = info.get("debt_to_equity") or 0
        
        if not is_bank:
            debt_values_non_bank.append(debt)

    # 2. Percentile Normalization
    roe_scores = percentile_normalize(roe_values)
    net_margin_scores = percentile_normalize(net_margin_values)
    op_margin_scores = percentile_normalize(op_margin_values)
    fcf_scores = percentile_normalize(fcf_values)
    
    # Hitung persentil DER HANYA untuk populasi non-bank
    debt_scores_non_bank = percentile_normalize(debt_values_non_bank)

    # Re-mapping skor DER ke dictionary
    debt_score_map = {}
    non_bank_idx = 0
    for i, ticker in enumerate(tickers):
        if not ticker_is_bank[i]:
            debt_score_map[ticker] = debt_scores_non_bank[non_bank_idx]
            non_bank_idx += 1
        else:
            debt_score_map[ticker] = 0  # Dummy, tidak akan dipakai

    ranking = []

    for i, ticker in enumerate(tickers):
        is_bank = ticker_is_bank[i]

        if is_bank:
            # RULE: Bank Anomaly. Matikan metrik DER. 
            # Bobot DER (20%) dialihkan untuk memperkuat ROE (25% -> 45%)
            w_roe = 0.45
            w_net = 0.20
            w_op  = 0.15
            w_debt = 0.0
            w_fcf  = 0.20
            debt_s = 0 
        else:
            # Standar Multi-Factor Weighting
            w_roe = 0.25
            w_net = 0.20
            w_op  = 0.15
            w_debt = 0.20
            w_fcf  = 0.20
            debt_s = 100 - debt_score_map[ticker] # Inverted: lower debt = higher score

        quality_score = (
            roe_scores[i] * w_roe +
            net_margin_scores[i] * w_net +
            op_margin_scores[i] * w_op +
            debt_s * w_debt +
            fcf_scores[i] * w_fcf
        )

        ranking.append({
            "ticker": ticker,
            "quality_score": round(quality_score, 2),
            "roe": roe_values[i],
            "net_margin": net_margin_values[i],
            "operating_margin": op_margin_values[i],
            "debt_to_equity": data[ticker].get("debt_to_equity", 0),
            "free_cash_flow": fcf_values[i],
            "is_bank": is_bank
        })

    ranking = sorted(ranking, key=lambda x: x["quality_score"], reverse=True)

    os.makedirs("output/scores", exist_ok=True)
    with open("output/scores/quality_ranking.json", "w") as f:
        json.dump(ranking, f, indent=4)

    print("\n=== QUALITY RANKING (PERCENTILE NORMALIZED + BANK ANOMALY FIX) ===\n")
    for i, stock in enumerate(ranking, start=1):
        bank_tag = "[BANK - DER EXCLUDED]" if stock["is_bank"] else ""
        print(f"{i}. {stock['ticker']} | Quality={stock['quality_score']} {bank_tag}")

if __name__ == "__main__":
    main()