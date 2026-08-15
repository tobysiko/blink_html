/* The map view: how big the board is drawn, and where the window onto it sits.
 *
 * jsdom has no layout engine, so the scale and pan maths are pure functions
 * taking measurements as arguments — which is exactly what makes them
 * checkable here. The rule being defended is that a hex never gets too small
 * to hit: past that point the board is panned, not shrunk.
 *
 * Needs jsdom:  npm install jsdom
 */
const fs = require('fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) { console.error('this test needs jsdom — run: npm install jsdom'); process.exit(2); }

const html = fs.readFileSync(__dirname + '/../Blink-play-v0.22.html', 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
const fail = [];

setTimeout(() => {
  const ev = (s) => w.eval(s);
  const MIN = ev('ZOOM_MIN'), MAX = ev('ZOOM_MAX');
  const R = ev('HEXR');
  // a hex measures sqrt(3)R x 2R units
  const px = (z) => [Math.round(Math.sqrt(3) * R * z), Math.round(2 * R * z)];

  // 1. a hex is always big enough to hit — 37px is about a fingertip
  if (px(MIN)[0] < 36)
    fail.push(`the smallest hex is ${px(MIN)[0]}px wide — too small to touch`);
  if (px(MAX)[0] > 70)
    fail.push(`the largest hex is ${px(MAX)[0]}px wide — bigger than a real tile`);

  // 2. the opening board: six tiles in a laptop panel, WITHOUT filling it
  const open = { cw: 260, ch: 200, W: 820, H: 380 };
  const s0 = ev(`mapScale(${open.cw}, ${open.ch}, ${open.W}, ${open.H}, null)`);
  if (s0 !== MAX) fail.push(`opening board drawn at ${s0}, expected the ${MAX} ceiling`);

  // 3. a phone-sized panel still fits the opening board comfortably
  const phone = ev(`mapScale(260, 200, 380, 320, null)`);
  if (phone < MIN) fail.push(`phone opening board at ${phone}, below the floor`);

  // 4. a late board is too big to fit: hold the floor and pan instead
  const late = { cw: 700, ch: 620, W: 726, H: 200 };
  const s1 = ev(`mapScale(${late.cw}, ${late.ch}, ${late.W}, ${late.H}, null)`);
  if (s1 !== MIN) fail.push(`late board drawn at ${s1}, expected the ${MIN} floor`);
  const v1 = ev(`viewBoxOf({cw:${late.cw},ch:${late.ch},cx:0,cy:0,W:${late.W},H:${late.H}},
                            null, {x:0,y:0})`);
  if (!v1.pans) fail.push('a board taller than its panel does not report as pannable');

  // 5. and one that fits must NOT claim the gesture
  const v2 = ev(`viewBoxOf({cw:260,ch:200,cx:0,cy:0,W:820,H:380}, null, {x:0,y:0})`);
  if (v2.pans) fail.push('a board that fits still claims the drag gesture');

  // 6. panning cannot throw the board away: clamped to one hex of overscroll
  const far = ev(`clampPan({x:9999,y:-9999}, ${late.cw}, ${late.ch}, ${v1.vw}, ${v1.vh})`);
  const lim = (content, view) => Math.max(0, (content - view) / 2 + R * 0.6);
  const limX = lim(late.cw, v1.vw), limY = lim(late.ch, v1.vh);
  if (Math.abs(far.x - limX) > 0.51 || Math.abs(far.y + limY) > 0.51)
    fail.push(`pan clamp let the board go to ${JSON.stringify(far)}`);
  // an axis that already fits does not pan at all
  const none = ev(`clampPan({x:500,y:500}, 260, 200, 820, 380)`);
  if (none.x || none.y) fail.push('an axis with room to spare still panned');

  // 7. the manual zoom is honoured, within its own limits
  const manual = ev(`mapScale(260, 200, 820, 380, 1.6)`);
  if (manual !== 1.6) fail.push(`manual zoom 1.6 became ${manual}`);
  const overshoot = ev(`mapScale(260, 200, 820, 380, 99)`);
  if (overshoot !== ev('ZOOM_CEIL')) fail.push('manual zoom is not capped');

  // 8. in the running app: a fresh game is auto-fitted, and +/- takes over
  require('./test_setup.js').start(w, d, { players: 3, seat: 0 });
  if (ev('ZOOM') !== null) fail.push('a new game does not start on the automatic scale');
  if (ev('PAN.x') || ev('PAN.y')) fail.push('a new game does not start centred');
  d.querySelector('#zin').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const z = ev('ZOOM');
  if (z === null) fail.push('the zoom button did not take over from auto');
  if (z < MIN) fail.push(`zooming IN went to ${z}, below the automatic floor`);
  d.querySelector('#zfit').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  if (ev('ZOOM') !== null || ev('PAN.x') !== 0)
    fail.push('the fit button did not hand a fitting board back to the game');

  /* 9. on a board too big to fit, the same button is an overview: it goes
   * BELOW the usable floor to show everything, then back again. */
  ev(`MAPGEO = {cw:900, ch:800, cx:0, cy:0, W:700, H:220}`);
  ev('zoomFit()');
  const over = ev('ZOOM');
  const wholeFit = 220 / 800;
  if (Math.abs(over - wholeFit) > 0.01)
    fail.push(`overview zoom is ${over}, expected the whole board at ${wholeFit.toFixed(3)}`);
  if (!ev(`viewBoxOf(MAPGEO, ZOOM, {x:0,y:0}).pans === false`))
    fail.push('the overview still reports the board as needing a pan');
  ev(`MAPGEO = {cw:900, ch:800, cx:0, cy:0, W:700, H:220}`);
  ev('zoomFit()');
  if (ev('ZOOM') !== null) fail.push('pressing fit twice did not return to playing size');
  // the viewBox is real, and nothing threw
  const vb = d.querySelector('#map').getAttribute('viewBox');
  if (!vb || !/^-?[\d.]+ -?[\d.]+ [\d.]+ [\d.]+$/.test(vb))
    fail.push('the map has no usable viewBox: ' + vb);

  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : `map view: hexes stay between ${px(MIN).join('x')} and ${px(MAX).join('x')} px, `
      + 'a board that fits is fitted, one that does not is panned, '
      + 'pan is clamped, +/- and fit behave');
  process.exit(fail.length ? 1 : 0);
}, 250);
