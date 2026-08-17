/* Making landfall, driven through the actual page.
 *
 * This test exists because of how the bug it covers was mishandled. The engine
 * function that lists eligible cells was fixed, unit-tested, and reported as
 * "water exploration fixed" — while the app still did not offer a single one of
 * those cells to a player, because the UI never asked for them. The engine was
 * right and the game was broken, and a passing engine test said nothing about
 * it. So this drives the built page: clicks Move, clicks a ship, and reads what
 * the map actually lights up.
 *
 * The rule, as the designer stated it: a move that starts on Ocean may end on
 * any Ocean tile the ship can reach through connected water, OR on any empty
 * space touching that water — in which case a tile is laid there and the unit
 * lands on it, all in the one move action.
 *
 * Needs jsdom.
 */
const fs = require('fs');
const path = require('path');
const E = require('./engine.js');

let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* ---- 1. the engine's own answer, on a board built for the question ------ */
/* Kept here as well as in move_test because the UI half below depends on it
 * being right, and a failure in both at once should say which is which. */
function board(spec) {
  const g = new E.Game(2, 1, { humans: [0] });
  g.m.tiles.clear();
  for (const [c, r, terrain, seat] of spec) {
    const t = g.m._add([c, r], terrain);
    if (seat !== undefined && seat !== null) t.units.push(seat);
  }
  return g;
}
{
  /* A lone ocean tile with a ship, two land tiles beside it, and a second
   * unconnected coastline far away. This is the geometry from the playtest
   * screenshot: the ship's water has NO connected ocean, so under a rule that
   * only fires on a water-to-water move the advantage could never happen and
   * the empty cells beside the ship were unreachable. */
  const g = board([
    [0, 0, 'ocean', 0], [0, 1, 'plains', null], [1, 0, 'mountain', null],
    [8, 0, 'plains', null], [9, 0, 'plains', null], [8, 1, 'plains', null],
  ]);
  const p = g.P[0];
  const sea = [...g.moveDests(p, '0,0')].filter((k) => {
    const t = g.m.tiles.get(k);
    return t && t.terrain === 'ocean';
  });
  ok(sea.length === 0, 'the test board is wrong — the ship has connected ocean');

  const cells = g.landfallCells(p, '0,0', false);
  ok(cells.length > 0,
     'a ship on a lone Ocean tile is offered nowhere to make landfall — this is '
     + 'exactly the board from the playtest screenshot, where the empty hexes '
     + 'beside the ship were unreachable');

  const water = g.seaGroup('0,0');
  for (const k of cells) {
    const [c, r] = E.unK(k);
    ok(E.nbrKeys(c, r).some((n) => water.has(n)),
       `${k} is offered for landfall but touches none of the ship's water`);
    ok(!g.m.tiles.has(k), `${k} is offered for landfall but already has a tile`);
    ok(E.nbrKeys(c, r).filter((n) => g.m.tiles.has(n)).length >= 2,
       `${k} is offered for landfall but touches fewer than two tiles`);
  }
  const far = cells.filter((k) => E.unK(k)[0] >= 7);
  ok(far.length === 0, `landfall offered ${far.join(' ')} across the map`);

  /* Once the advantage is spent, the option is gone. */
  ok(g.landfallCells(p, '0,0', true).length === 0,
     'landfall is still offered after the water advantage was already used');

  /* And it resolves: the tile appears, the unit is on it, the water is empty. */
  const target = cells[0];
  const it = g._humanTurn(p, []);
  let r = it.next();
  let guard = 0;
  while (!r.done && guard++ < 20) {
    const q = r.value;
    if (q.type === 'turn') r = it.next({ kind: 'move', src: '0,0', dest: target,
                                         terrain: 'forest' });
    else if (q.type === 'waterexplore') r = it.next({ cell: target, terrain: 'forest' });
    else break;
    if (guard > 1) break;
  }
  const made = g.m.tiles.get(target);
  ok(!!made, `the move onto ${target} laid no tile`);
  ok(made && made.terrain === 'forest',
     `landfall laid a ${made && made.terrain} tile, not the forest that was asked for`);
  ok(made && made.units.includes(0), 'the unit did not land on the tile it found');
  ok(g.m.tiles.get('0,0').units.length === 0,
     'the unit is ashore AND still on the water it sailed from');
}

/* ---- 2. and now the part that was actually broken: does the app offer it? */

const html = fs.readFileSync(path.join(__dirname, '..', 'Blink-play-v0.22.html'), 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
const errs = [];
w.addEventListener('error', (e) => errs.push(e.message));
w.console.error = (...a) => errs.push(a.join(' '));

setTimeout(() => {
  const click = (x) => x.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const q = (s) => d.querySelector(s);
  const qa = (s) => [...d.querySelectorAll(s)];
  const txt = () => q('#prompt').textContent.replace(/\s+/g, ' ');

  /* A seed where the human seat has a ship. Rather than hunt for one, the board
   * is arranged directly once the game is up — the point of this test is the
   * wiring between engine and screen, not the shuffle. */
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

  /* Put a ship on its own patch of water, with land beside it and empty cells
   * that touch the water — the screenshot's geometry, inside the real app. */
  const built = w.eval(`(() => {
    const p = G.P[ME];
    for (const [k, t] of G.m.tiles) { t.units.length = 0; t.owner = null; }
    const put = (c, r, terr, mine) => {
      let t = G.m.tiles.get(c + ',' + r);
      if (!t) t = G.m._add([c, r], terr);
      t.terrain = terr;
      t.units.length = 0;
      if (mine) t.units.push(ME);
      return t;
    };
    put(0, 0, 'ocean', true);
    put(0, 1, 'plains', false);
    put(1, 0, 'mountain', false);
    for (const terr of ['plains','forest','ocean','mountain']) G.m.supply[terr] = 5;
    REQ.opts = G.turnOptions(p, REQ.state);
    render();
    return { sources: REQ.opts.moveSources.slice(),
             landfall: JSON.parse(JSON.stringify(REQ.opts.landfall || {})) };
  })()`);

  ok(built.sources.includes('0,0'),
     'the ship is not even offered as a move source');
  ok(built.landfall && built.landfall['0,0'] && built.landfall['0,0'].length > 0,
     'the turn options carry no landfall cells for the ship — the engine knows '
     + 'where it may land and the client is never told');

  // click Move, then the ship, and read the map
  const moveBtn = qa('#prompt button').find((b) => /^Move/.test(b.textContent));
  ok(!!moveBtn, 'no Move button on a turn with a ship and moves left');
  if (moveBtn) click(moveBtn);
  const ship = q('#map [data-key="0,0"]');
  ok(!!ship, 'the ship is not clickable on the map');
  if (ship) click(ship);

  const lit = w.eval(`(() => {
    const out = [];
    for (const [k, a] of activeCells()) out.push(k + ':' + a.act);
    return out;
  })()`);
  const landfallLit = lit.filter((s) => s.endsWith(':landfall')).map((s) => s.split(':')[0]);
  ok(landfallLit.length > 0,
     'after picking the ship the map lights up no landfall cells — this is the '
     + `bug as reported; lit instead: ${lit.join(' ') || '(nothing)'}`);

  const expect = (built.landfall && built.landfall['0,0']) || [];
  for (const k of expect)
    ok(landfallLit.includes(k),
       `${k} is a legal landfall and the map does not offer it`);

  /* And the badge says what it will do, rather than leaving an empty hex lit
   * with no explanation. */
  const badge = w.eval(`(() => {
    const a = activeCells().get(${JSON.stringify(landfallLit[0] || '')});
    return a ? cellBadge(a) : null;
  })()`);
  ok(badge && /land/i.test(badge),
     `the landfall hex's badge reads ${JSON.stringify(badge)} — it should say a `
     + 'tile will be laid and the unit will step onto it');

  /* Click it for real and confirm the board changed the way the rule says. */
  const cell = landfallLit[0];
  if (cell) {
    const before = w.eval('G.m.tiles.size');
    /* An empty cell is drawn as a `ghost` polygon and carries data-key like any
     * other hex — that is what makes it clickable at all. */
    const hex = q(`#map [data-key="${cell}"]`);
    ok(!!hex, `the landfall cell ${cell} is lit but has nothing to click`);
    ok(hex && hex.classList.contains('ghost'),
       `${cell} should be drawn as an empty ghost hex, not an existing tile`);
    ok(hex && hex.classList.contains('hot'),
       `${cell} is a legal landfall but is not drawn as clickable`);
    if (hex) {
      click(hex);
      /* With more than one terrain left in the supply the engine asks which to
       * lay — and it must ask for the TERRAIN, not for the cell again. */
      const asked = txt();
      ok(/which terrain/i.test(asked) || /Landfall/i.test(asked),
         `after clicking the landfall hex the game asked: "${asked.slice(0, 90)}"`
         + ' — it should be asking which terrain to lay, not asking for a cell');
      const terrBtn = qa('#prompt button').find((b) => /^(Plains|Forest|Ocean|Mountain)$/
        .test(b.textContent.trim()));
      ok(!!terrBtn, 'no terrain buttons offered for the landfall: '
         + qa('#prompt button').map((b) => b.textContent.trim()).join('/'));
      if (terrBtn) click(terrBtn);
      setTimeout(() => {
        const after = w.eval(`(() => {
          const t = G.m.tiles.get(${JSON.stringify(cell)});
          return { size: G.m.tiles.size, exists: !!t,
                   mine: t ? t.units.includes(ME) : false,
                   terrain: t ? t.terrain : null,
                   ship: (G.m.tiles.get('0,0') || {}).units || [] };
        })()`);
        ok(after.exists, `clicking ${cell} laid no tile`);
        ok(after.size === before + 1,
           `the map went from ${before} tiles to ${after.size} — expected one more`);
        ok(after.mine, `the unit did not land on ${cell}`);
        ok(after.ship.length === 0, 'the unit is ashore and still on the water');
        report();
      }, 400);
      return;
    }
  }
  report();
}, 500);

function report() {
  ok(!errs.length, 'the page logged errors: ' + errs.slice(0, 3).join(' | '));
  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : 'landfall: a ship is offered the empty ground beside its own water, the '
      + 'map lights those cells with a badge that explains them, and clicking '
      + 'one lays the tile and puts the unit on it');
  process.exit(fail.length ? 1 : 0);
}
