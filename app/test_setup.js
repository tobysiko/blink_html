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
  for (const [id, value] of Object.entries(opts.advanced || {})) {
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
