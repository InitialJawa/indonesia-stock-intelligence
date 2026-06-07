"""Debug portfolio returns computation."""
import pandas as pd
import glob

wh = pd.read_csv("warehouse_historical/warehouse_v3.csv", usecols=["ticker","month","final_score","price"])
wh["month"] = pd.to_datetime(wh["month"])

prices = {}
for fp in glob.glob("database/monthly/*.csv"):
    ticker = fp.split("\\")[-1].replace(".csv","")
    df = pd.read_csv(fp)
    df["Date"] = pd.to_datetime(df["Date"])
    prices[ticker] = df

price_map = {}
for ticker, df in prices.items():
    for _, row in df.iterrows():
        price_map[(ticker, row["Date"])] = row["month_end_price"]

for month in wh["month"].unique()[:3]:
    me = month + pd.offsets.MonthEnd(0)
    nme = me + pd.offsets.MonthEnd(1)
    rows = []
    for _, row in wh[wh["month"] == month].iterrows():
        cp = price_map.get((row["ticker"], me))
        np_ = price_map.get((row["ticker"], nme))
        if cp and np_ and cp > 0 and np_ > 0:
            ret = (np_ / cp) - 1
            rows.append({"ticker": row["ticker"], "final_score": row["final_score"], "ret": ret})
    r = pd.DataFrame(rows)
    top5 = r.sort_values("final_score", ascending=False).head(5)
    print(f"Month {month.date()}: {len(r)} tickers")
    print(f"  Top 5: {top5['ticker'].tolist()}")
    print(f"  Returns: {[f'{x*100:.2f}%' for x in top5['ret']]}")
    print(f"  Mean return: {top5['ret'].mean()*100:.2f}%")
