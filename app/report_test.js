/* A playtest report has to be worth the person's time.
 *
 * The claim it makes is strong: "this is the whole game, replayable card for
 * card, from a named build". That claim is checkable, and this checks it — by
 * playing a real game through the real interface, taking the report it
 * produces, and **re-dealing the game from the report alone** in a separate
 * engine. If the two final positions differ by so much as a coin, the report
 * is a summary pretending to be a record.
 *
 * Also checks the things that fail quietly:
 *   - the build stamp is a real commit, and says when it is dirty;
 *   - undo rewinds the record too, or the replay stops matching the game;
 *   - flags carry where they were raised, not just what was typed;
 *   - every human decision is timed, and undo marks the one it took back;
 *   - nothing is sent anywhere without the person pressing the button.
 *
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const E = require('./engine.js');
/* The one decoder. See rebuild(). */
const S = require('./session.js');
const html = fs.readFileSync(require('./test_setup.js').PLAY_HTML, 'utf8');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
const errs = [];
w.addEventListener('error', (e) => errs.push(e.message));
w.console.error = (...a) => errs.push(a.join(' '));

/* Nothing may leave the machine on its own. If fetch is called at all before
 * the send button is pressed, that is a bug worth failing over. */
let posted = [];
w.fetch = (url, opts) => { posted.push({ url, opts }); return Promise.resolve({ ok: true }); };
let downloaded = 0;
w.URL.createObjectURL = () => { downloaded += 1; return 'blob:x'; };
w.URL.revokeObjectURL = () => {};

const click = (x) => x.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
const q = (s) => d.querySelector(s);
const qa = (s) => [...d.querySelectorAll(s)];
const btn = (re) => qa('#prompt button').find((b) => re.test(b.textContent) && !b.disabled);
const txt = () => q('#prompt').textContent.replace(/\s+/g, ' ');

setTimeout(() => {
  require('./test_setup.js').start(w, d, { players: 3, seat: 0, seed: 31 });

  const B = w.eval('JSON.stringify(BUILD)') && JSON.parse(w.eval('JSON.stringify(BUILD)'));
  ok(!!B.commit, 'the build carries no commit id');
  ok(B.commit === 'unknown' || /^[0-9a-f]{7,40}$/.test(B.commit),
     `the build stamp "${B.commit}" is not a commit id`);
  ok(typeof B.dirty === 'boolean' || B.dirty === null,
     'the build does not say whether it was made from uncommitted edits');
  ok(!!B.built && !!B.version, 'the build stamp is missing its version or date');

  let steps = 0, flagged = false, undos = 0;
  const tick = () => {
    const t = txt();
    if (/Game over/.test(t) || steps++ > 5000) return done();

    // raise one flag, mid-game, exactly as a person would
    if (!flagged && steps > 25 && w.eval('REQ && REQ.seat === ME')) {
      flagged = true;
      click(q('#flag'));
      ok(!q('#flagbox').hidden, 'the flag dialog did not open');
      ok(q('#flag-where').textContent.length > 4, 'the flag dialog does not say where you are');
      q('#flag-note').value = 'I could not tell why this was greyed out';
      click(q('#flag-save'));
      ok(q('#flagbox').hidden, 'the flag dialog did not close');
      ok(/1 flagged|1 gemeldet/.test(q('#flag').textContent),
         'the header does not show that something was flagged');
    }

    if (btn(/Begin research/)) click(btn(/Begin research/));
    else if (btn(/Continue my turn/)) click(btn(/Continue my turn/));
    else if (/Play a meld/.test(t)) {
      for (const b of qa('#hand button')) {
        click(b);
        const p = qa('#prompt button').find((x) => /Play meld/.test(x.textContent));
        if (p && p.disabled) click(b);
      }
      const p = btn(/Play meld/); if (p) click(p);
    } else if (/matched the winner/.test(t)) {
      const r = q('#mymeld button[data-aside]'); if (r) click(r);
    } else if (/Your turn/.test(t)) {
      const cs = qa('#mymeld button[data-turn]');
      if (cs.length) {
        click(cs[0]);
        const h = q('#map .hot');
        if (h) click(h); else { const c = btn(/^Cash /); if (c) click(c); }
        // undo occasionally: the record must rewind with the game
        if (steps % 7 === 0 && !q('#undo').disabled) { click(q('#undo')); undos += 1; }
      } else click(btn(/^End turn/));
    } else if (/Your attack|attacking your|Dein Angriff|Angriff auf dein/.test(t)) {
      /* A duel. Commit a card most of the time, decline sometimes — both are
       * legal answers and both have to survive the round trip through the
       * report, or a replayed game diverges the moment somebody fights. */
      const c = qa('#hand button')[0];
      if (steps % 5 === 0 || !c) { const d = btn(/Don't fight/); if (d) click(d); }
      else click(c);
    } else if (/Give up|Retire a card|spend one extra|shared pile/.test(t)) {
      const c = qa('#hand button.want')[0] || qa('#hand button')[0]; if (c) click(c);
    } else if (/Take a card/.test(t)) {
      const s = q('.slot.hot'); if (s) click(s); else click(btn(/Cancel/));
    } else if (/Famine/.test(t)) {
      const r = q('.vrowbox button.want'); if (r) click(r); else click(btn(/Take the loss/));
    } else if (/Secret objective/.test(t)) click(q('.objpick button'));
    else {
      const b = btn(/Skip|Stop|Cancel|Take the loss|Keep this card|Play no effect/);
      if (b) click(b); else { const h = q('#map .hot'); if (h) click(h); }
    }
    setTimeout(tick, 0);
  };

  function finish() {
    console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ') : 'report: ok');
    process.exit(fail.length ? 1 : 0);
  }

  function done() {
    /* A stall used to crash a few lines later on a missing feedback form,
     * which said nothing about the cause. Say what the game was waiting for. */
    if (!/Game over/.test(txt())) {
      fail.push('the game never finished — after ' + steps + ' steps it was still '
        + 'waiting on: "' + txt().replace(/\s+/g, ' ').slice(0, 160) + '"');
      return finish();
    }
    ok(undos > 0, 'the run never undid anything, so the rewind is unchecked');

    // ---------- the form is there, and nothing has been sent
    ok(!!q('.fb'), 'no feedback form on the results screen');
    ok(posted.length === 0, 'the report was posted before anybody pressed send');
    ok(downloaded === 0, 'the report was downloaded before anybody asked');
    ok(qa('.fb .fbopt').length >= 8, 'the form is missing its one-tap questions');

    // answer it the way a person would
    const rate = qa('.fb .seg')[0].querySelectorAll('.fbopt')[3];
    click(rate);
    ok(qa('.fb .seg')[0].querySelectorAll('.fbopt')[3].classList.contains('on'),
       'picking a rating did not stick');
    click(qa('.fb .seg')[1].querySelectorAll('.fbopt')[0]);
    const ta = q('#confusing');
    ta.value = 'the water advantage never seemed to happen';
    ta.dispatchEvent(new w.Event('input', { bubbles: true }));
    q('#fb-name').value = 'Anna';
    q('#fb-name').dispatchEvent(new w.Event('input', { bubbles: true }));

    const rep = JSON.parse(w.eval('JSON.stringify(REP)'));

    // ---------- the claim: this IS the game
    ok(rep.replay.length > 20, `only ${rep.replay.length} answers recorded`);
    ok(rep.replay.length === w.eval('LOG.length'),
       'the report and the undo log disagree about what was answered');

    /* A record that cannot be replayed is the failure this test exists for, so
     * a throw here is a result, not a crash. */
    let re = null;
    try { re = rebuild(rep); }
    catch (e) { fail.push('the report could not be replayed at all: ' + e.message); }
    if (re) {
      const played = w.eval(SNAP);
      ok(re.snap === played,
         'the report does NOT re-deal the game that was played:\n      played: '
         + played.slice(0, 160) + '\n      replay: ' + re.snap.slice(0, 160));
      ok(re.g.round === rep.outcome.rounds,
         `replay ended on round ${re.g.round}, the report says ${rep.outcome.rounds}`);
    }

    // ---------- outcome and counters
    ok(rep.outcome && rep.outcome.scores.length === 3, 'the report has no final scores');
    ok(rep.outcome.scores.every((x) => typeof x.total === 'number'),
       'a final score is not a number');
    ok(rep.counters && Object.keys(rep.counters).length > 15,
       'the engine counters did not make it into the report');
    ok(rep.setup.seed === 31 && rep.setup.n === 3, 'the report misremembers the setup');
    ok(rep.build.commit === B.commit, 'the report does not carry the build it ran on');

    // ---------- the flag
    ok(rep.flags.length === 1, `${rep.flags.length} flags recorded, expected 1`);
    const f = rep.flags[0];
    ok(f && f.r > 0, 'the flag does not say which round it was raised in');
    ok(f && typeof f.step === 'number', 'the flag does not point into the replay');
    ok(f && /greyed out/.test(f.note), 'the flag lost what the person typed');

    // ---------- hesitation, timed honestly
    ok(rep.decisions.length > 20, 'no decision timings recorded');
    ok(rep.decisions.every((x) => x.ms >= 0 && x.ms < 60000),
       'a decision was timed at something impossible');
    ok(rep.decisions.some((x) => x.undone), 'undo did not mark the decision it took back');
    ok(rep.undos === undos, `report says ${rep.undos} undos, the run did ${undos}`);

    // ---------- and it is small enough to actually send
    const bytes = JSON.stringify(rep).length;
    ok(bytes < 120000, `the report is ${Math.round(bytes / 1024)} kB — too big to post casually`);

    // ---------- send: no endpoint in a local build, so it must fall back
    click([...q('.fbrow').children][0]);
    setTimeout(() => {
      const after = JSON.parse(w.eval('JSON.stringify(REP)'));
      ok(after.feedback && after.feedback.rating === 4,
         'the rating did not reach the report');
      ok(after.feedback.again === 'yes' && after.feedback.name === 'Anna',
         'the form answers did not reach the report');
      ok(/water advantage/.test(after.feedback.confusing || ''),
         'the free-text answer did not reach the report');
      if (w.eval('BUILD.reportUrl')) {
        ok(posted.length === 1, 'a build with an endpoint did not post the report');
      } else {
        ok(downloaded === 1, 'with no endpoint the report was not downloaded instead');
        ok(posted.length === 0, 'a build with no endpoint tried to post anyway');
      }
      ok(!!q('.fbdone'), 'the screen does not confirm the report went');

      if (errs.length) fail.push('errors: ' + [...new Set(errs)].slice(0, 2).join(' | '));
      console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
        : `report: ${rep.replay.length} answers re-deal the played game exactly, `
          + `${rep.decisions.length} decisions timed, ${Object.keys(rep.counters).length} counters, `
          + `flag and form attached, ${Math.round(bytes / 1024)} kB, nothing sent unasked`);
      process.exit(fail.length ? 1 : 0);
    }, 60);
  }

  tick();
}, 250);

/* Re-deal the game from the report alone, in a fresh engine, with no help from
 * the page that produced it. This is the whole promise. */
/* Replay a report the way the real thing does.
 *
 * This used to hand-roll two things: the option list, and the answer decoder.
 * Both drifted, and the second failure is the nastier one — session.js says in
 * as many words that there must be ONE decoder "or a whole table desynchronises",
 * and this file quietly kept a second. When a move learned to carry a `terrain`
 * (landfall lays a tile as it resolves), the copy dropped it: the replay laid no
 * tile, and a later move onto that cell died reading `.terrain` of undefined.
 * The option list drifted the same way, so a report of a game played under
 * total-rank scoring was rebuilt under card-count scoring and diverged.
 *
 * So: the real decoder, and the whole of `setup` passed through. Anything added
 * to a report's setup from now on is carried automatically, and anything the
 * codec learns is understood here for free.
 */
function rebuild(rep) {
  const { n, seed, ...rules } = rep.setup;
  const g = new E.Game(n, seed, Object.assign({ botStyle: 'mixed' }, rules));
  const decode = (req, tok) => S.decodeAnswer(g, req, tok);
  let it = g.playRound(), r = it.next(), i = 0, guard = 0;
  for (;;) {
    if (guard++ > 100000) break;
    if (r.done) {
      if (g.finished()) break;
      it = g.playRound(); r = it.next(); continue;
    }
    if (i >= rep.replay.length) break;
    r = it.next(decode(r.value, rep.replay[i++]));
  }
  return { g, snap: snapOf(g) };
}

/* The same picture the page takes of itself, computed here instead. */
const SNAP = `JSON.stringify({
  round: G.round, gold: G.P.map((p) => p.gold),
  hand: G.P.map((p) => p.hand.map((c) => c.r + c.s).sort()),
  vrow: G.P.map((p) => p.vrow.map((c) => c.r + c.s).sort()),
  units: G.P.map((p) => p.reserve),
  map: [...G.m.tiles.entries()].map(([k, t]) =>
        k + ':' + t.terrain + ':' + (t.units || []).join(',')).sort(),
  supply: G.m.supply,
})`;
function snapOf(g) {
  return JSON.stringify({
    round: g.round, gold: g.P.map((p) => p.gold),
    hand: g.P.map((p) => p.hand.map((c) => c.r + c.s).sort()),
    vrow: g.P.map((p) => p.vrow.map((c) => c.r + c.s).sort()),
    units: g.P.map((p) => p.reserve),
    map: [...g.m.tiles.entries()].map(([k, t]) =>
          k + ':' + t.terrain + ':' + (t.units || []).join(',')).sort(),
    supply: g.m.supply,
  });
}
