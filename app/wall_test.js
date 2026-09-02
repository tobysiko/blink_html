/* A WALL IS A FLOOR, NOT A SUBSTITUTE.
 *
 * The proposal (COMBAT-SIMPLIFY.md): a fortification coin defends at
 * WALL_RANK — 10, the top of the starting deck — and the defender may still
 * answer with a card if it beats that. The higher of the two fights.
 *
 * The first wiring had the coin REPLACE the hand, and that version is kept as
 * `fortify: "wallonly"` because its numbers are in the document. It is also
 * the bug this file exists to prevent coming back: under it, a defender
 * holding a 16 was made WEAKER by the wall they had paid for, and one card
 * over the wall both broke it and took the ground.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* A fortified tile with one defender, and the seat next door to attack it. */
function scene(opts, hand, terrain) {
  const g = new E.Game(3, 77, Object.assign({ humans: [] }, opts));
  const tile = [...g.m.tiles.values()].find(
    (t) => t.owner !== null && t.units.length === 1);
  /* The opening map is all Plains and Mountain and nobody starts on high
   * ground, so the ground under the fight is set here rather than hunted for.
   * _duel reads the terrain for its bonus and nothing else. */
  if (terrain) tile.terrain = terrain;
  tile.gold = 1;                                   // fortified
  const me = g.P[(tile.owner + 1) % g.P.length];
  g.P[tile.owner].hand = hand.map((r) => ({ r, s: 'ocean' }));
  return { g, tile, me, owner: tile.owner };
}
function fight(s, rank, fort) {
  const it = s.g._duel(s.me, s.tile.key, s.tile, { r: rank, s: s.tile.terrain },
                       fort || 'wall');
  const asked = [];
  let r = it.next();
  while (!r.done) { asked.push(r.value && r.value.type); r = it.next(null); }
  return asked;
}

// ---------------------------------------------------------- the coin holds
{
  const s = scene({ fortify: 'wall' }, [5, 7], 'plains');
  fight(s, 10);
  ok(s.tile.owner === s.owner,
     'a 10 took a walled Plains tile — the coin defends at 10 and holds level fights');
  ok(s.tile.gold === 0, 'the coin was not spent by the fight it fought');
}
{
  const s = scene({ fortify: 'wall' }, [5, 7], 'plains');
  fight(s, 11);
  ok(s.tile.owner !== s.owner, 'an 11 did not break a wall of 10 on open ground');
}
{
  const s = scene({ fortify: 'wall', wallRank: 10 }, [5], 'mountain');
  fight(s, 12);
  ok(s.tile.owner === s.owner, 'a 12 beat a wall of 10 on a Mountain (+2 makes it level)');
}

// ------------------------------------ the hand still answers, and outranks it
{
  const s = scene({ fortify: 'wall' }, [16], 'plains');
  const before = s.g.P[s.owner].hand.length;
  fight(s, 14);
  ok(s.tile.owner === s.owner,
     'a 14 took a walled tile from a defender holding a 16 — the coin LOWERED the defence');
  ok(s.g.P[s.owner].hand.length === before - 1,
     'the 16 that fought was not spent');
}
{
  /* the regression itself: the same fight under the old substitute rule */
  const s = scene({ fortify: 'wallonly' }, [16], 'plains');
  fight(s, 14, 'wallonly');
  ok(s.tile.owner !== s.owner,
     '"wallonly" no longer replaces the hand — that variant is what the floor fixed');
}
{
  /* a card that cannot beat the wall is never spent on it */
  const s = scene({ fortify: 'wall' }, [8, 9], 'plains');
  const before = s.g.P[s.owner].hand.length;
  fight(s, 10);
  ok(s.g.P[s.owner].hand.length === before,
     'a card below the wall was spent for nothing');
}

// -------------------------------------- and a person is not asked pointlessly
{
  const g = new E.Game(3, 77, { humans: [1], fortify: 'wall' });
  const tile = [...g.m.tiles.values()].find((t) => t.owner === 1 && t.units.length === 1);
  if (tile) {
    tile.gold = 1;
    g.P[1].hand = [{ r: 4, s: 'ocean' }, { r: 9, s: 'ocean' }];
    const me = g.P[0];
    const it = g._duel(me, tile.key, tile, { r: 14, s: tile.terrain }, 'wall');
    const asked = [];
    let r = it.next();
    while (!r.done) { asked.push(r.value && r.value.type); r = it.next(null); }
    ok(!asked.includes('duel'),
       'a person was asked to answer a wall with cards that cannot beat it');
  }
}

// ------------------------------------------- the ladder: 10/12/14/16/18
/* The app's wall is the tier ladder — the rank cap of the tier you are on,
 * less two. It starts at 10 so a Tribe's wall is still exactly the top of the
 * starting deck, and it climbs with the civilization behind it. */
{
  const LADDER = { fortify: 'wall', wallRank: 'cap', wallOffset: -2 };
  const s = scene(LADDER, [3], 'plains');
  const d = s.g.P[s.owner];
  ok(d.band() === 0, 'the defender did not start at Tribe');
  ok(d.rankCap() === 12, `Tribe's rank cap is ${d.rankCap()}, not 12`);
  fight(s, 10);
  ok(s.tile.owner === s.owner, "a 10 broke a Tribe's wall — the ladder should start at 10");
}
{
  const LADDER = { fortify: 'wall', wallRank: 'cap', wallOffset: -2 };
  const s = scene(LADDER, [3], 'plains');
  fight(s, 11);
  ok(s.tile.owner !== s.owner, "an 11 did not break a Tribe's wall of 10");
}
{
  /* Empty the top two bands and the defender is a Kingdom: cap 16, wall 14. */
  const LADDER = { fortify: 'wall', wallRank: 'cap', wallOffset: -2 };
  const s = scene(LADDER, [3], 'plains');
  const d = s.g.P[s.owner];
  d.reserve[0] = 0; d.reserve[1] = 0;
  ok(d.band() === 2 && d.rankCap() === 16,
     `emptying two bands gave band ${d.band()} cap ${d.rankCap()}, expected 2 / 16`);
  fight(s, 13);
  ok(s.tile.owner === s.owner, "a 13 broke a Kingdom's wall — it should hold at 14");
}
{
  const LADDER = { fortify: 'wall', wallRank: 'cap', wallOffset: -2 };
  const s = scene(LADDER, [3], 'plains');
  const d = s.g.P[s.owner];
  d.reserve[0] = 0; d.reserve[1] = 0;
  fight(s, 15);
  ok(s.tile.owner !== s.owner, "a 15 did not break a Kingdom's wall of 14");
}

// ------------------------------------------------- one attack per map phase
{
  const g = new E.Game(3, 77, { humans: [], attacksPerTurn: 1 });
  const tile = [...g.m.tiles.values()].find((t) => t.owner !== null && t.units.length);
  const me = (tile.owner + 1) % g.P.length;
  const spaces = g.m.legalSpaces();
  g.m.atkLeft = 1;
  const with1 = g.m.cellActions(tile.key, tile.terrain, me, spaces, 9, 9);
  g.m.atkLeft = 0;
  const with0 = g.m.cellActions(tile.key, tile.terrain, me, spaces, 9, 9);
  ok(with1.includes('attack'), 'the first attack of a map phase was refused');
  ok(!with0.includes('attack'), 'a second attack was offered with the cap set to one');
}
{
  const g = E.playOut(4, 99, { attacksPerTurn: 1, fortify: 'wall' });
  ok(g.finished(), 'a full game with the wall and the cap did not finish');
  ok((g.stats.duels || 0) > 0, 'a full game with the cap contained no duels at all');
}

if (fail.length) { console.error(fail.join('\n')); process.exit(1); }
console.log('wall_test ok');
