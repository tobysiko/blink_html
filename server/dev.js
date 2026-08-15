/* The same session service, on your own machine.
 *
 *   node server/dev.js            # http://localhost:8787
 *   node server/dev.js 9000       # somewhere else
 *
 * Then build the app pointed at it and open the page:
 *
 *   BLINK_API=http://localhost:8787 node app/build.js
 *
 * This exists for two reasons. Developing against a deployed Worker is slow
 * and needs an account, and — more importantly — a protocol you can only
 * exercise in production is a protocol nobody tests. Everything that decides
 * anything lives in app/session.js, so this file and the Durable Object are
 * both pure transport and cannot drift on the rules.
 *
 * Sessions live in memory and reports are written to server/reports/. Losing
 * them when you press Ctrl-C is the point of a dev server.
 *
 * Needs ws:  npm install ws   (in app/)
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const E = require(path.join(APP, 'engine.js'));
const S = require(path.join(APP, 'session.js'));
let WebSocketServer;
try { ({ WebSocketServer } = require(path.join(APP, 'node_modules', 'ws'))); }
catch (e) {
  try { ({ WebSocketServer } = require('ws')); }
  catch (e2) { console.error('this needs ws — run: (cd app && npm install ws)'); process.exit(2); }
}

const PORT = Number(process.argv[2]) || 8787;
const REPORTS = path.join(__dirname, 'reports');

const sessions = new Map();          // code -> {s, sockets:Map(ws->token)}
const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,OPTIONS',
  'access-control-allow-headers': 'content-type',
};
const send = (res, code, body) => {
  res.writeHead(code, Object.assign({ 'content-type': 'application/json' }, CORS));
  res.end(JSON.stringify(body));
};
const body = (req) => new Promise((ok) => {
  let b = '';
  req.on('data', (c) => { b += c; if (b.length > 4e6) req.destroy(); });
  req.on('end', () => { try { ok(JSON.parse(b || '{}')); } catch (e) { ok({}); } });
});

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  const p = url.pathname.replace(/\/+$/, '') || '/';
  if (req.method === 'OPTIONS') { res.writeHead(204, CORS); return res.end(); }

  if (p === '/' || p === '/health')
    return send(res, 200, { ok: true, service: 'blink-sessions (dev)',
                            protocol: S.SESSION_PROTOCOL, sessions: sessions.size });

  if (p === '/session' && req.method === 'POST') {
    const opts = await body(req);
    const s = S.newSession(opts);
    sessions.set(s.code, { s, sockets: new Map() });
    console.log(`session ${s.code}  ${s.n}p  seed ${s.seed}`);
    return send(res, 200, { ok: true, code: s.code, state: S.sessionState(s) });
  }

  const m = p.match(/^\/session\/([A-Za-z0-9-]{4,12})$/);
  if (m) {
    const room = sessions.get(m[1].toUpperCase());
    if (!room) return send(res, 404, { ok: false, why: 'session.unknown' });
    return send(res, 200, { ok: true, state: S.sessionState(room.s) });
  }

  if (p === '/report' && req.method === 'POST') {
    const rep = await body(req);
    if (!rep || !rep.schema) return send(res, 400, { ok: false, why: 'not a report' });
    fs.mkdirSync(REPORTS, { recursive: true });
    const name = `blink-${rep.build ? rep.build.commit : 'unknown'}-${rep.id || Date.now()}.json`;
    fs.writeFileSync(path.join(REPORTS, name), JSON.stringify(rep, null, 1));
    console.log(`report ${name}  ${(JSON.stringify(rep).length / 1024).toFixed(1)} kB  `
      + `${(rep.flags || []).length} flags  rating ${rep.feedback && rep.feedback.rating}`);
    return send(res, 200, { ok: true, id: rep.id, stored: true });
  }

  if (p === '/reports') {
    fs.mkdirSync(REPORTS, { recursive: true });
    return send(res, 200, { ok: true, reports: fs.readdirSync(REPORTS) });
  }

  send(res, 404, { ok: false, why: 'no such route' });
});

/* ---- the sockets: transport, and nothing else -------------------------- */

const wss = new WebSocketServer({ noServer: true });
server.on('upgrade', (req, socket, head) => {
  const url = new URL(req.url, 'http://x');
  const m = url.pathname.match(/^\/session\/([A-Za-z0-9-]{4,12})\/ws$/);
  const room = m && sessions.get(m[1].toUpperCase());
  if (!room) { socket.destroy(); return; }
  wss.handleUpgrade(req, socket, head, (ws) => attach(room, ws));
});

function attach(room, ws) {
  room.sockets.set(ws, null);
  const fill = (msg, token) => msg.state === true
    ? Object.assign({}, msg, { state: S.sessionState(room.s, token) })
    : msg;
  const post = (sock, msg) => {
    try { sock.send(JSON.stringify(msg)); } catch (e) { /* gone */ }
  };

  ws.on('message', (data) => {
    let msg = null;
    try { msg = JSON.parse(data.toString()); }
    catch (e) { return post(ws, { t: 'error', why: 'bad json' }); }
    let out;
    try { out = S.sessionHandle(room.s, E, { token: room.sockets.get(ws) }, msg); }
    catch (e) {
      console.error('handler threw:', e.message);
      return post(ws, { t: 'error', why: 'server error' });
    }
    if (out.token) room.sockets.set(ws, out.token);
    for (const step of out.to) {
      if (step.who === 'self') post(ws, fill(step.msg, room.sockets.get(ws)));
      else for (const [sock, tok] of room.sockets) post(sock, fill(step.msg, tok));
    }
  });

  const drop = () => {
    const token = room.sockets.get(ws);
    room.sockets.delete(ws);
    if (!token) return;
    S.sessionLeave(room.s, token);
    for (const [sock, tok] of room.sockets)
      post(sock, fill({ t: 'seats', state: true }, tok));
  };
  ws.on('close', drop);
  ws.on('error', drop);
}

if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`blink sessions (dev) on http://localhost:${PORT}`);
    console.log(`build the app against it:  BLINK_API=http://localhost:${PORT} node app/build.js`);
  });
}

module.exports = { server, sessions };
