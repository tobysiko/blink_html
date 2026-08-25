const E = require('./engine.js');
const N = 300;
for (const n of [2, 3, 4]) {
  let seats = 0, gold = 0, res = 0, rowlen = 0, hand = 0;
  const stat = {};
  for (let s = 0; s < N; s++) {
    const g = E.playOut(n, (s * 40503) % 2147483647, {});
    for (const k in g.stats || {}) stat[k] = (stat[k] || 0) + g.stats[k];
    for (const p of g.P) {
      seats++; gold += p.gold; rowlen += p.vrow.length; hand += p.hand.length;
      res += p.vrow.length;            // one row card per research
    }
  }
  console.log(`${n}p  avg end gold ${(gold/seats).toFixed(1)}` +
              `   researches/player ${(res/seats).toFixed(2)}` +
              `   end hand ${(hand/seats).toFixed(1)}`);
  const keys = Object.keys(stat).filter(k => /research|blocked|buy/i.test(k));
  if (keys.length) console.log('     ' + keys.map(k => `${k}=${(stat[k]/N/n).toFixed(2)}`).join('  '));
}
