/* Effect B — found a colony (§07, §10), on hand-built maps.
 *
 * The rule being defended: a colony is an EXPLORE, so §06 applies in full —
 * the space must touch two tiles already on the map and be in your reach. Only
 * the 6-10 band may go further, and only "up to 2 tiles out", as the card
 * prints. Before this test the effect used every legal space on the board:
 * measured over 200 bot games, 58% of colonies landed outside their founder's
 * reach, a mean of 2.2 steps away and as far as 8.
 */
const E = require('./engine.js');
const fail = [];
const ok = (cond, what) => { if (!cond) fail.push(what); };

function board(spec) {
  const g = new E.Game(2, 1, { humans: [0] });
  g.m.tiles.clear();
  for (const [c, r, terrain, seat] of spec) {
    const t = g.m._add([c, r], terrain);
    if (seat !== undefined && seat !== null) t.units.push(seat);
  }
  return g;
}
/* How many steps a cell is from seat's civilization. */
function ring(m, pi, k) {
  let seen = new Set(m.civ(pi)), frontier = new Set(seen);
  for (let d = 1; d <= 9; d++) {
    const next = new Set();
    for (const c of frontier)
      for (const u of E.nbrKeys(...E.unK(c)))
        if (!seen.has(u)) { seen.add(u); next.add(u); if (u === k) return d; }
    frontier = next;
    if (!frontier.size) break;
  }
  return 99;
}
const card = (r, s) => ({ r, s: s || 'plains' });

/* A strip of tiles: seat 0 lives at the left end, seat 1 at the right, with
 * open ground between them. Legal spaces exist at both ends. */
const strip = () => board([
  [0, 0, 'plains', 0], [1, 0, 'plains', 0],
  [2, 0, 'plains', null], [3, 0, 'plains', null], [4, 0, 'plains', null],
  [5, 0, 'plains', 1], [6, 0, 'plains', 1],
  [0, 1, 'plains', null], [3, 1, 'plains', null], [6, 1, 'plains', null],
]);

// 1. an ordinary colony stays within reach
{
  const g = strip();
  const cells = g.colonyCells(g.P[0], card(3));
  ok(cells.length > 0, 'a colony had nowhere to go on an open board');
  const farthest = Math.max(...cells.map((k) => ring(g.m, 0, k)));
  ok(farthest <= 1, `a rank 1-5 colony may land ${farthest} steps out, should be 1`);
  ok(!cells.some((k) => ring(g.m, 1, k) <= 1 && ring(g.m, 0, k) > 1),
     'a colony could be founded on a rival doorstep, far from home');
}
// 2. the 6-10 band may go one further, and no more
{
  const g = strip();
  const near = g.colonyCells(g.P[0], card(3));
  const far = g.colonyCells(g.P[0], card(8));
  const reachOf = (cells) => Math.max(...cells.map((k) => ring(g.m, 0, k)));
  ok(far.length >= near.length, 'the distant colony offered fewer spaces than the near one');
  ok(reachOf(far) <= 2, `a rank 6-10 colony may land ${reachOf(far)} steps out, should be 2`);
  ok(near.every((k) => far.includes(k)), 'the distant colony lost a space the near one had');
}
// 3. every offered space is a legal space in the first place (touch-two)
{
  const g = strip();
  const legal = g.m.legalSpaces();
  for (const r of [3, 8, 13, 18])
    ok(g.colonyCells(g.P[0], card(r)).every((k) => legal.has(k)),
       `a rank ${r} colony offered a space that touches fewer than two tiles`);
}
// 4. swept off the map, the §06 re-entry exemption applies
{
  const g = strip();
  for (const t of g.m.tiles.values()) t.units = t.units.filter((u) => u !== 0);
  ok(g.colonyCells(g.P[0], card(3)).length === g.m.legalSpaces().size,
     'a player with no units on the map cannot re-found anywhere');
}

// 5. the human is ASKED where each tile goes, and it lands there
{
  const g = strip();
  const c = card(13);                       // 11-15: two tiles, one unit
  g.P[0].vrow.push(c);
  const it = g._playColonyHuman(g.P[0], c);
  const asked = [];
  let r = it.next();
  while (!r.done) {
    asked.push(r.value);
    const pick = r.value.options[r.value.options.length - 1];   // a cell of MY choosing
    r = it.next({ cell: pick, terrain: r.value.terrains[0] });
  }
  ok(asked.length === 2, `asked for ${asked.length} cells, the card lays 2`);
  ok(asked.every((q) => q.type === 'colony'), 'the colony step is not its own request');
  for (const q of asked)
    ok(g.m.tiles.has(q.options[q.options.length - 1]),
       'a cell the player chose did not become a tile');
  const mine = [...g.m.tiles.values()].filter((t) => t.owner === 0);
  ok(mine.length === 3, `founder ends with ${mine.length} tiles, expected 2 + 1 colony unit`);
  ok(!g.P[0].vrow.includes(c), 'the spent victory card is still in the row');
}
// 6. stopping early spends the card but lays only what was placed
{
  const g = strip();
  const c = card(13);
  g.P[0].vrow.push(c);
  const before = g.m.tiles.size;
  const it = g._playColonyHuman(g.P[0], c);
  let r = it.next();
  r = it.next({ cell: r.value.options[0], terrain: r.value.terrains[0] });
  if (!r.done) r = it.next(null);                    // stop after one
  ok(g.m.tiles.size === before + 1, 'stopping early still laid the second tile');
  ok(!g.P[0].vrow.includes(c), 'a card stopped early was not spent');
}
// 7. the top band takes ANY terrain; the lower bands take the card's suit
{
  const g = strip();
  const c = card(18, 'forest');
  g.P[0].vrow.push(c);
  const it = g._playColonyHuman(g.P[0], c);
  const q = it.next().value;
  ok(q.terrains.length === 4, 'a rank 16-20 colony did not offer every terrain');
  const g2 = strip();
  const c2 = card(3, 'forest');
  g2.P[0].vrow.push(c2);
  const q2 = g2._playColonyHuman(g2.P[0], c2).next().value;
  ok(q2.terrains.length === 1 && q2.terrains[0] === 'forest',
     'a rank 1-5 colony did not take the card\'s own suit');
}
// 8. a card that cannot found anything is never offered
{
  const g = strip();
  const c = card(3, 'ocean');
  g.P[0].vrow.push(c);
  g.m.supply.ocean = 0;                              // no Ocean tiles left
  const st = { cards: [], moves: 0, researches: 0, bUsed: false, waterUsed: false };
  ok(!g.turnOptions(g.P[0], st).colonyCards.includes(c),
     'a colony was offered with no tile of that terrain left in the supply');
}

console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : 'colonies: within reach (2 out for the 6-10 band), touch-two holds, the '
    + 'player picks every cell and terrain, stopping early is allowed, and a '
    + 'card that could not found anything is not offered');
process.exit(fail.length ? 1 : 0);
