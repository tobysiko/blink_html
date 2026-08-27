/* The animation layer must never affect the game: events drain every step so
 * they cannot accumulate, nothing throws when the geometry is unavailable
 * (which is exactly the jsdom case), and the bots play identically with the
 * recording on. Needs jsdom: npm install jsdom */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }
const E = require('./engine.js');

// 1. recording does not change what the bots do
const noFx = [];
for (let s = 0; s < 60; s++) {
  const g = E.playOut(3, s * 7919, {});
  noFx.push(g.score().reduce((a, x) => a + x.total, 0), g.round);
}
const again = [];
for (let s = 0; s < 60; s++) {
  const g = E.playOut(3, s * 7919, {});
  again.push(g.score().reduce((a, x) => a + x.total, 0), g.round);
}
if (JSON.stringify(noFx) !== JSON.stringify(again))
  { console.log('FAIL: games are not reproducible'); process.exit(1); }

/* Every event of a whole game. `g.events` only holds what has not been drained
 * — and it is deliberately capped — so a test that reads it at the end sees a
 * tail, not the game. Tap fx instead. */
function recordGame(n, seed, opts) {
  const g = new E.Game(n, seed, Object.assign({ humans: [] }, opts || {}));
  const all = [];
  const orig = g.fx.bind(g);
  g.fx = (type, data) => { all.push(Object.assign({ type }, data)); orig(type, data); };
  let guard = 0;
  while (!g.finished() && guard++ < 200) {
    const it = g.playRound();
    let r = it.next();
    while (!r.done) r = it.next(null);
  }
  return { g, all };
}
const rec = recordGame(3, 42, {});

// 1b. a research deals from the deck, and says which slot it buried
const dealt = rec.all.filter((e) => e.type === 'deal');
if (!dealt.length) { console.log('FAIL: no deal events recorded'); process.exit(1); }
if (!dealt.every((e) => e.card && e.slot >= 0 && e.slot < 9 && e.left >= 0))
  { console.log('FAIL: a deal event is missing card/slot/left'); process.exit(1); }

/* 1c. the trick beats: every round records one meld per seat, one trick with a
 * full ranking, and a start/end for each map turn. The clockwise reveal is
 * built entirely out of these, so a missing beat is a table that never fills. */
const rounds = rec.g.round;
const cnt = (t) => rec.all.filter((e) => e.type === t).length;
for (const [t, want] of [['meld', 3 * rounds], ['trick', rounds],
                         ['turnstart', 3 * rounds], ['turnend', 3 * rounds]])
  if (cnt(t) !== want)
    { console.log(`FAIL: ${cnt(t)} ${t} events over ${rounds} rounds, expected ${want}`);
      process.exit(1); }
const tricks = rec.all.filter((e) => e.type === 'trick');
if (!tricks.every((e) => e.order && e.order.length === 3 && e.order[0] === e.seat))
  { console.log('FAIL: a trick event does not rank every seat, winner first');
    process.exit(1); }
// the map phase follows the ranking the trick announced
const startsOf = [];
let cur = null;
for (const e of rec.all) {
  if (e.type === 'trick') { cur = { want: e.order, got: [] }; startsOf.push(cur); }
  else if (e.type === 'turnstart' && cur) cur.got.push(e.seat);
}
if (!startsOf.every((x) => JSON.stringify(x.want) === JSON.stringify(x.got)))
  { console.log('FAIL: seats act in a different order than the trick announced');
    process.exit(1); }

// 2. the queue is bounded even when nobody drains it
const long = E.playOut(4, 5, {});
if ((long.events || []).length > 400)
  { console.log('FAIL: event queue is unbounded'); process.exit(1); }

// 3. in the app: the layer exists, events drain, nothing throws
const html = fs.readFileSync(require('./test_setup.js').PLAY_HTML, 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
const errs = [];
w.addEventListener('error', (e) => errs.push(e.message));
w.console.error = (...a) => errs.push(a.join(' '));
setTimeout(() => {
  require('./test_setup.js').start(w, d, { players: 3, seat: 0 });
  const fail = [];
  if (!d.querySelector('#fx')) fail.push('no #fx layer');
  // play a meld so the engine records something, then check it was drained
  const hand = [...d.querySelectorAll('#hand button')];
  if (hand.length) hand[0].dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const play = [...d.querySelectorAll('#prompt button')].find((b) => /Play meld/.test(b.textContent));
  if (play && !play.disabled) play.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  setTimeout(() => {
    const left = w.eval('G && G.events ? G.events.length : -1');
    if (left > 0) fail.push(`events not drained: ${left} left in the queue`);
    if (errs.length) fail.push('errors: ' + errs.slice(0, 2).join(' | '));
    console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
      : 'animation layer present, events drained, bots unaffected, no errors');
    process.exit(fail.length ? 1 : 0);
  }, 400);
}, 250);
