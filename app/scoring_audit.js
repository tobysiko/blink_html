/* The three endgame questions where the app and the rulebook differ. */
const E = require('./engine.js');
const N = 300;
const run = (opts, n) => {
  const a = { score:[], pop:[], row:[], dom:[], rounds:[], trig:{} };
  for (let s = 0; s < N; s++) {
    const g = E.playOut(n, s * 2654435761 % 2147483647, Object.assign({ trickRule:'dock' }, opts));
    const sc = g.score();
    a.score.push(...sc.map(x=>x.total)); a.pop.push(...sc.map(x=>x.pop));
    a.row.push(...sc.map(x=>x.row ?? x.vrow)); a.dom.push(...sc.map(x=>x.dom));
    a.rounds.push(g.round);
    a.trig[g.endedOn] = (a.trig[g.endedOn]||0)+1;
  }
  const m = x => +(x.reduce((p,q)=>p+q,0)/x.length).toFixed(2);
  return { score:m(a.score), pop:m(a.pop), row:m(a.row), dom:m(a.dom),
           rounds:m(a.rounds),
           'ended on last unit %': Math.round(100*(a.trig['last unit placed']||0)/N) };
};
const rows = [];
for (const n of [2,3,4]) {
  rows.push(Object.assign({ n, variant:'app now (9-card market, area majority)' }, run({}, n)));
  rows.push(Object.assign({ n, variant:'rulebook market: 6 cards' }, run({ gridSize:6 }, n)));
  rows.push(Object.assign({ n, variant:'rulebook majority: most units, connected' }, run({ majority:'units' }, n)));
  rows.push(Object.assign({ n, variant:'both rulebook readings' }, run({ gridSize:6, majority:'units' }, n)));
}
console.table(rows);
