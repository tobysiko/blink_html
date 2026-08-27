/* Two people, two browsers, one table.
 *
 * session_test.js checks the rules of the protocol with no sockets in the way.
 * This one runs the whole thing for real: the node dev server on a port, two
 * jsdom pages loading the actual built file, a real WebSocket between them,
 * and a whole game played by clicking.
 *
 * What it is looking for is the failure this architecture could plausibly
 * have: **two boards that quietly stop agreeing.** Every client runs its own
 * engine, so a single dropped or misordered message would leave two people
 * playing different games while both screens look perfectly fine. So the two
 * pages are compared position for position, at every step, all game.
 *
 * Also checked, because each is a thing a real table does on a real evening:
 *   - joining by link, with a name, and being given a seat;
 *   - only the host starting, and empty seats becoming bots;
 *   - a player who taps twice, or whose message crosses with somebody else's;
 *   - a phone that drops the connection mid-game and comes back;
 *   - somebody trying to play out of turn from the console;
 *   - and undo, which is a request here rather than a local rewind.
 *
 * Needs jsdom and ws:  npm install jsdom ws
 */
const fs = require('fs');
const path = require('path');
let JSDOM, WebSocket;
try { ({ JSDOM } = require('jsdom')); WebSocket = require('ws'); }
catch (e) { console.error('this test needs jsdom and ws — run: npm install jsdom ws'); process.exit(2); }

const PORT = 8799 + (process.pid % 60);
const html = fs.readFileSync(require('./test_setup.js').PLAY_HTML, 'utf8');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };
/* Stop here, but say why. The setup path used to run on into `NET.seat` after
 * NET had stayed null, so a table that never opened was reported as
 * "Cannot read properties of null" at a line that is not the problem. */
function bail(what, pages) {
  fail.push(what);
  for (const [n, p] of pages || [])
    if (p.errs.length) fail.push(`  ${n} page errors: ` + [...new Set(p.errs)].slice(0, 3).join(' | '));
  console.log('FAIL:\n  ' + fail.join('\n  '));
  process.exit(1);
}
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
/* Poll rather than sleep: a round trip over a loopback socket takes about a
 * millisecond, and a test that sleeps for a fixed 35 takes six minutes. */
async function until(fn, ms, every) {
  const stop = Date.now() + (ms || 3000);
  for (;;) {
    let v; try { v = fn(); } catch (e) { v = false; }
    if (v) return v;
    if (Date.now() > stop) return false;
    await wait(every || 3);
  }
}

/* Point the built page at our own server. The page reads BUILD.api, which a
 * local build leaves null — this is exactly what BLINK_API sets at build time,
 * done here without rebuilding. */
const API = `http://localhost:${PORT}`;
const page = () => {
  const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true,
                                url: `${API}/play.html` });
  const w = dom.window;
  const errs = [];
  w.addEventListener('error', (e) => errs.push(e.message));
  w.console.error = (...a) => errs.push(a.join(' '));
  w.WebSocket = WebSocket;                  // jsdom has none
  /* jsdom's fetch is not wired to a server, so give it node's. */
  w.fetch = (u, o) => fetch(String(u), o);
  return { dom, w, d: w.document, errs };
};

const srv = require(path.join(__dirname, '..', 'server', 'dev.js'));

async function main() {
  await srv.ready();                       // the store is picked at boot now
  await new Promise((r) => srv.server.listen(PORT, r));

  const A = page(), B = page();
  /* The built page is one file with the whole engine in it, and jsdom parses
   * and runs it from cold. How long that takes is a property of the machine,
   * not of the game — 300ms was enough here and not on a laptop that had just
   * done an npm install. Wait for the page to have finished booting: a
   * function declaration hoists as soon as the script starts, so waiting for
   * netSetup alone would return before the page had called it itself. */
  const loaded = await until(() => A.w.netSetup && B.w.netSetup
    && A.d.readyState === 'complete' && B.d.readyState === 'complete', 20000, 10);
  if (!loaded) bail('the built page never finished loading in jsdom', [['host', A], ['guest', B]]);
  for (const p of [A, B]) p.w.eval(`BUILD.api = ${JSON.stringify(API)}`);

  // ---------------------------------------------------- host opens a table
  A.w.eval('netSetup()');
  ok(!A.d.querySelector('#remote').hidden,
     'a build that knows a table service does not offer to open one');
  A.d.querySelector('#net-name').value = 'Toby';
  A.d.querySelector('#net-host').dispatchEvent(new A.w.MouseEvent('click', { bubbles: true }));

  /* Opening a table is a POST and then a socket and then a hello coming back.
   * Three round trips, so wait for the answer rather than for a duration. */
  const code = await until(() => A.w.eval('NET && NET.code'), 20000, 5);
  if (!code) bail(`opening a table produced no code (NET is `
    + `${A.w.eval('NET ? NET.status : "null"')}, server on ${API})`, [['host', A]]);
  await until(() => A.w.eval('NET.seat !== null'), 20000, 5);
  ok(A.d.body.classList.contains('lobby'), 'the host was not shown the lobby');
  ok(A.w.eval('NET.seat') === 0, `the host got seat ${A.w.eval('NET.seat')}`);
  const link = A.d.querySelector('#lobby-link').value;
  ok(link.includes('?s=' + code), `the link "${link}" does not carry the code`);
  ok(A.d.querySelectorAll('.lseat').length === 3, 'the lobby does not list the seats');
  ok(!A.d.querySelector('#lobby-start').hidden, 'the host cannot start');

  // ------------------------------------------------- a guest opens the link
  /* The whole point of a link: a stranger with a URL and a name, nothing else. */
  B.w.eval(`history.replaceState(null, '', ${JSON.stringify('/play.html?s=' + code)})`);
  B.w.eval('$("#net-name").value = "Anna"');
  B.w.eval('netSetup()');
  const seated = await until(() => B.w.eval('NET && NET.seat !== null'), 20000, 5);
  if (!seated) bail(`the guest never got a seat at ${code} (NET is `
    + `${B.w.eval('NET ? NET.status : "null"')})`, [['guest', B]]);
  ok(B.w.eval('NET && NET.code') === code, 'the guest did not join from the link');
  ok(B.d.body.classList.contains('lobby'), 'the guest was not shown the lobby');
  const bSeat = B.w.eval('NET.seat');
  ok(bSeat !== null && bSeat !== 0, `the guest took seat ${bSeat}`);
  ok(A.d.querySelector('#lobby-seats').textContent.includes('Anna'),
     "the host's lobby never heard that Anna arrived");
  ok(B.d.querySelector('#lobby-start').hidden, 'a guest is offered the start button');

  // a guest cannot start it
  B.w.eval('netSend({t:"start"})');
  await wait(200);
  ok(A.w.eval('NET.state.phase') === 'lobby', 'a guest started the game');

  // ------------------------------------------------------------ play
  A.d.querySelector('#lobby-start').dispatchEvent(new A.w.MouseEvent('click', { bubbles: true }));
  const begun = await until(() => A.w.eval('G !== null') && B.w.eval('G !== null'), 20000, 5);
  if (!begun) bail('the game never started on both clients', [['host', A], ['guest', B]]);
  for (const [n, p] of [['host', A], ['guest', B]]) {
    ok(p.w.eval('G !== null'), `the ${n} has no game after start`);
    ok(!p.d.body.classList.contains('lobby'), `the ${n} is still in the lobby`);
    ok(p.d.body.classList.contains('playing'), `the ${n} is not playing`);
  }
  ok(A.w.eval('ME') === 0 && B.w.eval('ME') === bSeat,
     'a client is showing somebody else’s seat');
  ok(A.w.eval('HUMANS.join()') === B.w.eval('HUMANS.join()'),
     'the two clients disagree about which seats are people');
  ok(A.w.eval('G.n') === 3 && A.w.eval('HUMANS.length') === 2,
     'the third seat did not become a bot');

  /* Keep every refusal the server sends, so a stall can name its cause. */
  for (const p of [A, B])
    p.w.eval('NETERR = []; (function(){ const h = NET.on.error;'
           + ' NET.on.error = (w) => { NETERR.push(w); h(w); }; })()');

  // out of turn, from the console — the server must refuse it
  const asked = () => A.w.eval('REQ ? REQ.seat : null');
  const idle = asked() === 0 ? B : A;
  const before = A.w.eval('LOG.length');
  idle.w.eval('netSend({t:"answer", step: LOG.length, token: {pick:0}})');
  await wait(250);
  ok(A.w.eval('LOG.length') === before, 'a player answered out of turn');

  // the double tap: the same answer twice, as fast as a finger can do it
  const turnOf = asked();
  const actor = turnOf === 0 ? A : B;
  actor.w.eval('netSend({t:"answer", step: LOG.length, token: {pick:0}});'
             + 'netSend({t:"answer", step: LOG.length, token: {pick:0}})');
  await wait(300);
  ok(A.w.eval('LOG.length') === before + 1,
     `a double tap played ${A.w.eval('LOG.length') - before} answers`);

  // ------------------------------------------- a whole game, in step
  /* Defined once on each page and then called, rather than re-compiled on
   * every comparison: jsdom parses each eval afresh, and this one runs a few
   * thousand times. */
  for (const p of [A, B]) p.w.eval(`window.__snap = () => G ? JSON.stringify({
    round: G.round, len: LOG.length, gold: G.P.map((q) => q.gold),
    hands: G.P.map((q) => q.hand.length),
    map: [...G.m.tiles.entries()].map(([k, t]) => k + ':' + t.terrain + ':' + t.units.join(',')).sort(),
    vrow: G.P.map((q) => q.vrow.map((c) => c.r + c.s).sort()),
  }) : null;
  window.__at = () => (REQ ? REQ.seat : -1);
  window.__len = () => LOG.length;`);
  const snap = (p) => p.w.__snap();
  /* The host applies an answer when it sends it; the guest applies it when the
   * server echoes it back, which is a round trip later. So the two boards are
   * legitimately different for a millisecond or so after every move, and
   * comparing them at an arbitrary instant measures the network rather than
   * the game — it passed on a fast machine and failed on a laptop.
   *
   * What must be true is that they CONVERGE. Two clients that settle on the
   * same board after every answer are in step; two that never do are the
   * failure this whole test exists to find, and keeping them apart matters
   * because only one of them is a bug. */
  const level = (ms) => until(() => A.w.__len() === B.w.__len(), ms || 4000, 2);
  if (process.env.NET_TRACE)
    fs.appendFileSync('/tmp/nettrace.log', `pre-loop reached at ${Date.now()}, snap ok: `
      + (snap(A) ? 'yes' : 'no') + '\n');

  /* Long enough to cross several round boundaries, take turns each, lose a
   * connection and take moves back — not the whole game. Playing one to the
   * end is session_test.js's job, without sockets in the way. What is being
   * proved here is that the transport keeps two engines in step, and that is
   * either true within fifty moves or it is not true at all. */
  const STEPS = Number(process.env.NET_STEPS) || 30;
  let steps = 0, drifted = 0, undid = 0, dropped = false, rounds = 0;
  const started = Date.now();
  while (steps++ < STEPS && Date.now() - started < 150000) {
    if (A.w.eval('G && G.finished()')) break;
    rounds = Math.max(rounds, A.w.eval('G ? G.round : 0'));
    if (process.env.NET_TRACE)
      fs.appendFileSync('/tmp/nettrace.log',
        `step ${steps} t=${Date.now() - started}ms round ${rounds} log ${A.w.__len()}\n`);

    /* Neither client may ever move its view to somebody else's seat. In hot
     * seat that is the whole mechanic; here it would put another player's
     * hand on your screen. */
    if (A.w.eval('ME') !== 0 || B.w.eval('ME') !== bSeat) {
      fail.push(`a client is showing the wrong seat: host ME ${A.w.eval('ME')} (should be 0), `
        + `guest ME ${B.w.eval('ME')} (should be ${bSeat}) — that is somebody else's hand`);
      break;
    }

    // the two boards must be the same board, once both have caught up
    if (!dropped) {
      const caught = await level();
      const a = snap(A), b = snap(B);
      if (!caught) {
        drifted += 1;
        if (drifted === 1)
          fail.push(`the guest never caught up at step ${steps}: host has `
            + `${A.w.__len()} answers, guest ${B.w.__len()}, guest net `
            + `${B.w.eval('NET.status')} — a message went missing`);
      } else if (a !== b) {
        drifted += 1;
        if (drifted === 1)
          fail.push('the two clients applied the same answers and got DIFFERENT boards:'
            + '\n      host:  ' + String(a).slice(0, 150)
            + '\n      guest: ' + String(b).slice(0, 150));
      }
    }

    /* Bots resolve between our turns, so wait for the next question rather
     * than for the clock. */
    const seat = await until(() => {
      const x = A.w.__at();
      return x >= 0 ? x + 1 : false;
    }, 4000, 2);
    if (seat === false) {
      if (A.w.eval('G && G.finished()')) break;
      fail.push('the game stopped asking anybody anything at step ' + steps
        + ': host ' + String(snap(A)).slice(0, 120)
        + ' | guest ' + String(snap(B)).slice(0, 120)
        + ' | prompt "' + A.d.querySelector('#prompt').textContent.replace(/\s+/g, ' ').slice(0, 60) + '"');
      break;
    }
    const at = seat - 1;
    const who = at === A.w.eval('NET.seat') ? A : (at === bSeat ? B : null);
    if (!who) { fail.push(`the game is asking seat ${at}, which nobody holds`); break; }

    /* Halfway through, pull the guest's connection out — a phone going into a
     * tunnel is the normal case, not the exceptional one. */
    if (!dropped && steps === Math.floor(STEPS / 2)) {
      dropped = true;
      B.w.eval('NET.ws.close()');
      await until(() => B.w.eval('NET.status') === 'lost', 1500, 10);
      ok(B.w.eval('NET.status') === 'lost', 'the guest did not notice it had dropped');
      ok(!B.d.querySelector('#netbar').hidden,
         'the page says nothing while the connection is down');
      const backUp = await until(() => B.w.eval('NET.ws && NET.ws.readyState === 1'), 8000, 20);
      ok(backUp, 'the guest never reconnected');
      await until(() => B.w.eval('NET.status') === 'playing', 3000, 10);
      ok(B.w.eval('NET.seat') === bSeat, 'the guest came back in a different seat');
      /* Coming back means replaying everything missed, so give it the same
       * convergence test rather than a guess at how long that takes. */
      ok(await level(8000), 'the guest never caught up on what it missed while away');
      const a2 = snap(A), b2 = snap(B);
      ok(a2 === b2, 'after reconnecting the guest is on a different board:\n      host:  '
        + String(a2).slice(0, 150) + '\n      guest: ' + String(b2).slice(0, 150));
      dropped = false;
      continue;
    }

    const len = A.w.__len();
    /* Wait for the acting client to reach the same question before clicking
     * it. A person clicks what is on their own screen, and their screen has
     * caught up by the time they look at it — a test that clicks a stale one
     * is testing nothing. It is also an assertion: everybody must arrive. */
    const caught = await until(() => who.w.__len() === len && who.w.__at() === at, 3000, 2);
    if (!caught) {
      fail.push(`${who === A ? 'the host' : 'the guest'} never reached the question `
        + `the table is on: it is at log ${who.w.eval('LOG.length')} `
        + `${who.w.eval('REQ ? REQ.type + "@" + REQ.seat : "(no request)"')}, `
        + `the table at log ${len} seat ${at}`);
      break;
    }
    clickThrough(who);
    /* The answer is not applied until it comes back — that is the design, so
     * waiting for the echo IS the assertion. */
    const moved = await until(() => A.w.__len() !== len, 3000, 2);
    if (!moved) {
      const p = who.d.querySelector('#prompt').textContent.replace(/\s+/g, ' ').slice(0, 80);
      fail.push(`a click produced no answer: seat ${at}, `
        + `${who === A ? 'host' : 'guest'} prompt "${p}" `
        + `| its REQ ${who.w.eval('REQ ? REQ.type + "@" + REQ.seat : "none"')} `
        + `| its LOG ${who.w.eval('LOG.length')} vs host ${len} `
        + `| net ${who.w.eval('NET.status')} `
        + `| refusals ${who.w.eval('JSON.stringify(NETERR.slice(-3))')}`);
      break;
    }

    /* One undo, once, from whichever client happens to be acting — the limits
     * on it are session_test.js's business; what matters here is that a
     * request to take a move back travels and lands on both screens. */
    if (!undid && steps > 4 && !who.d.querySelector('#undo').disabled) {
      const n = A.w.__len();
      who.d.querySelector('#undo').dispatchEvent(new who.w.MouseEvent('click', { bubbles: true }));
      await until(() => A.w.__len() < n, 2000, 2);
      if (A.w.__len() < n) undid += 1;
    }
  }

  ok(rounds >= 2, `only reached round ${rounds} in ${steps} moves`);
  ok(drifted === 0, `the clients drifted apart on ${drifted} of ${steps} moves`);
  ok(undid > 0, 'the run never managed a remote undo');
  ok(await level(8000), 'the two clients ended with different numbers of answers applied');
  ok(snap(A) === snap(B), 'the two clients ended on different boards');
  /* Same log, same engine, same arithmetic — if the scores differ, the two
   * people at this table would be told different things about who is winning. */
  const fa = A.w.eval('JSON.stringify(G.score().map((x) => x.total))');
  const fb = B.w.eval('JSON.stringify(G.score().map((x) => x.total))');
  ok(fa === fb, `the two clients score the position differently: ${fa} vs ${fb}`);

  // ---------------------------------------------------- and the report
  const rep = JSON.parse(A.w.eval('JSON.stringify(REP)'));
  ok(rep.session === code, 'the report does not say which table it was played at');
  ok(rep.players.some((p) => p.name === 'Anna'),
     'the report does not record who was at the table');
  ok(rep.replay.length === A.w.eval('LOG.length'),
     'the report and the game disagree about what was answered');

  for (const [n, p] of [['host', A], ['guest', B]])
    if (p.errs.length) fail.push(`${n} errors: ` + [...new Set(p.errs)].slice(0, 2).join(' | '));

  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : `remote: two browsers joined one table by link and played ${rounds} rounds `
      + `over ${steps} moves in perfect step — surviving a dropped connection, a `
      + `double tap and ${undid} undos, refusing an out-of-turn move, and agreeing `
      + `on the board and the score throughout`);
  process.exit(fail.length ? 1 : 0);
}

/* One click, whatever the page is asking for. */
function clickThrough(p) {
  const { w, d } = p;
  const click = (x) => x && x.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const qa = (s) => [...d.querySelectorAll(s)];
  const q = (s) => d.querySelector(s);
  const btn = (re) => qa('#prompt button').find((b) => re.test(b.textContent) && !b.disabled);
  const t = q('#prompt').textContent.replace(/\s+/g, ' ');

  if (btn(/Begin research/)) return click(btn(/Begin research/));
  if (btn(/Continue my turn/)) return click(btn(/Continue my turn/));
  /* A duel arrives on somebody ELSE's turn and in whatever language the page
   * is set to, so it is matched on the request rather than on the sentence:
   * commit a card, or decline if the hand has nothing legal. */
  if (w.eval('REQ && REQ.type') === 'duel') {
    const c = qa('#hand button.want')[0] || qa('#hand button').find((b) => !b.disabled);
    return click(c || qa('#prompt button').find((b) => !b.disabled));
  }
  if (/Play a meld/.test(t)) {
    /* Look, then click, then look again. Every click re-renders the hand, so a
     * list of buttons captured once goes stale after the first one — and a
     * remote game re-renders on other people's moves too, which is how this
     * loop first went wrong. Grow the meld while it stays legal. */
    for (let i = 0; i < 8; i++) {
      const hand = qa('#hand button');
      const next = hand.find((b) => !/\bsel\b/.test(b.className));
      if (!next) break;
      const at = hand.indexOf(next);
      click(next);
      if (process.env.MELDTRACE)
        console.log(`  meld i=${i} clicked ${at}/${hand.length} -> SEL ` +
          w.eval('SEL.meld.length') + ' play ' +
          w.eval('(() => { const b = [...document.querySelectorAll("#prompt button")]'
          + '.find((x) => /Play meld/.test(x.textContent)); return b ? (b.disabled ? "off" : "ON") : "none"; })()'));
      const play = qa('#prompt button').find((x) => /Play meld/.test(x.textContent));
      if (play && play.disabled) {                 // that made it illegal
        const again = qa('#hand button')[at];
        if (again) click(again);                   // put it back
        break;
      }
    }
    return click(btn(/Play meld/));
  }
  if (/matched the winner/.test(t)) return click(q('#mymeld button[data-aside]'));
  if (/Your turn/.test(t)) {
    const cs = qa('#mymeld button[data-turn]');
    if (cs.length) {
      click(cs[0]);
      const h = q('#map .hot');
      return h ? click(h) : click(btn(/^Cash /));
    }
    return click(btn(/^End turn/));
  }
  if (/Give up|Retire a card|spend one extra|shared pile/.test(t))
    return click(qa('#hand button.want')[0] || qa('#hand button')[0]);
  if (/Take a card/.test(t)) return click(q('.slot.hot') || btn(/Cancel/));
  if (/Famine/.test(t)) return click(q('.vrowbox button.want') || btn(/Take the loss/));
  if (/Secret objective/.test(t)) return click(q('.objpick button'));
  const b = btn(/Skip|Stop|Cancel|Take the loss|Keep this card|Play no effect/);
  return b ? click(b) : click(q('#map .hot'));
}

main().catch((e) => {
  try { fs.appendFileSync('/tmp/nettrace.log', 'THREW: ' + e.stack + '\n'); } catch (x) { /* */ }
  console.error('FAIL: ' + e.stack);
  process.exit(1);
});
