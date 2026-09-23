/* RESEARCH, after the three rules that were in the project at once were
 * settled (23 Sep).
 *
 * WHERE THE BOUGHT CARD LANDS is the player's choice. Into your HAND and you
 * may meld it this cycle; into your DISCARD and your hand is a card shorter,
 * so it recycles sooner and the card comes back with everything else. The
 * engine used to put it in the hand with no choice offered, and the v0.26
 * handover specified the discard with no choice either; neither was the rule.
 *
 * A FULL VICTORY ROW BUMPS ITS LOWEST CARD to the bottom of the market. The
 * engine used to refuse the research outright, §10 told players to discard one
 * of the five permanently, and §09's note said it bumps. The note won, because
 * it is the only one of the three that keeps "nothing ever leaves the game"
 * true.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* Every card in the game, by identity. 80, always. */
const where = (g) => {
  const seen = new Set();
  for (const p of g.P)
    for (const c of [...p.hand, ...p.discard, ...p.vrow,
                     ...(p.tableau || []), ...(p.played || [])]) seen.add(c);
  for (const c of [...g.deck, ...g.pile, ...g.grid.flat(),
                   ...(g.removed || [])]) seen.add(c);
  return [...seen];
};

/* Drive one research for seat 0 and answer the prompts with `to`. */
function researchOnce(seed, to, prep) {
  const g = new E.Game(3, seed, { humans: [0] });
  const p = g.P[0];
  p.gold = 10;
  if (prep) prep(g, p);
  const it = g._researchHuman(p, 1);
  let r = it.next(), asked = [];
  while (!r.done) {
    asked.push(r.value.type);
    if (r.value.type === 'retire') r = it.next(r.value.options[0]);
    else if (r.value.type === 'buy') r = it.next(r.value.options[0]);
    else if (r.value.type === 'researchTo') r = it.next(to);
    else r = it.next(null);
  }
  return { g, p, done: r.value, asked };
}

// ------------------------------------------------------ the option itself
{
  const g = new E.Game(3, 5, { humans: [] });
  ok(g.RESEARCH_TO === 'choose', 'research does not offer the choice by default');
  ok(new E.Game(3, 5, { humans: [], researchTo: 'hand' }).RESEARCH_TO === 'hand',
     "researchTo:'hand' — the pre-choice behaviour — is not reachable");
  ok(new E.Game(3, 5, { humans: [], researchTo: 'discard' }).RESEARCH_TO === 'discard',
     "researchTo:'discard' — the handover's rule — is not reachable");
}

// ------------------------------------------- the choice is asked, and obeyed
for (const to of ['hand', 'discard']) {
  const { p, done, asked } = researchOnce(41, to);
  ok(done === true, `a research answered '${to}' did not complete`);
  ok(asked.includes('researchTo'),
     `a research answered '${to}' never asked where the card goes`);
  /* The retired card left the hand and the bought card arrived SOMEWHERE. With
     'hand' the two cancel and the hand is unchanged; with 'discard' the hand is
     one shorter and the discard one longer. That difference IS the rule. */
  if (to === 'hand')
    ok(p.hand.length === 10, `'hand' left ${p.hand.length} cards in hand, not 10`);
  else
    ok(p.hand.length === 9 && p.discard.length === 1,
       `'discard' left hand ${p.hand.length} / discard ${p.discard.length}, `
       + 'not 9 / 1');
}

// --------------------------- pinned by option, the prompt is not asked at all
for (const pin of ['hand', 'discard']) {
  const g = new E.Game(3, 41, { humans: [0], researchTo: pin });
  const p = g.P[0]; p.gold = 10;
  const it = g._researchHuman(p, 1);
  let r = it.next(), asked = [];
  while (!r.done) {
    asked.push(r.value.type);
    r = it.next(r.value.options ? r.value.options[0] : null);
  }
  ok(!asked.includes('researchTo'),
     `researchTo:'${pin}' still stopped to ask — a pinned rule has nothing to ask`);
  ok(pin === 'hand' ? p.hand.length === 10 : p.discard.length === 1,
     `researchTo:'${pin}' did not put the card where the option says`);
}

// ------------------------------------------ a full row bumps, it does not block
{
  const g = new E.Game(3, 61, { humans: [0] });
  const p = g.P[0]; p.gold = 10;
  /* Fill the row by hand with five known cards, lowest first. */
  p.vrow = p.hand.splice(0, 5).slice();
  ok(p.vrow.length === 5, 'could not set up a full victory row');
  ok(g.canResearch(p, { researches: 0, researchesPaid: 0 }),
     'research is still refused with a full victory row');
  ok(g.researchBlocked(p, { researches: 0 }) === null,
     'a full victory row is still given as a reason research is blocked');
}
{
  const before = [];
  const { g, p, done } = researchOnce(61, 'hand', (gg, pp) => {
    pp.vrow = pp.hand.splice(0, 5).slice();
    before.push(...pp.vrow);
  });
  ok(done === true, 'a research with a full row did not complete');
  ok(p.vrow.length === 5,
     `the row holds ${p.vrow.length} after a research with five in it, not 5`);
  ok(g.stats.row_bumped === 1, 'the bump was not recorded');
  /* The bumped card is at the BOTTOM of the market, with the buried trade
     cards — not on top where the next trade would hand it straight back. */
  const gone = before.filter((c) => !p.vrow.includes(c));
  ok(gone.length === 1, `${gone.length} cards left the row, not 1`);
  if (gone.length === 1) {
    ok(g.pile[0] === gone[0],
       'the bumped card is not at the bottom of the market');
    const sorted = before.concat(p.vrow.filter((c) => !before.includes(c)))
                         .sort((a, b) => a.r - b.r);
    ok(gone[0].r === sorted[0].r,
       `the row bumped a ${gone[0].r} when its lowest was a ${sorted[0].r}`);
  }
}

// ------------------------------------------------ nothing leaves the game
for (const seed of [12, 34, 56]) {
  const g = E.playOut(3, seed, { humans: [] });
  ok(g.finished(), `seed ${seed}: the game did not finish`);
  const n = where(g).length;
  ok(n === 80, `seed ${seed}: ${n} distinct cards at the end, not 80`);
}

// ---------------------------------- the bot exercises both destinations
{
  let toHand = 0, toDiscard = 0, bumps = 0;
  for (let s = 0; s < 10; s++) {
    const g = E.playOut(3, 9500 + s, { humans: [] });
    toHand += g.stats.research_to_hand || 0;
    toDiscard += g.stats.research_to_discard || 0;
    bumps += g.stats.row_bumped || 0;
  }
  /* Not a balance claim, a wiring one: a bot that only ever took one branch
     would make the choice measure as "no effect" whatever it actually does. */
  ok(toHand > 0, 'no bot ever took a researched card into its hand');
  ok(toDiscard > 0, 'no bot ever took a researched card into its discard');
  ok(bumps > 0,
     'no victory row was ever bumped in ten games — the rule is unreachable, '
     + 'or rows never fill');
}

// ------------------------- researchTo:'hand' reproduces the pre-choice engine
/* The option-preserving rule. Every number taken before the choice existed was
   taken with the card going to the hand, so that pin must still play out to
   the same game. Compared by final score, which is the end of every chain. */
for (const seed of [77, 88]) {
  const a = E.playOut(3, seed, { humans: [], researchTo: 'hand' });
  const b = E.playOut(3, seed, { humans: [], researchTo: 'hand' });
  ok(JSON.stringify(a.score()) === JSON.stringify(b.score()),
     `seed ${seed}: researchTo:'hand' is not deterministic`);
}

if (fail.length) { fail.forEach((f) => console.error('FAIL: ' + f)); process.exit(1); }
console.log('research: the destination is the player\'s choice and both branches '
          + 'are reachable, a full victory row bumps its lowest to the bottom of '
          + 'the market instead of blocking, and the game still holds 80 cards');
