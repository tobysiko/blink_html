/* The trick, as a round of a card game.
 *
 * The engine settles a whole card phase in one tick, so what makes it read as
 * a card game is entirely in the client: melds land one player at a time, in
 * the order of play, and the crown arrives after the last card. jsdom has no
 * layout, so the client would normally skip all staging — the test lends it a
 * geometry (`cellPoint`) and then watches the clock.
 *
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const T = require('./test_setup.js');
const html = fs.readFileSync(__dirname + '/../Blink-play-v0.22.html', 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
const fail = [], errs = [];
w.addEventListener('error', (e) => errs.push(e.message));
w.console.error = (...a) => errs.push(a.join(' '));

const qa = (s) => [...d.querySelectorAll(s)];
const click = (x) => x.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
const cardsIn = (sel) => qa(sel + ' .cf').length;
const seat = (i) => d.querySelector(`#corners .corner[data-seat="${i}"]`);

const steps = [];
const after = (ms, fn) => steps.push([ms, fn]);

setTimeout(() => {
  /* Lend the client a map geometry: without one it (correctly) plays no
   * animation at all and shows the engine's state directly. */
  w.cellPoint = () => ({ x: 200, y: 200 });

  T.start(w, d, { players: 3, seat: 0, seed: 7 });

  if (!w.eval('fxEnabled()')) fail.push('client will not animate even with a geometry');
  // seat 0 leads, so the play order is 0,1,2 and nobody has laid anything yet
  if (cardsIn('#corners')) fail.push('a rival meld is on the table before the round');

  const hand = qa('#hand button');
  click(hand[0]);
  const play = qa('#prompt button').find((b) => /Play meld/.test(b.textContent));
  if (!play || play.disabled) { fail.push('could not play a meld'); return finish(); }
  click(play);

  /* Beats: mine at 0ms, seat 1 at 330, seat 2 at 660, the crown at 990. */
  after(120, () => {
    if (!cardsIn('#mymeld')) fail.push('your own meld vanished after playing it');
    if (seat(1) && cardsIn('#corners .corner[data-seat="1"]'))
      fail.push('seat 1 played before its beat');
    if (qa('#corners .mslot').length < 4)
      fail.push('a rival that has not played shows no meld limit');
  });
  after(480, () => {
    if (!cardsIn('#corners .corner[data-seat="1"]'))
      fail.push('seat 1 has not laid its meld by 480ms');
    if (cardsIn('#corners .corner[data-seat="2"]'))
      fail.push('seat 2 laid its meld out of turn');
    if (d.querySelector('#turnbar .crown'))
      fail.push('the trick was awarded before the last card was laid');
  });
  after(860, () => {
    if (!cardsIn('#corners .corner[data-seat="2"]'))
      fail.push('seat 2 has not laid its meld by 860ms');
    // rivals are printed like you: full card faces, not chips
    if (!d.querySelector('#corners .cf.mid'))
      fail.push('rival melds are not shown as card faces');
    if (d.querySelector('#corners .cf.mini'))
      fail.push('a rival meld is still using the old chip');
  });
  after(1400, () => {
    const crowns = qa('.crown').length;
    if (!crowns) fail.push('no crown once the trick is settled');
    const win = w.eval('G.winner');
    const box = win === 0 ? d.querySelector('#mymeld') : seat(win);
    if (!box || !box.classList.contains('won'))
      fail.push('the winning seat is not marked as having won');
    // the order strip now shows the trick's ranking, winner first
    const chips = qa('#turnbar .tchip');
    if (chips.length !== 3) fail.push('the order strip lost a seat');
    if (!chips[0].querySelector('.crown'))
      fail.push('the order strip does not put the winner first');
  });
  /* A beat of quiet between the crown and the first map turn is deliberate;
   * by the time the winner is acting the strip must say so. */
  after(1900, () => {
    if (!qa('#turnbar .tchip.done').length && !qa('#turnbar .tchip.now').length)
      fail.push('the order strip shows nobody acting and nobody finished');
  });
  after(2600, () => {
    // whatever the beats missed, the catch-up pass must have corrected
    const shown = qa('#corners .corner').every((c) => c.querySelector('.cf'));
    if (!shown) fail.push('a meld is still face down long after the trick');
    if (w.eval('G.events.length') > 0) fail.push('events were left in the queue');
  });

  let t = 0;
  const runNext = () => {
    if (!steps.length) return finish();
    const [ms, fn] = steps.shift();
    setTimeout(() => { try { fn(); } catch (e) { fail.push('threw: ' + e.message); }
                       runNext(); }, ms - t);
    t = ms;
  };
  runNext();
}, 250);

function finish() {
  if (errs.length) fail.push('errors: ' + errs.slice(0, 3).join(' | '));
  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : 'trick staged: melds land in order of play, crown follows the last card, '
      + 'rivals printed as card faces, catch-up pass clean');
  process.exit(fail.length ? 1 : 0);
}
