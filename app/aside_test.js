/* WHEN THE SET-ASIDE IS RESOLVED — and the promise that it is only WHEN.
 *
 * The printed rule settles it at the top of each player's own map turn. The
 * variant settles every player's clockwise from the winner, right after the
 * trick, before anything moves on the map.
 *
 * The point of the change is not balance, it is a component: the coloured die
 * carries the winner's meld size only because the set-aside is read later than
 * the card phase. Settle it at the trick and the number is spent before the map
 * opens, the die stops carrying anything but its colour, and all four dice
 * become interchangeable — which is what an exploration roll would need, since
 * the winner cannot roll away a number three other players still have to read.
 *
 * So what this file asserts is that NOTHING ELSE MOVED: the same seats owe a
 * card, the same number of cards reach the shared pile, and a set-aside card is
 * still kept out of the meld that is about to be spent.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* One round, played to the point where every seat has taken its map turn. */
function oneRound(seed, timing) {
  const g = new E.Game(4, seed, { humans: [], asideTiming: timing });
  const it = g.playRound();
  let r = it.next(); while (!r.done) r = it.next(null);
  return g;
}

// ------------------------------------------------- the printed rule is intact
{
  const g = new E.Game(4, 5, { humans: [] });
  ok(g.ASIDE_AT_TRICK === false, 'the set-aside moved to the trick by default');
  ok(new E.Game(4, 5, { humans: [], asideTiming: 'turn' }).ASIDE_AT_TRICK === false,
     "asideTiming:'turn' did not select the printed rule");
}

// ------------------------------------- the rule is the same; only the clock moves
/* Round one is the fair comparison: after it the two games see different maps
 * and legitimately diverge. Within round one the trick is identical — same
 * seed, same deal, same melds — so exactly the same seats must owe a card. */
for (const seed of [3, 11, 29, 77, 101]) {
  const a = oneRound(seed, 'turn'), b = oneRound(seed, 'trick');
  ok((a.stats.docked_card || 0) === (b.stats.docked_card || 0),
     `seed ${seed}: ${a.stats.docked_card || 0} seats docked on the turn timing, `
     + `${b.stats.docked_card || 0} on the trick timing`);
  ok((a.stats.to_own_discard || 0) === (b.stats.to_own_discard || 0),
     `seed ${seed}: ${a.stats.to_own_discard || 0} cards reached their owner's `
     + `discard vs ${b.stats.to_own_discard || 0}`);
  ok((a.stats.gold_in_docked || 0) === (b.stats.gold_in_docked || 0),
     `seed ${seed}: the set-aside paid a different number of coins`);
}

// ------------------------------------ WHERE THE SET-ASIDE CARD ACTUALLY GOES
/* A MELD CARD NEVER LEAVES ITS OWNER. Only a victory-row card does.
 *
 * This was the other way round - the set-aside went to the shared market - and
 * nothing here or anywhere else checked it, so the routing was free to be
 * whatever the last edit left. It cost a player at the table: watching the
 * card fly to the middle, they reasonably asked whether it was gone for good.
 *
 * The change came out of the one human playtest: losing the card outright felt
 * too harsh. You still pay for matching the leader - the card is out of this
 * meld and out of this turn, and it returns only when your hand recycles.
 *
 * Checked on the cards themselves rather than on a counter, because a counter
 * is exactly what a wrong routing would keep incrementing. */
{
  const g = new E.Game(4, 42, { humans: [] });
  const it = g.playRound();
  let r = it.next(); while (!r.done) r = it.next(null);
  let checked = 0;
  for (const p of g.P) {
    if (!p.asideCard) continue;
    checked++;
    ok(p.discard.includes(p.asideCard),
       `seat ${p.i}'s set-aside card is not in that player's own discard`);
    ok(!g.pile.includes(p.asideCard),
       `seat ${p.i}'s set-aside card went to the SHARED market - a meld card `
       + 'never leaves its owner; only a victory-row card does');
  }
  ok(checked > 0, 'no seat set a card aside in this round, so nothing was tested');
  /* And the counters agree with the cards. */
  ok(!(g.stats.to_shared_pile || 0),
     `${g.stats.to_shared_pile} set-aside card(s) were counted into the shared market`);
}

// -------------------------------- the card is out of the meld before it is spent
/* Drive the trick pass by hand and look at what it parked on each player: the
 * card that went to the pile must NOT still be in the meld about to be played,
 * which is the bug that a second code path would reintroduce. */
{
  const g = new E.Game(4, 42, { humans: [], asideTiming: 'trick' });
  const it = g.playRound();
  let r = it.next(); while (!r.done) r = it.next(null);
  for (const p of g.P) {
    ok(Array.isArray(p.mapUse), `seat ${p.i} was never handed a meld to spend`);
    if (p.asideCard && p.mapUse)
      ok(!p.mapUse.includes(p.asideCard),
         `seat ${p.i} kept its set-aside card in the meld it then spent`);
  }
}

// ------------------------------------------------ and a whole game still runs
{
  for (const timing of ['turn', 'trick']) {
    const g = E.playOut(4, 9, { asideTiming: timing });
    ok(g.finished(), `a full game did not finish on the ${timing} timing`);
    ok((g.stats.docked_card || 0) > 0,
       `nobody ever matched the winner in a whole game (${timing})`);
  }
  /* And with everything else this session's variants can turn on at once. */
  const g = E.playOut(4, 9, { asideTiming: 'trick', food: false,
                              ascension: false, spoils: 'ground' });
  ok(g.finished(), 'the lean + spoils + trick-timing game did not finish');
}

if (fail.length) { console.error(fail.join('\n')); process.exit(1); }
console.log('aside_test ok');
