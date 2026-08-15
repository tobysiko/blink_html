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

module.exports = { memoryStore, redisStore, storeFromEnv, KEY, CHAN, TTL_SECONDS,
                   CAS_SCRIPT };
