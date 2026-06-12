import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { runAlgo, runSingle } from "./engine.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const milestonesRaw = JSON.parse(fs.readFileSync(path.join(__dirname, "dashboard/dashboard_v7/data/milestones.json"), "utf-8"));
const factors = JSON.parse(fs.readFileSync(path.join(__dirname, "dashboard/dashboard_v7/data/stock_factors.json"), "utf-8"));

let milestones = milestonesRaw.map(m => ({
  time: new Date(m.date).getTime(),
  ihsg: m.ihsg,
  gold: m.gold,
  stocks: m.stocks
}));

const now = new Date();
const todayStr = now.toISOString().slice(0, 10);
const lastMsTime = milestones[milestones.length - 1].time;

if (now.getTime() - lastMsTime > 3600000) {
  try {
    const livePath = path.join(__dirname, "dashboard/dashboard_v7/data/live_market.json");
    if (fs.existsSync(livePath)) {
      const live = JSON.parse(fs.readFileSync(livePath, "utf-8"));
      const liveDate = new Date(live.last_update || todayStr);
      if (liveDate.getTime() !== lastMsTime) {
        const lastMs = milestones[milestones.length - 1];
        for (const tk of Object.keys(lastMs.stocks)) {
          if (live.stock_prices && live.stock_prices[tk]) lastMs.stocks[tk] = live.stock_prices[tk];
        }
        milestones.push({
          time: liveDate.getTime(),
          ihsg: live.ihsg?.value ?? lastMs.ihsg,
          gold: live.gold?.value ?? lastMs.gold,
          stocks: { ...lastMs.stocks }
        });
        milestones.sort((a, b) => a.time - b.time);
        for (let i = 0; i < milestones.length - 1; i++) {
          if (milestones[i].time === milestones[i + 1].time) {
            milestones.splice(i, 1);
            break;
          }
        }
      }
    }
  } catch (_) {}
}

const lastIdx = milestones.length - 1;
if (milestones[lastIdx].time > now.getTime()) {
  milestones[lastIdx].time = now.getTime();
}

function extrapolatePastEnd(dayTime, day) {
  if (milestones.length < 2) {
    day.ihsg = milestones[0].ihsg;
    day.gold = milestones[0].gold;
    day.stocks = {};
    day.ranks = {};
    return;
  }
  day.stocks = {};
  day.ranks = {};
  const lastMs = milestones[milestones.length - 1];
  const prevMs = milestones[milestones.length - 2];
  const dt = lastMs.time - prevMs.time;
  let t = dt > 0 ? (dayTime - lastMs.time) / dt : 0;
  if (t < 0) t = 0;
  day.ihsg = lastMs.ihsg + (lastMs.ihsg - prevMs.ihsg) * t;
  day.gold = lastMs.gold + (lastMs.gold - prevMs.gold) * t;
  const tickers = Object.keys(lastMs.stocks);
  tickers.forEach(tk => {
    const price = lastMs.stocks[tk] + (lastMs.stocks[tk] - prevMs.stocks[tk]) * t;
    day.stocks[tk] = Math.max(10, Math.round(price));
    const f = factors[tk] || [40, 30, 20, 35];
    day.ranks[tk] = f[0]*0.30 + f[1]*0.25 + f[2]*0.15 + f[3]*0.30;
  });
  const sorted = tickers.sort((a, b) => day.ranks[b] - day.ranks[a]);
  sorted.forEach((tk, i) => day.ranks[tk] = i + 1);
}

function lin(a, b, t) { return a + (b - a) * t; }

const dailyData = [];
const start = new Date("2020-01-01");
const end = now;
for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
  dailyData.push({ date: d.toISOString().slice(0, 10), time: d.getTime() });
}

dailyData.forEach(day => {
  const lastMs = milestones[milestones.length - 1];
  if (day.time > lastMs.time) { extrapolatePastEnd(day.time, day); return; }
  let mPrev = milestones[0], mNext = milestones[1];
  for (let m = 0; m < milestones.length - 1; m++) {
    if (day.time >= milestones[m].time && day.time <= milestones[m + 1].time) {
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
    day.stocks[tk] = Math.max(10, Math.round(lin(mPrev.stocks[tk], mNext.stocks[tk], t)));
    const f = factors[tk] || [40, 30, 20, 35];
    day.ranks[tk] = f[0]*0.30 + f[1]*0.25 + f[2]*0.15 + f[3]*0.30;
  });
  const sorted = tickers.sort((a, b) => day.ranks[b] - day.ranks[a]);
  sorted.forEach((tk, i) => day.ranks[tk] = i + 1);
});

// Filter GOTO before IPO (April 11, 2022)
const GOTO_IPO_TS = new Date("2022-04-11").getTime();
for (const day of dailyData) {
  if (new Date(day.date).getTime() < GOTO_IPO_TS) {
    delete day.stocks["GOTO"];
    delete day.ranks["GOTO"];
  }
}

// === RUN ALL ===
console.log("=".repeat(100));
console.log(`BACKTEST 2020-01-01 to ${todayStr}  |  Modal: Rp 100.000.000`);
console.log("=".repeat(100));

console.log("\n┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐");
console.log("│                                                IHSG: " + dailyData[0].ihsg.toFixed(0).padStart(7) + " → " + dailyData[dailyData.length - 1].ihsg.toFixed(0).padStart(7) + `  (${((dailyData[dailyData.length-1].ihsg/dailyData[0].ihsg-1)*100).toFixed(1)}%)  |  Emas: Rp ${dailyData[dailyData.length-1].gold.toLocaleString("id-ID")} (${((dailyData[dailyData.length-1].gold/dailyData[0].gold-1)*100).toFixed(1)}%) │`);
console.log("└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘");

const strategies = [
  { label: "Algo Top1-Cash", fn: () => runAlgo(dailyData, { topN: 1, crashPct: 5, safeHaven: "cash", crossOverOn: true, reservePct: 10 }) },
  { label: "Algo Top3-Cash", fn: () => runAlgo(dailyData, { topN: 3, crashPct: 5, safeHaven: "cash", crossOverOn: true, reservePct: 10 }) },
  { label: "Algo Top5-Cash", fn: () => runAlgo(dailyData, { topN: 5, crashPct: 5, safeHaven: "cash", crossOverOn: true, reservePct: 10 }) },
  { label: "Algo Top1-Gold", fn: () => runAlgo(dailyData, { topN: 1, crashPct: 5, safeHaven: "gold", crossOverOn: true, reservePct: 10 }) },
  { label: "Algo Top3-Gold", fn: () => runAlgo(dailyData, { topN: 3, crashPct: 5, safeHaven: "gold", crossOverOn: true, reservePct: 10 }) },
  { label: "Algo Top5-Gold", fn: () => runAlgo(dailyData, { topN: 5, crashPct: 5, safeHaven: "gold", crossOverOn: true, reservePct: 10 }) },
  { label: "Algo T3-NoCrash", fn: () => runAlgo(dailyData, { topN: 3, crashPct: 0.1, safeHaven: "cash", crossOverOn: true, reservePct: 10 }) },
  { label: "Algo T3-NoSwap", fn: () => runAlgo(dailyData, { topN: 3, crashPct: 5, safeHaven: "cash", crossOverOn: false, reservePct: 10 }) },
  ...["BBCA","BBRI","BMRI","TLKM","ASII","ADRO","PTBA","ESSA"].map(t => ({
    label: `Single ${t}-Cash`, fn: () => runSingle(dailyData, t, { sellPct: 8, buyPct: 5, safeHaven: "cash" })
  })),
  ...["BBCA","BBRI","BMRI","TLKM","ASII","ADRO","PTBA","ESSA"].map(t => ({
    label: `Single ${t}-Gold`, fn: () => runSingle(dailyData, t, { sellPct: 8, buyPct: 5, safeHaven: "gold" })
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

const sorted = [...results].sort((a, b) => b.ret - a.ret);
console.log(`\n${"═".repeat(100)}`);
console.log("  RANK │ Strategy              │ Return    │ Final");
console.log(`${"═".repeat(100)}`);
sorted.forEach((r, i) => {
  const med = i === 0 ? " 🥇" : i === 1 ? " 🥈" : i === 2 ? " 🥉" : "   ";
  console.log(`  ${(i+1).toString().padStart(2)}${med} │ ${r.label.padEnd(22)} │ ${(r.ret >= 0 ? " " : "")}${r.ret.toFixed(1)}%${" ".repeat(6)}│ Rp ${r.finalVal.toLocaleString("id-ID")}`);
});
console.log(`\n(Benchmark: IHSG ${((dailyData[dailyData.length-1].ihsg/dailyData[0].ihsg-1)*100).toFixed(1)}%  |  Emas ${((dailyData[dailyData.length-1].gold/dailyData[0].gold-1)*100).toFixed(1)}%)`);

// === JOURNAL EXPORT — ALL STRATEGIES ===
const masterCsvPath = path.join(__dirname, "JURNAL_MASTER.csv");
const csvHeader = "Strategy,Tanggal,Aksi,Ticker,Harga,Lembar,Kas setelah,Total Portofolio,Keterangan";
const masterRows = [];

results.forEach(r => {
  const logs = r.logs || [];
  logs.forEach(l => {
    const s = l.action === "BELI-EMAS" || l.action === "JUAL-EMAS" ? l.shares.toFixed(4) : Math.round(l.shares);
    masterRows.push(`"${r.label}",${l.date},${l.action},${l.ticker},${l.price},${s},${l.cashAfter},${l.totalVal},"${l.detail}"`);
  });
});

fs.writeFileSync(masterCsvPath, csvHeader + "\n" + masterRows.join("\n"), "utf-8");
console.log(`\n📄 JURNAL MASTER (${results.length} strategy): ${masterRows.length} transaksi → ${masterCsvPath}`);

sorted.slice(0, 3).forEach(r => {
  const logs = r.logs || [];
  if (logs.length === 0) return;
  const csvPath = path.join(__dirname, `JURNAL_${r.label.replace(/\s+/g, "_")}.csv`);
  const rows = logs.map(l =>
    `${l.date},${l.action},${l.ticker},${l.price},${l.action === "BELI-EMAS" || l.action === "JUAL-EMAS" ? l.shares.toFixed(4) : Math.round(l.shares)},${l.cashAfter},${l.totalVal},"${l.detail}"`
  );
  fs.writeFileSync(csvPath, csvHeader.replace("Strategy,", "") + "\n" + rows.join("\n"), "utf-8");
  console.log(`📄 JURNAL ${r.label}: ${logs.length} transaksi → ${csvPath}`);
});

const juara1 = sorted[0];
const j = juara1.logs || [];
console.log(`\n${"=".repeat(100)}`);
console.log(`  BUKU JURNAL TRANSAKSI ALGORITMA HARIAN — ${juara1.label} (🥇)`);
console.log(`  Periode: ${dailyData[0].date} s/d ${dailyData[dailyData.length-1].date}  |  Total: ${j.length} transaksi`);
console.log(`${"=".repeat(100)}`);
console.log("  Tanggal    │ Aksi          │ Ticker  │   Harga │   Lembar │       Kas │   Total Portofolio │ Keterangan");
console.log(`${"─".repeat(100)}`);
j.forEach(l => {
  const sStr = l.action === "BELI-EMAS" || l.action === "JUAL-EMAS" ? l.shares.toFixed(2) : Math.round(l.shares).toString();
  console.log(`  ${l.date} │ ${l.action.padEnd(13)} │ ${(l.ticker||"").padEnd(7)} │ ${l.price.toString().padStart(7)} │ ${sStr.padStart(8)} │ ${l.cashAfter.toLocaleString("id-ID").padStart(10)} │ ${l.totalVal.toLocaleString("id-ID").padStart(16)} │ ${l.detail}`);
});
