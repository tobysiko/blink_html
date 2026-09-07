/* MELDS GO DOWN FACE DOWN.
 *
 * All anyone sees while the cards are being laid is HOW MANY each player put
 * down — which is the number that decides what matching the winner costs — and
 * every meld is turned over together once the last one is down.
 *
 * The bot never read a rival's cards when choosing its own meld, so this
 * changes nothing for it. It changes everything for a person: the last player
 * to lay used to choose knowing exactly what they had to beat. So what is
 * checked here is what the CLIENT is allowed to draw, at the moment it draws
 * it, which is the only place the rule can be broken.
 *
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const T = require('./test_setup.js');
const E = require('./engine.js');
const html = fs.readFileSync(T.PLAY_HTML, 'utf8');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* ---- the engine turns them over, once, after the last one is down ---- */
{
  const g = new E.Game(3, 21, { humans: [] });
  if (g.events) g.events.length = 0;
  const it = g.playRound();
  let r = it.next();
  while (!r.done) r = it.next(null);
  const order = (g.events || [])
    .filter((e) => e.type === 'meld' || e.type === 'reveal')
    .map((e) => (e.type === 'meld' ? 'm' : 'R')).join('');
  ok(order.includes('R'), 'the engine never says the melds are turned over');
  /* Every seat lays, and only then does the table turn over. One reveal. */
  ok(order.startsWith('mmmR'),
     `melds and reveals came in the order ${order.slice(0, 12)}`);
  ok((order.match(/R/g) || []).length === 1,
     `${(order.match(/R/g) || []).length} reveals in one round`);
}

/* ---- and the table shows backs until it happens ---- */
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
setTimeout(() => {
  /* Seat 2 of 3 is the person, so two bots lay before they are asked. */
  T.start(w, d, { players: 3, seat: 2, seed: 11 });
  setTimeout(() => {
    ok(w.eval('REQ && REQ.type') === 'meld',
       `expected to be asked for a meld, got ${w.eval('REQ && REQ.type')}`);
    /* Ask the DOM and the engine, not the animation queue: with the fx layer
       off - which is what jsdom is, and what a reduced-motion player gets -
       TRICK is never filled in, and the rule still has to hold. */
    ok(w.eval('!!(G.P[0].tableau && G.P[1].tableau)'),
       'the two bots have not laid before the person is asked');
    const backs = d.querySelectorAll('#corners .cf.mid.back').length;
    const faces = d.querySelectorAll('#corners .cf.mid:not(.back)').length;
    ok(backs > 0, 'no rival meld is face down while the person is still choosing');
    ok(faces === 0,
       `${faces} rival cards are face up while the person is still choosing`);
    /* The count is the one thing they may know, and it must be countable. */
    ok(backs === w.eval('G.P[0].tableau.length + G.P[1].tableau.length'),
       'the backs do not add up to the cards actually laid');
    /* Your own meld is never hidden from you. */
    ok(!d.querySelector('#mymeld .cf.back'),
       'your own meld was dealt back to you face down');

    /* Lay one, and the table turns over. */
    w.eval('answer(REQ.options[0])');
    setTimeout(() => {
      ok(w.eval('shown(0)') === true, 'the melds never turned over');
      ok(w.eval('G.winner !== null && G.winner !== undefined'),
         'the trick never resolved');
      ok(d.querySelectorAll('#corners .cf.mid.back').length === 0,
         'a rival meld is still face down after the reveal');
      ok(d.querySelectorAll('#corners .cf.mid').length > 0,
         'the rival melds vanished instead of turning over');
      if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
      console.log('face down: the engine reveals once, after the last meld is laid; '
        + 'until then a rival shows backs you can count and nothing else, and your own '
        + 'meld stays face up to you');
    }, 2600);
  }, 2200);
});
