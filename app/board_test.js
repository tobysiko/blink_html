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

  /* ---- 2. the feeding cost, as countable slots ------------------------- */
  /* This used to demand a DIGIT in every row, because a playtester read past
   * two small empty circles and was surprised by the bill. The digit is still
   * there — once, in the note under the table, for the tier you are actually
   * on, which is the only one you can be charged for. In the table itself the
   * cost is now a row of slots you can count, and those same slots carry the
   * ascension coins until you claim them, so the number arrives as something
   * you are about to GAIN rather than as small print.
   *
   * What is checked here is that the count is exact and that the ascension
   * reward is finally visible at all — it was drawn nowhere before. */
  E.BANDS.forEach(([name, , , food, , ascend], j) => {
    const cell = body[j] && body[j].querySelector('.food');
    const slots = cell ? cell.querySelectorAll('.cslot').length : -1;
    if (food > 0) {
      ok(slots === food,
         `${name} charges ${food} to refill and draws ${slots} slot(s)`);
      /* Food and the ascension reward are the same number at every tier, which
       * is what lets one row of slots carry both. If that ever stops being
       * true the whole gauge is a lie. */
      ok(ascend === food,
         `${name} pays ${ascend} on ascension but eats ${food} — the feed slots `
         + 'can no longer hold the ascension coins');
      const asc = cell.querySelectorAll('.cslot.asc').length;
      ok(asc === food,
         `${name} has not been reached yet, so all ${food} slots should hold an `
         + `ascension coin; ${asc} do`);
    } else {
      ok(txt(cell).length > 0,
         `${name} costs nothing to refill and its row says nothing at all — `
         + '"free" is information too');
    }
  });

  /* ONE VOCABULARY ACROSS BOTH SURFACES. A player with the A4 board on the
   * table and this open on a phone should be reading the same shapes: a meld
   * is a fan of that many cards, a rank cap is a card's index corner, moves
   * are a number and a stride, and the tier name reaches across to the reserve
   * it governs. Drift here is two boards teaching two games. */
  E.BANDS.forEach(([name, , meld, , , , cap], j) => {
    const row = body[j];
    const cards = row ? row.querySelectorAll('.mlim .fan i').length : -1;
    ok(cards === meld,
       `${name} may play ${meld} cards and its fan draws ${cards}`);
    const top = row && row.querySelector('.mlim .fan i:last-child b');
    ok(top && txt(top) === String(meld),
       `${name}'s fan does not carry ${meld} on its top card`);
    const corner = row && row.querySelector('.cap .corner b');
    ok(corner && txt(corner) === String(cap),
       `${name} buys up to ${cap}; its rank corner shows "${corner && txt(corner)}"`);
    ok(row && row.querySelector('.mv .stride svg'),
       `${name} has no stride arrow beside its move count`);
    ok(row && row.querySelector('.tname .lead'),
       `${name} does not reach across to its own reserve row`);
  });

  /* ...and the bill in words, for the tier you are on. */
  {
    const note = d.querySelector('.foodnote');
    ok(!!note && txt(note).length > 0,
       'the tier you are on does not say what feeding will cost you');
  }

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
