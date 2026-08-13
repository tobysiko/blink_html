/* Blink v0.22 — playable client.
 *
 * The engine yields a request whenever a human seat must decide; this file
 * renders that request and feeds the answer back. Nothing here knows the
 * rules: every legal option on screen came out of the engine.
 *
 * The map phase is a single persistent `turn` request. The engine hands back
 * everything still legal after each action, so the player takes them in any
 * order and presses End turn when done.
 */

const TC = { plains: "#C9992B", forest: "#37704A", ocean: "#256A8C", mountain: "#8A837A" };
const TL = { plains: "Plains", forest: "Forest", ocean: "Ocean", mountain: "Mountain" };
/* Brightened from the components' crimson/azure/violet/olive: a unit has to
 * read against its own terrain, and Azure-on-ocean and Olive-on-forest were
 * invisible at the printed values. */
const SEAT_C = ["#D6453A", "#3E9BD1", "#9370CE", "#86BE45"];
const SEAT_N = ["Crimson", "Azure", "Violet", "Olive"];
const ACT_LABEL = { settle: "Settle", explore: "Explore", attack: "Attack" };

let G = null, IT = null, REQ = null;
let ME = 0;
let ZOOM = 0.5;                       // px per engine unit; a hex is 30 units
/* The research action is four steps deep, so the client tracks where it is and
 * what has happened so far. Kept outside SEL because answer() clears SEL. */
let RESEARCH = null;
let SEL = blankSel();
function blankSel() {
  return { meld: [], card: null, mode: null, moveSrc: null, vcard: null, waterCell: null };
}

const $ = (s) => document.querySelector(s);
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
};
const cardSortUI = (a, b) => a.r - b.r || a.s.localeCompare(b.s);

// --------------------------------------------------------------- setup
function startGame() {
  const n = Number($("#n-players").value);
  const seat = Math.min(Number($("#my-seat").value), n - 1);
  const seed = Number($("#seed").value) || Math.floor(Math.random() * 1e6);
  $("#seed").value = seed;
  ME = seat;
  const trickRule = $("#trick-rule").value;
  const deck = $("#deck").value;
  const objectives = $("#objectives").value;
  G = new Game(n, seed, { humans: [seat], trickRule, deck, objectives });
  IT = null; REQ = null; SEL = blankSel();
  // toggle a class, never `style.display = ""` — that would just fall back to
  // the stylesheet, where #game is display:none
  $("#setup").classList.add("hide");
  $("#game").classList.add("show");
  nextRound();
}

// --------------------------------------------------------------- driver
function nextRound() {
  RESEARCH = null;
  if (G.finished()) { REQ = null; render(); return; }
  IT = G.playRound();
  pump(undefined);
}

function pump(a) {
  let r;
  try { r = IT.next(a); }
  catch (e) { console.error(e); G.say("Engine error: " + e.message); render(); return; }
  if (!r.done) { REQ = r.value; render(); return; }
  IT = null; REQ = null;
  render();
  if (!G.finished()) setTimeout(nextRound, 220);
}

function answer(a, keepSel) {
  if (!keepSel) SEL = blankSel();
  pump(a);
}

// --------------------------------------------------------------- geometry
const HEXR = 30;
function hexCentre(c, r) {
  const w = Math.sqrt(3) * HEXR;
  return [w * (c + 0.5 * (r & 1)), 1.5 * HEXR * r];
}
/* Text over terrain needs a halo. paint-order isn't reliable everywhere, so
 * the string is drawn twice: once as a fat stroke, once as the fill. */
function haloText(x, y, cls, txt) {
  return `<text class="${cls} halo" x="${x}" y="${y}">${txt}</text>` +
         `<text class="${cls}" x="${x}" y="${y}">${txt}</text>`;
}
function hexPoints(cx, cy, rad) {
  const pts = [];
  for (let k = 0; k < 6; k++) {
    const a = (Math.PI / 180) * (60 * k - 90);
    pts.push((cx + rad * Math.cos(a)).toFixed(1) + "," + (cy + rad * Math.sin(a)).toFixed(1));
  }
  return pts.join(" ");
}

// --------------------------------------------------------------- render
function render() {
  if (!G) return;
  renderMap();
  renderTable();
  renderPlayer();
  renderMarket();
  renderSide();
  renderPrompt();
}

const mine = () => REQ && REQ.seat === ME;

/* Which cells the player may click right now, and what clicking means. */
function activeCells() {
  const out = new Map();
  if (!mine()) return out;
  if (REQ.type === "turn") {
    if (SEL.mode === "move") {
      if (!SEL.moveSrc) for (const k of REQ.opts.moveSources) out.set(k, { act: "source" });
      else for (const k of G.moveDests(G.P[ME], SEL.moveSrc)) out.set(k, { act: "dest" });
    } else if (SEL.mode === "fortify") {
      for (const k of REQ.opts.fortifyCells) out.set(k, { act: "fortify" });
    } else if (SEL.card) {
      const e = REQ.opts.cards.find((m) => m.card === SEL.card);
      if (e) for (const [k, act] of e.options) out.set(k, { act });
    }
  }
  if (REQ.type === "waterexplore" && !SEL.waterCell)
    for (const k of REQ.options) out.set(k, { act: "explore" });
  if (REQ.type === "conquest")
    for (const k of REQ.options) out.set(k, { act: "strike" });
  return out;
}

function renderMap() {
  const svg = $("#map");
  const act = activeCells();
  const pts = [], draw = [], ghosts = [];
  const spaces = G.m.legalSpaces();

  for (const t of G.m.tiles.values()) {
    const [cx, cy] = hexCentre(t.cell[0], t.cell[1]);
    pts.push([cx, cy]); draw.push({ t, cx, cy, key: t.key });
  }
  // empty but legal spaces are drawn as ghosts so the map's growth is legible
  for (const k of spaces) {
    const [c, r] = unK(k);
    const [cx, cy] = hexCentre(c, r);
    pts.push([cx, cy]); ghosts.push({ key: k, cx, cy });
  }

  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const pad = HEXR * 1.3;
  const minx = Math.min(...xs) - pad, maxx = Math.max(...xs) + pad;
  const miny = Math.min(...ys) - pad, maxy = Math.max(...ys) + pad;
  const cw = maxx - minx, ch = maxy - miny;
  /* Fit the board, but never blow it up past ZOOM — six starting tiles used to
   * fill the whole panel with enormous hexes. */
  const box = svg.getBoundingClientRect();
  const W = box.width || 820, H = box.height || 380;
  const scale = Math.min(W / cw, H / ch, ZOOM);
  const vw = W / scale, vh = H / scale;
  svg.setAttribute("viewBox",
    `${(minx + maxx) / 2 - vw / 2} ${(miny + maxy) / 2 - vh / 2} ${vw} ${vh}`);

  let s = "";
  for (const gh of ghosts) {
    const a = act.get(gh.key);
    s += `<polygon class="ghost${a ? " hot" : ""}" data-key="${gh.key}"
      points="${hexPoints(gh.cx, gh.cy, HEXR - 1)}"/>`;
    if (a) s += haloText(gh.cx, gh.cy + 4, "badge", ACT_LABEL[a.act] || "");
  }
  for (const d of draw) {
    const t = d.t;
    const a = act.get(d.key);
    const isSrc = SEL.moveSrc === d.key;
    s += `<polygon class="tile${a ? " hot" : ""}${isSrc ? " src" : ""}" data-key="${d.key}"
      points="${hexPoints(d.cx, d.cy, HEXR - 1)}" fill="${TC[t.terrain]}"/>`;
    const n = t.units.length;
    for (let i = 0; i < n; i++) {
      const off = (i - (n - 1) / 2) * 13;
      s += `<circle class="pip" cx="${d.cx + off}" cy="${d.cy + 3}" r="6"
             fill="${SEAT_C[t.units[i]]}"/>`;
    }
    if (t.gold) s += `<circle class="coin" cx="${d.cx + 15}" cy="${d.cy - 14}" r="5"/>`;
    const cap = t.capacityFor(t.owner === null ? ME : t.owner);
    s += haloText(d.cx, d.cy - 12, "cap", `${n}/${cap}`);
    if (a) s += haloText(d.cx, d.cy + 19, "badge",
      ACT_LABEL[a.act] || (a.act === "source" ? "Move from"
                         : a.act === "dest" ? "Move here"
                         : a.act === "strike" ? "Strike" : "Fortify"));
  }
  svg.innerHTML = s;
  svg.querySelectorAll("[data-key]").forEach((node) =>
    node.addEventListener("click", () => onCell(node.dataset.key)));
}

function onCell(k) {
  const a = activeCells().get(k);
  if (!a) return;
  if (REQ.type === "waterexplore") { SEL.waterCell = k; render(); return; }
  if (REQ.type === "conquest") { answer(k); return; }
  if (REQ.type !== "turn") return;
  if (SEL.mode === "fortify") { answer({ kind: "fortify", cell: k }); return; }
  if (SEL.mode === "move") {
    if (a.act === "source") { SEL.moveSrc = k; render(); }
    else answer({ kind: "move", src: SEL.moveSrc, dest: k });
    return;
  }
  if (SEL.card) answer({ kind: "spend", card: SEL.card, cell: k, act: a.act });
}

function zoom(d) { ZOOM = Math.max(0.25, Math.min(1.1, ZOOM + d)); renderMap(); }

// --------------------------------------------------------------- cards
/* One card face at three sizes. "mini" is the old chip — rank and suit, for
 * places where the card is only an identity (the market, a rival's meld).
 * "mid" adds the terrain band and the one-line effect strip, so you can judge
 * what a card would be worth once retired. "full" prints all three effects,
 * exactly as the physical card does. */
function deckIsD() { return G && G.DECK === "abd"; }
function thirdEffect(c) {
  return deckIsD()
    ? { key: "D", long: effectDText(c.r).d, short: effectDText(c.r).dShort }
    : { key: "C", long: effectText(c.r).c, short: effectText(c.r).cShort };
}

function faceInner(c, size) {
  const e = effectText(c.r);
  const third = thirdEffect(c);
  if (size === "mini")
    return `<b>${c.r}</b><i>${SUIT_LETTER[c.s]}</i>`;
  if (size === "mid")
    return `<span class="band">${TL[c.s]}</span>
      <span class="rank">${c.r}</span>
      <span class="fx">${e.aShort} · ${third.short}</span>`;
  return `<span class="band">${TL[c.s]}</span>
    <span class="rank">${c.r}<em>${SUIT_LETTER[c.s]}</em></span>
    <ul class="fx3">
      <li><span class="ab">A</span>${e.a}</li>
      <li><span class="ab">B</span>${e.b}</li>
      <li><span class="ab">${third.key}</span>${third.long}</li>
    </ul>`;
}
function cardChip(c, cls, attr, size) {
  size = size || "mini";
  return `<span class="cf ${size} ${cls || ""}" ${attr || ""}
    style="--suit:${TC[c.s]}">${faceInner(c, size)}</span>`;
}
function cardBtn(c, cls, attr, size) {
  size = size || "mini";
  return `<button class="cf btn ${size} ${cls || ""}" ${attr || ""}
    style="--suit:${TC[c.s]}">${faceInner(c, size)}</button>`;
}

// --------------------------------------------------------------- play area
/* What everyone put on the table this trick. Public information: melds are
 * played face up, so this is the shared board state, not a hint. */
function renderTable() {
  const box = $("#table");
  let s = `<div class="tlab">This round</div><div class="seats">`;
  for (let i = 0; i < G.n; i++) {
    const q = G.P[i];
    const won = G.winner === i;
    const done = G.turnDone && G.turnDone.has(i);
    const acting = G.acting === i;
    s += `<div class="seatcard${won ? " won" : ""}${done ? " done" : ""}${
      acting ? " acting" : ""}">
      <div class="sn"><span class="dot" style="background:${SEAT_C[i]}"></span>
        ${SEAT_N[i]}${i === ME ? " (you)" : ""}
        ${won ? `<span class="tag">won</span>` : ""}
        ${acting ? `<span class="tag act">acting</span>`
          : done ? `<span class="tag muted">done</span>` : ""}</div>
      <div class="meld">`;
    if (q.tableau && q.tableau.length) {
      s += q.tableau.slice().sort(cardSortUI).map((c) => cardChip(c)).join("");
      if (q.tableauBonus)
        s += cardChip(q.tableauBonus, "bonus", 'title="winner&#39;s extra card"');
      const tot = q.tableau.reduce((a, c) => a + c.r, 0);
      s += `<span class="tot">${q.tableau.length} card${
        q.tableau.length > 1 ? "s" : ""} · ${tot}${
        q.tableauBonus ? " +bonus" : ""}</span>`;
    } else {
      s += `<span class="muted">— not played —</span>`;
    }
    s += `</div></div>`;
  }
  box.innerHTML = s + `</div>`;
}

// --------------------------------------------------------------- your board
function renderPlayer() {
  const p = G.P[ME];
  const sc = G.score().find((x) => x.seat === ME);
  const res = p.reserve.reduce((a, b) => a + b, 0);

  /* Laid out like the printed player board: one row per tier, unit slots that
   * empty as you settle, and the five victory-row slots pushed right with the
   * centre slot — the one that scores — called out. */
  let s = `<div class="pboard">
    <div class="pb-head"><span class="dot" style="background:${SEAT_C[ME]}"></span>
      <b>${SEAT_N[ME]}</b>
      <span class="tier">${BANDS[p.band()][0]}</span>
      <span class="purse">🪙 ${p.gold}</span>
      <span class="score">${sc.total} vp
        <em>pop ${sc.pop} · row ${sc.vrow} · dom ${sc.dom}</em></span></div>
    <div class="tiers">`;

  for (let j = 0; j < BANDS.length; j++) {
    const [name, units, meld, food, moves, , cap] = BANDS[j];
    const here = j === p.band();
    const left = p.reserve[j];
    let pips = "";
    for (let u = 0; u < units; u++)
      pips += `<i class="uslot${u < left ? " full" : ""}"
        style="${u < left ? `background:${SEAT_C[ME]}` : ""}"></i>`;
    let coins = food ? "" : `<span class="free">free</span>`;
    for (let f = 0; f < food; f++) coins += `<i class="cslot"></i>`;
    s += `<div class="tier-row${here ? " here" : ""}">
      <span class="mlim" title="meld limit">${meld}</span>
      <span class="tname">${name}<em>${units} units</em></span>
      <span class="uslots">${pips}</span>
      <span class="food" title="food per recycle">${coins}</span>
      <span class="mv" title="free moves">${moves}<em>mv</em></span>
      <span class="cap" title="highest rank you may buy">${cap}</span>
    </div>`;
  }
  s += `</div>`;

  // victory row — five slots, pushed right, centre slot marked
  const live = mine() && ["turn", "effectA"].includes(REQ.type);
  const sorted = p.vrow.slice().sort(cardSortUI);
  const pad = 5 - sorted.length;
  s += `<div class="vrowbox"><span class="vlab">victory row</span><div class="vslots">`;
  for (let k = 0; k < 5; k++) {
    const centre = k === 2;
    if (k < pad) {
      s += `<span class="vslot empty${centre ? " centre" : ""}"></span>`;
    } else {
      const c = sorted[k - pad];
      const on = SEL.vcard === c ? " pick" : "";
      const inner = live
        ? cardBtn(c, on, `data-row="${p.vrow.indexOf(c)}"`, "mid")
        : cardChip(c, "", "", "mid");
      s += `<span class="vslot${centre ? " centre" : ""}">${inner}</span>`;
    }
  }
  const scoring = sorted.length >= 3 ? sorted[sorted.length - 3].r : null;
  s += `</div><span class="vsum">${sorted.length} card${sorted.length === 1 ? "" : "s"}${
    scoring !== null ? ` + centre <b>${scoring}</b>` : ""} = <b>${sc.vrow} vp</b>${
    sorted.length && sorted.length < 3
      ? ` <span class="muted">— the centre slot starts paying at three</span>` : ""
  }</span></div></div>`;

  // your objective(s) — secret ones are yours alone, open ones are shared
  if (p.objectives && p.objectives.length) {
    const shared = G.OBJECTIVES_MODE === "open";
    s += `<div class="objbox"><span class="vlab">${shared
      ? "shared objectives — anyone may build these"
      : "your secret objective"}</span><div class="objrow">` +
      p.objectives.map((o) => objCard(o, G.objectiveDone(ME, o) ? "done" : "")).join("") +
      `</div></div>`;
  }

  // hand
  s += `<div class="handbox"><span class="vlab">hand (${p.hand.length})</span><div id="hand">`;
  const handPick = mine() && ["meld", "bonus", "discard", "retire"].includes(REQ.type);
  s += p.hand.slice().sort(cardSortUI).map((c) => {
    const idx = p.hand.indexOf(c);
    const on = SEL.meld.includes(c) ? " sel" : "";
    const playable = !handPick || REQ.type === "meld" || REQ.options.includes(c);
    return cardBtn(c, on + (playable && handPick ? "" : handPick ? " dead" : ""),
                   `data-hand="${idx}"`, "mid");
  }).join("") || `<span class="muted">empty</span>`;
  s += `</div></div>`;

  $("#player").innerHTML = s;
  $("#player").querySelectorAll("[data-hand]").forEach((n) =>
    n.addEventListener("click", () => onHandCard(G.P[ME].hand[Number(n.dataset.hand)])));
  $("#player").querySelectorAll("[data-row]").forEach((n) =>
    n.addEventListener("click", () => {
      const c = G.P[ME].vrow[Number(n.dataset.row)];
      SEL.vcard = SEL.vcard === c ? null : c;
      SEL.mode = null; SEL.card = null;
      render();
    }));
}

function onHandCard(c) {
  if (!mine()) return;
  if (REQ.type === "meld") {
    const i = SEL.meld.indexOf(c);
    if (i >= 0) SEL.meld.splice(i, 1); else SEL.meld.push(c);
    render();
    return;
  }
  if (["bonus", "discard", "retire"].includes(REQ.type) && REQ.options.includes(c)) {
    if (REQ.type === "retire" && RESEARCH) { RESEARCH.retired = c; RESEARCH.stage = "over"; }
    answer(c, REQ.type === "retire" && !!RESEARCH);
  }
}

// --------------------------------------------------------------- prompt
function meldOk() {
  return SEL.meld.length >= 1 && SEL.meld.length <= G.P[ME].meldLimit()
         && isLegalMeld(SEL.meld);
}

function renderPrompt() {
  const bar = $("#prompt");
  bar.innerHTML = "";
  if (G.finished()) return renderFinal(bar);
  if (!REQ) { bar.appendChild(el("div", "ask muted", "Opponents are playing…")); return; }
  if (!mine()) { bar.appendChild(el("div", "ask muted", "Waiting…")); return; }

  const ask = (t) => bar.appendChild(el("div", "ask", t));
  const btn = (label, fn, cls, dis) => {
    const b = el("button", "go " + (cls || ""), label);
    b.disabled = !!dis;
    b.addEventListener("click", fn);
    bar.appendChild(b);
    return b;
  };
  const p = G.P[ME];

  switch (REQ.type) {
    case "meld": {
      const sum = SEL.meld.reduce((a, c) => a + c.r, 0);
      const lim = p.meldLimit();
      /* Two different reasons a selection can be unplayable, and saying the
       * wrong one is worse than saying nothing: 8-9-9 IS an unbroken run, it
       * is simply three cards at a limit of two. */
      let verdict = "";
      if (SEL.meld.length) {
        if (!isLegalMeld(SEL.meld)) {
          const rs = [...new Set(SEL.meld.map((c) => c.r))].sort((a, b) => a - b);
          const gaps = [];
          for (let r = rs[0]; r <= rs[rs.length - 1]; r++) if (!rs.includes(r)) gaps.push(r);
          verdict = `<span class='bad'>not an unbroken run</span>` +
            (gaps.length ? ` — missing ${gaps.join(", ")}` : "");
        } else if (SEL.meld.length > lim) {
          verdict = `<span class='bad'>${SEL.meld.length} cards, over your ` +
            `${BANDS[p.band()][0]} meld limit of ${lim}</span> — drop ` +
            `${SEL.meld.length - lim}`;
        } else {
          verdict = `<span class='ok'>legal</span>`;
        }
      }
      ask(`<b>Card phase.</b> Play a meld — an unbroken run of ranks, duplicates free,
        suits irrelevant, up to <b>${lim}</b> cards. Click cards in your hand.
        ${SEL.meld.length ? ` — ${SEL.meld.length} selected, total ${sum}, ${verdict}` : ""}`);
      btn("Play meld", () => {
        const want = new Set(SEL.meld);
        answer(REQ.options.find((o) => o.length === want.size && o.every((c) => want.has(c))));
      }, "", !meldOk());
      break;
    }

    case "turn":
      if (RESEARCH && !["preview", "over"].includes(RESEARCH.stage)) {
        RESEARCH.blocked = !RESEARCH.bought;     // engine ended it early
        RESEARCH.stage = "over";
      }
      return renderTurn(bar, ask, btn, p);

    case "bonus":
      ask(`<b>You won the trick.</b> Spend one extra card from hand — click it.`); break;
    case "setaside":
      ask(`<b>You matched the winner's card count.</b> Only the trick winner uses every
        card. Set one of your played cards aside — it earns <b>1 gold</b> instead of a
        map action.`);
      rowPicker(bar, REQ.options, (c) => answer(c));
      break;
    case "discard":
      ask(`<b>You matched the winner's card count and lost.</b> Give one card from hand,
        face down, to the shared pile — click it.`); break;
    case "retire":
      if (RESEARCH) {
        researchPanel(bar, "retire", p);
        ask(`<b>Click a card in your hand</b> to retire it into your victory row.`);
      } else {
        ask(`<b>Retire a card</b> from hand to your victory row — click it. The row scores
          1 per card plus its third-highest rank.`);
      }
      break;
    case "gridslot":
      ask(`Place the drawn card ${cardChip(REQ.card)} on a market position — click one.
        Stacking buries what is underneath.`); break;
    case "buy":
      ask(`<b>Take a card</b> at or below rank ${p.rankCap()} — click a lit market slot.`);
      btn("Cancel", () => answer(null), "alt");
      break;
    case "effectA":
      if (SEL.vcard) { vcardPanel(bar, p); btn("Play no effect", () => answer(null), "alt"); break; }
      ask(`<b>Declare step.</b> You may spend one victory card on its <b>A</b> effect to
        add cards to this trick's count — declared blind, before you see anyone else's
        meld. <b>Click a card in your victory row</b> to see what it offers, or skip.`);
      btn("Skip", () => answer(null), "alt");
      break;
    case "feed":
      ask(`<b>Famine.</b> You owe ${REQ.owed} gold and hold ${p.gold}. Cash a victory card,
        or take the loss — each gold short sends one unit home.`);
      rowPicker(bar, REQ.options, (c) => answer(c));
      btn("Take the loss", () => answer(null), "alt");
      break;
    case "objective": {
      ask(`<b>Secret objective.</b> You were dealt two. Keep one — it stays hidden all
        game and scores <b>4 points</b> at the end if you have built it. Every chain is
        three tiles <b>you occupy</b>, the middle touching both ends.`);
      const pick = el("div", "objpick");
      pick.innerHTML = REQ.options.map((o, i) => objCard(o, "", `data-obj="${i}"`)).join("");
      bar.appendChild(pick);
      pick.querySelectorAll("[data-obj]").forEach((n) =>
        n.addEventListener("click", () => answer(REQ.options[Number(n.dataset.obj)])));
      break;
    }
    case "conquest":
      ask(`<b>${effectDText(REQ.card.r).d.split(":")[0]}.</b> ${REQ.left} strike${
        REQ.left > 1 ? "s" : ""} left — click a highlighted rival tile.
        ${REQ.maySettle ? "A tile you empty is settled with one of your units."
                        : "This band removes a unit but does not take the ground."}
        A fortification coin absorbs the hit first.`);
      btn("Stop", () => answer(null), "alt");
      break;
    case "waterexplore":
      if (!SEL.waterCell) {
        ask(`<b>Water advantage.</b> Your first sea move grants one free tile of
          <b>any</b> terrain. Click a highlighted space.`);
        btn("Skip", () => answer(null), "alt");
      } else {
        ask(`<b>Which terrain?</b>`);
        for (const t of REQ.terrains)
          btn(TL[t], () => answer({ cell: SEL.waterCell, terrain: t }), "terr " + t);
        btn("Back", () => { SEL.waterCell = null; render(); }, "alt");
      }
      break;
  }
}

/* The whole action laid out at once: what will happen, in what order, what it
 * costs, and which step we are on. The complaint this answers is not "which
 * button" but "what am I in the middle of, and when does it end". */
function researchPanel(bar, stage, p) {
  const R = RESEARCH || {};
  const cap = p.rankCap();
  const step = (n, state, label, result) =>
    `<li class="rs ${state}"><span class="marker">${
      state === "done" ? "✓" : state === "now" ? "▸" : "·"}</span>
      <span class="rl">${label}</span>
      ${result ? `<span class="rr">${result}</span>` : ""}</li>`;

  const st = (n) => stage === n ? "now" : (["preview","gridslot","buy","retire","over"]
    .indexOf(stage) > ["preview","gridslot","buy","retire","over"].indexOf(n) ? "done" : "todo");

  const box = el("div", "research");
  box.innerHTML = `
    <div class="rhead"><b>Research</b>
      <span class="muted">${stage === "preview" ? "3 steps · 1 gold · once per turn"
        : stage === "over" ? "complete" : "step " +
          ({ gridslot: 1, buy: 2, retire: 3 })[stage] + " of 3"}</span></div>
    <ol class="rsteps">
      ${step(1, st("gridslot"),
        "Draw the top upgrade card and place it on the market grid",
        R.drew ? `drew ${R.drew.r}${SUIT_LETTER[R.drew.s]}` : "")}
      ${step(2, st("buy"),
        `Take one face-up card at or below rank <b>${cap}</b> — it goes into your hand`,
        R.bought ? `took ${R.bought.r}${SUIT_LETTER[R.bought.s]}` : "")}
      ${step(3, st("retire"),
        "Retire a card from your hand to your victory row",
        R.retired ? `retired ${R.retired.r}${SUIT_LETTER[R.retired.s]}` : "")}
    </ol>
    <div class="rfoot">${stage === "preview"
      ? `Costs <b>1 gold</b> (you have ${p.gold}). Once begun the card is drawn and your
         research for this turn is used, even if you take nothing.`
      : stage === "over"
      ? (R.blocked
          ? `<span class="bad">Nothing on the grid was at or below rank ${cap}.</span>
             The draw stays on the grid and your research for this turn is used.`
          : `Research complete. Your research for this turn is used.`)
      : `Costs 1 gold · your one research this turn.`}</div>`;
  bar.appendChild(box);
  return box;
}

/* A victory card, face up, with its three effects as the buttons. This is the
 * whole point of the row: a retired card is not a point token, it is a choice
 * between winning a trick, founding colonies, and gold. Each effect says why it
 * cannot be used rather than just going grey. */
function vcardPanel(bar, p) {
  const c = SEL.vcard;
  if (!c) return false;
  const e = effectText(c.r);
  const inCardPhase = REQ.type === "effectA";
  const o = REQ.type === "turn" ? REQ.opts : null;

  const third = thirdEffect(c);
  const canA = inCardPhase;
  const canB = !!o && o.colonyCards.includes(c);
  const canThird = !!o && (deckIsD() ? !o.conquestBlocked : true);
  const whyThird = !o ? "map phase only"
    : deckIsD() ? o.conquestBlocked : "map phase only";
  /* Say the true reason. A 16–20 colony takes ANY terrain, so "no tiles of that
   * terrain" would be a lie for exactly the cards most likely to be spent. */
  const sameSuit = effectBv22(c.r)[2];
  const whyB = !o ? "map phase only"
    : o.colonyBlocked ? o.colonyBlocked
    : sameSuit ? `no ${TL[c.s]} tiles left in the supply`
    : "no tiles left in the supply";

  const box = el("div", "vpanel");
  box.innerHTML = `
    <div class="vp-card">${cardChip(c, "", "", "full")}</div>
    <div class="vp-opts">
      <div class="vp-lead">Spend this card on <b>one</b> of its three effects.
        It then leaves the game.</div>
      ${[["A", e.a, canA, inCardPhase ? "" : "card phase only — declared before melds"],
         ["B", e.b, canB, whyB],
         [third.key, third.long, canThird, whyThird]]
        .map(([k, txt, ok, why]) => `
        <button class="vp-opt${ok ? "" : " off"}" data-fx="${k}" ${ok ? "" : "disabled"}>
          <span class="ab">${k}</span>
          <span class="vp-txt">${txt}</span>
          ${ok ? "" : `<span class="vp-why">${why}</span>`}
        </button>`).join("")}
    </div>`;
  bar.appendChild(box);

  box.querySelectorAll("[data-fx]").forEach((n) =>
    n.addEventListener("click", () => {
      const k = n.dataset.fx;
      if (k === "A") return answer(c);
      if (k === "B") return answer({ kind: "colony", card: c });
      answer({ kind: k === "D" ? "conquest" : "cashRow", card: c });
    }));
  const back = el("button", "go alt", "Keep this card");
  back.addEventListener("click", () => { SEL.vcard = null; render(); });
  bar.appendChild(back);
  return true;
}

/* An objective card: the chain it asks for, drawn as three terrain chips with
 * the middle one marked, because the shape is the whole point. */
function objCard(o, cls, attr) {
  const chip = (t, mid) => `<span class="ochip${mid ? " mid" : ""}"
    style="background:${TC[t]}" title="${TL[t]}">${SUIT_LETTER[t]}</span>`;
  const tag = attr === undefined ? "span" : "button";
  return `<${tag} class="objcard ${cls || ""}" ${attr || ""}>
    <span class="oname">${o.name}<em>${o.points} pts</em></span>
    <span class="ochain">${chip(o.a)}${chip(o.mid, true)}${chip(o.b)}</span>
    <span class="oflav">${o.a === o.b
      ? `a ${TL[o.a]}, a ${TL[o.mid]}, another ${TL[o.b]} — in a chain`
      : `a ${TL[o.a]}, next to a ${TL[o.mid]}, next to an ${TL[o.b]}`}</span>
  </${tag}>`;
}

function rowPicker(bar, options, fn) {
  const row = el("div", "rowpick");
  row.innerHTML = options.map((c, i) => cardBtn(c, "", `data-p="${i}"`)).join("");
  bar.appendChild(row);
  row.querySelectorAll("[data-p]").forEach((n) =>
    n.addEventListener("click", () => fn(options[Number(n.dataset.p)])));
}

/* The map phase: everything still legal, all at once, in any order. */
function renderTurn(bar, ask, btn, p) {
  const o = REQ.opts;
  const left = o.cards.length;

  if (RESEARCH && RESEARCH.stage === "preview") {
    researchPanel(bar, "preview", p);
    btn("Begin research", () => {
      RESEARCH = { stage: "gridslot" };
      answer({ kind: "research" });
    });
    btn("Not now", () => { RESEARCH = null; render(); }, "alt");
    return;
  }
  if (RESEARCH && RESEARCH.stage === "over") {
    researchPanel(bar, "over", p);
    btn("Continue my turn", () => { RESEARCH = null; render(); });
    return;
  }

  if (SEL.mode === "move") {
    ask(`<b>Free move — ${o.moves} left.</b> ${SEL.moveSrc
      ? "Click a destination."
      : "Click a unit. Land moves cross your own tiles; a ship crosses open ocean."}`);
    btn(SEL.moveSrc ? "Pick another unit" : "Cancel", () => {
      if (SEL.moveSrc) SEL.moveSrc = null; else SEL.mode = null;
      render();
    }, "alt");
    return;
  }
  if (SEL.mode === "fortify") {
    ask(`<b>Fortify.</b> 1 gold puts a coin on one of your tiles; it absorbs the next
      attack. Click a tile.`);
    btn("Cancel", () => { SEL.mode = null; render(); }, "alt");
    return;
  }
  if (SEL.vcard) { vcardPanel(bar, p); return; }

  ask(`<b>Your map turn.</b> ${left
    ? `${left} meld card${left > 1 ? "s" : ""} left — click one, then a highlighted hex,
       or cash it. Do anything below in any order.`
    : `All cards spent. Anything else before you end the turn?`}${
    p.vrow.length ? ` <span class="muted">Click a card in your victory row to spend it
      on colonies or ${deckIsD() ? "conquest" : "gold"}.</span>` : ""}`);

  // the meld cards still in hand for this turn
  if (left) {
    const strip = el("div", "meldstrip");
    strip.innerHTML = o.cards.map((m, i) => {
      const on = SEL.card === m.card ? " sel" : "";
      // a card with no legal map action is still worth a coin: never dead
      const nomap = m.options.length ? "" : " nomap";
      return cardBtn(m.card, on + nomap, `data-turn="${i}"`, "mid");
    }).join("");
    bar.appendChild(strip);
    strip.querySelectorAll("[data-turn]").forEach((n) =>
      n.addEventListener("click", () => {
        SEL.card = o.cards[Number(n.dataset.turn)].card; SEL.mode = null; render();
      }));
    if (SEL.card) {
      const e = o.cards.find((m) => m.card === SEL.card);
      if (!e.options.length)
        ask(`<span class="bad">No legal map action for that card</span> — its suit reaches
             no tile or space you can use.`);
      btn(`Cash ${SEL.card.r}${SUIT_LETTER[SEL.card.s]} for 1 gold`,
          () => answer({ kind: "cash", card: SEL.card }), "alt");
    }
  }

  const acts = el("div", "acts");
  bar.appendChild(acts);
  const abtn = (label, fn, dis, title) => {
    const b = el("button", "go alt" + (dis ? " off" : ""), label);
    if (title) b.title = title;
    b.disabled = !!dis;
    b.addEventListener("click", fn);
    acts.appendChild(b);
  };

  abtn(REQ.state.researched ? "Research ✓ used" : "Research",
       () => { RESEARCH = { stage: "preview" }; render(); }, !o.canResearch,
       o.researchBlocked || "Draw a card, take one, retire one — 1 gold");
  abtn(`Move (${o.moves})`, () => { SEL.mode = "move"; SEL.card = null; render(); },
       !o.moves || !o.moveSources.length,
       !o.moves ? "no free moves left this turn" : "no unit has anywhere to go");
  abtn(`Fortify`, () => { SEL.mode = "fortify"; SEL.card = null; render(); },
       !o.fortifyCells.length, p.gold < 1 ? "needs 1 gold" : "nothing to fortify");

  const endLabel = left ? `End turn (${left} card${left > 1 ? "s" : ""} → ${left} gold)`
                        : "End turn";
  const end = el("button", "go end", endLabel);
  end.addEventListener("click", () => answer({ kind: "end" }));
  acts.appendChild(end);
}

function renderFinal(bar) {
  const sc = G.score().slice().sort((a, b) => b.total - a.total || b.gold - a.gold);
  let s = `<div class="ask"><b>Game over</b> — ${G.endedOn}, after ${G.round} rounds.</div>`;
  const anyObj = sc.some((d) => d.objDone && d.objDone.length);
  s += `<table class="final"><tr><th>Seat</th><th>Population</th><th>Victory row</th>
        <th>Dominance</th>${anyObj ? "<th>Objective</th>" : ""}<th>Total</th></tr>`;
  for (const d of sc) {
    s += `<tr class="${d.seat === ME ? "me" : ""}"><td><span class="dot"
      style="background:${SEAT_C[d.seat]}"></span>${SEAT_N[d.seat]}${
      d.seat === ME ? " (you)" : ""}</td><td>${d.pop}</td><td>${d.vrow}</td>
      <td>${d.dom}</td>`;
    if (anyObj) {
      s += `<td>${(d.objDone || []).map((x) =>
        `<span class="${x.done ? "ok" : "muted"}">${x.o.name}${
          x.done ? ` +${x.o.points}` : " ✗"}</span>`).join("<br>") || "—"}</td>`;
    }
    s += `<td><b>${d.total}</b></td></tr>`;
  }
  bar.innerHTML = s + `</table>`;
  const again = el("button", "go", "New game");
  again.addEventListener("click", () => {
    $("#setup").classList.remove("hide");
    $("#game").classList.remove("show");
  });
  bar.appendChild(again);
}

// --------------------------------------------------------------- sidebar
function renderMarket() {
  const p = G.P[ME];
  const lit = mine() && (REQ.type === "buy" || REQ.type === "gridslot")
    ? new Set(REQ.options) : null;
  let s = `<span class="vlab">market — you may take rank ≤ ${p.rankCap()}
    <span class="muted">· deck ${G.deck.length}</span></span><div class="grid">`;
  for (let k = 0; k < G.grid.length; k++) {
    const top = G.gridTop(k);
    const on = lit && lit.has(k);
    const over = top && top.r > p.rankCap();
    s += `<button class="slot${on ? " hot" : ""}${over ? " over" : ""}" data-slot="${k}"
      title="${over ? "above your rank cap" : ""}">`;
    s += top ? cardChip(top, "", "", "mid") : `<span class="muted">—</span>`;
    s += `<em>${G.grid[k].length > 1 ? "×" + G.grid[k].length : ""}</em></button>`;
  }
  $("#market").innerHTML = s + `</div>`;
  $("#market").querySelectorAll("[data-slot]").forEach((n) =>
    n.addEventListener("click", () => {
      const k = Number(n.dataset.slot);
      if (!mine() || !REQ.options || !REQ.options.includes(k)) return;
      if (REQ.type === "gridslot") { if (RESEARCH) RESEARCH.stage = "buy"; answer(k, true); }
      else if (REQ.type === "buy") {
        if (RESEARCH) { RESEARCH.bought = G.gridTop(k); RESEARCH.stage = "retire"; }
        answer(k, true);
      }
    }));
}

function renderSide() {
  let s = `<h3>Rivals</h3>`;

  const sc = G.score();
  for (const q of G.P) {
    if (q.i === ME) continue;
    const d = sc.find((x) => x.seat === q.i);
    s += `<div class="pl${q.i === G.leader ? " lead" : ""}">
      <div class="plhead"><span class="dot" style="background:${SEAT_C[q.i]}"></span>
        <b>${SEAT_N[q.i]}</b><span class="tier">${BANDS[q.band()][0]}</span>
        <span class="score">${d.total}</span></div>
      <div class="stats"><span>🪙 ${q.gold}</span><span>meld ≤${q.meldLimit()}</span>
        <span>reserve ${q.reserve.reduce((a, b) => a + b, 0)}</span>
        <span>hand ${q.hand.length}</span></div>
      <div class="vrow">${q.vrow.length
        ? q.vrow.slice().sort(cardSortUI).map((c) => cardChip(c)).join("")
        : `<span class="muted">no victory cards</span>`}</div></div>`;
  }
  $("#side").innerHTML = s;

  $("#log").innerHTML = G.log.slice(-12).map(([r, t]) => `<div><b>R${r}</b> ${t}</div>`).join("");
  $("#log").scrollTop = $("#log").scrollHeight;
  $("#roundno").textContent = G.round;
  $("#endnote").textContent = G.endedOn ? `· final rounds — ${G.endedOn}` : "";
}

window.addEventListener("DOMContentLoaded", () => {
  $("#start").addEventListener("click", startGame);
  $("#zin").addEventListener("click", () => zoom(0.1));
  $("#zout").addEventListener("click", () => zoom(-0.1));
  $("#n-players").addEventListener("change", () => {
    const n = Number($("#n-players").value);
    const sel = $("#my-seat");
    sel.innerHTML = "";
    for (let i = 0; i < n; i++) sel.innerHTML += `<option value="${i}">${i} — ${SEAT_N[i]}</option>`;
  });
  $("#n-players").dispatchEvent(new Event("change"));
  window.addEventListener("resize", () => { if (G) renderMap(); });
});
