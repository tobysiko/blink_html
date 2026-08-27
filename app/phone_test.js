/* Can you scroll on a phone?
 *
 * This exists because of a bug that was invisible to every other test and to
 * the desktop browser: during a game the page could not be scrolled at all on
 * a phone. The bottom of the player board, the victory row and the rules links
 * were simply unreachable, and the only way to see them was to pinch-zoom the
 * page and pan the visual viewport.
 *
 * The cause was one of CSS's genuinely nasty traps. The top of shell.html says
 *
 *     body.playing{overflow:hidden}          specificity (0,1,1)
 *
 * and the narrow-screen block said
 *
 *     @media (max-width: 900px){ body{overflow:auto} }      (0,0,1)
 *
 * **A media query adds no specificity.** So the override lost to the rule it
 * was written to override, and lost silently — there is no warning, no
 * console message, and on a desktop browser the media query never applies so
 * nothing looks wrong. Only the phone was broken, and only during a game.
 *
 * Testing this through jsdom's computed style does not work: jsdom does not
 * apply media-query rules. So this reads the stylesheet the build actually
 * ships and resolves the cascade itself, which is the part that was wrong.
 * The rule is simply: at phone width, with a game in progress, SOMETHING must
 * be able to scroll.
 */
const fs = require('fs');
const path = require('path');

/* Takes a path so the check can be pointed at an older or deployed build —
 * which is how it was confirmed to actually catch the bug it describes.
 *
 * With no argument it checks BOTH the readable build and the minified one that
 * is actually deployed. They are different files: the minifier rewrites the
 * stylesheet, and the readable build passing says nothing about the artifact
 * players load. */
const TARGETS = process.argv[2]
  ? [process.argv[2]]
  : [require('./test_setup.js').PLAY_HTML,
     path.join(__dirname, '..', 'deploy', 'index.html')].filter(fs.existsSync);
const fail = [];
let WHERE = '';
const ok = (c, what) => { if (!c) fail.push(`[${WHERE}] ${what}`); };

/* ---- a small cascade, for one element at one viewport width -------------
 *
 * Only what is needed to answer the question: selectors are plain enough here
 * (a tag, a class, an id, or a comma list of those) that a full CSS parser
 * would be more code than the thing it checks. Anything it cannot read, it
 * says so rather than quietly scoring zero. */

function specificity(sel) {
  const s = sel.trim();
  if (/[>+~\[]|::|:not|\s/.test(s.replace(/^\s+|\s+$/g, ''))) return null; // too clever for this
  const ids = (s.match(/#[\w-]+/g) || []).length;
  const classes = (s.match(/\.[\w-]+/g) || []).length + (s.match(/:[\w-]+/g) || []).length;
  const tags = (s.replace(/[#.:][\w-]+/g, '').match(/[\w-]+/g) || []).length;
  return ids * 100 + classes * 10 + tags;
}

/* Does this selector match an element described as {tag, classes, id}? */
function matches(sel, el) {
  const s = sel.trim();
  const tag = (s.replace(/[#.:][\w-]+/g, '').match(/[\w-]+/g) || [])[0];
  if (tag && tag !== el.tag) return false;
  const id = (s.match(/#([\w-]+)/) || [])[1];
  if (id && id !== el.id) return false;
  for (const c of s.match(/\.([\w-]+)/g) || [])
    if (!el.classes.includes(c.slice(1))) return false;
  return true;
}

/* Split the sheet into {media, selector, body} rules, one level of @media.
 *
 * Brace-matched rather than pattern-matched, because the file that actually
 * ships is MINIFIED — one long line with no indentation. An earlier version of
 * this found the end of an @media block by looking for a newline and two
 * spaces, which worked perfectly on the readable build and silently mis-parsed
 * the deployed one, reporting every media rule as unconditional. A test that
 * cannot read the artifact it is meant to protect is worse than no test, so
 * this reads both and is run against both. */
function rules(text) {
  const src = text.replace(/\/\*[\s\S]*?\*\//g, '');
  const out = [];

  /* Walk the block starting at `from` (the index of its `{`), returning the
   * body and the index just past its matching `}`. */
  function block(from) {
    let depth = 0;
    for (let i = from; i < src.length; i++) {
      if (src[i] === '{') depth++;
      else if (src[i] === '}') {
        depth--;
        if (!depth) return { body: src.slice(from + 1, i), end: i + 1 };
      }
    }
    return { body: src.slice(from + 1), end: src.length };
  }

  /* Flat rules inside a chunk of CSS that contains no at-rules. */
  function flat(chunk, media) {
    const re = /([^{}]+)\{([^{}]*)\}/g;
    let m;
    while ((m = re.exec(chunk))) out.push({ media, sel: m[1], body: m[2] });
  }

  /* Emitted strictly in source order. Two rules of equal specificity are
   * decided by which comes later, and `body.playing{overflow:hidden}` at the
   * top of the file versus `body.playing{overflow:auto}` in the media block at
   * the bottom is exactly that comparison — so collecting all the media rules
   * first would invert the very answer this test exists to check. */
  let i = 0;
  while (i < src.length) {
    const at = src.indexOf('@', i);
    if (at < 0) break;
    const open = src.indexOf('{', at);
    if (open < 0) break;
    flat(src.slice(i, at), null);              // the plain rules before it
    const prelude = src.slice(at, open);
    const { body, end } = block(open);
    if (/^@media/i.test(prelude)) flat(body, prelude.replace(/^@media/i, '').trim());
    /* @supports, @keyframes and friends: not what this test is about, and
     * their contents must not be mistaken for top-level rules. */
    i = end;
  }
  flat(src.slice(i), null);
  return out;
}

/* The declaration that actually wins for `prop` on `el` at `width` px. */
function winner(all, el, prop, width) {
  let best = null;
  all.forEach((r, order) => {
    if (r.media) {
      const max = (r.media.match(/max-width:\s*(\d+)px/) || [])[1];
      if (max && width > Number(max)) return;
      if (!max) return;                       // only max-width queries here
    }
    const decl = r.body.match(new RegExp(`(?:^|;)\\s*${prop}\\s*:\\s*([^;]+)`));
    if (!decl) return;
    for (const one of r.sel.split(',')) {
      if (!matches(one, el)) continue;
      const spec = specificity(one);
      if (spec === null) continue;
      if (!best || spec > best.spec || (spec === best.spec && order > best.order))
        best = { spec, order, value: decl[1].trim(), sel: one.trim(), media: r.media };
    }
  });
  return best;
}

const PHONE = 390, DESKTOP = 1400;
const playing = { tag: 'body', classes: ['playing'], id: null };
const setup = { tag: 'body', classes: [], id: null };
let summary = '';

for (const target of TARGETS) {
  WHERE = path.basename(target);
  const html = fs.readFileSync(target, 'utf8');
  const css = (html.match(/<style>([\s\S]*?)<\/style>/) || [, ''])[1];
  ok(css.length > 1000, 'no stylesheet found in the built page');

  const all = rules(css);
  ok(all.length > 50, `only parsed ${all.length} rules out of the stylesheet`);
  summary = check(all) || summary;
}

console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : `phone layout (${TARGETS.map((f) => path.basename(f)).join(' + ')}): ${summary}`);
process.exit(fail.length ? 1 : 0);

function check(all) {

/* ---- 1. the bug itself ------------------------------------------------- */

const phoneBody = winner(all, playing, 'overflow', PHONE);
ok(phoneBody && phoneBody.value !== 'hidden',
   `during a game on a ${PHONE}px screen the body is overflow:${phoneBody && phoneBody.value}`
   + ` (from \`${phoneBody && phoneBody.sel}\`) — the page cannot scroll, and neither`
   + ` can anything inside it`);

/* Belt and braces: whatever the body does, at phone width SOMETHING has to be
 * able to scroll, or the bottom of the board is unreachable. */
const phoneLower = winner(all, { tag: null, classes: ['lower'], id: null }, 'overflow', PHONE);
const bodyScrolls = phoneBody && ['auto', 'scroll', 'visible'].includes(phoneBody.value);
const lowerScrolls = phoneLower && ['auto', 'scroll'].includes(phoneLower.value);
ok(bodyScrolls || lowerScrolls,
   'on a phone, mid-game, neither the page nor the lower panel can scroll — '
   + 'the only way to reach the bottom of the board would be to zoom the page');

/* ---- 2. and the desktop behaviour it must not have cost ---------------- */

const deskBody = winner(all, playing, 'overflow', DESKTOP);
ok(deskBody && deskBody.value === 'hidden',
   `on a desktop the game body is overflow:${deskBody && deskBody.value}, expected hidden`
   + ' — the fixed-height app layout is supposed to pin to the window there');

const deskSetup = winner(all, setup, 'overflow', DESKTOP);
ok(!deskSetup || deskSetup.value !== 'hidden',
   'the setup page cannot scroll on a desktop — with the advanced rules open it '
   + 'is taller than a laptop window and the Start button would be cut off');

/* ---- 3. nothing a player needs is hidden on a phone -------------------- */

/* The narrow layout may drop decoration. It may not drop information the
 * player cannot get anywhere else. `.food` (what a refill costs you) and `.mv`
 * (how many free moves your tier gets) were both display:none below 560px,
 * which is how the feeding cost came to ambush people — on a phone it was not
 * merely unlabelled, it was absent. */
const MUSTSEE = {
  food: 'what a refill costs — the one rule that takes a unit off the map',
  mv: 'how many free moves your tier gets',
  mlim: 'your meld limit',
  cap: 'the highest card rank you may buy',
  uslots: 'your remaining population',
};
for (const [cls, why] of Object.entries(MUSTSEE)) {
  const el = { tag: null, classes: [cls], id: null };
  for (const w of [PHONE, 360, 560]) {
    const d = winner(all, el, 'display', w);
    ok(!d || d.value !== 'none',
       `at ${w}px the board hides \`.${cls}\` — ${why}`);
  }
}

/* ---- 4. the trap that caused it, stated as a rule ---------------------- */

/* Any narrow-screen override of a body rule must carry at least the
 * specificity of the rule it is overriding. This is the check that would have
 * caught the original bug on the day it was written.
 *
 * Judged per RULE, not per selector: `body, body.playing{...}` is correct even
 * though its first half alone would lose, because the half that matters wins.
 * Writing both is the readable way to say "the page scrolls here, whatever
 * state it is in". */
const strongest = (sel, el) => sel.split(',')
  .filter((s) => matches(s, el))
  .reduce((best, s) => Math.max(best, specificity(s) === null ? -1 : specificity(s)), -1);

for (const r of all.filter((x) => x.media && /(?:^|;)\s*overflow\s*:/.test(x.body))) {
  const mine = strongest(r.sel, playing);
  if (mine < 0) continue;                      // does not apply to a game in progress
  const beatenBy = all
    .filter((x) => !x.media && /(?:^|;)\s*overflow\s*:/.test(x.body))
    .map((x) => ({ sel: x.sel, spec: strongest(x.sel, playing) }))
    .find((x) => x.spec > mine);
  ok(!beatenBy, `\`@media{${r.sel.trim()}}\` is outranked by \``
    + `${beatenBy && beatenBy.sel.trim()}\` — a media query adds no specificity, `
    + 'so this override never applies');
}

  return `mid-game the page scrolls at ${PHONE}px `
    + `(body:${phoneBody && phoneBody.value} from \`${phoneBody && phoneBody.sel}\`) `
    + `and stays pinned at ${DESKTOP}px (body:${deskBody && deskBody.value}); `
    + 'setup scrolls everywhere; nothing a player needs is display:none';
}
