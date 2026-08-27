/* Is "two cards of the terrain's suit" a comparable price to 1 or 2 gold?
 *
 * The proposal: attacking Forest needs two Forest cards from your meld (the
 * HIGHER rank is the attack value); attacking Mountain needs two Mountain cards
 * (the LOWER rank counts). That replaces the flat 1 / 2 gold price.
 *
 * The thing to measure is not what a card is worth. It is whether the meld you
 * actually played CONTAINS two of that suit — because a meld is an unbroken run
 * of ranks with suits irrelevant, and it starts at two cards long. A price you
 * usually cannot pay is not a price, it is a prohibition.
 *
 *   node app/combatcost.js
 */
const E = require('./engine.js');
const N = Number(process.env.N) || 300;

const SUITS = ['plains', 'forest', 'ocean', 'mountain'];

/* Capture every meld as it is about to be spent on the map. */
const melds = [];
const goldAt = [];
const origPlace = E.Game.prototype._place;
E.Game.prototype._place = function* (p, cards) {
  melds.push({ n: cards.length, suits: cards.map((c) => c.s), ranks: cards.map((c) => c.r) });
  goldAt.push(p.gold);
  return yield* origPlace.call(this, p, cards);
};

for (const n of [2, 3, 4]) {
  melds.length = 0; goldAt.length = 0;
  for (let s = 0; s < N; s++) E.playOut(n, (s * 2654435761) % 2147483647, {});

  const total = melds.length;
  const sizes = {};
  for (const m of melds) sizes[m.n] = (sizes[m.n] || 0) + 1;
  const pct = (x) => (100 * x / total).toFixed(0) + '%';

  console.log(`\n${n} players — ${total} melds spent across ${N} games`);
  console.log('  meld size  : ' + Object.keys(sizes).sort()
    .map((k) => `${k}:${pct(sizes[k])}`).join('  '));

  /* Can this meld pay a two-same-suit price? */
  for (const suit of ['forest', 'mountain']) {
    const has1 = melds.filter((m) => m.suits.filter((s) => s === suit).length >= 1).length;
    const has2 = melds.filter((m) => m.suits.filter((s) => s === suit).length >= 2).length;
    console.log(`  ${suit.padEnd(9)}: one card ${pct(has1)}   TWO cards ${pct(has2)}`);
  }

  /* And how often could they simply have paid the gold instead? */
  const rich1 = goldAt.filter((g) => g >= 1).length;
  const rich2 = goldAt.filter((g) => g >= 2).length;
  console.log(`  gold in hand at the start of the map turn: >=1 ${pct(rich1)}   >=2 ${pct(rich2)}`);

  /* If you DO hold two of a suit, what does lower-vs-higher cost you? */
  for (const suit of ['forest', 'mountain']) {
    const pairs = melds
      .map((m) => m.ranks.filter((_, i) => m.suits[i] === suit))
      .filter((rs) => rs.length >= 2);
    if (!pairs.length) { console.log(`  ${suit}: no pairs to measure`); continue; }
    const hi = pairs.map((rs) => Math.max(...rs));
    const lo = pairs.map((rs) => Math.min(...rs));
    const avg = (xs) => (xs.reduce((a, b) => a + b, 0) / xs.length).toFixed(1);
    console.log(`  ${suit.padEnd(9)}: when you hold two, higher ${avg(hi)} / lower ${avg(lo)}`
      + `  — the rule costs ${(avg(hi) - avg(lo)).toFixed(1)} rank`);
  }
}
