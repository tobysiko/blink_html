/* HOMELANDS: every player starts with all four terrains, and chooses where
 * they face.
 *
 * The printed setup lays the whole starting map before anyone touches
 * anything: a block of Mountains and one Plains per player around it.
 * `startLayout: "homelands"` lays only the Mountains, then walks the table in
 * initiative order — the player who leads the first trick first — and has each
 * player add a Forest touching their Mountain, a Plains touching both, and an
 * Ocean touching the Plains. The first unit stands on the Plains.
 *
 * The order is the compensation: the seat that lays its meld last into a trick
 * where ties go to whoever played earlier is the seat that places its tiles
 * knowing the most about the map.
 *
 * One legality rule, asserted below, and it is the only thing stopping the
 * last placer from parking on top of the first: your Plains may not touch
 * another player's Plains.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };
const near = (a, b) => E.nbrKeys(a[0], a[1]).includes(E.K(b[0], b[1]));

/* ---- the printed layout is untouched ---- */
{
  for (const n of [2, 3, 4]) {
    const g = new E.Game(n, 5, { humans: [] });
    ok(g.m.tiles.size === 2 * n, `printed ${n}p setup no longer lays 2 tiles a player`);
    const ter = {};
    for (const t of g.m.tiles.values()) ter[t.terrain] = (ter[t.terrain] || 0) + 1;
    ok(ter.mountain === n && ter.plains === n && !ter.forest && !ter.ocean,
       `printed ${n}p setup is no longer mountains and plains only`);
  }
}

/* ---- nothing but the block exists until the players place ---- */
{
  const g = new E.Game(4, 5, { humans: [], startLayout: 'homelands' });
  ok(g.m.tiles.size === 4, 'homelands setup laid more than the mountain block');
  ok([...g.m.tiles.values()].every((t) => t.terrain === 'mountain'),
     'something other than a mountain was on the board before anyone placed');
  ok([...g.m.tiles.values()].every((t) => !t.units.length),
     'a unit was on the board before its owner had placed a plains');
  ok(g.m.starts.length === 0, 'starts were recorded before anyone had a homeland');
}

/* ---- what the table looks like once everyone has placed ---- */
for (const n of [2, 3, 4]) {
  const g = E.playOut(n, 40 + n, { humans: [], startLayout: 'homelands', maxRounds: 1 });
  const seen = {};
  for (const t of g.m.tiles.values()) seen[t.terrain] = (seen[t.terrain] || 0) + 1;
  ok(g.finished(), `a ${n}-player homelands game did not end`);
  ok(g.m.starts.length === n, `${n}p: not every player ended up with a start tile`);
  for (const c of g.m.starts) {
    const t = g.m.tiles.get(E.K(c[0], c[1]));
    ok(t && t.terrain === 'plains', `${n}p: a start tile is not a plains`);
  }
}

/* ---- the shape of one homeland, checked the moment it is laid ---- */
{
  for (const n of [2, 3, 4]) {
    /* Every seat human, so the generator stops at each placement and the board
       can be read the moment setup ends and before a single card is played.
       With no humans the whole round runs without ever yielding, and what you
       measure then is a round of play, not a setup. */
    const seats = []; for (let i = 0; i < n; i++) seats.push(i);
    const g = new E.Game(n, 12, { humans: seats, startLayout: 'homelands',
                                 handSetup: 'deal' });
    const it = g.playRound();
    let r = it.next();
    while (!r.done && r.value && r.value.type === 'homeland')
      r = it.next(r.value.options[0]);
    /* Four tiles a player: the mountain they were given and the three they
       added. Nothing else is on the board yet. */
    ok(g.m.tiles.size === 4 * n,
       `${n}p: ${g.m.tiles.size} tiles after setup, wanted ${4 * n}`);
    const ter = {};
    for (const t of g.m.tiles.values()) ter[t.terrain] = (ter[t.terrain] || 0) + 1;
    for (const k of ['mountain', 'forest', 'plains', 'ocean'])
      ok(ter[k] === n, `${n}p: ${ter[k] || 0} ${k} tiles at setup, wanted ${n}`);

    const plains = [...g.m.tiles.values()].filter((t) => t.terrain === 'plains');
    ok(plains.length === n, `${n}p: wrong number of plains`);
    for (const t of plains) {
      ok(t.units.length === 1, `${n}p: a starting plains does not hold exactly one unit`);
      const seat = t.units[0];
      const cell = E.unK(t.key);
      const mine = [...g.m.tiles.values()];
      const mt = mine.filter((u) => u.terrain === 'mountain' && near(cell, E.unK(u.key)));
      const fo = mine.filter((u) => u.terrain === 'forest' && near(cell, E.unK(u.key)));
      ok(mt.length >= 1, `${n}p: seat ${seat}'s plains touches no mountain`);
      ok(fo.length >= 1, `${n}p: seat ${seat}'s plains touches no forest`);
      const oc = mine.filter((u) => u.terrain === 'ocean' && near(cell, E.unK(u.key)));
      ok(oc.length >= 1, `${n}p: seat ${seat}'s plains touches no ocean`);
    }
    /* THE ONE LEGALITY RULE. */
    for (const a of plains) for (const b of plains) {
      if (a === b) continue;
      ok(!near(E.unK(a.key), E.unK(b.key)),
         `${n}p: two starting plains ended up next to each other`);
    }
    /* The tile supply paid for every tile that went down. */
    for (const k of ['mountain', 'forest', 'plains', 'ocean'])
      ok(g.m.supply[k] === 15 - n, `${n}p: the ${k} supply does not account for setup`);
  }
}

/* ---- a human is asked, in initiative order, and is obeyed ---- */
{
  const g = new E.Game(3, 21, { humans: [0, 1, 2], startLayout: 'homelands',
                                handSetup: 'deal' });
  const it = g.playRound();
  let r = it.next(), asked = [], picked = [];
  while (!r.done && r.value && r.value.type === 'homeland') {
    ok(r.value.options.length > 0, 'a player was asked to place with nowhere legal to place');
    asked.push(r.value.seat + ':' + r.value.stage);
    /* Answer with the LAST option rather than the first, so a game that quietly
       ignored the answer and used its own default would show up here. */
    const pick = r.value.options[r.value.options.length - 1];
    picked.push(pick);
    r = it.next(pick);
  }
  ok(asked.length === 9, `a 3-player setup asked ${asked.length} questions, wanted 9`);
  ok(asked.slice(0, 3).join() === '0:forest,0:plains,0:ocean',
     'the start player was not asked first, forest then plains then ocean: ' + asked.slice(0, 3));
  ok(asked[3].startsWith('1:') && asked[6].startsWith('2:'),
     'setup did not go clockwise from the start player: ' + asked.join(' '));
  for (const k of picked)
    ok(g.m.tiles.has(k), 'a cell the player chose was not the cell that was laid: ' + k);
}

/* ---- and a full game still finishes at every count ---- */
{
  for (const n of [2, 3, 4]) {
    const g = E.playOut(n, 90 + n, { humans: [], startLayout: 'homelands' });
    ok(g.finished(), `a ${n}-player homelands game did not end`);
    ok(g.m.tiles.size > 4 * n, `${n}p: the map never grew past its setup`);
  }
}

if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
console.log('homelands: the block is laid, then each player in initiative order adds forest, '
  + 'plains and ocean of their own; no two starting plains touch; the printed setup is unchanged');
