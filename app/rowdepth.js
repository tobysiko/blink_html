/* How deep does the victory row actually get, and what stops it?
 *
 * Slot perks are only worth designing if the slots are reached. The row is
 * rank-sorted and pushed RIGHT, so slot 5 fills with your first retired card
 * and slot 1 only exists once you hold five. That makes "which slot" and "how
 * many cards" the same question — and this answers it.
 *
 *   node app/rowdepth.js
 */
const E = require('./engine.js');
const N = Number(process.env.N) || 400;

console.log(`victory row depth over ${N} games per player count\n`);
for (const n of [2, 3, 4]) {
  const dist = [0, 0, 0, 0, 0, 0];
  const stat = {};
  let seats = 0, gold = 0, hand = 0, rounds = 0;
  for (let s = 0; s < N; s++) {
    const g = E.playOut(n, (s * 2654435761) % 2147483647, {});
    rounds += g.round;
    for (const k in g.stats || {}) stat[k] = (stat[k] || 0) + g.stats[k];
    for (const p of g.P) {
      dist[p.vrow.length] += 1; seats++; gold += p.gold; hand += p.hand.length;
    }
  }
  const pct = (x) => (100 * x / seats).toFixed(0).padStart(3) + '%';
  const atLeast = (k) => dist.slice(k).reduce((a, b) => a + b, 0);
  console.log(`${n} players — ${(rounds / N).toFixed(1)} rounds avg`);
  console.log('  final depth :  ' + dist.map((v, i) => `${i}:${pct(v)}`).join('  '));
  /* Slot 5 needs 1 card, slot 4 needs 2 ... slot 1 needs 5. */
  console.log('  slot reached:  ' +
    [5, 4, 3, 2, 1].map((slot, i) => `s${slot} ${pct(atLeast(i + 1))}`).join('  '));
  /* If gold were the brake, players would end broke. They do not — they end
   * with gold in hand and cards they would not give up. The row is shallow
   * because RETIRING A CARD costs more than the row pays. */
  console.log(`  end gold ${(gold / seats).toFixed(1)}   end hand ` +
              `${(hand / seats).toFixed(1)}   research declined ` +
              `${((stat.research_declined_blind || 0) / N / n).toFixed(2)}/player\n`);
}
