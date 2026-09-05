/* Asserts the app is actually VISIBLE after Start, not merely present in the
 * DOM. A DOM-querying test passes on a blank page; this one does not.
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const T = require('./test_setup.js');
const html = fs.readFileSync(require('./test_setup.js').PLAY_HTML, 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
const vis = (sel) => {
  const n = d.querySelector(sel);
  if (!n) return false;
  const s = w.getComputedStyle(n);
  return s.display !== 'none' && s.visibility !== 'hidden';
};
const fail = [];

setTimeout(() => {
  if (!vis('#setup')) fail.push('setup hidden before start');
  if (vis('#game')) fail.push('game visible before start');

  T.start(w, d, { players: 3, seat: 0 });

  if (vis('#setup')) fail.push('setup STILL VISIBLE after start');
  if (!vis('#game')) fail.push('game INVISIBLE after start (blank page)');
  for (const sel of ['.wrap', '#market', '#mapbox', '#map', '#corners', '#turnbar',
                     '.lower', '#prompt', '#hand', '#player', '#log'])
    if (!vis(sel)) fail.push(sel + ' not visible after start');

  if (!d.querySelector('#deck')) fail.push('no deck (A/B/C vs A/B/D) toggle on setup');
  if (!d.querySelector('#advanced')) fail.push('the advanced rules are not folded away');
  if (!d.querySelector('#objectives')) fail.push('no map-objectives toggle on setup');
  if (!d.querySelectorAll('#map polygon').length) fail.push('no hexes drawn');
  if (!d.querySelectorAll('#hand button').length) fail.push('no hand rendered');
  // one overlay per seat, in the map's corners, each carrying that seat's colour
  const corners = [...d.querySelectorAll('#corners .corner')];

  if (!corners.every((c) => c.querySelector('.pin')))
    fail.push('a corner overlay has no seat colour');
  // your own meld belongs on the map edge, never also in a corner
  if (corners.length !== 2) fail.push('corners should hold rivals only (2 of 3 seats)');
  if (d.querySelector('#corners .corner.mine'))
    fail.push('your own seat has a corner overlay as well as the meld strip');
  if (!d.querySelector('#mymeld')) fail.push('no meld strip on the map edge');
  // the meld limit is visible as slots, before a single card is chosen
  const slots = d.querySelectorAll('#mymeld > .cf, #mymeld > .mslot').length;
  if (slots !== 2) fail.push(`meld area shows ${slots} slots, Tribe allows 2`);
  if (d.querySelectorAll('#mymeld .mslot').length !== 2)
    fail.push('empty meld slots are not placeholders');
  // every seat carries its place in the order — yours too
  if (!d.querySelector('#mymeld .pin b')) fail.push('your meld has no seat/order pin');
  // rivals' melds are printed like your own: card faces, and their own limits
  for (const c of corners) {
    if (c.querySelectorAll('.mslot').length !== 2)
      fail.push('a rival meld does not show its meld limit as slots');
    if (!c.querySelector('.pin b')) fail.push('a rival has no order number');
  }
  // the order strip: one chip per seat, in the order of play
  const chips = [...d.querySelectorAll('#turnbar .tchip')];
  if (chips.length !== 3) fail.push(`order strip shows ${chips.length} seats, not 3`);
  if (d.querySelectorAll('#turnbar .tchip.me').length !== 1)
    fail.push('the order strip does not mark which seat is yours');
  if (chips.map((c) => c.querySelector('b').textContent).join('') !== '123')
    fail.push('the order strip is not numbered 1..n');
  if (!d.querySelector('.pboard')) fail.push('no player board');
  /* The heading row shares .tier-row because it shares the column layout, so
     count the tiers themselves — otherwise this passes or fails on whether a
     header happens to exist, which is a different question and is asked below. */
  if (d.querySelectorAll('.pboard .tier-row:not(.head)').length !== 5)
    fail.push('player board is missing its five tier rows');
  if (!d.querySelector('.pboard .tier-row.head'))
    fail.push('the player board has no column headings — every number on it is '
      + 'unlabelled, and a phone cannot reach a tooltip');
  if (d.querySelectorAll('.pboard .tier-row.here').length !== 1)
    fail.push('no current tier marked on the player board');
  if (d.querySelectorAll('.vslots .vslot').length !== 5)
    fail.push('victory row does not show five slots');
  if (!d.querySelector('.vslot.centre'))
    fail.push('the scoring centre slot is not marked');
  // unit slots: one per unit across the five tiers, 20 in total
  if (d.querySelectorAll('.pboard .uslot').length !== 20)
    fail.push('player board does not show 20 unit slots');
  // cards must read as cards: hand and market on the card table, with faces
  if (d.querySelectorAll('#hand .cf.mid').length !== 10)
    fail.push('hand is not showing ten card faces');
  if (!d.querySelector('#hand .cf.mid .band') || !d.querySelector('#hand .cf.mid .fx'))
    fail.push('hand cards are missing the terrain band or effect strip');
  if (d.querySelectorAll('#market .slot').length !== 9)
    fail.push('market is not on the card table');
  /* A CARD MUST LOOK LIKE A CARD, AND A MARKET MUST NOT LOOK LIKE A HAND.
     The face was 66px wide and about 70 tall - a square - and the market was a
     single row of nine, which is the one shape a hand also has. jsdom has no
     layout, so the shape is asserted where it is decided: in the stylesheet. */
  if (!/\.cf\.mid\{[^}]*height:calc\(var\(--cw\) \* 1\.4\)/.test(html))
    fail.push('card faces are not portrait');
  if (!d.querySelector('#marketside') || !d.querySelector('#market .grid'))
    fail.push('the market is not a grid of its own beside the map');
  if (!/#market \.grid\{[^}]*grid-template-columns:repeat\(3,/.test(html))
    fail.push('the market is not laid out three across, as it is on the table');
  /* Holding a card opens it: every face has to say which card it is, and there
     has to be somewhere for it to open into. */
  if (d.querySelectorAll('#hand .cf[data-r]').length !== 10)
    fail.push('hand cards do not carry their identity, so a hold cannot open one');
  if (!d.querySelector('#cardsheet')) fail.push('no card detail sheet in the page');
  /* Initiative is dice on the table; the strip has to be dice on screen. */
  if (d.querySelectorAll('#turnbar .tchip .die').length !== 3)
    fail.push('the order strip is not showing the initiative dice');
  // the face-down upgrade deck is where every research card comes from
  const pile = d.querySelector('#deckpile');
  if (!pile) fail.push('no face-down deck at the head of the market');
  else if (!/^\d+/.test(pile.textContent.trim()))
    fail.push('the deck does not show how many cards are left');
  // the shared discard is a stack in play: cards go in every trick, hands refill from it
  const shared = d.querySelector('#pilebox');
  if (!shared) fail.push('no shared discard pile on the table');
  else if (!/^\d+/.test(shared.textContent.trim()))
    fail.push('the shared pile does not show how many cards it holds');
  if (!d.querySelector('#retire-rule')) fail.push('no retire-rule toggle on setup');

  /* What you do to the GAME — take a move back, deal it again, walk away — is
   * in the title bar, and only once a game is on. */
  if (!vis('#hnav')) fail.push('the game controls are not visible while playing');
  for (const id of ['#undo', '#restart', '#abort']) {
    const b = d.querySelector(id);
    if (!b) { fail.push(`${id} is missing from the title bar`); continue; }
    if (!b.textContent.trim()) fail.push(`${id} has no label`);
    if (!b.title) fail.push(`${id} has no tooltip explaining it`);
  }
  /* And the rules themselves are on the board, not behind Leave. */
  const gd = [...d.querySelectorAll('.gamedocs .doclink')];
  if (gd.length !== 3) fail.push(`${gd.length} rule links on the board, expected 3`);
  if (!gd.every((a) => a.getAttribute('href') && a.target === '_blank'))
    fail.push('a rule link would navigate away from a game in progress');
  if (!vis('.gamedocs')) fail.push('the rule links are not visible while playing');
  /* The printed effect text must be what the engine says, not a UI copy — and
     effect A has two readings, because it depends on how the trick is won:
     "+1 card" when the most cards wins, "+12 total" when the highest total
     rank does. Matching only the first quietly asserted a default rather than
     the rule, and started failing the day the default moved to total-rank
     scoring. Either wording is correct; neither being there is not. */
  const strip = d.querySelector('#hand .cf.mid .fx').textContent;
  if (!/[+]\d+ (card|total)/.test(strip))
    fail.push(`effect strip does not show the A effect: "${strip.slice(0, 60)}"`);

  /* A famine, staged deterministically — it is rare in play, so the scripted
   * games almost never reach it, and it broke unnoticed: the victory row was
   * the lit area but rendered as dead chips, with the real buttons in the
   * prompt. Cards are chosen where the cards are. */
  w.eval(`G.P[ME].vrow.push(G.P[ME].hand[0], G.P[ME].hand[1]);
          REQ = { type: 'feed', seat: ME, owed: 2, options: G.P[ME].vrow.slice() };
          render();`);
  if (!d.querySelector('.vrowbox.needs')) fail.push('a famine does not light the victory row');
  const lit = d.querySelectorAll('.vrowbox button.want').length;
  if (lit !== 2) fail.push(`a famine lights ${lit} row cards, engine offers 2`);
  if (![...d.querySelectorAll('#prompt button')].some((b) => /Take the loss/.test(b.textContent)))
    fail.push('a famine offers no way to refuse');

  /* THE FRONTIER COIN HAS TO SAY SOMETHING. It was landing silently: the purse
   * ticked up by one, the coin animation flew out of the unit reserve (the
   * wrong furniture entirely), and nothing named the rule — so the first
   * report of it was "nothing happens when I explore with a low card". A gold
   * income nobody notices is a gold income nobody plays around. */
  w.eval(`(() => {
    const p = G.P[ME];
    const cell = [...G.m.legalSpaces()][0];
    G.log.length = 0;
    G._payFrontier(p, { r: 3, s: 'plains' }, cell);
    G._payFrontier(p, { r: 20, s: 'plains' }, cell);
    render();
  })()`);
  const logged = d.querySelector('#log').textContent;
  if (!/new ground/i.test(logged))
    fail.push('exploring with a low card says nothing in the log');
  if ((logged.match(/new ground/gi) || []).length !== 1)
    fail.push('a rank-20 card was paid the frontier coin as well');
  const goldFx = w.eval(`(() => {
    G.events.length = 0;
    G._payFrontier(G.P[ME], { r: 4, s: 'plains' }, [...G.m.legalSpaces()][0]);
    const e = G.events.find((x) => x.type === 'gold');
    return e ? String(e.from) : 'none';
  })()`);
  if (!/^-?\d+,-?\d+$/.test(goldFx))
    fail.push(`the frontier coin flies from "${goldFx}" — it should come off the `
      + 'new tile, not out of the furniture');

  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : 'visible after start: map, play area, player board, hand, sidebar — '
      + d.querySelectorAll('#map polygon').length + ' hexes, '
      + d.querySelectorAll('#hand button').length + ' cards in hand, '
      + d.querySelectorAll('#corners .corner').length + ' rivals in the map corners');
  process.exit(fail.length ? 1 : 0);
}, 250);
