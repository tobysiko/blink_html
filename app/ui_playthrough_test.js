/* Clicks whole games to completion through the real DOM — the same buttons and
 * hexes a person clicks. Catches wiring faults the engine tests cannot see.
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const html = fs.readFileSync(require('./test_setup.js').PLAY_HTML, 'utf8');

/* THIS TEST PRINTED NOTHING FOR MONTHS. Six games finish within a few
 * milliseconds of each other and the last one called process.exit immediately
 * after logging; console.log to a pipe or a file is buffered, and exit throws
 * the buffer away. The exit code was right, so the suite was green and nobody
 * noticed that the one test which clicks the actual DOM had no visible output
 * to read. Write synchronously instead — a test whose report can vanish is
 * only half a test. */
const say = (...a) => fs.writeSync(1, a.map(
  (x) => (typeof x === 'string' ? x : require('util').inspect(x))).join(' ') + '\n');

function run(seed, n, seat, deck, obj, cb, extra) {
  const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
  const w = dom.window, d = w.document;
  const errs = [];
  w.addEventListener('error', (e) => errs.push(e.message));
  w.console.error = (...a) => errs.push(a.join(' '));
  const click = (x) => x.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const q = (s) => d.querySelector(s);
  const qa = (s) => [...d.querySelectorAll(s)];
  const btn = (re, scope) =>
    [...(scope || d).querySelectorAll('button')].find((b) => re.test(b.textContent) && !b.disabled);
  const txt = () => q('#prompt').textContent.replace(/\s+/g, ' ');
  /* a hot polygon whose badge says `lab`; badges follow their own polygon but
   * not as the immediate sibling, so walk and remember the last one */
  const hexBadged = (lab) => {
    let last = null;
    for (const nd of [...q('#map').children]) {
      if (nd.tagName === 'polygon') last = nd;
      if (nd.tagName === 'text' && nd.classList.contains('badge')
          && nd.textContent === lab && last && last.classList.contains('hot')) return last;
    }
    return null;
  };
  const hot = () => q('#map .hot');
  const seenKinds = {};
  const note = (k) => { seenKinds[k] = (seenKinds[k] || 0) + 1; };

  setTimeout(() => {
    require('./test_setup.js').start(w, d, { players: n, seat, seed,
      advanced: Object.assign({}, deck ? { deck } : {}, obj ? { objectives: obj } : {},
                              extra || {}) });

    let steps = 0;
    const tick = () => {
      const t = txt();
      if (/Game over/.test(t) || steps++ > 6000) return done(t);

      /* A duel is asked of whoever is being attacked, so it lands in the middle
       * of another seat's turn and in whatever language the page is in. Match
       * it on the request, not on the sentence. */
      /* Laying out a homeland, before the first card is played. Three hexes in
       * a row and no buttons — matched on the request because the prompt is a
       * sentence in whatever language the page is in. */
      if (w.eval('REQ && REQ.type') === 'homeland') {
        note('homeland-' + w.eval('REQ.stage'));
        const h = hot();
        if (h) click(h);
        else { note('homeland-STUCK'); return done(t); }
        return setTimeout(tick, 0);
      }
      if (w.eval('REQ && REQ.type') === 'duel') {
        note('duel-' + w.eval('REQ.role'));
        const c = qa('#hand button.want')[0] || qa('#hand button').find((b) => !b.disabled);
        if (c) click(c);
        else { note('duel-decline'); click(qa('#prompt button').find((b) => !b.disabled)); }
        /* Reschedule. This said a bare `return` from the day the duel was
         * added, so the loop stopped dead at the first fight: every game
         * stalled, no callback ever fired, node ran out of timers and exited
         * 0 with nothing printed. The suite stayed green because a test that
         * never finishes never fails. */
        return setTimeout(tick, 0);
      }
      // research is a multi-step action now: preview -> steps -> completion
      if (btn(/Begin research/)) { note('research-begin'); click(btn(/Begin research/)); }
      else if (btn(/Continue my turn/)) { note('research-done'); click(btn(/Continue my turn/)); }
      else if (/Play a meld/.test(t)) {
        note('meld');
        // greedily grow the selection while it stays legal
        for (const b of qa('#hand button')) {
          click(b);
          const play = [...d.querySelectorAll('#prompt button')]
            .find((x) => /Play meld/.test(x.textContent));
          if (play && play.disabled) click(b);          // undo: made it illegal
        }
        const play = btn(/Play meld/);
        if (play) click(play);
      } else if (/Your turn/.test(t)) {
        note('turn');
        const cards = qa('#mymeld button');
        if (cards.length) {
          click(cards[0]);
          const s = hexBadged('Settle') || hot();
          if (s) { note('spend'); click(s); }
          else { const c = btn(/^Cash /); if (c) { note('cash'); click(c); } }
        } else if (btn(/^Research$/) && Math.random() < 0.85) {
          note('research-open'); click(btn(/^Research$/));
        } else if (btn(/^Move \(/) && Math.random() < 0.5) {
          note('move-open'); click(btn(/^Move \(/));
        } else if (qa('.vslot button.cf').length && Math.random() < 0.45) {
          note('vcard-open');                       // spend a victory card on A/B/C
          click(qa('.vslot button.cf')[0]);
        } else if (btn(/^Fortify$/) && Math.random() < 0.25) {
          note('fortify-open'); click(btn(/^Fortify$/));
        } else {
          note('end'); click(btn(/^End turn/));
        }
      } else if (/^\s*Move\b|Move —/.test(t)) {
        const h = hot();
        if (h) click(h); else click(btn(/Cancel/) || btn(/Pick another/));
      } else if (/Fortify —/.test(t)) {
        const h = hot();
        if (h && Math.random() < 0.6) click(h); else click(btn(/Cancel/));
      } else if (q('.vpanel')) {
        // the card is face up with its three effects; take a live one or back out
        const live = [...q('.vpanel').querySelectorAll('.vp-opt:not(.off)')];
        if (live.length && Math.random() < 0.7) {
          note('effect-' + live[0].dataset.fx); click(live[0]);
        } else {
          note('vcard-keep'); click(btn(/Keep this card/) || btn(/Play no effect/));
        }
      } else if (/matched the winner/.test(t)) {
        // forced, and made on the cards themselves in the meld area
        note('setaside');
        const r = q('#mymeld button[data-aside]');
        if (r) click(r); else { note('setaside-STUCK'); return done(t); }
      } else if (/spend one extra card|shared pile|Give up|Retire a card/.test(t)) {
        const c = qa('#hand button').find((b) => !b.className.includes('dead'));
        if (c) click(c);
      } else if (/Take a card/.test(t)) {
        const s = q('.slot.hot');
        if (s) click(s); else click(btn(/Cancel/));
      } else if (/Declare —|Declare\b/.test(t)) {
        note('declareA');
        if (qa('.vslot button.cf').length && Math.random() < 0.5) click(qa('.vslot button.cf')[0]);
        else click(btn(/Skip/));
      } else if (/Famine/.test(t)) {
        note('famine');
        const r = q('.vrowbox button.want');       // cashed on the row itself
        if (r) click(r); else click(btn(/Take the loss/));
      } else if (/Raid|Seize|Conquer|Overrun/.test(t)) {
        note('conquest');
        const h = hot();
        if (h) click(h); else click(btn(/Stop/));
      } else if (/Secret objective/.test(t)) {
        note('objective'); click(q('.objpick button'));
      } else if (/Water advantage/.test(t)) {
        note('water');
        const h = hot();
        if (h) click(h); else click(btn(/Skip/));
      } else if (/Found a colony/.test(t)) {
        note('colony-cell');
        const h = hot();
        if (h) click(h); else click(btn(/Stop here/));
      } else if (/Landfall/.test(t)) {
        /* A move that ends on ground that does not exist yet: the cell was
         * already chosen by the move itself, so the only question left is which
         * tile to lay. Matched before the general terrain case because it is
         * reached from a different place and is worth counting separately. */
        note('landfall');
        click(q('.go.terr'));
      } else if (/which terrain/i.test(t)) {
        click(q('.go.terr'));
      }
      setTimeout(tick, 0);
    };

    const done = (t) => {
      const rows = qa('table.final tr').slice(1).map((r) => [...r.children].map((c) => c.textContent.trim()));
      cb({ seed, n, seat, rows, errs, over: /Game over/.test(t), steps,
           tiles: qa('#map polygon.tile').length, kinds: seenKinds, last: t.slice(0, 120) });
    };
    tick();
  }, 200);
}

/* The last two play the homelands setup: every player builds their own corner
 * of the starting map before the first trick, so the setup phase is clicked
 * through the real DOM like everything else. */
const cases = [[11, 3, 0, 'abc', 'secret'], [12, 3, 1, 'abd', 'open'],
               [13, 4, 2, 'abd', 'both'],   [14, 2, 0, 'abc', 'off'],
               [15, 4, 1, 'abd', 'off', { startlayout: 'homelands' }],
               [16, 2, 0, 'abc', 'off', { startlayout: 'homelands' }]];
let done = 0, bad = 0;
const allKinds = {};
/* A watchdog, because the failure this file just had was silence: if a game
 * stalls, nothing reports and the process exits cleanly with an empty log. */
const WATCHDOG = setTimeout(() => {
  say(`FAIL: only ${done} of ${cases.length} games reported — the click loop stalled`);
  process.exit(1);
}, 300000);
for (const [s, n, seat, deck, obj, extra] of cases) run(s, n, seat, deck, obj, (r) => {
  if (!r.over) { bad++; say(`seed ${r.seed}: DID NOT FINISH — ${r.last}`); }
  if (r.errs.length) { bad++; say(`seed ${r.seed}: errors`, r.errs.slice(0, 3)); }
  say(`\nseed ${r.seed}  ${r.n}p  you=seat ${r.seat}  finished=${r.over}  tiles=${r.tiles}`);
  for (const row of r.rows) say('   ', row.join(' | '));
  for (const k in r.kinds) allKinds[k] = (allKinds[k] || 0) + r.kinds[k];
  if (++done === cases.length) {
    clearTimeout(WATCHDOG);
    say('\nUI actions exercised:', allKinds);
    /* The homelands games must actually have placed something, or the two
       extra cases quietly measured nothing. */
    for (const stage of ['forest', 'plains', 'ocean'])
      if (!allKinds['homeland-' + stage]) {
        say('FAIL: no homeland ' + stage + ' was ever placed through the DOM');
        bad++;
      }
    process.exit(bad ? 1 : 0);
  }
}, extra);
