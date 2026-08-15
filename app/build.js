const fs = require('fs');
const cp = require('child_process');

/* Which build is this?
 *
 * A playtest report is worthless if nobody can tell which version produced it.
 * The commit id is baked in here, at build time, along with whether the working
 * tree was dirty — because a build made from uncommitted edits is not the
 * commit it claims to be, and saying so is the whole point. */
function gitStamp() {
  const root = __dirname + '/..';
  const run = (cmd) => cp.execSync(cmd, { cwd: root, stdio: ['ignore', 'pipe', 'ignore'] })
    .toString().trim();
  try {
    /* "Dirty" must mean the SOURCE is uncommitted. The files this script
     * writes are outputs of this very run, so counting them would make every
     * build dirty forever — commit, rebuild, dirty again. */
    const outs = ['Blink-play-v0.22.html', 'deploy', 'rulebook.html',
                  'card-effects.html', 'map-objectives.html']
      .map((f) => `':(exclude)${f}'`).join(' ');
    return { commit: run('git rev-parse --short=10 HEAD'),
             branch: run('git rev-parse --abbrev-ref HEAD'),
             dirty: run(`git status --porcelain -- . ${outs}`) !== '',
             built: new Date().toISOString().slice(0, 19) + 'Z' };
  } catch (e) {
    // no git, or not a checkout: say so rather than inventing a number
    return { commit: 'unknown', branch: 'unknown', dirty: null,
             built: new Date().toISOString().slice(0, 19) + 'Z' };
  }
}
/* Where playtest reports and remote sessions go. Unset in a local build, so
 * the standalone file falls back to downloading the report — it must work with
 * no network at all. Set BLINK_API to point a build at the session service. */
const API = process.env.BLINK_API || null;
const BUILD = Object.assign({ version: 'v0.22', api: API,
                              reportUrl: API ? API.replace(/\/$/, '') + '/report' : null },
                            gitStamp());
console.log(`build ${BUILD.version} ${BUILD.commit}${BUILD.dirty ? '+dirty' : ''} (${BUILD.branch})`);
const strip = (f) => fs.readFileSync(f, 'utf8')
  .replace(/if \(typeof module[\s\S]*$/, '');       // drop the node export tail
const eng = strip('engine.js');
const lang = strip('i18n.js');
const sess = strip('session.js');
const rep = strip('report.js');
const net = fs.readFileSync('net.js', 'utf8');
const ui  = fs.readFileSync('ui.js', 'utf8');
const out = fs.readFileSync('shell.html', 'utf8')
  .replace('/*__ENGINE__*/',
    "document.documentElement.className += ' js';   // scripts run: hide the no-JS notice\n"
    + 'const BUILD = ' + JSON.stringify(BUILD) + ';\n'
    + lang + '\n' + eng + '\n' + sess + '\n' + rep)
  .replace('/*__UI__*/', net + '\n' + ui);
fs.writeFileSync('../Blink-play-v0.22.html', out);
console.log('built ../Blink-play-v0.22.html', (out.length/1024).toFixed(1)+' KB');

/* Also emit ../deploy/index.html — the same page with the tags a SERVED copy
 * wants (description, theme colour, noindex while it is a prototype) and, if
 * terser is installed, minified. Deploy that folder, not the whole project. */
const meta = `<title>Blink — play the prototype (v0.22)</title>
<meta name="description" content="Blink — a civilization card game by Toby Siko. Play the v0.22 prototype against tuned bots in your browser.">
<meta name="robots" content="noindex">
<meta name="theme-color" content="#1E4229">
<meta property="og:title" content="Blink — play the prototype">
<meta property="og:description" content="Climbing the Ladder of Civilization. Trick-taking melds, a growing hex map, and a victory row. Prototype v0.22.">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">`;
let page = out.replace('<title>Blink — play v0.22</title>', meta);
/* Served from the site, there is somewhere to go back to. The standalone file
 * has no such page, so this link only exists in the deploy build. */
page = page.replace('<span class="right">',
  '<a class="back" href="/blink/" data-i18n="app.back">← Blink</a>\n  <span class="right">');
fs.mkdirSync('../deploy', { recursive: true });

/* The same file is the deploy artifact and the page served at
 * deep-diversions.com/blink/play.html. Copy it straight into the site repo when
 * that repo is checked out beside this one, so the two cannot drift. */
const SITE = process.env.BLINK_SITE
  || `${process.env.HOME}/Code/deep-diversions/public/blink`;
function writeDeploy(text, how) {
  fs.writeFileSync('../deploy/index.html', text);
  console.log(`built ../deploy/index.html ${(text.length/1024).toFixed(1)} KB (${how})`);
  if (fs.existsSync(SITE)) {
    fs.writeFileSync(`${SITE}/play.html`, text);
    console.log(`copied to ${SITE}/play.html — commit the site repo too`);
  } else {
    console.log(`site repo not found at ${SITE}; set BLINK_SITE to copy play.html`);
  }
}
/* The three documents the setup page links to, put where those links point:
 * beside the page, both in the project root and in the deploy folder. A link
 * that 404s is worse than no link. */
const DOCS = { 'rulebook.html': '../source/Blink-rules-v0.22.html',
               'card-effects.html': '../source/Blink-card-effects.html',
               'map-objectives.html': '../source/Blink-map-objectives.html' };
for (const [name, src] of Object.entries(DOCS)) {
  if (!fs.existsSync(src)) { console.log(`missing ${src} — ${name} will 404`); continue; }
  const text = fs.readFileSync(src, 'utf8');
  fs.writeFileSync(`../${name}`, text);
  fs.writeFileSync(`../deploy/${name}`, text);
  if (fs.existsSync(SITE)) fs.writeFileSync(`${SITE}/${name}`, text);
}

let terser = null;
try { terser = require('terser'); } catch (e) { /* optional */ }
if (!terser) {
  writeDeploy(page, 'unminified — npm install terser for a smaller build');
} else {
  const a = page.indexOf('<script>') + 8, b = page.indexOf('</script>', a);
  terser.minify(page.slice(a, b), { compress: { passes: 2 }, mangle: true,
                                    format: { comments: false } })
    .then((r) => {
      let head = page.slice(0, a);
      const s0 = head.indexOf('<style>') + 7, s1 = head.indexOf('</style>');
      const sheet = head.slice(s0, s1).replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/\s+/g, ' ').replace(/\s*([{}:;,>])\s*/g, '$1').trim();
      head = head.slice(0, s0) + sheet + head.slice(s1);
      writeDeploy(head + r.code + page.slice(b), 'minified');
    });
}
