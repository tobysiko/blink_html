const fs = require('fs');
const { JSDOM } = require('jsdom');
const T = require('/sessions/beautiful-loving-turing/mnt/v0.23/app/test_setup.js');
const html = fs.readFileSync(T.PLAY_HTML, 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
setTimeout(() => {
  T.start(w, d, { players: 3, seat: 0, seed: 5, lang: process.env.LANG2 || 'en' });
  const head = d.querySelector('.tier-row.head');
  console.log('head cells:', [...head.children].map(c => `${c.className}="${c.textContent.trim()}"`).join('  '));
  const row = d.querySelectorAll('.tier-row')[1];
  console.log('body cells:', [...row.children].map(c => c.className).join(' | '));
  console.log('colCap en/de:',
    JSON.stringify(w.STRINGS ? '' : ''), 
    JSON.stringify(require('./i18n.js').STRINGS.en['board.colCap']),
    JSON.stringify(require('./i18n.js').STRINGS.de['board.colCap']));
  process.exit(0);
}, 400);
