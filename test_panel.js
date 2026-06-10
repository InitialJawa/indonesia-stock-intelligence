const vm = require('vm');
const fs = require('fs');
const js = fs.readFileSync('C:\\Users\\BEDILG~1\\AppData\\Local\\Temp\\opencode\\test_dynamic.js', 'utf8');

let panelHTML = '';
let ptkText = '', ptkColor = '', pnameText = '';
let overlayActive = false, panelActive = false;

// Track fetch calls
let fetchCalls = [];

const ctx = {
  document: {
    getElementById(id) {
      const o = {
        innerHTML: '', className: '',
        classList: { add() { if (id==='overlay') overlayActive=true; if (id==='panel') panelActive=true; }, remove() {} },
        style: { color: '' },
        textContent: '',
        getAttribute() { return ''; }
      };
      if (id==='ptk') return { ...o, get textContent() { return ptkText; }, set textContent(v) { ptkText=v; }, style: { set color(c) { ptkColor=c; }, get color() { return ptkColor; } } };
      if (id==='pname') return { ...o, get textContent() { return pnameText; }, set textContent(v) { pnameText=v; } };
      if (id==='pbody') return { ...o, get innerHTML() { return panelHTML; }, set innerHTML(v) { panelHTML=v; } };
      return { ...o, getContext() { return { canvas: { width: 100, height: 100 } }; } };
    },
    querySelectorAll() { return []; },
    addEventListener() {}
  },
  window: {},
  console: { log(){}, error(){}, warn(msg) { /* ignore */ } },
  Chart: function() { return { destroy(){}, update(){}, data: { datasets: [] } }; },
  fetch(url) {
    fetchCalls.push(url);
    return Promise.resolve({
      ok: true,
      json() {
        if (url.includes('leaders')) return Promise.resolve([]);
        if (url.includes('summary')) return Promise.resolve({});
        if (url.includes('streaks')) return Promise.resolve([]);
        if (url.includes('exit')) return Promise.resolve([]);
        if (url.includes('turnaround')) return Promise.resolve([]);
        if (url.includes('profiles')) return Promise.resolve({ADRO: {name:'Adaro', sector:'Energy', industry:'Coal', summary:'Test'}});
        if (url.includes('fundamentals')) return Promise.resolve({});
        if (url.includes('cw_b')) return Promise.resolve({quality:0.25,growth:0.30,value:0.10,momentum:0.35});
        if (url.includes('cw_f')) return Promise.resolve({quality:0.25,growth:0.10,value:0.30,momentum:0.35});
        if (url.includes('warehouse')) return Promise.resolve({});
        if (url.includes('ic')) return Promise.resolve({quality:{ic:0.02,role:'selector'},growth:{ic:0.01,role:'selector'},value:{ic:-0.01,role:'diversifier'},momentum:{ic:0.03,role:'selector'}});
        if (url.includes('bt')) return Promise.resolve({full:{config_b:{cagr:12,total_return:80,max_dd:-25,sharpe:0.8},config_f:{cagr:15,total_return:100,max_dd:-20,sharpe:1.0},ihsg:{cagr:5,total_return:40,max_dd:-30,sharpe:0.3}}});
        if (url.includes('fcolors')) return Promise.resolve({quality:'#00d68f',growth:'#3b82f6',value:'#f59e0b',momentum:'#ef4444'});
        if (url.includes('fnames')) return Promise.resolve({quality:'Quality',growth:'Growth',value:'Value',momentum:'Momentum'});
        return Promise.resolve({});
      }
    });
  }
};
ctx.window = ctx;

try {
  vm.runInNewContext(js, ctx, { timeout: 10000 });
  // After loadAllData completes, test openPanel
  setTimeout(function() {
    console.log('Fetch calls:', fetchCalls.length, '(expected 14)');
    ctx.openPanel('ADRO');
    console.log('ptk:', ptkText);
    console.log('pname:', pnameText);
    console.log('panelActive:', panelActive, 'overlayActive:', overlayActive);
    console.log('bodyLen:', panelHTML.length);
    const checks = ['TENTANG PERUSAHAAN','Adaro','FUNDAMENTAL','INTERPRETASI','STATUS DASHBOARD','HARGA','KEKUATAN RELATIF','POSISI TERHADAP MA','KESELARASAN','Score Breakdown'];
    checks.forEach(c => console.log('  Has ' + c + ':', panelHTML.indexOf(c) > -1));
  }, 100);
} catch(e) {
  console.log('ERROR:', e.message);
  console.log(e.stack.split('\n').slice(0,3).join('\n'));
}
