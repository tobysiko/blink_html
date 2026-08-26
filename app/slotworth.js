/* If players assign perks to slots freely, what is each slot WORTH?
 *
 * A perk only fires while its slot holds a card, and it refreshes on the
 * recycle — so the value of a slot is the number of recycles that happen
 * while the row is already that deep. Measure it by watching every recycle.
 */
const E = require('./engine.js');
const N = 300;
const orig = E.Game.prototype._recycle;
let log = [];
E.Game.prototype._recycle = function* (p) {
  log.push(p.vrow.length);            // depth at the moment the token flips
  return yield* orig.call(this, p);
};
console.log('recycles per player that happen at each row depth\n');
console.log('  n   recycles/player   usable by a perk in slot 4 / 3 / 2 / 1');
for (const n of [2, 3, 4]) {
  log = [];
  let seats = 0;
  for (let s = 0; s < N; s++) {
    const g = E.playOut(n, (s * 2654435761) % 2147483647, { perks: true });
    seats += g.P.length;
  }
  const per = (needs) => (log.filter((d) => d >= needs).length / seats).toFixed(2);
  console.log(`  ${n}p       ${(log.length / seats).toFixed(2)}` +
    `              ${per(2)} / ${per(3)} / ${per(4)} / ${per(5)}`);
}
