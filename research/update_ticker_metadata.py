import csv
from pathlib import Path

METADATA_FILE = Path("database/historical/ticker_metadata.csv")

# Existing metadata
existing_rows = {}
if METADATA_FILE.exists():
    with open(METADATA_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_rows[row["ticker"]] = row["listing_date"]

# New historical tickers with their listing/IPO dates
new_tickers = {
    "ACES.JK": "2018-01-31",
    "ADMR.JK": "2022-01-03",
    "AADI.JK": "2024-12-05",
    "AMRT.JK": "2018-01-31",
    "ARTO.JK": "2018-01-31",
    "BBTN.JK": "2018-01-31",
    "BSDE.JK": "2018-01-31",
    "BTPS.JK": "2018-05-08",
    "BUKA.JK": "2021-08-06",
    "BUMI.JK": "2018-01-31",
    "EMTK.JK": "2018-01-31",
    "ERAA.JK": "2018-01-31",
    "GGRM.JK": "2018-01-31",
    "HMSP.JK": "2018-01-31",
    "HRUM.JK": "2018-01-31",
    "INCO.JK": "2018-01-31",
    "ISAT.JK": "2018-01-31",
    "JPFA.JK": "2018-01-31",
    "JSMR.JK": "2018-01-31",
    "LPKR.JK": "2018-01-31",
    "LPPF.JK": "2018-01-31",
    "MBMA.JK": "2023-04-18",
    "MEDC.JK": "2018-01-31",
    "MNCN.JK": "2018-01-31",
    "PGEO.JK": "2023-02-24",
    "PTPP.JK": "2018-01-31",
    "PWON.JK": "2018-01-31",
    "SRIL.JK": "2018-01-31",
    "TBIG.JK": "2018-01-31",
    "TINS.JK": "2018-01-31",
    "TKIM.JK": "2018-01-31",
    "TOWR.JK": "2018-01-31",
    "WSBP.JK": "2018-01-31",
    "WSKT.JK": "2018-01-31"
}

# Merge
for t, d in new_tickers.items():
    if t not in existing_rows:
        existing_rows[t] = d

# Write back
with open(METADATA_FILE, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["ticker", "listing_date"])
    for ticker in sorted(existing_rows.keys()):
        writer.writerow([ticker, existing_rows[ticker]])

print(f"Successfully updated {METADATA_FILE} to include all historical tickers.")
