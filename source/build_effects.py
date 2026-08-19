# -*- coding: utf-8 -*-
"""Blink — Card Effects reference. Generated, so it cannot drift from the rules.

Reuses the rulebook stylesheet; the per-rank table is derived from the same four
rank bands the rulebook prints, so the two can never disagree.
"""
import pathlib
from version import VTAG

src = pathlib.Path("build_html.py").read_text(encoding="utf-8")
CSS = src.split('CSS = """', 1)[1].split('"""', 1)[0]

EXTRA = """
.bands td:first-child{font-family:"IBM Plex Mono",monospace;white-space:nowrap}
.allranks{font-size:.86rem}
.allranks td{padding:.34rem .7rem .34rem 0}
.allranks td:first-child{font-family:"IBM Plex Mono",monospace;
  font-variant-numeric:tabular-nums;width:3rem}
.allranks tbody tr:nth-child(5n) td{border-bottom:1.5px solid var(--stone)}
.ruling{border-left:3px solid var(--ocean);padding:.1rem 0 .1rem 1rem;margin:1.3rem 0;
  max-width:var(--measure)}
.ruling .tag{font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--stone);display:block;margin-bottom:.3rem}
"""

# the four bands: (ranks, A, B, C)
# A changed in v0.23. The trick is won on the highest TOTAL RANK, so "+1 card"
# bought almost nothing — it moved a tie-break that only runs when two totals
# are exactly equal. A now adds the card's own rank to your total, which has the
# happy property of needing no table at all: the same sentence prints on all
# twenty cards, and the number a player needs is the one already on the card.
BANDS = [
    ("1–5",   "Add this card's <b>rank</b> to your meld's total for this trick",
              "<b>Found a colony</b>: 1 new tile of this suit, 1 unit on it, fortified", "2 gold"),
    ("6–10",  "Add this card's <b>rank</b> to your total, <b>and win ties</b>",
              "<b>Distant colony</b>: as above, and the tile may sit up to 2 out", "3 gold"),
    ("11–15", "Add this card's <b>rank</b> to your meld's total",
              "<b>Open a frontier</b>: 2 new tiles of this suit, 1 unit on one, fortified", "4 gold"),
    ("16–20", "Add this card's <b>rank</b> to your total, <b>and win ties</b>",
              "<b>Two colonies</b>: 2 new tiles of ANY terrain, 1 unit on each, both fortified", "5 gold"),
]
SHORT = [("+rank to your total", "colony, this suit", "2 gold"),
         ("+rank, wins ties", "colony, up to 2 out", "3 gold"),
         ("+rank to your total", "2 tiles, 1 unit", "4 gold"),
         ("+rank, wins ties", "2 colonies, any terrain", "5 gold")]


def band_rows():
    return "".join(
        f"<tr><td>{r}</td><td>{a}</td><td>{b}</td><td class='num-cell'>{c}</td></tr>"
        for r, a, b, c in BANDS)


def rank_rows():
    out = ""
    for rank in range(1, 21):
        a, b, c = SHORT[(rank - 1) // 5]
        out += (f"<tr><td>{rank}</td><td>{a}</td><td>{b}</td>"
                f"<td class='num-cell'>{c}</td></tr>")
    return out


HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blink — Card Effects</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}{EXTRA}</style>
</head>
<body>
<div class="sheet">

<header class="mast pad">
  <p class="eyebrow">Reference · victory-card effects</p>
  <h1>Card Effects</h1>
  <p class="sub">The three things a victory card can do</p>
  <p class="meta"><span>Companion to base game rules {VTAG}</span><span>Toby Siko</span></p>
</header>
<div class="steprule"><i></i><i></i><i></i><i></i></div>

<main class="pad">

<section>
  <div class="h2"><span class="num">—</span><h2>The three effects</h2></div>
  <p class="lede">Every civilization card carries three printed effects. A card sitting in your
  <strong>victory row</strong> may be spent on exactly one of them, after which the card leaves
  the game — your row shrinks, and your end score with it. The options are always the same three
  kinds; only their strength grows with the card's rank.</p>
  <table class="bands">
    <thead><tr><th>Rank</th><th>A · card phase</th><th>B · map phase</th><th>C · any time</th></tr></thead>
    <tbody>{band_rows()}</tbody>
  </table>
  <p><strong>A</strong> is declared in the <em>declare step</em> at the top of the round, before
  any meld is played — blind, knowing only your own hand. <strong>B</strong> is used during your
  own map phase, when the board in front of you is already settled. <strong>C</strong> may be
  taken at any moment, even mid-payment when feeding falls short.</p>
</section>

<section>
  <div class="h2"><span class="num">01</span><h2>Three rulings</h2></div>

  <h3>What a colony is — effect B</h3>
  <p>B no longer settles into ground you already hold. It <strong>founds new ground</strong>:
  you lay tiles, put units on them from your board, and fortify them. At most
  <strong>one victory card may be spent on B per turn</strong>.</p>
  <p>The fortification coins come from the <strong>general supply</strong>, not from your
  own gold — B is the one place in Blink where a fortification is free.</p>
  <div class="ruling">
    <span class="tag">Placement</span>
    <p>Every colony tile still obeys <b>touch-two</b>: it must touch at least two tiles
    already on the map. <b>Reach does not apply</b> — a colony may be founded anywhere along
    the map's edge, not only beside your own civilization. Ranks <b>1&ndash;15</b> place tiles
    matching the spent card's suit; ranks <b>16&ndash;20</b> may place any terrain. Ranks
    <b>6&ndash;10</b> may reach up to two tiles out, laying the intervening tile first.</p>
  </div>
  <div class="ruling">
    <span class="tag">Two tiles, one unit</span>
    <p>Ranks <b>11&ndash;15</b> lay two tiles but take only <b>one</b> unit from your board:
    settle and fortify that one, and leave the second tile as open ground. Units come from
    the topmost tier holding any, so a colony still empties your board and still raises your
    food bill.</p>
  </div>

  <h3>What “add this card’s rank” means — effect A</h3>
  <p>This changes only the total the trick is judged on. It never adds cards to your meld, never
  puts a unit on the map, and never lets you exceed your meld-size limit. Your meld is still
  exactly the cards you physically played — a straight of four is four cards to spend, whatever
  you declared.</p>
  <p>The bonus is virtual: when the highest total wins, your meld is worth more, so it can take a
  trick it would otherwise lose. The reward is tempo — you win the trick, spend your full meld,
  and act first — not size.</p>
  <p>A spent victory card is <b>gone</b>: it leaves the game, not your hand, and it is no longer
  worth points in your victory row at the end. That is the whole cost. So declaring a 19 buys
  nineteen points of trick and gives up a card that was scoring for you.</p>
  <p class="fine">In v0.22 this effect read “+1 / +2 cards”, because the trick went to the most
  cards. Under a total, one extra card was worth an average card and the wording had to change
  with the rule. The v0.22 version is in the variants book.</p>

  <h3>Several A effects in one trick</h3>
  <p>Nothing stops two or more players spending A in the same round. Each applies, and the trick
  resolves on the modified totals — highest total wins, then most cards, then highest single
  rank, then earliest played, exactly as normal. Because every declaration is made before any meld is
  played, nobody can answer anybody: you are all guessing at once, and finding out together.</p>
  <div class="ruling">
    <span class="tag">A is a bet, B is a decision</span>
    <p>The difference in timing is the difference in kind. <strong>A</strong> is spent before you
    have seen a single card, so it is a wager on a trick you might have won anyway.
    <strong>B</strong> is spent in your own map phase with the board in front of you, so it is
    never a gamble — only a question of whether the units are worth the card.</p>
  </div>
  <div class="ruling">
    <span class="tag">Two players both winning ties</span>
    <p>If two players each spend an effect that <em>wins ties</em> and they are still tied, the
    player who spent the <strong>higher-ranked card</strong> takes the trick.</p>
  </div>
</section>

<section>
  <div class="h2"><span class="num">02</span><h2>Every card, at a glance</h2></div>
  <p>The production reference: the exact A / B / C each rank prints. All four suits of a rank
  share the same effects. A card's suit matters only for effect B's terrain requirement, and for
  the meld shapes the card can join.</p>
  <table class="allranks">
    <thead><tr><th>Rank</th><th>A · trick</th><th>B · map</th><th>C · gold</th></tr></thead>
    <tbody>{rank_rows()}</tbody>
  </table>
</section>

</main>

<div class="pad"><footer>Blink · card effects reference · companion to base game rules {VTAG} ·
Toby Siko · deep-diversions.com/blink · @tobysiko.bsky.social</footer></div>

</div>
</body>
</html>
"""

out = pathlib.Path("./Blink-card-effects.html")
out.write_text(HTML, encoding="utf-8")
print("wrote", out, len(HTML), "bytes")
