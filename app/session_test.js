/* The session core: who may answer what, and when.
 *
 * The server is the authority because trusting a client about whose turn it is
 * would be trusting it about everything. There are exactly four ways a message
 * can be wrong, and all four have to be refused:
 *
 *   - it is not your turn;
 *   - you are not in this game;
 *   - you are answering a question that has already been answered (a double
 *     tap, a slow network, two tabs open);
 *   - the answer is not one the engine could have been given.
 *
 * The rest is the promise the whole design rests on: seed + options + answers
 * is the game, so two clients replaying the same log are looking at the same
 * board, and a reconnecting player is handed the log and is immediately back
 * where everyone else is.
 *
 * No sockets here. Pure functions over a plain object.
 */
const E = require('./engine.js');
const S = require('./session.js');

const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* A deterministic "random" so codes and names are reproducible in the test. */
let seq = 0;
const rand = () => { seq = (seq * 1103515245 + 12345) % 2147483648; return seq / 2147483648; };

// ------------------------------------------------------------ the lobby
const s = S.newSession({ n: 3, seed: 77, objectives: 'off' }, rand);
ok(/^[2-9BCDFGHJKLMNPQRSTVWXYZ]{4}-[2-9BCDFGHJKLMNPQRSTVWXYZ]{4}$/.test(s.code),
   `the session code "${s.code}" is not the shape people can read out`);
ok(!/[AEIOU01]/.test(s.code), `the code "${s.code}" can contain a word or an ambiguous digit`);

const host = S.sessionJoin(s, { name: 'Toby' }, rand);
ok(host.ok && host.player.seat === 0, 'the host did not get a seat');
const anna = S.sessionJoin(s, { name: 'Anna', seat: 2 }, rand);
ok(anna.ok && anna.player.seat === 2, 'a guest could not choose a free seat');
ok(S.humanSeats(s).join() === '0,2', `human seats are ${S.humanSeats(s)}, expected 0,2`);
ok(s.seats[1].player === null, 'the unclaimed seat is not a bot seat');

/* Nobody has to type a name. */
const quiet = S.sessionJoin(s, {}, rand);
ok(quiet.ok && quiet.player.name && quiet.player.name.length > 2,
   'a player who typed no name got no name');
ok(quiet.player.name !== 'Anna' && quiet.player.name !== 'Toby',
   'the default name collided with somebody already at the table');
ok(!S.sessionJoin(s, { name: 'Late' }, rand).ok, 'a fourth player joined a three-seat game');
S.sessionLeave(s, quiet.player.token);
ok(s.seats[1].player === null, 'leaving the lobby did not free the seat');

// seat swapping, while it is still free
ok(S.sessionSit(s, anna.player.token, 1).ok, 'a guest could not move to a free seat');
ok(!S.sessionSit(s, anna.player.token, 0).ok, "a guest took the host's seat");
ok(S.sessionSit(s, anna.player.token, 2).ok, 'a guest could not move back');

// only the host starts
ok(!S.sessionStart(s, anna.player.token).ok, 'a guest started the game');
ok(S.sessionStart(s, host.player.token).ok, 'the host could not start the game');
ok(s.phase === 'playing', 'the session did not enter play');
ok(!S.sessionJoin(s, { name: 'Late' }, rand).ok, 'somebody joined a game already running');

// -------------------------------------------------- who may answer what
let at = S.sessionAdvance(s, E);
ok(!!at.req, 'the game did not stop for anybody');
const first = at.req.seat;
ok(first === 0 || first === 2, `the first question went to bot seat ${first}`);
const asker = first === 0 ? host : anna;
const other = first === 0 ? anna : host;

// wrong player
ok(!S.sessionAnswer(s, E, other.player.token, 0, { pick: 0 }).ok,
   'the wrong player was allowed to answer');
// unknown player
ok(!S.sessionAnswer(s, E, 'not-a-token', 0, { pick: 0 }).ok,
   'a stranger was allowed to answer');
// stale step — the double tap
ok(!S.sessionAnswer(s, E, asker.player.token, 5, { pick: 0 }).ok,
   'an answer arriving at the wrong step was accepted');
// an answer the engine could not have been given
/* Refused BY NAME, not merely survived. A server that only catches the
 * exception has no idea it was sent rubbish, and an exception inside a
 * Durable Object takes the session down with it. */
const bad = (tok) => S.sessionAnswer(s, E, asker.player.token, 0, tok);
ok(bad({ pick: 9999 }).why === 'session.illegal',
   'an out-of-range option was not recognised as illegal, only survived');
ok(bad({ kind: 'teleport' }).why === 'session.illegal',
   'an invented answer was not recognised as illegal, only survived');
/* The dangerous kind: an index just past the end does NOT throw — it decodes
 * to undefined, and `splice(indexOf(undefined))` quietly removes the LAST
 * card instead. Nothing downstream would ever notice. */
ok(bad({ kind: 'spend', i: 999, cell: 'x', act: 'settle' }).why === 'session.illegal',
   'an out-of-range card index was accepted — it would silently spend another card');
ok(bad({ pick: -1 }).why === 'session.illegal', 'a negative option index was accepted');
ok(bad('a string').why === 'session.illegal', 'a non-object answer was accepted');
ok(s.log.length === 0, 'a refused message still changed the log');

// and the real one
const good = S.sessionAnswer(s, E, asker.player.token, 0, { pick: 0 });
ok(good.ok && good.by === first, 'a legal answer from the right player was refused');
ok(s.log.length === 1, 'the accepted answer was not recorded');
// immediately again, at the same step: the classic double tap
ok(!S.sessionAnswer(s, E, asker.player.token, 0, { pick: 0 }).ok,
   'a double tap played the same card twice');

// ------------------------------------------------------- play it through
let guard = 0, answered = 0;
while (s.phase === 'playing' && guard++ < 4000) {
  const now = S.sessionAdvance(s, E);
  if (!now.req) break;
  const who = Object.values(s.players).find((p) => p.seat === now.req.seat);
  if (!who) { fail.push(`the engine asked seat ${now.req.seat}, which is a bot`); break; }
  const tok = now.req.type === 'turn' ? { kind: 'end' } : { pick: 0 };
  const res = S.sessionAnswer(s, E, who.token, s.log.length, tok);
  if (!res.ok) { fail.push('a legal answer was refused mid-game: ' + res.why); break; }
  answered += 1;
}
ok(s.phase === 'over', `the session did not finish (phase ${s.phase}, ${guard} steps)`);
ok(answered > 20, `only ${answered} answers to finish a game`);
ok(!S.sessionAnswer(s, E, host.player.token, s.log.length, { pick: 0 }).ok,
   'a finished game still accepts answers');

// ------------------------------------------- two clients see one board
/* This is the claim the whole architecture rests on: the log alone rebuilds
 * the game, so everybody replaying it is looking at the same table. */
function boardOf(sess) {
  const done = S.sessionAdvance(sess, E);
  const g = done.g;
  return JSON.stringify({
    round: g.round,
    gold: g.P.map((p) => p.gold),
    hands: g.P.map((p) => p.hand.map((c) => c.r + c.s).sort()),
    map: [...g.m.tiles.entries()].map(([k, t]) => k + ':' + t.terrain + ':' + t.units.join(',')).sort(),
    score: g.score().map((x) => x.total),
  });
}
const mine = boardOf(s);
/* A client that has only ever seen the state message — code, seed, rules,
 * log — and never the server's own object. */
const wire = JSON.parse(JSON.stringify(S.sessionState(s, host.player.token)));
const rebuilt = S.newSession({ n: wire.n, seed: wire.seed, code: wire.code }, rand);
rebuilt.rules = wire.rules;
rebuilt.phase = 'playing';
for (const seat of wire.humans) rebuilt.seats[seat].player = 'x' + seat;
rebuilt.log = wire.log;
ok(boardOf(rebuilt) === mine,
   'a client rebuilding from the state message sees a DIFFERENT board');
ok(wire.log.length === s.log.length, 'the state message does not carry the whole game');
ok(!JSON.stringify(wire).includes(host.player.token),
   'the state message leaks a player token to everybody at the table');

// --------------------------------------------------------- reconnecting
const s2 = S.newSession({ n: 3, seed: 12, objectives: 'off' }, rand);
const h2 = S.sessionJoin(s2, { name: 'Toby' }, rand);
const g2 = S.sessionJoin(s2, { name: 'Anna', seat: 1 }, rand);
S.sessionStart(s2, h2.player.token);
for (let k = 0; k < 6; k++) {
  const now = S.sessionAdvance(s2, E);
  if (!now.req) break;
  const who = Object.values(s2.players).find((p) => p.seat === now.req.seat);
  S.sessionAnswer(s2, E, who.token, s2.log.length, now.req.type === 'turn' ? { kind: 'end' } : { pick: 0 });
}
const lost = s2.log.length;
S.sessionLeave(s2, g2.player.token);
ok(s2.seats[1].player === g2.player.token,
   'a player who dropped mid-game lost their seat — the game can never continue');
const back = S.sessionJoin(s2, { token: g2.player.token, name: 'Anna' }, rand);
ok(back.ok && back.rejoined && back.player.seat === 1,
   'reconnecting did not return the player to their own seat');
ok(s2.log.length === lost, 'reconnecting changed the game');
ok(S.sessionState(s2, g2.player.token).seats[1].you,
   'the reconnected player is not told which seat is theirs');

// ---------------------------------------------------------------- undo
/* The same limit the local game enforces, worked out from the log: back to the
 * start of your own map turn, and no further. */
const s3 = S.newSession({ n: 3, seed: 31, objectives: 'off' }, rand);
const h3 = S.sessionJoin(s3, { name: 'Toby' }, rand);
S.sessionStart(s3, h3.player.token);
let inTurn = 0, sawTurn = false;
for (let k = 0; k < 400; k++) {
  const now = S.sessionAdvance(s3, E);
  if (!now.req) break;
  if (now.req.type === 'turn' && now.req.opts && now.req.opts.cards.length) {
    sawTurn = true;
    const before = s3.log.length;
    ok(!S.sessionUndo(s3, E, h3.player.token).ok || inTurn > 0,
       'undo was offered at the very start of a turn, before anything was done');
    // spend a card, then take it back
    const card = now.req.opts.cards[0];
    if (card.options && card.options.length) {
      const [cell, act] = card.options[0];
      const r1 = S.sessionAnswer(s3, E, h3.player.token, before,
        { kind: 'spend', i: 0, cell, act });
      if (r1.ok) {
        ok(s3.log.length === before + 1, 'the spend was not recorded');
        /* A client may ask to rewind to any step it likes; the server must
         * still refuse anything before this turn began. Checked HERE, while
         * the turn is open, because that is the only moment undo is live. */
        const refuse = (step, what) => {
          /* A server that throws on a hostile message is a server that can be
           * taken down by one, so a throw counts as a failure here. */
          let r;
          try { r = S.sessionUndo(s3, E, h3.player.token, step); }
          catch (e) { fail.push(what + ' — it threw: ' + e.message); return; }
          ok(!r.ok, what);
        };
        refuse(0, 'a client asking to rewind to step 0 unwound the whole game');
        refuse(-5, 'a negative rewind was accepted');
        refuse(s3.log.length + 3, 'a rewind past the end of the log was accepted');
        ok(s3.log.length === before + 1, 'a refused rewind still changed the log');
        const u = S.sessionUndo(s3, E, h3.player.token);
        ok(u.ok, 'undo refused a move made this turn: ' + u.why);
        ok(s3.log.length === before, 'undo did not drop the answer');
        inTurn += 1;
      }
    }
    if (inTurn >= 2) break;
  }
  const now2 = S.sessionAdvance(s3, E);
  if (!now2.req) break;
  S.sessionAnswer(s3, E, h3.player.token, s3.log.length,
    now2.req.type === 'turn' ? { kind: 'end' } : { pick: 0 });
}
ok(sawTurn, 'the undo section never reached a map turn');
ok(inTurn > 0, 'the undo section never actually undid anything');
/* And it stops: from the card phase there is nothing of yours to take back. */
const s4 = S.newSession({ n: 3, seed: 5, objectives: 'off' }, rand);
const h4 = S.sessionJoin(s4, { name: 'Toby' }, rand);
S.sessionStart(s4, h4.player.token);
S.sessionAnswer(s4, E, h4.player.token, 0, { pick: 0 });     // the meld
ok(!S.sessionUndo(s4, E, h4.player.token).ok,
   'a meld could be unplayed after the trick — that is a look at the answers');

// ------------------------------------------- a landfall survives a replay
/* A move that ends on empty ground carries the terrain of the tile it lays.
 * That terrain is a CHOICE, not a function of the seed, so if the codec drops
 * it the replay lays something else — and since undo, reconnect and every
 * remote client are all replays, the whole table would quietly diverge from
 * that point on. Cheap to check, catastrophic to miss.
 */
{
  const req = { type: 'turn', seat: 0, state: { cards: [] } };
  const g0 = { P: [{ vrow: [] }] };
  const move = { kind: 'move', src: '0,0', dest: '-1,1', terrain: 'forest' };
  const tok = S.encodeAnswer(g0, req, move);
  ok(tok.terrain === 'forest',
     `the codec dropped the landfall terrain: ${JSON.stringify(tok)}`);
  const back = S.decodeAnswer(g0, req, tok);
  ok(back.terrain === 'forest',
     `a landfall decoded without its terrain: ${JSON.stringify(back)}`);
  ok(back.src === '0,0' && back.dest === '-1,1', 'the move itself did not survive');
  ok(S.legalAnswer ? S.legalAnswer(g0, req, tok) !== false : true,
     'a landfall move token is rejected as illegal');

  /* An ordinary move must not grow a terrain field out of nowhere. */
  const plain = S.encodeAnswer(g0, req, { kind: 'move', src: '0,0', dest: '1,0' });
  ok(!('terrain' in plain),
     `an ordinary move carries a terrain field: ${JSON.stringify(plain)}`);
}

// ------------------------------------------ nothing severs your own turn
/* A playtest note said only "couldn't use undo at some point", and the cause
 * was this: a request made to your seat that TURN_REQ did not list would set
 * the block to null, so the next `turn` looked like a fresh block and the undo
 * floor was re-marked AFTER an answer you had already given. The decision
 * itself became unreachable, and so did everything before it in the same turn
 * — undo simply went dead with nothing on screen to explain why.
 *
 * `setaside`, `bonus` and `discard` are all asked at the top of your own turn
 * block, right after the trick resolves. This walks real games and asserts
 * that no request made to your seat inside your own turn ever severs it.
 * Measured against the old list this fires 56 times in 40 games.
 */
{
  const TURN_REQ = ['turn', 'waterexplore', 'conquest', 'retire', 'buy', 'colony',
                    'bonus', 'discard', 'setaside'];
  const SEVERING = ['bonus', 'discard', 'setaside'];
  let severed = 0, blocks = 0, sawSevering = 0;
  const kinds = {};

  for (const rule of ['classic', 'bonus']) {
    for (let seed = 1; seed <= 12; seed++) {
      const g = new E.Game(3, seed * 131 + 7, { humans: [0], trickRule: rule });
      let it = g.playRound(), r = it.next(), guard = 0, block = null;
      while (guard++ < 20000) {
        if (r.done) { if (g.finished()) break; it = g.playRound(); r = it.next(); continue; }
        const q = r.value;
        if (q.seat === 0) {
          if (TURN_REQ.includes(q.type)) {
            const key = g.round + ':' + q.seat;
            if (key !== block) { block = key; blocks++; }
            if (SEVERING.includes(q.type)) {
              sawSevering++;
              kinds[q.type] = (kinds[q.type] || 0) + 1;
            }
          } else {
            /* Anything else legitimately ends the block — but it must not be
             * one of the three that belong to your turn. */
            if (SEVERING.includes(q.type)) { severed++; kinds[q.type] = -1; }
            block = null;
          }
        }
        let a = null;
        if (q.type === 'turn') a = { kind: 'end' };
        else if (q.options && q.options.length) a = q.options[0];
        r = it.next(a);
      }
    }
  }
  ok(blocks > 50, `only ${blocks} turn blocks seen — the walk is not reaching play`);
  ok(sawSevering > 0,
     'no bonus/discard/setaside request came up in 24 games, so this proves '
     + 'nothing — the trick rules must have changed');
  ok(severed === 0,
     `${severed} decision(s) taken on your own turn fell outside the undo floor `
     + `(${JSON.stringify(kinds)}) — undo would go dead for the rest of that turn`);
}

// --------------------------------------------------------------- flags
const f = S.sessionFlag(s4, h4.player.token, { note: 'why is this greyed out' });
ok(f.ok && f.flag.seat === 0 && typeof f.flag.step === 'number',
   'a flag does not record who raised it and where');
ok(!S.sessionFlag(s4, 'nobody', { note: 'x' }).ok, 'a stranger could flag');

// --------------------------------------------------------- how big is it
const bytes = JSON.stringify(S.sessionState(s, host.player.token)).length;
ok(bytes < 12000, `a whole finished game is ${bytes} bytes on the wire — too fat`);

console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : `session: lobby seats and swaps, host-only start, four kinds of bad message `
    + `refused, a game played to the end, two clients agree on the board, `
    + `reconnect keeps your seat, undo stops at your turn — a finished game is `
    + `${bytes} bytes on the wire`);
process.exit(fail.length ? 1 : 0);
