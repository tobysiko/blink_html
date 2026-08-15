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
