/* Would "swap a hand card for one from the removed pile" actually help?
 *
 * The naive measure — does one extra rank lengthen your longest run — says yes
 * 100% of the time, and is worthless: melds are capped at your tier's limit
 * (2/3/4/5/6), so lengthening a run you already cannot play in full buys
 * nothing. This measures the real operation instead:
 *
 *   discard one card from hand, take one from the removed pile,
 *   and see whether the best PLAYABLE meld gets bigger.
 *
 *   node app/resurrect.js
 */
const E = require('./engine.js');
const N = Number(process.env.N) || 200;

/* Best meld = the most cards whose ranks form an unbroken run, capped by the
 * tier's meld limit. Duplicates count — 2-3-3-4-4 is five cards. */
function bestMeld(cards, limit) {
  const byRank = {};
  for (const c of cards) byRank[c.r] = (byRank[c.r] || 0) + 1;
  const ranks = Object.keys(byRank).map(Number).sort((a, b) => a - b);
  let best = ranks.length ? 1 : 0;
  for (let i = 0; i < ranks.length; i++) {
    let n = byRank[ranks[i]];
    best = Math.max(best, Math.min(n, limit));
    for (let j = i + 1; j < ranks.length; j++) {
      if (ranks[j] !== ranks[j - 1] + 1) break;
      n += byRank[ranks[j]];
      best = Math.max(best, Math.min(n, limit));
    }
  }
  return Math.min(best, limit);
}

for (const n of [2, 3, 4]) {
  let pile = 0, games = 0, hands = 0, helped = 0, gain = 0, capped = 0;
  const band = [0, 0, 0, 0];
  for (let s = 0; s < N; s++) {
    const g = E.playOut(n, (s * 2654435761) % 2147483647, {});
    games++; pile += g.removed.length;
    for (const c of g.removed) band[Math.min(3, Math.floor((c.r - 1) / 5))] += 1;
    const ranksInPile = [...new Set(g.removed.map((c) => c.r))];
    for (const p of g.P) {
      if (!p.hand.length) continue;
      const limit = p.meldLimit();
      const before = bestMeld(p.hand, limit);
      hands++;
      if (before >= limit) { capped++; continue; }   // already maxed: nothing to gain
      let after = before;
      for (let d = 0; d < p.hand.length; d++) {
        const kept = p.hand.filter((_, i) => i !== d);
        for (const r of ranksInPile) {
          const v = bestMeld([...kept, { r }], limit);
          if (v > after) after = v;
        }
      }
      if (after > before) { helped++; gain += after - before; }
    }
  }
  const pc = (x, d) => (100 * x / d).toFixed(0) + '%';
  console.log(`${n}p  removed pile ${(pile / games).toFixed(1)} cards/game   ` +
    `ranks 1-5:${pc(band[0], band.reduce((a, b) => a + b))} ` +
    `6-10:${pc(band[1], band.reduce((a, b) => a + b))} ` +
    `11-15:${pc(band[2], band.reduce((a, b) => a + b))} ` +
    `16-20:${pc(band[3], band.reduce((a, b) => a + b))}`);
  console.log(`     hands already at the meld limit: ${pc(capped, hands)}` +
    `   of the rest, a swap helps ${pc(helped, hands - capped)}` +
    ` (avg +${(gain / Math.max(1, helped)).toFixed(2)} cards)\n`);
}
