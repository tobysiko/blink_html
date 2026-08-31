const fs = require('fs'); const { JSDOM } = require('jsdom');
const HTML = require('/sessions/beautiful-loving-turing/mnt/v0.23/app/test_setup.js').PLAY_HTML;
const dom = new JSDOM(fs.readFileSync(HTML, 'utf8'), { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
setTimeout(() => { d.querySelector('#start').click(); setTimeout(() => {
  const rows = [...d.querySelectorAll('.tier-row')];
  console.log('rows', rows.length);
  for (const cell of d.querySelectorAll('.tier-row > *')) {
    const s = w.getComputedStyle(cell);
    console.log(cell.className.padEnd(12), 'op=' + s.opacity, 'pos=' + s.position, 'disp=' + s.display, JSON.stringify(cell.textContent.replace(/\s+/g,' ').trim().slice(0,14)));
  }
  process.exit(0);
}, 900); }, 400);
