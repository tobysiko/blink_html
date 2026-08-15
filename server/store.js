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
 */

const KEY = (code) => `blink:session:${code}`;
const CHAN = (code) => `blink:room:${code}`;
const TTL_SECONDS = 60 * 60 * 24 * 2;      // a table nobody returns to expires

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
    /* The plain client, for the few things that are not sessions — playtest
     * reports live in the same Redis, because a report is a few kilobytes and
     * there will be hundreds of them, not millions. */
    raw: client,

    async create(s) {
      await client.set(KEY(s.code), JSON.stringify(s), { EX: TTL_SECONDS });
      return s;
    },

    async get(code) {
      const raw = await client.get(KEY(code));
      return raw ? JSON.parse(raw) : null;
    },

    /* Compare-and-set. WATCH the key, apply the change to the copy we read,
     * and let the transaction fail if anyone else wrote in between — then read
     * again and redo it. The retry is not a formality: it is the only thing
     * standing between two simultaneous taps and a move that vanishes. */
    async update(code, fn, tries) {
      const limit = tries || 20;
      for (let i = 0; i < limit; i++) {
        const watcher = client.duplicate ? await client.duplicate().connect() : client;
        try {
          await watcher.watch(KEY(code));
          const raw = await watcher.get(KEY(code));
          if (!raw) { await watcher.unwatch(); return { ok: false, why: "session.unknown" }; }
          const s = JSON.parse(raw);
          const out = fn(s);
          /* A refusal changes nothing, so it needs no transaction at all —
           * and refusals are the common case under contention. */
          if (!out || out.ok === false) { await watcher.unwatch(); return out; }
          const tx = watcher.multi();
          tx.set(KEY(code), JSON.stringify(s), { EX: TTL_SECONDS });
          const res = await tx.exec();
          if (res !== null) return out;             // committed
          // somebody else got there first: read again and redo the work
        } finally {
          if (watcher !== client && watcher.quit) { try { await watcher.quit(); } catch (e) { /* */ } }
        }
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

module.exports = { memoryStore, redisStore, storeFromEnv, KEY, CHAN, TTL_SECONDS };
