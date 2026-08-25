/* What is an extra meld shape worth?
 *
 * FINDING: nothing measurable. Across 300 games at each count, friends of 10s,
 * combination melds and both together all land within ~0.2 points of the plain
 * run, with rounds, row depth and end gold effectively unchanged.
 *
 * That result has two readings and this harness CANNOT separate them:
 *
 *   1. The bots do not hunt for these shapes. Their meld search is built around
 *      runs, so an option they never reach for cannot show up in their scores.
 *   2. The shapes genuinely cannot spike power under sum scoring. A friends
 *      pair sums to exactly 10, 20 or 30 by definition — a run of three middling
 *      cards beats 10 or 20 outright. So friends of 10s is almost never the
 *      meld that WINS a trick; it is a way to spend two unconnected cards on the
 *      map while conceding, and conceding pays a coin.
 *
 * Reading 2 is a real structural property and survives whatever the bots do,
 * which makes these shapes good candidates for a low-stakes perk: flexibility
 * rather than force. But the size of the effect on a human table is not
 * something this file can tell you. Play it.
 *
 *   node app/meldrules.js
 */
const E = require('./engine.js');
const N = Number(process.env.N) || 300;
const variants = [
  ['run only (default)', {}],
  ['friends of 10s',     { friendsOf10: true }],
  ['combination melds',  { comboMelds: true }],
  ['both',               { friendsOf10: true, comboMelds: true }],
];
for (const n of [2, 3, 4]) {
  console.log(`\n${n} players, ${N} games each`);
  console.log('  ' + 'variant'.padEnd(20) + '  score  rounds    row   gold');
  for (const [label, opts] of variants) {
    let score = 0, rounds = 0, seats = 0, row = 0, gold = 0;
    for (let s = 0; s < N; s++) {
      const g = E.playOut(n, (s * 2654435761) % 2147483647, opts);
      rounds += g.round;
      for (const p of g.P) { seats++; row += p.vrow.length; gold += p.gold; }
      for (const x of g.score()) score += x.total;
    }
    const avg = (x, d) => (x / d).toFixed(2);
    console.log('  ' + label.padEnd(20) +
      avg(score, seats).padStart(7) + ' ' + avg(rounds, N).padStart(6) + ' ' +
      avg(row, seats).padStart(6) + ' ' + avg(gold, seats).padStart(6));
  }
}
