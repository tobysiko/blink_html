/* Blink v0.22 — playable client.
 *
 * The engine yields a request whenever a human seat must decide; this file
 * renders that request and feeds the answer back. Nothing here knows the
 * rules: every legal option on screen came out of the engine.
 *
 * The map phase is a single persistent `turn` request. The engine hands back
 * everything still legal after each action, so the player takes them in any
 * order and presses End turn when done.
 */

const TC = { plains: "#C9992B", forest: "#37704A", ocean: "#256A8C", mountain: "#8A837A" };
/* Names are looked up, not stored: they change with the language. */
const TL = new Proxy({}, { get: (_, k) => t("terrain." + String(k)) });
const seatName = (i) => t("seat." + i);
const tierName = (j) => t("tier." + j);
const styleName = (k) => t("style." + k);
const styleNote = (k) => t("style." + k + ".note");
/* Card effect text, in the reader's language, falling back to the engine's
 * English — which is the text printed on the physical card. */
const fxBand = (r) => bandOfRank(r);
function fxText(r) {
  const b = fxBand(r);
  const out = { a: t("fx.a." + b), aShort: t("fx.aShort." + b),
                b: t("fx.b." + b), bShort: t("fx.bShort." + b),
                c: t("fx.c." + b), cShort: t("fx.cShort." + b) };
  /* When the trick is won on total rank, A does something else entirely and the
   * card has to say so — a face still reading "+1 card" while the rule counts
   * totals is the game lying to the player at the moment they choose. The
   * number comes from the ladder the game is running, not from the string. */
  if (G && G.MELD_SCORE === "sum") {
    const [add, ties] = effectASum(r, G.A_SUM_LADDER);
    out.a = t(ties ? "fx.aSum.ties" : "fx.aSum", { n: add });
    out.aShort = t(ties ? "fx.aSumShort.ties" : "fx.aSumShort", { n: add });
  }
  return out;
}
function fxTextD(r) {
  const b = fxBand(r);
  return { d: t("fx.d." + b), dShort: t("fx.dShort." + b) };
}
const objName = (o) => t("obj." + o.id + ".name");
const objFlavour = (o) => t("obj." + o.id + ".flavour");
/* Brightened from the components' crimson/azure/violet/olive: a unit has to
 * read against its own terrain, and Azure-on-ocean and Olive-on-forest were
 * invisible at the printed values. */
const SEAT_C = ["#D6453A", "#3E9BD1", "#9370CE", "#86BE45"];
const SEAT_N = new Proxy({}, { get: (_, k) => t("seat." + String(k)) });
const ACT_LABEL = new Proxy({}, { get: (_, k) => t("hex." + String(k)) });

let G = null, IT = null, REQ = null;
/* ME is the seat whose hand and board are on screen. With one person that is
 * fixed; with several it follows whoever is being asked; with none it is just
 * a vantage point. */
let ME = 0;
let HUMANS = [0];              // seats a person plays
let PASSED = 0;                // the seat the device was last handed to
let PENDING_SEAT = null;       // waiting behind the pass gate
/* ---- how big the board is drawn ----
 * Pixels per engine unit; a hex is 30 units of radius, so it measures
 * 52 x 60 units. The old fixed 0.5 drew 26 x 30 px hexes — fine for a mouse on
 * a six-tile opening board, too small to hit with a thumb, and it kept
 * shrinking as the map grew until nothing was clickable.
 *
 * Now the scale FITS the board but is clamped to a range that stays usable:
 * never smaller than a hex you can hit, never so large that six tiles fill a
 * laptop. When the board no longer fits at the minimum, the map is panned
 * instead of shrunk. */
const ZOOM_MIN = 0.72;                // 37 x 43 px — the smallest honest target
const ZOOM_MAX = 1.10;                // 57 x 66 px — no bigger than a real tile
const ZOOM_FLOOR = 0.28, ZOOM_CEIL = 2.0;   // what the +/- buttons allow
let ZOOM = null;                      // null = auto-fit inside [MIN, MAX]
let PAN = { x: 0, y: 0 };             // engine units away from the board's centre
let MAPGEO = null;                    // last measured board + viewport, for panning
/* The research action is four steps deep, so the client tracks where it is and
 * what has happened so far. Kept outside SEL because answer() clears SEL. */
let RESEARCH = null;
let REP = null;                // the playtest record for the game in progress
let SEL = blankSel();
function blankSel() {
  return { meld: [], card: null, mode: null, moveSrc: null, vcard: null,
           waterCell: null, colonyCell: null };
}

const $ = (s) => document.querySelector(s);
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
};
const cardSortUI = (a, b) => a.r - b.r || a.s.localeCompare(b.s);

// --------------------------------------------------------------- setup
/* Which of a radio group is chosen. */
function radioValue(groupSel, fallback) {
  const on = document.querySelector(`${groupSel} input:checked`);
  return on ? on.value : fallback;
}
const playerCount = () => Number(radioValue("#n-players", 3));

/* One row per seat: a colour, a name, and what sits there — you, or a named
 * bot, or "auto" for whatever the mixed bag deals it. Rebuilt whenever the
 * player count or the language changes. */
function renderSeats() {
  const box = $("#seats");
  if (!box) return;
  const n = playerCount();
  const was = {};
  box.querySelectorAll("select").forEach((sel) => { was[sel.dataset.seat] = sel.value; });
  let s = "";
  for (let i = 0; i < n; i++) {
    const id = `seat-${i}`;
    const chosen = was[i] !== undefined ? was[i] : (i === 0 ? "you" : "auto");
    const opts = [`<option value="you">${t("setup.seat.you")}</option>`,
                  `<option value="auto">${t("setup.seat.auto")}</option>`]
      .concat(STYLE_KEYS.map((k) =>
        `<option value="${k}">${t("setup.seat.bot", { style: styleName(k) })}</option>`));
    s += `<div class="seatrow${chosen === "you" ? " human" : ""}">
      <span class="dot" style="background:${SEAT_C[i]}" aria-hidden="true"></span>
      <label class="who" for="${id}">${seatName(i)}</label>
      <select id="${id}" data-seat="${i}">${opts.join("")}</select>
    </div>`;
  }
  box.innerHTML = s;
  box.querySelectorAll("select").forEach((sel) => {
    const i = sel.dataset.seat;
    sel.value = was[i] !== undefined ? was[i] : (Number(i) === 0 ? "you" : "auto");
    sel.addEventListener("change", () => {
      sel.closest(".seatrow").classList.toggle("human", sel.value === "you");
      seatsNote();
    });
  });
  seatsNote();
}

/* Say what the current arrangement means, because "nobody is you" and "three
 * of you" are both legal and neither is obvious. */
function seatsNote() {
  const note = $("#seats-note");
  if (!note) return;
  const humans = seatSelections().humans;
  note.textContent = humans.length === 0 ? t("setup.seats.watch")
    : humans.length === 1 ? t("setup.seats.one")
    : t("setup.seats.hot", { n: humans.length });
}

function seatSelections() {
  const humans = [], styles = [];
  for (let i = 0; i < playerCount(); i++) {
    const sel = $(`#seat-${i}`);
    const v = sel ? sel.value : (i === 0 ? "you" : "auto");
    if (v === "you") { humans.push(i); styles.push(null); }
    else styles.push(v === "auto" ? null : v);
  }
  return { humans, styles };
}

/* Who is sitting where, in the report's terms. Names arrive later when a game
 * is played remotely; locally a seat is "you" or the style it was dealt. */
function seatRoster(styles, humans) {
  const out = [];
  for (let i = 0; i < playerCount(); i++)
    out.push({ seat: i, kind: humans.includes(i) ? "human" : "bot",
               style: humans.includes(i) ? null : (styles[i] || "auto"),
               name: null });
  return out;
}

/* The player board layout the setup page is asking for: a preset name, or the
 * custom column typed into the box. Returns null for the printed default so a
 * normal game's options look exactly as they always did — which keeps old
 * reports and session logs comparable. */
function chosenLayout() {
  const pick = $("#layout") ? $("#layout").value : "late";
  if (pick === "custom") {
    const raw = ($("#layout-custom") ? $("#layout-custom").value : "").trim();
    /* An unreadable column falls back rather than starting a game whose board
     * nobody can describe. The hint under the box has already said so. */
    return parseLayout(raw) ? raw : null;
  }
  /* Always named, never null. This used to send null for "rulebook", meaning
     "whatever the engine defaults to" — which was the same board right up until
     v0.23 moved the default to 2/3/5/5/5, at which point asking for the v0.22
     board would silently have handed you the new one. A preset says its name. */
  return pick;
}

/* Effect A's ladder only means anything when the trick is won on total rank,
 * so the control is hidden under the printed rule rather than sitting there
 * doing nothing. */
function syncALadderRow() {
  const row = $("#a-ladder-row"), sel = $("#meld-score");
  if (row && sel) row.hidden = sel.value !== "sum";
}

/* Show the custom box only when it is wanted, and say what the typed column
 * comes to — a total that is not 20 is usually a typo, and seeing it is the
 * cheapest way to catch one. */
function syncLayoutRow() {
  const row = $("#layout-custom-row"), sel = $("#layout");
  if (!row || !sel) return;
  const custom = sel.value === "custom";
  row.hidden = !custom;
  if (!custom) return;
  const hint = $("#layout-hint");
  if (!hint) return;
  const units = parseLayout(($("#layout-custom").value || "").trim());
  hint.textContent = units
    ? t("setup.layout.ok", { total: units.reduce((a, b) => a + b, 0), n: units.length })
    : t("setup.layout.bad", { n: BANDS.length });
  hint.classList.toggle("bad", !units);
}

function startGame(force) {
  lastMeldLimit = null;
  const n = playerCount();
  const { humans, styles } = seatSelections();
  const seed = (force && force.seed) ||
               Number($("#seed").value) || Math.floor(Math.random() * 1e6);
  $("#seed").value = seed;
  HUMANS = humans;
  ME = humans.length ? humans[0] : 0;      // no humans: watch from seat 0
  PASSED = ME;
  const trickRule = $("#trick-rule").value;
  const deck = $("#deck").value;
  const objectives = $("#objectives").value;
  const retireRule = $("#retire-rule").value;
  const botLevel = radioValue("#bot-level", "normal");
  const mv = $("#meld-rules").value;
  /* Kept whole, because undo deals this exact game again from here. */
  GARGS = { n, seed, opts: { humans, trickRule, deck, objectives, retireRule,
                             botStyle: "mixed", seatStyles: styles, botLevel,
                             comboMelds: mv === "combo" || mv === "both",
                             friendsOf10: mv === "friends" || mv === "both",
                             growLimits: $("#grow-limits").value === "grow",
                             perks: $("#perks") && $("#perks").value === "on",
                             consolation: $("#consolation").value,
                             researchRule: $("#research-rule").value,
                             meldScore: $("#meld-score").value,
                             aSumLadder: $("#a-ladder") ? $("#a-ladder").value : undefined,
                             layout: chosenLayout() } };
  G = new Game(GARGS.n, GARGS.seed, GARGS.opts);
  LOG = []; MARK = 0; BLOCK = null; RESUMING = false; TRICK = null;
  REP = newReport(BUILD, GARGS, { lang: getLang(), players: seatRoster(styles, humans) });
  IT = null; REQ = null; SEL = blankSel();
  lastZone = null;
  ZOOM = null; PAN = { x: 0, y: 0 };       // a new board fits itself again
  hidePass();
  // toggle a class, never `style.display = ""` — that would just fall back to
  // the stylesheet, where #game is display:none
  $("#setup").classList.add("hide");
  $("#game").classList.add("show");
  document.body.classList.add("playing");
  nextRound();
}

/* ---- more than one person at the table ----
 * The board shows the acting seat's hand, so it must not be visible while the
 * device changes hands. Between two different human seats the game is covered
 * until the next player says they have it. */
function maybePass(seat) {
  if (HUMANS.length < 2 || seat === PASSED) return false;
  const gate = $("#pass");
  if (!gate) { PASSED = seat; return false; }
  $("#pass-dot").style.background = SEAT_C[seat];
  $("#pass-name").textContent = seatName(seat);
  $("#pass-note").textContent = t("pass.note");
  gate.hidden = false;
  const go = $("#pass-go");
  go.textContent = t("pass.ready");
  go.focus();
  PENDING_SEAT = seat;
  return true;
}
function hidePass() {
  const gate = $("#pass");
  if (gate) gate.hidden = true;
}

/* Has the game actually STOPPED?
 *
 * Not the same question as `G.finished()`, and the difference is a bug that
 * reached a playtester: "the final round was announced, but at the same time
 * the winner was announced and the game ended."
 *
 * The round counter is bumped at the START of a round, and finished() is
 * `round >= finalRounds`. The trigger sets finalRounds = round + 1, so the
 * moment the extra round BEGINS, finished() is already true. The engine is fine
 * — the driver only consults it between rounds, so exactly one more round is
 * played, which is what §11 asks. But anything that renders on finished() was
 * treating the whole final round as over: the prompt showed the result table
 * instead of the turn, so the round the rules grant you could not be played.
 *
 * The game has stopped when the driver has nothing left in flight: no generator
 * and no outstanding question. */
function gameOver() {
  return !!(G && G.finished() && !IT && !REQ);
}

// --------------------------------------------------------------- driver
function nextRound() {
  RESEARCH = null;
  if (G.finished()) { REQ = null; render(); return; }
  IT = G.playRound();
  pump(undefined);
}

function pump(a) {
  let r;
  try { r = IT.next(a); }
  catch (e) { console.error(e); G.say("log.engineError", { msg: e.message }); render(); return; }
  if (!r.done) {
    REQ = r.value;
    /* Show the game from the seat that is being asked. With one human this
     * never moves; with several it is what makes hot seat work at all. */
    if (G.isHuman(REQ.seat) && !netOn()) {
      /* Hot seat: the board moves to whoever is being asked, behind a cover.
       * Remote: it stays on your own seat — the others' hands are not yours
       * to see, and there is no device to hand over. */
      if (REQ.seat !== ME) { ME = REQ.seat; lastMeldLimit = null; }
      if (maybePass(REQ.seat)) { noteBlock(); render(); return; }
    }
    noteBlock();
    if (G.isHuman(REQ.seat)) reportAsked(REP, REQ, G.round);
    render(); playEvents();
    if (netOn()) drainNet();               // anything that arrived mid-round
    return;
  }
  IT = null; REQ = null;
  BLOCK = null;
  render();
  /* Let the round's animations finish before the next one starts — otherwise a
   * bot's whole turn resolves in one frame and is impossible to follow. */
  const wait = Math.min(1400, 220 + playEvents());
  if (!G.finished()) setTimeout(nextRound, wait);
}

function answer(a, keepSel) {
  if (!REQ) return;
  const tok = encodeAns(REQ, a);
  /* Remote: the server decides the order things happen in, so this goes on
   * the wire and takes effect when it comes back. One round trip, and nobody
   * is ever looking at a board the others cannot see. */
  if (netOn() && NET.status === "playing") {
    if (REQ.seat !== netMySeat()) return;
    if (!keepSel) SEL = blankSel();
    if (!netSend({ t: "answer", step: LOG.length, token: tok })) netBar();
    render();
    return;
  }
  LOG.push(tok);
  reportAnswered(REP, tok);
  if (!keepSel) SEL = blankSel();
  pump(a);
}

/* ------------------------------------------------------- taking it back
 *
 * The engine is a running generator: you cannot rewind one. But the game is a
 * pure function of (seed, options, the answers people gave) — the shuffle is
 * seeded and the bots draw from the same stream — so undo is REPLAY. Every
 * answer is written down as a small token, and stepping back means dealing the
 * same game again from the beginning and giving all the same answers but the
 * last one. On a table this is the difference between picking a card back up
 * before you let go of it and unpicking the whole round.
 *
 * The limit the designer asked for is enforced by MARK: the point in the log
 * where the acting seat's own map turn began. You can take back anything you
 * did on your turn; you cannot reach back past the trick, which everyone has
 * already seen resolve.
 */
let LOG = [], GARGS = null, MARK = 0, BLOCK = null;
/* Which requests belong to one seat's map turn — the list lives in session.js,
 * because the server enforces the same limit from the other side. */

/* Where "this turn" starts. Called on every request and every answer; the
 * block is identified by round + seat, which a map turn has exactly one of. */
function noteBlock() {
  if (!G || !REQ || !G.isHuman(REQ.seat) || !TURN_REQ.includes(REQ.type)) {
    BLOCK = null;
    return;
  }
  const key = G.round + ":" + REQ.seat;
  if (key !== BLOCK) { BLOCK = key; MARK = LOG.length; }
}
const canUndo = () => !!(BLOCK !== null && LOG.length > MARK && !RESUMING
  && (!netOn() || (REQ && REQ.seat === netMySeat())));
let RESUMING = false;

/* The codec lives in session.js, with the server that also replays these
 * tokens — one encoder and one decoder, or a whole table desynchronises. */
const encodeAns = (req, a) => encodeAnswer(G, req, a);
const decodeAns = (g, req, tok) => decodeAnswer(g, req, tok);

/* Deal the same game again and give the first `len` answers back to it. */
function replay(len) {
  const g = new Game(GARGS.n, GARGS.seed, GARGS.opts);
  let it = g.playRound(), r = it.next(), i = 0, guard = 0;
  for (;;) {
    if (guard++ > 100000) break;          // a replay must terminate
    if (r.done) {
      if (g.finished()) return { g, it: null, req: null };
      it = g.playRound(); r = it.next(); continue;
    }
    if (i >= len) return { g, it, req: r.value };
    r = it.next(decodeAns(g, r.value, LOG[i++]));
  }
  return { g, it: null, req: null };
}

/* The trick is public by the time anyone is taking a map turn, so a rebuilt
 * game shows it whole — no re-running of the clockwise reveal. */
function syncTrick() {
  TRICK = newTrick(G.round);
  for (const q of G.P) if (q.tableau) TRICK.laid.add(q.i);
  TRICK.winner = G.winner;
  TRICK.order = G.trickOrder ? G.trickOrder.slice() : null;
  TRICK.acting = G.acting;
  TRICK.done = new Set(G.turnDone || []);
}

/* The flag button carries its own count: one flag raised is a thing you want
 * to see was recorded, and the count is game state, not language. */
function updateFlag() {
  const f = $("#flag");
  if (!f) return;
  const n = REP ? REP.flags.length : 0;
  f.textContent = n ? t("flag.count", { n }) : t("flag.btn");
  f.title = t("flag.tip");
  f.classList.toggle("has", n > 0);
}

/* Greyed out is not enough on its own — the button says WHY it is grey. */
function updateUndo() {
  const b = $("#undo");
  if (!b) return;
  const can = canUndo();
  b.disabled = !can;
  b.title = can ? t("nav.undo.tip") : t("nav.undo.none");
}

function doUndo() {
  if (!canUndo()) return;
  /* Remote: the server holds the same limit and works it out from the log
   * rather than taking this page's word for it. */
  if (netOn() && NET.status === "playing") { netSend({ t: "undo" }); return; }
  RESUMING = true;
  const target = LOG.length - 1;
  LOG.length = target;
  const out = replay(target);
  G = out.g; IT = out.it; REQ = out.req;
  if (G.events) G.events.length = 0;      // do not re-animate the whole game
  SEL = blankSel(); lastZone = null; lastMeldLimit = null;
  /* Research is a multi-step action, so landing back inside one has to put the
   * panel back in the state the request implies. */
  RESEARCH = !REQ ? null
    : REQ.type === "retire" ? { stage: "retire", drew: REQ.drew }
    : REQ.type === "buy" ? { stage: "buy", drew: REQ.drew, retired: REQ.retire }
    : null;
  if (REQ && G.isHuman(REQ.seat)) ME = REQ.seat;
  syncTrick();
  noteBlock();
  reportUndone(REP, LOG.length);
  if (REQ && G.isHuman(REQ.seat)) reportAsked(REP, REQ, G.round);
  RESUMING = false;
  render();
}

/* ---- raising a flag ----
 *
 * The moment somebody is confused is the moment worth recording, and it is
 * gone by the end of the game. One button, one optional sentence; the round,
 * the seat, the step in the replay and what the game was asking are taken from
 * the game itself, because those are exactly the things a person would get
 * wrong if asked to type them.
 */
function openFlag() {
  if (!G || !REP) return;
  const box = $("#flagbox");
  if (!box) return;
  $("#flag-title").textContent = t("flag.title");
  $("#flag-where").textContent = t("flag.where", {
    r: G.round,
    who: REQ ? seatName(REQ.seat) : seatName(ME),
    step: t(REQ ? "step." + REQ.type : "step.none"),
  });
  $("#flag-notelab").textContent = t("flag.note");
  const note = $("#flag-note");
  note.placeholder = t("flag.placeholder");
  note.value = "";
  $("#flag-save").textContent = t("flag.save");
  $("#flag-cancel").textContent = t("flag.cancel");
  box.hidden = false;
  note.focus();
}
function closeFlag() { const b = $("#flagbox"); if (b) b.hidden = true; }
function saveFlag() {
  const f = reportFlag(REP, G, REQ, $("#flag-note").value);
  closeFlag();
  if (f) { G.say("log.flagged", { r: f.r }); render(); }
}

/* ---- starting over, and walking away ---- */
function restartGame() {
  if (!G) return;
  if (!window.confirm(t("nav.restart.ask"))) return;
  startGame({ seed: GARGS.seed });
}
function abortGame() {
  if (!G || !window.confirm(t("nav.abort.ask"))) return;
  if (netOn()) { netClose(); history.replaceState(null, "", location.pathname); }
  G = null; IT = null; REQ = null; LOG = []; BLOCK = null; MARK = 0;
  SEL = blankSel(); RESEARCH = null; TRICK = null;
  $("#setup").classList.remove("hide");
  $("#game").classList.remove("show");
  document.body.classList.remove("playing");
  hidePass();
  updateUndo();
}

// --------------------------------------------------------------- geometry
const HEXR = 30;
function hexCentre(c, r) {
  const w = Math.sqrt(3) * HEXR;
  return [w * (c + 0.5 * (r & 1)), 1.5 * HEXR * r];
}
/* Text over terrain needs a halo. paint-order isn't reliable everywhere, so
 * the string is drawn twice: once as a fat stroke, once as the fill. */
function haloText(x, y, cls, txt) {
  return `<text class="${cls} halo" x="${x}" y="${y}">${txt}</text>` +
         `<text class="${cls}" x="${x}" y="${y}">${txt}</text>`;
}
function hexPoints(cx, cy, rad) {
  const pts = [];
  for (let k = 0; k < 6; k++) {
    const a = (Math.PI / 180) * (60 * k - 90);
    pts.push((cx + rad * Math.cos(a)).toFixed(1) + "," + (cy + rad * Math.sin(a)).toFixed(1));
  }
  return pts.join(" ");
}

// --------------------------------------------------------------- animation
/* Units, coins and cards are animated as throwaway tokens on the #fx layer.
 * Nothing on the board is transitioned, because render() replaces it wholesale
 * — a flying token survives that, a transitioning board node would not.
 *
 * Everything here is optional: if the geometry is unavailable (jsdom, an SVG
 * without getScreenCTM) or the reader prefers reduced motion, the effects are
 * skipped and the game is unaffected. */
const FX_STEP = 70;                      // ms between queued events
/* Some beats are the point of the round rather than a detail, and want their
 * own timing: a card being laid, and the pause before the trick is awarded. */
const FX_BEAT = { meld: 330, trick: 560, turnstart: 170, turnend: 120 };
let fxUntil = 0;                         // when the current queue finishes

function reducedMotion() {
  try { return window.matchMedia("(prefers-reduced-motion: reduce)").matches; }
  catch (e) { return false; }
}

/* Can anything actually be animated here? No, if the reader asked for less
 * motion, or if there is no layout to measure (jsdom, a hidden tab). When the
 * answer is no, the table shows the engine's state directly and nothing is
 * ever staged — the game must be fully readable without a single animation. */
let FX_OK = null;
function fxEnabled() {
  if (FX_OK === null) {
    FX_OK = false;
    try {
      const k = G && G.m && G.m.tiles.size ? [...G.m.tiles.keys()][0] : null;
      FX_OK = !reducedMotion() && !!cellPoint(k);
    } catch (e) { FX_OK = false; }
  }
  return FX_OK;
}

/* ---- the trick, as the table sees it ----
 * The engine resolves a whole card phase in one tick: every bot melds, the
 * trick is awarded and the map phase begins before the client is asked
 * anything. Replayed raw that is a single flash. So the client keeps its own
 * picture of the trick, advanced one beat at a time by the recorded events,
 * and the table renders from THIS rather than from the engine. When animation
 * is off, every accessor falls through to the engine and nothing is withheld.
 */
let TRICK = null;
function newTrick(r) {
  return { round: r, laid: new Set(), winner: null, order: null,
           acting: null, done: new Set() };
}
const laid = (i) => !fxEnabled() || TRICK.laid.has(i);
const uiWinner = () => (fxEnabled() ? TRICK.winner : G.winner);
const uiOrder = () => (fxEnabled() ? TRICK.order : G.trickOrder);
const uiActing = () => (fxEnabled() ? TRICK.acting : G.acting);
const uiDone = (i) =>
  !!(fxEnabled() ? TRICK.done.has(i) : G.turnDone && G.turnDone.has(i));

/* The order everyone is in right now: the trick's ranking once it is known,
 * the order of play around the table before that. */
function uiSeq() { return (uiOrder() || G.playOrder || []).slice(); }
function uiPos(i) { const k = uiSeq().indexOf(i); return k < 0 ? 0 : k; }

/* Whatever is happening to a seat this instant — a meld landing, a crown. Held
 * as state, not as a class poked onto a node, because render() rebuilds the
 * play area and would wipe it mid-animation. */
const FLASH = new Map();
function flash(seat, cls, ms) {
  ms = ms || 650;
  FLASH.set(seat, { cls, until: Date.now() + ms });
  renderTable();
  setTimeout(renderTable, ms + 20);
}
function flashCls(seat) {
  const f = FLASH.get(seat);
  return f && f.until > Date.now() ? f.cls : "";
}

/* Run fn later, but only if the round it belongs to is still on the table. */
function at(delay, round, fn) {
  setTimeout(() => { if (G && G.round === round) fn(); }, Math.max(0, delay));
}
/* Catch-up: after a queue drains, the client's picture is the engine's. Any
 * beat that was dropped (a queue cleared, a round cut short) is corrected here,
 * so a lost event can never leave a meld face down for the rest of the round. */
function syncTrick() {
  if (!G) return;
  if (!TRICK || TRICK.round !== G.round) TRICK = newTrick(G.round);
  for (let i = 0; i < G.n; i++) if (G.P[i].tableau) TRICK.laid.add(i);
  TRICK.winner = G.winner;
  TRICK.order = G.trickOrder;
  TRICK.acting = G.acting;
  if (G.turnDone) for (const i of G.turnDone) TRICK.done.add(i);
  renderTable();
}

function seatBox(i) {
  return i === ME ? $("#mymeld") : $(`#corners .corner[data-seat="${i}"]`);
}
function seatPoint(i) {
  const n = seatBox(i);
  if (!n || !n.getBoundingClientRect) return null;
  const b = n.getBoundingClientRect();
  if (!b.width && !b.height) return null;
  return { x: b.left + b.width / 2, y: b.top + b.height / 2 };
}

/* Screen point of a hex centre, through the SVG's own transform. */
function cellPoint(key) {
  const svg = $("#map");
  if (!svg || !svg.getScreenCTM || !key) return null;
  try {
    const [c, r] = unK(key);
    const [x, y] = hexCentre(c, r);
    const m = svg.getScreenCTM();
    if (!m) return null;
    const pt = svg.createSVGPoint();
    pt.x = x; pt.y = y;
    const o = pt.matrixTransform(m);
    return o.x || o.y ? { x: o.x, y: o.y } : null;
  } catch (e) { return null; }
}

/* Screen point of a piece of furniture — where a thing comes from or goes to. */
function uiPoint(what, arg) {
  const pick = {
    hand: "#hand", board: ".pboard .tiers", gold: ".pb-head .purse",
    vrow: ".vslots", market: "#market", meld: "#mymeld", deck: "#deckpile",
    pile: "#pilebox",
  }[what];
  let n = pick ? $(pick) : null;
  if (what === "market" && arg !== undefined) {
    const slots = document.querySelectorAll("#market .slot");
    if (slots[arg]) n = slots[arg];
  }
  if (!n || !n.getBoundingClientRect) return null;
  const b = n.getBoundingClientRect();
  if (!b.width && !b.height) return null;
  return { x: b.left + b.width / 2, y: b.top + b.height / 2 };
}

function point(spec, arg) {
  if (!spec) return null;
  return typeof spec === "string" && spec.includes(",")
    ? cellPoint(spec) : uiPoint(spec, arg);
}

function token(cls, from, to, style, delay) {
  const layer = $("#fx");
  if (!layer || !from || !to) return;
  const t = el("div", "tok " + cls);
  if (style) t.setAttribute("style", style);
  t.style.transform = `translate(${from.x}px, ${from.y}px)`;
  layer.appendChild(t);
  setTimeout(() => {
    t.style.transform = `translate(${to.x}px, ${to.y}px)`;
    if (cls === "gone") t.classList.add("gone");
  }, Math.max(16, delay));
  setTimeout(() => t.remove(), delay + 700);
}

/* A stack takes a card, or gives one up: nudge it, so the source or the
 * destination of a flying card is never in doubt. */
function shove(sel, delay) {
  const n = $(sel);
  if (!n) return;
  setTimeout(() => {
    n.classList.add("dealing");
    setTimeout(() => n.classList.remove("dealing"), 500);
  }, Math.max(0, delay));
}

function ring(at, bad, delay) {
  const layer = $("#fx");
  if (!layer || !at) return;
  setTimeout(() => {
    const r = el("div", "ring" + (bad ? " bad" : ""));
    r.style.transform = `translate(${at.x}px, ${at.y}px)`;
    layer.appendChild(r);
    setTimeout(() => r.remove(), 600);
  }, Math.max(0, delay));
}

/* Drain whatever the engine recorded since the last step and play it. */
function playEvents() {
  if (!G || !G.events || !G.events.length) return 0;
  const q = G.events.splice(0, G.events.length);
  FX_OK = null;
  if (!fxEnabled()) return 0;

  const round = G.round;
  let d = 0;
  for (const e of q) {
    const col = SEAT_C[e.seat] || "#888";
    switch (e.type) {
      case "unit-in":
        token("unit", uiPoint("board") || uiPoint("hand"), cellPoint(e.to),
              `background:${col}`, d);
        ring(cellPoint(e.to), false, d + 380);
        break;
      case "unit-out":
        token("unit gone", cellPoint(e.from), uiPoint("board") || uiPoint("hand"),
              `background:${col}`, d);
        ring(cellPoint(e.from), true, d);
        break;
      case "unit-move":
        token("unit", cellPoint(e.from), cellPoint(e.to), `background:${col}`, d);
        break;
      case "tile":
        token("tile", uiPoint("meld") || uiPoint("hand"), cellPoint(e.to),
              `background:${TC[G.m.tiles.get(e.to) ? G.m.tiles.get(e.to).terrain : "plains"]}`, d);
        break;
      case "shield":
        ring(cellPoint(e.at), true, d);
        break;
      case "gold": {
        const gained = e.amount > 0;
        const src = gained ? point(e.from) : uiPoint("gold");
        const dst = gained ? uiPoint("gold") : point(e.to);
        for (let k = 0; k < Math.min(Math.abs(e.amount), 4); k++)
          token("coin", src, dst, "", d + k * 60);
        break;
      }
      case "card": {
        /* A rival's cards come from and go to THEIR place at the table, not to
         * the furniture in front of you. */
        const own = (spec, slot) =>
          (e.seat !== undefined && e.seat !== ME
           && ["meld", "hand", "board", "vrow", "gold"].includes(spec))
            ? seatPoint(e.seat) : point(spec, slot);
        const from = own(e.from, e.slot), to = own(e.to);
        token("card" + (e.to === "pile" || e.from === "pile" ? " back" : ""),
              from, to, `--suit:${TC[e.card.s]}`, d);
        if (e.to === "pile") shove("#pilebox", d);
        if (e.from === "pile") shove("#pilebox", d);
        break;
      }
      case "deal": {
        /* Face down off the deck, turning over as it lands on the position it
         * buries. The pile itself gives a small shove so the source reads. */
        shove("#deckpile", d);
        token("card back", uiPoint("deck"), uiPoint("market", e.slot),
              `--suit:${TC[e.card.s]}`, d);
        ring(uiPoint("market", e.slot), false, d + 380);
        break;
      }
      /* ---- the round of cards, one beat per player ---- */
      case "meld": {
        const seat = e.seat;
        at(d, round, () => {
          TRICK.laid.add(seat);
          flash(seat, "laid");                    // the cards drop into the slots
        });
        break;
      }
      case "trick": {
        const seat = e.seat, ord = e.order.slice();
        at(d, round, () => {
          TRICK.winner = seat; TRICK.order = ord;
          flash(seat, "crowned", 900);
          ring(seatPoint(seat), false, 0);
        });
        break;
      }
      case "turnstart": {
        const seat = e.seat;
        at(d, round, () => { TRICK.acting = seat; renderTable(); });
        break;
      }
      case "turnend": {
        const seat = e.seat;
        at(d, round, () => {
          TRICK.done.add(seat);
          if (TRICK.acting === seat) TRICK.acting = null;
          renderTable();
        });
        break;
      }
    }
    d += FX_BEAT[e.type] || FX_STEP;
  }
  const ms = d + 400;
  fxUntil = Date.now() + ms;
  at(d + 30, round, syncTrick);      // whatever the beats missed, correct here
  return ms;
}

// --------------------------------------------------------------- render
function render() {
  if (!G) return;
  FX_OK = null;                                  // the map may have just appeared
  if (!TRICK || TRICK.round !== G.round) TRICK = newTrick(G.round);
  renderMap();
  renderLegend();
  renderTable();
  renderPlayer();
  renderMarket();
  renderSide();
  renderPrompt();
  renderZone();
  updateUndo();
  updateFlag();
}

/* ---- where do I click? ----
 * Every request that wants a click wants it in ONE place. That place lights up
 * and stays lit until the action is done, and the cards inside it that are
 * legal are lifted out of the rest. Nobody should have to read a sentence to
 * find out which part of the table is waiting for them.
 */
const ZONES = ["#hand", "#market", "#mymeld", ".vrowbox", ".objpick", "#mapbox"];
function needZone() {
  if (!mine() || !REQ) return null;
  switch (REQ.type) {
    case "meld": return "#hand";                 // build it out of your hand
    case "retire": case "discard": case "bonus": return "#hand";
    case "buy": return "#market";
    case "setaside": return "#mymeld";           // the cards are already on the table
    case "feed": case "effectA": return ".vrowbox";
    case "objective": return ".objpick";
    case "conquest": case "waterexplore": case "colony": return "#mapbox";
    default: return null;                        // `turn` is free-form on purpose
  }
}
let lastZone = null;
function renderZone() {
  const want = needZone();
  /* The zone may not be built yet — `.objpick` lives inside the prompt, which
   * is rendered after the table. Leave the state alone and wait for the pass
   * that follows renderPrompt. */
  if (want && !$(want)) return;
  for (const sel of ZONES) {
    const n = $(sel);
    if (n) n.classList.toggle("needs", sel === want);
  }
  /* Scroll it into view only when it CHANGES — on a phone the hand and the
   * market are below the map, and a step that silently waits off-screen reads
   * as a frozen game. */
  if (want && want !== lastZone) {
    const n = $(want);
    if (n && n.scrollIntoView) {
      try { n.scrollIntoView({ block: "nearest", behavior: "smooth" }); } catch (e) {}
    }
  }
  lastZone = want;
}

/* The shared table: who is in the trick, in what order, and what they laid.
 * Redrawn on its own between beats, without touching the map or the prompt. */
function renderTable() {
  if (!G || !TRICK) return;
  renderTurnbar();
  renderCorners();
  renderMyMeld();
  /* An animation beat rebuilds the meld area, and would take the highlight off
   * a step that is still waiting for a click. Put it back. */
  renderZone();
}

const mine = () => REQ && REQ.seat === ME;

/* Which cells the player may click right now, and what clicking means. */
/* A move is "by sea" only when it starts AND ends on Ocean — that is what §07
 * asks for, and it is what earns the water advantage. Stepping onto the water
 * from land is an ordinary land move and earns nothing, which is exactly the
 * thing a player cannot tell without being told. */
const isSea = (k) => {
  const t = G.m.tiles.get(k);
  return !!t && t.terrain === "ocean";
};
function seaDests(src) {
  const out = new Set();
  if (!isSea(src)) return out;
  for (const k of G.moveDests(G.P[ME], src)) if (isSea(k)) out.add(k);
  return out;
}
/* Which of those would actually collect the free tile. Asked of the engine,
 * because it is a rule: out in open water there is often nowhere legal to put
 * a tile, and a badge that promises one anyway is a lie the player only finds
 * out about after committing the move. */
function seaPays(src, dest) {
  try { return G.waterPays(G.P[ME], src, dest); } catch (e) { return false; }
}
/* The empty cells this source may make landfall on. The engine sends them with
 * the turn options, keyed by source; falling back to asking it directly keeps
 * an older server's reply from silently removing the option. */
function landfallFor(src) {
  const given = REQ && REQ.opts && REQ.opts.landfall;
  if (given && given[src]) return given[src];
  if (given) return [];
  try {
    return G.landfallCells(G.P[ME], src,
                           !(REQ && REQ.opts && REQ.opts.waterReady));
  } catch (e) { return []; }
}

function activeCells() {
  const out = new Map();
  if (!mine()) return out;
  if (REQ.type === "turn") {
    if (SEL.mode === "move") {
      if (!SEL.moveSrc) {
        for (const k of REQ.opts.moveSources)
          out.set(k, { act: "source",
                       sea: seaDests(k).size > 0 || landfallFor(k).length > 0 });
      } else {
        const sea = seaDests(SEL.moveSrc);
        for (const k of G.moveDests(G.P[ME], SEL.moveSrc))
          out.set(k, { act: "dest", sea: sea.has(k),
                       pays: sea.has(k) && seaPays(SEL.moveSrc, k) });
        /* And the empty ground this voyage may make landfall on. These are not
         * tiles yet — the engine lays one and lands the unit on it as the move
         * resolves — so they come from their own list, not from moveDests. */
        for (const k of landfallFor(SEL.moveSrc))
          if (!out.has(k)) out.set(k, { act: "landfall" });
      }
    } else if (SEL.mode === "fortify") {
      for (const k of REQ.opts.fortifyCells) out.set(k, { act: "fortify" });
    } else if (SEL.card) {
      const e = REQ.opts.cards.find((m) => m.card === SEL.card);
      if (e) {
        for (const [k, act] of e.options) out.set(k, { act });
        /* Rival tiles this card could take if the gold were there. Marked
         * `blocked` so the map draws them dimmed and refuses the click — the
         * point is to say WHY nothing happens, not to allow it. Added after the
         * legal options and only where there is no legal action already, so a
         * cell that can be settled is never overwritten by a refusal. */
        for (const [k, cost] of e.blocked || [])
          if (!out.has(k)) out.set(k, { act: "attack", blocked: "gold", cost });
      }
    }
  }
  if (REQ.type === "waterexplore" && !SEL.waterCell)
    for (const k of REQ.options) out.set(k, { act: "explore" });
  if (REQ.type === "colony" && !SEL.colonyCell)
    for (const k of REQ.options) out.set(k, { act: "colony" });
  if (REQ.type === "conquest")
    for (const k of REQ.options) out.set(k, { act: "strike" });
  return out;
}

function renderMap() {
  const svg = $("#map");
  const act = activeCells();
  const pts = [], draw = [], ghosts = [];
  const spaces = G.m.legalSpaces();

  for (const t of G.m.tiles.values()) {
    const [cx, cy] = hexCentre(t.cell[0], t.cell[1]);
    pts.push([cx, cy]); draw.push({ t, cx, cy, key: t.key });
  }
  // empty but legal spaces are drawn as ghosts so the map's growth is legible
  for (const k of spaces) {
    const [c, r] = unK(k);
    const [cx, cy] = hexCentre(c, r);
    pts.push([cx, cy]); ghosts.push({ key: k, cx, cy });
  }

  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const pad = HEXR * 1.3;
  const minx = Math.min(...xs) - pad, maxx = Math.max(...xs) + pad;
  const miny = Math.min(...ys) - pad, maxy = Math.max(...ys) + pad;
  const box = svg.getBoundingClientRect();
  MAPGEO = {
    cw: maxx - minx, ch: maxy - miny,
    cx: (minx + maxx) / 2, cy: (miny + maxy) / 2,
    W: box.width || 820, H: box.height || 380,
  };
  applyViewBox();

  let s = "";
  for (const gh of ghosts) {
    const a = act.get(gh.key);
    s += `<polygon class="ghost${a ? " hot" : ""}" data-key="${gh.key}"
      points="${hexPoints(gh.cx, gh.cy, HEXR - 1)}"/>`;
    if (a) s += haloText(gh.cx, gh.cy + 4, "badge", cellBadge(a));
  }
  for (const d of draw) {
    const t = d.t;
    const a = act.get(d.key);
    const isSrc = SEL.moveSrc === d.key;
    /* `nope` rather than `hot`: a tile that is only being explained must not
     * look like one that can be clicked. */
    const mark = a ? (a.blocked ? " nope" : " hot") : "";
    s += `<polygon class="tile${mark}${isSrc ? " src" : ""}" data-key="${d.key}"
      points="${hexPoints(d.cx, d.cy, HEXR - 1)}" fill="${TC[t.terrain]}"/>`;
    const n = t.units.length;
    for (let i = 0; i < n; i++) {
      const off = (i - (n - 1) / 2) * 13;
      s += `<circle class="pip" cx="${d.cx + off}" cy="${d.cy + 3}" r="6"
             fill="${SEAT_C[t.units[i]]}"/>`;
    }
    if (t.gold) s += `<circle class="coin" cx="${d.cx + 15}" cy="${d.cy - 14}" r="5"/>`;
    const cap = t.capacityFor(t.owner === null ? ME : t.owner);
    s += haloText(d.cx, d.cy - 12, "cap", `${n}/${cap}`);
    if (a) s += haloText(d.cx, d.cy + 19, "badge", cellBadge(a));
  }
  svg.innerHTML = s;
  svg.querySelectorAll("[data-key]").forEach((node) =>
    node.addEventListener("click", () => onCell(node.dataset.key)));
  /* If there is somewhere legal to click and none of it is on screen, go there.
   * A highlight you cannot see is worse than no highlight. */
  if (act.size) ensureVisible([...act.keys()]);
}

/* The terrain key shows what YOU may stack, which is not a constant when
 * population limits grow with your band — and a key that says "Plains 3" while
 * your Tribe may only hold 2 is worse than no key at all. */
function renderLegend() {
  const n = $("#legend");
  if (!n || !G) return;
  const p = G.P[ME];
  const grow = !!G.m.limits;
  n.innerHTML = TER.map((terr) => {
    const cap = grow ? G.m.limits[p.band()][terr] : HOLDS[terr];
    const top = grow ? G.m.limits[G.m.limits.length - 1][terr] : cap;
    const tip = grow
      ? t("board.legendGrow", { terrain: TL[terr], cap, tier: tierName(p.band()), top })
      : t("board.legend", { terrain: TL[terr], cap });
    return `<i style="background:${TC[terr]}" title="${tip}"></i>${cap}`;
  }).join("");
}

// --------------------------------------------------------------- map view
/* Pure, so it can be checked without a layout engine (jsdom has none). */
function mapScale(cw, ch, W, H, manual) {
  if (manual) return Math.max(ZOOM_FLOOR, Math.min(ZOOM_CEIL, manual));
  const fit = Math.min(W / cw, H / ch);
  return Math.max(ZOOM_MIN, Math.min(fit, ZOOM_MAX));
}
/* Never let the board be dragged away entirely: one hex of overscroll past the
 * edge, and no panning at all on an axis that already fits. */
function clampPan(pan, cw, ch, vw, vh) {
  const lim = (content, view) => Math.max(0, (content - view) / 2 + HEXR * 0.6);
  const mx = lim(cw, vw), my = lim(ch, vh);
  return { x: Math.max(-mx, Math.min(mx, pan.x)),
           y: Math.max(-my, Math.min(my, pan.y)) };
}
function viewBoxOf(geo, zoom, pan) {
  const scale = mapScale(geo.cw, geo.ch, geo.W, geo.H, zoom);
  const vw = geo.W / scale, vh = geo.H / scale;
  const p = clampPan(pan, geo.cw, geo.ch, vw, vh);
  return { scale, vw, vh, pan: p,
           x: geo.cx + p.x - vw / 2, y: geo.cy + p.y - vh / 2,
           /* does the board still fit? if not, the map is a window onto it and
            * the gesture belongs to the map rather than to the page */
           pans: geo.cw > vw + 1 || geo.ch > vh + 1 };
}
/* Move the viewBox only — no DOM rebuild, so a drag stays smooth. */
function applyViewBox() {
  const svg = $("#map");
  if (!svg || !MAPGEO) return null;
  /* Re-measure the element every time.
   *
   * The viewBox is built as W/scale by H/scale, which only produces `scale` if
   * W and H are the element's CURRENT size — SVG letterboxes a viewBox whose
   * aspect ratio does not match its box, and the real scale becomes the smaller
   * of the two axes. MAPGEO was measured once per render, and the map's own
   * height changes AFTER that as the prompt, hand and player board lay out
   * beneath it. So the first fit of a new game was computed against a box that
   * no longer existed: a viewBox of ratio 1.96 inside an element of ratio 2.98,
   * letterboxed down to 0.60 — under the 0.72 floor this file promises, tiles
   * at 30x35 px instead of 37x43, and the board adrift in a wide empty margin.
   * Three lines here are cheaper than a stale-geometry bug nobody can see. */
  const box = svg.getBoundingClientRect();
  if (box.width > 0 && box.height > 0) { MAPGEO.W = box.width; MAPGEO.H = box.height; }
  const v = viewBoxOf(MAPGEO, ZOOM, PAN);
  PAN = v.pan;
  svg.setAttribute("viewBox", `${v.x} ${v.y} ${v.vw} ${v.vh}`);
  svg.classList.toggle("pannable", v.pans);
  const fit = $("#zfit");
  if (fit) fit.classList.toggle("live", v.pans || ZOOM !== null);
  return v;
}
/* Bring cells into view if not one of them is currently on screen. */
function ensureVisible(keys) {
  if (!MAPGEO) return;
  const v = viewBoxOf(MAPGEO, ZOOM, PAN);
  if (!v.pans) return;
  let sx = 0, sy = 0, n = 0, seen = false;
  for (const k of keys) {
    const [c, r] = unK(k);
    const [x, y] = hexCentre(c, r);
    sx += x; sy += y; n++;
    if (x > v.x + HEXR && x < v.x + v.vw - HEXR
        && y > v.y + HEXR && y < v.y + v.vh - HEXR) seen = true;
  }
  if (seen || !n) return;
  PAN = clampPan({ x: sx / n - MAPGEO.cx, y: sy / n - MAPGEO.cy },
                 MAPGEO.cw, MAPGEO.ch, v.vw, v.vh);
  applyViewBox();
}

/* Drag to pan, mouse or finger. The map only claims the gesture when there is
 * something to pan to (`pannable`), so on a phone a swipe over a board that
 * fits still scrolls the page. A drag is not a click: past a few pixels the
 * click that follows is swallowed. */
let DRAG = null;
const PTRS = new Map();                 // live pointers, for the two-finger pinch
function initPan() {
  const svg = $("#map");
  if (!svg || !svg.addEventListener) return;

  /* The map box changes size for reasons that are not a window resize: the
   * prompt grows a line, the hand wraps, the player board opens. `resize` on
   * window never fires for any of those, so without this the board keeps a fit
   * computed for a box it no longer occupies. */
  if (typeof ResizeObserver === "function") {
    let last = "";
    const ro = new ResizeObserver(() => {
      const b = svg.getBoundingClientRect();
      const now = Math.round(b.width) + "x" + Math.round(b.height);
      if (now === last || !b.width || !b.height) return;   // no loop, no churn
      last = now;
      if (G) applyViewBox();
    });
    try { ro.observe(svg); } catch (e) { /* older engines: the resize handler still runs */ }
  }
  const at = (e) => ({ x: e.clientX, y: e.clientY });
  const spread = () => {
    const [a, b] = [...PTRS.values()];
    return Math.hypot(a.x - b.x, a.y - b.y);
  };
  const scaleNow = () =>
    MAPGEO ? mapScale(MAPGEO.cw, MAPGEO.ch, MAPGEO.W, MAPGEO.H, ZOOM) : ZOOM_MIN;

  svg.addEventListener("pointerdown", (e) => {
    if (e.button) return;
    PTRS.set(e.pointerId, at(e));
    /* Capture only when a gesture is actually about to start. Capturing on
     * every touch — including a one-finger touch on a map that is not
     * `pannable`, meant to fall through to the page's own scroll — is what
     * broke scrolling on iOS Safari: WebKit does not reliably fire
     * pointercancel when its native scroll wins over a captured pointer, so
     * DRAG/PTRS were left thinking a gesture was still live, and the *next*
     * touch — anywhere, not just over the map — inherited that broken state.
     * Leaving an ordinary swipe uncaptured means iOS never has a reason to
     * hand it to us at all. */
    if (PTRS.size === 2) {                       // pinch beats pan
      try { svg.setPointerCapture(e.pointerId); } catch (err) {}
      DRAG = { pinch: true, from: spread(), zoom: scaleNow(), moved: 99 };
    } else if (PTRS.size === 1 && svg.classList.contains("pannable")) {
      try { svg.setPointerCapture(e.pointerId); } catch (err) {}
      DRAG = { from: at(e), pan: { x: PAN.x, y: PAN.y }, scale: scaleNow(), moved: 0 };
    }
  });
  svg.addEventListener("pointermove", (e) => {
    if (!DRAG || !PTRS.has(e.pointerId)) return;
    PTRS.set(e.pointerId, at(e));
    if (DRAG.pinch) {
      if (PTRS.size < 2) return;
      const r = spread() / (DRAG.from || 1);
      ZOOM = Math.max(ZOOM_FLOOR, Math.min(ZOOM_CEIL, DRAG.zoom * r));
      applyViewBox();
      return;
    }
    const p = at(e);
    const dx = p.x - DRAG.from.x, dy = p.y - DRAG.from.y;
    DRAG.moved = Math.max(DRAG.moved, Math.abs(dx) + Math.abs(dy));
    PAN = { x: DRAG.pan.x - dx / DRAG.scale, y: DRAG.pan.y - dy / DRAG.scale };
    applyViewBox();
  });
  const end = (e) => {
    if (!PTRS.has(e.pointerId)) return;   // not one of ours — a touch elsewhere
    PTRS.delete(e.pointerId);
    try { svg.releasePointerCapture(e.pointerId); } catch (err) {}
    if (!DRAG || PTRS.size) return;
    const wasGesture = DRAG.moved > 6;
    DRAG = null;
    if (wasGesture) {                   // swallow the click this gesture ends in
      svg.addEventListener("click", (c) => { c.stopPropagation(); c.preventDefault(); },
                           { capture: true, once: true });
    }
  };
  /* On window, not svg: an uncaptured pointer — an ordinary scroll swipe that
   * started over a non-pannable map — finishes wherever the finger lifts,
   * which by then is very likely outside the map entirely once the page has
   * scrolled under it. A listener on svg alone would never see that pointerup
   * and PTRS would carry a dead entry forever, silently pushing the next
   * two-finger touch into thinking a pinch was already half-started. */
  window.addEventListener("pointerup", end);
  window.addEventListener("pointercancel", end);

  /* Wheel and trackpad zoom, where they cannot be confused with scrolling the
   * page: on a wide screen the page does not scroll, and on a narrow one only
   * a board that already owns the gesture takes it. */
  svg.addEventListener("wheel", (e) => {
    const wide = !window.matchMedia || !window.matchMedia("(max-width: 900px)").matches;
    if (!wide && !svg.classList.contains("pannable")) return;
    e.preventDefault();
    zoom(e.deltaY > 0 ? -0.08 : 0.08);
  }, { passive: false });
}

/* What clicking this hex will do, in as few words as fit on a hex. A sea move
 * says so, and says what it pays: the free tile is the whole reason the sea is
 * worth using, and it was invisible. */
function cellBadge(a) {
  /* A refusal says the price, not just "no": "needs 2 🪙" tells a player both
   * why the tile is dead and exactly what would revive it. */
  if (a.blocked === "gold") return t("hex.needGold", { n: a.cost });
  if (a.act === "source") return t(a.sea ? "hex.sailFrom" : "hex.moveFrom");
  if (a.act === "dest") {
    if (!a.sea) return t("hex.moveHere");
    // only promise the free tile where there is somewhere legal to put it
    return t(REQ.opts && REQ.opts.waterReady && a.pays ? "hex.sailFree" : "hex.sailHere");
  }
  if (a.act === "landfall") return t("hex.landfall");
  if (a.act === "strike") return t("hex.strike");
  if (a.act === "fortify") return t("hex.fortify");
  if (a.act === "explore") return t("hex.freeTile");
  if (a.act === "colony") return t("hex.colony");
  return ACT_LABEL[a.act] || "";
}

function onCell(k) {
  const a = activeCells().get(k);
  if (!a) return;
  if (a.blocked) return;              // shown to explain itself, never to click
  if (REQ.type === "waterexplore") { SEL.waterCell = k; render(); return; }
  if (REQ.type === "colony") {
    if (REQ.terrains.length === 1) return answer({ cell: k, terrain: REQ.terrains[0] });
    SEL.colonyCell = k; render(); return;
  }
  if (REQ.type === "conquest") { answer(k); return; }
  if (REQ.type !== "turn") return;
  if (SEL.mode === "fortify") { answer({ kind: "fortify", cell: k }); return; }
  if (SEL.mode === "move") {
    if (a.act === "source") { SEL.moveSrc = k; render(); }
    /* Landfall needs a terrain before the move can resolve, and the engine
     * asks for it — but where the supply has only one kind of tile left there
     * is nothing to ask, so send it and save the player a pointless tap. */
    else if (a.act === "landfall") {
      const left = TER.filter((x) => G.m.supply[x] > 0);
      answer({ kind: "move", src: SEL.moveSrc, dest: k,
               terrain: left.length === 1 ? left[0] : undefined });
    }
    else answer({ kind: "move", src: SEL.moveSrc, dest: k });
    return;
  }
  if (SEL.card) answer({ kind: "spend", card: SEL.card, cell: k, act: a.act });
}

/* +/- take over from the automatic scale, starting from whatever it had
 * chosen, so the first press never jumps. */
function zoom(d) {
  const now = MAPGEO ? mapScale(MAPGEO.cw, MAPGEO.ch, MAPGEO.W, MAPGEO.H, ZOOM) : ZOOM_MIN;
  ZOOM = Math.max(ZOOM_FLOOR, Math.min(ZOOM_CEIL, now + d));
  renderMap();
}
/* One button, two jobs, because a big board needs both: show me everything,
 * and put it back to a size I can play at. Press once on a board too big to
 * fit and it zooms out until the whole thing is on screen — below the usable
 * floor, deliberately, because an overview is for looking, not clicking. Press
 * again (or on a board that already fits) and the map goes back to automatic. */
function zoomFit() {
  PAN = { x: 0, y: 0 };
  if (!MAPGEO) { ZOOM = null; renderMap(); return; }
  const fit = Math.min(MAPGEO.W / MAPGEO.cw, MAPGEO.H / MAPGEO.ch);
  const auto = mapScale(MAPGEO.cw, MAPGEO.ch, MAPGEO.W, MAPGEO.H, null);
  const showingAll = ZOOM !== null && Math.abs(ZOOM - fit) < 0.02;
  ZOOM = (showingAll || fit >= auto) ? null : Math.max(ZOOM_FLOOR, fit);
  renderMap();
}

// --------------------------------------------------------------- cards
/* One card face at three sizes. "mini" is the old chip — rank and suit, for
 * places where the card is only an identity (the market, a rival's meld).
 * "mid" adds the terrain band and the one-line effect strip, so you can judge
 * what a card would be worth once retired. "full" prints all three effects,
 * exactly as the physical card does. */
function deckIsD() { return G && G.DECK === "abd"; }
function thirdEffect(c) {
  return deckIsD()
    ? { key: "D", long: fxTextD(c.r).d, short: fxTextD(c.r).dShort }
    : { key: "C", long: fxText(c.r).c, short: fxText(c.r).cShort };
}

function faceInner(c, size) {
  const e = fxText(c.r);
  const third = thirdEffect(c);
  if (size === "mini")
    return `<b>${c.r}</b><i>${SUIT_LETTER[c.s]}</i>`;
  if (size === "mid")
    return `<span class="band">${TL[c.s]}</span>
      <span class="rank">${c.r}</span>
      <span class="fx">${e.aShort} · ${third.short}</span>`;
  return `<span class="band">${TL[c.s]}</span>
    <span class="rank">${c.r}<em>${SUIT_LETTER[c.s]}</em></span>
    <ul class="fx3">
      <li><span class="ab">A</span>${e.a}</li>
      <li><span class="ab">B</span>${e.b}</li>
      <li><span class="ab">${third.key}</span>${third.long}</li>
    </ul>`;
}
function cardChip(c, cls, attr, size) {
  size = size || "mini";
  return `<span class="cf ${size} ${cls || ""}" ${attr || ""}
    style="--suit:${TC[c.s]}">${faceInner(c, size)}</span>`;
}
function cardBtn(c, cls, attr, size) {
  size = size || "mini";
  return `<button class="cf btn ${size} ${cls || ""}" ${attr || ""}
    style="--suit:${TC[c.s]}">${faceInner(c, size)}</button>`;
}

// --------------------------------------------------------------- play area
/* A crown is the one thing on this table worth a picture: it has to be
 * readable at a glance from across the map. */
const CROWN = `<svg class="crown" viewBox="0 0 24 16" aria-hidden="true">
  <path d="M2 14.5 L2.4 3 L8 8 L12 1.5 L16 8 L21.6 3 L22 14.5 Z"/></svg>`;

/* One meld, printed the same way for everyone: the same card faces you hold,
 * the card set aside for a coin faded out, the winner's extra card double
 * framed, and a faint placeholder for every card that seat's tier still
 * allows. Rank, terrain and effect are legible on a rival's cards because
 * whether to fight them for the trick depends on exactly that. */
function meldFaces(q) {
  const played = (q.tableau || []).slice().sort(cardSortUI);
  let html = played
    .map((c) => cardChip(c, c === q.asideCard ? "aside" : "", "", "mid")).join("");
  if (q.tableauBonus) html += cardChip(q.tableauBonus, "bonus", "", "mid");
  return { html, n: played.length + (q.tableauBonus ? 1 : 0) };
}
function meldSlots(q, n) {
  const empty = Math.max(0, Math.max(q.meldLimit(), n) - n);
  return `<span class="mslot"></span>`.repeat(empty);
}

/* What everyone played, laid out around the map the way the table is laid out
 * around you: you at the near edge, the next player clockwise on your left,
 * and so on. The seat's COLOUR is its name — the same colour as its units on
 * the map — and its number is its place in the order. State is the frame:
 * gold crown won the trick, dark pulsing frame is acting now, faded is done. */
const RIVAL_SPOT = { 2: ["top"], 3: ["left", "right"], 4: ["left", "top", "right"] };

/* Which rival sits in which corner of the screen.
 *
 * Around a real table your starting tile is the one in front of you, and the
 * player on your left is the one whose tile is on your left. On screen that
 * has to hold too, or the map and the play area disagree about where everyone
 * is — which is what a playtester saw: a red meld box at the bottom and the red
 * starting unit away on the left.
 *
 * It cannot be fixed by moving the units, because every client puts ITSELF at
 * the bottom and the map is the same for all of them. So the seating is worked
 * out here, per viewer: take the angle of each starting tile about the centre
 * of the opening layout, rotate the whole picture until YOUR tile points down,
 * and read the rivals off going clockwise. Same map, four different — and
 * correct — views of it.
 */
function rivalOrder() {
  const spots = RIVAL_SPOT[G.n] || RIVAL_SPOT[4];
  const others = [];
  for (let k = 1; k < G.n; k++) others.push((ME + k) % G.n);
  const starts = G.m && G.m.starts;
  if (!starts || starts.length < G.n) return others.map((i, k) => [i, spots[k] || "top"]);

  const pts = starts.map(([c, r]) => hexCentre(c, r));
  const cx = pts.reduce((a, p) => a + p[0], 0) / pts.length;
  const cy = pts.reduce((a, p) => a + p[1], 0) / pts.length;
  const ang = (i) => Math.atan2(pts[i][1] - cy, pts[i][0] - cx) * 180 / Math.PI;
  const mine = ang(ME);
  /* Clockwise from you. Screen y grows downward, so a growing angle already
   * turns clockwise and no sign flip is needed. */
  const turn = (i) => (((ang(i) - mine) % 360) + 360) % 360;
  others.sort((a, b) => turn(a) - turn(b));
  return others.map((i, k) => [i, spots[k] || "top"]);
}

function renderCorners() {
  const box = $("#corners");
  const sc = G.score();
  let s = "";
  for (const [i, spot] of rivalOrder()) {
    const q = G.P[i];
    const d = sc.find((x) => x.seat === i);
    const won = uiWinner() === i;
    const cls = [
      "corner", spot,
      won ? "won" : "",
      uiActing() === i ? "acting" : "",
      uiDone(i) ? "done" : "",
      flashCls(i),
    ].filter(Boolean).join(" ");

    // nothing until their beat: an empty place at the table is not a lie
    const shown = laid(i) && q.tableau && q.tableau.length;
    const m = shown ? meldFaces(q) : { html: "", n: 0 };
    // victory cards as squares — how many, not which
    const dots = q.vrow.length
      ? `<span class="vdots">${"<i></i>".repeat(q.vrow.length)}</span>` : "";

    // who you are actually playing against — its style, in one word
    const sty = BOT_STYLES[q.style] ? q.style : null;
    s += `<div class="${cls}" data-seat="${i}" title="${
           sty ? `${styleName(sty)}: ${styleNote(sty)} — ` : ""}${
           t("board.seatTip", { seat: seatName(i), score: d.total, gold: q.gold,
                                tier: tierName(q.band()), limit: q.meldLimit() })}${
           won ? " — " + t("board.wonTrick") : ""}">
      <span class="ohead">
        <span class="pin" style="background:${SEAT_C[i]}"><b>${uiPos(i) + 1}</b></span>
        ${sty ? `<span class="sty">${styleName(sty)}</span>` : ""}
        ${won ? CROWN : ""}
        <span class="ometa"><span class="sc">${d.total}</span>
          <span>🪙${q.gold}</span>${dots}</span>
      </span>
      <span class="ocards">${m.html}${meldSlots(q, m.n)}</span>
    </div>`;
  }
  box.innerHTML = s;
}

/* The order strip: everyone in the trick, left to right, in the order they
 * act. Before the trick is settled it is the order of play around the table;
 * after, it is the ranking the trick produced. Dimmed means finished, the
 * pulsing one is acting now, the crown won. No words: colour is identity,
 * position is order. */
function renderTurnbar() {
  const box = $("#turnbar");
  if (!box) return;
  const ord = uiOrder();
  const seq = uiSeq();
  const win = uiWinner();
  let s = "";
  seq.forEach((i, k) => {
    const p = G.P[i];
    const played = !!(p.tableau && p.tableau.length) && laid(i);
    const done = ord ? uiDone(i) : played;
    const now = ord ? uiActing() === i
      : !played && seq.slice(0, k).every((j) => G.P[j].tableau && laid(j));
    const cls = ["tchip", done ? "done" : "", now ? "now" : "",
                 win === i ? "won" : "", i === ME ? "me" : ""].filter(Boolean).join(" ");
    s += `<span class="${cls}" style="--c:${SEAT_C[i]}"
      title="${seatName(i)}${i === ME ? " " + t("board.you") : ""} — ${
        t(ord ? "board.acts" : "board.plays")} ${
        t("board.ofN", { k: k + 1, n: seq.length })}${
        win === i ? ", " + t("board.wonTrick") : ""}">
      <i></i><b>${k + 1}</b>${win === i ? CROWN : ""}</span>`;
  });
  box.innerHTML = s;
}

/* The meld area: always visible, always showing one slot per card your current
 * tier lets you play. Filled slots hold real cards; the rest are faint
 * placeholders, so the limit is a shape rather than a number you have to go
 * and read on the board — and it visibly grows a slot when you climb a tier.
 *
 * The placeholders are deliberately quiet. Playing fewer cards than the limit
 * is a real line in this game, and an empty slot must not read as a mistake. */
let lastMeldLimit = null, grewUntil = 0;

function renderMyMeld() {
  const box = $("#mymeld");
  const p = G.P[ME];
  const lim = p.meldLimit();
  const choosing = mine() && REQ.type === "meld";
  const spending = mine() && REQ.type === "turn";
  const aside = mine() && REQ.type === "setaside";
  const won = uiWinner() === ME;

  let cards = "";
  let n = 0;
  if (aside) {
    /* The forced set-aside happens HERE, on the cards already lying on the
     * table, rather than in a separate list in the prompt. One of these leaves
     * for the shared pile and pays you a coin; there is no way past it. */
    n = REQ.options.length;
    cards = REQ.options.map((c, i) => cardBtn(c, "want", `data-aside="${i}"`, "mid")).join("");
  } else if (choosing) {
    // building one: the cards you have picked so far land here as you pick them
    const picked = SEL.meld.slice().sort(cardSortUI);
    n = picked.length;
    cards = picked.map((c) => cardBtn(c, "sel", `data-unpick="${p.hand.indexOf(c)}"`, "mid")).join("");
  } else if (spending) {
    n = REQ.opts.cards.length;
    cards = REQ.opts.cards.map((m, i) => {
      const on = SEL.card === m.card ? " sel" : "";
      // a card with no legal map action is still worth a coin: never dead
      const nomap = m.options.length ? "" : " nomap";
      return cardBtn(m.card, on + nomap, `data-turn="${i}"`, "mid");
    }).join("");
  } else if (p.tableau && p.tableau.length) {
    const m = meldFaces(p);
    cards = m.html; n = m.n;
  }

  // one slot per allowed card; the winner's extra card may push past the limit
  const slots = Math.max(lim, n);
  const empties = "<span class=\"mslot\"></span>".repeat(Math.max(0, slots - n));

  // a tier climb widens the meld: show that it happened
  if (lastMeldLimit !== null && lim > lastMeldLimit) {
    grewUntil = Date.now() + 650;
    setTimeout(renderTable, 700);              // and take the pulse off again
  }
  lastMeldLimit = lim;

  box.className = [
    choosing || spending || aside ? "" : "idle",
    won ? "won" : "",
    Date.now() < grewUntil ? "grew" : "",
    flashCls(ME),
  ].filter(Boolean).join(" ");
  box.title = t(won ? "board.meldTipWon" : "board.meldTip",
    { seat: seatName(ME), limit: lim, tier: tierName(p.band()) });
  // your own place-card: the same number and crown the rivals wear
  box.innerHTML = `<span class="pin" style="background:${SEAT_C[ME]}">
      <b>${uiPos(ME) + 1}</b></span>${won ? CROWN : ""}` + cards + empties;

  box.querySelectorAll("[data-turn]").forEach((node) =>
    node.addEventListener("click", () => {
      SEL.card = REQ.opts.cards[Number(node.dataset.turn)].card;
      SEL.mode = null; render();
    }));
  box.querySelectorAll("[data-aside]").forEach((node) =>
    node.addEventListener("click", () => answer(REQ.options[Number(node.dataset.aside)])));
  box.querySelectorAll("[data-unpick]").forEach((node) =>
    node.addEventListener("click", () => {
      const c = G.P[ME].hand[Number(node.dataset.unpick)];
      const i = SEL.meld.indexOf(c);
      if (i >= 0) SEL.meld.splice(i, 1);
      render();
    }));
}

// --------------------------------------------------------------- your board
function renderPlayer() {
  const p = G.P[ME];
  const sc = G.score().find((x) => x.seat === ME);
  const res = p.reserve.reduce((a, b) => a + b, 0);

  /* Laid out like the printed player board: one row per tier, unit slots that
   * empty as you settle, and the five victory-row slots pushed right with the
   * centre slot — the one that scores — called out. */
  let s = `<div class="pboard">
    <div class="pb-head"><span class="dot" style="background:${SEAT_C[ME]}"></span>
      <b>${SEAT_N[ME]}</b>
      <span class="tier">${tierName(p.band())}</span>
      <span class="purse">🪙 ${p.gold}</span>
      <span class="score">${t("board.vp", { n: sc.total })}
        <em>${t("board.pop", { pop: sc.pop, row: sc.vrow, dom: sc.dom })}</em></span></div>
    <div class="tiers">
      <div class="tier-row head">
        <span class="mlim" title="${t("board.meldLimit")}">${t("board.colMeld")}</span>
        <span class="tname">${t("board.colTier")}</span>
        <span class="uslots">${t("board.colUnits")}</span>
        <span class="food" title="${t("board.foodPer")}">${t("board.colFood")}</span>
        <span class="mv" title="${t("board.freeMoves")}">${t("board.colMove")}</span>
        <span class="cap" title="${t("board.rankCap")}">${t("board.colCap")}</span>
      </div>`;

  /* THIS game's tier table, not the module default — a table playing a custom
   * layout must show the board it is actually using. */
  const bands = (G && G.BANDS) || BANDS;
  for (let j = 0; j < bands.length; j++) {
    const [name, units, meld, food, moves, , cap] = bands[j];
    const here = j === p.band();
    const left = p.reserve[j];
    let pips = "";
    for (let u = 0; u < units; u++)
      pips += `<i class="uslot${u < left ? " full" : ""}"
        style="${u < left ? `background:${SEAT_C[ME]}` : ""}"></i>`;
    /* The cost as a NUMBER first, then the coin slots that mirror the printed
     * board. The slots alone are the thing players were reading straight past:
     * two small empty circles do not say "this will cost you two gold every
     * time you refill your hand". */
    let coins = food
      ? `<b>${food}</b>` + `<i class="cslot"></i>`.repeat(food)
      : `<span class="free">${t("board.free")}</span>`;
    s += `<div class="tier-row${here ? " here" : ""}">
      <span class="mlim" title="${t("board.meldLimit")}">${meld}</span>
      <span class="tname">${tierName(j)}<em>${units} ${t("board.units")}</em></span>
      <span class="uslots">${pips}</span>
      <span class="food" title="${t("board.foodPer")}">${coins}</span>
      <span class="mv" title="${t("board.freeMoves")}">${moves}<em>${t("board.mv")}</em></span>
      <span class="cap" title="${t("board.rankCap")}">${cap}</span>
    </div>`;
  }
  s += `</div>`;

  /* And say the bill out loud, for the tier you are actually on. A table of
   * numbers is a reference; this is the warning — the feeding cost is the one
   * rule in the game that takes something away from you without you choosing
   * it, and it should never be the first time a player hears about it. */
  const owe = p.food();
  const nextFood = bands.findIndex((b) => b[3] > 0);
  s += `<div class="foodnote${owe ? " due" : ""}">${
    owe ? t("board.foodNote", { n: owe, tier: tierName(p.band()) })
        : t("board.foodNoteFree", { tier: tierName(p.band()),
                                    next: tierName(nextFood < 0 ? 1 : nextFood) })
  }</div>`;

  // victory row — five slots, pushed right, centre slot marked
  /* The row is clickable whenever a step wants a card FROM it — including the
   * famine, where you may cash a card rather than starve. It used to render as
   * dead chips there while the prompt held a separate copy of the same cards,
   * so the lit area had nothing in it to click. */
  const live = mine() && ["turn", "effectA", "feed"].includes(REQ.type);
  const feeding = mine() && REQ.type === "feed";
  const sorted = p.vrow.slice().sort(cardSortUI);
  const pad = 5 - sorted.length;
  s += `<div class="vrowbox"><span class="vlab">${t("board.victoryRow")}</span><div class="vslots">`;
  for (let k = 0; k < 5; k++) {
    const centre = k === 2;
    if (k < pad) {
      s += `<span class="vslot empty${centre ? " centre" : ""}"></span>`;
    } else {
      const c = sorted[k - pad];
      const on = SEL.vcard === c ? " pick" : "";
      const want = feeding && REQ.options.includes(c) ? " want" : "";
      const inner = live
        ? cardBtn(c, on + want, `data-row="${p.vrow.indexOf(c)}"`, "mid")
        : cardChip(c, "", "", "mid");
      s += `<span class="vslot${centre ? " centre" : ""}">${inner}</span>`;
    }
  }
  s += `</div>`;

  /* Perks sit UNDER the slot they belong to, in the same five columns, because
   * "which slot" and "how deep is my row" are the same question and the row
   * above is already showing the answer. Slot 5 never carries one. */
  if (G && G.PERKS) {
    s += `<div class="perkrow">`;
    for (let k = 0; k < 5; k++) {
      const slot = k + 1;
      const id = G.PERKS[slot];
      if (!id) { s += `<span class="pk none"></span>`; continue; }
      const needs = perkSlotNeeds(slot);
      const liveNow = p.vrow.length >= needs;
      const spent = liveNow && !p.perkReady(id);
      const cls = !liveNow ? "locked" : spent ? "spent" : "ready";
      const state = liveNow ? (spent ? t("perk.spent") : t("perk.ready"))
                            : t("perk.needs", { n: needs });
      s += `<span class="pk ${cls} d${slot}" title="${t("perk." + id)}">`
        + `<b>${t("perk." + id + ".name")}</b><em>${state}</em></span>`;
    }
    s += `</div>`;
  }

  const scoring = sorted.length >= 3 ? sorted[sorted.length - 3].r : null;
  s += `<span class="vsum">${tn("board.cards", sorted.length)}${
    scoring !== null ? " " + t("board.centre", { r: scoring }) : ""} = <b>${
    t("board.vp", { n: sc.vrow })}</b>${
    sorted.length && sorted.length < 3
      ? ` <span class="muted">${t("board.centreHint")}</span>` : ""
  }</span></div></div>`;

  // your objective(s) — secret ones are yours alone, open ones are shared
  if (p.objectives && p.objectives.length) {
    const shared = G.OBJECTIVES_MODE === "open";
    s += `<div class="objbox"><span class="vlab">${
      t(shared ? "board.sharedObjectives" : "board.myObjective")}</span><div class="objrow">` +
      p.objectives.map((o) => objCard(o, G.objectiveDone(ME, o) ? "done" : "")).join("") +
      `</div></div>`;
  }

  $("#player").innerHTML = s;

  /* The hand sits directly under the map, in its own strip. When a step wants a
   * card FROM the hand, the ones you may take are lifted (`want`) and the rest
   * go dead — so "which card can I give up" is answered by the cards, not by
   * the sentence above them. */
  const handPick = mine() && ["meld", "bonus", "discard", "retire"].includes(REQ.type);
  const wanted = handPick && REQ.type !== "meld";
  $("#hand").innerHTML = p.hand.slice().sort(cardSortUI).map((c) => {
    const idx = p.hand.indexOf(c);
    const on = SEL.meld.includes(c) ? " sel" : "";
    const playable = !handPick || REQ.type === "meld" || REQ.options.includes(c);
    const state = !handPick ? "" : !playable ? " dead" : wanted ? " want" : "";
    return cardBtn(c, on + state, `data-hand="${idx}"`, "mid");
  }).join("") || `<span class="muted small">${t("board.handEmpty")}</span>`;
  $("#hand").querySelectorAll("[data-hand]").forEach((n) =>
    n.addEventListener("click", () => onHandCard(G.P[ME].hand[Number(n.dataset.hand)])));
  $("#player").querySelectorAll("[data-row]").forEach((n) =>
    n.addEventListener("click", () => {
      const c = G.P[ME].vrow[Number(n.dataset.row)];
      // during a famine the click IS the answer: that card is cashed for food
      if (mine() && REQ.type === "feed") {
        if (REQ.options.includes(c)) answer(c);
        return;
      }
      SEL.vcard = SEL.vcard === c ? null : c;
      SEL.mode = null; SEL.card = null;
      render();
    }));
}

function onHandCard(c) {
  if (!mine()) return;
  if (REQ.type === "meld") {
    const i = SEL.meld.indexOf(c);
    if (i >= 0) SEL.meld.splice(i, 1); else SEL.meld.push(c);
    render();
    return;
  }
  if (["bonus", "discard", "retire"].includes(REQ.type) && REQ.options.includes(c)) {
    if (REQ.type === "retire" && RESEARCH) { RESEARCH.retired = c; RESEARCH.stage = "buy"; }
    answer(c, REQ.type === "retire" && !!RESEARCH);
  }
}

// --------------------------------------------------------------- prompt
function meldOk() {
  return SEL.meld.length >= 1 && SEL.meld.length <= G.P[ME].meldLimit()
         && isLegalMeld(SEL.meld);
}

function renderPrompt() {
  const bar = $("#prompt");
  bar.innerHTML = "";
  /* gameOver(), not finished(): during the extra round §11 grants, finished()
   * is already true and this would replace the player's turn with the result. */
  if (gameOver()) return renderFinal(bar);
  if (!REQ) { bar.appendChild(el("div", "ask muted", t("ask.waiting"))); return; }
  if (!mine()) { bar.appendChild(el("div", "ask muted", t("ask.wait"))); return; }

  const ask = (html) => bar.appendChild(el("div", "ask", html));
  const btn = (label, fn, cls, dis) => {
    const b = el("button", "go " + (cls || ""), label);
    b.disabled = !!dis;
    b.addEventListener("click", fn);
    bar.appendChild(b);
    return b;
  };
  const p = G.P[ME];

  switch (REQ.type) {
    case "meld": {
      const sum = SEL.meld.reduce((a, c) => a + c.r, 0);
      const lim = p.meldLimit();
      /* Two different reasons a selection can be unplayable, and saying the
       * wrong one is worse than saying nothing: 8-9-9 IS an unbroken run, it
       * is simply three cards at a limit of two. */
      let verdict = "";
      if (SEL.meld.length) {
        if (!isLegalMeld(SEL.meld)) {
          // the engine says why, in the terms THIS game's variants allow
          verdict = `<span class='bad'>${meldFault(SEL.meld)}</span>`;
        } else if (SEL.meld.length > lim) {
          verdict = `<span class='bad'>${t("ask.meld.over", {
            n: SEL.meld.length, tier: tierName(p.band()), lim,
            drop: SEL.meld.length - lim })}</span>`;
        } else {
          verdict = `<span class='ok'>${t("ask.meld.legal")}</span>`;
        }
      }
      const mr = meldRules();
      const what = t("ask.meld." + (mr.combo && mr.friends ? "both"
        : mr.combo ? "combo" : mr.friends ? "friends" : "run"));
      ask(t("ask.meld", { what, lim }) + (SEL.meld.length
        ? ` · ${t("ask.meld.count", { n: SEL.meld.length, sum })} · ${verdict}` : ""));
      btn(t("btn.playMeld"), () => {
        const want = new Set(SEL.meld);
        answer(REQ.options.find((o) => o.length === want.size && o.every((c) => want.has(c))));
      }, "", !meldOk());
      break;
    }

    case "turn":
      if (RESEARCH && !["preview", "over"].includes(RESEARCH.stage)) {
        RESEARCH.blocked = !RESEARCH.bought;     // engine ended it early
        RESEARCH.stage = "over";
      }
      return renderTurn(bar, ask, btn, p);

    case "bonus":
      ask(t("ask.bonus")); break;
    case "setaside":
      /* No skip: matching the winner's count costs a card. The choice is made
       * on the cards themselves, in the meld area — see renderMyMeld. */
      ask(t("ask.setaside"));
      break;
    case "discard":
      ask(t("ask.discard"));
      break;
    case "retire":
      if (RESEARCH) {
        RESEARCH.drew = REQ.drew;
        researchPanel(bar, "retire", p);
        ask(retireAsk(p));
      } else {
        ask(retireAsk(p));
      }
      break;
    case "buy":
      ask(t("ask.buy", { cap: p.rankCap() }));
      btn(t("btn.cancel"), () => answer(null), "alt");
      break;
    case "effectA":
      if (SEL.vcard) { vcardPanel(bar, p); btn(t("btn.noEffect"), () => answer(null), "alt"); break; }
      ask(t("ask.declare"));
      btn(t("btn.skip"), () => answer(null), "alt");
      break;
    case "feed":
      /* Chosen on the row itself, where the cards are — see renderPlayer. */
      ask(t("ask.famine", { owed: REQ.owed, gold: p.gold }));
      btn(t("btn.takeLoss"), () => answer(null), "alt");
      break;
    case "objective": {
      ask(t("ask.objective"));
      const pick = el("div", "objpick");
      pick.innerHTML = REQ.options.map((o, i) => objCard(o, "", `data-obj="${i}"`)).join("");
      bar.appendChild(pick);
      pick.querySelectorAll("[data-obj]").forEach((n) =>
        n.addEventListener("click", () => answer(REQ.options[Number(n.dataset.obj)])));
      break;
    }
    case "conquest":
      ask(tn("ask.conquest", REQ.left, {
        name: fxTextD(REQ.card.r).d.split(":")[0], left: REQ.left,
        settle: t(REQ.maySettle ? "ask.conquest.settle" : "ask.conquest.nosettle") }));
      btn(t("btn.stop"), () => answer(null), "alt");
      break;
    case "colony": {
      const one = REQ.terrains.length === 1;
      if (!SEL.colonyCell) {
        ask(tn("ask.colony", REQ.left, {
          left: REQ.left,
          settles: REQ.settles ? t("ask.colony.settles", { n: REQ.settles }) : "",
          terrain: one ? TL[REQ.terrains[0]] : t("ask.colony.any") }));
        btn(t("btn.stopHere"), () => answer(null), "alt");
      } else {
        ask(t("ask.terrain"));
        for (const terr of REQ.terrains)
          btn(TL[terr], () => answer({ cell: SEL.colonyCell, terrain: terr }), "terr " + terr);
        btn(t("btn.back"), () => { SEL.colonyCell = null; render(); }, "alt");
      }
      break;
    }
    case "waterexplore": {
      /* A landfall has already had its cell chosen — that WAS the move. Asking
       * for it a second time is the step that made the whole thing look broken:
       * the player clicks the empty hex, and the game answers by asking them to
       * click an empty hex. So go straight to the terrain. */
      const cell = REQ.landfall ? REQ.options[0] : SEL.waterCell;
      if (!cell) {
        ask(t("ask.water"));
        btn(t("btn.skip"), () => answer(null), "alt");
      } else {
        ask(t(REQ.landfall ? "ask.landTerrain" : "ask.terrain"));
        for (const terr of REQ.terrains)
          btn(TL[terr], () => answer({ cell, terrain: terr }), "terr " + terr);
        if (!REQ.landfall)
          btn(t("btn.back"), () => { SEL.waterCell = null; render(); }, "alt");
      }
      break;
    }
  }
}

/* Which card leaves your hand. Under the "lowest" rule the engine offers only
 * the lowest rank you hold, so the sentence says what the cards already show:
 * those are lit, everything else is dead. */
function retireAsk(p) {
  const opts = REQ.options || [];
  const low = opts.length ? opts[0].r : null;
  return REQ.rule === "lowest"
    ? t("ask.retire.lowest", { low,
        more: opts.length > 1 ? t("ask.retire.lowest.more", { n: opts.length }) : "" })
    : t("ask.retire.any");
}

/* The whole action laid out at once: what will happen, in what order, what it
 * costs, and which step we are on. The complaint this answers is not "which
 * button" but "what am I in the middle of, and when does it end". */
function researchPanel(bar, stage, p) {
  const R = RESEARCH || {};
  const cap = p.rankCap();
  const step = (n, state, label, result) =>
    `<li class="rs ${state}"><span class="marker">${
      state === "done" ? "✓" : state === "now" ? "▸" : "·"}</span>
      <span class="rl">${label}</span>
      ${result ? `<span class="rr">${result}</span>` : ""}</li>`;

  const ORDER = ["preview", "retire", "buy", "over"];
  const st = (n) => stage === n ? "now"
    : (ORDER.indexOf(stage) > ORDER.indexOf(n) ? "done" : "todo");

  const box = el("div", "research");
  const cardName = (c) => c.r + SUIT_LETTER[c.s];
  box.innerHTML = `
    <div class="rhead"><b>${t("res.title")}</b>
      <span class="muted">${stage === "preview" ? t("res.preview")
        : stage === "over" ? t("res.complete")
        : t("res.step", { n: ({ retire: 1, buy: 2 })[stage] })}</span></div>
    ${R.drew ? `<div class="rdrew">${t("res.drew", {
      card: cardChip(R.drew.card), slot: R.drew.slot + 1 })}</div>` : ""}
    <ol class="rsteps">
      ${step(1, st("retire"),
        t(G.RETIRE_RULE === "lowest" ? "res.step1.lowest" : "res.step1.any"),
        R.retired ? t("res.step1.done", { card: cardName(R.retired) }) : "")}
      ${step(2, st("buy"), t("res.step2", { cap }),
        R.bought ? t("res.step2.done", { card: cardName(R.bought) }) : "")}
    </ol>
    <div class="rfoot">${stage === "preview" ? t("res.cost", { gold: p.gold })
      : stage === "over" ? (R.blocked ? t("res.blocked", { cap }) : t("res.done"))
      : t("res.running")}</div>`;
  bar.appendChild(box);
  return box;
}

/* A victory card, face up, with its three effects as the buttons. This is the
 * whole point of the row: a retired card is not a point token, it is a choice
 * between winning a trick, founding colonies, and gold. Each effect says why it
 * cannot be used rather than just going grey. */
function vcardPanel(bar, p) {
  const c = SEL.vcard;
  if (!c) return false;
  const e = fxText(c.r);
  const inCardPhase = REQ.type === "effectA";
  const o = REQ.type === "turn" ? REQ.opts : null;

  const third = thirdEffect(c);
  const canA = inCardPhase;
  const canB = !!o && o.colonyCards.includes(c);
  const canThird = !!o && (deckIsD() ? !o.conquestBlocked : true);
  const whyThird = !o ? t("vcard.mapPhase")
    : deckIsD() ? t(o.conquestBlocked || "") : t("vcard.mapPhase");
  /* Say the true reason. A 16–20 colony takes ANY terrain, so "no tiles of that
   * terrain" would be a lie for exactly the cards most likely to be spent. */
  const sameSuit = effectBv22(c.r)[2];
  const whyB = !o ? t("vcard.mapPhase")
    : o.colonyBlocked ? t(o.colonyBlocked)
    : sameSuit ? t("vcard.noTerrain", { terrain: TL[c.s] })
    : t("vcard.noTiles");

  const box = el("div", "vpanel");
  box.innerHTML = `
    <div class="vp-card">${cardChip(c, "", "", "full")}</div>
    <div class="vp-opts">
      <div class="vp-lead">${t("vcard.lead")}</div>
      ${[["A", e.a, canA, inCardPhase ? "" : t("vcard.cardPhase")],
         ["B", e.b, canB, whyB],
         [third.key, third.long, canThird, whyThird]]
        .map(([k, txt, ok, why]) => `
        <button class="vp-opt${ok ? "" : " off"}" data-fx="${k}" ${ok ? "" : "disabled"}>
          <span class="ab">${k}</span>
          <span class="vp-txt">${txt}</span>
          ${ok ? "" : `<span class="vp-why">${why}</span>`}
        </button>`).join("")}
    </div>`;
  bar.appendChild(box);

  box.querySelectorAll("[data-fx]").forEach((n) =>
    n.addEventListener("click", () => {
      const k = n.dataset.fx;
      if (k === "A") return answer(c);
      if (k === "B") return answer({ kind: "colony", card: c });
      answer({ kind: k === "D" ? "conquest" : "cashRow", card: c });
    }));
  const back = el("button", "go alt", t("btn.keepCard"));
  back.addEventListener("click", () => { SEL.vcard = null; render(); });
  bar.appendChild(back);
  return true;
}

/* An objective card: the chain it asks for, drawn as three terrain chips with
 * the middle one marked, because the shape is the whole point. */
function objCard(o, cls, attr) {
  // `terr`, not `t` — `t` is the translator, and shadowing it here would be a
  // silent, language-shaped bug
  const chip = (terr, mid) => `<span class="ochip${mid ? " mid" : ""}"
    style="background:${TC[terr]}" title="${TL[terr]}">${SUIT_LETTER[terr]}</span>`;
  const tag = attr === undefined ? "span" : "button";
  return `<${tag} class="objcard ${cls || ""}" ${attr || ""}>
    <span class="oname">${objName(o)}<em>${t("obj.points", { n: o.points })}</em></span>
    <span class="ochain">${chip(o.a)}${chip(o.mid, true)}${chip(o.b)}</span>
    <span class="oflav">${t(o.a === o.b ? "obj.chainSame" : "obj.chain",
      { a: TL[o.a], mid: TL[o.mid], b: TL[o.b] })}</span>
  </${tag}>`;
}

function rowPicker(bar, options, fn) {
  const row = el("div", "rowpick");
  row.innerHTML = options.map((c, i) => cardBtn(c, "", `data-p="${i}"`)).join("");
  bar.appendChild(row);
  row.querySelectorAll("[data-p]").forEach((n) =>
    n.addEventListener("click", () => fn(options[Number(n.dataset.p)])));
}

/* The map phase: everything still legal, all at once, in any order. */
function renderTurn(bar, ask, btn, p) {
  const o = REQ.opts;
  const left = o.cards.length;

  if (RESEARCH && RESEARCH.stage === "preview") {
    researchPanel(bar, "preview", p);
    btn(t("btn.beginResearch"), () => {
      RESEARCH = { stage: "retire" };
      answer({ kind: "research" });
    });
    btn(t("btn.notNow"), () => { RESEARCH = null; render(); }, "alt");
    return;
  }
  if (RESEARCH && RESEARCH.stage === "over") {
    researchPanel(bar, "over", p);
    btn(t("btn.continueTurn"), () => { RESEARCH = null; render(); });
    return;
  }

  if (SEL.mode === "move") {
    ask(t("ask.move", { n: o.moves,
      what: t(SEL.moveSrc ? "ask.move.dest" : "ask.move.pick") }));
    btn(t(SEL.moveSrc ? "btn.pickAnother" : "btn.cancel"), () => {
      if (SEL.moveSrc) SEL.moveSrc = null; else SEL.mode = null;
      render();
    }, "alt");
    return;
  }
  if (SEL.mode === "fortify") {
    ask(t("ask.fortify"));
    btn(t("btn.cancel"), () => { SEL.mode = null; render(); }, "alt");
    return;
  }
  if (SEL.vcard) { vcardPanel(bar, p); return; }

  ask(t(left ? "ask.turn" : "ask.turn.spent"));

  // the cards themselves live on the map edge (renderMyMeld); here we only
  // offer what to do with the one that is selected
  if (left && SEL.card) {
    const e = o.cards.find((m) => m.card === SEL.card);
    if (!e.options.length)
      ask(t("ask.noHex"));
    btn(t("btn.cash", { card: SEL.card.r + SUIT_LETTER[SEL.card.s] }),
        () => answer({ kind: "cash", card: SEL.card }), "alt");
  } else if (left && o.cards.every((m) => !m.options.length)) {
    ask(t("ask.noHexAny"));
  }

  const acts = el("div", "acts");
  bar.appendChild(acts);
  const abtn = (label, fn, dis, title) => {
    const b = el("button", "go alt" + (dis ? " off" : ""), label);
    if (title) b.title = title;
    b.disabled = !!dis;
    b.addEventListener("click", fn);
    acts.appendChild(b);
  };

  /* The price is on the button, not in a tooltip. Under the escalating rule it
   * goes up with every research this turn, and a player must be able to see
   * what the next one costs before committing to it — a tooltip is no use on a
   * phone, where the first sight of the price would be the gold leaving. */
  const rCost = o.researchCost === undefined ? 1 : o.researchCost;
  const rDone = (o.researchesUsed || 0) > 0;
  abtn(t(rCost > 1 ? "btn.researchAgain" : "btn.research", { n: rCost })
         + (rDone && !o.canResearch ? " ✓" : ""),
       () => { RESEARCH = { stage: "preview" }; render(); }, !o.canResearch,
       o.researchBlocked ? t(o.researchBlocked) : t("tip.research"));
  abtn(t("btn.move", { n: o.moves }),
       () => { SEL.mode = "move"; SEL.card = null; render(); },
       !o.moves || !o.moveSources.length,
       t(!o.moves ? "tip.noMoves" : "tip.nowhereToGo"));
  abtn(t("btn.fortifyAct"), () => { SEL.mode = "fortify"; SEL.card = null; render(); },
       !o.fortifyCells.length, t(p.gold < 1 ? "why.research.gold" : "tip.nothingToWall"));

  const endLabel = left ? tn("btn.endTurnCards", left) : t("btn.endTurn");
  const end = el("button", "go end", endLabel);
  end.addEventListener("click", () => answer({ kind: "end" }));
  acts.appendChild(end);
}

function renderFinal(bar) {
  const sc = G.score().slice().sort((a, b) => b.total - a.total || b.gold - a.gold);
  let s = `<div class="ask">${t("final.over", {
    why: t(G.endedOn || ""), rounds: G.round })}</div>`;
  const anyObj = sc.some((d) => d.objDone && d.objDone.length);
  s += `<table class="final"><tr><th>${t("final.seat")}</th><th>${t("final.pop")}</th>
        <th>${t("final.row")}</th><th>${t("final.dom")}</th>${
        anyObj ? `<th>${t("final.obj")}</th>` : ""}<th>${t("final.total")}</th></tr>`;
  for (const d of sc) {
    s += `<tr class="${d.seat === ME ? "me" : ""}"><td><span class="dot"
      style="background:${SEAT_C[d.seat]}"></span>${SEAT_N[d.seat]}${
      d.seat === ME ? " " + t("board.you") : ""}</td><td>${d.pop}</td><td>${d.vrow}</td>
      <td>${d.dom}</td>`;
    if (anyObj) {
      s += `<td>${(d.objDone || []).map((x) =>
        `<span class="${x.done ? "ok" : "muted"}">${objName(x.o)}${
          x.done ? ` +${x.o.points}` : " ✗"}</span>`).join("<br>") || "—"}</td>`;
    }
    s += `<td><b>${d.total}</b></td></tr>`;
  }
  bar.innerHTML = s + `</table>`;
  renderFeedback(bar);
  const again = el("button", "go", t("btn.newGame"));
  again.addEventListener("click", () => {
    $("#setup").classList.remove("hide");
    $("#game").classList.remove("show");
    document.body.classList.remove("playing");
  });
  bar.appendChild(again);
}

/* ---- the end-of-game form ----
 *
 * Asked here and nowhere else, because this is the one moment a player has
 * both the whole game in their head and nothing left to do. Four questions,
 * two of them one tap; everything else is optional. What is actually sent is
 * stated plainly above the button — a report that quietly ships a browser
 * string is not a report anybody should trust.
 */
let FB = { rating: null, again: null };
function renderFeedback(bar) {
  if (!REP) return;
  if (REP.sent) {                                   // already handed over
    bar.appendChild(el("p", "fbdone", t("fb.sent", { id: REP.id })));
    return;
  }
  reportFinish(REP, G);
  const box = el("div", "fb");
  const seg = (name, opts, cur, pick) => {
    const g = el("div", "seg");
    for (const [v, label] of opts) {
      const b = el("button", "fbopt" + (cur === v ? " on" : ""), label);
      b.type = "button";
      b.addEventListener("click", () => { pick(v); renderPrompt(); });
      g.appendChild(b);
    }
    return g;
  };
  box.appendChild(el("h3", null, t("fb.title")));
  box.appendChild(el("p", "hint", t("fb.lede")));

  box.appendChild(el("label", "fblab", `${t("fb.rating")} <span class="muted">${
    t("fb.rating.1")} → ${t("fb.rating.5")}</span>`));
  box.appendChild(seg("rating", [1, 2, 3, 4, 5].map((n) => [n, String(n)]),
    FB.rating, (v) => { FB.rating = v; }));

  box.appendChild(el("label", "fblab", t("fb.again")));
  box.appendChild(seg("again", [["yes", t("fb.again.yes")], ["maybe", t("fb.again.maybe")],
    ["no", t("fb.again.no")]], FB.again, (v) => { FB.again = v; }));

  const area = (id, label, ph, rows) => {
    box.appendChild(el("label", "fblab", label));
    const a = el("textarea");
    a.id = id; a.rows = rows || 3; a.placeholder = ph;
    a.value = FB[id] || "";
    a.addEventListener("input", () => { FB[id] = a.value; });
    box.appendChild(a);
  };
  area("confusing", t("fb.confusing"), t("fb.confusing.ph"), 3);
  area("best", t("fb.best"), t("fb.best.ph"), 2);
  box.appendChild(el("label", "fblab", t("fb.name")));
  const nm = el("input");
  nm.id = "fb-name"; nm.type = "text"; nm.placeholder = t("fb.name.ph");
  nm.value = FB.name || "";
  nm.addEventListener("input", () => { FB.name = nm.value; });
  box.appendChild(nm);

  box.appendChild(el("p", "hint what", t("fb.what", {
    id: REP.id, size: Math.round(reportSize(REP) / 1024) + " kB",
    flags: REP.flags.length })));

  const row = el("div", "fbrow");
  const send = el("button", "go", t("fb.send"));
  send.addEventListener("click", () => {
    send.disabled = true; send.textContent = t("fb.sending");
    finishFeedback().then((how) => {
      REP.sent = how;
      renderPrompt();
    });
  });
  const down = el("button", "go alt", t("fb.download"));
  down.addEventListener("click", () => {
    reportFeedback(REP, FB);
    downloadReport(REP);
    REP.sent = "download";
    renderPrompt();
  });
  row.appendChild(send); row.appendChild(down);
  box.appendChild(row);
  bar.appendChild(box);
}

/* Post it if there is somewhere to post it, and fall back to a file if not —
 * a playtester who has just written three sentences must never lose them to a
 * network error. */
function finishFeedback() {
  reportFeedback(REP, FB);
  const url = BUILD.reportUrl;
  if (!url) { downloadReport(REP); return Promise.resolve("download"); }
  return fetch(url, { method: "POST", headers: { "content-type": "application/json" },
                      body: JSON.stringify(REP) })
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    /* A 200 is not the same as "kept". The service will accept a report and
     * say `stored: false` when it has nowhere durable to put it — and the one
     * thing this must never do is thank somebody for an evening's work and
     * quietly drop it. */
    .then((r) => { if (!r || r.stored === false) throw new Error("not stored"); return "post"; })
    .catch(() => { downloadReport(REP); return "failed"; });
}

function downloadReport(rep) {
  try {
    const blob = new Blob([JSON.stringify(rep, null, 1)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = reportFilename(rep);
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  } catch (e) { console.error(e); }
}

// --------------------------------------------------------------- sidebar
function renderMarket() {
  const p = G.P[ME];
  const lit = mine() && REQ.type === "buy" ? new Set(REQ.options) : null;
  /* No heading: the cards above your rank cap are simply faded, which says
   * "you may not take these" without a sentence. */
  /* The deck sits at the head of the row, face down, wearing what is left of
   * it — a card comes off it every research, and when it runs out the game is
   * near its end. */
  let s = `<div class="deckpile${G.deck.length ? "" : " empty"}" id="deckpile"
    title="${t("board.deckTip", { n: G.deck.length })}"><b>${G.deck.length}</b>
    <em>${t("board.deck")}</em></div><div class="grid">`;
  const pileTail = `<div class="deckpile shared${G.pile.length ? "" : " empty"}" id="pilebox"
    title="${tn("board.sharedTip", G.pile.length)}"><b>${G.pile.length}</b>
    <em>${t("board.shared")}</em></div>`;
  for (let k = 0; k < G.grid.length; k++) {
    const top = G.gridTop(k);
    const on = lit && lit.has(k);
    const over = top && top.r > p.rankCap();
    s += `<button class="slot${on ? " hot" : ""}${over ? " over" : ""}" data-slot="${k}"
      title="${over ? t("board.slotOver", { r: top.r, cap: p.rankCap() })
                    : top ? t("board.slotRank", { r: top.r }) : t("board.slotEmpty")}">`;
    s += top ? cardChip(top, "", "", "mid") : `<span class="muted">—</span>`;
    s += `<em>${G.grid[k].length > 1 ? "×" + G.grid[k].length : ""}</em></button>`;
  }
  $("#market").innerHTML = s + `</div>` + pileTail;
  $("#market").querySelectorAll("[data-slot]").forEach((n) =>
    n.addEventListener("click", () => {
      const k = Number(n.dataset.slot);
      if (!mine() || !REQ.options || !REQ.options.includes(k)) return;
      if (REQ.type === "buy") {
        if (RESEARCH) { RESEARCH.bought = G.gridTop(k); RESEARCH.stage = "over"; }
        answer(k, true);
      }
    }));
}

/* The sidebar is gone — rivals live in the map corners now. All that is left is
 * a quiet log strip, and the round counter in the header. */
/* One log line. `log.recycle` carries a clause that only appears when cards
 * were actually drawn, so it is composed rather than looked up whole. */
function logLine(key, vars) {
  const v = Object.assign({}, vars || {});
  if (key === "log.recycle")
    v.drew = v.drew ? t("log.recycle.drew", { n: v.drew }) : "";
  return tn(key, v.n !== undefined ? v.n : 1, v);
}

function renderSide() {
  /* The engine logs a KEY and its variables; the sentence is made here, in
   * whatever language is on. */
  $("#log").innerHTML = G.log.slice(-6)
    .map(([r, key, vars]) => `<div><b>R${r}</b> ${
      logLine(key, vars)}</div>`).join("");
  $("#log").scrollTop = $("#log").scrollHeight;
  $("#roundno").textContent = G.round;
  renderEndBanner();
}

/* How the game ends, said out loud while there is still time to act on it.
 *
 * §11 gives a whole extra round after a trigger fires, which is the difference
 * between a scramble and an ambush — but only if the player knows the clock has
 * started. The log line scrolls away and "· last round" in the corner is four
 * small words next to a number nobody is watching. So: a banner, in the panel
 * they are already reading, naming what tripped the trigger and how much game
 * is left.
 *
 * Two states, because they call for different play. `round < finalRounds` means
 * this round finishes and then one more; `round === finalRounds` means this is
 * the last one and nothing after it counts. */
function renderEndBanner() {
  const box = $("#endbanner"), note = $("#endnote");
  if (!box) return;
  if (!G || !G.endedOn) {
    box.hidden = true; box.textContent = "";
    if (note) { note.textContent = ""; note.classList.remove("final"); }
    return;
  }
  /* Once the game is actually over, this must go.
   *
   * It used to stay up, so the final panel appeared directly beneath a banner
   * still promising "the game ends when this round is over" — which reads as the
   * last round and the result being announced in the same breath, and had a
   * playtester reporting that the extra round was never played. It was: the
   * engine gives a full one every time, and this was the banner outliving it.
   * The result table below says everything that needs saying. */
  if (gameOver()) {
    box.hidden = true; box.textContent = "";
    if (note) { note.textContent = t("app.gameOver"); note.classList.add("final"); }
    return;
  }
  const last = G.finalRounds !== null && G.round >= G.finalRounds;
  box.hidden = false;
  box.classList.toggle("final", last);
  box.innerHTML = `<b>${t(last ? "end.final" : "end.soon")}</b>`
    + `<span class="why">${t("end.why", { why: t(G.endedOn) })}</span>`;
  if (note) {
    note.textContent = t(last ? "app.lastRound" : "app.endTriggered");
    note.classList.toggle("final", last);
  }
}

window.addEventListener("DOMContentLoaded", () => {
  $("#start").addEventListener("click", startGame);
  $("#zin").addEventListener("click", () => zoom(0.12));
  $("#zout").addEventListener("click", () => zoom(-0.12));
  $("#zfit").addEventListener("click", zoomFit);
  initPan();
  $("#n-players").addEventListener("change", renderSeats);
  $("#undo").addEventListener("click", doUndo);
  $("#restart").addEventListener("click", restartGame);
  $("#abort").addEventListener("click", abortGame);
  $("#flag").addEventListener("click", openFlag);
  $("#flag-cancel").addEventListener("click", closeFlag);
  $("#flag-save").addEventListener("click", saveFlag);
  $("#flagbox").addEventListener("click", (e) => { if (e.target.id === "flagbox") closeFlag(); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !$("#flagbox").hidden) closeFlag();
  });
  $("#reseed").addEventListener("click", () => {
    $("#seed").value = Math.floor(Math.random() * 1e6);
  });
  $("#bot-level").addEventListener("change", levelNote);
  if ($("#layout")) $("#layout").addEventListener("change", syncLayoutRow);
  if ($("#layout-custom")) $("#layout-custom").addEventListener("input", syncLayoutRow);
  if ($("#meld-score")) $("#meld-score").addEventListener("change", syncALadderRow);
  $("#pass-go").addEventListener("click", () => {
    PASSED = PENDING_SEAT === null ? PASSED : PENDING_SEAT;
    PENDING_SEAT = null;
    hidePass();
    render();
    playEvents();
  });
  setLang(pickLang());
  applyLang();
  syncLayoutRow();                  // after applyLang, so the hint is translated
  syncALadderRow();
  netSetup();
  window.addEventListener("resize", () => { if (G) renderMap(); });
});

/* What the chosen difficulty actually does, in one line under the control. */
function levelNote() {
  const note = $("#level-note");
  if (note) note.textContent = t("setup.level." + radioValue("#bot-level", "normal"));
}

/* Put the current language on the page: every element carrying data-i18n, the
 * controls built from engine tables, and — if a game is running — the whole
 * board, since almost everything on it is a translated string. */
function applyLang() {
  /* Language as flags, side by side: every option visible without opening
   * anything, and the name beside the flag because a flag alone is not a
   * language. */
  const box = $("#lang");
  if (box) {
    box.innerHTML = Object.keys(LANGS).map((k) => `
      <input type="radio" name="lang" id="lang-${k}" value="${k}"${
        k === getLang() ? " checked" : ""}>
      <label for="lang-${k}"><span class="flag" aria-hidden="true">${t("flag." + k)}</span>
        <span class="lname">${LANGS[k]}</span></label>`).join("");
    box.querySelectorAll("input").forEach((n) =>
      n.addEventListener("change", () => { setLang(n.value); applyLang(); }));
  }
  document.querySelectorAll("[data-i18n]").forEach((n) => {
    const key = n.dataset.i18n;
    if (n.dataset.i18nAttr) n.setAttribute(n.dataset.i18nAttr, t(key));
    else n.innerHTML = t(key);
  });
  renderSeats();
  levelNote();
  renderNav();
  renderBuild();
  if (G) render();
}

/* Which build a person is looking at, in the smallest honest form. */
function renderBuild() {
  const n = $("#buildline");
  if (!n) return;
  n.textContent = t("build.line", { version: BUILD.version, commit: BUILD.commit,
                                    built: BUILD.built.slice(0, 10) });
  if (BUILD.dirty) n.innerHTML += ' <span class="dirty">' + t("build.dirty") + "</span>";
}

/* The game's own controls: take one action back, replay this deal, or leave.
 * Always in the header, always in the same order. */
function renderNav() {
  const set = (id, label, tip) => {
    const n = $(id);
    if (!n) return;
    n.textContent = label;
    n.title = tip;
    n.setAttribute("aria-label", label);
  };
  set("#undo", t("nav.undo"), t("nav.undo.tip"));
  set("#restart", t("nav.restart"), t("nav.restart.tip"));
  /* Re-dealing is not one client's decision when other people are at the
   * table, so it is simply not offered there. */
  const rs = $("#restart");
  if (rs) rs.hidden = netOn();
  set("#abort", t("nav.abort"), t("nav.abort.tip"));
  updateFlag();
  updateUndo();
}

/* =====================================================================
 * Playing with people who are not in the room
 *
 * The local game and the remote one are the SAME game — same engine, same
 * screen, same clicks. Three things differ, and they are all consequences of
 * one rule: the server decides the order in which answers happen.
 *
 *   1. Your answer is sent, not applied. It takes effect when it comes back,
 *      because a client that moved first and asked afterwards would be showing
 *      you a board nobody else can see.
 *   2. The view never follows somebody else's turn. In hot seat the board
 *      moves to whoever is being asked; here it stays on your own seat, and
 *      the other players' hands are none of your business.
 *   3. Undo is a request. The server holds the same limit — back to the start
 *      of your own map turn — and works it out from the log rather than
 *      trusting you about it.
 * ===================================================================== */

let LOBBY = null;                  // the last state message, while we wait

function netHandlers() {
  return {
    welcome: (m) => {
      LOBBY = m.state;
      if (m.state.phase === "lobby") showLobby();
      else startNetGame(m.state);          // walked back into a running game
    },
    seats: (st) => { LOBBY = st; if (!G) showLobby(); else renderTable(); },
    start: (st) => startNetGame(st),
    answer: (m) => applyRemote(m.step, m.token),
    undo: (m) => applyRemoteUndo(m.step),
    sync: (st) => resyncFrom(st),
    status: () => netBar(),
    error: (why) => netSay(t(why) === why ? why : t(why), true),
  };
}

/* ---- the lobby ---- */

function showLobby() {
  document.body.classList.add("lobby");
  document.body.classList.remove("playing");
  netBar();
  const st = LOBBY;
  if (!st) return;
  const iAmHost = st.seats.some((x) => x.you && x.seat === st.host);
  $("#lobby-lede").textContent = iAmHost ? t("net.lobby.ledeHost")
    : t("net.lobby.lede", { host: (st.seats[st.host] || {}).name || seatName(st.host) });
  $("#lobby-link").value = netLink(st.code);
  $("#lobby-copy").textContent = t("net.copy");
  $("#lobby-code").textContent = t("net.codeIs", { code: st.code });
  $("#lobby-note").textContent = t("net.note", {
    n: st.seats.filter((x) => x.taken).length, total: st.n });

  const box = $("#lobby-seats");
  box.innerHTML = "";
  for (const x of st.seats) {
    const row = el("div", "lseat" + (x.you ? " mine" : "") + (x.taken && !x.here ? " away" : ""));
    row.appendChild(el("span", "dot")).style.background = SEAT_C[x.seat];
    row.appendChild(el("span", "who", x.taken ? x.name : t("net.seat.free")));
    if (x.you) row.appendChild(el("span", "tag", t("net.seat.you")));
    else if (x.taken && !x.here) row.appendChild(el("span", "tag", t("net.seat.away")));
    else if (!x.taken) {
      const b = el("button", null, t("net.seat.take"));
      b.addEventListener("click", () => netSend({ t: "sit", seat: x.seat }));
      row.appendChild(b);
    }
    box.appendChild(row);
  }
  const go = $("#lobby-start");
  go.textContent = t("net.start");
  go.hidden = !iAmHost;
  $("#lobby-leave").textContent = t("net.leave");
}

/* ---- the game itself ---- */

function startNetGame(st) {
  LOBBY = st;
  document.body.classList.remove("lobby");
  lastMeldLimit = null;
  GARGS = { n: st.n, seed: st.seed,
            opts: Object.assign({ humans: st.humans.slice() }, st.rules) };
  HUMANS = st.humans.slice();
  ME = netMySeat();
  PASSED = ME;                                  // no device is being handed over
  REP = newReport(BUILD, GARGS, {
    lang: getLang(), session: st.code,
    players: st.seats.map((x) => ({ seat: x.seat, kind: x.taken ? "human" : "bot",
                                    style: null, name: x.name })),
  });
  NETQ = [];
  ZOOM = null; PAN = { x: 0, y: 0 };
  hidePass();
  $("#setup").classList.add("hide");
  $("#game").classList.add("show");
  document.body.classList.add("playing");
  /* Straight to the position, whether that is the start or the middle of a
   * game somebody is walking back into. */
  rebuildFrom(st.log || []);
  netBar();
}

/* Build the game from a list of answers and nothing else.
 *
 * Not by feeding them to the running generator one at a time: `nextRound` is
 * asynchronous — it is on a timer so bot turns can be watched — so a loop that
 * pumped answers would stop dead at the first round boundary with the rest of
 * the game unplayed. Replay is synchronous, which is exactly what catching up
 * and resynchronising both need. It is also the same function undo uses.
 */
function rebuildFrom(log) {
  LOG = log.slice();
  const out = replay(LOG.length);
  G = out.g; IT = out.it; REQ = out.req;
  if (G && G.events) G.events.length = 0;       // history, not a replay to watch
  SEL = blankSel(); RESEARCH = null; lastZone = null;
  MARK = 0; BLOCK = null; RESUMING = false;
  syncTrick();
  noteBlock();
  render();
  if (!IT && G && !G.finished()) nextRound();   // a round boundary: carry on
}

/* Answers arrive from everybody, including as the echo of your own. They are
 * queued rather than applied on the spot, because between two rounds this
 * client is briefly not waiting on anything — the next round is on a timer —
 * and an answer that turned up in that gap would otherwise look like a
 * desynchronisation and trigger a pointless full resync. */
let NETQ = [];
let DRAINING = false;

function applyRemote(step, tok) {
  NETQ.push({ step, tok });
  drainNet();
}

function drainNet() {
  if (DRAINING || !G) return;
  DRAINING = true;
  try {
    while (NETQ.length) {
      const { step, tok } = NETQ[0];
      if (step < LOG.length) { NETQ.shift(); continue; }   // already have it
      if (step > LOG.length) {                             // we missed one
        NETQ.length = 0;
        netSend({ t: "sync" });
        return;
      }
      if (!REQ) return;                       // between rounds; try again later
      NETQ.shift();
      LOG.push(tok);
      reportAnswered(REP, tok);
      const a = decodeAns(G, REQ, tok);
      SEL = blankSel();
      pump(a);
    }
  } finally { DRAINING = false; }
}

function applyRemoteUndo(step) {
  if (!G || step >= LOG.length) return;
  NETQ.length = 0;
  const kept = LOG.slice(0, step);
  reportUndone(REP, step);
  rebuildFrom(kept);
}

/* When the server and this page disagree, the server is right — and the cheap
 * way to agree again is to build the whole game from the log rather than to
 * work out which message went missing. */
function resyncFrom(st) {
  if (!st) return;
  if (!G || st.phase === "lobby") { LOBBY = st; return showLobby(); }
  NETQ.length = 0;
  rebuildFrom(st.log || []);
}

/* ---- the two lines a player sees about the connection ---- */

function netBar() {
  const bar = $("#netbar");
  if (!bar) return;
  if (!netOn() || NET.status !== "lost") { bar.hidden = true; return; }
  bar.textContent = t("net.lost");
  bar.hidden = false;
}
function netSay(text, bad) {
  const n = $("#net-msg");
  if (!n) return;
  n.textContent = text || "";
  n.classList.toggle("bad", !!bad);
}

/* ---- wiring the setup page ---- */

/* netSetup() early-returns when the build has no table service, so it binds
 * nothing on that first pass and has to be safe to run again once an api is
 * known. It was not: every call added another listener to the same six
 * controls, so on the second pass ONE click on "open a table" ran netCreate
 * twice — two sessions on the server, the player left in whichever one
 * happened to answer last, and the link they copied pointing at the other. */
let NET_WIRED = false;

function netSetup() {
  const box = $("#remote");
  if (!box) return;
  if (!BUILD.api) { box.hidden = true; return; }   // a local file has no table
  box.hidden = false;
  const nameBox = $("#net-name");
  if (!nameBox.value) nameBox.value = defaultName();

  if (NET_WIRED) { netFromUrl(); return; }
  NET_WIRED = true;

  $("#net-host").addEventListener("click", () => {
    netSay(t("net.opening"));
    netCreate(Object.assign({ n: playerCount(), build: BUILD.commit },
                            netRules())).then((code) => {
      netConnect(code, nameBox.value.trim(), netHandlers());
    }).catch(() => netSay(t("net.failed"), true));
  });
  $("#net-join").addEventListener("click", () => joinCode($("#net-code").value));
  $("#net-code").addEventListener("keydown", (e) => {
    if (e.key === "Enter") joinCode($("#net-code").value);
  });
  $("#lobby-start").addEventListener("click", () => netSend({ t: "start" }));
  $("#lobby-leave").addEventListener("click", () => {
    netClose();
    document.body.classList.remove("lobby");
    history.replaceState(null, "", location.pathname);
  });
  $("#lobby-copy").addEventListener("click", () => {
    const f = $("#lobby-link");
    f.select();
    const done = () => { $("#lobby-copy").textContent = t("net.copied"); };
    if (navigator.clipboard) navigator.clipboard.writeText(f.value).then(done, done);
    else { try { document.execCommand("copy"); } catch (e) { /* select is enough */ } done(); }
  });

  /* Arriving on somebody's link: no setup page, just a name and a seat. */
  netFromUrl();
}

/* Joining whatever table the address bar names — unless we are already sitting
 * at it, because a second netConnect to the same code opens a second socket
 * and the seat you get back may not be the seat you were in. */
function netFromUrl() {
  const code = netCodeInUrl();
  if (!code || (NET && NET.code === code)) return;
  $("#net-code").value = code;
  netSay(t("net.joining", { code }));
  joinCode(code);
}

function joinCode(raw) {
  const code = String(raw || "").trim().toUpperCase();
  if (code.length < 4) return netSay(t("net.badcode"), true);
  try { netConnect(code, $("#net-name").value.trim(), netHandlers()); }
  catch (e) { netSay(t("net.failed"), true); }
}

/* The rules a hosted table is played under: whatever the setup page says. */
function netRules() {
  const mv = $("#meld-rules").value;
  return {
    seed: Number($("#seed").value) || undefined,
    trickRule: $("#trick-rule").value,
    deck: $("#deck").value,
    objectives: $("#objectives").value,
    retireRule: $("#retire-rule").value,
    botLevel: radioValue("#bot-level", "normal"),
    comboMelds: mv === "combo" || mv === "both",
    friendsOf10: mv === "friends" || mv === "both",
    growLimits: $("#grow-limits").value === "grow",
    perks: $("#perks") && $("#perks").value === "on",
    consolation: $("#consolation").value,
    researchRule: $("#research-rule").value,
    meldScore: $("#meld-score").value,
    aSumLadder: $("#a-ladder") ? $("#a-ladder").value : undefined,
    layout: chosenLayout(),
  };
}
