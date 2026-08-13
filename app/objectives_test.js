/* Passive completion rate per objective — the measurement the module says it
 * needs re-doing: it was balanced against v0.20 pattern placement. Bots do NOT
 * steer toward their objective, so this is how often a chain appears by
 * ordinary expansion, exactly as the module's own figures were taken. */
const E = require('./engine.js');
const N = 500;
const hits = {}, seen = {};
for (const o of E.OBJECTIVES) { hits[o.name] = 0; seen[o.name] = 0; }
const perN = {};
for (const n of [2, 3, 4]) {
  let done = 0, dealt = 0;
  for (let s = 0; s < N; s++) {
    const g = E.playOut(n, s * 2654435761 % 2147483647,
                        { trickRule: 'dock', objectives: 'off' });
    // score every objective against every finished map: the passive rate
    for (const p of g.P) for (const o of E.OBJECTIVES) {
      seen[o.name]++; dealt++;
      if (g.objectiveDone(p.i, o)) { hits[o.name]++; done++; }
    }
  }
  perN[n] = +(100 * done / dealt).toFixed(1);
}
const rows = E.OBJECTIVES.map((o) => ({
  objective: o.name,
  chain: `${o.a[0].toUpperCase()} – ${o.mid[0].toUpperCase()} – ${o.b[0].toUpperCase()}`,
  'completed %': +(100 * hits[o.name] / seen[o.name]).toFixed(1),
})).sort((a, b) => b['completed %'] - a['completed %']);
console.log(`passive completion, ${N} games at each of 2/3/4 players`);
console.table(rows);
console.log('overall by player count:', perN);
