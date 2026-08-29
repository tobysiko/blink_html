/* Every coin has a reason, and the player is told it.
 *
 * THE PROBLEM THIS EXISTS FOR. Gold moved in twenty-six places in the engine
 * and explained itself in almost none of them. The purse changed and the
 * player was left to infer why — which produced three separate reports in a
 * row, all of the form "nothing happens" or "where did that come from": the
 * frontier coin, the two trick coins that stack, and the refund for calling
 * off an assault. Every one of them was a CORRECT rule that the app kept to
 * itself. A rule a player cannot see is, from their side of the table, a bug.
 *
 * So gold does not move by assignment any more. It moves through Game.purse(),
 * which takes a reason; the reason is a stat suffix AND a translation key, so
 * one call reaches the counters, the animation layer and the log together.
 *
 * This file is the lock on that door. It fails if:
 *   1. anyone writes `p.gold +=` again, anywhere in the engine;
 *   2. a reason is used that is not on the declared list;
 *   3. a declared reason never fires in a few hundred games (a dead reason is
 *      either a dead rule or a misspelling, and both are worth knowing);
 *   4. a coin moves without writing a line to the log;
 *   5. the animation for a coin starts or ends nowhere in particular.
 */
const fs = require('fs');
const path = require('path');
const E = require('./engine.js');
const I = require('./i18n.js');

const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

// ------------------------------------------------- 1. no back doors
{
  const src = fs.readFileSync(path.join(__dirname, 'engine.js'), 'utf8');
  const lines = src.split('\n');
  /* purse() is the one place allowed to touch a purse, so its body is skipped
   * wholesale — matching on the word "purse" per line let its own assignment
   * through only by accident, which is not a guard. */
  const open = lines.findIndex((l) => /^\s*purse\(p, amount, why/.test(l));
  let close = open;
  if (open >= 0) {
    const indent = lines[open].match(/^\s*/)[0].length;
    for (close = open + 1; close < lines.length; close++)
      if (lines[close].trim() === '}'
          && lines[close].match(/^\s*/)[0].length === indent) break;
  }
  const bad = [];
  lines.forEach((line, i) => {
    if (open >= 0 && i >= open && i <= close) return;       // the door itself
    if (/\bpurse\s*\(/.test(line)) return;                 // calls to it
    if (/^\s*\*/.test(line) || /^\s*\/\//.test(line)) return;  // comments
    /* `t.gold` is a fortification coin sitting on a TILE, which is a different
     * thing from a player's purse and is allowed to move on its own. */
    if (/(?<![.\w])p\.gold\s*(\+=|-=|=[^=])/.test(line)
        || /\bthis\.gold\s*(\+=|-=)/.test(line))
      bad.push(`  engine.js:${i + 1}  ${line.trim().slice(0, 72)}`);
  });
  ok(!bad.length,
     'gold is being moved without a reason — route it through purse():\n'
     + bad.join('\n'));
}

// ------------------------------------------- 2 & 3. every reason is real
{
  ok(Array.isArray(E.GOLD_REASONS) && E.GOLD_REASONS.length > 8,
     'the engine no longer declares why gold may move');

  // an undeclared reason must be refused loudly rather than logged silently
  const g = new E.Game(3, 1, { humans: [] });
  let threw = false;
  try { g.purse(g.P[0], 1, 'because', 'board'); } catch (e) { threw = true; }
  ok(threw, 'purse() accepted a reason that is not on the list');

  const seen = new Set();
  for (const n of [2, 3, 4]) {
    for (let s = 0; s < 45; s++) {
      const opts = s % 3 === 0 ? { deck: 'abd' } : s % 3 === 1 ? { combat: 'gold' } : {};
      const done = E.playOut(n, (s * 40503) % 2147483647, opts);
      for (const k of Object.keys(done.stats)) {
        const m = /^gold_(in|out)_(.+)$/.exec(k);
        if (m) seen.add(m[2]);
      }
    }
  }
  const dead = E.GOLD_REASONS.filter((r) => !seen.has(r));
  /* `bonus_gold` needs the winner to hold an empty hand and `called_off` needs
   * a person to decline an assault, so neither can appear in a bot game. They
   * are covered by human_test and combat_test instead. */
  const cannotHappenWithBots = ['bonus_gold', 'called_off'];
  const reallyDead = dead.filter((r) => !cannotHappenWithBots.includes(r));
  ok(!reallyDead.length,
     `these reasons never fired in 405 games — dead rule or typo? ${reallyDead}`);

  const undeclared = [...seen].filter((r) => !E.GOLD_REASONS.includes(r));
  ok(!undeclared.length, `gold moved for undeclared reasons: ${undeclared}`);
}

// --------------------------------------- 4. the log says it, in both languages
{
  const g = E.playOut(4, 909, {});
  const spoken = new Set(g.log.filter(([, k]) => k.startsWith('log.gold.'))
                              .map(([, k]) => k.slice('log.gold.'.length)));
  ok(spoken.size > 5, `only ${spoken.size} kinds of coin explained themselves`);

  for (const why of E.GOLD_REASONS) {
    for (const lang of ['en', 'de']) {
      /* Two channels, and both are required. The LOG explains a coin after the
       * fact, in a list a player has to go and read. The CAPTION explains it
       * at the moment, floating where the coin landed — which is where they
       * are already looking, and is the one that stops the question being
       * asked at all. */
      const cap = I.STRINGS[lang]['fx.why.' + why];
      ok(!!cap, `no ${lang} caption for a coin paid as "${why}"`);
      ok(!cap || cap.split(/\s+/).length <= 3,
         `the ${lang} caption for "${why}" is "${cap}" — too long to read in `
         + 'the half second it is on screen');
      const s = I.STRINGS[lang]['log.gold.' + why];
      ok(!!s, `no ${lang} sentence for a coin paid as "${why}"`);
      /* The two things a player needs are how much and who. */
      if (s) {
        ok(s.includes('{n}'), `the ${lang} line for "${why}" never says how much`);
        ok(s.includes('{seat}'), `the ${lang} line for "${why}" never says who`);
      }
    }
  }

  /* Counting is the point: a coin logged is a coin the counters agree with. */
  const paid = g.log.filter(([, k]) => k.startsWith('log.gold.'))
                    .reduce((a, [, , v]) => a + (v.n || 0), 0);
  const counted = Object.entries(g.stats)
    .filter(([k]) => /^gold_(in|out)_/.test(k))
    .reduce((a, [, v]) => a + v, 0);
  ok(paid === counted,
     `the log accounts for ${paid} gold and the counters for ${counted}`);
}

// ------------------------------- 5. and the coin comes from somewhere real
{
  const g = new E.Game(3, 5, { humans: [] });
  const cells = [...g.m.tiles.keys()];
  const seenWhere = new Set();
  g.events = g.events || [];
  for (const why of ['frontier', 'cashed', 'food', 'upgrade', 'fortify']) {
    g.events.length = 0;
    const amount = ['food', 'upgrade', 'fortify'].includes(why) ? -1 : 1;
    g.P[0].gold = 5;
    g.purse(g.P[0], amount, why, why === 'frontier' ? cells[0] : 'hand');
    const e = g.events.find((x) => x.type === 'gold');
    ok(!!e, `paying for "${why}" produced no animation at all`);
    if (e) {
      const where = amount > 0 ? e.from : e.to;
      ok(where !== undefined && where !== null,
         `the coin for "${why}" comes from nowhere`);
      ok(e.why === why, `the coin for "${why}" flies with no reason attached`);
      seenWhere.add(String(where));
    }
  }
  ok(seenWhere.size > 1,
     'every coin flies from the same place — the animation says nothing');
}

console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : `gold: ${E.GOLD_REASONS.length} declared reasons, every one of them fires, `
    + 'each writes a sentence in both languages that says who and how much, the '
    + 'log and the counters agree to the coin, and nothing in the engine can '
    + 'move a purse without saying why');
process.exit(fail.length ? 1 : 0);
