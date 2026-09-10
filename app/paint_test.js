/* STATES A PERSON HAS TO SEE.
 *
 * Reported from a real game: "drafting in the app is broken, can't select the
 * cards I want to keep." The clicks were landing, the selection was right, the
 * class was on the card — and the chosen card computed byte-identically to an
 * unchosen one, because `.cf.sel` and `.cf.want` both say what they mean with
 * a box-shadow and both lost theirs to the card's own. The app registered
 * every pick and showed nothing.
 *
 * jsdom cannot catch that: it has no layout and no cascade, so the DOM tests
 * saw the class land and called it done. This one needs a REAL browser, which
 * is why it is optional — it skips cleanly where Playwright is not installed
 * rather than failing a suite that has no way to run it.
 *
 *   npm install playwright            (once)
 *   node app/paint_test.js            (uses the built play page)
 *   BLINK_PLAY=/path/to/play.html node app/paint_test.js
 *
 * ADD TO THIS whenever a rule is communicated only by how something looks. The
 * question it asks is the one no other test asks: are these two states
 * actually different on screen?
 */
let chromium;
try { ({ chromium } = require('playwright')); }
catch (e) {
  console.log('paint: skipped — needs a real browser (npm install playwright). '
    + 'Nothing else in the suite can see a style collision.');
  process.exit(0);
}
const PLAY = process.env.BLINK_PLAY || require('./test_setup.js').PLAY_HTML;
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  await p.goto('file://' + PLAY);
  await p.waitForTimeout(400);
  await p.evaluate(() => document.querySelector('#np-3').click());
  await p.click('#start');
  await p.waitForTimeout(1200);

  const at = await p.evaluate(() => (typeof REQ !== 'undefined' && REQ) ? REQ.type : null);
  ok(at === 'draft', `the game did not open on a draft (it was ${at})`);
  if (at !== 'draft') { await b.close(); return report(); }

  /* Real mouse clicks, not dispatched events: the card-hold handler listens on
     pointerdown and can swallow a click, which a synthetic event never shows. */
  for (const i of [0, 2, 5, 7]) {
    const el = await p.$(`#hand [data-pack="${i}"]`);
    const box = await el.boundingBox();
    ok(!!box && box.width > 10, `pack card ${i} has no clickable box`);
    await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    await p.waitForTimeout(150);
  }

  const seen = await p.evaluate(() => {
    const paint = (n) => { const s = getComputedStyle(n);
      return [s.outlineWidth, s.outlineColor, s.boxShadow, s.transform,
              s.opacity, s.backgroundColor, s.borderColor].join(' | '); };
    const keep = [...document.querySelectorAll('#hand [data-pack].keep')];
    const pass = [...document.querySelectorAll('#hand [data-pack].passing')];
    return { picked: SEL.draft.length, keeps: keep.length, passes: pass.length,
             keepPaint: keep.length ? paint(keep[0]) : null,
             passPaint: pass.length ? paint(pass[0]) : null,
             prompt: (document.querySelector('#prompt .ask') || {}).textContent || '',
             ready: document.querySelector('#prompt button')
                    ? !document.querySelector('#prompt button').disabled : false };
  });

  ok(seen.picked === 4, `four clicks chose ${seen.picked} cards`);
  ok(seen.keeps === 4 && seen.passes === 6,
     `${seen.keeps} kept and ${seen.passes} passing, wanted 4 and 6`);
  /* THE ASSERTION THIS FILE EXISTS FOR. */
  ok(seen.keepPaint !== seen.passPaint,
     'a chosen card and an unchosen one are painted identically — '
     + 'the pick registers and the table does not move:\n      ' + seen.keepPaint);
  ok(seen.ready, 'four cards chosen and the keep button is still disabled');
  ok(/4/.test(seen.prompt),
     `the prompt does not say how many are chosen: "${seen.prompt.trim()}"`);

  /* ...and the choice actually goes through to the next pack. */
  await p.click('#prompt button');
  await p.waitForTimeout(400);
  const next = await p.evaluate(() => (REQ && REQ.type) + ':' + (REQ && REQ.need));
  ok(next === 'draft:2', `after keeping four the next question was ${next}, wanted draft:2`);

  await b.close();
  report();
})().catch((e) => { console.error('paint: threw — ' + e.message); process.exit(1); });

function report() {
  if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
  console.log('paint: a card chosen in the draft is painted differently from one passing on, '
    + 'the count is in the prompt, and four picks let the keep button through');
}
