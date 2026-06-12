import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const milestones = JSON.parse(fs.readFileSync(path.join(__dirname, "dashboard/dashboard_v7/data/milestones.json"), "utf-8"));
const factors = JSON.parse(fs.readFileSync(path.join(__dirname, "dashboard/dashboard_v7/data/stock_factors.json"), "utf-8"));

// Interpolate daily
function toUnix(y, m, d) { return new Date(y, m, d).getTime(); }
function lin(a, b, t) { return a + (b - a) * t; }

const dailyData = [];
const start = new Date("2020-01-01");
const end = new Date("2026-06-11");
for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
  dailyData.push({
    date: d.toISOString().slice(0, 10),
    time: d.getTime(),
  });
}

const msTimes = milestones.map(m => new Date(m.date).getTime());

// Fill prices
dailyData.forEach(day => {
  let mPrev = milestones[0], mNext = milestones[1];
  for (let m = 0; m < milestones.length - 1; m++) {
    if (day.time >= msTimes[m] && day.time <= msTimes[m + 1]) {
      mPrev = milestones[m]; mNext = milestones[m + 1]; break;
    }
  }
  const t = mNext.time !== mPrev.time ? (day.time - mPrev.time) / (mNext.time - mPrev.time) : 0;
  day.ihsg = lin(mPrev.ihsg, mNext.ihsg, t);
  day.gold = lin(mPrev.gold, mNext.gold, t);
  day.stocks = {};
  day.ranks = {};
  const tickers = Object.keys(mPrev.stocks);
  tickers.forEach(tk => {
    day.stocks[tk] = lin(mPrev.stocks[tk], mNext.stocks[tk], t);
    const f = factors[tk] || [40, 30, 20, 35];
    day.stocks[tk] = Math.max(10, Math.round(day.stocks[tk]));
    day.ranks[tk] = f[0]*0.30 + f[1]*0.25 + f[2]*0.15 + f[3]*0.30;
  });
  // Rank
  const sorted = tickers.sort((a, b) => day.ranks[b] - day.ranks[a]);
  sorted.forEach((tk, i) => day.ranks[tk] = i + 1);
});

// === STRATEGIES ===
function runAlgo(data, topN, crashPct, safeHaven, crossOverOn, reservePct) {
  let cash = 100_000_000;
  const buffer = cash * (reservePct / 100);
  let investable = cash - buffer;
  cash = investable;
  let goldG = 0, inCrash = false, crashCd = 0;
  let positions = {};
  let logs = [];
  let maxVal = cash;
  let maxDD = 0;
  let totalSwaps = 0;

  const day0 = data[0];
  const initIhsg = day0.ihsg;
  const initGold = day0.gold;

  // Day 0
  const topInit = Object.entries(day0.ranks).sort((a, b) => a[1] - b[1]).slice(0, topN).map(x => x[0]);
  const alloc = cash / topInit.length;
  topInit.forEach(tk => {
    const p = day0.stocks[tk];
    const s = Math.floor(alloc / p);
    positions[tk] = s;
    cash -= s * p;
  });

  for (let i = 0; i < data.length; i++) {
    const day = data[i];
    let sv = 0;
    Object.entries(positions).forEach(([tk, sh]) => { sv += sh * day.stocks[tk]; });
    const gv = goldG * day.gold;
    const pv = cash + gv + sv + buffer;
    if (pv > maxVal) maxVal = pv;
    else { const dd = (maxVal - pv) / maxVal * 100; if (dd > maxDD) maxDD = dd; }

    // Crash check
    let crashSig = false;
    if (i >= 60) {
      const hi60 = Math.max(...data.slice(i - 60, i + 1).map(x => x.ihsg));
      if ((day.ihsg - hi60) / hi60 * 100 <= -crashPct) crashSig = true;
    }
    if (crashSig && !inCrash && crashCd <= 0) {
      inCrash = true;
      let liq = 0;
      Object.entries(positions).forEach(([tk, sh]) => { liq += sh * day.stocks[tk]; });
      positions = {};
      cash += liq;
      if (safeHaven === "gold") { goldG = cash / day.gold; cash = 0; }
      crashCd = 20;
    }

    // Recovery
    if (inCrash && crashCd <= 0 && i >= 5) {
      const prev5 = data[i - 5].ihsg;
      if ((day.ihsg - prev5) / prev5 * 100 >= 1.5) {
        inCrash = false;
        let rc = cash;
        if (goldG > 0) { rc += goldG * day.gold; goldG = 0; }
        const topR = Object.entries(day.ranks).sort((a, b) => a[1] - b[1]).slice(0, topN).map(x => x[0]);
        const a2 = rc / topR.length;
        topR.forEach(tk => {
          const p = day.stocks[tk];
          const s = Math.floor(a2 / p);
          positions[tk] = s;
          rc -= s * p;
        });
        cash = rc;
        crashCd = 20;
      }
    }
    if (crashCd > 0) crashCd--;

    // Crossover
    if (!inCrash && crossOverOn) {
      for (const [tk, sh] of Object.entries(positions)) {
        if (sh > 0 && day.ranks[tk] >= 7) {
          const sellVal = sh * day.stocks[tk];
          delete positions[tk];
          const cands = Object.entries(day.ranks).sort((a, b) => a[1] - b[1]).slice(0, 4).map(x => x[0]);
          const swapIn = cands.find(t => !positions[t] || positions[t] === 0) || cands[0];
          const bp = day.stocks[swapIn];
          const ns = Math.floor(sellVal / bp);
          positions[swapIn] = (positions[swapIn] || 0) + ns;
          cash += sellVal - ns * bp;
          totalSwaps++;
          break;
        }
      }
    }
  }

  const last = data[data.length - 1];
  let finalSV = 0;
  Object.entries(positions).forEach(([tk, sh]) => { finalSV += sh * last.stocks[tk]; });
  const finalGV = goldG * last.gold;
  const finalVal = cash + finalGV + finalSV + buffer;
  const ret = (finalVal - 100_000_000) / 100_000_000 * 100;
  const ihsgRet = (last.ihsg - initIhsg) / initIhsg * 100;
  const goldRet = (last.gold - initGold) / initGold * 100;
  return { finalVal: Math.round(finalVal), ret, ihsgRet, goldRet, maxDD, totalSwaps };
}

function runSingle(data, ticker, sellPct, buyPct, safeHaven) {
  let cash = 100_000_000;
  let goldG = 0;
  let shares = 0;
  let inStock = false;
  let peak = 0;
  let trough = Infinity;
  let logs = [];

  const initIhsg = data[0].ihsg;
  const initGold = data[0].gold;

  for (let i = 0; i < data.length; i++) {
    const day = data[i];
    const price = day.stocks[ticker] || 1000;

    if (!inStock) {
      if (trough === Infinity || price >= trough * (1 + buyPct / 100)) {
        shares = Math.floor(cash / price);
        if (shares > 0) {
          cash -= shares * price;
          peak = price;
          inStock = true;
        }
      }
    }

    if (inStock) {
      if (price > peak) peak = price;
      if ((price - peak) / peak * 100 <= -sellPct) {
        cash += shares * price;
        if (safeHaven === "gold") { goldG = cash / day.gold; cash = 0; }
        shares = 0;
        inStock = false;
        trough = price;
        peak = 0;
      }
    }
  }

  const last = data[data.length - 1];
  const finalVal = cash + shares * (last.stocks[ticker] || 1000) + goldG * last.gold;
  const ret = (finalVal - 100_000_000) / 100_000_000 * 100;
  const ihsgRet = (last.ihsg - initIhsg) / initIhsg * 100;
  const goldRet = (last.gold - initGold) / initGold * 100;
  return { finalVal: Math.round(finalVal), ret, ihsgRet, goldRet, trades: logs.length };
}

// === RUN ALL ===
console.log("=".repeat(100));
console.log("BACKTEST 2020-01-01 to 2026-06-11  |  Modal: Rp 100.000.000");
console.log("=".repeat(100));

console.log("\n┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐");
console.log("│                                                IHSG: " + dailyData[0].ihsg.toFixed(0).padStart(7) + " → " + dailyData[dailyData.length - 1].ihsg.toFixed(0).padStart(7) + `  (${((dailyData[dailyData.length-1].ihsg/dailyData[0].ihsg-1)*100).toFixed(1)}%)  |  Emas: Rp ${dailyData[dailyData.length-1].gold.toLocaleString("id-ID")} (${((dailyData[dailyData.length-1].gold/dailyData[0].gold-1)*100).toFixed(1)}%) │`);
console.log("└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘");

const strategies = [
  // Algo variants
  { label: "Algo Top1-Cash", fn: () => runAlgo(dailyData, 1, 5, "cash", true, 10) },
  { label: "Algo Top3-Cash", fn: () => runAlgo(dailyData, 3, 5, "cash", true, 10) },
  { label: "Algo Top5-Cash", fn: () => runAlgo(dailyData, 5, 5, "cash", true, 10) },
  { label: "Algo Top1-Gold", fn: () => runAlgo(dailyData, 1, 5, "gold", true, 10) },
  { label: "Algo Top3-Gold", fn: () => runAlgo(dailyData, 3, 5, "gold", true, 10) },
  { label: "Algo Top5-Gold", fn: () => runAlgo(dailyData, 5, 5, "gold", true, 10) },
  { label: "Algo Top3-NoCrash", fn: () => runAlgo(dailyData, 3, 0.1, "cash", true, 10) },
  { label: "Algo Top3-NoSwap", fn: () => runAlgo(dailyData, 3, 5, "cash", false, 10) },
  // Single Stock variants - sell 8%, buy 5%
  ...["BBCA","BBRI","BMRI","TLKM","ASII","ADRO","PTBA","ESSA"].map(t => ({
    label: `Single ${t}-Cash`, fn: () => runSingle(dailyData, t, 8, 5, "cash")
  })),
  ...["BBCA","BBRI","BMRI","TLKM","ASII","ADRO","PTBA","ESSA"].map(t => ({
    label: `Single ${t}-Gold`, fn: () => runSingle(dailyData, t, 8, 5, "gold")
  })),
];

console.log(`\n${"─".repeat(100)}`);
console.log("  #  │ Strategy              │ Final        │ Return    │ IHSG Ret  │ Gold Ret  │ Max DD  │ Swaps");
console.log(`${"─".repeat(100)}`);

const results = strategies.map((s, i) => {
  const r = s.fn();
  const retStr = (r.ret >= 0 ? " " : "") + r.ret.toFixed(1) + "%";
  const ihsgStr = (r.ihsgRet >= 0 ? " " : "") + r.ihsgRet.toFixed(1) + "%";
  const goldStr = (r.goldRet >= 0 ? " " : "") + r.goldRet.toFixed(1) + "%";
  const ddStr = (r.maxDD >= 0 ? " " : "") + (r.maxDD || 0).toFixed(1) + "%";
  const swaps = "totalSwaps" in r ? r.totalSwaps.toString() : ("trades" in r ? r.trades.toString() : "-");
  console.log(`  ${(i+1).toString().padStart(2)} │ ${s.label.padEnd(22)} │ Rp ${r.finalVal.toLocaleString("id-ID").padStart(14)} │ ${retStr.padStart(8)} │ ${ihsgStr.padStart(8)} │ ${goldStr.padStart(8)} │ ${ddStr.padStart(7)} │ ${swaps.padStart(5)}`);
  return { label: s.label, ...r };
});

// Sort by return
const sorted = [...results].sort((a, b) => b.ret - a.ret);
console.log(`\n${"═".repeat(100)}`);
console.log("  RANK │ Strategy              │ Return    │ Final");
console.log(`${"═".repeat(100)}`);
sorted.forEach((r, i) => {
  const med = i === 0 ? " 🥇" : i === 1 ? " 🥈" : i === 2 ? " 🥉" : "   ";
  console.log(`  ${(i+1).toString().padStart(2)}${med} │ ${r.label.padEnd(22)} │ ${(r.ret >= 0 ? " " : "")}${r.ret.toFixed(1)}%${" ".repeat(6)}│ Rp ${r.finalVal.toLocaleString("id-ID")}`);
});
console.log(`\n(Benchmark: IHSG ${((dailyData[dailyData.length-1].ihsg/dailyData[0].ihsg-1)*100).toFixed(1)}%  |  Emas ${((dailyData[dailyData.length-1].gold/dailyData[0].gold-1)*100).toFixed(1)}%)`);
