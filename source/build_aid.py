# -*- coding: utf-8 -*-
"""Blink -- the player aid. One card each, four to a page.

WHAT IT IS FOR. The app tells you what you may do because it can only offer
legal things; at a table nobody does. Everything a turn contains is in the
rulebook, spread over four sections, and a player who has to look up "can I
still fortify?" has stopped playing. So: one card, in front of each player, with
the whole turn on it.

IT IS A FOLD-OVER, for the reason the perk tokens are. Duplex registration is
the thing print-and-play does worst, and a two-sided card whose faces are two
millimetres out looks broken. Both faces print on one side of the sheet, side by
side; fold backwards along the middle and the card is double thickness with the
turn on one face and the numbers on the other. Nothing needs rotating.

LANDSCAPE, 88x63mm -- a poker card turned on its side, so it belongs in the same
box as the deck, and four fit on one A4 page: one page is a whole table's worth.

WHAT IS ON IT. The front is the turn as a MENU, in the order you meet it: the
four things a card can be, then everything that is free. The back is every
number you would otherwise interrupt somebody to ask for. What is deliberately
NOT on it: any explanation. This is a reminder for a player who has been taught,
not a second rulebook -- the moment it starts teaching it stops being scannable,
and Your First Game already teaches.

    python3 build_aid.py           ->  Blink-player-aid.html
    python3 build_aid.py --bw      ->  Blink-player-aid-bw.html
"""
import pathlib
import sys

from version import VTAG

BW = "--bw" in sys.argv

# ---- palette, matching the player board and the perk tokens --------------
if BW:
    INK, SOFT, FAINT = "#000000", "#3A3A3A", "#9A9A9A"
    PAPER, PANEL, LINE = "#FFFFFF", "#F0F0F0", "#000000"
    GOLD, FOREST, OCEAN, STONE = "#000000", "#000000", "#000000", "#000000"
else:
    INK, SOFT, FAINT = "#2A2E2B", "#6B6F68", "#B9B4A8"
    PAPER, PANEL, LINE = "#FBFAF6", "#EFECE3", "#CDC7B8"
    GOLD, FOREST, OCEAN, STONE = "#C9992B", "#37704A", "#256A8C", "#8A837A"

# ---- geometry ------------------------------------------------------------
W, H = 88.0, 63.0                 # finished card, mm -- a poker card sideways
PER_PAGE = 4                      # 4 x 63mm = 252mm, inside an A4 text height

# ---- the turn, as the table meets it -------------------------------------
# (key, colour, what, detail)
CARD_USES = [
    ("SETTLE",  GOLD,   "one unit from your top tier"),
    ("EXPLORE", FOREST, "lay a tile: it must touch TWO already there. "
                        "Rank 10 or under also pays 1 gold"),
    ("ATTACK",  "#C0392B", "a duel — your rank vs their card + the ground"),
    ("CASH",    STONE,  "take 1 gold"),
]

FREE = [
    ("MOVE", "your tier's number",
     "by land across your own units onto a free tile, or by sea across empty "
     "Ocean. Never an attack."),
    ("WATER", "first sea move",
     "explore one free tile of ANY terrain, anywhere. Touch-two applies; "
     "reach does not."),
    ("RESEARCH", "twice · 1 then 2 gold",
     "draw onto the highest rank showing, retire your lowest card, buy one at "
     "or under your cap."),
    ("FORTIFY", "1 gold",
     "a coin on a unit. A lone card cannot attack it; an assault costs two "
     "cards and the lower rank fights."),
    ("GOLD", "free",
     "shift coins between reserve, food and walls. Research is one way."),
    ("COLONY", "one a turn",
     "spend a card from your victory row on its B effect."),
]

TIERS = [
    ("Tribe",        "2", "2", "1", "—", "12", "—"),
    ("Settlement",   "3", "3", "2", "1", "14", "1"),
    ("Kingdom",      "5", "4", "3", "2", "16", "2"),
    ("Empire",       "5", "5", "4", "3", "18", "3"),
    ("Civilization", "5", "6", "5", "4", "20", "4"),
]

TERRAIN = [("Plains", GOLD, "holds 3"), ("Forest", FOREST, "2 · +1 defence"),
           ("Ocean", OCEAN, "1 · sea road"), ("Mountain", STONE, "1 · +2 defence")]

CSS = f"""
@page {{ size: A4; margin: 9mm 8mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: {PAPER}; color: {INK};
       font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.sheet {{ width: {2 * W}mm; font-size: 0; }}

/* One aid = two faces side by side with the fold between them. */
.aid {{ display: block; width: {2 * W}mm; height: {H}mm; position: relative;
       border: .25mm dashed {FAINT}; }}
.face {{ position: absolute; top: 0; height: {H}mm; width: {W}mm;
        padding: 2.4mm 2.8mm 1.4mm; overflow: hidden; }}
.face.front {{ left: 0; }}
.face.back  {{ left: {W}mm; background: {PANEL}; }}
/* The fold, marked at both ends so it cannot be taken for a cut line. */
.fold {{ position: absolute; left: {W}mm; top: 0; height: {H}mm;
        border-left: .3mm dotted {SOFT}; }}
.fold::before, .fold::after {{ content: ""; position: absolute; left: -1.4mm;
        border-left: 1.4mm solid transparent; border-right: 1.4mm solid transparent; }}
.fold::before {{ top: 0; border-top: 1.8mm solid {SOFT}; }}
.fold::after {{ bottom: 0; border-bottom: 1.8mm solid {SOFT}; }}

.hd {{ font-size: 6.2pt; letter-spacing: .16em; font-weight: 600;
      text-transform: uppercase; color: {SOFT}; }}
.hd b {{ color: {INK}; }}
.rule {{ border-top: .3mm solid {LINE}; margin: 1mm 0 1.1mm; }}
.lead {{ font-size: 5.4pt; letter-spacing: .12em; text-transform: uppercase;
        color: {SOFT}; margin: 0 0 .7mm; }}

/* the four things a card can be */
.use {{ display: flex; gap: 1.6mm; align-items: baseline; margin: 0 0 .65mm; }}
.use .k {{ font-size: 6.6pt; font-weight: 600; letter-spacing: .04em;
          width: 13.5mm; flex: none; }}
.use .d {{ font-size: 5.2pt; line-height: 1.2; color: {INK}; }}
.both {{ font-size: 5pt; line-height: 1.22; color: {SOFT};
        border-top: .3mm solid {LINE}; padding-top: .9mm; margin-top: .3mm; }}
.both b {{ color: {INK}; }}

/* the free actions */
.free {{ display: flex; gap: 1.6mm; align-items: baseline; margin: 0 0 .4mm; }}
.free .k {{ font-size: 5.8pt; font-weight: 600; width: 13.5mm; flex: none; }}
.free .k em {{ display: block; font-style: normal; font-size: 4.5pt;
              font-weight: 400; color: {SOFT}; letter-spacing: .02em; }}
.free .d {{ font-size: 5pt; line-height: 1.18; }}

/* the numbers */
table {{ border-collapse: collapse; width: 100%; font-size: 5.3pt; }}
th {{ font-weight: 600; font-size: 4.6pt; letter-spacing: .07em;
     text-transform: uppercase; color: {SOFT}; text-align: right;
     padding: 0 0 .5mm .8mm; }}
th.n, td.n {{ text-align: left; }}
td {{ padding: .38mm 0 .38mm .8mm; text-align: right; border-top: .2mm solid {LINE}; }}
td.n {{ font-weight: 600; }}
.note {{ font-size: 4.8pt; line-height: 1.3; color: {SOFT}; margin: .8mm 0 0; }}
.ter {{ display: flex; flex-wrap: wrap; gap: .8mm 2.4mm; font-size: 5pt;
       margin: 1mm 0 0; }}
.ter span {{ white-space: nowrap; }}
.ter i {{ display: inline-block; width: 1.6mm; height: 1.6mm; border-radius: .3mm;
         margin-right: .6mm; }}
.foot {{ position: absolute; left: 3mm; right: 3mm; bottom: 1.8mm;
        font-size: 4.4pt; color: {FAINT}; display: flex;
        justify-content: space-between; }}
"""


def front():
    uses = "".join(
        f'<div class="use"><span class="k" style="color:{c}">{k}</span>'
        f'<span class="d">{d}</span></div>' for k, c, d in CARD_USES)
    free = "".join(
        f'<div class="free"><span class="k">{k}<em>{w}</em></span>'
        f'<span class="d">{d}</span></div>' for k, w, d in FREE)
    return f"""<div class="face front">
  <div class="hd"><b>Your turn</b> · map phase</div>
  <div class="rule"></div>
  <p class="lead">Each card of your meld — one of</p>
  {uses}
  <div class="both">Every card: <b>in reach</b> (a tile you hold, or one beside it)
    and its <b>suit matches the terrain</b>. No units on the map? Act anywhere.</div>
  <p class="lead" style="margin-top:1.2mm">Free · no card · any order</p>
  {free}
</div>"""


def back():
    rows = "".join(
        f'<tr><td class="n">{n}</td><td>{u}</td><td>{m}</td><td>{mv}</td>'
        f'<td>{f}</td><td>{c}</td><td>{a}</td></tr>'
        for n, u, m, mv, f, c, a in TIERS)
    ter = "".join(f'<span><i style="background:{c}"></i>{n} {d}</span>'
                  for n, c, d in TERRAIN)
    return f"""<div class="face back">
  <div class="hd"><b>The numbers</b></div>
  <div class="rule"></div>
  <table>
    <tr><th class="n">Tier</th><th>Units</th><th>Meld</th><th>Moves</th>
        <th>Food</th><th>Cap</th><th>Asc.</th></tr>
    {rows}
  </table>
  <p class="note">Read your top tier that still holds units. Food is due each
    recycle and is not cumulative; ascension is paid once, on arrival.</p>
  <div class="ter">{ter}</div>
  <p class="note" style="margin-top:1.1mm"><b>Round.</b> Declare A → everyone plays a
    meld → highest total wins → the winner's die shows their meld size and leads,
    others 2/3/4 → spend in that order. Matched the winner and lost: set one card
    aside, take 1 gold. Last: 1 gold.</p>
  <p class="note"><b>Meld.</b> Any unbroken run; duplicates free, suits irrelevant.
    2-3-3-4-4 ✓ · 2-2-4-4 ✗ (no 3).</p>
  <p class="note"><b>Duel.</b> Your spent card's rank against their hand card plus the
    ground. Higher wins; level goes to the card matching the ground, and otherwise to
    the defender. Clear the last unit and the tile is yours — settle it at once.</p>
  <p class="note"><b>End.</b> A last unit placed, or the market down to one layer:
    finish the round, play one more. Score 1 per unit · 1 per row card, plus the
    centre rank at 3+ · 3 per terrain dominated.</p>
  <div class="foot"><span>Blink {VTAG}</span><span>deep-diversions.com/blink</span></div>
</div>"""


def main():
    aid = f'<div class="aid">{front()}<div class="fold"></div>{back()}</div>'
    sheet = "".join(aid for _ in range(PER_PAGE))
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Blink — player aid</title>
<style>{CSS}</style></head>
<body><div class="sheet">{sheet}</div></body></html>"""
    name = "Blink-player-aid-bw.html" if BW else "Blink-player-aid.html"
    pathlib.Path(name).write_text(html, encoding="utf-8")
    print(f"  {name}  ({PER_PAGE} aids, {W:.0f}x{H:.0f}mm folded)")


if __name__ == "__main__":
    main()
