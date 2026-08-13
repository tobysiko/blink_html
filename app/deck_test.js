/* A/B the base deck against the Effect D proposal, bot-only, matched seeds. */
const E = require('./engine.js');
const N = 300;
const rows = [];
for (const deck of ['abc', 'abd']) {
  for (const n of [2, 3, 4]) {
    const a = { score:[], pop:[], row:[], dom:[], rounds:[], kills:[], settle:[],
                cash:[], fort:[], starve:[], eb:[], e3:[], conqSettle:[], gold:[] };
    for (let s = 0; s < N; s++) {
      const g = E.playOut(n, s * 2654435761 % 2147483647, { deck, trickRule: 'dock' });
      const sc = g.score();
      a.score.push(...sc.map(x => x.total)); a.pop.push(...sc.map(x => x.pop));
      a.row.push(...sc.map(x => x.vrow));    a.dom.push(...sc.map(x => x.dom));
      a.gold.push(...sc.map(x => x.gold));
      const st = k => g.stats[k] || 0;
      a.rounds.push(g.round); a.kills.push(st('killed_by_attack'));
      a.settle.push(st('settle')); a.cash.push(st('cards_to_gold'));
      a.fort.push(st('fortified')); a.starve.push(st('starved_back'));
      a.eb.push(st('effect_b_used'));
      a.e3.push(deck === 'abc' ? st('effect_c_used') : st('effect_d_used'));
      a.conqSettle.push(st('conquest_settle'));
    }
    const m = x => +(x.reduce((p, q) => p + q, 0) / x.length).toFixed(2);
    rows.push({ deck, n, score: m(a.score), pop: m(a.pop), row: m(a.row), dom: m(a.dom),
                rounds: m(a.rounds), kills: m(a.kills), settles: m(a.settle),
                'cards→gold': m(a.cash), fort: m(a.fort), starved: m(a.starve),
                'B used': m(a.eb), 'C/D used': m(a.e3),
                'taken by D': m(a.conqSettle), 'gold left': m(a.gold) });
  }
}
console.table(rows);
