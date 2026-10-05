/* THE GUIDE BANNER SAYS WHAT TO DO, AND ONLY WHEN IT IS TRUE.
 *
 * Toby asked for "clearer cues for what to do next as large banners — drafting
 * phase, now play your first meld, now use your meld on the map — very obvious
 * for beginners, and switchable off for experienced players". This plays whole
 * games through the page and checks, at every question the engine asks the
 * person:
 *
 *   - the banner is up and says something specific to that question (never
 *     the catch-all line, never a raw i18n key);
 *   - its step marker agrees with the phase (meld / reveal / map);
 *   - it can be hidden from the banner and brought back from the map toolbar,
 *     and the setup select follows both.
 *
 * And one thing a playthrough cannot reach, because jsdom has no layout and
 * therefore no animation: the engine asks for your map turn while the table is
 * still showing a rival's. The banner must follow the table there and name the
 * rival, or it teaches a beginner the wrong turn order.
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const html = fs.readFileSync(require('./test_setup.js').PLAY_HTML, 'utf8');
const fail = [];
const seenTypes = {};

const STEP = { meld: '1', effectA: '2', setaside: '3', turn: '3', duel: '3', bonus: '3',
               retire: '3', buy: '3', trade: '3', researchTo: '3', colony: '3' };

function game(seed, n, handsetup) {
  return new Promise((done) => {
    const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
    const w = dom.window, d = w.document;
    w.addEventListener('error', (e) => fail.push('error: ' + e.message));
    const q = (s) => d.querySelector(s);
    const click = (x) => x.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
    const other = w.eval('t("guide.other.h")');

    setTimeout(() => {
      require('./test_setup.js').start(w, d, { players: n, seat: 0, seed, showObjective: 'ask',
        advanced: handsetup ? { handsetup } : {} });
      let steps = 0, toggled = false;
      const tick = () => {
        if (w.eval('gameOver()')) {
          const head = (q('#guide .ghead') || {}).textContent || '';
          if (!/over|Spielende/i.test(head)) fail.push(`seed ${seed}: game over but the banner says "${head}"`);
          return done();
        }
        const type = w.eval('REQ && mine() ? REQ.type : null');
        if (type) {
          seenTypes[type] = (seenTypes[type] || 0) + 1;
          const box = q('#guide');
          const head = (q('#guide .ghead') || {}).textContent || '';
          const on = (q('#guide .gsteps li.on') || {}).textContent || '';
          if (!box || box.hidden) fail.push(`${type}: no banner`);
          else if (!head.trim()) fail.push(`${type}: an empty banner`);
          else if (/\bguide\.\w/.test(box.textContent)) fail.push(`${type}: a raw key in the banner: ${head}`);
          else if (head === other) fail.push(`${type}: only the catch-all line — this request has no guidance of its own`);
          if (STEP[type] && !on.startsWith(STEP[type]))
            fail.push(`${type}: step marker says "${on}", expected step ${STEP[type]}`);
          if (['draft', 'mulligan', 'homeland', 'objective'].includes(type) && q('#guide .gsteps'))
            fail.push(`${type}: a setup question shows the round's steps`);

          /* once per game: hide from the banner, restore from the toolbar */
          if (type === 'turn' && !toggled) {
            toggled = true;
            click(q('#guide .gx'));
            if (!q('#guide').hidden) fail.push('the Hide button left the banner up');
            if (q('#guideon').hidden) fail.push('with the banner hidden there is no way to bring it back');
            if (q('#guide-pref').value !== 'off') fail.push('hiding the banner did not reach the setup select');
            w.eval('render()');
            if (!q('#guide').hidden) fail.push('the banner came back by itself on the next render');
            click(q('#guideon'));
            if (q('#guide').hidden) fail.push('the Guide button did not bring the banner back');
            if (!q('#guideon').hidden) fail.push('the Guide button stayed up next to the banner');
          }
          w.eval(`(() => {
            if (REQ.type === 'turn') {
              const o = REQ.opts;
              if (o.cards.length) return answer({ kind: 'cash', card: o.cards[0].card });
              return answer({ kind: 'end' });
            }
            if (REQ.type === 'draft') return answer(REQ.pool.slice(0, REQ.pass));
            if (REQ.type === 'trade') return answer(null);
            if (REQ.options && REQ.options.length) return answer(REQ.options[REQ.options.length - 1]);
            answer(null);
          })()`);
        }
        if (++steps > 4000) { fail.push(`seed ${seed}: did not finish`); return done(); }
        setTimeout(tick, 0);
      };
      tick();
    }, 0);
  });
}

/* The table, not the engine. */
function followsTable() {
  return new Promise((done) => {
    const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
    const w = dom.window, d = w.document;
    setTimeout(() => {
      require('./test_setup.js').start(w, d, { players: 3, seat: 0, seed: 11 });
      let n = 0;
      const tick = () => {
        const type = w.eval('REQ && mine() ? REQ.type : null');
        if (type === 'turn') {
          const rival = w.eval('uiSeq().find((i) => i !== ME)');
          /* Pretend the animation is still on the rival's turn. */
          w.eval(`fxEnabled = () => true; TRICK.winner = G.winner;
                  TRICK.order = G.trickOrder; TRICK.acting = ${rival}; renderGuide();`);
          const head = d.querySelector('#guide .ghead').textContent;
          const name = w.eval(`seatName(${rival})`);
          if (!head.includes(name))
            fail.push(`your turn was announced while ${name} was still on the map: "${head}"`);
          w.eval('TRICK.acting = ME; renderGuide();');
          const mine = d.querySelector('#guide .ghead').textContent;
          if (mine.includes(name) || mine === head)
            fail.push(`the banner did not move on when the table reached your seat: "${mine}"`);
          return done();
        }
        if (type) w.eval(`(() => {
          if (REQ.options && REQ.options.length) return answer(REQ.options[REQ.options.length - 1]);
          answer(null); })()`);
        if (++n > 500) { fail.push('never reached a map turn'); return done(); }
        setTimeout(tick, 0);
      };
      tick();
    }, 0);
  });
}

(async () => {
  await game(3, 3, 'draft');
  await game(8, 4);
  await game(21, 2);
  await followsTable();
  for (const need of ['draft', 'meld', 'turn'])
    if (!seenTypes[need]) fail.push(`no game ever asked for "${need}" — the test lost its footing`);
  if (fail.length) { console.error([...new Set(fail)].slice(0, 30).join('\n')); process.exit(1); }
  console.log('guide banner: specific and on the right step for '
    + Object.entries(seenTypes).map(([k, v]) => `${k} ×${v}`).join(', ')
    + '; hides and returns; follows the table, not the engine');
})();
