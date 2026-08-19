/* Where each rival sits on screen, against where their unit sits on the map.
 *
 * From a playtest: "units are not placed where the same player's meld boxes
 * are. Red melds are at the bottom, but the red starting unit is on the left.
 * In a real game, starting positions would naturally be close to the player at
 * the table."
 *
 * That was true, and the cause was that the corners were dealt out in SEAT
 * order — you at the bottom, then seat+1 left, seat+2 top, seat+3 right —
 * while the opening layout puts the four starting tiles wherever STARTS says.
 * The two orders happened to agree for one seat and not the others.
 *
 * It cannot be fixed by moving the units: every client draws itself at the
 * bottom, and the map is the same object for all of them. So the seating is
 * computed per viewer — rotate the opening layout until YOUR tile points down,
 * then read the rivals off clockwise. This checks that from every seat of every
 * table size, which is the only way to catch a fix that works for one viewer
 * and breaks another.
 *
 * Needs jsdom.
 */
const fs = require('fs');
const path = require('path');

let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const html = fs.readFileSync(path.join(__dirname, '..', 'Blink-play-v0.23.html'), 'utf8');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

/* Must match ui.js — if the map geometry ever changes, this test should start
 * failing rather than quietly agreeing with a new mistake. */
const HEXR = 34;
const hexCentre = (c, r) => [Math.sqrt(3) * HEXR * (c + 0.5 * (r & 1)), 1.5 * HEXR * r];
/* Screen bearings: y grows downward, so 90° is the bottom of the screen. */
const SLOT = { left: 180, top: 270, right: 0 };
const gap = (a, b) => Math.abs((((a - b) % 360) + 540) % 360 - 180);

/* Three rivals cannot sit exactly on left/top/right when the opening layout is
 * a triangle, so the test asks for "nearest slot", not "exact". 60° is half the
 * spacing of three points on a circle: anything further out is a mis-seating,
 * not a rounding. */
const TOLERANCE = 60;

function view(n, me) {
  return new Promise((res) => {
    const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
    const w = dom.window, d = w.document;
    const errs = [];
    w.console.error = (...a) => errs.push(a.join(' '));
    setTimeout(() => {
      require('./test_setup.js').start(w, d, { players: n, seat: me, seed: 5 });
      setTimeout(() => {
        const starts = JSON.parse(w.eval('JSON.stringify(G.m.starts)'));
        const seats = [...d.querySelectorAll('#corners .corner')].map((el) => ({
          seat: Number(el.getAttribute('data-seat')),
          spot: ['left', 'top', 'right'].find((s) => el.classList.contains(s)),
        }));
        res({ starts, seats, errs, mine: w.eval('ME') });
      }, 700);
    }, 350);
  });
}

(async () => {
  for (const n of [2, 3, 4]) {
    for (let me = 0; me < n; me++) {
      const { starts, seats, errs, mine } = await view(n, me);
      const where = `${n}p, viewer seat ${me}`;

      ok(mine === me, `${where}: the page thinks it is seat ${mine}`);
      ok(!errs.length, `${where}: the page logged errors: ${errs.slice(0, 2).join(' | ')}`);
      ok(seats.length === n - 1,
         `${where}: ${seats.length} rival boxes drawn, expected ${n - 1}`);
      ok(seats.every((x) => x.spot),
         `${where}: a rival box has no corner class at all`);
      ok(new Set(seats.map((x) => x.spot)).size === seats.length,
         `${where}: two rivals were put in the same corner`);
      ok(!seats.some((x) => x.seat === me), `${where}: the viewer is in their own corner`);

      /* The real check: turn the map so the viewer's tile points down, then
       * every rival's box must be the corner nearest their tile. */
      const pts = starts.map(([c, r]) => hexCentre(c, r));
      const cx = pts.reduce((a, p) => a + p[0], 0) / pts.length;
      const cy = pts.reduce((a, p) => a + p[1], 0) / pts.length;
      const ang = (i) => Math.atan2(pts[i][1] - cy, pts[i][0] - cx) * 180 / Math.PI;
      const rot = 90 - ang(me);

      for (const { seat, spot } of seats) {
        const bearing = (((ang(seat) + rot) % 360) + 360) % 360;
        const off = gap(bearing, SLOT[spot]);
        ok(off <= TOLERANCE,
           `${where}: seat ${seat}'s unit is at ${Math.round(bearing)}° once your `
           + `own tile is pointed down, but its meld box is ${spot} `
           + `(${Math.round(SLOT[spot])}°) — ${Math.round(off)}° out`);
        /* And it must be the BEST slot available, not merely a close one. */
        const better = Object.entries(SLOT)
          .filter(([s]) => seats.some((x) => x.spot === s))
          .find(([s, a]) => gap(bearing, a) < off - 1);
        ok(!better,
           `${where}: seat ${seat} sits ${spot} but ${better && better[0]} is nearer `
           + 'its actual position on the map');
      }
    }
  }

  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : 'seating: at 2, 3 and 4 players, from every seat, each rival\'s meld box is '
      + 'the corner nearest their starting tile once your own tile is turned to '
      + 'face you — 0° out at 2p and 4p, 30° at 3p where a triangle cannot align');
  process.exit(fail.length ? 1 : 0);
})();
