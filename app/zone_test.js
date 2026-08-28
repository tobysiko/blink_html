/* "Don't make me read the prompt."
 *
 * Every step that wants a click must light exactly one area, that area must
 * hold something clickable, and the cards in it that are legal must be the
 * ones the engine would accept. This drives whole games and checks all three
 * on every single request — a step that lights nothing, or lights an area with
 * nothing live in it, is a dead end for a player who is going by the
 * highlight, which is what we are asking them to do.
 *
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const html = fs.readFileSync(require('./test_setup.js').PLAY_HTML, 'utf8');

function run(seed, n, seat, retire, deck, obj, cb) {
  const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
  const w = dom.window, d = w.document;
  const fail = [], seen = {};
  w.addEventListener('error', (e) => fail.push('error: ' + e.message));
  w.console.error = (...a) => fail.push('error: ' + a.join(' '));
  const click = (x) => x.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const q = (s) => d.querySelector(s);
  const qa = (s) => [...d.querySelectorAll(s)];
  const btn = (re) => qa('#prompt button').find((b) => re.test(b.textContent) && !b.disabled);
  const txt = () => q('#prompt').textContent.replace(/\s+/g, ' ');
  const note = (k) => { seen[k] = (seen[k] || 0) + 1; };

  setTimeout(() => {
    require('./test_setup.js').start(w, d, { players: n, seat, seed,
      advanced: Object.assign({ 'retire-rule': retire },
        deck ? { deck } : {}, obj ? { objectives: obj } : {}) });

    let steps = 0;
    const check = () => {
      const type = w.eval('REQ && REQ.seat === ME ? REQ.type : null');
      if (!type) return;
      const zone = w.eval('needZone()');
      if (!zone) return;                       // `turn` is free-form by design
      note(type);
      const box = q(zone);
      if (!box) { fail.push(`${type}: zone ${zone} does not exist`); return; }
      if (!box.classList.contains('needs'))
        fail.push(`${type}: ${zone} is where the click goes but is not lit`);
      // and it must actually hold something to click
      const live = zone === '#market'
        ? qa('#market .slot.hot')
        : zone === '#mapbox'
        ? qa('#map .hot')
        : [...box.querySelectorAll('button')].filter((b) => !b.disabled
            && !b.className.includes('dead'));
      if (!live.length) fail.push(`${type}: ${zone} is lit but has nothing to click`);
      // exactly one area is ever lit
      const lit = qa('.needs').length;
      if (lit !== 1) fail.push(`${type}: ${lit} areas lit at once`);
      // a famine must offer the row cards themselves, lit
      if (type === 'feed') {
        const want = qa('.vrowbox button.want').length;
        const opts = w.eval('REQ.options.length');
        if (want !== opts) fail.push(`feed: ${want} row cards lit, engine allows ${opts}`);
      }
      // the lit cards are the ones the engine would take, no more and no fewer
      /* A duel must SHOW what is being answered: the contested tile marked on
       * the map, and the attacking card next to the question. Both were
       * missing in the first build of it, and "which Forest?" was the first
       * thing anybody asked. */
      if (type === 'duel') {
        const lit = qa('#map .fight');
        if (lit.length !== 1)
          fail.push(`duel: ${lit.length} tiles marked as contested, expected 1`);
        if (lit[0] && lit[0].dataset.key !== w.eval('REQ.cell'))
          fail.push('duel: the marked tile is not the one being fought over');
        if (w.eval('REQ.against') && !q('.duelsum'))
          fail.push('duel: the attacking card is not shown beside the question');
      }
      if (['retire', 'discard', 'bonus', 'duel'].includes(type)) {
        const want = qa('#hand button.want').length;
        const opts = w.eval('REQ.options.length');
        if (want !== opts)
          fail.push(`${type}: ${want} cards lit, engine allows ${opts}`);
        if (type === 'retire' && w.eval('G.RETIRE_RULE') === 'lowest') {
          const low = w.eval('Math.min(...G.P[ME].hand.map((c) => c.r))');
          const lowN = w.eval(`G.P[ME].hand.filter((c) => c.r === ${low}).length`);
          if (want !== lowN)
            fail.push(`retire: ${want} lit, but ${lowN} cards of the lowest rank ${low}`);
        }
      }
      // the forced set-aside must not be escapable
      if (type === 'setaside') {
        const outs = qa('#prompt button').filter((b) => !b.disabled);
        if (outs.length) fail.push(`setaside: prompt offers a way out (${outs[0].textContent.trim()})`);
        if (!qa('#mymeld button[data-aside]').length)
          fail.push('setaside: no card to click in the meld area');
      }
    };

    const tick = () => {
      const t = txt();
      if (/Game over/.test(t) || steps++ > 6000) return finish(t);
      check();
      if (btn(/Begin research/)) click(btn(/Begin research/));
      else if (btn(/Continue my turn/)) click(btn(/Continue my turn/));
      else if (/Play a meld/.test(t)) {
        for (const b of qa('#hand button')) {
          click(b);
          const play = qa('#prompt button').find((x) => /Play meld/.test(x.textContent));
          if (play && play.disabled) click(b);
        }
        const play = btn(/Play meld/);
        if (play) click(play);
      } else if (/matched the winner/.test(t)) {
        const r = q('#mymeld button[data-aside]');
        if (r) click(r);
      } else if (/Your turn/.test(t)) {
        const cards = qa('#mymeld button[data-turn]');
        if (cards.length) {
          click(cards[0]);
          const h = q('#map .hot');
          if (h) click(h);
          else { const c = btn(/^Cash /); if (c) click(c); }
        } else if (btn(/^Research$/)) click(btn(/^Research$/));
        else if (qa('.vslot button.cf').length && Math.random() < 0.5) {
          // open a victory card, and take B when it is live — the colony step
          // is a map click like any other and must light the map
          click(qa('.vslot button.cf')[0]);
          const b = qa('.vpanel .vp-opt:not(.off)').find((x) => x.dataset.fx === 'B');
          if (b) click(b); else click(btn(/Keep this card/) || btn(/Play no effect/));
        } else click(btn(/^End turn/));
      } else if (w.eval('REQ && REQ.type') === 'assault') {
        /* An assault asks for a SECOND meld card, off the table rather
         * than out of hand — the same list the set-aside uses. */
        const c = q('#mymeld button[data-aside]');
        if (c) click(c);
        else click(qa('#prompt button').find((b) => !b.disabled));
      } else if (w.eval('REQ && REQ.type') === 'duel') {
        /* A duel interrupts whoever's turn it is, so it cannot be matched on
         * prompt text like the branches around it — this file runs in whatever
         * language the page is in. Ask the page what it wants instead. */
        const c = qa('#hand button.want')[0] || qa('#hand button').find((b) => !b.disabled);
        if (c) click(c); else click(qa('#prompt button').find((b) => !b.disabled));
      } else if (/Give up|Retire a card|spend one extra card|shared pile/.test(t)) {
        const c = qa('#hand button.want')[0] || qa('#hand button').find((b) => !b.className.includes('dead'));
        if (c) click(c);
      } else if (/Take a card/.test(t)) {
        const s = q('.slot.hot');
        if (s) click(s); else click(btn(/Cancel/));
      } else if (/Declare/.test(t)) click(btn(/Skip/));
      else if (/Famine/.test(t)) {
        const r = q('.vrowbox button.want');
        if (r) click(r); else click(btn(/Take the loss/));
      } else if (/Secret objective/.test(t)) click(q('.objpick button'));
      else if (/Water advantage/.test(t)) {
        const h = q('#map .hot');
        if (h) click(h); else click(btn(/Skip/));
      } else if (/Found a colony/.test(t)) {
        const h = q('#map .hot');
        if (h) click(h); else click(btn(/Stop here/));
      } else if (/Which terrain/.test(t)) click(q('.go.terr'));
      else if (/Raid|Seize|Conquer|Overrun/.test(t)) {
        const h = q('#map .hot');
        if (h) click(h); else click(btn(/Stop/));
      } else if (/Move —|Fortify —/.test(t)) {
        const h = q('#map .hot');
        if (h) click(h); else click(btn(/Cancel/) || btn(/Pick another/));
      }
      setTimeout(tick, 0);
    };
    const finish = (t) => cb({ seed, n, seat, retire, fail, seen,
                               over: /Game over/.test(t), last: t.slice(0, 90) });
    tick();
  }, 200);
}

const cases = [[21, 3, 0, 'lowest', 'abc', 'secret'],
               [22, 4, 2, 'lowest', 'abd', 'open'],
               [23, 2, 1, 'any', 'abc', 'off']];
let done = 0, bad = 0;
const all = {};
for (const [s, n, seat, r, dk, ob] of cases) run(s, n, seat, r, dk, ob, (x) => {
  if (!x.over) { bad++; console.log(`seed ${x.seed}: DID NOT FINISH — ${x.last}`); }
  if (x.fail.length) {
    bad++;
    console.log(`seed ${x.seed} (${x.n}p, retire=${x.retire}):`);
    for (const f of [...new Set(x.fail)].slice(0, 6)) console.log('   ' + f);
  }
  for (const k in x.seen) all[k] = (all[k] || 0) + x.seen[k];
  if (++done === cases.length) {
    console.log(bad ? 'FAIL' :
      'every step lit exactly one area, with something live in it — ' +
      Object.entries(all).map(([k, v]) => `${k} ×${v}`).join(', '));
    process.exit(bad ? 1 : 0);
  }
});
