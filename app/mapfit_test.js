/* Two things a player has to be able to do: hit a tile, and see the end coming.
 *
 * TILES. ui.js promises a floor on how small a hex may be drawn — ZOOM_MIN,
 * "37 x 43 px, the smallest honest target". It was not keeping that promise. The
 * viewBox is built as W/scale by H/scale, which only yields `scale` when W and H
 * are the element's CURRENT size: SVG letterboxes a viewBox whose aspect ratio
 * does not match its box, and the effective scale becomes the smaller of the two
 * axes. MAPGEO was measured once per render, and the map's own height changes
 * AFTER that as the prompt, hand and player board lay out beneath it. Measured
 * live on the deployed page: a viewBox of ratio 1.96 inside an element of ratio
 * 2.98, letterboxed to 0.60 — tiles at 30x35 px, adrift in a wide empty margin,
 * and hard to click.
 *
 * THE END. §11 gives a whole extra round after a trigger fires. That is enough
 * warning to act on, and the game was giving it only as a log line that scrolls
 * away and four small words beside the round number.
 *
 * Needs jsdom. jsdom does no layout, so the element box is stubbed at sizes that
 * matter — a wide short window is the shape that starves the map of height.
 */
const fs = require('fs');
const path = require('path');
const E = require('./engine.js');

let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const html = fs.readFileSync(path.join(__dirname, '..', 'Blink-play-v0.22.html'), 'utf8');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* Must match ui.js. If these move, this test should start failing rather than
 * quietly certifying a smaller tile. */
const HEXR = 34, ZOOM_MIN = 0.72;
const HEX_W = Math.sqrt(3) * (HEXR - 1), HEX_H = 2 * (HEXR - 1);

function page() {
  const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
  const errs = [];
  dom.window.console.error = (...a) => errs.push(a.join(' '));
  return { w: dom.window, d: dom.window.document, errs };
}

/* jsdom has no layout engine, so getBoundingClientRect is stubbed on #map to
 * report the box a real browser would give it. */
function stubBox(w, d, width, height) {
  const svg = d.querySelector('#map');
  svg.getBoundingClientRect = () => ({
    x: 0, y: 0, top: 0, left: 0, right: width, bottom: height,
    width, height, toJSON() { return this; },
  });
  return svg;
}

const A = page();
setTimeout(() => {
  const { w, d, errs } = A;
  require('./test_setup.js').start(w, d, { players: 3, seat: 0, seed: 77 });

  setTimeout(() => {
    /* ---- 1. the fit keeps its own floor, at every window shape ---------- */
    /* A wide short box is the case that broke: the map is fitted to its height
     * and the width is all margin. */
    for (const [bw, bh] of [[1396, 364], [1396, 468], [820, 380], [700, 900], [390, 300]]) {
      const svg = stubBox(w, d, bw, bh);
      w.eval('applyViewBox()');
      const vb = (svg.getAttribute('viewBox') || '').split(' ').map(Number);
      ok(vb.length === 4 && vb.every(Number.isFinite),
         `${bw}x${bh}: the viewBox is "${svg.getAttribute('viewBox')}"`);
      if (vb.length !== 4) continue;

      /* The scale a browser will actually apply, letterboxing included. */
      const scale = Math.min(bw / vb[2], bh / vb[3]);
      ok(Math.abs(bw / vb[2] - bh / vb[3]) < 0.01,
         `${bw}x${bh}: the viewBox is ${(vb[2] / vb[3]).toFixed(2)}:1 inside a box of `
         + `${(bw / bh).toFixed(2)}:1 — SVG will letterbox it and the real scale `
         + `drops to ${scale.toFixed(2)}`);
      ok(scale >= ZOOM_MIN - 0.001,
         `${bw}x${bh}: hexes are drawn at scale ${scale.toFixed(2)}, under the `
         + `${ZOOM_MIN} floor — ${Math.round(HEX_W * scale)}x${Math.round(HEX_H * scale)} px `
         + 'instead of 37x43, which is what makes them hard to hit');
    }

    /* And the cached geometry cannot be stale, because that was the mechanism. */
    stubBox(w, d, 1396, 364);
    w.eval('applyViewBox()');
    const geo = JSON.parse(w.eval('JSON.stringify({W: MAPGEO.W, H: MAPGEO.H})'));
    ok(Math.round(geo.W) === 1396 && Math.round(geo.H) === 364,
       `the fit is still using a box of ${Math.round(geo.W)}x${Math.round(geo.H)} `
       + 'after the element became 1396x364');

    /* ---- 2. the end of the game announces itself ------------------------ */
    const banner = d.querySelector('#endbanner');
    ok(!!banner, 'there is no end-of-game banner in the page at all');
    ok(banner && banner.hidden, 'the end banner is showing before anything triggered it');

    /* The trigger has fired, one more full round to come. */
    w.eval('G.endedOn = "end.lastUnit"; G.finalRounds = G.round + 1; renderSide();');
    ok(banner && !banner.hidden, 'a triggered end shows no banner');
    let txt = banner ? banner.textContent.replace(/\s+/g, ' ') : '';
    ok(/ONE more full round/i.test(txt),
       `the warning does not say a whole round is left: "${txt.slice(0, 110)}"`);
    ok(/last unit placed/i.test(txt),
       `the warning does not say what triggered it: "${txt.slice(0, 110)}"`);
    ok(banner && !banner.classList.contains('final'),
       'a round that is not the last is styled as the last');
    ok(/one round left/i.test(d.querySelector('#endnote').textContent),
       `the round counter reads "${d.querySelector('#endnote').textContent}"`);

    /* And now it IS the last round. */
    w.eval('G.finalRounds = G.round; renderSide();');
    txt = banner ? banner.textContent.replace(/\s+/g, ' ') : '';
    ok(/FINAL ROUND/i.test(txt), `the last round does not say so: "${txt.slice(0, 110)}"`);
    ok(banner && banner.classList.contains('final'),
       'the final round is not marked as different from the one before it');
    ok(/FINAL ROUND/i.test(d.querySelector('#endnote').textContent),
       `the round counter reads "${d.querySelector('#endnote').textContent}"`);

    /* ---- the extra round must be PLAYABLE, and then must end -------------
     *
     * From a playtest: "the final round was announced, but at the same time the
     * winner was announced and the game ended."
     *
     * The engine was right — it plays a full extra round every time. The UI was
     * not. The round counter is bumped at the START of a round and finished() is
     * `round >= finalRounds`, so finished() is already true the moment the extra
     * round begins. renderPrompt rendered the result table on finished(), which
     * replaced the player's turn with the score the instant the round they were
     * granted started. Hence: announced and over at once.
     *
     * The two states are told apart by whether the driver still has anything in
     * flight, so both are set up here explicitly. */

    /* (a) the final round, in progress: a question is outstanding. */
    w.eval('G.endedOn = "end.lastUnit"; G.finalRounds = G.round;');
    ok(w.eval('G.finished()'),
       'the engine does not consider itself finished during the final round — '
       + 'the premise of this check has changed');
    ok(!w.eval('gameOver()'),
       'the UI thinks the game has stopped while a question is still outstanding');
    w.eval('renderSide(); renderPrompt();');
    txt = banner ? banner.textContent.replace(/\s+/g, ' ') : '';
    ok(banner && !banner.hidden && /FINAL ROUND/i.test(txt),
       `during the final round the banner reads "${txt.slice(0, 80)}"`);
    ok(!/Game over/i.test(d.querySelector('#prompt').textContent),
       'the prompt shows the result table during the final round — the round the '
       + 'rules grant cannot be played');

    /* (b) truly over: the driver has emptied out. */
    w.eval('IT = null; REQ = null; renderSide(); renderPrompt();');
    ok(w.eval('gameOver()'), 'the UI does not recognise a finished game');
    ok(banner && banner.hidden,
       `the end banner is still up after the game finished, reading `
       + `"${banner && banner.textContent.replace(/\s+/g, ' ').slice(0, 70)}" — next to `
       + 'the result table, which reads as both being announced at once');
    ok(/game over/i.test(d.querySelector('#endnote').textContent),
       `after the game the round counter reads "${d.querySelector('#endnote').textContent}"`);

    /* It goes away again if a game is restarted rather than sticking around. */
    w.eval('G.endedOn = null; G.finalRounds = null; renderSide();');
    ok(banner && banner.hidden, 'the end banner survives the end being cleared');

    /* ---- 3. and the rule itself: one whole extra round, every time ------ */
    /* The complaint was about the rule, so the rule is checked too, on real
     * games rather than on a poked-at state. §11: finish the round the trigger
     * fired in, then play exactly ONE more. */
    for (const seed of [4242, 77, 31, 1234]) {
      const g = new E.Game(2, seed, { humans: [], meldScore: 'sum', aSumLadder: 'rank',
                                      researchRule: 'twice', layout: 'late' });
      let triggeredAt = null, guard = 0;
      while (!g.finished() && guard++ < 80) {
        const it = g.playRound();
        let r = it.next();
        while (!r.done) r = it.next(null);
        if (g.endedOn && triggeredAt === null) triggeredAt = g.round;
      }
      ok(triggeredAt !== null, `seed ${seed}: the game ended without a trigger`);
      ok(g.round === triggeredAt + 1,
         `seed ${seed}: the trigger fired after round ${triggeredAt} and the game `
         + `ran to round ${g.round} — §11 asks for exactly one more`);
    }

    ok(!errs.length, 'the page logged errors: ' + errs.slice(0, 2).join(' | '));
    console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
      : 'map and endgame: the viewBox matches its element at five window shapes so '
        + `no hex is drawn under ${ZOOM_MIN} scale, and the end of the game is `
        + 'announced a full round ahead, then again as the final round');
    process.exit(fail.length ? 1 : 0);
  }, 700);
}, 400);
