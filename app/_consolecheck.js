/* What does the app itself complain about while a game is played? */
const fs = require('fs');
const { JSDOM } = require('jsdom');
const T = require('/sessions/beautiful-loving-turing/mnt/v0.23/app/test_setup.js');
const html = fs.readFileSync(T.PLAY_HTML, 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
const seen = [];
for (const level of ['error', 'warn']) {
  const orig = w.console[level];
  w.console[level] = (...a) => { seen.push(level + ': ' + a.join(' ').slice(0, 150)); orig(...a); };
}
w.addEventListener('error', (e) => seen.push('uncaught: ' + e.message));
setTimeout(() => {
  T.start(w, d, { players: 3, seat: 0, seed: 5, lang: process.env.LANG2 || 'en' });
  let steps = 0;
  const click = (x) => x && x.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const qa = (s) => [...d.querySelectorAll(s)];
  const tick = () => {
    if (steps++ > 700 || /Game over/.test(d.querySelector('#prompt').textContent)) {
      const uniq = [...new Set(seen)];
      console.log(uniq.length ? uniq.join('\n') : 'the app reported nothing');
      return process.exit(0);
    }
    const type = w.eval('REQ && REQ.type');
    if (type === 'meld') {
      const h = qa('#hand button')[0];
      if (h) { click(h); const p = qa('#prompt button').find((b) => /Play meld|Kombination/.test(b.textContent)); if (p && !p.disabled) click(p); }
    } else if (type === 'turn') {
      click(qa('#prompt button').find((b) => /End turn|Zug beenden/.test(b.textContent)));
    } else if (type) {
      const c = qa('#hand button.want')[0] || d.querySelector('#mymeld button[data-aside]')
        || qa('.vrowbox button.want')[0] || qa('#hand button')[0];
      if (c) click(c); else click(qa('#prompt button').find((b) => !b.disabled));
    }
    setTimeout(tick, 0);
  };
  tick();
}, 400);
