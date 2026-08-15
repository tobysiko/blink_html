/* Are the bot labels honest?
 *
 * Two claims are being made to a player, and both have to be true or the
 * setting is a lie:
 *   1. Difficulty is ORDERED — hard beats normal beats easy, at the same style.
 *   2. Styles are DIFFERENT but not broken — each plays its own way, and none
 *      dominates or collapses.
 *
 * Every seat is a bot, so a win rate is a fair fight. `hard` carries no noise,
 * so a hard table reproduces the numbers every other measurement was taken
 * with. Needs nothing but node; takes about a minute.
 *
 *   node bots_test.js            # the full round robin
 *   node bots_test.js 120        # fewer games, for a quick look
 */
const E = require('./engine.js');
const N = Number(process.argv[2]) || 300;
const STYLES = E.STYLE_KEYS.filter((k) => k !== 'tuned').concat(['tuned']);

/* One table of `styles`, seeded so every matchup sees the same deals. */
function table(styles, level, games) {
  const wins = styles.map(() => 0);
  const score = styles.map(() => 0);
  const stats = styles.map(() => ({}));
  let rounds = 0, ties = 0;
  for (let s = 0; s < games; s++) {
    const g = new E.Game(styles.length, s * 7919 + 13,
      { humans: [], botLevel: level });
    // deal the styles by seat, in a rotation so nobody keeps the lead seat
    g.P.forEach((p, i) => {
      const st = styles[(i + s) % styles.length];
      p.style = st;
      p.w = E.botWeights(st);
      p.noise = E.BOT_LEVELS[level];
    });
    let guard = 0;
    while (!g.finished() && guard++ < 300) {
      const it = g.playRound();
      let r = it.next();
      while (!r.done) r = it.next(null);
    }
    rounds += g.round;
    const tbl = g.score();
    const best = Math.max(...tbl.map((x) => x.total));
    const top = tbl.filter((x) => x.total === best);
    if (top.length > 1) ties++;
    for (const row of tbl) {
      const k = styles.indexOf(g.P[row.seat].style);
      score[k] += row.total;
      stats[k].row = (stats[k].row || 0) + row.vrow;
      stats[k].pop = (stats[k].pop || 0) + row.pop;
      if (row.total === best) wins[k] += 1 / top.length;
    }
    for (const p of g.P) {
      const k = styles.indexOf(p.style);
      const own = stats[k];
      for (const key of ['killed_by_attack', 'settle', 'upgrades', 'fortified',
                         'cards_to_gold', 'effect_b_used', 'free_move'])
        own[key] = (own[key] || 0) + (g.stats[key] || 0) / styles.length;
    }
  }
  return { wins, score, stats, rounds: rounds / games, ties };
}

const pct = (x, n) => (100 * x / n).toFixed(1).padStart(5) + '%';
const fail = [];

// ---------------------------------------------------------------- 1. levels
/* The same style at three levels, three seats, one table. If difficulty is
 * real, the ordering falls out of the win rates. */
console.log(`difficulty — three tuned bots, one per level, ${N} games`);
{
  const wins = { easy: 0, normal: 0, hard: 0 };
  const names = ['easy', 'normal', 'hard'];
  for (let s = 0; s < N; s++) {
    const g = new E.Game(3, s * 104729 + 7, { humans: [] });
    g.P.forEach((p, i) => {
      const lv = names[(i + s) % 3];
      p.style = 'tuned'; p.lv = lv;
      p.w = E.botWeights('tuned');
      p.noise = E.BOT_LEVELS[lv];
    });
    let guard = 0;
    while (!g.finished() && guard++ < 300) {
      const it = g.playRound();
      let r = it.next();
      while (!r.done) r = it.next(null);
    }
    const tbl = g.score();
    const best = Math.max(...tbl.map((x) => x.total));
    const top = tbl.filter((x) => x.total === best);
    for (const row of top) wins[g.P[row.seat].lv] += 1 / top.length;
  }
  for (const k of names) console.log(`  ${k.padEnd(7)} ${pct(wins[k], N)}`);
  if (!(wins.hard > wins.normal && wins.normal > wins.easy))
    fail.push(`difficulty is not ordered: easy ${wins.easy.toFixed(1)}, `
      + `normal ${wins.normal.toFixed(1)}, hard ${wins.hard.toFixed(1)}`);
  if (wins.hard / Math.max(1, wins.easy) < 1.25)
    fail.push('hard is not meaningfully better than easy — the noise does too little');
}

// ---------------------------------------------------------------- 2. styles
/* Head to head, every pairing, at two players — the cleanest read on whether
 * any style simply beats the others. (The game seats 2–4, so five styles
 * cannot share one table.) */
const each = Math.max(40, Math.round(N / 2));
console.log(`\nstyles — head to head, every pairing, hard, ${each} games each`);
{
  const played = STYLES.map(() => 0), won = STYLES.map(() => 0);
  const grid = STYLES.map(() => STYLES.map(() => null));
  for (let a = 0; a < STYLES.length; a++) {
    for (let b = a + 1; b < STYLES.length; b++) {
      const r = table([STYLES[a], STYLES[b]], 'hard', each);
      grid[a][b] = 100 * r.wins[0] / each;
      grid[b][a] = 100 * r.wins[1] / each;
      played[a] += each; played[b] += each;
      won[a] += r.wins[0]; won[b] += r.wins[1];
    }
  }
  const head = STYLES.map((s) => (E.BOT_STYLES[s].label || s).slice(0, 8).padStart(8));
  console.log('             ' + head.join(' ') + '     overall');
  STYLES.forEach((st, a) => {
    const row = STYLES.map((_, b) =>
      (a === b ? '—' : grid[a][b].toFixed(0) + '%').padStart(8)).join(' ');
    console.log(`  ${(E.BOT_STYLES[st].label || st).padEnd(10)} ${row}`
      + `   ${pct(won[a], played[a])}`);
    const w = 100 * won[a] / played[a];
    if (w > 68) fail.push(`${st} wins ${w.toFixed(0)}% head to head — it dominates`);
    if (w < 32) fail.push(`${st} wins ${w.toFixed(0)}% head to head — it is broken`);
  });
}

// -------------------------------------------------- 3. styles play differently
/* A style that measures the same as the baseline is a label, not a policy. */
console.log('\nstyle fingerprints — each style at a table of its own, 3p');
{
  const base = {};
  const rows = [];
  for (const st of STYLES) {
    const r = table([st, st, st], 'hard', Math.max(60, Math.round(N / 3)));
    const n = Math.max(60, Math.round(N / 3));
    const s = r.stats[0];
    const row = {
      st,
      kills: s.killed_by_attack / n, settles: s.settle / n, upgrades: s.upgrades / n,
      walls: s.fortified / n, cashed: s.cards_to_gold / n, colonies: s.effect_b_used / n,
      row: s.row / (n * 3), pop: s.pop / (n * 3),
    };
    rows.push(row);
    if (st === 'tuned') Object.assign(base, row);
  }
  console.log('  style       kills settles upgrades walls cashed colonies    row    pop');
  for (const r of rows)
    console.log(`  ${(E.BOT_STYLES[r.st].label || r.st).padEnd(11)}`
      + [r.kills, r.settles, r.upgrades, r.walls, r.cashed, r.colonies, r.row, r.pop]
        .map((x) => x.toFixed(1).padStart(6)).join(' '));
  for (const r of rows) {
    if (r.st === 'tuned') continue;
    const moved = ['kills', 'settles', 'upgrades', 'walls', 'cashed', 'colonies', 'row', 'pop']
      .filter((k) => Math.abs(r[k] - base[k]) > 0.15 * Math.max(1, base[k]));
    if (!moved.length)
      fail.push(`${r.st} plays exactly like the baseline — it is a label, not a style`);
  }
}

console.log('');
console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : 'bots: difficulty is ordered, no style dominates or collapses, '
    + 'and every style leaves a different mark on the game');
process.exit(fail.length ? 1 : 0);
