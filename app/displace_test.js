/* DISPLACEMENT: a beaten unit falls back, it does not evaporate.
 *
 * The printed rule sends it home to the reserve, which quietly refills the one
 * thing that ends the game. `loss: "displace"` has it retreat to a
 * NEIGHBOURING tile its owner holds that has room — staying on the map and
 * staying theirs — and only die when there is nowhere beside it to go.
 *
 * Two consequences fall out of the printed capacities with no new rule, and
 * both are asserted here because they are the whole character of the change:
 * a retreat can only ever reach plains or forest, and a detached unit dies.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

const HOLDS = { plains: 3, forest: 2, ocean: 1, mountain: 1 };

/* ---- the printed rule is untouched ---- */
{
  const g = E.playOut(4, 11, { humans: [] });
  ok((g.stats.displaced || 0) === 0,
     'a unit was displaced in a game playing the printed rule');
  ok((g.stats.killed_by_attack || 0) > 0, 'the printed rule stopped taking units');
}

/* ---- displacement moves units instead of banking them ---- */
{
  let moved = 0, killed = 0, plainsOrForest = 0, elsewhere = 0;
  for (let s = 0; s < 40; s++) {
    const g = E.playOut(4, 700 + s, { humans: [], loss: 'displace' });
    moved += (g.stats.displaced || 0);
    killed += (g.stats.killed_by_attack || 0);
    /* Where retreats actually landed: only tiles that can hold more than one
       unit can ever take one, and only plains and forest can. */
    for (const [, t] of g.m.tiles)
      if (t.units.length > 1) { plainsOrForest += ['plains', 'forest'].includes(t.terrain) ? 1 : 0;
                                elsewhere += ['ocean', 'mountain'].includes(t.terrain) ? 1 : 0; }
  }
  ok(moved > 0, 'no unit ever retreated under displacement');
  ok(elsewhere === 0,
     `${elsewhere} ocean/mountain tiles ended up holding more than one unit`);
  ok(plainsOrForest > 0, 'no tile ever held a retreating unit');
  ok(killed > 0, 'nothing ever died — the fallback never fired in 40 games');
}

/* ---- a retreat only ever goes NEXT DOOR, and only into room ---- */
{
  const g = new E.Game(3, 5, { humans: [], loss: 'displace' });
  /* Stage it: a defender on a mountain with one plains neighbour of their own
     that has room, and a second owned tile far away that must NOT be used. */
  const tiles = [...g.m.tiles.values()];
  const target = tiles.find((t) => t.owner !== null && t.units.length);
  const victim = target.owner;
  const near = target.neighbours().filter((t) => t.terrain !== 'ocean');
  ok(near.length > 0, 'the staged tile has no land neighbour to retreat to');
  const refuge = near[0];
  refuge.owner = victim; refuge.units = [victim];
  refuge.terrain = 'plains';              // room for three
  const before = refuge.units.length;
  const attacker = g.P[(victim + 1) % g.n];
  const it = g._takeUnit(attacker, target.key);
  let r = it.next();
  while (!r.done) r = it.next(r.value && r.value.options ? r.value.options[0] : null);
  ok(refuge.units.length === before + 1,
     `the unit did not fall back next door (refuge holds ${refuge.units.length})`);
  ok(refuge.units.every((u) => u === victim), 'the retreat changed hands');
}

/* ---- a detached unit has nowhere to go, so it dies ---- */
{
  const g = new E.Game(3, 9, { humans: [], loss: 'displace' });
  const tiles = [...g.m.tiles.values()];
  const target = tiles.find((t) => t.owner !== null && t.units.length);
  const victim = target.owner;
  for (const t of target.neighbours()) if (t.owner === victim) t.owner = null, t.units = [];
  const reserve0 = g.P[victim].reserve.reduce((a, b) => a + b, 0);
  const attacker = g.P[(victim + 1) % g.n];
  const it = g._takeUnit(attacker, target.key);
  let r = it.next();
  while (!r.done) r = it.next(r.value && r.value.options ? r.value.options[0] : null);
  const reserve1 = g.P[victim].reserve.reduce((a, b) => a + b, 0);
  ok(reserve1 === reserve0 + 1,
     'a detached unit did not go home when it had nowhere to fall back to');
}

/* ---- and a full hinterland is the same case ---- */
{
  const g = new E.Game(3, 13, { humans: [], loss: 'displace' });
  const tiles = [...g.m.tiles.values()];
  const target = tiles.find((t) => t.owner !== null && t.units.length);
  const victim = target.owner;
  for (const t of target.neighbours()) {
    t.owner = victim;
    t.units = new Array(HOLDS[t.terrain]).fill(victim);   // packed to capacity
  }
  const reserve0 = g.P[victim].reserve.reduce((a, b) => a + b, 0);
  const it = g._takeUnit(g.P[(victim + 1) % g.n], target.key);
  let r = it.next();
  while (!r.done) r = it.next(r.value && r.value.options ? r.value.options[0] : null);
  ok(g.P[victim].reserve.reduce((a, b) => a + b, 0) === reserve0 + 1,
     'a unit squeezed into a neighbour that was already full');
}

/* ---- the defender is the one asked ---- */
{
  const g = new E.Game(3, 21, { humans: [1], loss: 'displace' });
  const tiles = [...g.m.tiles.values()];
  const target = tiles.find((t) => t.owner === 1 && t.units.length)
    || tiles.find((t) => t.owner !== null && t.units.length);
  if (target.owner !== 1) { target.owner = 1; target.units = [1]; }
  const near = target.neighbours().filter((t) => t.terrain !== 'ocean').slice(0, 2);
  for (const t of near) { t.owner = 1; t.units = [1]; t.terrain = 'plains'; }
  const it = g._takeUnit(g.P[0], target.key);
  const r = it.next();
  if (near.length > 1) {
    ok(!r.done && r.value && r.value.type === 'retreat',
       `the defender was not asked where to fall back (${r.value && r.value.type})`);
    ok(r.value.seat === 1, `seat ${r.value.seat} was asked, not the defender`);
    ok(r.value.options.every((k) => near.some((t) => t.key === k)),
       'a retreat was offered somewhere that is not next door');
  }
}

/* ---- and a full game still finishes ---- */
{
  for (const n of [2, 3, 4]) {
    const g = E.playOut(n, 33 + n, { humans: [], loss: 'displace' });
    ok(g.finished(), `a ${n}-player displacement game did not end`);
  }
}

if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
console.log('displacement: units fall back next door and stay on the map; only plains and '
  + 'forest can take one; a detached or hemmed-in unit goes home; the defender chooses');
