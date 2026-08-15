/* The Blink session service.
 *
 * A Cloudflare Worker in front of one Durable Object per session. The Durable
 * Object is the right shape for this because a session is exactly what it is
 * good at: a small piece of state with a single writer and a handful of
 * sockets attached to it.
 *
 * It is deliberately thin. All the rules live in session.js, which knows
 * nothing about sockets and is tested without them — this file is transport,
 * error codes and storage.
 *
 * Routes
 *   POST /session            create one; body is the rules, returns the code
 *   GET  /session/:code      the state, for a page that has not connected yet
 *   GET  /session/:code/ws   the socket (Upgrade: websocket)
 *   POST /report             a playtest report, stored as-is
 *   GET  /reports            list them (needs ADMIN_KEY)
 *   GET  /report/:id         one of them (needs ADMIN_KEY)
 *
 * Built by `node build.js` in this folder, which glues engine.js, session.js
 * and this file into one deployable worker.js — the same trick the app uses,
 * for the same reason: no module system, no bundler, nothing to go wrong
 * between what is tested and what is deployed.
 */

/* ------------------------------------------------------------ the router */

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-headers": "content-type",
  "access-control-max-age": "86400",
};
const json = (body, status) => new Response(JSON.stringify(body), {
  status: status || 200,
  headers: Object.assign({ "content-type": "application/json" }, CORS),
});

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });

    try {
      if (path === "/" || path === "/health")
        return json({ ok: true, service: "blink-sessions", protocol: SESSION_PROTOCOL });

      // ---- create
      if (path === "/session" && request.method === "POST") {
        const body = await request.json().catch(() => ({}));
        const code = makeCode();
        const id = env.SESSIONS.idFromName(code);
        const stub = env.SESSIONS.get(id);
        const r = await stub.fetch("https://do/create", {
          method: "POST",
          body: JSON.stringify(Object.assign({}, body, { code })),
        });
        return new Response(r.body, { status: r.status, headers: Object.assign(
          { "content-type": "application/json" }, CORS) });
      }

      // ---- one session: state, or a socket
      const m = path.match(/^\/session\/([A-Za-z0-9-]{4,12})(\/ws)?$/);
      if (m) {
        const code = m[1].toUpperCase();
        const stub = env.SESSIONS.get(env.SESSIONS.idFromName(code));
        const to = m[2] ? "https://do/ws" + url.search : "https://do/state";
        return stub.fetch(to, request);
      }

      // ---- playtest reports
      if (path === "/report" && request.method === "POST") {
        const rep = await request.json().catch(() => null);
        if (!rep || !rep.schema) return json({ ok: false, why: "not a report" }, 400);
        const id = `${(rep.build && rep.build.commit) || "unknown"}/${
          (rep.started || "").slice(0, 10)}/${rep.id || Date.now()}.json`;
        if (env.REPORTS) {
          await env.REPORTS.put(id, JSON.stringify(rep), {
            httpMetadata: { contentType: "application/json" },
            customMetadata: {
              commit: String((rep.build && rep.build.commit) || ""),
              players: String(rep.setup ? rep.setup.n : ""),
              seed: String(rep.setup ? rep.setup.seed : ""),
              rating: String((rep.feedback && rep.feedback.rating) || ""),
              flags: String((rep.flags || []).length),
            },
          });
        }
        return json({ ok: true, id: rep.id, stored: !!env.REPORTS });
      }

      /* Reading reports back is not public: they carry names and free text
       * people wrote for the designer, not for the internet. */
      if (path === "/reports" || path.startsWith("/report/")) {
        if (!env.ADMIN_KEY || url.searchParams.get("key") !== env.ADMIN_KEY)
          return json({ ok: false, why: "not yours" }, 403);
        if (!env.REPORTS) return json({ ok: false, why: "no store bound" }, 503);
        if (path === "/reports") {
          const list = await env.REPORTS.list({ limit: 200,
            prefix: url.searchParams.get("commit") || undefined });
          return json({ ok: true, reports: list.objects.map((o) => ({
            key: o.key, size: o.size, at: o.uploaded, meta: o.customMetadata })) });
        }
        const obj = await env.REPORTS.get(path.slice("/report/".length));
        if (!obj) return json({ ok: false, why: "no such report" }, 404);
        return new Response(obj.body, { headers: { "content-type": "application/json" } });
      }

      return json({ ok: false, why: "no such route" }, 404);
    } catch (e) {
      return json({ ok: false, why: "server error", detail: String(e && e.message) }, 500);
    }
  },
};

/* ------------------------------------------------------ one live session */

export class BlinkSession {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.sockets = new Map();          // WebSocket -> token
    this.s = null;
  }

  async load() {
    if (!this.s) this.s = (await this.state.storage.get("session")) || null;
    return this.s;
  }
  async save() {
    this.s.touched = new Date().toISOString();
    await this.state.storage.put("session", this.s);
  }

  async fetch(request) {
    const url = new URL(request.url);
    await this.load();

    if (url.pathname === "/create") {
      const body = await request.json().catch(() => ({}));
      this.s = newSession(body);
      await this.save();
      return json({ ok: true, code: this.s.code, state: sessionState(this.s) });
    }

    if (!this.s) return json({ ok: false, why: "session.unknown" }, 404);

    if (url.pathname === "/state")
      return json({ ok: true, state: sessionState(this.s) });

    if (url.pathname === "/ws") {
      if (request.headers.get("Upgrade") !== "websocket")
        return json({ ok: false, why: "expected a websocket" }, 426);
      const pair = new WebSocketPair();
      const [client, server] = Object.values(pair);
      server.accept();
      this.attach(server);
      return new Response(null, { status: 101, webSocket: client });
    }

    return json({ ok: false, why: "no such route" }, 404);
  }

  attach(ws) {
    this.sockets.set(ws, null);
    ws.addEventListener("message", (ev) => {
      let msg = null;
      try { msg = JSON.parse(ev.data); } catch (e) { return this.send(ws, { t: "error", why: "bad json" }); }
      this.handle(ws, msg).catch((e) =>
        this.send(ws, { t: "error", why: "server error", detail: String(e && e.message) }));
    });
    const drop = () => {
      const token = this.sockets.get(ws);
      this.sockets.delete(ws);
      if (token) {
        sessionLeave(this.s, token);
        this.save();
        this.broadcast({ t: "seats", state: true });
      }
    };
    ws.addEventListener("close", drop);
    ws.addEventListener("error", drop);
  }

  send(ws, msg) { try { ws.send(JSON.stringify(msg)); } catch (e) { /* gone */ } }

  /* Everybody hears the same thing, except the bits that are theirs alone:
   * which seat is "you" depends on who is being told. */
  broadcast(msg) {
    for (const [ws, token] of this.sockets) this.send(ws, this.fill(msg, token));
  }

  /* Transport only. Every decision about who may do what lives in
   * session.js, so the Durable Object and the node dev server cannot drift
   * apart on the one thing that matters. */
  async handle(ws, msg) {
    const out = sessionHandle(this.s, { Game }, { token: this.sockets.get(ws) }, msg);
    if (out.token) this.sockets.set(ws, out.token);
    let changed = false;
    for (const step of out.to) {
      if (step.who === "self") this.send(ws, this.fill(step.msg, this.sockets.get(ws)));
      else { this.broadcast(step.msg); changed = true; }
    }
    if (changed || out.token) await this.save();
  }

  fill(msg, token) {
    return msg.state === true
      ? Object.assign({}, msg, { state: sessionState(this.s, token) })
      : msg;
  }
}
