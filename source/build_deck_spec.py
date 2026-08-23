# -*- coding: utf-8 -*-
"""Blink — full deck specification, with the proposed Effect D (Conquest).

A PROPOSAL document, not part of the v0.22 rules set. Effect D exists in the
simulator (`USE_EFFECT_D`, off by default) and in the findings; it has never
been printed on a card face. This lays out what the deck would look like if D
replaced C, so the decision can be made by looking at it rather than imagining
it.

Reads the stylesheet out of build_html.py as TEXT rather than importing it, so
it does not need figs.json — the same trick build_effects.py uses.
"""
import pathlib
from version import VTAG

src = pathlib.Path("build_html.py").read_text(encoding="utf-8")
CSS = src.split('CSS = """', 1)[1].split('"""', 1)[0]

EXTRA = """
.spec td:first-child{font-family:"IBM Plex Mono",monospace;white-space:nowrap;
  font-variant-numeric:tabular-nums}
.allranks{font-size:.86rem}
.allranks td{padding:.34rem .7rem .34rem 0}
.allranks td:first-child{font-family:"IBM Plex Mono",monospace;
  font-variant-numeric:tabular-nums;width:3rem}
.allranks tbody tr:nth-child(5n) td{border-bottom:1.5px solid var(--stone)}
.gone{text-decoration:line-through;color:var(--stone)}
.new{background:#EDF3EE}
.note-d{border-left:3px solid var(--forest);padding:.1rem 0 .1rem 1rem;
  margin:1.3rem 0;max-width:var(--measure)}
.note-d .tag{font-family:"IBM Plex Mono",monospace;font-size:.68rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--stone);
  display:block;margin-bottom:.3rem}
.count{font-family:"IBM Plex Mono",monospace;font-size:.8rem;color:var(--stone)}
"""

# (ranks, A, B, D) — C is dropped; D takes its place on the face
BANDS = [
    ("1–5",
     "Add this card's <b>rank</b> to your meld's total for this trick",
     "<b>Found a colony</b>: 1 new tile of this suit, 1 unit on it, fortified",
     "<b>Raid</b>: remove 1 rival unit from a tile touching your civilization"),
    ("6–10",
     "Add this card's <b>rank</b> to your total, <b>and win ties</b>",
     "<b>Distant colony</b>: as above, and the tile may sit up to 2 out",
     "<b>Seize</b>: remove 1 rival unit — and settle the tile if you empty it"),
    ("11–15",
     "Add this card's <b>rank</b> to your meld's total",
     "<b>Open a frontier</b>: 2 new tiles of this suit, 1 unit on one, fortified",
     "<b>Conquer</b>: remove 2 rival units, settling each tile you empty"),
    ("16–20",
     "Add this card's <b>rank</b> to your total, <b>and win ties</b>",
     "<b>Two colonies</b>: 2 new tiles of ANY terrain, 1 unit on each, both fortified",
     "<b>Overrun</b>: remove 2 rival units from ANY tiles you can reach, settling each"),
]
SHORT = [("+rank to your total", "colony, this suit", "raid 1"),
         ("+rank, wins ties", "colony, up to 2 out", "seize 1, settle"),
         ("+rank to your total", "2 tiles, 1 unit", "conquer 2, settle"),
         ("+rank, wins ties", "2 colonies, any terrain", "overrun 2, settle")]

SUITS = [("plains", "Plains"), ("forest", "Forest"),
         ("ocean", "Ocean"), ("mountain", "Mountain")]

COUNTS = [
    ("2 players", "6–10", "11–20", "20 cards", "40 cards",
     "ranks 1–5 stay in the box"),
    ("3 players", "3–10 †", "11–20", "30 cards", "40 cards",
     "ranks 1–2 stay in the box"),
    ("4 players", "1–10", "11–20", "40 cards", "40 cards",
     "every card is in play"),
]


def band_rows():
    return "".join(
        f"<tr><td>{r}</td><td>{a}</td><td>{b}</td><td class='new'>{d}</td></tr>"
        for r, a, b, d in BANDS)


def rank_rows():
    out = ""
    for rank in range(1, 21):
        a, b, d = SHORT[(rank - 1) // 5]
        cap = ("Tribe" if rank <= 12 else "Settlement" if rank <= 14 else
               "Kingdom" if rank <= 16 else "Empire" if rank <= 18 else
               "Civilization")
        out += (f"<tr><td>{rank}</td><td>{a}</td><td>{b}</td>"
                f"<td class='new'>{d}</td><td class='count'>{cap}</td></tr>")
    return out


def count_rows():
    return "".join(
        f"<tr><td>{n}</td><td>{s}</td><td>{u}</td>"
        f"<td class='count'>{sc}</td><td class='count'>{uc}</td>"
        f"<td class='count'>{note}</td></tr>"
        for n, s, u, sc, uc, note in COUNTS)


HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blink — deck specification with Effect D</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}{EXTRA}</style>
</head>
<body>
<div class="sheet">

<header class="mast pad">
  <p class="eyebrow">Blink · proposal, not yet a rule</p>
  <h1>The deck, with Effect D</h1>
  <p class="sub">What 80 cards look like if Conquest replaces Take Gold</p>
  <p class="meta"><span>rules {VTAG}</span><span>Toby Siko</span></p>
</header>
<div class="steprule"><i></i><i></i><i></i><i></i></div>

<main class="pad">

<section>
  <div class="h2"><span class="num">01</span><h2>The deck</h2></div>
  <p class="lede"><strong>80 cards: four suits &times; ranks 1–20.</strong> One
  card of each rank in each suit — Plains, Forest, Ocean, Mountain. The suit
  says which terrain the card acts on; the rank says how strong its printed
  effects are, and how hard it is to win a trick with.</p>

  <p>The deck splits by rank into a <strong>starting deck</strong> you draft
  from and an <strong>upgrade deck</strong> that feeds the market. Which ranks
  are used depends on the player count; the upgrade half is the full 11–20 at
  every count, so the tier rank caps mean something in every game.</p>

  <table class="spec">
    <thead><tr><th>Players</th><th>Starting deck</th><th>Upgrade deck</th>
      <th>starting</th><th>upgrade</th><th></th></tr></thead>
    <tbody>{count_rows()}</tbody>
  </table>
  <p class="fine">† <b>Three-player balance.</b> Ranks 3–10 give 32 starting
  cards for 30 dealt: draw two of the four rank-3 cards at random and keep them,
  boxing the other two.</p>
</section>

<section>
  <div class="h2"><span class="num">02</span><h2>Three effects per card</h2></div>
  <p>Every card carries three printed effects. A card in your victory row may be
  spent on <strong>exactly one</strong> of them, and then leaves the game. The
  three are one per ambition — win the round, grow, or take what someone else
  has grown.</p>

  <table class="spec">
    <thead><tr><th>Rank</th><th>A &middot; card phase</th>
      <th>B &middot; map phase</th><th>D &middot; map phase</th></tr></thead>
    <tbody>{band_rows()}</tbody>
  </table>

  <div class="note-d">
    <span class="tag">What changed, and why</span>
    <p><b>C — “take 2–5 gold” — is gone.</b> Measured across hundreds of games it
    was chosen almost never, and the reason was not its price: gold is the one
    resource a player can always print, by cashing a card from hand. An effect
    that returns gold cannot matter in an economy where gold is not what is
    scarce.</p>
    <p><b>D takes its place because attacking needed a reason to exist.</b> A
    card spent attacking removes a rival unit worth one point and puts nothing of
    yours on the ground — pure denial, which is why an aggressive player kills far
    more and wins no more. D settles what it empties, so a strike becomes a
    two-point swing, a tile, and a unit off your board: the step that climbs your
    tier ladder.</p>
  </div>

  <p>Gold has not gone anywhere. It still comes from cashing a card during your
  map phase, from ascension coins, and from ranking last in a trick — the three
  taps that already fund the whole economy between them.</p>
</section>

<section>
  <div class="h2"><span class="num">03</span><h2>All twenty ranks</h2></div>
  <p>The last column is the <strong>lowest tier that may buy this card</strong>
  from the market — the rank cap, printed on your player board as
  11 / 13 / 15 / 17 / 20.</p>
  <table class="allranks">
    <thead><tr><th>Rank</th><th>A</th><th>B</th><th>D</th>
      <th>buyable from</th></tr></thead>
    <tbody>{rank_rows()}</tbody>
  </table>
  <p class="fine">Each row is <b>four physical cards</b>, one per suit. Twenty
  rows, eighty cards.</p>
</section>

<section>
  <div class="h2"><span class="num">04</span><h2>What a card face has to carry</h2></div>
  <ul>
    <li>the <strong>rank</strong>, large, readable across the table and in a fan</li>
    <li>the <strong>suit</strong> as both colour and shape, at the top edge so a
    fanned hand still reads</li>
    <li><strong>three effect lines</strong>, labelled A / B / D, in that order —
    card phase first, then the two map-phase options</li>
    <li>nothing else. The tier numbers live on the player board; the terrain
    table lives on the aid.</li>
  </ul>
  <p>Three effects is also the printable number: four lines of effect text at a
  legible size does not fit a poker-sized face alongside a rank that has to be
  visible from across the table.</p>
</section>

<footer class="pad">
  <p class="fine">Blink · {VTAG} · deck specification with Effect D · Toby Siko ·
  a proposal; the base rules still print A / B / C</p>
</footer>

</main>
</div>
</body>
</html>
"""

out = pathlib.Path("./Blink-deck-with-D.html")
out.write_text(HTML, encoding="utf-8")
print("wrote", out, len(HTML), "bytes")
