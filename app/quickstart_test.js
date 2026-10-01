/* QUICK START: TWO UNITS EACH (optional rule, rulebook §03).
 *
 * Everyone places two units on their homeland instead of one. On the printed
 * 2-3-5-5-5 board that empties Tribe, so the first card phase is played at
 * Settlement. Checked on both starting maps, and that the default is still the
 * printed one-unit start.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

for (const layout of ['block', 'homelands']) {
  for (const n of [2, 3, 4]) {
    const g = new E.Game(n, 40 + n, { humans: [], startUnits: 2, startLayout: layout });
    if (layout === 'homelands') {                   // homelands are laid in round one
      const it = g.playRound(); it.next();
    }
    for (const p of g.P) {
      const onMap = [...g.m.tiles.values()].reduce((a, t) => a + t.units.filter((u) => u === p.i).length, 0);
      if (layout === 'block') {
        ok(onMap === 2, `${layout}/${n}p seat ${p.i}: ${onMap} units on the map, expected 2`);
        const home = g.m.tiles.get(g.m.starts[p.i].join(','));
        ok(home && home.units.filter((u) => u === p.i).length === 2,
           `${layout}/${n}p seat ${p.i}: the two units are not both on the homeland Plains`);
        ok(p.gold === 0, `${layout}/${n}p seat ${p.i}: starts with ${p.gold} gold`);
      }
      ok(p.reserve[0] === 0 || layout === 'homelands' && p.band() >= 1,
         `${layout}/${n}p seat ${p.i}: Tribe still holds ${p.reserve[0]}`);
      ok(p.band() >= 1, `${layout}/${n}p seat ${p.i}: not at Settlement`);
      ok(p.reached >= 1, `${layout}/${n}p seat ${p.i}: leaving Tribe at setup was left to pay later`);
    }
    if (layout === 'block')
      ok(g.P.every((p) => p.meldLimit() === 3 && p.rankCap() === 14),
         `${layout}/${n}p: the first card phase is not at melds of 3 / research 14`);
  }
}
{
  const g = new E.Game(3, 1, { humans: [] });
  ok(g.START_UNITS === 1 && g.P.every((p) => p.band() === 0 && p.meldLimit() === 2),
     'the default is no longer the printed one-unit start');
}
{
  const g = E.playOut(3, 9, { startUnits: 2 });
  ok(g.finished(), 'a quick-start game did not finish');
}
if (fail.length) { console.error(fail.join('\n')); process.exit(1); }
console.log('quick start: two units on the homeland, Settlement from the first card, both maps; default unchanged');
