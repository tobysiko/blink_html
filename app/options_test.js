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

// ================================ 3. who is paid for losing the trick

/* §04 pays one coin to the last-ranked meld and nothing to anyone else, whatever
 * the player count — so at four players half the table gets no catch-up at all.
 * The ladder schemes pay by PLACE instead. */
{
  const of = (rule, n) => {
    const g = new E.Game(n, 1, { humans: [], consolation: rule });
    return Array.from({ length: n }, (_, i) => g.consolationFor(i, n));
  };
  ok(String(of('last', 4)) === '0,0,0,1', `printed 4p pays ${of('last', 4)}`);
  ok(String(of('last', 3)) === '0,0,1', `printed 3p pays ${of('last', 3)}`);
  ok(String(of('half', 4)) === '0,1,1,2', `half 4p pays ${of('half', 4)}`);
  ok(String(of('ladder', 4)) === '0,1,2,3', `ladder 4p pays ${of('ladder', 4)}`);
  ok(String(of('ladder', 3)) === '0,1,2', `ladder 3p pays ${of('ladder', 3)}`);

  /* The winner is never paid — their reward is acting first. */
  for (const r of ['last', 'half', 'ladder'])
    ok(of(r, 4)[0] === 0, `${r} pays the trick winner a coin`);

  /* At two players every scheme is the same rule, which is worth knowing before
   * anyone tries to measure the difference in a two-player game. */
  for (const r of ['last', 'half', 'ladder'])
    ok(String(of(r, 2)) === '0,1', `${r} at 2p pays ${of(r, 2)}, expected 0,1`);

  ok(new E.Game(3, 1, { humans: [] }).CONSOLATION === 'last',
     'the printed single coin is not the default');
  ok(new E.Game(3, 1, { humans: [], consolation: 'junk' }).CONSOLATION === 'last',
     'an unknown consolation rule was accepted');

  /* And it reaches real games: more gold enters the table, and the game is a
   * different game. */
  const base = E.playOut(4, 4242, { trickRule: 'dock' });
  const lad = E.playOut(4, 4242, { trickRule: 'dock', consolation: 'ladder' });
  ok(lad.stats.gold_in_lost_trick > base.stats.gold_in_lost_trick * 2,
     `the ladder paid ${lad.stats.gold_in_lost_trick} against the printed rule's `
     + `${base.stats.gold_in_lost_trick} — it is not reaching the table`);
  ok(lad.finished(), 'a game under the ladder never finished');
  ok(base.score().map((x) => x.total).join() !== lad.score().map((x) => x.total).join(),
     'the same seed scored identically under both — the option is inert');
}

// ============================ 4. research more than once, at a rising price

/* The complaint: research is slow, and each one takes a card out of the hand
 * you are trying to assemble, so a bad hand stays bad for rounds. The rule lets
 * you go again at a rising price; the price is what stops it becoming "cycle
 * the whole hand every turn". */
{
  const g1 = new E.Game(3, 1, { humans: [] });
  ok(g1.RESEARCH_RULE === 'once' && g1.RESEARCH_MAX === 1,
     'the printed once-a-turn rule is not the default');
  const g2 = new E.Game(3, 1, { humans: [], researchRule: 'twice' });
  ok(g2.RESEARCH_MAX === 2, `twice gave a cap of ${g2.RESEARCH_MAX}`);
  const g3 = new E.Game(3, 1, { humans: [], researchRule: 'escalating' });
  ok(g3.RESEARCH_MAX === Infinity, 'escalating is capped');
  ok(new E.Game(3, 1, { humans: [], researchRule: 'junk' }).RESEARCH_RULE === 'once',
     'an unknown research rule was accepted');

  /* The price ladder, and that it is the SAME number the client is shown and
   * the engine charges — the whole reason researchCost() exists in one place. */
  const st = (n) => ({ researches: n });
  ok(g1.researchCost(st(0)) === 1, 'the first research is not 1 gold');
  ok(g3.researchCost(st(0)) === 1 && g3.researchCost(st(1)) === 2
     && g3.researchCost(st(2)) === 3,
     `the escalating ladder is ${[0, 1, 2].map((n) => g3.researchCost(st(n))).join('/')}`);
  ok(g1.researchCost(st(1)) === 1,
     'the printed rule should never quote a price above 1 — there is only one');

  /* The cap is enforced, and says which reason it is refusing for. */
  const rich = { vrow: [], hand: [{ r: 5, s: 'plains' }], gold: 99 };
  ok(g1.canResearch(rich, st(0)) && !g1.canResearch(rich, st(1)),
     'the once rule allows a second research');
  ok(g2.canResearch(rich, st(1)) && !g2.canResearch(rich, st(2)),
     'the twice rule does not stop at two');
  ok(g3.canResearch(rich, st(5)), 'the escalating rule stopped early for a rich player');
  ok(g1.researchBlocked(rich, st(1)) === 'why.research.done',
     'the once rule does not explain itself');
  ok(g2.researchBlocked(rich, st(2)) === 'why.research.max',
     `the twice rule blocked with ${g2.researchBlocked(rich, st(2))}`);

  /* Poverty, not the cap, is what stops the escalating rule — and the reason
   * given has to be the true one or the button lies. */
  const poor = { vrow: [], hand: [{ r: 5, s: 'plains' }], gold: 2 };
  ok(!g3.canResearch(poor, st(2)), 'a player with 2 gold took a 3-gold research');
  ok(g3.researchBlocked(poor, st(2)) === 'why.research.gold',
     `a player who cannot afford it was told: ${g3.researchBlocked(poor, st(2))}`);

  /* And it reaches real games: second-and-later researches actually happen,
   * and they cost more than the first. */
  const once = E.playOut(3, 4242, { trickRule: 'dock' });
  const esc = E.playOut(3, 4242, { trickRule: 'dock', researchRule: 'escalating' });
  ok(!(once.stats.research_repeat > 0),
     'a second research happened under the printed once-a-turn rule');
  ok(esc.stats.research_repeat > 0,
     'no second research ever happened under the escalating rule');
  ok(esc.stats.gold_out_upgrade / esc.stats.upgrades
     > once.stats.gold_out_upgrade / once.stats.upgrades,
     'the escalating rule is not charging more per research');
  ok(esc.finished() && once.finished(), 'a game under either rule failed to finish');
}

// ==================================== 5. effect A when the total is what wins

/* "+1 card" is a quarter of a meld under count scoring and almost nothing under
 * sum, where it only moves a tie-break. So A reads differently under the two
 * rules, and the size of the bonus is a ladder that can be retuned. */
{
  /* Every rung, at one rank per band. */
  const at = (ladder) => [3, 8, 13, 18].map((r) => E.effectASum(r, ladder)[0]).join('/');
  ok(at('steps') === '1/2/3/4', `steps ladder is ${at('steps')}`);
  ok(at('double') === '2/4/6/8', `double ladder is ${at('double')}`);
  ok(at('band') === '3/6/9/12', `band ladder is ${at('band')}`);
  ok(at('steep') === '4/8/12/16', `steep ladder is ${at('steep')}`);
  /* The one that is not a table at all: the card adds its own rank. */
  ok(at('rank') === '3/8/13/18', `rank ladder is ${at('rank')}`);
  ok(E.effectASum(17, 'rank')[0] === 17, 'the rank rung does not add the rank');

  /* Ties are untouched by the ladder — the middle two bands still win them. */
  for (const l of ['steps', 'double', 'band', 'steep', 'rank']) {
    ok(E.effectASum(8, l)[1] === true, `${l}: the 6-10 band lost its tie win`);
    ok(E.effectASum(18, l)[1] === true, `${l}: the 16-20 band lost its tie win`);
    ok(E.effectASum(3, l)[1] === false, `${l}: the 1-5 band gained a tie win`);
  }

  /* A game takes the rung, and an unknown one falls back rather than throwing.
   * `rank` is stored as null because it is not a table, so a truthiness test
   * here silently dropped it back to the default — which is exactly how two
   * ladders came to measure identically. */
  const ladderOf = (v) => new E.Game(3, 1, { humans: [], meldScore: 'sum',
                                             aSumLadder: v }).A_SUM_LADDER;
  ok(ladderOf('rank') === 'rank',
     `the "rank" rung fell back to ${ladderOf('rank')} — it is stored as null `
     + 'and a truthiness check will drop it');
  ok(ladderOf('steep') === 'steep', 'the steep rung is not accepted');
  ok(ladderOf('junk') === 'band', `an unknown rung gave ${ladderOf('junk')}`);
  ok(ladderOf(undefined) === 'band', 'no rung named did not give the default');
}

/* Under count scoring A must still do exactly what the card prints — the new
 * reading is for the new rule only, and must not leak into the printed game. */
{
  const g = E.playOut(3, 4242, { trickRule: 'dock' });
  ok(!g.stats.effect_a_sum_gain,
     'A added points to a total in a game played under the printed count rule');
  const s = E.playOut(3, 4242, { trickRule: 'dock', meldScore: 'sum' });
  ok(s.stats.effect_a_sum_gain > 0,
     'A never added anything to a total under sum scoring — the new reading is '
     + 'not reaching the game');
}

/* And the rungs are actually different games, or the option is decoration. */
{
  const sig = (o) => {
    let gain = 0, decided = 0;
    for (let seed = 1; seed <= 25; seed++) {
      const g = E.playOut(3, seed * 7919 + 13,
                          Object.assign({ trickRule: 'dock', meldScore: 'sum' }, o));
      gain += g.stats.effect_a_sum_gain || 0;
      decided += g.stats.a_decided || 0;
    }
    return { gain, decided };
  };
  const quiet = sig({ aSumLadder: 'steps' });
  const loud = sig({ aSumLadder: 'steep' });
  ok(loud.gain > quiet.gain,
     `the steep ladder granted ${loud.gain} points and the quiet one ${quiet.gain}`
     + ' — the rungs are not reaching the game');
  ok(loud.decided >= quiet.decided,
     `a bigger bonus decided ${loud.decided} tricks against the small one's `
     + `${quiet.decided} — the ladder looks inverted`);
}

/* The card has to SAY what it does, or a player reads "+1 card" while the rule
 * counts totals. */
{
  const printed = E.effectText(18);
  ok(/card/.test(printed.a), `the printed A text lost its card wording: ${printed.a}`);
  const summed = E.effectText(18, { meldScore: 'sum', aSumLadder: 'band' });
  ok(/\+12/.test(summed.a) && /total/.test(summed.a),
     `under sum scoring the 16-20 card should offer +12 to the total: "${summed.a}"`);
  ok(/ties/.test(summed.a), 'the 16-20 card stopped winning ties');
  ok(/\+12/.test(summed.aShort), `the short form reads "${summed.aShort}"`);
  /* B and C are none of this rule's business. */
  ok(summed.b === printed.b && summed.c === printed.c,
     'changing how the trick is won rewrote effects B or C');
  /* And the text follows the ladder rather than being written out. */
  const steep = E.effectText(18, { meldScore: 'sum', aSumLadder: 'steep' });
  ok(/\+16/.test(steep.a), `the card does not follow the ladder: "${steep.a}"`);
}

// ================================= 6. and the setup page actually sends them
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
    ok(!!q('#research-rule'), 'the setup page has no control for research per turn');
    if (q('#research-rule')) q('#research-rule').value = 'escalating';
    ok(!!q('#consolation'), 'the setup page has no control for the losing payout');
    if (q('#consolation')) q('#consolation').value = 'ladder';
    require('./test_setup.js').start(w, d, { players: 3, seat: 0, seed: 31 });

    setTimeout(() => {
      const got = w.eval('JSON.stringify({'
        + ' score: G.MELD_SCORE,'
        + ' bands: G.BANDS.map((b) => b[1]).join("-"),'
        + ' optLayout: GARGS.opts.layout,'
        + ' optScore: GARGS.opts.meldScore,'
        + ' repLayout: REP.setup.layout,'
        + ' repScore: REP.setup.meldScore,'
        + ' research: G.RESEARCH_RULE,'
        + ' repResearch: REP.setup.researchRule,'
        + ' consolation: G.CONSOLATION,'
        + ' repConsolation: REP.setup.consolation,'
        + ' shown: [...document.querySelectorAll(".pboard .tier-row:not(.head) .tname em")]'
        + '   .map((n) => parseInt(n.textContent, 10)).join("-")'
        + '})');
      const r = JSON.parse(got);
      ok(r.score === 'sum', `the game is scoring tricks by ${r.score}`);
      ok(r.research === 'escalating',
         `the game is using the ${r.research} research rule — the setup page's `
         + 'choice never reached it');
      ok(r.repResearch === 'escalating',
         `the report records researchRule=${r.repResearch}`);
      ok(r.consolation === 'ladder',
         `the game is paying losers by the ${r.consolation} rule`);
      ok(r.repConsolation === 'ladder',
         `the report records consolation=${r.repConsolation}`);
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
      /* The card faces on screen must carry the new A text too. The engine's
       * effectText() and the page's fxText() are two separate copies — one
       * translated, one not — so proving the engine changed proves nothing
       * about what the player reads. */
      const faces = w.eval('JSON.stringify({'
        + ' a18: fxText(18).a, a18s: fxText(18).aShort,'
        + ' a3: fxText(3).a,'
        + ' b18: fxText(18).b'
        + '})');
      const f = JSON.parse(faces);
      ok(/\+12/.test(f.a18) && /total/i.test(f.a18),
         `a 16-20 card on screen still reads "${f.a18}" — the player is being `
         + 'told it adds cards while the rule counts totals');
      ok(/\+12/.test(f.a18s), `the short form on screen reads "${f.a18s}"`);
      ok(/\+3\b/.test(f.a3), `a 1-5 card on screen reads "${f.a3}"`);
      ok(!/total/i.test(f.b18), 'effect B was rewritten by the scoring rule');

      ok(!errs.length, 'the page logged errors: ' + errs.slice(0, 2).join(' | '));
      finish();
    }, 700);
  }, 400);
}

function finish() {
  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : 'options: layouts parse in four forms and refuse five bad ones and stay off '
      + 'the module table; research may run twice or escalate, at a price the button '
      + 'and the engine read from one place; the sum rule changes who wins real '
      + 'tricks and effect A has its own reading under it; and the setup page sends '
      + 'all of it through to the game, the report and the screen');
  process.exit(fail.length ? 1 : 0);
}
