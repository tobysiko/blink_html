/* HOW A STARTING HAND IS SETTLED: draft, deal, or one do-over.
 *
 * The draft is the printed rule and was never actually offered to a person:
 * `_deal()` runs in the constructor, constructors cannot ask questions, so
 * `draftPick()` chose for every seat including the human's. It is a setup
 * phase now, like the homelands map.
 *
 * The do-over has a hard limit that comes straight from §03: the whole 1-10
 * deck is dealt at every player count and the remainder starts the shared pile
 * - twenty spare at two players, ten at three, NONE at four. So the pool a
 * do-over draws from is the pile plus every hand handed back at the same
 * moment, and at four players a lone caller reshuffles their own ten cards.
 * That is asserted here rather than left as a surprise at a table.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };
const key = (c) => c.r + c.s;
const bag = (cards) => cards.map(key).sort().join(',');

function everyCardOnce(g, n, what) {
  const all = g.P.map((p) => p.hand).reduce((a, b) => a.concat(b), []).concat(g.pile);
  ok(all.length === 40, `${what}: ${all.length} starting cards accounted for, wanted 40`);
  const seen = new Set(all.map(key));
  ok(seen.size === 40, `${what}: only ${seen.size} distinct cards — one was duplicated or lost`);
  for (const p of g.P)
    ok(p.hand.length === 10, `${what}: seat ${p.i} holds ${p.hand.length} cards, wanted 10`);
  ok(g.pile.length === 40 - 10 * n, `${what}: the shared pile is ${g.pile.length}, wanted ${40 - 10 * n}`);
}

/* ---- deal: ten cards, no questions ---- */
{
  for (const n of [2, 3, 4]) {
    const seats = []; for (let i = 0; i < n; i++) seats.push(i);
    const g = new E.Game(n, 3, { humans: seats, handSetup: 'deal' });
    const before = g.P.map((p) => bag(p.hand));
    const it = g.playRound();
    let r = it.next(), asked = 0;
    while (!r.done && ['draft', 'mulligan'].includes(r.value && r.value.type)) { asked++; r = it.next(null); }
    ok(asked === 0, `${n}p deal: ${asked} setup questions asked, wanted none`);
    ok(g.P.map((p) => bag(p.hand)).join('|') === before.join('|'),
       `${n}p deal: a hand changed when nothing should have touched it`);
    everyCardOnce(g, n, `${n}p deal`);
  }
}

/* ---- draft: three real decisions a seat, and the choice is obeyed ---- */
{
  for (const n of [2, 3, 4]) {
    const seats = []; for (let i = 0; i < n; i++) seats.push(i);
    const g = new E.Game(n, 4, { humans: seats });          // draft is the default
    ok(g._packs && g._packs.length === n,
       `${n}p draft: the packs were resolved in the constructor after all`);
    ok(g.P.every((p) => p.hand.length === 10),
       `${n}p draft: a seat is not holding its dealt pack before the draft`);
    const it = g.playRound();
    let r = it.next();
    const asked = [], mine = [];
    while (!r.done && r.value && r.value.type === 'draft') {
      const q = r.value;
      asked.push(`${q.seat}:${q.need}/${q.pack.length}`);
      /* Take the LAST cards of the pack, which the heuristic would not, so a
         game that quietly ignored the answer shows up here. */
      const picks = [];
      for (let k = 0; k < q.need; k++) picks.push(q.pack.length - 1 - k);
      if (q.seat === 0) for (const i of picks) mine.push(key(q.pack[i]));
      r = it.next(picks);
    }
    ok(asked.length === 3 * n, `${n}p draft: ${asked.length} questions, wanted ${3 * n}`);
    ok(asked[0] === '0:4/10', `${n}p draft: the first question was ${asked[0]}, wanted 0:4/10`);
    const rounds = asked.filter((a) => a.startsWith('0:')).join(' ');
    ok(rounds === '0:4/10 0:2/6 0:2/4',
       `${n}p draft: seat 0 was asked ${rounds}, wanted 4 of 10, 2 of 6, 2 of 4`);
    /* Eight chosen, and the last two arrive without being asked for. */
    const held = g.P[0].hand.map(key).sort();
    for (const k of mine)
      ok(held.includes(k), `${n}p draft: a card seat 0 chose is not in their hand`);
    everyCardOnce(g, n, `${n}p draft`);
  }
}

/* ---- the do-over, and the pool it draws from ---- */
{
  /* two players: twenty spare cards, so a lone do-over is a real one */
  const g = new E.Game(2, 6, { humans: [0, 1], handSetup: 'mulligan' });
  const was = bag(g.P[0].hand);
  const it = g.playRound();
  let r = it.next(), pools = [];
  while (!r.done && r.value && r.value.type === 'mulligan') {
    pools.push(r.value.pool);
    r = it.next(r.value.seat === 0);                 // only seat 0 calls it
  }
  ok(pools.length === 2, `a 2-player table was asked ${pools.length} times, wanted 2`);
  ok(pools[0] === 20, `the do-over said it drew from ${pools[0]} cards, wanted 20`);
  ok(bag(g.P[0].hand) !== was, 'the do-over handed back the same ten cards at two players');
  everyCardOnce(g, 2, '2p do-over');
}
{
  /* four players: the pile is empty, so a LONE do-over is the same ten cards */
  const g = new E.Game(4, 6, { humans: [0, 1, 2, 3], handSetup: 'mulligan' });
  const was = bag(g.P[0].hand);
  const it = g.playRound();
  let r = it.next(), pool0 = null;
  while (!r.done && r.value && r.value.type === 'mulligan') {
    if (r.value.seat === 0) pool0 = r.value.pool;
    r = it.next(r.value.seat === 0);
  }
  ok(pool0 === 0, `at four players the do-over offered a pool of ${pool0}, wanted 0`);
  ok(bag(g.P[0].hand) === was,
     'a lone four-player do-over changed the hand — there is nothing to change it with');
  ok((g.stats.mulligan_futile || 0) === 1, 'the futile do-over was not counted');
  everyCardOnce(g, 4, '4p lone do-over');
}
{
  /* ...but two callers at four players really do swap */
  const g = new E.Game(4, 6, { humans: [0, 1, 2, 3], handSetup: 'mulligan' });
  const was = [bag(g.P[0].hand), bag(g.P[1].hand)];
  const it = g.playRound();
  let r = it.next();
  while (!r.done && r.value && r.value.type === 'mulligan') r = it.next(r.value.seat < 2);
  ok(bag(g.P[0].hand) !== was[0] || bag(g.P[1].hand) !== was[1],
     'two do-overs at four players changed nothing between them');
  ok((g.stats.mulligan_futile || 0) === 0, 'two callers were counted as futile');
  everyCardOnce(g, 4, '4p two do-overs');
}

/* ---- a draft answer survives the wire ---- */
{
  /* The answer is a list of positions, not one of a list of options, so it
     takes the `raw` path through the session log. A network game that refused
     it would leave the host staring at a prompt that does nothing. */
  const S = require('./session.js');
  const g = new E.Game(3, 4, { humans: [0, 1, 2] });
  const req = g.playRound().next().value;
  ok(req.type === 'draft', `the first question of a drafted game is ${req.type}`);
  ok(req.options === undefined, 'the draft REQ grew an options list — it encodes by index');
  const tok = S.encodeAnswer(g, req, [0, 1, 2, 3]);
  ok(tok && Array.isArray(tok.raw), `a draft answer encoded as ${JSON.stringify(tok)}`);
  ok(S.legalAnswer(g, req, tok) === true, 'a session refused a legal draft answer');
  ok(JSON.stringify(S.decodeAnswer(g, req, tok)) === '[0,1,2,3]',
     'a draft answer did not come back off the wire intact');
}

/* ---- and every mode still plays a whole game ---- */
{
  for (const mode of ['draft', 'deal', 'mulligan'])
    for (const n of [2, 3, 4]) {
      const g = E.playOut(n, 55 + n, { humans: [], handSetup: mode });
      ok(g.finished(), `a ${n}-player "${mode}" game did not end`);
    }
}

if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
console.log('starting hands: the draft is three real decisions a seat and the choice is obeyed; '
  + 'deal asks nothing; the do-over draws from the shared pile plus every hand handed back, '
  + 'which at four players is nothing at all unless somebody else calls it too');
