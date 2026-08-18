/* GENERATED — do not edit.
 * Built by server/build.js from app/engine.js, app/session.js and
 * server/worker.src.js. Edit those and rebuild:  node server/build.js
 * Built 2026-08-18T06:54:48Z
 */

/* ---------------- app/engine.js ---------------- */
/* Blink v0.22 — rules engine, JavaScript port of sim/engine.py.
 *
 * Faithful to the Python engine at the v0.22 defaults. The structure, the
 * method names and the comments-that-are-rules are kept so the two can be
 * diffed by eye.
 *
 * The one structural change: every method that needs a decision is a
 * GENERATOR. A bot seat answers inline; a human seat yields a request object
 * and is resumed with the answer. That keeps one code path for both, so a
 * human cannot be offered a move the bot engine would call illegal.
 *
 * Coordinates are pointy-top odd-r offset (col, row).
 */

// --------------------------------------------------------------- rng
function makeRng(seed) {
  let a = (seed >>> 0) || 1;
  const rnd = () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  return {
    random: rnd,
    randrange: (n) => Math.floor(rnd() * n),
    choice: (arr) => arr[Math.floor(rnd() * arr.length)],
    shuffle(arr) {                       // Fisher-Yates
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(rnd() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
      }
      return arr;
    },
    sample(arr, k) {
      const c = arr.slice();
      this.shuffle(c);
      return c.slice(0, k);
    },
  };
}

// --------------------------------------------------------------- constants
const TER = ["plains", "forest", "ocean", "mountain"];
const SUIT_LETTER = { plains: "P", forest: "F", ocean: "O", mountain: "M" };
const HOLDS = { plains: 3, forest: 2, ocean: 1, mountain: 1 };

/* Variant: population limits that grow with your board (Blink-variants.html).
 * The limit that applies to a tile is its OWNER'S, so two players may legally
 * stack the same terrain differently.
 *
 * The booklet prints four bands — Founding / Growth / Expansion / Empire — from
 * a version of the game that had four. v0.22 has five tiers, so Civilization
 * repeats Empire's row: the variant's own line is that "Mountain and Ocean stay
 * low throughout — hostile ground never becomes comfortable", and a fifth,
 * higher row would be the one thing it says not to do. */
const BAND_HOLDS = [
  { plains: 2, forest: 1, ocean: 1, mountain: 1 },   // Tribe        (Founding)
  { plains: 2, forest: 2, ocean: 1, mountain: 1 },   // Settlement   (Growth)
  { plains: 3, forest: 2, ocean: 1, mountain: 1 },   // Kingdom      (Expansion)
  { plains: 3, forest: 3, ocean: 2, mountain: 2 },   // Empire       (Empire)
  { plains: 3, forest: 3, ocean: 2, mountain: 2 },   // Civilization (as Empire)
];
const ATTACK_COST = { plains: 0, ocean: 0, forest: 1, mountain: 2 };
const BAG_EACH = 15;

/* tier -> [name, units, meld limit, food per recycle, free moves,
 *          ascension coins taken once on arrival, rank cap when buying]
 *
 * UNITS follow the printed player board and rulebook §04 — 2/4/6/4/4. The sim
 * (engine.py) has 2/4/5/5/4; measured, the difference is not detectable, so the
 * component wins.
 *
 * RANK CAPS follow the sim — 11/13/15/17/20, one tier tighter than the board's
 * 13/15/17/20. That gap is NOT cosmetic: the printed caps cut blocked buys from
 * 5.1 to 1.8 per game and let research run 21% more freely. The board and §04
 * need their cap column reprinted, not the engine. */
const BANDS = [
  ["Tribe", 2, 2, 0, 1, 0, 11],
  ["Settlement", 4, 3, 1, 2, 1, 13],
  ["Kingdom", 6, 4, 2, 3, 2, 15],
  ["Empire", 4, 5, 3, 4, 3, 17],
  ["Civilization", 4, 6, 4, 5, 4, 20],
];

/* The variants, kept so any can still be measured. Defaults above are board
 * units + sim caps. setTiers() changes the module default and must be called
 * BEFORE constructing a Game; a single game is better served by the `layout`
 * option, which is per-game and leaves this table alone. */
const TIER_UNITS = {
  sim: [2, 4, 5, 5, 4],
  rulebook: [2, 4, 6, 4, 4],
  /* Asked for on the strength of a playtest: a cheap Tribe, a lean Settlement,
   * and three broad late tiers. Twenty units like the other two, so it is a
   * redistribution rather than more material — which is what makes it
   * comparable. */
  late: [2, 3, 5, 5, 5],
};
const TIER_CAPS = { sim: [11, 13, 15, 17, 20], rulebook: [13, 15, 17, 20, 20] };
function setTiers(which) {
  const u = TIER_UNITS[which.units || "sim"], c = TIER_CAPS[which.caps || "sim"];
  for (let j = 0; j < BANDS.length; j++) { BANDS[j][1] = u[j]; BANDS[j][6] = c[j]; }
}

/* ---- per-game tier layout ----
 *
 * A layout is just the units column: how many of your twenty (or however many)
 * units sit in each tier. `layout` may be
 *
 *   a name from TIER_UNITS  ("sim", "rulebook", "late")
 *   "2-3-5-5-5"             a custom column, dashes, commas or spaces
 *   [2, 3, 5, 5, 5]         the same as an array
 *
 * Returned as a fresh BANDS table rather than by mutating the module's. That
 * matters more than it looks: the server replays many sessions in one process,
 * and a global table would mean a game with a custom layout silently rewrote
 * the tiers of every other game being replayed alongside it.
 */
function parseLayout(spec) {
  if (!spec) return null;
  if (typeof spec === "string" && TIER_UNITS[spec]) return TIER_UNITS[spec].slice();
  const nums = Array.isArray(spec)
    ? spec.map(Number)
    : String(spec).split(/[^0-9]+/).filter((x) => x !== "").map(Number);
  if (nums.length !== BANDS.length) return null;
  if (nums.some((n) => !Number.isInteger(n) || n < 0 || n > 99)) return null;
  /* A layout with nothing in the first tier has no starting unit to place and
   * the game cannot begin, so it is refused rather than left to fail later. */
  if (!nums[0]) return null;
  return nums;
}

function bandsFor(spec) {
  const units = parseLayout(spec);
  const out = BANDS.map((b) => b.slice());
  if (units) for (let j = 0; j < out.length; j++) out[j][1] = units[j];
  return out;
}

/* Map objectives — the advanced module. Every card is the same shape: three
 * tiles YOU OCCUPY in a chain, the middle touching both ends. Worth 4 points,
 * once, or nothing. Ends need not touch each other. */
const OBJECTIVES = [
  ["Foothills",        "mountain", "forest",   "plains",   "Where the stone gives way to soil"],
  ["Watershed",        "mountain", "plains",   "ocean",    "Every drop from here reaches the sea"],
  ["Highland Rivers",  "mountain", "forest",   "ocean",    "Snowmelt finds its way down"],
  ["Fjord",            "mountain", "ocean",    "mountain", "Deep water between two shoulders of rock"],
  ["Mountain Pass",    "plains",   "mountain", "plains",   "The one way through"],
  ["Coastal Chain",    "plains",   "ocean",    "plains",   "Two shores and the water between"],
  ["Clearing",         "forest",   "plains",   "forest",   "Open sky in the middle of the wood"],
  ["Mountain Lookout", "ocean",    "mountain", "ocean",    "One peak, the sea on either hand"],
  ["Riverbank",        "plains",   "forest",   "ocean",    "Soft ground, and everything grows"],
  ["Timberline",       "forest",   "mountain", "forest",   "The last trees before the rock"],
  ["River Delta",      "ocean",    "plains",   "forest",   "Where the water spreads and slows"],
  ["Sheltered Water",  "forest",   "ocean",    "forest",   "Wooded on both sides, calm between"],
].map(([name, a, mid, b, flavour], id) =>
  ({ id, name, a, mid, b, flavour, points: 4 }));

const STARTS = {
  2: [[[1, 0], [2, 0]], [[0, 0], [3, 0]]],
  3: [[[1, 3], [2, 2], [2, 3]], [[0, 3], [2, 1], [3, 4]]],
  4: [[[1, 2], [2, 2], [2, 3], [3, 3]], [[0, 2], [2, 1], [2, 4], [4, 3]]],
};

// --------------------------------------------------------------- geometry
const DIRS = ["E", "NE", "SE", "W", "NW", "SW"];
const OPPOSITE = { E: "W", W: "E", NE: "SW", SW: "NE", NW: "SE", SE: "NW" };

const K = (c, r) => c + "," + r;                 // cell key
const unK = (k) => k.split(",").map(Number);

function step(cell, d) {
  const [c, r] = cell;
  const odd = r & 1;
  switch (d) {
    case "E": return [c + 1, r];
    case "W": return [c - 1, r];
    case "NE": return [c + odd, r - 1];
    case "NW": return [c - 1 + odd, r - 1];
    case "SE": return [c + odd, r + 1];
    case "SW": return [c - 1 + odd, r + 1];
  }
}

function nbrKeys(c, r) {
  return DIRS.map((d) => { const [x, y] = step([c, r], d); return K(x, y); });
}

// --------------------------------------------------------------- tile
class Tile {
  constructor(cell, terrain, m) {
    this.cell = cell;                 // [c, r]
    this.key = K(cell[0], cell[1]);
    this.terrain = terrain;
    this.m = m;
    this.units = [];                  // owner ids; single-owner while occupied
    this.gold = 0;                    // fortification coins, at most one per unit
    this.link = {}; for (const d of DIRS) this.link[d] = null;
  }
  get owner() { return this.units.length ? this.units[0] : null; }

  capacityFor(seat) {
    if (!this.m || !this.m.limits || seat === null) return HOLDS[this.terrain];
    return this.m.limits[this.m.bandOf(seat)][this.terrain];
  }
  get capacity() {
    if (!this.m || !this.m.limits) return HOLDS[this.terrain];
    return Math.max(...this.m.limits.map((b) => b[this.terrain]));
  }
  hasRoom(p) {
    return (this.owner === null || this.owner === p) &&
           this.units.length < this.capacityFor(p);
  }
  neighbours() { return DIRS.map((d) => this.link[d]).filter((t) => t !== null); }
  emptySlots() {
    const out = [];
    for (const d of DIRS) if (this.link[d] === null) out.push(step(this.cell, d));
    return out;
  }
}

// --------------------------------------------------------------- melds
/* THE RULE: the ranks of the cards must form an unbroken run — every rank
 * between the lowest and the highest must be present. Duplicates of any rank
 * are free and suits are irrelevant. One card is always legal. */
/* ---- the meld rule, and the two variants that widen it ----
 * Base v0.22 (§05): a meld is any cards whose ranks form an unbroken run.
 *   combination melds — two or more multi-card melds played as one meld. Every
 *     component must be legal on its own and hold at least two cards; a single
 *     card can never be part of a combination.
 *   friends of 10s — any two cards whose ranks sum to 10, 20 or 30.
 * Both are off unless a game turns them on. */
let MELD_RULES = { combo: false, friends: false };
function setMeldRules(r) {
  MELD_RULES = { combo: !!(r && r.combo), friends: !!(r && r.friends) };
}
function meldRules() { return MELD_RULES; }

function isRun(cards) {
  const ranks = new Set(cards.map((c) => c.r));
  return Math.max(...ranks) - Math.min(...ranks) + 1 === ranks.size;
}
function isFriends(cards) {
  if (cards.length !== 2) return false;
  const s = cards[0].r + cards[1].r;
  return s === 10 || s === 20 || s === 30;
}
/* One piece of a combination: a legal meld in its own right, never a single. */
function isComponent(cards) {
  if (cards.length < 2) return false;
  return isRun(cards) || (MELD_RULES.friends && isFriends(cards));
}
/* Can these cards be cut into two or more legal pieces? Melds are capped at
 * six cards, so the search is tiny — the lowest unused card must belong to
 * some piece, and every piece containing it is tried. */
function canCombine(cards) {
  const n = cards.length;
  if (n < 4) return false;                       // two pieces of two, at least
  const used = new Array(n).fill(false);
  const rec = (parts) => {
    const first = used.indexOf(false);
    if (first === -1) return parts >= 2;
    const rest = [];
    for (let i = first + 1; i < n; i++) if (!used[i]) rest.push(i);
    for (let mask = 1; mask < (1 << rest.length); mask++) {
      const idx = [first];
      for (let b = 0; b < rest.length; b++) if (mask & (1 << b)) idx.push(rest[b]);
      if (!isComponent(idx.map((i) => cards[i]))) continue;
      for (const i of idx) used[i] = true;
      const ok = rec(parts + 1);
      for (const i of idx) used[i] = false;
      if (ok) return true;
    }
    return false;
  };
  return rec(0);
}

function isLegalMeld(cards) {
  if (!cards || !cards.length) return false;
  if (isRun(cards)) return true;
  if (MELD_RULES.friends && isFriends(cards)) return true;
  if (MELD_RULES.combo && canCombine(cards)) return true;
  return false;
}

/* Why a selection is not a meld, in the terms the current rules allow. */
function meldFault(cards) {
  if (!cards || !cards.length) return "no cards";
  if (isLegalMeld(cards)) return null;
  const rs = [...new Set(cards.map((c) => c.r))].sort((a, b) => a - b);
  const gaps = [];
  for (let r = rs[0]; r <= rs[rs.length - 1]; r++) if (!rs.includes(r)) gaps.push(r);
  const run = gaps.length ? `not an unbroken run — missing ${gaps.join(", ")}`
                          : "not an unbroken run";
  if (!MELD_RULES.combo && !MELD_RULES.friends) return run;
  const extra = [];
  if (MELD_RULES.combo) extra.push("nor two or more melds of 2+ cards each");
  if (MELD_RULES.friends) extra.push("nor a pair summing to 10, 20 or 30");
  return `${run}, ${extra.join(", ")}`;
}

function cardSort(a, b) { return a.r - b.r || a.s.localeCompare(b.s); }

function enumerateMelds(hand, limit) {
  const out = [];
  const src = hand.slice().sort(cardSort);
  const n = Math.min(limit, src.length);
  const combo = [];
  for (let k = 1; k <= n; k++) {
    (function rec(start) {
      if (combo.length === k) {
        if (isLegalMeld(combo)) out.push(combo.slice());
        return;
      }
      for (let i = start; i < src.length; i++) {
        combo.push(src[i]); rec(i + 1); combo.pop();
      }
    })(0);
  }
  return out;
}

/* How much trick-winning material a hand holds. Measured, the property that
 * predicts results is ADJACENCY, not rank height. */
function handPower(cards) {
  const cnt = {};
  for (const c of cards) cnt[c.r] = (cnt[c.r] || 0) + 1;
  let v = 0;
  for (const rs of Object.keys(cnt)) {
    const r = Number(rs), k = cnt[r];
    v += 1.4 * (k - 1);
    if (cnt[r + 1]) v += 1.0 * Math.min(k, cnt[r + 1]);
  }
  v += 0.03 * cards.reduce((a, c) => a + c.r, 0);
  v += 0.25 * new Set(cards.map((c) => c.s)).size;
  return v;
}

function draftPick(kept, offered, need) {
  const picks = [];
  const pool = offered.slice();
  for (let i = 0; i < Math.min(need, offered.length); i++) {
    let best = null, bv = -1e9;
    for (const c of pool) {
      const v = handPower(kept.concat(picks, [c]));
      if (v > bv) { best = c; bv = v; }
    }
    picks.push(best);
    pool.splice(pool.indexOf(best), 1);
  }
  return picks;
}

// --------------------------------------------------------------- map
class GameMap {
  constructor(n) {
    const [mts, pls] = STARTS[n];
    this.limits = null;
    this.bandOf = () => 0;
    this.tiles = new Map();
    for (const c of mts) this._add(c, "mountain");
    for (const c of pls) this._add(c, "plains");
    this.starts = pls.map((c) => c.slice());
    pls.forEach((c, i) => this.tiles.get(K(c[0], c[1])).units.push(i));
    // An open supply: every unused tile is visible and may be taken freely
    // until that terrain runs out. No bag, no face-up tile market.
    this.supply = {}; for (const t of TER) this.supply[t] = BAG_EACH;
    for (const t of this.tiles.values()) this.supply[t.terrain] -= 1;
  }

  _add(cell, terrain) {
    const t = new Tile(cell, terrain, this);
    this.tiles.set(t.key, t);
    for (const d of DIRS) {
      const [x, y] = step(cell, d);
      const other = this.tiles.get(K(x, y));
      if (other) { t.link[d] = other; other.link[OPPOSITE[d]] = t; }
    }
    return t;
  }

  legalSpaces() {                       // empty slots touching >= 2 tiles (§06)
    const cand = new Set();
    for (const t of this.tiles.values())
      for (const s of t.emptySlots()) cand.add(K(s[0], s[1]));
    const out = new Set();
    for (const k of cand) {
      const [c, r] = unK(k);
      let n = 0;
      for (const nk of nbrKeys(c, r)) if (this.tiles.has(nk)) n++;
      if (n >= 2) out.add(k);
    }
    return out;
  }

  tileAvailable(suit) { return this.supply[suit] > 0; }
  civ(p) {
    const out = new Set();
    for (const [k, t] of this.tiles) if (t.owner === p) out.add(k);
    return out;
  }

  cellActions(k, suit, p, spaces, budget) {
    const t = this.tiles.get(k);
    if (t) {
      if (t.terrain !== suit) return [];
      if (t.owner === null || t.owner === p) return t.hasRoom(p) ? ["settle"] : [];
      return budget >= ATTACK_COST[t.terrain] ? ["attack"] : [];
    }
    if (spaces.has(k) && this.tileAvailable(suit)) return ["explore"];
    return [];
  }

  doExplore(k, suit) {
    if (this.supply[suit] <= 0) return false;   // a tile can never come from nothing
    this.supply[suit] -= 1;
    this._add(unK(k), suit);
    return true;
  }
  settle(k, p) {
    const t = this.tiles.get(k);
    if (t.gold) t.gold = 0;                     // "stacked onto" disturbs the unit
    t.units.push(p);
  }
  takeUnitOff(k) {                              // starvation, not combat
    const t = this.tiles.get(k);
    const u = t.units.length ? t.units.pop() : null;
    t.gold = Math.min(t.gold, t.units.length);
    return u;
  }
  fortify(k) {
    const t = this.tiles.get(k);
    if (t.units.length && t.gold < t.units.length) { t.gold += 1; return true; }
    return false;
  }
  removeUnit(k) {                               // gold absorbs the hit first
    const t = this.tiles.get(k);
    if (t.gold) { t.gold -= 1; return null; }
    return t.units.length ? t.units.pop() : null;
  }
}

// --------------------------------------------------------------- placement
function adjacentKeys(m, k) {
  const t = m.tiles.get(k);
  if (t) return t.neighbours().map((u) => u.key)
                .concat(t.emptySlots().map((s) => K(s[0], s[1])));
  const [c, r] = unK(k);
  return nbrKeys(c, r);
}

/* Every cell a card of yours may act on: a tile you occupy, or any tile /
 * legal empty space adjacent to one you occupy. */
function reach(m, pi, civ) {
  civ = civ || m.civ(pi);
  const spaces = m.legalSpaces();
  const out = new Set(civ);
  for (const c of civ)
    for (const u of adjacentKeys(m, c))
      if (m.tiles.has(u) || spaces.has(u)) out.add(u);
  return out;
}

/* The same thing, `n` steps out. Only effect B's 6-10 band uses n = 2 — "found
 * a DISTANT colony: as above, up to 2 tiles out". Everything else in the game
 * reaches exactly one. */
function reachOut(m, pi, n) {
  const spaces = m.legalSpaces();
  const out = new Set(m.civ(pi));
  let frontier = new Set(out);
  for (let step = 0; step < n; step++) {
    const next = new Set();
    for (const c of frontier)
      for (const u of adjacentKeys(m, c))
        if ((m.tiles.has(u) || spaces.has(u)) && !out.has(u)) { out.add(u); next.add(u); }
    frontier = next;
  }
  return out;
}

/* Every legal (cell, action) for ONE card, judged against the map NOW. */
function cardOptions(m, card, p, gold, reachable, spaces) {
  spaces = spaces || m.legalSpaces();
  reachable = reachable || reach(m, p);
  const out = [];
  for (const k of Array.from(reachable).sort())
    for (const a of m.cellActions(k, card.s, p, spaces, gold)) out.push([k, a]);
  return out;
}

// --------------------------------------------------------------- player
class Player {
  /* `bands` is the tier table this player's board is printed with. It defaults
   * to the module table so every existing caller and test keeps working, and a
   * game with a custom layout hands its own in — which is what keeps one game's
   * layout out of another's. */
  constructor(i, bands) {
    this.i = i;
    this.bands = bands || BANDS;
    this.hand = [];
    this.discard = [];
    this.gold = 0;
    this.reserve = this.bands.map((b) => b[1]);
    this.vrow = [];
    this.played = [];
    this.bonus = 0;        // effect A under "count" scoring: extra cards
    this.sumBonus = 0;     // effect A under "sum" scoring: points on the total
    this.ties = false;
    this.spentA = 0;
    this.aBand = null;
    this.reached = 0;
  }
  band() {
    for (let j = 0; j < this.reserve.length; j++) if (this.reserve[j] > 0) return j;
    return this.bands.length - 1;
  }
  meldLimit() { return this.bands[this.band()][2]; }
  rankCap() { return this.bands[this.band()][6]; }
  ascensionDue() {
    let owed = 0;
    const j = this.band();
    while (this.reached < j) { this.reached += 1; owed += this.bands[this.reached][5]; }
    return owed;
  }
  food() { return this.bands[this.band()][3]; }
  freeMoves() { return this.bands[this.band()][4]; }
  takeUnit() {
    const j = this.band();
    if (this.reserve[j] > 0) { this.reserve[j] -= 1; return true; }
    return false;
  }
  /* A returned unit goes back to the LOWEST band with a free slot — regression
   * is one step, not a reset to Founding. */
  returnUnit() {
    for (let j = this.bands.length - 1; j >= 0; j--) {
      if (this.reserve[j] < this.bands[j][1]) { this.reserve[j] += 1; return true; }
    }
    return false;
  }
  reserveEmpty() { return this.reserve.reduce((a, b) => a + b, 0) === 0; }
}

// --------------------------------------------------------------- scoring
function bandOfRank(r) { return r <= 5 ? 0 : r <= 10 ? 1 : r <= 15 ? 2 : 3; }
function effectA(r) { const b = bandOfRank(r); return [b < 2 ? 1 : 2, b === 1 || b === 3]; }

/* ---- effect A when the trick is won on total rank ----
 *
 * "+1 card" is a strong effect when the trick goes to the most cards — a
 * winning meld is about three and a half cards, so one more is a quarter again
 * as much meld. Under sum scoring it buys almost nothing: it moves a tie-break
 * that only runs when two totals are exactly equal. So A needs its own reading
 * under that rule, adding to the TOTAL rather than to the count.
 *
 * The ladder is by band, like every other effect on the card, and is a named
 * table rather than a literal because the right size is a question for the
 * table and not for me. `effect_a_sum_*` in the stats measures what it does.
 *
 *   "steps"  1/2/3/4   the plainest reading of "+1, +2, +3"
 *   "double" 2/4/6/8   what steps measured as, if steps proves too quiet
 *   "band"   3/6/9/12  roughly a card of that band, so spending A is close to
 *                      playing one more card of the rank you gave up
 *
 * Ties are unchanged: the middle two bands still win a tie, which under sum
 * scoring is rarer but not empty — equal totals happen.
 */
const A_SUM_LADDERS = {
  steps: [1, 2, 3, 4],
  double: [2, 4, 6, 8],
  band: [3, 6, 9, 12],
  steep: [4, 8, 12, 16],
  /* Not a band table: the card adds its OWN rank, which is the most literal
   * reading of "depending on rank" and the only rung that needs no table at
   * all — "add this card to your total" is a sentence a player never has to
   * look up. Written as null and handled below. */
  rank: null,
};
let A_SUM_LADDER = "band";
function setASumLadder(which) {
  if (which in A_SUM_LADDERS) A_SUM_LADDER = which;
}
function effectASum(r, ladder) {
  const b = bandOfRank(r);
  const which = (ladder && ladder in A_SUM_LADDERS) ? ladder : A_SUM_LADDER;
  const table = A_SUM_LADDERS[which];
  return [table ? table[b] : r, b === 1 || b === 3];
}
function effectBv22(r) {
  return [[1, 1, true, 1], [1, 1, true, 2], [2, 1, true, 1], [2, 2, false, 1]][bandOfRank(r)];
}
function effectC(r) { return r <= 5 ? 2 : r <= 10 ? 3 : r <= 15 ? 4 : 5; }

/* What the card itself prints. Lifted verbatim from source/Blink-card-effects.html
 * so the app and the production reference cannot drift apart. All four suits of
 * a rank share the same effects; the suit only matters for B's terrain. */
const EFFECT_TEXT = [
  { a: "Meld counts as +1 card for winning this trick",
    b: "Found a colony: 1 new tile of this suit, 1 unit on it, fortified",
    c: "2 gold", aShort: "+1 card", bShort: "colony, this suit", cShort: "2g" },
  { a: "+1 card, and wins ties",
    b: "Distant colony: as above, and the tile may sit up to 2 out",
    c: "3 gold", aShort: "+1 card · ties", bShort: "colony, up to 2 out", cShort: "3g" },
  { a: "Meld counts as +2 cards",
    b: "Open a frontier: 2 new tiles of this suit, 1 unit on one, fortified",
    c: "4 gold", aShort: "+2 cards", bShort: "2 tiles, 1 unit", cShort: "4g" },
  { a: "+2 cards, and wins ties",
    b: "Two colonies: 2 new tiles of ANY terrain, 1 unit on each, both fortified",
    c: "5 gold", aShort: "+2 cards · ties", bShort: "2 colonies, any terrain", cShort: "5g" },
];
/* What A prints when the trick is won on total rank. The rest of the card is
 * unchanged — B and C do not care how the trick is decided — so only the two A
 * fields are overlaid, and they are generated from the ladder in play rather
 * than written out, or the card would lie the moment a rung is retuned. */
function effectText(rank, opts) {
  const base = EFFECT_TEXT[bandOfRank(rank)];
  if (!opts || opts.meldScore !== "sum") return base;
  const [add, ties] = effectASum(rank, opts.aSumLadder);
  return Object.assign({}, base, {
    a: ties ? `+${add} to your meld's total, and wins ties`
            : `+${add} to your meld's total for winning this trick`,
    aShort: ties ? `+${add} total · ties` : `+${add} total`,
  });
}

/* Effect D — conquest. From the deck-with-D proposal: D REPLACES C rather than
 * joining it ("three effects is the printable number"), because gold is the one
 * resource a player can always print, while attacking had no reason to exist —
 * it removed a rival point and put nothing of yours on the ground. D settles
 * what it empties, so a strike is a two-point swing plus a tile plus a step up
 * the tier ladder. Returns [units removed, may settle what it empties]. */
function effectD(rank) {
  return [[1, false], [1, true], [2, true], [2, true]][bandOfRank(rank)];
}
const EFFECT_D_TEXT = [
  { d: "Raid: remove 1 rival unit from a tile touching your civilization",
    dShort: "raid 1" },
  { d: "Seize: remove 1 rival unit — and settle the tile if you empty it",
    dShort: "seize 1, settle" },
  { d: "Conquer: remove 2 rival units, settling each tile you empty",
    dShort: "conquer 2, settle" },
  { d: "Overrun: remove 2 rival units from ANY tiles you can reach, settling each",
    dShort: "overrun 2, settle" },
];
function effectDText(rank) { return EFFECT_D_TEXT[bandOfRank(rank)]; }

/* Victory-row points (§13). Two readings are in circulation and they disagree:
 *   "card+centre" — the SIM: 1 per card, plus the centre-slot rank at 3+.
 *   "centre"      — the RULEBOOK's worked table: the centre-slot rank ALONE at
 *                   3+, and 1 per card only with fewer than three.
 * The centre slot is always your third-highest, because the row is pushed to
 * the right of five slots. */
let VROW_RULE = "card+centre";
function setVrowRule(r) { VROW_RULE = r; }
function vrowScore(ranks) {
  const r = ranks.slice().sort((a, b) => a - b);
  if (r.length < 3) return r.length;
  return VROW_RULE === "centre" ? r[r.length - 3]
                                : r.length + r[r.length - 3];
}

/* ---- how a bot values the world ----
 * Every number a bot weighs lives here, so a "style" is a small override of
 * this object rather than a different code path. TUNED is the policy every
 * measurement in RULEBOOK-CORRECTIONS.md was taken with; leave it alone.
 */
const TUNED = {
  // spending a card
  CASH_THRESHOLD: 1.0,     // below this a card is cashed for a coin instead
  SETTLE_V: 3.0,           // worth of putting a unit down
  MAJORITY_V: 1.2,         // ...on a terrain where you are not already ahead
  ROUGH_V: 0.6,            // ...on ground that costs gold to take from you
  EXPLORE_V: 1.0,          // worth of laying new ground
  EXPLORE_SUIT_V: 0.3,     // ...that your hand can use again
  ATTACK_V: 1.4,           // worth of a strike, before its price
  ATTACK_COST_W: 0.9,      // how much its price puts you off
  ATTACK_LONE_V: 1.0,      // ...a tile you would empty outright
  // choosing a meld
  MELD_GREED: 0.30,        // how much you value the hand you keep back
  // the victory row
  ROW_HORIZON: 2, ROW_PAD_RANK: 12, C_GOLD_PER_POINT: 2,
  RETIRE_GAIN_W: 3.0, RETIRE_RANK_W: 1.2,
  BLIND_RESEARCH_ODDS: 0.35,   // fish for an upgrade at worse odds than this? no
  D_DENIAL_W: 0.5,         // what a rival's lost point is worth to you
  // policies that are not weights
  COLONY_MIN_ROW: 4,       // hold effect B until the row is this deep
  FORTIFY_MIN_GOLD: 2,     // keep this much in hand before spending on walls
  /* Research only with a hand this short or shorter — the "hold back until your
   * lowest card is a high one" line. 10 means "whenever I can afford it".
   *
   * MEASURED, and the answer is not what the line promises: waiting moves the
   * mean rank retired by about one (9.6 -> 10.7 at the extreme) and costs half
   * your upgrades (12.8 -> 4.9 a game), which the row feels immediately because
   * every card in it is a point. Win rate against the tuned bot falls 47% ->
   * 8%. Kept as a lever because it is a real decision a person can make; NOT
   * used by any style, because a style must not be a handicap. */
  RESEARCH_MAX_HAND: 10,
  // buying from the market: match what you hold, sit next to it, or chase rank
  BUY_MATCH_W: 3.0, BUY_NEAR_W: 1.5, BUY_RANK_W: 0.08,
  BUY_RANDOM: 0,           // 1 = the pre-14-Aug behaviour: buy anything affordable
};

/* Deliberately NOT a style knob — see bots_test.js and RULEBOOK-CORRECTIONS
 * item 15. Measured head to head against the baseline, changing this one
 * number from 4 to 3 is worth 71% of games on its own, while every other
 * weight in every style is within noise of par. Letting a style carry it would
 * mean picking that style is picking to win, and would hide a real question
 * about effect B's price behind a flavour label. */
const STYLE_LOCKED = ["COLONY_MIN_ROW"];

/* Four ways to play the same game. Each is a delta from TUNED, and each is a
 * real policy rather than a handicap — difficulty is a separate axis (noise).
 * The numbers are deliberately modest: a style should change what a bot
 * REACHES FOR, not how well it plays. */
const BOT_STYLES = {
  tuned: { label: "Balanced", note: "the tuned baseline every measurement uses", w: {} },
  settler: {
    label: "Settler",
    note: "takes ground and holds it; fights only when the price is low",
    w: { SETTLE_V: 3.8, MAJORITY_V: 1.8, ATTACK_V: 0.7, ATTACK_COST_W: 1.4,
         EXPLORE_V: 1.3, FORTIFY_MIN_GOLD: 1 },
  },
  raider: {
    label: "Raider",
    note: "prices ground in blood; cashes cards to pay for it",
    w: { ATTACK_V: 2.6, ATTACK_COST_W: 0.35, ATTACK_LONE_V: 1.6, D_DENIAL_W: 0.9,
         CASH_THRESHOLD: 1.35, SETTLE_V: 2.6, EXPLORE_V: 0.7 },
  },
  scholar: {
    label: "Scholar",
    note: "buys ideas early and often, and feeds the victory row",
    w: { BLIND_RESEARCH_ODDS: 0.15, RETIRE_GAIN_W: 4.2, RETIRE_RANK_W: 1.6,
         ROW_HORIZON: 3, C_GOLD_PER_POINT: 3,
         BUY_RANK_W: 0.5, BUY_MATCH_W: 2.0,      // chases the tallest idea it may take
         CASH_THRESHOLD: 1.2, SETTLE_V: 2.7 },
  },
  merchant: {
    label: "Merchant",
    note: "keeps the purse full, walls what it owns, waits out trouble",
    w: { CASH_THRESHOLD: 1.35, FORTIFY_MIN_GOLD: 1, C_GOLD_PER_POINT: 1,
         ATTACK_V: 1.0, MELD_GREED: 0.18, ROUGH_V: 1.0, MAJORITY_V: 1.5 },
  },
};
const STYLE_KEYS = Object.keys(BOT_STYLES);

/* Difficulty is NOT a worse weight vector — that produces bots that are bad in
 * strange ways. It is the chance of taking a legal option at random instead of
 * the best one, which degrades a policy evenly and never plays illegally.
 * `hard` is 0, so a hard table reproduces every number ever measured here. */
const BOT_LEVELS = { easy: 0.35, normal: 0.15, hard: 0 };

function botWeights(style) {
  const s = BOT_STYLES[style] || BOT_STYLES.tuned;
  const w = Object.assign({}, TUNED, s.w);
  for (const k of STYLE_LOCKED) w[k] = TUNED[k];
  return w;
}

/* Score ONE card spent on one cell. A card scoring below CASH_THRESHOLD is
 * cashed for a coin instead — that comparison is the central decision. */
function valueCard(game, p, k, card, act) {
  const m = game.m;
  const w = p.w || TUNED;
  if (act === "settle") {
    let v = w.SETTLE_V;
    const t = m.tiles.get(k);
    let mine = 0;
    for (const x of m.tiles.values()) if (x.terrain === t.terrain && x.owner === p.i) mine++;
    let best = 0;
    for (const q of game.P) {
      if (q.i === p.i) continue;
      let n = 0;
      for (const x of m.tiles.values()) if (x.terrain === t.terrain && x.owner === q.i) n++;
      best = Math.max(best, n);
    }
    if (mine <= best) v += w.MAJORITY_V;               // contesting a majority
    if (t.terrain === "forest" || t.terrain === "mountain") v += w.ROUGH_V;
    return v;
  }
  if (act === "explore") {
    let v = w.EXPLORE_V;
    if (p.hand.some((c) => c.s === card.s)) v += w.EXPLORE_SUIT_V;
    return v;
  }
  if (act === "attack") {
    const t = m.tiles.get(k);
    let v = w.ATTACK_V - w.ATTACK_COST_W * ATTACK_COST[t.terrain];
    if (t.units.length === 1) v += w.ATTACK_LONE_V;
    return v;
  }
  return 0.2;
}

const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);

/* A stronger meld chooser — see pro_bot in engine.py. */
function proBot(game, p, what, options) {
  const m = game.m;
  const w = p.w || TUNED;
  const spaces = m.legalSpaces();
  const civ = m.civ(p.i);
  const reachable = civ.size ? reach(m, p.i, civ)
                             : new Set([...m.tiles.keys(), ...spaces]);
  const cache = new Map();
  const cardValue = (card) => {
    const id = card.r + card.s;
    if (!cache.has(id)) {
      const opts = cardOptions(m, card, p.i, p.gold, reachable, spaces);
      cache.set(id, Math.max(w.CASH_THRESHOLD,
        ...opts.map(([k, a]) => valueCard(game, p, k, card, a))));
    }
    return cache.get(id);
  };
  const rivals = game.P.filter((q) => q.i !== p.i).map((q) => q.meldLimit());
  const topRival = rivals.length ? Math.max(...rivals) : 0;

  /* A less certain bot sometimes plays a legal meld that is not its best —
   * that is the whole of "difficulty", and it is applied here because the meld
   * is the decision the rest of the turn hangs off. */
  if (p.noise && game.rng.random() < p.noise) return game.rng.choice(options);

  /* Under sum scoring the trick is won by total rank, not by card count, so the
   * bot has to estimate its chances the same way the rule decides them — or it
   * spends the game optimising a quantity that no longer wins anything, and
   * every measurement taken from bot play describes the wrong game.
   *
   * A rival's hand is hidden, so their likely total is a guess: their meld limit
   * times a typical rank. "Typical" is taken from this bot's own hand, which is
   * the only sample of the deck's current level it has. Crude, but it moves the
   * choice in the right direction, which is all the count version does either. */
  const bySum = game.MELD_SCORE === "sum";
  const typicalRank = p.hand.length ? mean(p.hand.map((c) => c.r)) : 10.5;
  const rivalSum = topRival * typicalRank;

  let best = null, bestV = -1e9;
  for (const cards of options) {
    const n = cards.length;
    let v = cards.reduce((a, c) => a + cardValue(c), 0);
    let win;
    if (bySum) {
      const sum = cards.reduce((a, c) => a + c.r, 0);
      /* A smooth curve rather than the three steps the count rule uses: sums
       * are far more granular than card counts, and a cliff at exactly equal
       * totals would make the bot indifferent across most of the range. */
      win = rivalSum > 0
        ? Math.max(0.02, Math.min(0.95, 0.5 + 0.5 * ((sum - rivalSum) / rivalSum)))
        : 0.9;
    } else {
      win = n > topRival ? 0.9 : n === topRival ? 0.45
          : Math.pow(0.12, topRival - n + 1);
    }
    v += win * (1.1 + 0.35 * mean(cards.map(cardValue)));
    const rest = p.hand.filter((c) => !cards.includes(c));
    v += w.MELD_GREED * handPower(rest);
    if (p.gold < p.food()) v += 0.25 * n;
    if (v > bestV) { best = cards; bestV = v; }
  }
  return best;
}

// --------------------------------------------------------------- game
class Game {
  constructor(n, seed, opts) {
    opts = opts || {};
    this.rng = makeRng(seed === undefined ? 1 : seed);
    this.n = n;
    this.m = new GameMap(n);
    /* The player board this table is using. `layout` is a name, a "2-3-5-5-5"
     * string or an array; anything unreadable falls back to the printed board
     * rather than to a half-applied one. Held on the game and handed to each
     * player, so two games in one process cannot tread on each other. */
    this.BANDS = bandsFor(opts.layout);
    this.LAYOUT = opts.layout || null;
    this.P = []; for (let i = 0; i < n; i++) this.P.push(new Player(i, this.BANDS));
    this.humans = new Set(opts.humans || []);        // seats a person plays
    /* "dock"  — classic: winner uses every card; a player who matched the
     *           winner's count sets one played card aside for 1 gold.
     * "bonus" — v0.22 as printed: winner spends one EXTRA card from hand, and
     *           a matcher gives a card from hand face down to the shared pile.
     * The sim was measured on "bonus"; see verify.js. */
    this.TRICK_RULE = opts.trickRule || "dock";
    /* How a meld is scored for winning the trick.
     * "count" — v0.22 as printed: most cards wins, and the ranks only break a
     *           tie. A run of low cards beats one high card.
     * "sum"   — the proposal: the meld is worth the SUM of the ranks in it, and
     *           the highest sum wins whatever the card counts are. One 20 beats
     *           three 6s. Card count then breaks a tie, so a cheaper meld of
     *           equal value still loses to a bigger one.
     * This changes what a hand is FOR, so it is a whole-game option rather than
     * a variant toggle: under "sum" holding one high card is a plan. */
    this.MELD_SCORE = opts.meldScore === "sum" ? "sum" : "count";
    /* Which rung effect A adds to a total under sum scoring. Only consulted
     * when MELD_SCORE is "sum"; under "count" A still prints and does "+1/+2
     * cards" exactly as before. */
    /* `in`, not truthiness: the "rank" rung is stored as null because it is not
     * a table, and a truthiness test silently dropped it back to the default —
     * which showed up as two ladders measuring identically to three decimals. */
    this.A_SUM_LADDER = (opts.aSumLadder in A_SUM_LADDERS)
      ? opts.aSumLadder : A_SUM_LADDER;
    /* "abc" — the base rules as printed. "abd" — the proposal: conquest takes
     * the third slot and the take-gold effect leaves the deck entirely, which
     * also removes the row as a famine valve. */
    this.DECK = opts.deck || "abc";
    /* Rulebook §03/§10 print a 2x3 market of six; the sim uses a 3x3 of nine. */
    this.GRID_SIZE = opts.gridSize || 9;
    /* "area"  — the sim: your biggest CONNECTED STRETCH of a terrain, in tiles.
     * "units" — rulebook §13: most UNITS on that terrain, and only if all your
     *           units on it form one connected group. */
    this.MAJORITY = opts.majority || "area";
    /* off | secret (deal two, keep one) | open (two face up, shared) | both */
    this.OBJECTIVES_MODE = opts.objectives || "off";
    /* "lowest" — research retires the LOWEST rank you hold (any suit of it).
     *            Research is then an upgrade in the plain sense: your worst
     *            card leaves and a better one arrives.
     * "any"    — rulebook §10 as printed: "retire one card from your hand or
     *            discard", no restriction. Kept so the two can be measured. */
    this.RETIRE_RULE = opts.retireRule || "lowest";
    /* How many times you may research in one turn, and what each costs.
     * "once"       — §10 as printed: one research a turn, 1 gold.
     * "escalating" — as many as you can pay for, at 1 gold, then 2, then 3...
     *                the count resetting each turn.
     *
     * The complaint this answers: research is the only way to fix a hand, once a
     * turn is slow, and each one takes a card OUT of a hand you are trying to
     * assemble into a run — so a bad hand can stay bad for several rounds while
     * you feed it one card at a time. The escalating price is what stops that
     * from becoming "cycle your whole hand every turn": the second costs twice
     * the first and the third three times, so the gold runs out fast. */
    this.RESEARCH_RULE = ["once", "twice", "escalating"].includes(opts.researchRule)
      ? opts.researchRule : "once";
    /* How many a turn may hold at most. "twice" exists because unlimited
     * measured as a 29% wider gap between leader and last: the player who can
     * afford the second and third research is the one already ahead, which is
     * the same failure mode the growing-population-limits variant has. */
    this.RESEARCH_MAX = this.RESEARCH_RULE === "once" ? 1
      : this.RESEARCH_RULE === "twice" ? 2 : Infinity;
    /* Who the bots are. `botStyle` is one of BOT_STYLES, or "mixed" to deal a
     * different one to each seat; `botLevel` is easy | normal | hard. Both are
     * policy, never rules: no style may do anything a person could not. */
    this.BOT_STYLE = opts.botStyle || "tuned";
    this.BOT_LEVEL = opts.botLevel || "hard";
    /* Per-seat styles, when the table was set one seat at a time. A null entry
     * falls back to BOT_STYLE (or the mixed bag). */
    this.SEAT_STYLES = opts.seatStyles || null;
    /* Meld variants (Blink-variants.html). Module-level, like the victory-row
     * rule, because the client asks the same free functions the engine does. */
    this.MELD_VARIANTS = { combo: !!opts.comboMelds, friends: !!opts.friendsOf10 };
    setMeldRules(this.MELD_VARIANTS);
    /* Variant: population limits per band. `Tile.capacityFor(seat)` already
     * asked the map for them and fell back to the fixed table, so switching it
     * on is one assignment. */
    this.GROW_LIMITS = !!opts.growLimits;
    if (this.GROW_LIMITS) this.m.limits = BAND_HOLDS;
    this.round = 0;
    this.stats = {};
    this.log = [];
    this.endedOn = null;
    this.finalRounds = null;
    this.pile = [];            // shared face-down discard pile (§04, §09)
    this.removed = [];         // cards spent on effects; out of the game
    this.m.bandOf = (seat) => this.P[seat].band();
    this._dealStyles();
    for (const pl of this.P) pl.takeUnit();          // the starting unit
    this._deal();
  }

  // ---- rules, at the v0.22 base-game defaults ----------------------
  get MARKET_GRID() { return this.GRID_SIZE; }
  get CONSOLATION_GOLD() { return 1; }
  /* Bot weights are per SEAT (`p.w`), not per game — see TUNED and BOT_STYLES.
   * These stay only so old callers and tests that ask the game for a weight
   * still get the tuned answer. */
  get CASH_THRESHOLD() { return TUNED.CASH_THRESHOLD; }
  get MELD_GREED() { return TUNED.MELD_GREED; }

  isHuman(i) { return this.humans.has(i); }

  /* A record of what physically moved, for the client to animate. Recording
   * only — nothing here changes a decision, so the bots play identically with
   * it on. The client drains the queue after every step; the cap is a guard in
   * case nobody is listening (headless runs, tests). */
  fx(type, data) {
    if (!this.events) this.events = [];
    if (this.events.length > 400) this.events.length = 0;
    this.events.push(Object.assign({ type }, data));
  }
  inc(k, n) { this.stats[k] = (this.stats[k] || 0) + (n === undefined ? 1 : n); }
  /* The log is read by a person, so the engine stores a KEY and its variables
   * rather than a sentence — the client renders it in whatever language is on.
   * Nothing in the engine may contain text a player sees. */
  say(key, vars) { this.log.push([this.round, key, vars || null]); }

  // --- setup ---------------------------------------------------
  _deal() {
    const n = this.n, R = this.rng;
    const range = (a, b) => { const o = []; for (let i = a; i < b; i++) o.push(i); return o; };
    const sr = n === 2 ? range(6, 11) : n === 3 ? range(3, 11) : range(1, 11);
    // FULL_ADV_DECK: the rank caps only mean anything if the market reaches
    // above them, so ranks 11-20 at every player count.
    const ar = range(11, 21);
    let start = [], adv = [];
    for (const r of sr) for (const s of TER) start.push({ r, s });
    for (const r of ar) for (const s of TER) adv.push({ r, s });
    if (n === 3) {                                   // three-player suit balance
      const threes = start.filter((c) => c.r === 3);
      const keep = R.sample(threes, 2);
      start = start.filter((c) => c.r !== 3).concat(keep);
      const kept = keep.map((c) => c.s);
      const missing = TER.filter((s) => !kept.includes(s));
      adv = adv.filter((c) => !(c.r === 18 && missing.includes(c.s)));
    }
    R.shuffle(start);
    const hands = [];
    for (let i = 0; i < n; i++) hands.push(start.slice(i * 10, (i + 1) * 10));
    // draft: cumulative keeps of 4, 6, 8, 10
    let kept = []; for (let i = 0; i < n; i++) kept.push([]);
    for (const target of [4, 6, 8, 10]) {
      for (let i = 0; i < n; i++) {
        const need = target - kept[i].length;
        const picks = draftPick(kept[i], hands[i], need);
        kept[i] = kept[i].concat(picks);
        hands[i] = hands[i].filter((c) => !picks.includes(c));
      }
      const rot = [];
      for (let i = 0; i < n; i++) rot.push(hands[(i - 1 + n) % n]);
      for (let i = 0; i < n; i++) hands[i] = rot[i];
    }
    for (let i = 0; i < n; i++) this.P[i].hand = kept[i];
    // ONE shuffled upgrade deck and a face-up 3x3 grid. Each grid position is a
    // STACK — a drawn card is placed on top of one, burying what was under it.
    this.deck = adv.slice();
    R.shuffle(this.deck);
    this.grid = [];
    for (let i = 0; i < this.MARKET_GRID; i++)
      this.grid.push(this.deck.length ? [this.deck.pop()] : []);
    this.leader = 0;
    this.playOrder = null;                    // set each round, leader first
    this._dealObjectives();
  }

  /* Give every seat its weights. A human seat gets the tuned set so that
   * anything the client asks the engine to value on their behalf is answered
   * neutrally, and no noise — a person's mistakes are their own. */
  _dealStyles() {
    const opts = STYLE_KEYS.filter((k) => k !== "tuned");
    let bag = [];
    this.P.forEach((p, i) => {
      let style = (this.SEAT_STYLES && this.SEAT_STYLES[i]) || this.BOT_STYLE;
      if (style === "mixed" || style === "auto") {
        if (!bag.length) { bag = opts.slice(); this.rng.shuffle(bag); }
        style = bag.pop();
      }
      p.style = this.isHuman(i) ? "you" : style;
      p.w = botWeights(this.isHuman(i) ? "tuned" : style);
      p.noise = this.isHuman(i) ? 0 : (BOT_LEVELS[this.BOT_LEVEL] || 0);
    });
  }

  /* Twelve cards is enough for four players to be dealt two each with four
   * still unseen, so no table ever sees the whole deck. */
  _dealObjectives() {
    this.objectives = [];                       // shared, when they are open
    for (const p of this.P) { p.objectives = []; p.objOffer = []; }
    if (this.OBJECTIVES_MODE === "off") return;
    const pool = OBJECTIVES.slice();
    this.rng.shuffle(pool);
    if (this.OBJECTIVES_MODE === "open") {
      this.objectives = [pool.pop(), pool.pop()];
      for (const p of this.P) p.objectives = this.objectives;
      return;
    }
    for (const p of this.P) {
      const two = [pool.pop(), pool.pop()].filter(Boolean);
      if (this.OBJECTIVES_MODE === "both") p.objectives = two;
      else { p.objOffer = two; p.objectives = []; }   // "secret": choose one
    }
  }

  /* Three tiles you occupy: a middle of one terrain touching an end of each of
   * the other two. The ends need not touch each other. */
  objectiveDone(seat, o) {
    for (const [k, t] of this.m.tiles) {
      if (t.terrain !== o.mid || t.owner !== seat || !t.units.length) continue;
      const ends = t.neighbours().filter(
        (u) => u.owner === seat && u.units.length);
      for (const x of ends) {
        if (x.terrain !== o.a) continue;
        for (const y of ends) {
          if (y === x) continue;
          if (y.terrain === o.b) return true;
        }
      }
    }
    return false;
  }

  gridTop(k) { return this.grid[k].length ? this.grid[k][this.grid[k].length - 1] : null; }

  // --- one round -----------------------------------------------
  *playRound() {
    setMeldRules(this.MELD_VARIANTS);      // safe if two games are interleaved
    if (this.OBJECTIVES_MODE === "secret" && !this._objChosen) {
      this._objChosen = true;
      for (const p of this.P) {
        if (!p.objOffer.length) continue;
        if (this.isHuman(p.i)) {
          const pick = yield { type: "objective", seat: p.i, options: p.objOffer };
          p.objectives = [pick || p.objOffer[0]];
        } else {
          p.objectives = [this.rng.choice(p.objOffer)];
        }
        p.objOffer = [];
      }
    }
    this.round += 1;
    const order = [];
    for (let k = 0; k < this.n; k++) order.push((this.leader + k) % this.n);
    /* Who lays cards in what order — the leader first, then clockwise. Public
     * information: at a table you can see whose turn it is to play. */
    this.playOrder = order.slice();

    // ---------------- card phase ----------------
    /* Clear the table first. A seat that has not played yet must show nothing,
     * not last round's meld — the play area is public information about THIS
     * trick, and a stale card would be a lie. */
    for (const q of this.P) { q.tableau = null; q.tableauBonus = null; q.asideCard = null; }
    this.trickOrder = null; this.winner = null; this.turnDone = new Set();
    for (const i of order) {
      const p = this.P[i];
      const melds = enumerateMelds(p.hand, p.meldLimit());
      let cards;
      if (this.isHuman(i)) {
        cards = yield { type: "meld", seat: i, options: melds };
      } else {
        cards = proBot(this, p, "meld", melds);
      }
      p.played = cards.slice();
      /* Kept for the shared play area: `played` is emptied when a seat takes
       * its map turn, but the table should still show what everyone put down
       * until the next card phase. */
      p.tableau = cards.slice();
      p.tableauBonus = null;
      /* One beat per player: bots resolve in the same tick, so without this the
       * whole trick would appear at once instead of going round the table. */
      this.fx("meld", { seat: i, n: cards.length });
      p.bonus = 0; p.sumBonus = 0; p.ties = false; p.spentA = 0; p.aBand = null;
      for (const c of cards) p.hand.splice(p.hand.indexOf(c), 1);
      this.inc("meld_" + cards.length);
      yield* this._maybeDeclareABlind(p);          // A is declared blind (§10)
    }

    /* v0.22 ranking: most cards, then highest card, then next-highest, and so
     * on; earliest played breaks what is left. There are never ties.
     *
     * Under MELD_SCORE "sum" the first comparison is the total of the ranks
     * instead of the number of cards, and the count drops to being the first
     * tie-break. Everything after that is unchanged, so the two rules share one
     * comparator and cannot drift apart.
     *
     * Effect A is read differently by each rule, because "+1 card" is worth a
     * quarter of a meld under one and almost nothing under the other. Under
     * "count" it adds cards (`bonus`); under "sum" it adds points to the total
     * (`sumBonus`, from effectASum). Both are computed here so the comparator
     * has them whichever rule is running. */
    const keyOf = (seat) => {
      const i = order[seat], p = this.P[i];
      const ranks = p.played.map((c) => c.r).sort((a, b) => b - a);
      return { size: p.played.length + p.bonus,
               bareSize: p.played.length,
               sum: ranks.reduce((a, b) => a + b, 0) + p.sumBonus,
               bare: ranks.reduce((a, b) => a + b, 0),
               ties: p.ties ? 1 : 0,
               a: -p.spentA, lex: ranks, seat };
    };
    const bySum = this.MELD_SCORE === "sum";
    const cmp = (x, y) => {
      if (bySum && x.sum !== y.sum) return y.sum - x.sum;
      if (x.size !== y.size) return y.size - x.size;
      if (x.ties !== y.ties) return y.ties - x.ties;
      if (x.a !== y.a) return x.a - y.a;
      for (let i = 0; i < Math.max(x.lex.length, y.lex.length); i++) {
        const a = x.lex[i] === undefined ? -1 : x.lex[i];
        const b = y.lex[i] === undefined ? -1 : y.lex[i];
        if (a !== b) return b - a;
      }
      return x.seat - y.seat;
    };
    const keys = order.map((_, s) => keyOf(s));
    const ranked = keys.slice().sort(cmp).map((x) => order[x.seat]);
    const winner = ranked[0];
    const loser = ranked[ranked.length - 1];
    this.winner = winner;
    // captured BEFORE the map phase: the winner acts first and clears `played`
    const winSize = this.P[winner].played.length;
    this.say("log.trick", { seat: winner });

    /* How often the two scorings would disagree, and whether the sum rule is
     * rewarding fewer cards or the same cards. Recorded under both rules so a
     * pair of runs can be compared directly. */
    {
      const byCount = keys.slice().sort((x, y) => {
        if (x.size !== y.size) return y.size - x.size;
        return x.seat - y.seat;
      })[0];
      const top = keys.find((k) => order[k.seat] === winner);
      this.inc("meld_sum_tricks");
      if (byCount && top && byCount.seat !== top.seat) this.inc("meld_sum_differs");
      if (top) {
        this.inc("meld_sum_total", top.bare);       // the cards alone, not A
        this.inc("meld_sum_cards", top.lex.length);
      }
      /* Did effect A actually decide this trick? Take the bonus away and ask
       * whether the same seat still wins. Counted the same way under BOTH
       * rules — cards under "count", points under "sum" — because the only
       * useful question about a new A is whether it matters as much as the old
       * one did, and that needs the two measured on the same footing.
       *
       * `a_won` counts tricks won by a seat that had spent A; `a_decided`, the
       * subset where taking the bonus away loses it. `a_wasted` is A spent by
       * somebody who lost anyway, which is the other half of "is it worth it". */
      const gainOf = (k) => (bySum ? k.sum - k.bare : k.size - k.bareSize);
      const scoreOf = (k) => (bySum ? k.sum : k.size);
      const bareOf = (k) => (bySum ? k.bare : k.bareSize);
      if (top) {
        for (const k of keys) if (gainOf(k) > 0 && k !== top) this.inc("a_wasted");
        if (gainOf(top) > 0) {
          this.inc("a_won");
          const second = keys.filter((k) => k !== top)
            .reduce((b, k) => (b === null || scoreOf(k) > scoreOf(b) ? k : b), null);
          if (second && bareOf(top) <= scoreOf(second)) this.inc("a_decided");
        }
      }
    }

    // ---------------- map phase ----------------
    this.trickOrder = ranked.slice();
    this.fx("trick", { seat: winner, order: ranked.slice(), last: loser });
    for (const i of ranked) {
      const p = this.P[i];
      this.acting = i;
      this.fx("turnstart", { seat: i });
      const cards = p.played.slice();
      const spent = cards.slice();
      const use = cards.slice();

      // the catch-up coin, without docking anyone a card
      if (i === loser && i !== winner) {
        p.gold += this.CONSOLATION_GOLD;
        this.inc("gold_in_lost_trick", this.CONSOLATION_GOLD);
      }

      if (this.TRICK_RULE === "bonus") {
        /* v0.22 as printed: the winner spends one extra card, and a player who
         * matched the winner's count and lost gives a card from hand, face
         * down, to the shared pile. Nobody is docked a played card. */
        if (i === winner) {
          const bonus = yield* this._pickBonus(p);
          if (bonus !== null) {
            p.hand.splice(p.hand.indexOf(bonus), 1);
            use.push(bonus); spent.push(bonus);
            p.tableauBonus = bonus;
            this.inc("bonus_card");
          } else {                       // hand empty: take the consolation coin
            p.gold += 1; this.inc("bonus_gold");
          }
        }
        if (i !== winner && cards.length === winSize && p.hand.length) {
          const drop = yield* this._pickDiscard(p);
          p.hand.splice(p.hand.indexOf(drop), 1);
          this.pile.push(drop);
          this.inc("match_discard");
        }
      } else {
        /* Classic: only the trick winner uses every card of their meld. A
         * player who matched the winner's count sets one of their played cards
         * aside unused — it earns 1 gold instead (§06). Playing FEWER than the
         * winner costs nothing, because you are already below the cap. */
        if (i !== winner && cards.length === winSize && cards.length) {
          /* Forced, not offered: matching the winner's count costs you a card,
           * and the only decision is which one. A null answer (a client that
           * shows no way to comply) still gives one up — the bot's choice. */
          const aside = (yield* this._pickSetAside(p, use)) || use[0];
          use.splice(use.indexOf(aside), 1);
          spent.splice(spent.indexOf(aside), 1);
          p.asideCard = aside;
          /* §09: the card leaves your economy for the SHARED pile — this is the
           * tap that feeds everyone's refill. Under the old routing it went to
           * the player's own discard and came straight back, so the shared pile
           * was never fed and nobody ever drew from it. */
          this.pile.push(aside);
          p.gold += 1;
          this.inc("docked_card"); this.inc("cards_to_gold");
          this.inc("gold_in_docked"); this.inc("to_shared_pile");
          this.fx("card", { seat: p.i, card: aside, from: "meld", to: "pile" });
          this.fx("gold", { seat: p.i, amount: 1, from: "pile" });
        } else {
          p.asideCard = null;
        }
      }
      this.inc("cards_played", cards.length);

      if (this.isHuman(i)) {
        /* A person takes the whole map phase as one open turn: cards, moves,
         * research, colonies and fortifying in any order, ended when they say.
         * The bot below keeps the fixed sequence, so the sim's numbers still
         * describe the same engine. */
        p.played = [];
        // the card set aside has already gone to the shared pile, not to yours
        yield* this._humanTurn(p, use);
      } else {
        yield* this._place(p, use);
        p.discard = p.discard.concat(spent);
        p.played = [];

        /* Your hand refills the MOMENT it empties, not at the end of the turn —
         * so playing your whole hand no longer silently costs the upgrade. */
        if (!p.hand.length) { yield* this._reclaimForFood(p); yield* this._recycle(p); }
        yield* this._maybeUpgrade(p);
        yield* this._maybeUseB(p);
        if (this.DECK === "abd") yield* this._maybeUseD(p);
        else yield* this._maybeCashC(p, false);
        yield* this._freeMoves(p);
        yield* this._maybeFortify(p);
        if (!p.hand.length) { yield* this._reclaimForFood(p); yield* this._recycle(p); }
      }
      this.turnDone.add(i);
      this.fx("turnend", { seat: i });
    }
    this.acting = null;

    this.leader = winner;
    this._checkEnd();
  }

  _payAscension(p) {
    const owed = p.ascensionDue();
    if (owed) {
      p.gold += owed; this.inc("gold_in_ascension", owed); this.inc("ascensions");
      this.fx("gold", { seat: p.i, amount: owed, from: "board" });
    }
  }

  // --- the human map turn ---------------------------------------
  /* Everything a person may still do this turn, recomputed after every action
   * because each one changes the map. This is the whole rules surface of the
   * map phase in one object; the client only has to draw it. */
  /* Rival-held tiles this player could strike: occupied by someone else,
   * touching a tile you occupy, and whose terrain you can afford. Conquest pays
   * the same attack price as a card does (§06) — 0 Plains, 0 Ocean, 1 Forest,
   * 2 Mountain — so dear ground still defends itself. */
  conquestTargets(p) {
    const out = [];
    for (const [k, t] of this.m.tiles) {
      if (t.owner === null || t.owner === p.i || !t.units.length) continue;
      if (p.gold < ATTACK_COST[t.terrain]) continue;
      if (t.neighbours().some((u) => u.owner === p.i && u.units.length)) out.push(k);
    }
    return out;
  }

  _anyRivalAdjacent(p) {
    for (const [, t] of this.m.tiles) {
      if (t.owner === null || t.owner === p.i || !t.units.length) continue;
      if (t.neighbours().some((u) => u.owner === p.i && u.units.length)) return true;
    }
    return false;
  }

  turnOptions(p, st) {
    const spaces = this.m.legalSpaces();
    const exempt = this.m.civ(p.i).size === 0;            // re-entry rule (§06)
    const reachable = exempt ? new Set([...this.m.tiles.keys(), ...spaces])
                             : reach(this.m, p.i);
    const cards = st.cards.map((card) => ({
      card, options: cardOptions(this.m, card, p.i, p.gold, reachable, spaces),
    }));
    const fortifyCells = [];
    for (const [k, t] of this.m.tiles)
      if (t.owner === p.i && t.gold < t.units.length) fortifyCells.push(k);
    const colonyBlocked =
      st.bUsed ? "why.colony.used"
      : p.reserveEmpty() ? "why.colony.noUnits"
      : !spaces.size ? "why.colony.noSpace" : null;
    /* A card is only offered if it could actually found something: the terrain
     * is still in the supply AND there is a space for it in reach. Offering a
     * card that then does nothing is how the effect came to look broken. */
    const colonyCards = colonyBlocked ? []
      : p.vrow.filter((c) => {
          const sameSuit = effectBv22(c.r)[2];
          const supplyOk = sameSuit ? this.m.supply[c.s] > 0
                                    : TER.some((t) => this.m.supply[t] > 0);
          return supplyOk && this.colonyCells(p, c).length > 0;
        });
    const colonyNoRoom = !colonyBlocked && !colonyCards.length && p.vrow.length
      ? "why.colony.noReach" : null;
    return {
      cards,
      moves: st.moves,
      moveSources: st.moves > 0 ? this.moveSources(p) : [],
      /* Landfall cells per ocean source, so the client can light them up as
       * move destinations beside the ordinary ones. Keyed by source because
       * which cells are eligible depends on which water the ship is in. */
      landfall: st.moves > 0 && !st.waterUsed
        ? this.moveSources(p).reduce((acc, k) => {
            const cells = this.landfallCells(p, k, st.waterUsed);
            if (cells.length) acc[k] = cells;
            return acc;
          }, {})
        : {},
      /* What the NEXT research costs this turn. Under the printed rule that is
       * always 1 and there is only ever one; under the escalating rule it is
       * one more each time, and the client shows the price on the button so
       * nobody commits to a cost they could not see. */
      researchCost: this.researchCost(st),
      researchesUsed: st.researches,
      canResearch: this.canResearch(p, st),
      researchBlocked: this.researchBlocked(p, st),
      colonyCards, colonyBlocked: colonyBlocked || colonyNoRoom,
      /* Is the water advantage still on the table this turn? The client marks
       * the sea moves that would collect it. */
      waterReady: !st.waterUsed,
      deck: this.DECK,
      cashCards: this.DECK === "abc" ? p.vrow.slice() : [],
      conquestTargets: this.DECK === "abd" ? this.conquestTargets(p) : [],
      conquestBlocked: this.DECK !== "abd" ? "why.conquest.deck"
        : this.conquestTargets(p).length ? null
        : this._anyRivalAdjacent(p)
          ? "why.conquest.gold"
          : "why.conquest.none",
      fortifyCells: p.gold >= 1 ? fortifyCells : [],
    };
  }

  *_humanTurn(p, use) {
    const st = { cards: use.slice(), moves: p.freeMoves(),
                 researches: 0, bUsed: false, waterUsed: false };
    /* Refill only once the meld is fully resolved. Recycling while cards are
     * still on the table would swap the discard into hand and then take those
     * cards back on top of it — over the ten-card ceiling. The bot cannot hit
     * this because it always spends the whole meld before recycling. */
    const refill = function* (self) {
      if (st.cards.length || p.hand.length) return;
      yield* self._reclaimForFood(p);
      yield* self._recycle(p);
    };
    for (;;) {
      const opts = this.turnOptions(p, st);
      const ans = yield { type: "turn", seat: p.i, state: st, opts };
      if (!ans || ans.kind === "end") break;

      switch (ans.kind) {
        case "spend": {
          st.cards.splice(st.cards.indexOf(ans.card), 1);
          p.discard.push(ans.card);            // spent before any recycle can fire
          this._resolve(p, ans.card, ans.cell, ans.act);
          break;
        }
        case "cash": {
          st.cards.splice(st.cards.indexOf(ans.card), 1);
          p.discard.push(ans.card);
          p.gold += 1;
          this.inc("cards_to_gold"); this.inc("gold_in_cashed");
          this.fx("gold", { seat: p.i, amount: 1, from: "hand" });
          this.say("log.cashed", { card: ans.card.r + SUIT_LETTER[ans.card.s] });
          break;
        }
        case "move": {
          if (st.moves <= 0) break;

          /* Landfall: the destination is a cell with no tile on it yet. A move
           * that starts on water may end on ground that does not exist —
           * the tile is laid now and the unit steps onto it, all inside this
           * one move action (§07).
           *
           * Checked against landfallCells rather than trusting the answer: the
           * client works out the same set, but a client is not the authority on
           * where a tile may be placed. */
          if (!this.m.tiles.has(ans.dest)) {
            const legal = this.landfallCells(p, ans.src, st.waterUsed);
            if (!legal.includes(ans.dest)) break;
            const terrains = TER.filter((t) => this.m.supply[t] > 0);
            if (!terrains.length) break;
            /* Spent as the offer is made, not before: a voyage with nowhere to
             * land must not lose the advantage for the rest of the turn. */
            st.waterUsed = true;
            const terr = ans.terrain && terrains.includes(ans.terrain)
              ? ans.terrain
              : yield { type: "waterexplore", seat: p.i,
                        options: [ans.dest], terrains, landfall: true };
            const chosen = terr && terr.terrain ? terr.terrain : terr;
            if (!chosen || !terrains.includes(chosen)) break;
            if (!this.m.doExplore(ans.dest, chosen)) break;
            this._doMove(p, ans.src, ans.dest);
            st.moves -= 1;
            this.inc("water_explore"); this.inc("water_landfall");
            this.say("log.water");
            break;
          }

          const fromSea = this.m.tiles.get(ans.src).terrain === "ocean";
          const toSea = this.m.tiles.get(ans.dest).terrain === "ocean";
          this._doMove(p, ans.src, ans.dest);
          st.moves -= 1;
          /* The water advantage (§07): your FIRST sea move each turn grants one
           * free explore of ANY terrain. It is a real choice, so it is asked. */
          if (fromSea && toSea && !st.waterUsed) {
            const cells = this.waterExploreCells(ans.src, ans.dest);
            const terrains = TER.filter((t) => this.m.supply[t] > 0);
            if (cells.length && terrains.length) {
              /* Spent only when it is actually offered. It used to be marked
               * used before this check, so sailing into open water — where
               * nothing legal is in reach — burned the advantage for the whole
               * turn without ever showing the player a choice. */
              st.waterUsed = true;
              const pick = yield { type: "waterexplore", seat: p.i,
                                   options: cells, terrains };
              if (pick) {
                this.m.doExplore(pick.cell, pick.terrain);
                /* The ship goes ashore. Sighting land and then staying at sea
                 * left the new tile unowned and the voyage with nothing to
                 * show for itself; landing on it is what makes the advantage
                 * read as "you found somewhere and took it". */
                this._doMove(p, ans.dest, pick.cell);
                this.inc("water_explore");
                this.say("log.water");
              }
            } else {
              // say so: silence here reads as a broken rule
              this.inc("water_nowhere");
              this.say("log.waterNone");
            }
          }
          break;
        }
        case "fortify": {
          if (p.gold >= 1 && this.m.fortify(ans.cell)) {
            p.gold -= 1; this.inc("fortified");
          }
          break;
        }
        case "research": {
          /* Counted when the action is TAKEN, not when it succeeds. The draw
           * onto the grid has already happened and the deck is the game's
           * clock; letting a blocked attempt be retried for free would let a
           * player thin the deck at no cost. Under the escalating rule this is
           * also what raises the price of the next one — an attempt that found
           * nothing still puts the price up, for the same reason. */
          if (!this.canResearch(p, st)) break;
          const price = this.researchCost(st);
          st.researches += 1;
          yield* this._researchHuman(p, price);
          break;
        }
        case "colony": {
          if (!st.bUsed && (yield* this._playColonyHuman(p, ans.card))) st.bUsed = true;
          break;
        }
        case "conquest": {
          /* Spend a victory card on D. Each hit takes the fortification coin
           * first if there is one; a tile you empty is settled if the card's
           * band allows it and a unit is left in your reserve. */
          const i = p.vrow.indexOf(ans.card);
          if (i < 0) break;
          const [kills, maySettle] = effectD(ans.card.r);
          let targets = this.conquestTargets(p);
          if (!targets.length) break;
          p.vrow.splice(i, 1);
          this.removed.push(ans.card);
          this.inc("effect_d_used");
          for (let n = 0; n < kills; n++) {
            targets = this.conquestTargets(p);
            if (!targets.length) break;
            const cell = yield { type: "conquest", seat: p.i, options: targets,
                                 left: kills - n, card: ans.card, maySettle };
            if (!cell) break;
            const t = this.m.tiles.get(cell);
            const cost = ATTACK_COST[t.terrain];
            if (p.gold < cost) break;
            p.gold -= cost;
            this.inc("gold_out_attack", cost); this.inc("gold_out_conquest", cost);
            const victim = this.m.removeUnit(cell);
            if (victim === null) { this.inc("absorbed_by_fortification"); continue; }
            this.P[victim].returnUnit();
            this.fx("unit-out", { seat: victim, from: cell });
            this.inc("killed_by_attack"); this.inc("conquest_kill");
            if (maySettle && !t.units.length && p.takeUnit()) {
              this.m.settle(cell, p.i);
              this._payAscension(p);
              this.inc("conquest_settle");
            }
          }
          this.say("log.conquest");
          break;
        }
        case "cashRow": {
          const i = p.vrow.indexOf(ans.card);
          if (i >= 0) {
            p.vrow.splice(i, 1);
            this.removed.push(ans.card);
            p.gold += effectC(ans.card.r);
            this.inc("effect_c_used"); this.inc("gold_in_effect_c", effectC(ans.card.r));
            this.say("log.cashRow", { n: effectC(ans.card.r) });
          }
          break;
        }
      }
      yield* refill(this);
    }
    /* Meld cards not used for map actions earn one gold each (§06). */
    for (const c of st.cards) {
      p.discard.push(c);
      p.gold += 1;
      this.inc("cards_to_gold"); this.inc("gold_in_unplaceable");
    }
    if (st.cards.length)
      this.say("log.unusedGold", { n: st.cards.length });
    st.cards = [];
    yield* refill(this);
  }

  /* Which card to give up when you matched the winner and lost: the one whose
   * removal costs the least hand_power. */
  *_pickDiscard(p) {
    if (!p.hand.length) return null;
    if (this.isHuman(p.i))
      return yield { type: "discard", seat: p.i, options: p.hand.slice() };
    let best = null, bv = -1e9;
    for (const c of p.hand) {
      const v = handPower(p.hand.filter((x) => x !== c));
      if (v > bv) { best = c; bv = v; }
    }
    return best;
  }

  /* Which played card to set aside when you matched the winner's count. It is
   * not spent on the map; it pays 1 gold. The bot gives up whatever the map
   * wants least, judged the same way it judges cashing. */
  *_pickSetAside(p, use) {
    if (!use.length) return null;
    if (this.isHuman(p.i))
      return yield { type: "setaside", seat: p.i, options: use.slice() };
    const spaces = this.m.legalSpaces();
    const civ = this.m.civ(p.i);
    const reachable = civ.size ? reach(this.m, p.i, civ)
                               : new Set([...this.m.tiles.keys(), ...spaces]);
    let worst = null, wv = 1e9;
    for (const c of use) {
      const opts = cardOptions(this.m, c, p.i, p.gold, reachable, spaces);
      const v = Math.max(p.w.CASH_THRESHOLD,
        ...opts.map(([k, a]) => valueCard(this, p, k, c, a)));
      if (v < wv) { wv = v; worst = c; }
    }
    return worst;
  }

  /* The extra card the trick winner spends. null if the hand is empty — the
   * caller then pays a coin instead. */
  *_pickBonus(p) {
    if (!p.hand.length) return null;
    if (this.isHuman(p.i))
      return yield { type: "bonus", seat: p.i, options: p.hand.slice() };
    const spaces = this.m.legalSpaces();
    const civ = this.m.civ(p.i);
    const reachable = civ.size ? reach(this.m, p.i, civ)
                               : new Set([...this.m.tiles.keys(), ...spaces]);
    let best = null, bestV = -1e9;
    for (const c of p.hand) {
      const opts = cardOptions(this.m, c, p.i, p.gold, reachable, spaces);
      const v = Math.max(p.w.CASH_THRESHOLD,
        ...opts.map(([k, a]) => valueCard(this, p, k, c, a)));
      if (v > bestV) { best = c; bestV = v; }
    }
    return best;
  }

  /* Spend each card of the meld INDEPENDENTLY (§06). No pattern, no shape, no
   * ordering constraint; the map is re-read between cards, so an explore can
   * deliberately open ground that a later card settles. */
  *_place(p, cards) {
    if (!cards.length) return;
    const todo = cards.slice();
    while (todo.length) {
      const exempt = this.m.civ(p.i).size === 0;      // re-entry rule (§06)
      const spaces = this.m.legalSpaces();
      const reachable = exempt ? new Set([...this.m.tiles.keys(), ...spaces])
                               : reach(this.m, p.i);

      let best = null;                               // [value, card, cell, act]
      const all = [];
      for (const card of todo) {
        for (const [k, act] of cardOptions(this.m, card, p.i, p.gold, reachable, spaces)) {
          const v = valueCard(this, p, k, card, act);
          all.push([v, card, k, act]);
          if (best === null || v > best[0]) best = [v, card, k, act];
        }
      }
      // a less certain bot sometimes spends a card somewhere other than its best
      if (best !== null && p.noise && this.rng.random() < p.noise)
        best = this.rng.choice(all);
      if (best === null) {                           // nothing legal for any card
        this.inc("no_legal_placement", todo.length);
        this.inc("cards_to_gold", todo.length);
        p.gold += todo.length;
        return;
      }
      const [v, card, cell, act] = best;
      todo.splice(todo.indexOf(card), 1);

      // cashing on purpose: gold is a first-class use of a card, not a fallback
      let thr = 0.8;
      if (p.gold < p.food() + 1) thr = 2.2;
      else if (p.gold >= 3) thr = 0.4;
      if (v < thr || p.gold < p.food()) {
        this.inc("cash_events"); this.inc("cards_to_gold"); this.inc("gold_in_cashed");
        if (act === "settle") this.inc("cash_gave_up_a_settle");
        p.gold += 1;
        continue;
      }
      this._resolve(p, card, cell, act);
    }
  }

  _resolve(p, card, cell, act) {
    this.inc("cards_resolved");
    if (act === "cash") { p.gold += 1; this.inc("cards_to_gold"); return; }
    if (act === "explore") {
      if (this.m.doExplore(cell, card.s)) {
        this.inc("explore");
        this.fx("tile", { seat: p.i, to: cell });
      }
      else { p.gold += 1; this.inc("cards_to_gold"); }
    } else if (act === "settle") {
      /* Holding back — taking gold rather than climbing into a tier you cannot
       * feed — is the BOT'S policy, not a rule. Applying it to a person turned
       * a chosen Settle into a coin with no explanation, which reads as the
       * game losing your unit. A human who clicks Settle, settles. */
      if (!this.isHuman(p.i) && !p.reserveEmpty()
          && this._wouldClimb(p) && p.gold < this._nextFood(p)) {
        this.inc("held_back"); this.inc("cards_to_gold"); p.gold += 1;
      } else if (p.takeUnit()) {
        this.inc("settle");
        this.m.settle(cell, p.i);
        this.fx("unit-in", { seat: p.i, to: cell });
        this._payAscension(p);
      } else {
        this.inc("settle_no_reserve"); this.inc("cards_to_gold"); p.gold += 1;
      }
    } else if (act === "attack") {
      const tile = this.m.tiles.get(cell);
      const cost = ATTACK_COST[tile.terrain];
      if (p.gold >= cost && tile.units.length) {
        p.gold -= cost; this.inc("gold_out_attack", cost);
        const victim = this.m.removeUnit(cell);
        if (victim === null) {
          this.inc("absorbed_by_fortification");
          this.fx("shield", { seat: p.i, at: cell });
        } else {
          this.inc("killed_by_attack"); this.P[victim].returnUnit();
          this.fx("unit-out", { seat: victim, from: cell });
        }
      } else { p.gold += 1; this.inc("cards_to_gold"); }
    }
  }

  // --- research -------------------------------------------------
  _vrowGain(p, card) {
    const row = p.vrow.map((c) => c.r);
    return vrowScore(row.concat([card.r])) - vrowScore(row);
  }

  /* Which cards research may retire. Under "lowest" it is the lowest rank in
   * hand and every copy of it, so the only decision is which SUIT to lose —
   * and that is a real decision, because a suit is the terrain a card can be
   * spent on. Under "any" it is the whole hand, as §10 prints it. */
  retirable(p) {
    if (!p.hand.length) return [];
    if (this.RETIRE_RULE !== "lowest") return p.hand.slice();
    const low = Math.min(...p.hand.map((c) => c.r));
    return p.hand.filter((c) => c.r === low);
  }

  *_pickRetire(p) {
    const pool = this.retirable(p);
    if (!pool.length) return null;
    let best = null, bv = -1e9;
    for (const c of pool) {
      const rest = p.hand.filter((x) => x !== c);
      const v = p.w.RETIRE_GAIN_W * this._vrowGain(p, c)
              + p.w.RETIRE_RANK_W * c.r + handPower(rest);
      if (v > bv) { best = c; bv = v; }
    }
    return best;
  }

  /* WHICH card to buy. `_buyValue` existed from the first port and was never
   * called: the line here was `this.rng.choice(avail)`, so every bot in every
   * measurement taken before 14 Aug 2026 chose its upgrades by coin flip. See
   * RULEBOOK-CORRECTIONS item 16 for what fixing it is worth. */
  _chooseBuy(p, avail, pool) {
    if (p.w.BUY_RANDOM || (p.noise && this.rng.random() < p.noise))
      return this.rng.choice(avail);
    let best = avail[0], bv = -1e9;
    for (const k of avail) {
      const v = this._buyValue(p, this.gridTop(k), pool);
      if (v > bv) { bv = v; best = k; }
    }
    return best;
  }

  _buyValue(p, card, pool) {
    if (!card) return -1e9;
    const ranks = pool.map((c) => c.r);
    const cnt = (r) => ranks.filter((x) => x === r).length;
    return p.w.BUY_MATCH_W * cnt(card.r)
         + p.w.BUY_NEAR_W * (cnt(card.r - 1) + cnt(card.r + 1))
         + p.w.BUY_RANK_W * card.r;
  }

  /* Research (§10). Draw the top of the upgrade deck onto a grid position of
   * your choice, retire a card FROM YOUR HAND to the victory row, pay, and take
   * any visible card at or below your RANK CAP.
   *
   * Once a turn under the printed rule. Under the escalating rule the bot keeps
   * going while it can pay the rising price AND the hand is still short enough
   * to be worth fixing — a bot that only ever took one would make the variant
   * measure as "no effect" no matter what the rule actually does. */
  *_maybeUpgrade(p) {                                  // bot path
    let taken = 0;
    for (;;) {
      if (taken >= this.RESEARCH_MAX) return;
      const price = this.RESEARCH_RULE === "once" ? 1 : taken + 1;
      if (taken && p.gold < price + p.w.CASH_THRESHOLD) return;   // keep a cushion
      const did = yield* this._upgradeOnce(p, price);
      if (!did) return;
      taken += 1;
      if (taken >= 4) return;      // a bot's stop, not a rule: no runaway loops
    }
  }

  *_upgradeOnce(p, price) {
    if (p.vrow.length >= 5) return false;
    if (p.gold < price) { this.inc("upgrade_no_gold"); return false; }
    if (!p.hand.length) { this.inc("upgrade_no_card_to_retire"); return false; }
    /* Wait for the hand to run short, so the card retired is a high one. A
     * policy, not a rule — see RESEARCH_MAX_HAND. */
    if (p.hand.length > p.w.RESEARCH_MAX_HAND) {
      this.inc("research_held_for_timing"); return false;
    }
    const pool = p.hand.concat(p.discard);
    const cap0 = p.rankCap();

    // would this be a blind fish? A real player looks first.
    const visible = this.grid.some((_, k) => {
      const t = this.gridTop(k); return t && t.r <= cap0;
    });
    if (!visible) {
      const odds = this.deck.length
        ? this.deck.filter((c) => c.r <= cap0).length / this.deck.length : 0;
      if (odds < p.w.BLIND_RESEARCH_ODDS) {
        this.inc("research_declined_blind"); return false;
      }
    }

    this._drawOntoGrid();                              // 1. draw onto the grid

    const avail = this.buyable(p);                     // 2. what may this tier buy?
    if (!avail.length) { this.inc("upgrade_blocked_by_cap"); return false; }
    const k = this._chooseBuy(p, avail, pool);
    const retire = yield* this._pickRetire(p);
    if (retire === null) return false;
    this._completeResearch(p, k, retire, price);
    return true;
  }

  /* Where a drawn card lands. NOT the player's choice any more: it goes on the
   * position showing the HIGHEST rank, burying it. Ties break to the leftmost
   * position so the rule is deterministic and a person can predict it.
   *
   * The consequence is the point: the tallest card on the market is the one
   * most likely to be covered, so the top of the market keeps sinking out of
   * reach. That tightens access to high ranks on top of the rank cap, rather
   * than letting each player bury whatever suits them. */
  autoGridSlot() {
    let best = 0, bestRank = -1;
    for (let k = 0; k < this.grid.length; k++) {
      const t = this.gridTop(k);
      const r = t ? t.r : 0;
      if (r > bestRank) { bestRank = r; best = k; }
    }
    return best;
  }

  _drawOntoGrid() {
    if (!this.deck.length) return null;
    const card = this.deck.pop();
    const k = this.autoGridSlot();
    this.grid[k].push(card);
    this.inc("grid_draws");
    this.fx("deal", { card, slot: k, left: this.deck.length });
    return { card, slot: k };
  }

  buyable(p) {
    const cap = p.rankCap();
    const out = [];
    for (let k = 0; k < this.grid.length; k++) {
      const t = this.gridTop(k);
      if (t && t.r <= cap) out.push(k);
    }
    return out;
  }

  /* 3. retire, pay, take. The card you buy goes STRAIGHT INTO YOUR HAND. */
  _completeResearch(p, k, retire, cost) {
    const price = cost === undefined ? 1 : cost;
    const buy = this.gridTop(k);
    p.hand.splice(p.hand.indexOf(retire), 1);
    p.vrow.push(retire);
    this.fx("card", { seat: p.i, card: retire, from: "hand", to: "vrow" });
    p.gold -= price;
    this.inc("gold_out_upgrade", price); this.inc("upgrades");
    if (price > 1) this.inc("research_repeat"); // a second or later one this turn
    this.fx("gold", { seat: p.i, amount: -price, to: "market" });
    this.grid[k].pop();
    p.hand.push(buy);
    this.fx("card", { seat: p.i, card: buy, from: "market", to: "hand", slot: k });
    for (let j = 0; j < this.grid.length; j++)
      if (!this.grid[j].length && this.deck.length) this.grid[j].push(this.deck.pop());
    return buy;
  }

  /* The same research, asked step by step. Returns true if it completed — a
   * player who backs out at the buy step keeps their gold and their card, but
   * the drawn card stays on the grid, because it has been seen. */
  /* Two decisions: which card leaves your hand, and which one you take. The
   * draw is automatic (autoGridSlot), so it is shown, not chosen. */
  /* ---- what a research costs, and whether you may take one ----
   *
   * One place, asked by the turn options, by the action itself and by the bot,
   * so a button that says "2 gold" and an engine that charges 3 cannot happen.
   * `st.researches` is how many have already been taken THIS turn. */
  researchCost(st) {
    const used = (st && st.researches) || 0;
    return this.RESEARCH_RULE === "once" ? 1 : used + 1;
  }
  canResearch(p, st) {
    if (((st && st.researches) || 0) >= this.RESEARCH_MAX) return false;
    return p.vrow.length < 5 && p.hand.length > 0
      && p.gold >= this.researchCost(st);
  }
  researchBlocked(p, st) {
    if (((st && st.researches) || 0) >= this.RESEARCH_MAX)
      return this.RESEARCH_MAX === 1 ? "why.research.done" : "why.research.max";
    if (p.vrow.length >= 5) return "why.research.rowFull";
    if (!p.hand.length) return "why.research.noCard";
    if (p.gold < this.researchCost(st)) return "why.research.gold";
    return null;
  }

  *_researchHuman(p, cost) {
    const price = cost === undefined ? 1 : cost;
    if (p.vrow.length >= 5 || p.gold < price || !p.hand.length) return false;
    const drew = this._drawOntoGrid();

    /* Check the market BEFORE asking for a card, so nobody gives one up only to
     * find there is nothing they may take. */
    const avail = this.buyable(p);
    if (!avail.length) {
      this.inc("upgrade_blocked_by_cap");
      this.say("log.noBuy");
      return false;
    }
    const retire = yield {
      type: "retire", seat: p.i, options: this.retirable(p), drew,
      rule: this.RETIRE_RULE, cost: price,
    };
    if (!retire) return false;
    const k = yield { type: "buy", seat: p.i, options: avail, retire, drew,
                      cost: price };
    if (k === null || k === undefined) return false;
    const buy = this._completeResearch(p, k, retire, price);
    this.say("log.researched", { out: retire.r + SUIT_LETTER[retire.s],
                                 in: buy.r + SUIT_LETTER[buy.s] });
    return true;
  }

  // --- victory-card effects -------------------------------------
  /* A, declared blind: commit before seeing anyone else's meld. */
  *_maybeDeclareABlind(p) {
    let card;
    if (this.isHuman(p.i)) {
      /* A person may spend A whenever they hold a victory card — the size and
       * row-depth tests below are the BOT'S policy, not the rule. */
      if (!p.vrow.length) return;
      card = yield { type: "effectA", seat: p.i, options: p.vrow.slice() };
      if (!card) return;
    } else if (this.MELD_SCORE === "sum") {
      /* Under sum scoring "rescue a small meld" is the wrong instinct — a meld
       * of two big cards may already be winning, and one of five small ones may
       * not be. The bot spends A when the bonus could plausibly close the gap
       * to a rival's likely total, which is the same guess its meld chooser
       * makes. Policy, not rule: a person may spend A whenever they hold one. */
      if (p.vrow.length < 3) return;
      const mine = p.played.reduce((a, c) => a + c.r, 0);
      const rivals = this.P.filter((q) => q.i !== p.i).map((q) => q.meldLimit());
      const typical = p.hand.length
        ? p.hand.reduce((a, c) => a + c.r, 0) / p.hand.length : 10.5;
      const target = (rivals.length ? Math.max(...rivals) : 0) * typical;
      const best = p.vrow.slice().sort(cardSort)[0];
      const [gain] = effectASum(best.r, this.A_SUM_LADDER);
      if (mine + gain < target * 0.8) return;       // hopeless: keep the card
      if (mine > target * 1.25) return;             // already ahead: keep it
      card = best;
    } else {
      if (p.vrow.length < 3) return;
      const size = p.played.length;
      if (size >= p.meldLimit()) return;            // already your best
      if (size > 2) return;                         // only rescue weak melds
      card = p.vrow.slice().sort(cardSort)[0];
    }
    p.vrow.splice(p.vrow.indexOf(card), 1);
    this.removed.push(card);
    /* Two readings of the same card, one per scoring rule: cards under "count",
     * points on the total under "sum". Both are kept on the player because the
     * comparator reads whichever the rule needs and a replay must not care. */
    if (this.MELD_SCORE === "sum") {
      const [add, ties] = effectASum(card.r, this.A_SUM_LADDER);
      p.sumBonus += add; p.ties = p.ties || ties;
      this.inc("effect_a_sum_gain", add);
    } else {
      const [add, ties] = effectA(card.r);
      p.bonus += add; p.ties = p.ties || ties;
    }
    p.spentA = Math.max(p.spentA, card.r);
    p.aBand = bandOfRank(card.r);
    this.inc("effect_a_used");
  }

  /* B — found colonies (§10). Lay new tiles, put units on them, fortify them
   * from the GENERAL SUPPLY. Touch-two still applies; REACH does not. */
  *_maybeUseB(p) {                                   // bot path
    /* The four-card guard is the BOT'S, matched to D's so the two can be
     * compared. The rule is one card per turn, a legal space, and a tile of
     * the right terrain still in the supply. */
    if (p.reserveEmpty() || p.vrow.length < p.w.COLONY_MIN_ROW) return;
    for (const c of p.vrow.slice().sort(cardSort)) if (this._playColony(p, c)) return;
    if (false) yield null;                           // keeps the generator signature
  }

  /* Where a colony may be founded. Exploring is exploring (§06): the space
   * must touch two tiles already on the map AND be in your reach. The 6-10
   * band is the one exception the card prints — "up to 2 tiles out".
   *
   * This was missing entirely: B used every legal space on the board, so a
   * colony could be founded on the far side of the map, next to somebody
   * else's civilization. */
  colonyCells(p, card) {
    const dist = effectBv22(card.r)[3] || 1;
    const spaces = this.m.legalSpaces();
    if (!spaces.size) return [];
    // swept off the map: the §06 re-entry exemption, or B could never restart you
    if (this.m.civ(p.i).size === 0) return Array.from(spaces).sort();
    const rr = reachOut(this.m, p.i, dist);
    return Array.from(spaces).filter((k) => rr.has(k)).sort();
  }

  /* One colony tile: lay it, settle a unit on it if the card still owes one,
   * and fortify from the GENERAL supply. Shared by both paths so the rule
   * cannot drift between the bot and the person. */
  _foundColony(p, cell, terr, settleIt) {
    if (!this.m.doExplore(cell, terr)) return false;
    this.inc("colony_tile");
    this.fx("tile", { seat: p.i, to: cell });
    if (settleIt && p.takeUnit()) {
      this.m.settle(cell, p.i);
      this._payAscension(p);
      this.inc("colony_unit");
      this.fx("unit-in", { seat: p.i, to: cell });
      if (this.m.fortify(cell)) { this.inc("colony_fortify"); this.fx("shield", { at: cell }); }
    }
    return true;
  }

  _playColony(p, c) {                                // bot path
    if (p.reserveEmpty()) return false;
    const [tiles, units, sameSuit] = effectBv22(c.r);
    const want = sameSuit ? c.s : null;
    if (want !== null && this.m.supply[want] <= 0) return false;
    if (!this.colonyCells(p, c).length) return false;

    p.vrow.splice(p.vrow.indexOf(c), 1);
    this.removed.push(c);
    this.inc("effect_b_used");

    let placed = 0, settled = 0;
    while (placed < tiles) {
      const usable = this.colonyCells(p, c);         // re-read: the map just grew
      if (!usable.length) break;
      let terr = want;
      if (terr === null) {                           // ranks 16-20: any terrain
        const opts = TER.filter((t) => this.m.supply[t] > 0);
        if (!opts.length) break;
        terr = opts.reduce((a, b) => (this.m.supply[b] > this.m.supply[a] ? b : a));
      }
      if (!this._foundColony(p, usable[0], terr, settled < units)) break;
      placed += 1;
      if (settled < units) settled += 1;
    }
    return true;
  }

  /* The same effect, asked. Where a colony lands is a real decision — it is
   * new ground, and it decides who your next neighbour is — so a person picks
   * the cell, and the terrain too when the card allows any. */
  *_playColonyHuman(p, c) {
    if (p.reserveEmpty()) return false;
    const [tiles, units, sameSuit] = effectBv22(c.r);
    const want = sameSuit ? c.s : null;
    if (want !== null && this.m.supply[want] <= 0) return false;
    if (!this.colonyCells(p, c).length) return false;

    p.vrow.splice(p.vrow.indexOf(c), 1);
    this.removed.push(c);
    this.inc("effect_b_used");

    let placed = 0, settled = 0;
    while (placed < tiles) {
      const options = this.colonyCells(p, c);
      const terrains = want !== null ? [want] : TER.filter((t) => this.m.supply[t] > 0);
      if (!options.length || !terrains.length) break;
      const pick = yield { type: "colony", seat: p.i, card: c, options, terrains,
                           left: tiles - placed, settles: Math.max(0, units - settled) };
      if (!pick) break;                              // may stop early; the card is spent
      if (!this._foundColony(p, pick.cell, pick.terrain || terrains[0], settled < units)) break;
      placed += 1;
      if (settled < units) settled += 1;
    }
    this.say("log.colony", { n: placed });
    return true;
  }

  /* D — CONQUEST, bot path.
   *
   * Two guards were tried and both measure the guard rather than the effect:
   *   - B's four-card guard: D took ground 0 times in 900 games. A row does not
   *     reach four cards until late, and by then the reserve is empty, so the
   *     settle step — D's entire point — always failed.
   *   - no guard: D fired 18-24 times a game, B never fired at all, the row
   *     scored 1, and table scores halved. It simply ate the row.
   *
   * So the bot prices it instead, the way it prices C: a strike is worth the
   * rival point it removes plus the point it plants, and the card costs what
   * the row would lose (_rowCost, padded for the cards still to come). Spend
   * only when the swing beats the point. This is a policy, not a rule. */
  *_maybeUseD(p) {
    if (this.DECK !== "abd" || !p.vrow.length) return;
    const targets = this.conquestTargets(p);
    if (!targets.length) return;
    // tiles a strike would actually empty, and so take
    const thin = targets.filter((k) => {
      const t = this.m.tiles.get(k);
      return t.units.length === 1 && !t.gold;
    });
    // what the cheapest strikes would cost in coins
    const prices = targets.map((k) => ATTACK_COST[this.m.tiles.get(k).terrain])
                          .sort((a, b) => a - b);
    for (const card of p.vrow.slice().sort(cardSort)) {
      const [kills, maySettle] = effectD(card.r);
      const takes = maySettle && !p.reserveEmpty()
        ? Math.min(kills, thin.length) : 0;
      /* A kill is a point off a RIVAL, not onto you; only the settle adds to
       * your own total. Pricing denial at 1.0 made every card a strike. */
      const gain = takes + p.w.D_DENIAL_W * Math.min(kills, targets.length);
      const coins = prices.slice(0, kills).reduce((a, b) => a + b, 0);
      if (coins > p.gold) continue;                   // cannot pay the terrain
      // a coin is worth roughly a third of a point in this economy
      if (gain <= this._rowCost(p, card) + 0.33 * coins) continue;
      p.vrow.splice(p.vrow.indexOf(card), 1);
      this.removed.push(card);
      this.inc("effect_d_used");
      let done = 0, list = targets;
      while (done < kills) {
        list = this.conquestTargets(p);
        if (!list.length) break;
        // prefer a thin tile we can actually take over
        list.sort((x, y) => {
          const tx = this.m.tiles.get(x), ty = this.m.tiles.get(y);
          return tx.units.length - ty.units.length
                 || ATTACK_COST[tx.terrain] - ATTACK_COST[ty.terrain]
                 || tx.gold - ty.gold || x.localeCompare(y);
        });
        const cell = list[0];
        const t = this.m.tiles.get(cell);
        const cost = ATTACK_COST[t.terrain];
        if (p.gold < cost) break;
        p.gold -= cost;
        this.inc("gold_out_attack", cost);
        if (cost) this.fx("gold", { seat: p.i, amount: -cost, to: cell }); this.inc("gold_out_conquest", cost);
        const victim = this.m.removeUnit(cell);
        done += 1;
        if (victim === null) { this.inc("absorbed_by_fortification"); continue; }
        this.P[victim].returnUnit();
        this.inc("killed_by_attack"); this.inc("conquest_kill");
        if (maySettle && !t.units.length && p.takeUnit()) {
          this.m.settle(cell, p.i);
          this._payAscension(p);
          this.inc("conquest_settle");
        }
      }
      return;
    }
    if (false) yield null;
  }

  /* What spending this victory card REALLY costs. The row only scores at the
   * very end, so pricing it at today's score is wrong — pad the row with the
   * cards still to come and price the sale against that. */
  _rowCost(p, card) {
    const horizon = this.endedOn ? 0 : p.w.ROW_HORIZON;
    const row = p.vrow.map((c) => c.r);
    const rest = row.slice();
    rest.splice(rest.indexOf(card.r), 1);
    const pad = new Array(horizon).fill(p.w.ROW_PAD_RANK);
    return vrowScore(row.concat(pad)) - vrowScore(rest.concat(pad));
  }

  /* C — cash a victory card for gold when the coins are worth more than the
   * point (§12). Bot path; a person cashes from the turn menu at will. */
  *_maybeCashC(p, ahead) {
    if (!p.vrow.length) return;
    while (p.vrow.length) {
      const low = p.vrow.slice().sort(cardSort)[0];
      const cost = this._rowCost(p, low);
      const gain = effectC(low.r);
      const need = ahead ? p.food() + 1 : Math.max(1, p.food());
      const broke = p.gold < need;
      if (!broke || gain < cost * p.w.C_GOLD_PER_POINT) return;
      p.vrow.splice(p.vrow.indexOf(low), 1);
      this.removed.push(low);
      p.gold += gain;
      this.inc("effect_c_used"); this.inc("gold_in_effect_c", gain);
    }
    if (false) yield null;
  }

  _spendC(p, need) {
    while (p.gold < need && p.vrow.length) {
      const card = p.vrow.slice().sort(cardSort)[0];
      p.vrow.splice(p.vrow.indexOf(card), 1);
      this.removed.push(card);
      p.gold += effectC(card.r);
      this.inc("effect_c_used"); this.inc("gold_in_effect_c", effectC(card.r));
    }
  }

  // --- movement -------------------------------------------------
  /* Where a unit can legally go. Land moves travel across your own occupied
   * tiles and step off at the end; sea moves cross open Ocean. */
  moveDests(p, srcKey) {
    const t = this.m.tiles.get(srcKey);
    const seen = new Set([srcKey]), frontier = [srcKey];
    while (frontier.length) {
      const c = frontier.pop();
      for (const u of this.m.tiles.get(c).neighbours()) {
        if (seen.has(u.key)) continue;
        if (u.owner === p.i && u.units.length) { seen.add(u.key); frontier.push(u.key); }
      }
    }
    const pool = new Set();
    for (const c of seen)
      for (const u of this.m.tiles.get(c).neighbours())
        if ((u.owner === null || u.owner === p.i) && u.hasRoom(p.i) && u.key !== srcKey)
          pool.add(u.key);
    if (t.terrain === "ocean")            // sea: across unoccupied Ocean
      for (const k of this.seaGroup(srcKey)) if (k !== srcKey) pool.add(k);
    return pool;
  }

  /* The open water a ship at `srcKey` can actually reach: Ocean tiles joined to
   * it by other Ocean, stopping at any tile that already holds a unit. Includes
   * srcKey itself, so it is also "the body of water this ship is in".
   *
   * Pulled out of moveDests because the water advantage needs the same answer.
   * When the two were computed separately they drifted apart, and the explore
   * ended up offering the whole map. */
  seaGroup(srcKey) {
    const start = this.m.tiles.get(srcKey);
    const seen = new Set([srcKey]);
    if (!start || start.terrain !== "ocean") return seen;
    const fr = [srcKey];
    while (fr.length) {
      const c = fr.pop();
      for (const u of this.m.tiles.get(c).neighbours()) {
        if (seen.has(u.key) || u.terrain !== "ocean") continue;
        if (u.units.length) continue;     // your own ships block your own lane
        seen.add(u.key); fr.push(u.key);
      }
    }
    return seen;
  }

  /* ---- where a voyage may make landfall ----
   *
   * The other half of a move that starts on water, and NOT a tile: these are
   * empty cells. A ship may end its move on ground that does not exist yet —
   * the tile is laid as the move resolves and the unit steps onto it (§07).
   *
   * Kept separate from moveDests() on purpose. That returns tiles, and three
   * different callers (the bots' mover, moveSources, the legality check) all
   * assume they can look every key up in `m.tiles`. Mixing empty cells into it
   * would break them silently. So: two questions, two methods, and the caller
   * that wants to offer both asks twice.
   *
   * Eligible means all of:
   *   - the ship is on Ocean;
   *   - the cell touches the body of water the ship is in (its own tile counts:
   *     a ship moored on a lone Ocean tile can still see the shore);
   *   - the cell is a legal space, so touch-two still holds — §06's "Blink has
   *     no bridges" is structural and a voyage does not get to break it;
   *   - there is a tile left in the supply to lay;
   *   - and the advantage has not already been taken this turn.
   */
  landfallCells(p, srcKey, waterUsed) {
    if (waterUsed) return [];
    const t = this.m.tiles.get(srcKey);
    if (!t || t.terrain !== "ocean") return [];
    if (!TER.some((x) => this.m.supply[x] > 0)) return [];
    const spaces = this.m.legalSpaces();
    if (!spaces.size) return [];
    const water = this.seaGroup(srcKey);       // includes srcKey
    const out = [];
    for (const k of spaces) {
      const [c, r] = unK(k);
      if (nbrKeys(c, r).some((nb) => water.has(nb))) out.push(k);
    }
    return out.sort();
  }

  moveSources(p) {
    const out = [];
    for (const [k, t] of this.m.tiles)
      if (t.owner === p.i && t.units.length && this.moveDests(p, k).size) out.push(k);
    return out;
  }

  /* Move for a reason: reinforce a tile a rival can take, or evacuate one that
   * is already lost. Never spread thin. */
  _proMove(p) {
    let best = null;
    for (const [k, t] of this.m.tiles) {
      if (t.owner !== p.i || t.units.length < 2) continue;   // need a spare unit
      for (const u of t.neighbours()) {
        if (u.owner !== p.i || !u.units.length) continue;
        let threat = 0;
        for (const w of u.neighbours())
          if (w.owner !== null && w.owner !== p.i && w.units.length) threat++;
        if (!threat) continue;
        if (u.units.length < u.capacityFor(p.i)) {
          const score = 2.0 * threat - u.units.length;
          if (best === null || score > best[0]) best = [score, k, u.key];
        }
      }
    }
    return best ? [best[1], best[2]] : null;
  }

  _moveSource(p) {
    let best = null;
    for (const [k, t] of this.m.tiles) {
      if (t.owner !== p.i || !t.units.length) continue;
      const threatened = t.neighbours().some(
        (u) => u.owner !== null && u.owner !== p.i && u.units.length);
      let score = 0;
      if (threatened && t.gold === 0) score += 2.0;
      if (t.units.length > 1) score += 1.0;             // a spare unit
      else score -= 1.5;                                // moving surrenders the tile
      if (score <= 0) continue;
      if (best === null || score > best[0]) best = [score, k];
    }
    return best ? best[1] : null;
  }

  _moveDest(p, srcKey) {
    const pool = Array.from(this.moveDests(p, srcKey));
    if (!pool.length) return null;
    pool.sort((a, b) => {
      const ta = this.m.tiles.get(a), tb = this.m.tiles.get(b);
      const ka = [ta.units.length ? 1 : 0, -ta.capacityFor(p.i)];
      const kb = [tb.units.length ? 1 : 0, -tb.capacityFor(p.i)];
      return ka[0] - kb[0] || ka[1] - kb[1] || a.localeCompare(b);
    });
    return pool[0];
  }

  _doMove(p, srcKey, destKey) {
    const t = this.m.tiles.get(srcKey);
    t.units.splice(t.units.indexOf(p.i), 1);
    t.gold = Math.min(t.gold, t.units.length);          // a moved unit loses its coin
    this.m.settle(destKey, p.i);
    this.inc("free_move");
    this.fx("unit-move", { seat: p.i, from: srcKey, to: destKey });
  }

  /* Where the water advantage may lay its free tile: a legal space (touch-two,
   * §06) that is in your reach. `civ` may be supplied to ask the question of a
   * civilization you do not have yet — which is what deciding whether a sea
   * move will pay requires, since the destination only becomes yours once the
   * unit has moved. */
  exploreCells(p, civ) {
    const spaces = this.m.legalSpaces();
    if (!spaces.size) return [];
    if (!civ) {
      const rr = reach(this.m, p.i);
      return Array.from(spaces).filter((c) => rr.has(c)).sort();
    }
    const out = [];
    for (const c of spaces)
      for (const nb of nbrKeys(...unK(c)))
        if (civ.has(nb)) { out.push(c); break; }
    return out.sort();
  }

  /* ---- where the water advantage may lay its tile ----
   *
   * A voyage finds new land ON THE COAST IT SAILED TO. The eligible cells are
   * the empty spaces touching the body of water the ship is in — not the whole
   * map, and not your own civilization's frontier.
   *
   * This used to return every legal space on the board, which made the rule
   * incoherent at the table: a ship could sail two hexes and a player would
   * then place a tile in a completely unconnected corner of the map, with no
   * story attached to it and no relation to the voyage that earned it. That is
   * the bug this replaces. What a voyage buys is still that the ground it
   * finds need not be your own (a card explore acts next to your civilization,
   * §06) — but it must be ground the ship could actually have sighted.
   *
   * Touch-two still holds: §06's "Blink has no bridges" is the structural rule
   * that keeps the map one reachable body, and a voyage does not break it. So
   * a cell must both touch the water and touch two tiles overall.
   *
   * `srcKey` is where the ship started, `destKey` where it ended; the water it
   * can see is the union of both, since it sailed through. */
  waterExploreCells(srcKey, destKey) {
    const spaces = this.m.legalSpaces();
    if (!spaces.size) return [];
    const water = new Set();
    for (const k of [srcKey, destKey]) {
      if (k === undefined || k === null) continue;
      for (const w of this.seaGroup(k)) water.add(w);
      water.add(k);                       // the ship's own tile counts as coast
    }
    /* No voyage named — the caller is asking a question about the map rather
     * than about a ship. Answering "everywhere" here is what the old bug did;
     * answering "nowhere" is the safe direction, and no caller does this. */
    if (!water.size) return [];
    const out = [];
    for (const k of spaces) {
      const [c, r] = unK(k);
      if (nbrKeys(c, r).some((nb) => water.has(nb))) out.push(k);
    }
    return out.sort();
  }

  /* Would THIS sea move collect the advantage? A question about this voyage:
   * is there a tile left to lay, and is there anywhere on this coast to lay
   * it. Asked before the move, so it must be given both ends explicitly. */
  waterPays(p, srcKey, destKey) {
    const src = this.m.tiles.get(srcKey), dest = this.m.tiles.get(destKey);
    if (!src || !dest) return false;
    if (src.terrain !== "ocean" || dest.terrain !== "ocean") return false;
    if (!TER.some((t) => this.m.supply[t] > 0)) return false;
    return this.waterExploreCells(srcKey, destKey).length > 0;
  }

  /* The first sea move each turn grants one free explore of ANY terrain (§07),
   * on the coast the ship sailed to. A bot takes the same deal a person is
   * offered — including going ashore — or the two would be playing different
   * games and every measurement taken from bot play would be wrong. */
  _waterExplore(p, srcKey, destKey) {
    const opts = this.waterExploreCells(srcKey, destKey);
    if (!opts.length) return null;
    const avail = TER.filter((t) => this.m.supply[t] > 0);
    if (!avail.length) return null;
    const terr = avail.reduce((a, b) => (this.m.supply[b] > this.m.supply[a] ? b : a));
    if (!this.m.doExplore(opts[0], terr)) return null;
    this.inc("water_explore");
    if (destKey !== undefined && destKey !== null) this._doMove(p, destKey, opts[0]);
    return opts[0];
  }

  _seaMove(p) {
    if (!this.m.legalSpaces().size) return null;
    for (const [k, t] of this.m.tiles) {
      if (t.terrain !== "ocean" || t.owner !== p.i || !t.units.length) continue;
      for (const u of t.neighbours())
        if (u.terrain === "ocean" && !u.units.length) return [k, u.key];
    }
    return null;
  }

  *_freeMoves(p) {
    let budget = p.freeMoves();
    // the first sea move    // the first sea move buys a free explore, which is worth more than most
    // land moves — a bot that never takes it makes the rule measure as dead
    const sea = this._seaMove(p);
    if (budget > 0 && sea) {
      this._doMove(p, sea[0], sea[1]);
      this._waterExplore(p, sea[0], sea[1]);
      budget -= 1;
    }
    /* Pro seats move ONLY for a reason. There is deliberately no fallback to
     * the naive mover here: spreading thin measured worse than not moving. */
    while (budget > 0) {
      const mv = this._proMove(p);
      if (mv === null) return;
      this._doMove(p, mv[0], mv[1]);
      budget -= 1;
    }
    if (false) yield null;
  }

  // --- gold on the map ------------------------------------------
  /* Tiles worth protecting: a coin is only worth spending where losing the
   * unit actually costs something, and only if a rival next door can pay. */
  fortifyCandidates(p) {
    const out = [];
    for (const [k, t] of this.m.tiles) {
      if (t.owner !== p.i || t.gold >= t.units.length) continue;
      const threats = t.neighbours().filter((u) => u.owner !== null && u.owner !== p.i);
      if (!threats.length) continue;
      const cost = ATTACK_COST[t.terrain];
      if (!threats.some((u) => this.P[u.owner].gold >= cost)) continue;
      let v = threats.length * 1.0;
      if (t.units.length === 1) v += 2.0;      // losing this loses the tile
      v -= cost;                               // dear ground defends itself
      if (v > 0) out.push([v, k]);
    }
    out.sort((a, b) => b[0] - a[0]);
    return out;
  }

  *_maybeFortify(p) {
    /* Only out of genuine surplus: feed first, then keep this style's cushion.
     * (The line was a duplicated `if` — harmless, since a bare `if` nests, but
     * it hid the knob.) */
    if (p.gold < p.food() + 1 + p.w.FORTIFY_MIN_GOLD) return;
    const cand = this.fortifyCandidates(p);
    if (!cand.length) return;
    if (this.m.fortify(cand[0][1])) { p.gold -= 1; this.inc("fortified"); }
    if (false) yield null;
  }

  /* Gold reallocation (§07): a fortification coin is not sunk — pull it back
   * off the map rather than starve. */
  *_reclaimForFood(p) {
    const need = p.food();
    for (const [k, t] of this.m.tiles) {
      if (p.gold >= need) return;
      if (t.owner === p.i && t.gold) {
        const take = Math.min(t.gold, need - p.gold);
        t.gold -= take; p.gold += take;
        this.inc("gold_reclaimed", take);
      }
    }
    if (false) yield null;                     // keeps the generator signature
  }

  /* Variant: growing population limits. "If starvation drops your band, your
   * cities shed the difference — every tile of yours holding more than your new
   * limit sends the surplus back to the reserve. Those returned units refill
   * your reserve, which can drop your band again — repeat until no stack is
   * over its limit."
   *
   * So it is a cascade, and it can run more than once: units come back, the
   * reserve refills from the bottom, the band falls, and the new limit is
   * lower still. Only starvation culls — nothing lost in combat does this. */
  _shedOverLimit(p) {
    if (!this.GROW_LIMITS) return;
    for (let pass = 0; pass < 10; pass++) {
      let shed = 0;
      for (const [k, t] of this.m.tiles) {
        if (t.owner !== p.i) continue;
        while (t.units.length > t.capacityFor(p.i)) {
          this.m.takeUnitOff(k);
          p.returnUnit();
          shed++;
          this.inc("shed_over_limit");
          this.fx("unit-out", { seat: p.i, from: k, why: "over the limit" });
        }
      }
      if (!shed) return;
      this.say("log.shed", { n: shed });
    }
  }

  _wouldClimb(p) {
    const j = p.band();
    return p.reserve[j] === 1 && j + 1 < this.BANDS.length;
  }
  _nextFood(p) {
    const j = Math.min(p.band() + 1, this.BANDS.length - 1);
    return this.BANDS[j][3];
  }

  *_recycle(p) {
    let owed = p.food();
    if (this.DECK === "abd") {
      /* No take-gold effect: the row cannot be eaten. Gold comes from cashing a
       * card in hand, ascension, and ranking last — the three taps the proposal
       * says already fund the economy. */
    } else if (this.isHuman(p.i) && p.gold < owed && p.vrow.length) {
      // offer the row before the famine, exactly as the bot's _spend_c does
      while (p.gold < owed && p.vrow.length) {
        const card = yield { type: "feed", seat: p.i, owed, options: p.vrow.slice() };
        if (!card) break;
        p.vrow.splice(p.vrow.indexOf(card), 1);
        this.removed.push(card);
        p.gold += effectC(card.r);
        this.inc("effect_c_used"); this.inc("gold_in_effect_c", effectC(card.r));
      }
    } else if (!this.isHuman(p.i)) {
      this._spendC(p, owed);
    }
    const short = Math.max(0, owed - p.gold);      // one unit back per gold short
    for (let s = 0; s < short; s++) {
      const cells = [];
      for (const [k, t] of this.m.tiles) if (t.owner === p.i) cells.push(k);
      if (!cells.length) break;
      const c = this.rng.choice(cells);
      this.m.takeUnitOff(c);
      this.inc("starved_back");
      this.fx("unit-out", { seat: p.i, from: c, why: "starved" });
      p.returnUnit();
    }
    if (short) this._shedOverLimit(p);
    owed = Math.min(owed, p.gold);
    this.inc("gold_out_food", Math.min(owed, p.gold));
    p.gold = Math.max(0, p.gold - owed);
    this.inc("recycles"); this.inc("food_paid", owed);

    /* §09: take back everything you played, then draw from the SHARED pile up
     * to ten. The pile is shuffled first, so what comes back is whatever the
     * table has been throwing away — not your own cards in order. */
    p.hand = p.discard; p.discard = [];
    if (this.pile.length) this.rng.shuffle(this.pile);
    let drew = 0;
    while (p.hand.length < 10 && this.pile.length) {
      const c = this.pile.pop();
      p.hand.push(c);
      this.inc("drawn_from_pile"); drew++;
      this.fx("card", { seat: p.i, card: c, from: "pile", to: "hand" });
    }
    this.say("log.recycle", { back: p.hand.length - drew, drew });
  }

  // --- end and score --------------------------------------------
  /* Size, in TILES, of this seat's biggest connected group of `terrain`. */
  _largestPatch(seat, terrain) {
    const mine = new Set();
    for (const [k, t] of this.m.tiles)
      if (t.terrain === terrain && t.owner === seat && t.units.length) mine.add(k);
    let best = 0;
    const unseen = new Set(mine);
    while (unseen.size) {
      const first = unseen.values().next().value;
      unseen.delete(first);
      const comp = new Set([first]); const stack = [first];
      while (stack.length) {
        const c = stack.pop();
        const [x, y] = unK(c);
        for (const u of nbrKeys(x, y))
          if (unseen.has(u)) { unseen.delete(u); comp.add(u); stack.push(u); }
      }
      best = Math.max(best, comp.size);
    }
    return best;
  }

  /* Do all this seat's units on `terrain` sit in a single connected group? */
  _onePatch(seat, terrain) {
    const mine = new Set();
    for (const [k, t] of this.m.tiles)
      if (t.terrain === terrain && t.owner === seat && t.units.length) mine.add(k);
    if (mine.size <= 1) return true;
    const first = mine.values().next().value;
    const seen = new Set([first]), stack = [first];
    while (stack.length) {
      const c = stack.pop();
      const [x, y] = unK(c);
      for (const u of nbrKeys(x, y))
        if (mine.has(u) && !seen.has(u)) { seen.add(u); stack.push(u); }
    }
    return seen.size === mine.size;
  }

  _checkEnd() {
    if (this.endedOn) return;
    if (this.P.some((p) => p.reserveEmpty())) {
      this.endedOn = "end.lastUnit";
    } else if (!this.deck.length && this.grid.every((st) => st.length <= 1)) {
      /* The market THINNING to a single layer ends the game, not the deck
       * emptying: while the deck lasts every upgrade deepens the grid. */
      this.endedOn = "end.marketThin";
    }
    if (this.endedOn) {
      this.finalRounds = this.round + 1;   // finish this round, then ONE more
      this.say("log.endTriggered", { why: this.endedOn });
    }
  }

  /* §11: "Finish the current round, then play one more full round." The trigger
   * is checked at the END of a round, so the current round is already finished
   * and exactly one more should follow. `round > finalRounds` played TWO —
   * the Python sim has the same off-by-one, so every figure measured there
   * includes an extra round. */
  finished() { return this.finalRounds !== null && this.round >= this.finalRounds; }

  score() {
    const out = [];
    for (const p of this.P) {
      let pop = 0;
      for (const t of this.m.tiles.values())
        pop += t.units.filter((u) => u === p.i).length;
      const vp = vrowScore(p.vrow.map((c) => c.r));
      let dom = 0;
      const detail = {};
      for (const t of TER) {
        if (this.MAJORITY === "units") {
          /* Rulebook §13: most units on the terrain, disqualified entirely if
           * your units on it are not one connected group. Tied players score. */
          const cnt = {};
          for (const q of this.P) cnt[q.i] = 0;
          for (const tile of this.m.tiles.values())
            if (tile.terrain === t)
              for (const u of tile.units) cnt[u] += 1;
          const top = Math.max(...Object.values(cnt));
          if (!top || cnt[p.i] < top) continue;
          if (!this._onePatch(p.i, t)) { this.inc("majority_lost_to_split"); continue; }
          dom += 3; detail[t] = true;
          continue;
        }
        /* Dominance is the BIGGEST CONNECTED STRETCH of a terrain you occupy,
         * counted in tiles. Not most units — a tall stack dominates nothing. */
        const sizes = {};
        for (const q of this.P) sizes[q.i] = this._largestPatch(q.i, t);
        const mine = sizes[p.i], top = Math.max(...Object.values(sizes));
        if (mine < 1 || mine < top) continue;
        const level = Object.keys(sizes).filter((q) => sizes[q] === top);
        if (level.length > 1) {                    // level-breaker: units
          const u = {};
          for (const q of level) {
            let n = 0;
            for (const tile of this.m.tiles.values())
              if (tile.terrain === t) n += tile.units.filter((x) => x === Number(q)).length;
            u[q] = n;
          }
          if (u[p.i] < Math.max(...Object.values(u))) continue;
        }
        dom += 3; detail[t] = true;
      }
      let obj = 0;
      const objDone = [];
      for (const o of p.objectives || []) {
        const done = this.objectiveDone(p.i, o);
        objDone.push({ o, done });
        if (done) obj += o.points;
      }
      out.push({ seat: p.i, pop, vrow: vp, dom, obj, objDone,
                 total: pop + vp + dom + obj,
                 gold: p.gold, band: this.BANDS[p.band()][0], detail });
    }
    return out;
  }
}

// --------------------------------------------------------------- driver
/* Run a whole game with no human seats. Returns the final score table. */
function playOut(n, seed, opts) {
  const g = new Game(n, seed, Object.assign({ humans: [] }, opts || {}));
  let guard = 0;
  while (!g.finished() && guard++ < 200) {
    const it = g.playRound();
    let r = it.next();
    while (!r.done) r = it.next(null);      // no human seats: nothing to answer
  }
  return g;
}

/* ---------------- app/session.js --------------- */
/* A game of Blink played by people who are not in the same room.
 *
 * The whole design rests on one property the engine already has: a game is a
 * pure function of its seed, its options and the answers people gave. So a
 * session does not need to hold a board, a hand, or a map. It holds:
 *
 *     seed · options · who is sitting where · the list of answers
 *
 * Every client runs its own copy of the engine and stays in step by applying
 * the same answers in the same order. Nothing about the board crosses the
 * wire, which is why a session is a few hundred bytes and why reconnecting is
 * just "here is the list again".
 *
 * The server is still the authority, because trusting clients about whose turn
 * it is would be trusting them about everything. It replays the log, finds the
 * request the engine is waiting on, and accepts an answer only if:
 *
 *   - it comes from the player holding that seat,
 *   - it arrives at the step the log is actually at (so a double-click or a
 *     race cannot play the same card twice),
 *   - and the engine can decode it into a legal option.
 *
 * Undo is the same rule seen from the other side: a player may drop answers
 * back to the point where their own map turn began, and no further.
 *
 * This file has no idea what a WebSocket is. It is a set of functions over a
 * plain object, so it runs unchanged in a Cloudflare Durable Object, in a
 * throwaway node server, and inside a test with no sockets at all.
 */

const SESSION_PROTOCOL = 1;

/* Codes are read out loud and typed on phones, so: no vowels (no accidental
 * words), no 0/O or 1/I, and a dash in the middle to make it sayable. */
const CODE_ALPHABET = "23456789BCDFGHJKLMNPQRSTVWXYZ";
function makeCode(rand) {
  const r = rand || Math.random;
  let s = "";
  for (let i = 0; i < 8; i++) {
    if (i === 4) s += "-";
    s += CODE_ALPHABET[Math.floor(r() * CODE_ALPHABET.length)];
  }
  return s;
}

/* Somebody who has not typed a name still needs one on the table. */
const DEFAULT_NAMES = [
  "Wanderer", "Mason", "Navigator", "Cartographer", "Forager", "Shepherd",
  "Smith", "Miner", "Weaver", "Herald", "Sailor", "Astronomer",
];
function defaultName(rand, taken) {
  const r = rand || Math.random;
  const free = DEFAULT_NAMES.filter((n) => !(taken || []).includes(n));
  const pool = free.length ? free : DEFAULT_NAMES;
  return pool[Math.floor(r() * pool.length)];
}

function newSession(opts, rand) {
  const o = opts || {};
  const n = Math.min(4, Math.max(2, o.n || 3));
  return {
    protocol: SESSION_PROTOCOL,
    code: o.code || makeCode(rand),
    build: o.build || null,             // which commit the host was running
    created: new Date().toISOString(),
    touched: new Date().toISOString(),
    n,
    seed: o.seed === undefined ? Math.floor((rand || Math.random)() * 1e6) : o.seed,
    /* Everything the Game constructor takes except `humans`, which is derived
     * from who has actually claimed a seat when the host presses start. */
    rules: {
      trickRule: o.trickRule || "dock",
      deck: o.deck || "abc",
      objectives: o.objectives || "off",
      retireRule: o.retireRule || "lowest",
      researchRule: ["once", "twice", "escalating"].includes(o.researchRule)
        ? o.researchRule : "once",
      botStyle: "mixed",
      seatStyles: o.seatStyles || new Array(n).fill(null),
      botLevel: o.botLevel || "normal",
      comboMelds: !!o.comboMelds,
      friendsOf10: !!o.friendsOf10,
      growLimits: !!o.growLimits,
      /* Both of these change the board everyone is looking at, so they belong
       * to the TABLE and travel with the session — a guest whose client decided
       * these for itself would be replaying a different game. */
      meldScore: o.meldScore === "sum" ? "sum" : "count",
      aSumLadder: o.aSumLadder || null,
      layout: o.layout || null,
    },
    /* One entry per seat. `player` is null for a bot seat. */
    seats: new Array(n).fill(null).map((_, i) => ({ seat: i, player: null, name: null })),
    players: {},          // token -> {token, name, seat, joined, seen, gone}
    phase: "lobby",       // lobby -> playing -> over
    log: [],              // the answers, in order: this IS the game
    flags: [],
    started: null,
    ended: null,
  };
}

/* ---------------------------------------------------------------- joining */

function sessionJoin(s, req, rand) {
  const name = String((req && req.name) || "").trim().slice(0, 24);
  /* Coming back to a session you were already in must return you to YOUR
   * seat, not hand you a new one — a dropped phone is the common case. */
  if (req && req.token && s.players[req.token]) {
    const p = s.players[req.token];
    p.gone = false;
    p.seen = new Date().toISOString();
    if (name) { p.name = name; if (s.seats[p.seat]) s.seats[p.seat].name = name; }
    return { ok: true, player: p, rejoined: true };
  }
  if (s.phase !== "lobby")
    return { ok: false, why: "session.started" };
  const free = s.seats.filter((x) => x.player === null);
  if (!free.length) return { ok: false, why: "session.full" };
  const want = req && req.seat !== undefined && req.seat !== null
    ? s.seats.find((x) => x.seat === req.seat && x.player === null)
    : null;
  const spot = want || free[0];
  const token = (req && req.token) || makeCode(rand).replace("-", "") + makeCode(rand).replace("-", "");
  const taken = Object.values(s.players).map((x) => x.name);
  const p = { token, name: name || defaultName(rand, taken), seat: spot.seat,
              joined: new Date().toISOString(), seen: new Date().toISOString(), gone: false };
  s.players[token] = p;
  spot.player = token;
  spot.name = p.name;
  return { ok: true, player: p, rejoined: false };
}

function sessionLeave(s, token) {
  const p = s.players[token];
  if (!p) return false;
  p.gone = true;
  /* In the lobby, leaving frees the seat. Mid-game it does not: the seat is
   * still yours, the game is still waiting for you, and the link still works.
   * Dropping a player from a game in progress would leave a hole nobody can
   * fill without invalidating every answer already given. */
  if (s.phase === "lobby") {
    const spot = s.seats.find((x) => x.player === token);
    if (spot) { spot.player = null; spot.name = null; }
    delete s.players[token];
  }
  return true;
}

/* Seat swapping, while it is still free to do so. */
function sessionSit(s, token, seat) {
  if (s.phase !== "lobby") return { ok: false, why: "session.started" };
  const p = s.players[token];
  if (!p) return { ok: false, why: "session.unknown" };
  const spot = s.seats.find((x) => x.seat === seat);
  if (!spot) return { ok: false, why: "session.noSeat" };
  if (spot.player && spot.player !== token) return { ok: false, why: "session.seatTaken" };
  const old = s.seats.find((x) => x.player === token);
  if (old) { old.player = null; old.name = null; }
  spot.player = token; spot.name = p.name;
  p.seat = seat;
  return { ok: true };
}

function humanSeats(s) {
  return s.seats.filter((x) => x.player !== null).map((x) => x.seat);
}

function sessionStart(s, token) {
  if (s.phase !== "lobby") return { ok: false, why: "session.started" };
  const host = s.seats.find((x) => x.player !== null);
  if (!host || host.player !== token) return { ok: false, why: "session.notHost" };
  if (!humanSeats(s).length) return { ok: false, why: "session.nobody" };
  s.phase = "playing";
  s.started = new Date().toISOString();
  return { ok: true };
}

/* ------------------------------------------------------- running the game */

function gameArgs(s) {
  return { n: s.n, seed: s.seed,
           opts: Object.assign({ humans: humanSeats(s) }, s.rules) };
}

/* Replay the log in a fresh engine and stop at the request nobody has answered
 * yet. This is the server's whole model of "where are we" — it holds no board
 * between calls, because the log is the board. */
function sessionAdvance(s, Engine, upto) {
  const a = gameArgs(s);
  const g = new Engine.Game(a.n, a.seed, a.opts);
  const len = upto === undefined ? s.log.length : Math.min(upto, s.log.length);
  let it = g.playRound(), r = it.next(), i = 0, guard = 0;
  for (;;) {
    if (guard++ > 200000) return { g, req: null, i, overrun: true };
    if (r.done) {
      if (g.finished()) return { g, req: null, i, over: true };
      it = g.playRound(); r = it.next(); continue;
    }
    if (i >= len) return { g, req: r.value, i };
    r = it.next(decodeAnswer(g, r.value, s.log[i++]));
  }
}

/* ---- the codec ----
 *
 * An answer, in a form that survives its Game object. Cards are recorded by
 * WHERE they were rather than by what they were: the same replay puts the same
 * card in the same place, and two cards of one rank and suit are genuinely
 * interchangeable anyway.
 *
 * Both halves live here, together, because undo, the report and the server all
 * replay the same tokens — an encoder and a decoder that drift apart would
 * desynchronise a whole table and there would be nothing to see. */
function encodeAnswer(g, req, a) {
  if (a === null || a === undefined) return null;
  if (req.type === "turn") {
    const st = req.state, p = g.P[req.seat], o = { kind: a.kind };
    if (a.kind === "spend") { o.i = st.cards.indexOf(a.card); o.cell = a.cell; o.act = a.act; }
    else if (a.kind === "cash") o.i = st.cards.indexOf(a.card);
    /* `terrain` only appears on a landfall — a move onto a cell with no tile —
     * and it has to be carried, or a replay lays a different tile than the game
     * did and every board downstream of it disagrees. */
    else if (a.kind === "move") {
      o.src = a.src; o.dest = a.dest;
      if (a.terrain) o.terrain = a.terrain;
    }
    else if (a.kind === "fortify") o.cell = a.cell;
    else if (["colony", "conquest", "cashRow"].includes(a.kind)) o.i = p.vrow.indexOf(a.card);
    return o;
  }
  if (req.options) {
    const i = req.options.indexOf(a);
    if (i >= 0) return { pick: i };
  }
  return { raw: a };                      // a plain {cell, terrain} and the like
}

function decodeAnswer(g, req, tok) {
  if (tok === null || tok === undefined) return null;
  if (req.type === "turn") {
    const st = req.state, p = g.P[req.seat], k = tok.kind;
    if (k === "spend") return { kind: k, card: st.cards[tok.i], cell: tok.cell, act: tok.act };
    if (k === "cash") return { kind: k, card: st.cards[tok.i] };
    if (k === "move")
      return { kind: k, src: tok.src, dest: tok.dest, terrain: tok.terrain };
    if (k === "fortify") return { kind: k, cell: tok.cell };
    if (["colony", "conquest", "cashRow"].includes(k)) return { kind: k, card: p.vrow[tok.i] };
    return { kind: k };
  }
  if (tok.pick !== undefined) return req.options[tok.pick];
  return tok.raw;
}

/* Is this token something the engine could actually have been given here?
 * A client that sends nonsense must be refused rather than corrupting a log
 * that everybody else is replaying. */
function legalAnswer(g, req, tok) {
  if (tok === null || tok === undefined) return true;      // declining is legal
  if (typeof tok !== "object") return false;
  if (req.type === "turn") {
    const kinds = ["spend", "cash", "move", "fortify", "research", "colony",
                   "conquest", "cashRow", "end"];
    if (!kinds.includes(tok.kind)) return false;
    const st = req.state, p = g.P[req.seat];
    if (tok.kind === "spend" || tok.kind === "cash")
      return Number.isInteger(tok.i) && tok.i >= 0 && tok.i < st.cards.length;
    if (["colony", "conquest", "cashRow"].includes(tok.kind))
      return Number.isInteger(tok.i) && tok.i >= 0 && tok.i < p.vrow.length;
    return true;
  }
  if (tok.pick !== undefined)
    return Number.isInteger(tok.pick) && req.options
      && tok.pick >= 0 && tok.pick < req.options.length;
  return "raw" in tok;
}

/* An answer from a player. `step` is the log length the client believed it was
 * answering at — the guard against a double tap and against two clients
 * answering the same request. */
function sessionAnswer(s, Engine, token, step, tok) {
  if (s.phase !== "playing") return { ok: false, why: "session.notPlaying" };
  const p = s.players[token];
  if (!p) return { ok: false, why: "session.unknown" };
  if (step !== s.log.length) return { ok: false, why: "session.stale", step: s.log.length };
  const at = sessionAdvance(s, Engine);
  if (!at.req) {
    if (at.over) { s.phase = "over"; s.ended = new Date().toISOString(); }
    return { ok: false, why: "session.noRequest" };
  }
  if (at.req.seat !== p.seat) return { ok: false, why: "session.notYourTurn" };
  if (!legalAnswer(at.g, at.req, tok)) return { ok: false, why: "session.illegal" };
  /* Belt and braces, because the log is shared. `legalAnswer` above refuses
   * the malformed tokens we can name, cleanly; this catches the ones we
   * cannot. Both are needed and they are not the same thing: a server that
   * merely survives bad input has no idea it received any, and an exception
   * inside a Durable Object takes the whole session down with it. Applied,
   * then rolled back if it does not survive. */
  s.log.push(tok);
  let after;
  try { after = sessionAdvance(s, Engine); }
  catch (e) { s.log.pop(); return { ok: false, why: "session.threw" }; }
  s.touched = new Date().toISOString();
  if (!after.req && after.over) { s.phase = "over"; s.ended = new Date().toISOString(); }
  return { ok: true, step, by: p.seat, phase: s.phase };
}

/* Where the acting seat's own map turn began — the same limit the local game
 * enforces, worked out here from the log rather than remembered.
 *
 * `bonus`, `discard` and `setaside` are on this list because they happen INSIDE
 * the acting seat's own block, immediately before the map turn: the trick has
 * resolved, it is your turn, and the first thing you are asked is which card to
 * spend or give up. Leaving them off did two things, and the second is worse
 * than the first:
 *
 *   1. the choice itself could not be taken back — and picking which card
 *      leaves your hand is exactly the kind of decision a player wants back;
 *   2. it moved the floor. An unlisted request set the block to null, so the
 *      `turn` that followed looked like a NEW block and re-marked the floor
 *      after the answer already given. Everything before it in the same turn
 *      became unreachable, and the player simply found undo dead for no reason
 *      they could see.
 *
 * `feed` is deliberately NOT here: it belongs to the recycle at the end of the
 * round, not to anyone's turn, and by then the round it would rewind into has
 * been seen by everybody. */
const TURN_REQ = ["turn", "waterexplore", "conquest", "retire", "buy", "colony",
                  "bonus", "discard", "setaside"];
function undoFloor(s, Engine, seat) {
  const a = gameArgs(s);
  const g = new Engine.Game(a.n, a.seed, a.opts);
  let it = g.playRound(), r = it.next(), i = 0, guard = 0;
  let block = null, mark = null;
  for (;;) {
    if (guard++ > 200000) break;
    if (r.done) {
      if (g.finished()) break;
      it = g.playRound(); r = it.next(); continue;
    }
    const q = r.value;
    if (q.seat === seat && TURN_REQ.includes(q.type)) {
      const key = g.round + ":" + q.seat;
      if (key !== block) { block = key; mark = i; }
    } else if (q.seat === seat) {
      block = null;
    }
    if (i >= s.log.length) break;
    r = it.next(decodeAnswer(g, q, s.log[i++]));
  }
  return block === null ? null : mark;
}

function sessionUndo(s, Engine, token, step) {
  if (s.phase !== "playing") return { ok: false, why: "session.notPlaying" };
  const p = s.players[token];
  if (!p) return { ok: false, why: "session.unknown" };
  const at = sessionAdvance(s, Engine);
  if (!at.req || at.req.seat !== p.seat) return { ok: false, why: "session.notYourTurn" };
  const floor = undoFloor(s, Engine, p.seat);
  if (floor === null || s.log.length <= floor) return { ok: false, why: "session.noUndo" };
  const to = step === undefined ? s.log.length - 1 : step;
  if (to < floor || to >= s.log.length) return { ok: false, why: "session.noUndo" };
  s.log.length = to;
  s.touched = new Date().toISOString();
  return { ok: true, step: to };
}

function sessionFlag(s, token, flag) {
  const p = s.players[token];
  if (!p) return { ok: false, why: "session.unknown" };
  const f = Object.assign({}, flag, { seat: p.seat, name: p.name,
                                      step: s.log.length,
                                      at: new Date().toISOString() });
  if (typeof f.note === "string") f.note = f.note.slice(0, 800);
  s.flags.push(f);
  return { ok: true, flag: f };
}

/* Everything a client needs to build the game from nothing. Tokens are secret,
 * so they never appear here. */
function sessionState(s, forToken) {
  return {
    protocol: s.protocol,
    code: s.code,
    n: s.n,
    seed: s.seed,
    rules: s.rules,
    phase: s.phase,
    seats: s.seats.map((x) => ({
      seat: x.seat,
      name: x.name,
      taken: x.player !== null,
      here: x.player !== null && s.players[x.player] && !s.players[x.player].gone,
      you: !!forToken && x.player === forToken,
    })),
    host: (s.seats.find((x) => x.player !== null) || {}).seat,
    humans: humanSeats(s),
    log: s.log,
    flags: s.flags.length,
    created: s.created,
  };
}

/* ------------------------------------------------------- one message in
 *
 * The protocol, in one place. Both servers — the Durable Object and the
 * throwaway node one — are pure transport around this function, because two
 * implementations of "who may do what" is one too many, and the one that
 * would drift is the one nobody tests.
 *
 * Returns what to say and to whom: `self` goes back down the socket that
 * spoke, `all` goes to everybody, and `state: true` means "fill in the state
 * message per recipient", since which seat is *you* depends on who is asked.
 */
function sessionHandle(s, Engine, ctx, msg) {
  const token = ctx.token;
  /* `ok` is not for the client — it tells the STORE whether the session
   * changed. A refusal changes nothing, so it must not be written back, and
   * under contention refusals are the common case. */
  const err = (why) => ({ ok: false, to: [{ who: "self", msg: { t: "error", why } }] });
  if (!msg || typeof msg.t !== "string") return err("session.badMessage");

  switch (msg.t) {
    case "hello": {
      const r = sessionJoin(s, { name: msg.name, seat: msg.seat, token: msg.token });
      if (!r.ok) return err(r.why);
      return {
        ok: true,
        token: r.player.token,
        /* The token is how a dropped phone gets its seat back, so it goes to
         * that player and to nobody else. */
        to: [{ who: "self", msg: { t: "welcome", token: r.player.token,
                                   seat: r.player.seat, name: r.player.name,
                                   rejoined: r.rejoined, state: true } },
             { who: "all", msg: { t: "seats", state: true } }],
      };
    }
    case "sit": {
      const r = sessionSit(s, token, msg.seat);
      if (!r.ok) return err(r.why);
      return { ok: true, to: [{ who: "all", msg: { t: "seats", state: true } }] };
    }
    case "start": {
      const r = sessionStart(s, token);
      if (!r.ok) return err(r.why);
      return { ok: true, to: [{ who: "all", msg: { t: "start", state: true } }] };
    }
    case "answer": {
      const r = sessionAnswer(s, Engine, token, msg.step, msg.token);
      if (!r.ok) {
        /* A stale answer is not something a player should be told off for —
         * it is a double tap, or two messages that crossed. Send the truth
         * back and let the client resynchronise silently. */
        if (r.why === "session.stale")
          return { ok: false, to: [{ who: "self", msg: { t: "sync", state: true } }] };
        return err(r.why);
      }
      return { ok: true, to: [{ who: "all", msg: { t: "answer", step: r.step, token: msg.token,
                                                  by: r.by, phase: s.phase } }] };
    }
    case "undo": {
      const r = sessionUndo(s, Engine, token, msg.step);
      if (!r.ok) return err(r.why);
      return { ok: true, to: [{ who: "all", msg: { t: "undo", step: r.step } }] };
    }
    case "flag": {
      const r = sessionFlag(s, token, msg.flag || {});
      if (!r.ok) return err(r.why);
      return { ok: true, to: [{ who: "self", msg: { t: "flagged", flag: r.flag } }] };
    }
    case "sync":
      return { ok: false, to: [{ who: "self", msg: { t: "sync", state: true } }] };
    case "ping":
      return { ok: false, to: [{ who: "self", msg: { t: "pong", at: Date.now() } }] };
    default:
      return err("session.unknownMessage");
  }
}

const SESSION = { sessionState, sessionHandle, sessionLeave, newSession };
/* ---------------- server/store.js -------------- */
/* Where a table lives, and how everyone at it hears about a move.
 *
 * On Cloudflare a Durable Object was both of these for free: one object per
 * session, single writer, sockets attached. Vercel gives neither. A connection
 * is pinned to one function instance, but new connections are not — so two
 * people at one table can easily be talking to two different instances, and a
 * deployment splits them again. Two things follow:
 *
 *   1. The session cannot live in a variable. It goes in a store.
 *   2. A broadcast has to leave the process. It goes over pub/sub.
 *
 * And one thing that was free now has to be earned: **two players answering at
 * the same instant.** A Durable Object serialises writes. Redis does not, so
 * two instances could both read a log of length 14 and both write 15 — the
 * second silently erasing the first. The `step` guard in session.js *detects*
 * a stale answer but cannot prevent a lost update, because by then both reads
 * have already happened. So every change goes through `update()`, which is a
 * compare-and-set with a retry, and the whole rest of the codebase carries on
 * knowing nothing about any of it.
 *
 * Two implementations, one interface:
 *
 *   memoryStore()  — a Map. For the dev server and the tests.
 *   redisStore(url) — for Vercel. Needs `redis` (or any node-redis-compatible
 *                     client); the marketplace add-on supplies the URL.
 *
 * What it costs, because the point of a free tier is not paying for a
 * prototype. A move is three commands — one GET, one compare-and-set, one
 * publish — and an instance holds two connections, not one per move.
 * store_test.js counts both and fails if they grow: the day this quietly
 * becomes five commands is the day the allowance runs out in a fortnight
 * instead of a year.
 *
 * The store is deliberately NOT where anything valuable lives. A free Redis
 * is RAM only — no persistence, no failover. Losing a table in progress on a
 * restart is a shrug: every client is holding the same log, and the seats
 * come back with them. Losing a playtest report would not be a shrug, so
 * reports are not kept here.
 */

const KEY = (code) => `blink:session:${code}`;
const CHAN = (code) => `blink:room:${code}`;
const TTL_SECONDS = 60 * 60 * 24 * 2;      // a table nobody returns to expires

/* Write only if the value is still the one we read. Comparing the whole
 * previous string rather than keeping a version counter means the session
 * stays a single key with nothing to hold in step — a table is about a
 * kilobyte, and a kilobyte of argument is cheaper than a second key that can
 * go stale. */
const CAS_SCRIPT = `
if redis.call('GET', KEYS[1]) ~= ARGV[1] then return 0 end
redis.call('SET', KEYS[1], ARGV[2], 'EX', tonumber(ARGV[3]))
return 1`;

/* ------------------------------------------------------------- in memory */

function memoryStore() {
  const rooms = new Map();                 // code -> {s, listeners:Set}
  const room = (code) => {
    if (!rooms.has(code)) rooms.set(code, { s: null, listeners: new Set() });
    return rooms.get(code);
  };
  return {
    kind: "memory",
    raw: null,                             // nowhere to keep a report on a laptop
    async create(s) { room(s.code).s = s; return s; },
    async get(code) { return room(code).s; },
    /* Single-threaded node: read-modify-write cannot be interleaved here, so
     * the retry loop the Redis version needs is simply absent. */
    async update(code, fn) {
      const r = room(code);
      if (!r.s) return { ok: false, why: "session.unknown" };
      const out = fn(r.s);
      return out;
    },
    async publish(code, msg) {
      for (const f of room(code).listeners) { try { f(msg); } catch (e) { /* gone */ } }
    },
    async subscribe(code, fn) {
      const r = room(code);
      r.listeners.add(fn);
      return () => r.listeners.delete(fn);
    },
    async close() { rooms.clear(); },
    _rooms: rooms,
  };
}

/* ----------------------------------------------------------------- redis */

/* `client` and `sub` are separate connections on purpose: a Redis client in
 * subscribe mode cannot run ordinary commands. */
function redisStore(client, sub) {
  const listeners = new Map();             // code -> Set(fn)
  let wired = false;

  function wire() {
    if (wired) return;
    wired = true;
    sub.on("message", (chan, payload) => {
      const set = listeners.get(chan);
      if (!set) return;
      let msg = null;
      try { msg = JSON.parse(payload); } catch (e) { return; }
      for (const f of set) { try { f(msg); } catch (e) { /* gone */ } }
    });
  }

  return {
    kind: "redis",
    /* The plain client, for the few things that are not sessions. Note what
     * is NOT here: a free Redis has no persistence, so nothing that would be
     * missed after a restart may be kept in it. */
    raw: client,

    async create(s) {
      await client.set(KEY(s.code), JSON.stringify(s), { EX: TTL_SECONDS });
      return s;
    },

    async get(code) {
      const raw = await client.get(KEY(code));
      return raw ? JSON.parse(raw) : null;
    },

    /* Compare-and-set, in two commands.
     *
     * The obvious way is WATCH/MULTI/EXEC, and the first version did that. It
     * costs five commands and a fresh connection per move — a WATCH cannot be
     * shared between two overlapping updates in one process — and on a free
     * tier capped at thirty connections, a connection per move is not a cost,
     * it is an outage.
     *
     * This is a GET and then a script that writes only if nobody else has.
     * Two commands, atomic by definition (a Lua script is one operation to
     * Redis), no connection churn, and the same guarantee: two instances
     * cannot both append to the log, because the second one's compare fails
     * and it redoes its work against what actually happened.
     *
     * A refusal writes nothing at all, and under contention refusals are the
     * common case. */
    async update(code, fn, tries) {
      const limit = tries || 20;
      for (let i = 0; i < limit; i++) {
        const raw = await client.get(KEY(code));
        if (!raw) return { ok: false, why: "session.unknown" };
        const s = JSON.parse(raw);
        const out = fn(s);
        if (!out || out.ok === false) return out;
        const won = await client.eval(CAS_SCRIPT, {
          keys: [KEY(code)],
          arguments: [raw, JSON.stringify(s), String(TTL_SECONDS)],
        });
        if (Number(won) === 1) return out;
        // somebody else got there first: read again and redo the work
      }
      return { ok: false, why: "session.busy" };
    },

    async publish(code, msg) {
      await client.publish(CHAN(code), JSON.stringify(msg));
    },

    async subscribe(code, fn) {
      wire();
      const chan = CHAN(code);
      if (!listeners.has(chan)) {
        listeners.set(chan, new Set());
        await sub.subscribe(chan);
      }
      listeners.get(chan).add(fn);
      return async () => {
        const set = listeners.get(chan);
        if (!set) return;
        set.delete(fn);
        if (!set.size) { listeners.delete(chan); try { await sub.unsubscribe(chan); } catch (e) { /* */ } }
      };
    },

    async close() {
      try { await sub.quit(); } catch (e) { /* */ }
      try { await client.quit(); } catch (e) { /* */ }
    },
  };
}

/* Pick one from the environment. No REDIS_URL means the memory store, which is
 * exactly right on a laptop and exactly wrong on Vercel — so the Vercel entry
 * point says so loudly rather than half-working. */
async function storeFromEnv(env) {
  const url = (env || process.env).REDIS_URL || (env || process.env).KV_URL || null;
  if (!url) return memoryStore();
  let createClient;
  try { ({ createClient } = require("redis")); }
  catch (e) { throw new Error("REDIS_URL is set but the `redis` package is not installed"); }
  const client = createClient({ url });
  const sub = client.duplicate();
  await client.connect();
  await sub.connect();
  return redisStore(client, sub);
}

/* ---------------- server/hub.js ---------------- */
/* The sockets in *this* process, and how they hear about everyone else's.
 *
 * Every server — the node dev one, the Vercel function, and anything later —
 * is this file plus a way of getting a socket. It owns three things and no
 * more:
 *
 *   1. which local sockets belong to which table, and who each one is;
 *   2. running a message through `sessionHandle` inside the store's
 *      compare-and-set, so two people answering at the same instant cannot
 *      erase each other;
 *   3. turning a `who: "all"` into something that reaches players on OTHER
 *      instances, which on Vercel is most of them.
 *
 * A broadcast carries the session with it. The alternative — publish the
 * message, then have every instance read the store to fill in each player's
 * view — is an extra round trip per recipient per move, and it can race with
 * the next write and show somebody a board one move ahead of the message that
 * describes it. The session is about a kilobyte. Send it.
 *
 * A socket here is anything with `send(string)`. That is the whole interface,
 * which is why the same file runs under `ws`, under Vercel's upgrade API, and
 * in a test with no sockets at all.
 */


const E = { Game };
const S = SESSION;

function createHub(store) {
  /* code -> { socks: Map(sock -> token), off: () => void } */
  const rooms = new Map();

  const post = (sock, msg) => {
    try { sock.send(JSON.stringify(msg)); } catch (e) { /* gone */ }
  };
  /* `state: true` is a promise to fill in the view for whoever is being told —
   * which seat is "you" depends on the reader. */
  const fill = (msg, s, token) => (msg.state === true
    ? Object.assign({}, msg, { state: S.sessionState(s, token) })
    : msg);

  async function room(code) {
    if (rooms.has(code)) return rooms.get(code);
    const r = { socks: new Map(), off: null };
    rooms.set(code, r);
    /* Everything published for this table — by us or by another instance —
     * is delivered to whichever of its players happen to be here. */
    r.off = await store.subscribe(code, ({ msg, session }) => {
      for (const [sock, token] of r.socks) post(sock, fill(msg, session, token));
    });
    return r;
  }

  return {
    store,

    async open(code, sock) {
      const r = await room(code);
      r.socks.set(sock, null);
      return r;
    },

    /* A socket going away is not a player going away: in the lobby the seat is
     * freed, mid-game it is kept, and session.js is the one that knows the
     * difference. */
    async close(code, sock) {
      const r = rooms.get(code);
      if (!r) return;
      const token = r.socks.get(sock);
      r.socks.delete(sock);
      if (token) {
        const out = await store.update(code, (s) => {
          const was = S.sessionState(s);
          S.sessionLeave(s, token);
          return { ok: JSON.stringify(was) !== JSON.stringify(S.sessionState(s)), s };
        });
        if (out && out.ok) {
          const s = await store.get(code);
          if (s) await store.publish(code, { msg: { t: "seats", state: true }, session: s });
        }
      }
      /* The last socket here stops listening. On Vercel this matters: an
       * instance holding a subscription for a table nobody on it is playing
       * is paying to hear about a game it cannot show anyone. */
      if (!r.socks.size) {
        rooms.delete(code);
        if (r.off) { try { await r.off(); } catch (e) { /* */ } }
      }
    },

    async handle(code, sock, msg) {
      const r = rooms.get(code);
      if (!r) return;
      let session = null;
      const out = await store.update(code, (s) => {
        const res = S.sessionHandle(s, E, { token: r.socks.get(sock) }, msg);
        session = s;                 // the state as of this change, for the fan-out
        return res;
      });
      if (!out) return;
      if (out.why && !out.to) return post(sock, { t: "error", why: out.why });
      if (out.token) r.socks.set(sock, out.token);
      if (!session) session = await store.get(code);
      if (!session) return post(sock, { t: "error", why: "session.unknown" });

      for (const step of out.to || []) {
        if (step.who === "self") post(sock, fill(step.msg, session, r.socks.get(sock)));
        /* Published rather than looped over locally, even when everybody at
         * this table happens to be on this instance — one path, so the
         * multi-instance case is the one that gets exercised. */
        else await store.publish(code, { msg: step.msg, session });
      }
    },

    /* For a server that wants to make one before anybody connects. */
    async create(opts) {
      const s = S.newSession(opts);
      await store.create(s);
      return s;
    },

    async get(code) { return store.get(code); },

    /* How many sockets this process is holding, for a health route. */
    get size() { return rooms.size; },
    _rooms: rooms,
  };
}

/* ---------------- server/vercel.src.js --------- */
/* The session service as a Vercel Function.
 *
 * Vercel serves WebSockets by letting a function export an http server, and
 * pins each connection to the instance that accepted it. What it does not give
 * you is a home for the table: a *new* connection may land anywhere, and a
 * deployment splits old connections from new ones. So both of the things a
 * Durable Object handed us for free are done explicitly here — the session
 * lives in Redis, and a broadcast goes out over pub/sub — and neither
 * `session.js` nor the client knows or cares.
 *
 * One consequence worth stating plainly: **Vercel closes a WebSocket when the
 * function hits its maximum duration.** Every table will therefore be dropped
 * periodically, whatever anyone does. That is survivable only because the
 * client already treats reconnection as normal rather than exceptional: it
 * keeps its player token, backs off, and rebuilds the whole game from the log
 * it is handed on the way back in. The same path a phone takes into a tunnel.
 *
 * Routes, all under /api so they sit on the same origin as the play page —
 * which means no CORS, no second domain, and one `git push` to ship both:
 *
 *   POST /api/blink/session          open a table
 *   GET  /api/blink/session/:code    its state, before connecting
 *   GET  /api/blink/session/:code/ws the socket
 *   POST /api/blink/report           a playtest report
 *
 * Generated into one file by server/build.js. Do not edit the generated copy.
 */

const http = require("http");

let WebSocketServer = null;
try { ({ WebSocketServer } = require("ws")); }
catch (e) { /* reported on the first upgrade rather than at import time */ }

/* One hub per instance, made once and kept for the life of it. */
let hubPromise = null;
function getHub() {
  if (!hubPromise) {
    hubPromise = storeFromEnv(process.env).then((store) => {
      if (store.kind === "memory" && process.env.VERCEL)
        console.warn("blink: no REDIS_URL — players on different instances will "
          + "not see each other. Add a Redis and set REDIS_URL.");
      return createHub(store);
    });
  }
  return hubPromise;
}

const JSONH = { "content-type": "application/json" };
const reply = (res, code, body) => {
  res.writeHead(code, JSONH);
  res.end(JSON.stringify(body));
};
const readBody = (req) => new Promise((ok) => {
  let b = "";
  req.on("data", (c) => { b += c; if (b.length > 4e6) req.destroy(); });
  req.on("end", () => { try { ok(JSON.parse(b || "{}")); } catch (e) { ok({}); } });
});

/* Everything after /api/blink, so the same file works whatever the function is
 * mounted as. */
function route(url) {
  return url.pathname.replace(/^\/api\/blink/, "").replace(/\/+$/, "") || "/";
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  const p = route(url);
  try {
    const hub = await getHub();

    if (p === "/" || p === "/health")
      return reply(res, 200, { ok: true, service: "blink-sessions",
                               protocol: SESSION_PROTOCOL, store: hub.store.kind });

    if (p === "/session" && req.method === "POST") {
      const s = await hub.create(await readBody(req));
      return reply(res, 200, { ok: true, code: s.code, state: sessionState(s) });
    }

    const m = p.match(/^\/session\/([A-Za-z0-9-]{4,12})$/);
    if (m) {
      const s = await hub.get(m[1].toUpperCase());
      if (!s) return reply(res, 404, { ok: false, why: "session.unknown" });
      return reply(res, 200, { ok: true, state: sessionState(s) });
    }

    /* Reports are written by whoever finished a game, and read by nobody
     * without the key: they carry names and free text people wrote for the
     * designer, not for the internet. */
    if (p === "/report" && req.method === "POST") {
      const rep = await readBody(req);
      if (!rep || !rep.schema) return reply(res, 400, { ok: false, why: "not a report" });
      const stored = await putReport(hub.store, rep);
      return reply(res, 200, { ok: true, id: rep.id, stored });
    }
    if (p === "/reports" || p.startsWith("/report/")) {
      if (!process.env.ADMIN_KEY || url.searchParams.get("key") !== process.env.ADMIN_KEY)
        return reply(res, 403, { ok: false, why: "not yours" });
      return reply(res, 200, await getReports(hub.store, p, url));
    }

    return reply(res, 404, { ok: false, why: "no such route" });
  } catch (e) {
    return reply(res, 500, { ok: false, why: "server error", detail: String(e && e.message) });
  }
});

/* ---- the socket -------------------------------------------------------- */

const wss = WebSocketServer ? new WebSocketServer({ noServer: true }) : null;

server.on("upgrade", async (req, socket, head) => {
  if (!wss) { socket.destroy(); return; }
  const url = new URL(req.url, "http://x");
  const m = route(url).match(/^\/session\/([A-Za-z0-9-]{4,12})\/ws$/);
  const code = m && m[1].toUpperCase();
  if (!code) { socket.destroy(); return; }
  let hub;
  try {
    hub = await getHub();
    if (!(await hub.get(code))) { socket.destroy(); return; }
  } catch (e) { socket.destroy(); return; }

  wss.handleUpgrade(req, socket, head, async (ws) => {
    await hub.open(code, ws);
    ws.on("message", (data) => {
      let msg = null;
      try { msg = JSON.parse(data.toString()); }
      catch (e) { return ws.send(JSON.stringify({ t: "error", why: "bad json" })); }
      hub.handle(code, ws, msg).catch(() => {
        try { ws.send(JSON.stringify({ t: "error", why: "server error" })); } catch (x) { /* */ }
      });
    });
    const drop = () => hub.close(code, ws).catch(() => {});
    ws.on("close", drop);
    ws.on("error", drop);
  });
});

/* ---- reports -----------------------------------------------------------
 *
 * A free Redis is RAM only: no persistence, no failover. A table in progress
 * can survive being lost — every client is holding the same log — but a
 * playtest report cannot. Somebody spent an evening on that and wrote three
 * sentences at the end of it, and losing it to a maintenance restart would be
 * indefensible.
 *
 * So reports go to Blob storage if the project has any, and if it has none
 * the route says so plainly and the page falls back to downloading the file
 * for the player to send on. The one thing it must never do is accept a
 * report, say "thank you", and drop it.
 */

async function putReport(store, rep) {
  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token) return false;                     // the page will download it instead
  let put;
  try { ({ put } = require("@vercel/blob")); }
  catch (e) { return false; }
  const key = `blink/reports/${(rep.build && rep.build.commit) || "unknown"}/`
    + `${(rep.started || "").slice(0, 10)}/${rep.id || Date.now()}.json`;
  await put(key, JSON.stringify(rep), {
    access: "public",                 // unguessable URL; the listing needs the key
    contentType: "application/json",
    token,
    addRandomSuffix: true,
  });
  return true;
}

async function getReports(store, p, url) {
  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token) return { ok: false, why: "no report store bound" };
  let list;
  try { ({ list } = require("@vercel/blob")); }
  catch (e) { return { ok: false, why: "no report store bound" }; }
  const prefix = "blink/reports/" + (url.searchParams.get("commit") || "");
  const out = await list({ prefix, limit: 500, token });
  return { ok: true, reports: out.blobs.map((b) => ({
    key: b.pathname, size: b.size, at: b.uploadedAt, url: b.url })) };
}

/* Vercel runs this by taking whatever the file exports and, if it is an http
 * server, serving it. Truncating the file while editing once removed these two
 * lines, and the deployment's only symptom was FUNCTION_INVOCATION_FAILED with
 * no stack — hence vercel_test.js, which loads the built file the way the
 * platform does and checks there is something here with a `.listen` on it. */
module.exports = server;
module.exports.default = server;
