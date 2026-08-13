/* Asserts the app is actually VISIBLE after Start, not merely present in the
 * DOM. A DOM-querying test passes on a blank page; this one does not.
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const html = fs.readFileSync(__dirname + '/../Blink-play-v0.22.html', 'utf8');
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

  d.querySelector('#n-players').value = '3';
  d.querySelector('#n-players').dispatchEvent(new w.Event('change'));
  d.querySelector('#my-seat').value = '0';
  d.querySelector('#start').click();

  if (vis('#setup')) fail.push('setup STILL VISIBLE after start');
  if (!vis('#game')) fail.push('game INVISIBLE after start (blank page)');
  for (const sel of ['.wrap', '#mapbox', '#map', '#table', '.lower', '#prompt',
                     '#player', '#hand', 'aside', '#side', '#zoom'])
    if (!vis(sel)) fail.push(sel + ' not visible after start');

  if (!d.querySelector('#deck')) fail.push('no deck (A/B/C vs A/B/D) toggle on setup');
  if (!d.querySelector('#objectives')) fail.push('no map-objectives toggle on setup');
  if (!d.querySelectorAll('#map polygon').length) fail.push('no hexes drawn');
  if (!d.querySelectorAll('#hand button').length) fail.push('no hand rendered');
  if (d.querySelectorAll('#table .seatcard').length !== 3)
    fail.push('play area does not show three seats');
  if (!d.querySelector('.pboard')) fail.push('no player board');
  if (d.querySelectorAll('.pboard .tier-row').length !== 5)
    fail.push('player board is missing its five tier rows');
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
  // the printed effect text must be what the engine says, not a UI copy
  const strip = d.querySelector('#hand .cf.mid .fx').textContent;
  if (!/[+]\d card/.test(strip)) fail.push('effect strip does not show the A effect');

  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : 'visible after start: map, play area, player board, hand, sidebar — '
      + d.querySelectorAll('#map polygon').length + ' hexes, '
      + d.querySelectorAll('#hand button').length + ' cards in hand, '
      + d.querySelectorAll('#table .seatcard').length + ' seats on the table');
  process.exit(fail.length ? 1 : 0);
}, 250);
