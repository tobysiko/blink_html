/* Playing with people who are not in the room.
 *
 * Nothing about the board crosses the wire. Every client runs its own copy of
 * the engine and stays in step by applying the same answers in the same order,
 * because a game is a pure function of seed, options and answers. So this file
 * is small: it opens a socket, sends what you did, and applies what everybody
 * else did.
 *
 * The rules of who may do what are the server's, in session.js. What is left
 * here is the part that is genuinely a client's problem:
 *
 *   - **Your answer is not applied until it comes back.** The server is the
 *     authority on order, and a client that moved first and asked afterwards
 *     would show you a board nobody else can see. The wait is one round trip.
 *   - **A dropped connection is normal.** Phones sleep, trains go into
 *     tunnels. The player token is kept, reconnection is automatic with a
 *     backoff, and coming back means being handed the log again — there is
 *     nothing else to restore.
 *   - **If we ever disagree with the server, the server is right.** A `sync`
 *     rebuilds the whole game from the log rather than trying to patch it.
 */

const NET_RETRY = [400, 900, 2000, 4000, 8000, 15000];

let NET = null;   /* {api, code, token, seat, name, ws, state, tries, timer,
                     status: "connecting"|"lobby"|"playing"|"lost"|"gone"} */

const netOn = () => !!(NET && NET.code);
const netMySeat = () => (NET ? NET.seat : null);

/* Tokens are per session and per browser: keeping one lets a refresh — or a
 * phone that went to sleep for ten minutes — walk back into the same seat. */
function netToken(code, set) {
  const key = "blink.session." + code;
  try {
    if (set !== undefined) { localStorage.setItem(key, set); return set; }
    return localStorage.getItem(key);
  } catch (e) { return null; }          // private mode: you get one connection
}

function netApi() {
  return (BUILD.api || "").replace(/\/$/, "");
}

/* The link you send people. Same page, one parameter — no separate app, no
 * install, and it still works if they have never heard of the game. */
function netLink(code) {
  const u = new URL(location.href);
  u.search = "?s=" + code;
  u.hash = "";
  return u.toString();
}
function netCodeInUrl() {
  const m = /[?&]s=([A-Za-z0-9-]{4,12})/.exec(location.search);
  return m ? m[1].toUpperCase() : null;
}

/* ---- opening one ------------------------------------------------------- */

function netCreate(rules) {
  const api = netApi();
  if (!api) return Promise.reject(new Error("no session service in this build"));
  return fetch(api + "/session", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(rules),
  }).then((r) => r.json()).then((r) => {
    if (!r.ok) throw new Error(r.why || "could not open a session");
    return r.code;
  });
}

function netConnect(code, name, handlers) {
  const api = netApi();
  if (!api) throw new Error("no session service in this build");
  NET = { api, code, name, token: netToken(code), seat: null, ws: null,
          state: null, tries: 0, timer: null, status: "connecting",
          on: handlers || {} };
  netOpen();
  return NET;
}

function netOpen() {
  if (!NET) return;
  const url = NET.api.replace(/^http/, "ws") + "/session/" + NET.code + "/ws";
  let ws;
  try { ws = new WebSocket(url); }
  catch (e) { return netLost(); }
  NET.ws = ws;
  ws.onopen = () => {
    NET.tries = 0;
    netSend({ t: "hello", name: NET.name, token: NET.token || undefined });
  };
  ws.onmessage = (ev) => {
    let msg = null;
    try { msg = JSON.parse(ev.data); } catch (e) { return; }
    netMessage(msg);
  };
  ws.onclose = () => netLost();
  ws.onerror = () => { /* onclose follows */ };
}

/* Reconnect with a backoff, and say so on screen. A game that silently stops
 * responding is indistinguishable from a game that has crashed. */
function netLost() {
  if (!NET || NET.status === "gone") return;
  NET.ws = null;
  NET.status = "lost";
  if (NET.on.status) NET.on.status(NET);
  const wait = NET_RETRY[Math.min(NET.tries++, NET_RETRY.length - 1)];
  clearTimeout(NET.timer);
  NET.timer = setTimeout(netOpen, wait);
}

function netClose() {
  if (!NET) return;
  NET.status = "gone";
  clearTimeout(NET.timer);
  try { if (NET.ws) NET.ws.close(); } catch (e) { /* already gone */ }
  NET = null;
}

function netSend(msg) {
  if (!NET || !NET.ws || NET.ws.readyState !== 1) return false;
  try { NET.ws.send(JSON.stringify(msg)); return true; }
  catch (e) { return false; }
}

/* ---- what comes back --------------------------------------------------- */

function netMessage(msg) {
  if (!NET) return;
  const on = NET.on;
  switch (msg.t) {
    case "welcome":
      NET.token = msg.token;
      NET.seat = msg.seat;
      NET.name = msg.name;
      netToken(NET.code, msg.token);
      NET.state = msg.state;
      NET.status = msg.state.phase === "lobby" ? "lobby" : "playing";
      if (on.welcome) on.welcome(msg);
      return;
    case "seats":
      NET.state = msg.state;
      if (on.seats) on.seats(msg.state);
      return;
    case "start":
      NET.state = msg.state;
      NET.status = "playing";
      if (on.start) on.start(msg.state);
      return;
    case "answer":
      if (on.answer) on.answer(msg);
      return;
    case "undo":
      if (on.undo) on.undo(msg);
      return;
    case "sync":
      NET.state = msg.state;
      if (on.sync) on.sync(msg.state);
      return;
    case "flagged":
      if (on.flagged) on.flagged(msg.flag);
      return;
    case "error":
      if (on.error) on.error(msg.why);
      return;
    default:
      return;
  }
}

if (typeof module !== "undefined" && module.exports)
  module.exports = { netOn, netMySeat, netLink, netCodeInUrl, netCreate,
                     netConnect, netClose, netSend, netMessage };
