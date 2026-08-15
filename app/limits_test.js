/* Variant: population limits that grow with your band.
 *
 * The interesting half of this rule is the one that never happens in a bot
 * game — 200 games of each player count starve exactly zero times, so the
 * cascade below is built by hand. "If starvation drops your band, your cities
 * shed the difference… those returned units refill your reserve, which can drop
 * your band again — repeat until no stack is over its limit."
 */
const E = require('./engine.js');
const fail = [];
const ok = (cond, what) => { if (!cond) fail.push(what); };

function board(spec, opts) {
  const g = new E.Game(2, 1, Object.assign({ humans: [] }, opts || {}));
  g.m.tiles.clear();
  for (const [c, r, terrain, seat, n] of spec) {
    const t = g.m._add([c, r], terrain);
    for (let i = 0; i < (n || (seat === undefined || seat === null ? 0 : 1)); i++) t.units.push(seat);
  }
  return g;
}
/* Put a seat on a given tier by emptying the tiers above it. */
function setTier(p, tier) {
  p.reserve = E.BANDS.map((b, j) => (j < tier ? 0 : b[1]));
}

// ------------------------------------------------- the limits themselves
{
  const g = board([[0, 0, 'plains', 0], [1, 0, 'forest', 1]], { growLimits: true });
  const t = g.m.tiles.get('0,0');
  for (let tier = 0; tier < E.BANDS.length; tier++) {
    setTier(g.P[0], tier);
    ok(t.capacityFor(0) === E.BAND_HOLDS[tier].plains,
       `Plains holds ${t.capacityFor(0)} at tier ${tier}, table says ${E.BAND_HOLDS[tier].plains}`);
  }
  // the limit that applies is the OWNER'S — two players may stack differently
  setTier(g.P[0], 0); setTier(g.P[1], 3);
  ok(t.capacityFor(0) === 2 && t.capacityFor(1) === 3,
     'the same Plains tile does not hold different amounts for different owners');
  // and without the variant, nothing moves
  const h = board([[0, 0, 'plains', 0]], {});
  setTier(h.P[0], 0);
  ok(h.m.tiles.get('0,0').capacityFor(0) === 3,
     'the fixed game stopped holding 3 on Plains');
}

// ------------------------------------------------------- hostile ground
{
  const top = E.BAND_HOLDS[E.BAND_HOLDS.length - 1];
  ok(top.ocean <= 2 && top.mountain <= 2,
     'Ocean or Mountain grew past 2 — "hostile ground never becomes comfortable"');
  for (let i = 1; i < E.BAND_HOLDS.length; i++)
    for (const t of E.TER)
      ok(E.BAND_HOLDS[i][t] >= E.BAND_HOLDS[i - 1][t],
         `${t} shrinks from tier ${i - 1} to ${i} — limits must climb`);
}

// --------------------------------------------------------- the cascade
/* A reachable state, which takes some care: the reserve empties top-down, so a
 * LOW band always means a BIG reserve and few units on the map. You cannot be a
 * Tribe with eighteen units placed. The only way to be over your limit is to
 * have been higher and fallen — an Empire stacking Forest 3 deep, starved until
 * the board walks it back to Kingdom, where Forest holds 2. */
{
  const g = board([[0, 0, 'forest', 0, 3], [1, 0, 'forest', 0, 3], [2, 0, 'forest', 0, 3],
                   [0, 1, 'forest', 0, 3], [1, 1, 'forest', 0, 3],
                   [3, 0, 'plains', 1, 1]], { growLimits: true });
  const p = g.P[0];
  p.reserve = [0, 0, 0, 1, 4];         // Empire, 15 placed, 5 in reserve = 20
  ok(p.band() === 3, 'the hand-built board is not at Empire');
  const total = () => [...g.m.tiles.values()]
    .reduce((a, t) => a + t.units.filter((u) => u === 0).length, 0)
    + p.reserve.reduce((a, b) => a + b, 0);
  ok(total() === 20, `the hand-built board holds ${total()} units, not 20`);

  // starve twice: the first recycle tops the Empire tier back up, the second
  // spills into Kingdom — and Kingdom only holds two Forest
  for (let i = 0; i < 2; i++) {
    p.gold = 0;
    const it = g._recycle(p);
    let r = it.next();
    while (!r.done) r = it.next(null);
    p.discard = [];                    // the hand churn is not what is under test
  }
  ok(p.band() === 2, `starvation left the seat at band ${p.band()}, expected Kingdom`);
  ok(g.stats.shed_over_limit > 0, 'the band fell to Kingdom and nothing was shed');
  ok(total() === 20, `units do not add up after the cascade: ${total()}`);
  for (const [k, t] of g.m.tiles) {
    if (t.owner !== 0) continue;
    ok(t.units.length <= t.capacityFor(0),
       `${k} still holds ${t.units.length} of ${t.capacityFor(0)} after shedding`);
  }
}
{
  /* The loop itself, on a state that genuinely needs two passes.
   *
   * Kingdom with its reserve tier already full: Forest holds 2 there, so the
   * Forest stack of 3 sheds one — and that unit has nowhere to go but the
   * Settlement tier, which drops the band again, and Settlement holds only 2
   * Plains.
   *
   * The Plains tile is laid FIRST on purpose. Within a pass each tile is judged
   * against the limit that applies when it is reached, so a tile visited before
   * the drop is judged by the old limit and has to be caught on the next pass.
   * Lay them the other way round and one pass is enough — which is exactly the
   * bug the outer loop exists to prevent. */
  const g = board([[1, 0, 'plains', 0, 3], [0, 0, 'forest', 0, 3],
                   [3, 0, 'plains', 1, 1]], { growLimits: true });
  const p = g.P[0];
  p.reserve = [0, 0, 6, 4, 4];         // Kingdom, tier full: 14 + 6 placed = 20
  ok(p.band() === 2, 'the two-pass board is not at Kingdom');
  g._shedOverLimit(p);
  ok(p.band() === 1, `shedding left the seat at band ${p.band()}, expected Settlement`);
  for (const [k, t] of g.m.tiles) {
    if (t.owner !== 0) continue;
    ok(t.units.length <= t.capacityFor(0),
       `${k} holds ${t.units.length} of ${t.capacityFor(0)} — the cascade stopped early`);
  }
  const total = [...g.m.tiles.values()]
    .reduce((a, t) => a + t.units.filter((u) => u === 0).length, 0)
    + p.reserve.reduce((a, b) => a + b, 0);
  ok(total === 20, `the two-pass cascade lost units: ${total}`);
}
{
  // combat losses must NOT shed: only starvation culls
  const g = board([[0, 0, 'plains', 0, 3], [1, 0, 'plains', 1, 1]], { growLimits: true });
  const p = g.P[0];
  setTier(p, 3);
  g.m.takeUnitOff('0,0');              // as an attack would
  p.returnUnit();
  setTier(p, 0);                       // and say that dropped the band
  const held = g.m.tiles.get('0,0').units.length;
  ok(held === 2, `a combat loss shed units too: ${held} left on a tile of 2`);
}

// --------------------------------------------------- whole games survive
{
  let shed = 0;
  for (let s = 0; s < 20; s++) {
    const g = E.playOut(3, s * 313 + 5, { growLimits: true });
    if (!g.finished()) fail.push('a growing-limits game did not finish');
    shed += g.stats.shed_over_limit || 0;
    for (const p of g.P) {
      const on = [...g.m.tiles.values()]
        .reduce((a, t) => a + t.units.filter((u) => u === p.i).length, 0);
      if (on + p.reserve.reduce((a, b) => a + b, 0) !== 20)
        fail.push('units do not add up to 20');
    }
    /* A stack over its owner's limit is NOT a fault here. The booklet is
     * explicit: "units lost in combat lower your band without emptying your
     * cities, so a stack can sit above your current limit until the next
     * famine." Only starvation culls — that is what the cascade tests above
     * pin down. What must always hold is the unit count. */
    for (const t of g.m.tiles.values())
      if (t.units.length > t.capacity)
        fail.push(`a tile ended over the highest limit any band allows: ${t.units.length}`);
  }
  console.log(`20 bot games with growing limits: clean, ${shed} units shed `
    + '(bots feed themselves, so the cascade is a human-play rule); '
    + 'over-limit stacks left by combat are legal and were not counted as faults');
}

console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : 'growing limits: the table applies per OWNER, hostile ground stays low, '
    + 'starvation sheds the surplus and cascades, combat does not');
process.exit(fail.length ? 1 : 0);
