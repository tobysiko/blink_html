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

const path = require('path');
const E = require(path.join(__dirname, '..', 'app', 'engine.js'));
const S = require(path.join(__dirname, '..', 'app', 'session.js'));

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

module.exports = { createHub };
