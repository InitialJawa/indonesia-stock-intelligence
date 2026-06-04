import pandas as pd
tickers = ["PTBA.JK", "ICBP.JK", "BBCA.JK", "SMGR.JK", "GGRM.JK"]
for t in tickers:
    df = pd.read_csv(f"database/monthly/{t}.csv")
    df["month_key"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m")
    val = df[df["month_key"] == "2019-02"]
    if not val.empty:
        print(f"{t}: Price={val['month_end_price'].values[0]:.2f}, Return={val['monthly_return'].values[0]*100:.2f}%")
    else:
        print(f"{t}: No data for 2019-02")
