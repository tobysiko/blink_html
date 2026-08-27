/* Drives a human seat through the engine directly (no DOM), answering every
 * request type at random, and checks the invariants after every round. */
const E = require('./engine.js');

function autoHuman(G, req, rng) {
  const p = G.P[req.seat];
  const pick = (a) => a[Math.floor(rng() * a.length)];
  switch (req.type) {
    case 'meld': return pick(req.options);
    case 'bonus':
    case 'discard':
    case 'setaside':
    case 'retire': return pick(req.options);
    case 'buy': return pick(req.options);
    case 'effectA': return rng() < 0.3 ? req.options[0] : null;
    case 'feed': return rng() < 0.7 ? req.options[0] : null;
    case 'waterexplore':
      return rng() < 0.8 ? { cell: pick(req.options), terrain: pick(req.terrains) } : null;
    case 'colony':
      return rng() < 0.9 ? { cell: pick(req.options), terrain: pick(req.terrains) } : null;
    case 'conquest': return rng() < 0.85 ? pick(req.options) : null;
    case 'objective': return pick(req.options);
    case 'turn': {
      const o = req.opts;
      const roll = rng();
      // spend a card if one has a legal action
      const live = o.cards.filter((m) => m.options.length);
      if (live.length && roll < 0.55) {
        const m = pick(live);
        const [cell, act] = pick(m.options);
        return { kind: 'spend', card: m.card, cell, act };
      }
      if (o.cards.length && roll < 0.62) return { kind: 'cash', card: pick(o.cards).card };
      if (o.canResearch && roll < 0.72) return { kind: 'research' };
      if (o.moves && o.moveSources.length && roll < 0.82) {
        const src = pick(o.moveSources);
        const dests = [...G.moveDests(p, src)];
        if (dests.length) return { kind: 'move', src, dest: pick(dests) };
      }
      if (o.fortifyCells.length && roll < 0.86) return { kind: 'fortify', cell: pick(o.fortifyCells) };
      if (o.colonyCards.length && roll < 0.90) return { kind: 'colony', card: pick(o.colonyCards) };
      if (o.cashCards.length && roll < 0.93) return { kind: 'cashRow', card: pick(o.cashCards) };
      if (o.deck === 'abd' && !o.conquestBlocked && p.vrow.length && roll < 0.95)
        return { kind: 'conquest', card: pick(p.vrow) };
      // anything still legal that must not be silently lost
      if (o.cards.length) {
        const m = pick(o.cards);
        return m.options.length
          ? { kind: 'spend', card: m.card, ...(() => { const [cell, act] = pick(m.options); return { cell, act }; })() }
          : { kind: 'cash', card: m.card };
      }
      return { kind: 'end' };
    }
    /* A duel: commit a card from hand, or decline. Both are legal, and a
     * driver that always fought would never exercise the decline path. */
    case 'duel':
      return rng() < 0.25 ? null : pick(req.options);
    default: throw new Error('unhandled request type: ' + req.type);
  }
}

const seen = new Set();
let games = 0, unfinished = 0;
for (const n of [2, 3, 4]) {
  for (let s = 1; s <= 40; s++) {
    for (const seat of [0, n - 1]) {
      const rng = E.makeRng(s * 104729 + seat);
      const G = new E.Game(n, s * 31337 + seat,
        { humans: [seat], trickRule: (s % 2 ? 'dock' : 'bonus'),
          deck: (s % 3 === 0 ? 'abd' : 'abc'),
          retireRule: (s % 5 === 0 ? 'any' : 'lowest'),
          comboMelds: s % 7 === 0, friendsOf10: s % 11 === 0,
          growLimits: s % 6 === 0,
          botStyle: ['tuned','mixed','raider','scholar'][s % 4],
          botLevel: ['hard','normal','easy'][s % 3],
          objectives: ['off','secret','open','both'][s % 4] });
      /* Every card in the game at the start. Nothing may vanish: the set-aside
       * card now leaves the player's own economy for the shared pile, and a
       * routing change is exactly how a card gets dropped on the floor. */
      const allCards = () => {
        const cnt = new Map();
        const add = (c) => cnt.set(c.r + c.s, (cnt.get(c.r + c.s) || 0) + 1);
        for (const q of G.P) { q.hand.forEach(add); q.discard.forEach(add);
                               q.played.forEach(add); q.vrow.forEach(add); }
        G.removed.forEach(add); G.pile.forEach(add); G.deck.forEach(add);
        G.grid.forEach((st) => st.forEach(add));
        return cnt;
      };
      const TOTAL = allCards().size;
      let guard = 0;
      while (!G.finished() && guard++ < 300) {
        const it = G.playRound();
        let r = it.next();
        let inner = 0;
        while (!r.done) {
          if (inner++ > 6000) throw new Error('request loop did not terminate');
          seen.add(r.value.type);
          if (r.value.seat !== seat) throw new Error('a bot seat was asked a question');
          r = it.next(autoHuman(G, r.value, rng.random));
        }
        for (const q of G.P) {
          const onmap = [...G.m.tiles.values()]
            .reduce((a, t) => a + t.units.filter((u) => u === q.i).length, 0);
          const res = q.reserve.reduce((a, b) => a + b, 0);
          if (res + onmap !== 20) throw new Error(`units ${res}+${onmap} n=${n} seed=${s}`);
          if (q.hand.length + q.discard.length + q.played.length > 10)
            throw new Error('over ten cards');
          if (q.vrow.length > 5) throw new Error('victory row over five');
          if (q.gold < 0) throw new Error('negative gold');
        }
        for (const t of G.m.tiles.values()) {
          if (new Set(t.units).size > 1) throw new Error('tile has two owners');
          if (t.units.length > t.capacity) throw new Error('overstacked tile');
          if (t.gold > t.units.length) throw new Error('stray fortification coin');
        }
        const tc = {}; for (const t of E.TER) tc[t] = G.m.supply[t];
        for (const t of G.m.tiles.values()) tc[t.terrain]++;
        for (const t of E.TER) if (tc[t] !== 15) throw new Error('tile conservation ' + t);
        // no card may be duplicated or lost
        const cnt = allCards();
        for (const [k, v] of cnt) if (v > 1) throw new Error('duplicated card ' + k);
        if (cnt.size !== TOTAL)
          throw new Error(`cards lost: ${cnt.size} of ${TOTAL} n=${n} seed=${s}`);
      }
      if (!G.finished()) { unfinished++; console.log('DID NOT FINISH', n, s, seat); }
      games++;
    }
  }
}
console.log(`${games} human-seat games clean — both trick rules, both decks, both retire rules, the meld variants, growing population limits, every bot style and level, all objective modes, no card lost or duplicated; ${unfinished} unfinished`);
console.log('request types exercised:', [...seen].sort().join(', '));
