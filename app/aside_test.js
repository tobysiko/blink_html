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
  ok((a.stats.to_shared_pile || 0) === (b.stats.to_shared_pile || 0),
     `seed ${seed}: the shared pile was fed ${a.stats.to_shared_pile || 0} vs `
     + `${b.stats.to_shared_pile || 0} cards`);
  ok((a.stats.gold_in_docked || 0) === (b.stats.gold_in_docked || 0),
     `seed ${seed}: the set-aside paid a different number of coins`);
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
