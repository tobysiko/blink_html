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
