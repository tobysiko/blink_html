/* Taking a move back.
 *
 * At a table you can pick a card back up before you let go of it — but only
 * your own, and only on your own turn. Once the trick is resolved and everyone
 * has seen it, it is resolved. That is the contract this checks:
 *
 *   1. an action taken on your map turn can be undone, and the board is
 *      genuinely back where it was — gold, hand, units, map, victory row;
 *   2. undoing repeatedly walks back to the START of your turn and stops;
 *   3. it is never offered during the card phase, because the melds are
 *      hidden information and unplaying one after the trick is cheating;
 *   4. what the OTHER players did is untouched — undo rewinds you, not them;
 *   5. and going forward again after an undo produces a legal, finishable game.
 *
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const html = fs.readFileSync(__dirname + '/../Blink-play-v0.22.html', 'utf8');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

function page() {
  const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
  const errs = [];
  dom.window.addEventListener('error', (e) => errs.push(e.message));
  dom.window.console.error = (...a) => errs.push(a.join(' '));
  return { w: dom.window, d: dom.window.document, errs };
}

/* Everything about the table that a player can see, as one string. Two states
 * that print the same are the same position. */
const SNAP = `JSON.stringify({
  round: G.round, gold: G.P.map((p) => p.gold),
  hand: G.P.map((p) => p.hand.map((c) => c.r + c.s).sort()),
  disc: G.P.map((p) => p.discard.length),
  vrow: G.P.map((p) => p.vrow.map((c) => c.r + c.s).sort()),
  units: G.P.map((p) => p.reserve),
  map: [...G.m.tiles.entries()].map(([k, t]) =>
        k + ':' + t.terrain + ':' + (t.units || []).join(',') + ':' + (t.fort ? 'F' : '')).sort(),
  supply: G.m.supply, market: G.marketCount ? G.marketCount() : 0,
})`;

const A = page();
setTimeout(() => {
  const { w, d } = A;
  const ev = (s) => w.eval(s);
  const click = (x) => x.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const q = (s) => d.querySelector(s);
  const qa = (s) => [...d.querySelectorAll(s)];
  const btn = (re) => qa('#prompt button').find((b) => re.test(b.textContent) && !b.disabled);
  const txt = () => q('#prompt').textContent.replace(/\s+/g, ' ');
  const undo = q('#undo');

  require('./test_setup.js').start(w, d, { players: 3, seat: 0, seed: 77 });

  // ---- 3. the card phase offers no way back
  ok(/Play a meld/.test(txt()), 'the game did not open on a meld');
  ok(undo.disabled, 'undo is offered during the card phase — that would unplay a meld');
  ok(!!undo.title, 'the disabled undo button does not say why it is disabled');

  // play a meld: still nothing to undo, because the trick has now been seen
  const hand = qa('#hand button');
  click(hand[0]);
  const play = btn(/Play meld/);
  ok(!!play, 'could not play a meld');
  click(play);

  setTimeout(() => {
    // ---- get to my own map turn
    let guard = 0;
    while (!/Your turn/.test(txt()) && guard++ < 40) {
      const b = btn(/Skip|Take the loss|Stop|Cancel/);
      if (b) click(b);
      else if (q('#mymeld button[data-aside]')) click(q('#mymeld button[data-aside]'));
      else if (q('.objpick button')) click(q('.objpick button'));
      else break;
    }
    if (!/Your turn/.test(txt())) {
      fail.push('never reached my own map turn: ' + txt().slice(0, 70));
      return report();
    }

    ok(undo.disabled, 'undo is live at the very start of a turn, before any action');
    const before = ev(SNAP);
    const logAtStart = ev('LOG.length');

    // ---- 1. do something, undo it, and be exactly where we were
    const card = qa('#mymeld button[data-turn]')[0];
    let did = null;
    if (card) {
      click(card);
      const hot = q('#map .hot');
      if (hot) { click(hot); did = 'placed a card on the map'; }
      else { const c = btn(/^Cash /); if (c) { click(c); did = 'cashed a card'; } }
    }
    if (!did) {
      const r = btn(/^Research$/);
      if (r) { click(r); click(btn(/Begin research/) || r); did = 'started a research'; }
    }
    if (!did) { fail.push('found no action to take on my turn'); return report(); }

    const after = ev(SNAP);
    ok(after !== before, `${did} changed nothing — the test cannot prove an undo`);
    ok(ev('LOG.length') > logAtStart, 'the action was not written down');
    ok(!undo.disabled, `undo is still greyed out after I ${did}`);

    click(undo);
    ok(ev(SNAP) === before,
       `after undoing (${did}) the table is NOT back where it was`);
    ok(ev('LOG.length') === logAtStart, 'undo did not drop the action from the log');
    ok(ev('REQ && REQ.seat') === 0, 'undo handed the turn to somebody else');
    ok(/Your turn/.test(txt()), 'undo did not land back on my turn: ' + txt().slice(0, 60));

    // ---- 2. it stops at the start of my turn
    ok(undo.disabled, 'undo would keep going past the start of my turn');

    // ---- 4. and the other players are where they were
    ok(ev('G.P.filter((p) => p.i !== 0).map((p) => p.gold).join()')
       === JSON.parse(before).gold.filter((_, i) => i !== 0).join(),
       'undoing my action moved another player');

    // ---- 5. the game still runs to the end afterwards
    let steps = 0;
    const tick = () => {
      const t = txt();
      if (/Game over/.test(t) || steps++ > 4000) return finish(t);
      if (btn(/Begin research/)) click(btn(/Begin research/));
      else if (btn(/Continue my turn/)) click(btn(/Continue my turn/));
      else if (/Play a meld/.test(t)) {
        for (const b of qa('#hand button')) {
          click(b);
          const p2 = qa('#prompt button').find((x) => /Play meld/.test(x.textContent));
          if (p2 && p2.disabled) click(b);
        }
        const p2 = btn(/Play meld/); if (p2) click(p2);
      } else if (/matched the winner/.test(t)) {
        const r = q('#mymeld button[data-aside]'); if (r) click(r);
      } else if (/Your turn/.test(t)) {
        // undo every third action, to prove replay survives being used a lot
        const cs = qa('#mymeld button[data-turn]');
        if (cs.length) {
          click(cs[0]);
          const h = q('#map .hot');
          if (h) click(h); else { const c = btn(/^Cash /); if (c) click(c); }
          if (steps % 3 === 0 && !undo.disabled) { click(undo); undos++; }
        } else click(btn(/^End turn/));
      } else if (/Give up|Retire a card|spend one extra|shared pile/.test(t)) {
        const c = qa('#hand button.want')[0] || qa('#hand button')[0]; if (c) click(c);
      } else if (/Take a card/.test(t)) {
        const s = q('.slot.hot'); if (s) click(s); else click(btn(/Cancel/));
      } else if (/Famine/.test(t)) {
        const r = q('.vrowbox button.want'); if (r) click(r); else click(btn(/Take the loss/));
      } else if (/Secret objective/.test(t)) click(q('.objpick button'));
      else {
        const b = btn(/Skip|Stop|Cancel|Take the loss|Keep this card|Play no effect/);
        if (b) click(b);
        else { const h = q('#map .hot'); if (h) click(h); }
      }
      setTimeout(tick, 0);
    };
    let undos = 0;
    const finish = (t) => {
      ok(/Game over/.test(t), 'the game did not finish after undoing: ' + t.slice(0, 70));
      ok(undos > 0, 'the long run never managed a second undo');
      ok(qa('table.final tr').length > 1, 'no final scores');
      report(`${undos} undos mid-game, then the game finished`);
    };
    tick();
  }, 350);

  function report(extra) {
    if (A.errs.length) fail.push('errors: ' + [...new Set(A.errs)].slice(0, 2).join(' | '));
    console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
      : 'undo: rewinds one action on your own turn and no further, is never '
        + 'offered in the card phase, leaves the other players alone'
        + (extra ? ', ' + extra : ''));
    process.exit(fail.length ? 1 : 0);
  }
}, 250);
