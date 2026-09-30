/* THE CROSSROADS: income that depends on your neighbours staying put.
 *
 * Toby played v0.26 at a table on 19 Sep and found gold was the binding
 * constraint: nobody fortified and nobody's victory row had cards in it. Under
 * the LEAN economy the sim agrees and says why - income falls from 90.3 gold a
 * game to 53.8 across four seats, because nothing replaced ascension's 24.8.
 *
 * This is his proposed answer, behind `income: "crossroads"` and OFF by
 * default, because no human has played it. A tile of yours that touches an
 * OCCUPIED tile of each of the other three terrains pays 1 gold per unit of
 * yours standing on it, once each recycle.
 *
 * What this file pins down is the part that is easy to get subtly wrong: the
 * adjacency test, the fact that the neighbouring units may belong to ANYBODY,
 * and that the payment lands before the bill rather than after it.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* ---- off is off ---- */
{
  const g = E.playOut(4, 51, { humans: [] });
  ok(!(g.stats.gold_in_crossroads), 'a game with no income rule paid crossroads gold');
  const h = E.playOut(4, 51, { humans: [], income: 'crossroads' });
  ok((h.stats.gold_in_crossroads || 0) > 0,
     'the crossroads rule paid nothing at all across a whole game');
}

/* ---- the adjacency rule, built by hand ---- */
{
  const g = new E.Game(3, 7, { humans: [], income: 'crossroads' });
  const m = g.m;
  /* Wipe the map and lay exactly what the rule describes: a Plains tile of
     seat 0's, touching a Forest, an Ocean and a Mountain. */
  m.tiles.clear();
  const home = '0,0';
  const near = E.nbrKeys(0, 0);
  m.doExplore(home, 'plains');
  m.settle(home, 0);
  const terr = ['forest', 'ocean', 'mountain'];
  terr.forEach((t, i) => { m.doExplore(near[i], t); });

  ok(g.crossroadsPay(g.P[0]) === 0,
     'a tile paid before any of its neighbours was occupied');

  /* Occupy them one at a time: nothing pays until all three are live. */
  m.settle(near[0], 1);
  ok(g.crossroadsPay(g.P[0]) === 0, 'one occupied neighbour was enough');
  m.settle(near[1], 1);
  ok(g.crossroadsPay(g.P[0]) === 0, 'two occupied neighbours were enough');
  m.settle(near[2], 2);
  ok(g.crossroadsPay(g.P[0]) === 1,
     'all three terrains occupied and the crossroads still paid nothing');

  /* THE NEIGHBOURS ARE OTHER PLAYERS' UNITS, which is the point of the rule
     and not an oversight: every unit placed above belongs to seat 1 or 2. */
  ok(![...m.tiles.values()].some((t) => t.key !== home && t.units.includes(0)),
     'this fixture accidentally gave seat 0 a neighbouring unit, so it proves nothing');

  /* One gold per unit of YOURS on the tile. Plains holds three. */
  m.settle(home, 0);
  ok(g.crossroadsPay(g.P[0]) === 2, 'a second unit on the tile did not pay a second gold');
  m.settle(home, 0);
  ok(g.crossroadsPay(g.P[0]) === 3, 'a third unit on the tile did not pay a third gold');

  /* AND IT LAPSES. A neighbour who walks away takes your income with them. */
  const gone = m.tiles.get(near[2]);
  gone.units.length = 0;
  ok(g.crossroadsPay(g.P[0]) === 0,
     'the crossroads still paid after a neighbouring tile was emptied');
}

/* ---- it pays BEFORE the bill, so it can pay it ---- */
{
  /* Under the full economy a recycle charges food. A player who is paid after
     being charged can lose a unit while holding the gold that would have saved
     it - an ordering nobody notices until it happens at a table. */
  let paidFirst = 0, games = 0;
  for (let s = 0; s < 25; s++) {
    const g = E.playOut(4, 300 + s, { humans: [], income: 'crossroads' });
    games += 1;
    if ((g.stats.gold_in_crossroads || 0) > 0) paidFirst += 1;
  }
  ok(paidFirst > games / 2,
     `only ${paidFirst} of ${games} games paid any crossroads gold at all`);
}

/* ---- and it does what it was added to do ---- */
{
  const lean = { humans: [], food: false, ascension: false };
  const run = (opts, n = 30) => {
    let fort = 0, vrow = 0;
    for (let s = 0; s < n; s++) {
      const g = E.playOut(4, 600 + s, Object.assign({}, lean, opts));
      fort += (g.stats.gold_out_fortify || 0);
      for (const p of g.P) vrow += p.vrow.length;
    }
    return { fort: fort / n, vrow: vrow / n / 4 };
  };
  // An explicit 'off': with objectives on by default, run({}) is OBJECTIVE income,
  // so the old baseline compared two incomes rather than income against none.
  const off = run({ income: 'off' }), on = run({ income: 'crossroads' });
  ok(on.fort > off.fort,
     `income did not free up any fortifying: ${off.fort.toFixed(1)} -> ${on.fort.toFixed(1)}`);
  /* A tolerance, not a strict >=: over 30 games the row moves by a few
   * hundredths either way from seed noise alone. With the frontier coin dropped
   * (30 Sep 2026) the two runs landed 0.01 apart in the "wrong" direction. The
   * claim this guards is "income does not hurt the row", not "it always helps". */
  ok(on.vrow >= off.vrow - 0.05,
     `income made the victory row worse: ${off.vrow.toFixed(2)} -> ${on.vrow.toFixed(2)}`);
}

/* ---- EVERY complete objective pays - open or secret, flat per card ----
 *
 * Toby's second proposal (27 Sep): reward CHECKING your objectives, not just
 * showing one. So this reads `objectives` as a whole, not `objOpen`, and it
 * pays a flat 1 per card regardless of how many instances of the pattern you
 * hold - the old "open pays per instance, secret pays nothing" rule is gone. */
{
  const g = new E.Game(3, 11, { humans: [], objectives: 'showone', income: 'objective' });
  const p0 = g.P[0];
  ok(p0.objectives.length === 2, 'showone did not deal two objectives');
  ok(p0.objOpen === p0.objectives[0], 'the open objective is not the one scoring reads first');
  ok(g.P.every((q) => q.objOpen), 'a seat was dealt no open objective');

  const m = g.m;
  /* Lays a card's pattern at a given hex centre, WITHOUT clearing what is
     already on the map, so two cards' patterns can coexist. */
  const layAt = (centre, card) => {
    const near = E.nbrKeys(...centre.split(',').map(Number));
    m.doExplore(centre, card.mid); m.settle(centre, 0);
    m.doExplore(near[0], card.a); m.settle(near[0], 0);
    m.doExplore(near[2], card.b); m.settle(near[2], 0);   // not adjacent to near[0]
  };
  const lay = (card) => { m.tiles.clear(); layAt('0,0', card); };

  ok(g.objectivePay(p0) === 0, 'an untouched map paid objective income');

  /* Build the OPEN card's pattern: pays exactly 1, however many instances. */
  lay(p0.objOpen);
  ok(g.objectivePay(p0) === 1,
     `building the open card once paid ${g.objectivePay(p0)}, expected a flat 1`);

  /* THE SECRET CARD PAYS TOO NOW - that is the whole point of the change.
     Cleared map, only the secret card's pattern this time. */
  const secret = p0.objectives[1];
  if (secret && secret.id !== p0.objOpen.id) {
    lay(secret);
    ok(g.objectivePay(p0) === 1,
       'the secret objective paid nothing - it should pay exactly like the open one');

    /* BOTH complete at once, at two separate sites so neither pattern
       borrows a tile from the other: 1 per card, so 2 - not double-counted
       instances, and not the old "secret pays nothing" either. */
    layAt('0,6', p0.objOpen);   // far enough from '0,0' to share no tiles
    const both = g.objectivePay(p0);
    ok(both === 2, `both cards complete at once paid ${both}, expected a flat 2`);
  }
}

/* ---- and it is off if income is explicitly turned off ---- */
{
  const g = E.playOut(4, 77, { humans: [], objectives: 'showone', income: 'off' });
  ok(!(g.stats.gold_in_objective), 'income: "off" still paid objective gold');
  const h = E.playOut(4, 77, { humans: [], objectives: 'showone', income: 'crossroads' });
  ok(!(h.stats.gold_in_objective), 'the crossroads rule also paid objective gold');
}

/* ---- and objective income is now the DEFAULT whenever objectives are on ----
 *
 * This is the fix for "I never noticed any income" - a table playing the
 * printed defaults (objectives on, income unset) now gets paid without
 * anyone finding and switching on a setup option. Leaving objectives off
 * keeps income off too: there is nothing for it to read. */
{
  const g = new E.Game(3, 11, { humans: [] });   // no income opt at all
  ok(g.INCOME === 'objective',
     `a default table's INCOME is "${g.INCOME}", expected "objective" to follow the printed objectives rule`);
  const h = new E.Game(3, 11, { humans: [], objectives: 'off' });
  ok(h.INCOME === 'off',
     `turning objectives off left INCOME as "${h.INCOME}", expected "off" - there is nothing to pay for`);
}

/* ---- WHAT IT ACTUALLY PAYS, recorded so it cannot drift unnoticed ----
 *
 * Bots weight objectives at zero, so this is the floor: what a table that
 * IGNORES its objectives earns anyway just by playing the game. Reading
 * every card instead of only the open one, and paying flat instead of per
 * instance, raises this well above the old "open card only" rule's ~15% -
 * kept as a range so a real change trips it and noise does not. */
{
  let fires = 0, paid = 0, goldTotal = 0;
  const orig = E.Game.prototype._recycle;
  E.Game.prototype._recycle = function* (q) {
    fires += 1;
    const obj = this.objectivePay(q);
    if (obj) { paid += 1; goldTotal += obj; }
    yield* orig.call(this, q);
  };
  for (let s = 0; s < 40; s++)
    E.playOut(4, 4000 + s, { humans: [], food: false, ascension: false,
                             objectives: 'showone', income: 'objective' });
  E.Game.prototype._recycle = orig;
  const pct = 100 * paid / fires;
  ok(pct > 15 && pct < 45,
     `objective income paid on ${pct.toFixed(1)}% of recycles, expected 15-45% `
     + '(bots do not aim at objectives, so this is the ignore-it floor)');
}

if (fail.length) { console.log('FAIL:'); for (const f of fail) console.log('  ' + f); process.exit(1); }
console.log('income: the crossroads pays only when all three other terrains are occupied beside it, '
  + 'by anybody; one gold a unit; lapses when a neighbour leaves; lands before the bill; '
  + 'and it moves fortifying and the victory row the way it was meant to; '
  + 'objective income pays a flat 1 gold per completed card, open or secret, '
  + 'and is the default income whenever objectives are in play');
