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

if (typeof module !== "undefined" && module.exports)
  module.exports = { SESSION_PROTOCOL, makeCode, defaultName, newSession,
                     sessionJoin, sessionLeave, sessionSit, sessionStart,
                     sessionAdvance, sessionAnswer, sessionUndo, sessionFlag,
                     sessionState, sessionHandle, gameArgs, humanSeats, decodeAnswer,
                     legalAnswer, encodeAnswer, undoFloor };
