# -*- coding: utf-8 -*-
"""Blink — turn-by-turn replay viewer.

Plays one game, snapshots the table after every round, and writes a single
self-contained HTML file you can flip through with the arrow keys. No
dependencies, no server, no build step: open the file.

    python3 replay.py [seed] [players] > /dev/null   # writes replay.html

What a frame shows
------------------
  the map      every tile, its terrain, who holds it and how many units,
               with fortification coins marked
  the players  tier, gold, units on the map, victory row, running score
  the cards    every hand in full, the meld each player played this round,
               the 3x3 market grid with its stack depths, and the SHARED PILE
               with its contents and its size across the whole game
  the round    what each player played, who won the trick, and the events
               that followed (settles, colonies, attacks, ascensions)
  the clock    upgrade deck, shared pile, and how deep the market still is —
               the game ends when the market thins to a SINGLE LAYER

The point is not analytics. It is to watch one game and notice the thing a
summary table cannot show you: when the map stops growing, when someone runs
away with it, whether the ending arrives with any warning.
"""
import json, pathlib, sys, html
import engine as E

TERR_COLOUR = {"plains": "#C9992B", "forest": "#37704A",
               "ocean": "#256A8C", "mountain": "#8A837A"}
SEAT_COLOUR = ["#C0392B", "#2F6F8F", "#7A5CA8", "#4E7A32"]


def axial(col, row):
    """Pointy-top odd-r offset -> pixel centre, matching the rulebook figures."""
    x = 26 * (col + 0.5 * (row & 1))
    y = 22 * row
    return x, y


SUIT_SHORT = {"plains": "P", "forest": "F", "ocean": "O", "mountain": "M"}


def cards(cs):
    """[(rank, suit)] -> [[rank, suit-letter]] for the viewer."""
    return [[c[0], SUIT_SHORT[c[1]]] for c in sorted(cs)]


class Tracker:
    """Watches one game and records where every CARD and every COIN went.

    The first version of this viewer inferred the meld by diffing the personal
    discard across a round. That is wrong twice over: the market card you buy is
    appended to the same discard (so a purchase looked like a played card), and
    the card you retire to the victory row is often taken back OUT of it. The
    result was a 'played' row that did not match the hand, and a deck that
    appeared to lose cards for no reason.

    So we watch the five moments a card leaves a player instead of guessing:
      meld     -> the cards played as a meld: ALWAYS an unbroken run of ranks
      bonus    -> the trick winner's one extra card (§04). It is NOT part of the
                  meld and does not have to extend the run — the rulebook's own
                  example spends a 3 of Plains after a meld of 15-16. Showing it
                  inside the meld made legal play look illegal.
      retired  -> pulled out by _maybe_upgrade, goes to the victory row
      bought   -> taken from the market grid into the personal discard
      dropped  -> match-discard, face down to the SHARED pile (leaves the deck)
    Only `dropped` shrinks a player's ten cards, and only until the next recycle.
    """

    def __init__(self, g):
        self.g = g
        self.clear()
        cls = type(g)
        self._orig = (cls._place, cls._maybe_upgrade, cls._pick_discard,
                      cls._pick_bonus)
        place, upgrade, pick, bonus = self._orig
        t = self

        def _place(self, p, cs):
            t.spent.setdefault(p.i, []).extend(cs)
            return place(self, p, cs)

        def _pick_bonus(self, p):
            c = bonus(self, p)
            if c is not None:
                t.bonus[p.i] = c
            return c

        def _maybe_upgrade(self, p):
            before_row = len(p.vrow)
            before_hand, before_disc = list(p.hand), list(p.discard)
            r = upgrade(self, p)
            if len(p.vrow) > before_row:
                gone = p.vrow[-1]
                t.retired[p.i] = gone
                # Retiring must come out of the HAND. The purchase now lands in
                # the hand too (BUY_INTO_HAND), so look in both places for what
                # arrived rather than assuming the discard.
                after = list(before_hand)
                if gone in after:
                    after.remove(gone)
                    t.rfrom[p.i] = ""
                else:
                    t.rfrom[p.i] = "!! from the table"
                new = [c for c in p.hand if c not in after]
                if not new:
                    new = [c for c in p.discard if c not in before_disc]
                t.bought[p.i] = new[-1] if new else None
                if t.bought[p.i] is None:
                    t.bought.pop(p.i)
            return r

        def _pick_discard(self, p):
            d = pick(self, p)
            t.dropped[p.i] = d
            return d

        (cls._place, cls._maybe_upgrade, cls._pick_discard,
         cls._pick_bonus) = (_place, _maybe_upgrade, _pick_discard, _pick_bonus)

    def restore(self):
        cls = type(self.g)
        (cls._place, cls._maybe_upgrade, cls._pick_discard,
         cls._pick_bonus) = self._orig

    def meld_of(self, seat):
        """What was played AS A MELD: everything spent, less the bonus card."""
        spent = list(self.spent.get(seat, []))
        b = self.bonus.get(seat)
        if b is not None and b in spent:
            spent.remove(b)
        return spent

    def clear(self):
        self.spent, self.retired, self.bought, self.dropped = {}, {}, {}, {}
        self.rfrom, self.bonus = {}, {}


def money(ledger, seat):
    """The round's coin movements for one seat, as '+1 ascension' strings."""
    out = []
    for _, i, _phase, kind, n in ledger:
        if i != seat:
            continue
        sign = -1 if kind.startswith("spend") else 1
        label = kind.split(": ", 1)[-1]
        if out and out[-1][0] == label:
            out[-1][1] += sign * n
        else:
            out.append([label, sign * n])
    return [[lab, amt] for lab, amt in out if amt]


def snapshot(g, log, tr=None, led=()):
    tiles = []
    for (c, r), t in sorted(g.m.tiles.items()):
        x, y = axial(c, r)
        tiles.append(dict(x=round(x, 1), y=round(y, 1), t=t.terrain,
                          o=(t.owner if t.owner is not None else -1),
                          n=len(t.units), g=t.gold))
    scores = {d["seat"]: d for d in g.score()}
    sp = tr.spent if tr else {}
    players = []
    for p in g.P:
        d = scores[p.i]
        one = lambda m: cards([m[p.i]]) if tr and p.i in m else []
        players.append(dict(
            seat=p.i, tier=E.BANDS[p.band()][0], limit=p.meld_limit(),
            gold=p.gold, onmap=d["pop"], vrow=len(p.vrow),
            score=d["total"], reserve=sum(p.reserve), cap=p.rank_cap(),
            hand=cards(p.hand),                 # the whole hand, not a count
            meld=cards(tr.meld_of(p.i) if tr else []),   # the run, and only the run
            bonus=one(tr.bonus if tr else {}),           # the winner's extra card
            legal=(E.is_legal_meld(tr.meld_of(p.i)) if tr and tr.meld_of(p.i)
                   else True),
            bought=one(tr.bought if tr else {}),
            retired=one(tr.retired if tr else {}),
            rfrom=(tr.rfrom.get(p.i, "") if tr else ""),
            dropped=one(tr.dropped if tr else {}),
            disc=len(p.discard),
            deck=len(p.hand) + len(p.discard),  # your ten cards, minus losses
            money=money(led, p.i),
            row=cards(p.vrow)))
    # the market: top card of each grid position, plus how deep the stack is
    grid = []
    for st in g.grid:
        if st:
            grid.append(dict(r=st[-1][0], s=SUIT_SHORT[st[-1][1]], d=len(st)))
        else:
            grid.append(None)
    return dict(round=g.round, tiles=tiles, players=players, log=log,
                deck=len(g.deck), pile=len(g.pile),
                pilecards=cards(g.pile), grid=grid,
                ended=(g.ended_on[0] if g.ended_on else None))


def play_and_record(n=3, seed=5, cap=80):
    g = E.Game(n, seed=seed, bot=E.pro_bot)
    g.smart = True
    g.pro = set(range(n))
    g._deal()
    tr = Tracker(g)
    frames = [snapshot(g, ["Setup — starting map dealt, hands drafted."])]
    prev = dict(g.stats)
    while not g.finished() and g.round < cap:
        tr.clear()
        mark = len(g.ledger)
        g.play_round()
        led = g.ledger[mark:]
        cur = dict(g.stats)

        def d(k):
            return cur.get(k, 0) - prev.get(k, 0)

        log = []
        w = g.leader                      # winner leads the next round
        log.append(f"Seat {w} won the trick.")
        bits = []
        for k, label in (("settle", "settled"), ("explore", "explored"),
                         ("killed_by_attack", "units killed"),
                         ("colony_tile", "colony tiles"),
                         ("colony_unit", "colony units"),
                         ("match_discard", "discards to the pile"),
                         ("water_explore", "water explores"),
                         ("free_move", "free moves"),
                         ("upgrades", "upgrades"),
                         ("ascensions", "ascensions"),
                         ("starved_back", "starved"),
                         ("cards_to_gold", "cards cashed")):
            if d(k):
                bits.append(f"{d(k)} {label}")
        if bits:
            log.append(" · ".join(bits))
        if g.ended_on and g.ended_on[1] == g.round:
            log.append(f"END TRIGGERED — {g.ended_on[0]}.")
        frames.append(snapshot(g, log, tr, led))
        prev = cur
    tr.restore()
    return g, frames


HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Blink replay — %(title)s</title>
<style>
:root{--paper:#EDEAE1;--page:#FBFAF6;--ink:#1C1F1D;--soft:#5A5F59;--rule:#CDC7B8}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:"IBM Plex Sans",-apple-system,"Segoe UI",sans-serif;font-size:14px}
.wrap{max-width:1240px;margin:0 auto;padding:18px}
header{display:flex;justify-content:space-between;align-items:baseline;
  border-bottom:2px solid var(--ink);padding-bottom:8px;margin-bottom:14px}
h1{font-size:22px;margin:0;letter-spacing:-.02em}
.meta{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--soft)}
.bar{display:flex;gap:10px;align-items:center;margin-bottom:14px}
button{font:inherit;padding:5px 12px;border:1.5px solid var(--ink);
  background:var(--page);border-radius:5px;cursor:pointer}
button:hover{background:#e8e4d8}
input[type=range]{flex:1}
.grid{display:grid;grid-template-columns:1fr 300px;gap:16px}
.card{background:var(--page);border:1px solid var(--rule);border-radius:6px;padding:12px}
svg{display:block;width:100%%;height:auto}
h2{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--soft);
  margin:0 0 8px;font-weight:600}
table{width:100%%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;font-size:10px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--soft);border-bottom:1px solid var(--ink);padding:0 4px 3px 0}
td{padding:4px 4px 4px 0;border-bottom:1px solid var(--rule)}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%%;margin-right:5px}
.log{font-size:12.5px;line-height:1.5}
.log div{padding:3px 0;border-bottom:1px dotted var(--rule)}
.clock{display:flex;gap:14px;font-family:ui-monospace,Menlo,monospace;font-size:11.5px;
  color:var(--soft);margin-top:8px}
.end{color:#C0392B;font-weight:600}
.spark{height:46px;width:100%%}
.chip{display:inline-flex;flex-direction:column;align-items:center;justify-content:center;
  width:22px;height:30px;border:1px solid #1C1F1D;border-radius:3px;background:#fff;
  margin:0 2px 3px 0;font-size:11px;font-weight:700;line-height:1;vertical-align:top}
.chip i{display:block;width:100%%;height:4px;border-radius:2px 2px 0 0;margin-bottom:2px}
.chip.dim{opacity:.32}
.chip.big{width:26px;height:36px;font-size:12.5px}
.hands{font-size:12px}
.prow{border-bottom:1px solid var(--rule);padding:8px 0}
.prow:last-child{border-bottom:none}
.cols{display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap}
.col{min-width:90px}
.col.sep{border-left:2px solid var(--rule);padding-left:12px}
.who{font-weight:600;white-space:nowrap;min-width:132px}
.chip.hi{box-shadow:inset 0 0 0 1.5px #B8952E}
.lbl{font-family:ui-monospace,Menlo,monospace;font-size:9.5px;color:var(--soft);
  letter-spacing:.06em;text-transform:uppercase;display:block;margin-bottom:2px}
.acct{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;color:var(--soft);
  margin-top:5px}
.acct b{color:var(--ink)}
.acct .neg{color:#C0392B}
.acct .pos{color:#2E7D46}
.short{color:#C0392B;font-weight:700}
.pilenote{font-family:ui-monospace,Menlo,monospace;font-size:10px;
  color:var(--soft);margin:2px 0 6px}
#pile{min-height:34px}
.lbl.bad{color:#C0392B;font-weight:700}
.mkt{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}
.slot{border:1px solid var(--rule);border-radius:4px;padding:6px;text-align:center;
  background:#fff}
.slot.empty{background:#F0ECE2;border-style:dashed}
.depth{font-family:ui-monospace,Menlo,monospace;font-size:9px;color:var(--soft);
  display:block;margin-top:3px}
.row2{display:grid;grid-template-columns:230px 1fr;gap:16px;margin-top:14px}
.over{outline:2px solid #C0392B;outline-offset:1px}
</style></head><body><div class="wrap">

<header>
  <h1>Blink replay</h1>
  <div class="meta">%(title)s</div>
</header>

<div class="bar">
  <button id="prev">&larr; prev</button>
  <button id="next">next &rarr;</button>
  <button id="play">play</button>
  <input type="range" id="slider" min="0" max="0" value="0">
  <div class="meta" id="counter"></div>
</div>

<div class="grid">
  <div class="card">
    <h2>The map</h2>
    <svg id="map" viewBox="0 0 640 420"></svg>
    <div class="clock" id="clock"></div>
  </div>
  <div>
    <div class="card" style="margin-bottom:14px">
      <h2>Players</h2>
      <table id="players"></table>
      <svg class="spark" id="spark" viewBox="0 0 280 46"></svg>
    </div>
    <div class="card">
      <h2>This round</h2>
      <div class="log" id="log"></div>
    </div>
  </div>
</div>

<div class="row2">
  <div>
    <div class="card" style="margin-bottom:14px">
      <h2>Market &mdash; 3&times;3 grid</h2>
      <div class="mkt" id="market"></div>
      <div class="clock" id="mktclock"></div>
    </div>
    <div class="card">
      <h2>Shared pile</h2>
      <div id="pile"></div>
      <svg class="spark" id="pilechart" viewBox="0 0 240 54"></svg>
      <div class="clock" id="pileclock"></div>
    </div>
  </div>
  <div class="card">
    <h2>Hands and melds</h2>
    <div class="hands" id="hands"></div>
  </div>
</div>
</div>

<script>
const F = %(frames)s;
const TC = %(terr)s, SC = %(seat)s;
let i = 0, timer = null;

const $ = s => document.querySelector(s);
const slider = $("#slider");
slider.max = F.length - 1;

function hex(cx, cy, r){
  let p = [];
  for (let k = 0; k < 6; k++){
    const a = Math.PI/180 * (60*k - 30);
    p.push((cx + r*Math.cos(a)).toFixed(1) + "," + (cy + r*Math.sin(a)).toFixed(1));
  }
  return p.join(" ");
}

const SUITC = {P:"#C9992B", F:"#37704A", O:"#256A8C", M:"#8A837A"};

function chip(r, su, cls){
  return `<span class="chip ${cls||''}"><i style="background:${SUITC[su]}"></i>${r}</span>`;
}

function drawCards(f){
  // market: top card of each position, with stack depth
  $("#market").innerHTML = f.grid.map(g => g === null
    ? `<div class="slot empty"><span class="chip dim">&nbsp;</span><span class="depth">empty</span></div>`
    : `<div class="slot">${chip(g.r, g.s, "big")}<span class="depth">${g.d > 1 ? g.d + " deep" : "top"}</span></div>`
  ).join("");
  $("#mktclock").innerHTML = `<span>deck ${f.deck}</span><span>pile ${f.pile}</span>`;

  // the shared pile. Face down at the table — this is the designer's X-ray.
  $("#pile").innerHTML = f.pilecards.length
    ? `<div class="pilenote">${f.pilecards.length} card${f.pilecards.length>1?"s":""}, face down</div>`
      + f.pilecards.map(c => chip(c[0], c[1], c[0] >= 11 ? "hi" : "")).join("")
    : `<div class="pilenote">empty</div><span class="depth">nothing discarded yet</span>`;
  // size over the whole game, so you can see it is a trickle, not a reservoir
  const mx = Math.max(2, ...F.map(z => z.pile));
  const bw = 232 / F.length;
  $("#pilechart").innerHTML = F.map((z, k) => {
    const h = (z.pile / mx) * 40;
    return `<rect x="${(4 + k*bw).toFixed(1)}" y="${(46-h).toFixed(1)}" `
         + `width="${Math.max(1.5, bw-1.4).toFixed(1)}" height="${h.toFixed(1)}" `
         + `fill="${k===i ? "#C0392B" : "#B4AFA3"}"/>`;
  }).join("") + `<line x1="0" y1="46" x2="240" y2="46" stroke="#CDC7B8"/>`
    + `<text x="2" y="10" font-size="9" fill="#5A5F59" font-family="ui-monospace,Menlo,monospace">peak ${mx}</text>`;
  $("#pileclock").innerHTML = `<span>in play across the table</span>`;

  // every card that LEFT a player this round, in its own column
  const H = c => chip(c[0], c[1], c[0] >= 11 ? "hi" : "");
  const col = (label, cs, sep, empty) =>
    `<div class="col${sep?" sep":""}"><span class="lbl${label===label.toUpperCase()&&label.length>6?" bad":""}">${label}</span>`
    + (cs.length ? cs.map(H).join("") : `<span class="depth">${empty||"—"}</span>`)
    + `</div>`;

  let h = "";
  for (const p of f.players){
    // your deck is ten cards: hand + personal discard. Anything less went to
    // the SHARED pile via the match-discard; it returns at the next recycle.
    const lost = 10 - p.deck;
    const acct = p.money.map(([lab, amt]) =>
        `<span class="${amt<0?'neg':'pos'}">${amt>0?"+":""}${amt}</span> ${lab}`)
      .join(" · ") || "no coins moved";

    h += `<div class="prow"><div class="cols">`
       + `<div class="who"><span class="dot" style="background:${SC[p.seat]}"></span>`
       + `seat ${p.seat}<br><span class="depth">limit ${p.limit} · cap `
       + `${p.cap > 90 ? "\u2014" : p.cap} \u00b7 ${p.gold} gold</span></div>`
       + col(`hand (${p.hand.length})`, p.hand)
       + col(p.legal ? "meld" : "MELD — NOT A RUN", p.meld, true, "nothing played")
       + col("winner +1", p.bonus, false)
       + col(`retired → row${p.rfrom ? " ("+p.rfrom+")" : ""}`, p.retired, true)
       + col("bought", p.bought, false)
       + col("lost to pile", p.dropped, false)
       + col(`victory row ${p.row.length}/5`, p.row, true, "empty")
       + `</div><div class="acct">`
       + `deck <b>${p.deck}</b>/10 (hand ${p.hand.length} + discard ${p.disc})`
       + (lost > 0 ? ` <span class="short">−${lost} in the shared pile</span>` : "")
       + ` &nbsp;·&nbsp; ${acct}</div></div>`;
  }
  $("#hands").innerHTML = h;
}

function draw(){
  const f = F[i];
  // --- map, auto-centred on its own extent
  const xs = f.tiles.map(t=>t.x), ys = f.tiles.map(t=>t.y);
  const minx = Math.min(...xs), maxx = Math.max(...xs);
  const miny = Math.min(...ys), maxy = Math.max(...ys);
  const ox = 320 - (minx+maxx)/2, oy = 210 - (miny+maxy)/2;
  let s = "";
  for (const t of f.tiles){
    const cx = t.x + ox, cy = t.y + oy;
    s += `<polygon points="${hex(cx,cy,14)}" fill="${TC[t.t]}" stroke="#1C1F1D" stroke-width="1" opacity="0.92"/>`;
    if (t.n > 0){
      s += `<circle cx="${cx}" cy="${cy}" r="7" fill="${SC[t.o]}" stroke="#fff" stroke-width="1.4"/>`;
      if (t.n > 1)
        s += `<text x="${cx}" y="${cy+3.5}" text-anchor="middle" font-size="9" font-weight="700" fill="#fff">${t.n}</text>`;
    }
    if (t.g > 0){
      // one coin per fortified unit — a Plains tile can carry three
      s += `<circle cx="${cx+10}" cy="${cy-10}" r="${t.g > 1 ? 5.5 : 4}" fill="#E8C049" stroke="#8A6A18" stroke-width="1"/>`;
      if (t.g > 1)
        s += `<text x="${cx+10}" y="${cy-7.4}" text-anchor="middle" font-size="7.5" font-weight="700" fill="#5A4408">${t.g}</text>`;
    }
  }
  $("#map").innerHTML = s;

  // --- players
  let rows = "<tr><th>seat</th><th>tier</th><th>gold</th><th>map</th><th>row</th><th>score</th></tr>";
  for (const p of f.players){
    rows += `<tr><td><span class="dot" style="background:${SC[p.seat]}"></span>${p.seat}</td>`
         +  `<td>${p.tier}</td><td>${p.gold}</td><td>${p.onmap}</td>`
         +  `<td>${p.vrow}</td><td><b>${p.score}</b></td></tr>`;
  }
  $("#players").innerHTML = rows;

  // --- score sparkline to this point
  let sp = "";
  const N = F.length;
  for (let seat = 0; seat < f.players.length; seat++){
    const pts = F.slice(0, i+1).map((fr, k) => {
      const x = (k/(Math.max(1,N-1)))*272 + 4;
      const mx = Math.max(10, ...F.map(z=>Math.max(...z.players.map(q=>q.score))));
      const y = 42 - (fr.players[seat].score/mx)*38;
      return x.toFixed(1)+","+y.toFixed(1);
    }).join(" ");
    sp += `<polyline points="${pts}" fill="none" stroke="${SC[seat]}" stroke-width="1.8"/>`;
  }
  $("#spark").innerHTML = sp;

  // --- log + clock
  $("#log").innerHTML = f.log.map(l =>
     `<div${l.startsWith("END")?' class="end"':''}>${l}</div>`).join("");
  $("#clock").innerHTML =
      `<span>upgrade deck ${f.deck}</span><span>shared pile ${f.pile}</span>`
    + `<span>tiles ${f.tiles.length}</span>`
    + (f.ended ? `<span class="end">${f.ended}</span>` : "");
  drawCards(f);
  $("#counter").textContent = "round " + f.round + " / " + F[F.length-1].round;
  slider.value = i;
}

function go(k){ i = Math.max(0, Math.min(F.length-1, k)); draw(); }
$("#prev").onclick = () => go(i-1);
$("#next").onclick = () => go(i+1);
slider.oninput = e => go(+e.target.value);
$("#play").onclick = function(){
  if (timer){ clearInterval(timer); timer = null; this.textContent = "play"; return; }
  this.textContent = "pause";
  timer = setInterval(() => { if (i >= F.length-1){ clearInterval(timer); timer=null; $("#play").textContent="play"; } else go(i+1); }, 700);
};
document.addEventListener("keydown", e => {
  if (e.key === "ArrowLeft") go(i-1);
  if (e.key === "ArrowRight") go(i+1);
});
draw();
</script></body></html>
"""


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    g, frames = play_and_record(n=n, seed=seed)
    final = sorted(g.score(), key=lambda d: -d["total"])
    title = (f"{n} players · seed {seed} · {g.round} rounds · "
             f"{g.ended_on[0] if g.ended_on else 'no trigger'} · "
             f"winner seat {final[0]['seat']} on {final[0]['total']}")
    out = pathlib.Path("replay.html")
    out.write_text(HTML % dict(title=html.escape(title),
                               frames=json.dumps(frames, separators=(",", ":")),
                               terr=json.dumps(TERR_COLOUR),
                               seat=json.dumps(SEAT_COLOUR)),
                   encoding="utf-8")
    print(f"wrote {out} — {len(frames)} frames, {title}")


if __name__ == "__main__":
    main()
