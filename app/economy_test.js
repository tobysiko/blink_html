/* THE LEAN ECONOMY AND SPOILS — two variants, and the promise that neither of
 * them is on by default.
 *
 * Both exist because of measurements taken 3 Sep 2026:
 *
 *   - Ascension pays 26.6 gold a game and food takes 31.8 back, and a player
 *     arrived at a recycle short of the food owed in 0.1% of 6,913 recycles.
 *     No unit was ever starved off the map. So the loop is very nearly closed,
 *     and `food:false, ascension:false` asks what the game is without it.
 *   - A bot forbidden to attack outscores one that fights by 2.0 points, even
 *     with DUEL_TAKE on. `spoils` asks what the smallest rule is that reverses
 *     that, and the answer measured was one coin.
 *
 * The most important assertions in this file are the ones in the FIRST block:
 * the printed game must be bit-for-bit what it was before either option
 * existed. A variant that quietly changes the default game is worse than no
 * variant, because every number in COMBAT-SIMPLIFY.md and DUEL-SPOILS.md was
 * taken under the default.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

// -------------------------------------------------- the printed rule is intact
{
  const g = new E.Game(4, 5, { humans: [] });
  ok(g.FOOD_ON === true,      'food was not on by default');
  ok(g.ASCEND_ON === true,    'the ascension reward was not on by default');
  ok(g.SPOILS === 'none',     'spoils were not off by default');
  /* The printed food row: 0/1/2/3/4, one number per tier, not cumulative. */
  const p = g.P[0];
  const row = g.BANDS.map((_, i) => { p.reserve = p.reserve.map((_, j) => j < i ? 0 : 1);
                                      return p.food(); });
  ok(row.join() === '0,1,2,3,4', 'the printed food row changed: ' + row.join('/'));

  const full = E.playOut(4, 11, {});
  ok((full.stats.gold_out_food || 0) > 0,   'a default game paid no food at all');
  ok((full.stats.gold_in_ascension || 0) > 0, 'a default game paid no ascension reward');
  ok(!(full.stats.gold_in_spoils || 0),     'a default game paid spoils');
}

// ------------------------------------------------------------ food switched off
{
  const g = new E.Game(4, 5, { humans: [], food: false });
  ok(g.FOOD_ON === false, 'food:false did not reach the game');
  const p = g.P[0];
  const row = g.BANDS.map((_, i) => { p.reserve = p.reserve.map((_, j) => j < i ? 0 : 1);
                                      return p.food(); });
  ok(row.join() === '0,0,0,0,0', 'a tier still asked to be fed: ' + row.join('/'));

  const lean = E.playOut(4, 11, { food: false });
  ok(!(lean.stats.gold_out_food || 0),  'a coin was spent on food with food off');
  ok(!(lean.stats.starved_back || 0),   'a unit starved with food off');
  ok(lean.finished(),                   'a game with food off did not finish');
  /* The ascension reward is untouched by this switch on its own — the two are
   * offered as one switch in the UI, but the engine keeps them separable so
   * the middle configurations stay measurable. */
  ok((lean.stats.gold_in_ascension || 0) > 0, 'food:false also stopped the ascension reward');
}

// ------------------------------------------------- the ascension reward switched off
{
  const lean = E.playOut(4, 11, { ascension: false });
  ok(!(lean.stats.gold_in_ascension || 0), 'the ascension reward was paid with it off');
  ok(lean.finished(),                      'a game without the reward did not finish');
  /* THE TRAP THIS GUARDS. ascensionDue() is what advances `reached`, and it is
   * called for that side effect as much as for the coin. Skip the call and a
   * player who climbs two tiers later collects for every tier below them at
   * once — the bug would only appear in a game long enough to climb twice. */
  for (const p of lean.P)
    ok(p.reached >= p.band(),
       'seat ' + p.i + ' climbed to band ' + p.band() + ' but only reached ' + p.reached);
}

// ------------------------------------------------------------------ the spoils
/* One defender, no coin on it, and an empty hand to answer with — so the
 * attacker wins and the ground is taken. `units` is topped up to ask the other
 * question: a won fight that does NOT empty the tile. */
function duel(opts, defenders) {
  const g = new E.Game(3, 77, Object.assign({ humans: [] }, opts));
  const tile = [...g.m.tiles.values()].find(
    (t) => t.owner !== null && t.units.length === 1);
  tile.gold = 0;
  while (tile.units.length < (defenders || 1)) tile.units.push(tile.owner);
  const me = g.P[(tile.owner + 1) % g.P.length];
  g.P[tile.owner].hand = [];                       // nothing to defend with
  const it = g._duel(me, tile.key, tile, { r: 9, s: tile.terrain }, null);
  let r = it.next(); while (!r.done) r = it.next(null);
  /* Read the SPOILS line, not the purse: taking the ground settles a unit off
   * the reserve, which can empty a band and pay an ascension reward in the same
   * breath. A test that watched `me.gold` would be measuring both. */
  return { g, tile, me, gained: g.stats.gold_in_spoils || 0,
           took: tile.owner === me.i };
}

{
  const d = duel({}, 1);
  ok(d.took,        'the attacker won and did not take the emptied ground');
  ok(d.gained === 0, 'the printed rule paid ' + d.gained + ' gold for a won duel');
}
{
  const d = duel({ spoils: 'gold' }, 1);
  ok(d.gained === 1, "spoils:'gold' paid " + d.gained + ' gold, not 1');
}
{
  const d = duel({ spoils: 'gold' }, 2);
  ok(d.gained === 1, "spoils:'gold' paid " + d.gained + ' for a fight that took no ground');
}
{
  const d = duel({ spoils: 'ground' }, 1);
  ok(d.took,         "spoils:'ground' — the tile was not taken, so the case is untested");
  ok(d.gained === 1, "spoils:'ground' paid " + d.gained + ' for taking the ground');
}
{
  const d = duel({ spoils: 'ground' }, 2);
  ok(!d.took,        "the tile changed hands with 2 defenders and one won duel");
  ok(d.gained === 0, "spoils:'ground' paid " + d.gained + ' without taking the ground');
}
{
  const g = E.playOut(4, 11, { spoils: 'ground' });
  ok((g.stats.gold_in_spoils || 0) > 0, 'a full game paid no spoils with them on');
  ok((g.stats.gold_in_spoils || 0) === (g.stats.duel_settle || 0),
     'spoils and taken ground disagree: ' + (g.stats.gold_in_spoils || 0)
     + ' vs ' + (g.stats.duel_settle || 0));
}
{
  const g = E.playOut(4, 11, { food: false, ascension: false, spoils: 'ground' });
  ok(g.finished(), 'the lean + spoils game did not finish');
}

if (fail.length) { console.error(fail.join('\n')); process.exit(1); }
console.log('economy_test ok');

// ------------------------------------------- the frontier: chance, and scarcity
/* `chance` is the die on the table: some faces pay. It exists because coins
 * under an OPEN supply — which players take from freely all game — cannot be
 * handled, and because `seams` measured at 34.5% of explorations paying, which
 * is two faces of six. */
{
  const g = new E.Game(4, 5, { humans: [] });
  ok(g.FRONTIER === 'low', 'the printed frontier rule is no longer the default');
  ok(Math.abs(g.FRONTIER_CHANCE - 2 / 6) < 1e-9,
     'the default chance is not two faces of six');

  const paid = E.playOut(4, 11, { frontier: 'chance', frontierChance: 1 });
  const ex = paid.stats.explore || 0;
  ok(ex > 0, 'no exploration happened at all, so the rule is untested');
  ok((paid.stats.gold_in_frontier || 0) === ex,
     `chance:1 paid ${paid.stats.gold_in_frontier || 0} for ${ex} explorations`);
  const never = E.playOut(4, 11, { frontier: 'chance', frontierChance: 0 });
  ok(!(never.stats.gold_in_frontier || 0), 'chance:0 still paid a coin');
}
{
  /* SCARCITY. At the printed 15 a game ends with a third of every terrain
   * unused, so terrain can always be manufactured and combat never has to be
   * the way to get it. The dial is what makes that testable. */
  const loose = E.playOut(4, 3, {});
  const tight = E.playOut(4, 3, { tileSupply: 8 });
  const left = (g) => Object.values(g.m.supply).reduce((a, b) => a + b, 0);
  ok(left(loose) > 0, 'the printed supply ran out — the measurement changed');
  ok(left(tight) < left(loose),
     `a tighter supply left ${left(tight)} tiles against ${left(loose)}`);
  ok(tight.finished(), 'a game with a scarce supply did not finish');
}
