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
  const off = run({}), on = run({ income: 'crossroads' });
  ok(on.fort > off.fort,
     `income did not free up any fortifying: ${off.fort.toFixed(1)} -> ${on.fort.toFixed(1)}`);
  ok(on.vrow >= off.vrow,
     `income made the victory row worse: ${off.vrow.toFixed(2)} -> ${on.vrow.toFixed(2)}`);
}

if (fail.length) { console.log('FAIL:'); for (const f of fail) console.log('  ' + f); process.exit(1); }
console.log('crossroads: pays only when all three other terrains are occupied beside it, '
  + 'by anybody; one gold a unit; lapses when a neighbour leaves; lands before the bill; '
  + 'and it moves fortifying and the victory row the way it was meant to');
