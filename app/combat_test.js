/* Combat as a duel.
 *
 * An attack declares a duel: both sides may commit one card from hand, the
 * defender adds the terrain's bonus, higher total wins, a level fight goes to
 * the card matching the ground and otherwise to the defender.
 *
 * THIS FILE WAS REWRITTEN ONCE, AND THE REASON IS WORTH KEEPING. The first
 * version measured the rule the way everything else here is measured — play a
 * few hundred bot games and count. It asserted that attackers win less often on
 * Mountain than on Plains, and it passed. Then the bot was taught to look at
 * its hand before picking a fight, and the file broke: not because the rule
 * changed, but because a bot that avoids bad fights stops generating them.
 * Mountain duels went to ZERO and there was nothing left to take a rate over.
 *
 * A measurement that a better opponent can delete was never measuring the rule.
 * So the rule is now tested where it lives — `duelWinner` is a pure function of
 * two cards and a patch of ground — and the simulator is used only for what it
 * is actually good at: proving that thousands of games do not crash, do not
 * leak cards, and do still contain fights.
 *
 * The subtle one is TIMING. A duel is the only place a hand empties on someone
 * ELSE's turn, so the ordinary end-of-turn recycle never runs for the defender
 * — and a player with no cards cannot play a meld, which section 05 requires.
 * That bug crashed 26 games in 60 before it was found.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };
const card = (r, s) => ({ r, s });

// ------------------------------------------------------- the terrain bonus
ok(E.TERRAIN_DEFENCE.plains === 0 && E.TERRAIN_DEFENCE.ocean === 0,
   'open ground should give no defence bonus');
ok(E.TERRAIN_DEFENCE.forest === 1, `Forest gives ${E.TERRAIN_DEFENCE.forest}, not 1`);
ok(E.TERRAIN_DEFENCE.mountain === 2, `Mountain gives ${E.TERRAIN_DEFENCE.mountain}, not 2`);

// --------------------------------------------------------- it is the rule
ok(E.playOut(3, 7, {}).COMBAT === 'duel', 'the duel is not the default combat');
ok(E.playOut(3, 7, { combat: 'gold' }).COMBAT === 'gold',
   'the older flat-gold rule can no longer be selected for comparison');

// ------------------------------------------------ the rule itself, exactly
{
  const w = (a, d, t) => E.duelWinner(a, d, t);

  // rank alone, on open ground
  ok(w(card(9, 'ocean'), card(8, 'ocean'), 'plains'), 'the higher rank should win on Plains');
  ok(!w(card(8, 'ocean'), card(9, 'ocean'), 'plains'), 'the lower rank should lose on Plains');

  // the defender holds a level fight when neither card is of the ground
  ok(!w(card(9, 'ocean'), card(9, 'forest'), 'plains'),
     'a level fight on Plains should go to the defender');

  // ...and the ground breaks it when exactly one card matches
  ok(w(card(9, 'plains'), card(9, 'forest'), 'plains'),
     "the attacker's matching card should break a level fight");
  ok(!w(card(9, 'ocean'), card(9, 'plains'), 'plains'),
     "the defender's matching card should hold a level fight");
  ok(!w(card(9, 'plains'), card(9, 'plains'), 'plains'),
     'two matching cards should leave the tie with the defender');

  /* THE TERRAIN BONUS BITES — the same attack, tile for tile. This is the
   * claim the old bot-rate test was reaching for, and here it is exact. */
  const a = card(10, 'ocean'), d = card(9, 'ocean');
  ok(w(a, d, 'plains'), '10 should beat 9 on Plains');
  ok(w(a, d, 'ocean'), '10 should beat 9 on Ocean');
  ok(!w(a, d, 'forest'), '10 should NOT beat 9 on Forest (+1 makes it level)');
  ok(!w(a, d, 'mountain'), '10 should NOT beat 9 on Mountain (+2)');
  ok(w(card(12, 'ocean'), d, 'mountain'), '12 should beat 9 on Mountain (+2)');

  /* How much rank the ground is worth, read back out of the rule rather than
   * out of the table it came from. */
  for (const [ter, bonus] of Object.entries(E.TERRAIN_DEFENCE)) {
    const need = [...Array(21).keys()].find((r) => w(card(r, 'x'), card(10, 'y'), ter));
    ok(need === 11 + bonus,
       `on ${ter} an attacker needs ${need} to beat a 10, expected ${11 + bonus}`);
  }

  // declining is legal and simply loses
  ok(!w(null, card(1, 'x'), 'plains'), 'an attacker who declines cannot win');
  ok(!w(null, null, 'plains'), 'if nobody commits a card, the defender holds');
  ok(w(card(1, 'x'), null, 'plains'), 'a defender who declines on open ground loses to anything');
  ok(!w(card(2, 'x'), null, 'mountain'),
     'a defender who declines on a Mountain still has the ground under them');
}

// -------------------------------- the attacker never pays twice for one attack
/* The rule as first built asked the attacker for a card from HAND on top of
 * the meld card already spent on the tile. Two cards for one attack is not
 * what the rules charge, and it left the rank of the spent card meaning
 * nothing — you could storm a Mountain with a 2 as long as you held a 19 back.
 * Now the card you spend IS the attack, and only the defender is asked. */
{
  const g = new E.Game(3, 77, { humans: [] });
  const tile = [...g.m.tiles.values()]
    .find((t) => t.owner !== null && t.units.length === 1 && !t.gold);
  const me = g.P[(tile.owner + 1) % g.P.length];
  const before = me.hand.length;
  g.P[tile.owner].hand = [{ r: 2, s: 'ocean' }];       // a token defence
  const it = g._duel(me, tile.key, tile, { r: 18, s: tile.terrain });
  let r = it.next(), asked = [];
  while (!r.done) { asked.push(r.value && r.value.type); r = it.next(null); }
  ok(!asked.includes('duel') || asked.length <= 1,
     `the engine asked ${asked.length} questions for one attack: ${asked}`);
  ok(me.hand.length === before,
     'the attacker lost a card from hand — the spent card is the whole attack');
  ok(tile.owner === me.i, 'an 18 against a 2 did not take the tile');
}

/* ...and the rank of the spent card is what decides it. Same defender, same
 * ground, two different cards spent. */
{
  const fight = (rank) => {
    const g = new E.Game(3, 77, { humans: [] });
    const tile = [...g.m.tiles.values()]
      .find((t) => t.owner !== null && t.units.length === 1 && !t.gold);
    const me = g.P[(tile.owner + 1) % g.P.length];
    g.P[tile.owner].hand = [{ r: 9, s: 'ocean' }];
    const it = g._duel(me, tile.key, tile, { r: rank, s: 'ocean' });
    let r = it.next();
    while (!r.done) r = it.next(null);
    return tile.owner === me.i;
  };
  ok(fight(20), 'a 20 lost to a 9 on open ground');
  ok(!fight(3), 'a 3 beat a 9 — the spent card is not deciding the fight');
}

// ------------------------------ a coin is a WALL now; the assault is an option
/* The rule this replaces let a coin absorb an attack outright. It read well and
 * measured terribly: once the bots learned that hitting a wall bought nothing,
 * walls were never hit again — ZERO absorbs in 360 games, with 8.5 coins still
 * sitting on the map at final scoring. A rule no competent player triggers is
 * not a rule.
 *
 * The assault replaced it — two cards, the lower rank fighting — and the WALL
 * replaced the assault: the coin defends at the tier ladder and one card may
 * always try. Both older rules stay reachable as options, and both are still
 * tested here, because the engine still offers them.
 */
{
  // the printed rule: a lone card may attack a wall, and beat it or not
  const g = new E.Game(3, 4242, { humans: [] });
  const tile = [...g.m.tiles.values()].find((t) => t.owner !== null && t.units.length);
  const me = (tile.owner + 1) % g.P.length;
  tile.gold = 1;
  const card = { r: 12, s: tile.terrain };
  const reachable = new Set(g.m.tiles.keys());
  const alone = E.cardOptions(g.m, card, me, 9, reachable, g.m.legalSpaces(), 0);
  ok(alone.some(([k, a]) => k === tile.key && a === 'attack'),
     'a lone card was refused a fortified tile — the wall is a floor, not a veto');
}

{
  // ...and under the assault OPTION, one card is refused outright
  const g = new E.Game(3, 4242, { humans: [], fortify: 'assault' });
  const tile = [...g.m.tiles.values()].find((t) => t.owner !== null && t.units.length);
  const me = (tile.owner + 1) % g.P.length;
  tile.gold = 1;
  const card = { r: 12, s: tile.terrain };
  const reachable = new Set(g.m.tiles.keys());
  const alone = E.cardOptions(g.m, card, me, 9, reachable, g.m.legalSpaces(), 0);
  ok(!alone.some(([k, a]) => k === tile.key && a === 'attack'),
     'a lone card was offered an attack on a fortified tile');
  const backed = E.cardOptions(g.m, card, me, 9, reachable, g.m.legalSpaces(), 1);
  ok(backed.some(([k, a]) => k === tile.key && a === 'attack'),
     'a fortified tile stayed un-attackable even with a second card in hand');
  // and the map says WHY, rather than going quiet
  const why = E.cardBlocked(g.m, card, me, 9, reachable, 0);
  ok(why.some(([k, r]) => k === tile.key && r === 'wall'),
     'the refusal is silent — the map gives no reason for a fortified tile');
}

{
  // ...two cards break the wall, and the LOWER rank fights — the assault option
  const g = new E.Game(3, 4242, { humans: [], fortify: 'assault' });
  const tile = [...g.m.tiles.values()]
    .find((t) => t.owner !== null && t.units.length === 1);
  const me = g.P[(tile.owner + 1) % g.P.length];
  tile.gold = 1;
  const lead = { r: 20, s: tile.terrain };
  const pool = [{ r: 4, s: 'ocean' }];        // a poor second card drags it down
  g.P[tile.owner].hand = [{ r: 8, s: 'plains' }];   // defends at 8 + the ground
  const it = g._assault(me, tile.key, tile, lead, pool);
  let r = it.next();
  while (!r.done) r = it.next(null);
  ok(tile.gold === 0, 'the coin was not spent by the assault');
  ok((g.stats.assaults || 0) === 1, 'the assault was not recorded');
  ok(pool.length === 0, 'the second card was not taken out of the meld');
  /* 20 and 4 make an attack of FOUR, which loses to a defended 8. If the rule
   * took the higher card this would have been a walkover. */
  ok(tile.units.length === 1,
     'a 20 backed by a 4 took the tile — the assault used the higher rank');
  ok((g.stats.duel_held || 0) === 1, 'the defender was not credited with holding');
}

{
  // ...and two good cards do take it
  const g = new E.Game(3, 4242, { humans: [] });
  const tile = [...g.m.tiles.values()]
    .find((t) => t.owner !== null && t.units.length === 1);
  const me = g.P[(tile.owner + 1) % g.P.length];
  tile.gold = 1;
  const pool = [{ r: 19, s: 'ocean' }];
  g.P[tile.owner].hand = [{ r: 8, s: 'plains' }];
  const it = g._assault(me, tile.key, tile, { r: 20, s: tile.terrain }, pool);
  let r = it.next();
  while (!r.done) r = it.next(null);
  ok(tile.owner === me.i, 'two high cards failed to break a wall');
  ok((g.stats.wall_broken || 0) === 1, 'the wall was not recorded as broken');
}

// ------------------------------------------- a won duel takes the ground
/* The change that made combat worth doing at all — see DUEL-SPOILS.md. Built
 * by hand, because it only fires on the LAST defender and a bot game gives no
 * control over when that happens. */
{
  const g = new E.Game(3, 909, { humans: [] });
  const tile = [...g.m.tiles.values()]
    .find((x) => x.owner !== null && x.units.length === 1 && !x.gold);
  const me = g.P[(tile.owner + 1) % g.P.length];
  const victim = tile.owner;
  g.P[victim].hand = [];                          // certain not to be beaten
  const reserve = me.reserve.slice();
  /* The attack is the card spent on the tile, so it is passed in rather than
   * asked for — the attacker's own hand is not consulted at all. */
  const it = g._duel(me, tile.key, tile, { r: 20, s: tile.terrain });
  let r = it.next();
  while (!r.done) r = it.next(null);
  ok(tile.owner === me.i, `the winner did not take the tile (owner ${tile.owner})`);
  ok(tile.units.length === 1, `the tile holds ${tile.units.length} units after the duel`);
  ok(String(reserve) !== String(me.reserve), 'the settled unit did not come off the board');
  ok((g.stats.duel_settle || 0) === 1, 'the settle was not recorded');
}

/* ...but only the LAST defender. A stack that still has someone standing is
 * not yours, and taking it would make one card worth three. */
{
  const g = new E.Game(3, 909, { humans: [] });
  const tile = [...g.m.tiles.values()].find((x) => x.owner !== null && !x.gold);
  const victim = tile.owner;
  while (tile.units.length < 2) tile.units.push(victim);
  const me = g.P[(victim + 1) % g.P.length];
  g.P[victim].hand = [];
  const it = g._duel(me, tile.key, tile, { r: 20, s: tile.terrain });
  let r = it.next();
  while (!r.done) r = it.next(null);
  ok(tile.owner === victim, 'a tile with a defender still standing changed hands');
  ok((g.stats.duel_settle || 0) === 0, 'a settle was recorded on a tile still held');
}

/* And it can be switched off, to reproduce every number measured before it. */
ok(E.playOut(3, 7, {}).DUEL_TAKE === true, 'a won duel no longer takes the ground');
ok(E.playOut(3, 7, { duelTake: false }).DUEL_TAKE === false,
   'the older spoils cannot be selected for comparison');

// --------------------------------------------------- the frontier pays
/* Gold, not appetite, is what limits fortification: holding everything else
 * still and varying only the surplus a bot keeps back moves walls built from
 * 19.9 a game to 0.6. So exploring with a starting-deck card now pays a coin —
 * measured at +4.2 gold a game, walls 2.9 to 3.5, and the upgrade race
 * untouched at 34.4.
 *
 * The boundary is the one that explains itself: rank 10 is the top of every
 * starting deck and the bottom of the market. */
{
  const g = E.playOut(3, 7, {});
  ok(g.FRONTIER === 'low', `the frontier rule defaults to ${g.FRONTIER}`);
  ok(g.FRONTIER_RANK === 10, `the frontier pays up to ${g.FRONTIER_RANK}, not 10`);
  ok(E.playOut(3, 7, { frontier: 'off' }).FRONTIER === 'off',
     'the older economy cannot be selected for comparison');

  let paid = 0, explored = 0, off = 0;
  for (const n of [2, 3, 4]) for (let s = 0; s < 40; s++) {
    const a = E.playOut(n, (s * 40503) % 2147483647, {});
    paid += a.stats.frontier_paid || 0;
    explored += a.stats.explore || 0;
    off += E.playOut(n, (s * 40503) % 2147483647, { frontier: 'off' })
             .stats.frontier_paid || 0;
  }
  ok(paid > 0, 'no explore ever paid a coin');
  ok(paid < explored, `every one of ${explored} explores paid — the rank gate is not biting`);
  ok(off === 0, 'the frontier paid even with the rule turned off');
}

// ------------------------------------------ nobody arrives with no cards
// The regression that started this: a defender spends out of turn, their hand
// empties, and nothing recycles it.
{
  let crashed = 0, emptyMelds = 0, played = 0;
  for (const n of [2, 3, 4]) {
    for (let s = 0; s < 80; s++) {
      try {
        const g = E.playOut(n, (s * 2654435761) % 2147483647, {});
        played += 1;
        emptyMelds += (g.stats && g.stats.meld_from_empty_hand) || 0;
        for (const p of g.P) ok(p.hand.length <= 10, `a hand grew to ${p.hand.length}`);
      } catch (e) { crashed += 1; }
    }
  }
  ok(crashed === 0, `${crashed} games crashed with the duel on`);
  ok(emptyMelds === 0,
     `${emptyMelds} melds were played from an empty hand — the out-of-turn recycle is leaking`);
  ok(played === 240, `only ${played} games finished`);
}

// ------------------------------------------- fights still happen at a table
/* Not a balance reading — a liveness one. If the whole game can be played
 * without a single duel, the rule is decorative. */
{
  const st = {};
  for (const n of [2, 3, 4])
    for (let s = 0; s < 100; s++) {
      const g = E.playOut(n, (s * 40503) % 2147483647, {});
      for (const k in g.stats || {}) st[k] = (st[k] || 0) + g.stats[k];
    }
  ok((st.duels || 0) > 0, 'three hundred games contained no duel at all');
  ok((st.duel_won || 0) > 0, 'no attack ever succeeded');
  ok((st.duel_held || 0) > 0, 'no defender ever held');
  const rate = (t) => {
    const n = st['duel_on_' + t] || 0;
    return n ? `${(100 * (st['duel_won_on_' + t] || 0) / n).toFixed(0)}% of ${n}` : 'none';
  };
  /* Printed, never asserted. Both numbers are bot policy: the bot chooses when
   * to fight AND which card to spend, so a change to either moves these without
   * the rule moving at all. That is precisely what happened to the version of
   * this file that asserted them. */
  console.log(`    (${st.duels} duels · attacker takes the tile: `
    + ['plains', 'ocean', 'forest', 'mountain'].map((t) => `${t} ${rate(t)}`).join(' · ')
    + ' — bot policy, not a balance reading)');
}

// --------------------------------------------- the game still works at all
{
  for (const n of [2, 3, 4]) {
    let rounds = 0, score = 0, seats = 0;
    for (let s = 0; s < 60; s++) {
      const g = E.playOut(n, (s * 2654435761) % 2147483647, {});
      rounds += g.round;
      for (const x of g.score()) { score += x.total; seats += 1; }
    }
    const r = rounds / 60, sc = score / seats;
    ok(r > 5 && r < 30, `${n}p games run ${r.toFixed(1)} rounds`);
    ok(sc > 10 && sc < 80, `${n}p seats score ${sc.toFixed(1)}`);
  }
}

console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : 'combat: an attack is a duel — the card you SPEND is the attack, the defender '
    + 'answers from hand, and the ground is added to them (0/0/1/2). The rule is '
    + 'checked card by card rather than by counting bot fights. A coin does not '
    + 'stop an attack: it is a WALL, defending at the tier ladder unless a better '
    + 'card from hand fights instead, and one card may always try. Clear the last '
    + 'defender and the ground changes hands; leave one standing and it does not. '
    + "A hand emptied on somebody else's turn recycles instead of arriving at the "
    + 'card phase with nothing');
process.exit(fail.length ? 1 : 0);
