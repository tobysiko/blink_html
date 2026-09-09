/* EVERY RULE ON THE SETUP PAGE HAS TO REACH A NETWORK GAME.
 *
 * A local game is started from one object literal and a network game from
 * netRules(). They are written by hand, in two places, and nothing compared
 * them - so `startLayout` and `objectiveScoring` were both added to the local
 * one only. The host would pick "Homelands", the online table would lay the
 * printed block, and nothing anywhere would say so: the option is present, the
 * game starts, and it plays by a different rule than the one on screen.
 *
 * So: every <select> on the setup page is a rule unless it is named below as
 * something else.
 */
const fs = require('fs');
const path = require('path');
const here = (f) => path.join(__dirname, f);
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

const shell = fs.readFileSync(here('shell.html'), 'utf8');
const ui = fs.readFileSync(here('ui.js'), 'utf8');

/* Not rules, or read through a helper that IS in netRules. */
const EXEMPT = {
  coach: 'a display preference, not a rule',
  economy: 'read through leanEconomy() into food and ascension',
  layout: 'read through chosenLayout()',
};

const ids = [...shell.matchAll(/<select id="([a-z0-9-]+)"/g)].map((m) => m[1]);
ok(ids.length > 15, `only found ${ids.length} setup selects — did the page change shape?`);

const start = ui.indexOf('function netRules()');
ok(start > 0, 'netRules() is gone');
const body = ui.slice(start, ui.indexOf('\n}', start));
ok(body.includes('seed'), 'the netRules body did not parse out properly');

for (const id of ids) {
  if (EXEMPT[id]) continue;
  ok(body.includes(`#${id}"`),
     `#${id} is on the setup page but never reaches a network game — add it to netRules()`);
}

/* And the exemptions have to stay true: their helpers must still be there. */
ok(body.includes('leanEconomy()'), 'leanEconomy() left netRules — #economy is now unwired');
ok(body.includes('chosenLayout()'), 'chosenLayout() left netRules — #layout is now unwired');

/* The local game must carry them too. One object literal, so a missing key
 * here is the same silent divergence in the other direction. */
for (const id of ids) {
  if (EXEMPT[id]) continue;
  ok(ui.includes(`$("#${id}")`) || ui.includes(`$("#${id}").value`),
     `#${id} is on the setup page and read nowhere at all`);
}

if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
console.log(`setup options: all ${ids.length - Object.keys(EXEMPT).length} rule selects reach both `
  + `a local and a network game (${Object.keys(EXEMPT).join(', ')} exempt, and their helpers checked)`);
