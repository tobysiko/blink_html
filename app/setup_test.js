/* The setup page, and the two modes the seat rows unlock.
 *
 * Per-seat human/bot is not just a layout change: nought humans is a game you
 * watch, and two or more is one device passed around a table. Both are legal
 * in the engine and both have to be legal on screen — including the part that
 * matters most in hot seat, which is that the board is COVERED while the
 * device changes hands.
 *
 * Also checks the accessibility promises that are cheap to break: every
 * control labelled, groups in fieldsets with legends, and the advanced rules
 * folded away by default.
 *
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }
const T = require('./test_setup.js');

const html = fs.readFileSync(__dirname + '/../Blink-play-v0.22.html', 'utf8');
const fail = [];
const ok = (cond, what) => { if (!cond) fail.push(what); };

function page() {
  const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
  const errs = [];
  dom.window.console.error = (...a) => errs.push(a.join(' '));
  dom.window.addEventListener('error', (e) => errs.push(e.message));
  return { w: dom.window, d: dom.window.document, errs };
}

const A = page();
setTimeout(() => {
  const { w, d } = A;
  const qa = (s) => [...d.querySelectorAll(s)];

  // ---------------------------------------------------- the page itself
  /* Every control a person can operate needs a name a screen reader can read:
   * a <label for>, an enclosing <label>, or an aria-label. */
  for (const n of qa('#setup select, #setup input, #setup button')) {
    if (n.type === 'radio') {
      ok(!!d.querySelector(`label[for="${n.id}"]`), `radio ${n.id} has no label`);
      continue;
    }
    const named = (n.id && d.querySelector(`label[for="${n.id}"]`))
      || n.getAttribute('aria-label') || n.textContent.trim();
    ok(!!named, `${n.tagName.toLowerCase()}#${n.id || '(no id)'} has no accessible name`);
  }
  // radio groups are grouped and titled
  for (const g of ['#n-players', '#bot-level', '#lang']) {
    const fs_ = d.querySelector(g).closest('fieldset');
    ok(!!fs_, `${g} is not inside a fieldset`);
    ok(fs_ && !!fs_.querySelector('legend'), `${g}'s fieldset has no legend`);
  }
  ok(d.querySelector('#seats').closest('fieldset'), 'the seats are not a group');
  // the three headline choices are on the page, not behind the disclosure
  for (const sel of ['#lang', '#n-players', '#seed', '#seats', '#bot-level'])
    ok(!d.querySelector(sel).closest('#advanced'), `${sel} is hidden in Advanced`);
  // and the variants are behind it, closed
  const adv = d.querySelector('#advanced');
  ok(adv && adv.tagName === 'DETAILS', 'Advanced is not a disclosure element');
  ok(adv && !adv.open, 'Advanced starts open');
  for (const sel of ['#trick-rule', '#deck', '#meld-rules', '#grow-limits',
                     '#retire-rule', '#objectives'])
    ok(d.querySelector(sel).closest('#advanced'), `${sel} is not folded into Advanced`);

  // the defaults asked for
  ok(d.querySelector('#bot-level input:checked').value === 'normal',
     'difficulty does not default to normal');
  /* Every language visible at once, as a flag AND its name — a flag alone is
   * not a language, and a closed <select> hides the option people came for. */
  ok(qa('#lang input[type=radio]').length === Object.keys(w.eval('LANGS')).length,
     'the languages are not all on the page as radio buttons');
  ok(qa('#lang label .lname').every((n) => n.textContent.trim().length > 1),
     'a language flag has no name beside it');
  ok(!!d.querySelector('#lang input:checked'), 'no language is selected');
  // switching language redraws the page in it, without touching the game
  const de = d.querySelector('#lang-de');
  de.checked = true; de.dispatchEvent(new w.Event('change', { bubbles: true }));
  ok(w.eval('getLang()') === 'de', 'picking the German flag did not switch language');
  ok(/Partie|Aufbau|Spiel/.test(d.querySelector('#start').textContent + d.querySelector('h2').textContent),
     'the page did not redraw in German');
  d.querySelector('#lang-en').checked = true;
  d.querySelector('#lang-en').dispatchEvent(new w.Event('change', { bubbles: true }));

  /* The disclosure has to LOOK like one: a marker that moves when it opens. */
  ok(!!d.querySelector('#advanced > summary .chev'),
     'Advanced has no visual cue that it expands');

  /* Somewhere to read the actual rules, without leaving the game — and the
   * objectives filed as what they are, a variant you have to switch on. */
  const groups = qa('#setup .docs');
  ok(groups.length === 2, `${groups.length} document groups, expected rules and variants`);
  ok(groups[1] && groups[1].contains(d.querySelector('#doc-objectives')),
     'map objectives is not under the variant-rules heading');
  ok(groups[0] && !groups[0].contains(d.querySelector('#doc-objectives')),
     'map objectives is still filed with the base rules');
  ok(groups[1] && /variant|Variant/i.test(groups[1].querySelector('.sublab').textContent),
     'the second group is not headed as variant rules');
  for (const id of ['#doc-rules', '#doc-effects', '#doc-objectives']) {
    const a = d.querySelector(id);
    ok(!!a && a.getAttribute('href'), `${id} is missing or has no href`);
    ok(a && a.target === '_blank', `${id} would navigate away from the game`);
    ok(a && a.textContent.trim().length > 2, `${id} has no label`);
  }
  ok(d.querySelector('#seat-0').value === 'you', 'seat 0 is not you by default');
  ok(qa('#seats select').slice(1).every((s) => s.value === 'auto'),
     'the other seats do not default to an automatic mix');

  // the seat list follows the player count
  ok(qa('.seatrow').length === 3, 'three players do not make three seat rows');
  const np4 = d.querySelector('#np-4');
  np4.checked = true; np4.dispatchEvent(new w.Event('change', { bubbles: true }));
  ok(qa('.seatrow').length === 4, 'four players do not make four seat rows');
  // a choice already made survives the count changing
  d.querySelector('#seat-1').value = 'raider';
  d.querySelector('#seat-1').dispatchEvent(new w.Event('change', { bubbles: true }));
  const np3 = d.querySelector('#np-3');
  np3.checked = true; np3.dispatchEvent(new w.Event('change', { bubbles: true }));
  ok(d.querySelector('#seat-1').value === 'raider',
     'changing the player count forgot a seat that had been set');

  /* The setup page is a form that grows — with the advanced rules open it is
   * taller than a laptop window. If the body cannot scroll, the Start button
   * is simply unreachable. */
  ok(w.getComputedStyle(d.body).overflow !== 'hidden',
     'the setup page cannot be scrolled — a tall form would cut off Start');

  // the reseed button actually rolls
  const before = d.querySelector('#seed').value;
  d.querySelector('#reseed').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  ok(d.querySelector('#seed').value !== before, 'the reseed button did nothing');

  // per-seat styles reach the engine
  T.start(w, d, { players: 3, seat: 0, styles: { 1: 'raider', 2: 'merchant' } });
  ok(w.eval('G.P[1].style') === 'raider', 'seat 1 did not get the style it was given');
  ok(w.eval('G.P[2].style') === 'merchant', 'seat 2 did not get the style it was given');
  ok(w.eval('G.P[0].style') === 'you', 'seat 0 is not the human seat');
  ok(w.eval('G.P[1].noise') > 0, 'normal difficulty gave the bots no noise');

  /* ---- the two ways out of a game ----
   * Both ask first: a misplaced tap must not throw a game away. */
  let asked = 0;
  w.confirm = () => { asked += 1; return false; };
  const seedNow = w.eval('GARGS.seed');
  d.querySelector('#restart').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  ok(asked === 1, 'Restart did not ask before throwing the game away');
  ok(w.eval('G !== null'), 'Restart wiped the game even though I said no');
  d.querySelector('#abort').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  ok(asked === 2, 'Leave did not ask first');
  ok(w.eval('G !== null'), 'Leave abandoned the game even though I said no');

  w.confirm = () => true;
  w.eval('G.round = 9');
  d.querySelector('#restart').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  ok(w.eval('G.round') < 9, 'Restart did not deal a fresh game');
  ok(w.eval('GARGS.seed') === seedNow, 'Restart changed the seed — that is a new game, not this one');
  ok(w.eval('LOG.length') === 0, 'Restart kept the old game\'s answers');

  d.querySelector('#abort').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  ok(w.eval('G') === null, 'Leave did not end the game');
  ok(!d.querySelector('#setup').classList.contains('hide'), 'Leave did not bring setup back');
  ok(!d.body.classList.contains('playing'), 'Leave left the page in its playing state');
  ok(d.querySelector('#pass').hidden, 'Leave left the hand-over screen up');

  // and setup still works afterwards: start again from a clean page
  T.start(w, d, { players: 3, seat: 0 });
  ok(w.eval('G !== null'), 'could not start a new game after leaving one');

  next();
}, 250);

/* ------------------------------------------------ nobody is playing */
function next() {
  const B = page();
  setTimeout(() => {
    const { w, d } = B;
    T.start(w, d, { players: 3, humans: [] });
    ok(w.eval('HUMANS.length') === 0, 'a table with no humans still has one');
    ok(w.eval('G.humans.size') === 0, 'the engine was told there is a human');
    // it should just play: no request is ever addressed to a person
    setTimeout(() => {
      const rounds = w.eval('G.round');
      ok(rounds > 1, `watching a game got no further than round ${rounds}`);
      ok(w.eval('REQ') === null, 'a watched game stopped to ask somebody something');
      if (B.errs.length) fail.push('watch mode errors: ' + B.errs.slice(0, 2).join(' | '));
      hotSeat();
    }, 900);
  }, 250);
}

/* ------------------------------------------- two people, one device */
function hotSeat() {
  const C = page();
  setTimeout(() => {
    const { w, d } = C;
    T.start(w, d, { players: 3, humans: [0, 1], seed: 4 });
    ok(w.eval('HUMANS.length') === 2, 'two human seats were not carried through');
    ok(w.eval('G.humans.size') === 2, 'the engine has the wrong number of humans');

    const gate = d.querySelector('#pass');
    const askedOf = () => w.eval('REQ ? REQ.seat : null');
    // seat 0 is asked first and is already holding the device
    ok(askedOf() === 0, `the first question went to seat ${askedOf()}`);
    ok(gate.hidden, 'the pass screen is up before the device has to move');
    ok(w.eval('ME') === 0, 'the board is not showing the seat being asked');

    // answer for seat 0, and the device must be handed to seat 1
    const hand = [...d.querySelectorAll('#hand button')];
    hand[0].dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
    const play = [...d.querySelectorAll('#prompt button')]
      .find((b) => !b.disabled && /Play meld|Kombination/.test(b.textContent));
    ok(!!play, 'could not play a meld for the first player');
    if (play) play.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));

    ok(askedOf() === 1, `after seat 0 played, seat ${askedOf()} was asked`);
    ok(!gate.hidden, 'the board was NOT covered when the device changed hands');
    ok(w.eval('ME') === 1, 'the board is not showing the new player');
    ok(d.querySelector('#pass-name').textContent.length > 0,
       'the pass screen does not say whose turn it is');

    // and it clears when the next player says they have it
    d.querySelector('#pass-go').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
    ok(gate.hidden, 'the pass screen did not clear');
    ok(d.querySelectorAll('#hand .cf').length > 0, 'the new player has no hand on screen');
    // and the game itself does not scroll while it is being played
    ok(w.getComputedStyle(d.body).overflow === 'hidden',
       'the board scrolls the whole page while a game is running');

    if (C.errs.length) fail.push('hot seat errors: ' + C.errs.slice(0, 2).join(' | '));
    console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
      : 'setup: every control named and grouped, variants folded away, defaults '
        + 'are normal + auto-mixed, seats follow the count and reach the engine, '
        + 'nobody-playing watches itself, and hot seat covers the board on the pass');
    process.exit(fail.length ? 1 : 0);
  }, 250);
}
