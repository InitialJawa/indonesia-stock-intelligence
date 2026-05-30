import json

with open("../output/ranking.json") as f:
    ranking = json.load(f)

rows = ""

for i, stock in enumerate(ranking, start=1):
    rows += f"""
    <tr>
        <td>{i}</td>
        <td>{stock['ticker']}</td>
        <td>{stock['score']}</td>
        <td>{stock['roe']*100:.2f}%</td>
        <td>{stock['pe']:.2f}</td>
    </tr>
    """

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Indonesia Stock Intelligence</title>

<style>

body {{
    font-family: Arial, sans-serif;
    margin: 40px;
}}

table {{
    border-collapse: collapse;
    width: 100%;
}}

th, td {{
    border: 1px solid #ddd;
    padding: 10px;
}}

th {{
    background: #f2f2f2;
}}

</style>

</head>
<body>

<h1>Indonesia Stock Intelligence</h1>

<table>

<tr>
    <th>Rank</th>
    <th>Ticker</th>
    <th>Score</th>
    <th>ROE</th>
    <th>PE</th>
</tr>

{rows}

</table>

</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Dashboard generated!")