/* One place that knows how the setup page is driven.
 *
 * Every DOM test starts a game, and they all did it by poking `#n-players` and
 * `#my-seat` directly — so a change to the setup page broke eight files at
 * once. They now ask for a game by description and this translates.
 */
/* Where the built page is. Every DOM test read `../Blink-play-v0.23.html`
 * straight out of a string literal, so bumping the version silently broke
 * twenty files at once — the same failure this module was written to prevent
 * for the setup page. The name is derived from the VERSION file, which is the
 * one place the number lives. */
const PLAY_HTML = require("path").join(
  __dirname, "..",
  "Blink-play-v" + require("fs")
    .readFileSync(require("path").join(__dirname, "..", "VERSION"), "utf8").trim()
  + ".html");

/* THE BUILT PAGE IS A GENERATED FILE, AND A STALE ONE IS A DECOY.
 *
 * Every DOM test runs the engine that is baked into that page, not the one in
 * app/engine.js. So a rule change plus a forgotten `node app/build.js` means
 * the tests play LAST WEEK'S RULES against this week's expectations — and the
 * way that surfaces is not "stale page", it is a replay that mysteriously
 * deals a different game and a multiplayer click that mysteriously answers
 * nothing. Both of those were chased a long way on 19 Sep before the page's
 * timestamp was looked at.
 *
 * The check is a timestamp, not a hash, because it has to be cheap enough to
 * run in every DOM test: if any source the page is built FROM is newer than
 * the page, the page cannot be this version of the game. */
(function checkFresh() {
  const fs = require("fs"), path = require("path");
  if (process.env.BLINK_ALLOW_STALE_PAGE) return;
  if (!fs.existsSync(PLAY_HTML)) {
    console.error(`${path.basename(PLAY_HTML)} has not been built — run: node app/build.js`);
    process.exit(2);
  }
  const built = fs.statSync(PLAY_HTML).mtimeMs;
  const sources = ["engine.js", "ui.js", "i18n.js", "net.js", "session.js",
                   "report.js", "meldrules.js", "shell.html"]
    .map((f) => path.join(__dirname, f))
    .filter((f) => fs.existsSync(f));
  const newer = sources.filter((f) => fs.statSync(f).mtimeMs > built);
  if (newer.length) {
    console.error(`${path.basename(PLAY_HTML)} is OLDER than `
      + newer.map((f) => "app/" + path.basename(f)).join(", ")
      + `\n  The page carries its own copy of the engine, so this test would `
      + `play the rules as they were when it was built.`
      + `\n  Rebuild it:  node app/build.js`);
    process.exit(2);
  }
})();

function configure(w, d, opts) {
  opts = opts || {};
  const players = opts.players || 3;
  const pick = (sel, value) => {
    const n = d.querySelector(sel);
    if (!n) return false;
    n.checked = true;
    n.dispatchEvent(new w.Event("change", { bubbles: true }));
    return true;
  };
  if (opts.lang) pick(`#lang-${opts.lang}`);
  pick(`#np-${players}`);

  /* Seats: `seat` names the one human (the common case); `humans` names
   * several; `styles` sets a named bot on a seat. */
  const humans = opts.humans || [opts.seat === undefined ? 0 : opts.seat];
  for (let i = 0; i < players; i++) {
    const sel = d.querySelector(`#seat-${i}`);
    if (!sel) continue;
    sel.value = humans.includes(i) ? "you"
      : (opts.styles && opts.styles[i]) ? opts.styles[i] : "auto";
    sel.dispatchEvent(new w.Event("change", { bubbles: true }));
  }
  if (opts.level) pick(`#lv-${opts.level}`);
  if (opts.seed !== undefined) d.querySelector("#seed").value = String(opts.seed);
  /* THE DRAFT IS NOW A QUESTION, and the printed default. Every DOM test here
   * was written before that: they start a game and expect the first thing the
   * app asks for to be a meld. Give them the dealt hand unless the test says
   * otherwise, so each one goes on testing the thing it was written for, and
   * let a test that means to exercise the draft ask for it by name
   * (`advanced: { handsetup: 'draft' }`, as ui_playthrough_test does). */
  const advanced = Object.assign({ handsetup: "deal" }, opts.advanced || {});
  for (const [id, value] of Object.entries(advanced)) {
    const sel = d.querySelector(`#${id}`);
    if (sel) sel.value = value;
  }
  return { players, humans };
}

/* Configure and press Start. */
function start(w, d, opts) {
  const cfg = configure(w, d, opts);
  d.querySelector("#start").click();
  return cfg;
}

module.exports = { configure, start, PLAY_HTML };
