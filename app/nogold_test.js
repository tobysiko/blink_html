/* "There is no indication when an enemy tile cannot be attacked for lack of
 * gold. This is confusing."
 *
 * It was, and the reason is worth stating: an unaffordable attack is the only
 * refusal in Blink that leaves no trace. cellActions() returned an empty list,
 * so the tile was simply not highlighted — identical on screen to a tile out of
 * reach, or of the wrong suit, or already full. Every other refusal explains
 * itself: a full tile prints n/cap, distance is visible, and the suit is on the
 * card in your hand. Only the price was invisible.
 *
 * So the tile is now drawn dimmed, with the price on it, and refuses the click.
 * Checked at both levels, because the engine knowing is not the player seeing.
 */
const fs = require('fs');
const path = require('path');
const E = require('./engine.js');

let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

// ---------------------------------------------------------- 1. the engine
/* A board where seat 0 sits next to a rival Mountain (attack costs 2) and a
 * rival Forest (costs 1), with the gold varied underneath.
 *
 * The gold rule is pinned on, because a price is the thing being tested and
 * the duel does not charge one. What the duel does to this complaint is
 * checked at the bottom of this section: it answers it by deletion. */
function board(gold) {
  const g = new E.Game(2, 1, { humans: [0], combat: 'gold' });
  g.m.tiles.clear();
  const put = (c, r, terrain, seat) => {
    const t = g.m._add([c, r], terrain);
    if (seat !== null && seat !== undefined) t.units.push(seat);
    return t;
  };
  put(0, 0, 'plains', 0);          // mine, so the rivals are in reach
  put(1, 0, 'mountain', 1);        // rival, attack costs 2
  put(0, 1, 'forest', 1);          // rival, attack costs 1
  g.P[0].gold = gold;
  return g;
}
const keysOf = (list) => list.map((x) => x[0]).sort().join(' ');

{
  const g = board(0);
  const mtn = { r: 9, s: 'mountain' }, forest = { r: 9, s: 'forest' };
  const reachable = E.reach(g.m, 0);

  /* With no gold, neither is a legal option... */
  ok(!E.cardOptions(g.m, mtn, 0, 0, reachable).some(([, a]) => a === 'attack'),
     'a Mountain attack was offered with no gold to pay for it');
  /* ...and both are reported as blocked, with their price. */
  const bM = E.cardBlocked(g.m, mtn, 0, 0, reachable);
  ok(keysOf(bM) === '1,0', `the blocked Mountain list is ${keysOf(bM)}`);
  ok(bM[0] && bM[0][1] === 2, `the Mountain price is reported as ${bM[0] && bM[0][1]}`);
  const bF = E.cardBlocked(g.m, forest, 0, 0, reachable);
  ok(bF[0] && bF[0][1] === 1, `the Forest price is reported as ${bF[0] && bF[0][1]}`);

  /* With the money, it stops being blocked and starts being an option. */
  const rich = E.reach(board(2).m, 0);
  ok(E.cardBlocked(board(2).m, mtn, 0, 2, rich).length === 0,
     'a Mountain is still flagged as unaffordable when the gold is there');
  ok(E.cardBlocked(board(1).m, mtn, 0, 1, rich).length === 1,
     'one gold short of a Mountain and nothing is flagged');
  ok(E.cardBlocked(board(1).m, forest, 0, 1, rich).length === 0,
     'a Forest costing 1 is flagged as unaffordable with 1 gold in hand');

  /* Only rival tiles, and only the matching suit. Flagging your own tiles, or
   * tiles this card could never touch, would be noise pretending to be help. */
  const own = E.cardBlocked(g.m, { r: 9, s: 'plains' }, 0, 0, reachable);
  ok(own.length === 0, `a Plains card flagged ${own.length} cells — its own tile `
     + 'is not an attack and there is no rival Plains on this board');
}

/* Under the DUEL — the default — the complaint is answered by removing the
 * thing complained about. An attack costs no coins at all, so a player with an
 * empty purse is refused nothing, and there is no price left to fail to
 * display. The badge above must not appear here, or it would be telling the
 * truth about a rule that is not being played. */
{
  const g = new E.Game(2, 1, { humans: [0] });          // no combat option: duel
  g.m.tiles.clear();
  const put = (c, r, terrain, seat) => {
    const t = g.m._add([c, r], terrain);
    if (seat !== null) t.units.push(seat);
    return t;
  };
  put(0, 0, 'plains', 0);
  put(1, 0, 'mountain', 1);
  g.P[0].gold = 0;
  const mtn = { r: 9, s: 'mountain' };
  const reachable = E.reach(g.m, 0);
  ok(E.cardOptions(g.m, mtn, 0, 0, reachable).some(([, a]) => a === 'attack'),
     'the duel refused a penniless attack — it charges no coins');
  ok(E.cardBlocked(g.m, mtn, 0, 0, reachable).length === 0,
     'the duel flagged a tile as unaffordable, but there is no price to afford');
  ok(g.m.attackGold('mountain') === 0 && g.m.attackGold('forest') === 0,
     'the map is still quoting the gold rule\'s prices under the duel');
}

// ------------------------------------------------------------ 2. the page
const html = fs.readFileSync(require('./test_setup.js').PLAY_HTML, 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
const errs = [];
w.console.error = (...a) => errs.push(a.join(' '));

setTimeout(() => {
  const click = (x) => x.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const q = (s) => d.querySelector(s);
  const qa = (s) => [...d.querySelectorAll(s)];
  const txt = () => q('#prompt').textContent.replace(/\s+/g, ' ');

  require('./test_setup.js').start(w, d, { players: 3, seat: 0, seed: 77 });

  /* Wait for the MAP turn itself, asked of the page rather than read off the
   * prompt: a duel can interrupt on somebody else's turn while the sentence
   * above still reads like your own, and the setup below writes into
   * REQ.state, which only a turn request has. */
  const isTurn = () => w.eval('REQ && REQ.type') === 'turn';
  let guard = 0;
  while (!isTurn() && guard++ < 60) {
    if (w.eval('REQ && REQ.type') === 'duel') {
      const c = qa('#hand button.want')[0] || qa('#hand button').find((x) => !x.disabled);
      if (c) { click(c); continue; }
    }
    const b = qa('#prompt button').find((x) =>
      /Skip|Take the loss|Stop|Cancel|Play meld/.test(x.textContent) && !x.disabled);
    if (b) { click(b); continue; }
    const h = qa('#hand button')[0];
    if (h && /Play a meld/.test(txt())) { click(h); continue; }
    const aside = q('#mymeld button[data-aside]') || q('.objpick button');
    if (aside) { click(aside); continue; }
    break;
  }
  if (!isTurn()) {
    fail.push('never reached my own map turn: ' + txt().slice(0, 80));
    return report();
  }

  /* Build the situation the complaint describes: a rival Mountain beside me, a
   * Mountain card in the meld, and NOT A COIN to my name.
   *
   * Under the gold rule this was the confusing case — the tile simply was not
   * highlighted, identically to a tile out of reach. The app now plays the
   * duel, where an attack costs no coins at all, so the same board must come
   * out the other way: the tile is live, there is no price on it, and a
   * penniless player may walk straight into the fight. The complaint is
   * answered by deletion rather than by a better badge, and this is where that
   * is checked end to end. The badge itself still has a test — above, at the
   * engine, with the gold rule pinned on, because the option still exists. */
  const set = w.eval(`(() => {
    const p = G.P[ME];
    for (const [k, t] of G.m.tiles) { t.units.length = 0; t.owner = null; }
    const put = (c, r, terr, seat) => {
      let t = G.m.tiles.get(c + ',' + r);
      if (!t) t = G.m._add([c, r], terr);
      t.terrain = terr; t.units.length = 0;
      if (seat !== null) t.units.push(seat);
      return t;
    };
    put(0, 0, 'plains', ME);
    put(1, 0, 'mountain', (ME + 1) % G.P.length);
    p.gold = 0;
    const card = { r: 9, s: 'mountain' };
    REQ.state.cards = [card];
    REQ.opts = G.turnOptions(p, REQ.state);
    SEL.card = card;
    render();
    const e = REQ.opts.cards[0];
    return { options: e.options.length, blocked: (e.blocked || []).map((x) => x.join(':')),
             combat: G.COMBAT };
  })()`);

  ok(set.combat === 'duel', `the page is playing ${set.combat}, not the duel`);
  ok(set.blocked.length === 0,
     `a penniless attack was flagged as unaffordable: ${JSON.stringify(set.blocked)}`);
  ok(set.options > 0, 'the Mountain card was offered no cell at all with no gold');

  const hex = q('#map [data-key="1,0"]');
  ok(!!hex, 'the rival Mountain is not drawn at all');
  ok(hex && hex.classList.contains('hot'),
     `the rival Mountain is drawn as "${hex && hex.getAttribute('class')}" — under `
     + 'the duel an empty purse refuses nothing, so it should be live');
  ok(hex && !hex.classList.contains('nope'),
     'the tile is dimmed as unaffordable under a rule that charges nothing');

  const badges = qa('#map text').map((n) => n.textContent).join(' | ');
  ok(!/needs \d/i.test(badges),
     `the map is still quoting a price that is not charged: ${badges.slice(0, 120)}`);

  /* And the click goes through: a penniless player gets their fight. */
  if (hex) click(hex);
  const after = w.eval('REQ && REQ.type');
  ok(after === 'duel',
     `clicking the tile with no gold led to "${after}" instead of a duel`);


  report();
}, 500);

function report() {
  ok(!errs.length, 'the page logged errors: ' + errs.slice(0, 2).join(' | '));
  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : 'unaffordable attacks: under the gold rule the engine still reports the '
      + 'price so the map can dim the tile and say what it costs — and under the '
      + 'duel, which is what the app plays, there is no price, no dimmed tile and '
      + 'no refusal: a player with an empty purse clicks the Mountain and gets '
      + 'their fight');
  process.exit(fail.length ? 1 : 0);
}
