const E = require('./engine.js');
const RULE = process.argv[2] || 'bonus';   // 'bonus' matches the Python sim
const N = 300;
const out = {};
for (const n of [2,3,4]) {
  const a = {score:[],pop:[],row:[],dom:[],rounds:[],kills:[],settle:[],upg:[],cash:[],
             fort:[],moves:[],colony:[],ec:[],ea:[],starve:[],tiles:[]};
  for (let s = 0; s < N; s++) {
    const g = E.playOut(n, s*2654435761 % 2147483647, { trickRule: RULE });
    const sc = g.score();
    a.score.push(...sc.map(x=>x.total)); a.pop.push(...sc.map(x=>x.pop));
    a.row.push(...sc.map(x=>x.vrow));    a.dom.push(...sc.map(x=>x.dom));
    a.rounds.push(g.round); a.tiles.push(g.m.tiles.size);
    const st=k=>g.stats[k]||0;
    a.kills.push(st('killed_by_attack')); a.settle.push(st('settle'));
    a.upg.push(st('upgrades')); a.cash.push(st('cards_to_gold'));
    a.fort.push(st('fortified')); a.moves.push(st('free_move'));
    a.colony.push(st('colony_tile')); a.ec.push(st('effect_c_used'));
    a.ea.push(st('effect_a_used')); a.starve.push(st('starved_back'));
  }
  out[n]=a;
}
const m=x=>(x.reduce((p,q)=>p+q,0)/x.length);
const keys=['score','pop','row','dom','rounds','tiles','settle','kills','upg','cash','moves','colony','ea','ec','fort','starve'];
console.log('JS ' + JSON.stringify(Object.fromEntries(
  [2,3,4].map(n=>[n, Object.fromEntries(keys.map(k=>[k, +m(out[n][k]).toFixed(2)]))]))));
