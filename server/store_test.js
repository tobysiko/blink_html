/* The two failures moving to Vercel introduces.
 *
 * On Cloudflare neither of these could happen, so neither is covered anywhere
 * else. A Durable Object is one home per table: every socket for a session is
 * attached to the same object, and its writes are serialised for you.
 *
 * Vercel is not that. A connection is pinned to one function instance, but a
 * NEW connection may land anywhere, so two people at one table are routinely
 * talking to two different processes — and a deployment separates them again.
 * Two things can now go wrong that could not before:
 *
 *   1. **A move that nobody else hears.** Player A's answer is applied on the
 *      instance holding A's socket. If it does not cross to the instance
 *      holding B's socket, B sits there watching a board that has stopped.
 *
 *   2. **A move that vanishes.** Two players answer at the same instant, on
 *      two instances. Both read a log of length 14; both write 15. The second
 *      write erases the first, and the game quietly loses a card. The `step`
 *      guard in session.js *detects* a stale answer, but it cannot prevent a
 *      lost update — by the time it runs, both reads have already happened.
 *
 * The first is tested with two hubs over one store. The second needs Redis
 * semantics rather than node's single thread, so there is a small fake Redis
 * here with real WATCH/MULTI/EXEC behaviour — including a hook that forces the
 * interleaving, because a race you cannot reproduce on demand is a race you
 * are not really testing.
 */
const path = require('path');
const E = require(path.join(__dirname, '..', 'app', 'engine.js'));
const S = require(path.join(__dirname, '..', 'app', 'session.js'));
const { memoryStore, redisStore } = require('./store.js');
const { createHub } = require('./hub.js');

const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* A socket is anything with send(). These also remember what they were told. */
function fakeSock(name) {
  const got = [];
  return { name, got, send: (s) => got.push(JSON.parse(s)),
           last: (t) => [...got].reverse().find((m) => m.t === t) };
}

async function main() {
  // ============================================ 1. two instances, one table
  const store = memoryStore();
  /* Two hubs over one store is exactly the shape Vercel gives you: separate
   * processes, separate sockets, nothing shared but the store. */
  const A = createHub(store), B = createHub(store);
  ok(A !== B && A._rooms !== B._rooms, 'the two hubs share their socket tables');

  const s = await A.create({ n: 3, seed: 9, objectives: 'off' });
  const code = s.code;

  const toby = fakeSock('toby'), anna = fakeSock('anna');
  await A.open(code, toby);
  await B.open(code, anna);                     // the guest lands elsewhere

  await A.handle(code, toby, { t: 'hello', name: 'Toby' });
  await B.handle(code, anna, { t: 'hello', name: 'Anna' });

  ok(!!toby.last('welcome'), 'the host was never welcomed');
  ok(!!anna.last('welcome'), 'the guest was never welcomed');
  const tobySeat = toby.last('welcome').seat, annaSeat = anna.last('welcome').seat;
  ok(tobySeat === 0 && annaSeat === 1, `seats went ${tobySeat} and ${annaSeat}`);

  /* The whole point: Anna arrived on a different instance, and Toby heard
   * about it. Without pub/sub this is where a table silently splits in two. */
  const seatsOnA = toby.last('seats');
  ok(!!seatsOnA, "the host never heard that somebody joined on another instance");
  ok(seatsOnA && seatsOnA.state.seats[annaSeat].name === 'Anna',
     'the host was told a seat changed but not who is in it');
  /* And each is told which seat is theirs, not which seat is the sender's. */
  ok(seatsOnA && seatsOnA.state.seats[0].you && !seatsOnA.state.seats[1].you,
     "the host's view of the table says the wrong seat is his");
  const seatsOnB = anna.last('seats');
  ok(seatsOnB && seatsOnB.state.seats[annaSeat].you && !seatsOnB.state.seats[0].you,
     "the guest's view of the table says the wrong seat is hers");

  await A.handle(code, toby, { t: 'start' });
  const startedB = anna.last('start');
  ok(!!startedB, 'the guest was never told the game had started');
  ok(startedB && startedB.state.humans.join() === '0,1',
     'the two instances disagree about who is playing');

  // play a few moves, alternating instances, and check both hear every one
  let moves = 0;
  for (let i = 0; i < 12; i++) {
    const live = await store.get(code);
    const at = S.sessionAdvance(live, E);
    if (!at.req) break;
    const [hub, sock] = at.req.seat === tobySeat ? [A, toby] : [B, anna];
    const step = live.log.length;
    await hub.handle(code, sock, { t: 'answer', step,
      token: at.req.type === 'turn' ? { kind: 'end' } : { pick: 0 } });
    const heardA = toby.last('answer'), heardB = anna.last('answer');
    if (!heardA || heardA.step !== step) {
      fail.push(`move ${i} (seat ${at.req.seat}) never reached the host's instance`);
      break;
    }
    if (!heardB || heardB.step !== step) {
      fail.push(`move ${i} (seat ${at.req.seat}) never reached the guest's instance`);
      break;
    }
    moves += 1;
  }
  ok(moves >= 8, `only ${moves} moves crossed between the two instances`);

  /* A socket closing on one instance frees the seat everywhere — or it does
   * not, and the other player is left waiting for somebody who has gone. */
  const before = (await store.get(code)).log.length;
  await B.close(code, anna);
  ok(B._rooms.size === 0, 'the instance kept a subscription for a table it no longer holds');
  ok((await store.get(code)).log.length === before,
     'a player leaving changed the game');
  ok((await store.get(code)).seats[annaSeat].player !== null,
     'a player who dropped mid-game lost their seat — the game can never continue');

  // ======================================= 2. two answers, the same instant
  /* node is single-threaded, so a memory store cannot interleave a
   * read-modify-write. Redis can, and does. This fake has real WATCH/MULTI
   * semantics plus a hook that forces the interleaving on demand. */
  const redis = fakeRedis();
  const rstore = redisStore(redis.client, redis.sub);
  const r = S.newSession({ n: 3, seed: 4, objectives: 'off' });
  const p1 = S.sessionJoin(r, { name: 'One' });
  const p2 = S.sessionJoin(r, { name: 'Two', seat: 1 });
  S.sessionStart(r, p1.player.token);
  await rstore.create(r);

  const whose = (sess) => S.sessionAdvance(sess, E).req.seat;
  const live0 = await rstore.get(r.code);
  const seat = whose(live0);
  const actor = seat === 0 ? p1 : p2;
  const other = seat === 0 ? p2 : p1;

  /* Both players answer at once, on two instances, at the same step. One is
   * the player whose turn it is; the other is not — and neither has any way to
   * know the other is mid-flight. */
  redis.raceOnce();
  const [first, second] = await Promise.all([
    rstore.update(r.code, (sess) =>
      S.sessionAnswer(sess, E, actor.player.token, 0, { pick: 0 })),
    rstore.update(r.code, (sess) =>
      S.sessionAnswer(sess, E, other.player.token, 0, { pick: 0 })),
  ]);
  const after = await rstore.get(r.code);
  ok(after.log.length === 1,
     `two simultaneous answers left ${after.log.length} moves in the log, expected 1`);
  ok([first.ok, second.ok].filter(Boolean).length === 1,
     'both simultaneous answers were accepted');

  /* That one is caught by the seat check alone — only one of the two players
   * was ever entitled to answer. The case that genuinely needs the
   * compare-and-set is two messages that BOTH look legal at the same step:
   * one seat, tapping twice, on two instances. Nothing but the store can tell
   * them apart, because at the moment each is read the other has not happened
   * yet. */
  redis.retries = 0;
  redis.raceOnce();
  const now = await rstore.get(r.code);
  const seat2 = whose(now);
  const who2 = seat2 === p1.player.seat ? p1 : p2;
  const len = now.log.length;
  const both = await Promise.all([
    rstore.update(r.code, (sess) =>
      S.sessionAnswer(sess, E, who2.player.token, len, { pick: 0 })),
    rstore.update(r.code, (sess) =>
      S.sessionAnswer(sess, E, who2.player.token, len, { pick: 0 })),
  ]);
  const end = await rstore.get(r.code);
  ok(end.log.length === len + 1,
     `a double tap across two instances played ${end.log.length - len} answers`);
  ok(both.filter((x) => x.ok).length === 1, 'a double tap was accepted twice');
  ok(redis.retries > 0,
     'the forced race never collided — this test is proving nothing');

  /* Refusals must not cost a write at all: under contention they are the
   * common case, and a write per refusal is a queue nobody needs. */
  redis.writes = 0;
  await rstore.update(r.code, (sess) =>
    S.sessionAnswer(sess, E, 'not-a-player', 0, { pick: 0 }));
  ok(redis.writes === 0, 'a refused message still wrote to the store');

  /* ---- what a move costs -------------------------------------------------
   * The free Redis on Vercel allows 100 operations a second and 30
   * connections. Neither is generous enough to be ignored, and both are the
   * kind of number that creeps: an extra command per move looks like nothing
   * in a diff and is a third of the budget. So it is pinned here. */
  redis.cmds = 0;
  const liveNow = await rstore.get(r.code);          // 1: the test's own read
  const seatNow = whose(liveNow);
  const actorNow = Object.values(r.players).find((x) => x.seat === seatNow);
  redis.cmds = 0;
  const atNow = S.sessionAdvance(liveNow, E);
  const move = await rstore.update(r.code, (sess) =>
    S.sessionAnswer(sess, E, actorNow.token, liveNow.log.length,
      atNow.req.type === 'turn' ? { kind: 'end' } : { pick: 0 }));
  ok(move.ok, 'the costed move was refused: ' + move.why);
  const perMove = redis.cmds;
  ok(perMove <= 2, `a move now costs ${perMove} Redis commands before the publish, `
     + 'expected a GET and a compare-and-set');
  redis.cmds = 0;
  await rstore.publish(r.code, { msg: { t: 'answer' }, session: liveNow });
  ok(redis.cmds === 1, `a broadcast costs ${redis.cmds} commands, expected 1`);

  /* And no connection churn. The WATCH version made one per move, which on a
   * thirty-connection plan is not an expense, it is an outage. */
  ok(redis.dups === 0,
     `a move opened ${redis.dups} new connections — the free plan allows 30 in total`);

  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : `store: two instances over one table stayed in step for ${moves} moves and `
      + `agreed on who sits where; a double tap across two instances collided `
      + `${redis.retries} time(s) in the store and still played exactly one move; `
      + `a move costs ${perMove} commands plus one publish, opens no new `
      + `connection, and a refusal costs nothing`);
  process.exit(fail.length ? 1 : 0);
}

/* ---------------------------------------------------------------------------
 * A Redis with the parts that matter: strings, pub/sub, and WATCH/MULTI/EXEC
 * that fails the transaction if a watched key moved. `raceOnce()` makes the
 * next two updates interleave their reads, which is the whole point — a race
 * you can only hope to hit is a race you cannot test.
 */
function fakeRedis() {
  const data = new Map();
  const subs = new Map();
  const api = {
    retries: 0,
    writes: 0,
    cmds: 0,
    bytes: 0,
    dups: 0,
    _race: 0,
    raceOnce() { api._race = 2; },
  };
  let version = 0;

  /* Only the short-lived clients `update()` makes for its compare-and-set
   * honour the hook. A plain `get()` from the test itself must not eat one of
   * the two slots, or the pair we are trying to collide never overlaps. */
  const make = (isTx) => {
    let watching = null, watchedAt = 0;
    const c = {
      duplicate: () => { api.dups += 1; return { connect: async () => make(true) }; },
      quit: async () => {},
      async watch(k) { watching = k; watchedAt = version; },
      async unwatch() { watching = null; },
      async get(k) {
        /* The hook. The READ happens first and the delay after it, which is
         * what a slow network actually does: both clients see the same old
         * value, and one of them is late getting it home. Sleeping before the
         * read would just serialise them, and prove nothing. */
        api.cmds += 1;
        const v = data.has(k) ? data.get(k) : null;
        if (isTx && api._race > 0) {
          api._race -= 1;
          await new Promise((r) => setTimeout(r, 5));
        }
        return v;
      },
      async set(k, v) { api.cmds += 1; data.set(k, v); version += 1; api.writes += 1; },
      /* The compare-and-set, with the script's semantics rather than a Lua
       * interpreter: write only if the value is still the one that was read. */
      async eval(script, { keys, arguments: args }) {
        api.cmds += 1;
        const cur = data.has(keys[0]) ? data.get(keys[0]) : null;
        if (cur !== args[0]) { api.retries += 1; return 0; }
        data.set(keys[0], args[1]);
        version += 1;
        api.writes += 1;
        return 1;
      },
      async publish(chan, payload) {
        api.cmds += 1;
        api.bytes += payload.length;
        for (const f of subs.get(chan) || []) f(chan, payload);
      },
    };
    return c;
  };

  const client = make(false);
  const sub = {
    handlers: [],
    on(ev, fn) { if (ev === 'message') sub.handlers.push(fn); },
    async subscribe(chan) {
      if (!subs.has(chan)) subs.set(chan, new Set());
      subs.get(chan).add((c, p) => sub.handlers.forEach((f) => f(c, p)));
    },
    async unsubscribe(chan) { subs.delete(chan); },
    async quit() {},
  };
  api.client = client;
  api.sub = sub;
  return api;
}

main().catch((e) => { console.error('FAIL: ' + e.stack); process.exit(1); });
