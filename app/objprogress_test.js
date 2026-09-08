/* MAP OBJECTIVES: what counts, what overlaps, and how close you are.
 *
 * An objective is three tiles YOU OCCUPY: a middle of one terrain touching an
 * end of each of the other two. The ends need not touch each other, but they
 * must be two different tiles - which is the entire rule on a card like the
 * Fjord, whose two ends are the same terrain.
 *
 * The two questions a player actually asks, pinned here because the answers
 * are design decisions rather than accidents:
 *
 *   - Objectives are judged INDEPENDENTLY against the whole map, so one tile
 *     may be the middle of two of them at once. Nothing is reserved.
 *   - Each objective scores ONCE. A pattern you have built twice is worth no
 *     more than a pattern you have built once.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };
const byName = (n) => E.OBJECTIVES.find((o) => o.name === n);

function blank() {
  const g = new E.Game(2, 1, { humans: [], objectives: 'both' });
  for (const [, t] of g.m.tiles) t.units.length = 0;
  return g;
}
function put(g, cell, ter, seat) {
  const k = E.K(cell[0], cell[1]);
  let t = g.m.tiles.get(k);
  if (!t) { g.m.supply[ter] = Math.max(1, g.m.supply[ter]); g.m.doExplore(k, ter); t = g.m.tiles.get(k); }
  t.terrain = ter;
  t.units.length = 0;
  if (seat !== undefined) t.units.push(seat);
  return k;
}

/* ---- the two ends have to be two different tiles ---- */
{
  const fjord = byName('Fjord');            // mountain - OCEAN - mountain
  const g = blank();
  const c = E.unK([...g.m.tiles.keys()][0]);
  put(g, c, 'ocean', 0);
  put(g, E.step(c, 'E'), 'mountain', 0);
  let pr = g.objectiveProgress(0, fjord);
  ok(!pr.done, 'one mountain beside the water already finished a Fjord');
  ok(pr.n === 2, `one end in place reported ${pr.n} of 3`);
  ok(pr.missing === 'mountain', `wanted the second mountain, was told ${pr.missing}`);

  put(g, E.step(c, 'W'), 'mountain', 0);
  pr = g.objectiveProgress(0, fjord);
  ok(pr.done, 'two mountains either side of the water did not finish a Fjord');
  ok(pr.cells.length === 3, `a finished objective named ${pr.cells.length} tiles`);
}

/* ---- the tiles have to be YOURS ---- */
{
  const fjord = byName('Fjord');
  const g = blank();
  const c = E.unK([...g.m.tiles.keys()][0]);
  put(g, c, 'ocean', 0);
  put(g, E.step(c, 'E'), 'mountain', 0);
  put(g, E.step(c, 'W'), 'mountain', 1);          // the rival's mountain
  ok(!g.objectiveProgress(0, fjord).done,
     "a rival's tile completed your objective");
  ok(g.objectiveProgress(1, fjord).n <= 1,
     'the rival scored progress off a middle that is not theirs');
}

/* ---- one tile is the middle of two objectives at once ---- */
{
  const fjord = byName('Fjord');              // mountain - ocean - mountain
  const shelt = byName('Sheltered Water');    // forest   - ocean - forest
  const g = blank();
  const c = E.unK([...g.m.tiles.keys()][0]);
  const mid = put(g, c, 'ocean', 0);
  put(g, E.step(c, 'E'), 'mountain', 0);
  put(g, E.step(c, 'W'), 'mountain', 0);
  put(g, E.step(c, 'NE'), 'forest', 0);
  put(g, E.step(c, 'SE'), 'forest', 0);
  const a = g.objectiveProgress(0, fjord), b = g.objectiveProgress(0, shelt);
  ok(a.done && b.done, 'one middle did not serve both objectives');
  ok(a.cells[0] === mid && b.cells[0] === mid,
     'the two objectives did not share the middle tile they both stand on');
}

/* ---- and each objective scores once, however many times you built it ---- */
{
  const fjord = byName('Fjord');
  const g = blank();
  const keys = [...g.m.tiles.keys()];
  const c = E.unK(keys[0]);
  put(g, c, 'ocean', 0);
  put(g, E.step(c, 'E'), 'mountain', 0);
  put(g, E.step(c, 'W'), 'mountain', 0);
  g.P[0].objectives = [fjord];
  g.P[1].objectives = [];
  const one = g.score()[0].obj;
  /* A second, separate Fjord somewhere else on the map. */
  const d = E.step(E.step(c, 'SE'), 'SE');
  put(g, d, 'ocean', 0);
  put(g, E.step(d, 'E'), 'mountain', 0);
  put(g, E.step(d, 'W'), 'mountain', 0);
  const two = g.score()[0].obj;
  ok(one === fjord.points, `one Fjord scored ${one}, wanted ${fjord.points}`);
  ok(two === one, `two Fjords scored ${two} against one Fjord's ${one} — it is meant to score once`);
}

/* ---- progress never disagrees with done, over real games ---- */
{
  for (let s = 0; s < 25; s++) {
    const g = E.playOut(4, 900 + s, { humans: [], objectives: 'both' });
    for (const p of g.P) for (const o of p.objectives) {
      const q = g.objectiveProgress(p.i, o);
      ok(q.done === g.objectiveDone(p.i, o), 'progress and done disagree');
      ok(q.done ? q.missing === null : q.missing !== null,
         'an unfinished objective did not say what it is missing');
      ok(q.n === q.cells.length, 'the count and the tiles named disagree');
    }
  }
}

if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
console.log('objectives: three tiles you occupy, the two ends distinct; objectives overlap freely '
  + 'and each scores once; progress reports how many tiles are in place and what is missing');
