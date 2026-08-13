/* A/B the tier table where the sim and the rulebook disagree (§04). */
const E = require('./engine.js');
const N = 300;
const rows = [];
for (const [lab, cfg] of [
  ['sim (as now)',        { units: 'sim',      caps: 'sim' }],
  ['rulebook units',      { units: 'rulebook', caps: 'sim' }],
  ['rulebook caps',       { units: 'sim',      caps: 'rulebook' }],
  ['rulebook both',       { units: 'rulebook', caps: 'rulebook' }]]) {
  for (const n of [3]) {
    E.setTiers(cfg);
    const sc=[],row=[],pop=[],rounds=[],upg=[],blocked=[],declined=[],meld=[],topTier=[];
    for (let s = 0; s < N; s++) {
      const g = E.playOut(n, s * 2654435761 % 2147483647, { trickRule: 'bonus' });
      const t = g.score();
      sc.push(...t.map(x => x.total)); row.push(...t.map(x => x.vrow));
      pop.push(...t.map(x => x.pop));
      rounds.push(g.round);
      upg.push(g.stats.upgrades || 0);
      blocked.push(g.stats.upgrade_blocked_by_cap || 0);
      declined.push(g.stats.research_declined_blind || 0);
      // mean meld size actually played
      let tot = 0, cnt = 0;
      for (const k in g.stats) if (k.startsWith('meld_')) {
        const sz = +k.slice(5); tot += sz * g.stats[k]; cnt += g.stats[k];
      }
      meld.push(tot / cnt);
      topTier.push(...g.P.map(p => p.reached));
    }
    const m = a => +(a.reduce((x, y) => x + y, 0) / a.length).toFixed(2);
    rows.push({ variant: lab, score: m(sc), row: m(row), pop: m(pop), rounds: m(rounds),
                meldSize: m(meld), upgrades: m(upg),
                'buys blocked by cap': m(blocked), 'research declined': m(declined),
                'top tier reached': m(topTier) });
  }
}
console.log('3 players, 300 games each, trick rule "bonus"');
console.table(rows);
