/* A playtest session, written down.
 *
 * The point of this file is that a game played by a stranger comes back as
 * something you can *act* on rather than a sentence in an email. Three things
 * make that true:
 *
 *   1. It names its build. A report that cannot say which version produced it
 *      is an anecdote. `BUILD.commit` is baked in at build time, along with
 *      whether the tree was dirty, because a build made from uncommitted edits
 *      is not the commit it claims to be.
 *
 *   2. It carries the whole game, not a summary. The engine is deterministic —
 *      seed plus options plus the answers people gave *is* the game — so the
 *      replay log reconstructs it exactly, card for card. That is the same
 *      machinery undo uses, so it costs nothing extra and is already tested.
 *
 *   3. It records where people HESITATED. Every human decision is timed from
 *      the moment it appears on screen to the moment it is answered. A long
 *      pause is the shape of confusion, and it is invisible in a score table.
 *
 * Plus what a person says: flags raised mid-game, and the end-of-game form.
 *
 * The whole thing is a plain object. Nothing here touches the network — the
 * transport decides whether it is posted, downloaded, or kept.
 */

const REPORT_SCHEMA = 3;

/* Short, unambiguous, sayable out loud — these end up in filenames and get
 * read down a phone. No 0/O or 1/I. */
const ID_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";
function shortId(n) {
  let s = "";
  for (let i = 0; i < (n || 8); i++)
    s += ID_ALPHABET[Math.floor(Math.random() * ID_ALPHABET.length)];
  return s;
}

function newReport(build, gargs, extra) {
  const o = extra || {};
  return {
    schema: REPORT_SCHEMA,
    id: shortId(8),
    build: {
      version: build.version, commit: build.commit, branch: build.branch,
      dirty: build.dirty, built: build.built,
    },
    started: new Date().toISOString(),
    ended: null,
    lang: o.lang || null,
    session: o.session || null,          // set when the game is played remotely
    players: o.players || [],            // [{seat, kind, style, name}]
    setup: {
      n: gargs.n,
      seed: gargs.seed,
      humans: (gargs.opts.humans || []).slice(),
      seatStyles: (gargs.opts.seatStyles || []).slice(),
      botLevel: gargs.opts.botLevel,
      trickRule: gargs.opts.trickRule,
      deck: gargs.opts.deck,
      objectives: gargs.opts.objectives,
      retireRule: gargs.opts.retireRule,
      consolation: gargs.opts.consolation || "last",
      /* These fallbacks must match the ENGINE's defaults, not an older rule.
       * A report that records "once" for a game the engine played "twice"
       * replays a different game, and nothing downstream can tell. */
      researchRule: gargs.opts.researchRule || "twice",
      combat: gargs.opts.combat || "duel",
      duelTake: gargs.opts.duelTake !== false,   // note: NOT `|| true`
      frontier: gargs.opts.frontier || "low",
      duelKeep: !!gargs.opts.duelKeep,
      perks: gargs.opts.perks || false,
      comboMelds: !!gargs.opts.comboMelds,
      friendsOf10: !!gargs.opts.friendsOf10,
      growLimits: !!gargs.opts.growLimits,
      /* Two reports of games played under different scoring or a different
       * player board are not comparable, and without these there is no way to
       * tell afterwards which was which. */
      meldScore: gargs.opts.meldScore || "count",
      aSumLadder: gargs.opts.aSumLadder || null,
      layout: gargs.opts.layout || null,
    },
    replay: [],        // the answer tokens: this alone re-deals the whole game
    decisions: [],     // {r, s, t, ms} — one per human decision, in order
    flags: [],         // {at, r, s, t, note} — raised by a person, mid-game
    outcome: null,
    counters: null,
    feedback: null,
    ui: {              // what the page could actually show them
      w: typeof window === "undefined" ? null : window.innerWidth,
      h: typeof window === "undefined" ? null : window.innerHeight,
      touch: typeof window === "undefined" ? null
        : (("ontouchstart" in window) || navigator.maxTouchPoints > 0),
      agent: typeof navigator === "undefined" ? null : navigator.userAgent,
    },
  };
}

/* --- while the game runs ---------------------------------------------- */

/* Called when a request appears on screen. Timing starts here, not when the
 * previous answer was given: the gap between them is the bots playing, and
 * blaming a person for that would make every report lie. */
function reportAsked(rep, req, round) {
  if (!rep || !req) return;
  rep._pending = { r: round, s: req.seat, t: req.type, at: Date.now() };
}

function reportAnswered(rep, token) {
  if (!rep) return;
  if (rep._pending) {
    const p = rep._pending;
    rep.decisions.push({ r: p.r, s: p.s, t: p.t, ms: Date.now() - p.at });
    rep._pending = null;
  }
  if (token !== undefined) rep.replay.push(token);
}

/* Undo rewinds the game, so it has to rewind the record too — otherwise the
 * replay log no longer produces the game that was played. The decision that
 * was taken back is kept, marked, because "they did this and immediately took
 * it back" is one of the more useful things in the whole file. */
function reportUndone(rep, length) {
  if (!rep) return;
  rep.replay.length = Math.min(rep.replay.length, length);
  for (let i = rep.decisions.length - 1; i >= 0; i--) {
    if (!rep.decisions[i].undone) { rep.decisions[i].undone = true; break; }
  }
  rep.undos = (rep.undos || 0) + 1;
}

/* Somebody hit the flag. Where they were is the whole value, so it is taken
 * from the game rather than typed. */
function reportFlag(rep, g, req, note) {
  if (!rep) return null;
  const f = {
    at: new Date().toISOString(),
    r: g ? g.round : null,
    s: req ? req.seat : null,
    t: req ? req.type : null,
    step: rep.replay.length,          // exactly where in the replay to look
    note: (note || "").slice(0, 800),
  };
  rep.flags.push(f);
  return f;
}

/* --- when it is over --------------------------------------------------- */

function reportFinish(rep, g) {
  if (!rep || !g) return rep;
  rep.ended = new Date().toISOString();
  rep.seconds = Math.round((Date.parse(rep.ended) - Date.parse(rep.started)) / 1000);
  rep.outcome = {
    rounds: g.round,
    endedOn: g.endedOn,
    scores: g.score().map((x) => ({
      seat: x.seat, total: x.total, pop: x.pop, row: x.vrow, dom: x.dom,
      obj: x.obj, objDone: x.objDone, gold: x.gold, band: x.band,
    })),
  };
  rep.counters = Object.assign({}, g.stats);
  return rep;
}

function reportFeedback(rep, answers) {
  if (!rep) return rep;
  rep.feedback = Object.assign({ at: new Date().toISOString() }, answers || {});
  return rep;
}

/* One line a person can read before they send it. Deliberately not a summary
 * of the game — a summary of the RECORD, so they can see what they are
 * handing over. */
function reportSize(rep) {
  return JSON.stringify(rep).length;
}

function reportFilename(rep) {
  const seed = rep.setup.seed, n = rep.setup.n;
  return `blink-${rep.build.version}-${rep.build.commit}-${n}p-seed${seed}-${rep.id}.json`;
}

if (typeof module !== "undefined" && module.exports)
  module.exports = { REPORT_SCHEMA, shortId, newReport, reportAsked, reportAnswered,
                     reportUndone, reportFlag, reportFinish, reportFeedback,
                     reportSize, reportFilename };
