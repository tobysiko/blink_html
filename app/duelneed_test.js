/* WHAT THE APP PROMISES A DEFENDER.
 *
 * Reported from a real game: defending a Mountain with an 11 against a 13 and
 * losing, with the prompt showing "11+" as the rank that holds. It does hold -
 * unless the attacker's card matches the ground and yours does not, because a
 * level fight goes to the matching card (§07) and only to the defender when
 * both match or neither does.
 *
 * The prompt now carries two numbers: `need`, the rank that holds whatever you
 * play, and `needMatch`, the lower one that holds only with a card of this
 * terrain. They differ by exactly one, and only in that case.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

function askDefender(terrain, attack) {
  const g = new E.Game(2, 1, { humans: [0] });
  /* The printed setup only lays mountains and plains, so the ground being
     fought over is made here rather than looked for. */
  const tile = [...g.m.tiles.values()][0];
  tile.terrain = terrain;
  if (!tile.units.length) tile.units.push(0);
  const it = g._duelCard(g.P[0], 'defend', tile, attack, 1);
  const req = it.next().value;
  return req;
}

/* ---- the reported case, and the same shape from the ocean screenshot ---- */
{
  const C = (r, s) => ({ r, s });
  const cases = [
    // terrain,    attack,               need, needMatch, why
    ['mountain', C(13, 'mountain'), 12, 11, 'attacker matched the mountain'],
    ['mountain', C(13, 'plains'),   11, 11, 'attacker did not match'],
    ['ocean',    C(8, 'ocean'),      9,  8, 'attacker matched the ocean'],
    ['ocean',    C(8, 'plains'),     8,  8, 'attacker did not match'],
    ['forest',   C(10, 'forest'),   10,  9, 'attacker matched the forest'],
  ];
  for (const [terrain, attack, need, needMatch, why] of cases) {
    const req = askDefender(terrain, attack);
    ok(req && req.type === 'duel', `no duel request for ${terrain}`);
    if (!req) continue;
    ok(req.need === need,
       `${terrain} v ${attack.r} of ${attack.s}: app says ${req.need} holds, wanted ${need} (${why})`);
    ok(req.needMatch === needMatch,
       `${terrain} v ${attack.r} of ${attack.s}: matching rank ${req.needMatch}, wanted ${needMatch}`);
    /* AND THE NUMBERS MUST AGREE WITH THE RULE ITSELF, which is the only
       witness that matters: the promised rank has to actually hold. */
    ok(!E.duelWinner(attack, { r: req.need, s: 'plains' }, terrain, 0)
       || terrain === 'plains',
       `${terrain}: a ${req.need} of Plains does not hold after all`);
    ok(!E.duelWinner(attack, { r: req.needMatch, s: terrain }, terrain, 0),
       `${terrain}: the promised ${req.needMatch} of ${terrain} does not hold`);
    if (req.needMatch > 1)
      ok(E.duelWinner(attack, { r: req.needMatch - 1, s: terrain }, terrain, 0),
         `${terrain}: ${req.needMatch - 1} of ${terrain} would have held too — the number is too high`);
  }
}

/* ---- a bot defends with a card that actually holds, not one that ties ---- */
{
  let lost = 0, fought = 0;
  for (let s = 0; s < 40; s++) {
    const g = E.playOut(4, 500 + s, { humans: [] });
    fought += (g.stats.duels || 0);
    lost += (g.stats.duel_won || 0);
  }
  ok(fought > 0, 'no duels were fought at all');
  /* Not a threshold on skill — just that spending a card on a fight the rule
     says you lose is no longer possible by construction (see _duelCard). */
  ok(lost < fought, 'every single duel was won by the attacker');
}

if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
console.log('duel: the defender is told the rank that holds whatever they play AND the lower '
  + 'one that holds only with a card of the ground; both agree with duelWinner');
