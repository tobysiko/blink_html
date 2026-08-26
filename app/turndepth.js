/* Row depth at the START OF EVERY TURN, not just at recycles.
 * If perks refreshed per turn instead of per recycle, this is what each slot
 * would be worth — and it decides whether the deep slots are playable. */
const E = require('./engine.js');
const N = 300;
const orig = E.Game.prototype._place;
let seen = [];
E.Game.prototype._place = function* (p, cards) {
  seen.push(p.vrow.length);
  return yield* orig.call(this, p, cards);
};
console.log('row depth at the start of each map turn\n');
console.log('  n    turns/player   turns a perk could fire, slot 4 / 3 / 2 / 1');
for (const n of [2, 3, 4]) {
  seen = [];
  let seats = 0;
  for (let s = 0; s < N; s++) {
    const g = E.playOut(n, (s * 2654435761) % 2147483647, {});
    seats += g.P.length;
  }
  const per = (needs) => (seen.filter((d) => d >= needs).length / seats).toFixed(2);
  console.log(`  ${n}p       ${(seen.length / seats).toFixed(2)}` +
    `           ${per(2)} / ${per(3)} / ${per(4)} / ${per(5)}`);
}
