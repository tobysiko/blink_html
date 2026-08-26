/* Does the victory row price its own perks?
 *
 * The claim: spending a victory card on A/B/C removes it from the row, so a
 * player holding perks they like will spend fewer effects to keep the row deep
 * enough to run them. If that is true, strong perks pay for themselves and
 * tiering them by slot is solving a problem the game already solves.
 *
 * This measures the trade WITHOUT perks in play, which is the honest baseline:
 * how often does an effect spend actually cross a perk threshold?
 *
 *   node app/perkcost.js
 */
const E = require('./engine.js');
const N = Number(process.env.N) || 300;

/* Every removal from the row goes through Array.splice on p.vrow, so wrap the
 * player rather than nine call sites — this cannot miss one. */
function watch(g, tally) {
  for (const p of g.P) {
    const row = p.vrow;
    row.splice = function (...args) {
      const before = this.length;
      const out = Array.prototype.splice.apply(this, args);
      const after = this.length;
      if (after < before) {
        tally.spends += 1;
        /* Which thresholds did this spend drop the player below? */
        for (const needs of [2, 3, 4, 5])
          if (before >= needs && after < needs) tally.crossed[needs] += 1;
      }
      return out;
    };
  }
}

console.log('effect spends from the victory row, and what they would cost a perk\n');
for (const n of [2, 3, 4]) {
  const tally = { spends: 0, crossed: { 2: 0, 3: 0, 4: 0, 5: 0 } };
  let seats = 0;
  for (let s = 0; s < N; s++) {
    /* playOut builds its own Game, so drive one by hand — same loop it uses. */
    const g = new E.Game(n, (s * 2654435761) % 2147483647, { humans: [] });
    watch(g, tally);
    let guard = 0;
    while (!g.finished() && guard++ < 200) {
      const it = g.playRound();
      let r = it.next();
      while (!r.done) r = it.next(null);
    }
    seats += g.P.length;
  }
  const per = (x) => (x / seats).toFixed(2);
  console.log(`${n}p  effects spent ${per(tally.spends)}/player`);
  console.log('    of those, spends that switched a perk OFF, by threshold:');
  console.log(`      needs 2 (slot 4): ${per(tally.crossed[2])}   `
    + `needs 3 (slot 3): ${per(tally.crossed[3])}   `
    + `needs 4 (slot 2): ${per(tally.crossed[4])}   `
    + `needs 5 (slot 1): ${per(tally.crossed[5])}\n`);
}
