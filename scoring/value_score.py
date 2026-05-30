import json
from datetime import date

# Baca data fundamental
with open("output/fundamentals.json") as f:
    data = json.load(f)

ranking = []

# Hitung score setiap saham
for ticker, info in data.items():

    score = 0

    roe = info.get("roe")
    pe = info.get("pe_ratio")
    pb = info.get("pb_ratio")

    # ROE
    if roe:
        score += roe * 100

    # PE
    if pe:
        if pe < 10:
            score += 20
        elif pe < 15:
            score += 10

    # PB
    if pb:
        if pb < 1.5:
            score += 20
        elif pb < 3:
            score += 10

    ranking.append({
        "ticker": ticker,
        "score": round(score, 2),
        "roe": roe,
        "pe": pe,
        "pb": pb
    })

# Urutkan dari score tertinggi
ranking = sorted(
    ranking,
    key=lambda x: x["score"],
    reverse=True
)

# Simpan ranking terbaru
with open("output/ranking.json", "w") as f:
    json.dump(ranking, f, indent=4)

# Simpan snapshot harian
today = str(date.today())

with open(f"output/history/{today}.json", "w") as f:
    json.dump(ranking, f, indent=4)

# Tampilkan hasil di terminal
print("\n=== VALUE RANKING ===\n")

for i, stock in enumerate(ranking, start=1):

    print(
        f"{i}. {stock['ticker']} | "
        f"Score={stock['score']} | "
        f"ROE={stock['roe']:.2%} | "
        f"PE={stock['pe']:.2f} | "
        f"PB={stock['pb']:.2f}"
    )

