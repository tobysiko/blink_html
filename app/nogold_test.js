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
 * rival Forest (costs 1), with the gold varied underneath. */
function board(gold) {
  const g = new E.Game(2, 1, { humans: [0] });
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

// ------------------------------------------------------------ 2. the page
const html = fs.readFileSync(path.join(__dirname, '..', 'Blink-play-v0.22.html'), 'utf8');
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

  let guard = 0;
  while (!/Your turn/.test(txt()) && guard++ < 60) {
    const b = qa('#prompt button').find((x) =>
      /Skip|Take the loss|Stop|Cancel|Play meld/.test(x.textContent) && !x.disabled);
    if (b) { click(b); continue; }
    const h = qa('#hand button')[0];
    if (h && /Play a meld/.test(txt())) { click(h); continue; }
    const aside = q('#mymeld button[data-aside]') || q('.objpick button');
    if (aside) { click(aside); continue; }
    break;
  }
  if (!/Your turn/.test(txt())) {
    fail.push('never reached my own map turn: ' + txt().slice(0, 80));
    return report();
  }

  /* Build the situation directly: a rival Mountain beside me, a Mountain card
   * in the meld, and no gold. This is the exact board the complaint describes. */
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
    return { options: e.options.length, blocked: (e.blocked || []).map((x) => x.join(':')) };
  })()`);

  ok(set.blocked.includes('1,0:2'),
     `the turn options do not flag the unaffordable Mountain: ${JSON.stringify(set.blocked)}`);

  /* The map must SHOW it — this is the whole complaint. */
  const hex = q('#map [data-key="1,0"]');
  ok(!!hex, 'the rival Mountain is not drawn at all');
  ok(hex && hex.classList.contains('nope'),
     `the unaffordable tile is drawn as "${hex && hex.getAttribute('class')}" — `
     + 'it needs to be visibly refused, not silently absent');
  ok(hex && !hex.classList.contains('hot'),
     'the unaffordable tile is drawn as clickable');

  /* And it must say the price. */
  const badges = qa('#map text').map((n) => n.textContent).join(' | ');
  ok(/needs 2/i.test(badges),
     `no badge names the price on the map: ${badges.slice(0, 120)}`);

  /* Clicking it does nothing at all — no answer, no state change. */
  const before = w.eval('JSON.stringify({log: LOG.length, gold: G.P[ME].gold,'
    + ' units: [...G.m.tiles.values()].map((t) => t.units.length).join("")})');
  if (hex) click(hex);
  const after = w.eval('JSON.stringify({log: LOG.length, gold: G.P[ME].gold,'
    + ' units: [...G.m.tiles.values()].map((t) => t.units.length).join("")})');
  ok(before === after,
     'clicking a tile that says it cannot be attacked did something anyway');

  /* Give them the gold and the same tile becomes a real target. */
  const now = w.eval(`(() => {
    G.P[ME].gold = 2;
    REQ.opts = G.turnOptions(G.P[ME], REQ.state);
    render();
    const h = document.querySelector('#map [data-key="1,0"]');
    return { cls: h ? h.getAttribute('class') : null,
             blocked: (REQ.opts.cards[0].blocked || []).length };
  })()`);
  ok(now.blocked === 0, 'the tile is still flagged as unaffordable with 2 gold');
  ok(now.cls && /\bhot\b/.test(now.cls) && !/\bnope\b/.test(now.cls),
     `with the gold in hand the tile is drawn as "${now.cls}" — it should be live`);

  report();
}, 500);

function report() {
  ok(!errs.length, 'the page logged errors: ' + errs.slice(0, 2).join(' | '));
  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : 'unaffordable attacks: the engine reports them with their price, the map '
      + 'draws them dimmed and says what they cost, the click is refused, and '
      + 'they become live targets the moment the gold is there');
  process.exit(fail.length ? 1 : 0);
}
