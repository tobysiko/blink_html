const fs = require('fs');
const eng = fs.readFileSync('engine.js', 'utf8')
  .replace(/if \(typeof module[\s\S]*$/, '');       // drop the node export tail
const ui  = fs.readFileSync('ui.js', 'utf8');
const out = fs.readFileSync('shell.html', 'utf8')
  .replace('/*__ENGINE__*/',
    "document.documentElement.className += ' js';   // scripts run: hide the no-JS notice\n"
    + eng)
  .replace('/*__UI__*/', ui);
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
const page = out.replace('<title>Blink — play v0.22</title>', meta);
fs.mkdirSync('../deploy', { recursive: true });

function writeDeploy(text, how) {
  fs.writeFileSync('../deploy/index.html', text);
  console.log(`built ../deploy/index.html ${(text.length/1024).toFixed(1)} KB (${how})`);
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
