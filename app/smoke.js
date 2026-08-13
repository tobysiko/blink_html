const E = require('./engine.js');
for (const n of [2,3,4]) {
  const scores=[], rounds=[], pops=[], vrows=[], doms=[], kills=[], starv=[];
  for (let s=1; s<=60; s++) {
    const g = E.playOut(n, s*7919);
    // invariants
    for (const p of g.P) {
      const onmap = [...g.m.tiles.values()].reduce((a,t)=>a+t.units.filter(u=>u===p.i).length,0);
      const res = p.reserve.reduce((a,b)=>a+b,0);
      if (res+onmap !== 20) throw new Error(`seat ${p.i}: ${res}+${onmap} units, n=${n} seed=${s}`);
      if (p.hand.length+p.discard.length+p.played.length > 10) throw new Error('over ten cards');
      if (p.vrow.length > 5) throw new Error('row over five');
    }
    // tile conservation
    const tc = {}; for (const t of E.TER) tc[t]=g.m.supply[t];
    for (const t of g.m.tiles.values()) tc[t.terrain]++;
    for (const t of E.TER) if (tc[t]!==15) throw new Error(`tiles ${t}=${tc[t]}`);
    // map connected + touch-two
    const keys=new Set(g.m.tiles.keys());
    const first=keys.values().next().value; const seen=new Set([first]); const st=[first];
    while(st.length){const c=st.pop(); const [x,y]=E.unK(c);
      for(const u of E.nbrKeys(x,y)) if(keys.has(u)&&!seen.has(u)){seen.add(u);st.push(u);} }
    if (seen.size!==keys.size) throw new Error('map not connected');
    const sc = g.score();
    scores.push(...sc.map(x=>x.total));
    pops.push(...sc.map(x=>x.pop));
    vrows.push(...sc.map(x=>x.vrow));
    doms.push(...sc.map(x=>x.dom));
    rounds.push(g.round);
    kills.push(g.stats.killed_by_attack||0);
    starv.push(g.stats.starved_back||0);
  }
  const m = a => (a.reduce((x,y)=>x+y,0)/a.length).toFixed(2);
  console.log(`${n}p  score ${m(scores)}  pop ${m(pops)}  row ${m(vrows)}  dom ${m(doms)}  rounds ${m(rounds)}  kills ${m(kills)}  starved ${m(starv)}`);
}
