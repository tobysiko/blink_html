/* One victory-row effect per round (§10) — A, B, C and D (under the "abd"
 * deck, where D replaces C) all draw on a single allowance, `p.vrowUsed`,
 * reset at meld time. Before this test, only B ("one victory card on
 * colonies per turn") was capped: a player — or a bot — could found a
 * colony AND cash gold from the row AND, under "abd", strike with D, all
 * in the same round. Spending any one of the four now blocks the other
 * three until the next round.
 *
 * The forced sale of the row at famine time (§ recycle, "the row before the
 * famine") is deliberately NOT part of this cap — that is survival, not a
 * turn choice, and the game must not be able to trap a starving player who
 * already spent their one effect this round.
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
const strip = () => board([
  [0, 0, 'plains', 0], [1, 0, 'plains', 0],
  [2, 0, 'plains', null], [3, 0, 'plains', null], [4, 0, 'plains', null],
  [5, 0, 'plains', 1], [6, 0, 'plains', 1],
  [0, 1, 'plains', null], [3, 1, 'plains', null], [6, 1, 'plains', null],
]);
const card = (r, s) => ({ r, s: s || 'plains' });
const baseSt = () => ({ cards: [], moves: 0, researches: 0, waterUsed: false });

// 1. once ANY vrow effect is spent this round, the turn menu offers no others
{
  const g = strip();
  g.P[0].vrow.push(card(3), card(5), card(7));
  const before = g.turnOptions(g.P[0], baseSt());
  ok(before.colonyCards.length > 0, 'colony was not offered before anything was spent');
  ok(before.cashCards.length > 0, 'cashing was not offered before anything was spent');
  g.P[0].vrowUsed = true;                    // simulate: one effect already used
  const after = g.turnOptions(g.P[0], baseSt());
  ok(after.colonyCards.length === 0,
     'colony was still offered after another vrow effect was spent this round');
  ok(after.colonyBlocked === 'why.vrow.used',
     `colonyBlocked reads "${after.colonyBlocked}", expected the shared reason`);
  ok(after.cashCards.length === 0,
     'cashing was still offered after another vrow effect was spent this round');
  ok(after.cashBlocked === 'why.vrow.used',
     `cashBlocked reads "${after.cashBlocked}", expected the shared reason`);
}

// 2. actually founding a colony (B) marks the round used, and blocks a real
//    cashRow answer sent to the same _humanTurn afterwards
{
  const g = strip();
  const b = card(3), c = card(5);
  g.P[0].vrow.push(b, c);
  g.P[0].hand = [card(1)];                   // non-empty: refill() will not fire mid-turn
  const it = g._humanTurn(g.P[0], []);
  let r = it.next();
  ok(r.value.type === 'turn', 'the first request out of _humanTurn was not a turn menu');
  r = it.next({ kind: 'colony', card: b });   // found the colony
  while (r.value && r.value.type === 'colony')
    r = it.next({ cell: r.value.options[0], terrain: r.value.terrains[0] });
  ok(g.P[0].vrowUsed, 'founding a colony did not mark this round\'s vrow allowance as used');
  ok(r.value.type === 'turn', 'expected another turn menu after the colony resolved');
  ok(!r.value.opts.cashCards.length, 'cashing was offered again in the same round');
  r = it.next({ kind: 'cashRow', card: c });  // try to also cash — should be a no-op
  ok(c.r === 5 && g.P[0].vrow.includes(c),
     'a cashRow answer sent after B still spent the card, in the same round');
  it.next({ kind: 'end' });
}

// 3. the bot's C-cashing spends at most ONE card per call, even while still
//    broke afterwards — this used to be a `while` loop that could empty the
//    whole row in a single call
{
  const g = strip();
  g.P[0].vrow.push(card(1), card(2));
  g.P[0].gold = 0;
  const before = g.P[0].vrow.length;
  const it = g._maybeCashC(g.P[0], false);
  let r = it.next();
  while (!r.done) r = it.next();
  ok(before - g.P[0].vrow.length === 1,
     `the bot cashed ${before - g.P[0].vrow.length} card(s) in one call, expected exactly 1`);
  ok(g.P[0].vrowUsed, 'the bot cashing a card did not mark the round\'s allowance as used');
  // and calling it again the same round does nothing more
  const it2 = g._maybeCashC(g.P[0], false);
  let r2 = it2.next();
  while (!r2.done) r2 = it2.next();
  ok(g.P[0].vrow.length === before - 1,
     'the bot cashed a second card in the same round after already using its allowance');
}

// 4. the forced famine sale is NOT capped by the shared allowance — a
//    starving player can still sell the row for food even after using B/C/D
{
  const g = strip();
  g.P[0].vrowUsed = true;                    // already spent this round's one effect
  g.P[0].vrow.push(card(3));
  g.P[0].gold = 0;
  const before = g.P[0].vrow.length;
  g._spendC(g.P[0], 5);                      // the bot's forced food payment
  ok(g.P[0].vrow.length < before,
     'a starving bot could not sell from the row for food after using its round\'s vrow effect');
}

console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : 'vrow effects: A/B/C/D share one allowance per round, spending any of ' +
    'them blocks the others until the next round for both the human dispatch ' +
    'and the bots, and the forced famine sale stays exempt from the cap');
process.exit(fail.length ? 1 : 0);
