/* TRADE — the other face of an improvement.
 *
 * v0.26 gives a player two improvements a turn, the first costing 1 gold and
 * the second 2, and each one is either a RESEARCH or a TRADE. They share one
 * allowance. Research reaches UP: a card above anything in the starting deck,
 * paid for by retiring one of yours to the victory row. Trade reaches
 * SIDEWAYS: the top two of the shared pile into your hand, any two of yours
 * buried at its bottom. Nothing is retired and no rank is gained.
 *
 * What this file is really guarding is CONSERVATION and the SHARED ALLOWANCE.
 * The project's standing failure is a rule implemented twice and drifting, and
 * trade is the second implementation of an allowance research already owned -
 * so the tests that matter are: does a trade cost one of the two improvements,
 * does it charge the escalating price research would have charged, and are
 * there still exactly as many cards in the game afterwards.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* Every card in the game, wherever it is — the same census setupdeck_test.js
 * takes, by identity rather than by count, so a card that got duplicated shows
 * up as a shortfall rather than hiding inside a matching total. 80 cards, and
 * nothing ever leaves the game in v0.26. */
const where = (g) => {
  const seen = new Set();
  for (const p of g.P)
    for (const c of [...p.hand, ...p.discard, ...p.vrow,
                     ...(p.tableau || []), ...(p.played || [])]) seen.add(c);
  for (const c of [...g.deck, ...g.pile, ...g.grid.flat(),
                   ...(g.removed || [])]) seen.add(c);
  return [...seen];
};

// ------------------------------------------------------- the option itself
{
  const on = new E.Game(3, 5, { humans: [] });
  ok(on.TRADE === 'on', 'trade is not on by default in v0.26');
  const off = new E.Game(3, 5, { humans: [], trade: 'off' });
  ok(off.TRADE === 'off', "trade:'off' did not reach the engine");
  ok(on.TRADE_TAKE === 2, 'a trade does not take two cards');
}

// --------------------------------------- trade:'off' reproduces the v0.25 game
/* The option-preserving rule: every measurement taken before trade existed has
 * to still reproduce. Same seed, same bots, trade off - the whole game must be
 * identical to one built by an engine that never heard of trade, which is the
 * closest thing to that assertion we can make from inside: no seat ever
 * traded, and no gold ever left a purse for one. */
for (const seed of [3, 17, 44]) {
  const g = E.playOut(4, seed, { humans: [], trade: 'off' });
  ok(!g.stats.traded, `seed ${seed}: a seat traded with trade:'off'`);
  ok(!g.stats.gold_out_trade,
     `seed ${seed}: gold was spent on a trade with trade:'off'`);
}

// ------------------------------------------------ nothing leaves the game
/* 80 cards before, 80 cards after. A trade moves four cards across two piles
 * in opposite directions and is exactly the sort of thing that loses one. */
for (const seed of [7, 23, 61]) {
  const g = E.playOut(3, seed, { humans: [] });
  ok(g.finished(), `seed ${seed}: the game did not finish`);
  const after = where(g).length;
  ok(after === 80,
     `seed ${seed}: ${after} distinct cards after a game with trade on, not 80`);
  ok(g.stats.traded > 0, `seed ${seed}: no trade happened, so nothing was tested`);
}

// ----------------------------------------------- the bot does use it
{
  let traded = 0, games = 0;
  for (let seed = 1; seed <= 6; seed++) {
    const g = E.playOut(4, seed, { humans: [] });
    traded += g.stats.traded || 0; games++;
  }
  /* Not a balance claim - a wiring claim. A bot that never trades would make
   * every measurement of trade come back "no effect", which is how a rule
   * ships unmeasured. */
  ok(traded > 0, `no bot traded in ${games} games — the action is unreachable`);
}

// --------------------------------- one allowance, shared with research
/* Two improvements a turn, whichever face each wears. A turn cannot hold two
 * researches AND a trade. Asserted against the engine's own counter rather
 * than by counting actions, because the counter is what the price reads. */
{
  const g = new E.Game(3, 9, { humans: [] });
  ok(g.RESEARCH_MAX === 2, 'the allowance is not two improvements a turn');
  const st = { researches: 0, researchesPaid: 0 };
  const p = g.P[0];
  p.gold = 20;
  ok(g.canTrade(p, st) === (g.pile.length >= 2),
     'trade is refused with gold in hand and cards in the pile');
  st.researches = 2;
  ok(!g.canTrade(p, st),
     'a third improvement was allowed as a trade after two researches');
  ok(g.tradeBlocked(p, st) === 'why.trade.max',
     'the reason given for a spent allowance is not why.trade.max');
}

// ------------------------------------------- the price is research's price
{
  const g = new E.Game(3, 9, { humans: [] });
  ok(g.researchCost({ researches: 0, researchesPaid: 0 }) === 1,
     'the first improvement does not cost 1');
  ok(g.researchCost({ researches: 1, researchesPaid: 1 }) === 2,
     'the second improvement does not cost 2');
  /* The point: a trade taken FIRST makes the research after it cost 2. If
   * trade kept its own counter this would come back 1. */
  const p = g.P[0]; p.gold = 10;
  const st = { researches: 0, researchesPaid: 0 };
  const before = p.gold;
  const it = g._tradeHuman(p, g.researchCost(st));
  let r = it.next();
  ok(r.value && r.value.type === 'trade', 'a trade did not ask which cards to bury');
  ok(r.value.drew && r.value.drew.length === 2,
     'a trade did not draw two cards before asking');
  st.researches = 1; st.researchesPaid = 1;
  r = it.next(r.value.drew.slice());     // bury the two just drawn
  ok(r.done && r.value === true, 'the trade did not complete');
  ok(p.gold === before - 1, `the first trade cost ${before - p.gold} gold, not 1`);
  ok(g.researchCost(st) === 2,
     'a research after a trade does not cost 2 — the allowance is not shared');
}

// --------------------------- you always return two, whatever you answer
/* The draw commits the trade: the two cards are in hand and the pile is two
 * shorter before the question is even asked. A client that answers with one
 * card, or none, or the same card twice, must not be able to keep all four. */
for (const bad of [[], null, 'nonsense']) {
  const g = new E.Game(3, 31, { humans: [] });
  const p = g.P[0]; p.gold = 10;
  const hand = p.hand.length, pile = g.pile.length;
  const it = g._tradeHuman(p, 1);
  let r = it.next();
  r = it.next(bad);
  ok(r.done, `a trade answered with ${JSON.stringify(bad)} never finished`);
  ok(p.hand.length === hand,
     `answering ${JSON.stringify(bad)} left ${p.hand.length} in hand, not ${hand}`);
  ok(g.pile.length === pile,
     `answering ${JSON.stringify(bad)} left ${g.pile.length} in the pile, not ${pile}`);
  ok(g.stats.trade_fallback === 1, 'the fallback was not recorded');
}
{
  /* The same card twice is the subtle one: naively splicing twice would remove
   * it once and bury it twice, inventing a card. */
  const g = new E.Game(3, 31, { humans: [] });
  const p = g.P[0]; p.gold = 10;
  const pile = g.pile.length, hand = p.hand.length;
  const it = g._tradeHuman(p, 1);
  let r = it.next();
  const dup = r.value.drew[0];
  r = it.next([dup, dup]);
  ok(p.hand.length === hand, 'the duplicate answer changed the hand size');
  ok(g.pile.length === pile, 'the duplicate answer changed the pile size');
  ok(g.pile.filter((c) => c === dup).length === 1,
     'the same card was buried twice');
}

// ----------------------------------- the cards go to the BOTTOM, and come back
/* The buried cards must not be the next two drawn. This is the whole theme -
 * what you bury comes round again, but not soon - and it is one line of code
 * away from being the opposite. */
{
  const g = new E.Game(3, 13, { humans: [] });
  const p = g.P[0]; p.gold = 10;
  const it = g._tradeHuman(p, 1);
  let r = it.next();
  const buried = r.value.drew.slice();
  it.next(buried);
  ok(g.pile[0] === buried[1] || g.pile[0] === buried[0],
     'a buried card is not at the bottom of the pile');
  ok(g.pile[g.pile.length - 1] !== buried[0]
     && g.pile[g.pile.length - 1] !== buried[1],
     'a card just buried is sitting back on top of the pile');
}

// -------------------------------------------- the pile can run out
{
  const g = new E.Game(3, 13, { humans: [] });
  const p = g.P[0]; p.gold = 10;
  g.pile = g.pile.slice(0, 1);
  ok(!g.canTrade(p, { researches: 0, researchesPaid: 0 }),
     'a trade was offered with one card in the pile');
  ok(g.tradeBlocked(p, { researches: 0 }) === 'why.trade.pile',
     'the reason given for a short pile is not why.trade.pile');
}

// ---------------------------------- an orphan is a card that connects to nothing
{
  const C = (r, s) => ({ r, s });
  const orph = E.Game._orphans([C(3, 'plains'), C(4, 'forest'), C(9, 'ocean')]);
  ok(orph.length === 1 && orph[0].r === 9,
     'the 9 beside a 3-4 run was not the only orphan');
  const twins = E.Game._orphans([C(7, 'plains'), C(7, 'forest')]);
  ok(twins.length === 0, 'a held pair was counted as two orphans');
  const none = E.Game._orphans([C(1, 'plains'), C(2, 'forest'), C(3, 'ocean')]);
  ok(none.length === 0, 'a straight run reported orphans');
}

if (fail.length) { fail.forEach((f) => console.error('FAIL: ' + f)); process.exit(1); }
console.log('trade: one allowance with research, two cards each way, 80 cards '
          + 'in the game before and after, and the buried pair goes to the bottom');
