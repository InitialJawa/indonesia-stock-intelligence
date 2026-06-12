// engine.mjs — Shared backtest engine
// Pure data-in/data-out, works in Node.js & Browser (no I/O, no DOM)

/**
 * Normalize daily data row to { date, ihsg, gold, stocks, ranks }
 * Accepts both CLI format (ihsg/gold/stocks/ranks) and API format (ihsgPrice/goldPrice/stockPrices/stockRanks)
 */
export function normalizeDay(day) {
  return {
    date: day.date,
    ihsg: day.ihsg ?? day.ihsgPrice ?? 0,
    gold: day.gold ?? day.goldPrice ?? 0,
    stocks: day.stocks ?? day.stockPrices ?? {},
    ranks: day.ranks ?? day.stockRanks ?? {}
  };
}

function addLog(logs, date, action, ticker, price, shares, cashAfter, totalVal, detail) {
  logs.push({ date, action, ticker, price: Math.round(price), shares, cashAfter: Math.round(cashAfter), totalVal: Math.round(totalVal), detail: detail || "" });
}

export function runAlgo(rawData, opts = {}) {
  const {
    topN = 3, crashPct = 5, safeHaven = "cash",
    crossOverOn = true, reservePct = 10, capital = 100_000_000
  } = opts;

  const data = rawData.map(normalizeDay);
  let cash = capital - capital * (reservePct / 100);
  const buffer = capital * (reservePct / 100);
  let goldG = 0, inCrash = false, crashCd = 0;
  let positions = {};
  let logs = [];
  let maxVal = cash;
  let maxDD = 0;
  let totalSwaps = 0;
  const initIhsg = data[0].ihsg;
  const initGold = data[0].gold;

  const chartData = [];

  const topInit = Object.entries(data[0].ranks).sort((a, b) => a[1] - b[1]).slice(0, topN).map(x => x[0]);
  const alloc = cash / topInit.length;
  topInit.forEach(tk => {
    const p = data[0].stocks[tk];
    const s = Math.floor(alloc / p);
    positions[tk] = s;
    cash -= s * p;
    addLog(logs, data[0].date, "BELI", tk, p, s, cash + buffer, cash + s * p + buffer, `INISIAL TOP-${topN}`);
  });

  for (let i = 0; i < data.length; i++) {
    const day = data[i];
    const sv = Object.entries(positions).reduce((s, [tk, sh]) => s + sh * day.stocks[tk], 0);
    const gv = goldG * day.gold;
    const pv = cash + gv + sv + buffer;

    if (i % 8 === 0 || i === data.length - 1) {
      chartData.push({
        date: day.date, strategi: Math.round(pv),
        ihsg: Math.round((day.ihsg / initIhsg) * capital),
        gold: Math.round((day.gold / initGold) * capital),
      });
    }
    if (pv > maxVal) maxVal = pv;
    else maxDD = Math.max(maxDD, (maxVal - pv) / maxVal * 100);

    let crashSig = false, crashReason = "";
    if (i >= 5) {
      const ihsg5d = data[i - 5].ihsg;
      if ((day.ihsg - ihsg5d) / ihsg5d * 100 <= -2) { crashSig = true; crashReason = "VELOCITY -2%/5D"; }
      if (!crashSig && i >= 60) {
        const hi60 = Math.max(...data.slice(i - 60, i + 1).map(x => x.ihsg));
        if ((day.ihsg - hi60) / hi60 * 100 <= -crashPct) { crashSig = true; crashReason = `HIGH-60D -${crashPct}%`; }
      }
    }
    if (crashSig && !inCrash && crashCd <= 0) {
      inCrash = true;
      const posSnapshot = { ...positions };
      let liq = 0;
      Object.entries(positions).forEach(([tk, sh]) => liq += sh * day.stocks[tk]);
      positions = {};
      cash += liq;
      Object.entries(posSnapshot).forEach(([tk, sh]) =>
        addLog(logs, day.date, "JUAL-CRASH", tk, day.stocks[tk], sh, cash + buffer, cash + buffer, crashReason));
      if (safeHaven === "gold") { goldG = cash / day.gold; cash = 0; addLog(logs, day.date, "BELI-EMAS", "EMAS", day.gold, goldG, cash + buffer, goldG * day.gold + buffer, "SAFE HAVEN"); }
      crashCd = 20;
    }

    if (inCrash && crashCd <= 0) {
      const crashLow = Math.min(...data.slice(Math.max(0, i - 60), i + 1).map(x => x.ihsg));
      if ((day.ihsg - crashLow) / crashLow * 100 >= 3) {
        inCrash = false;
        let rc = cash;
        if (goldG > 0) { const gv2 = goldG * day.gold; addLog(logs, day.date, "JUAL-EMAS", "EMAS", day.gold, goldG, rc + gv2, rc + gv2 + buffer, "RECOVERY"); rc += gv2; goldG = 0; }
        const topR = Object.entries(day.ranks).sort((a, b) => a[1] - b[1]).slice(0, topN).map(x => x[0]);
        const a2 = rc / topR.length;
        topR.forEach(tk => { const p = day.stocks[tk]; const s = Math.floor(a2 / p); positions[tk] = s; rc -= s * p; addLog(logs, day.date, "BELI-RECOVERY", tk, p, s, rc + buffer, rc + s * p + buffer, `RE-ENTRY TOP-${topN}`); });
        cash = rc;
        crashCd = 20;
      }
    }
    if (crashCd > 0) crashCd--;

    if (!inCrash && crossOverOn) {
      for (const [tk, sh] of Object.entries(positions)) {
        if (sh > 0 && (day.ranks[tk] ?? 99) >= 7) {
          const sellVal = sh * day.stocks[tk];
          delete positions[tk];
          addLog(logs, day.date, "JUAL-SWAP", tk, day.stocks[tk], sh, cash + sellVal + buffer, cash + sellVal + buffer, `RANK ${day.ranks[tk]} >=7`);
          const cands = Object.entries(day.ranks).sort((a, b) => a[1] - b[1]).slice(0, 4).map(x => x[0]);
          const swapIn = cands.find(t => !positions[t]) || cands[0];
          const bp = day.stocks[swapIn];
          const ns = Math.floor(sellVal / bp);
          positions[swapIn] = (positions[swapIn] || 0) + ns;
          cash += sellVal - ns * bp;
          addLog(logs, day.date, "BELI-SWAP", swapIn, bp, ns, cash + buffer, cash + ns * bp + buffer, `SWAP DARI ${tk}`);
          totalSwaps++;
          break;
        }
      }
    }
  }

  const last = data[data.length - 1];
  const finalSV = Object.entries(positions).reduce((s, [tk, sh]) => s + sh * last.stocks[tk], 0);
  const finalVal = cash + goldG * last.gold + finalSV + buffer;
  return {
    finalVal: Math.round(finalVal), ret: (finalVal - capital) / capital * 100,
    ihsgRet: (last.ihsg - initIhsg) / initIhsg * 100,
    goldRet: (last.gold - initGold) / initGold * 100,
    maxDD, totalSwaps, logs, chartData
  };
}

export function runSingle(rawData, ticker, opts = {}) {
  const { sellPct = 8, buyPct = 5, safeHaven = "cash", capital = 100_000_000 } = opts;
  const data = rawData.map(normalizeDay);
  let cash = capital, goldG = 0, shares = 0, inStock = false, peak = 0, trough = Infinity;
  let logs = [];
  const chartData = [];
  const initIhsg = data[0].ihsg, initGold = data[0].gold;

  for (let i = 0; i < data.length; i++) {
    const day = data[i];
    const price = day.stocks[ticker] || 1000;
    if (!inStock) {
      if (trough === Infinity || price >= trough * (1 + buyPct / 100)) {
        shares = Math.floor(cash / price);
        if (shares > 0) { cash -= shares * price; peak = price; inStock = true; addLog(logs, day.date, "BELI", price, shares, cash, cash + shares * price, trough === Infinity ? "INISIAL" : `RE-ENTRY ${ticker}`); }
      }
    }
    const pv = cash + shares * price + goldG * day.gold;
    if (i % 8 === 0 || i === data.length - 1) {
      chartData.push({
        date: day.date, strategi: Math.round(pv),
        ihsg: Math.round((day.ihsg / initIhsg) * capital),
        gold: Math.round((day.gold / initGold) * capital),
      });
    }

    if (inStock) {
      if (price > peak) peak = price;
      if ((price - peak) / peak * 100 <= -sellPct) {
        cash += shares * price;
        addLog(logs, day.date, "JUAL", price, shares, cash, cash, `DROP ${((price - peak) / peak * 100).toFixed(1)}%`);
        if (safeHaven === "gold") { goldG = cash / day.gold; cash = 0; addLog(logs, day.date, "BELI-EMAS", day.gold, goldG, 0, goldG * day.gold, "SELAMAT KE EMAS"); }
        shares = 0; inStock = false; trough = price; peak = 0;
      }
    }
  }

  const last = data[data.length - 1];
  const finalVal = cash + shares * (last.stocks[ticker] || 1000) + goldG * last.gold;
  return {
    finalVal: Math.round(finalVal), ret: (finalVal - capital) / capital * 100,
    ihsgRet: (last.ihsg - initIhsg) / initIhsg * 100,
    goldRet: (last.gold - initGold) / initGold * 100,
    trades: logs.length, logs, chartData
  };
}
