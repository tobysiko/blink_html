/* Does the player board tell a player what the game is about to do to them?
 *
 * Written after a playtest note: "the player board is lacking crucial
 * information and will confuse players. Especially the population feeding cost
 * is completely unavailable and will hit players without warning."
 *
 * That was accurate, and in three separate ways at once:
 *   - every column was an unlabelled number, its meaning only in a `title`
 *     tooltip — which needs a hover, and a phone has no hover;
 *   - the feeding cost was drawn as small empty coin circles, which read as
 *     decoration rather than as a bill;
 *   - below 560px the whole feeding and movement columns were display:none.
 *
 * So the board is checked here the way a player reads it: as text on a screen.
 * The numbers themselves are the engine's (BANDS), not copies — a test that
 * hard-coded "2 gold at Kingdom" would keep passing after a rebalance and
 * would be worse than no test.
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');
const E = require('./engine.js');

const HTML = require('./test_setup.js').PLAY_HTML;
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

const dom = new JSDOM(fs.readFileSync(HTML, 'utf8'),
                      { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;

setTimeout(() => {
  const start = d.querySelector('#start');
  ok(!!start, 'no Start button — the page did not build');
  if (start) start.click();
  setTimeout(check, 900);
}, 400);

function txt(n) { return n ? n.textContent.replace(/\s+/g, ' ').trim() : ''; }

function check() {
  const rows = [...d.querySelectorAll('.tier-row')];
  const head = rows.find((r) => r.classList.contains('head'));
  const body = rows.filter((r) => !r.classList.contains('head'));

  ok(body.length === E.BANDS.length,
     `the board shows ${body.length} tiers, the game has ${E.BANDS.length}`);

  /* ---- 1. every column says what it is ---------------------------------- */
  ok(!!head, 'the tier table has no heading row — every number on the player '
     + 'board is unlabelled, and the meanings live in tooltips a phone cannot show');
  if (head) {
    for (const cls of ['mlim', 'tname', 'uslots', 'food', 'mv', 'cap']) {
      const cell = head.querySelector('.' + cls);
      ok(cell && txt(cell).length > 0,
         `the \`${cls}\` column has no heading — its numbers mean nothing on sight`);
    }
  }

  /* ---- 2. the feeding cost is a number, per tier ------------------------ */
  /* This is the one the note singled out. For every tier that charges, the
   * amount has to be READABLE — present as a digit, not implied by how many
   * small circles are drawn. */
  E.BANDS.forEach(([name, , , food], j) => {
    const cell = body[j] && body[j].querySelector('.food');
    const shown = txt(cell);
    if (food > 0) {
      ok(new RegExp(`\\b${food}\\b`).test(shown),
         `${name} charges ${food} to refill, and its board row shows "${shown}"`
         + ' — the cost is not written anywhere a player can read it');
    } else {
      ok(shown.length > 0,
         `${name} costs nothing to refill and its row says nothing at all — `
         + '"free" is information too');
    }
  });

  /* ---- 3. move limit and rank cap, per tier ----------------------------- */
  /* `\b` is no use against "1mv" — there is no word boundary between a digit
   * and a letter. The number is what matters, so pull the digits out. */
  const digits = (s) => (s.match(/\d+/g) || []).map(Number);
  E.BANDS.forEach(([name, , , , moves, , cap], j) => {
    const mv = txt(body[j] && body[j].querySelector('.mv'));
    ok(digits(mv).includes(moves),
       `${name} gets ${moves} free move(s); its row shows "${mv}"`);
    const cp = txt(body[j] && body[j].querySelector('.cap'));
    ok(digits(cp).includes(cap),
       `${name} may buy up to rank ${cap}; its row shows "${cp}"`);
  });

  /* ---- 4. and YOUR bill, in a sentence ---------------------------------- */
  /* The table is a reference. A player needs to be told in words what their
   * own tier costs — not to work it out from a row they are not on yet.
   *
   * Which tier that is comes from the board itself (`.here`), not from an
   * assumption about where a game starts. That is deliberate: it means this
   * checks the note is DERIVED from the tier rather than a fixed line of text
   * that happens to be right on turn one. */
  const note = d.querySelector('.foodnote');
  ok(!!note, 'nothing on the board states the feeding cost in words; the table '
     + 'alone is what let it ambush people');
  const hereIdx = body.findIndex((r) => r.classList.contains('here'));
  ok(hereIdx >= 0, 'no tier row is marked as the one you are on');

  if (note && hereIdx >= 0) {
    const noteText = txt(note);
    const [hereName, , , hereFood] = E.BANDS[hereIdx];
    ok(noteText.includes(hereName),
       `you are a ${hereName} and the feeding note does not say so: "${noteText}"`);

    if (hereFood > 0) {
      ok(digits(noteText).includes(hereFood),
         `a ${hereName} pays ${hereFood} to refill; the note says "${noteText}"`);
      ok(note.classList.contains('due'),
         'the tier you are on charges for refills and the note is not marked as '
         + 'due — it reads exactly like "this is free"');
    } else {
      ok(!note.classList.contains('due'),
         `refilling is free at ${hereName} but the note is flagged as a cost`);
      /* Free now, not free later: the whole point is advance warning. */
      const firstCharging = E.BANDS.findIndex((b) => b[3] > 0);
      ok(firstCharging < 0 || noteText.includes(E.BANDS[firstCharging][0]),
         'refilling is free at your tier and the note does not say which tier '
         + `starts charging: "${noteText}"`);
    }
  }

  const cols = head ? [...head.children].map((c) => txt(c)).join(' · ') : '—';
  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : `player board: ${body.length} tiers under headings [${cols}], `
      + 'every feeding cost, move limit and rank cap legible as a number, and '
      + 'the bill for your own tier stated in words');
  process.exit(fail.length ? 1 : 0);
}
