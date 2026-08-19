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
      /* Awaited, not fired and forgotten: this process may be frozen the
       * instant it answers. */
      const notified = await notifyReport(rep, stored);
      return reply(res, 200, { ok: true, id: rep.id, stored, notified });
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
  const body = JSON.stringify(rep);
  const base = { contentType: "application/json", token, addRandomSuffix: true };

  /* PRIVATE first, and not only because the live store happens to be private.
   * A report carries a playtester's name and whatever they typed in the box —
   * written for the designer, not for the internet — so authentication is the
   * right default and a public URL was the wrong one. The fallback to public is
   * for a store somebody set up the other way, not a preference.
   *
   * This used to pass access:"public" unconditionally. Against a private store
   * the SDK throws, the throw reached the route, and the route answered 500 —
   * which the page read as "failed" and fell back to downloading the file. So
   * no report was ever lost, but none was ever kept either, and the only sign
   * was an error the player was asked to work around. */
  let last = null;
  for (const access of ["private", "public"]) {
    try {
      await put(key, body, Object.assign({ access }, base));
      return true;
    } catch (e) { last = e; }
  }
  /* Never throw from here. The route's contract with the page is a truthful
   * `stored` flag: false makes it save the file locally, an exception makes it
   * look like the service is down. */
  console.error("blink: could not store a report —", last && last.message);
  return false;
}

/* ---- telling the designer a report has arrived ----
 *
 * Polling a listing means remembering to poll. This pushes instead, the moment
 * something lands, to whatever webhook `BLINK_NOTIFY_URL` names.
 *
 * The payload carries BOTH `text` and `content` because that one line makes it
 * work with Slack and Discord unchanged — Slack reads `text` and ignores
 * `content`, Discord reads `content` and ignores `text`. Anything else that
 * accepts a JSON POST gets the structured fields alongside.
 *
 * Three rules, all learned the hard way elsewhere in this file:
 *   - it is best effort. A webhook that is down, slow or misconfigured must
 *     never turn into a failed report — the person has already typed their
 *     three sentences and pressed send.
 *   - it goes out whether or not the store kept the report. If storing failed
 *     the page hands the player a file instead, and that is exactly when you
 *     want to know, so you can ask them for it.
 *   - it is awaited before replying. A serverless function may be frozen the
 *     instant it responds, and a fire-and-forget fetch would be a coin toss.
 */
function notifyLines(rep, stored) {
  const fb = rep.feedback || {};
  const s = rep.setup || {};
  const who = (rep.players || [])
    .filter((p) => p && p.kind === "human").map((p) => p.name)
    .filter(Boolean).join(", ");
  const rules = [
    s.meldScore === "sum" ? "sum" : null,
    s.researchRule && s.researchRule !== "once" ? "research:" + s.researchRule : null,
    s.layout ? "board:" + s.layout : null,
    s.consolation && s.consolation !== "last" ? "payout:" + s.consolation : null,
  ].filter(Boolean).join(" ");
  return [
    `Blink playtest report ${rep.id || "?"}${stored ? "" : "  (NOT STORED — ask them for the file)"}`,
    [s.n ? s.n + "p" : null, rep.outcome && rep.outcome.rounds
      ? rep.outcome.rounds + " rounds" : null,
     rep.build && rep.build.commit ? "build " + rep.build.commit : null,
     rules || null, fb.name || who ? "from " + (fb.name || who) : null,
    ].filter(Boolean).join(" · "),
    fb.rating ? `rating ${fb.rating}/5` + (fb.again ? `, play again: ${fb.again}` : "") : null,
    fb.confusing ? `confusing: ${fb.confusing}` : null,
    fb.best ? `best: ${fb.best}` : null,
    (rep.flags || []).length ? `${rep.flags.length} flag(s) raised mid-game` : null,
  ].filter(Boolean);
}

async function notifyReport(rep, stored) {
  const url = process.env.BLINK_NOTIFY_URL;
  if (!url) return false;
  const text = notifyLines(rep, stored).join("\n");
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, content: text, stored, id: rep.id }),
    });
    return !!(r && r.ok);
  } catch (e) {
    console.error("blink: could not send the report notification —", e && e.message);
    return false;
  }
}

/* Read one stored report back. A private blob's URL is not fetchable on its
 * own, so this goes through the SDK with the token; a public store still works
 * because `get` handles both and a plain fetch is the fallback. */
async function readReport(blob, token) {
  let get = null;
  try { ({ get } = require("@vercel/blob")); } catch (e) { /* older SDK */ }
  if (get) {
    for (const access of ["private", "public"]) {
      try {
        const r = await get(blob.pathname, { access, token });
        if (r && r.stream) {
          const chunks = [];
          for await (const c of r.stream) chunks.push(Buffer.from(c));
          return JSON.parse(Buffer.concat(chunks).toString("utf8"));
        }
      } catch (e) { /* try the other access mode, then the URL */ }
    }
  }
  try {
    const r = await fetch(blob.url);
    if (r.ok) return await r.json();
  } catch (e) { /* reported by the caller as a null entry */ }
  return null;
}

/* List what has been kept, and — with `?full=1` — what people actually wrote.
 *
 * A list of blob keys answers "did anything arrive"; it does not answer "what
 * did they say", which is the only reason any of this exists. So `full` pulls
 * each report and returns the human parts: the feedback form, the flags raised
 * mid-game, who was playing and under which rules. The whole replay stays out
 * of it — it is most of the bytes and none of the reading.
 */
async function getReports(store, p, url) {
  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token) return { ok: false, why: "no report store bound" };
  let list;
  try { ({ list } = require("@vercel/blob")); }
  catch (e) { return { ok: false, why: "no report store bound" }; }
  const prefix = "blink/reports/" + (url.searchParams.get("commit") || "");
  try {
    const out = await list({ prefix, limit: 500, token });
    const blobs = out.blobs.slice().sort((a, b) =>
      String(b.uploadedAt).localeCompare(String(a.uploadedAt)));   // newest first
    if (!url.searchParams.get("full"))
      return { ok: true, count: blobs.length, reports: blobs.map((b) => ({
        key: b.pathname, size: b.size, at: b.uploadedAt, url: b.url })) };

    const want = Math.min(Number(url.searchParams.get("limit")) || 50, 200);
    const reports = [];
    for (const b of blobs.slice(0, want)) {
      const rep = await readReport(b, token);
      if (!rep) { reports.push({ key: b.pathname, at: b.uploadedAt, unreadable: true }); continue; }
      reports.push({
        key: b.pathname, at: b.uploadedAt,
        id: rep.id, lang: rep.lang, seconds: rep.seconds,
        build: rep.build && rep.build.commit,
        setup: rep.setup,
        players: rep.players,
        rounds: rep.outcome && rep.outcome.rounds,
        scores: rep.outcome && rep.outcome.scores
          && rep.outcome.scores.map((s) => `${s.seat}:${s.total}`).join(" "),
        /* The point of the whole file. */
        feedback: rep.feedback || null,
        flags: (rep.flags || []).map((f) => ({ r: f.r, t: f.t, note: f.note })),
        undos: rep.undos || 0,
      });
    }
    return { ok: true, count: blobs.length, shown: reports.length, reports };
  } catch (e) {
    /* Same reasoning as putReport: say what went wrong rather than 500 at the
     * one person who is allowed to read this and has the key in hand. */
    return { ok: false, why: "listing failed", detail: String(e && e.message) };
  }
}

/* Vercel runs this by taking whatever the file exports and, if it is an http
 * server, serving it. Truncating the file while editing once removed these two
 * lines, and the deployment's only symptom was FUNCTION_INVOCATION_FAILED with
 * no stack — hence vercel_test.js, which loads the built file the way the
 * platform does and checks there is something here with a `.listen` on it. */
module.exports = server;
module.exports.default = server;
