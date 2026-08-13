/* A/B the two readings of the victory row (§13), on matched seeds. */
const E = require('./engine.js');
const N = 300;
const rows = [];
for (const rule of ['card+centre', 'centre']) {
  for (const n of [2, 3, 4]) {
    E.setVrowRule(rule);
    const sc = [], row = [], pop = [], rounds = [], upg = [], cards = [], ec = [];
    for (let s = 0; s < N; s++) {
      const g = E.playOut(n, s * 2654435761 % 2147483647, { trickRule: 'bonus' });
      const t = g.score();
      sc.push(...t.map(x => x.total)); row.push(...t.map(x => x.vrow));
      pop.push(...t.map(x => x.pop));
      rounds.push(g.round); upg.push(g.stats.upgrades || 0);
      ec.push(g.stats.effect_c_used || 0);
      cards.push(...g.P.map(p => p.vrow.length));
    }
    const m = a => +(a.reduce((x, y) => x + y, 0) / a.length).toFixed(2);
    rows.push({ rule, n, score: m(sc), row: m(row), 'row%': +(100 * m(row) / m(sc)).toFixed(0),
                cardsInRow: m(cards), pop: m(pop), rounds: m(rounds),
                upgrades: m(upg), effectC: m(ec) });
  }
}
console.table(rows);
