/* The page must (a) hide the notice and work when scripts run, and
   (b) show the notice and hide the game when they do not. */
const fs = require('fs'); const { JSDOM } = require('jsdom');
const html = fs.readFileSync('/sessions/beautiful-loving-turing/mnt/v0.22/Blink-play-v0.23.html','utf8');
const check = (runScripts, label, cb) => {
  const dom = new JSDOM(html, runScripts ? { runScripts:'dangerously', pretendToBeVisual:true } : {});
  const w = dom.window, d = w.document;
  setTimeout(() => {
    const vis = s => { const n=d.querySelector(s); if(!n) return 'MISSING';
      const st=w.getComputedStyle(n); return st.display!=='none'; };
    cb({ label,
      htmlClass: d.documentElement.className.trim() || '(none)',
      notice: vis('#nojs'), setup: vis('#setup'),
      seatRows: d.querySelectorAll('#seats .seatrow').length });
  }, runScripts ? 250 : 50);
};
let n=0; const out=[];
check(false, 'scripts BLOCKED (iOS Files preview)', r=>{out.push(r); if(++n===2) done();});
check(true,  'scripts running (a real browser)',    r=>{out.push(r); if(++n===2) done();});
function done(){
  out.sort((a,b)=>a.label.localeCompare(b.label));
  for (const r of out) console.log(
    `${r.label.padEnd(34)} html="${r.htmlClass.padEnd(3)}"  notice=${String(r.notice).padEnd(5)}`+
    `  setup=${String(r.setup).padEnd(5)}  seat rows=${r.seatRows}`);
  process.exit(0);
}
