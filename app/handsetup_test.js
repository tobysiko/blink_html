/* HOW A STARTING HAND IS SETTLED: draft, deal, or one do-over.
 *
 * The draft is the printed rule and was never actually offered to a person:
 * `_deal()` runs in the constructor, constructors cannot ask questions, so
 * `draftPick()` chose for every seat including the human's. It is a setup
 * phase now, like the homelands map.
 *
 * A do-over RE-DEALS THE WHOLE TABLE: every card of the 1-10 deck goes back,
 * hands and shared pile alike, and the lot is shuffled and dealt again. That
 * is the only version that works at four players, where §03 leaves no spare
 * cards - a do-over that refreshed only the caller's ten would hand back the
 * same ten. One call each, asked in seat order, so it always ends.
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

/* ---- the do-over re-deals everybody, at every player count ---- */
{
  for (const n of [2, 3, 4]) {
    const seats = []; for (let i = 0; i < n; i++) seats.push(i);
    const g = new E.Game(n, 6, { humans: seats, handSetup: 'mulligan' });
    const before = g.P.map((p) => bag(p.hand));
    const it = g.playRound();
    let r = it.next(), asked = 0;
    while (!r.done && r.value && r.value.type === 'mulligan') {
      asked++;
      r = it.next(r.value.seat === 0);            // only seat 0 calls it
    }
    ok(asked === n, `${n}p: ${asked} seats were asked, wanted ${n}`);
    const after = g.P.map((p) => bag(p.hand));
    let changed = 0;
    for (let i = 0; i < n; i++) if (before[i] !== after[i]) changed++;
    /* EVERY hand, not just the caller's - that is what "re-deal" means, and it
       is the whole reason this works at four players where nothing is spare. */
    ok(changed === n,
       `${n}p: one call changed ${changed} of ${n} hands, wanted all of them`);
    ok((g.stats.mulligans || 0) === 1, `${n}p: ${g.stats.mulligans} re-deals for one call`);
    everyCardOnce(g, n, `${n}p do-over`);
  }
}

/* ---- one each, and no more ---- */
{
  const g = new E.Game(3, 8, { humans: [0, 1, 2], handSetup: 'mulligan' });
  const it = g.playRound();
  let r = it.next(), asked = 0;
  while (!r.done && r.value && r.value.type === 'mulligan') { asked++; r = it.next(true); }
  ok(asked === 3, `everyone calling it asked ${asked} seats, wanted 3`);
  ok((g.stats.mulligans || 0) === 3, `three calls gave ${g.stats.mulligans} re-deals`);
  everyCardOnce(g, 3, 'three do-overs');
  /* Nobody is asked twice: the pass is over even though the last re-deal may
     have handed seat 0 something worse than what it gave up. */
  const again = g.playRound().next();
  ok(!again.value || again.value.type !== 'mulligan',
     'a seat was asked for a second do-over');
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
  + 'deal asks nothing; a do-over re-deals the whole starting deck to everybody, one call each, '
  + 'and works the same at two, three and four players');
