/* THE APP AND THE RULEBOOK HAVE TO BE THE SAME GAME.
 *
 * A person downloads the v0.25 rulebook from the website and opens the v0.25
 * play page beside it. If a default on the setup page is not the printed rule,
 * those two disagree and nothing anywhere says so — the page still says v0.25,
 * the game still starts, and the table plays something the book does not
 * describe. That is this project's failure mode with a version number on it.
 *
 * The chain this asserts:
 *   the ENGINE's defaults are the printed rules  (check_rules.py checks the
 *     numbers against the rulebook it builds)
 *   the SETUP PAGE's defaults are the engine's defaults  (here)
 * so the page's defaults are the printed rules.
 *
 * Every <select> on the page is read for whichever <option selected> it
 * carries, those values are fed in exactly as starting a game feeds them, and
 * the resulting Game is compared field by field against one built with no
 * options at all. Any difference is a default that has drifted.
 */
const fs = require('fs');
const path = require('path');
const E = require('./engine.js');
const S = require('./session.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

const shell = fs.readFileSync(path.join(__dirname, 'shell.html'), 'utf8');
const VERSION = fs.readFileSync(path.join(__dirname, '..', 'VERSION'), 'utf8').trim();

/* ---- what the page opens with ---- */
const chosen = {};
for (const m of shell.matchAll(/<select id="([a-z0-9-]+)">([\s\S]*?)<\/select>/g)) {
  const [, id, body] = m;
  const sel = [...body.matchAll(/<option value="([^"]*)"([^>]*)>/g)]
    .filter((o) => /\sselected/.test(o[2]));
  ok(sel.length <= 1, `#${id} has ${sel.length} options marked selected`);
  /* No `selected` means the browser takes the first one. */
  const first = body.match(/<option value="([^"]*)"/);
  chosen[id] = sel.length ? sel[0][1] : (first ? first[1] : null);
}
ok(Object.keys(chosen).length > 15,
   `only ${Object.keys(chosen).length} setup selects found — did the page change shape?`);

/* ---- fed in the way the app feeds them ---- */
const n = (v) => Number(v);
const opts = {
  trickRule: chosen['trick-rule'],
  deck: chosen.deck,
  objectives: chosen.objectives,
  objectiveScoring: chosen.objscoring,
  handSetup: chosen.handsetup,
  retireRule: chosen['retire-rule'],
  consolation: chosen.consolation,
  researchRule: chosen['research-rule'],
  comboMelds: chosen['meld-rules'] === 'combo' || chosen['meld-rules'] === 'both',
  friendsOf10: chosen['meld-rules'] === 'friends' || chosen['meld-rules'] === 'both',
  growLimits: chosen['grow-limits'] === 'grow',
  perks: chosen.perks === 'on',
  fortify: chosen.fortify,
  loss: chosen.loss,
  startLayout: chosen.startlayout,
  attacksPerTurn: chosen.attacks === 'one' ? 1 : 0,
  food: chosen.economy !== 'lean',
  ascension: chosen.economy !== 'lean',
  spoils: chosen.spoils,
  asideTiming: chosen.aside,
  frontier: chosen.frontier,
  tileSupply: n(chosen.supply),
  meldScore: chosen['meld-score'],
  aSumLadder: chosen['a-ladder'],
  layout: chosen.layout,
};

const RULE_FIELDS = (g) => Object.keys(g)
  .filter((k) => ['string', 'number', 'boolean'].includes(typeof g[k]))
  /* Not rules. `leader`, `n` and `round` are state; BOT_STYLE and BOT_LEVEL are
     how the computer opponents play, which the rulebook says nothing about and
     a table of people never sees. Everything else in this list IS a rule and
     has to match the book. */
  .filter((k) => !['leader', 'n', 'round', 'BOT_STYLE', 'BOT_LEVEL'].includes(k));

const asPage = new E.Game(3, 99, Object.assign({ humans: [] }, opts));
const asPrinted = new E.Game(3, 99, { humans: [] });

for (const k of RULE_FIELDS(asPrinted))
  ok(asPage[k] === asPrinted[k],
     `the setup page opens with ${k} = ${JSON.stringify(asPage[k])}, `
     + `the printed rule is ${JSON.stringify(asPrinted[k])}`);

/* The board itself, which `layout` sets and which is a printed component. */
ok(String(asPage.BANDS.map((b) => b[1])) === String(asPrinted.BANDS.map((b) => b[1])),
   `the setup page opens with a ${asPage.BANDS.map((b) => b[1])} board, `
   + `the printed one is ${asPrinted.BANDS.map((b) => b[1])}`);

/* ---- and a NETWORK game opens on the same rules as a local one ---- */
{
  const net = S.gameArgs(S.newSession(Object.assign({ n: 3, seed: 99 }, opts))).opts;
  const asNet = new E.Game(3, 99, Object.assign({ humans: [] }, net));
  for (const k of RULE_FIELDS(asPrinted))
    ok(asNet[k] === asPrinted[k],
       `an online table opens with ${k} = ${JSON.stringify(asNet[k])}, `
       + `the printed rule is ${JSON.stringify(asPrinted[k])}`);
}

/* ---- the app says which version it is, and it is this one ---- */
{
  const play = path.join(__dirname, '..', `Blink-play-v${VERSION}.html`);
  ok(fs.existsSync(play), `the built play page for v${VERSION} is missing`);
  if (fs.existsSync(play)) {
    const txt = fs.readFileSync(play, 'utf8');
    ok(txt.includes(`v${VERSION}`), `the play page never names v${VERSION}`);
    /* The rulebook it links to has to be the same version - a page offering
       last version's book beside this version's rules is the whole problem. */
    ok(/rulebook\.html/.test(txt), 'the play page does not link the rulebook');
  }
  const rules = path.join(__dirname, '..', 'source', `Blink-rules-v${VERSION}.html`);
  ok(fs.existsSync(rules), `the v${VERSION} rulebook source is missing`);
}

if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
console.log(`defaults: the setup page, an online table and the printed rules are the same game `
  + `— ${RULE_FIELDS(asPrinted).length} rule fields agree, at v${VERSION}`);
