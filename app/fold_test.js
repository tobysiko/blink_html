/* What folds away on a small screen, and what it still says while folded.
 *
 * The market and the tier table are reference: things a player consults, not
 * things they act on every turn. On a phone they were most of the scroll
 * between the prompt and the map. Both fold now, and the interesting parts are
 * the ones a screenshot cannot check:
 *
 *   - a fold that is closed must still carry the one line of itself a player
 *     needs from moment to moment, or it is not folded, it is hidden;
 *   - the market must OPEN ITSELF when a step is asking for a card in it,
 *     because a lit area nobody can see is worse than no lit area at all;
 *   - and the app opening it that way must not be recorded as the player's
 *     own choice.
 *
 * jsdom's matchMedia answers `false` to everything, so the phone is staged by
 * replacing it before the page's own script runs.
 *
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const T = require('./test_setup.js');
const html = fs.readFileSync(T.PLAY_HTML, 'utf8');
const fail = [];

function play(narrow) {
  /* `beforeParse` is the only moment matchMedia can be replaced: after it the
     page's own script has already read the width and decided what to fold. */
  const dom = new JSDOM(html, {
    runScripts: 'dangerously', pretendToBeVisual: true,
    beforeParse(w) {
      w.matchMedia = (q) => ({
        matches: narrow && /max-width:\s*900px/.test(q),
        media: q, onchange: null,
        addEventListener() {}, removeEventListener() {},
        addListener() {}, removeListener() {}, dispatchEvent() { return false; },
      });
    },
  });
  return { w: dom.window, d: dom.window.document };
}

const phone = play(true);
const roomy = play(false);

/* Two waits, and both are needed. The first lets each page finish loading, so
   that Start has a listener on it at all; the second lets the game it starts
   reach its first render. */
setTimeout(() => {
  for (const g of [phone, roomy]) T.start(g.w, g.d, { players: 3, seat: 0 });
  setTimeout(run, 40);
}, 40);

function run() {
  // ------------------------------------------------------------- a phone
  {
    const { w, d } = phone;
    const mkt = d.querySelector('#marketfold');
    const brd = d.querySelector('#player .boardfold');
    if (!mkt || !brd) fail.push('the folds are missing from the page');
    else {
      if (mkt.open) fail.push('the market is open on a phone');
      if (brd.open) fail.push('the tier table is open on a phone');
      const m = mkt.querySelector('.foldnow').textContent.trim();
      const b = brd.querySelector('.foldnow').textContent.trim();
      if (!/\d/.test(m)) fail.push(`the folded market says nothing countable: "${m}"`);
      if (!/\d/.test(b)) fail.push(`the folded tier table says no numbers: "${b}"`);
      /* The two numbers a player most needs off the board and cannot deduce
         from anything else on screen: the feeding cost and the move allowance. */
      if (!/feed/i.test(b) || !/move/i.test(b))
        fail.push(`the folded tier table drops the feed or the moves: "${b}"`);

      /* A step that wants a card OUT of the market opens it. */
      w.eval('REQ = { type: "buy", seat: ME, options: [0, 1] }; renderMarket();');
      if (!mkt.open) fail.push('a buy does not open the folded market');
      /* ...and that is the app's doing, not the player's, so the moment the
         buy is over the market goes back to where they left it. */
      w.eval('REQ = { type: "turn", seat: ME, opts: { cards: [] } }; renderMarket();');
      if (mkt.open) fail.push('the market stayed open after the step that needed it');
    }
  }

  // --------------------------------------------------- a screen with room
  {
    const d = roomy.d;
    const mkt = d.querySelector('#marketfold');
    const brd = d.querySelector('#player .boardfold');
    if (!mkt || !mkt.open) fail.push('the market is folded away on a desktop');
    if (!brd || !brd.open) fail.push('the tier table is folded away on a desktop');
  }

  if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
  console.log('folds: on a phone the market and the tier table start closed and still '
    + 'say their current line; a buy opens the market and closes it again; '
    + 'with room, both are open');
}
