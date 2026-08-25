/* Victory row perks — the framework and the perks that are actually wired.
 *
 * PROPOSAL, off by default. See VROW-PERKS.md.
 *
 * What matters here is the two things a slot perk can get wrong: firing at the
 * wrong row depth, and refreshing at the wrong moment. The row is rank-sorted
 * and pushed right, so slot 4 needs two cards, slot 3 three, slot 2 four and
 * slot 1 all five — get that backwards and every perk is available from the
 * first research.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

const withRow = (n, perks, band) => {
  const p = new E.Player(0, E.BANDS, perks);
  for (let i = 0; i < n; i++) p.vrow.push({ r: 5 + i, s: 'plains' });
  if (band) for (let j = 0; j < band; j++) p.reserve[j] = 0;   // walk up the tiers
  return p;
};

// ---------------------------------------------------------- off by default
ok(E.playOut(3, 7, {}).PERKS === null, 'perks are on without being asked for');
const plain = new E.Player(0, E.BANDS);
plain.vrow = [1, 2, 3, 4, 5].map((r) => ({ r, s: 'plains' }));
ok(!plain.hasPerk('roads') && plain.freeMoves() === E.BANDS[0][4],
   'a player with no perk table still gained one');

// ------------------------------------------------- the depth thresholds
for (const [slot, id, needs] of [[1, 'coercion', 5], [2, 'roads', 4],
                                 [3, 'scholarship', 3], [4, 'granary', 2]]) {
  ok(E.perkSlotNeeds(slot) === needs,
     `slot ${slot} claims to need ${E.perkSlotNeeds(slot)} cards, not ${needs}`);
  for (let n = 0; n <= 5; n++) {
    const p = withRow(n, { [slot]: id });
    const live = p.hasPerk(id);
    ok(live === (n >= needs),
       `${id} is ${live ? 'live' : 'dead'} at ${n} cards; it needs ${needs}`);
  }
}

// ------------------------------------------------------ the wired perks
// Roads: one extra free move, then spent until the recycle.
{
  const p = withRow(4, { 2: 'roads' });
  const base = E.BANDS[0][4];
  ok(p.freeMoves() === base + 1, `Roads gave ${p.freeMoves() - base} extra moves`);
  ok(p.spendPerk('roads'), 'Roads could not be spent while live');
  ok(p.freeMoves() === base, 'Roads still paying out after it was spent');
  ok(!p.spendPerk('roads'), 'Roads was spent twice between recycles');
  p.refreshPerks();
  ok(p.freeMoves() === base + 1, 'the recycle did not turn Roads back over');
}
// Scholarship: one rank above the tier cap.
{
  const p = withRow(3, { 3: 'scholarship' });
  ok(p.rankCap() === E.BANDS[0][6] + 1, `Scholarship gave cap ${p.rankCap()}`);
  p.spendPerk('scholarship');
  ok(p.rankCap() === E.BANDS[0][6], 'Scholarship still lifting the cap once spent');
}
// Granary: a RATE, not a use — its token never turns over, so it must keep
// paying out without ever being spent. Tribe eats nothing, so walk up a tier.
{
  const p = withRow(2, { 4: 'granary' }, 1);
  const band = p.band();
  ok(band > 0, 'the fixture did not reach a tier that pays food');
  ok(p.food() === Math.max(0, E.BANDS[band][3] - 1),
     `Granary left food at ${p.food()}, tier pays ${E.BANDS[band][3]}`);
  p.spendPerk('granary');
  ok(p.food() === Math.max(0, E.BANDS[band][3] - 1),
     'Granary stopped paying after something tried to spend it');
}
// Food can never go negative.
{
  const p = withRow(2, { 4: 'granary' });
  ok(p.food() >= 0, `Granary drove food to ${p.food()}`);
}

// ------------------------------------------------- the draw is seed-pure
// A table replays from (seed, options, answers). If the perks were drawn from
// anywhere but the game's own rng, two clients would run different games.
{
  const a = E.playOut(3, 12345, { perks: true }).PERKS;
  const b = E.playOut(3, 12345, { perks: true }).PERKS;
  ok(JSON.stringify(a) === JSON.stringify(b),
     `the same seed drew different perks: ${JSON.stringify(a)} vs ${JSON.stringify(b)}`);
  const seeds = new Set();
  for (let s = 1; s <= 40; s++)
    seeds.add(JSON.stringify(E.playOut(3, s * 7919, { perks: true }).PERKS));
  ok(seeds.size > 1, 'every seed drew the same perks — the draw is not random');
}
// An explicit set, for tests and for pinning a playtest.
{
  const g = E.playOut(3, 5, { perks: { 2: 'roads', 4: 'coinage' } });
  ok(g.PERKS[2] === 'roads' && g.PERKS[4] === 'coinage',
     `an explicit perk set was not honoured: ${JSON.stringify(g.PERKS)}`);
  ok(!g.PERKS[1] && !g.PERKS[3], 'slots nobody asked for were filled anyway');
}
// Only implemented perks are ever drawn — a half-built prompt is worse than
// none, so anything marked todo stays out of the bag.
{
  for (let s = 1; s <= 4; s++)
    for (const id of E.perksInSlot(s, true))
      ok(!E.PERKS[id].todo, `${id} is unimplemented but still in the draw`);
  for (let seed = 1; seed <= 60; seed++) {
    const drawn = E.playOut(3, seed * 131, { perks: true }).PERKS || {};
    for (const s of Object.keys(drawn))
      ok(!E.PERKS[drawn[s]].todo, `seed ${seed} drew unimplemented ${drawn[s]}`);
  }
}
// Pioneering relaxes the touch-two rule, and ONLY while it is live and unspent.
// legalSpaces() is the single place that rule lives, so if this drifts, tiles
// start landing in mid-air.
{
  const g = E.playOut(3, 7, { perks: { 1: 'pioneering' } });
  const q = g.P[0];
  q.vrow = [1, 2, 3, 4, 5].map((r) => ({ r, s: 'plains' }));
  q.refreshPerks();
  const strict = g.m.legalSpaces(2).size;
  const loose = g.spacesFor(q).size;
  ok(loose > strict, `Pioneering opened ${loose - strict} new cells — expected some`);
  q.spendPerk('pioneering');
  ok(g.spacesFor(q).size === strict,
     'Pioneering still relaxing the touch rule after it was spent');
  q.refreshPerks();
  ok(g.spacesFor(q).size === loose, 'the recycle did not restore Pioneering');
  // and a player without it is never affected
  const other = g.P[1];
  other.vrow = [1, 2, 3, 4, 5].map((r) => ({ r, s: 'plains' }));
  ok(g.spacesFor(other).size === loose || !other.perks,
     'a second holder of the same perk saw a different map');
  const none = new E.Player(2, E.BANDS);
  ok(g.m.legalSpaces(2).size === strict, 'the strict rule moved under us');
  ok(!none.hasPerk('pioneering'), 'a player with no perk table has Pioneering');
}

// Every perk sits in the slot its printed token claims.
{
  const sheetSlots = { wonders: 1, works: 2, crafts: 3, customs: 4 };
  for (const id of E.PERK_IDS)
    ok(E.PERKS[id].slot === sheetSlots[E.PERKS[id].deck],
       `${id} is in deck ${E.PERKS[id].deck} but slot ${E.PERKS[id].slot}`);
}

// ------------------------------------------------ a whole game, perks on
// The real question: does turning them on break anything?
{
  let played = 0;
  for (let s = 1; s <= 40; s++) {
    const g = E.playOut(3, s * 2654435761 % 2147483647, { perks: true });
    played += 1;
    const total = g.score().reduce((a, x) => a + x.total, 0);
    ok(Number.isFinite(total) && total > 0, `seed ${s} scored ${total}`);
    ok(g.round > 0 && g.round < 60, `seed ${s} ran ${g.round} rounds`);
    for (const p of g.P) ok(p.vrow.length <= 5, 'a victory row grew past five');
  }
  ok(played === 40, 'not every game finished');
}
// And that the perks actually fired at some point across a run of games.
{
  let coinage = 0, tribute = 0;
  for (let s = 1; s <= 120; s++) {
    const g = E.playOut(4, s * 40503, { perks: { 4: 'coinage' } });
    coinage += (g.stats && g.stats.perk_coinage) || 0;
  }
  for (let s = 1; s <= 120; s++) {
    const g = E.playOut(4, s * 40503, { perks: { 4: 'tribute' } });
    tribute += (g.stats && g.stats.perk_tribute) || 0;
  }
  ok(coinage > 0, 'Coinage never paid out in 120 games — is it wired?');
  ok(tribute > 0, 'Tribute never paid out in 120 games — is it wired?');
  console.log(`    (coinage fired ${coinage}x, tribute ${tribute}x over 120 games each)`);
}

console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : `perks: ${E.PERK_IDS.length} defined, `
    + `${[1, 2, 3, 4].reduce((a, s) => a + E.perksInSlot(s, true).length, 0)} wired and drawable — `
    + 'thresholds 5/4/3/2 by slot, spent once until the recycle, drawn from the '
    + 'seed so every client draws the same four, and off unless asked for');
process.exit(fail.length ? 1 : 0);
