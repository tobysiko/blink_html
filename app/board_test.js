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
    /* `food` is NOT in this list: the printed economy has no feeds column, so
     * demanding a heading for it is demanding the column back. It is checked
     * on the full-economy page at the end of this file, where it exists. */
    for (const cls of ['mlim', 'tname', 'uslots', 'mv', 'capcol']) {
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
  /* THE PRINTED GAME HAS NOTHING TO FEED, so the board must not have a column
   * for it. This test used to REQUIRE the feeds column and its slots, and went
   * on passing after v0.26 removed food from the game: BANDS still carries the
   * old numbers, the renderer still drew a slot per unit of them, and the test
   * still counted them and was satisfied. The board showed a column of
   * ascension coins for a reward that no longer exists, under a heading for a
   * bill that never comes, and the one thing watching it was enforcing that.
   *
   * A player asked about it at a table, which is how it was found.
   *
   * `economy: "full"` is still a real option and is checked below, on its own
   * page, where the column SHOULD be there. */
  const foodOn = w.eval('!!(G && G.FOOD_ON)');
  ok(foodOn === false,
     'this page started with food ON — the printed economy is lean, so the rest '
     + 'of these checks would be testing the wrong game');
  ok(!d.querySelector('.tiers .food'),
     'the board still draws a FEEDS column, and v0.26 has nothing to feed');
  ok(!d.querySelector('.foodnote'),
     'the board still warns about the refill bill, and there is no bill');
  ok(!!d.querySelector('.tiers.nofood'),
     'the tier table is not marked .nofood, so the grid keeps an empty column '
     + 'where the feeds used to be');
  ok(!/feed|nahrung/i.test(txt(head)),
     `a column heading still says feeding: "${txt(head)}"`);

  /* ONE VOCABULARY ACROSS BOTH SURFACES. A player with the A4 board on the
   * table and this open on a phone should be reading the same shapes: a meld
   * is a fan of that many cards, a rank cap is a card's index corner, moves
   * are a number and a stride, and the tier name reaches across to the reserve
   * it governs. Drift here is two boards teaching two games. */
  E.BANDS.forEach(([name, , meld, , , , cap], j) => {
    const row = body[j];
    const cards = row ? row.querySelectorAll('.mlim .meldfan i').length : -1;
    ok(cards === meld,
       `${name} may play ${meld} cards and its fan draws ${cards}`);
    const top = row && row.querySelector('.mlim .meldfan i:last-child b');
    ok(top && txt(top) === String(meld),
       `${name}'s fan does not carry ${meld} on its top card`);
    const corner = row && row.querySelector('.capcol .rankix b');
    ok(corner && txt(corner) === String(cap),
       `${name} buys up to ${cap}; its rank corner shows "${corner && txt(corner)}"`);
    ok(row && row.querySelector('.mv .movestride svg'),
       `${name} has no stride arrow beside its move count`);
    ok(row && row.querySelector('.tname .lead'),
       `${name} does not reach across to its own reserve row`);
  });

  /* ...AND EVERY CELL HAS TO SURVIVE THE CASSCADE.
   *
   * The name check above is the cause; this is the symptom, and it is worth
   * testing separately because the next collision will have a different cause.
   * "The player board has parts missing" was reported while every assertion
   * above passed: the markup was correct and complete, and the paint deleted
   * it. `.cap` meant three things - a label on a map tile, a floating caption
   * for a coin, and this column - and the caption's `position:absolute;
   * opacity:0` won, so BUY UP TO was rendered at zero opacity, out of flow.
   *
   * jsdom resolves the cascade, so the board can be asked what it actually
   * looks like rather than what it contains. */
  {
    const gone = [];
    d.querySelectorAll('.tier-row > *').forEach((cell) => {
      const s = w.getComputedStyle(cell);
      const why = s.display === 'none' ? 'display:none'
        : s.visibility === 'hidden' ? 'visibility:hidden'
        : parseFloat(s.opacity || '1') < 0.1 ? `opacity:${s.opacity}`
        : /^(absolute|fixed)$/.test(s.position) ? `position:${s.position}`
        : null;
      if (why) gone.push(`.${cell.className.split(' ')[0]} (${why})`);
    });
    ok(!gone.length,
       `these cells are in the DOM but not on the board: ${[...new Set(gone)]}`);
  }

  /* THE TIER TABLE'S CLASS NAMES MUST BE ITS OWN.
   *
   * This is a whole-file app: one <style> block, one namespace. The rank glyph
   * was first called `.corner` - a name that already belonged to the RIVAL SEAT
   * PANELS around the map, complete with `grid-area` placements. Five rank
   * corners were duly laid out as seat panels and disappeared off the board,
   * while every DOM assertion above kept passing, because the markup was right
   * and only the paint was wrong.
   *
   * So: a class used inside the tier table may not also be worn by anything
   * outside the player board. The allowlist is for deliberately shared atoms -
   * a card face is a card face wherever it appears. */
  {
    const shared = new Set(['cf', 'mini', 'mid', 'dot', 'coin', 'want', 'sel',
                            'dead', 'btn', 'muted', 'small', 'here', 'head']);
    const inside = new Set();
    d.querySelectorAll('.tiers *').forEach((n) =>
      n.classList.forEach((c) => inside.add(c)));
    const outside = new Set();
    d.querySelectorAll('body *').forEach((n) => {
      if (n.closest('#player')) return;
      n.classList.forEach((c) => outside.add(c));
    });
    const clash = [...inside].filter((c) => outside.has(c) && !shared.has(c));
    ok(!clash.length,
       `the tier table shares class name(s) with the rest of the page: ${clash} `
       + '- one <style> block means one namespace, and the other rule wins');
  }

  /* (The bill in words used to be checked here. There is no bill under the
   * printed economy - see the block above - and the full-economy page at the
   * end of this file is where the note is still required.) */

  /* ---- 3. move limit and rank cap, per tier ----------------------------- */
  /* `\b` is no use against "1mv" — there is no word boundary between a digit
   * and a letter. The number is what matters, so pull the digits out. */
  const digits = (s) => (s.match(/\d+/g) || []).map(Number);
  E.BANDS.forEach(([name, , , , moves, , cap], j) => {
    const mv = txt(body[j] && body[j].querySelector('.mv'));
    ok(digits(mv).includes(moves),
       `${name} gets ${moves} free move(s); its row shows "${mv}"`);
    const cp = txt(body[j] && body[j].querySelector('.capcol'));
    ok(digits(cp).includes(cap),
       `${name} may buy up to rank ${cap}; its row shows "${cp}"`);
  });

  /* ---- 4. the tier you are on is marked ---------------------------------- */
  const hereIdx = body.findIndex((r) => r.classList.contains('here'));
  ok(hereIdx >= 0, 'no tier row is marked as the one you are on');

  const cols = head ? [...head.children].map((c) => txt(c)).join(' · ') : '—';
  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : `player board: ${body.length} tiers under headings [${cols}], `
      + 'every move limit and rank cap legible as a number, no feeding column '
      + 'under the printed economy, and the full economy still drawing one');
  if (fail.length) process.exit(1);
  return checkFullEconomy();
}

/* ---- 5. AND THE FULL ECONOMY STILL HAS ITS COLUMN -----------------------
 * Removing food from the printed game must not remove the OPTION. A second
 * page, started with economy: full, has to draw the feeds column, the slots
 * that carry the ascension coins, and the note that states the bill - all the
 * things checked above for their absence. Without this the lean board and a
 * deleted feature look identical to the suite. */
function checkFullEconomy() {
  const dom2 = new JSDOM(fs.readFileSync(HTML, 'utf8'),
                         { runScripts: 'dangerously', pretendToBeVisual: true });
  const w2 = dom2.window, d2 = w2.document;
  setTimeout(() => {
    const sel = d2.querySelector('#economy');
    if (sel) sel.value = 'full';
    const st = d2.querySelector('#start');
    if (st) st.click();
    setTimeout(() => {
      const f2 = [];
      const ok2 = (c, what) => { if (!c) f2.push(what); };
      ok2(w2.eval('!!(G && G.FOOD_ON)'),
          'economy:full did not reach the game, so this proves nothing');
      const rows2 = [...d2.querySelectorAll('.tier-row')]
        .filter((r) => !r.classList.contains('head'));
      ok2(!!d2.querySelector('.tiers .food'),
          'economy:full draws no FEEDS column - the option has been lost, not '
          + 'just unprinted');
      ok2(!d2.querySelector('.tiers.nofood'),
          'the tier table is marked .nofood under the full economy');
      ok2(!!d2.querySelector('.foodnote'),
          'economy:full states no refill bill in words');
      E.BANDS.forEach(([name, , , food, , ascend], j) => {
        if (!(food > 0)) return;
        const cell = rows2[j] && rows2[j].querySelector('.food');
        const slots = cell ? cell.querySelectorAll('.cslot').length : -1;
        ok2(slots === food,
            `under economy:full ${name} charges ${food} and draws ${slots} slot(s)`);
        ok2(ascend === food,
            `${name} pays ${ascend} on ascension but eats ${food} - the feed `
            + 'slots can no longer hold the ascension coins');
      });
      dom2.window.close();
      console.log(f2.length
        ? 'FAIL:\n  ' + f2.join('\n  ')
        : 'and economy:full still draws the feeds column, its ascension coins '
          + 'and the bill in words');
      process.exit(f2.length ? 1 : 0);
    }, 900);
  }, 400);
}
