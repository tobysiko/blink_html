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
    const el = await p.$(`#hand [data-pool="${i}"]`);
    const box = await el.boundingBox();
    ok(!!box && box.width > 10, `pool card ${i} has no clickable box`);
    await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    await p.waitForTimeout(150);
  }

  const seen = await p.evaluate(() => {
    const paint = (n) => { const s = getComputedStyle(n);
      return [s.outlineWidth, s.outlineColor, s.boxShadow, s.transform,
              s.opacity, s.backgroundColor, s.borderColor].join(' | '); };
    const keep = [...document.querySelectorAll('#hand [data-pool].keep')];
    const pass = [...document.querySelectorAll('#hand [data-pool].passing')];
    return { picked: SEL.draft.length, keeps: keep.length, passes: pass.length,
             keepPaint: keep.length ? paint(keep[0]) : null,
             passPaint: pass.length ? paint(pass[0]) : null,
             plainPaint: paint([...document.querySelectorAll('#hand [data-pool]')]
                               .find((n) => !n.className.includes('passing'))),
             /* ::after carries the collar, so it has to be measured, not the
                card. Round one marks every card fresh, so `fresh` here is
                whatever the first pool gives us and the comparison is against
                a card with the class removed. */
             freshPaint: (() => {
               const n = document.querySelector('#hand [data-pool].fresh');
               if (!n) return null;
               const s = getComputedStyle(n, '::after');
               return [s.content, s.borderTopWidth, s.borderTopStyle,
                       s.borderTopColor, s.top, s.left].join(' | ');
             })(),
             plainNotFreshPaint: (() => {
               const n = document.querySelector('#hand [data-pool]');
               if (!n) return null;
               const clone = n.cloneNode(true);
               clone.className = clone.className.replace(/\bfresh\b/, '');
               n.parentElement.appendChild(clone);
               const s = getComputedStyle(clone, '::after');
               const out = [s.content, s.borderTopWidth, s.borderTopStyle,
                            s.borderTopColor, s.top, s.left].join(' | ');
               clone.remove();
               return out;
             })(),
             prompt: (document.querySelector('#prompt .ask') || {}).textContent || '',
             ready: document.querySelector('#prompt button')
                    ? !document.querySelector('#prompt button').disabled : false };
  });

  ok(seen.picked === 4, `four clicks chose ${seen.picked} cards`);
  /* SELECTING NOW MEANS PASSING ON, so four clicks mark four to leave. The
     other six are not painted `keep` until the quota of six is full, which is
     the deliberate middle state: before you have chosen everything, no card
     is claiming to be safe. */
  ok(seen.passes === 4 && seen.keeps === 0,
     `${seen.passes} marked to pass and ${seen.keeps} marked keep, wanted 4 and 0`);
  /* THE ASSERTION THIS FILE EXISTS FOR. */
  ok(seen.passPaint && seen.passPaint !== seen.plainPaint,
     'a card marked to pass and an untouched one are painted identically — '
     + 'the pick registers and the table does not move:\n      ' + seen.passPaint);
  /* AND THE OTHER THING ON THIS SCREEN THAT IS TOLD APART BY LOOKING. The
     pool is your kept cards and the pack in one ascending row, so the only
     way to see what has just reached you is the collar on it. The first
     version drew that collar at inset:-4px, OUTSIDE the card — and .cf is
     overflow:hidden, so it computed as a perfectly good 2px dotted gold
     border and painted absolutely nothing. Every style query said it was
     there. Only the pixels said otherwise. */
  ok(seen.freshPaint && seen.freshPaint !== seen.plainNotFreshPaint,
     'a card that just reached you is painted identically to one you already '
     + 'kept — the draft cannot be read:\n      ' + seen.freshPaint);
  ok(!seen.ready, 'four of six chosen and the pass button is already enabled');
  ok(/2/.test(seen.prompt),
     `the prompt does not say how many are still to choose: "${seen.prompt.trim()}"`);

  /* ...and six goes through to the next pool. */
  for (const i of [1, 3]) {
    const el = await p.$(`#hand [data-pool="${i}"]`);
    const box = await el.boundingBox();
    await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    await p.waitForTimeout(120);
  }
  const ready = await p.evaluate(() =>
    !document.querySelector('#prompt button').disabled);
  ok(ready, 'six cards chosen and the pass button is still disabled');
  await p.click('#prompt button');
  await p.waitForTimeout(400);
  const next = await p.evaluate(() => (REQ && REQ.type) + ':' + (REQ && REQ.pass));
  ok(next === 'draft:4', `after passing six the next question was ${next}, wanted draft:4`);

  await b.close();
  report();
})().catch((e) => { console.error('paint: threw — ' + e.message); process.exit(1); });

function report() {
  if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
  console.log('paint: a card marked to pass in the draft is painted differently from an '
    + 'untouched one, the count still to choose is in the prompt, and six picks let the '
    + 'pass button through');
}
