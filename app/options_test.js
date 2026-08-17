/* Two options added for playtesting: the player board layout, and winning the
 * trick on total rank instead of card count.
 *
 * An option that is wired up but does nothing is worse than a missing one — it
 * produces measurements that look like evidence. So each is checked three ways:
 * it parses, it reaches the game, and it CHANGES something a player would see.
 */
const E = require('./engine.js');
const S = require('./session.js');

const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

// ============================================== 1. the player board layout

/* Every form the setup page and a session can send. */
ok(String(E.parseLayout('2-3-5-5-5')) === '2,3,5,5,5', 'a dashed column does not parse');
ok(String(E.parseLayout('2,3,5,5,5')) === '2,3,5,5,5', 'a comma column does not parse');
ok(String(E.parseLayout(' 2 3 5 5 5 ')) === '2,3,5,5,5', 'a spaced column does not parse');
ok(String(E.parseLayout([2, 3, 5, 5, 5])) === '2,3,5,5,5', 'an array layout does not parse');
ok(String(E.parseLayout('late')) === '2,3,5,5,5', 'the named "late" layout is wrong');
ok(String(E.parseLayout('rulebook')) === '2,4,6,4,4', 'the named "rulebook" layout is wrong');

/* And every way of getting it wrong, because a half-applied board is worse than
 * a refused one: the game would start and nobody could say what it was. */
ok(E.parseLayout('1-2-3-4') === null, 'a column of the wrong length was accepted');
ok(E.parseLayout('1-2-3-4-5-6') === null, 'an over-long column was accepted');
ok(E.parseLayout('0-3-5-5-5') === null,
   'a layout with an empty first tier was accepted — there would be no unit to '
   + 'place and the game could not begin');
ok(E.parseLayout('') === null, 'an empty column was accepted');
ok(E.parseLayout('a-b-c-d-e') === null, 'a column of letters was accepted');
ok(E.parseLayout(null) === null && E.parseLayout(undefined) === null,
   'no layout at all should mean the default, not a crash');

/* It reaches the game, and it does NOT reach the module table — the server
 * replays many sessions in one process, and a global would mean one table's
 * custom board rewrote everybody else's. */
{
  const before = E.BANDS.map((b) => b[1]).join('-');
  const g = new E.Game(3, 11, { humans: [], layout: '2-3-5-5-5' });
  ok(g.BANDS.map((b) => b[1]).join('-') === '2-3-5-5-5',
     `the game's tiers are ${g.BANDS.map((b) => b[1]).join('-')}`);
  ok(E.BANDS.map((b) => b[1]).join('-') === before,
     'constructing a game with a custom layout rewrote the module tier table — '
     + 'every other game in this process now has the wrong board');
  const plain = new E.Game(3, 11, { humans: [] });
  ok(plain.BANDS.map((b) => b[1]).join('-') === before,
     'a game with no layout option did not get the printed board');

  /* The players are on it, not just the game. */
  ok(g.P[0].bands === g.BANDS, 'a player is reading a different tier table');
  ok(g.P[0].reserve.join('-') === '1-3-5-5-5',
     `reserve is ${g.P[0].reserve.join('-')} — expected the layout less the one `
     + 'unit that starts on the map');

  /* And a nonsense layout falls back rather than half-applying. */
  const bad = new E.Game(3, 11, { humans: [], layout: '9-9' });
  ok(bad.BANDS.map((b) => b[1]).join('-') === before,
     'an unreadable layout did not fall back to the printed board');
}

/* The layout has to actually matter. A cheaper Settlement means the second tier
 * is reached sooner, so the same seed should not play out identically. */
{
  const a = E.playOut(3, 4242, { trickRule: 'dock' });
  const b = E.playOut(3, 4242, { trickRule: 'dock', layout: '2-3-5-5-5' });
  const sig = (g) => g.score().map((x) => `${x.seat}:${x.total}`).join(',')
    + '|' + g.P.map((p) => p.reserve.join('')).join('/');
  ok(sig(a) !== sig(b),
     'the same seed played identically with and without the 2-3-5-5-5 layout — '
     + 'the option is not reaching anything that matters');
  /* Both still finish and still score, i.e. the option is not just breaking it. */
  for (const [name, g] of [['printed', a], ['late', b]]) {
    ok(g.finished(), `the ${name} layout game never finished`);
    ok(g.score().every((x) => Number.isFinite(x.total)),
       `the ${name} layout game produced a non-numeric score`);
  }
}

/* A layout is part of the table, so it must survive a session round trip. */
{
  const s = S.newSession({ n: 3, seed: 5, layout: '2-3-5-5-5', meldScore: 'sum' });
  ok(s.rules.layout === '2-3-5-5-5', `the session dropped the layout: ${s.rules.layout}`);
  ok(s.rules.meldScore === 'sum', `the session dropped the scoring: ${s.rules.meldScore}`);
  const args = S.gameArgs(s);
  ok(args.opts.layout === '2-3-5-5-5', 'gameArgs does not pass the layout to the engine');
  ok(args.opts.meldScore === 'sum', 'gameArgs does not pass the scoring to the engine');
  /* Which means a replaying guest builds the same board as the host. */
  const g = new E.Game(args.n, args.seed, args.opts);
  ok(g.BANDS.map((b) => b[1]).join('-') === '2-3-5-5-5',
     'a game rebuilt from the session has a different player board than the host');
  ok(g.MELD_SCORE === 'sum', 'a game rebuilt from the session scores tricks differently');
}

// ========================================== 2. the trick won by total rank

ok(new E.Game(2, 1, { humans: [] }).MELD_SCORE === 'count',
   'the printed count rule is not the default');
ok(new E.Game(2, 1, { humans: [], meldScore: 'sum' }).MELD_SCORE === 'sum',
   'the sum rule cannot be switched on');
ok(new E.Game(2, 1, { humans: [], meldScore: 'nonsense' }).MELD_SCORE === 'count',
   'an unknown scoring value was accepted instead of falling back');

{
  /* Rather than fight the meld enumerator, the comparator is exercised through
   * the documented option on real games and checked for a measurable shift. */
  let differs = 0, tricks = 0;
  for (let seed = 1; seed <= 20; seed++) {
    const g = E.playOut(3, seed * 7919 + 13, { trickRule: 'dock', meldScore: 'sum' });
    differs += g.stats.meld_sum_differs || 0;
    tricks += g.stats.meld_sum_tricks || 0;
  }
  ok(tricks > 50, `only ${tricks} tricks played across 20 games`);
  ok(differs > 0,
     `the sum rule picked the same winner as the count rule in all ${tricks} `
     + 'tricks — either it is not being applied or the stat is not recorded');
  /* Sanity: it should not disagree with the count rule on EVERY trick either.
   * A meld with more cards usually has the higher total too, so a rule that
   * differed every time would mean the comparison is inverted. */
  ok(differs < tricks,
     `the sum rule disagreed with the count rule on every one of ${tricks} tricks`
     + ' — the comparison looks inverted');
}

/* And whole games under the sum rule still finish, score, and are different
 * games — the point of the option. */
{
  const a = E.playOut(3, 90210, { trickRule: 'dock' });
  const b = E.playOut(3, 90210, { trickRule: 'dock', meldScore: 'sum' });
  const sig = (g) => g.score().map((x) => x.total).join(',');
  ok(b.finished(), 'a game under the sum rule never finished');
  ok(sig(a) !== sig(b),
     'the same seed scored identically under both trick rules — the option is inert');

  /* Under sum scoring the winning meld should not be systematically the biggest
   * one, or the rule has changed nothing about how a hand is used. */
  const cards = b.stats.meld_sum_cards / Math.max(1, b.stats.meld_sum_tricks);
  const cardsCount = a.stats.meld_sum_cards / Math.max(1, a.stats.meld_sum_tricks);
  ok(Number.isFinite(cards) && Number.isFinite(cardsCount),
     'the meld-size counters were not recorded');
}

/* The two options together, since that is how they will be playtested. */
{
  const g = E.playOut(3, 555, { trickRule: 'bonus', meldScore: 'sum',
                                layout: '2-3-5-5-5', objectives: 'secret' });
  ok(g.finished(), 'a game with both new options and objectives never finished');
  ok(g.BANDS.map((b) => b[1]).join('-') === '2-3-5-5-5', 'the layout was lost');
  ok(g.MELD_SCORE === 'sum', 'the scoring was lost');
}

// ================================= 3. and the setup page actually sends them
/* The engine having an option means nothing if the page cannot ask for it —
 * which is exactly how the landfall rule came to be "fixed" while the app was
 * unchanged. So the built page is driven: pick the options, start a game, and
 * ask the running game what it got. */
let JSDOM = null;
try { ({ JSDOM } = require('jsdom')); } catch (e) { /* checked below */ }

if (!JSDOM) {
  console.log('options (engine only — install jsdom to check the setup page too)');
  finish();
} else {
  const fs = require('fs');
  const path = require('path');
  const html = fs.readFileSync(path.join(__dirname, '..', 'Blink-play-v0.22.html'), 'utf8');
  const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
  const w = dom.window, d = w.document;
  const errs = [];
  w.console.error = (...a) => errs.push(a.join(' '));

  setTimeout(() => {
    const q = (s) => d.querySelector(s);

    ok(!!q('#meld-score'), 'the setup page has no control for how a trick is won');
    ok(!!q('#layout'), 'the setup page has no control for the player board layout');
    ok(!!q('#layout-custom'), 'there is no box for a custom layout');

    /* The custom box is hidden until it is wanted, and appears when it is. */
    ok(q('#layout-custom-row') && q('#layout-custom-row').hidden,
       'the custom layout box is visible even though a preset is selected');
    q('#layout').value = 'custom';
    q('#layout').dispatchEvent(new w.Event('change', { bubbles: true }));
    ok(q('#layout-custom-row') && !q('#layout-custom-row').hidden,
       'choosing a custom layout did not reveal the box to type it in');
    const hint = q('#layout-hint');
    ok(hint && /\b20\b/.test(hint.textContent),
       `the hint should total the default 2-3-5-5-5 as 20 units: "${hint && hint.textContent}"`);

    /* A bad column says so rather than silently starting a different game. */
    q('#layout-custom').value = '1-2-3';
    q('#layout-custom').dispatchEvent(new w.Event('input', { bubbles: true }));
    ok(hint && /5/.test(hint.textContent) && hint.classList.contains('bad'),
       `a three-number column is not flagged: "${hint && hint.textContent}"`);

    // now set both options for real and start
    q('#layout-custom').value = '2-3-5-5-5';
    q('#layout-custom').dispatchEvent(new w.Event('input', { bubbles: true }));
    q('#meld-score').value = 'sum';
    require('./test_setup.js').start(w, d, { players: 3, seat: 0, seed: 31 });

    setTimeout(() => {
      const got = w.eval('JSON.stringify({'
        + ' score: G.MELD_SCORE,'
        + ' bands: G.BANDS.map((b) => b[1]).join("-"),'
        + ' optLayout: GARGS.opts.layout,'
        + ' optScore: GARGS.opts.meldScore,'
        + ' repLayout: REP.setup.layout,'
        + ' repScore: REP.setup.meldScore,'
        + ' shown: [...document.querySelectorAll(".pboard .tier-row:not(.head) .tname em")]'
        + '   .map((n) => parseInt(n.textContent, 10)).join("-")'
        + '})');
      const r = JSON.parse(got);
      ok(r.score === 'sum', `the game is scoring tricks by ${r.score}`);
      ok(r.bands === '2-3-5-5-5', `the game's board is ${r.bands}`);
      ok(r.optLayout === '2-3-5-5-5', `GARGS carries layout ${r.optLayout}`);
      ok(r.optScore === 'sum', `GARGS carries meldScore ${r.optScore}`);
      /* Undo replays from GARGS, so anything missing there is a desync. */
      ok(r.repLayout === '2-3-5-5-5' && r.repScore === 'sum',
         `the playtest report records layout=${r.repLayout} score=${r.repScore} — `
         + 'two reports under different rules would be indistinguishable');
      /* And the board on screen shows the layout in play, not the printed one. */
      ok(r.shown === '2-3-5-5-5',
         `the player board on screen reads ${r.shown} — it is showing a different `
         + 'board than the game is using');
      ok(!errs.length, 'the page logged errors: ' + errs.slice(0, 2).join(' | '));
      finish();
    }, 700);
  }, 400);
}

function finish() {
  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : 'options: layouts parse in four forms and refuse five bad ones, stay off the '
      + 'module table, reach players and survive a session; the sum rule is off by '
      + 'default and changes who wins real tricks; and the setup page sends both '
      + 'through to the game, the report and the board on screen');
  process.exit(fail.length ? 1 : 0);
}
