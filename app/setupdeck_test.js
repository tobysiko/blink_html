/* ONE DECK, EVERY PLAYER COUNT, AND EVERY CARD STILL IN PLAY.
 *
 * The starting deck used to be cut to fit the table — ranks 6-10 at two
 * players, 3-10 at three, with a hand-tuned patch removing two 3s and two 18s
 * to keep the suits even. Two costs: the rank caps printed on the board are
 * decoration in a game whose market stops at 15, and it was a setup step, with
 * a table, that had to be got right before a card was dealt.
 *
 * Now ranks 1..DECK_SPLIT are the starting deck and the rest the advanced one
 * at every count, and what nobody drafted becomes the shared pile rather than
 * leaving the game. This file is the accounting: 80 cards go in, 80 cards are
 * somewhere, and the only thing that ever removes one is the victory row.
 *
 * THE SPLIT IS READ FROM THE ENGINE, never written down here. v0.26 moved it
 * from 10 to 11 and this file failed nine ways on a change that had broken
 * nothing - it was asserting the constant rather than the property. What it
 * means to assert is that the two decks PARTITION the eighty cards: nothing
 * above the split is dealt, nothing at or below it is in the market, and the
 * shared pile is whatever the draft did not take.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

const SPLIT = E.DECK_SPLIT;          // highest rank in the starting deck
const START = 4 * SPLIT;             // four suits of each of those ranks

/* By IDENTITY, not by count: `tableau` and `played` are two views of the same
   cards mid-trick, so adding lengths counts some of them twice. A Set also
   makes the stronger statement - that no card is in two places at once. */
const where = (g) => {
  const seen = new Set();
  for (const p of g.P)
    for (const c of [...p.hand, ...p.discard, ...p.vrow,
                     ...(p.tableau || []), ...(p.played || [])]) seen.add(c);
  for (const c of [...g.deck, ...g.pile, ...g.grid.flat(),
                   ...(g.removed || [])]) seen.add(c);
  return [...seen];
};

for (const n of [2, 3, 4]) {
  const g = new E.Game(n, 77, { humans: [] });

  const all = where(g);
  ok(all.length === 80, `${n}p: ${all.length} cards at setup, not 80`);

  /* Four suits of every rank, at every count, whatever the split. */
  const ranks = {};
  for (const c of all) ranks[c.r] = (ranks[c.r] || 0) + 1;
  for (let r = 1; r <= 20; r++)
    ok(ranks[r] === 4, `${n}p: rank ${r} appears ${ranks[r] || 0} times, not 4`);

  for (const p of g.P) ok(p.hand.length === 10, `${n}p: a hand holds ${p.hand.length}`);
  ok(g.deck.concat(g.grid.flat()).every((c) => c.r > SPLIT),
     `${n}p: a starting-deck card is in the market`);
  ok(g.P.every((p) => p.hand.every((c) => c.r <= SPLIT)),
     `${n}p: an advanced card was dealt to a hand`);

  /* What the draft never touched is the shared pile, not the bin. */
  ok(g.pile.length === START - n * 10,
     `${n}p: shared pile holds ${g.pile.length}, expected ${START - n * 10}`);
  ok(g.pile.every((c) => c.r <= SPLIT),
     `${n}p: an advanced card was left in the shared pile`);
}

/* THE PILE IS LIVE AT EVERY COUNT, which is the whole reason v0.26 moved the
   split. Under 1-10 four players drafted the starting deck dry and the shared
   pile was empty until somebody recycled into it — so trade, the rule that
   reads two cards off the top of it, did nothing for the first third of a
   four-player game. At 1-11 the leftover is 44 - 10n: 24, 14, 4. */
for (const n of [2, 3, 4])
  ok(new E.Game(n, 5, { humans: [] }).pile.length === START - n * 10,
     `${n}p: the shared pile is not the ${START - n * 10} cards the draft left over`);

/* Play them out: the accounting has to survive the game, and the ONLY cards
   that may go missing are the ones spent out of a victory row. */
for (const n of [2, 3, 4]) {
  const g = E.playOut(n, 300 + n, { humans: [] });
  const all = where(g);
  ok(all.length === 80,
     `${n}p: ${all.length} cards at the end of a full game, not 80 ` +
     `(removed ${(g.removed || []).length})`);
}

/* ONE END TRIGGER. A thinning market used to end the game as well and almost
   never got there first; it is off, and kept only so it can be measured. */
{
  const why = {};
  for (let s = 0; s < 40; s++) {
    const g = E.playOut(3, 900 + s, { humans: [] });
    ok(g.finished(), `a 3-player game did not end (seed ${900 + s})`);
    why[g.endedOn] = (why[g.endedOn] || 0) + 1;
  }
  ok(!why['end.marketThin'],
     `the market still ends games: ${JSON.stringify(why)}`);
  ok(why['end.lastUnit'] === 40,
     `not every game ended on the last unit: ${JSON.stringify(why)}`);
  const back = E.playOut(4, 42, { humans: [], endOnMarket: true });
  ok(back.finished(), 'the old two-trigger rule no longer finishes a game');
}

if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
console.log(`setup: ranks 1-${SPLIT} and ${SPLIT + 1}-20 at 2, 3 and 4 players, all 80 cards in play, `
  + 'the undrafted remainder in the shared pile, and the last unit the only end');
