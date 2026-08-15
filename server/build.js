/* Glue engine.js, session.js and worker.src.js into one deployable worker.js.
 *
 * The same trick the app build uses, for the same reason: no module system, no
 * bundler, nothing that can differ between what the tests ran and what is
 * deployed. The two library files carry a `module.exports` tail for node,
 * which is stripped here.
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const strip = (f) => fs.readFileSync(f, 'utf8')
  .replace(/if \(typeof module[\s\S]*$/, '')
  .trimEnd();

const engine = strip(path.join(APP, 'engine.js'));
const session = strip(path.join(APP, 'session.js'));
const worker = fs.readFileSync(path.join(__dirname, 'worker.src.js'), 'utf8');

/* store.js and hub.js are node modules for the dev server and plain source for
 * the bundles: the tail and the requires come off the same way the library
 * files' exports do. */
const inline = (f) => fs.readFileSync(path.join(__dirname, f), 'utf8')
  .replace(/^const path = require\('path'\);$/m, '')
  .replace(/^const E = require\(.*$/m, 'const E = { Game };')
  .replace(/^const S = require\(.*$/m, 'const S = SESSION;')
  .replace(/module\.exports = \{[\s\S]*$/, '')
  .trimEnd();

const head = `/* GENERATED — do not edit.
 * Built by server/build.js from app/engine.js, app/session.js and
 * server/worker.src.js. Edit those and rebuild:  node server/build.js
 * Built ${new Date().toISOString().slice(0, 19)}Z
 */\n\n`;

const out = head
  + '/* ---------------- app/engine.js ---------------- */\n' + engine + '\n\n'
  + '/* ---------------- app/session.js --------------- */\n' + session + '\n\n'
  + '/* ---------------- server/worker.src.js --------- */\n' + worker;

fs.writeFileSync(path.join(__dirname, 'worker.js'), out);
console.log(`built server/worker.js  ${(out.length / 1024).toFixed(1)} KB`);

/* ---- and the same service as one Vercel Function ----------------------- */

/* hub.js reaches for session.js by name; inlined, the names are already here.
 * Bound once, explicitly, rather than left to a bundler. */
const SHIM = `const SESSION = { sessionState, sessionHandle, sessionLeave, newSession };\n`;

const vercel = head.replace('server/build.js from', 'server/build.js from')
  + '/* ---------------- app/engine.js ---------------- */\n' + engine + '\n\n'
  + '/* ---------------- app/session.js --------------- */\n' + session + '\n\n'
  + SHIM
  + '/* ---------------- server/store.js -------------- */\n' + inline('store.js') + '\n\n'
  + '/* ---------------- server/hub.js ---------------- */\n' + inline('hub.js') + '\n\n'
  + '/* ---------------- server/vercel.src.js --------- */\n'
  + fs.readFileSync(path.join(__dirname, 'vercel.src.js'), 'utf8');

/* The bundle is CommonJS, and the site it is dropped into is very likely a
 * Vite or Next project with `"type": "module"` — under which a .js file is
 * ESM, `module.exports` assigns to nothing, and Vercel finds no handler. The
 * nearest package.json wins, so one goes beside the function. */
const API_PKG = JSON.stringify({ type: 'commonjs' }) + '\n';

const apiDir = path.join(__dirname, 'api');
fs.mkdirSync(apiDir, { recursive: true });
fs.writeFileSync(path.join(apiDir, 'blink.js'), vercel);
fs.writeFileSync(path.join(apiDir, 'package.json'), API_PKG);
console.log(`built server/api/blink.js  ${(vercel.length / 1024).toFixed(1)} KB`);

/* Refuse to ship a function that exports nothing. This exact failure reached
 * production once, and its only symptom was FUNCTION_INVOCATION_FAILED with no
 * stack — a build is the cheapest place to notice. */
if (!/^module\.exports = server;$/m.test(vercel))
  throw new Error('the built function exports no handler — Vercel would fail '
    + 'to invoke it with no useful error');

/* Drop it straight into the site repo when that is checked out beside this
 * one, the same way the play page is copied — the function has to live in the
 * repo Vercel builds, and two copies of it would be one too many. */
const SITE = process.env.BLINK_SITE
  || `${process.env.HOME}/Code/deep-diversions/public/blink`;
const siteRoot = path.join(SITE, '..', '..');
if (fs.existsSync(siteRoot) && fs.existsSync(path.join(siteRoot, 'package.json'))) {
  const dest = path.join(siteRoot, 'api');
  fs.mkdirSync(dest, { recursive: true });
  fs.writeFileSync(path.join(dest, 'blink.js'), vercel);
  fs.writeFileSync(path.join(dest, 'package.json'), API_PKG);
  console.log(`copied to ${path.join(dest, 'blink.js')} — commit the site repo too`);
} else {
  console.log('site repo not found; copy server/api/blink.js into its api/ folder');
}
