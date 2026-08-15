/* Movement and the water advantage (§07), on hand-built maps.
 *
 * Every claim here is a sentence from the rulebook, turned into a board where
 * it either holds or does not. Needs nothing but node.
 */
const E = require('./engine.js');
const fail = [];
const ok = (cond, what) => { if (!cond) fail.push(what); };

/* A bare map: no starting layout, just the tiles this case needs.
 * cells are [col, row]; `seat` puts one unit of that seat on the tile. */
function board(spec) {
  const g = new E.Game(2, 1, { humans: [] });
  g.m.tiles.clear();
  for (const [c, r, terrain, seat] of spec) {
    const t = g.m._add([c, r], terrain);
    if (seat !== undefined && seat !== null) t.units.push(seat);
  }
  return g;
}
const dests = (g, seat, k) => [...g.moveDests(g.P[seat], k)].sort();
const has = (a, k) => a.includes(k);

// ---------------------------------------------------------------- by land
/* "move a unit any distance across tiles occupied by your units, stepping off
 *  at the end onto an adjacent free tile with room under its population limit" */
{
  // 0,0 - 1,0 - 2,0 mine; 3,0 empty plains beyond the far end
  const g = board([[0, 0, 'plains', 0], [1, 0, 'plains', 0], [2, 0, 'plains', 0],
                   [3, 0, 'plains', null]]);
  const d = dests(g, 0, '0,0');
  ok(has(d, '3,0'), 'a unit cannot cross its own network to the far end');
  ok(has(d, '1,0') && has(d, '2,0'), 'stepping onto your own tile with room is refused');
}
{
  // the network is broken by a rival: "you may not move onto or through a rival"
  const g = board([[0, 0, 'plains', 0], [1, 0, 'plains', 1], [2, 0, 'plains', null]]);
  const d = dests(g, 0, '0,0');
  ok(!has(d, '1,0'), 'a move landed on a rival — movement is never an attack');
  ok(!has(d, '2,0'), 'a move travelled THROUGH a rival tile');
}
{
  // "moving onto a tile is only possible while it has room" — Ocean holds 1
  const g = board([[0, 0, 'plains', 0], [1, 0, 'ocean', 0]]);
  const d = dests(g, 0, '0,0');
  ok(!has(d, '1,0'), 'a unit moved onto a full Ocean tile');
}
{
  // Plains holds 3: two of yours still leaves room
  const g = board([[0, 0, 'plains', 0], [1, 0, 'plains', 0]]);
  g.m.tiles.get('1,0').units.push(0);
  ok(has(dests(g, 0, '0,0'), '1,0'), 'a Plains holding 2 of 3 refused a third unit');
  g.m.tiles.get('1,0').units.push(0);
  ok(!has(dests(g, 0, '0,0'), '1,0'), 'a Plains holding 3 of 3 accepted a fourth unit');
}

// ----------------------------------------------------------------- by sea
/* "move a unit standing on Ocean across unoccupied Ocean, as far as the open
 *  water reaches, ending on an empty Ocean tile" */
{
  const g = board([[0, 0, 'ocean', 0], [1, 0, 'ocean', null], [2, 0, 'ocean', null],
                   [3, 0, 'ocean', null]]);
  const d = dests(g, 0, '0,0');
  ok(has(d, '3,0'), 'the open sea does not carry a unit to its far end');
}
{
  // an occupied Ocean tile is not "unoccupied Ocean": the lane is closed
  const g = board([[0, 0, 'ocean', 0], [1, 0, 'ocean', 1], [2, 0, 'ocean', null]]);
  ok(!has(dests(g, 0, '0,0'), '2,0'), 'a sea move sailed through an occupied tile');
}
{
  // a unit on LAND does not get the sea lane, only the one step off its network
  const g = board([[0, 0, 'plains', 0], [1, 0, 'ocean', null], [2, 0, 'ocean', null]]);
  const d = dests(g, 0, '0,0');
  ok(has(d, '1,0'), 'a land unit cannot step onto the adjacent water');
  ok(!has(d, '2,0'), 'a LAND unit sailed the open sea');
}

// ------------------------------------------------------- water advantage
/* "The first time each turn that you move by sea, you may immediately explore
 *  one tile of any terrain you like." A sea move starts AND ends on Ocean —
 *  stepping onto the water from land is an ordinary land move. */
function turnRun(g, seat, answers) {
  const it = g._humanTurn(g.P[seat], []);
  const seen = [];
  let r = it.next();
  while (!r.done) {
    seen.push(r.value.type);
    const a = answers.shift();
    r = it.next(typeof a === 'function' ? a(r.value) : a);
  }
  return seen;
}
{
  //  land -> water is NOT a sea move
  const g = board([[0, 0, 'plains', 0], [1, 0, 'ocean', null], [1, 1, 'plains', null],
                   [0, 1, 'plains', null]]);
  const seen = turnRun(g, 0, [{ kind: 'move', src: '0,0', dest: '1,0' }, { kind: 'end' }]);
  ok(!seen.includes('waterexplore'),
     'stepping onto the water from land paid the water advantage');
}
{
  //  water -> water IS, and only once per turn
  const g = board([[0, 0, 'ocean', 0], [1, 0, 'ocean', null], [2, 0, 'ocean', null],
                   [0, 1, 'plains', null], [1, 1, 'plains', null]]);
  g.P[0].reserve = [2, 4, 6, 4, 4];
  const seen = turnRun(g, 0, [
    { kind: 'move', src: '0,0', dest: '1,0' },
    null,                                   // decline the free tile
    { kind: 'move', src: '1,0', dest: '2,0' },
    { kind: 'end' },
  ]);
  const n = seen.filter((t) => t === 'waterexplore').length;
  ok(n === 1, `the water advantage fired ${n} times in one turn, expected once`);
}
{
  // and the free tile really is any terrain, not the mover's suit
  const g = board([[0, 0, 'ocean', 0], [1, 0, 'ocean', null], [0, 1, 'plains', null],
                   [1, 1, 'plains', null]]);
  let offered = null;
  turnRun(g, 0, [
    { kind: 'move', src: '0,0', dest: '1,0' },
    (req) => { offered = req; return null; },
    { kind: 'end' },
  ]);
  ok(offered && offered.terrains.length === 4,
     'the water advantage did not offer every terrain in the supply');
  ok(offered && offered.options.every((k) => {
    const [c, r] = E.unK(k);
    return E.nbrKeys(c, r).filter((n) => g.m.tiles.has(n)).length >= 2;
  }), 'the water advantage offered a space touching fewer than two tiles');
}

// ------------------------------- the advantage is not limited by reach
/* The geometry that used to kill it: a ship sails into an enclosed pocket, so
 * there is no empty cell beside it at all. Under the old reach rule the
 * advantage found nothing and paid nothing; a voyage now lays its tile
 * anywhere the map legally takes one.
 *
 * A seven-hex flower does it — a centre with all six neighbours already tiles.
 * (The other half of the complaint, a ship at the frontier, turns out to be the
 * same case: any destination with at least one neighbouring tile shares two
 * cells with it, and those touch two tiles, so they are legal. The only way to
 * have nothing beside you is to be surrounded.) */
{
  const ring = E.nbrKeys(0, 0).map((k) => E.unK(k));
  const spec = [[0, 0, 'ocean', null]];
  ring.forEach(([c, r], i) => spec.push([c, r, i === 0 ? 'ocean' : 'plains',
                                         i === 0 ? 0 : null]));
  const g = board(spec);
  g.P[0].reserve = [2, 4, 6, 4, 4];
  const [sc, sr] = ring[0];
  const src = `${sc},${sr}`;
  ok(g.moveDests(g.P[0], src).has('0,0'), 'the ship cannot reach the enclosed centre');
  ok(E.nbrKeys(0, 0).every((k) => g.m.tiles.has(k)),
     'the flower is not closed — the test board is wrong');
  ok(g.m.legalSpaces().size > 0, 'the flower has no legal space anywhere');
  ok(g.waterPays(g.P[0], src, '0,0'),
     'sailing into a closed pocket still reports no free tile');

  let offered = null;
  turnRun(g, 0, [
    { kind: 'move', src, dest: '0,0' },
    (req) => { offered = req; return null; },
    { kind: 'end' },
  ]);
  const gotWater = !!offered && offered.type === 'waterexplore';
  ok(gotWater, `no explore was offered after sailing into a closed pocket`
     + `${offered ? ` — got a ${offered.type} request instead` : ""}`);
  ok(gotWater && offered.options.length === g.m.legalSpaces().size,
     'the offer is still being narrowed to your own reach');
  // and every cell offered is a legal space — touch-two still holds
  if (gotWater) {
    for (const k of offered.options) {
      const [c, r] = E.unK(k);
      ok(E.nbrKeys(c, r).filter((n) => g.m.tiles.has(n)).length >= 2,
         `${k} was offered but touches fewer than two tiles`);
    }
  }
}

// ------------------------------------------- the advantage is not burned
/* Sailing when the advantage CANNOT be collected must not spend it. The
 * cheapest way to make it uncollectable is an empty tile supply — no terrain
 * left to lay — and the test then sails twice: if the first sail consumed the
 * right, the second would report nothing at all. */
{
  /* A Settlement, so there are two free moves to spend — a Tribe has one, and
   * the second sail would be refused for want of a move rather than for want
   * of the advantage. */
  const g = board([[0, 0, 'ocean', 0], [1, 0, 'ocean', null], [2, 0, 'ocean', null],
                   [0, 1, 'plains', 0, 2], [1, 1, 'plains', 0, 3]]);
  for (const terr of E.TER) g.m.supply[terr] = 0;
  g.P[0].reserve = [0, 4, 6, 4, 4];             // 14 in reserve + 6 placed = 20
  const seen = turnRun(g, 0, [
    { kind: 'move', src: '0,0', dest: '1,0' },
    { kind: 'move', src: '1,0', dest: '2,0' },
    { kind: 'end' },
  ]);
  ok(!seen.includes('waterexplore'), 'an empty supply still offered a free tile');
  ok((g.stats.water_nowhere || 0) === 2,
     `the advantage was reported unavailable ${g.stats.water_nowhere} times, expected twice `
     + '— the first sail spent it');
}

/* And the promise the map makes has to be true. `waterPays()` is what the hex
 * badge asks before it offers "Sail — free tile"; if it ever disagrees with
 * what the engine then does, the badge is lying to the player at the exact
 * moment they commit a move. Checked over whole games, both ways. */
{
  let sails = 0, wrong = 0, paid = 0;
  for (let s = 1; s <= 25; s++) {
    const rng = E.makeRng(s * 7919 + 3);
    const g = new E.Game(3, s * 3001 + 7, { humans: [0] });
    let pending = null;
    let guard = 0;
    while (!g.finished() && guard++ < 300) {
      const it = g.playRound();
      let r = it.next(), inner = 0;
      while (!r.done) {
        if (inner++ > 6000) throw new Error('loop');
        const req = r.value;
        if (pending !== null) {                 // the request right after a sail
          const got = req.type === 'waterexplore';
          if (got !== pending.expect) wrong++;
          if (got) paid++;
          pending = null;
        }
        let ans = null;
        if (req.type === 'turn') {
          const o = req.opts;
          let sea = null;
          for (const src of o.moveSources) {
            for (const d of g.moveDests(g.P[0], src)) {
              if (g.m.tiles.get(src).terrain === 'ocean'
                  && g.m.tiles.get(d).terrain === 'ocean') { sea = [src, d]; break; }
            }
            if (sea) break;
          }
          if (sea && o.moves && !req.state.waterUsed) {
            sails++;
            pending = { expect: g.waterPays(g.P[0], sea[0], sea[1]) };
            ans = { kind: 'move', src: sea[0], dest: sea[1] };
          } else {
            const live = o.cards.filter((m) => m.options.length);
            if (live.length) {
              const m = live[0], [cell, act] = m.options[0];
              ans = { kind: 'spend', card: m.card, cell, act };
            } else if (o.cards.length) ans = { kind: 'cash', card: o.cards[0].card };
            else ans = { kind: 'end' };
          }
        } else if (req.type === 'waterexplore') {
          ans = { cell: req.options[0], terrain: req.terrains[0] };
        } else if (req.options && req.options.length) {
          ans = req.options[Math.floor(rng.random() * req.options.length)];
        }
        r = it.next(ans);
      }
      pending = null;                            // the round ended in between
    }
  }
  ok(sails > 20, `only ${sails} sea moves tried — the check saw too little`);
  ok(wrong === 0,
     `the hex badge would have lied ${wrong} times in ${sails} sea moves`);
  console.log(`waterPays agreed with the engine on all ${sails} sea moves `
    + `(${paid} of them paid a tile)`);
}

// --------------------------------------------------------- fortifications
/* "The coin is lost to the supply the moment the unit is disturbed in any way
 *  — attacked, moved, or stacked onto." */
{
  const g = board([[0, 0, 'plains', 0], [1, 0, 'plains', null]]);
  g.m.tiles.get('0,0').gold = 1;
  g._doMove(g.P[0], '0,0', '1,0');
  ok(g.m.tiles.get('0,0').gold === 0, 'a moved unit kept its fortification coin');
}
{
  const g = board([[0, 0, 'plains', 0], [1, 0, 'plains', 0]]);
  g.m.tiles.get('1,0').gold = 1;
  g.m.tiles.get('0,0').units.push(0);
  g._doMove(g.P[0], '0,0', '1,0');
  ok(g.m.tiles.get('1,0').gold === 0, 'stacking onto a fortified tile left the coin');
}

console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : 'movement: land crosses your own network and steps off, sea crosses open '
    + 'water only, rivals block both, capacity holds, the water advantage pays '
    + 'once a turn and only for a real sea move, coins fall off disturbed units');
process.exit(fail.length ? 1 : 0);
