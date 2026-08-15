/* Two languages, one interface.
 *
 * The failure modes of a translation are all quiet: a key that exists in one
 * language and not the other, a key the code asks for that nobody wrote, a
 * placeholder that survives in English and is dropped in German (so a number
 * silently vanishes), and text left hard-coded in the source where no
 * translator will ever find it. Each of those is checked here.
 *
 * Needs jsdom for the last part:  npm install jsdom
 */
const fs = require('fs');
const path = require('path');
const I = require('./i18n.js');

const fail = [];
const warn = [];
const ok = (cond, what) => { if (!cond) fail.push(what); };
const src = (f) => fs.readFileSync(path.join(__dirname, f), 'utf8');

const EN = I.STRINGS.en, DE = I.STRINGS.de;
const langs = Object.keys(I.STRINGS);
ok(langs.length >= 2, 'fewer than two languages');

// ---------------------------------------------------- 1. the two agree
for (const k of Object.keys(EN)) if (!(k in DE)) fail.push(`de is missing "${k}"`);
for (const k of Object.keys(DE)) if (!(k in EN)) fail.push(`en is missing "${k}"`);

// placeholders must survive translation, or a number quietly disappears
for (const k of Object.keys(EN)) {
  if (!(k in DE)) continue;
  const vars = (s) => (String(s).match(/\{\w+\}/g) || []).sort().join(",");
  if (vars(EN[k]) !== vars(DE[k]))
    fail.push(`"${k}": placeholders differ — en {${vars(EN[k])}} vs de {${vars(DE[k])}}`);
}
// and so must the markup, or a <b> is left hanging open
for (const k of Object.keys(EN)) {
  if (!(k in DE)) continue;
  const tags = (s) => (String(s).match(/<\/?\w+/g) || []).sort().join(",");
  if (tags(EN[k]) !== tags(DE[k]))
    fail.push(`"${k}": markup differs between languages`);
}

// -------------------------------------------- 2. every key asked for exists
const ui = src('ui.js'), shell = src('shell.html'), engine = src('engine.js');
const asked = new Set();
/* Any string literal shaped like a key, so `t(cond ? "a.b" : "c.d")` counts
 * too. Prefix fragments — "fx.a." built up at run time — are skipped here and
 * covered by RUNTIME below. */
for (const m of ui.matchAll(/"([a-z][\w]*(?:\.[\w]+)+)"/g))
  if (!m[1].endsWith(".")) asked.add(m[1]);
for (const m of shell.matchAll(/data-i18n="([\w.]+)"/g)) asked.add(m[1]);
// the deploy build injects one more tagged element (the back link)
for (const m of src('build.js').matchAll(/data-i18n=\\?"([\w.]+)\\?"/g)) asked.add(m[1]);
for (const m of engine.matchAll(/\bsay\("([\w.]+)"/g)) asked.add(m[1]);
for (const m of engine.matchAll(/"(why\.[\w.]+)"/g)) asked.add(m[1]);
for (const m of engine.matchAll(/"(end\.[\w.]+)"/g)) asked.add(m[1]);
for (const k of asked) if (!(k in EN)) fail.push(`nobody wrote "${k}", but the code asks for it`);

/* Keys built at run time — "fx.a." + band, "seat." + i — cannot be found by
 * scanning, so they are listed by prefix and checked for completeness. */
const RUNTIME = {
  "seat.": 4, "tier.": 5,
  "terrain.": ["plains", "forest", "ocean", "mountain"],
  "hex.": ["settle", "explore", "attack", "moveFrom", "sailFrom", "moveHere",
           "sailHere", "sailFree", "strike", "fortify", "freeTile", "colony"],
  "fx.a.": 4, "fx.aShort.": 4, "fx.b.": 4, "fx.bShort.": 4,
  "fx.c.": 4, "fx.cShort.": 4, "fx.d.": 4, "fx.dShort.": 4,
  "style.": ["tuned", "settler", "raider", "scholar", "merchant"],
  "ask.meld.": ["run", "combo", "friends", "both"],
};
for (const [pre, spec] of Object.entries(RUNTIME)) {
  const keys = typeof spec === "number"
    ? Array.from({ length: spec }, (_, i) => pre + i)
    : spec.map((s) => pre + s);
  for (const k of keys) {
    if (!(k in EN)) fail.push(`runtime key "${k}" is missing from en`);
    asked.add(k);
  }
}
for (let i = 0; i < 12; i++) {
  for (const suffix of ["name", "flavour"]) {
    const k = `obj.${i}.${suffix}`;
    if (!(k in EN)) fail.push(`objective key "${k}" is missing`);
    asked.add(k);
  }
}
for (const k of ["style.tuned.note", "style.settler.note", "style.raider.note",
                 "style.scholar.note", "style.merchant.note"]) asked.add(k);

// ------------------------------------------------- 3. nothing is left over
for (const k of Object.keys(EN))
  if (!asked.has(k)) warn.push(`"${k}" is translated but never used`);

// ------------------------------- 4. no user-facing English left in the code
/* A sentence in a template literal that never went through t(). Looks for two
 * or more words of prose inside markup the player sees. */
const leaks = [];
for (const m of ui.matchAll(/(?:ask|btn|abtn)\(\s*`([^`]{12,})`/g)) {
  const s = m[1];
  if (/\$\{t[n]?\(/.test(s)) continue;              // built from t() pieces
  if (/[a-z]{3,}\s+[a-z]{3,}\s+[a-z]{3,}/.test(s.replace(/\$\{[^}]*\}/g, "")))
    leaks.push(s.replace(/\s+/g, " ").slice(0, 60));
}
for (const s of leaks) fail.push(`hard-coded English in ui.js: "${s}…"`);

// --------------------------------------- 5. the app actually plays in German
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch (e) {
  console.log('(jsdom not installed — skipping the live check)');
  finish();
}
const html = fs.readFileSync(path.join(__dirname, '..', 'Blink-play-v0.22.html'), 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
const errs = [];
w.console.error = (...a) => errs.push(a.join(' '));
w.addEventListener('error', (e) => errs.push(e.message));

setTimeout(() => {
  const play = (lang) => {
    require('./test_setup.js').start(w, d, { players: 3, seat: 0, seed: 5, lang });
    // click a card and open a victory-card panel's worth of interface
    const hand = [...d.querySelectorAll('#hand button')];
    if (hand.length) hand[0].dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
    return [...d.querySelectorAll('#prompt, #player, #market, #turnbar, #mymeld')]
      .map((n) => n.textContent).join(' ') + ' '
      + [...d.querySelectorAll('[title]')].map((n) => n.getAttribute('title')).join(' ');
  };
  const de = play('de');
  ok(/Kombination|Siegreihe|Karmin/.test(de), 'the German build shows no German');
  ok(!/victory row|Play a meld|Give up/.test(de), 'English leaked into the German build');
  const en = play('en');
  ok(/victory row|meld/.test(en), 'the English build shows no English');

  // an untranslated key renders as the key itself: "ask.foo", "board.bar"
  for (const [lang, text] of [['de', de], ['en', en]]) {
    const raw = text.match(/\b(?:ask|board|btn|res|vcard|final|log|setup|hex|fx|obj|why|tip|end|style|seat|tier|terrain)\.[a-zA-Z]\w*/g);
    if (raw) fail.push(`${lang}: untranslated key(s) on screen — ${[...new Set(raw)].slice(0, 3)}`);
  }
  if (errs.length) fail.push('errors: ' + errs.slice(0, 2).join(' | '));
  finish();
}, 250);

function finish() {
  for (const wmsg of warn.slice(0, 8)) console.log('note: ' + wmsg);
  if (warn.length > 8) console.log(`note: …and ${warn.length - 8} more unused`);
  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : `i18n: ${Object.keys(EN).length} strings in ${langs.join(' + ')}, `
      + 'placeholders and markup match, every key the code asks for exists, '
      + 'nothing hard-coded, and the app plays in both');
  process.exit(fail.length ? 1 : 0);
}
