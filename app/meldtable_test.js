/* THE MELD AREA SHOWS THE TABLE, NOT THE RECORD.
 *
 * Reported from a real game: "I just played all my cards. Now I'm being
 * attacked. I again see my meld that should be gone." It was there because the
 * meld area fell back to `tableau` - the record of what was played, cleared
 * only at the start of the next round - the moment the seat stopped being the
 * one acting. So every card you had already spent on the map came back and sat
 * in front of you for the rest of the round, including while you were being
 * asked to defend a duel.
 *
 * `onTable` is what is actually lying there. `tableau` stays the record,
 * because the turnbar reads its length for the winner's card count and that
 * number must not shrink as the winner spends.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* ---- a human spends the whole meld: the table empties, the record does not */
{
  const g = new E.Game(3, 4, { humans: [0] });
  const it = g.playRound();
  let r = it.next();
  const sizes = [];
  let laid = 0, everSawTurn = false;
  while (!r.done) {
    const q = r.value;
    if (q.type === 'meld' && q.seat === 0) {
      /* the biggest meld on offer, so there is something to spend */
      const big = q.options.slice().sort((a, b) => b.length - a.length)[0];
      laid = big.length;
      r = it.next(big);
      continue;
    }
    if (q.type === 'turn' && q.seat === 0) {
      everSawTurn = true;
      ok(Array.isArray(g.P[0].onTable), 'onTable is not a list during your own turn');
      sizes.push(g.P[0].onTable.length);
      ok(g.P[0].onTable.length === q.state.cards.length,
         `the table shows ${g.P[0].onTable.length} cards, ${q.state.cards.length} are left to spend`);
      if (q.state.cards.length) { r = it.next({ kind: 'cash', card: q.state.cards[0] }); continue; }
      r = it.next({ kind: 'end' });
      continue;
    }
    r = it.next(null);
  }
  ok(everSawTurn, 'the human seat never got a map turn');
  ok(laid > 1, 'the test never laid a meld worth spending');
  /* At or below the meld: a card set aside at the trick has already left the
     table before the map phase begins, which is the point of onTable. */
  ok(sizes.length > 1 && sizes[0] >= 1 && sizes[0] <= laid,
     `the table started at ${sizes[0]} cards, the meld was ${laid}`);
  for (let i = 1; i < sizes.length; i++)
    ok(sizes[i] < sizes[i - 1], 'the table did not empty as cards were spent: ' + sizes.join(','));
  ok(g.P[0].onTable.length === 0,
     `${g.P[0].onTable.length} cards still on the table after the whole meld was spent`);
  /* THE RECORD SURVIVES. The turnbar reads this for the winner's card count. */
  ok(g.P[0].tableau && g.P[0].tableau.length === laid,
     'the played-meld record shrank with the table; the winner die would lie');
}

/* ---- bots empty their own tables too, so a rival's corner is honest ---- */
{
  for (const n of [2, 3, 4]) {
    const g = E.playOut(n, 300 + n, { humans: [] });
    for (const p of g.P)
      ok(!p.onTable || p.onTable.length === 0,
         `${n}p: seat ${p.i} finished the game with cards still on the table`);
  }
}

/* ---- and it is cleared at the head of the next round ---- */
{
  const g = new E.Game(2, 9, { humans: [] });
  const one = g.playRound(); let r = one.next(); while (!r.done) r = one.next(null);
  ok(g.P[0].onTable !== null, 'a round went by without anyone putting a card on the table');
  const two = g.playRound(); two.next();
  /* playRound clears the table before the first meld is asked for */
  ok(g.P[0].onTable === null || g.P[0].onTable.length <= g.P[0].meldLimit(),
     'last round\'s table survived into the new round');
}

if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
console.log('meld area: shows the cards still on the table and empties as they are spent, '
  + 'while the played-meld record stays intact for the winner\'s count');
