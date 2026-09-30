/* THE OTHER PLAYERS' BOARDS: EVERYTHING THE TABLE SHOWS, NOTHING IT HIDES.
 *
 * Toby: "In the app I can't see much about the other players. At the table I
 * would see their boards and VP row and one map objective." So every rival now
 * has a small board under your own. This plays whole games through the page
 * and checks, at every question the engine asks:
 *
 *   - one board per rival, carrying their tier, gold, hand and discard counts,
 *     their victory row card for card, and the objective they SHOW;
 *   - the objective they keep HIDDEN appears nowhere on the page - not on
 *     their board, not in the log line the engine writes when it completes -
 *     and the score shown for them leaves its points out (the "+?");
 *   - once the game is over, all of it is revealed.
 *
 * The hidden-name check is the one that found the leak this was written with:
 * the log announced "Fjord completed - 2 points" for a rival's secret card.
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const html = fs.readFileSync(require('./test_setup.js').PLAY_HTML, 'utf8');
const fail = [];
let checks = 0, leaksLooked = 0, toggles = 0;

function game(seed, n) {
  return new Promise((done) => {
    /* a real origin, so localStorage exists and remembering can be checked */
    const dom = new JSDOM(html, { url: 'https://blink.test/', runScripts: 'dangerously', pretendToBeVisual: true });
    const w = dom.window, d = w.document;
    w.addEventListener('error', (e) => fail.push('error: ' + e.message));
    const q = (s) => d.querySelector(s);
    const qa = (s) => [...d.querySelectorAll(s)];

    const inspect = () => {
      const G = w.eval('G'), ME = w.eval('ME');
      const over = w.eval('gameOver()');
      const sc = G.score();
      const boards = qa('#rivals .rboard');
      if (boards.length !== G.n - 1) {
        fail.push(`seed ${seed}: ${boards.length} rival boards for ${G.n - 1} rivals`);
        return;
      }
      checks++;
      /* names the page may legitimately show: yours, and everyone's open ones */
      const allowed = new Set((G.P[ME].objectives || []).map((o) => o.id));
      for (let i = 0; i < G.n; i++) for (const o of G.openObjectivesOf(i)) allowed.add(o.id);
      const body = q('#game').textContent;           // not d.body: that includes the scripts
      for (const b of boards) {
        const i = Number(b.dataset.seat);
        const p = G.P[i];
        const txt = b.textContent.replace(/\s+/g, ' ');
        const name = w.eval(`seatName(${i})`);
        if (!txt.includes(name)) fail.push(`seat ${i}: board does not name ${name}`);
        if (!txt.includes(`🪙 ${p.gold}`)) fail.push(`seat ${i}: gold ${p.gold} not shown`);
        if (!new RegExp(`\\b${p.hand.length}\\b`).test(txt)) fail.push(`seat ${i}: hand size missing`);
        const chips = b.querySelectorAll('.rvs .cf').length;
        if (chips !== p.vrow.length) fail.push(`seat ${i}: ${chips} victory cards drawn, ${p.vrow.length} held`);
        const open = over ? p.objectives || [] : G.openObjectivesOf(i);
        const cards = b.querySelectorAll('.objcard').length;
        if (cards !== open.length) fail.push(`seat ${i}: ${cards} objectives shown, ${open.length} are public`);
        /* the score: public points only until the end */
        const d0 = sc.find((x) => x.seat === i);
        let hidden = 0;
        if (!over) for (const x of d0.objDone || []) if (!open.includes(x.o)) hidden += x.points;
        const want = d0.total - hidden;
        const got = Number((b.querySelector('.score').textContent.match(/\d+/) || [])[0]);
        if (got !== want) fail.push(`seat ${i}: score shows ${got}, public score is ${want} (full ${d0.total})`);
        const corner = q(`#corners .corner[data-seat="${i}"] .sc`);
        if (corner && Number(corner.textContent.match(/\d+/)[0]) !== want)
          fail.push(`seat ${i}: map corner shows ${corner.textContent}, public score is ${want}`);
        /* and no hidden card's name anywhere on the page */
        if (!over) for (const o of p.objectives || []) {
          if (allowed.has(o.id)) continue;
          leaksLooked++;
          const nm = w.eval(`objName({ id: ${o.id} })`);
          if (body.includes(nm))
            fail.push(`seat ${i}'s hidden objective "${nm}" is readable on the page`);
        }
      }
    };

    setTimeout(() => {
      require('./test_setup.js').start(w, d, { players: n, seat: 0, seed });
      let steps = 0, toggled = false;
      const tick = () => {
        if (w.eval('gameOver()')) {
          w.eval('render()');
          inspect();
          const b = q('#rivals .rboard');
          if (b && b.textContent.includes('+?')) fail.push('after the game a rival still shows "+?"');
          return done();
        }
        if (w.eval('REQ && mine()')) {
          if (steps % 3 === 0) inspect();
          /* One tap folds them all away and one brings them back; folded, the
           * bar still gives every rival's public score; the choice sticks. */
          if (!toggled && steps >= 30) {
            toggled = true; toggles++;
            const click = (x) => x.dispatchEvent(new w.MouseEvent('click', { bubbles: true, cancelable: true }));
            const fold = () => q('#rivals .rivalsfold');
            if (!fold().open) fail.push('the other boards start folded on a wide screen');
            click(q('#rivals summary'));
            if (fold().open) fail.push('the Hide bar did not fold the boards away');
            if (qa('#rivals .rdig').length !== w.eval('G.n') - 1)
              fail.push('folded, the bar does not list every rival');
            if (w.localStorage.getItem('blink_rivals') !== 'shut') fail.push('folding was not remembered');
            w.eval('render()');
            if (fold().open) fail.push('the boards unfolded themselves on the next render');
            click(q('#corners .corner[data-seat] .ohead'));
            if (!fold().open) fail.push('tapping a rival in the map corner did not show the boards');
            click(q('#rivals summary'));
            click(q('#rivals summary'));
            if (!fold().open || w.localStorage.getItem('blink_rivals') !== 'open')
              fail.push('the Show bar did not bring the boards back and remember it');
          }
          w.eval(`(() => {
            if (REQ.type === 'turn') {
              const o = REQ.opts;
              const m = o.cards.find((m) => m.options.length);
              if (m) { const e = m.options[0];
                return answer({ kind: 'spend', card: m.card, cell: e[0], act: e[1] }); }
              if (o.cards.length) return answer({ kind: 'cash', card: o.cards[0].card });
              return answer({ kind: 'end' });
            }
            if (REQ.options && REQ.options.length) return answer(REQ.options[0]);
            answer(null);
          })()`);
        }
        if (++steps > 6000) { fail.push(`seed ${seed}: did not finish`); return done(); }
        setTimeout(tick, 0);
      };
      tick();
    }, 0);
  });
}

(async () => {
  await game(5, 4);
  await game(12, 3);
  await game(30, 2);
  if (toggles !== 3) fail.push(`the fold was exercised in ${toggles} of 3 games`);
  if (!leaksLooked) fail.push('no rival ever held a hidden objective — the leak check never ran');
  if (fail.length) { console.error([...new Set(fail)].slice(0, 30).join('\n')); process.exit(1); }
  console.log(`rival boards: ${checks} inspections — tiers, gold, hand, victory row and shown `
    + `objective on every board; ${leaksLooked} hidden-objective checks, none readable; `
    + 'public score until the end, everything after');
})();
